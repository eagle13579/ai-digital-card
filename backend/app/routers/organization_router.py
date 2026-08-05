"""
组织/企业名片管理路由 — 多租户组织 CRUD API

API路径: /api/business-card/organizations/*
响应格式: {code: number, message: string, data: any}

功能清单:
  - POST   /api/business-card/organizations                           — 创建组织
  - GET    /api/business-card/organizations                           — 获取我的组织列表
  - GET    /api/business-card/organizations/{id}                      — 组织详情
  - PUT    /api/business-card/organizations/{id}                      — 更新组织
  - DELETE /api/business-card/organizations/{id}                      — 删除组织（仅owner）
  - POST   /api/business-card/organizations/{id}/members              — 添加成员
  - GET    /api/business-card/organizations/{id}/members              — 成员列表
  - DELETE /api/business-card/organizations/{id}/members/{user_id}    — 移除成员
  - POST   /api/business-card/organizations/{id}/invites              — 创建邀请
  - GET    /api/business-card/organizations/{id}/invites              — 邀请列表
  - POST   /api/business-card/organizations/invites/{token}/accept    — 接受邀请
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.organization import Organization, OrganizationMember, Invite
from app.models.user import User
from app.routers.auth import get_current_user
from app.api_standards import raise_http_error, ErrorCode
from app.services import organization_service as org_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/business-card/organizations", tags=["组织-企业管理"])


# ── Pydantic 模型 ──────────────────────────────────────────────────────────────


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="组织名称")


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="组织名称")


class MemberAdd(BaseModel):
    user_id: int = Field(..., description="用户ID")
    role: str = Field("member", description="角色: admin/member")


class InviteCreate(BaseModel):
    email: str = Field(..., description="受邀邮箱")


# ── 辅助函数 ──────────────────────────────────────────────────────────────────


def success(data: any = None, message: str = "操作成功") -> dict:
    """统一成功响应"""
    return {"code": 0, "message": message, "data": data}


async def _get_org_or_404(db: AsyncSession, org_id: int) -> Organization:
    """获取组织，不存在则抛 404"""
    org = await db.run_sync(lambda s: org_service.get_organization(s, org_id))
    if org is None:
        raise_http_error(404, ErrorCode.NOT_FOUND, "组织不存在")
    return org


async def _require_org_owner(
    db: AsyncSession, org_id: int, current_user: User
) -> Organization:
    """验证当前用户是否为组织 owner，返回组织对象"""
    org = await _get_org_or_404(db, org_id)
    if org.owner_id != current_user.id:
        raise_http_error(403, ErrorCode.FORBIDDEN, "仅组织所有者可执行此操作")
    return org


async def _require_org_admin(
    db: AsyncSession, org_id: int, current_user: User
) -> OrganizationMember:
    """验证当前用户是否为组织管理员，返回成员记录"""
    # 先获取组织（确保存在）
    await _get_org_or_404(db, org_id)

    members = await db.run_sync(lambda s: org_service.get_org_members(s, org_id))
    for m in members:
        if m["user_id"] == current_user.id and m["role"] == "admin":
            return m
    raise_http_error(403, ErrorCode.FORBIDDEN, "仅组织管理员可执行此操作")


# ── API 端点 ────────────────────────────────────────────────────────────────────


@router.post("")
async def create_organization(
    data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建组织 — 创建者自动成为 admin"""
    org = await db.run_sync(
        lambda s: org_service.create_organization(s, owner_id=current_user.id, name=data.name)
    )

    logger.info("组织创建: id=%d, name=%s, owner=%d", org.id, org.name, current_user.id)

    return success(
        {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "owner_id": org.owner_id,
            "created_at": org.created_at.isoformat() if org.created_at else "",
        },
        message="组织创建成功",
    )


@router.get("")
async def list_my_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户所属的所有组织列表"""
    orgs = await db.run_sync(lambda s: org_service.get_user_orgs(s, current_user.id))

    # 格式化时间
    for org in orgs:
        created = org.get("created_at")
        org["created_at"] = created.isoformat() if created else ""

    return success(orgs)


@router.get("/{org_id}")
async def get_organization_detail(
    org_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取组织详情"""
    org = await _get_org_or_404(db, org_id)

    # 成员数统计
    members = await db.run_sync(lambda s: org_service.get_org_members(s, org_id))

    return success({
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "owner_id": org.owner_id,
        "member_count": len(members),
        "created_at": org.created_at.isoformat() if org.created_at else "",
    })


