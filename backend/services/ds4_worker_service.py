"""DS4 Worker Service — AI数智名片"""
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class JobPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Job:
    priority: JobPriority = JobPriority.NORMAL
    task_id: str = ""
    payload: Any = None


@dataclass
class JobResult:
    success: bool = False
    data: Any = None
    error: str = ""


class WorkerQueue:
    def __init__(self, worker_name: str = "ds4-worker"):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_name = worker_name
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._handler: Optional[Callable] = None

    def set_handler(self, handler: Callable):
        self._handler = handler

    async def submit(self, job: Job):
        await self._queue.put(job)

    async def worker_loop(self):
        self._running = True
        while self._running:
            try:
                job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                try:
                    if self._handler:
                        await self._handler(job)
                except Exception as e:
                    logger.error(f"Job failed: {e}")
                finally:
                    self._queue.task_done()
            except asyncio.TimeoutError:
                continue

    async def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self.worker_loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
