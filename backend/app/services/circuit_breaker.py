"""
circuit_breaker.py — 熔断器状态机服务

状态转换:
    CLOSED ──(连续失败 >= threshold)──→ OPEN
    OPEN   ──(超过 recovery_timeout)──→ HALF_OPEN
    HALF_OPEN ──(试探成功)──→ CLOSED
    HALF_OPEN ──(试探失败)──→ OPEN

特性:
  - 指数退避重试（base_delay * 2^retry_count，带抖动）
  - 支持异步和同步函数包装
  - 集成 TaskSlicer（任务切片引擎）
  - 线程安全（threading.Lock）
"""
from __future__ import annotations
import asyncio
import logging
import random
import time
import threading
from typing import Any, Callable, TypeVar

from app.models.circuit_breaker import (
    CircuitBreakerEvent,
    CircuitBreakerRule,
    CircuitBreakerStatus,
    CircuitState,
)
from app.services.task_slicer import TaskSlicer

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ──────────────────────────────────────────────
# 默认配置常量
# ──────────────────────────────────────────────
DEFAULT_FAILURE_THRESHOLD = 5            # 连续失败 5 次熔断
DEFAULT_RECOVERY_TIMEOUT = 30.0          # 30 秒后尝试恢复
DEFAULT_HALF_OPEN_MAX_REQUESTS = 3       # 半开最多 3 个试探请求
DEFAULT_SUCCESS_THRESHOLD = 2            # 半开连续成功 2 次恢复
DEFAULT_BASE_DELAY = 1.0                 # 指数退避初始延迟（秒）
DEFAULT_MAX_DELAY = 60.0                 # 指数退避最大延迟（秒）
DEFAULT_JITTER_FACTOR = 0.1              # 抖动因子


class CircuitBreakerOpenError(Exception):
    """熔断器打开时抛出的异常——请求被快速拒绝。"""
    pass


