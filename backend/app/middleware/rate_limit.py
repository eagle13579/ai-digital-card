"""
IP Rate Limiter Middleware — 基于 IP 的滑动窗口限流中间件

限制每个 IP 每分钟最多 60 次请求，超限返回 429 Too Many Requests。
白名单中的 IP（127.0.0.1 / localhost）不限制。

默认使用 Redis 滑动窗口限流（跨实例共享），Redis 不可用时自动降级到内存限流。

用法:
    from app.middleware.rate_limit import IPRateLimitMiddleware
    app.add_middleware(IPRateLimitMiddleware)
"""

from __future__ import annotations

import json
import time
import threading
from collections import defaultdict

# ── 默认配置 ──────────────────────────────────────────────────────────────────
DEFAULT_MAX_REQUESTS = 60
"""每个 IP 每分钟最大请求数。"""

DEFAULT_WINDOW_SECONDS = 60
"""滑动窗口大小（秒）。"""

WHITELIST_IPS = {"127.0.0.1", "::1", "localhost"}
"""不受限流限制的白名单 IP 集合。"""


class IPRateLimitMiddleware:
    """基于 IP 地址的滑动窗口限流中间件。

    限流后端（按优先级）:
        1. RedisRateLimiter — Redis 滑动窗口（跨实例共享）
        2. MemoryRateLimiter — 进程内内存限流（降级方案）

    限制每个 IP 每分钟（默认）最多 60 次请求。
    127.0.0.1 和 localhost 不受限制。

    被限流时返回:
        - 状态码: 429 Too Many Requests
        - 响应头: RateLimit-Limit, RateLimit-Remaining, RateLimit-Reset, Retry-After
        - 响应体: {"detail": "请求过于频繁", "retry_after": <秒数>}

    用法:
        app.add_middleware(IPRateLimitMiddleware)

        # 自定义参数:
        app.add_middleware(
            IPRateLimitMiddleware,
            max_requests=30,
            window_seconds=60,
        )
    """

    def __init__(
        self,
        app,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
    ):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        # ── Redis 限流后端（惰性初始化，不可用时降级到内存） ──
        self._redis_limiter = None
        self._use_redis = False
        self._init_redis_limiter()

        # {ip: [timestamp, ...]}  按时间序存储每个请求的时间戳（内存降级）
        self._visits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()
        # 清理阈值 — 当累计超过 N 条记录时触发一次清理
        self._cleanup_trigger = 10000

    def _init_redis_limiter(self) -> None:
        """尝试初始化 Redis 限流后端。"""
        try:
            from app.cache.redis_rate_limiter import RedisRateLimiter
            from app.config import settings

            self._redis_limiter = RedisRateLimiter(settings.REDIS_URL)
            self._use_redis = True
        except Exception:
            self._redis_limiter = None
            self._use_redis = False

    # ── IP 提取 ──────────────────────────────────────────────────────────────

    @staticmethod
    def _get_client_ip(scope: dict) -> str:
        """从 ASGI scope 中提取客户端 IP。"""
        headers = dict(scope.get("headers", []) or [])
        # 按优先级：X-Forwarded-For > X-Real-IP > remote address
        for header_name in (b"x-forwarded-for", b"x-real-ip"):
            value = headers.get(header_name)
            if value:
                ip = value.decode("utf-8").split(",")[0].strip()
                if ip:
                    return ip
        client = scope.get("client")
        if client:
            return client[0]
        return "127.0.0.1"

    @staticmethod
    def _is_whitelisted(ip: str) -> bool:
        """检查 IP 是否在白名单中（白名单 IP 不限制）。"""
        return ip in WHITELIST_IPS

    # ── 滑动窗口限流核心 ────────────────────────────────────────────────────

    def _build_rate_limit_key(self, ip: str) -> str:
        """构建 Redis 限流键。"""
        return f"ratelimit:ip:{ip}"

    def _cleanup_old(self, now: float):
        """移除窗口之外的过期时间戳。"""
        cutoff = now - self.window_seconds
        expired_ips = []
        for ip, timestamps in self._visits.items():
            while timestamps and timestamps[0] < cutoff:
                timestamps.pop(0)
            if not timestamps:
                expired_ips.append(ip)
        for ip in expired_ips:
            del self._visits[ip]

    async def _check_rate_limit_redis(
        self, ip: str
    ) -> tuple[bool, int, float]:
        """使用 Redis 后端检查速率限制。"""
        key = self._build_rate_limit_key(ip)
        try:
            return await self._redis_limiter.check_rate_limit(
                key,
                max_requests=self.max_requests,
                window_seconds=self.window_seconds,
            )
        except Exception:
            # Redis 异常 → 降级到内存
            self._use_redis = False
            self._redis_limiter = None
            return self._check_rate_limit_memory(ip)

    def _check_rate_limit_memory(
        self, ip: str
    ) -> tuple[bool, int, float]:
        """使用内存后端检查速率限制。返回 (allowed, remaining, retry_after)。"""
        now = time.time()
        with self._lock:
            timestamps = self._visits[ip]
            cutoff = now - self.window_seconds

            # 移除过期记录
            while timestamps and timestamps[0] < cutoff:
                timestamps.pop(0)

            current_count = len(timestamps)
            remaining = max(0, self.max_requests - current_count)

            if current_count >= self.max_requests:
                oldest = timestamps[0]
                reset_time = oldest + self.window_seconds
                retry_after = max(0, reset_time - now)
                return False, 0, retry_after

            # 记录本次请求
            timestamps.append(now)
            # 重算 remaining（包含本次请求）
            current_count = len(timestamps)
            remaining = max(0, self.max_requests - current_count)

            # 定期清理全表
            total_records = sum(len(v) for v in self._visits.values())
            if total_records > self._cleanup_trigger:
                self._cleanup_old(now)

            return True, remaining, 0.0

    async def _check_rate_limit(
        self, ip: str
    ) -> tuple[bool, int, float]:
        """检查速率限制。优先使用 Redis，不可用时降级到内存。

        Returns:
            allowed: True 表示允许通过
            remaining: 窗口内剩余可用请求数（0 表示已超限）
            retry_after: 建议重试等待秒数
        """
        if self._use_redis and self._redis_limiter is not None:
            return await self._check_rate_limit_redis(ip)
        return self._check_rate_limit_memory(ip)

    # ── ASGI 接口 ────────────────────────────────────────────────────────────

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client_ip = self._get_client_ip(scope)

        # 白名单 IP 直接放行，不限流
        if self._is_whitelisted(client_ip):
            await self.app(scope, receive, send)
            return

        allowed, remaining, retry_after = await self._check_rate_limit(client_ip)

        if not allowed:
            retry_seconds = int(retry_after) + 1
            body_data = {
                "detail": "请求过于频繁",
                "retry_after": retry_seconds,
            }
            body_bytes = json.dumps(body_data).encode("utf-8")

            reset_ts = int(time.time()) + retry_seconds
            headers = [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body_bytes)).encode()),
                (b"RateLimit-Limit", str(self.max_requests).encode()),
                (b"RateLimit-Remaining", b"0"),
                (b"RateLimit-Reset", str(reset_ts).encode()),
                (b"Retry-After", str(retry_seconds).encode()),
            ]
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": headers,
            })
            await send({
                "type": "http.response.body",
                "body": body_bytes,
            })
            return

        # 正常请求 — 拦截 send 以注入响应头
        rate_limit_headers = [
            (b"RateLimit-Limit", str(self.max_requests).encode()),
            (b"RateLimit-Remaining", str(remaining).encode()),
            (b"RateLimit-Reset", str(int(time.time()) + self.window_seconds).encode()),
        ]

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                existing_headers = list(message.get("headers", []) or [])
                header_names = {h[0].lower() for h in existing_headers}
                new_headers = existing_headers + [
                    h for h in rate_limit_headers
                    if h[0].lower() not in header_names
                ]
                message["headers"] = new_headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
