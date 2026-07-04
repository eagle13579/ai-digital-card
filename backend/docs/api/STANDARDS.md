# 链客宝 API 设计规范

> 版本：1.0  
> 最后更新：2026-06-26  
> 适用范围：所有后端 RESTful API 端点

---

## 1. RESTful URI 命名规范

### 1.1 资源路径（Resource Path）

| 规则 | 要求 | 正确示例 | 错误示例 |
|------|------|-----------|-----------|
| 资源名使用复数 | 所有集合资源用英文复数 | `/api/v1/users` | `/api/v1/user` |
| 单词连接用 kebab-case | 多个单词以连字符分隔 | `/api/v1/business-cards` | `/api/v1/businessCards`、`/api/v1/business_cards` |
| 层级关系用嵌套 | 子资源通过父资源 ID 嵌套 | `/api/v1/contacts/{contact_id}/activities` | `/api/v1/activities?contact_id=xxx` |
| 动词仅用于 action 模式 | 非 CRUD 操作使用 `:` 或动词后缀 | `POST /api/v1/orders/{id}:cancel` | `POST /api/v1/cancel-order` |

### 1.2 URL 模板

```
/api/v{version}/{resources}[/{resource_id}][/{sub_resources}[/{sub_resource_id}]][/:action]
```

示例：
- `GET    /api/v1/users`                — 用户列表
- `GET    /api/v1/users/{user_id}`      — 用户详情
- `POST   /api/v1/users`                — 创建用户
- `PUT    /api/v1/users/{user_id}`      — 全量更新用户
- `PATCH  /api/v1/users/{user_id}`      — 部分更新用户
- `DELETE /api/v1/users/{user_id}`      — 删除用户
- `POST   /api/v1/orders/{id}:cancel`   — 取消订单（动作）

### 1.3 路径前缀一览（当前状态 vs 目标状态）

| 当前前缀 | 目标前缀 | 说明 |
|-----------|----------|------|
| `/api/auth` | `/api/v1/auth` | 认证模块 |
| `/api/business-card` | `/api/v1/business-cards` | 名片（单数→复数） |
| `/api/brochure` | `/api/v1/brochures` | 电子画册 |
| `/api/contacts` | `/api/v1/contacts` | 联系人 |
| `/api/products` | `/api/v1/products` | 产品 |
| `/api/orders` | `/api/v1/orders` | 订单 |
| `/api/needs` | `/api/v1/needs` | 需求 |
| `/api/promoter` | `/api/v1/promoters` | 推广分润 |
| `/api/recharge` | `/api/v1/recharges` | 充值 |

---

## 2. 统一响应格式

所有 API 响应必须遵循以下三层结构：

### 2.1 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

- `code`：业务状态码，`0` 表示成功
- `message`：人类可读的描述信息
- `data`：实际业务负载（对象、数组，或 `null`）

### 2.2 错误响应

```json
{
  "code": 10001,
  "message": "用户不存在",
  "error": {
    "type": "NOT_FOUND",
    "detail": "user_id=abc-123 在数据库中未找到",
    "trace_id": "txn-20260626-abcdef"
  }
}
```

- `code`：业务错误码（非零）
- `message`：用户友好的错误提示
- `error`：调试信息层（生产环境可选择性隐藏 `detail`）
  - `type`：错误类型枚举
  - `detail`：详细技术信息（可选）
  - `trace_id`：请求追踪 ID，用于日志关联

