"""
业务级指标看板路由 — GET /api/admin/metrics/*

提供:
  - /api/admin/metrics/funnel           — 用户行为漏斗
  - /api/admin/metrics/growth-gaps      — 增长缺口分析
  - /api/admin/metrics/dau              — 日活趋势
  - /api/admin/metrics/retention        — 留存率
  - /api/admin/metrics/recommendation   — 推荐效果指标
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/metrics", tags=["业务指标看板"])


@router.get("/funnel")
async def get_funnel(
    start_date: date | None = Query(None, description="起始日期 (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """获取用户行为漏斗数据

    漏斗阶段:
      1. 注册用户 → 2. 创建名片 → 3. 搜索匹配 → 4. 查看联系人 → 5. 发送消息 → 6. 成交

    Returns:
      每阶段: 用户数 / 转化率 / 流失率 / 基准转化率
    """
    try:
        service = MetricsService(db)
        data = await service.get_funnel_data(start_date, end_date)
        return {"code": 200, "message": "ok", "data": data}
    except Exception as exc:
        logger.exception("漏斗查询异常: %s", exc)
        return {"code": 500, "message": f"漏斗查询失败: {exc}", "data": []}


@router.get("/growth-gaps")
async def get_growth_gaps(
    start_date: date | None = Query(None, description="起始日期 (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """获取增长缺口分析

    对比实际转化率 vs 行业基准转化率, 标记 P0/P1/P2 优先级。
    """
    try:
        service = MetricsService(db)
        data = await service.get_growth_gaps(start_date, end_date)
        return {"code": 200, "message": "ok", "data": data}
    except Exception as exc:
        logger.exception("增长缺口查询异常: %s", exc)
        return {"code": 500, "message": f"增长缺口查询失败: {exc}", "data": []}


@router.get("/dau")
async def get_dau(
    days: int = Query(30, description="查询天数 (默认30天)", ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """获取日活用户趋势 (DAU / 新增注册 / 活跃名片)"""
    try:
        service = MetricsService(db)
        data = await service.get_daily_active_users(days)
        return {"code": 200, "message": "ok", "data": data}
    except Exception as exc:
        logger.exception("DAU查询异常: %s", exc)
        return {"code": 500, "message": f"DAU查询失败: {exc}", "data": []}


@router.get("/retention")
async def get_retention(
    cohort_days: int = Query(30, description="群组天数 (默认30天)", ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """获取留存率 (D+1 / D+7 / D+30 留存)"""
    try:
        service = MetricsService(db)
        data = await service.get_retention_rate(cohort_days)
        return {"code": 200, "message": "ok", "data": data}
    except Exception as exc:
        logger.exception("留存率查询异常: %s", exc)
        return {"code": 500, "message": f"留存率查询失败: {exc}", "data": []}


@router.get("/recommendation")
async def get_recommendation(
    start_date: date | None = Query(None, description="起始日期 (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """获取推荐效果指标 (曝光 / 点击 / 转化)"""
    try:
        service = MetricsService(db)
        data = await service.get_recommendation_effectiveness(start_date, end_date)
        return {"code": 200, "message": "ok", "data": data}
    except Exception as exc:
        logger.exception("推荐效果查询异常: %s", exc)
        return {"code": 500, "message": f"推荐效果查询失败: {exc}", "data": {}}
