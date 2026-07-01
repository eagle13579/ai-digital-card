"""订阅/试用服务 — 免费→试用→升级完整转化漏斗。

定义套餐、试用验证、升级/降级逻辑。
所有函数都基于 SQLAlchemy async session 和当前 User 对象操作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import EnterpriseSubscription
from app.models.user import User

# ── 套餐定义 ─────────────────────────────────────────────────────────────


@dataclass
class PlanFeature:
    """单个套餐的功能特性描述"""
    name: str
    enabled: bool = True
    limit: Optional[int] = None       # 数量限制，None=无限制
    description: str = ""


@dataclass
class PlanConfig:
    """套餐配置"""
    tier: str
    name_cn: str
    name_en: str
    price_cents: int                     # 0 = 免费
    price_yuan: str
    interval: str = "month"              # month / year
    features: list[PlanFeature] = field(default_factory=list)
    feature_tags: list[str] = field(default_factory=list)
    max_seats: int = 1                   # 企业席位
    quota_per_month: int = 0             # 每月解锁配额
    trial_days_allowed: bool = False     # 是否允许试用此套餐


# ── 三档套餐定义 ─────────────────────────────────────────────────────────

PLANS: dict[str, PlanConfig] = {
    "free": PlanConfig(
        tier="free",
        name_cn="免费版",
        name_en="Free",
        price_cents=0,
        price_yuan="0",
        features=[
            PlanFeature(name="AI电子名片", description="创建并分享个人电子名片"),
            PlanFeature(name="基础匹配", description="每日有限次匹配推荐"),
            PlanFeature(name="访客记录", limit=30, description="最近30天访客记录"),
        ],
        feature_tags=["AI名片", "基础匹配", "30天访客记录"],
        quota_per_month=0,
    ),
    "standard": PlanConfig(
        tier="standard",
        name_cn="标准版",
        name_en="Standard",
        price_cents=9900,     # ¥99/月
        price_yuan="99",
        features=[
            PlanFeature(name="AI电子名片", description="创建并分享个人电子名片"),
            PlanFeature(name="智能匹配", description="AI驱动的精准人脉匹配"),
            PlanFeature(name="无限访客记录", description="完整访客分析"),
            PlanFeature(name="信任网络", description="构建信任关系链"),
            PlanFeature(name="导出数据", description="支持CSV/Excel导出"),
            PlanFeature(name="API访问", limit=1000, description="每月1000次API调用"),
        ],
        feature_tags=["AI名片", "智能匹配", "无限访客", "信任网络", "数据导出", "API"],
        quota_per_month=60,
        trial_days_allowed=True,
    ),
    "enterprise": PlanConfig(
        tier="enterprise",
        name_cn="企业版",
        name_en="Enterprise",
        price_cents=49900,    # ¥499/月
        price_yuan="499",
        features=[
            PlanFeature(name="AI电子名片", description="团队名片集中管理"),
            PlanFeature(name="智能匹配", description="AI驱动的精准人脉匹配"),
            PlanFeature(name="无限访客记录", description="完整访客分析与热力图"),
            PlanFeature(name="信任网络", description="团队级信任关系管理"),
            PlanFeature(name="导出数据", description="支持CSV/Excel/PDF导出"),
            PlanFeature(name="API访问", limit=10000, description="每月10000次API调用"),
            PlanFeature(name="SSO登录", description="企业单点登录集成"),
            PlanFeature(name="自定义域名", description="绑定企业自有域名"),
            PlanFeature(name="专属支持", description="7×24小时专属客服"),
            PlanFeature(name="团队协作", description="多席位团队管理"),
        ],
        feature_tags=["团队管理", "SSO", "自定义域名", "专属支持", "高级API", "无限访客"],
        quota_per_month=500,
        trial_days_allowed=True,
    ),
}

# 套餐等级权重（用于升降级判断）
TIER_WEIGHT: dict[str, int] = {
    "free": 0,
    "standard": 1,
    "enterprise": 2,
}

# 试用配置
TRIAL_DAYS = 14
TRIAL_TIER = "standard"   # 试用自动升级到的套餐


def get_plan(tier: str) -> PlanConfig:
    """按名称获取套餐配置"""
    plan = PLANS.get(tier)
    if not plan:
        raise ValueError(f"不支持的套餐: {tier}")
    return plan


def can_upgrade(current_tier: str, target_tier: str) -> bool:
    """判断是否允许从 current 升级到 target"""
    cur_w = TIER_WEIGHT.get(current_tier, 0)
    tgt_w = TIER_WEIGHT.get(target_tier, 0)
    return tgt_w > cur_w


def can_downgrade(current_tier: str, target_tier: str) -> bool:
    """判断是否允许从 current 降级到 target"""
    cur_w = TIER_WEIGHT.get(current_tier, 0)
    tgt_w = TIER_WEIGHT.get(target_tier, 0)
    return tgt_w < cur_w


# ── 试用服务 ─────────────────────────────────────────────────────────────


async def has_used_trial(user_id: int, db: AsyncSession) -> bool:
    """检查用户是否已使用过免费试用

    查找 TrialRecord 表中该用户的记录。
    如果表不存在则通过 EnterpriseSubscription 的 trial 标记回退检测。
    """
    # 方式1: 检查显式的试用记录表（如果已迁移）
    try:
        from app.models.payment import TrialRecord
        result = await db.execute(
            select(TrialRecord).where(
                TrialRecord.user_id == user_id,
                TrialRecord.status == "used",
            )
        )
        if result.scalar_one_or_none():
            return True
    except (ImportError, Exception):
        pass

    # 方式2: 通过 EnterpriseSubscription 中的 trial_used 标记检测
    try:
        result = await db.execute(
            select(EnterpriseSubscription).where(
                EnterpriseSubscription.user_id == user_id,
                EnterpriseSubscription.features.get("is_trial").as_string() == "true",
            )
        )
        if result.scalar_one_or_none():
            return True
    except Exception:
        pass

    return False


async def start_trial(
    user: User,
    db: AsyncSession,
    company_name: str = "",
) -> EnterpriseSubscription:
    """为用户开通14天试用（标准版），返回创建的订阅记录

    Raises:
        ValueError: 如果用户已使用过试用
    """
    if await has_used_trial(user.id, db):
        raise ValueError("您已使用过免费试用，每个用户仅限一次")

    now = datetime.utcnow()
    end_date = now + timedelta(days=TRIAL_DAYS)

    sub = EnterpriseSubscription(
        user_id=user.id,
        company_name=company_name or f"{user.name}的试用",
        seats=1,
        tier=TRIAL_TIER,
        start_date=now,
        end_date=end_date,
        auto_renew=False,
        status="trial",   # 试用状态
        features={
            "is_trial": True,
            "trial_start": now.isoformat(),
            "trial_end": end_date.isoformat(),
            "trial_days": TRIAL_DAYS,
            "plan_tier": TRIAL_TIER,
            "features": [f.description for f in PLANS[TRIAL_TIER].features],
            "quota": PLANS[TRIAL_TIER].quota_per_month,
        },
    )
    db.add(sub)
    await db.flush()  # 获取 sub.id

    # 创建试用记录
    from app.models.payment import TrialRecord
    trial_record = TrialRecord(
        user_id=user.id,
        subscription_id=sub.id,
        trial_tier=TRIAL_TIER,
        status="active",
        started_at=now,
        expires_at=end_date,
    )
    db.add(trial_record)

    # 更新用户会员信息
    user.membership_tier = TRIAL_TIER
    user.membership_expires_at = end_date
    user.unlock_quota = PLANS[TRIAL_TIER].quota_per_month
    user.quota_reset_at = now + timedelta(days=30)

    await db.commit()
    await db.refresh(sub)
    return sub


async def get_trial_status(
    user: User,
    db: AsyncSession,
) -> dict:
    """查询用户的试用状态"""
    result = await db.execute(
        select(EnterpriseSubscription).where(
            EnterpriseSubscription.user_id == user.id,
            EnterpriseSubscription.status == "trial",
        ).order_by(EnterpriseSubscription.created_at.desc())
    )
    sub = result.scalars().first()

    now = datetime.utcnow()
    if not sub:
        # 检查是否已过期或被转换
        result = await db.execute(
            select(EnterpriseSubscription).where(
                EnterpriseSubscription.user_id == user.id,
                EnterpriseSubscription.status.in_(["active", "cancelled", "expired"]),
            ).order_by(EnterpriseSubscription.created_at.desc())
        )
        expired_sub = result.scalars().first()
        if expired_sub and expired_sub.features.get("is_trial"):
            return {
                "has_used_trial": True,
                "is_active_trial": False,
                "trial_ended_at": expired_sub.end_date.isoformat() if expired_sub.end_date else None,
                "status": expired_sub.status,
                "converted_to": expired_sub.tier,
                "remaining_days": 0,
            }
        return {
            "has_used_trial": await has_used_trial(user.id, db),
            "is_active_trial": False,
            "trial_ended_at": None,
            "status": "none",
            "converted_to": None,
            "remaining_days": 0,
        }

    remaining = (sub.end_date - now).days if sub.end_date > now else 0
    return {
        "has_used_trial": True,
        "is_active_trial": True,
        "trial_start": sub.start_date.isoformat() if sub.start_date else None,
        "trial_end": sub.end_date.isoformat() if sub.end_date else None,
        "status": sub.status,
        "tier": sub.tier,
        "remaining_days": max(0, remaining),
        "features": sub.features,
    }


# ── 升级/降级服务 ────────────────────────────────────────────────────────


async def upgrade_subscription(
    user: User,
    db: AsyncSession,
    target_tier: str,
    company_name: str = "",
    seats: int = 1,
) -> EnterpriseSubscription:
    """升级订阅套餐

    Raises:
        ValueError: 如果 target_tier 无效或不允许升级
    """
    plan = get_plan(target_tier)

    # 查找当前活跃订阅
    result = await db.execute(
        select(EnterpriseSubscription).where(
            EnterpriseSubscription.user_id == user.id,
            EnterpriseSubscription.status.in_(["active", "trial"]),
        ).order_by(EnterpriseSubscription.created_at.desc())
    )
    current_sub = result.scalars().first()

    current_tier = current_sub.tier if current_sub else "free"

    if current_tier == target_tier:
        raise ValueError(f"当前已是 {plan.name_cn}，无需重复升级")

    if not can_upgrade(current_tier, target_tier):
        raise ValueError(
            f"不支持从 {current_tier} 升级到 {target_tier}。"
            f"升级路径: free → standard → enterprise"
        )

    now = datetime.utcnow()
    end_date = now + timedelta(days=30)

    if current_sub and current_sub.status == "trial":
        # 从试用转换：保留原有记录，更新为正式版
        current_sub.tier = target_tier
        current_sub.company_name = company_name or current_sub.company_name
        current_sub.seats = max(seats, current_sub.seats)
        current_sub.start_date = now
        current_sub.end_date = end_date
        current_sub.auto_renew = True
        current_sub.status = "active"
        current_sub.features = {
            "is_trial": False,   # 标记试用已完成
            "trial_converted_at": now.isoformat(),
            "plan_tier": target_tier,
            "features": [f.description for f in plan.features],
            "quota": plan.quota_per_month,
            "auto_renew": True,
        }
        sub = current_sub
    elif current_sub and current_sub.status == "active":
        # 升级现有正式订阅
        current_sub.tier = target_tier
        current_sub.company_name = company_name or current_sub.company_name
        current_sub.seats = max(seats, current_sub.seats)
        current_sub.end_date = end_date
        current_sub.auto_renew = True
        current_sub.features = {
            "is_trial": False,
            "plan_tier": target_tier,
            "features": [f.description for f in plan.features],
            "quota": plan.quota_per_month,
            "upgraded_from": current_tier,
            "upgraded_at": now.isoformat(),
            "auto_renew": True,
        }
        sub = current_sub
    else:
        # 全新订阅（从 free 首次升级）
        sub = EnterpriseSubscription(
            user_id=user.id,
            company_name=company_name or f"{user.name}的订阅",
            seats=seats,
            tier=target_tier,
            start_date=now,
            end_date=end_date,
            auto_renew=True,
            status="active",
            features={
                "is_trial": False,
                "plan_tier": target_tier,
                "features": [f.description for f in plan.features],
                "quota": plan.quota_per_month,
                "auto_renew": True,
            },
        )
        db.add(sub)

    # 更新用户会员信息
    user.membership_tier = target_tier
    user.membership_expires_at = end_date
    user.unlock_quota = plan.quota_per_month
    user.quota_reset_at = now + timedelta(days=30)

    await db.commit()
    await db.refresh(sub)
    return sub


async def downgrade_subscription(
    user: User,
    db: AsyncSession,
    target_tier: str,
) -> EnterpriseSubscription:
    """降级订阅套餐

    Raises:
        ValueError: 如果 target_tier 无效或不允许降级
    """
    plan = get_plan(target_tier)

    result = await db.execute(
        select(EnterpriseSubscription).where(
            EnterpriseSubscription.user_id == user.id,
            EnterpriseSubscription.status == "active",
        ).order_by(EnterpriseSubscription.created_at.desc())
    )
    current_sub = result.scalars().first()

    if not current_sub:
        raise ValueError("没有活跃的订阅可降级")

    current_tier = current_sub.tier

    if current_tier == target_tier:
        raise ValueError(f"当前已是 {plan.name_cn}")

    if not can_downgrade(current_tier, target_tier):
        raise ValueError(
            f"不支持从 {current_tier} 降级到 {target_tier}"
        )

    now = datetime.utcnow()

    # 降级在当前周期结束时生效（保持当前服务到周期结束）
    current_sub.features = {
        **current_sub.features,
        "downgrade_to": target_tier,
        "downgrade_effective_at": current_sub.end_date.isoformat() if current_sub.end_date else None,
        "downgrade_requested_at": now.isoformat(),
    }

    if target_tier == "free":
        # 降级到免费：当前周期结束后取消订阅
        current_sub.auto_renew = False
        # 标记为降级待处理
        current_sub.status = "active"   # 保持活跃直到周期结束
        await db.commit()
        await db.refresh(current_sub)
        return current_sub

    # 降级到另一个付费套餐
    current_sub.tier = target_tier
    current_sub.end_date = current_sub.end_date  # 保持原到期时间
    current_sub.features = {
        "is_trial": False,
        "plan_tier": target_tier,
        "features": [f.description for f in plan.features],
        "quota": plan.quota_per_month,
        "downgraded_from": current_tier,
        "downgraded_at": now.isoformat(),
        "auto_renew": current_sub.auto_renew,
    }

    # 更新用户会员信息
    user.membership_tier = target_tier
    user.unlock_quota = plan.quota_per_month

    await db.commit()
    await db.refresh(current_sub)
    return current_sub


async def get_current_subscription(
    user: User,
    db: AsyncSession,
) -> Optional[EnterpriseSubscription]:
    """获取用户当前活跃订阅"""
    result = await db.execute(
        select(EnterpriseSubscription).where(
            EnterpriseSubscription.user_id == user.id,
            EnterpriseSubscription.status.in_(["active", "trial"]),
        ).order_by(EnterpriseSubscription.created_at.desc())
    )
    return result.scalars().first()
