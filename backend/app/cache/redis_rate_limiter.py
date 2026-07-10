"""
RedisRateLimiter — 基于 Redis 的滑动窗口速率限制器
================================================

使用 Redis Sorted Set 实现滑动窗口限流：
  - 每个限流键对应一个 Sorted Set，member=请求时间戳，score=时间戳
  - 每次请求先清理窗口外的旧记录，再检查窗口内请求数
  - 如果 Redis 不可用，自动降级到内存限流（不崩溃）

滑动窗口 vs 固定窗口：
  - 固定窗口（如计数重置）在边界处可能出现 2 倍流量突刺
  - 滑动窗口在每个请求到达时动态计算窗口区间，更精确

用法:
    from app.cache.redis_rate_limiter import RedisRateLimiter

    limiter = RedisRateLimiter(settings.REDIS_URL)
    allowed, remaining, retry_after = await limiter.check_rate_limit(
        "ratelimit:127.0.0.1:api", max_requests=60, window_seconds=60
    )
"""

from __future__ import annotations

import logging
import time
import threading
from collections import defaultdict
from typing import Optional

logger = logging.getLogger(__name__)


class MemoryRateLimiter:
    """内存滑动窗口速率限制器 — Redis 不可用时的降级方案。

    与 RedisRateLimiter 接口一致，但数据仅存于当前进程内存中，
    重启丢失，多实例不共享。
    """

    def __init__(self) -> None:
        self._visits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int, float]:
        """检查速率限制。

        Args:
            key: 限流键（通常为 "ratelimit:{ip}:{path}"）
            max_requests: 窗口内允许的最大请求数
            window_seconds: 滑动窗口大小（秒）

        Returns:
            (allowed, remaining, retry_after)
            - allowed: True 表示允许通过
            - remaining: 窗口内剩余可用请求数
            - retry_after: 建议重试等待秒数（被限流时）
        """
        now = time.time()
        with self._lock:
            timestamps = self._visits[key]
            cutoff = now - window_seconds

            # 移除窗口外记录
            while timestamps and timestamps[0] < cutoff:
                timestamps.pop(0)

            current_count = len(timestamps)
            if current_count >= max_requests:
                oldest = timestamps[0]
                retry_after = max(0.0, oldest + window_seconds - now)
                return False, 0, retry_after

            # 记录本次请求
            timestamps.append(now)
            remaining = max(0, max_requests - current_count - 1)
            return True, remaining, 0.0


class RedisRateLimiter:
    """基于 Redis Sorted Set 的滑动窗口速率限制器。

    特性:
      - 滑动窗口算法（精度到秒级）
      - Redis 不可用时自动降级到 MemoryRateLimiter
      - 自动清理过期键（TTL = window_seconds * 2）
      - 线程安全

    用法:
        limiter = RedisRateLimiter("redis://localhost:6379/0")
        ok, remaining, retry = await limiter.check_rate_limit(
            "ratelimit:192.168.1.1",
            max_requests=60,
            window_seconds=60,
        )
    """

    def __init__(self, redis_url: str) -> None:
        """初始化 RedisRateLimiter。

        Args:
            redis_url: Redis 连接 URL（如 "redis://localhost:6379/0"）
        """
        self._redis_url = redis_url
        self._redis: Optional[object] = None
        self._memory_fallback = MemoryRateLimiter()
        self._initialized = False

    async def _ensure_redis(self) -> None:
        """惰性初始化 Redis 连接（仅首次调用时连接）。"""
        if self._initialized:
            return
        self._initialized = True
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(
                self._redis_url,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
                decode_responses=True,
            )
            await self._redis.ping()  # type: ignore[union-attr]
            logger.info("RedisRateLimiter: Redis 连接成功 (%s)", self._redis_url)
        except Exception as e:
            logger.warning(
                "RedisRateLimiter: Redis 不可用, 降级到内存限流: %s", e
            )
            self._redis = None

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int, float]:
        """检查速率限制（滑动窗口）。

        算法:
          1. ZREMRANGEBYSCORE 清理窗口外旧记录
          2. ZCARD 获取窗口内当前请求数
          3. 如果 >= max_requests → 返回 429
          4. 否则 ZADD 记录本次请求，设置 TTL

        Args:
            key: 限流键
            max_requests: 窗口内允许的最大请求数
            window_seconds: 滑动窗口大小（秒）

        Returns:
            (allowed, remaining, retry_after)
        """
        await self._ensure_redis()

        # ── Redis 不可用 → 降级到内存限流 ──────────────────────────
        if self._redis is None:
            return self._memory_fallback.check_rate_limit(
                key, max_requests, window_seconds
            )

        now = time.time()
        window_start = now - window_seconds

        try:
            # Step 1: 清理窗口外记录
            removed = await self._redis.zremrangebyscore(  # type: ignore[union-attr]
                key, 0, window_start
            )
            if removed:
                logger.debug("RedisRateLimiter: 清理 %d 条过期记录 (key=%s)", removed, key)

            # Step 2: 获取窗口内当前请求数
            count = await self._redis.zcard(key)  # type: ignore[union-attr]

            # Step 3: 超限判断
            if count >= max_requests:
                # 获取最早的时间戳计算重试时间
                oldest = await self._redis.zrange(  # type: ignore[union-attr]
                    key, 0, 0, withscores=True
                )
                if oldest:
                    retry_after = max(0.0, oldest[0][1] + window_seconds - now)
                else:
                    retry_after = float(window_seconds)
                return False, 0, retry_after

            # Step 4: 记录本次请求
            await self._redis.zadd(key, {str(now): now})  # type: ignore[union-attr]
            # 设置 TTL = 2 倍窗口大小，确保自动清理
            await self._redis.expire(key, window_seconds * 2)  # type: ignore[union-attr]

            remaining = max(0, max_requests - count - 1)
            return True, remaining, 0.0

        except Exception as e:
            logger.warning(
                "RedisRateLimiter: Redis 操作失败, 降级到内存限流: %s", e
            )
            # 连接失效 → 降级到内存
            self._redis = None
            return self._memory_fallback.check_rate_limit(
                key, max_requests, window_seconds
            )
