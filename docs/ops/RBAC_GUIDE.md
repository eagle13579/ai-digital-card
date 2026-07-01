# CRM 角色权限系统 (RBAC) 管理指南

## 概述

CRM 模块内置了基于角色的权限控制系统 (RBAC)，支持 4 种预定义角色和 9 种细粒度权限。

### 角色定义

| 角色 | 标识 | 说明 |
|------|------|------|
| 管理员 | `admin` | 全部权限，包括管理工作流、管理权限 |
| 经理 | `manager` | 联系人增删改查 + Pipeline 操作 + 报表查看 |
| 销售员 | `sales` | 联系人增改查（不可删除）+ Pipeline 查看/移动 + 报表查看 |
| 只读 | `viewer` | 仅可查看联系人和报表 |

### 权限矩阵

| 操作 | 权限标识 | admin | manager | sales | viewer |
|------|---------|-------|---------|-------|--------|
| 查看联系人 | `contacts.view` | ✅ | ✅ | ✅ | ✅ |
| 创建联系人 | `contacts.create` | ✅ | ✅ | ✅ | ❌ |
| 编辑联系人 | `contacts.edit` | ✅ | ✅ | ✅ | ❌ |
| 删除联系人 | `contacts.delete` | ✅ | ✅ | ❌ | ❌ |
| 查看 Pipeline | `pipeline.view` | ✅ | ✅ | ✅ | ✅ |
| 移动阶段 | `pipeline.move` | ✅ | ✅ | ✅ | ❌ |
| 查看报表 | `reports.view` | ✅ | ✅ | ✅ | ✅ |
| 管理工作流 | `workflow.manage` | ✅ | ❌ | ❌ | ❌ |
| 管理权限 | `permissions.manage` | ✅ | ❌ | ❌ | ❌ |

## API 端点

所有 RBAC 管理端点均以 `/api/crm/rbac/` 为前缀，需要 `permissions.manage` 权限（仅 admin）。

### 1. 获取所有角色及权限

```
GET /api/crm/rbac/roles
```

**权限要求:** `permissions.manage` (仅 admin)

**响应示例:**
```json
[
  {
    "name": "admin",
    "display_name": "管理员",
    "description": "CRM 管理员",
    "permissions": [
      {"key": "contacts.create", "label": "创建联系人"},
      {"key": "contacts.delete", "label": "删除联系人"},
      {"key": "contacts.edit", "label": "编辑联系人"},
      {"key": "contacts.view", "label": "查看联系人"},
      {"key": "permissions.manage", "label": "管理权限"},
      {"key": "pipeline.move", "label": "移动阶段"},
      {"key": "pipeline.view", "label": "查看Pipeline"},
      {"key": "reports.view", "label": "查看报表"},
      {"key": "workflow.manage", "label": "管理工作流"}
    ]
  },
  ...
]
```

### 2. 创建/同步角色到数据库

```
POST /api/crm/rbac/roles
```

**权限要求:** `permissions.manage` (仅 admin)

**请求体:**
```json
{
  "name": "manager"
}
```

**说明:** 将角色的权限定义同步到 `rbac_roles` 和 `rbac_role_permissions` 表中。内置角色已自动注册，一般无需手动调用。

### 3. 分配角色给用户

```
POST /api/crm/rbac/assign
```

**权限要求:** `permissions.manage` (仅 admin)

**请求体:**
```json
{
  "user_id": 42,
  "role": "sales"
}
```

**响应示例:**
```json
{
  "message": "用户 42 已分配角色「销售员」",
  "user_id": 42,
  "role": "sales",
  "role_display": "销售员",
  "permissions": ["contacts.create", "contacts.edit", ...],
  "permission_labels": [
    {"key": "contacts.create", "label": "创建联系人"},
    ...
  ]
}
```

### 4. 查询当前用户权限

```
GET /api/crm/rbac/my-permissions
```

**权限要求:** 无（任何已认证用户均可查询自身权限）

**响应示例:**
```json
{
  "user_id": 42,
  "role": "sales",
  "role_display": "销售员",
  "permissions": ["contacts.create", "contacts.edit", "contacts.view", ...],
  "permission_labels": [
    {"key": "contacts.create", "label": "创建联系人"},
    ...
  ]
}
```

## 权限检查机制

权限检查通过 FastAPI 依赖注入实现。

