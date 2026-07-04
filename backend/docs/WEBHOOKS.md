# 链客宝 — 对外 Webhook 系统文档

## 概述

链客宝对外 Webhook 系统允许第三方服务订阅平台内部事件，实时接收事件通知。Webhook 通过 HTTP POST 请求将事件负载推送到您指定的回调 URL。

---

## 目录

1. [快速开始](#快速开始)
2. [事件类型列表](#事件类型列表)
3. [API 端点](#api-端点)
4. [签名验证](#签名验证)
5. [重试策略](#重试策略)
6. [限流规则](#限流规则)
7. [幂等性](#幂等性)
8. [Webhook Payload Schema](#webhook-payload-schema)
9. [常见问题](#常见问题)

---

## 快速开始

### 1. 注册 Webhook 订阅

```bash
curl -X POST https://api.liankebao.top/api/v1/webhooks \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-service.com/webhook/callback",
    "events": ["match.found", "order.created"]
  }'
```

### 2. 验证回调签名

在您的回调端点中，验证 `X-Webhook-Signature` 请求头以确保请求来自链客宝。

**Python 示例：**

```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """验证 Webhook 签名"""
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### 3. 返回 2xx 确认接收

链客宝期望您的回调端点返回 HTTP 200-299 状态码以确认成功接收。如果返回非 2xx 状态码或超时，系统将按[重试策略](#重试策略)重新投递。

---

## 事件类型列表

| 事件类型 | 说明 | 触发场景 |
|---------|------|---------|
| `contact.created` | 联系人创建 | 用户添加新联系人时触发 |
| `contact.updated` | 联系人更新 | 联系人信息变更时触发 |
| `match.found` | 匹配成功 | 系统为用户找到新的匹配时触发 |
| `payment.completed` | 支付完成 | 支付成功完成时触发 |
| `nfc.shared` | NFC 名片分享 | 用户通过 NFC 分享名片时触发 |
| `order.created` | 订单创建 | 新订单生成时触发 |

**事件订阅规则：**
- 每次订阅最少选择 1 个事件类型，最多 20 个
- 事件类型不区分大小写，系统会自动归一化
- 每个用户可创建多个 Webhook 订阅，每个订阅可订阅不同的事件组合

---

## API 端点

所有端点需要认证（Bearer Token）。

### `POST /api/v1/webhooks` — 创建订阅

**请求体：**
```json
{
  "url": "https://your-service.com/webhook/callback",
  "events": ["match.found", "order.created"],
  "secret": "your-custom-secret"  // 可选，不传则自动生成
}
```

**响应 (200)：**
```json
{
  "code": 0,
  "message": "Webhook 订阅创建成功",
  "data": {
    "id": 1,
    "user_id": 42,
    "url": "https://your-service.com/webhook/callback",
    "events": ["match.found", "order.created"],
    "secret": "whsec_abc123def456...",
    "active": true,
    "created_at": "2026-07-04T10:30:00",
    "last_triggered_at": null
  }
}
```

> ⚠️ **重要：** `secret` 仅在创建时返回一次，请立即保存。之后无法再次查看。

### `GET /api/v1/webhooks` — 列出订阅

**查询参数：**
- `active_only` (bool, 默认: true) — 仅显示活跃订阅

**响应 (200)：**
```json
{
  "code": 0,
  "data": {
    "total": 2,
    "webhooks": [
      {
        "id": 1,
        "user_id": 42,
        "url": "https://your-service.com/webhook/callback",
        "events": ["match.found", "order.created"],
        "active": true,
        "created_at": "2026-07-04T10:30:00",
        "last_triggered_at": "2026-07-04T11:00:00"
      }
    ]
  }
}
```

> 列表接口**不返回** `secret` 字段。

### `PUT /api/v1/webhooks/{id}` — 更新订阅

**请求体（全部可选）：**
```json
{
  "url": "https://new-url.com/webhook",
  "events": ["match.found"],
  "secret": "new-whsec-secret",
  "active": true
}
```

**响应：** 返回更新后的完整 Webhook 信息（包含 `secret`）。

### `DELETE /api/v1/webhooks/{id}` — 删除订阅

**响应 (200)：**
```json
{
  "code": 0,
  "message": "Webhook 订阅 #1 已删除"
}
```

> 注意：这是**硬删除**，数据将从数据库中移除。如需暂停请使用 `PUT` 设置 `active: false`。

### `POST /api/v1/webhooks/{id}/test` — 发送测试事件

向指定 Webhook 发送一条测试消息（事件类型: `webhook.test`）。

**响应 (200)：**
```json
{
  "code": 0,
  "message": "测试事件发送成功",
  "data": {
    "success": true,
    "event_id": "test_1720093800",
    "subscription_id": 1
  }
}
```

如果投递失败，`code` 为 1，`message` 包含失败提示。

### `GET /api/v1/webhooks/{id}/logs` — 投递日志

**查询参数：**
- `status` (可选) — 筛选: `success` / `failed`
- `limit` (int, 默认: 20, 最大: 200)
- `offset` (int, 默认: 0)

**响应 (200)：**
```json
{
  "code": 0,
  "data": {
    "total": 5,
    "logs": [
      {
        "id": 100,
        "subscription_id": 1,
        "event_type": "match.found",
        "event_id": "evt_abc123",
        "status": "success",
        "attempt": 1,
        "response_code": 200,
        "error_message": null,
        "created_at": "2026-07-04T11:00:00"
      }
    ]
  }
}
```

---

## 签名验证

每个 Webhook 请求都包含以下请求头用于验证：

| 请求头 | 说明 | 示例 |
|--------|------|------|
| `X-Webhook-Signature` | HMAC-SHA256 签名 | `sha256=a1b2c3d4e5f6...` |
| `X-Webhook-Id` | 事件唯一 ID (用于幂等) | `evt_550e8400-e29b-41d4-a716-446655440000` |
| `X-Webhook-Event` | 事件类型 | `match.found` |
| `X-Webhook-Timestamp` | 事件发生时间戳 | `1720093800` |
| `User-Agent` | 客户端标识 | `Chainke-Webhook/2.0` |
| `Content-Type` | 内容类型 | `application/json` |

### 签名算法（HMAC-SHA256）

```
signature = HMAC-SHA256(secret, request_body)
```

其中：
- `secret` 是您创建 Webhook 订阅时获得的密钥
- `request_body` 是**原始请求体**（未解析的 JSON 字符串）
- 最终签名以 `sha256=` 前缀发送

### 签名验证示例

**Python：**
```python
import hmac
import hashlib

def verify_signature(request_body: bytes, signature_header: str, secret: str) -> bool:
    if not signature_header.startswith("sha256="):
        return False
    received_sig = signature_header[7:]  # 去掉 "sha256="
    expected = hmac.new(
        secret.encode("utf-8"),
        request_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, received_sig)
```

**Node.js：**
```javascript
const crypto = require('crypto');

function verifySignature(rawBody, signature, secret) {
    const expected = crypto
        .createHmac('sha256', secret)
        .update(rawBody)
        .digest('hex');
    return crypto.timingSafeEqual(
        Buffer.from(expected),
        Buffer.from(signature.replace('sha256=', ''))
    );
}
```

---

## 重试策略

| 重试次数 | 等待时间 | 说明 |
|---------|---------|------|
| 第 1 次 | 1 秒 | 首次失败后立即重试 |
| 第 2 次 | 5 秒 | 第二次失败后等待 5 秒 |
| 第 3 次 | 30 秒 | 最后一次重试等待 30 秒 |
| 超过 3 次 | — | **自动标记订阅为 inactive** |

### 触发重试的条件

以下情况会触发重试：

1. **HTTP 非 2xx 状态码** — 返回 3xx/4xx/5xx
2. **网络超时** — 超过 15 秒未响应
3. **连接错误** — DNS 解析失败、连接被拒绝

### 不触发重试的条件

- HTTP 2xx 状态码 — 视为成功投递
- 订阅被标记为 inactive — 不再投递

### 订阅自动停用

当所有 3 次重试均失败后，系统会：
1. 记录最终失败日志（status: `failed`）
2. **自动将订阅标记为 `active: false`**
3. 不再向该订阅投递任何事件

您需要手动通过 `PUT /api/v1/webhooks/{id}` 重新激活订阅。

---

## 限流规则

| 限制项 | 值 | 说明 |
|-------|-----|------|
| 最大并发投递 | 20 | 系统全局并发 Webhook 投递数 |
| 每个回调超时 | 15 秒 | 超过此时间视为投递失败 |
| 每个订阅最大重试 | 3 次 | 超过后自动停用 |
| 幂等缓存大小 | 10,000 | 内存中缓存最近的事件 ID 用于去重 |
| 每个用户订阅数 | 不限 | 无硬性限制 |
| 每个订阅事件数 | 1-20 | 最少 1 个，最多 20 个事件类型 |

---

## 幂等性

每个 Webhook 投递请求都包含唯一的 `X-Webhook-Id` 请求头。该 ID 是事件的全局唯一标识。

**建议您：**
1. 在回调端点记录最近处理过的 `X-Webhook-Id`
2. 如果收到重复的 `X-Webhook-Id`，直接返回 200 OK 并跳过处理

链客宝系统内部也会对同一订阅+同一事件 ID 进行幂等去重（缓存最近 10,000 个记录），避免重复投递。

---

## Webhook Payload Schema

### 标准事件 Payload

```json
{
  "event_id": "evt_550e8400-e29b-41d4-a716-446655440000",
  "event_type": "match.found",
  "timestamp": 1720093800.123,
  "data": {
    // 事件具体数据，因事件类型而异
  }
}
```

### 各事件类型 Data 示例

#### `match.found`
```json
{
  "event_id": "evt_abc123",
  "event_type": "match.found",
  "timestamp": 1720093800.123,
  "data": {
    "match_id": 456,
    "user_id": 42,
    "matched_user_id": 99,
    "score": 0.95,
    "type": "ai_recommend"
  }
}
```

#### `order.created`
```json
{
  "event_id": "evt_def456",
  "event_type": "order.created",
  "timestamp": 1720093800.123,
  "data": {
    "order_id": 789,
    "user_id": 42,
    "product_id": "pro_001",
    "amount": 998.00,
    "currency": "CNY",
    "status": "pending_payment"
  }
}
```

#### `payment.completed`
```json
{
  "event_id": "evt_ghi789",
  "event_type": "payment.completed",
  "timestamp": 1720093800.123,
  "data": {
    "payment_id": "pay_001",
    "order_id": 789,
    "user_id": 42,
    "amount": 998.00,
    "currency": "CNY",
    "method": "wechat",
    "paid_at": "2026-07-04T11:00:00"
  }
}
```

#### `contact.created`
```json
{
  "event_id": "evt_jkl012",
  "event_type": "contact.created",
  "timestamp": 1720093800.123,
  "data": {
    "contact_id": 555,
    "user_id": 42,
    "name": "张三",
    "company": "某科技有限公司",
    "phone": "138****1234"
  }
}
```

#### `nfc.shared`
```json
{
  "event_id": "evt_mno345",
  "event_type": "nfc.shared",
  "timestamp": 1720093800.123,
  "data": {
    "nfc_binding_id": 777,
    "user_id": 42,
    "card_id": "card_abc",
    "shared_at": "2026-07-04T11:05:00",
    "device_info": "iPhone 15 Pro"
  }
}
```

### 测试事件 Payload

```json
{
  "event_id": "test_1720093800",
  "event_type": "webhook.test",
  "timestamp": 1720093800.123,
  "data": {
    "message": "This is a test webhook from Chainke platform",
    "subscription_id": 1,
    "url": "https://your-service.com/webhook/callback",
    "events": ["match.found", "order.created"]
  }
}
```

---

## 常见问题

### Q: Webhook 投递失败怎么办？

1. 检查您的回调端点是否可达（公网可达性）
2. 确认端点能在 15 秒内返回响应
3. 检查是否返回 2xx 状态码
4. 查看投递日志：`GET /api/v1/webhooks/{id}/logs`
5. 如果订阅已被停用，请通过 `PUT /api/v1/webhooks/{id}` 重新激活

### Q: Secret 丢失了怎么办？

Secret 仅在创建时返回一次。如果丢失，请：
1. 通过 `PUT /api/v1/webhooks/{id}` 设置新的 `secret`
2. 更新您的回调端点中的验证逻辑

### Q: 能否同时使用 V1 和 V2 的 Webhook？

可以。系统同时支持：
- **V1** (`/api/v1/developer/webhooks`) — 使用旧的 `WebhookSubscriptionDB` 模型
- **V2** (`/api/v1/webhooks`) — 使用新的 `WebhookSubscription` 模型，支持更新的特性

建议新用户直接使用 V2。

### Q: 如何测试 Webhook 是否正常工作？

使用 `POST /api/v1/webhooks/{id}/test` 发送测试事件。系统会向您的回调 URL 发送一条 `webhook.test` 事件，并返回投递结果。

### Q: 收到重复的 Webhook 事件怎么办？

每个事件包含唯一的 `X-Webhook-Id` 请求头。建议您在回调端点记录最近处理过的 ID，并在收到重复 ID 时直接返回 200 OK。

---

## 架构说明

```
外部服务                  链客宝平台
    │                         │
    │   POST /webhook/callback│
    │   X-Webhook-Signature   │
    │   X-Webhook-Id          │
    │   X-Webhook-Event       │
    │   X-Webhook-Timestamp   │
    │◄────────────────────────│
    │                         │
    │   200 OK (成功接收)      │
    │────────────────────────►│
    │                         │
    │   非 2xx / 超时         │
    │────────────────────────►│
    │   等待 1s / 5s / 30s    │
    │   (最多重试 3 次)       │
    │                         │
    │   全部失败 → 订阅停用   │
    │                         │
```

---

*文档版本: v2.0 (2026-07-04)*
*如有问题请联系链客宝技术支持*
