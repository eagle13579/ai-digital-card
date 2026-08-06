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


def _get_profile_service() -> UnifiedProfileService:
    """FastAPI dependency: create a UnifiedProfileService instance."""
    from app.database import get_db as _get_db

    adapter = SQLAlchemyProfileAdapter(_get_db)
    return UnifiedProfileService(adapter)


# ======================================================================
# Endpoints
# ======================================================================


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: str,
    service: UnifiedProfileService = Depends(_get_profile_service),
):
    """Retrieve a single unified profile by user ID."""
    profile = await service.get_profile(user_id)
    if profile is None:
        raise_http_error(404, "NOT_FOUND", f"Profile not found: {user_id}")
    return ProfileResponse.from_profile(profile)


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
):
    """Search profiles by keyword, or list all with pagination."""
    if keyword:
        profiles = await service.search_profiles(keyword, limit=limit)
    else:
        profiles = await service.list_all_profiles(skip=skip, limit=limit)

    items = [ProfileResponse.from_profile(p) for p in profiles]
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
):
    """List all user profiles belonging to a specific product.

    Examples:
      - ``ai-digital-brochure``  → local users table
      - ``chainke-full``         → (requires RemoteApiAdapter)
      - ``go-aiport``            → (requires RemoteApiAdapter)
    """
    profiles = await service.get_cross_product_users(product_name)
    return [ProfileResponse.from_profile(p) for p in profiles]


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
