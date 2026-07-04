# 开发者门户 — API Key 管理 + 应用注册

## 概述

开发者门户提供 API Key 管理和应用注册功能，支持第三方开发者接入链客宝平台。

### 架构

```
开发者
   │
   ├─ JWT Bearer Token (AuthMiddleware) ──┐
   │                                       │
   ├─ X-API-Key Header  ──┤               │
   │                      │               │
   │              api_key_middleware       │
   │                      │               │
   └─ ?api_key=param  ────┘               │
                                           ▼
                                   FastAPI Router 层
                              /api/v1/developer/*
                                   │
                                   ▼
                              数据库 (SQLite/PostgreSQL)
                           developer_apps / api_keys / api_usage_logs
```

## 认证方式

### 1. JWT 认证 (现有)

通过 `Authorization: Bearer <token>` 传递。由 `AuthMiddleware` 统一处理。

### 2. API Key 认证 (新增)

通过以下两种方式传递:

- **Header**: `X-API-Key: <your-api-key>`
- **Query 参数**: `?api_key=<your-api-key>`

**优先级**: API Key 的优先级高于 JWT。如果同时提供两者，系统优先使用 API Key。

## API 端点

所有端点通过 `domain_routes.py` 自动版本化到 `/api/v1/developer/*`.
同时保留 `/api/developer/*` 作为向后兼容的 legacy 路径。

### 应用注册

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/developer/apps | 注册新应用 |
| GET | /api/v1/developer/apps | 列出应用 |
| PUT | /api/v1/developer/apps/{app_id} | 更新应用 |
| DELETE | /api/v1/developer/apps/{app_id} | 删除应用 |
| POST | /api/v1/developer/apps/{app_id}/regenerate-secret | 重置密钥 |

**POST /api/v1/developer/apps**

```json
{
  "name": "我的应用",
  "description": "应用描述",
  "website": "https://example.com",
  "redirect_uris": ["https://example.com/callback"],
  "scopes": ["read", "write"]
}
```

**响应** (client_secret 仅创建时返回一次):

```json
{
  "code": 0,
  "message": "应用注册成功",
  "data": {
    "id": 1,
    "name": "我的应用",
    "description": "应用描述",
    "website": "https://example.com",
    "redirect_uris": ["https://example.com/callback"],
    "client_id": "app_3a8f2c1b...",
    "client_secret": "sec_9d8e3f...",
    "client_secret_prefix": "sec_9d8e",
    "scopes": ["read", "write"],
    "active": true,
    "created_at": "2026-07-04T10:00:00",
    "updated_at": "2026-07-04T10:00:00",
    "warning": "请立即保存此 client_secret，之后无法再次查看完整密钥"
  }
}
```

### API Key 管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/developer/keys | 创建 API Key |
| GET | /api/v1/developer/keys | 列出 API Key |
| DELETE | /api/v1/developer/keys/{key_id} | 撤销 API Key |
| POST | /api/v1/developer/keys/{key_id}/rotate | 轮换 API Key |

**API Key 等级与速率限制**:

| 等级 | 速率限制 | 说明 |
|------|---------|------|
| free | 100 次/小时 | 免费版 |
| pro | 1,000 次/小时 | 专业版 |
| enterprise | 10,000 次/小时 | 企业版 |

### 用量统计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/developer/usage | 用量统计 (按日/按月) |

**参数**:
- `granularity`: `day` (按日) 或 `month` (按月), 默认 `day`
- `days`: 统计天数, 1-365, 默认 30

### 调用日志

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/developer/logs | API 调用日志 |

**参数**:
- `page`: 页码, 默认 1
- `page_size`: 每页条数, 默认 20, 最大 100
- `status_code`: 按状态码过滤 (可选)
- `days`: 查询最近 N 天, 1-90, 默认 7

### 仪表盘页面

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /developer/dashboard | 开发者仪表盘 HTML 页面 |

使用 Chart.js CDN 渲染 API 调用趋势图表 (过去 30 天).

## 数据模型

