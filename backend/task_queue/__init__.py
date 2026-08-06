"""异步任务队列系统 — 支持名片AI扫描/匹配/通知/导出等后台任务。

基于 asyncio.Queue 的轻量级后台任务队列，无需外部依赖（如 Redis），
与应用进程同生命周期。支持任务优先级、结果回调、超时和重试。

任务类型枚举:
    - SCAN_CARD:    名片AI扫描/OCR处理
    - MATCH_REQUEST: 名片匹配请求
    - SEND_NOTIFICATION: 通知推送（邮件/IM/站内信）
    - EXPORT_DATA:   数据导出（CSV/Excel/PDF）
"""

from __future__ import annotations

import enum
import logging
from typing import Any, Callable, Coroutine, TypeVar

from task_queue.worker import AsyncTaskQueue, Task

logger = logging.getLogger(__name__)

# ── 任务类型枚举 ──────────────────────────────────────────────────────


class TaskType(str, enum.Enum):
    """标准后台任务类型。"""

    SCAN_CARD = "scan_card"              # 名片AI扫描/OCR
    MATCH_REQUEST = "match_request"      # 名片匹配请求
    SEND_NOTIFICATION = "send_notification"  # 通知推送
    EXPORT_DATA = "export_data"          # 数据导出


# ── 任务处理器类型签名 ───────────────────────────────────────────────

HandlerFunc = Callable[[dict[str, Any]], Coroutine[Any, Any, Any]]
"""异步任务处理器签名: async def handler(ctx: dict) -> Any"""

# ── 全局单例 ──────────────────────────────────────────────────────────

_task_queue: AsyncTaskQueue | None = None
"""全局任务队列单例。由 init_task_queue() 创建。"""


# ── 生命周期管理 ──────────────────────────────────────────────────────


def get_task_queue() -> AsyncTaskQueue:
    """获取全局任务队列单例。

    Returns:
        AsyncTaskQueue 实例。

    Raises:
        RuntimeError: 如果队列尚未初始化（未调用 init_task_queue）。
    """
    if _task_queue is None:
        raise RuntimeError(
            "TaskQueue not initialized. Call init_task_queue() first."
        )
    return _task_queue


async def init_task_queue(
    max_workers: int = 4,
    max_queue_size: int = 0,
    register_default_handlers: bool = True,
) -> AsyncTaskQueue:
    """初始化全局任务队列并启动工作线程。

    Args:
        max_workers: 并发工作协程数（默认 4）。
        max_queue_size: 队列最大长度（0 = 无限）。
        register_default_handlers: 是否注册内置默认处理器。

    Returns:
        AsyncTaskQueue 实例。

    Example:
        await init_task_queue(max_workers=8)
    """
    global _task_queue

    if _task_queue is not None:
        logger.warning("TaskQueue already initialized, reusing existing instance")
        return _task_queue

    _task_queue = AsyncTaskQueue(
        max_workers=max_workers,
        max_queue_size=max_queue_size,
    )

    # 注册默认任务处理器
    if register_default_handlers:
        _register_default_handlers(_task_queue)

    await _task_queue.start()
    logger.info(
        "TaskQueue initialized: max_workers=%d, max_queue_size=%s",
        max_workers,
        max_queue_size if max_queue_size > 0 else "unlimited",
    )
    return _task_queue


async def shutdown_task_queue() -> None:
    """关闭全局任务队列，等待所有进行中的任务完成。

    在 FastAPI 的 shutdown 事件中调用。
    """
    global _task_queue

    if _task_queue is None:
        logger.debug("TaskQueue not initialized, nothing to shut down")
        return

    logger.info("Shutting down TaskQueue...")
    await _task_queue.stop()
    _task_queue = None
    logger.info("TaskQueue shut down complete")


# ── 便捷入队函数 ────────────────────────────────────────────────────


