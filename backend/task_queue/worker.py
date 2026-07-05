"""异步任务队列工作线程实现 — 基于 asyncio.Queue 的轻量级后台任务引擎。

支持特性:
    - 优先级队列 (高优先级任务先执行)
    - 并发工作协程池
    - 任务超时控制
    - 失败重试 (可配置)
    - 任务结果回调查询
    - 优雅关闭 (等待进行中任务完成)
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


class Priority(IntEnum):
    """任务优先级（数值越大优先级越高）。"""

    LOW = 0
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


# ── 任务状态 ──────────────────────────────────────────────────────────


PENDING = "pending"
RUNNING = "running"
SUCCEEDED = "succeeded"
FAILED = "failed"
TIMEOUT = "timeout"
CANCELLED = "cancelled"


# ── 数据类型 ──────────────────────────────────────────────────────────


@dataclass(order=True)
class PrioritizedItem:
    """支持优先级的队列项，排序规则: 优先级降序 → 入队时间升序。"""

    priority: int
    timestamp: float
    task_id: str = field(compare=False)

    def __init__(self, priority: int, task_id: str) -> None:
        self.priority = priority
        self.timestamp = time.monotonic()
        self.task_id = task_id


@dataclass
class Task:
    """单个任务实例。"""

    task_id: str
    task_type: str
    payload: dict[str, Any]
    priority: int = 0
    timeout: float | None = None  # seconds
    max_retries: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    # 运行时字段
    status: str = PENDING  # TaskStatus value
    retry_count: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    result: Any = None
    error: str | None = None


# Task handler signature
HandlerFunc = Callable[[dict[str, Any]], Coroutine[Any, Any, Any]]


class AsyncTaskQueue:
    """基于 asyncio.PriorityQueue 的轻量级异步任务队列。

    Usage:
        queue = AsyncTaskQueue(max_workers=4)

        # 注册处理器
        async def handle_scan(ctx):
            print(f"Scanning card: {ctx['card_id']}")

        queue.register_handler("scan_card", handle_scan)

        # 启动
        await queue.start()

        # 入队
        await queue.enqueue("scan_card", {"card_id": "abc"})

        # 停止
        await queue.stop()

    Attributes:
        max_workers: 最大并发工作协程数。
        max_queue_size: 队列最大长度（0 = 无限）。
    """

    def __init__(
        self,
        max_workers: int = 4,
        max_queue_size: int = 0,
    ) -> None:
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size

        # 优先级队列: (PrioritizedItem, Task)
        self._queue: asyncio.PriorityQueue[tuple[PrioritizedItem, Task]] = (
            asyncio.PriorityQueue(maxsize=max_queue_size)
        )

        # 已注册的任务类型 → 处理器映射
        self._handlers: dict[str, HandlerFunc] = {}

        # 运行状态
        self._running = False
        self._workers: list[asyncio.Task[None]] = []
        self._tasks: dict[str, Task] = {}  # task_id -> Task
        self._lock = asyncio.Lock()

    # ── 生命周期 ───────────────────────────────────────────────────────

    async def start(self) -> None:
        """启动工作协程池。"""
        if self._running:
            logger.warning("TaskQueue already running")
            return

        self._running = True
        self._workers = [
            asyncio.create_task(
                self._worker_loop(worker_id=i),
                name=f"task-queue-worker-{i}",
            )
            for i in range(self.max_workers)
        ]
        logger.debug("Started %d task queue workers", self.max_workers)

    async def stop(self, wait: bool = True, timeout: float = 30.0) -> None:
        """停止任务队列。

        Args:
            wait: 是否等待进行中的任务完成。
            timeout: 等待超时秒数。
        """
        if not self._running:
            return

        self._running = False

        if wait:
            # 等待所有工作协程完成当前任务
            logger.info("Waiting for %d workers to finish...", len(self._workers))
            done, pending = await asyncio.wait(
                self._workers,
                timeout=timeout,
            )
            if pending:
                logger.warning(
                    "%d workers did not finish within %ss, cancelling",
                    len(pending),
                    timeout,
                )
                for t in pending:
                    t.cancel()
        else:
            for w in self._workers:
                w.cancel()

        self._workers.clear()
        logger.info("TaskQueue stopped")

    # ── 处理器注册 ─────────────────────────────────────────────────────

    def register_handler(
        self,
        task_type: str,
        handler: HandlerFunc,
    ) -> None:
        """注册指定任务类型的处理器。

        Args:
            task_type: 任务类型字符串（如 'scan_card'）。
            handler: 异步处理函数，接收 payload dict 作为参数。
        """
        if not asyncio.iscoroutinefunction(handler):
            raise TypeError(f"Handler for '{task_type}' must be an async function")

        self._handlers[task_type] = handler
        logger.debug("Registered handler for task type: %s", task_type)

    def unregister_handler(self, task_type: str) -> None:
        """注销指定任务类型的处理器。"""
        self._handlers.pop(task_type, None)
        logger.debug("Unregistered handler for task type: %s", task_type)

    # ── 入队 ───────────────────────────────────────────────────────────

    async def enqueue(
        self,
        task_type: str,
        payload: dict[str, Any],
        *,
        priority: int = 0,
        timeout: float | None = None,
        max_retries: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """将新任务加入队列。

        Args:
            task_type: 任务类型。
            payload: 任务数据。
            priority: 优先级（数值越大越先执行）。
            timeout: 超时秒数。
            max_retries: 失败重试次数。
            metadata: 附加元数据。

        Returns:
            任务 ID (UUID v4 字符串)。

        Raises:
            asyncio.QueueFull: 如果队列已满（max_queue_size > 0 时）。
        """
        task = Task(
            task_id=uuid.uuid4().hex,
            task_type=task_type,
            payload=payload,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
            metadata=metadata or {},
        )

        item = PrioritizedItem(priority=-priority, task_id=task.task_id)  # 取负 → 高优先级先出队

        async with self._lock:
            self._tasks[task.task_id] = task
            await self._queue.put((item, task))

        logger.debug(
            "Enqueued task %s (type=%s, priority=%d)",
            task.task_id[:8],
            task_type,
            priority,
        )
        return task.task_id

    # ── 查询 ───────────────────────────────────────────────────────────

    def get_task(self, task_id: str) -> Task | None:
        """获取指定任务的状态和结果。"""
        return self._tasks.get(task_id)

    def stats(self) -> dict[str, Any]:
        """获取队列统计信息。"""
        pending = sum(
            1 for t in self._tasks.values() if t.status == PENDING
        )
        running = sum(
            1 for t in self._tasks.values() if t.status == RUNNING
        )
        succeeded = sum(
            1 for t in self._tasks.values() if t.status == SUCCEEDED
        )
        failed = sum(
            1 for t in self._tasks.values() if t.status == FAILED
        )
        active_workers = sum(
            1 for w in self._workers if not w.done()
        ) if self._workers else 0

        return {
            "pending": pending,
            "running": running,
            "succeeded": succeeded,
            "failed": failed,
            "queue_size": self._queue.qsize(),
            "workers_total": self.max_workers,
            "workers_active": active_workers,
            "workers_idle": self.max_workers - active_workers,
        }

    def pending_count(self, task_type: str | None = None) -> int:
        """统计待处理任务数，可按类型过滤。"""
        if task_type:
            return sum(
                1
                for t in self._tasks.values()
                if t.status == PENDING and t.task_type == task_type
            )
        return sum(1 for t in self._tasks.values() if t.status == PENDING)

    # ── 工作协程 ───────────────────────────────────────────────────────

    async def _worker_loop(self, worker_id: int) -> None:
        """工作协程主循环：不断从队列取任务并执行。"""
        logger.debug("Worker-%d started", worker_id)

        while self._running:
            try:
                # 从队列取任务（阻塞直到有任务或队列关闭）
                item, task = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0,  # 每秒唤醒检查 _running 标志
                )
            except asyncio.TimeoutError:
                continue  # 正常超时，重新检查 _running
            except asyncio.CancelledError:
                logger.debug("Worker-%d cancelled", worker_id)
                break

            try:
                await self._execute_task(task)
            except Exception as exc:
                logger.exception(
                    "Worker-%d: unexpected error executing task %s: %s",
                    worker_id,
                    task.task_id[:8],
                    exc,
                )
            finally:
                self._queue.task_done()

        logger.debug("Worker-%d stopped", worker_id)

    async def _execute_task(self, task: Task) -> None:
        """执行单个任务（包括超时、重试、结果处理）。"""
        handler = self._handlers.get(task.task_type)
        if handler is None:
            logger.error(
                "No handler registered for task type '%s' (task %s)",
                task.task_type,
                task.task_id[:8],
            )
            task.status = FAILED
            task.error = f"No handler for task type: {task.task_type}"
            return

        while task.retry_count <= task.max_retries:
            # 标记为运行中
            task.status = RUNNING
            task.started_at = time.time()

            try:
                # 执行处理器（支持超时）
                if task.timeout is not None and task.timeout > 0:
                    task.result = await asyncio.wait_for(
                        handler(task.payload),
                        timeout=task.timeout,
                    )
                else:
                    task.result = await handler(task.payload)

                task.status = SUCCEEDED
                task.completed_at = time.time()
                logger.info(
                    "Task %s (%s) completed in %.2fs",
                    task.task_id[:8],
                    task.task_type,
                    task.completed_at - task.started_at,
                )
                return

            except asyncio.TimeoutError:
                task.status = TIMEOUT
                task.error = f"Task timed out after {task.timeout}s"
                logger.warning(
                    "Task %s (%s) timed out after %ss",
                    task.task_id[:8],
                    task.task_type,
                    task.timeout,
                )
                # 超时不重试
                return

            except Exception as exc:
                task.retry_count += 1
                task.error = f"{type(exc).__name__}: {exc}"
                logger.warning(
                    "Task %s (%s) failed (attempt %d/%d): %s",
                    task.task_id[:8],
                    task.task_type,
                    task.retry_count,
                    task.max_retries + 1,
                    exc,
                )

                if task.retry_count > task.max_retries:
                    task.status = FAILED
                    task.completed_at = time.time()
                    logger.error(
                        "Task %s (%s) failed after %d attempts",
                        task.task_id[:8],
                        task.task_type,
                        task.retry_count,
                    )
                else:
                    # 指数退避重试
                    backoff = min(2 ** (task.retry_count - 1), 30)
                    logger.info(
                        "Retrying task %s in %ds (attempt %d/%d)",
                        task.task_id[:8],
                        backoff,
                        task.retry_count,
                        task.max_retries + 1,
                    )
                    await asyncio.sleep(backoff)


# ── 便捷工厂 ──────────────────────────────────────────────────────────


def create_task_queue(
    max_workers: int = 4,
    max_queue_size: int = 0,
) -> AsyncTaskQueue:
    """创建并返回一个新的 AsyncTaskQueue 实例。

    Args:
        max_workers: 并发工作协程数。
        max_queue_size: 队列最大长度（0 = 无限）。

    Returns:
        未启动的 AsyncTaskQueue 实例（需要调用 start()）。
    """
    return AsyncTaskQueue(max_workers=max_workers, max_queue_size=max_queue_size)
