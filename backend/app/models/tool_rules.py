"""
tool_rules.py — 工具规则数据模型

定义 ToolRuleDef（规则定义）、PreCondition / PostCondition（前置/后置条件）、
BoundaryHandler（边界处理策略）、CostDeclaration（成本声明）、
ValidationResult（验证结果）、ToolRuleStats（全局统计）。
"""

from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any, Callable


# ── 条件类型 ─────────────────────────────────


class ConditionOperator(str, Enum):
    """条件操作符枚举"""
    EQ = "eq"               # 等于
    NE = "ne"               # 不等于
    GT = "gt"               # 大于
    GE = "ge"               # 大于等于
    LT = "lt"               # 小于
    LE = "le"               # 小于等于
    IN = "in"               # 在集合中
    NOT_IN = "not_in"       # 不在集合中
    CONTAINS = "contains"   # 包含子串
    MATCHES = "matches"     # 正则匹配
    IS_NONE = "is_none"     # 是否为 None
    IS_NOT_NONE = "is_not_none"  # 是否不为 None
    CUSTOM = "custom"       # 自定义验证函数


class ConditionSeverity(str, Enum):
    """条件严重级别"""
    ERROR = "error"         # 检查失败则抛出异常
    WARNING = "warning"     # 检查失败仅记录警告
    SKIP = "skip"           # 检查失败则跳过工具执行


# ── 前置 / 后置条件 ─────────────────────────


class PreCondition:
    """
    前置条件定义。

    Attributes:
        name: 条件名称（唯一标识）
        description: 人类可读描述
        param: 检查的参数名称（如 input_text, user_id）
        operator: 条件操作符
        expected: 期望值
        severity: 失败时的处理级别
        custom_fn: 自定义验证函数（operator=CUSTOM 时使用）
        error_message: 自定义错误消息模板
    """

    def __init__(
        self,
        name: str,
        description: str,
        param: str,
        operator: ConditionOperator = ConditionOperator.NE,
        expected: Any = None,
        severity: ConditionSeverity = ConditionSeverity.ERROR,
        custom_fn: Callable[[Any], bool] | None = None,
        error_message: str | None = None,
    ):
        self.name: str = name
        self.description: str = description
        self.param: str = param
        self.operator: ConditionOperator = operator
        self.expected: Any = expected
        self.severity: ConditionSeverity = severity
        self.custom_fn: Callable[[Any], bool] | None = custom_fn
        self.error_message: str | None = error_message

    def check(self, value: Any) -> tuple[bool, str]:
        """
        检查条件是否满足。

        Returns:
            (passed: bool, message: str)
        """
        if self.operator == ConditionOperator.CUSTOM and self.custom_fn:
            passed = self.custom_fn(value)
            return passed, "" if passed else (self.error_message or f"自定义前置条件 '{self.name}' 检查失败")

        if self.operator == ConditionOperator.IS_NONE:
            passed = value is None
            return passed, "" if passed else (self.error_message or f"参数 '{self.param}' 应为 None，实际为非 None")
        if self.operator == ConditionOperator.IS_NOT_NONE:
            passed = value is not None
            return passed, "" if passed else (self.error_message or f"参数 '{self.param}' 不应为 None")

        try:
            if self.operator == ConditionOperator.EQ:
                passed = value == self.expected
            elif self.operator == ConditionOperator.NE:
                passed = value != self.expected
            elif self.operator == ConditionOperator.GT:
                passed = value > self.expected
            elif self.operator == ConditionOperator.GE:
                passed = value >= self.expected
            elif self.operator == ConditionOperator.LT:
                passed = value < self.expected
            elif self.operator == ConditionOperator.LE:
                passed = value <= self.expected
            elif self.operator == ConditionOperator.IN:
                passed = value in (self.expected or [])
            elif self.operator == ConditionOperator.NOT_IN:
                passed = value not in (self.expected or [])
            elif self.operator == ConditionOperator.CONTAINS:
                passed = self.expected in value if isinstance(value, (str, list, dict, tuple)) else False
            elif self.operator == ConditionOperator.MATCHES:
                import re
                passed = bool(re.match(str(self.expected or ""), str(value)))
            else:
                passed = True
        except (TypeError, ValueError) as e:
            return False, f"前置条件 '{self.name}' 检查异常: {e}"

        if not passed:
            msg = self.error_message or (
                f"前置条件 '{self.name}' 检查失败: "
                f"参数 '{self.param}' (值={value!r}) "
                f"不满足 {self.operator.value} {self.expected!r}"
            )
            return False, msg
        return True, ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "param": self.param,
            "operator": self.operator.value,
            "expected": self.expected,
            "severity": self.severity.value,
            "error_message": self.error_message,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> PreCondition:
        return PreCondition(
            name=data["name"],
            description=data.get("description", ""),
            param=data["param"],
            operator=ConditionOperator(data.get("operator", "ne")),
            expected=data.get("expected"),
            severity=ConditionSeverity(data.get("severity", "error")),
            error_message=data.get("error_message"),
        )

    def __repr__(self) -> str:
        return f"<PreCondition '{self.name}' {self.param} {self.operator.value} {self.expected!r}>"


