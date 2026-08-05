"""F21 Agent化任务决策矩阵 — REST API。

API:
  POST   /api/decision-matrix/evaluate   — 评估单个任务的Agent适配度
  POST   /api/decision-matrix/batch       — 批量评估多个任务
  GET    /api/decision-matrix/matrix      — 获取矩阵全局统计与边界信息
  GET    /api/decision-matrix/categories  — 获取四象限分类定义及示例
  GET    /api/decision-matrix/history     — 获取历史评估记录
  POST   /api/decision-matrix/reset       — 重置历史统计
"""

from __future__ import annotations
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.models.decision_matrix import (
    DecisionQuadrant,
    EvaluationRequest,
    BatchEvaluationRequest,
    BatchEvaluationResult,
    TaskEvaluationResult,
    MatrixStats,
    AgentReadinessCategory,
)
from app.services.decision_matrix import (
    DecisionMatrixEngine,
    get_decision_matrix,
    COMPLEXITY_THRESHOLD,
    REPETITION_THRESHOLD,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/decision-matrix", tags=["F21 Agent化任务决策矩阵"])


# ── 统一响应模型 ─────────────────────────


def ok(data: dict | list | None = None, message: str = "success") -> JSONResponse:
    return JSONResponse(content={"code": 0, "message": message, "data": data})


def fail(message: str, code: int = 1, status: int = 400) -> JSONResponse:
    return JSONResponse(
        content={"code": code, "message": message, "data": None},
        status_code=status,
    )


# ── API 端点 ──────────────────────────────


@router.post("/evaluate", summary="评估单任务Agent适配度")
async def evaluate_task(request: EvaluationRequest) -> JSONResponse:
    """评估单个任务的Agent化适配度，返回四象限分类与评分。"""
    try:
        engine = get_decision_matrix()
        result = engine.evaluate(request)
        return ok(data=result.model_dump())
    except Exception as exc:
        logger.exception("决策矩阵评估失败")
        return fail(message=f"评估异常: {exc}", status=500)


@router.post("/batch", summary="批量评估任务Agent适配度")
async def batch_evaluate(request: BatchEvaluationRequest) -> JSONResponse:
    """批量评估多个任务，返回各任务结果及象限分布统计。"""
    try:
        engine = get_decision_matrix()
        result = engine.batch_evaluate(request)
        return ok(data=result.model_dump())
    except Exception as exc:
        logger.exception("批量评估异常")
        return fail(message=f"批量评估异常: {exc}", status=500)


@router.get("/matrix", summary="获取矩阵全局统计")
async def get_matrix() -> JSONResponse:
    """返回决策矩阵的累计统计信息：评估总数、象限分布、平均分。"""
    try:
        engine = get_decision_matrix()
        stats = engine.get_stats()
        return ok(
            data={
                "stats": stats.model_dump(),
                "thresholds": {
                    "complexity_threshold": COMPLEXITY_THRESHOLD,
                    "repetition_threshold": REPETITION_THRESHOLD,
                    "complexity_range": [0, 100],
                    "repetition_range": [0, 100],
                },
            }
        )
    except Exception as exc:
        logger.exception("获取矩阵统计异常")
        return fail(message=f"获取矩阵统计异常: {exc}", status=500)


@router.get("/categories", summary="获取四象限分类定义")
async def get_categories() -> JSONResponse:
    """返回四象限分类的详细定义、评分范围和建议，附带示例任务。"""
    try:
        engine = get_decision_matrix()
        categories = engine.get_categories()
        return ok(
            data={
                "categories": [c.model_dump() for c in categories],
                "classification_rule": (
                    f"复杂度 >= {COMPLEXITY_THRESHOLD} 为高复杂度, "
                    f"重复度 >= {REPETITION_THRESHOLD} 为高重复度; "
                    "适配度评分基于象限基准 + 重复度增益 - 复杂度损耗"
                ),
            }
        )
    except Exception as exc:
        logger.exception("获取分类异常")
        return fail(message=f"获取分类异常: {exc}", status=500)


@router.get("/history", summary="获取历史评估记录")
async def get_history() -> JSONResponse:
    """返回所有历史评估记录。"""
    try:
        engine = get_decision_matrix()
        history = engine.get_history()
        return ok(data={"tasks": [h.model_dump() for h in history], "total": len(history)})
    except Exception as exc:
        logger.exception("获取历史记录异常")
        return fail(message=f"获取历史记录异常: {exc}", status=500)


@router.post("/reset", summary="重置历史统计")
async def reset_stats() -> JSONResponse:
    """清空历史评估记录，重置累计统计。"""
    try:
        engine = get_decision_matrix()
        engine.reset_stats()
        return ok(message="统计已重置")
    except Exception as exc:
        logger.exception("重置统计异常")
        return fail(message=f"重置统计异常: {exc}", status=500)
