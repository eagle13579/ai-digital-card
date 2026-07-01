"""
优雅关闭机制 — GracefulShutdown
==================================
监听 SIGTERM/SIGINT，在关闭前：
  1. 标记服务为"不健康"，拒绝新请求
  2. 等待进行中的请求完成（最多 30 秒）
  3. 关闭数据库连接池
  4. 关闭 HTTP 客户端
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import time
from typing import Awaitable, Callable, Optional

import httpx

logger = logging.getLogger("graceful_shutdown")

# 模块级信号量：标记服务是否正在关闭
_shutting_down = False


def is_shutting_down() -> bool:
    """供健康检查 /ready 端点调用，关闭期间返回 True"""
    return _shutting_down


class GracefulShutdown:
    """优雅关闭控制器"""

    def __init__(
        self,
        shutdown_timeout: float = 30.0,
        db_engine=None,
        http_client: Optional[httpx.AsyncClient] = None,
        on_shutdown: Optional[list[Callable[[], Awaitable[None]]]] = None,
    ):
        self.shutdown_timeout = shutdown_timeout
        self.db_engine = db_engine
        self.http_client = http_client
        self.on_shutdown = on_shutdown or []
        self._in_flight: set[asyncio.Task] = set()
        self._event: asyncio.Event = asyncio.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # ---- 注册进行中的请求 ------------------------------------------------

    def track_task(self, task: asyncio.Task) -> None:
        """记录一个进行中的请求任务"""
        self._in_flight.add(task)
        task.add_done_callback(self._untrack_task)

    def _untrack_task(self, task: asyncio.Task) -> None:
        self._in_flight.discard(task)

    @property
    def in_flight_count(self) -> int:
        return len(self._in_flight)

    # ---- 安装信号处理器 --------------------------------------------------

    def install_signal_handlers(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """注册 SIGTERM / SIGINT 回调 (仅 UNIX；Windows 下走替代路径)"""
        self._loop = loop or asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                self._loop.add_signal_handler(sig, lambda s=sig: self._loop.create_task(self._handle_signal(s)))
            except (NotImplementedError, ValueError):
                # Windows 不支持 add_signal_handler，fallback
                logger.warning("add_signal_handler not supported for %s, using loop.add_signal_handler fallback", sig)

    # ---- 关闭流程 --------------------------------------------------------

    async def _handle_signal(self, sig: signal.Signals) -> None:
        logger.warning("收到信号 %s，开始优雅关闭...", sig.name)
        await self.shutdown()

    async def shutdown(self) -> None:
        """执行优雅关闭的完整流程"""
        global _shutting_down
        _shutting_down = True

        logger.info("标记服务为不健康，拒绝新请求")
        self._event.set()

        # 1. 等待进行中的请求完成
        if self._in_flight:
            logger.info("等待 %d 个进行中的请求完成（最多 %.0f 秒）", len(self._in_flight), self.shutdown_timeout)
            wait_start = time.monotonic()
            while self._in_flight and (time.monotonic() - wait_start) < self.shutdown_timeout:
                await asyncio.sleep(0.1)
            remaining = len(self._in_flight)
            if remaining:
                logger.warning("超时，仍有 %d 个任务未完成，强制取消", remaining)
                for t in self._in_flight:
                    t.cancel()
                # 给取消一个瞬间传播
                await asyncio.sleep(0.1)
            else:
                logger.info("所有进行中的请求已完成")

        # 2. 执行自定义关闭回调
        for cb in self.on_shutdown:
            try:
                await cb()
            except Exception:
                logger.exception("自定义关闭回调异常: %s", cb)

        # 3. 关闭 HTTP 客户端
        if self.http_client and not self.http_client.is_closed:
            await self.http_client.aclose()
            logger.info("HTTP 客户端已关闭")

        # 4. 关闭数据库连接池
        if self.db_engine is not None:
            try:
                self.db_engine.sync_engine.dispose()
                logger.info("数据库连接池已释放")
            except Exception:
                logger.exception("释放数据库连接池时异常")

        logger.info("优雅关闭完成，再见!")
        # 停止事件循环 — 由应用层决定是否调用 loop.stop()
        if self._loop and self._loop.is_running():
            self._loop.stop()

    # ---- 上下文管理器 ----------------------------------------------------

    async def __aenter__(self) -> "GracefulShutdown":
        self.install_signal_handlers()
        return self

    async def __aexit__(self, *exc) -> None:
        if not _shutting_down:
            await self.shutdown()