class PostCondition:
    """
    后置条件定义。

    Attributes:
        name: 条件名称（唯一标识）
        description: 人类可读描述
        operator: 条件操作符
        expected: 期望值
        severity: 失败时的处理级别
        custom_fn: 自定义验证函数（operator=CUSTOM 时使用），签名: def fn(result: Any) -> bool
        error_message: 自定义错误消息模板
    """

    def __init__(
        self,
        name: str,
        description: str,
        operator: ConditionOperator = ConditionOperator.IS_NOT_NONE,
        expected: Any = None,
        severity: ConditionSeverity = ConditionSeverity.ERROR,
        custom_fn: Callable[[Any], bool] | None = None,
        error_message: str | None = None,
    ):
        self.name: str = name
        self.description: str = description
        self.operator: ConditionOperator = operator
        self.expected: Any = expected
        self.severity: ConditionSeverity = severity
        self.custom_fn: Callable[[Any], bool] | None = custom_fn
        self.error_message: str | None = error_message

    def check(self, result: Any) -> tuple[bool, str]:
        """检查后置条件是否满足。"""
        if self.operator == ConditionOperator.CUSTOM and self.custom_fn:
            passed = self.custom_fn(result)
            return passed, "" if passed else (self.error_message or f"自定义后置条件 '{self.name}' 检查失败")

        if self.operator == ConditionOperator.IS_NONE:
            passed = result is None
            return passed, "" if passed else (self.error_message or f"后置条件 '{self.name}' 检查失败: 结果应为 None")
        if self.operator == ConditionOperator.IS_NOT_NONE:
            passed = result is not None
            return passed, "" if passed else (self.error_message or f"后置条件 '{self.name}' 检查失败: 结果为 None")

        try:
            if self.operator == ConditionOperator.EQ:
                passed = result == self.expected
            elif self.operator == ConditionOperator.NE:
                passed = result != self.expected
            elif self.operator == ConditionOperator.GT:
                passed = result > self.expected
            elif self.operator == ConditionOperator.GE:
                passed = result >= self.expected
            elif self.operator == ConditionOperator.LT:
                passed = result < self.expected
            elif self.operator == ConditionOperator.LE:
                passed = result <= self.expected
            elif self.operator == ConditionOperator.CONTAINS:
                passed = self.expected in result if result is not None else False
            elif self.operator == ConditionOperator.MATCHES:
                import re
                passed = bool(re.match(str(self.expected or ""), str(result or "")))
            else:
                passed = True
        except (TypeError, ValueError) as e:
            return False, f"后置条件 '{self.name}' 检查异常: {e}"

        if not passed:
            msg = self.error_message or (
                f"后置条件 '{self.name}' 检查失败: "
                f"结果值={result!r} 不满足 {self.operator.value} {self.expected!r}"
            )
            return False, msg
        return True, ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "operator": self.operator.value,
            "expected": self.expected,
            "severity": self.severity.value,
            "error_message": self.error_message,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> PostCondition:
        return PostCondition(
            name=data["name"],
            description=data.get("description", ""),
            operator=ConditionOperator(data.get("operator", "is_not_none")),
            expected=data.get("expected"),
            severity=ConditionSeverity(data.get("severity", "error")),
            error_message=data.get("error_message"),
        )

    def __repr__(self) -> str:
        return f"<PostCondition '{self.name}' {self.operator.value} {self.expected!r}>"


