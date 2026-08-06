"""
Usage Limit Service — 使用限制服务

基于 MECE 定价策略，对不同类型的用户（free/pro/enterprise）进行功能使用限制。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.usage_counter import UsageCounter
from app.models.user import User

logger = logging.getLogger(__name__)

# ===================================================================
# MECE 定价策略 — 层级与限制
# ===================================================================
# User.membership_tier 原始值: free / gold / diamond / board
# 映射到 MECE 层级: free → free, gold → pro, diamond/board → enterprise
# ===================================================================

TIER_MAP = {
    "free": "free",
    "gold": "pro",
    "diamond": "enterprise",
    "board": "enterprise",
}

# -1 表示无限制（unlimited）
MECE_LIMITS: dict[str, dict[str, int]] = {
    "free": {
        "card": 1,
        "ocr": 3,
        "visitor": 5,
        "batch_import": 10,
        "api": 100,
        "recommend": 30,  # 每月30次推荐
    },
    "pro": {
        "card": -1,  # unlimited
        "ocr": 1000,
        "visitor": -1,
        "batch_import": 500,
        "api": 5000,
        "recommend": -1,  # unlimited
    },
    "enterprise": {
        "card": -1,
        "ocr": -1,
        "visitor": -1,
        "batch_import": -1,
        "api": -1,
        "recommend": -1,  # unlimited
    },
}


def get_user_tier(user: User) -> str:
    """获取用户的 MECE 层级（free / pro / enterprise）。"""
    raw_tier = user.membership_tier or "free"
    return TIER_MAP.get(raw_tier, "free")


def get_limits(tier: str) -> dict[str, int]:
    """根据 MECE 层级返回功能限制字典。"""
    return MECE_LIMITS.get(tier, MECE_LIMITS["free"])


def get_feature_limit(tier: str, feature: str) -> int:
    """获取指定层级的某个功能限制值（-1 表示无限制）。"""
    limits = get_limits(tier)
    return limits.get(feature, 0)


async def check_limit(
    user_id: int,
    feature: str,
    db: AsyncSession | None = None,
) -> tuple[bool, int, int]:
    """
    检查用户对某个功能的使用是否已达上限。

    Returns:
        (allowed, remaining, limit)
        - allowed:   True = 允许继续使用, False = 已达上限
        - remaining: 剩余可用次数（-1 表示无限制）
        - limit:     功能上限（-1 表示无限制）
    """
    own_session = db is None
    if own_session:
        db = AsyncSessionLocal()

    try:
        # 获取用户信息
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False, 0, 0

        tier = get_user_tier(user)
        limit_num = get_feature_limit(tier, feature)

        # 无限制 → 直接放行
        if limit_num == -1:
            return True, -1, -1

        if limit_num == 0:
            return False, 0, 0

        # 查询当前使用量
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        result = await db.execute(
            select(UsageCounter).where(
                UsageCounter.user_id == user_id,
                UsageCounter.feature == feature,
                UsageCounter.period == "monthly",
                UsageCounter.reset_at >= period_start,
            )
        )
        counter = result.scalar_one_or_none()

        used = counter.used_count if counter else 0
        remaining = max(0, limit_num - used)

        return remaining > 0, remaining, limit_num
    finally:
        if own_session:
            await db.close()


async def increment_usage(
    user_id: int,
    feature: str,
    count: int = 1,
    db: AsyncSession | None = None,
) -> bool:
    """
    增加用户对某个功能的使用计数。

    如果对应的 UsageCounter 记录不存在则自动创建。
    Returns:
        True 表示增加成功（计数已更新）
    """
    own_session = db is None
    if own_session:
        db = AsyncSessionLocal()

    try:
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = period_start.replace(month=period_start.month + 1) if period_start.month < 12 else period_start.replace(year=period_start.year + 1, month=1)
        reset_at = next_month

        # 获取用户的层级上限
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        tier = get_user_tier(user)
        limit_num = get_feature_limit(tier, feature)

        # 尝试获取现有计数器
        result = await db.execute(
            select(UsageCounter).where(
                UsageCounter.user_id == user_id,
                UsageCounter.feature == feature,
                UsageCounter.period == "monthly",
                UsageCounter.reset_at >= period_start,
            )
        )
        counter = result.scalar_one_or_none()

        if counter:
            counter.used_count += count
            counter.limit_count = limit_num
        else:
            new_counter = UsageCounter(
                user_id=user_id,
                feature=feature,
                period="monthly",
                used_count=count,
                limit_count=limit_num,
                reset_at=reset_at,
            )
            db.add(new_counter)

        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.exception("增加使用计数失败: user_id=%s, feature=%s", user_id, feature)
        return False
    finally:
        if own_session:
            await db.close()


async def get_user_usage(
    user_id: int,
    db: AsyncSession,
) -> dict[str, dict]:
    """
    获取用户的完整使用情况（所有功能）。

    Returns:
        {
            "tier": "free",
            "limits": { ... },
            "usage": {
                "card": {"used": 1, "limit": 1, "remaining": 0},
                "ocr": {"used": 0, "limit": 3, "remaining": 3},
                ...
            }
        }
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {}

    tier = get_user_tier(user)
    limits = get_limits(tier)

    # 查询所有使用计数
    result = await db.execute(
        select(UsageCounter).where(
            UsageCounter.user_id == user_id,
            UsageCounter.period == "monthly",
        )
    )
    counters = result.scalars().all()

    usage_map: dict[str, int] = {}
    for c in counters:
        usage_map[c.feature] = c.used_count

    now = datetime.utcnow()
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result_usages: dict[str, dict] = {}

    for feature, limit_val in limits.items():
        used = usage_map.get(feature, 0)
        if limit_val == -1:
            remaining = -1
        else:
            remaining = max(0, limit_val - used)
        result_usages[feature] = {
            "used": used,
            "limit": limit_val,
            "remaining": remaining,
        }

    return {
        "tier": tier,
        "limits": limits,
        "usage": result_usages,
    }


