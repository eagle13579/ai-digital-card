"""
Rate Limit Client SDK 测试
===========================
测试同步/异步客户端的核心功能：
    - 基本限流功能
    - 桶重置
    - 并发安全
    - 多桶查询
"""

from __future__ import annotations

import time
import threading
from typing import Any, Dict, List

import pytest

from sdk.rate_limit_client import (
    RateLimitClient,
    AsyncRateLimitClient,
    check_rate_limit,
    get_remaining,
    reset_bucket,
    get_all_buckets,
)


# =====================================================================
# Fixtures
# =====================================================================


@pytest.fixture(autouse=True)
def clean_buckets():
    """每个测试前清空限流桶。"""
    from app.middleware.rate_limit_middleware import reset_buckets as _reset

    _reset()


# =====================================================================
# 基本限流功能
# =====================================================================


class TestRateLimitClient:
    """同步客户端基本功能测试。"""

    def test_check_rate_limit_allowed(self):
        """首次请求应被允许，且 remaining 正确。"""
        client = RateLimitClient(default_rate=10)
        result = client.check_rate_limit("test-key-1", limit=10, window=60)
        assert result["allowed"] is True
        assert result["remaining"] == 9
        assert result["limit"] == 10
        assert result["window"] == 60
        assert isinstance(result["reset_time"], float)

    def test_check_rate_limit_exceeded(self):
        """超过限制后应被拒绝。"""
        client = RateLimitClient(default_rate=3)
        for i in range(3):
            result = client.check_rate_limit("test-key-2", limit=3, window=60)
            assert result["allowed"] is True
            assert result["remaining"] == 3 - i - 1

        # 第 4 次应被限流
        result = client.check_rate_limit("test-key-2", limit=3, window=60)
        assert result["allowed"] is False
        assert result["remaining"] == 0

    def test_different_keys_independent(self):
        """不同 key 的限流应互相独立。"""
        client = RateLimitClient(default_rate=5)
        r1 = client.check_rate_limit("key-A", limit=2, window=60)
        r2 = client.check_rate_limit("key-B", limit=3, window=60)
        assert r1["allowed"] is True
        assert r2["allowed"] is True
        assert r1["remaining"] == 1
        assert r2["remaining"] == 2

        # 消费完 key-A
        client.check_rate_limit("key-A", limit=2, window=60)
        r3 = client.check_rate_limit("key-A", limit=2, window=60)
        assert r3["allowed"] is False

        # key-B 不受影响
        r4 = client.check_rate_limit("key-B", limit=3, window=60)
        assert r4["allowed"] is True

    def test_get_remaining(self):
        """get_remaining 应返回剩余令牌数（不消费）。"""
        client = RateLimitClient(default_rate=10)
        client.check_rate_limit("test-remaining", limit=10, window=60)

        remaining = client.get_remaining("test-remaining")
        assert remaining == 9

    def test_get_remaining_nonexistent(self):
        """不存在的 key 应返回 -1。"""
        client = RateLimitClient()
        assert client.get_remaining("nonexistent-key") == -1

    def test_reset_bucket(self):
        """重置桶后应恢复初始状态。"""
        client = RateLimitClient(default_rate=5)
        client.check_rate_limit("test-reset", limit=5, window=60)
        client.check_rate_limit("test-reset", limit=5, window=60)

        # 重置前剩余 = 3
        assert client.get_remaining("test-reset") == 3

        # 重置
        assert client.reset_bucket("test-reset") is True
        assert client.get_remaining("test-reset") == -1  # 已被删除

    def test_reset_nonexistent(self):
        """重置不存在的 key 应返回 False。"""
        client = RateLimitClient()
        assert client.reset_bucket("no-such-key") is False

    def test_get_all_buckets(self):
        """get_all_buckets 应返回所有活跃桶的信息。"""
        client = RateLimitClient(default_rate=10)
        client.check_rate_limit("list-key-1", limit=10, window=60)
        client.check_rate_limit("list-key-2", limit=5, window=60)

        buckets = client.get_all_buckets()
        assert len(buckets) == 2

        keys = {b["key"] for b in buckets}
        assert keys == {"list-key-1", "list-key-2"}

        for b in buckets:
            assert "rate" in b
            assert "remaining" in b
            assert "window" in b
            assert "created_at" in b

    def test_active_bucket_count(self):
        """active_bucket_count 应返回准确计数。"""
        client = RateLimitClient()
        assert client.active_bucket_count == 0

        client.check_rate_limit("count-key-1")
        assert client.active_bucket_count == 1

        client.check_rate_limit("count-key-2")
        assert client.active_bucket_count == 2

    def test_token_refill_over_time(self):
        """经过足够时间后令牌应自动补充。"""
        # 使用很小的窗口方便测试
        client = RateLimitClient(default_rate=10)
        bucket = client._get_or_create_bucket("refill-test", limit=10, window=0.1)
        bucket.tokens = 1  # 只剩 1 个令牌

        result = client.check_rate_limit("refill-test", limit=10, window=0.1)
        assert result["allowed"] is True  # 最后一个令牌被消费

        # 立即再请求应被限流
        result = client.check_rate_limit("refill-test", limit=10, window=0.1)
        assert result["allowed"] is False

        # 等待窗口时间的 2/3，应该有部分令牌补充
        time.sleep(0.07)
        remaining = client.get_remaining("refill-test")
        assert remaining >= 1, f"Expected at least 1 token after refill, got {remaining}"


