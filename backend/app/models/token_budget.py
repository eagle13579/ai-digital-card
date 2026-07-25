"""
token_budget.py — Token 预算数据模型

定义 DegradeStrategy（降级策略枚举）、TokenBudgetRule（预算规则）、
TokenBudgetEvent（预算事件）、TokenBudgetStatus（当前预算状态快照）。
"""
from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any


class DegradeStrategy(str, Enum):
    """Token 超限降级策略"""
    TRUNCATE = "truncate"          # 截断内容至预算上限
    DOWNGRADE = "downgrade"        # 切换到更便宜的模型/策略
    REJECT = "reject"              # 拒绝请求
    WARN_ONLY = "warn_only"        # 仅告警不截断


# 兼容名
DegradeStrategyEnum = DegradeStrategy


class TokenBudgetRule:
    """
    Token 预算规则配置。

    Attributes:
        name: 预算规则唯一名称（如 openai_gpt4, claude_sonnet, embedding）
        token_limit: Token 预算上限
        degrade_strategy: 超限后的降级策略
        warn_threshold: 触发告警的阈值比例（0.0~1.0，如 0.8 表示用量达 80% 时告警）
        description: 人类可读描述
        tags: 标签，用于分组/筛选
        model_mapping: 降级时使用的模型映射 {"full": "gpt-4", "lite": "gpt-3.5-turbo"}
    """

    def __init__(
        self,
        name: str,
        token_limit: int = 4096,
        degrade_strategy: DegradeStrategy = DegradeStrategy.TRUNCATE,
        warn_threshold: float = 0.8,
        description: str = "",
        tags: list[str] | None = None,
        model_mapping: dict[str, str] | None = None,
    ):
        if token_limit < 1:
            raise ValueError("token_limit 必须 >= 1")
        if not 0.0 < warn_threshold <= 1.0:
            raise ValueError("warn_threshold 必须在 (0.0, 1.0] 范围内")
        if degrade_strategy == DegradeStrategy.TRUNCATE:
            degrade_strategy = DegradeStrategy.TRUNCATE

        self.name: str = name
        self.token_limit: int = token_limit
        self.degrade_strategy: DegradeStrategy = degrade_strategy
        self.warn_threshold: float = warn_threshold
        self.description: str = description
        self.tags: list[str] = tags or []
        self.model_mapping: dict[str, str] = model_mapping or {
            "full": "gpt-4",
            "lite": "gpt-3.5-turbo",
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "token_limit": self.token_limit,
            "degrade_strategy": self.degrade_strategy.value
            if isinstance(self.degrade_strategy, DegradeStrategy)
            else self.degrade_strategy,
            "warn_threshold": self.warn_threshold,
            "description": self.description,
            "tags": self.tags,
            "model_mapping": self.model_mapping,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> TokenBudgetRule:
        ds = data.get("degrade_strategy", "truncate")
        if isinstance(ds, str):
            ds = DegradeStrategy(ds)
        return TokenBudgetRule(
            name=data["name"],
            token_limit=data.get("token_limit", 4096),
            degrade_strategy=ds,
            warn_threshold=data.get("warn_threshold", 0.8),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            model_mapping=data.get("model_mapping", {"full": "gpt-4", "lite": "gpt-3.5-turbo"}),
        )

    def __repr__(self) -> str:
        return (
            f"<TokenBudgetRule '{self.name}' "
            f"limit={self.token_limit} "
            f"strategy={self.degrade_strategy.value}>"
        )


class TokenBudgetEvent:
    """
    Token 预算事件记录。

    Attributes:
        event_id: 事件唯一标识
        rule_name: 所属预算规则名称
        timestamp: 事件发生时间戳
        event_type: 事件类型（estimate, truncate, degrade, warn, reset）
        requested_tokens: 请求的 token 数
        actual_tokens: 实际使用的 token 数（截断后）
        message: 事件描述
        metadata: 附加元数据
    """

    def __init__(
        self,
        rule_name: str,
        event_type: str,
        requested_tokens: int = 0,
        actual_tokens: int = 0,
        message: str = "",
        metadata: dict[str, Any] | None = None,
    ):
        self.event_id: str = f"tbe_{uuid.uuid4().hex[:12]}"
        self.rule_name: str = rule_name
        self.timestamp: float = time.time()
        self.event_type: str = event_type
        self.requested_tokens: int = requested_tokens
        self.actual_tokens: int = actual_tokens
        self.message: str = message
        self.metadata: dict[str, Any] = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "rule_name": self.rule_name,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "requested_tokens": self.requested_tokens,
            "actual_tokens": self.actual_tokens,
            "message": self.message,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return (
            f"<TokenBudgetEvent {self.event_type} "
            f"rule={self.rule_name} "
            f"req={self.requested_tokens} "
            f"act={self.actual_tokens}>"
        )


class TokenBudgetStatus:
    """
    Token 预算当前状态快照。

    Attributes:
        name: 预算规则名称
        rule: 预算规则
        current_usage: 当前已用 token 数
        peak_usage: 历史峰值 token 数
        total_requests: 总请求次数
        total_truncations: 截断次数
        total_downgrades: 降级次数
        last_request_time: 最近请求时间戳
        recent_events: 最近 N 条事件
    """

    def __init__(
        self,
        name: str,
        rule: TokenBudgetRule | None = None,
        current_usage: int = 0,
        peak_usage: int = 0,
        total_requests: int = 0,
        total_truncations: int = 0,
        total_downgrades: int = 0,
        last_request_time: float | None = None,
        recent_events: list[TokenBudgetEvent] | None = None,
    ):
        self.name: str = name
        self.rule: TokenBudgetRule = rule or TokenBudgetRule(name=name)
        self.current_usage: int = current_usage
        self.peak_usage: int = peak_usage
        self.total_requests: int = total_requests
        self.total_truncations: int = total_truncations
        self.total_downgrades: int = total_downgrades
        self.last_request_time: float | None = last_request_time
        self.recent_events: list[TokenBudgetEvent] = recent_events or []

    @property
    def usage_ratio(self) -> float:
        """当前用量占预算比例 (0.0~1.0)"""
        if self.rule.token_limit <= 0:
            return 0.0
        return round(self.current_usage / self.rule.token_limit, 4)

    @property
    def remaining_tokens(self) -> int:
        """剩余可用 token 数"""
        return max(0, self.rule.token_limit - self.current_usage)

    @property
    def is_warning(self) -> bool:
        """是否触发告警阈值"""
        return self.usage_ratio >= self.rule.warn_threshold

    @property
    def is_exceeded(self) -> bool:
        """是否超过预算上限"""
        return self.current_usage >= self.rule.token_limit

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rule": self.rule.to_dict(),
            "current_usage": self.current_usage,
            "peak_usage": self.peak_usage,
            "total_requests": self.total_requests,
            "total_truncations": self.total_truncations,
            "total_downgrades": self.total_downgrades,
            "usage_ratio": self.usage_ratio,
            "remaining_tokens": self.remaining_tokens,
            "is_warning": self.is_warning,
            "is_exceeded": self.is_exceeded,
            "last_request_time": self.last_request_time,
            "recent_events": [e.to_dict() for e in self.recent_events[-20:]],
        }

    def __repr__(self) -> str:
        return (
            f"<TokenBudgetStatus '{self.name}' "
            f"{self.current_usage}/{self.rule.token_limit} "
            f"({self.usage_ratio:.1%})>"
        )
