"""CRM 报表/分析服务。

功能:
  1. get_pipeline_summary()  — 每阶段机会数+金额+赢单率
  2. get_team_performance()  — 每人联系人数+机会数+成交率
  3. get_conversion_rate()   — 各阶段转化率
  4. get_activity_trend()    — 每日活动量趋势
  5. get_contact_growth()    — 联系人数增长曲线
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crm.crm_models import (
    CrmActivity,
    CrmContact,
    CrmDeal,
)

logger = logging.getLogger(__name__)


class CrmAnalyticsService:
    """CRM 分析/报表业务逻辑。"""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id

    # ── Pipeline 摘要 ──────────────────────────────────────────────────────────────

    async def get_pipeline_summary(self) -> list[dict]:
        """每阶段机会数+金额+赢单率。"""
        # 先确保阶段存在（让用户有默认阶段）
        from app.crm.crm_service import CrmService
        svc = CrmService(self.db, self.user_id)
        stages = await svc.ensure_default_stages()

        # 按管道阶段统计 deals（open + won）
        deals_query = (
            select(
                CrmDeal.pipeline_stage_id,
                func.count(CrmDeal.id).label("deal_count"),
                func.coalesce(func.sum(CrmDeal.value), 0).label("total_value"),
                func.avg(CrmDeal.probability).label("avg_probability"),
            )
            .where(CrmDeal.owner_id == self.user_id)
            .group_by(CrmDeal.pipeline_stage_id)
        )
        result = await self.db.execute(deals_query)
        deal_stats = {
            row.pipeline_stage_id: {
                "deal_count": row.deal_count,
                "total_value": float(row.total_value),
                "avg_probability": round(float(row.avg_probability or 0), 1),
            }
            for row in result.all()
        }

        # 按管道阶段统计 won deals
        won_query = (
            select(
                CrmDeal.pipeline_stage_id,
                func.count(CrmDeal.id).label("won_count"),
            )
            .where(
                CrmDeal.owner_id == self.user_id,
                CrmDeal.status == "won",
            )
            .group_by(CrmDeal.pipeline_stage_id)
        )
        result = await self.db.execute(won_query)
        won_stats = {row.pipeline_stage_id: row.won_count for row in result.all()}

        # 按管道阶段统计 contacts 数量
        contact_query = (
            select(
                CrmContact.pipeline_stage_id,
                func.count(CrmContact.id).label("contact_count"),
            )
            .where(CrmContact.owner_id == self.user_id)
            .group_by(CrmContact.pipeline_stage_id)
        )
        result = await self.db.execute(contact_query)
        contact_stats = {
            row.pipeline_stage_id: row.contact_count for row in result.all()
        }

        # 计算总赢单数（所有 won deals）
        total_won = sum(won_stats.values()) or 1  # 避免除零

        summary = []
        for stage in stages:
            ds = deal_stats.get(stage.id, {})
            wc = won_stats.get(stage.id, 0)
            summary.append({
                "stage_id": stage.id,
                "stage_name": stage.name,
                "sort_order": stage.sort_order,
                "color": stage.color,
                "is_closed": stage.is_closed,
                "win_probability": stage.win_probability,
                "contact_count": contact_stats.get(stage.id, 0),
                "deal_count": ds.get("deal_count", 0),
                "total_value": ds.get("total_value", 0.0),
                "avg_probability": ds.get("avg_probability", 0.0),
                "won_count": wc,
                "won_rate": round(wc / total_won * 100, 1) if total_won else 0.0,
            })

        return summary

    # ── 团队绩效 ──────────────────────────────────────────────────────────────────

    async def get_team_performance(self) -> list[dict]:
        """每人联系人数+机会数+成交率。"""
        # 由于每个用户 owner_id 就是自己，这里统计自己即可
        # 如果有 team 功能可以扩展为按 team_id 查询所有成员
        from app.models.user import User

        # 获取当前用户信息
        user_result = await self.db.execute(
            select(User).where(User.id == self.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return []

        # 联系人总数
        contact_result = await self.db.execute(
            select(func.count(CrmContact.id))
            .where(CrmContact.owner_id == self.user_id)
        )
        total_contacts = contact_result.scalar() or 0

        # 机会总数
        deal_result = await self.db.execute(
            select(func.count(CrmDeal.id))
            .where(CrmDeal.owner_id == self.user_id)
        )
        total_deals = deal_result.scalar() or 0

        # 成交数
        won_result = await self.db.execute(
            select(func.count(CrmDeal.id))
            .where(
                CrmDeal.owner_id == self.user_id,
                CrmDeal.status == "won",
            )
        )
        won_deals = won_result.scalar() or 0

        # 丢失数
        lost_result = await self.db.execute(
            select(func.count(CrmDeal.id))
            .where(
                CrmDeal.owner_id == self.user_id,
                CrmDeal.status == "lost",
            )
        )
        lost_deals = lost_result.scalar() or 0

        # 所有机会金额总和
        value_result = await self.db.execute(
            select(func.coalesce(func.sum(CrmDeal.value), 0))
            .where(CrmDeal.owner_id == self.user_id)
        )
        total_value = float(value_result.scalar() or 0)

        # 成交金额
        won_value_result = await self.db.execute(
            select(func.coalesce(func.sum(CrmDeal.value), 0))
            .where(
                CrmDeal.owner_id == self.user_id,
                CrmDeal.status == "won",
            )
        )
        won_value = float(won_value_result.scalar() or 0)

        close_rate = round(won_deals / total_deals * 100, 1) if total_deals else 0.0

        return [{
            "user_id": self.user_id,
            "name": user.name or f"用户{self.user_id}",
            "contact_count": total_contacts,
            "deal_count": total_deals,
            "won_deals": won_deals,
            "lost_deals": lost_deals,
            "total_value": total_value,
            "won_value": won_value,
            "close_rate": close_rate,
        }]

    # ── 阶段转化率 ────────────────────────────────────────────────────────────────

    async def get_conversion_rate(self) -> dict:
        """各阶段转化率（基于联系人 pipeline 分布和 deal 流转）。"""
        from app.crm.crm_service import CrmService
        svc = CrmService(self.db, self.user_id)
        stages = await svc.ensure_default_stages()

        # 获取每个阶段的联系人数量
        contact_query = (
            select(
                CrmContact.pipeline_stage_id,
                func.count(CrmContact.id).label("count"),
            )
            .where(CrmContact.owner_id == self.user_id)
            .group_by(CrmContact.pipeline_stage_id)
        )
        result = await self.db.execute(contact_query)
        stage_contacts = {
            row.pipeline_stage_id: row.count for row in result.all()
        }

        # 获取每个阶段的机会数量
        deal_query = (
            select(
                CrmDeal.pipeline_stage_id,
                func.count(CrmDeal.id).label("count"),
            )
            .where(CrmDeal.owner_id == self.user_id)
            .group_by(CrmDeal.pipeline_stage_id)
        )
        result = await self.db.execute(deal_query)
        stage_deals = {
            row.pipeline_stage_id: row.count for row in result.all()
        }

        # 获取 final won 和 final lost 数量
        won_result = await self.db.execute(
            select(func.count(CrmDeal.id))
            .where(
                CrmDeal.owner_id == self.user_id,
                CrmDeal.status == "won",
            )
        )
        total_won = won_result.scalar() or 0

        lost_result = await self.db.execute(
            select(func.count(CrmDeal.id))
            .where(
                CrmDeal.owner_id == self.user_id,
                CrmDeal.status == "lost",
            )
        )
        total_lost = lost_result.scalar() or 0

        # 构建阶段转化漏斗
        stages_data = []
        total_contacts = sum(stage_contacts.values()) or 1

        for stage in stages:
            sc = stage_contacts.get(stage.id, 0)
            sd = stage_deals.get(stage.id, 0)

            # 转化率 = 当前阶段 / 第一个阶段的联系人数量 * 100
            conversion_rate = round(sc / total_contacts * 100, 1) if total_contacts else 0.0

            stages_data.append({
                "stage_id": stage.id,
                "stage_name": stage.name,
                "sort_order": stage.sort_order,
                "is_closed": stage.is_closed,
                "contact_count": sc,
                "deal_count": sd,
                "conversion_rate": conversion_rate,
            })

        # 整体转化指标
        # 从"非成交/非丢失阶段"到"成交"的整体转化
        open_stage_ids = [s.id for s in stages if not s.is_closed]
        open_contacts = sum(
            stage_contacts.get(sid, 0) for sid in open_stage_ids
        )
        overall_conversion = round(
            total_won / (open_contacts + total_won) * 100, 1
        ) if (open_contacts + total_won) else 0.0

        return {
            "stages": stages_data,
            "total_contacts": sum(stage_contacts.values()),
            "total_deals": sum(stage_deals.values()),
            "total_won": total_won,
            "total_lost": total_lost,
            "overall_conversion_rate": overall_conversion,
        }

    # ── 活动量趋势 ─────────────────────────────────────────────────────────────────

    async def get_activity_trend(self, days: int = 30) -> list[dict]:
        """每日活动量趋势。返回最近 N 天每天的活动计数。"""
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                func.date(CrmActivity.activity_date).label("date"),
                func.count(CrmActivity.id).label("count"),
            )
            .where(
                CrmActivity.owner_id == self.user_id,
                CrmActivity.activity_date >= since,
            )
            .group_by(func.date(CrmActivity.activity_date))
            .order_by(func.date(CrmActivity.activity_date))
        )
        result = await self.db.execute(query)
        rows = result.all()

        # 构建完整的日期序列（填充零值）
        date_map = {str(row.date): row.count for row in rows}

        trend = []
        for i in range(days - 1, -1, -1):
            d = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            trend.append({
                "date": d,
                "count": date_map.get(d, 0),
            })

        return trend

    # ── 联系人增长曲线 ─────────────────────────────────────────────────────────────

    async def get_contact_growth(self, days: int = 30) -> list[dict]:
        """联系人数增长曲线。返回最近 N 天每天的累计联系人数量。"""
        since = datetime.utcnow() - timedelta(days=days)

        # 获取每天的增量
        query = (
            select(
                func.date(CrmContact.created_at).label("date"),
                func.count(CrmContact.id).label("increment"),
            )
            .where(
                CrmContact.owner_id == self.user_id,
                CrmContact.created_at >= since,
            )
            .group_by(func.date(CrmContact.created_at))
            .order_by(func.date(CrmContact.created_at))
        )
        result = await self.db.execute(query)
        rows = result.all()

        # 获取起始日之前的累计数
        before_result = await self.db.execute(
            select(func.count(CrmContact.id))
            .where(
                CrmContact.owner_id == self.user_id,
                CrmContact.created_at < since,
            )
        )
        base_count = before_result.scalar() or 0

        # 构建填充序列
        inc_map = {str(row.date): row.increment for row in rows}
        cumulative = base_count

        growth = []
        for i in range(days - 1, -1, -1):
            d = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            cumulative += inc_map.get(d, 0)
            growth.append({
                "date": d,
                "cumulative_count": cumulative,
                "daily_increment": inc_map.get(d, 0),
            })

        return growth

    # ── Dashboard 汇总 ─────────────────────────────────────────────────────────────

    async def get_dashboard(self, days: int = 30) -> dict:
        """汇总仪表盘数据。"""
        pipeline = await self.get_pipeline_summary()
        conversion = await self.get_conversion_rate()
        activity_trend = await self.get_activity_trend(days)
        contact_growth = await self.get_contact_growth(days)
        performance = await self.get_team_performance()

        # 统计概要
        total_contacts = sum(s.get("contact_count", 0) for s in pipeline)
        total_deals = sum(s.get("deal_count", 0) for s in pipeline)
        total_value = sum(s.get("total_value", 0) for s in pipeline)
        total_won = sum(s.get("won_count", 0) for s in pipeline)

        # 近 7 天活动量
        recent_activity = sum(
            a["count"] for a in activity_trend[-7:]
        ) if activity_trend else 0

        # 近 7 天新增联系人
        recent_contacts = sum(
            g["daily_increment"] for g in contact_growth[-7:]
        ) if contact_growth else 0

        return {
            "summary": {
                "total_contacts": total_contacts,
                "total_deals": total_deals,
                "total_pipeline_value": total_value,
                "total_won_deals": total_won,
                "overall_conversion_rate": conversion.get("overall_conversion_rate", 0.0),
                "recent_7d_activity": recent_activity,
                "recent_7d_new_contacts": recent_contacts,
            },
            "pipeline": pipeline,
            "conversion": conversion,
            "activity_trend": activity_trend,
            "contact_growth": contact_growth,
            "team_performance": performance,
        }
