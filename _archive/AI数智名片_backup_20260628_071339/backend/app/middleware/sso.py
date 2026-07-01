"""
SSO OAuth2/OIDC 中间件

提供 OAuth2 授权码流程 + OpenID Connect 身份验证的 FastAPI 中间件。
支持 Google、GitHub 和企业自建 OIDC 提供商。
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import RedirectResponse

from app.config import settings

logger = logging.getLogger("sso.middleware")

# ── Session store for OAuth state (in production, use Redis) ──────────────
# Maps state_token -> {provider, original_path, nonce}
_oauth_sessions: dict[str, dict] = {}


def get_oauth_session(state: str) -> Optional[dict]:
    """Get and remove an OAuth session by state token."""
    return _oauth_sessions.pop(state, None)


def set_oauth_session(state: str, data: dict) -> None:
    """Store an OAuth session."""
    _oauth_sessions[state] = data


# ── SSO configuration check ────────────────────────────────────────────────

SSO_PROVIDERS: dict[str, dict] = {
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
        "scopes": ["openid", "email", "profile"],
        "client_id": settings.SSO_GOOGLE_CLIENT_ID,
        "client_secret": settings.SSO_GOOGLE_CLIENT_SECRET,
    },
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scopes": ["read:user", "user:email"],
        "client_id": settings.SSO_GITHUB_CLIENT_ID,
        "client_secret": settings.SSO_GITHUB_CLIENT_SECRET,
    },
    "oidc": {
        "authorize_url": settings.SSO_OIDC_AUTHORIZE_URL,
        "token_url": settings.SSO_OIDC_TOKEN_URL,
        "userinfo_url": settings.SSO_OIDC_USERINFO_URL,
        "scopes": settings.SSO_OIDC_SCOPES.split(","),
        "client_id": settings.SSO_OIDC_CLIENT_ID,
        "client_secret": settings.SSO_OIDC_CLIENT_SECRET,
    },
}


# ── SSO Middleware ──────────────────────────────────────────────────────────

class SSOMiddleware(BaseHTTPMiddleware):
    """
    SSO 中间件：拦截需要 SSO 保护的路径，跳转到 OAuth2 授权页面。

    用法：
        app.add_middleware(SSOMiddleware, protected_paths=["/admin", "/api/sso-protected"])

    该中间件仅做强制跳转保护，认证逻辑在 routers/sso.py 中处理。
    """

    def __init__(
        self,
        app,
        protected_paths: Optional[list[str]] = None,
        provider: str = "google",
    ):
        super().__init__(app)
        self.protected_paths = protected_paths or []
        self.provider = provider

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):
        # Check if this path needs SSO authentication
        path = request.url.path
        if self._is_protected(path):
            # Skip if already authenticated via JWT (handled by auth router)
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                return await call_next(request)

            # Also skip SSO-related paths to avoid redirect loops
            if path.startswith("/api/auth/sso") or path.startswith("/api/sso"):
                return await call_next(request)

            # Redirect to SSO login
            redirect_uri = str(request.url_for("sso_login", provider=self.provider))
            return RedirectResponse(url=redirect_uri)

        return await call_next(request)

    def _is_protected(self, path: str) -> bool:
        return any(path.startswith(p) for p in self.protected_paths)


# ── SSO state helpers ────────────────────────────────────────────────────────

def build_authorize_redirect_uri(base_url: str) -> str:
    """Build the callback URL for the SSO provider."""
    return f"{base_url.rstrip('/')}/api/auth/sso/callback"
