"""
tool_rules_router.py — 工具规则管理 API (FastAPI)

API:
  GET    /api/tool-rules/rules            — 所有规则定义列表
  GET    /api/tool-rules/rules/{name}     — 指定规则定义详情
  POST   /api/tool-rules/validate         — 验证指定规则
  PUT    /api/tool-rules/rules/{name}     — 更新规则定义
  DELETE /api/tool-rules/rules/{name}     — 删除规则
  POST   /api/tool-rules/rules            — 创建新规则
  PATCH  /api/tool-rules/rules/{name}/toggle — 启用/禁用规则
  GET    /api/tool-rules/stats            — 全局统计
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Optional

from app.services.tool_rules import (
    ToolRuleDecorator,
    tool_rule_registry,
    validate_with_rules,
)
from app.models.tool_rules import (
    BoundaryAction,
    BoundaryHandler,
    ConditionOperator,
    ConditionSeverity,
    CostDeclaration,
    CostUnit,
    PostCondition,
    PreCondition,
    ToolRuleDef,
    ToolRuleStats,
    ValidationResult,
)

router = APIRouter(prefix="/api/tool-rules", tags=["工具规则管理"])


# ── 请求/响应模型 ──────────────────────────


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: dict | list | None = None


class PreConditionSchema(BaseModel):
    name: str = Field(..., description="条件名称（唯一标识）")
    description: str = Field(default="", description="人类可读描述")
    param: str = Field(..., description="检查的参数名称")
    operator: str = Field(default="ne", description="条件操作符 (eq, ne, gt, ge, lt, le, in, not_in, contains, matches, is_none, is_not_none, custom)")
    expected: Any = Field(default=None, description="期望值")
    severity: str = Field(default="error", description="失败处理级别 (error, warning, skip)")
    error_message: str | None = Field(default=None, description="自定义错误消息")


class PostConditionSchema(BaseModel):
    name: str = Field(..., description="条件名称（唯一标识）")
    description: str = Field(default="", description="人类可读描述")
    operator: str = Field(default="is_not_none", description="条件操作符")
    expected: Any = Field(default=None, description="期望值")
    severity: str = Field(default="error", description="失败处理级别")
    error_message: str | None = Field(default=None, description="自定义错误消息")


class BoundaryHandlerSchema(BaseModel):
    name: str = Field(..., description="策略名称")
    description: str = Field(default="", description="描述")
    param: str = Field(..., description="目标参数名")
    min_value: float | None = Field(default=None, description="最小值")
    max_value: float | None = Field(default=None, description="最大值")
    max_length: int | None = Field(default=None, description="最大长度")
    min_length: int | None = Field(default=None, description="最小长度")
    allowed_values: list[Any] | None = Field(default=None, description="允许值集合")
    action: str = Field(default="warn", description="超界动作 (clamp, round, truncate, reject, fallback, warn)")
    fallback_value: Any = Field(default=None, description="回退值")
    warn_message: str | None = Field(default=None, description="自定义警告消息")


class CostDeclarationSchema(BaseModel):
    name: str = Field(..., description="声明名称")
    description: str = Field(default="", description="描述")
    unit: str = Field(default="tokens", description="成本单位 (tokens, requests, credits, seconds, bytes, dollars)")
    estimated_amount: float = Field(default=0.0, description="预估消耗量")
    max_amount: float | None = Field(default=None, description="单次上限")
    currency: str = Field(default="CNY", description="货币单位")
    warn_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="预警阈值")


class CreateRuleRequest(BaseModel):
    tool_name: str = Field(..., description="工具名称（唯一标识）")
    description: str = Field(default="", description="工具描述")
    pre_conditions: list[PreConditionSchema] = Field(default=[], description="前置条件列表")
    post_conditions: list[PostConditionSchema] = Field(default=[], description="后置条件列表")
    boundary_handlers: list[BoundaryHandlerSchema] = Field(default=[], description="边界处理策略列表")
    cost_declarations: list[CostDeclarationSchema] = Field(default=[], description="成本声明列表")
    enabled: bool = Field(default=True, description="是否启用")


class UpdateRuleRequest(BaseModel):
    description: str | None = Field(default=None, description="工具描述")
    pre_conditions: list[PreConditionSchema] | None = Field(default=None, description="前置条件列表")
    post_conditions: list[PostConditionSchema] | None = Field(default=None, description="后置条件列表")
    boundary_handlers: list[BoundaryHandlerSchema] | None = Field(default=None, description="边界处理策略列表")
    cost_declarations: list[CostDeclarationSchema] | None = Field(default=None, description="成本声明列表")
    enabled: bool | None = Field(default=None, description="是否启用")


class ValidateRequest(BaseModel):
    tool_name: str = Field(..., description="工具名称")
    kwargs: dict[str, Any] = Field(default={}, description="函数参数（键值对）")
    result: Any = Field(default=None, description="函数结果（可选，用于后置条件检查）")


# ── GET /rules — 所有规则定义 ──────────


@router.get("/rules", response_model=ApiResponse)
async def list_all_rules(
    enabled_only: bool = Query(default=False, description="仅返回启用状态的规则"),
    tag: str | None = Query(default=None, description="按标签筛选"),
):
    """获取所有工具规则定义列表"""
    rules = tool_rule_registry.all_rules

    if enabled_only:
        rules = [r for r in rules if r.enabled]

    if tag:
        rules = [r for r in rules if tag in r.metadata.get("tags", [])]

    return ApiResponse(data={
        "rules": [r.to_dict() for r in rules],
        "total": len(rules),
    })


# ── GET /rules/{name} — 指定规则详情 ──


@router.get("/rules/{name}", response_model=ApiResponse)
async def get_rule_detail(name: str):
    """获取指定工具的规则定义详情"""
    rule = tool_rule_registry.get(name)
    if rule is None:
        raise HTTPException(
            status_code=404,
            detail=f"规则 '{name}' 不存在",
        )

    data = rule.to_dict()
    data["description_with_rules"] = rule.description_with_rules
    return ApiResponse(data=data)


# ── POST /rules — 创建新规则 ────────────


@router.post("/rules", response_model=ApiResponse)
async def create_rule(req: CreateRuleRequest):
    """创建新的工具规则定义（如果已存在则返回现有）"""
    existing = tool_rule_registry.get(req.tool_name)
    if existing:
        return ApiResponse(
            message=f"规则 '{req.tool_name}' 已存在，返回现有定义",
            data=existing.to_dict(),
        )

    rule_def = _build_rule_def(req)
    tool_rule_registry.register(rule_def)

    return ApiResponse(
        message=f"规则 '{req.tool_name}' 创建成功",
        data=rule_def.to_dict(),
    )


# ── PUT /rules/{name} — 更新规则 ────────


@router.put("/rules/{name}", response_model=ApiResponse)
async def update_rule(name: str, req: UpdateRuleRequest):
    """更新指定工具的规则定义"""
    existing = tool_rule_registry.get(name)
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=f"规则 '{name}' 不存在",
        )

    if req.description is not None:
        existing.description = req.description
    if req.enabled is not None:
        existing.enabled = req.enabled
    if req.pre_conditions is not None:
        existing.pre_conditions = [_build_pre_condition(s) for s in req.pre_conditions]
    if req.post_conditions is not None:
        existing.post_conditions = [_build_post_condition(s) for s in req.post_conditions]
    if req.boundary_handlers is not None:
        existing.boundary_handlers = [_build_boundary_handler(s) for s in req.boundary_handlers]
    if req.cost_declarations is not None:
        existing.cost_declarations = [_build_cost_declaration(s) for s in req.cost_declarations]

    import time
    existing.updated_at = time.time()

    return ApiResponse(
        message=f"规则 '{name}' 更新成功",
        data=existing.to_dict(),
    )


# ── DELETE /rules/{name} — 删除规则 ─────


@router.delete("/rules/{name}", response_model=ApiResponse)
async def delete_rule(name: str):
    """删除指定工具的规则定义"""
    success = tool_rule_registry.remove(name)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"规则 '{name}' 不存在",
        )
    return ApiResponse(message=f"规则 '{name}' 已删除")


# ── PATCH /rules/{name}/toggle — 启用/禁用 ──


@router.patch("/rules/{name}/toggle", response_model=ApiResponse)
async def toggle_rule(name: str, enabled: bool = Query(..., description="true=启用, false=禁用")):
    """启用或禁用指定工具的规则检查"""
    success = tool_rule_registry.enable(name) if enabled else tool_rule_registry.disable(name)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"规则 '{name}' 不存在",
        )
    state = "启用" if enabled else "禁用"
    return ApiResponse(message=f"规则 '{name}' 已{state}")


# ── POST /validate — 验证规则 ──────────


@router.post("/validate", response_model=ApiResponse)
async def validate_rule(req: ValidateRequest):
    """手动验证指定工具的规则"""
    rule_def = tool_rule_registry.get(req.tool_name)
    if rule_def is None:
        raise HTTPException(
            status_code=404,
            detail=f"规则 '{req.tool_name}' 不存在",
        )

    result = validate_with_rules(rule_def, req.kwargs, req.result)

    return ApiResponse(data={
        "validation": result.to_dict(),
        "passed": result.passed,
    })


# ── GET /stats — 全局统计 ──────────────


@router.get("/stats", response_model=ApiResponse)
async def get_stats():
    """获取工具规则系统全局统计信息"""
    tool_rule_registry.update_stats_from_rules()
    return ApiResponse(data={
        "stats": tool_rule_registry.stats.to_dict(),
        "wrapped_count": len([
            n for n in tool_rule_registry._wrapped_fns  # type: ignore[attr-defined]
        ]) if hasattr(tool_rule_registry, '_wrapped_fns') else 0,
    })


# ── GET /health — 健康检查 ──────────────


@router.get("/health", response_model=ApiResponse)
async def tool_rules_health():
    """工具规则子系统健康检查"""
    return ApiResponse(data={
        "subsystem": "tool_rules",
        "healthy": True,
        "total_rules": len(tool_rule_registry.all_rules),
    })


# ── 辅助构建函数 ─────────────────────────


def _build_pre_condition(s: PreConditionSchema) -> PreCondition:
    return PreCondition(
        name=s.name,
        description=s.description,
        param=s.param,
        operator=ConditionOperator(s.operator),
        expected=s.expected,
        severity=ConditionSeverity(s.severity),
        error_message=s.error_message,
    )


def _build_post_condition(s: PostConditionSchema) -> PostCondition:
    return PostCondition(
        name=s.name,
        description=s.description,
        operator=ConditionOperator(s.operator),
        expected=s.expected,
        severity=ConditionSeverity(s.severity),
        error_message=s.error_message,
    )


def _build_boundary_handler(s: BoundaryHandlerSchema) -> BoundaryHandler:
    return BoundaryHandler(
        name=s.name,
        description=s.description,
        param=s.param,
        min_value=s.min_value,
        max_value=s.max_value,
        max_length=s.max_length,
        min_length=s.min_length,
        allowed_values=s.allowed_values,
        action=BoundaryAction(s.action),
        fallback_value=s.fallback_value,
        warn_message=s.warn_message,
    )


def _build_cost_declaration(s: CostDeclarationSchema) -> CostDeclaration:
    return CostDeclaration(
        name=s.name,
        description=s.description,
        unit=CostUnit(s.unit),
        estimated_amount=s.estimated_amount,
        max_amount=s.max_amount,
        currency=s.currency,
        warn_threshold=s.warn_threshold,
    )


def _build_rule_def(req: CreateRuleRequest) -> ToolRuleDef:
    return ToolRuleDef(
        tool_name=req.tool_name,
        description=req.description,
        pre_conditions=[_build_pre_condition(p) for p in req.pre_conditions],
        post_conditions=[_build_post_condition(p) for p in req.post_conditions],
        boundary_handlers=[_build_boundary_handler(h) for h in req.boundary_handlers],
        cost_declarations=[_build_cost_declaration(c) for c in req.cost_declarations],
        enabled=req.enabled,
    )
