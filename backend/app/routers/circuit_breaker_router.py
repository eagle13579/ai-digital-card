"""
circuit_breaker_router.py — 熔断器管理 API (FastAPI)

API:
  GET    /api/circuit-breaker/status          — 所有熔断器状态列表
  GET    /api/circuit-breaker/status/{name}   — 指定熔断器状态详情
  POST   /api/circuit-breaker/trigger         — 手动触发熔断（强制 OPEN）
  DELETE /api/circuit-breaker/reset/{name}    — 重置指定熔断器
  DELETE /api/circuit-breaker/reset           — 重置所有熔断器
  POST   /api/circuit-breaker/create          — 创建新熔断器（自定义规则）
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from app.services.circuit_breaker import (
    circuit_breaker_registry,
    CircuitBreaker,
    CircuitBreakerOpenError,
)
from app.models.circuit_breaker import (
    CircuitBreakerRule,
    CircuitBreakerStatus,
    CircuitState,
)

router = APIRouter(prefix="/api/circuit-breaker", tags=["熔断器管理"])


# ── 请求/响应模型 ──────────────────────────

class CreateBreakerRequest(BaseModel):
    name: str = Field(..., description="熔断器名称（唯一标识）")
    failure_threshold: int = Field(default=5, ge=1, description="连续失败阈值")
    recovery_timeout: float = Field(default=30.0, gt=0, description="恢复超时（秒）")
    half_open_max_requests: int = Field(default=3, ge=1, description="半开最大试探请求数")
    success_threshold: int = Field(default=2, ge=1, description="半开连续成功恢复阈值")
    description: str = Field(default="", description="描述")
    tags: list[str] = Field(default=[], description="标签列表")


class TriggerRequest(BaseModel):
    name: str = Field(..., description="要触发的熔断器名称")
    reason: str = Field(default="管理员手动触发", description="触发原因")


class BreakerResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: dict | list | None = None


# ── GET /status — 所有熔断器状态 ──────────

@router.get("/status", response_model=BreakerResponse)
async def list_all_breakers():
    """获取所有熔断器的状态列表"""
    statuses = circuit_breaker_registry.all_status()
    return BreakerResponse(data={
        "breakers": [s.to_dict() for s in statuses],
        "total": len(statuses),
    })


# ── GET /status/{name} — 指定熔断器状态 ──

@router.get("/status/{name}", response_model=BreakerResponse)
async def get_breaker_status(name: str):
    """获取指定熔断器的详细状态"""
    cb = circuit_breaker_registry.get(name)
    if cb is None:
        raise HTTPException(
            status_code=404,
            detail=f"熔断器 '{name}' 不存在",
        )
    return BreakerResponse(data=cb.get_status().to_dict())


# ── POST /trigger — 手动触发熔断 ─────────

@router.post("/trigger", response_model=BreakerResponse)
async def trigger_breaker(req: TriggerRequest):
    """手动触发熔断（强制 OPEN），用于模拟故障或主动降级"""
    success = circuit_breaker_registry.force_open(req.name, req.reason)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"熔断器 '{req.name}' 不存在",
        )
    cb = circuit_breaker_registry.get(req.name)
    return BreakerResponse(
        message=f"熔断器 '{req.name}' 已强制打开",
        data=cb.get_status().to_dict() if cb else None,
    )


# ── DELETE /reset/{name} — 重置指定熔断器 ──

@router.delete("/reset/{name}", response_model=BreakerResponse)
async def reset_breaker(name: str):
    """重置指定熔断器到 CLOSED 状态"""
    success = circuit_breaker_registry.reset(name)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"熔断器 '{name}' 不存在",
        )
    return BreakerResponse(message=f"熔断器 '{name}' 已重置为 CLOSED")


# ── DELETE /reset — 重置所有熔断器 ──────

@router.delete("/reset", response_model=BreakerResponse)
async def reset_all_breakers():
    """重置所有熔断器到 CLOSED 状态"""
    count = circuit_breaker_registry.reset_all()
    return BreakerResponse(
        message=f"已重置所有熔断器",
        data={"reset_count": count},
    )


# ── POST /create — 创建自定义熔断器 ────

@router.post("/create", response_model=BreakerResponse)
async def create_breaker(req: CreateBreakerRequest):
    """创建自定义熔断器（如果已存在则返回现有实例）"""
    rule = CircuitBreakerRule(
        name=req.name,
        failure_threshold=req.failure_threshold,
        recovery_timeout=req.recovery_timeout,
        half_open_max_requests=req.half_open_max_requests,
        success_threshold=req.success_threshold,
        description=req.description,
        tags=req.tags,
    )
    cb = circuit_breaker_registry.get_or_create(req.name, rule)
    return BreakerResponse(
        message=f"熔断器 '{req.name}' 已就绪",
        data=cb.get_status().to_dict(),
    )


# ── GET /health — 熔断器子系统健康检查 ──

@router.get("/health", response_model=BreakerResponse)
async def circuit_breaker_health():
    """熔断器子系统健康检查"""
    total = circuit_breaker_registry.count()
    open_breakers = [
        s for s in circuit_breaker_registry.all_status()
        if s.state == CircuitState.OPEN
    ]
    return BreakerResponse(data={
        "subsystem": "circuit_breaker",
        "total_breakers": total,
        "open_count": len(open_breakers),
        "open_breakers": [s.name for s in open_breakers],
        "healthy": len(open_breakers) == 0,
    })
