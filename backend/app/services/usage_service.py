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
    },
    "pro": {
        "card": -1,  # unlimited
        "ocr": 1000,
        "visitor": -1,
        "batch_import": 500,
        "api": 5000,
    },
    "enterprise": {
        "card": -1,
        "ocr": -1,
        "visitor": -1,
        "batch_import": -1,
        "api": -1,
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
