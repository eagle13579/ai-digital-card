"""
Rate Limit 客户端 SDK
======================
为内部微服务提供的速率限制客户端封装。

功能:
    - check_rate_limit(key, limit, window)  — 检查某个 key 是否超过限流
    - get_remaining(key)                     — 查询某个 key 的剩余请求数
    - reset_bucket(key)                      — 重置某个 key 的限流桶
    - get_all_buckets()                      — 获取所有活跃的限流桶信息

支持同步 (RateLimitClient) 和异步 (AsyncRateLimitClient) 两种使用模式。

注意:
    当前版本直接操作内存存储（与 middleware/rate_limit_middleware.py 共享 _IP_BUCKETS）。
    在分布式微服务场景下，应使用 Redis 等集中式存储替代内存 dict。
"""

from __future__ import annotations

import time
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.middleware.rate_limit_middleware import (
    _IP_BUCKETS,
    TokenBucket,
    _get_bucket_for_ip,
    reset_buckets as _reset_all,
    get_bucket_count,
)

logger = logging.getLogger("chainke.sdk.ratelimit")

# =====================================================================
# 同步客户端
# =====================================================================


class RateLimitClient:
    """Rate Limit 同步客户端。

    直接操作进程内共享的 TokenBucket 存储。
    适用于同进程服务间调用。
    """

    def __init__(
        self,
        default_rate: int = 60,
        auth_rate: int = 10,
        admin_rate: int = 120,
    ) -> None:
        self.default_rate = default_rate
        self.auth_rate = auth_rate
        self.admin_rate = admin_rate

    # -----------------------------------------------------------------
    # 公开 API
    # -----------------------------------------------------------------

    def check_rate_limit(
        self,
        key: str,
        limit: Optional[int] = None,
        window: int = 60,
    ) -> Dict[str, Any]:
        """检查指定 key 是否被限流。

        Args:
            key:    限流标识（如 IP、用户ID、API Key）
            limit:  窗口内允许的最大请求数（None = 使用默认速率）
            window: 时间窗口（秒），默认 60 秒

        Returns:
            {
                "allowed": bool,       # True=允许, False=被限流
                "remaining": int,      # 剩余请求数
                "reset_time": float,   # 重置时间 (Unix timestamp)
                "limit": int,          # 速率上限
                "window": int,         # 时间窗口（秒）
            }
        """
        bucket = self._get_or_create_bucket(key, limit, window)
        allowed, remaining, reset_time = bucket.consume()
        return {
            "allowed": allowed,
            "remaining": remaining,
            "reset_time": reset_time,
            "limit": bucket.rate,
            "window": bucket.per_second,
        }

    def get_remaining(self, key: str) -> int:
        """查询指定 key 的剩余请求数（不消费令牌）。

        Args:
            key: 限流标识

        Returns:
            剩余请求数（-1 表示该 key 不存在）
        """
        cached = _IP_BUCKETS.get(key)
        if not cached:
            return -1
        bucket, _ = cached
        bucket._refill()  # 先补充
        return int(bucket.tokens)

    def reset_bucket(self, key: str) -> bool:
        """重置指定 key 的限流桶。

        Args:
            key: 限流标识

        Returns:
            True=成功重置, False=该 key 不存在
        """
        if key in _IP_BUCKETS:
            del _IP_BUCKETS[key]
            logger.info("[SDK] 已重置限流桶: key=%s", key)
            return True
        return False

    def get_all_buckets(self) -> List[Dict[str, Any]]:
        """获取所有活跃的限流桶信息。

        Returns:
            [
                {
                    "key": str,
                    "rate": int,
                    "remaining": int,
                    "window": int,
                    "created_at": float,
                },
                ...
            ]
        """
        results: List[Dict[str, Any]] = []
        now = time.monotonic()
        for key, (bucket, created_at) in _IP_BUCKETS.items():
            bucket._refill()
            results.append({
                "key": key,
                "rate": bucket.rate,
                "remaining": int(bucket.tokens),
                "window": bucket.per_second,
                "created_at": created_at,
            })
        return results

    @property
    def active_bucket_count(self) -> int:
        """当前活跃的桶数量。"""
        return get_bucket_count()

    # -----------------------------------------------------------------
    # 内部方法
    # -----------------------------------------------------------------

    def _get_or_create_bucket(
        self,
        key: str,
        limit: Optional[int],
        window: int,
    ) -> TokenBucket:
        """获取或创建一个 TokenBucket。"""
        rate = limit if limit is not None else self.default_rate

        cached = _IP_BUCKETS.get(key)
        if cached:
            bucket, _ = cached
            if bucket.rate != rate or bucket.per_second != window:
                bucket = TokenBucket(rate, window)
                _IP_BUCKETS[key] = (bucket, time.monotonic())
            return bucket

        bucket = TokenBucket(rate, window)
        _IP_BUCKETS[key] = (bucket, time.monotonic())
        return bucket


# =====================================================================
# 异步客户端
# =====================================================================


class AsyncRateLimitClient:
    """Rate Limit 异步客户端。

    当前实现与同步客户端相同（内存操作无 I/O 阻塞），
    但提供一致的 async/await 接口，便于在异步代码中
    保持调用风格统一。未来若切换到 Redis 等异步驱动，
    接口无需变更。
    """

    def __init__(
        self,
        default_rate: int = 60,
        auth_rate: int = 10,
        admin_rate: int = 120,
    ) -> None:
        self._sync = RateLimitClient(default_rate, auth_rate, admin_rate)

    async def check_rate_limit(
        self,
        key: str,
        limit: Optional[int] = None,
        window: int = 60,
    ) -> Dict[str, Any]:
        """检查指定 key 是否被限流（异步版本）。

        同 :meth:`RateLimitClient.check_rate_limit`。
        """
        return self._sync.check_rate_limit(key, limit, window)

    async def get_remaining(self, key: str) -> int:
        """查询指定 key 的剩余请求数（异步版本）。

        同 :meth:`RateLimitClient.get_remaining`。
        """
        return self._sync.get_remaining(key)

    async def reset_bucket(self, key: str) -> bool:
        """重置指定 key 的限流桶（异步版本）。

        同 :meth:`RateLimitClient.reset_bucket`。
        """
        return self._sync.reset_bucket(key)

    async def get_all_buckets(self) -> List[Dict[str, Any]]:
        """获取所有活跃的限流桶信息（异步版本）。

        同 :meth:`RateLimitClient.get_all_buckets`。
        """
        return self._sync.get_all_buckets()

    @property
    def active_bucket_count(self) -> int:
        """当前活跃的桶数量。"""
        return self._sync.active_bucket_count


# =====================================================================
# 模块级便利函数（同步版本）
# =====================================================================

_client: Optional[RateLimitClient] = None


def _get_client() -> RateLimitClient:
    global _client
    if _client is None:
        _client = RateLimitClient()
    return _client


def check_rate_limit(
    key: str,
    limit: Optional[int] = None,
    window: int = 60,
) -> Dict[str, Any]:
    """检查限流（单例便捷函数）。

    等同于 ``RateLimitClient().check_rate_limit(key, limit, window)``。
    """
    return _get_client().check_rate_limit(key, limit, window)


def get_remaining(key: str) -> int:
    """查询剩余次数（单例便捷函数）。"""
    return _get_client().get_remaining(key)


def reset_bucket(key: str) -> bool:
    """重置桶（单例便捷函数）。"""
    return _get_client().reset_bucket(key)


def get_all_buckets() -> List[Dict[str, Any]]:
    """获取所有桶信息（单例便捷函数）。"""
    return _get_client().get_all_buckets()
