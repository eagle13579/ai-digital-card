"""OAuth2/OIDC SSO 服务 — 可注册多 provider，支持 google/github/wechat"""

from __future__ import annotations

import logging
import secrets
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    name: str
    client_id: str
    client_secret: str
    auth_url: str
    token_url: str
    userinfo_url: str
    scopes: list[str]


class OAuthService:
    """OAuth2/OIDC SSO 认证服务，支持动态注册 provider"""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderConfig] = {}
        self._state_store: dict[str, dict] = {}
        self._state_ttl = timedelta(minutes=10)

    # ── Provider 注册与管理 ────────────────────────────────────────────────

    def register_provider(
        self, name: str, client_id: str, client_secret: str,
        auth_url: str, token_url: str, userinfo_url: str,
        scopes: Optional[list[str]] = None,
    ) -> None:
        self._providers[name] = ProviderConfig(
            name=name,
            client_id=client_id,
            client_secret=client_secret,
            auth_url=auth_url,
            token_url=token_url,
            userinfo_url=userinfo_url,
            scopes=scopes or ["openid", "email", "profile"],
        )
        logger.info("OAuth provider registered: %s", name)

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    # ── OAuth2 授权码流程 ──────────────────────────────────────────────────

    def get_authorization_url(self, provider: str, redirect_uri: str) -> Optional[str]:
        config = self._providers.get(provider)
        if not config:
            logger.warning("OAuth provider '%s' not registered", provider)
            return None

        state = secrets.token_urlsafe(32)
        self._state_store[state] = {
            "provider": provider,
            "created_at": datetime.utcnow().isoformat(),
        }

        params = {
            "client_id": config.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": " ".join(config.scopes),
            "state": state,
        }
        qs = urllib.parse.urlencode(params)
        return f"{config.auth_url}?{qs}"

    async def exchange_code(
        self, provider: str, code: str, redirect_uri: str,
    ) -> dict[str, Any]:
        config = self._providers.get(provider)
        if not config:
            raise ValueError(f"OAuth provider '{provider}' not registered")

        headers: dict[str, str] = {"Accept": "application/json"}
        data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(config.token_url, data=data, headers=headers)
                resp.raise_for_status()
                token_data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("Token exchange HTTP %s for %s: %s", e.response.status_code, provider, e.response.text)
            raise ValueError(f"令牌交换 HTTP 错误: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error("Token exchange request failed for %s: %s", provider, e)
            raise ValueError(f"令牌交换请求失败: {e}")

        if "error" in token_data:
            desc = token_data.get("error_description", token_data["error"])
            logger.error("Token exchange error for %s: %s", provider, desc)
            raise ValueError(f"提供商返回错误: {desc}")
        return token_data

    async def get_user_info(self, provider: str, token: str) -> dict[str, Any]:
        config = self._providers.get(provider)
        if not config:
            raise ValueError(f"OAuth provider '{provider}' not registered")

        headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
        if provider == "github":
            headers["Accept"] = "application/vnd.github.v3+json"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(config.userinfo_url, headers=headers)
                resp.raise_for_status()
                raw = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("Userinfo HTTP %s for %s: %s", e.response.status_code, provider, e.response.text)
            raise ValueError(f"获取用户信息 HTTP 错误: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error("Userinfo request failed for %s: %s", provider, e)
            raise ValueError(f"获取用户信息请求失败: {e}")

        return self._normalize_user_info(provider, raw)

    # ── 标准化 ────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_user_info(provider: str, raw: dict[str, Any]) -> dict[str, Any]:
        if provider == "google":
            return {
                "sub": raw.get("sub"),
                "email": raw.get("email", ""),
                "name": raw.get("name", ""),
                "picture": raw.get("picture", ""),
            }
        if provider == "github":
            return {
                "sub": str(raw.get("id", "")),
                "email": raw.get("email", "") or f"{raw.get('login', 'user')}@users.noreply.github.com",
                "name": raw.get("name", "") or raw.get("login", ""),
                "picture": raw.get("avatar_url", ""),
            }
        if provider == "wechat":
            return {
                "sub": raw.get("openid", ""),
                "email": raw.get("email", ""),
                "name": raw.get("nickname", ""),
                "picture": raw.get("headimgurl", ""),
            }
        return {
            "sub": raw.get("sub", raw.get("id", "")),
            "email": raw.get("email", ""),
            "name": raw.get("name", raw.get("nickname", "")),
            "picture": raw.get("picture", raw.get("avatar_url", "")),
        }


# ── 工厂函数 ────────────────────────────────────────────────────────────

_default_service: Optional[OAuthService] = None


def get_oauth_service() -> OAuthService:
    """返回单例 OAuthService（自动注册 google/github/wechat）"""
    global _default_service
    if _default_service is not None:
        return _default_service

    svc = OAuthService()
    svc.register_provider(
        name="google",
        client_id="",
        client_secret="",
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
        scopes=["openid", "email", "profile"],
    )
    svc.register_provider(
        name="github",
        client_id="",
        client_secret="",
        auth_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        userinfo_url="https://api.github.com/user",
        scopes=["read:user", "user:email"],
    )
    svc.register_provider(
        name="wechat",
        client_id="",
        client_secret="",
        auth_url="https://open.weixin.qq.com/connect/qrconnect",
        token_url="https://api.weixin.qq.com/sns/oauth2/access_token",
        userinfo_url="https://api.weixin.qq.com/sns/userinfo",
        scopes=["snsapi_login"],
    )
    _default_service = svc
    return svc
