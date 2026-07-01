"""
Tiered Rate Limiter Middleware — 三级分层速率限制中间件

支持三级分层限流策略:
  - anonymous:  100 req/min (免费/未认证用户)
  - standard:  1000 req/min (已认证用户)
  - enterprise: 10000 req/min (企业用户)
敏感端点 (/auth/*, /payment/*) 在上述基础上再减半。

等级判定优先级:
  1. scope["state"]["user_tier"]      — 由上游认证中间件设置 (request.state)
  2. scope["user_tier"]                — ASGI scope 直接注入
  3. scope["rate_limit_tier_override"] — 显式覆盖
  4. _determine_user_tier(scope)       — JWT token 解析降级
  5. "anonymous"                       — 默认值
"""

from __future__ import annotations

import json
import time
import threading
from collections import defaultdict
from typing import Optional


# ── 默认分级配置 ───────────────────────────────────────────────────────────────
DEFAULT_LIMITS = {
    "anonymous": 100,
    "standard": 1000,
    "enterprise": 10000,
}
"""默认三级分层速率限制 (req/min)。

Tiers:
  - anonymous:   100 req/min  (免费/未认证用户)
  - standard:   1000 req/min  (已认证用户)
  - enterprise: 10000 req/min (企业用户)
"""

SENSITIVE_PREFIXES = ("/auth/login", "/api/register", "/api/auth/", "/api/payment/")
"""敏感端点前缀，速率在上表基础上减半。"""