# ===================================================================
# Token 追踪服务 — 双重计费支持
# ===================================================================
# 记录每次 AI 调用的 token 消耗，区分 internal/external 两类模型。
# internal: 按平台定价收费（固定单价）
# external: 按大模型成本 + 加价率收费
# ===================================================================


async def record_token_usage(
    user_id: int,
    feature: str,
    model_type: str,
    model_name: str,
    token_type: str = "chat",
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int | None = None,
    db: AsyncSession | None = None,
) -> bool:
    """记录一次 AI 调用的 token 消耗。

    自动计算费用（token_cost）和外部成本（external_cost）。
    如果当月已有该 feature 的 token 记录则累加，否则新建。

    Args:
        user_id: 用户 ID
        feature: 功能标识（如 ai_chat / ai_rag / ai_embed）
        model_type: "internal"（自有模型）或 "external"（第三方 LLM）
        model_name: 模型标准名（deepseek-chat / m3e / mlx 等）
        token_type: token 类型（chat / embedding / search / rule / query）
        prompt_tokens: 输入 token 数
        completion_tokens: 输出 token 数
        total_tokens: 总 token 数（默认 = prompt + completion）
        db: 数据库会话（可选，不传则自动创建）

    Returns:
        True 表示记录成功
    """
    from app.ai.token_pricing import calculate_cost, classify_model

    own_session = db is None
    if own_session:
        db = AsyncSessionLocal()

    try:
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (
            period_start.replace(month=period_start.month + 1)
            if period_start.month < 12
            else period_start.replace(year=period_start.year + 1, month=1)
        )
        reset_at = next_month

        # 自动分类 model_type（如果未指定）
        if not model_type:
            model_type = classify_model(model_name)

        token_count = total_tokens or (prompt_tokens + completion_tokens)

        # 计算费用
        cost_info = calculate_cost(
            model_type=model_type,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=token_count,
        )

        # 尝试获取现有计数器
        result = await db.execute(
            select(UsageCounter).where(
                UsageCounter.user_id == user_id,
                UsageCounter.feature == feature,
                UsageCounter.period == "monthly",
                UsageCounter.reset_at >= period_start,
            )
        )
        counter = result.scalar_one_or_none()

        if counter:
            # 累加 token 计数
            counter.used_count += 1  # 调用次数 +1
            counter.total_tokens += token_count
            counter.prompt_tokens += prompt_tokens
            counter.completion_tokens += completion_tokens
            counter.token_cost = round(counter.token_cost + cost_info["token_cost"], 6)
            counter.external_cost = round(counter.external_cost + cost_info["external_cost"], 6)

            # 如果已有记录没有 model_type 字段，更新它
            if not counter.model_type or counter.model_type == "internal":
                counter.model_type = model_type
            if not counter.model_name:
                counter.model_name = model_name
            if not counter.token_type or counter.token_type == "chat":
                counter.token_type = token_type
            counter.markup_rate = cost_info["markup_rate"]
        else:
            # 新建 token 追踪记录
            new_counter = UsageCounter(
                user_id=user_id,
                feature=feature,
                period="monthly",
                used_count=1,  # 调用次数
                limit_count=-1,  # token 无限制（默认）
                reset_at=reset_at,
                model_type=model_type,
                model_name=model_name,
                token_type=token_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=token_count,
                token_cost=round(cost_info["token_cost"], 6),
                external_cost=round(cost_info["external_cost"], 6),
                markup_rate=cost_info["markup_rate"],
            )
            db.add(new_counter)

        await db.commit()
        logger.debug(
            "Token usage recorded: user=%s, feature=%s, model_type=%s, "
            "model=%s, tokens=%d, cost=%.6f",
            user_id, feature, model_type, model_name,
            token_count, cost_info["token_cost"],
        )
        return True
    except Exception as e:
        await db.rollback()
        logger.exception(
            "记录 token 使用失败: user_id=%s, feature=%s, model=%s",
            user_id, feature, model_name,
        )
        return False
    finally:
        if own_session:
            await db.close()


