"""API Key 管理路由：创建、列出、吊销、用量统计。"""
import json
from datetime import datetime, timedelta, date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.api_key import ApiKey, ApiKeyUsage
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/api-keys", tags=["API Key 管理"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class ApiKeyCreateRequest(BaseModel):
    name: str = Field(default="默认 Key", max_length=128)
    permissions: list[str] = Field(default=["read"], description="权限列表")
    rate_limit: int = Field(default=1000, ge=1, le=10000, description="每小时速率限制")


class ApiKeyCreateResponse(BaseModel):
    id: int
    key: str  # 全量 Key（仅创建时返回一次）
    name: str
    permissions: list[str]
    rate_limit: int
    is_active: bool
    created_at: datetime
    warning: str = "请立即保存此 Key，它只会被显示这一次！"


class ApiKeyItem(BaseModel):
    id: int
    masked_key: str  # 掩码后的 Key
    name: str
    permissions: list[str]
    rate_limit: int
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyUsageItem(BaseModel):
    date: str
    key_id: int
    key_name: str
    request_count: int


class ApiKeyUsageResponse(BaseModel):
    usage: list[ApiKeyUsageItem]
    total: int


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    req: ApiKeyCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建新的 API Key（返回完整 Key，仅此一次）"""
    api_key = ApiKey(
        user_id=user.id,
        name=req.name,
        permissions=json.dumps(req.permissions, ensure_ascii=False),
        rate_limit=req.rate_limit,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return ApiKeyCreateResponse(
        id=api_key.id,
        key=api_key.key,
        name=api_key.name,
        permissions=api_key.get_permissions_list(),
        rate_limit=api_key.rate_limit,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
    )


@router.get("", response_model=list[ApiKeyItem])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """列出当前用户的所有 API Key（返回掩码后的 Key）"""
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()

    return [
        ApiKeyItem(
            id=k.id,
            masked_key=k.mask_key(),
            name=k.name,
            permissions=k.get_permissions_list(),
            rate_limit=k.rate_limit,
            is_active=k.is_active,
            last_used_at=k.last_used_at,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """吊销指定的 API Key"""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id)
    )
    api_key = result.scalars().first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key 不存在")

    api_key.is_active = False
    await db.commit()


@router.get("/usage", response_model=ApiKeyUsageResponse)
async def get_api_key_usage(
    days: int = Query(default=7, ge=1, le=90, description="查询最近N天"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取 API Key 用量统计（按天/按 Key）"""
    since = date.today() - timedelta(days=days - 1)

    # 查询当前用户的所有 key
    keys_result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id)
    )
    keys = {k.id: k.name for k in keys_result.scalars().all()}

    if not keys:
        return ApiKeyUsageResponse(usage=[], total=0)

    # 聚合用量
    usage_result = await db.execute(
        select(
            ApiKeyUsage.api_key_id,
            ApiKeyUsage.date,
            func.sum(ApiKeyUsage.request_count).label("total_count"),
        ).where(
            and_(
                ApiKeyUsage.api_key_id.in_(list(keys.keys())),
                ApiKeyUsage.date >= since.isoformat(),
            )
        ).group_by(ApiKeyUsage.api_key_id, ApiKeyUsage.date)
        .order_by(ApiKeyUsage.date.desc(), ApiKeyUsage.api_key_id)
    )

    usage_items = []
    for row in usage_result.all():
        usage_items.append(ApiKeyUsageItem(
            key_id=row.api_key_id,
            key_name=keys.get(row.api_key_id, "未知"),
            date=row.date,
            request_count=row.total_count or 0,
        ))

    total = sum(item.request_count for item in usage_items)

    return ApiKeyUsageResponse(usage=usage_items, total=total)
