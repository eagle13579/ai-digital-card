"""模型部署管理API路由 — Canary deployment management endpoints.

提供模型注册、流量分配、自动提升、回滚的API接口。
集成 CanaryDeployManager + ModelRegistry。

端點:
  POST   /api/v1/deploy/models          — 注册新模型版本
  POST   /api/v1/deploy/traffic         — 设置流量分配
  POST   /api/v1/deploy/promote/{model_name}  — 提升到100%
  POST   /api/v1/deploy/rollback/{model_name} — 回滚
  POST   /api/v1/deploy/advance/{model_name}  — 逐步推进到下一阶段
  GET    /api/v1/deploy/status          — 查看所有模型部署状态
  GET    /api/v1/deploy/status/{model_name}   — 查看指定模型状态
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from app.ai.gateway.canary_deploy import (
    CanaryDeployManager,
    get_canary_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/deploy", tags=["模型部署"])


# ======================================================================
# Pydantic Schemas
# ======================================================================


class RegisterModelRequest(BaseModel):
    """Request body for registering a new model version.

    The actual AIGatewayProtocol instance is identified by the gateway_type
    and configuration parameters; the manager will instantiate it.
    For simplicity, the API records the registration — the caller must
    have the gateway wired in at the manager level or use the default
    DirectAIGateway.
    """
    model_name: str = Field(..., description="Model name (e.g. 'business-card-lora')")
    version: str = Field(..., description="Version string (e.g. 'v2.0-beta')")
    status: str = Field("staging", description="Initial status: staging / canary / active")


class SetTrafficRequest(BaseModel):
    """Request body for setting traffic split."""
    model_name: str = Field(..., description="Model name")
    old_version: str = Field(..., description="Baseline (current production) version")
    new_version: str = Field(..., description="Canary version being rolled out")
    new_percent: int = Field(5, ge=0, le=100, description="Traffic percentage for new version (0-100)")


class PromoteResponse(BaseModel):
    """Response from promote/rollback operations."""
    success: bool
    message: str
    data: dict[str, Any] | None = None


# ======================================================================
# Helper: get manager instance
# ======================================================================


def _get_manager() -> CanaryDeployManager:
    """Get the global CanaryDeployManager singleton.

    Returns:
        CanaryDeployManager instance.

    Raises:
        HTTPException 500 if manager is unavailable.
    """
    try:
        return get_canary_manager()
    except Exception as exc:
        logger.error("Failed to get CanaryDeployManager: %s", exc)
        raise HTTPException(status_code=500, detail=f"Canary deploy manager unavailable: {exc}")


# ======================================================================
# API Endpoints
# ======================================================================


@router.post("/models", summary="注册新模型版本")
async def register_model(
    req: RegisterModelRequest,
    manager: CanaryDeployManager = Depends(_get_manager),
):
    """Register a new model version in the canary deployment system.

    This registers the model so it can be used in traffic splits,
    canary rollouts, and promotions. The actual AIGatewayProtocol
    instance must be wired through the manager's registry.

    Returns:
        Registration confirmation with version details.
    """
    try:
        # Check if the manager has registered versions — this API endpoint
        # records intent. The actual gateway wiring happens outside the API.
        if req.model_name in manager._versions:
            # Check for duplicate version
            existing = manager._versions.get(req.model_name, {}).get(req.version)
            if existing:
                return {
                    "code": 200,
                    "message": f"版本 '{req.version}' 已存在，无需重复注册",
                    "data": {
                        "model_name": req.model_name,
                        "version": req.version,
                        "status": existing.status,
                    },
                }

        # We need at minimum a placeholder gateway. For API-driven registration
        # without a live gateway, we create a deferred placeholder.
        # The actual gateway setup should use the manager's direct API.
        from app.ai.gateway.adapters.direct_api_adapter import DirectAIGateway

        gateway = DirectAIGateway()
        entry = manager.register_model(
            name=req.model_name,
            version=req.version,
            gateway=gateway,
            status=req.status,
        )

        logger.info(
            "API: registered model '%s' version '%s' (status=%s)",
            req.model_name, req.version, req.status,
        )
        return {
            "code": 200,
            "message": f"模型 '{req.model_name}' 版本 '{req.version}' 注册成功",
            "data": {
                "model_name": req.model_name,
                "version": entry.version,
                "status": entry.status,
                "deployed_at": entry.deployed_at,
            },
        }
    except Exception as exc:
        logger.error("API: register model failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"注册模型失败: {exc}",
        )


@router.post("/traffic", summary="设置流量分配")
async def set_traffic(
    req: SetTrafficRequest,
    manager: CanaryDeployManager = Depends(_get_manager),
):
    """Set traffic split between old and new model versions.

    Configures what percentage of requests go to the canary version.
    Uses consistent hashing to ensure the same user always gets the
    same version.

    Args:
        req: Traffic split configuration.

    Returns:
        Traffic split confirmation with current percentages.
    """
    try:
        split = manager.set_traffic_split(
            model_name=req.model_name,
            version_old=req.old_version,
            version_new=req.new_version,
            new_percent=req.new_percent,
        )
        return {
            "code": 200,
            "message": f"流量分配已设置: {req.old_version}={split.baseline_percent}%, "
                       f"{req.new_version}={split.new_percent}%",
            "data": {
                "model_name": req.model_name,
                "old_version": split.old_version,
                "new_version": split.new_version,
                "old_percent": split.baseline_percent,
                "new_percent": split.new_percent,
                "next_step": manager.next_step(req.model_name),
            },
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("API: set traffic failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"设置流量分配失败: {exc}")


@router.post("/promote/{model_name}", summary="提升目标模型到100%")
async def promote_model(
    model_name: str = Path(..., description="Model name to promote"),
    manager: CanaryDeployManager = Depends(_get_manager),
):
    """Promote the canary version of a model to 100% traffic.

    This is an explicit manual promotion. For automatic promotion
    based on metrics, use the auto-promote endpoint.

    Returns:
        Promotion result with version details.
    """
    try:
        split = manager.get_traffic_split(model_name)
        if not split:
            raise HTTPException(
                status_code=400,
                detail=f"模型 '{model_name}' 没有活跃的流量分配配置",
            )

        # Manual promote: set to 100%
        manager.set_traffic_split(
            model_name=model_name,
            version_old=split.old_version,
            version_new=split.new_version,
            new_percent=100,
        )
        # Mark as promoted
        versions = manager._versions.get(model_name, {})
        if split.new_version in versions:
            versions[split.new_version].status = "promoted"
        if split.old_version in versions:
            versions[split.old_version].status = "active"

        # Remove traffic split (all traffic goes to new version now)
        if model_name in manager._traffic_splits:
            del manager._traffic_splits[model_name]

        logger.info(
            "API: promoted '%s' to 100%% (new=%s, old=%s)",
            model_name, split.new_version, split.old_version,
        )
        return {
            "code": 200,
            "message": f"模型 '{model_name}' 版本 '{split.new_version}' 已提升到 100%",
            "data": {
                "model_name": model_name,
                "promoted_version": split.new_version,
                "old_version": split.old_version,
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("API: promote failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"提升模型失败: {exc}")


@router.post("/auto-promote/{model_name}", summary="自动提升（根据指标）")
async def auto_promote_model(
    model_name: str = Path(..., description="Model name to auto-promote"),
    threshold: float = Query(0.95, ge=0.0, le=1.0, description="Satisfaction threshold (0-1)"),
    min_requests: int = Query(100, ge=1, description="Minimum requests before auto-promotion"),
    manager: CanaryDeployManager = Depends(_get_manager),
):
    """Auto-promote the canary version based on collected metrics.

    Checks:
    - Canary has at least `min_requests` observations
    - Error rate <= 5%
    - P95 latency <= 2x baseline
    - User satisfaction >= threshold (if available)

    Returns:
        Auto-promotion decision with metrics.
    """
    try:
        decision = manager.auto_promote(
            model_name=model_name,
            threshold=threshold,
            min_requests=min_requests,
        )
        if decision.get("promoted"):
            return {
                "code": 200,
                "message": f"模型 '{model_name}' 自动提升成功",
                "data": decision,
            }
        elif "auto_rolled_back" in decision.get("reason", ""):
            return {
                "code": 200,
                "message": f"模型 '{model_name}' 自动回滚",
                "data": decision,
            }
        else:
            return {
                "code": 200,
                "message": f"模型 '{model_name}' 尚未满足自动提升条件",
                "data": decision,
            }
    except Exception as exc:
        logger.error("API: auto-promote failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"自动提升失败: {exc}")


@router.post("/rollback/{model_name}", summary="一键回滚")
async def rollback_model(
    model_name: str = Path(..., description="Model name to rollback"),
    manager: CanaryDeployManager = Depends(_get_manager),
):
    """Rollback a model to its previous stable version.

    Works both for active canary splits and previously promoted versions.
    The old (baseline) version gets 100% traffic.

    Returns:
        Rollback result with version details.
    """
    try:
        result = manager.rollback(model_name)
        if not result.get("rolled_back"):
            raise HTTPException(
                status_code=400,
                detail=f"回滚失败: {result.get('reason', '未知原因')}",
            )

        logger.warning(
            "API: rolled back '%s' from '%s' to '%s'",
            model_name, result.get("rolled_from", "?"), result.get("rolled_to", "?"),
        )
        return {
            "code": 200,
            "message": f"模型 '{model_name}' 已从 '{result['rolled_from']}' "
                       f"回滚到 '{result['rolled_to']}'",
            "data": result,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("API: rollback failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"回滚失败: {exc}")


@router.post("/advance/{model_name}", summary="逐步推进到下一阶段")
async def advance_step(
    model_name: str = Path(..., description="Model name to advance"),
    manager: CanaryDeployManager = Depends(_get_manager),
):
    """Advance the canary rollout to the next progressive percentage.

    Steps: 5% → 10% → 25% → 50% → 100%
    Auto-rollback is checked before advancing.

    Returns:
        Advance result with new traffic split.
    """
    try:
        split = manager.advance_step(model_name)
        if split is None:
            # Check if already at 100%
            current_split = manager.get_traffic_split(model_name)
            if current_split and current_split.new_percent >= 100:
                return {
                    "code": 200,
                    "message": f"模型 '{model_name}' 已在 100% 阶段，无需推进",
                    "data": {
                        "model_name": model_name,
                        "new_percent": 100,
                        "baseline_percent": 0,
                        "next_step": None,
                    },
                }
            return {
                "code": 200,
                "message": f"模型 '{model_name}' 没有活跃的 canary 部署",
                "data": {"model_name": model_name},
            }

        next_step = manager.next_step(model_name)
        return {
            "code": 200,
            "message": f"模型 '{model_name}' 已推进到 {split.new_percent}%",
            "data": {
                "model_name": model_name,
                "new_percent": split.new_percent,
                "baseline_percent": split.baseline_percent,
                "next_step": next_step,
            },
        }
    except ValueError as exc:
        # Auto-rollback was triggered
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("API: advance step failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"推进失败: {exc}")


@router.get("/status", summary="查看所有模型部署状态")
async def get_all_status(
    manager: CanaryDeployManager = Depends(_get_manager),
):
    """Get deployment status for all models under canary management.

    Returns:
        Status dict with per-model version, traffic split, metrics,
        and auto-rollback risk information.
    """
    try:
        status = manager.get_status()
        return {
            "code": 200,
            "message": "ok",
            "data": {
                "models": status,
                "total_models": len(status),
                "deploy_log_count": len(manager.get_deploy_log()),
            },
        }
    except Exception as exc:
        logger.error("API: get status failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"获取状态失败: {exc}")


@router.get("/status/{model_name}", summary="查看指定模型部署状态")
async def get_model_status(
    model_name: str = Path(..., description="Model name"),
    manager: CanaryDeployManager = Depends(_get_manager),
):
    """Get deployment status for a specific model.

    Returns detailed version info, traffic split, metrics,
    and auto-rollback risk assessment.

    Args:
        model_name: Name of the model.

    Returns:
        Detailed status for the model.
    """
    try:
        status = manager.get_model_status(model_name)
        if status is None:
            raise HTTPException(
                status_code=404,
                detail=f"模型 '{model_name}' 未找到（尚未注册）",
            )
        return {
            "code": 200,
            "message": "ok",
            "data": {
                "model_name": model_name,
                **status,
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("API: get model status failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"获取模型状态失败: {exc}")


@router.get("/log", summary="查看部署历史日志")
async def get_deploy_log(
    model_name: str | None = Query(None, description="Filter by model name"),
    limit: int = Query(50, ge=1, le=500, description="Max entries to return"),
    manager: CanaryDeployManager = Depends(_get_manager),
):
    """Get deployment event history.

    Args:
        model_name: Optional model name filter.
        limit: Maximum number of log entries.

    Returns:
        List of deployment events.
    """
    try:
        log = manager.get_deploy_log(model_name)
        return {
            "code": 200,
            "message": "ok",
            "data": {
                "total": len(log),
                "items": log[-limit:],
            },
        }
    except Exception as exc:
        logger.error("API: get deploy log failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"获取部署日志失败: {exc}")