async def get_token_usage_summary(
    user_id: int,
    db: AsyncSession,
) -> dict[str, dict]:
    """获取用户的 token 使用汇总。

    Returns:
        {
            "internal": {
                "total_tokens": N,
                "total_calls": N,
                "total_cost": M  (¥),
                "models": {...},
            },
            "external": {
                "total_tokens": N,
                "total_calls": N,
                "total_cost": M  (¥, 售价),
                "external_cost": C  (¥, 第三方成本),
                "markup_cost": C * markup_rate (¥, 加价部分),
                "models": {...},
            },
            "grand_total": {
                "total_tokens": N,
                "total_calls": N,
                "total_cost": M  (¥),
            }
        }
    """
    now = datetime.utcnow()
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(UsageCounter).where(
            UsageCounter.user_id == user_id,
            UsageCounter.period == "monthly",
            UsageCounter.reset_at >= period_start,
        )
    )
    counters = result.scalars().all()

    summary: dict[str, dict] = {
        "internal": {
            "total_tokens": 0,
            "total_calls": 0,
            "total_cost": 0.0,
            "models": {},
        },
        "external": {
            "total_tokens": 0,
            "total_calls": 0,
            "total_cost": 0.0,
            "external_cost": 0.0,
            "markup_cost": 0.0,
            "models": {},
        },
    }

    for c in counters:
        mt = c.model_type or "internal"
        if mt not in summary:
            continue

        cat = summary[mt]
        cat["total_tokens"] += c.total_tokens
        cat["total_calls"] += c.used_count
        cat["total_cost"] = round(cat["total_cost"] + c.token_cost, 6)

        if mt == "external":
            cat["external_cost"] = round(cat["external_cost"] + c.external_cost, 6)
            cat["markup_cost"] = round(cat["markup_cost"] + c.token_cost - c.external_cost, 6)

        # 按模型细分
        mname = c.model_name or "unknown"
        if mname not in cat["models"]:
            cat["models"][mname] = {
                "total_tokens": 0,
                "total_calls": 0,
                "total_cost": 0.0,
            }
        mod = cat["models"][mname]
        mod["total_tokens"] += c.total_tokens
        mod["total_calls"] += c.used_count
        mod["total_cost"] = round(mod["total_cost"] + c.token_cost, 6)

    grand_total = {
        "total_tokens": summary["internal"]["total_tokens"] + summary["external"]["total_tokens"],
        "total_calls": summary["internal"]["total_calls"] + summary["external"]["total_calls"],
        "total_cost": round(
            summary["internal"]["total_cost"] + summary["external"]["total_cost"], 6
        ),
    }

    return {
        "internal": summary["internal"],
        "external": summary["external"],
        "grand_total": grand_total,
    }


