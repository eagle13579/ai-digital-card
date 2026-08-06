"""定价/订阅服务 — 三档套餐 + 年付折扣 + 订阅关系基础逻辑。

函数全部基于 SQLAlchemy async session 操作，与 app/models/subscription.py 配套。
注意: 本模块不依赖 payment.py / subscription_service.py，仅新增扩展。
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Plan, Subscription

# ── 定价参数 ─────────────────────────────────────────────────────────────

# 年付折扣: 年付 = 月付 × 12 × 0.8 (8折)
ANNUAL_DISCOUNT_RATIO = 0.8

# 订阅周期天数 (基础逻辑: 月付30天 / 年付365天)
CYCLE_DAYS = {"month": 30, "year": 365}

# 免费套餐专属周期（免费版默认按 30 天续期）
FREE_CYCLE_DAYS = 30

# ── 内置三档套餐（DB 未种子化时的兜底数据，与 ensure_default_plans 保持一致）──

_DEFAULT_FEATURES = {
    "free": [
        {"name": "AI电子名片", "description": "创建并分享个人电子名片", "enabled": True},
        {"name": "基础匹配", "description": "每日有限次匹配推荐", "enabled": True},
        {"name": "访客记录", "description": "最近30天访客记录", "enabled": True},
    ],
    "pro": [
        {"name": "AI电子名片", "description": "创建并分享个人电子名片", "enabled": True},
        {"name": "高级匹配", "description": "每日100次匹配推荐", "enabled": True},
        {"name": "访客记录", "description": "全部访客记录(90天)", "enabled": True},
        {"name": "数据分析", "description": "名片浏览/转化数据洞察", "enabled": True},
        {"name": "去水印", "description": "名片与页面无水印", "enabled": True},
        {"name": "专属客服", "description": "优先在线客服支持", "enabled": True},
    ],
    "enterprise": [
        {"name": "Pro全部权益", "description": "包含Pro版全部功能", "enabled": True},
        {"name": "无限匹配", "description": "匹配推荐无次数限制", "enabled": True},
        {"name": "团队管理", "description": "多成员团队协作", "enabled": True},
        {"name": "CRM集成", "description": "Salesforce/企业微信等集成", "enabled": True},
        {"name": "定制域名", "description": "专属域名与品牌化页面", "enabled": True},
        {"name": "专属客户成功", "description": "1对1客户成功经理", "enabled": True},
    ],
}

# 月付定价 (元): free=0 / pro=199 / enterprise=999 (来自 docs/产品矩阵/AI数字名片_定价提价方案_完整分析.md 价值阶梯L2/L3)
_DEFAULT_PRICES = {"free": 0.0, "pro": 199.0, "enterprise": 999.0}

DEFAULT_PLANS: list[dict] = [
    {
        "name": "免费版",
        "tier": "free",
        "price_monthly": 0.0,
        "price_annual": 0.0,
        "is_active": True,
        "is_decoy": False,
        "features": _DEFAULT_FEATURES["free"],
    },
    {
        "name": "Pro版",
        "tier": "pro",
        "price_monthly": 199.0,
        "price_annual": round(199.0 * 12 * ANNUAL_DISCOUNT_RATIO, 2),  # 1910.4 (年付8折)
        "is_active": True,
        "is_decoy": False,
        "features": _DEFAULT_FEATURES["pro"],
    },
    {
        "name": "企业版",
        "tier": "enterprise",
        "price_monthly": 999.0,
        "price_annual": round(999.0 * 12 * ANNUAL_DISCOUNT_RATIO, 2),  # 9590.4
        "is_active": True,
        "is_decoy": True,  # 企业版作为"诱饵"锚定 Pro 版性价比
        "features": _DEFAULT_FEATURES["enterprise"],
    },
]


# ── 工具函数 ─────────────────────────────────────────────────────────────


def annual_discount(plan: Plan | dict) -> float:
    """计算年付折扣比例 (0~1)，如 0.2 表示年付打8折。

    规则: 折扣 = 1 - 年付价 / (月付价 × 12)；免费套餐或月付为0时返回 0。
    """
    monthly = plan.price_monthly if isinstance(plan, Plan) else plan["price_monthly"]
    annual = plan.price_annual if isinstance(plan, Plan) else plan["price_annual"]
    if not monthly:
        return 0.0
    original = round(monthly * 12, 2)
    if original <= 0:
        return 0.0
    return round(1 - annual / original, 2)


def plan_to_dict(plan: Plan) -> dict:
    """Plan ORM → dict（含年付折扣与划线价，便于路由直接返回）"""
    monthly = plan.price_monthly or 0.0
    annual = plan.price_annual or 0.0
    original_annual = round(monthly * 12, 2)
    return {
        "id": plan.id,
        "tier": plan.tier,
        "name": plan.name,
        "price_monthly": monthly,
        "price_annual": annual,
        "original_annual": original_annual,      # 划线价(年付原价)
        "annual_discount": annual_discount(plan),  # 年付折扣比例
        "is_decoy": plan.is_decoy,
        "is_active": plan.is_active,
        "features": plan.features or [],
    }


# ── 核心服务函数 ─────────────────────────────────────────────────────────


async def get_plans(db: AsyncSession, include_inactive: bool = False) -> list[Plan]:
    """获取套餐列表（默认仅上架套餐）。

    若 plans 表为空，自动执行幂等种子化并返回内置三档。
    """
    stmt = select(Plan).order_by(Plan.price_monthly.asc())
    if not include_inactive:
        stmt = stmt.where(Plan.is_active.is_(True))
    rows = list((await db.execute(stmt)).scalars().all())

    if not rows:
        await ensure_default_plans(db)
        rows = list((await db.execute(stmt)).scalars().all())
    return rows


async def ensure_default_plans(db: AsyncSession) -> None:
    """幂等写入内置三档套餐（不覆盖已有记录）。"""
    existing = set((await db.execute(select(Plan.tier))).scalars().all())
    for item in DEFAULT_PLANS:
        if item["tier"] in existing:
            continue
        db.add(Plan(**item))
    await db.commit()


async def get_plan_by_tier(db: AsyncSession, tier: str) -> Plan | None:
    """按套餐标识查询套餐"""
    return (
        await db.execute(select(Plan).where(Plan.tier == tier))
    ).scalar_one_or_none()


async def get_plan_by_id(db: AsyncSession, plan_id: int) -> Plan | None:
    """按 ID 查询套餐"""
    return (
        await db.execute(select(Plan).where(Plan.id == plan_id))
    ).scalar_one_or_none()


async def get_user_plan(
    db: AsyncSession, user_id: int
) -> tuple[Subscription | None, Plan | None]:
    """查询用户当前订阅关系及其套餐。

    返回 (subscription, plan)；无订阅记录时返回 (None, 免费套餐兜底)。
    """
    sub = (
        await db.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if sub is not None:
        # 到期自动标记 expired（基础状态机）
        if sub.status == "active" and sub.end_date and sub.end_date < datetime.utcnow():
            sub.status = "expired"
            await db.commit()
        plan = await get_plan_by_id(db, sub.plan_id)
        return sub, plan

    # 无订阅 → 免费套餐兜底
    free_plan = await get_plan_by_tier(db, "free")
    return None, free_plan


async def subscribe(
    db: AsyncSession,
    user_id: int,
    plan_id: int,
    billing_cycle: str = "month",
) -> tuple[Subscription, Plan]:
    """用户订阅套餐（基础逻辑）。

    - 校验套餐存在且上架
    - 将用户旧订阅置为 cancelled
    - 创建新订阅: status=active, start=now, end=now+周期
    - 免费套餐固定 30 天周期
    """
    plan = await get_plan_by_id(db, plan_id)
    if plan is None or not plan.is_active:
        raise ValueError(f"套餐不存在或未上架: plan_id={plan_id}")

    cycle = billing_cycle.lower() if billing_cycle in ("month", "year") else "month"
    days = CYCLE_DAYS[cycle]
    if plan.price_monthly == 0:
        days = FREE_CYCLE_DAYS

    now = datetime.utcnow()

    # 旧订阅置为 cancelled
    await db.execute(
        update(Subscription)
        .where(Subscription.user_id == user_id, Subscription.status == "active")
        .values(status="cancelled", updated_at=now)
    )

    sub = Subscription(
        user_id=user_id,
        plan_id=plan.id,
        status="active",
        start_date=now,
        end_date=now + timedelta(days=days),
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub, plan
