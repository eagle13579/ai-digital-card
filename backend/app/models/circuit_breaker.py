"""
circuit_breaker.py — 熔断器数据模型

定义 CircuitState（熔断状态枚举）、CircuitBreakerRule（熔断规则）、
CircuitBreakerEvent（状态变更事件）、CircuitBreakerStatus（当前状态快照）。
"""
from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any


class CircuitState(str, Enum):
    """熔断器状态枚举"""
    CLOSED = "closed"          # 正常，请求通过
    OPEN = "open"              # 熔断打开，请求快速失败
    HALF_OPEN = "half_open"    # 半开，允许试探性请求


class CircuitBreakerRule:
    """
    熔断规则配置。

    Attributes:
        name: 熔断器唯一名称（如 task_slicer, openai_api）
        failure_threshold: 连续失败次数阈值，超过后状态由 CLOSED → OPEN
        recovery_timeout: 熔断打开后等待秒数，超时后由 OPEN → HALF_OPEN
        half_open_max_requests: 半开状态下最多允许的试探请求数
        success_threshold: 半开状态下连续成功次数阈值，达到后状态由 HALF_OPEN → CLOSED
        description: 人类可读描述
        tags: 标签，用于分组/筛选
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_requests: int = 3,
        success_threshold: int = 2,
        description: str = "",
        tags: list[str] | None = None,
    ):
        if failure_threshold < 1:
            raise ValueError("failure_threshold 必须 >= 1")
        if recovery_timeout <= 0:
            raise ValueError("recovery_timeout 必须 > 0")
        if half_open_max_requests < 1:
            raise ValueError("half_open_max_requests 必须 >= 1")
        if success_threshold < 1:
            raise ValueError("success_threshold 必须 >= 1")

        self.name: str = name
        self.failure_threshold: int = failure_threshold
        self.recovery_timeout: float = recovery_timeout
        self.half_open_max_requests: int = half_open_max_requests
        self.success_threshold: int = success_threshold
        self.description: str = description
        self.tags: list[str] = tags or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "half_open_max_requests": self.half_open_max_requests,
            "success_threshold": self.success_threshold,
            "description": self.description,
            "tags": self.tags,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CircuitBreakerRule:
        return CircuitBreakerRule(
            name=data["name"],
            failure_threshold=data.get("failure_threshold", 5),
            recovery_timeout=data.get("recovery_timeout", 30.0),
            half_open_max_requests=data.get("half_open_max_requests", 3),
            success_threshold=data.get("success_threshold", 2),
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )

    def __repr__(self) -> str:
        return (
            f"<CircuitBreakerRule '{self.name}' "
            f"threshold={self.failure_threshold} "
            f"timeout={self.recovery_timeout}s>"
        )


class CircuitBreakerEvent:
    """
    熔断器事件记录。

    Attributes:
        event_id: 事件唯一标识
        breaker_name: 所属熔断器名称
        timestamp: 事件发生时间戳
        event_type: 事件类型（failure, success, state_change, reset, manual_open）
        from_state: 前一状态
        to_state: 当前状态
        message: 事件描述
        metadata: 附加元数据
    """

    def __init__(
        self,
        breaker_name: str,
        event_type: str,
        message: str = "",
        from_state: CircuitState | None = None,
        to_state: CircuitState | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.event_id: str = f"evt_{uuid.uuid4().hex[:12]}"
        self.breaker_name: str = breaker_name
        self.timestamp: float = time.time()
        self.event_type: str = event_type  # failure, success, state_change, reset, manual_open
        self.from_state: CircuitState | None = from_state
        self.to_state: CircuitState | None = to_state
        self.message: str = message
        self.metadata: dict[str, Any] = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        def _s(val):
            return val.value if isinstance(val, CircuitState) else val
        return {
            "event_id": self.event_id,
            "breaker_name": self.breaker_name,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "from_state": _s(self.from_state),
            "to_state": _s(self.to_state),
            "message": self.message,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return (
            f"<CircuitBreakerEvent {self.event_type} "
            f"breaker={self.breaker_name} "
            f"at={self.timestamp:.3f}>"
        )


class CircuitBreakerStatus:
    """
    熔断器当前状态快照。

    Attributes:
        name: 熔断器名称
        state: 当前状态
        rule: 熔断规则
        failure_count: 当前连续失败计数
        success_count: 当前连续成功计数（半开状态下跟踪）
        last_failure_time: 最近一次失败时间戳
        last_success_time: 最近一次成功时间戳
        last_state_change_time: 最近一次状态变更时间戳
        total_failures: 历史总失败次数
        total_successes: 历史总成功次数
        is_locked: 是否被手动锁定（管理员强制 OPEN）
        recent_events: 最近 N 条事件
    """

    def __init__(
        self,
        name: str,
        state: CircuitState = CircuitState.CLOSED,
        rule: CircuitBreakerRule | None = None,
        failure_count: int = 0,
        success_count: int = 0,
        last_failure_time: float | None = None,
        last_success_time: float | None = None,
        last_state_change_time: float | None = None,
        total_failures: int = 0,
        total_successes: int = 0,
        is_locked: bool = False,
        recent_events: list[CircuitBreakerEvent] | None = None,
    ):
        self.name: str = name
        self.state: CircuitState = state
        self.rule: CircuitBreakerRule = rule or CircuitBreakerRule(name=name)
        self.failure_count: int = failure_count
        self.success_count: int = success_count
        self.last_failure_time: float | None = last_failure_time
        self.last_success_time: float | None = last_success_time
        self.last_state_change_time: float | None = last_state_change_time
        self.total_failures: int = total_failures
        self.total_successes: int = total_successes
        self.is_locked: bool = is_locked
        self.recent_events: list[CircuitBreakerEvent] = recent_events or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value if isinstance(self.state, CircuitState) else self.state,
            "rule": self.rule.to_dict(),
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "last_state_change_time": self.last_state_change_time,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "is_locked": self.is_locked,
            "recent_events": [e.to_dict() for e in self.recent_events[-20:]],
        }

    def __repr__(self) -> str:
        return (
            f"<CircuitBreakerStatus '{self.name}' "
            f"state={self.state.value} "
            f"failures={self.failure_count}/{self.rule.failure_threshold}>"
        )
