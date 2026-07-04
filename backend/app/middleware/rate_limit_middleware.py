"""
RateLimitMiddleware — 全局速率限制中间件
=========================================
基于内存 Token Bucket 算法，对每个 IP 进行请求频率限制。

配置 (环境变量):
    RATE_LIMIT_DEFAULT  — 默认速率 (60 请求/分钟/IP)
    RATE_LIMIT_AUTH     — 登录注册速率 (10 请求/分钟/IP)
    RATE_LIMIT_ADMIN    — 管理员端点速率 (120 请求/分钟)

速率限制 Header:
    X-RateLimit-Limit       — 上限
    X-RateLimit-Remaining   — 剩余
    X-RateLimit-Reset       — 重置时间戳 (Unix)

豁免路径:
    /health/*                   — 健康检查不限流
    /api/v1/rate-limit/*        — Rate Limit SDK 端点不限流

用法:
    app.add_middleware(RateLimitMiddleware)
"""

import os
import time
import logging
import ipaddress
from collections import defaultdict
from typing import Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp

logger = logging.getLogger("chainke.ratelimit")

# ===================================================================
# Token Bucket 实现
# ===================================================================


class TokenBucket:
    """内存 Token Bucket 速率限制器。"""

    __slots__ = ("rate", "per_second", "capacity", "tokens", "last_refill")

    def __init__(self, rate: int, per_seconds: int = 60) -> None:
        """
        初始化 Token Bucket。

        Args:
            rate:         允许的最大请求数
            per_seconds:  时间窗口（秒），默认 60 秒
        """
        self.rate = rate
        self.per_second = per_seconds
        self.capacity = rate
        self.tokens = float(rate)
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        """根据时间间隔补充令牌。"""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * (self.rate / self.per_second))
        self.last_refill = now

    def consume(self) -> Tuple[bool, int, float]:
        """
        尝试消费一个令牌。

        Returns:
            (allowed, remaining_tokens, reset_time)
        """
        self._refill()
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True, int(self.tokens), time.time() + self.per_second
        return False, 0, time.time() + self.per_second


# ===================================================================
# 全局存储：IP -> TokenBucket
# ===================================================================

# 存储桶字典，自动清理超过 1 小时未活跃的条目
_IP_BUCKETS: dict[str, tuple[TokenBucket, float]] = {}
_BUCKET_CLEANUP_INTERVAL = 3600.0  # 1 小时清理一次
_LAST_CLEANUP = time.monotonic()


def _get_client_ip(request: Request) -> str:
    """从请求中提取客户端真实 IP。"""
    # 优先取 X-Forwarded-For (代理环境下)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For: client, proxy1, proxy2
        client_ip = forwarded.split(",")[0].strip()
        # 如果是内网 IP，回退到直接连接 IP
        try:
            addr = ipaddress.ip_address(client_ip)
            if addr.is_private or addr.is_loopback:
                return request.client.host if request.client else "127.0.0.1"
        except ValueError:
            pass
        return client_ip
    # 直接连接
    return request.client.host if request.client else "127.0.0.1"


def _get_bucket_for_ip(
    client_ip: str,
    path: str,
    default_rate: int,
    auth_rate: int,
    admin_rate: int,
) -> TokenBucket:
    """根据 IP 和路径获取对应的 Token Bucket，自动创建。"""
    # 判断速率级别
    if path.startswith("/api/auth/") or path in ("/api/auth/login", "/api/auth/register"):
        rate = auth_rate
    elif path.startswith("/api/admin/") or path.startswith("/admin/"):
        rate = admin_rate
    else:
        rate = default_rate

    per_seconds = 60  # 所有限制都是每 60 秒

    # 检查缓存
    cached = _IP_BUCKETS.get(client_ip)
    if cached:
        bucket, created_at = cached
        # 如果速率变化了（比如运行时改了环境变量），重建桶
        if bucket.rate != rate:
            bucket = TokenBucket(rate, per_seconds)
            _IP_BUCKETS[client_ip] = (bucket, time.monotonic())
        return bucket

    # 创建新桶
    bucket = TokenBucket(rate, per_seconds)
    _IP_BUCKETS[client_ip] = (bucket, time.monotonic())
    return bucket


