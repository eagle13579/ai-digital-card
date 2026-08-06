"""CRM 报表 API 路由。

端点前缀: /api/crm/reports

管道报表:
  GET    /api/crm/reports/pipeline    → 管道转换漏斗(每个阶段的联系人数量)

活动报表:
  GET    /api/crm/reports/activities   → 最近活动统计(按类型分组)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user

from app.crm.crm_models import CrmActivity, CrmContact, CrmPipelineStage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crm/reports", tags=["CRM 报表"])


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/pipeline", response_model=dict, summary="管道转换漏斗")
async def get_pipeline_funnel(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取销售管道转换漏斗数据。

    返回每个管道阶段的联系人数量，按 sort_order 升序排列。
    """
    # 查询每个阶段及其联系人数量
    stmt = (
        select(
            CrmPipelineStage.id,
            CrmPipelineStage.name,
            CrmPipelineStage.sort_order,
            CrmPipelineStage.color,
            CrmPipelineStage.win_probability,
            func.count(CrmContact.id).label("contact_count"),
        )
        .outerjoin(
            CrmContact,
            CrmContact.pipeline_stage_id == CrmPipelineStage.id,
        )
        .group_by(CrmPipelineStage.id)
        .order_by(CrmPipelineStage.sort_order)
    )
    result = await db.execute(stmt)
    rows = result.all()

    stages = []
    total_contacts = 0
    for row in rows:
        count = row.contact_count or 0
        total_contacts += count
        stages.append(
            {
                "stage_id": row.id,
                "stage_name": row.name,
                "sort_order": row.sort_order,
                "color": row.color,
                "win_probability": row.win_probability,
                "contact_count": count,
            }
        )

    # 计算转化率（相对于上一阶段）
    funnel = []
    prev_count = total_contacts
    for s in stages:
        conversion_rate = (
            round((s["contact_count"] / prev_count * 100), 2)
            if prev_count > 0
            else 0.0
        )
        funnel.append(
            {
                **s,
                "conversion_rate": conversion_rate,
            }
        )
        prev_count = s["contact_count"]

    return {
        "success": True,
        "data": {
            "total_contacts": total_contacts,
            "stages": funnel,
        },
    }


@router.get("/activities", response_model=dict, summary="最近活动统计")
async def get_activities_report(
    days: int = Query(30, ge=1, le=365, description="统计最近N天的活动"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取最近一段时间内的活动统计，按活动类型分组。

    返回每种活动类型的数量及占比。
    """
    # 使用 text() 构建带参数的时间过滤查询
    stmt = text(
        """
        SELECT
            activity_type,
            COUNT(*) AS type_count
        FROM crm_activities
        WHERE activity_date >= NOW() - INTERVAL '1 day' * :days
        GROUP BY activity_type
        ORDER BY type_count DESC
        """
    )

    # 兼容 SQLite (SQLite 不支持 INTERVAL)
    # 检测数据库类型
    try:
        result = await db.execute(stmt, {"days": days})
        rows = result.all()
    except Exception:
        # SQLite fallback
        stmt_sqlite = text(
            """
            SELECT
                activity_type,
                COUNT(*) AS type_count
            FROM crm_activities
            WHERE activity_date >= datetime('now', ? || ' days')
            GROUP BY activity_type
            ORDER BY type_count DESC
            """
        )
        result = await db.execute(stmt_sqlite, (f"-{days}",))
        rows = result.all()

    activity_types = []
    total = 0
    for row in rows:
        count = row.type_count or 0
        total += count
        activity_types.append(
            {
                "activity_type": row.activity_type,
                "count": count,
            }
        )

    # 计算百分比
    for a in activity_types:
        a["percentage"] = (
            round((a["count"] / total * 100), 2) if total > 0 else 0.0
        )

    return {
        "success": True,
        "data": {
            "total_activities": total,
            "days_range": days,
            "activity_types": activity_types,
        },
    }