class CircuitBreaker:
    """
    熔断器实例——管理单个服务/操作的熔断状态。

    用法:
        cb = CircuitBreaker("openai_api")
        async_result = await cb.call_async(some_async_func, arg1, arg2)
        sync_result = cb.call_sync(some_sync_func, arg1, arg2)
    """

    def __init__(
        self,
        name: str,
        rule: CircuitBreakerRule | None = None,
        task_slicer: TaskSlicer | None = None,
    ):
        self._name: str = name
        self._rule: CircuitBreakerRule = rule or CircuitBreakerRule(
            name=name,
            failure_threshold=DEFAULT_FAILURE_THRESHOLD,
            recovery_timeout=DEFAULT_RECOVERY_TIMEOUT,
            half_open_max_requests=DEFAULT_HALF_OPEN_MAX_REQUESTS,
            success_threshold=DEFAULT_SUCCESS_THRESHOLD,
        )
        self._lock = threading.Lock()

        # 状态
        self._state: CircuitState = CircuitState.CLOSED
        self._failure_count: int = 0
        self._success_count: int = 0
        self._last_failure_time: float | None = None
        self._last_success_time: float | None = None
        self._last_state_change_time: float = time.time()
        self._total_failures: int = 0
        self._total_successes: int = 0
        self._is_locked: bool = False
        self._half_open_requests: int = 0              # 当前半开试探请求数
        self._retry_count: int = 0                      # 指数退避重试计数
        self._recent_events: list[CircuitBreakerEvent] = []

        # TaskSlicer 集成
        self._task_slicer: TaskSlicer | None = task_slicer

        self._add_event("init", f"熔断器 '{name}' 初始化完成 (state=closed)")

    # ── 属性 ────────────────────────────────

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def rule(self) -> CircuitBreakerRule:
        return self._rule

    # ── 状态机核心 ─────────────────────────

    def _transition_to(self, new_state: CircuitState, reason: str = "") -> None:
        """线程安全的状态迁移。"""
        old_state = self._state
        if old_state == new_state:
            return
        self._state = new_state
        self._last_state_change_time = time.time()
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
            self._half_open_requests = 0
            self._retry_count = 0
        elif new_state == CircuitState.OPEN:
            self._half_open_requests = 0
            self._retry_count += 1
        elif new_state == CircuitState.HALF_OPEN:
            self._half_open_requests = 0
            self._success_count = 0
        self._add_event("state_change", reason, old_state, new_state)
        logger.info(
            "熔断器 '%s' 状态变更: %s → %s (原因: %s)",
            self._name, old_state.value, new_state.value, reason,
        )

    def _add_event(
        self,
        event_type: str,
        message: str = "",
        from_state: CircuitState | None = None,
        to_state: CircuitState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        evt = CircuitBreakerEvent(
            breaker_name=self._name,
            event_type=event_type,
            message=message,
            from_state=from_state or self._state,
            to_state=to_state or self._state,
            metadata=metadata,
        )
        self._recent_events.append(evt)
        # 最多保留 200 条
        if len(self._recent_events) > 200:
            self._recent_events = self._recent_events[-200:]

    def _should_allow_request(self) -> bool:
        """
        判断当前是否允许请求通过。
        - CLOSED: 总是允许
        - OPEN:  如果超过 recovery_timeout 则自动进入 HALF_OPEN
        - HALF_OPEN: 不超过 half_open_max_requests 时允许
        """
        with self._lock:
            if self._is_locked:
                return False

            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                elapsed = time.time() - self._last_state_change_time
                if elapsed >= self._rule.recovery_timeout:
                    self._transition_to(
                        CircuitState.HALF_OPEN,
                        f"恢复超时已到 ({elapsed:.1f}s >= {self._rule.recovery_timeout}s)",
                    )
                    self._half_open_requests = 1
                    return True
                return False

            # HALF_OPEN
            if self._half_open_requests < self._rule.half_open_max_requests:
                self._half_open_requests += 1
                return True
            return False

    def _on_success(self) -> None:
        """请求成功后的状态更新。"""
        with self._lock:
            self._total_successes += 1
            self._last_success_time = time.time()
            self._failure_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                self._add_event("success", f"半开试探成功 ({self._success_count}/{self._rule.success_threshold})")
                if self._success_count >= self._rule.success_threshold:
                    self._transition_to(
                        CircuitState.CLOSED,
                        f"半开连续成功 {self._success_count} 次，恢复 CLOSED",
                    )
            else:
                self._success_count = 0
                self._add_event("success", "请求成功")

    def _on_failure(self, exc_info: str = "") -> None:
        """请求失败后的状态更新。"""
        with self._lock:
            self._total_failures += 1
            self._last_failure_time = time.time()
            self._failure_count += 1
            self._success_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._add_event(
                    "failure", f"半开试探失败 ({self._failure_count}/{self._rule.failure_threshold})",
                    metadata={"exc_info": exc_info},
                )
                self._transition_to(
                    CircuitState.OPEN,
                    f"半开状态下请求失败，回到 OPEN (推理: 服务仍未恢复)",
                )
            elif self._state == CircuitState.CLOSED:
                self._add_event(
                    "failure", f"连续失败 {self._failure_count}/{self._rule.failure_threshold}",
                    metadata={"exc_info": exc_info},
                )
                if self._failure_count >= self._rule.failure_threshold:
                    self._transition_to(
                        CircuitState.OPEN,
                        f"连续失败 {self._failure_count} 次，触发熔断",
                    )
            # OPEN 状态下理论上不会到这里，但以防万一
            elif self._state == CircuitState.OPEN:
                self._add_event("failure", "OPEN 状态下收到失败（异常状态）")

    # ── 指数退避 ──────────────────────────

    def get_backoff_delay(self) -> float:
        """
        计算指数退避延迟。
        公式: min(base_delay * 2^retry_count, max_delay) + jitter
        """
        base = DEFAULT_BASE_DELAY * (2 ** self._retry_count)
        capped = min(base, DEFAULT_MAX_DELAY)
        jitter = random.uniform(0, DEFAULT_JITTER_FACTOR * capped)
        return capped + jitter

    # ── 装饰器 / 包装器 ───────────────────

    async def call_async(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        异步调用包装——自动检查熔断状态、重试、结果处理。

        如果熔断器打开则抛出 CircuitBreakerOpenError。
        如果函数执行抛出异常，则计入失败计数。
        """
        if not self._should_allow_request():
            delay = self.get_backoff_delay()
            raise CircuitBreakerOpenError(
                f"熔断器 '{self._name}' 已打开，拒绝请求。"
                f"当前状态: {self._state.value}, "
                f"重试计数: {self._retry_count}, "
                f"建议等待 {delay:.1f}s 后重试"
            )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except CircuitBreakerOpenError:
            # 内部嵌套的熔断器异常不计数
            raise
        except Exception as e:
            self._on_failure(exc_info=str(e))
            raise

    def call_sync(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        同步调用包装——自动检查熔断状态、重试、结果处理。
        """
        if not self._should_allow_request():
            delay = self.get_backoff_delay()
            raise CircuitBreakerOpenError(
                f"熔断器 '{self._name}' 已打开，拒绝请求。"
                f"当前状态: {self._state.value}, "
                f"重试计数: {self._retry_count}, "
                f"建议等待 {delay:.1f}s 后重试"
            )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except CircuitBreakerOpenError:
            raise
        except Exception as e:
            self._on_failure(exc_info=str(e))
            raise

    # ── TaskSlicer 集成 ───────────────────

    def wrap_task_slicer(self, slicer: TaskSlicer | None = None) -> TaskSlicer:
        """
        包装 TaskSlicer 实例——将切片引擎的所有 API 调用包裹熔断器。

        返回包装后的 TaskSlicer，其 auto_slice / slice_by_token_budget /
        slice_by_steps / slice_by_semantic 方法受熔断器保护。
        """
        target = slicer or self._task_slicer
        if target is None:
            raise ValueError("TaskSlicer 实例未提供，请在构造时传入 task_slicer 参数")

        class _CircuitBreakerTaskSlicer:
            def __init__(self, cb: CircuitBreaker, inner: TaskSlicer):
                self._cb = cb
                self._inner = inner

            async def auto_slice(self, *args: Any, **kwargs: Any) -> Any:
                return await self._cb.call_async(self._inner.auto_slice, *args, **kwargs)

            async def slice_by_token_budget(self, *args: Any, **kwargs: Any) -> Any:
                return await self._cb.call_async(self._inner.slice_by_token_budget, *args, **kwargs)

            async def slice_by_steps(self, *args: Any, **kwargs: Any) -> Any:
                return await self._cb.call_async(self._inner.slice_by_steps, *args, **kwargs)

            async def slice_by_semantic(self, *args: Any, **kwargs: Any) -> Any:
                return await self._cb.call_async(self._inner.slice_by_semantic, *args, **kwargs)

        return _CircuitBreakerTaskSlicer(self, target)

    # ── 管理操作 ──────────────────────────

    def reset(self) -> None:
        """手动重置熔断器到 CLOSED 状态。"""
        with self._lock:
            self._transition_to(CircuitState.CLOSED, "管理员手动重置")
            self._is_locked = False
            logger.info("熔断器 '%s' 已手动重置为 CLOSED", self._name)

    def force_open(self, reason: str = "管理员手动触发") -> None:
        """
        手动强制熔断器为 OPEN 状态。
        可用于模拟故障或主动降级。
        """
        with self._lock:
            self._transition_to(CircuitState.OPEN, reason)
            self._is_locked = True
            logger.warning("熔断器 '%s' 已强制打开: %s", self._name, reason)

    def force_close(self) -> None:
        """手动强制关闭熔断器（覆盖锁定）。"""
        with self._lock:
            self._transition_to(CircuitState.CLOSED, "管理员强制关闭")
            self._is_locked = False
            logger.info("熔断器 '%s' 已强制关闭", self._name)

    def get_status(self) -> CircuitBreakerStatus:
        """获取当前状态快照。"""
        with self._lock:
            now = time.time()
            remaining = max(0.0, self._rule.recovery_timeout - (now - self._last_state_change_time)) if self._state == CircuitState.OPEN else 0.0
            return CircuitBreakerStatus(
                name=self._name,
                state=self._state,
                rule=self._rule,
                failure_count=self._failure_count,
                success_count=self._success_count,
                last_failure_time=self._last_failure_time,
                last_success_time=self._last_success_time,
                last_state_change_time=self._last_state_change_time,
                total_failures=self._total_failures,
                total_successes=self._total_successes,
                is_locked=self._is_locked,
                recent_events=list(self._recent_events),
            )


# ──────────────────────────────────────────────
# 熔断器注册表（全局单例管理）
# ──────────────────────────────────────────────

class CircuitBreakerRegistry:
    """
    全局熔断器注册表——管理所有 CircuitBreaker 实例。

    用法:
        registry = CircuitBreakerRegistry()
        cb = registry.get_or_create("openai_api")
        cb2 = registry.get("task_slicer")
    """

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
        self._task_slicer: TaskSlicer | None = None

    def set_task_slicer(self, slicer: TaskSlicer) -> None:
        """设置全局 TaskSlicer 实例。"""
        self._task_slicer = slicer

    def get_task_slicer(self) -> TaskSlicer | None:
        return self._task_slicer

    def get_or_create(
        self,
        name: str,
        rule: CircuitBreakerRule | None = None,
    ) -> CircuitBreaker:
        """
        获取或创建熔断器实例。
        如果已存在则返回现有实例（忽略 rule 参数）。
        """
        with self._lock:
            if name in self._breakers:
                return self._breakers[name]
            cb = CircuitBreaker(
                name=name,
                rule=rule,
                task_slicer=self._task_slicer,
            )
            self._breakers[name] = cb
            logger.info("熔断器注册表: 创建 '%s'", name)
            return cb

    def get(self, name: str) -> CircuitBreaker | None:
        """获取指定名称的熔断器，不存在返回 None。"""
        return self._breakers.get(name)

    def all_status(self) -> list[CircuitBreakerStatus]:
        """获取所有熔断器状态。"""
        return [cb.get_status() for cb in self._breakers.values()]

    def reset_all(self) -> int:
        """重置所有熔断器到 CLOSED。返回重置的数量。"""
        count = 0
        for cb in self._breakers.values():
            cb.reset()
            count += 1
        return count

    def reset(self, name: str) -> bool:
        """重置指定熔断器。"""
        cb = self.get(name)
        if cb is None:
            return False
        cb.reset()
        return True

    def force_open(self, name: str, reason: str = "管理员手动触发") -> bool:
        """强制打开指定熔断器。"""
        cb = self.get(name)
        if cb is None:
            return False
        cb.force_open(reason)
        return True

    def remove(self, name: str) -> bool:
        """从注册表中移除熔断器。"""
        with self._lock:
            if name in self._breakers:
                del self._breakers[name]
                logger.info("熔断器注册表: 移除 '%s'", name)
                return True
            return False

    def count(self) -> int:
        """当前注册的熔断器数量。"""
        return len(self._breakers)

    def clear(self) -> None:
        """清空所有熔断器。"""
        with self._lock:
            self._breakers.clear()
            logger.info("熔断器注册表: 已清空")


# 全局单例
circuit_breaker_registry = CircuitBreakerRegistry()
