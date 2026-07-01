"""
SSO 服务层 — OAuth2/OIDC 认证逻辑

封装 Google、GitHub、企业 OIDC 的 OAuth2 授权码流程，
包括授权 URL 构建、令牌交换、用户信息获取、用户查找/创建。
"""
from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from jose import jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User

logger = logging.getLogger("sso.service")


# ── SSO 提供商配置 ────────────────────────────────────────────────────────────

class ProviderConfig(BaseModel):
    """OAuth2 提供商配置"""
    provider: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: list[str]
    client_id: str
    client_secret: str
    extra_params: dict = {}

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)


class SSOService:
    """
    SSO 服务：管理 OAuth2/OIDC 认证流程。

    支持 Google、GitHub 和通用 OpenID Connect 提供商。
    """

    def __init__(self):
        # In-memory state store (use Redis in production)
        self._state_store: dict[str, dict] = {}
        self._state_ttl = timedelta(minutes=10)

        # Build provider configurations
        self._providers: dict[str, ProviderConfig] = self._init_providers()

    def _init_providers(self) -> dict[str, ProviderConfig]:
        """从 settings 初始化提供商配置"""
        providers = {}

        # Google OAuth2/OIDC
        if settings.SSO_GOOGLE_CLIENT_ID:
            providers["google"] = ProviderConfig(
                provider="google",
                authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
                scopes=["openid", "email", "profile"],
                client_id=settings.SSO_GOOGLE_CLIENT_ID,
                client_secret=settings.SSO_GOOGLE_CLIENT_SECRET,
                extra_params={"access_type": "offline", "prompt": "consent"},
            )

        # GitHub OAuth2
        if settings.SSO_GITHUB_CLIENT_ID:
            providers["github"] = ProviderConfig(
                provider="github",
                authorize_url="https://github.com/login/oauth/authorize",
                token_url="https://github.com/login/oauth/access_token",
                userinfo_url="https://api.github.com/user",
                scopes=["read:user", "user:email"],
                client_id=settings.SSO_GITHUB_CLIENT_ID,
                client_secret=settings.SSO_GITHUB_CLIENT_SECRET,
                extra_params={},
            )

        # Enterprise OIDC
        oidc_client_id = settings.SSO_OIDC_CLIENT_ID
        oidc_auth_url = settings.SSO_OIDC_AUTHORIZE_URL
        if oidc_client_id and oidc_auth_url:
            providers["oidc"] = ProviderConfig(
                provider="oidc",
                authorize_url=oidc_auth_url,
                token_url=settings.SSO_OIDC_TOKEN_URL,
                userinfo_url=settings.SSO_OIDC_USERINFO_URL,
                scopes=settings.SSO_OIDC_SCOPES.split(","),
                client_id=oidc_client_id,
                client_secret=settings.SSO_OIDC_CLIENT_SECRET,
                extra_params={},
            )

        return providers

    # ── State 管理 ────────────────────────────────────────────────────────────

    def store_state(self, state: str, data: dict) -> None:
        """存储 OAuth state 用于 CSRF 校验"""
        self._state_store[state] = data

    def verify_state(self, state: Optional[str]) -> Optional[dict]:
        """
        验证并移除 OAuth state。

        返回 state 关联的数据，如果无效或过期返回 None。
        """
        if not state:
            return None

        data = self._state_store.pop(state, None)
        if not data:
            return None

        # Check TTL
        created = data.get("created_at")
        if created:
            try:
                created_dt = datetime.fromisoformat(created)
                if datetime.utcnow() - created_dt > self._state_ttl:
                    logger.warning("SSO state expired: %s", state[:8])
                    return None
            except (ValueError, TypeError):
                pass

        return data

    # ── 授权 URL 构建 ─────────────────────────────────────────────────────────

    async def get_authorize_url(
        self,
        provider: str,
        state: str,
        redirect_uri: str,
    ) -> Optional[str]:
        """
        构建 OAuth2 授权页面的 URL。

        Args:
            provider: 提供商名称 (google/github/oidc)
            state: CSRF state token
            redirect_uri: 回调地址

        Returns:
            完整的授权 URL，如果提供商未配置则返回 None
        """
        config = self._providers.get(provider)
        if not config or not config.is_configured:
            logger.warning("SSO provider %s not configured", provider)
            return None

        params = {
            "client_id": config.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": " ".join(config.scopes),
            "state": state,
        }
        params.update(config.extra_params)

        # Build URL with query params
        query_string = "&".join(f"{k}={self._urlencode(v)}" for k, v in params.items())
        return f"{config.authorize_url}?{query_string}"

    # ── 令牌交换 ──────────────────────────────────────────────────────────────

    async def exchange_code(
        self,
        provider: str,
        code: str,
        redirect_uri: str,
    ) -> dict[str, Any]:
        """
        用授权码交换访问令牌。

        Args:
            provider: 提供商名称
            code: 授权码
            redirect_uri: 回调地址（必须与授权请求一致）

        Returns:
            token 数据字典，包含 access_token, id_token (OIDC), token_type 等

        Raises:
            ValueError: 令牌交换失败
        """
        config = self._providers.get(provider)
        if not config or not config.is_configured:
            raise ValueError(f"SSO provider '{provider}' not configured")

        # GitHub 期望 Accept header 为 json
        headers = {"Accept": "application/json"}
        data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    config.token_url,
                    data=data,
                    headers=headers,
                )
                resp.raise_for_status()
                token_data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "Token exchange HTTP error for %s: %s - %s",
                provider, e.response.status_code, e.response.text,
            )
            raise ValueError(f"令牌交换 HTTP 错误: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error("Token exchange request failed for %s: %s", provider, e)
            raise ValueError(f"令牌交换请求失败: {str(e)}")

        # Check error in response
        if "error" in token_data:
            error_desc = token_data.get("error_description", token_data["error"])
            logger.error(
                "Token exchange error for %s: %s", provider, error_desc
            )
            raise ValueError(f"提供商返回错误: {error_desc}")

        return token_data

    # ── 用户信息获取 ──────────────────────────────────────────────────────────

    async def get_user_info(
        self,
        provider: str,
        access_token: str,
        id_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        用访问令牌获取用户信息。

        OIDC 提供商优先从 id_token 中直接解析用户信息（无需额外请求）。

        Args:
            provider: 提供商名称
            access_token: OAuth2 访问令牌
            id_token: OIDC ID 令牌（可选）

        Returns:
            标准化的用户信息字典，包含 sub/email/name/picture 等字段
        """
        config = self._providers.get(provider)
        if not config:
            raise ValueError(f"SSO provider '{provider}' not configured")

        # 对于 OIDC 提供商，优先从 id_token 解码
        if id_token and provider in ("google", "oidc"):
            try:
                user_info = self._decode_id_token(id_token, config)
                if user_info:
                    return user_info
            except Exception as e:
                logger.warning(
                    "Failed to decode id_token for %s, falling back to userinfo: %s",
                    provider, e,
                )

        # Fallback: 调用 userinfo 端点
        headers = {"Authorization": f"Bearer {access_token}"}

        if provider == "github":
            headers["Accept"] = "application/vnd.github.v3+json"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(config.userinfo_url, headers=headers)
                resp.raise_for_status()
                raw_info = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "Userinfo request failed for %s: %s - %s",
                provider, e.response.status_code, e.response.text,
            )
            raise ValueError(f"获取用户信息 HTTP 错误: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error("Userinfo request failed for %s: %s", provider, e)
            raise ValueError(f"获取用户信息请求失败: {str(e)}")

        # 标准化字段
        return self._normalize_user_info(provider, raw_info)

    def _decode_id_token(
        self, id_token: str, config: ProviderConfig
    ) -> Optional[dict[str, Any]]:
        """
        解码并验证 OIDC ID 令牌。

        不验证签名（开发模式），仅解析 payload。
        生产环境应验证 issuer、audience 和签名。
        """
        try:
            # 不验证签名的快速解码（开发/演示用）
            unverified = jwt.get_unverified_claims(id_token)
            if isinstance(unverified, dict):
                return self._normalize_user_info(config.provider, unverified)
        except Exception as e:
            logger.debug("id_token decode failed: %s", e)
        return None

    def _normalize_user_info(
        self, provider: str, raw: dict[str, Any]
    ) -> dict[str, Any]:
        """将不同提供商的用户信息标准化为统一格式"""
        normalized = {}

        if provider == "google":
            normalized = {
                "sub": raw.get("sub"),
                "email": raw.get("email", ""),
                "name": raw.get("name", ""),
                "picture": raw.get("picture", ""),
                "locale": raw.get("locale", ""),
            }
        elif provider == "github":
            normalized = {
                "sub": str(raw.get("id", "")),
                "email": raw.get("email", "") or self._get_github_email(raw.get("login", "")),
                "name": raw.get("name", "") or raw.get("login", ""),
                "picture": raw.get("avatar_url", ""),
                "login": raw.get("login", ""),
            }
        elif provider == "oidc":
            normalized = {
                "sub": raw.get("sub"),
                "email": raw.get("email", ""),
                "name": raw.get("name", raw.get("preferred_username", "")),
                "picture": raw.get("picture", raw.get("avatar", "")),
            }
        else:
            # Generic fallback
            normalized = {
                "sub": raw.get("sub", raw.get("id", "")),
                "email": raw.get("email", ""),
                "name": raw.get("name", raw.get("display_name", "")),
                "picture": raw.get("picture", raw.get("avatar_url", "")),
            }

        return {k: v for k, v in normalized.items() if v is not None}

    def _get_github_email(self, username: str) -> str:
        """GitHub 公共邮箱占位（生产环境应调用 /user/emails API）"""
        return f"{username}@users.noreply.github.com"

    # ── 用户查找/创建 ─────────────────────────────────────────────────────────

    async def find_or_create_user(
        self,
        db: AsyncSession,
        provider: str,
        sso_id: str,
        email: str,
        name: str,
        avatar: str = "",
    ) -> User:
        """
        根据 SSO 信息查找或创建用户。

        查找策略：
        1. 先按 sso_{provider}_id 精确匹配
        2. 再按 email 匹配
        3. 都未找到则创建新用户

        Args:
            db: 数据库会话
            provider: SSO 提供商名称
            sso_id: 提供商返回的用户唯一标识
            email: 用户邮箱
            name: 用户显示名
            avatar: 用户头像 URL

        Returns:
            User 实例
        """
        from app.routers.auth import pwd_context

        sso_field = f"sso_{provider}_id"

        # 1. 通过 SSO ID 查找
        query = select(User).where(
            getattr(User, sso_field, None) == sso_id
        )
        result = await db.execute(query)
        user = result.scalars().first()

        if user:
            # Update profile from SSO
            if name:
                user.name = name
            if avatar:
                user.avatar = avatar
            await db.commit()
            await db.refresh(user)
            logger.info("SSO user found and updated: user=%d, provider=%s", user.id, provider)
            return user

        # 2. 通过 email 查找
        if email:
            result = await db.execute(select(User).where(User.phone == email))
            user = result.scalars().first()
            if user:
                # Link SSO ID to existing user
                setattr(user, sso_field, sso_id)
                if name:
                    user.name = name
                if avatar:
                    user.avatar = avatar
                await db.commit()
                await db.refresh(user)
                logger.info(
                    "Existing user linked to SSO: user=%d, provider=%s",
                    user.id, provider,
                )
                return user

        # 3. 创建新用户
        import uuid
        random_suffix = uuid.uuid4().hex[:8]
        # Use email as phone if available, otherwise generate
        phone = email if email else f"sso_{random_suffix[:10]}"

        user = User(
            phone=phone,
            name=name or f"{provider}_user_{random_suffix[:6]}",
            password_hash=pwd_context.hash(secrets.token_urlsafe(16)),
            avatar=avatar or "",
            company="",
            title="",
            intro=f"通过 {provider} SSO 登录",
            role="viewer",  # New SSO users default to viewer
        )
        # Set provider-specific SSO ID
        setattr(user, sso_field, sso_id)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info("New user created via SSO: user=%d, provider=%s", user.id, provider)
        return user

    # ── 提供商配置（给前端用） ────────────────────────────────────────────────

    async def get_provider_config(
        self, provider: str, redirect_uri: str
    ) -> Optional[dict]:
        """
        获取提供商的前端配置（不含 secret）。

        前端用此配置渲染 SSO 登录按钮。
        """
        config = self._providers.get(provider)
        if not config or not config.is_configured:
            return None

        return {
            "provider": config.provider,
            "authorize_url": config.authorize_url,
            "client_id": config.client_id,
            "scopes": config.scopes,
            "redirect_uri": redirect_uri,
        }

    # ── 工具方法 ──────────────────────────────────────────────────────────────

    @staticmethod
    def _urlencode(value: str) -> str:
        """简易 URL 编码（替代 urllib.parse.quote）"""
        import urllib.parse
        return urllib.parse.quote(value, safe="")


# ── 单例 / 依赖注入 ───────────────────────────────────────────────────────────

_sso_service_instance: Optional[SSOService] = None


def get_sso_service() -> SSOService:
    """FastAPI 依赖项：获取 SSO 服务实例"""
    global _sso_service_instance
    if _sso_service_instance is None:
        _sso_service_instance = SSOService()
    return _sso_service_instance
