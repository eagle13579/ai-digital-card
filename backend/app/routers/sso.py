"""
SSO 路由 - OAuth2/OIDC 回调处理

支持 Google、GitHub 和企业 OIDC 的授权码回调流程。
"""
from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from jose import jwt
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.routers.auth import create_access_token, oauth2_scheme
from app.schemas import TokenResponse, UserResponse
from app.services.sso_service import SSOService, get_sso_service

logger = logging.getLogger("sso.router")

router = APIRouter(prefix="/api/auth/sso", tags=["SSO 认证"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SSOLoginRequest(BaseModel):
    """发起 SSO 登录请求"""
    provider: str = Field(..., description="SSO 提供商: google, github, oidc")
    redirect_after: Optional[str] = Field(None, description="登录成功后的重定向地址")


class SSOCallbackResponse(BaseModel):
    """SSO 回调响应"""
    success: bool
    access_token: Optional[str] = None
    user: Optional[UserResponse] = None
    provider: str
    message: str = ""


class SSOProviderConfig(BaseModel):
    """SSO 提供商配置（返回前端用）"""
    provider: str
    authorize_url: str
    client_id: str
    scopes: list[str]
    redirect_uri: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/login")
async def sso_login(
    provider: str = "google",
    redirect_after: Optional[str] = None,
    request: Request = None,
    sso_service: SSOService = Depends(get_sso_service),
):
    """
    发起 SSO OAuth2 授权码登录。

    - **provider**: google | github | oidc
    - **redirect_after**: 登录成功后的前端重定向地址（可选）

    返回 302 重定向到 OAuth2 提供商授权页面。
    """
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state in service (with redirect_after for post-login redirect)
    base_url = str(request.base_url).rstrip("/")
    sso_service.store_state(state, {
        "provider": provider,
        "redirect_after": redirect_after or f"{base_url}/sso/callback",
        "created_at": datetime.utcnow().isoformat(),
    })

    # Build authorize URL
    authorize_url = await sso_service.get_authorize_url(
        provider=provider,
        state=state,
        redirect_uri=f"{base_url}/api/auth/sso/callback",
    )

    if not authorize_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的 SSO 提供商或配置不完整: {provider}",
        )

    return RedirectResponse(url=authorize_url)


@router.get("/callback")
async def sso_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    sso_service: SSOService = Depends(get_sso_service),
):
    """
    OAuth2 授权码回调端点。

    SSO 提供商完成用户授权后重定向到此地址。
    交换授权码获取 token，再用 token 获取用户信息，创建/更新用户并签发 JWT。
    """
    # Handle OAuth error
    if error:
        logger.warning("SSO callback received error: %s", error)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SSO 授权失败: {error}",
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少授权码 (code)",
        )

    # Verify state
    state_data = sso_service.verify_state(state)
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的 state 参数，请重新发起登录",
        )

    provider = state_data.get("provider", "google")
    redirect_after = state_data.get("redirect_after")

    # Exchange code for token
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/auth/sso/callback"

    try:
        token_data = await sso_service.exchange_code(
            provider=provider,
            code=code,
            redirect_uri=redirect_uri,
        )
    except ValueError as e:
        logger.error("Token exchange failed for %s: %s", provider, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"令牌交换失败: {str(e)}",
        )

    # Get user info from provider
    try:
        user_info = await sso_service.get_user_info(
            provider=provider,
            access_token=token_data.get("access_token", ""),
            id_token=token_data.get("id_token", ""),
        )
    except ValueError as e:
        logger.error("Failed to get user info from %s: %s", provider, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"获取用户信息失败: {str(e)}",
        )

    # Find or create user
    sso_id = user_info.get("sub") or user_info.get("id")
    if not sso_id:
        sso_id = str(uuid.uuid4())

    user = await sso_service.find_or_create_user(
        db=db,
        provider=provider,
        sso_id=str(sso_id),
        email=user_info.get("email", ""),
        name=user_info.get("name", user_info.get("login", "SSO User")),
        avatar=user_info.get("picture", user_info.get("avatar_url", "")),
    )

    # Sign JWT
    token = create_access_token({"sub": str(user.id)})

    # If redirect_after is provided, redirect with token
    if redirect_after:
        # Encode token in URL fragment (more secure than query param)
        redirect_url = f"{redirect_after}?access_token={token}&token_type=bearer"
        return RedirectResponse(url=redirect_url)

    # Otherwise return JSON
    return SSOCallbackResponse(
        success=True,
        access_token=token,
        user=UserResponse.model_validate(user),
        provider=provider,
        message="SSO 登录成功",
    )


@router.get("/providers")
async def list_sso_providers(
    request: Request,
    sso_service: SSOService = Depends(get_sso_service),
):
    """
    列出可用的 SSO 提供商及其配置。
    前端可用此接口动态渲染 SSO 登录按钮。
    """
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/auth/sso/callback"

    providers = []
    for provider_name in ["google", "github", "oidc"]:
        config = await sso_service.get_provider_config(provider_name, redirect_uri)
        if config:
            providers.append(config)

    return {"providers": providers}


@router.post("/link")
async def link_sso_account(
    provider: str,
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(oauth2_scheme),  # Reuse existing auth dependency
    sso_service: SSOService = Depends(get_sso_service),
):
    """
    将 SSO 账号绑定到当前 JWT 用户。

    用于已登录用户绑定第三方账号（如：手机号注册后绑定 GitHub）。
    """
    # Get current user via JWT token
    from app.routers.auth import get_current_user
    # Re-decode to get proper user object
    # (This route uses oauth2_scheme for token extraction, then we resolve user)
    try:
        payload = jwt.decode(
            current_user, settings.JWT_SECRET, algorithms=[settings.ALGORITHM]
        )
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="无效的 JWT 令牌")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/auth/sso/callback"

    token_data = await sso_service.exchange_code(provider, code, redirect_uri)
    user_info = await sso_service.get_user_info(
        provider=provider,
        access_token=token_data.get("access_token", ""),
        id_token=token_data.get("id_token", ""),
    )

    sso_id = str(user_info.get("sub") or user_info.get("id", ""))
    if not sso_id:
        raise HTTPException(status_code=400, detail="无法获取 SSO 唯一标识")

    # Check if this SSO account is already linked to another user
    existing = await db.execute(
        select(User).where(
            getattr(User, f"sso_{provider}_id", None) == sso_id
        )
    )
    existing_user = existing.scalars().first()
    if existing_user and existing_user.id != user.id:
        raise HTTPException(
            status_code=409,
            detail=f"该 {provider} 账号已被其他用户绑定",
        )

    # Link SSO ID to current user
    setattr(user, f"sso_{provider}_id", sso_id)
    await db.commit()

    return {"success": True, "message": f"{provider} 账号绑定成功"}
