"""
在线学习引擎 — FastAPI 路由

提供在线学习的手动触发和状态查询 API 端点。
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Query

from app.ai.online_learning import (
    get_online_learning_engine,
    trigger_learning,
    get_learning_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai/learning", tags=["在线学习引擎"])


# ======================================================================
# 学习控制
# ======================================================================


@router.post("/trigger")
async def manual_trigger():
    """手动触发一次在线学习

    从 FeedbackLoop 读取当前反馈统计，计算全局调整系数，
    更新 RecommendEngine 的权重，并记录学习日志。

    Returns:
        学习结果报告，包含调整前后的权重变化
    """
    logger.info("手动触发在线学习")
    result = trigger_learning()
    return {
        "code": 200,
        "message": "在线学习完成" if result.get("status") == "completed" else "在线学习执行异常",
        "data": {
            "cycle": result.get("cycle"),
            "duration_seconds": result.get("duration_seconds"),
            "feedback_stats": result.get("feedback_stats"),
            "weight_changes": result.get("weight_changes"),
        },
    }


# ======================================================================
# 状态查询
# ======================================================================


@router.get("/status")
async def get_status():
    """获取在线学习引擎状态

    返回: 反馈统计、学习进度、上次学习时间、当前权重等。

    Returns:
        dict: 引擎状态概览
    """
    status = get_learning_status()
    return {
        "code": 200,
        "message": "ok",
        "data": status,
    }


# ======================================================================
# 学习日志
# ======================================================================


@router.get("/logs")
async def get_logs(
    limit: int = Query(50, ge=1, le=200, description="返回最新日志条数"),
):
    """获取在线学习历史日志

    Args:
        limit: 返回最新日志条数 (max: 200)

    Returns:
        list[dict]: 学习日志记录列表
    """
    engine = get_online_learning_engine()
    logs = engine.get_recent_logs(limit=limit)
    return {
        "code": 200,
        "message": "ok",
        "data": {
            "items": logs,
            "total": len(logs),
        },
    }