# ── 边界处理策略 ─────────────────────────


class BoundaryAction(str, Enum):
    """边界动作枚举"""
    CLAMP = "clamp"             # 钳制到合法范围
    ROUND = "round"             # 四舍五入
    TRUNCATE = "truncate"       # 截断
    REJECT = "reject"           # 拒绝执行
    FALLBACK = "fallback"       # 使用默认值回退
    WARN = "warn"               # 仅记录警告，不做修改


class BoundaryHandler:
    """
    边界处理策略定义。

    Attributes:
        name: 策略名称
        description: 描述
        param: 目标参数名
        min_value: 最小值（数值类型）
        max_value: 最大值（数值类型）
        max_length: 最大长度（字符串/列表类型）
        min_length: 最小长度（字符串/列表类型）
        allowed_values: 允许值集合
        action: 超界时执行的动作
        fallback_value: 回退值
        warn_message: 自定义警告/错误消息
    """

    def __init__(
        self,
        name: str,
        description: str,
        param: str,
        min_value: float | None = None,
        max_value: float | None = None,
        max_length: int | None = None,
        min_length: int | None = None,
        allowed_values: list[Any] | None = None,
        action: BoundaryAction = BoundaryAction.WARN,
        fallback_value: Any = None,
        warn_message: str | None = None,
    ):
        self.name: str = name
        self.description: str = description
        self.param: str = param
        self.min_value: float | None = min_value
        self.max_value: float | None = max_value
        self.max_length: int | None = max_length
        self.min_length: int | None = min_length
        self.allowed_values: list[Any] | None = allowed_values
        self.action: BoundaryAction = action
        self.fallback_value: Any = fallback_value
        self.warn_message: str | None = warn_message

    def apply(self, value: Any) -> tuple[Any, str | None]:
        """
        应用边界处理策略。

        Returns:
            (processed_value: Any, warning: str | None)

        示例：
            handler = BoundaryHandler("max_len", "截断文本", param="text", max_length=100, action=BoundaryAction.TRUNCATE)
            result, warn = handler.apply(long_text)  # result 被截断
        """
        warning = None
        original = value

        # 数值边界检查
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                if self.action == BoundaryAction.CLAMP:
                    value = self.min_value
                elif self.action == BoundaryAction.REJECT:
                    return None, self.warn_message or f"数值 {value} 低于最小值 {self.min_value}"
                elif self.action == BoundaryAction.FALLBACK:
                    value = self.fallback_value
                warning = self.warn_message or f"数值 {value} 低于最小值 {self.min_value}，已处理"

            if self.max_value is not None and value > self.max_value:
                if self.action == BoundaryAction.CLAMP:
                    value = self.max_value
                elif self.action == BoundaryAction.REJECT:
                    return None, self.warn_message or f"数值 {value} 超过最大值 {self.max_value}"
                elif self.action == BoundaryAction.FALLBACK:
                    value = self.fallback_value
                elif self.action == BoundaryAction.ROUND:
                    value = round(value, 0)
                warning = self.warn_message or f"数值 {value} 超过最大值 {self.max_value}，已处理"

        # 字符串/列表长度检查
        if isinstance(value, (str, list)):
            if self.max_length is not None and len(value) > self.max_length:
                if self.action == BoundaryAction.TRUNCATE:
                    value = value[:self.max_length]
                elif self.action == BoundaryAction.REJECT:
                    return None, self.warn_message or f"长度 {len(value)} 超过最大长度 {self.max_length}"
                elif self.action == BoundaryAction.FALLBACK:
                    value = self.fallback_value
                warning = self.warn_message or f"长度 {len(value)} 超过最大长度 {self.max_length}，已截断"

            if self.min_length is not None and len(value) < self.min_length:
                if self.action == BoundaryAction.REJECT:
                    return None, self.warn_message or f"长度 {len(value)} 低于最小长度 {self.min_length}"
                elif self.action == BoundaryAction.FALLBACK:
                    value = self.fallback_value
                warning = self.warn_message or f"长度 {len(value)} 低于最小长度 {self.min_length}，已处理"

        # 允许值检查
        if self.allowed_values is not None and value not in self.allowed_values:
            if self.action == BoundaryAction.REJECT:
                return None, self.warn_message or f"值 {value!r} 不在允许值集合 {self.allowed_values} 中"
            elif self.action == BoundaryAction.FALLBACK:
                value = self.fallback_value
                warning = self.warn_message or f"值 {value!r} 不在允许值集合中，使用回退值"

        return value, warning

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "param": self.param,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "max_length": self.max_length,
            "min_length": self.min_length,
            "allowed_values": self.allowed_values,
            "action": self.action.value,
            "fallback_value": self.fallback_value,
            "warn_message": self.warn_message,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> BoundaryHandler:
        return BoundaryHandler(
            name=data["name"],
            description=data.get("description", ""),
            param=data["param"],
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
            max_length=data.get("max_length"),
            min_length=data.get("min_length"),
            allowed_values=data.get("allowed_values"),
            action=BoundaryAction(data.get("action", "warn")),
            fallback_value=data.get("fallback_value"),
            warn_message=data.get("warn_message"),
        )

    def __repr__(self) -> str:
        return f"<BoundaryHandler '{self.name}' action={self.action.value}>"