async def enqueue(
    task_type: str | TaskType,
    payload: dict[str, Any],
    *,
    priority: int = 0,
    timeout: float | None = None,
    max_retries: int = 0,
    metadata: dict[str, Any] | None = None,
) -> str:
    """便捷入队函数 — 将任务提交到全局队列。

    Args:
        task_type: 任务类型（TaskType 枚举值或字符串）。
        payload: 任务数据字典。
        priority: 优先级（数值越大优先级越高，默认 0）。
        timeout: 超时秒数（None = 不超时）。
        max_retries: 失败重试次数（默认 0 = 不重试）。
        metadata: 附加元数据（如 request_id, user_id 等）。

    Returns:
        任务 ID（UUID 字符串）。

    Raises:
        RuntimeError: 如果队列未初始化。

    Example:
        task_id = await enqueue(
            TaskType.SCAN_CARD,
            {"card_id": "abc123", "image_url": "..."},
            priority=10,
            metadata={"user_id": "u_001"},
        )
    """
    q = get_task_queue()
    return await q.enqueue(
        task_type=str(task_type),
        payload=payload,
        priority=priority,
        timeout=timeout,
        max_retries=max_retries,
        metadata=metadata,
    )


def enqueue_nowait(
    task_type: str | TaskType,
    payload: dict[str, Any],
    *,
    priority: int = 0,
    timeout: float | None = None,
    max_retries: int = 0,
    metadata: dict[str, Any] | None = None,
) -> str:
    """非异步入队 — 在同步上下文中将任务提交到全局队列。

    适用于 FastAPI 路由中的同步端点。

    Args:
        同 enqueue()。

    Returns:
        任务 ID。

    Raises:
        RuntimeError: 如果队列未初始化。
    """
    import asyncio

    q = get_task_queue()
    # 获取或创建事件循环，立即入队
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # 已经在事件循环中 — 创建任务
        future = asyncio.run_coroutine_threadsafe(
            q.enqueue(
                task_type=str(task_type),
                payload=payload,
                priority=priority,
                timeout=timeout,
                max_retries=max_retries,
                metadata=metadata,
            ),
            loop,
        )
        return future.result()
    else:
        return loop.run_until_complete(
            q.enqueue(
                task_type=str(task_type),
                payload=payload,
                priority=priority,
                timeout=timeout,
                max_retries=max_retries,
                metadata=metadata,
            )
        )


# ── 默认任务处理器注册 ──────────────────────────────────────────────


def _register_default_handlers(queue: AsyncTaskQueue) -> None:
    """注册内置的默认任务处理器。

    这些处理器是骨架实现，实际业务逻辑应由具体服务层替换或扩展。
    """
    from task_queue.handlers import (
        handle_export_data,
        handle_match_request,
        handle_scan_card,
        handle_send_notification,
    )

    queue.register_handler(TaskType.SCAN_CARD.value, handle_scan_card)
    queue.register_handler(TaskType.MATCH_REQUEST.value, handle_match_request)
    queue.register_handler(TaskType.SEND_NOTIFICATION.value, handle_send_notification)
    queue.register_handler(TaskType.EXPORT_DATA.value, handle_export_data)

    logger.debug("Default task handlers registered: %s", [t.value for t in TaskType])


# ── 队列统计信息（用于 /health 或 /metrics 端点） ────────────────────


def get_queue_stats() -> dict[str, Any]:
    """获取任务队列统计信息。

    Returns:
        包含队列统计数据的字典。

    Example:
        >>> get_queue_stats()
        {
            "pending": 3,
            "running": 2,
            "completed_total": 150,
            "failed_total": 2,
            "workers_active": 4,
            "workers_idle": 0,
        }
    """
    if _task_queue is None:
        return {"status": "not_initialized"}
    return _task_queue.stats()


__all__ = [
    "AsyncTaskQueue",
    "Task",
    "TaskType",
    "HandlerFunc",
    "init_task_queue",
    "shutdown_task_queue",
    "enqueue",
    "enqueue_nowait",
    "get_task_queue",
    "get_queue_stats",
]
