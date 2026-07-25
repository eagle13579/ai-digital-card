"""
token_budget.py — Token 预算指令系统服务

功能:
  - 预算追踪：记录每条指令的 Token 用量
  - 超限降级：根据配置的策略自动降级（截断/换模型/拒绝/仅告警）
  - 截断策略：智能截断内容至预算上限（保留关键部分）
  - 用量估算：基于文本内容和模型估算 Token 数

用法:
    budget = TokenBudgetManager.get_or_create("openai_gpt4")
    result = await budget.process_with_budget(
        instruction="请总结以下内容...",
        content=long_text,
    )
"""
from __future__ import annotations
import asyncio
import logging
import threading
import time
from typing import Any, Callable

from app.models.token_budget import (
    DegradeStrategy,
    TokenBudgetEvent,
    TokenBudgetRule,
    TokenBudgetStatus,
)

logger = logging.getLogger(__name__)

# ── 默认配置常量 ──────────────────────────────

DEFAULT_TOKEN_LIMIT = 4096
DEFAULT_WARN_THRESHOLD = 0.8
DEFAULT_TRUNCATE_HEADROOM = 64  # 截断时保留的余量（token）

# 简单 Token 估算：中英文混合按字符估算
# 英文约 1 token / 4 chars，中文约 1 token / 1.5 chars
TOKEN_RATE_EN = 0.25    # 每个字符对应的 token 数（英文）
TOKEN_RATE_CN = 0.67    # 每个字符对应的 token 数（中文）


# ── 工具函数 ──────────────────────────────────

def estimate_tokens(text: str) -> int:
    """
    估算文本的 Token 数。
    简单启发式：中文字符 * 0.67 + 非中文字符 * 0.25
    """
    if not text:
        return 0
    cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - cn_chars
    estimated = int(cn_chars * TOKEN_RATE_CN + other_chars * TOKEN_RATE_EN)
    return max(1, estimated)


def truncate_to_limit(text: str, token_limit: int, headroom: int = DEFAULT_TRUNCATE_HEADROOM) -> str:
    """
    将文本截断至指定 Token 预算上限。
    保留头部和尾部关键信息，截断中间部分。

    Args:
        text: 原始文本
        token_limit: 目标 Token 上限
        headroom: 截断余量，确保不会刚好卡在边界

    Returns:
        截断后的文本
    """
    effective_limit = max(1, token_limit - headroom)
    current_estimate = estimate_tokens(text)

    if current_estimate <= effective_limit:
        return text

    # 按比例缩小：保留头部 60% 和尾部 40% 的关键信息
    ratio = effective_limit / current_estimate
    head_ratio = min(0.6, ratio * 0.7)
    tail_ratio = max(0.1, ratio * 0.3)

    chars = len(text)
    head_chars = int(chars * head_ratio)
    tail_chars = int(chars * tail_ratio)

    head_part = text[:head_chars]
    tail_part = text[-tail_chars:]

    truncated = f"{head_part}\n\n[... 中间内容已截断，原始 {current_estimate} tokens，保留约 {effective_limit} tokens ...]\n\n{tail_part}"

    # 再次估算，确保不超过
    if estimate_tokens(truncated) > effective_limit + headroom:
        # 递归进一步截断
        return truncate_to_limit(head_part, effective_limit, headroom)

    return truncated


def estimate_instruction_tokens(instruction: str, content: str = "") -> int:
    """
    估算指令+内容的总 Token 数。
    """
    return estimate_tokens(instruction) + estimate_tokens(content)


# ── 预算管理器 ────────────────────────────────