### 2.3 分页响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [ ... ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 156,
      "total_pages": 8
    }
  }
}
```

分页请求参数：
| 参数 | 类型 | 默认值 | 最大值 | 说明 |
|------|------|--------|--------|------|
| `page` | integer | 1 | - | 当前页码 |
| `page_size` | integer | 20 | 100 | 每页条数 |

---

## 3. HTTP 状态码使用规范

| 状态码 | 含义 | 适用场景 |
|--------|------|----------|
| `200 OK` | 请求成功 | GET 查询成功、PUT/PATCH 更新成功 |
| `201 Created` | 资源创建成功 | POST 创建新资源 |
| `204 No Content` | 删除成功 | DELETE 删除资源（无响应体） |
| `400 Bad Request` | 请求参数错误 | 参数校验失败、JSON 格式错误 |
| `401 Unauthorized` | 未认证 | Token 缺失或无效 |
| `403 Forbidden` | 无权限 | 已认证但无权访问 |
| `404 Not Found` | 资源不存在 | 资源 ID 无效或已删除 |
| `409 Conflict` | 资源冲突 | 唯一约束冲突、重复创建 |
| `422 Unprocessable Entity` | 请求体语义错误 | Pydantic 校验失败，字段类型/格式不符 |
| `429 Too Many Requests` | 频率限制 | 触发 API 限流 |
| `500 Internal Server Error` | 服务端异常 | 未捕获的异常（应由全局异常处理器兜底） |

> 原则：不要将业务错误映射为 500。所有可预期的业务异常使用 4xx + 业务错误码。

---

## 4. 错误码枚举表

### 4.1 通用错误码（0xxx）

| code | name | HTTP Status | 说明 |
|------|------|-------------|------|
| 0 | SUCCESS | 200 | 成功 |
| 1000 | UNKNOWN_ERROR | 500 | 未知服务端错误 |
| 1001 | DATABASE_ERROR | 500 | 数据库操作异常 |
| 1002 | EXTERNAL_SERVICE_ERROR | 502 | 外部服务调用失败 |
| 1003 | RATE_LIMITED | 429 | 请求频率超限 |

### 4.2 认证与鉴权错误码（1xxx）

| code | name | HTTP Status | 说明 |
|------|------|-------------|------|
| 1001 | INVALID_TOKEN | 401 | Token 无效或过期 |
| 1002 | TOKEN_EXPIRED | 401 | Token 已过期 |
| 1003 | FORBIDDEN | 403 | 无操作权限 |
| 1004 | INVALID_CREDENTIALS | 401 | 用户名或密码错误 |

### 4.3 参数与校验错误码（2xxx）

| code | name | HTTP Status | 说明 |
|------|------|-------------|------|
| 2001 | INVALID_PARAMETER | 400 | 请求参数非法 |
| 2002 | MISSING_PARAMETER | 400 | 缺少必要参数 |
| 2003 | VALIDATION_ERROR | 422 | 数据校验失败 |
| 2004 | RESOURCE_NOT_FOUND | 404 | 请求的资源不存在 |
| 2005 | RESOURCE_CONFLICT | 409 | 资源冲突（如重复） |

### 4.4 业务逻辑错误码（3xxx）

| code | name | HTTP Status | 说明 |
|------|------|-------------|------|
| 3001 | BUSINESS_RULE_VIOLATION | 400 | 违反业务规则 |
| 3002 | INSUFFICIENT_BALANCE | 400 | 余额不足 |
| 3003 | OPERATION_NOT_ALLOWED | 403 | 当前状态下不允许操作 |
| 3004 | DUPLICATE_OPERATION | 409 | 重复操作 |

### 4.5 使用方式

在路由 handler 中：

```python
from app.exceptions import AppException

# 方式一：直接抛出异常（推荐）
raise AppException(code=2004, message="用户不存在", http_status=404)

# 方式二：在依赖或 service 层返回错误码
return APIResponse(code=3001, message="余额不足", data=None)
```

---

## 5. 请求头规范

| 头字段 | 必需 | 示例 | 说明 |
|--------|------|------|------|
| `Authorization` | 是（认证接口除外） | `Bearer eyJhbGci...` | JWT 令牌 |
| `Content-Type` | POST/PUT/PATCH 时必需 | `application/json` | 请求体类型 |
| `Accept-Language` | 否 | `zh-CN`, `en` | 多语言偏好 |
| `X-Request-Id` | 推荐 | `uuid-v4` | 请求追踪 ID |
| `X-Api-Version` | 否 | `1` | 客户端期望的 API 版本 |

---

## 6. 命名约定总结

| 类别 | 约定 | 示例 |
|------|------|------|
| URL 路径 | kebab-case + 复数 | `/api/v1/business-cards` |
| 查询参数 | snake_case | `?page_size=20&sort_by=created_at` |
| JSON 键 | snake_case | `{"user_id": "abc", "created_at": "..."}` |
| 枚举值 | UPPER_SNAKE_CASE | `PENDING`, `ACTIVE`, `DELETED` |
| 错误类型 | UPPER_SNAKE_CASE | `RESOURCE_NOT_FOUND` |
| 路由文件名 | snake_case | `business_card.py`, `brochure_bridge.py` |

---

## 7. 附录：过渡规则

对于当前已发布的 `/api/*` 路径（无版本前缀），在 v1 迁移完成前：

1. 旧路径 `/api/*` 继续可用（通过 middleware 转发到 `/api/v1/*`）
2. 新端点只注册在 `/api/v1/*` 下
3. 每个迭代清除一部分旧路径，直至全部废弃
