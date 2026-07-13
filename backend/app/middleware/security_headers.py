"""Security Headers Middleware — ASGI middleware adding hardened security headers.

Adds CSP, HSTS, XFO, XXP, X-CTO, Referrer-Policy, Permissions-Policy,
Cross-Origin-Embedder-Policy, and Cross-Origin-Opener-Policy to every HTTP
response.  Designed to be placed early in the FastAPI middleware chain so all
downstream responses inherit the headers.
"""

from __future__ import annotations

from typing import Any

# ── Hardened security header values ──────────────────────────────────────
SECURITY_HEADERS: dict[str, str] = {
    # CSP: Tight default with explicit allowances for self-hosted assets
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://hm.baidu.com https://*.baidu.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: blob: https:; "
        "font-src 'self' data: https://fonts.gstatic.com; "
        "connect-src 'self' https://api.liankebao.top wss:; "
        "frame-src 'self' https:; "
        "frame-ancestors 'none'; "
        "form-action 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "upgrade-insecure-requests"
    ),
    # HSTS: 1 year, include subdomains, preload
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    # Prevent MIME type sniffing
    "X-Content-Type-Options": "nosniff",
    # Deny framing (clickjacking protection)
    "X-Frame-Options": "DENY",
    # Legacy XSS filter (deprecated but harmless)
    "X-XSS-Protection": "1; mode=block",
    # Referrer policy: strict on cross-origin
    "Referrer-Policy": "strict-origin-when-cross-origin",
    # Permissions: deny camera/mic/geo by default
    "Permissions-Policy": (
        "camera=(), microphone=(), geolocation=(), "
        "display-capture=(), fullscreen=(self), "
        "payment=(), usb=(), magnetometer=(), "
        "accelerometer=(), gyroscope=(), "
        "interest-cohort=()"
    ),
    # Cross-Origin isolation
    "Cross-Origin-Embedder-Policy": "require-corp",
    "Cross-Origin-Opener-Policy": "same-origin",
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
            await send(message)

        await self.app(scope, receive, send_wrapper)