class TokenBudget:
    """
    单个 Token 预算实例——管理指定规则下的 Token 预算追踪和执行。

    用法:
        budget = TokenBudget("openai_gpt4", rule)
        result = budget.process("指令", "内容")
    """

    def __init__(
        self,
        name: str,
        rule: TokenBudgetRule | None = None,
    ):
        self._name: str = name
        self._rule: TokenBudgetRule = rule or TokenBudgetRule(
            name=name,
            token_limit=DEFAULT_TOKEN_LIMIT,
            degrade_strategy=DegradeStrategy.TRUNCATE,
        )
        self._lock = threading.Lock()

        # 状态追踪
        self._current_usage: int = 0
        self._peak_usage: int = 0
        self._total_requests: int = 0
        self._total_truncations: int = 0
        self._total_downgrades: int = 0
        self._last_request_time: float | None = None
        self._recent_events: list[TokenBudgetEvent] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def rule(self) -> TokenBudgetRule:
        return self._rule

    def get_status(self) -> TokenBudgetStatus:
        """获取当前预算状态快照"""
        with self._lock:
            return TokenBudgetStatus(
                name=self._name,
                rule=self._rule,
                current_usage=self._current_usage,
                peak_usage=self._peak_usage,
                total_requests=self._total_requests,
                total_truncations=self._total_truncations,
                total_downgrades=self._total_downgrades,
                last_request_time=self._last_request_time,
                recent_events=list(self._recent_events),
            )

    # ── 事件记录 ──────────────────────────

    def _add_event(
        self,
        event_type: str,
        requested_tokens: int = 0,
        actual_tokens: int = 0,
        message: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        event = TokenBudgetEvent(
            rule_name=self._name,
            event_type=event_type,
            requested_tokens=requested_tokens,
            actual_tokens=actual_tokens,
            message=message,
            metadata=metadata,
        )
        with self._lock:
            self._recent_events.append(event)
            # 最多保留 200 条事件
            if len(self._recent_events) > 200:
                self._recent_events = self._recent_events[-200:]

    # ── 核心方法 ──────────────────────────

    def estimate(self, instruction: str, content: str = "") -> dict[str, Any]:
        """
        估算指定指令+内容的 Token 用量。

        Returns:
            {
                "rule_name": str,
                "token_limit": int,
                "instruction_tokens": int,
                "content_tokens": int,
                "total_estimated": int,
                "remaining_tokens": int,
                "is_exceeded": bool,
                "suggested_action": str,
            }
        """
        inst_tokens = estimate_tokens(instruction)
        cont_tokens = estimate_tokens(content)
        total_est = inst_tokens + cont_tokens

        with self._lock:
            remaining = max(0, self._rule.token_limit - self._current_usage)
            is_exceeded = total_est > self._rule.token_limit

        if is_exceeded:
            suggested = self._rule.degrade_strategy.value
        else:
            suggested = "ok"

        result = {
            "rule_name": self._name,
            "token_limit": self._rule.token_limit,
            "current_usage": self._current_usage,
            "instruction_tokens": inst_tokens,
            "content_tokens": cont_tokens,
            "total_estimated": total_est,
            "remaining_tokens": remaining,
            "is_exceeded": is_exceeded,
            "suggested_action": suggested,
            "degrade_strategy": self._rule.degrade_strategy.value,
        }

        self._add_event(
            event_type="estimate",
            requested_tokens=total_est,
            actual_tokens=total_est,
            message=f"估算: 指令 {inst_tokens} + 内容 {cont_tokens} = {total_est} tokens",
            metadata=result,
        )

        return result

    def process(
        self,
        instruction: str,
        content: str = "",
    ) -> dict[str, Any]:
        """
        处理一条指令/内容，应用 Token 预算控制。

        Args:
            instruction: 指令文本
            content: 待处理内容

        Returns:
            {
                "instruction": str,          # 原始指令
                "content": str,              # 处理后的内容（可能被截断）
                "original_tokens": int,       # 原始估算 Token 数
                "actual_tokens": int,         # 实际使用 Token 数
                "truncated": bool,            # 是否被截断
                "downgraded": bool,           # 是否被降级
                "degrade_strategy": str,       # 使用的策略
                "status": str,                # ok / truncated / downgraded / rejected / warned
                "events": list[dict],         # 关联事件
            }
        """
        total_est = estimate_instruction_tokens(instruction, content)
        status = "ok"
        truncated = False
        downgraded = False
        actual_content = content
        actual_tokens = total_est

        with self._lock:
            current_usage_before = self._current_usage
            projected_usage = current_usage_before + total_est
            strategy = self._rule.degrade_strategy

        # ── 策略执行 ──────────────────────

        if projected_usage > self._rule.token_limit:
            if strategy == DegradeStrategy.REJECT:
                status = "rejected"
                self._add_event(
                    event_type="reject",
                    requested_tokens=total_est,
                    actual_tokens=0,
                    message=f"请求被拒绝: 预估 {total_est} tokens 超出预算 {self._rule.token_limit}",
                )
                return {
                    "instruction": instruction,
                    "content": "",
                    "original_tokens": total_est,
                    "actual_tokens": 0,
                    "truncated": False,
                    "downgraded": False,
                    "degrade_strategy": DegradeStrategy.REJECT.value,
                    "status": "rejected",
                    "events": [],
                }

            elif strategy == DegradeStrategy.DOWNGRADE:
                downgraded = True
                status = "downgraded"
                # 降级：按比例截断内容到预算内
                allowed_tokens = max(64, self._rule.token_limit - current_usage_before - estimate_tokens(instruction))
                if allowed_tokens < estimate_tokens(content):
                    actual_content = truncate_to_limit(content, allowed_tokens)
                    actual_tokens = estimate_instruction_tokens(instruction, actual_content)
                message = (
                    f"降级处理: 原始 {total_est} tokens > 预算 {self._rule.token_limit}，"
                    f"已截断至 ~{actual_tokens} tokens，"
                    f"建议降级模型 {self._rule.model_mapping.get('full', '?')} → {self._rule.model_mapping.get('lite', '?')}"
                )
                self._add_event(
                    event_type="downgrade",
                    requested_tokens=total_est,
                    actual_tokens=actual_tokens,
                    message=message,
                    metadata={"model_mapping": self._rule.model_mapping},
                )
                with self._lock:
                    self._total_downgrades += 1

            elif strategy == DegradeStrategy.TRUNCATE:
                truncated = True
                status = "truncated"
                allowed_tokens = max(64, self._rule.token_limit - current_usage_before - estimate_tokens(instruction))
                actual_content = truncate_to_limit(content, allowed_tokens)
                actual_tokens = estimate_instruction_tokens(instruction, actual_content)
                message = (
                    f"截断处理: 原始 {total_est} tokens > 预算 {self._rule.token_limit}，"
                    f"已截断至 ~{actual_tokens} tokens"
                )
                self._add_event(
                    event_type="truncate",
                    requested_tokens=total_est,
                    actual_tokens=actual_tokens,
                    message=message,
                )
                with self._lock:
                    self._total_truncations += 1

            elif strategy == DegradeStrategy.WARN_ONLY:
                status = "warned"
                self._add_event(
                    event_type="warn",
                    requested_tokens=total_est,
                    actual_tokens=total_est,
                    message=f"预算超限告警: {total_est} tokens > {self._rule.token_limit}（未截断）",
                )

        # ── 是否触发告警阈值 ──────────────
        usage_ratio = projected_usage / self._rule.token_limit if self._rule.token_limit > 0 else 1.0
        if usage_ratio >= self._rule.warn_threshold and status == "ok":
            self._add_event(
                event_type="warn",
                requested_tokens=total_est,
                actual_tokens=total_est,
                message=f"预算使用率 {usage_ratio:.1%} 达到告警阈值 {self._rule.warn_threshold:.0%}",
            )
            status = "warned"

        # ── 更新状态 ──────────────────────
        with self._lock:
            self._current_usage += actual_tokens
            if self._current_usage > self._peak_usage:
                self._peak_usage = self._current_usage
            self._total_requests += 1
            self._last_request_time = time.time()

        return {
            "instruction": instruction,
            "content": actual_content,
            "original_tokens": total_est,
            "actual_tokens": actual_tokens,
            "truncated": truncated,
            "downgraded": downgraded,
            "degrade_strategy": strategy.value,
            "status": status,
            "events": [e.to_dict() for e in self._recent_events[-3:]],
        }

    async def process_async(
        self,
        instruction: str,
        content: str = "",
        callback: Callable[[str, str], Any] | None = None,
    ) -> dict[str, Any]:
        """
        异步版本：处理指令/内容并可选调用回调函数处理截断后的内容。

        Args:
            instruction: 指令文本
            content: 待处理内容
            callback: 可选异步回调，参数为 (instruction, processed_content)

        Returns:
            与 process() 相同的结果字典
        """
        result = self.process(instruction, content)
        if callback and result["status"] not in ("rejected",):
            if asyncio.iscoroutinefunction(callback):
                await callback(result["instruction"], result["content"])
            else:
                callback(result["instruction"], result["content"])
        return result

    def reset(self) -> None:
        """重置当前预算用量（不清除历史事件）"""
        with self._lock:
            self._current_usage = 0
            self._add_event(event_type="reset", message="预算用量已重置")


# ── 全局注册表 ────────────────────────────────

class TokenBudgetRegistry:
    """
    Token 预算注册表——全局管理所有 TokenBudget 实例。

    用法:
        registry = TokenBudgetRegistry()
        budget = registry.get_or_create("openai_gpt4")
    """

    def __init__(self):
        self._budgets: dict[str, TokenBudget] = {}
        self._lock = threading.Lock()

    def get(self, name: str) -> TokenBudget | None:
        """获取指定名称的预算实例"""
        with self._lock:
            return self._budgets.get(name)

    def get_or_create(
        self,
        name: str,
        rule: TokenBudgetRule | None = None,
    ) -> TokenBudget:
        """获取或创建预算实例"""
        with self._lock:
            if name not in self._budgets:
                self._budgets[name] = TokenBudget(name, rule)
            return self._budgets[name]

    def create(
        self,
        name: str,
        rule: TokenBudgetRule,
    ) -> TokenBudget:
        """创建新的预算实例（如已存在则覆盖）"""
        with self._lock:
            budget = TokenBudget(name, rule)
            self._budgets[name] = budget
            return budget

    def remove(self, name: str) -> bool:
        """移除指定预算实例"""
        with self._lock:
            if name in self._budgets:
                del self._budgets[name]
                return True
            return False

    def all_status(self) -> list[TokenBudgetStatus]:
        """获取所有预算实例的状态"""
        with self._lock:
            return [b.get_status() for b in self._budgets.values()]

    def count(self) -> int:
        """获取预算实例数量"""
        with self._lock:
            return len(self._budgets)

    def reset_all(self) -> int:
        """重置所有预算实例"""
        with self._lock:
            count = len(self._budgets)
            for b in self._budgets.values():
                b.reset()
            return count

    def get_or_create_from_dict(self, data: dict[str, Any]) -> TokenBudget:
        """从字典创建或获取预算实例"""
        rule = TokenBudgetRule.from_dict(data)
        return self.get_or_create(rule.name, rule)


# ── 全局实例 ──────────────────────────────────

token_budget_registry = TokenBudgetRegistry()

# 注册默认预算规则
_default_rules = [
    TokenBudgetRule(
        name="openai_gpt4",
        token_limit=4096,
        degrade_strategy=DegradeStrategy.DOWNGRADE,
        warn_threshold=0.8,
        description="OpenAI GPT-4 Turbo 预算",
        tags=["llm", "openai"],
        model_mapping={"full": "gpt-4-turbo", "lite": "gpt-3.5-turbo"},
    ),
    TokenBudgetRule(
        name="openai_embedding",
        token_limit=8192,
        degrade_strategy=DegradeStrategy.TRUNCATE,
        warn_threshold=0.85,
        description="OpenAI Embedding 预算",
        tags=["embedding", "openai"],
    ),
    TokenBudgetRule(
        name="claude_sonnet",
        token_limit=4096,
        degrade_strategy=DegradeStrategy.DOWNGRADE,
        warn_threshold=0.8,
        description="Claude Sonnet 预算",
        tags=["llm", "anthropic"],
        model_mapping={"full": "claude-3-sonnet", "lite": "claude-3-haiku"},
    ),
    TokenBudgetRule(
        name="instruction_default",
        token_limit=2048,
        degrade_strategy=DegradeStrategy.TRUNCATE,
        warn_threshold=0.9,
        description="通用指令预算",
        tags=["default"],
    ),
]

for _rule in _default_rules:
    token_budget_registry.get_or_create(_rule.name, _rule)