### 如何在代码中使用

```python
from app.crm.crm_rbac import require_permission

@router.get("/contacts")
async def list_contacts(
    svc: CrmService = Depends(...),
    _: None = Depends(require_permission("contacts.view")),
):
    ...
```

当用户缺乏所需权限时，API 返回 `403 Forbidden`，错误信息包含中文描述。

### 现有端点权限映射

| 端点 | 所需权限 |
|------|---------|
| `POST /api/crm/contacts` | `contacts.create` |
| `GET /api/crm/contacts` | `contacts.view` |
| `GET /api/crm/contacts/{id}` | `contacts.view` |
| `PUT /api/crm/contacts/{id}` | `contacts.edit` |
| `DELETE /api/crm/contacts/{id}` | `contacts.delete` |
| `POST /api/crm/activities` | `contacts.edit` |
| `GET /api/crm/contacts/{id}/timeline` | `contacts.view` |
| `POST /api/crm/notes` | `contacts.edit` |
| `GET /api/crm/contacts/{id}/notes` | `contacts.view` |
| `PUT /api/crm/notes/{id}` | `contacts.edit` |
| `DELETE /api/crm/notes/{id}` | `contacts.delete` |
| `GET /api/crm/pipeline/stages` | `pipeline.view` |
| `GET /api/crm/pipeline/deals` | `pipeline.view` |
| `POST /api/crm/deals` | `contacts.edit` |
| `PUT /api/crm/deals/{id}/stage` | `pipeline.move` |
| `GET /api/crm/analytics/*` | `reports.view` |
| `GET /api/crm/stats` | `reports.view` |
| `GET /api/crm/export/csv` | `contacts.view` |
| `POST /api/crm/import/csv` | `contacts.create` |
| `POST /api/crm/auto/*` | `contacts.create` |
| `POST /api/crm/workflow/rules` | `workflow.manage` |
| `GET /api/crm/workflow/rules` | `workflow.manage` |
| `PUT /api/crm/workflow/rules/*` | `workflow.manage` |
| `DELETE /api/crm/workflow/rules/*` | `workflow.manage` |
| `POST /api/crm/rbac/*` | `permissions.manage` |
| `GET /api/crm/rbac/my-permissions` | 无需特殊权限 |

## 用户角色解析顺序

系统按以下顺序确定用户的 CRM 角色：

1. **`rbac_user_roles` 表**: 查找该用户关联的 `admin`/`manager`/`sales`/`viewer` 角色
2. **`User.role` 字段**: 如果用户的 `role` 字段值为 `admin`，则映射为 CRM admin；其他值默认映射为 `viewer`
3. **兜底**: 以上均未匹配时，默认为 `viewer`（只读）

## 数据库表

RBAC 系统复用 `app.models.rbac` 中的现有模型：

| 表名 | 说明 |
|------|------|
| `rbac_roles` | 角色定义（CRM 4 角色 + 其他系统角色） |
| `rbac_role_permissions` | 角色-权限关联 |
| `rbac_user_roles` | 用户-角色分配 |

## 初始设置

### 首次部署

首次运行时，调用 `ensure_crm_role_definition()` 函数会自动同步所有 CRM 角色到 `rbac_roles` 表。

可以通过 API 触发：
```bash
# 同步所有角色
curl -X POST http://localhost:8000/api/crm/rbac/roles \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "admin"}'
```

### 分配初始管理员

1. 通过数据库直接插入，或注册后通过 API 分配：
```bash
curl -X POST http://localhost:8000/api/crm/rbac/assign \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "role": "admin"}'
```

## 自定义与扩展

如需添加新的 CRM 权限：

1. 在 `crm_rbac.py` 中定义新的权限常量
2. 在 `CRM_PERMISSION_MATRIX` 中为各角色添加权限
3. 在 `CRM_PERMISSION_LABELS` 中添加中文描述
4. 在相应的 API 端点上添加 `require_permission()` 依赖

## 开发注意事项

- 权限检查是**增量式**的，不影响已有 API 的请求/响应格式
- 未认证用户仍会先经过 JWT 认证，再进入权限检查
- `require_permission()` 抛出 `HTTPException(403)`，保持与现有错误处理一致
- 工作流引擎的规则 CRUD 目前仅允许 admin 操作（后续可按需放宽）