# ── 成本声明 ─────────────────────────────


class CostUnit(str, Enum):
    """成本单位枚举"""
    TOKENS = "tokens"               # Token 数（LLM）
    REQUESTS = "requests"           # API 请求次数
    CREDITS = "credits"             # 积分
    SECONDS = "seconds"             # 秒（计算时间）
    BYTES = "bytes"                 # 字节（存储/带宽）
    DOLLARS = "dollars"             # 美元（货币）


class CostDeclaration:
    """
    工具成本声明定义。

    Attributes:
        name: 声明名称
        description: 描述
        unit: 成本单位
        estimated_amount: 预估消耗量
        max_amount: 单次调用最大消耗量（上限）
        currency: 货币单位（仅 DOLLARS 时使用）
        warn_threshold: 警告阈值（比例 0.0~1.0）
        metadata: 附加元数据
    """

    def __init__(
        self,
        name: str,
        description: str,
        unit: CostUnit = CostUnit.TOKENS,
        estimated_amount: float = 0.0,
        max_amount: float | None = None,
        currency: str = "CNY",
        warn_threshold: float = 0.8,
        metadata: dict[str, Any] | None = None,
    ):
        if warn_threshold < 0.0 or warn_threshold > 1.0:
            raise ValueError("warn_threshold 必须在 0.0 ~ 1.0 范围内")

        self.name: str = name
        self.description: str = description
        self.unit: CostUnit = unit
        self.estimated_amount: float = estimated_amount
        self.max_amount: float | None = max_amount
        self.currency: str = currency
        self.warn_threshold: float = warn_threshold
        self.metadata: dict[str, Any] = metadata or {}

    def check_cost(self, actual_amount: float) -> tuple[bool, str]:
        """
        检查实际消耗是否在声明范围内。

        Returns:
            (within_budget: bool, message: str)
        """
        if self.max_amount is not None and actual_amount > self.max_amount:
            return False, (
                f"消耗 {actual_amount:.2f} {self.unit.value} "
                f"超过声明上限 {self.max_amount:.2f} {self.unit.value}"
            )

        if self.max_amount is not None:
            ratio = actual_amount / self.max_amount
            if ratio >= self.warn_threshold:
                return True, (
                    f"消耗预警: {actual_amount:.2f}/{self.max_amount:.2f} "
                    f"{self.unit.value} ({ratio:.1%} ≥ 阈值 {self.warn_threshold:.0%})"
                )

        return True, ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "unit": self.unit.value,
            "estimated_amount": self.estimated_amount,
            "max_amount": self.max_amount,
            "currency": self.currency,
            "warn_threshold": self.warn_threshold,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CostDeclaration:
        return CostDeclaration(
            name=data["name"],
            description=data.get("description", ""),
            unit=CostUnit(data.get("unit", "tokens")),
            estimated_amount=data.get("estimated_amount", 0.0),
            max_amount=data.get("max_amount"),
            currency=data.get("currency", "CNY"),
            warn_threshold=data.get("warn_threshold", 0.8),
            metadata=data.get("metadata"),
        )

    def __repr__(self) -> str:
        return (
            f"<CostDeclaration '{self.name}' "
            f"~{self.estimated_amount} {self.unit.value}>"
        )


