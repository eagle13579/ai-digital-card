import json
import time
import threading
from collections import defaultdict


class RateLimiterMiddleware:
    """基于IP的速率限制中间件，使用滑动窗口算法。

    用法:
        from app.middleware import RateLimiterMiddleware

        app.add_middleware(RateLimiterMiddleware, max_requests=100, window_seconds=60)
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # {ip: [timestamp, ...]}  按时间序存储每个请求的时间戳
        self._visits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()
        # 清理阈值 — 当累计超过 N 条记录时触发一次清理
        self._cleanup_trigger = max_requests * 10

    def _get_client_ip(self, scope: dict) -> str:
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

    def _cleanup_old(self, now: float):
        """移除窗口之外的过期时间戳。"""
        cutoff = now - self.window_seconds
        expired_ips = []
        for ip, timestamps in self._visits.items():
            # 二分查找第一个在窗口内的索引
            # 由于 timestamps 是自然有序的（append 顺序），可直接遍历清理
            while timestamps and timestamps[0] < cutoff:
                timestamps.pop(0)
            if not timestamps:
                expired_ips.append(ip)
        for ip in expired_ips:
            del self._visits[ip]

    def _check_rate_limit(self, ip: str) -> tuple[bool, int, float]:
        """检查速率限制。返回 (allowed, remaining, reset_time)。

        Returns:
            allowed: True 表示允许通过
            remaining: 窗口内剩余可用请求数
            reset_time: 窗口重置的 Unix 时间戳
        """
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
                # 计算 retry_after: 最早时间戳 + window_seconds - now
                oldest = timestamps[0]
                reset_time = oldest + self.window_seconds
                retry_after = max(0, reset_time - now)
                return False, 0, retry_after

            # 记录本次请求
            timestamps.append(now)

            # 计算 reset_time: 最早记录 + window_seconds，如果没有记录则用 now + window_seconds
            if timestamps:
                reset_time = timestamps[0] + self.window_seconds
            else:
                reset_time = now + self.window_seconds

            # 定期清理全表
            total_records = sum(len(v) for v in self._visits.values())
            if total_records > self._cleanup_trigger:
                self._cleanup_old(now)

            return True, remaining, reset_time

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client_ip = self._get_client_ip(scope)
        allowed, remaining, reset_or_retry = self._check_rate_limit(client_ip)

        if not allowed:
            # 被限制 — 直接返回 429
            retry_after = int(reset_or_retry) + 1  # 向上取整
            body_data = {
                "detail": "请求过于频繁",
                "retry_after": retry_after,
            }
            body_bytes = json.dumps(body_data).encode("utf-8")
            headers = [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body_bytes)).encode()),
                (b"ratelimit-limit", str(self.max_requests).encode()),
                (b"ratelimit-remaining", b"0"),
                (b"ratelimit-reset", str(int(time.time()) + retry_after).encode()),
                (b"retry-after", str(retry_after).encode()),
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
        reset_time = int(reset_or_retry)
        rate_limit_headers = [
            (b"ratelimit-limit", str(self.max_requests).encode()),
            (b"ratelimit-remaining", str(remaining).encode()),
            (b"ratelimit-reset", str(reset_time).encode()),
        ]

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                existing_headers = list(message.get("headers", []) or [])
                # 合并自定义头（去重 — 自定义头覆盖已有同名头）
                header_names = {h[0].lower() for h in existing_headers}
                new_headers = existing_headers + [
                    h for h in rate_limit_headers
                    if h[0].lower() not in header_names
                ]
                message["headers"] = new_headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
