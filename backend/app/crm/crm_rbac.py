"""CRM 角色权限系统 (RBAC).

本模块为 CRM 提供四种角色和细粒度权限控制。
角色: admin(管理员) | manager(经理) | sales(销售员) | viewer(只读)

权限矩阵:
| 操作               | admin | manager | sales | viewer |
|-------------------|-------|---------|-------|--------|
| contacts.view     | ✅    | ✅      | ✅    | ✅     |
| contacts.create   | ✅    | ✅      | ✅    | ❌     |
| contacts.edit     | ✅    | ✅      | ✅    | ❌     |
| contacts.delete   | ✅    | ✅      | ❌    | ❌     |
| pipeline.view     | ✅    | ✅      | ✅    | ✅     |
| pipeline.move     | ✅    | ✅      | ✅    | ❌     |
| reports.view      | ✅    | ✅      | ✅    | ✅     |
| workflow.manage   | ✅    | ❌      | ❌    | ❌     |
| permissions.manage| ✅    | ❌      | ❌    | ❌     |

使用方式:
    from app.crm.crm_rbac import require_permission

    @router.get("/contacts")
    async def list_contacts(
        ...,
        _: None = Depends(require_permission("contacts.view")),
    ):
        ...
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CRM 角色常量
# ═══════════════════════════════════════════════════════════════════════════════


class CrmRole(str, Enum):
    """CRM 预定义角色。"""

    ADMIN = "admin"
    MANAGER = "manager"
    SALES = "sales"
    VIEWER = "viewer"


CRM_ROLE_DISPLAY = {
    CrmRole.ADMIN: "管理员",
    CrmRole.MANAGER: "经理",
    CrmRole.SALES: "销售员",
    CrmRole.VIEWER: "只读用户",
}


# ═══════════════════════════════════════════════════════════════════════════════
# CRM 权限定义
# ═══════════════════════════════════════════════════════════════════════════════


# 联系人
CONTACTS_VIEW = "contacts.view"
CONTACTS_CREATE = "contacts.create"
CONTACTS_EDIT = "contacts.edit"
CONTACTS_DELETE = "contacts.delete"

# Pipeline / 销售管道
PIPELINE_VIEW = "pipeline.view"
PIPELINE_MOVE = "pipeline.move"

# 报表
REPORTS_VIEW = "reports.view"

# 系统管理
WORKFLOW_MANAGE = "workflow.manage"
PERMISSIONS_MANAGE = "permissions.manage"


# ═══════════════════════════════════════════════════════════════════════════════
# 权限矩阵
# ═══════════════════════════════════════════════════════════════════════════════

CRM_PERMISSION_MATRIX: dict[CrmRole, set[str]] = {
    CrmRole.ADMIN: {
        CONTACTS_VIEW,
        CONTACTS_CREATE,
        CONTACTS_EDIT,
        CONTACTS_DELETE,
        PIPELINE_VIEW,
        PIPELINE_MOVE,
        REPORTS_VIEW,
        WORKFLOW_MANAGE,
        PERMISSIONS_MANAGE,
    },
    CrmRole.MANAGER: {
        CONTACTS_VIEW,
        CONTACTS_CREATE,
        CONTACTS_EDIT,
        CONTACTS_DELETE,
        PIPELINE_VIEW,
        PIPELINE_MOVE,
        REPORTS_VIEW,
    },
    CrmRole.SALES: {
        CONTACTS_VIEW,
        CONTACTS_CREATE,
        CONTACTS_EDIT,
        PIPELINE_VIEW,
        PIPELINE_MOVE,
        REPORTS_VIEW,
    },
    CrmRole.VIEWER: {
        CONTACTS_VIEW,
        PIPELINE_VIEW,
        REPORTS_VIEW,
    },
}

# 所有有效的 CRM 权限(用于校验)
ALL_CRM_PERMISSIONS: set[str] = {
    CONTACTS_VIEW,
    CONTACTS_CREATE,
    CONTACTS_EDIT,
    CONTACTS_DELETE,
    PIPELINE_VIEW,
    PIPELINE_MOVE,
    REPORTS_VIEW,
    WORKFLOW_MANAGE,
    PERMISSIONS_MANAGE,
}

# 权限中文描述
CRM_PERMISSION_LABELS: dict[str, str] = {
    CONTACTS_VIEW: "查看联系人",
    CONTACTS_CREATE: "创建联系人",
    CONTACTS_EDIT: "编辑联系人",
    CONTACTS_DELETE: "删除联系人",
    PIPELINE_VIEW: "查看Pipeline",
    PIPELINE_MOVE: "移动阶段",
    REPORTS_VIEW: "查看报表",
    WORKFLOW_MANAGE: "管理工作流",
    PERMISSIONS_MANAGE: "管理权限",
}


# ═══════════════════════════════════════════════════════════════════════════════
# 权限获取与检查
# ═══════════════════════════════════════════════════════════════════════════════


def get_crm_permissions_for_role(role: str) -> set[str]:
    """根据 CRM 角色名返回对应的权限集合。"""
    try:
        role_enum = CrmRole(role)
        return set(CRM_PERMISSION_MATRIX.get(role_enum, set()))
    except ValueError:
        return set()


async def get_user_crm_role(db: AsyncSession, user_id: int) -> str:
    """获取用户的 CRM 角色名。

    查找顺序:
      1. rbac_user_roles 表中以 'crm_' 开头的角色
      2. User.role 字段 (admin → admin, 其他 → viewer)
    如果都没有找到，返回 'viewer'。
    """
    # 尝试从 rbac_user_roles 获取 CRM 角色
    from app.models.rbac import RoleDefinition, UserRole

    result = await db.execute(
        sa_select(RoleDefinition)
        .join(UserRole, UserRole.role_id == RoleDefinition.id)
        .where(UserRole.user_id == user_id)
    )
    roles = result.scalars().all()

    if roles:
        for role in roles:
            if role.name in ("admin", "manager", "sales", "viewer"):
                return role.name
        # 取第一个非 CRM 角色名作为 fallback
        return roles[0].name

    # 回退到 User.role 字段
    result = await db.execute(sa_select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user:
        # CRM 角色映射: user → viewer
        if user.role == "admin":
            return "admin"
        return "viewer"

    return "viewer"


async def has_crm_permission(
    db: AsyncSession, user_id: int, required_permission: str
) -> bool:
    """检查用户是否拥有指定的 CRM 权限。"""
    role = await get_user_crm_role(db, user_id)
    permissions = get_crm_permissions_for_role(role)
    return required_permission in permissions


async def get_user_crm_permissions(
    db: AsyncSession, user_id: int
) -> dict[str, Any]:
    """获取用户的 CRM 角色及所有权限。"""
    role = await get_user_crm_role(db, user_id)
    permissions = get_crm_permissions_for_role(role)
    return {
        "user_id": user_id,
        "role": role,
        "role_display": CRM_ROLE_DISPLAY.get(CrmRole(role), role) if role in CrmRole._value2member_ else role,
        "permissions": sorted(permissions),
        "permission_labels": [
            {"key": p, "label": CRM_PERMISSION_LABELS.get(p, p)}
            for p in sorted(permissions)
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FastAPI 依赖注入: require_permission
# ═══════════════════════════════════════════════════════════════════════════════


def require_permission(permission: str):
    """FastAPI 依赖项工厂 — 要求当前用户拥有指定 CRM 权限。

    用法:
        @router.get("/contacts")
        async def list_contacts(
            svc = Depends(...),
            _: None = Depends(require_permission("contacts.view")),
        ):
            ...

    无权限时抛出 403 Forbidden。
    """
    from fastapi.security import OAuth2PasswordBearer
    _oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    async def _check(
        token: str = Depends(_oauth2_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        # 延迟导入以避免循环导入: crm_rbac ↔ routers.__init__ → crm_router
        from app.routers.auth import get_current_user
        current_user = await get_current_user(token=token, db=db)
        if not await has_crm_permission(db, current_user.id, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权限: 需要「{CRM_PERMISSION_LABELS.get(permission, permission)}」权限",
            )

    return _check


# ═══════════════════════════════════════════════════════════════════════════════
# 角色分配辅助函数
# ═══════════════════════════════════════════════════════════════════════════════


async def ensure_crm_role_definition(db: AsyncSession) -> dict[str, int]:
    """确保 CRM 角色定义存在于 rbac_roles 表中。

    返回 {角色名: 角色ID} 映射。
    """
    from app.models.rbac import RoleDefinition, RolePermission

    role_ids: dict[str, int] = {}

    for role_enum in CrmRole:
        name = role_enum.value
        # 查找或创建角色
        result = await db.execute(
            sa_select(RoleDefinition).where(RoleDefinition.name == name)
        )
        role_def = result.scalar_one_or_none()

        if not role_def:
            role_def = RoleDefinition(
                name=name,
                display_name=CRM_ROLE_DISPLAY.get(role_enum, name),
                description=f"CRM {CRM_ROLE_DISPLAY.get(role_enum, name)}",
                is_system=True,
            )
            db.add(role_def)
            await db.flush()

        role_ids[name] = role_def.id

        # 同步权限到 rbac_role_permissions 表
        expected_perms = CRM_PERMISSION_MATRIX.get(role_enum, set())
        # 删除多余权限
        await db.execute(
            RolePermission.__table__.delete().where(
                RolePermission.role_id == role_def.id,
                RolePermission.permission_key.notin_(expected_perms),
            )
        )
        # 添加缺失的权限
        for perm in expected_perms:
            existing = await db.execute(
                sa_select(RolePermission).where(
                    RolePermission.role_id == role_def.id,
                    RolePermission.permission_key == perm,
                )
            )
            if not existing.scalar_one_or_none():
                rp = RolePermission(role_id=role_def.id, permission_key=perm)
                db.add(rp)

    await db.commit()
    return role_ids


async def assign_crm_role(
    db: AsyncSession,
    target_user_id: int,
    role_name: str,
    granted_by: int | None = None,
) -> bool:
    """为用户分配 CRM 角色。

    先确保角色定义存在，然后删除该用户的旧 CRM 角色，再分配新角色。
    返回 True 表示成功。
    """
    from app.models.rbac import UserRole

    # 校验角色名
    if role_name not in CrmRole._value2member_:
        raise ValueError(f"无效的 CRM 角色: {role_name}，可选: {list(CrmRole._value2member_.keys())}")

    # 确保角色定义存在
    role_ids = await ensure_crm_role_definition(db)
    role_id = role_ids[role_name]

    # 删除该用户已有的所有 CRM 角色
    crm_role_ids = list(role_ids.values())
    await db.execute(
        UserRole.__table__.delete().where(
            UserRole.user_id == target_user_id,
            UserRole.role_id.in_(crm_role_ids),
        )
    )

    # 分配新角色
    ur = UserRole(user_id=target_user_id, role_id=role_id, granted_by=granted_by)
    db.add(ur)
    await db.commit()
    logger.info(
        "为用户 %s 分配 CRM 角色 %s (授权人: %s)",
        target_user_id, role_name, granted_by,
    )
    return True
