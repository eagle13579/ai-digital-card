"""
付款转化分析服务 — trial / MRR / churn / LTV 指标
==================================================

提供从数据库实时聚合的付款相关业务指标，供运营仪表盘和 API 使用。

指标定义:
  - trial_start:       试用启动数（总 / 近30天）
  - trial_conversion:  试用→付费转化率 (%)
  - mrr:               月度经常性收入 (Monthly Recurring Revenue)
  - churn_rate:        月度客户流失率 (%)
  - ltv:               客户生命周期价值 (Lifetime Value，平均)

依赖:
  - app.models.payment.PaymentOrder
  - app.models.payment.EnterpriseSubscription
  - app.models.payment.TrialRecord
  - app.services.subscription_service.PLANS
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import PaymentOrder, EnterpriseSubscription, TrialRecord
from app.services.subscription_service import PLANS

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 分析服务
# ═══════════════════════════════════════════════════════════════


class PaymentAnalyticsService:
    """付款转化分析服务

    所有方法均为 async，使用异步数据库会话查询。
    get_overview() 一次性返回所有指标。
    """

    async def get_overview(self, db: AsyncSession) -> dict[str, Any]:
        """获取付款指标总览

        Returns:
            dict 包含:
              - trial:     试用统计数据
              - mrr:       月度经常性收入
              - churn_rate: 客户流失率
              - ltv:       客户生命周期价值
              - paid_users:付费用户分布
        """
        trial_stats = await self._get_trial_stats(db)
        mrr = await self._calc_mrr(db)
        churn = await self._calc_churn_rate(db)
        ltv = await self._calc_ltv(db)
        paid_stats = await self._get_paid_stats(db)

        return {
            "trial": trial_stats,
            "mrr": mrr,
            "churn_rate": churn,
            "ltv": ltv,
            "paid_users": paid_stats,
            "calculated_at": datetime.utcnow().isoformat(),
        }

    # ── 试用统计 ────────────────────────────────────────────

    async def _get_trial_stats(self, db: AsyncSession) -> dict[str, Any]:
        """试用启动与转化统计"""
        # 总试用数
        result = await db.execute(select(func.count(TrialRecord.id)))
        total_trials = result.scalar() or 0

        # 活跃试用
        result = await db.execute(
            select(func.count(TrialRecord.id)).where(
                TrialRecord.status == "active",
            )
        )
        active_trials = result.scalar() or 0

        # 已转化 (converted_at 非空)
        result = await db.execute(
            select(func.count(TrialRecord.id)).where(
                TrialRecord.converted_at.isnot(None),
            )
        )
        converted = result.scalar() or 0

        # 已过期
        result = await db.execute(
            select(func.count(TrialRecord.id)).where(
                TrialRecord.status == "expired",
            )
        )
        expired = result.scalar() or 0

        conversion_rate = round(converted / total_trials * 100, 2) if total_trials > 0 else 0.0

        # 近30天试用
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        result = await db.execute(
            select(func.count(TrialRecord.id)).where(
                TrialRecord.started_at >= thirty_days_ago,
            )
        )
        recent_trials = result.scalar() or 0

        return {
            "total_trials": total_trials,
            "active_trials": active_trials,
            "converted": converted,
            "expired": expired,
            "conversion_rate_pct": conversion_rate,
            "recent_30d_trials": recent_trials,
        }

    # ── MRR ─────────────────────────────────────────────────

    async def _calc_mrr(self, db: AsyncSession) -> dict[str, Any]:
        """计算月度经常性收入 (MRR)"""
        result = await db.execute(
            select(EnterpriseSubscription).where(
                EnterpriseSubscription.status == "active",
                EnterpriseSubscription.tier.in_(["standard", "enterprise"]),
            )
        )
        active_subs = result.scalars().all()

        total_mrr_cents = 0
        tier_breakdown: dict[str, dict[str, int]] = {}

        for sub in active_subs:
            plan = PLANS.get(sub.tier)
            if plan is None:
                continue
            total_mrr_cents += plan.price_cents
            if sub.tier not in tier_breakdown:
                tier_breakdown[sub.tier] = {"count": 0, "mrr_cents": 0}
            tier_breakdown[sub.tier]["count"] += 1
            tier_breakdown[sub.tier]["mrr_cents"] += plan.price_cents

        return {
            "total_mrr_cents": total_mrr_cents,
            "total_mrr_yuan": round(total_mrr_cents / 100, 2),
            "active_subscriptions": len(active_subs),
            "tier_breakdown": tier_breakdown,
        }

    # ── 流失率 ──────────────────────────────────────────────

    async def _calc_churn_rate(self, db: AsyncSession) -> dict[str, Any]:
        """计算30天客户流失率

        churn_rate = 流失用户数 / 期初活跃用户数
        流失 = 过期未续费 + 主动取消
        """
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        now = datetime.utcnow()

        # 期初（30天前）活跃的用户
        result = await db.execute(
            select(func.count(EnterpriseSubscription.id)).where(
                EnterpriseSubscription.status.in_(["active", "trial"]),
                EnterpriseSubscription.start_date <= thirty_days_ago,
            )
        )
        active_before = result.scalar() or 1

        # 30天内到期的订阅
        result = await db.execute(
            select(func.count(EnterpriseSubscription.id)).where(
                EnterpriseSubscription.end_date.between(thirty_days_ago, now),
                EnterpriseSubscription.status.in_(["active", "trial"]),
            )
        )
        expiring = result.scalar() or 0

        # 已过期标记
        result = await db.execute(
            select(func.count(EnterpriseSubscription.id)).where(
                EnterpriseSubscription.end_date.between(thirty_days_ago, now),
                EnterpriseSubscription.status == "expired",
            )
        )
        expired = result.scalar() or 0

        # 主动取消
        result = await db.execute(
            select(func.count(EnterpriseSubscription.id)).where(
                EnterpriseSubscription.status == "cancelled",
                EnterpriseSubscription.updated_at >= thirty_days_ago,
            )
        )
        cancelled = result.scalar() or 0

        total_churned = expired + cancelled
        churn_rate_pct = round(total_churned / active_before * 100, 2)

        return {
            "churn_rate_30d_pct": churn_rate_pct,
            "churned_30d": total_churned,
            "expired_30d": expired,
            "cancelled_30d": cancelled,
            "expiring_30d": expiring,
            "active_before_30d": active_before,
        }

    # ── LTV ─────────────────────────────────────────────────

    async def _calc_ltv(self, db: AsyncSession) -> dict[str, Any]:
        """计算客户生命周期价值 (LTV)

        LTV = 总付费收入 / 唯一付费用户数
        """
        # 总付费订单数和收入
        result = await db.execute(
            select(
                func.count(PaymentOrder.id),
                func.sum(PaymentOrder.total_cents),
            ).where(PaymentOrder.status == "paid")
        )
        row = result.one()
        paid_count = row[0] or 0
        total_revenue_cents = row[1] or 0

        # 去重付费用户数
        result = await db.execute(
            select(func.count(func.distinct(PaymentOrder.user_id))).where(
                PaymentOrder.status == "paid",
            )
        )
        unique_payers = result.scalar() or 1

        avg_ltv_cents = total_revenue_cents // unique_payers

        return {
            "total_paid_orders": paid_count,
            "total_revenue_cents": total_revenue_cents,
            "total_revenue_yuan": round(total_revenue_cents / 100, 2),
            "unique_payers": unique_payers,
            "avg_ltv_cents": avg_ltv_cents,
            "avg_ltv_yuan": round(avg_ltv_cents / 100, 2),
        }

    # ── 付费用户概览 ────────────────────────────────────────

    async def _get_paid_stats(self, db: AsyncSession) -> dict[str, Any]:
        """获取付费用户套餐分布"""
        result = await db.execute(
            select(
                EnterpriseSubscription.tier,
                func.count(EnterpriseSubscription.id),
            ).where(
                EnterpriseSubscription.status == "active",
            ).group_by(EnterpriseSubscription.tier)
        )
        tier_distribution: dict[str, int] = {row[0]: row[1] for row in result.all()}

        total_paid = sum(
            tier_distribution.get(t, 0)
            for t in ["standard", "enterprise"]
        )

        return {
            "tier_distribution": tier_distribution,
            "total_paid": total_paid,
        }


# ── 全局单例 ────────────────────────────────────────────────

analytics_service = PaymentAnalyticsService()


async def get_payment_overview(db: AsyncSession) -> dict[str, Any]:
    """获取付款指标总览（便捷函数）"""
    return await analytics_service.get_overview(db)
