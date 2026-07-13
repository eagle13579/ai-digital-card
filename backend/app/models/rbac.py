"""
RBAC 角色权限模型

定义角色等级 (admin/editor/viewer) 及其对应的资源权限矩阵。
使用 SQLAlchemy ORM 模型存储角色和权限映射，支持细粒度资源级授权。
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import select as sa_select

from app.database import Base


# ── 权限常量定义 ──────────────────────────────────────────────────────────────

class Role(str, Enum):
    """预定义角色"""
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class Permission(str, Enum):
    """预定义权限标识"""
    # 名片管理
    BROC_READ = "brochure:read"
    BROC_CREATE = "brochure:create"
    BROC_UPDATE = "brochure:update"
    BROC_DELETE = "brochure:delete"
    BROC_PUBLISH = "brochure:publish"

    # 用户管理
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # 团队管理
    TEAM_READ = "team:read"
    TEAM_CREATE = "team:create"
    TEAM_UPDATE = "team:update"
    TEAM_DELETE = "team:delete"
    TEAM_INVITE = "team:invite"

    # SSO 管理
    SSO_CONFIGURE = "sso:configure"
    SSO_READ = "sso:read"

    # 系统管理
    SYS_SETTINGS = "system:settings"
    SYS_LOGS = "system:logs"
    SYS_METRICS = "system:metrics"

    # AI 能力
    AI_ASSIST = "ai:assist"
    AI_ANALYZE = "ai:analyze"
    AI_GENERATE = "ai:generate"

    # 导出
    EXPORT_READ = "export:read"
    EXPORT_CREATE = "export:create"


# ── 权限矩阵（硬编码默认值） ──────────────────────────────────────────────────

PERMISSION_MATRIX: dict[Role, set[Permission]] = {
    Role.ADMIN: {
        # Admin: 所有权限
        Permission.BROC_READ, Permission.BROC_CREATE,
        Permission.BROC_UPDATE, Permission.BROC_DELETE,
        Permission.BROC_PUBLISH,
        Permission.USER_READ, Permission.USER_CREATE,
        Permission.USER_UPDATE, Permission.USER_DELETE,
        Permission.TEAM_READ, Permission.TEAM_CREATE,
        Permission.TEAM_UPDATE, Permission.TEAM_DELETE,
        Permission.TEAM_INVITE,
        Permission.SSO_CONFIGURE, Permission.SSO_READ,
        Permission.SYS_SETTINGS, Permission.SYS_LOGS,
        Permission.SYS_METRICS,
        Permission.AI_ASSIST, Permission.AI_ANALYZE,
        Permission.AI_GENERATE,
        Permission.EXPORT_READ, Permission.EXPORT_CREATE,
    },
    Role.EDITOR: {
        # Editor: 读写权限，部分管理权限
        Permission.BROC_READ, Permission.BROC_CREATE,
        Permission.BROC_UPDATE,
        # 不能删除或发布
        Permission.USER_READ,
        Permission.TEAM_READ,
        Permission.SSO_READ,
        Permission.AI_ASSIST, Permission.AI_ANALYZE,
        Permission.AI_GENERATE,
        Permission.EXPORT_READ, Permission.EXPORT_CREATE,
    },
    Role.VIEWER: {
        # Viewer: 只读权限
        Permission.BROC_READ,
        Permission.USER_READ,
        Permission.TEAM_READ,
        Permission.SSO_READ,
        Permission.AI_ASSIST,
        Permission.EXPORT_READ,
    },
}


def get_permissions_for_role(role: str) -> set[str]:
    """根据角色名称获取对应的权限集合"""
    try:
        role_enum = Role(role)
        return {p.value for p in PERMISSION_MATRIX.get(role_enum, set())}
    except ValueError:
        return set()


def check_permission(role: str, required_permission: str) -> bool:
    """检查角色是否拥有指定权限"""
    permitted = get_permissions_for_role(role)
    return required_permission in permitted


# ── ORM 模型 ──────────────────────────────────────────────────────────────────

class RoleDefinition(Base):
    """
    角色定义表（可扩展，支持自定义角色）

    预置 admin / editor / viewer 三条记录。
    """
    __tablename__ = "rbac_roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, comment="角色标识")
    display_name: Mapped[str] = mapped_column(String(64), default="", comment="角色显示名")
    description: Mapped[str] = mapped_column(Text, default="", comment="角色描述")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, comment="系统预置角色（不可删除）")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )


class RolePermission(Base):
    """
    角色-权限关联表

    每个角色可关联多个权限标识。
    """
    __tablename__ = "rbac_role_permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rbac_roles.id", ondelete="CASCADE"), nullable=False
    )
    permission_key: Mapped[str] = mapped_column(String(64), nullable=False, comment="权限标识")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    role: Mapped["RoleDefinition"] = relationship(back_populates="permissions")

    __table_args__ = (
        UniqueConstraint("role_id", "permission_key", name="uq_role_permission"),
    )


class UserRole(Base):
    """
    用户-角色关联表

    支持一个用户拥有多个角色（权限取并集）。
    """
    __tablename__ = "rbac_user_roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="用户 ID")
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rbac_roles.id", ondelete="CASCADE"), nullable=False
    )
    granted_by: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="授权人用户 ID"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

async def get_user_permissions(db: AsyncSession, user_id: int) -> set[str]:
    """
    获取指定用户的所有权限（合并其所有角色的权限）。

    先从数据库读取角色-权限关联，如果没有找到则回退到默认权限矩阵。
    """
    # 查询用户关联的角色
    result = await db.execute(
        sa_select(RoleDefinition)
        .join(UserRole, UserRole.role_id == RoleDefinition.id)
        .where(UserRole.user_id == user_id)
    )
    roles = result.scalars().all()

    if not roles:
        # Fallback: 从 User 表的 role 字段读取
        from app.models.user import User
        user_result = await db.execute(sa_select(User).where(User.id == user_id))
        user = user_result.scalars().first()
        if user:
            return get_permissions_for_role(user.role)
        return set()

    permissions = set()
    for role in roles:
        for rp in role.permissions:
            permissions.add(rp.permission_key)

    # 如果数据库中没有明确的权限配置，回退到默认矩阵
    if not permissions:
        for role in roles:
            permissions.update(get_permissions_for_role(role.name))

    return permissions


async def has_permission(
    db: AsyncSession, user_id: int, required_permission: str
) -> bool:
    """检查用户是否拥有指定权限"""
    permissions = await get_user_permissions(db, user_id)
    return required_permission in permissions