def _cleanup_stale_buckets() -> None:
    """清理超过 1 小时未使用的桶，防止内存泄漏。"""
    global _LAST_CLEANUP
    now = time.monotonic()
    if now - _LAST_CLEANUP < _BUCKET_CLEANUP_INTERVAL:
        return
    stale_ips = [ip for ip, (_, created_at) in _IP_BUCKETS.items()
                 if now - created_at > _BUCKET_CLEANUP_INTERVAL]
    for ip in stale_ips:
        del _IP_BUCKETS[ip]
    if stale_ips:
        logger.debug("[RateLimit] 已清理 %d 个过期桶", len(stale_ips))
    _LAST_CLEANUP = now


# ===================================================================
# 中间件
# ===================================================================


def _is_whitelisted_path(path: str) -> bool:
    """判断是否为豁免路径（不限流）。"""
    if path == "/health" or path.startswith("/health/"):
        return True
    if path.startswith("/api/v1/rate-limit/"):
        return True
    return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    全局速率限制中间件。

    基于客户端 IP 进行 Token Bucket 速率限制，支持不同端点不同速率。

    豁免路径:
        /health, /health/*           — 不限流
        /api/v1/rate-limit/*         — Rate Limit SDK 端点不限流
    """

    def __init__(
        self,
        app: ASGIApp,
        default_rate: Optional[int] = None,
        auth_rate: Optional[int] = None,
        admin_rate: Optional[int] = None,
    ) -> None:
        super().__init__(app)

        # 从环境变量读取配置，支持构造参数覆盖
        self.default_rate = default_rate or int(os.getenv("RATE_LIMIT_DEFAULT", "60"))
        self.auth_rate = auth_rate or int(os.getenv("RATE_LIMIT_AUTH", "10"))
        self.admin_rate = admin_rate or int(os.getenv("RATE_LIMIT_ADMIN", "120"))

        logger.info(
            "[RateLimit] 初始化: default=%d/min, auth=%d/min, admin=%d/min",
            self.default_rate,
            self.auth_rate,
            self.admin_rate,
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        # ── 豁免路径不限流 ────────────────────────────────────────
        if _is_whitelisted_path(request.url.path):
            return await call_next(request)

        # ── 获取客户端 IP 并检查速率 ──────────────────────────────
        client_ip = _get_client_ip(request)
        bucket = _get_bucket_for_ip(
            client_ip,
            request.url.path,
            self.default_rate,
            self.auth_rate,
            self.admin_rate,
        )

        allowed, remaining, reset_time = bucket.consume()

        # ── 如果被限流，返回 429 ──────────────────────────────────
        if not allowed:
            logger.warning(
                "[RateLimit] IP=%s 被限流 (path=%s, method=%s)",
                client_ip,
                request.url.path,
                request.method,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "请求过于频繁，请稍后再试",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": int(reset_time - time.time()),
                },
                headers={
                    "X-RateLimit-Limit": str(bucket.rate),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time)),
                    "Retry-After": str(int(reset_time - time.time())),
                },
            )

        # ── 正常请求 — 处理并附加限流 Header ─────────────────────
        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(bucket.rate)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))

        return response


# ===================================================================
# 便捷工具函数 (供单元测试使用)
# ===================================================================


def reset_buckets() -> None:
    """清空所有速率限制桶（用于测试）。"""
    _IP_BUCKETS.clear()
    logger.debug("[RateLimit] 所有速率限制桶已清空")


def get_bucket_count() -> int:
    """返回当前活跃的桶数量（用于监控/测试）。"""
    return len(_IP_BUCKETS)
