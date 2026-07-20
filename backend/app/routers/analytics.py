"""
付款转化分析 API — GET /api/analytics/payment/overview
=======================================================

提供付款相关业务指标的实时查询接口。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.payment_analytics import get_payment_overview

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["付款分析"])


@router.get("/payment/overview")
async def payment_overview(db: AsyncSession = Depends(get_db)):
    """获取付款转化指标总览

    返回以下指标:
      - trial:          试用统计 (启动数 / 活跃 / 转化 / 过期)
      - mrr:            月度经常性收入
      - churn_rate:     30天客户流失率
      - ltv:            客户生命周期价值
      - paid_users:     付费用户套餐分布

    Returns:
        {
          "code": 200,
          "message": "ok",
          "data": { ... }
        }
    """
    data = await get_payment_overview(db)
    return {
        "code": 200,
        "message": "ok",
        "data": data,
    }


@router.get("/funnel")
async def get_funnel(db: AsyncSession = Depends(get_db)):
    """用户增长漏斗: 注册→名片→匹配→连接"""
    from sqlalchemy import text
    result = await db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM users) AS registered,
            (SELECT COUNT(*) FROM brochures WHERE status='active') AS card_created,
            (SELECT COUNT(DISTINCT user_a_id) FROM match_records) AS matched_users,
            (SELECT COUNT(*) FROM connections) AS connected,
            (SELECT COUNT(*) FROM users WHERE updated_at > NOW() - INTERVAL '7 days') AS active_7d
    """))
    row = result.fetchone()
    return {
        "code": 200,
        "message": "ok",
        "data": {
            "funnel": {
                "registered": row[0],
                "card_created": row[1],
                "matched_users": row[2],
                "connected": row[3],
                "active_7d": row[4]
            },
            "conversion_rates": {
                "register_to_card": f"{row[1]/max(row[0],1)*100:.1f}%",
                "card_to_match": f"{row[2]/max(row[1],1)*100:.1f}%",
                "match_to_connect": f"{row[3]/max(row[2],1)*100:.1f}%"
            }
        }
    }