# ── 规则定义 ─────────────────────────────


class ToolRuleDef:
    """
    工具规则定义——封装一组前置条件、后置条件、边界处理策略和成本声明。

    Attributes:
        tool_name: 工具名称（唯一标识）
        description: 工具描述（嵌入前置/后置条件、边界处理、成本声明信息）
        pre_conditions: 前置条件列表
        post_conditions: 后置条件列表
        boundary_handlers: 边界处理策略列表
        cost_declarations: 成本声明列表
        enabled: 是否启用规则检查
        metadata: 附加元数据
        created_at: 创建时间戳
        updated_at: 更新时间戳
    """

    def __init__(
        self,
        tool_name: str,
        description: str = "",
        pre_conditions: list[PreCondition] | None = None,
        post_conditions: list[PostCondition] | None = None,
        boundary_handlers: list[BoundaryHandler] | None = None,
        cost_declarations: list[CostDeclaration] | None = None,
        enabled: bool = True,
        metadata: dict[str, Any] | None = None,
    ):
        self.tool_name: str = tool_name
        self.description: str = description
        self.pre_conditions: list[PreCondition] = pre_conditions or []
        self.post_conditions: list[PostCondition] = post_conditions or []
        self.boundary_handlers: list[BoundaryHandler] = boundary_handlers or []
        self.cost_declarations: list[CostDeclaration] = cost_declarations or []
        self.enabled: bool = enabled
        self.metadata: dict[str, Any] = metadata or {}
        now = time.time()
        self.created_at: float = now
        self.updated_at: float = now

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "description": self.description,
            "pre_conditions": [c.to_dict() for c in self.pre_conditions],
            "post_conditions": [c.to_dict() for c in self.post_conditions],
            "boundary_handlers": [h.to_dict() for h in self.boundary_handlers],
            "cost_declarations": [c.to_dict() for c in self.cost_declarations],
            "enabled": self.enabled,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @property
    def description_with_rules(self) -> str:
        """
        生成嵌入规则的描述文本（用于 LLM 工具描述的自动增强）。
        """
        parts = [self.description]

        if self.pre_conditions:
            parts.append("\n[前置条件]")
            for c in self.pre_conditions:
                parts.append(f"  - {c.description} ({c.severity.value})")

        if self.post_conditions:
            parts.append("\n[后置条件]")
            for c in self.post_conditions:
                parts.append(f"  - {c.description} ({c.severity.value})")

        if self.boundary_handlers:
            parts.append("\n[边界处理]")
            for h in self.boundary_handlers:
                parts.append(f"  - {h.description}")

        if self.cost_declarations:
            parts.append("\n[成本声明]")
            for c in self.cost_declarations:
                parts.append(f"  - {c.description} (~{c.estimated_amount} {c.unit.value})")

        return "\n".join(parts)

    def __repr__(self) -> str:
        return (
            f"<ToolRuleDef '{self.tool_name}' "
            f"pre={len(self.pre_conditions)} "
            f"post={len(self.post_conditions)} "
            f"boundary={len(self.boundary_handlers)} "
            f"cost={len(self.cost_declarations)}>"
        )


# ── 验证结果 ─────────────────────────────


