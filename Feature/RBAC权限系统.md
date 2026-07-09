---
id: feature-rbac
name: RBAC三层权限系统
version: 1.0.0
created: 2026-07-09
status: stable
dependencies: []
source: code/api/services/rbac_service.py
---

## 一句话定位
admin/manager/viewer三层角色+permission路由守卫

## 能力
- 3个系统角色: admin(*)/manager(读写)/viewer(只读)
- 可扩展自定义角色+权限列表
- FastAPI依赖注入: require_permission("dealers:read")
- 用户-角色-租户三层绑定
- 管理API: 列出角色、分配角色、查询用户角色

## 适用产品
所有多租户B2B SaaS产品

## 使用方式
```python
from api.services.rbac_service import require_permission, assign_role

@router.get("/dealers")
async def list_dealers(payload = Depends(require_permission("dealers:read"))):
    return dealers_list()
```

## 部署要求
- roles + user_roles 两张表
- 启动时初始化3个默认角色