async def get_token_details(
    user_id: int,
    db: AsyncSession,
    model_type: str | None = None,
) -> list[dict]:
    """获取用户的 token 使用明细（按记录逐条返回）。

    Args:
        user_id: 用户 ID
        db: 数据库会话
        model_type: 可选筛选（internal / external），不传则返回全部

    Returns:
        按 created_at 降序排列的记录列表
    """
    now = datetime.utcnow()
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    query = select(UsageCounter).where(
        UsageCounter.user_id == user_id,
        UsageCounter.period == "monthly",
        UsageCounter.reset_at >= period_start,
    )

    if model_type:
        query = query.where(UsageCounter.model_type == model_type)

    query = query.order_by(UsageCounter.updated_at.desc())

    result = await db.execute(query)
    counters = result.scalars().all()

    return [
        {
            "id": c.id,
            "feature": c.feature,
            "model_type": c.model_type,
            "model_name": c.model_name,
            "token_type": c.token_type,
            "total_tokens": c.total_tokens,
            "prompt_tokens": c.prompt_tokens,
            "completion_tokens": c.completion_tokens,
            "token_cost": c.token_cost,
            "external_cost": c.external_cost,
            "markup_rate": c.markup_rate,
            "call_count": c.used_count,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in counters
    ]


async def get_platform_token_summary(
    db: AsyncSession,
) -> dict[str, dict]:
    """获取全平台的 token 使用汇总（管理员视角）。"""
    now = datetime.utcnow()
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(UsageCounter).where(
            UsageCounter.period == "monthly",
            UsageCounter.reset_at >= period_start,
        )
    )
    counters = result.scalars().all()

    summary: dict = {
        "internal": {"total_tokens": 0, "total_calls": 0, "total_cost": 0.0, "users": 0},
        "external": {"total_tokens": 0, "total_calls": 0, "total_cost": 0.0, "external_cost": 0.0, "users": 0},
    }
    internal_users: set[int] = set()
    external_users: set[int] = set()

    for c in counters:
        mt = c.model_type or "internal"
        cat = summary.get(mt)
        if not cat:
            continue
        cat["total_tokens"] += c.total_tokens
        cat["total_calls"] += c.used_count
        cat["total_cost"] = round(cat["total_cost"] + c.token_cost, 6)
        if mt == "external":
            cat["external_cost"] = round(cat["external_cost"] + c.external_cost, 6)
            external_users.add(c.user_id)
        else:
            internal_users.add(c.user_id)

    summary["internal"]["users"] = len(internal_users)
    summary["external"]["users"] = len(external_users)

    grand_total = {
        "total_tokens": summary["internal"]["total_tokens"] + summary["external"]["total_tokens"],
        "total_calls": summary["internal"]["total_calls"] + summary["external"]["total_calls"],
        "total_cost": round(summary["internal"]["total_cost"] + summary["external"]["total_cost"], 6),
    }

    return {"internal": summary["internal"], "external": summary["external"], "grand_total": grand_total}
