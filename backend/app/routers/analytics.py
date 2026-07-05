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

router = APIRouter(prefix="/api/v1/analytics", tags=["付款分析"])


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