@router.put("/{org_id}")
async def update_organization(
    org_id: int,
    data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新组织信息（仅 owner 可操作）"""
    await _require_org_owner(db, org_id, current_user)

    org = await db.run_sync(
        lambda s: org_service.update_organization(s, org_id, name=data.name)
    )
    if org is None:
        raise_http_error(404, ErrorCode.NOT_FOUND, "组织不存在")

    logger.info("组织更新: id=%d, name=%s", org_id, data.name)

    return success(
        {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "owner_id": org.owner_id,
        },
        message="组织信息已更新",
    )


@router.delete("/{org_id}")
async def delete_organization(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除组织（仅 owner 可操作）"""
    await _require_org_owner(db, org_id, current_user)

    deleted = await db.run_sync(lambda s: org_service.delete_organization(s, org_id))
    if not deleted:
        raise_http_error(404, ErrorCode.NOT_FOUND, "组织不存在")

    logger.info("组织删除: id=%d, user=%d", org_id, current_user.id)

    return success(message="组织已删除")


@router.post("/{org_id}/members")
async def add_organization_member(
    org_id: int,
    data: MemberAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """添加成员到组织（仅管理员可操作）"""
    await _require_org_admin(db, org_id, current_user)

    member = await db.run_sync(
        lambda s: org_service.add_member(s, org_id=org_id, user_id=data.user_id, role=data.role)
    )

    logger.info("成员添加: org_id=%d, user_id=%d, role=%s", org_id, data.user_id, data.role)

    return success(
        {
            "id": member.id,
            "org_id": member.org_id,
            "user_id": member.user_id,
            "role": member.role,
            "joined_at": member.joined_at.isoformat() if member.joined_at else "",
        },
        message="成员添加成功",
    )


@router.get("/{org_id}/members")
async def list_organization_members(
    org_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取组织成员列表"""
    await _get_org_or_404(db, org_id)

    members = await db.run_sync(lambda s: org_service.get_org_members(s, org_id))

    # 格式化时间
    for m in members:
        joined = m.get("joined_at")
        m["joined_at"] = joined.isoformat() if joined else ""

    return success(members)


@router.delete("/{org_id}/members/{user_id}")
async def remove_organization_member(
    org_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """从组织移除成员（仅管理员可操作）"""
    await _require_org_admin(db, org_id, current_user)

    try:
        removed = await db.run_sync(lambda s: org_service.remove_member(s, org_id, user_id))
    except ValueError as e:
        raise_http_error(400, ErrorCode.RESOURCE_CONFLICT, str(e))

    if not removed:
        raise_http_error(404, ErrorCode.NOT_FOUND, "成员不存在于该组织")

    logger.info("成员移除: org_id=%d, user_id=%d", org_id, user_id)

    return success(message="成员已移除")


@router.post("/{org_id}/invites")
async def create_organization_invite(
    org_id: int,
    data: InviteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建组织邀请（仅管理员可操作）"""
    await _require_org_admin(db, org_id, current_user)

    invite = await db.run_sync(
        lambda s: org_service.create_invite(s, org_id=org_id, email=data.email)
    )

    logger.info("邀请创建: org_id=%d, email=%s", org_id, data.email)

    return success(
        {
            "id": invite.id,
            "org_id": invite.org_id,
            "email": invite.email,
            "token": invite.token,
            "status": invite.status,
            "created_at": invite.created_at.isoformat() if invite.created_at else "",
        },
        message="邀请已创建",
    )


@router.get("/{org_id}/invites")
async def list_organization_invites(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取组织邀请列表（仅管理员可操作）"""
    await _require_org_admin(db, org_id, current_user)

    invites = await db.run_sync(lambda s: org_service.get_org_invites(s, org_id))

    result = []
    for inv in invites:
        result.append({
            "id": inv.id,
            "org_id": inv.org_id,
            "email": inv.email,
            "token": inv.token,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else "",
        })

    return success(result)


@router.post("/invites/{token}/accept")
async def accept_organization_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """接受组织邀请"""
    try:
        result = await db.run_sync(
            lambda s: org_service.accept_invite(s, token=token, user_id=current_user.id)
        )
    except ValueError as e:
        raise_http_error(400, ErrorCode.RESOURCE_CONFLICT, str(e))

    logger.info("邀请已接受: token=%s, user_id=%d, org_id=%d", token[:8], current_user.id, result["org_id"])

    return success(result, message="已加入组织")