### DeveloperApp

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 自增主键 |
| user_id | Integer | 所属用户 ID |
| name | String(100) | 应用名称 |
| description | Text | 应用描述 |
| website | String(512) | 应用网站 |
| redirect_uris | Text | OAuth2 回调 URI (逗号分隔) |
| client_id | String(64) | 客户端 ID (app_xxx) |
| client_secret_hash | String(128) | SHA256 哈希 |
| client_secret_prefix | String(8) | 前缀 (用于显示) |
| scopes | String(500) | 权限范围 (逗号分隔) |
| active | Boolean | 是否启用 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### ApiKey

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 自增主键 |
| key_id | String(64) | 公开标识 (lk_xxx) |
| key_hash | String(128) | SHA256 哈希 |
| key_prefix | String(16) | 前缀 (用于显示) |
| name | String(100) | 名称 |
| user_id | String(64) | 所属用户 ID |
| scopes | String(500) | 权限范围 |
| tier | String(20) | 等级 |
| rate_limit_per_hour | Integer | 速率限制 |
| is_active | Boolean | 是否活跃 |
| last_used_at | DateTime | 最后使用 |
| created_at | DateTime | 创建时间 |
| revoked_at | DateTime | 撤销时间 |

### ApiUsageLog

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 自增主键 |
| api_key_id | Integer | 关联 API Key |
| user_id | String(64) | 用户 ID |
| endpoint | String(255) | 调用端点 |
| method | String(10) | HTTP 方法 |
| status_code | Integer | HTTP 状态码 |
| latency_ms | Integer | 延迟 (ms) |
| ip_address | String(45) | 客户端 IP |
| created_at | DateTime | 调用时间 |

## 中间件架构

### 认证中间件链

```
请求进入
  │
  ▼
CORS Middleware
  │
  ▼
RateLimit Middleware (IP 级别)
  │
  ▼
AuthMiddleware (JWT: Authorization: Bearer ***)
  │
  ▼
api_key_middleware (API Key: X-API-Key header 或 ?api_key=)
  │  ├─ 无 API Key → 跳过 (回退 JWT)
  │  └─ 有 API Key → 验证 → 注入 request.state.api_key_info → 记录日志
  │
  ▼
业务路由
```

### API Key 认证流程

1. 请求进入 `api_key_middleware`
2. 从 `X-API-Key` header 或 `?api_key=` 参数提取 API Key
3. 无 API Key → 跳过中间件，回退到 JWT 认证
4. 有 API Key → SHA256 哈希后查询 `api_keys` 表
5. 验证: Key 存在 + `is_active=True` + 未吊销
6. 速率限制: 检查过去 1 小时内的调用次数是否超出 `rate_limit_per_hour`
7. 注入 `request.state.api_key_info`
8. 调用完成后记录 `ApiUsageLog`

## FastAPI 依赖注入

### require_api_key

强制要求 API Key 认证:

```python
from app.middleware.api_key_middleware import require_api_key

@router.get("/secure")
def secure_endpoint(api_key_info: dict = Depends(require_api_key)):
    ...
```

### require_jwt_or_api_key

接受 JWT 或 API Key 任一认证方式:

```python
from app.middleware.api_key_middleware import require_jwt_or_api_key

@router.get("/data")
def get_data(auth_info: dict = Depends(require_jwt_or_api_key)):
    ...
```

## 安全性

1. **API Key 哈希存储**: 使用 SHA256 哈希，数据库中不存储明文
2. **仅创建时返回**: API Key 和 client_secret 仅创建时返回一次
3. **前缀显示**: 列表页面仅显示前缀 (前 8 位)，用于识别
4. **软删除**: 撤销 Key 时保留数据库记录，设置 `is_active=False`
5. **速率限制**: 双层限流 (IP 级别 + API Key 级别)
6. **调用日志**: 每次 API 调用都记录日志，支持审计和用量统计

## 仪表盘

访问 `GET /developer/dashboard` 查看开发者仪表盘，包括:

- 统计卡片: 应用总数、API Key 数量、调用次数
- API 调用趋势图表 (Chart.js, 过去 30 天)
- 应用列表
- API Key 列表
- 调用日志

## 测试

```bash
# 运行所有测试
cd backend && python -m pytest tests/test_developer_portal.py -v

# 运行语法检查
python -m py_compile app/models/developer_app.py
python -m py_compile app/routers/developer.py
python -m py_compile app/middleware/api_key_middleware.py
```
