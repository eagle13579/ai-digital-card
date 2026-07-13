"""自助取消/退款服务 — 支持周期末取消和立即取消+按比例退款。

功能:
  - cancel_at_period_end: 取消订阅（当前周期结束后不再续费，服务可用至周期结束）
  - cancel_immediate: 立即取消 + 按比例计算退款金额
  - 取消原因枚举（提供下拉选项）
  - 退款策略：按已使用天数 / 总天数比例计算，向下取整到分
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import EnterpriseSubscription
from app.models.user import User
from app.services.subscription_service import TRIAL_DAYS, get_plan

logger = logging.getLogger(__name__)


# ── 取消原因枚举 ──────────────────────────────────────────────────────────


class CancelReason(str, Enum):
    """取消订阅的原因列表（前端下拉选择）"""

    TOO_EXPENSIVE = "too_expensive"
    """价格太高"""
    NOT_USING = "not_using"
    """使用频率低 / 不常用"""
    MISSING_FEATURES = "missing_features"
    """缺少需要的功能"""
    SWITCHING_ALTERNATIVE = "switching_alternative"
    """切换到其他替代产品"""
    TEMPORARY_PAUSE = "temporary_pause"
    """暂时不需要，后续再续费"""
    QUALITY_ISSUES = "quality_issues"
    """产品质量问题"""
    BUGS_OR_ERRORS = "bugs_or_errors"
    """遇到错误或 Bug"""
    CUSTOMER_SERVICE = "customer_service"
    """客服体验不佳"""
    OTHER = "other"
    """其他原因"""


CANCEL_REASON_LABELS: dict[CancelReason, str] = {
    CancelReason.TOO_EXPENSIVE: "价格太高",
    CancelReason.NOT_USING: "使用频率低 / 不常用",
    CancelReason.MISSING_FEATURES: "缺少需要的功能",
    CancelReason.SWITCHING_ALTERNATIVE: "切换到其他替代产品",
    CancelReason.TEMPORARY_PAUSE: "暂时不需要，后续再续费",
    CancelReason.QUALITY_ISSUES: "产品质量问题",
    CancelReason.BUGS_OR_ERRORS: "遇到错误或 Bug",
    CancelReason.CUSTOMER_SERVICE: "客服体验不佳",
    CancelReason.OTHER: "其他原因",
}


# ── 退款计算 ──────────────────────────────────────────────────────────────


def calculate_prorated_refund(
    total_cents: int,
    start_date: datetime,
    end_date: datetime,
    cancel_date: datetime | None = None,
) -> dict:
    """按比例计算退款金额。

    公式：
      已用天数 = max(1, (cancel_date - start_date).days)
      总天数   = max(1, (end_date - start_date).days)
      退款比例 = 1 - (已用天数 / 总天数)
      退款金额 = floor(total_cents * 退款比例)  # 向下取整到分

    注意：
      - 试用订阅退款金额为 0（未付费）
      - 退款比例向下取整，最小为 0
      - 如果 cancel_date < start_date 或 cancel_date >= end_date，返回 0

    Args:
        total_cents: 订单总金额（分）
        start_date: 订阅开始时间
        end_date: 订阅到期时间
        cancel_date: 取消时间（默认当前时间）

    Returns:
        {
            "refund_cents": int,       # 退款金额（分）
            "used_days": int,          # 已使用天数
            "total_days": int,         # 订阅总天数
            "refund_ratio": float,     # 退款比例
            "message": str,            # 退款说明
        }
    """
    cancel = cancel_date or datetime.utcnow()

    total_days = max(1, (end_date - start_date).days)
    used_days = max(1, (cancel - start_date).days)

    if cancel <= start_date or cancel >= end_date:
        return {
            "refund_cents": 0,
            "used_days": used_days,
            "total_days": total_days,
            "refund_ratio": 0.0,
            "message": "取消时间在订阅期之外，不产生退款",
        }

    used_ratio = used_days / total_days
    refund_ratio = max(0.0, 1.0 - used_ratio)
    refund_cents = int(total_cents * refund_ratio)  # 向下取整到分

    return {
        "refund_cents": refund_cents,
        "used_days": used_days,
        "total_days": total_days,
        "refund_ratio": round(refund_ratio, 4),
        "message": f"按比例退款 {refund_cents / 100:.2f} 元（已用 {used_days}/{total_days} 天）",
    }


async def _get_active_subscription(
    user: User,
    db: AsyncSession,
) -> EnterpriseSubscription:
    """获取用户的活跃订阅（active 或 trial），不存在则抛 ValueError"""
    result = await db.execute(
        select(EnterpriseSubscription).where(
            EnterpriseSubscription.user_id == user.id,
            EnterpriseSubscription.status.in_(["active", "trial"]),
        ).order_by(EnterpriseSubscription.created_at.desc())
    )
    sub = result.scalars().first()
    if not sub:
        raise ValueError("没有活跃的订阅可取消")
    return sub


# ── 取消服务 ──────────────────────────────────────────────────────────────


async def cancel_at_period_end(
    user: User,
    db: AsyncSession,
    reason: str = "",
    reason_detail: str = "",
) -> EnterpriseSubscription:
    """取消订阅 —— 当前周期结束后停止续费，服务可用至结束日期。

    操作：
      - auto_renew = False
      - status 保持 active（直到周期结束）
      - features 中记录取消原因和取消时间

    Raises:
        ValueError: 没有活跃订阅
    """
    sub = await _get_active_subscription(user, db)

    now = datetime.utcnow()

    # 记录取消信息
    features = sub.features or {}
    features["cancelled_at"] = now.isoformat()
    features["cancel_type"] = "period_end"
    features["cancel_reason"] = reason
    features["cancel_reason_detail"] = reason_detail
    features["effective_end_date"] = sub.end_date.isoformat() if sub.end_date else None

    sub.auto_renew = False
    sub.features = features
    # 如果当前是 trial，取消后标记为 expired 更合适
    if sub.status == "trial":
        sub.status = "expired"
    # 如果是 active，保持 active 直到周期结束

    await db.commit()
    await db.refresh(sub)

    logger.info(
        "订阅已标记为周期末取消: user_id=%s, sub_id=%s, tier=%s, "
        "service_until=%s, reason=%s",
        user.id, sub.id, sub.tier, sub.end_date, reason,
    )

    return sub


async def cancel_immediate(
    user: User,
    db: AsyncSession,
    reason: str = "",
    reason_detail: str = "",
) -> dict:
    """立即取消订阅 + 按比例退款。

    操作：
      - 计算按比例退款金额
      - status = "cancelled"
      - features 中记录取消原因、取消时间、退款信息
      - 用户权限立即降级为 free

    Returns:
        {
            "subscription": EnterpriseSubscription,
            "refund": dict,   # 退款详情
        }

    Raises:
        ValueError: 没有活跃订阅
    """
    sub = await _get_active_subscription(user, db)

    now = datetime.utcnow()
    plan = get_plan(sub.tier)

    # ── 退款计算 ──────────────────────────────────────────────────────
    is_trial = sub.status == "trial" or (sub.features or {}).get("is_trial", False)

    if is_trial:
        # 试用订阅无实际付款，退款为 0
        refund_info = {
            "refund_cents": 0,
            "used_days": max(1, (now - sub.start_date).days) if sub.start_date else 1,
            "total_days": TRIAL_DAYS,
            "refund_ratio": 0.0,
            "message": "试用订阅不产生退款",
        }
    else:
        refund_info = calculate_prorated_refund(
            total_cents=plan.price_cents,
            start_date=sub.start_date,
            end_date=sub.end_date,
            cancel_date=now,
        )

    # ── 更新订阅 ──────────────────────────────────────────────────────
    features = sub.features or {}
    features["cancelled_at"] = now.isoformat()
    features["cancel_type"] = "immediate"
    features["cancel_reason"] = reason
    features["cancel_reason_detail"] = reason_detail
    features["refund_info"] = {
        "refund_cents": refund_info["refund_cents"],
        "used_days": refund_info["used_days"],
        "total_days": refund_info["total_days"],
        "refund_ratio": refund_info["refund_ratio"],
        "message": refund_info["message"],
    }

    sub.status = "cancelled"
    sub.auto_renew = False
    sub.features = features
    sub.end_date = now  # 立即终止

    # ── 降级用户权限 ───────────────────────────────────────────────────
    free_plan = get_plan("free")
    user.membership_tier = "free"
    user.membership_expires_at = now
    user.unlock_quota = free_plan.quota_per_month

    await db.commit()
    await db.refresh(sub)

    logger.info(
        "订阅已立即取消: user_id=%s, sub_id=%s, tier=%s, "
        "refund_cents=%s, reason=%s",
        user.id, sub.id, sub.tier,
        refund_info["refund_cents"], reason,
    )

    return {
        "subscription": sub,
        "refund": refund_info,
    }
