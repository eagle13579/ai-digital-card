"""
tool_rules.py — 工具使用规则装饰器核心

提供 ToolRuleDecorator 类，支持：
  - 前置条件检查（PreCondition）
  - 后置条件验证（PostCondition）
  - 成本声明与检查（CostDeclaration）
  - 边界处理策略（BoundaryHandler）
  - 工具描述自动增强（description_with_rules）
  - 异步和同步函数装饰
  - 全局注册表管理
  - 验证器（parse_rule_from_docstring / validate_with_rules）

用法:
    @tool_rule_registry.create("search_knowledge_base",
        description="搜索知识库。支持关键词和语义检索。",
        pre_conditions=[
            PreCondition("非空查询", "查询参数不能为空", param="query",
                         operator=ConditionOperator.IS_NOT_NONE),
        ],
        post_conditions=[
            PostCondition("非空结果", "结果不能为空", operator=ConditionOperator.IS_NOT_NONE),
        ],
        boundary_handlers=[
            BoundaryHandler("查询长度", "查询文本不超过500字", param="query",
                            max_length=500, action=BoundaryAction.TRUNCATE),
        ],
        cost_declarations=[
            CostDeclaration("嵌入成本", "每次查询消耗嵌入 Token",
                            unit=CostUnit.TOKENS, estimated_amount=150, max_amount=500),
        ],
    )
    async def search_knowledge_base(query: str) -> list[dict]:
        ...
"""

from __future__ import annotations
import asyncio
import functools
import logging
import re
import time
from typing import Any, Callable, TypeVar

