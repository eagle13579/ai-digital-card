"""
链客宝 — A/B 测试仪表盘路由
=============================
提供 REST API 用于查看和管理自动 A/B 测试实验。

端点:
    GET     /api/ab-tests/experiments         — 列出所有实验
    GET     /api/ab-tests/experiments/{name}  — 实验详情 + 统计
    POST    /api/ab-tests/experiments          — 创建并启动实验
    POST    /api/ab-tests/experiments/{name}/start    — 启动
    POST    /api/ab-tests/experiments/{name}/pause    — 暂停
    POST    /api/ab-tests/experiments/{name}/cancel   — 取消
    POST    /api/ab-tests/experiments/{name}/analyze  — 分析
    POST    /api/ab-tests/auto-declare                — 自动宣布胜者
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query

from app.services.auto_ab_testing import (
    ExperimentStatus,
    ExperimentType,
    engine as ab_engine,
)

logger = logging.getLogger("chainke.ab_test_router")

router = APIRouter(prefix="/api/ab-tests", tags=["A/B 测试 (自进化)"])


# ===================================================================
# API 模型
# ===================================================================

class CreateExperimentRequest(BaseModel):
    name: str
    experiment_type: ExperimentType
    variants: Dict[str, float]
    min_sample_size: int = 50
    confidence_threshold: float = 0.95
    max_duration_days: int = 14
    metadata: Dict[str, Any] = {}


# ===================================================================
# 端点
# ===================================================================

@router.get(
    "/experiments",
    summary="列出所有 A/B 实验",
)
def list_experiments(
    status: Optional[str] = Query(None, description="筛选状态"),
    experiment_type: Optional[str] = Query(None, description="筛选实验类型"),
) -> Dict[str, Any]:
    """返回所有 A/B 测试实验列表"""
    st = ExperimentStatus(status) if status else None
    et = ExperimentType(experiment_type) if experiment_type else None

    experiments = ab_engine.list_experiments(status=st, experiment_type=et)
    return {
        "experiments": [e.to_dict() for e in experiments],
        "total": len(experiments),
    }


@router.get(
    "/experiments/{name}",
    summary="获取实验详情和统计",
)
def get_experiment(name: str) -> Dict[str, Any]:
    """返回指定实验的详情和最新统计"""
    exp = ab_engine.get_experiment(name)
    if exp is None:
        raise HTTPException(status_code=404, detail=f"实验 '{name}' 不存在")

    analysis = ab_engine.analyze(name)
    return {
        "experiment": exp.to_dict(),
        "analysis": analysis,
    }


@router.post(
    "/experiments",
    summary="创建并自动启动实验",
    status_code=201,
)
def create_experiment(req: CreateExperimentRequest) -> Dict[str, Any]:
    """创建一个新的 A/B 测试实验并自动启动"""
    try:
        exp = ab_engine.create_and_run_experiment(
            name=req.name,
            experiment_type=req.experiment_type,
            variants=req.variants,
            min_sample_size=req.min_sample_size,
            confidence_threshold=req.confidence_threshold,
            max_duration_days=req.max_duration_days,
            metadata=req.metadata,
        )
        return {"experiment": exp.to_dict(), "message": "实验已创建并启动"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/experiments/{name}/start",
    summary="启动实验",
)
def start_experiment(name: str) -> Dict[str, Any]:
    """启动指定实验"""
    success = ab_engine.start_experiment(name)
    if not success:
        raise HTTPException(status_code=400, detail=f"无法启动实验 '{name}'")
    return {"message": f"实验 '{name}' 已启动"}


@router.post(
    "/experiments/{name}/pause",
    summary="暂停实验",
)
def pause_experiment(name: str) -> Dict[str, Any]:
    """暂停指定实验"""
    success = ab_engine.pause_experiment(name)
    if not success:
        raise HTTPException(status_code=400, detail=f"无法暂停实验 '{name}'")
    return {"message": f"实验 '{name}' 已暂停"}


@router.post(
    "/experiments/{name}/cancel",
    summary="取消实验",
)
def cancel_experiment(name: str) -> Dict[str, Any]:
    """取消指定实验"""
    success = ab_engine.cancel_experiment(name)
    if not success:
        raise HTTPException(status_code=400, detail=f"无法取消实验 '{name}'")
    return {"message": f"实验 '{name}' 已取消"}


@router.post(
    "/experiments/{name}/analyze",
    summary="分析实验统计结果",
)
def analyze_experiment(name: str) -> Dict[str, Any]:
    """分析指定实验的统计结果"""
    exp = ab_engine.get_experiment(name)
    if exp is None:
        raise HTTPException(status_code=404, detail=f"实验 '{name}' 不存在")
    analysis = ab_engine.analyze(name)
    return {"analysis": analysis}


@router.post(
    "/auto-declare",
    summary="自动检查并宣布所有实验的胜者",
)
def auto_declare_winners() -> Dict[str, Any]:
    """自动检查所有运行中的实验，宣布统计显著的胜者"""
    results = ab_engine.auto_declare_all_winners()
    declared = [(name, w) for name, w in results if w is not None]
    return {
        "checked": len(results),
        "declared": len(declared),
        "winners": [{"experiment": n, "winner": w} for n, w in declared],
        "message": f"检查了 {len(results)} 个实验，{len(declared)} 个宣布胜者",
    }


__all__ = ["router"]
