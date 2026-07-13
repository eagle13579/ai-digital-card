"""CSRF Protection Middleware — Double Submit Cookie 模式。

使用双重提交 Cookie（Double Submit Cookie）模式防御 CSRF 攻击：

工作流程:
  1. 前端调用 GET /api/csrf/token 获取 CSRF token
  2. 服务器生成随机 token，写入非 HttpOnly Cookie（JS 可读取）
  3. 前端从 document.cookie 读取 csrf_token，放入 X-CSRF-Token 请求头
  4. 后端中间件对 POST/PUT/DELETE/PATCH 校验 Cookie 值与请求头值是否一致
  5. 匹配则放行，否则返回 403

排除端点（不校验 CSRF）:
  - /api/auth/login, /api/auth/register  — 认证端点
  - /api/payments/webhook, /api/webhooks/ — 第三方 webhook 回调
  - 所有 GET/HEAD/OPTIONS 请求            — 安全方法
"""

from __future__ import annotations

import logging
import secrets
from typing import Any

logger = logging.getLogger(__name__)

# ── 配置常量 ──────────────────────────────────────────────────────────────────
CSRF_COOKIE_NAME = "csrf_token"
"""CSRF token 在 Cookie 中的名称（非 HttpOnly，供 JS 读取）。"""

CSRF_HEADER_NAME = "X-CSRF-Token"
"""前端提交 CSRF token 时使用的请求头名称。"""

CSRF_TOKEN_PATH = "/api/csrf/token"
"""生成 CSRF token 的端点路径。"""

EXCLUDED_PATHS = (
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/wx-mini-login",
    "/api/auth/wx-login",
    "/api/payments/webhook",
    "/api/webhooks",
    "/api/brochures",
    "/api/brochure/",
    "/api/match/",
    "/api/trust/",
    "/api/card/",
    "/api/visitors/",
    "/api/bot/",
    "/api/tags/",
    "/api/users/",
    "/api/crm/forms/",
    "/api/ai/",
    "/api/design-qa/",
    "/api/v1/admin",
    "/api/v1/developer",
    "/api/admin",
    "/api/developer",
)
"""不进行 CSRF 校验的路径前缀（登录、注册、第三方回调等）。"""


class CsrfMiddleware:
    """Double Submit Cookie CSRF 保护中间件。

    对 POST/PUT/DELETE/PATCH 请求校验 Cookie 中的 CSRF token
    与请求头 ``X-CSRF-Token`` 的值是否一致。不一致时返回 403。

    使用方式 (FastAPI)::

        app.add_middleware(CsrfMiddleware)

    或直接包装 ASGI 应用::

        app = CsrfMiddleware(raw_asgi_app)
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]

        # ── 处理 CSRF Token 生成请求 ──────────────────────────────────────
        if method == "GET" and path == CSRF_TOKEN_PATH:
            await self._handle_csrf_token(scope, receive, send)
            return

        # ── 安全方法不校验 ────────────────────────────────────────────────
        if method in ("GET", "HEAD", "OPTIONS"):
            await self.app(scope, receive, send)
            return

        # ── 排除端点不校验 ────────────────────────────────────────────────
        if path.startswith(EXCLUDED_PATHS):
            await self.app(scope, receive, send)
            return

        # ── 校验 CSRF Token ──────────────────────────────────────────────
        await self._validate_csrf(scope, receive, send)

    # ──────────────────────────────────────────────────────────────────────────
    # 内部方法
    # ──────────────────────────────────────────────────────────────────────────

    async def _handle_csrf_token(
        self, scope: dict, receive: Any, send: Any
    ) -> None:
        """生成 CSRF Token 并设置为 Cookie，同时返回 JSON 响应。"""
        token = secrets.token_hex(32)
        body = f'{{"token":"{token}"}}'.encode("utf-8")

        # 检测是否为 HTTPS 连接
        scheme = scope.get("scheme", "http")
        secure_flag = scheme == "https"

        cookie_value = (
            f"{CSRF_COOKIE_NAME}={token}; Path=/; SameSite=Lax"
            f"{'; Secure' if secure_flag else ''}"
        )

        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("latin-1")),
            (b"set-cookie", cookie_value.encode("latin-1")),
        ]

        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": headers,
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })

    async def _validate_csrf(
        self, scope: dict, receive: Any, send: Any
    ) -> None:
        """校验 CSRF Token：比较 Cookie 值与请求头值是否一致。"""
        headers = dict(scope.get("headers", []))

        # 从 Cookie 中提取 CSRF Token
        cookie_str = headers.get(b"cookie", b"").decode("latin-1")
        csrf_cookie = self._parse_cookie(cookie_str, CSRF_COOKIE_NAME)

        if not csrf_cookie:
            logger.warning("CSRF cookie missing (path=%s)", scope["path"])
            await self._send_error(send, "CSRF token missing in cookie")
            return

        # 从请求头中提取 CSRF Token（兼容大小写）
        header_key = CSRF_HEADER_NAME.lower().encode("latin-1")
        csrf_header = headers.get(header_key, b"").decode()
        if not csrf_header:
            # 备用：从 body 中读取（用于表单提交场景）
            csrf_header = await self._extract_from_body(receive)

        if not csrf_header:
            logger.warning("CSRF header missing (path=%s)", scope["path"])
            await self._send_error(send, "CSRF token missing in header")
            return

        # 使用恒定时间比较防止时序攻击
        if not secrets.compare_digest(csrf_cookie, csrf_header):
            logger.warning(
                "CSRF token mismatch (path=%s, cookie=%s..., header=%s...)",
                scope["path"],
                csrf_cookie[:8],
                csrf_header[:8],
            )
            await self._send_error(send, "CSRF token mismatch")
            return

        # 验证通过，放行
        await self.app(scope, receive, send)

    @staticmethod
    def _parse_cookie(cookie_str: str, name: str) -> str | None:
        """从 Cookie 字符串中提取指定名称的值。

        Args:
            cookie_str: 完整的 Cookie 字符串（如 ``csrf_token=abc123; session=xyz``）
            name: 目标 Cookie 名称

        Returns:
            匹配到的 Cookie 值，未找到返回 None
        """
        if not cookie_str:
            return None
        for part in cookie_str.split(";"):
            part = part.strip()
            if part.startswith(name + "="):
                return part[len(name) + 1:]
        return None

    @staticmethod
    async def _extract_from_body(receive: Any) -> str | None:
        """尝试从请求 body 中提取 CSRF token（用于表单提交场景）。

        仅解析 application/x-www-form-urlencoded 或 application/json 格式。
        """
        try:
            from urllib.parse import parse_qs

            more_body = True
            chunks = []
            while more_body:
                message = await receive()
                chunks.append(message.get("body", b""))
                more_body = message.get("more_body", False)

            body_bytes = b"".join(chunks)
            if not body_bytes:
                return None

            # 尝试 JSON 解析
            try:
                import json

                data = json.loads(body_bytes)
                return data.get("csrf_token") or data.get(CSRF_HEADER_NAME)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

            # 尝试表单格式解析
            try:
                text = body_bytes.decode("utf-8")
                params = parse_qs(text)
                return (params.get("csrf_token") or params.get("_csrf_token") or [None])[0]
            except UnicodeDecodeError:
                return None

        except Exception:
            return None

    @staticmethod
    async def _send_error(send: Any, message: str) -> None:
        """发送 403 错误 JSON 响应。

        Args:
            send: ASGI send 回调
            message: 错误描述字符串
        """
        body = f'{{"detail":"{message}"}}'.encode("utf-8")
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("latin-1")),
        ]
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": headers,
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })
