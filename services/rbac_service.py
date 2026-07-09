"""
芯森态·RBAC权限服务
角色管理 + 权限验证 + API路由守卫
使用: from api.services.rbac_service import require_permission, get_user_roles
"""
import json, logging, sqlite3, os
from functools import wraps
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                  "api", "data", "xinsentai.db")

def _get_db():
    return sqlite3.connect(DB)

def get_user_roles(user_id: int, tenant_id: str = None) -> list:
    """获取用户的角色列表"""
    c = _get_db()
    try:
        rows = c.execute("""
            SELECT r.name, r.permissions, r.description
            FROM user_roles ur JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = ? AND (ur.tenant_id = ? OR ur.tenant_id IS NULL)
        """, (user_id, tenant_id or "")).fetchall()
        return [{"name": r[0], "permissions": json.loads(r[1]), "description": r[2]} for r in rows]
    finally:
        c.close()

def get_user_permissions(user_id: int, tenant_id: str = None) -> list:
    """获取用户的所有权限（去重合并）"""
    perms = set()
    for role in get_user_roles(user_id, tenant_id):
        for p in role["permissions"]:
            perms.add(p)
    return list(perms)

def has_permission(user_id: int, required: str, tenant_id: str = None) -> bool:
    """检查用户是否有指定权限（* = 超级管理员）"""
    perms = get_user_permissions(user_id, tenant_id)
    if "*" in perms:
        return True
    return required in perms

async def require_permission(permission: str):
    """FastAPI依赖注入：路由守卫"""
    async def _check(request: Request):
        # 从JWT中提取用户
        from api.routers.auth import _extract_token, _decode_jwt
        token = _extract_token(request)
        if not token:
            raise HTTPException(401, "未提供认证令牌")
        payload = _decode_jwt(token)
        if not payload:
            raise HTTPException(401, "令牌无效或已过期")
        
        user_id = payload.get("user_id")
        tenant_id = payload.get("tenant_id")
        
        if not has_permission(user_id, permission, tenant_id):
            raise HTTPException(403, f"权限不足：需要 {permission}")
        
        return payload
    return _check

def assign_role(user_id: int, role_name: str, tenant_id: str = None) -> bool:
    """为用户分配角色"""
    c = _get_db()
    try:
        role = c.execute("SELECT id FROM roles WHERE name=?", (role_name,)).fetchone()
        if not role:
            logger.error(f"角色不存在: {role_name}")
            return False
        c.execute(
            "INSERT OR IGNORE INTO user_roles (user_id, role_id, tenant_id) VALUES (?, ?, ?)",
            (user_id, role[0], tenant_id)
        )
        c.commit()
        logger.info(f"为用户 {user_id} 分配角色 {role_name}")
        return True
    finally:
        c.close()

# Admin API endpoints
def list_roles() -> list:
    c = _get_db()
    try:
        rows = c.execute("SELECT id, name, description, permissions, is_system FROM roles ORDER BY id").fetchall()
        return [{"id": r[0], "name": r[1], "description": r[2],
                 "permissions": json.loads(r[3]), "is_system": bool(r[4])} for r in rows]
    finally:
        c.close()

def list_user_roles(tenant_id: str = None) -> list:
    c = _get_db()
    try:
        rows = c.execute("""
            SELECT ur.id, ur.user_id, a.email, a.company_name, r.name as role_name
            FROM user_roles ur
            JOIN auth_accounts a ON ur.user_id = a.id
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.tenant_id = ? OR ur.tenant_id IS NULL
            ORDER BY a.email
        """, (tenant_id or "",)).fetchall()
        return [{"id": r[0], "user_id": r[1], "email": r[2],
                 "company": r[3], "role": r[4]} for r in rows]
    finally:
        c.close()
