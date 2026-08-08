"""
token_budget_router.py — Token 预算指令系统 API (FastAPI)

API:
  GET    /api/token-budget/status              — 所有预算规则状态列表
  GET    /api/token-budget/status/{name}       — 指定预算规则状态详情
  POST   /api/token-budget/estimate            — 估算指令 Token 用量
  POST   /api/token-budget/process             — 执行指令并应用预算控制
  GET    /api/token-budget/quota               — 获取所有预算配额概览
  GET    /api/token-budget/quota/{name}        — 获取指定预算配额详情
  POST   /api/token-budget/create              — 创建自定义预算规则
  DELETE /api/token-budget/reset/{name}        — 重置指定预算用量
  DELETE /api/token-budget/reset               — 重置所有预算用量
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Optional

from app.middleware.rbac import require_permission
from app.services.token_budget import (
    token_budget_registry,
    TokenBudget,
    TokenBudgetRegistry,
    estimate_tokens,
    estimate_instruction_tokens,
)
from app.models.token_budget import (
    DegradeStrategy,
    TokenBudgetRule,
    TokenBudgetStatus,
)

router = APIRouter(prefix="/api/token-budget", tags=["Token 预算指令系统"])


# ── 请求/响应模型 ──────────────────────────

class EstimateRequest(BaseModel):
    instruction: str = Field(..., description="指令文本")
    content: str = Field(default="", description="待处理内容（可选）")
    rule_name: str = Field(default="instruction_default", description="预算规则名称")


class EstimateResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: dict | list | None = None


class ProcessRequest(BaseModel):
    instruction: str = Field(..., description="指令文本")
    content: str = Field(default="", description="待处理内容")
    rule_name: str = Field(default="instruction_default", description="预算规则名称")


class CreateRuleRequest(BaseModel):
    name: str = Field(..., description="预算规则名称（唯一标识）")
    token_limit: int = Field(default=4096, ge=1, description="Token 预算上限")
    degrade_strategy: str = Field(default="truncate", description="超限降级策略 (truncate/downgrade/reject/warn_only)")
    warn_threshold: float = Field(default=0.8, gt=0.0, le=1.0, description="告警阈值比例 (0.0~1.0)")
    description: str = Field(default="", description="描述")
    tags: list[str] = Field(default=[], description="标签列表")
    model_mapping: dict[str, str] = Field(
        default={"full": "gpt-4", "lite": "gpt-3.5-turbo"},
        description="降级模型映射",
    )


class ResetResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: dict | None = None


class QuotaSummary(BaseModel):
    """预算配额概览"""
    name: str
    token_limit: int
    current_usage: int
    usage_ratio: float
    remaining_tokens: int
    is_warning: bool
    is_exceeded: bool
    degrade_strategy: str
    total_requests: int
    total_truncations: int
    total_downgrades: int


# ── 辅助函数 ──────────────────────────────

def _resolve_budget(rule_name: str) -> TokenBudget:
    """根据规则名称解析 TokenBudget 实例，不存在则返回默认"""
    budget = token_budget_registry.get(rule_name)
    if budget is None:
        # 使用默认规则
        budget = token_budget_registry.get_or_create(
            rule_name,
            TokenBudgetRule(name=rule_name),
        )
    return budget


# ── GET /status — 所有预算状态列表 ──────

@router.get("/status", response_model=EstimateResponse)
async def list_all_budgets(_: bool = Depends(require_permission("system:metrics"))):
    """获取所有预算规则的状态列表（修复 BUG-013：读操作 system:metrics）"""
    statuses = token_budget_registry.all_status()
    return EstimateResponse(data={
        "budgets": [s.to_dict() for s in statuses],
        "total": len(statuses),
    })


# ── GET /status/{name} — 指定预算状态 ──

@router.get("/status/{name}", response_model=EstimateResponse)
async def get_budget_status(name: str, _: bool = Depends(require_permission("system:metrics"))):
    """获取指定预算规则的详细状态（修复 BUG-013：读操作 system:metrics）"""
    budget = token_budget_registry.get(name)
    if budget is None:
        raise HTTPException(
            status_code=404,
            detail=f"预算规则 '{name}' 不存在",
        )
    return EstimateResponse(data=budget.get_status().to_dict())


# ── POST /estimate — 估算 Token 用量 ────

@router.post("/estimate", response_model=EstimateResponse)
async def estimate(req: EstimateRequest, _: bool = Depends(require_permission("system:metrics"))):
    """估算指令+内容的 Token 用量，并给出预算建议（修复 BUG-013：读操作 system:metrics）"""
    budget = _resolve_budget(req.rule_name)
    result = budget.estimate(req.instruction, req.content)
    return EstimateResponse(data=result)


# ── POST /process — 执行指令并应用预算 ──

@router.post("/process", response_model=EstimateResponse)
async def process_instruction(
    req: ProcessRequest,
    _: bool = Depends(require_permission("system:settings")),
):
    """执行指令，自动应用预算控制（截断/降级/拒绝）（修复 BUG-013：写操作 system:settings）"""
    budget = _resolve_budget(req.rule_name)
    result = budget.process(req.instruction, req.content)
    return EstimateResponse(
        message=f"处理完成: {result['status']}",
        data=result,
    )


# ── GET /quota — 所有预算配额概览 ──────

@router.get("/quota", response_model=EstimateResponse)
async def list_all_quotas(_: bool = Depends(require_permission("system:metrics"))):
    """获取所有预算规则的配额概览（修复 BUG-013：读操作 system:metrics）"""
    statuses = token_budget_registry.all_status()
    quotas = [
        QuotaSummary(
            name=s.name,
            token_limit=s.rule.token_limit,
            current_usage=s.current_usage,
            usage_ratio=s.usage_ratio,
            remaining_tokens=s.remaining_tokens,
            is_warning=s.is_warning,
            is_exceeded=s.is_exceeded,
            degrade_strategy=s.rule.degrade_strategy.value
            if isinstance(s.rule.degrade_strategy, DegradeStrategy)
            else s.rule.degrade_strategy,
            total_requests=s.total_requests,
            total_truncations=s.total_truncations,
            total_downgrades=s.total_downgrades,
        ).model_dump()
        for s in statuses
    ]
    return EstimateResponse(data={
        "quotas": quotas,
        "total": len(quotas),
        "summary": {
            "total_budgets": len(quotas),
            "total_exceeded": sum(1 for q in quotas if q["is_exceeded"]),
            "total_warning": sum(1 for q in quotas if q["is_warning"]),
        },
    })


# ── GET /quota/{name} — 指定预算配额 ──

@router.get("/quota/{name}", response_model=EstimateResponse)
async def get_quota(name: str, _: bool = Depends(require_permission("system:metrics"))):
    """获取指定预算规则的配额详情（修复 BUG-013：读操作 system:metrics）"""
    budget = token_budget_registry.get(name)
    if budget is None:
        raise HTTPException(
            status_code=404,
            detail=f"预算规则 '{name}' 不存在",
        )
    status = budget.get_status()
    quota = QuotaSummary(
        name=status.name,
        token_limit=status.rule.token_limit,
        current_usage=status.current_usage,
        usage_ratio=status.usage_ratio,
        remaining_tokens=status.remaining_tokens,
        is_warning=status.is_warning,
        is_exceeded=status.is_exceeded,
        degrade_strategy=status.rule.degrade_strategy.value
        if isinstance(status.rule.degrade_strategy, DegradeStrategy)
        else status.rule.degrade_strategy,
        total_requests=status.total_requests,
        total_truncations=status.total_truncations,
        total_downgrades=status.total_downgrades,
    )
    return EstimateResponse(data=quota.model_dump())


# ── POST /create — 创建自定义预算规则 ──

@router.post("/create", response_model=EstimateResponse)
async def create_budget_rule(
    req: CreateRuleRequest,
    _: bool = Depends(require_permission("system:settings")),
):
    """创建自定义 Token 预算规则（如果已存在则更新）（修复 BUG-013：写操作 system:settings）"""
    try:
        strategy = DegradeStrategy(req.degrade_strategy.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"无效的降级策略 '{req.degrade_strategy}'，可选: truncate, downgrade, reject, warn_only",
        )

    rule = TokenBudgetRule(
        name=req.name,
        token_limit=req.token_limit,
        degrade_strategy=strategy,
        warn_threshold=req.warn_threshold,
        description=req.description,
        tags=req.tags,
        model_mapping=req.model_mapping,
    )
    budget = token_budget_registry.create(req.name, rule)
    return EstimateResponse(
        message=f"预算规则 '{req.name}' 已创建/更新",
        data=budget.get_status().to_dict(),
    )


# ── DELETE /reset/{name} — 重置指定预算 ──

@router.delete("/reset/{name}", response_model=ResetResponse)
async def reset_budget(name: str, _: bool = Depends(require_permission("system:settings"))):
    """重置指定预算规则的用量计数（修复 BUG-013：写操作 system:settings）"""
    budget = token_budget_registry.get(name)
    if budget is None:
        raise HTTPException(
            status_code=404,
            detail=f"预算规则 '{name}' 不存在",
        )
    budget.reset()
    return ResetResponse(message=f"预算规则 '{name}' 已重置")


# ── DELETE /reset — 重置所有预算 ──────

@router.delete("/reset", response_model=ResetResponse)
async def reset_all_budgets(_: bool = Depends(require_permission("system:settings"))):
    """重置所有预算规则的用量计数（修复 BUG-013：写操作 system:settings）"""
    count = token_budget_registry.reset_all()
    return ResetResponse(
        message=f"已重置所有预算规则",
        data={"reset_count": count},
    )


# ── GET /health — 预算子系统健康检查（公开白名单，PUBLIC-BYPASS） ──

@router.get("/health", response_model=EstimateResponse)
# PUBLIC-BYPASS: 健康检查端点，设计上公开（BUG-013 P2 公开白名单登记）
async def token_budget_health():
    """Token 预算子系统健康检查（PUBLIC-BYPASS）"""
    statuses = token_budget_registry.all_status()
    exceeded = [s for s in statuses if s.is_exceeded]
    warning = [s for s in statuses if s.is_warning]
    return EstimateResponse(data={
        "subsystem": "token_budget",
        "total_rules": len(statuses),
        "exceeded_count": len(exceeded),
        "warning_count": len(warning),
        "exceeded_rules": [s.name for s in exceeded],
        "warning_rules": [s.name for s in warning],
        "healthy": len(exceeded) == 0,
        "overall_usage_ratio": max([s.usage_ratio for s in statuses], default=0.0),
    })
