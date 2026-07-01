# AI数字名片 — API 设计规范

> 版本: v1.0  
> 最后更新: 2026-07-01  
> 适用于: 所有 `/api/v1/` 路由

---

## 1. URL 命名规则

### 1.1 基本格式

```
/api/v1/{resource}
/api/v1/{resource}/{id}
/api/v1/{resource}/{id}/{sub-resource}
```

- **全小写**: 所有路径段使用小写英文字母。
- **中划线连接**: 多词资源使用中划线（`-`）而非下划线（`_`）或驼峰。
- **名词复数**: 资源名使用复数形式。

| ✅ 正确 | ❌ 错误 |
|---------|---------|
| `/api/v1/brochures` | `/api/v1/brochure` |
| `/api/v1/ai-assist` | `/api/v1/ai_assist` |
| `/api/v1/users/{id}/visitor-logs` | `/api/v1/users/{id}/visitorLogs` |

### 1.2 版本控制

- 版本号嵌入 URL 路径：`/api/v1/`、`/api/v2/`。
- 响应的 `Content-Type` 中**不包含**版本信息。
- 兼容性说明见第 5 节（Deprecation 策略）。

### 1.3 查询参数

- 使用 `camelCase`（小驼峰）命名查询参数，与 JSON 响应字段保持一致。
- 布尔参数使用 `true`/`false`（小写），禁止 `1`/`0` 或 `yes`/`no`。

```
GET /api/v1/brochures?pageSize=20&hasVideo=true
```

---

## 2. OperationId 命名规范

OperationId 是 OpenAPI 规范中每个端点的唯一标识符，用于生成 SDK 客户端方法名。

### 2.1 格式

```
{action}{Resource}
```

- **{action}**: 小驼峰动词前缀（`list`、`get`、`create`、`update`、`delete`、`batchCreate` 等）
- **{Resource}**: 资源名首字母大写（PascalCase）

| HTTP 方法 | 路径 | operationId |
|-----------|------|-------------|
| GET | `/api/v1/users` | `listUsers` |
| POST | `/api/v1/users` | `createUser` |
| GET | `/api/v1/users/{id}` | `getUser` |
| PUT | `/api/v1/users/{id}` | `updateUser` |
| DELETE | `/api/v1/users/{id}` | `deleteUser` |
| PATCH | `/api/v1/users/{id}` | `patchUser` |
| POST | `/api/v1/brochures/{id}/publish` | `publishBrochure` |
| GET | `/api/v1/users/{id}/visitor-logs` | `listUserVisitorLogs` |

### 2.2 FastAPI 实现方式

在路由装饰器上使用 `operation_id` 参数显式指定：

```python
@router.get("", operation_id="listUsers")
async def list_users(...):
    ...
```

> **注意**: 不从函数名自动推导 operationId，必须显式设定。

---

## 3. 分页标准

### 3.1 推荐：Cursor-based 分页（适用于大集合、实时数据）

```
GET /api/v1/brochures?cursor=eyJsYXN0X2lkIjoxMDB9&pageSize=20
```

**请求参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `cursor` | string | 否 | 不透明分页游标（Base64 编码 JSON）。首次请求不传。 |
| `pageSize` | integer | 否 | 每页条数，默认 20，最大 100。 |

**响应体**:

```json
{
  "items": [...],
  "total": 1050,
  "pageSize": 20,
  "hasMore": true,
  "nextCursor": "eyJsYXN0X2lkIjoyMDB9"
}
```

### 3.2 兼容：Offset/Limit 分页（适用于管理后台、简单列表）

```
GET /api/v1/brochures?page=1&pageSize=20
```

**请求参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `page` | integer | 否 | 页码（从 1 开始），默认 1。 |
| `pageSize` | integer | 否 | 每页条数，默认 20，最大 100。 |

**响应体**:

```json
{
  "items": [...],
  "total": 1050,
  "page": 1,
  "pageSize": 20,
  "hasMore": true
}
```

### 3.3 统一响应模型

所有分页响应使用 `PaginatedResponse` 模型（详见 `api_standards.py`）：

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False
    next_cursor: Optional[str] = None
```

---

## 4. 错误处理

### 4.1 统一错误响应格式

所有错误响应使用以下 JSON 结构：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数校验失败",
  "details": {
    "fields": [
      {"field": "email", "reason": "不是一个有效的邮箱地址"}
    ]
  },
  "request_id": "req_abc123def456"
}
```

### 4.2 错误码规范

**格式**: `{CATEGORY}_{SPECIFIC}` — 全大写+下划线

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| `VALIDATION_ERROR` | 400 | 请求参数校验失败 |
| `UNAUTHORIZED` | 401 | 未认证或 token 过期 |
| `FORBIDDEN` | 403 | 无权限访问资源 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `RESOURCE_CONFLICT` | 409 | 资源冲突（如重复创建） |
| `RATE_LIMITED` | 429 | 请求频率超限 |
| `INTERNAL_ERROR` | 500 | 服务端内部错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务暂不可用（如第三方依赖故障） |
| `DEPRECATED` | 410 | 接口已废弃 |

