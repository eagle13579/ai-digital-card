"""Security Headers Middleware — ASGI middleware adding 7 security headers.

Adds CSP, HSTS, XFO, XXP, X-CTO, Referrer-Policy, and Permissions-Policy
to every HTTP response.  Designed to be placed early in the FastAPI
middleware chain so all downstream responses inherit the headers.
"""

from __future__ import annotations

from typing import Any

# ── Default security header values ──────────────────────────────────────
SECURITY_HEADERS: dict[str, str] = {
    "Content-Security-Policy": "default-src 'self'",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


class SecurityHeadersMiddleware:
    """ASGI middleware that injects security headers into every HTTP response.

    Usage (FastAPI)::

        app.add_middleware(SecurityHeadersMiddleware)

    Or use with any ASGI application::

        app = SecurityHeadersMiddleware(raw_asgi_app)
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                # Merge security headers, not overriding existing ones
                existing_keys = {k.lower() for k, _ in headers}
                new_headers = [
                    (key.encode("latin-1"), value.encode("latin-1"))
                    for key, value in SECURITY_HEADERS.items()
                    if key.lower() not in existing_keys
                ]
                message["headers"] = headers + new_headers
                # Remove server version information leak
                message["headers"] = [
                    h for h in message["headers"]
                    if not h[0].lower() == b"server"
                ]
                message["headers"].append((b"server", b"uvicorn"))
            await send(message)

        await self.app(scope, receive, send_wrapper)