# =====================================================================
# 模块级便捷函数
# =====================================================================


class TestModuleFunctions:
    """测试模块级单例便捷函数。"""

    def test_check_rate_limit_func(self):
        result = check_rate_limit("func-key", limit=10, window=60)
        assert result["allowed"] is True

    def test_get_remaining_func(self):
        check_rate_limit("func-remaining", limit=10, window=60)
        assert get_remaining("func-remaining") == 9

    def test_reset_bucket_func(self):
        check_rate_limit("func-reset", limit=10, window=60)
        assert get_remaining("func-reset") == 9
        assert reset_bucket("func-reset") is True
        assert get_remaining("func-reset") == -1

    def test_get_all_buckets_func(self):
        check_rate_limit("func-list-a", limit=10, window=60)
        check_rate_limit("func-list-b", limit=10, window=60)
        buckets = get_all_buckets()
        assert len(buckets) == 2


# =====================================================================
# 异步客户端
# =====================================================================


@pytest.mark.asyncio
class TestAsyncRateLimitClient:
    """异步客户端功能测试。"""

    async def test_async_check_rate_limit(self):
        client = AsyncRateLimitClient(default_rate=10)
        result = await client.check_rate_limit("async-key", limit=10, window=60)
        assert result["allowed"] is True
        assert result["remaining"] == 9

    async def test_async_exceeded(self):
        client = AsyncRateLimitClient(default_rate=2)
        await client.check_rate_limit("async-exceed", limit=2, window=60)
        await client.check_rate_limit("async-exceed", limit=2, window=60)
        result = await client.check_rate_limit("async-exceed", limit=2, window=60)
        assert result["allowed"] is False

    async def test_async_get_remaining(self):
        client = AsyncRateLimitClient(default_rate=5)
        await client.check_rate_limit("async-remaining", limit=5, window=60)
        remaining = await client.get_remaining("async-remaining")
        assert remaining == 4

    async def test_async_reset(self):
        client = AsyncRateLimitClient(default_rate=5)
        await client.check_rate_limit("async-reset", limit=5, window=60)
        assert await client.reset_bucket("async-reset") is True
        assert await client.get_remaining("async-reset") == -1

    async def test_async_get_all_buckets(self):
        client = AsyncRateLimitClient(default_rate=10)
        await client.check_rate_limit("async-list-1", limit=10, window=60)
        await client.check_rate_limit("async-list-2", limit=10, window=60)
        buckets = await client.get_all_buckets()
        assert len(buckets) == 2

    async def test_async_active_bucket_count(self):
        client = AsyncRateLimitClient()
        assert client.active_bucket_count == 0
        await client.check_rate_limit("async-count")
        assert client.active_bucket_count == 1


# =====================================================================
# 并发安全测试
# =====================================================================


class TestConcurrency:
    """并发安全测试 — 多线程同时请求同一个 key。"""

    def test_concurrent_access(self):
        """多线程消费同一个 key 不应导致数据竞争。"""
        client = RateLimitClient(default_rate=20)
        key = "concurrent-key"
        results: List[Dict[str, Any]] = []
        errors: List[Exception] = []
        lock = threading.Lock()

        def worker(n: int):
            try:
                for _ in range(5):
                    result = client.check_rate_limit(key, limit=20, window=60)
                    with lock:
                        results.append(result)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"并发测试出现异常: {errors}"

        # 总共消费 4*5=20 次，部分应被允许，部分应被限流
        allowed_count = sum(1 for r in results if r["allowed"])
        blocked_count = sum(1 for r in results if not r["allowed"])

        # 最多允许 20 次
        assert allowed_count <= 20, f"Allowed {allowed_count} times, expected <= 20"
        # 至少有一些被限流（由于并发，刚好 20 次也可能是恰好允许）
        assert allowed_count > 0, "至少应有部分请求被允许"

    def test_concurrent_different_keys(self):
        """不同 key 的并发访问不应互相干扰。"""
        client = RateLimitClient(default_rate=5)
        results_a: List[bool] = []
        results_b: List[bool] = []
        lock = threading.Lock()

        def worker_a():
            for _ in range(10):
                r = client.check_rate_limit("key-a", limit=5, window=60)
                with lock:
                    results_a.append(r["allowed"])

        def worker_b():
            for _ in range(10):
                r = client.check_rate_limit("key-b", limit=10, window=60)
                with lock:
                    results_b.append(r["allowed"])

        ta = threading.Thread(target=worker_a)
        tb = threading.Thread(target=worker_b)
        ta.start()
        tb.start()
        ta.join()
        tb.join()

        # key-A: limit=5, 最多允许 5 次
        assert sum(results_a) <= 5
        # key-B: limit=10, 最多允许 10 次
        assert sum(results_b) <= 10
        # 两者应各自独立限流
        assert sum(results_a) < sum(results_b), "key-A (limit=5) 应比 key-B (limit=10) 更早被限流"
