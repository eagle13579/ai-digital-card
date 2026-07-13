"""
Tenant 管理 API — 租户 CRUD 与当前租户信息查询。

路由:
  - POST   /api/v1/admin/tenants   — 创建租户 (admin only)
  - GET    /api/v1/admin/tenants   — 租户列表 (admin only)
  - GET    /api/v1/tenant/profile  — 当前租户信息 (需要 tenant_id)
"""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tenant import Plan, Tenant
from app.models.user import User
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tenant 管理"])

# ── Admin 依赖 ─────────────────────────────────────────────────────────────

async def _require_admin(current_user: User = Depends(get_current_user)) -> bool:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足：需要管理员角色")
    return True


AdminDep = Depends(_require_admin)


# ── Schemas (内联) ────────────────────────────────────────────────────────

from pydantic import BaseModel, Field  # noqa: E402


class TenantCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="租户名称")
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9_-]+$", description="唯一标识（小写字母/数字/下划线/连字符）")
    plan: str = Field(default=Plan.FREE, description=f"套餐: {', '.join(p.value for p in Plan)}")


class TenantResponse(BaseModel):
    id: int
    name: str
    slug: str
    plan: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TenantListResponse(BaseModel):
    total: int
    items: list[TenantResponse]


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post(
    "/api/v1/admin/tenants",
    response_model=TenantResponse,
    summary="创建租户 (admin only)",
)
async def create_tenant(
    data: TenantCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = AdminDep,
):
    """创建一个新租户。仅 admin 角色可操作。"""
    # 检查 slug 唯一
    result = await db.execute(select(Tenant).where(Tenant.slug == data.slug))
    if result.scalars().first():
        raise HTTPException(status_code=409, detail=f"slug '{data.slug}' 已被占用")

    tenant = Tenant(name=data.name, slug=data.slug, plan=data.plan)
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    logger.info("租户创建成功: id=%d slug=%s", tenant.id, tenant.slug)
    return TenantResponse.model_validate(tenant)


@router.get(
    "/api/v1/admin/tenants",
    response_model=TenantListResponse,
    summary="租户列表 (admin only)",
)
async def list_tenants(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    _: bool = AdminDep,
):
    """分页获取所有租户列表。仅 admin 角色可操作。"""
    count_q = select(func.count(Tenant.id))
    total = (await db.execute(count_q)).scalar() or 0

    q = select(Tenant).order_by(Tenant.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(q)).scalars().all()

    return TenantListResponse(
        total=total,
        items=[TenantResponse.model_validate(r) for r in rows],
    )


@router.get(
    "/api/v1/tenant/profile",
    response_model=TenantResponse,
    summary="当前租户信息",
)
async def tenant_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """返回当前请求关联的租户信息（需要 tenant_id context）。"""
    from app.middleware.tenant import tenant_id_var

    tid = tenant_id_var.get()
    if tid is None:
        raise HTTPException(status_code=400, detail="当前请求未关联租户")

    result = await db.execute(select(Tenant).where(Tenant.id == tid))
    tenant = result.scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    return TenantResponse.model_validate(tenant)