### 4.3 实现方式

使用 `api_standards.py` 中的 `raise_http_error` 辅助函数：

```python
from app.api_standards import raise_http_error, ErrorCode

# 简单的 404
raise_http_error(404, ErrorCode.NOT_FOUND, "用户不存在")

# 带详细字段的 400
raise_http_error(400, ErrorCode.VALIDATION_ERROR, "参数校验失败",
    details={"fields": [{"field": "email", "reason": "格式错误"}]})
```

### 4.4 request_id

- 每个请求在中间件层自动生成并注入 `request_id`。
- 可通过 `X-Request-ID` 响应头获取。
- 所有日志和 Sentry 事件自动关联 `request_id`。

---

## 5. Deprecation 策略

### 5.1 废弃流程

```
宣布废弃 → 6个月迁移期 → 最终移除
```

| 阶段 | 行为 | 响应头 | 说明 |
|------|------|--------|------|
| 活跃 | 正常服务 | 无 | 当前稳定版本 |
| 弃用 | 正常服务 + 告警 | `Sunset: Sat, 01 Jan 2027 00:00:00 GMT` | 至少 6 个月 |
| 移除 | 返回 410 Gone | — | 彻底不可用 |

### 5.2 Deprecation 响应头

弃用期间的端点必须返回以下 HTTP 头：

```
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Deprecation: true
Link: </api/v2/users>; rel="successor-version"
```

### 5.3 实现方式

使用 `api_standards.py` 中的 `deprecated` 装饰器：

```python
from app.api_standards import deprecated

@router.get("/api/v1/old-endpoint")
@deprecated(sunset="2027-01-01", successor="/api/v2/brochures")
async def old_endpoint():
    ...
```

### 5.4 版本间兼容性保证

- 不删除或重命名必填字段。
- 不更改字段类型。
- 新增字段使用 `Optional`，默认为 `None` 或空值。
- 枚举值只增加不减少。

---

## 6. 通用规范

### 6.1 HTTP 方法语义

| 方法 | 语义 | 幂等 | 安全 |
|------|------|------|------|
| GET | 查询资源 | ✅ | ✅ |
| POST | 创建资源 / 执行动作 | ❌ | ❌ |
| PUT | 全量替换资源 | ✅ | ❌ |
| PATCH | 部分更新资源 | ❌ | ❌ |
| DELETE | 删除资源 | ✅ | ❌ |

### 6.2 响应状态码

| 范围 | 使用场景 |
|------|---------|
| 200 | GET / PUT / PATCH 成功 |
| 201 | POST 创建成功（含 `Location` 头） |
| 204 | DELETE 成功（无响应体） |
| 400 | 客户端请求错误 |
| 401 | 未认证 |
| 403 | 已认证但无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 请求体校验失败（Pydantic） |
| 429 | 速率限制 |
| 500 | 服务端内部错误 |

### 6.3 日期时间格式

- 全部使用 **ISO 8601** 格式：`2026-07-01T14:30:00Z`
- 统一使用 UTC（末尾带 `Z`），除非业务场景明确需要本地时间。
- 字段命名：`created_at`、`updated_at`、`expires_at`

### 6.4 国际化

- 所有错误消息的 `message` 字段返回英文，前端根据 `Accept-Language` 做本地化。
- 用户可见的字段（如 brochure title）支持多语言存储，详见 `docs/i18n/translation_platform.md`。

---

## 7. 安全规范

### 7.1 认证

- 使用 `Authorization: Bearer <jwt_token>` 头传递 Token。
- Token 通过 `/api/v1/auth/login` 获取。
- 敏感端点需额外验证（如修改手机号需短信验证码）。

### 7.2 速率限制

| 层级 | 限制 | 窗口 |
|------|------|------|
| 匿名 | 100 次 | 60 秒 |
| 标准用户 | 1000 次 | 60 秒 |
| 企业用户 | 10000 次 | 60 秒 |

限制超限返回 `429 Too Many Requests`，响应头携带 `Retry-After`。

### 7.3 敏感信息

- 响应中绝不返回明文密码。
- 手机号、邮箱等个人信息视业务需求做脱敏。
- 所有请求日志不记录 `Authorization` 头和密码字段。

---

## 8. 可观测性

### 8.1 请求日志

每条请求日志包含：

| 字段 | 说明 |
|------|------|
| `request_id` | 唯一请求 ID |
| `method` | HTTP 方法 |
| `path` | 请求路径 |
| `status` | HTTP 状态码 |
| `duration_ms` | 耗时（毫秒） |
| `user_id` | 认证用户 ID（如已认证） |

### 8.2 Metrics

- **RED 指标**: Rate（请求率）、Errors（错误率）、Duration（延迟分布）
- **业务指标**: 用户注册数、名片创建数、匹配成功数
- 通过 `/metrics` 端点暴露，格式兼容 Prometheus。

---

## 9. 变更记录

| 日期 | 版本 | 变更说明 |
|------|------|---------|
| 2026-07-01 | v1.0 | 初始版本 |