class RateLimiterMiddleware:
    """基于 IP + 用户等级的速率限制中间件，使用滑动窗口算法。

    支持三级分层限流：anonymous(100/min) / standard(1000/min) / enterprise(10000/min)
    敏感端点（/auth/*, /payment/*）速率减半。

    响应头（标准 RateLimit 规范）:
      - RateLimit-Limit:      窗口内总限制数
      - RateLimit-Remaining:  窗口内剩余可用请求数
      - RateLimit-Reset:      窗口重置的 Unix 时间戳

    用法:
        from app.middleware import RateLimiterMiddleware

        # 三级分层限流（默认使用 DEFAULT_LIMITS）
        app.add_middleware(RateLimiterMiddleware)

        # 自定义分级限流
        app.add_middleware(
            RateLimiterMiddleware,
            limits={"anonymous": 50, "standard": 500, "enterprise": 5000},
            window_seconds=60,
        )

    等级判定优先级:
        1. scope["state"]["user_tier"]  — 由上游认证中间件设置
        2. scope["user_tier"]            — ASGI scope 直接注入
        3. _determine_user_tier(scope)   — JWT token 解析降级
        4. "anonymous"                    — 默认值
    """

    def __init__(
        self,
        app,
        max_requests: Optional[int] = None,
        window_seconds: int = 60,
        limits: Optional[dict[str, int]] = None,
    ):
        self.app = app
        self.window_seconds = window_seconds

        # ── 限流模式判定 ──────────────────────────────────────────────────
        if max_requests is not None:
            # 向后兼容：单级限流模式
            self._legacy_mode = True
            self._default_limit = max_requests
        else:
            self._legacy_mode = False
            self._limits = dict(DEFAULT_LIMITS)
            if limits:
                self._limits.update(limits)

        # {ip: [timestamp, ...]}  按时间序存储每个请求的时间戳
        self._visits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()
        # 清理阈值 — 当累计超过 N 条记录时触发一次清理
        self._cleanup_trigger = 10000

    # ── 等级判定 ──────────────────────────────────────────────────────────────

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

    def _get_request_path(self, scope: dict) -> str:
        """从 ASGI scope 中提取请求路径。"""
        return scope.get("path", "/")

    def _is_sensitive_endpoint(self, path: str) -> bool:
        """检查请求路径是否为敏感端点。"""
        return path.startswith(SENSITIVE_PREFIXES)

    def _determine_user_tier(self, scope: dict) -> str:
        """从请求 scope 中推断用户等级，优先级如下：

        1. scope["state"]["user_tier"]  — 上游中间件通过 request.state 设置
        2. scope["user_tier"]            — ASGI scope 直接注入
        3. scope["rate_limit_tier_override"] — 显式覆盖
        4. JWT token 解析降级 (兼容旧方式)
        5. "anonymous" — 默认

        Returns:
            "anonymous" | "standard" | "enterprise"
        """
        # ── 优先级 1: scope["state"] (来自上游 FastAPI middleware 的 request.state) ──
        state = scope.get("state")
        if isinstance(state, dict):
            user_tier = state.get("user_tier")
            if user_tier in ("anonymous", "standard", "enterprise"):
                return user_tier

        # ── 优先级 2: scope["user_tier"] ──
        user_tier = scope.get("user_tier")
        if user_tier in ("anonymous", "standard", "enterprise"):
            return user_tier

        # ── 优先级 3: scope["rate_limit_tier_override"] ──
        override = scope.get("rate_limit_tier_override")
        if override in ("anonymous", "standard", "enterprise"):
            return override

        # ── 优先级 4: JWT token 解析降级（兼容旧式 auth） ──
        headers = dict(scope.get("headers", []) or [])

        # 检查 Authorization header — 有 token 则为已认证
        auth_header = headers.get(b"authorization", b"").decode("utf-8", errors="ignore")
        if not auth_header or not auth_header.startswith("Bearer "):
            return "anonymous"

        # 尝试解码 JWT 判断是否为企业用户
        try:
            import base64
            import json as _json

            # JWT 格式: header.payload.signature
            parts = auth_header.split(".")
            if len(parts) >= 2:
                # Base64 解码 payload (第2段)
                payload_b64 = parts[1]
                # 补全 padding
                padding = 4 - len(payload_b64) % 4
                if padding != 4:
                    payload_b64 += "=" * padding
                payload_bytes = base64.urlsafe_b64decode(payload_b64)
                payload = _json.loads(payload_bytes)
                role = payload.get("role", "")
                membership_tier = payload.get("membership_tier", "")
                # 企业用户判定
                if role in ("admin", "enterprise", "enterprise_admin"):
                    return "enterprise"
                if membership_tier in ("enterprise", "board"):
                    return "enterprise"
            return "standard"
        except Exception:
            # 解析失败，保守处理为 standard（有 token 但解析失败的已认证用户）
            return "standard"

    def _get_effective_limit(self, tier: str, is_sensitive: bool) -> int:
        """获取当前等级和端点的有效速率限制。"""
        if self._legacy_mode:
            return self._default_limit

        limit = self._limits.get(tier, self._limits.get("anonymous", 100))
        if is_sensitive:
            limit = max(1, limit // 2)
        return limit

    # ── 滑动窗口限流核心 ──────────────────────────────────────────────────────

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

    def _check_rate_limit(
        self, ip: str, limit: int
    ) -> tuple[bool, int, float]:
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
            remaining = max(0, limit - current_count)

            if current_count >= limit:
                oldest = timestamps[0]
                reset_time = oldest + self.window_seconds
                retry_after = max(0, reset_time - now)
                return False, 0, retry_after

            # 记录本次请求
            timestamps.append(now)
            # 重算 remaining（包含本次请求）
            current_count = len(timestamps)
            remaining = max(0, limit - current_count)

            # 计算 reset_time
            if timestamps:
                reset_time = timestamps[0] + self.window_seconds
            else:
                reset_time = now + self.window_seconds

            # 定期清理全表
            total_records = sum(len(v) for v in self._visits.values())
            if total_records > self._cleanup_trigger:
                self._cleanup_old(now)

            return True, remaining, reset_time

    # ── ASGI 接口 ─────────────────────────────────────────────────────────────

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client_ip = self._get_client_ip(scope)
        path = self._get_request_path(scope)

        # ── 确定限流等级与有效限制 ──────────────────────────────────────────
        if self._legacy_mode:
            # 旧式单级限流（向后兼容）
            effective_limit = self._default_limit
            tier = "legacy"
            is_sensitive = False
        else:
            tier = self._determine_user_tier(scope)
            is_sensitive = self._is_sensitive_endpoint(path)
            effective_limit = self._get_effective_limit(tier, is_sensitive)
            # 注入等级标记供审计链路使用
            scope["rate_limit_tier"] = tier
            scope["rate_limit_sensitive"] = is_sensitive

        allowed, remaining, reset_or_retry = self._check_rate_limit(
            client_ip, effective_limit
        )

        if not allowed:
            retry_after = int(reset_or_retry) + 1
            body_data = {
                "detail": "请求过于频繁",
                "retry_after": retry_after,
            }
            body_bytes = json.dumps(body_data).encode("utf-8")

            reset_ts = int(time.time()) + retry_after
            headers = [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body_bytes)).encode()),
                (b"RateLimit-Limit", str(effective_limit).encode()),
                (b"RateLimit-Remaining", b"0"),
                (b"RateLimit-Reset", str(reset_ts).encode()),
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
            (b"RateLimit-Limit", str(effective_limit).encode()),
            (b"RateLimit-Remaining", str(remaining).encode()),
            (b"RateLimit-Reset", str(reset_time).encode()),
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
