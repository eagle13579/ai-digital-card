"""
测试: 优雅关闭机制 (GracefulShutdown)
======================================
覆盖:
  - 信号量标记 (is_shutting_down)
  - 追踪/取消追踪任务
  - 关闭流程 (超时等待、强制取消)
  - HTTP 客户端关闭
  - 多次调用幂等
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.graceful_shutdown import GracefulShutdown, is_shutting_down


@pytest.fixture(autouse=True)
def _reset_shutdown_flag():
    """每个测试前重置模块级关闭标记"""
    import app.graceful_shutdown as gs_mod
    gs_mod._shutting_down = False
    yield


class TestGracefulShutdown:
    """GracefulShutdown 单元测试"""

    # ── Fixtures ──────────────────────────────────────────────────────────

    @pytest.fixture
    def gs(self):
        """返回一个干净的 GracefulShutdown 实例"""
        return GracefulShutdown(shutdown_timeout=2.0)

    @pytest.fixture
    def gs_with_client(self):
        """带 mock HTTP 客户端的实例"""
        client = httpx.AsyncClient()
        return GracefulShutdown(shutdown_timeout=1.0, http_client=client), client

    # ── 1. 信号量标记 ─────────────────────────────────────────────────────

    def test_is_shutting_down_default_false(self):
        """默认关闭标记为 False"""
        assert is_shutting_down() is False

    @pytest.mark.asyncio
    async def test_is_shutting_down_becomes_true_after_shutdown(self, gs):
        """调用 shutdown() 后标记变为 True"""
        await gs.shutdown()
        assert is_shutting_down() is True

    # ── 2. 任务追踪 ──────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_track_task_increases_count(self, gs):
        """追踪任务后 in_flight_count 增加"""
        task = asyncio.create_task(asyncio.sleep(10))
        gs.track_task(task)
        assert gs.in_flight_count == 1
        task.cancel()
        await asyncio.sleep(0.05)

    @pytest.mark.asyncio
    async def test_untrack_on_completion(self, gs):
        """任务完成后自动从 in_flight 移除"""
        task = asyncio.create_task(asyncio.sleep(0.01))
        gs.track_task(task)
        await task
        await asyncio.sleep(0.05)
        assert gs.in_flight_count == 0

    # ── 3. 关闭流程 ──────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_shutdown_waits_for_in_flight_tasks(self, gs):
        """关闭等待进行中的任务完成 (不超过超时)"""
        async def short_task():
            await asyncio.sleep(0.1)
        task = asyncio.create_task(short_task())
        gs.track_task(task)

        start = time.monotonic()
        await gs.shutdown()
        elapsed = time.monotonic() - start

        assert elapsed < 1.0          # 不应等到超时
        assert gs.in_flight_count == 0

    @pytest.mark.asyncio
    async def test_shutdown_forces_cancel_on_timeout(self, gs):
        """超时后强制取消残留任务"""
        gs.shutdown_timeout = 0.1     # 极短超时

        cancelled_flag = []

        async def long_task():
            try:
                await asyncio.sleep(999)
            except asyncio.CancelledError:
                cancelled_flag.append(True)

        task = asyncio.create_task(long_task())
        gs.track_task(task)

        await gs.shutdown()
        # 任务应收到 CancelledError
        assert len(cancelled_flag) == 1, "任务应被取消"
        assert task.done()

    # ── 4. HTTP 客户端关闭 ────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_http_client_closed_on_shutdown(self):
        """关闭时 HTTP 客户端应被释放"""
        client = httpx.AsyncClient()
        gs = GracefulShutdown(shutdown_timeout=1.0, http_client=client)
        assert not client.is_closed
        await gs.shutdown()
        assert client.is_closed

    # ── 5. 自定义回调 ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_custom_callbacks_executed(self, gs):
        """自定义关闭回调应按顺序执行"""
        calls = []

        async def cb1():
            calls.append("cb1")
        async def cb2():
            calls.append("cb2")

        gs.on_shutdown = [cb1, cb2]
        await gs.shutdown()
        assert calls == ["cb1", "cb2"]

    # ── 6. 多次调用幂等 ───────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_shutdown_idempotent(self, gs):
        """多次 shutdown() 不应异常"""
        await gs.shutdown()
        await gs.shutdown()          # 第二次调用
        assert is_shutting_down() is True

    # ── 7. 上下文管理器 ───────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """async with 应触发 shutdown"""
        client = httpx.AsyncClient()
        async with GracefulShutdown(shutdown_timeout=1.0, http_client=client) as gs:
            assert not client.is_closed
            assert not is_shutting_down()
        assert client.is_closed
        assert is_shutting_down() is True
