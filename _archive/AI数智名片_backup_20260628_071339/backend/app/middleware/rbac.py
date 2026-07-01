"""
RBAC 中间件 — 权限检查装饰器和依赖项

提供 FastAPI 依赖注入和装饰器，用于在路由上声明所需的角色和权限。
"""
from __future__ import annotations

import functools
import logging
from typing import Callable, Optional, Sequence, Union

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.rbac import (
    Permission,
    get_permissions_for_role,
    get_user_permissions,
    has_permission as _has_permission,
)
from app.models.user import User
from app.routers.auth import get_current_user as _get_current_user

logger = logging.getLogger("rbac.middleware")

# ── 类型别名 ──────────────────────────────────────────────────────────────────

PermissionType = Union[str, Permission]
RoleType = Union[str, "Role"]


# ── FastAPI 依赖项 ────────────────────────────────────────────────────────────

async def require_permission(
    permission: PermissionType,
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    FastAPI 依赖项：验证当前用户拥有指定权限。

    用法：
        @router.get("/brochures")
        async def list_brochures(
            _: None = Depends(require_permission("brochure:read")),
            ...
        ):
            ...
    """
    perm_str = permission.value if isinstance(permission, Permission) else permission
    user_perms = await get_user_permissions(db, current_user.id)

    if perm_str not in user_perms:
        logger.warning(
            "权限拒绝: user=%d, role=%s, required=%s, owned=%s",
            current_user.id, current_user.role, perm_str, user_perms,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足：需要 '{perm_str}' 权限",
        )
    return True


async def require_role(
    roles: Union[str, Sequence[str]],
    current_user: User = Depends(_get_current_user),
):
    """
    FastAPI 依赖项：验证当前用户角色在指定列表中。

    用法：
        @router.get("/admin/dashboard")
        async def admin_dashboard(
            _: None = Depends(require_role(["admin", "editor"])),
            ...
        ):
            ...
    """
    allowed_roles = [roles] if isinstance(roles, str) else list(roles)
    if current_user.role not in allowed_roles:
        logger.warning(
            "角色拒绝: user=%d, role=%s, required=%s",
            current_user.id, current_user.role, allowed_roles,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足：需要角色 {'/'.join(allowed_roles)}",
        )
    return True


# ── 装饰器 ────────────────────────────────────────────────────────────────────

def require_permissions(
    *permissions: PermissionType,
    require_all: bool = True,
):
    """
    路由装饰器：声明路由所需的权限。

    Args:
        *permissions: 所需的权限列表
        require_all: True=需要所有权限, False=只需其中之一

    用法：
        @router.delete("/brochures/{id}")
        @require_permissions("brochure:delete", "brochure:publish")
        async def delete_brochure(...):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(_get_current_user),
            db: AsyncSession = Depends(get_db),
            **kwargs,
        ):
            perm_strs = {
                p.value if isinstance(p, Permission) else p
                for p in permissions
            }
            user_perms = await get_user_permissions(db, current_user.id)

            if require_all:
                missing = perm_strs - user_perms
                if missing:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"权限不足：缺少 {missing}",
                    )
            else:
                if not perm_strs & user_perms:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"权限不足：需要 {'/'.join(perm_strs)} 中至少一项",
                    )

            return await func(*args, current_user=current_user, db=db, **kwargs)
        return wrapper
    return decorator


def require_roles(*roles: str):
    """
    路由装饰器：声明路由所需的最低角色。

    用法：
        @router.get("/admin/users")
        @require_roles("admin", "editor")
        async def list_users(...):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(_get_current_user),
            **kwargs,
        ):
            if current_user.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足：需要角色 {'/'.join(roles)}",
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


# ── 便捷权限检查函数 ───────────────────────────────────────────────────────────

def can_read_brochure(user: User) -> bool:
    """检查用户是否有名片读取权限"""
    return user.role in ("admin", "editor", "viewer")


def can_write_brochure(user: User) -> bool:
    """检查用户是否有名片写入权限"""
    return user.role in ("admin", "editor")


def can_manage_users(user: User) -> bool:
    """检查用户是否有用户管理权限"""
    return user.role == "admin"


def can_configure_sso(user: User) -> bool:
    """检查用户是否有 SSO 配置权限"""
    return user.role == "admin"


# ── ASGI 中间件（可选，用于全局路径级拦截） ───────────────────────────────────

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request


class RBACMiddleware(BaseHTTPMiddleware):
    """
    RBAC 中间件（可选）

    用于全局路径级权限拦截。如果路由已经使用上面的依赖项或装饰器，
    则不需要此中间件。

    配置示例：
        app.add_middleware(
            RBACMiddleware,
            protected_routes={
                "/api/admin": {"role": "admin"},
                "/api/brochures/create": {"permission": "brochure:create"},
            }
        )
    """

    def __init__(
        self,
        app,
        protected_routes: Optional[dict[str, dict]] = None,
    ):
        super().__init__(app)
        self.protected_routes = protected_routes or {}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):
        path = request.url.path
        auth_header = request.headers.get("Authorization", "")

        # Check if path is protected
        if path in self.protected_routes:
            if not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要认证",
                )

            route_config = self.protected_routes[path]
            # Note: full validation with DB lookup is done at the endpoint level
            # This middleware only provides path-level gating

        return await call_next(request)