class ValidationResult:
    """
    单次规则验证结果。

    Attributes:
        rule_def: 关联的规则定义
        passed: 是否通过所有检查
        pre_check_results: 前置条件检查结果
        post_check_results: 后置条件检查结果
        boundary_warnings: 边界处理警告
        cost_check_results: 成本检查结果
        error: 错误信息（如有）
        timing_ms: 验证耗时（毫秒）
        timestamp: 验证时间戳
    """

    def __init__(
        self,
        rule_def: ToolRuleDef,
        passed: bool = True,
        pre_check_results: list[tuple[str, bool, str]] | None = None,
        post_check_results: list[tuple[str, bool, str]] | None = None,
        boundary_warnings: list[str] | None = None,
        cost_check_results: list[tuple[str, bool, str]] | None = None,
        error: str | None = None,
        timing_ms: float = 0.0,
    ):
        self.rule_def: ToolRuleDef = rule_def
        self.passed: bool = passed
        self.pre_check_results: list[tuple[str, bool, str]] = pre_check_results or []
        self.post_check_results: list[tuple[str, bool, str]] = post_check_results or []
        self.boundary_warnings: list[str] = boundary_warnings or []
        self.cost_check_results: list[tuple[str, bool, str]] = cost_check_results or []
        self.error: str | None = error
        self.timing_ms: float = timing_ms
        self.timestamp: float = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.rule_def.tool_name,
            "passed": self.passed,
            "pre_check_results": [
                {"name": n, "passed": p, "message": m}
                for n, p, m in self.pre_check_results
            ],
            "post_check_results": [
                {"name": n, "passed": p, "message": m}
                for n, p, m in self.post_check_results
            ],
            "boundary_warnings": self.boundary_warnings,
            "cost_check_results": [
                {"name": n, "passed": p, "message": m}
                for n, p, m in self.cost_check_results
            ],
            "error": self.error,
            "timing_ms": round(self.timing_ms, 2),
            "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:
        return (
            f"<ValidationResult '{self.rule_def.tool_name}' "
            f"passed={self.passed} "
            f"timing={self.timing_ms:.1f}ms>"
        )


# ── 全局统计 ─────────────────────────────


class ToolRuleStats:
    """
    工具规则系统全局统计。

    Attributes:
        total_rules: 总规则数
        enabled_rules: 启用规则数
        total_validations: 总验证次数
        passed_validations: 通过次数
        failed_validations: 失败次数
        boundary_triggers: 边界触发次数
        cost_warnings: 成本预警次数
        total_timing_ms: 总耗时（毫秒）
        last_validation_timestamp: 最近验证时间戳
    """

    def __init__(self):
        self.total_rules: int = 0
        self.enabled_rules: int = 0
        self.total_validations: int = 0
        self.passed_validations: int = 0
        self.failed_validations: int = 0
        self.boundary_triggers: int = 0
        self.cost_warnings: int = 0
        self.total_timing_ms: float = 0.0
        self.last_validation_timestamp: float | None = None

    def record(self, result: ValidationResult) -> None:
        """记录一次验证结果到统计。"""
        self.total_validations += 1
        if result.passed:
            self.passed_validations += 1
        else:
            self.failed_validations += 1
        self.boundary_triggers += len(result.boundary_warnings)
        cost_warn_count = sum(1 for _, p, _ in result.cost_check_results if not p)
        self.cost_warnings += cost_warn_count
        self.total_timing_ms += result.timing_ms
        self.last_validation_timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        avg_timing = 0.0
        if self.total_validations > 0:
            avg_timing = self.total_timing_ms / self.total_validations

        return {
            "total_rules": self.total_rules,
            "enabled_rules": self.enabled_rules,
            "total_validations": self.total_validations,
            "passed_validations": self.passed_validations,
            "failed_validations": self.failed_validations,
            "pass_rate": round(
                self.passed_validations / max(self.total_validations, 1), 4
            ),
            "boundary_triggers": self.boundary_triggers,
            "cost_warnings": self.cost_warnings,
            "average_timing_ms": round(avg_timing, 2),
            "total_timing_ms": round(self.total_timing_ms, 2),
            "last_validation_timestamp": self.last_validation_timestamp,
        }

    def __repr__(self) -> str:
        return (
            f"<ToolRuleStats rules={self.total_rules} "
            f"validations={self.total_validations} "
            f"pass_rate={self.passed_validations / max(self.total_validations, 1):.0%}>"
        )
