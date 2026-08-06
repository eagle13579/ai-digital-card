"""MultiLLMFailover — 多 LLM Session 故障转移混入层.

支持多个同构或异构 LLM Session 组成集群，自动故障转移：

    sessions = [SessionA, SessionB, SessionC]
    failover = MultiLLMFailover(sessions)
    response = await failover.chat(messages, tools=tools_list)

故障转移策略:
    - 每个 session 最多 2 次尝试 (首次 + 1 次重试)
    - 全部 session 失败后才抛出 AllSessionsExhaustedError
    - current 属性指向当前活跃 session
    - 故障时自动发布事件 (如有 event_bus)
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Protocol

logger = logging.getLogger(__name__)


# ======================================================================
# Session Protocol
# ======================================================================


class LLMSessionProtocol(Protocol):
    """LLM Session 必须实现的协议.

    chat(messages, tools) 是核心方法,
    返回 {"content": str, "usage": {...}, "model": str} 格式.
    """

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """执行一次 LLM 对话.

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            tools: 可选的工具定义列表.

        Returns:
            包含 "content" 键的响应字典.

        Raises:
            Exception: 任何连接/超时/认证错误.
        """
        ...


# ======================================================================
# Exceptions
# ======================================================================


class AllSessionsExhaustedError(Exception):
    """所有 LLM Session 均已耗尽 (全部失败)."""

    def __init__(
        self,
        session_errors: list[tuple[int, str, Exception]],
        message: str = "所有 LLM Session 均失败，无法完成请求",
    ) -> None:
        self.session_errors = session_errors
        self.details = "; ".join(
            f"[{idx}]{name}: {exc}" for idx, name, exc in session_errors
        )
        super().__init__(f"{message}. 详情: {self.details}")


# ======================================================================
# MultiLLMFailover
# ======================================================================


class MultiLLMFailover:
    """多 LLM Session 故障转移管理器.

    将一组 LLM Session 组成高可用集群:

        - __init__(sessions): 接收多个 LLM Session 实例.
        - current: 返回当前活跃的 session.
        - chat(messages, tools): 自动故障转移调用.
        - 每个 session 最多 2 次尝试.
        - 全部失败后抛出 AllSessionsExhaustedError.

    Args:
        sessions: LLM Session 实例列表 (至少 1 个).
        event_bus: 可选事件总线, 用于发布 failover 事件.
        session_names: 可选, session 显示名称列表, 默认使用 class name.
        max_retries_per_session: 每个 session 最大尝试次数 (默认 2).
    """

    def __init__(
        self,
        sessions: list[Any],
        *,
        event_bus: Any | None = None,
        session_names: list[str] | None = None,
        max_retries_per_session: int = 2,
    ) -> None:
        if not sessions:
            raise ValueError("至少需要 1 个 LLM Session")
        if max_retries_per_session < 1:
            raise ValueError("max_retries_per_session 必须 >= 1")

        self._sessions = list(sessions)
        self._session_count = len(sessions)
        self._current_idx: int = 0
        self._event_bus = event_bus
        self._max_retries = max_retries_per_session
        self._session_names = session_names or [
            type(s).__name__ for s in sessions
        ]

        # ── 统计指标 ─────────────────────────────────────────────
        self._metrics: list[dict[str, int]] = [
            {"name": name, "attempts": 0, "successes": 0, "failures": 0}
            for name in self._session_names
        ]
        self._total_requests: int = 0
        self._total_failovers: int = 0
        self._last_failover_time: float | None = None

        # ── 历史记录 (保留最近 100 条) ──────────────────────────
        self._failover_history: list[dict[str, Any]] = []

        logger.info(
            "MultiLLMFailover initialized: %d sessions, %d max retries/session",
            self._session_count,
            self._max_retries,
        )

    # ── 属性 ─────────────────────────────────────────────────────

    @property
    def current(self) -> Any:
        """当前活跃的 LLM Session."""
        return self._sessions[self._current_idx]

    @property
    def current_index(self) -> int:
        """当前活跃 session 的索引."""
        return self._current_idx

    @property
    def current_name(self) -> str:
        """当前活跃 session 的名称."""
        return self._session_names[self._current_idx]

    @property
    def sessions(self) -> list[Any]:
        """所有 LLM Session 列表 (只读)."""
        return list(self._sessions)

    @property
    def metrics(self) -> dict[str, Any]:
        """返回全部统计指标."""
        return {
            "total_requests": self._total_requests,
            "total_failovers": self._total_failovers,
            "last_failover_time": self._last_failover_time,
            "active_session_index": self._current_idx,
            "active_session": self.current_name,
            "sessions": list(self._metrics),
        }

    # ── 公共方法 ────────────────────────────────────────────────

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """执行一次带有故障转移的 LLM 对话.

        流程:
            1. 从当前 session 开始.
            2. 每个 session 最多尝试 max_retries_per_session 次.
            3. 成功后返回并记录 metrics.
            4. 失败后切换到下一个 session (如果有).
            5. 全部失败则抛出 AllSessionsExhaustedError.

        Args:
            messages: 消息列表.
            tools: 可选工具定义列表.

        Returns:
            响应字典, 包含 "content" 键.

        Raises:
            AllSessionsExhaustedError: 所有 session 均失败.
        """
        self._total_requests += 1
        request_id = uuid.uuid4().hex[:12]
        all_errors: list[tuple[int, str, Exception]] = []

        # 从当前 session 开始, 遍历全部 session
        for offset in range(self._session_count):
            idx = (self._current_idx + offset) % self._session_count
            session = self._sessions[idx]
            name = self._session_names[idx]

            for attempt in range(self._max_retries):
                self._metrics[idx]["attempts"] += 1
                try:
                    start = time.monotonic()
                    response = await session.chat(messages, tools=tools)
                    elapsed = time.monotonic() - start

                    # ── 成功 ─────────────────────────────────
                    self._metrics[idx]["successes"] += 1
                    self._current_idx = idx

                    if attempt > 0 or offset > 0:
                        self._total_failovers += 1
                        self._last_failover_time = time.time()
                        self._record_failover(
                            request_id=request_id,
                            succeeded_index=idx,
                            succeeded_name=name,
                            attempt=attempt,
                            after_failures=list(all_errors),
                        )

                    logger.info(
                        "MultiLLMFailover.chat SUCCESS [session=%s idx=%d "
                        "attempt=%d elapsed=%.2fs request=%s]",
                        name,
                        idx,
                        attempt + 1,
                        elapsed,
                        request_id,
                    )
                    return response

                except Exception as exc:
                    self._metrics[idx]["failures"] += 1
                    all_errors.append((idx, name, exc))
                    remaining = self._max_retries - attempt - 1

                    log_level = logger.warning if remaining > 0 else logger.error
                    log_level(
                        "MultiLLMFailover.chat FAILURE [session=%s idx=%d "
                        "attempt=%d/%d request=%s]: %s",
                        name,
                        idx,
                        attempt + 1,
                        self._max_retries,
                        request_id,
                        exc,
                    )

                    # 此 session 还有重试次数 → 继续尝试
                    if remaining > 0:
                        continue

                    # 此 session 已耗尽, 如果还有下一个 session 则切换
                    if offset < self._session_count - 1:
                        next_idx = (idx + 1) % self._session_count
                        next_name = self._session_names[next_idx]
                        logger.warning(
                            "MultiLLMFailover: session '%s' exhausted, "
                            "failing over to '%s' (request=%s)",
                            name,
                            next_name,
                            request_id,
                        )
                        # 发布 failover 事件
                        await self._publish_failover_event(
                            from_session=name,
                            to_session=next_name,
                            error=str(exc),
                            request_id=request_id,
                        )

        # ── 所有 session 全部失败 ──────────────────────────────
        self._total_failovers += 1
        self._last_failover_time = time.time()

        logger.error(
            "MultiLLMFailover.chat ALL SESSIONS EXHAUSTED "
            "(request=%s, %d errors)",
            request_id,
            len(all_errors),
        )

        await self._publish_all_exhausted_event(
            errors=all_errors,
            request_id=request_id,
        )

        raise AllSessionsExhaustedError(all_errors)

    async def close(self) -> None:
        """关闭所有 session (调用每个 session 的 close 方法, 如果存在)."""
        for idx, session in enumerate(self._sessions):
            name = self._session_names[idx]
            if hasattr(session, "close"):
                try:
                    if asyncio.iscoroutinefunction(session.close):
                        await session.close()
                    else:
                        session.close()
                    logger.debug("MultiLLMFailover: closed session '%s'", name)
                except Exception as exc:
                    logger.warning(
                        "MultiLLMFailover: error closing session '%s': %s",
                        name,
                        exc,
                    )

    def reset(self) -> None:
        """重置到第一个 session 并清空统计."""
        self._current_idx = 0
        self._total_requests = 0
        self._total_failovers = 0
        self._last_failover_time = None
        self._metrics = [
            {"name": name, "attempts": 0, "successes": 0, "failures": 0}
            for name in self._session_names
        ]

    # ── 内部方法 ────────────────────────────────────────────────

    def _record_failover(
        self,
        request_id: str,
        succeeded_index: int,
        succeeded_name: str,
        attempt: int,
        after_failures: list[tuple[int, str, Exception]],
    ) -> None:
        """记录一次故障转移事件到历史."""
        record = {
            "timestamp": time.time(),
            "request_id": request_id,
            "succeeded_session": succeeded_name,
            "succeeded_index": succeeded_index,
            "attempt": attempt + 1,
            "previous_failures": [
                {"index": idx, "name": name, "error": str(exc)}
                for idx, name, exc in after_failures
            ],
        }
        self._failover_history.append(record)
        # 保留最近 100 条
        if len(self._failover_history) > 100:
            self._failover_history = self._failover_history[-100:]

    async def _publish_failover_event(
        self,
        from_session: str,
        to_session: str,
        error: str,
        request_id: str,
    ) -> None:
        """发布 session 故障转移事件到 event bus."""
        if self._event_bus is None:
            return
        try:
            await self._event_bus.publish(
                {
                    "type": "llm.failover",
                    "source": "MultiLLMFailover",
                    "payload": {
                        "from_session": from_session,
                        "to_session": to_session,
                        "error": error,
                        "request_id": request_id,
                        "timestamp": time.time(),
                    },
                }
            )
        except Exception as exc:
            logger.warning(
                "MultiLLMFailover: failed to publish failover event: %s",
                exc,
            )

    async def _publish_all_exhausted_event(
        self,
        errors: list[tuple[int, str, Exception]],
        request_id: str,
    ) -> None:
        """发布全部 session 耗尽事件."""
        if self._event_bus is None:
            return
        try:
            await self._event_bus.publish(
                {
                    "type": "llm.all_sessions_exhausted",
                    "source": "MultiLLMFailover",
                    "payload": {
                        "request_id": request_id,
                        "session_count": self._session_count,
                        "errors": [
                            {"index": idx, "name": name, "error": str(exc)}
                            for idx, name, exc in errors
                        ],
                        "timestamp": time.time(),
                    },
                }
            )
        except Exception as exc:
            logger.warning(
                "MultiLLMFailover: failed to publish exhausted event: %s",
                exc,
            )

    def __repr__(self) -> str:
        return (
            f"<MultiLLMFailover sessions={self._session_count} "
            f"active={self.current_name} "
            f"requests={self._total_requests} "
            f"failovers={self._total_failovers}>"
        )
