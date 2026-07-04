"""
链客宝 — ML 仪表盘路由
======================
提供 ML 相关仪表盘页面和 API 端点。

端点:
    GET  /ml/dashboard       — ML 仪表盘 HTML 页面
    GET  /api/ml/status      — ML 系统状态 API
    POST /api/ml/train       — 触发训练
    GET  /api/ml/versions    — 模型版本列表
    POST /api/ml/deploy/{version_id}  — 部署模型
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.services.ml_pipeline import pipeline as ml_pipeline
from app.services.auto_ab_testing import engine as ab_engine

logger = logging.getLogger("chainke.ml_dashboard_router")

router = APIRouter(tags=["ML 仪表盘 (自进化)"])

# 模板目录
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


@router.get(
    "/ml/dashboard",
    response_class=HTMLResponse,
    summary="ML 仪表盘页面",
)
async def ml_dashboard():
    """ML 仪表盘 HTML 页面"""
    html_path = _TEMPLATES_DIR / "ml_dashboard.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="<h1>ML 仪表盘页面未找到</h1><p>请确保 templates/ml_dashboard.html 存在</p>",
        status_code=404,
    )


@router.get(
    "/api/ml/status",
    summary="ML 系统状态 API",
)
def ml_status() -> Dict[str, Any]:
    """返回 ML 系统的当前状态"""
    versions = ml_pipeline.list_versions()
    prod_model = ml_pipeline.get_production_model()
    recent_runs = ml_pipeline.get_recent_runs(limit=5)

    # A/B 测试运行状态
    ab_running = len(ab_engine.list_experiments(
        status=__import__("app.services.auto_ab_testing", fromlist=["ExperimentStatus"])
        .ExperimentStatus.RUNNING
    ))

    return {
        "model_count": len(versions),
        "production_model": prod_model,
        "recent_runs": [r.to_dict() for r in recent_runs],
        "ab_tests_running": ab_running,
        "pipeline_ready": True,
        "models_dir": str(ml_pipeline.MODELS_DIR),
    }


@router.post(
    "/api/ml/train",
    summary="触发模型训练",
)
def trigger_training() -> Dict[str, Any]:
    """触发一次完整的 ML 训练管线"""
    try:
        run = ml_pipeline.run_full_pipeline()
        result = run.to_dict()
        return {
            "status": "started" if run.status == "running" else run.status,
            "run": result,
            "message": f"训练管线完成: {run.status} (样本数: {run.samples_count})",
        }
    except Exception as e:
        logger.exception("[MLDashboard] 训练触发失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/api/ml/versions",
    summary="模型版本列表",
)
def ml_versions() -> Dict[str, Any]:
    """返回所有模型版本"""
    versions = ml_pipeline.list_versions()
    prod_model = ml_pipeline.get_production_model()
    return {
        "versions": [v.to_dict() for v in versions],
        "total": len(versions),
        "production_model": prod_model,
    }


@router.post(
    "/api/ml/deploy/{version_id}",
    summary="部署模型到生产",
)
def deploy_model(version_id: str) -> Dict[str, Any]:
    """部署指定模型版本到生产"""
    success = ml_pipeline.deploy(version_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"模型版本 '{version_id}' 不存在或部署失败",
        )
    return {
        "message": f"模型 {version_id} 已部署到生产",
        "version_id": version_id,
    }


@router.post(
    "/api/ml/auto-deploy",
    summary="自动部署最优模型",
)
def auto_deploy_model() -> Dict[str, Any]:
    """自动选择并部署最优模型到生产"""
    deployed = ml_pipeline.auto_deploy()
    if deployed:
        return {
            "message": f"自动部署完成，最优版本: {deployed}",
            "version_id": deployed,
        }
    return {
        "message": "无可用模型版本，跳过自动部署",
        "version_id": None,
    }


@router.get(
    "/api/ml/ab-tests",
    summary="A/B 测试实验列表 (用于仪表盘)",
)
def ml_ab_tests() -> Dict[str, Any]:
    """返回所有 A/B 测试实验 (供 ML 仪表盘使用)"""
    experiments = ab_engine.list_experiments()
    return {
        "experiments": [e.to_dict() for e in experiments],
        "total": len(experiments),
        "running": sum(1 for e in experiments if e.status.value == "running"),
        "completed": sum(1 for e in experiments if e.status.value in ("completed", "declared_winner")),
    }


__all__ = ["router"]
