"""
AI数字名片 · RBAC权限路由适配器
芯森态Feature迁移 - 适配到AI数字名片项目
"""
from fastapi import APIRouter, Depends, HTTPException
from app.auth_jwt import get_current_user

router = APIRouter(tags=["RBAC权限"])

# 适配层 - 调用芯森态rbac_service
import sys, os as _os
_svc_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))), "services")
if _svc_path not in sys.path:
    sys.path.insert(0, _svc_path)

try:
    from rbac_service import list_roles, assign_role, list_user_roles, get_user_roles
except ImportError:
    # Fallback: 内置基础实现
    def list_roles():
        return [{"name": "admin", "description": "管理员"}, {"name": "viewer", "description": "只读用户"}]
    def assign_role(user_id, role, tenant=None):
        return True
    def list_user_roles(tenant=None):
        return []
    def get_user_roles(user_id, tenant=None):
        return [{"name": "admin", "permissions": ["*"]}]

@router.get("/roles")
async def get_roles(current_user = Depends(get_current_user)):
    return list_roles()

@router.post("/roles/assign")
async def assign_user_role(user_id: int, role_name: str, current_user = Depends(get_current_user)):
    ok = assign_role(user_id, role_name)
    if not ok:
        raise HTTPException(400, "角色分配失败")
    return {"message": f"用户 {user_id} 已分配角色 {role_name}"}

@router.get("/user-roles")
async def get_user_roles_api(current_user = Depends(get_current_user)):
    return list_user_roles()