from app.models.tool_rules import (
    BoundaryAction,
    BoundaryHandler,
    ConditionSeverity,
    CostDeclaration,
    CostUnit,
    PostCondition,
    PreCondition,
    ToolRuleDef,
    ToolRuleStats,
    ValidationResult,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ──────────────────────────────────────────────
# 规则验证异常
# ──────────────────────────────────────────────


class PreConditionError(Exception):
    """前置条件检查失败时抛出。"""
    pass


class PostConditionError(Exception):
    """后置条件检查失败时抛出。"""
    pass


class BoundaryRejectError(Exception):
    """边界处理拒绝执行时抛出。"""
    pass


class CostOverrunError(Exception):
    """成本超过声明上限时抛出。"""
    pass


# ──────────────────────────────────────────────
# 规则装饰器核心
# ──────────────────────────────────────────────


class ToolRuleDecorator:
    """
    工具规则装饰器——为工具函数附加规则检查层。

    用法:
        decorator = ToolRuleDecorator(rule_def)
        wrapped_fn = decorator(async_fn)
        result = await wrapped_fn(...)

    或通过装饰器语法:
        @ToolRuleDecorator(rule_def)
        async def my_tool(...): ...
    """

    def __init__(self, rule_def: ToolRuleDef):
        if not isinstance(rule_def, ToolRuleDef):
            raise TypeError("rule_def 必须是 ToolRuleDef 实例")
        self._rule_def: ToolRuleDef = rule_def

    @property
    def rule_def(self) -> ToolRuleDef:
        return self._rule_def

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """装饰器入口——自动检测 async/sync 并返回包装后的函数。"""

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await self._execute_async(func, *args, **kwargs)
            # 附加规则元数据到函数对象
            async_wrapper._tool_rule_decorator = self  # type: ignore[attr-defined]
            async_wrapper._tool_rule_def = self._rule_def  # type: ignore[attr-defined]
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                return self._execute_sync(func, *args, **kwargs)
            sync_wrapper._tool_rule_decorator = self  # type: ignore[attr-defined]
            sync_wrapper._tool_rule_def = self._rule_def  # type: ignore[attr-defined]
            return sync_wrapper

    # ── 执行流程 ──────────────────────────

    async def _execute_async(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """异步执行——前置检查 → 边界处理 → 执行 → 后置检查 → 成本记录"""
        start = time.time()
        result = None

        try:
            # 1. 前置条件检查
            pre_check_results = self._check_pre_conditions(kwargs)

            # 2. 边界处理
            boundary_warnings = self._apply_boundary_handlers(kwargs)

            # 3. 执行工具函数
            result = await func(*args, **kwargs)

            # 4. 后置条件检查
            post_check_results = self._check_post_conditions(result)

            # 5. 验证结果
            elapsed = (time.time() - start) * 1000
            all_passed = all(p for _, p, _ in pre_check_results) and all(p for _, p, _ in post_check_results)
            validation = ValidationResult(
                rule_def=self._rule_def,
                passed=all_passed,
                pre_check_results=pre_check_results,
                post_check_results=post_check_results,
                boundary_warnings=boundary_warnings,
                timing_ms=elapsed,
            )
            tool_rule_registry.record_validation(validation)

            # 如果后置条件有 ERROR 级别的失败，抛异常
            for name, passed, msg in post_check_results:
                if not passed:
                    pc = self._find_post_condition(name)
                    if pc and pc.severity == ConditionSeverity.ERROR:
                        raise PostConditionError(msg)

            return result

        except BoundaryRejectError:
            raise
        except PreConditionError:
            raise
        except PostConditionError:
            raise
        except CostOverrunError:
            raise
        except Exception as e:
            if not isinstance(e, (PreConditionError, PostConditionError, BoundaryRejectError, CostOverrunError)):
                elapsed = (time.time() - start) * 1000
                validation = ValidationResult(
                    rule_def=self._rule_def,
                    passed=False,
                    error=str(e),
                    timing_ms=elapsed,
                )
                tool_rule_registry.record_validation(validation)
            raise

    def _execute_sync(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """同步执行——前置检查 → 边界处理 → 执行 → 后置检查"""
        start = time.time()

        try:
            # 1. 前置条件检查
            pre_check_results = self._check_pre_conditions(kwargs)

            # 2. 边界处理
            boundary_warnings = self._apply_boundary_handlers(kwargs)

            # 3. 执行工具函数
            result = func(*args, **kwargs)

            # 4. 后置条件检查
            post_check_results = self._check_post_conditions(result)

            # 5. 验证结果
            elapsed = (time.time() - start) * 1000
            all_passed = all(p for _, p, _ in pre_check_results) and all(p for _, p, _ in post_check_results)
            validation = ValidationResult(
                rule_def=self._rule_def,
                passed=all_passed,
                pre_check_results=pre_check_results,
                post_check_results=post_check_results,
                boundary_warnings=boundary_warnings,
                timing_ms=elapsed,
            )
            tool_rule_registry.record_validation(validation)

            # 后置条件 ERROR 级别检查
            for name, passed, msg in post_check_results:
                if not passed:
                    pc = self._find_post_condition(name)
                    if pc and pc.severity == ConditionSeverity.ERROR:
                        raise PostConditionError(msg)

            return result

        except (PreConditionError, PostConditionError, BoundaryRejectError, CostOverrunError):
            raise
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            validation = ValidationResult(
                rule_def=self._rule_def,
                passed=False,
                error=str(e),
                timing_ms=elapsed,
            )
            tool_rule_registry.record_validation(validation)
            raise

    # ── 检查逻辑 ──────────────────────────

    def _check_pre_conditions(self, kwargs: dict[str, Any]) -> list[tuple[str, bool, str]]:
        """检查所有启用规则的前置条件。"""
        if not self._rule_def.enabled:
            return []

        results: list[tuple[str, bool, str]] = []
        for cond in self._rule_def.pre_conditions:
            value = kwargs.get(cond.param)
            passed, msg = cond.check(value)

            if not passed:
                if cond.severity == ConditionSeverity.ERROR:
                    raise PreConditionError(msg)
                elif cond.severity == ConditionSeverity.WARNING:
                    logger.warning("前置条件警告 [%s]: %s", self._rule_def.tool_name, msg)

            results.append((cond.name, passed, msg))

        return results

    def _check_post_conditions(self, result: Any) -> list[tuple[str, bool, str]]:
        """检查所有后置条件。"""
        if not self._rule_def.enabled:
            return []

        results: list[tuple[str, bool, str]] = []
        for cond in self._rule_def.post_conditions:
            passed, msg = cond.check(result)

            if not passed:
                if cond.severity == ConditionSeverity.WARNING:
                    logger.warning("后置条件警告 [%s]: %s", self._rule_def.tool_name, msg)
                # ERROR 级别在后置统一检查阶段再抛异常（以便收集所有结果）

            results.append((cond.name, passed, msg))

        return results

    def _apply_boundary_handlers(self, kwargs: dict[str, Any]) -> list[str]:
        """应用边界处理策略到 kwargs，原地修改。"""
        if not self._rule_def.enabled:
            return []

        warnings: list[str] = []
        for handler in self._rule_def.boundary_handlers:
            if handler.param not in kwargs:
                continue
            value = kwargs[handler.param]
            processed, warning = handler.apply(value)

            if handler.action == BoundaryAction.REJECT and processed is None:
                raise BoundaryRejectError(warning or f"边界处理拒绝: {handler.name}")

            if warning:
                logger.warning("边界处理 [%s]: %s", self._rule_def.tool_name, warning)
                warnings.append(warning)

            # 更新 kwargs（如果处理后的值不同）
            kwargs[handler.param] = processed

        return warnings

    def _find_post_condition(self, name: str) -> PostCondition | None:
        """按名称查找后置条件。"""
        for c in self._rule_def.post_conditions:
            if c.name == name:
                return c
        return None


# ──────────────────────────────────────────────
# 规则注册表（全局单例管理）
# ──────────────────────────────────────────────


class ToolRuleRegistry:
    """
    全局规则注册表——管理所有 ToolRuleDef 和已包装的函数。

    用法:
        registry = ToolRuleRegistry()

        # 创建并注册规则
        @registry.create("search_tool",
            description="搜索工具",
            pre_conditions=[...],
            post_conditions=[...],
        )
        async def search(...): ...

        # 手动注册
        rule = ToolRuleDef(tool_name="my_tool", ...)
        registry.register(rule)
        decorated = ToolRuleDecorator(rule)(my_func)
        registry.register_wrapped("my_tool", decorated)
    """

    def __init__(self):
        self._rules: dict[str, ToolRuleDef] = {}
        self._wrapped_fns: dict[str, Callable[..., Any]] = {}
        self._stats: ToolRuleStats = ToolRuleStats()

    # ── 属性 ──────────────────────────────

    @property
    def stats(self) -> ToolRuleStats:
        """获取全局统计。"""
        return self._stats

    @property
    def all_rules(self) -> list[ToolRuleDef]:
        """获取所有规则定义。"""
        return list(self._rules.values())

    # ── 注册 ──────────────────────────────

    def register(self, rule_def: ToolRuleDef) -> ToolRuleDef:
        """注册一个规则定义。"""
        if rule_def.tool_name in self._rules:
            logger.warning("规则 '%s' 已存在，将被覆盖", rule_def.tool_name)
        self._rules[rule_def.tool_name] = rule_def
        self._stats.total_rules = len(self._rules)
        self._stats.enabled_rules = sum(1 for r in self._rules.values() if r.enabled)
        logger.info("规则注册表: 注册 '%s' (%d 前置, %d 后置, %d 边界, %d 成本)",
                     rule_def.tool_name,
                     len(rule_def.pre_conditions),
                     len(rule_def.post_conditions),
                     len(rule_def.boundary_handlers),
                     len(rule_def.cost_declarations))
        return rule_def

    def register_wrapped(self, tool_name: str, wrapped_fn: Callable[..., Any]) -> None:
        """注册已包装的函数。"""
        self._wrapped_fns[tool_name] = wrapped_fn

    def create(
        self,
        tool_name: str,
        description: str = "",
        pre_conditions: list[PreCondition] | None = None,
        post_conditions: list[PostCondition] | None = None,
        boundary_handlers: list[BoundaryHandler] | None = None,
        cost_declarations: list[CostDeclaration] | None = None,
        enabled: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        装饰器工厂——创建规则定义并立即装饰函数。

        用法:
            @registry.create("my_tool", description="...", pre_conditions=[...])
            async def my_tool(...): ...
        """
        rule_def = ToolRuleDef(
            tool_name=tool_name,
            description=description,
            pre_conditions=pre_conditions or [],
            post_conditions=post_conditions or [],
            boundary_handlers=boundary_handlers or [],
            cost_declarations=cost_declarations or [],
            enabled=enabled,
            metadata=metadata,
        )
        self.register(rule_def)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            decorator_instance = ToolRuleDecorator(rule_def)
            wrapped = decorator_instance(func)
            self.register_wrapped(tool_name, wrapped)
            return wrapped

        return decorator

    # ── 查询 ──────────────────────────────

    def get(self, tool_name: str) -> ToolRuleDef | None:
        """获取指定工具的规则定义。"""
        return self._rules.get(tool_name)

    def get_wrapped(self, tool_name: str) -> Callable[..., Any] | None:
        """获取指定工具的包装函数。"""
        return self._wrapped_fns.get(tool_name)

    def get_or_create(self, tool_name: str, **kwargs: Any) -> ToolRuleDef:
        """获取或创建规则定义。"""
        existing = self.get(tool_name)
        if existing:
            return existing
        rule_def = ToolRuleDef(tool_name=tool_name, **kwargs)
        return self.register(rule_def)

    # ── 管理 ──────────────────────────────

    def enable(self, tool_name: str) -> bool:
        """启用指定工具的规则检查。"""
        rule = self.get(tool_name)
        if rule is None:
            return False
        rule.enabled = True
        rule.updated_at = time.time()
        self._stats.enabled_rules = sum(1 for r in self._rules.values() if r.enabled)
        return True

    def disable(self, tool_name: str) -> bool:
        """禁用指定工具的规则检查。"""
        rule = self.get(tool_name)
        if rule is None:
            return False
        rule.enabled = False
        rule.updated_at = time.time()
        self._stats.enabled_rules = sum(1 for r in self._rules.values() if r.enabled)
        return True

    def remove(self, tool_name: str) -> bool:
        """移除指定工具的规则定义和包装函数。"""
        existed = False
        if tool_name in self._rules:
            del self._rules[tool_name]
            existed = True
        if tool_name in self._wrapped_fns:
            del self._wrapped_fns[tool_name]
        if existed:
            self._stats.total_rules = len(self._rules)
            self._stats.enabled_rules = sum(1 for r in self._rules.values() if r.enabled)
            logger.info("规则注册表: 移除 '%s'", tool_name)
        return existed

    def clear(self) -> None:
        """清空所有规则。"""
        self._rules.clear()
        self._wrapped_fns.clear()
        self._stats.total_rules = 0
        self._stats.enabled_rules = 0
        logger.info("规则注册表: 已清空")

    # ── 验证记录 ──────────────────────────

    def record_validation(self, result: ValidationResult) -> None:
        """记录验证结果到全局统计。"""
        self._stats.record(result)

    def update_stats_from_rules(self) -> None:
        """从当前规则集更新统计信息。"""
        self._stats.total_rules = len(self._rules)
        self._stats.enabled_rules = sum(1 for r in self._rules.values() if r.enabled)

    # ── 序列化 ────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """将注册表序列化为字典。"""
        return {
            "rules": {name: rule.to_dict() for name, rule in self._rules.items()},
            "wrapped_count": len(self._wrapped_fns),
            "stats": self._stats.to_dict(),
        }


# ──────────────────────────────────────────────
# 验证工具函数
# ──────────────────────────────────────────────


def validate_with_rules(
    rule_def: ToolRuleDef,
    kwargs: dict[str, Any],
    result: Any | None = None,
) -> ValidationResult:
    """
    独立验证函数——对给定的规则定义、参数和结果进行验证。

    用于不经过装饰器的场景（如直接调用验证）。

    Args:
        rule_def: 规则定义
        kwargs: 函数参数（用于前置条件和边界处理检查）
        result: 函数结果（用于后置条件检查，可为 None）

    Returns:
        ValidationResult 实例
    """
    start = time.time()
    pre_results: list[tuple[str, bool, str]] = []
    post_results: list[tuple[str, bool, str]] = []
    boundary_warnings: list[str] = []
    error: str | None = None

    try:
        # 前置条件
        for cond in rule_def.pre_conditions:
            value = kwargs.get(cond.param)
            passed, msg = cond.check(value)
            pre_results.append((cond.name, passed, msg))

        # 边界处理
        for handler in rule_def.boundary_handlers:
            if handler.param in kwargs:
                _, warning = handler.apply(kwargs[handler.param])
                if warning:
                    boundary_warnings.append(warning)

        # 后置条件
        if result is not None:
            for cond in rule_def.post_conditions:
                passed, msg = cond.check(result)
                post_results.append((cond.name, passed, msg))

    except Exception as e:
        error = str(e)

    elapsed = (time.time() - start) * 1000
    all_passed = (
        all(p for _, p, _ in pre_results)
        and all(p for _, p, _ in post_results)
        and error is None
    )

    return ValidationResult(
        rule_def=rule_def,
        passed=all_passed,
        pre_check_results=pre_results,
        post_check_results=post_results,
        boundary_warnings=boundary_warnings,
        error=error,
        timing_ms=elapsed,
    )


def parse_rule_from_docstring(docstring: str, tool_name: str) -> ToolRuleDef | None:
    """
    从文档字符串解析规则定义（实验性功能）。

    支持从文档字符串中提取格式化的规则描述：
        [前置条件]
          - 查询参数不能为空 (error)
        [后置条件]
          - 结果不能为空 (error)
        [边界处理]
          - 查询文本不超过500字
        [成本声明]
          - 每次查询消耗嵌入 Token (~150 tokens)

    Args:
        docstring: 函数文档字符串
        tool_name: 工具名称

    Returns:
        解析出的 ToolRuleDef，或 None（解析失败）
    """
    if not docstring:
        return None

    pre_conditions: list[PreCondition] = []
    post_conditions: list[PostCondition] = []
    boundary_handlers: list[BoundaryHandler] = []
    cost_declarations: list[CostDeclaration] = []
    description_parts: list[str] = []

    current_section: str | None = None
    lines = docstring.strip().split("\n")

    for line in lines:
        stripped = line.strip()

        # 检测段落标题
        section_match = re.match(r'^\[(前置条件|后置条件|边界处理|成本声明)\]', stripped)
        if section_match:
            current_section = section_match.group(1)
            continue

        # 检测描述段落（非列表项、非段落标题的行）
        if not stripped.startswith("- ") and not stripped.startswith("* "):
            if stripped and not stripped.endswith("]"):
                if current_section is None:
                    description_parts.append(stripped)
            continue

        if current_section == "前置条件":
            # 格式: - 描述 (severity)
            severity = ConditionSeverity.ERROR
            sev_match = re.search(r'\((\w+)\)$', stripped)
            if sev_match:
                try:
                    severity = ConditionSeverity(sev_match.group(1))
                except ValueError:
                    pass
            text = re.sub(r'\s*\((\w+)\)$', '', stripped).lstrip("-* ").strip()
            pre_conditions.append(PreCondition(
                name=f"pre_{len(pre_conditions) + 1}",
                description=text,
                param="",  # 自动解析困难，由调用方填充
                operator=ConditionOperator.CUSTOM,
                severity=severity,
            ))

        elif current_section == "后置条件":
            severity = ConditionSeverity.ERROR
            sev_match = re.search(r'\((\w+)\)$', stripped)
            if sev_match:
                try:
                    severity = ConditionSeverity(sev_match.group(1))
                except ValueError:
                    pass
            text = re.sub(r'\s*\((\w+)\)$', '', stripped).lstrip("-* ").strip()
            post_conditions.append(PostCondition(
                name=f"post_{len(post_conditions) + 1}",
                description=text,
                severity=severity,
            ))

        elif current_section == "边界处理":
            text = stripped.lstrip("-* ").strip()
            boundary_handlers.append(BoundaryHandler(
                name=f"boundary_{len(boundary_handlers) + 1}",
                description=text,
                param="",
            ))

        elif current_section == "成本声明":
            # 格式: - 描述 (~N unit)
            text = stripped.lstrip("-* ").strip()
            cost_match = re.search(r'~\(?([\d.]+)\s*(\w+)\)?', text)
            if cost_match:
                try:
                    amount = float(cost_match.group(1))
                    unit_str = cost_match.group(2)
                    unit = CostUnit(unit_str)
                except (ValueError, KeyError):
                    amount = 0.0
                    unit = CostUnit.TOKENS
            else:
                amount = 0.0
                unit = CostUnit.TOKENS
            clean_text = re.sub(r'\s*~\(?[\d.]+\s*\w+\)?', '', text).strip() or text
            cost_declarations.append(CostDeclaration(
                name=f"cost_{len(cost_declarations) + 1}",
                description=clean_text,
                unit=unit,
                estimated_amount=amount,
            ))

    description = "\n".join(description_parts).strip()

    if not pre_conditions and not post_conditions and not boundary_handlers and not cost_declarations:
        return None

    return ToolRuleDef(
        tool_name=tool_name,
        description=description or f"从文档字符串解析的工具 '{tool_name}' 规则",
        pre_conditions=pre_conditions,
        post_conditions=post_conditions,
        boundary_handlers=boundary_handlers,
        cost_declarations=cost_declarations,
    )


# ──────────────────────────────────────────────
# 全局单例
# ──────────────────────────────────────────────

tool_rule_registry = ToolRuleRegistry()
