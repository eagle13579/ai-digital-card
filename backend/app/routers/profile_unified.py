"""Unified User Profile Router — cross-product user identity API.

Prefix: /api/unified/profile
Tags: 统一用户画像

Exposes UnifiedProfileService as REST endpoints so all products
(AI数字名片, chainke-full, go-aiport, CRM) can share user profile data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api_standards import PaginatedResponse, raise_http_error
from app.database import get_db
from app.identity.unified_profile import (
    UnifiedProfileService,
    SQLAlchemyProfileAdapter,
    UnifiedUserProfile,
)

# NOTE: 认证依赖在本地定义(复用 app.auth_jwt), 避免导入 app.routers.auth 造成
# app.routers.auth <-> crm_router 循环导入 (crm_router 会 import auth 的 get_current_user)
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth_jwt import decode_access_token
from app.models.user import User

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def _get_current_user(
    token: str | None = Depends(_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """本地认证依赖: 从 JWT 解析当前用户 (与 auth.py::get_current_user 等价)。"""
    from fastapi import HTTPException
    cred_exc = HTTPException(status_code=401, detail="无法验证凭证")
    if not token:
        raise cred_exc
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", 0))
    except (JWTError, ValueError, TypeError):
        raise cred_exc
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise cred_exc
    return user

router = APIRouter(prefix="/api/unified/profile", tags=["统一用户画像"])


# ======================================================================
# Pydantic schemas for API I/O
# ======================================================================


class ProfileResponse(BaseModel):
    """API response model for a unified user profile."""

    user_id: str = Field(..., description="Unique user identifier")
    source_product: str = Field("", description="Origin product name")
    username: str | None = Field(None, description="Login username")
    phone: str | None = Field(None, description="Phone number")
    name: str = Field("", description="Display name")
    company: str = Field("", description="Company / organization")
    title: str = Field("", description="Job title")
    intro: str = Field("", description="Brief introduction")
    avatar: str = Field("", description="Avatar URL")
    email: str | None = Field(None, description="Email address")
    role: str = Field("user", description="User role")
    membership_tier: str = Field("free", description="Subscription tier")
    is_active: bool = Field(True, description="Whether account is active")
    created_at: str | None = Field(None, description="Account creation timestamp")
    updated_at: str | None = Field(None, description="Last update timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra data")

    @classmethod
    def from_profile(cls, p: UnifiedUserProfile) -> ProfileResponse:
        return cls(
            user_id=p.user_id,
            source_product=p.source_product,
            username=p.username,
            phone=p.phone,
            name=p.name,
            company=p.company,
            title=p.title,
            intro=p.intro,
            avatar=p.avatar,
            email=p.email,
            role=p.role,
            membership_tier=p.membership_tier,
            is_active=p.is_active,
            created_at=p.created_at.isoformat() if p.created_at else None,
            updated_at=p.updated_at.isoformat() if p.updated_at else None,
            metadata=p.metadata,
        )


class ProfileMergeRequest(BaseModel):
    """Request body for merging two profiles."""

    source: dict[str, Any] = Field(..., description="Source profile data")
    target: dict[str, Any] = Field(..., description="Target profile data")


class ProfileUpsertRequest(BaseModel):
    """Request body for inserting or updating a profile."""

    user_id: str = Field(..., description="Unique user identifier")
    source_product: str = Field("", description="Origin product name")
    username: str | None = Field(None)
    phone: str | None = Field(None)
    name: str = Field("")
    company: str = Field("")
    title: str = Field("")
    intro: str = Field("")
    avatar: str = Field("")
    email: str | None = Field(None)
    role: str = Field("user")
    membership_tier: str = Field("free")
    is_active: bool = Field(True)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ======================================================================
# Dependency — wire up the service
# ======================================================================


async def _get_profile_service(db: AsyncSession = Depends(get_db)):
    """FastAPI dependency: create a UnifiedProfileService instance.

    复用 FastAPI 注入的同一个 db session (不再内部新建 session),
    避免多重 AsyncSession 导致 IllegalStateChangeError 关闭时序冲突。
    """
    async def _yield_once(_session: AsyncSession):
        yield _session

    adapter = SQLAlchemyProfileAdapter(lambda: _yield_once(db))
    return UnifiedProfileService(adapter)


def _mask_pii(resp: ProfileResponse, is_self: bool = False, is_admin: bool = False) -> ProfileResponse:
    """脱敏 PII: 非本人/非admin时掩码 phone/email (与 match.py::_desensitize_user 风格一致)。

    规则:
      - phone: 保留前3后4 → 138****0001
      - email: 保留用户名首字符 + *** + @域名
    """
    if is_self or is_admin:
        return resp
    if resp.phone:
        p = resp.phone
        resp.phone = (p[:3] + "*" * max(0, len(p) - 7) + p[-4:]) if len(p) >= 7 else p[:1] + "***"
    if resp.email and "@" in resp.email:
        local, _, domain = resp.email.partition("@")
        resp.email = (local[:1] + "***@" + domain) if local else resp.email
    return resp


# ======================================================================
# Endpoints
# ======================================================================


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: str,
    service: UnifiedProfileService = Depends(_get_profile_service),
    current_user: User = Depends(_get_current_user),
):
    """Retrieve a single unified profile by user ID. (需登录; 非本人/非admin返回脱敏PII)"""
    profile = await service.get_profile(user_id)
    if profile is None:
        raise_http_error(404, "NOT_FOUND", f"Profile not found: {user_id}")
    is_self = str(current_user.id) == str(user_id) or str(current_user.phone) == str(profile.phone)
    is_admin = getattr(current_user, "role", "") == "admin"
    return _mask_pii(ProfileResponse.from_profile(profile), is_self=is_self, is_admin=is_admin)


@router.post("/merge", response_model=ProfileResponse)
async def merge_profiles(
    body: ProfileMergeRequest,
    service: UnifiedProfileService = Depends(_get_profile_service),
):
    """Merge source profile into target profile and persist the result.

    Non-empty / non-None fields from source override target fields.
    """
    source = UnifiedUserProfile.from_dict(body.source)
    target = UnifiedUserProfile.from_dict(body.target)
    merged = await service.merge_profile(source, target)
    return ProfileResponse.from_profile(merged)


@router.get("", response_model=PaginatedResponse[ProfileResponse])
async def search_profiles(
    keyword: str = Query("", description="Keyword to search across name, company, title, phone"),
    limit: int = Query(20, ge=1, le=200, description="Max results"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    service: UnifiedProfileService = Depends(_get_profile_service),
    current_user: User = Depends(_get_current_user),
):
    """Search profiles by keyword, or list all with pagination. (需登录; PII脱敏)"""
    if keyword:
        profiles = await service.search_profiles(keyword, limit=limit)
    else:
        profiles = await service.list_all_profiles(skip=skip, limit=limit)

    is_admin = getattr(current_user, "role", "") == "admin"
    items = [_mask_pii(ProfileResponse.from_profile(p), is_self=False, is_admin=is_admin) for p in profiles]
    return PaginatedResponse(
        items=items,
        total=len(items),
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get("/product/{product_name}", response_model=list[ProfileResponse])
async def get_cross_product_users(
    product_name: str,
    service: UnifiedProfileService = Depends(_get_profile_service),
    current_user: User = Depends(_get_current_user),
):
    """List all user profiles belonging to a specific product. (需登录; PII脱敏)

    Examples:
      - ``ai-digital-brochure``  → local users table
      - ``chainke-full``         → (requires RemoteApiAdapter)
      - ``go-aiport``            → (requires RemoteApiAdapter)
    """
    profiles = await service.get_cross_product_users(product_name)
    is_admin = getattr(current_user, "role", "") == "admin"
    return [_mask_pii(ProfileResponse.from_profile(p), is_self=False, is_admin=is_admin) for p in profiles]


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def upsert_profile(
    body: ProfileUpsertRequest,
    service: UnifiedProfileService = Depends(_get_profile_service),
):
    """Insert a new profile or update an existing one.

    If the user_id matches an existing user, fields are updated.
    Otherwise, a stub user is created in the local users table.
    """
    profile = UnifiedUserProfile(
        user_id=body.user_id,
        source_product=body.source_product,
        username=body.username,
        phone=body.phone,
        name=body.name,
        company=body.company,
        title=body.title,
        intro=body.intro,
        avatar=body.avatar,
        email=body.email,
        role=body.role,
        membership_tier=body.membership_tier,
        is_active=body.is_active,
        metadata=body.metadata,
    )
    result = await service.upsert_profile(profile)
    return ProfileResponse.from_profile(result)


@router.post("/{user_id}/refresh", response_model=ProfileResponse)
async def refresh_profile_cache(
    user_id: str,
    service: UnifiedProfileService = Depends(_get_profile_service),
):
    """Refresh cached profile data from the source database.

    (Placeholder for Redis caching layer — for now just re-reads from DB.)
    """
    profile = await service.get_profile(user_id)
    if profile is None:
        raise_http_error(404, "NOT_FOUND", f"Profile not found: {user_id}")
    return ProfileResponse.from_profile(profile)
