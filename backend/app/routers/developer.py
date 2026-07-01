"""Developer API: API Key management and usage statistics."""
import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.api_key import ApiKey, ApiKeyUsage
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/developer", tags=["Developer API"])


# ── Schemas ──

class CreateApiKeyRequest(BaseModel):
    name: str = Field(default="Default Key", max_length=128)
    permissions: list[str] = Field(default=["read"])


class CreateApiKeyResponse(BaseModel):
    id: int
    key: str
    name: str
    permissions: list[str]
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class ApiKeyListItem(BaseModel):
    id: int
    masked_key: str
    name: str
    permissions: list[str]
    is_active: bool
    last_used_at: str | None
    created_at: str

    model_config = {"from_attributes": True}


class UsageResponse(BaseModel):
    total_requests: int
    this_month: int
    today: int


# ── Routes ──

@router.post("/api-keys", response_model=CreateApiKeyResponse, status_code=201)
async def create_api_key(
    req: CreateApiKeyRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new API Key (full token returned only once)."""
    api_key = ApiKey(
        user_id=user.id,
        name=req.name,
        permissions=json.dumps(req.permissions, ensure_ascii=False),
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return CreateApiKeyResponse(
        id=api_key.id,
        key=api_key.key,
        name=api_key.name,
        permissions=req.permissions,
        is_active=api_key.is_active,
        created_at=str(api_key.created_at),
    )


@router.get("/api-keys", response_model=list[ApiKeyListItem])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all API keys for the current user (masked tokens only)."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        ApiKeyListItem(
            id=k.id,
            masked_key=k.mask_key(),
            name=k.name,
            permissions=k.get_permissions_list(),
            is_active=k.is_active,
            last_used_at=str(k.last_used_at) if k.last_used_at else None,
            created_at=str(k.created_at),
        )
        for k in keys
    ]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Revoke (deactivate) an API Key by ID."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id)
    )
    api_key = result.scalars().first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    api_key.is_active = False
    await db.commit()


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get usage statistics: total requests, this month, today."""
    today_str = date.today().isoformat()
    month_start = date.today().replace(day=1).isoformat()

    keys_result = await db.execute(
        select(ApiKey.id).where(ApiKey.user_id == user.id)
    )
    key_ids = [row[0] for row in keys_result.all()]

    if not key_ids:
        return UsageResponse(total_requests=0, this_month=0, today=0)

    total_result = await db.execute(
        select(func.coalesce(func.sum(ApiKeyUsage.request_count), 0))
        .where(ApiKeyUsage.api_key_id.in_(key_ids))
    )
    total = total_result.scalar() or 0

    month_result = await db.execute(
        select(func.coalesce(func.sum(ApiKeyUsage.request_count), 0))
        .where(
            and_(
                ApiKeyUsage.api_key_id.in_(key_ids),
                ApiKeyUsage.date >= month_start,
            )
        )
    )
    this_month = month_result.scalar() or 0

    today_result = await db.execute(
        select(func.coalesce(func.sum(ApiKeyUsage.request_count), 0))
        .where(
            and_(
                ApiKeyUsage.api_key_id.in_(key_ids),
                ApiKeyUsage.date == today_str,
            )
        )
    )
    today = today_result.scalar() or 0

    return UsageResponse(
        total_requests=total,
        this_month=this_month,
        today=today,
    )
