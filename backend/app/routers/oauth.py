"""OAuth2 SSO 路由 — login / callback / providers / link"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.routers.auth import create_access_token, get_current_user
from app.schemas import TokenResponse, UserResponse
from app.services.oauth_service import OAuthService, get_oauth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/oauth", tags=["OAuth2 SSO"])


def _get_sso_id_field(provider: str, sso_id: str) -> str:
    """直接返回 provider ID 字段名供 getattr/setattr 使用"""
    return f"sso_{provider}_id"


# ── 登录：重定向到三方授权页 ────────────────────────────────────────────────

@router.get("/{provider}/login")
async def oauth_login(
    provider: str,
    request: Request,
    sso: OAuthService = Depends(get_oauth_service),
):
    config = sso.get_provider(provider)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的 OAuth provider: {provider}",
        )

    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/v1/oauth/{provider}/callback"
    auth_url = sso.get_authorization_url(provider, redirect_uri)
    if not auth_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="无法生成授权 URL",
        )
    return RedirectResponse(url=auth_url)


# ── 回调：兑换 code → token → 用户信息 → 创建/登录 → JWT ──────────────────

@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: Optional[str] = None,
    error: Optional[str] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    sso: OAuthService = Depends(get_oauth_service),
):
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth 授权失败: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="缺少授权码 code")

    config = sso.get_provider(provider)
    if not config:
        raise HTTPException(status_code=400, detail=f"不支持的 provider: {provider}")

    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/v1/oauth/{provider}/callback"

    # 1. 兑换 token
    try:
        token_data = await sso.exchange_code(provider, code, redirect_uri)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    access_token = token_data.get("access_token", "")
    user_raw = await sso.get_user_info(provider, access_token)

    sso_id = str(user_raw.get("sub") or user_raw.get("id", ""))
    email = user_raw.get("email", "")
    name = user_raw.get("name", "SSO User")
    picture = user_raw.get("picture", "")

    # 2. 查找或创建用户
    id_field = _get_sso_id_field(provider, sso_id)
    result = await db.execute(select(User).where(getattr(User, id_field, None) == sso_id))
    user = result.scalars().first()

    if not user and email:
        result = await db.execute(select(User).where(User.phone == email))
        user = result.scalars().first()
        if user:
            setattr(user, id_field, sso_id)

    if not user:
        from app.routers.auth import pwd_context
        import uuid
        import secrets

        rand = uuid.uuid4().hex[:8]
        phone = email or f"sso_{rand}"
        user = User(
            phone=phone,
            name=name or f"{provider}_user_{rand[:6]}",
            password_hash=pwd_context.hash(secrets.token_urlsafe(16)),
            avatar=picture or "",
            company="",
            title="",
            intro=f"通过 {provider} 登录",
            role="viewer",
        )
        setattr(user, id_field, sso_id)
        db.add(user)

    if name:
        user.name = name
    if picture:
        user.avatar = picture
    await db.commit()
    await db.refresh(user)

    # 3. 签发 JWT
    jwt_token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


# ── 列出已注册 provider ─────────────────────────────────────────────────────

@router.get("/providers")
async def list_providers(sso: OAuthService = Depends(get_oauth_service)):
    providers = []
    for name in sso.list_providers():
        cfg = sso.get_provider(name)
        if cfg:
            providers.append({
                "provider": cfg.name,
                "auth_url": cfg.auth_url,
                "scopes": cfg.scopes,
                "configured": bool(cfg.client_id and cfg.client_secret),
            })
    return {"providers": providers}


# ── 绑定 OAuth 账号到当前用户 ──────────────────────────────────────────────

class LinkRequest:
    def __init__(self, provider: str, code: str):
        self.provider = provider
        self.code = code


@router.post("/link")
async def link_oauth_account(
    provider: str,
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sso: OAuthService = Depends(get_oauth_service),
):
    config = sso.get_provider(provider)
    if not config:
        raise HTTPException(status_code=400, detail=f"不支持的 provider: {provider}")

    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/v1/oauth/{provider}/callback"

    try:
        token_data = await sso.exchange_code(provider, code, redirect_uri)
        user_raw = await sso.get_user_info(provider, token_data.get("access_token", ""))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    sso_id = str(user_raw.get("sub") or user_raw.get("id", ""))
    if not sso_id:
        raise HTTPException(status_code=400, detail="无法获取 OAuth 唯一标识")

    # 检查是否已被其他用户绑定
    id_field = _get_sso_id_field(provider, sso_id)
    result = await db.execute(select(User).where(getattr(User, id_field, None) == sso_id))
    existing = result.scalars().first()
    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=409, detail=f"该 {provider} 账号已被其他用户绑定")

    setattr(current_user, id_field, sso_id)
    await db.commit()
    return {"success": True, "message": f"{provider} 账号绑定成功"}
