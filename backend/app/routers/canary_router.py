"""
canary_router.py — 灰度发布管理 API (F17 彩虹部署)

API:
  POST   /api/canary/deploy      — 创建并启动灰度部署
  POST   /api/canary/rollback    — 一键回滚灰度部署
  GET    /api/canary/status      — 查询部署状态（支持过滤）
  GET    /api/canary/groups      — 查询用户分组列表
  POST   /api/canary/promote     — 手动全量发布
  POST   /api/canary/traffic     — 手动调整灰度流量比例
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Optional

from app.services.canary_service import (
    canary_registry,
    CanaryService,
    CanaryError,
    DeploymentNotFoundError,
    DeploymentStateError,
    InvalidTrafficError,
)
from app.models.canary import (
    CanaryGroup,
    CanaryStrategy,
    CanaryStatus,
    TrafficAllocationMode,
)

router = APIRouter(prefix="/api/canary", tags=["F17 灰度发布"])


# ── 请求/响应模型 ──────────────────────────

class CanaryGroupRequest(BaseModel):
    group_id: Optional[str] = None
    name: str = Field(..., description="分组名称")
    description: str = Field(default="", description="分组描述")
    user_ids: list[int] = Field(default=[], description="用户 ID 白名单")
    traffic_weight: float = Field(default=100.0, ge=0, le=100, description="流量权重")


class CanaryStepRequest(BaseModel):
    traffic: float = Field(..., ge=0, le=100, description="该步的目标流量百分比")
    duration: int = Field(default=300, ge=1, description="该步持续秒数")


class DeployRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="部署名称")
    version: str = Field(..., min_length=1, max_length=64, description="部署版本号")
    service: str = Field(..., min_length=1, max_length=128, description="目标服务名称")
    strategy: str = Field(default="manual", description="放量策略: manual/auto_timed/stepped/auto_metric")
    allocation_mode: str = Field(default="percentage", description="流量分配模式: percentage/user_group/hybrid")
    initial_traffic: float = Field(default=10.0, ge=0, le=100, description="初始灰度流量比例 %")
    target_traffic: float = Field(default=100.0, ge=0, le=100, description="目标全量流量比例 %")
    steps: list[CanaryStepRequest] = Field(default=[], description="阶梯放量步骤")
    user_groups: list[CanaryGroupRequest] = Field(default=[], description="用户分组")
    auto_promote: bool = Field(default=False, description="达到目标流量后是否自动全量")
    created_by: str = Field(default="system", description="创建者标识")
    snapshot_before: Optional[dict] = Field(default=None, description="部署前快照（用于回滚）")


class RollbackRequest(BaseModel):
    deployment_id: str = Field(..., description="部署 ID")
    reason: str = Field(default="管理员手动回滚", description="回滚原因")


class TrafficRequest(BaseModel):
    deployment_id: str = Field(..., description="部署 ID")
    percentage: float = Field(..., ge=0, le=100, description="目标流量比例 %")


class PromoteRequest(BaseModel):
    deployment_id: str = Field(..., description="部署 ID")


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None


# ── POST /api/canary/deploy — 创建并启动灰度部署 ──

@router.post("/deploy", response_model=ApiResponse)
async def deploy_canary(req: DeployRequest):
    """创建并启动灰度部署"""
    try:
        # 解析放量策略
        strategy_map = {
            "manual": CanaryStrategy.MANUAL,
            "auto_timed": CanaryStrategy.AUTO_TIMED,
            "stepped": CanaryStrategy.STEPPED,
            "auto_metric": CanaryStrategy.AUTO_METRIC,
        }
        strategy = strategy_map.get(req.strategy)
        if strategy is None:
            raise HTTPException(status_code=400, detail=f"无效的放量策略: {req.strategy}")

        # 解析流量分配模式
        mode_map = {
            "percentage": TrafficAllocationMode.PERCENTAGE,
            "user_group": TrafficAllocationMode.USER_GROUP,
            "hybrid": TrafficAllocationMode.HYBRID,
        }
        allocation_mode = mode_map.get(req.allocation_mode)
        if allocation_mode is None:
            raise HTTPException(status_code=400, detail=f"无效的流量分配模式: {req.allocation_mode}")

        # 构建用户分组
        groups = []
        for g in req.user_groups:
            group = CanaryGroup(
                group_id=g.group_id or f"grp_{id(g):x}",
                name=g.name,
                description=g.description,
                user_ids=g.user_ids,
                traffic_weight=g.traffic_weight,
            )
            groups.append(group)

        # 构建阶梯步骤
        steps = [{"traffic": s.traffic, "duration": s.duration} for s in req.steps]

        # 创建部署
        svc = canary_registry.create_deployment(
            name=req.name,
            version=req.version,
            service=req.service,
            strategy=strategy,
            allocation_mode=allocation_mode,
            initial_traffic=req.initial_traffic,
            target_traffic=req.target_traffic,
            steps=steps,
            user_groups=groups,
            auto_promote=req.auto_promote,
            created_by=req.created_by,
            snapshot_before=req.snapshot_before,
        )

        # 启动部署
        deployment = svc.start()

        return ApiResponse(
            message=f"灰度部署 '{req.name}' v{req.version} 创建并启动成功",
            data=deployment.to_dict(),
        )

    except CanaryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建灰度部署失败: {str(e)}")


# ── POST /api/canary/rollback — 一键回滚 ──

@router.post("/rollback", response_model=ApiResponse)
async def rollback_canary(req: RollbackRequest):
    """一键回滚灰度部署到部署前状态"""
    try:
        svc = canary_registry.get_or_raise(req.deployment_id)
        deployment = svc.rollback(reason=req.reason)

        return ApiResponse(
            message=f"灰度部署 '{deployment.name}' 已回滚",
            data=deployment.to_status_dict(),
        )

    except DeploymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DeploymentStateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回滚失败: {str(e)}")


# ── GET /api/canary/status — 查询部署状态 ──

@router.get("/status", response_model=ApiResponse)
async def get_canary_status(
    deployment_id: Optional[str] = Query(None, description="部署 ID（不传则返回所有部署）"),
    service: Optional[str] = Query(None, description="按服务名过滤"),
    status: Optional[str] = Query(None, description="按状态过滤: pending/deploying/canary/promoted/rolled_back/failed/cancelled"),
):
    """查询灰度部署状态"""
    try:
        if deployment_id:
            # 查询指定部署
            svc = canary_registry.get_or_raise(deployment_id)
            data = svc.get_full_status()
            return ApiResponse(data=data)

        # 查询所有部署（可过滤）
        status_filter = None
        if status:
            try:
                status_filter = CanaryStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的状态值: {status}")

        deployments = canary_registry.list_deployments(
            service=service,
            status=status_filter,
        )

        # 额外统计
        active_count = len([d for d in deployments if d.get("status") == "canary"])
        total_count = len(deployments)

        return ApiResponse(data={
            "total": total_count,
            "active": active_count,
            "deployments": deployments,
        })

    except DeploymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询状态失败: {str(e)}")


# ── GET /api/canary/groups — 查询用户分组 ──

@router.get("/groups", response_model=ApiResponse)
async def get_canary_groups(
    service: Optional[str] = Query(None, description="按服务名过滤"),
    deployment_id: Optional[str] = Query(None, description="按部署 ID 过滤"),
):
    """查询灰度用户分组列表"""
    try:
        if deployment_id:
            svc = canary_registry.get_or_raise(deployment_id)
            groups = svc.get_groups()
        else:
            groups = canary_registry.get_service_groups(service_name=service)

        return ApiResponse(data={
            "total": len(groups),
            "groups": [g.to_dict() for g in groups],
        })

    except DeploymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询分组失败: {str(e)}")


# ── POST /api/canary/promote — 手动全量发布 ──

@router.post("/promote", response_model=ApiResponse)
async def promote_canary(req: PromoteRequest):
    """手动执行全量发布"""
    try:
        svc = canary_registry.get_or_raise(req.deployment_id)
        deployment = svc.promote()

        return ApiResponse(
            message=f"灰度部署 '{deployment.name}' 已全量发布",
            data=deployment.to_status_dict(),
        )

    except DeploymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DeploymentStateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"全量发布失败: {str(e)}")


# ── POST /api/canary/traffic — 调整流量比例 ──

@router.post("/traffic", response_model=ApiResponse)
async def set_canary_traffic(req: TrafficRequest):
    """手动调整灰度流量比例"""
    try:
        svc = canary_registry.get_or_raise(req.deployment_id)
        deployment = svc.set_traffic(req.percentage)

        return ApiResponse(
            message=f"灰度流量已调整为 {req.percentage}%",
            data=deployment.to_status_dict(),
        )

    except DeploymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (DeploymentStateError, InvalidTrafficError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调整流量失败: {str(e)}")


# ── POST /api/canary/check-metrics — 指标检查与自动放量 ──

class MetricsCheckRequest(BaseModel):
    deployment_id: str = Field(..., description="部署 ID")
    error_rate: Optional[float] = Field(None, ge=0, le=100, description="当前错误率 %")
    success_rate: Optional[float] = Field(None, ge=0, le=100, description="当前成功率 %")
    latency_p99: Optional[float] = Field(None, ge=0, description="当前 p99 延迟 ms")


@router.post("/check-metrics", response_model=ApiResponse)
async def check_metrics(req: MetricsCheckRequest):
    """检查指标并根据配置自动放量（AUTO_METRIC 策略使用）"""
    try:
        svc = canary_registry.get_or_raise(req.deployment_id)
        result = svc.check_metrics_and_promote(
            error_rate=req.error_rate,
            success_rate=req.success_rate,
            latency_p99=req.latency_p99,
        )

        return ApiResponse(
            message=result.get("reason", "指标检查完成"),
            data=result,
        )

    except DeploymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"指标检查失败: {str(e)}")


# ── DELETE /api/canary/{deployment_id} — 删除部署记录 ──

@router.delete("/{deployment_id}", response_model=ApiResponse)
async def delete_deployment(deployment_id: str):
    """从注册表中移除部署记录"""
    removed = canary_registry.remove(deployment_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"部署 '{deployment_id}' 不存在")
    return ApiResponse(message=f"部署 '{deployment_id}' 已移除")
