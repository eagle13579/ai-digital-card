# Web 表单捕获部署指南

> AI数字名片 — 嵌入网站表单 → 自动创建 CRM 联系人

---

## 1. 功能概述

**Web 表单捕获**允许您创建网页表单，嵌入到您的网站中。访客填写表单后，系统自动在 CRM 中创建联系人，无需手动录入。

### 工作流程

```
┌─────────────────┐      ┌──────────────────────┐      ┌──────────────────┐
│  管理员创建表单   │ ──→  │  获取嵌入代码放入网站  │ ──→  │  访客填写并提交   │
│  POST /api/...  │      │  <script src="..." /> │      │  点击"提交"按钮   │
└────────┬────────┘      └──────────────────────┘      └────────┬─────────┘
         │                                                      │
         ▼                                                      ▼
┌─────────────────┐                                    ┌──────────────────┐
│  CRM 联系人创建   │ ←─────────────────────────────────│  API 处理提交     │
│  自动添加标签     │                                    │  反垃圾检测       │
│  记录活动时间线   │                                    │  Honeypot + 限流  │
└─────────────────┘                                    └──────────────────┘
```

### 核心能力

| 能力 | 说明 |
|------|------|
| **表单生成** | 可视化定义字段（姓名、手机、邮箱、公司、职位等） |
| **嵌入代码** | 自动生成 HTML/JS 嵌入脚本，粘贴到网站即可使用 |
| **自动创建联系人** | 提交自动写入 CRM，带来源标记 `web_form` |
| **防垃圾** | Honeypot 隐藏字段 + IP 速率限制（每小时10次） |
| **自定义标签** | 表单提交自动给联系人打标签 |
| **提交日志** | 完整审计日志，含 IP、UA、提交数据、结果 |

---

## 2. 快速开始

### 2.1 创建表单

```bash
# 需要 JWT Token
TOKEN="your-jwt-token"

curl -X POST "https://api.yourdomain.com/api/crm/forms" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "产品咨询表单",
    "title": "获取产品资料",
    "description": "留下联系方式，我们将为您发送详细产品资料",
    "fields": [
      {"name": "姓名", "field": "name", "type": "text", "required": true, "placeholder": "请输入姓名"},
      {"name": "手机", "field": "phone", "type": "tel", "required": true, "placeholder": "请输入手机号"},
      {"name": "邮箱", "field": "email", "type": "email", "required": false, "placeholder": "请输入邮箱"},
      {"name": "公司", "field": "company", "type": "text", "required": false, "placeholder": "请输入公司名称"},
      {"name": "留言", "field": "intro", "type": "textarea", "required": false, "placeholder": "请输入留言内容"}
    ],
    "redirect_url": "https://yourdomain.com/thank-you",
    "success_message": "感谢您的咨询，我们的顾问将在24小时内联系您！",
    "auto_tags": ["网站咨询", "产品意向"],
    "embed_theme": "light",
    "embed_primary_color": "#1890ff"
  }'
```

**响应示例:**
```json
{
  "id": 1,
  "owner_id": 42,
  "name": "产品咨询表单",
  "title": "获取产品资料",
  "fields": [...],
  "submit_action": "create_contact",
  "redirect_url": "https://yourdomain.com/thank-you",
  "success_message": "感谢您的咨询...",
  "enable_honeypot": true,
  "enable_rate_limit": true,
  "auto_tags": ["网站咨询", "产品意向"],
  "is_active": true,
  "submission_count": 0,
  "embed_theme": "light",
  "embed_primary_color": "#1890ff",
  "created_at": "2026-07-02T10:00:00",
  "updated_at": "2026-07-02T10:00:00"
}
```

### 2.2 获取嵌入代码

```bash
curl -X GET "https://api.yourdomain.com/api/crm/forms/1/embed" \
  -H "Authorization: Bearer $TOKEN"
```

**响应示例:**
```json
{
  "form_id": 1,
  "embed_code": "<!-- AI数字名片... -->\n<div id=\"fc-...\">...</div>\n<script>...</script>",
  "html_snippet": "<!-- AI数字名片... -->\n<div id=\"fc-...\">...</div>\n<script>...</script>",
  "script_tag": "<!-- AI数字名片... -->\n<div id=\"fc-...\">...</div>\n<script>...</script>"
}
```

### 2.3 嵌入到网站

将返回的 `embed_code` 放入网站 HTML 的任意位置：

```html
<!DOCTYPE html>
<html>
<head>
    <title>我的网站</title>
</head>
<body>
    <h1>欢迎访问</h1>
    
    <!-- 粘贴嵌入代码到需要显示表单的位置 -->
    <!-- AI数字名片 - 表单捕获 产品咨询表单 -->
    <div id="fc-1a2b3c4d-root" data-form-id="1"></div>
    <script>
    (function() {
        // ... 自动生成的嵌入脚本
    })();
    </script>
</body>
</html>
```

### 2.4 访客提交

访客填写表单 → 点击提交 → JavaScript 将数据发送到 `POST /api/crm/forms/{id}/submit` → 自动创建 CRM 联系人。

### 2.5 查看提交日志

```bash
curl -X GET "https://api.yourdomain.com/api/crm/forms/1/logs" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 3. API 端点

### 3.1 认证端点（需 JWT）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/crm/forms` | 创建表单 |
| `GET` | `/api/crm/forms` | 表单列表 |
| `GET` | `/api/crm/forms/{id}` | 表单详情 |
| `PUT` | `/api/crm/forms/{id}` | 更新表单 |
| `DELETE` | `/api/crm/forms/{id}` | 删除表单 |
| `GET` | `/api/crm/forms/{id}/embed` | 获取嵌入代码 |
| `GET` | `/api/crm/forms/{id}/logs` | 提交日志 |

### 3.2 公开端点（无需认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/crm/forms/{id}/submit` | 访客提交表单 |

---

## 4. 表单字段映射

嵌入表单的字段名 (`field`) 与 CRM 联系人字段的映射关系：

| 表单字段名 | CRM 字段 | 字段类型 | 说明 |
|-----------|----------|---------|------|
| `name` | `name` | text | 联系人姓名 |
| `phone` | `phone` | tel | 手机号 |
| `email` | `email` | email | 邮箱 |
| `company` | `company` | text | 公司名称 |
| `title` | `title` | text | 职位 |
| `department` | `department` | text | 部门 |
| `intro` | `intro` | textarea | 简介/留言 |

> 如果 `name` 字段未提供，系统会自动填入"网站访客"。

---

## 5. 反垃圾机制

### 5.1 Honeypot（蜜罐）

嵌入代码会自动生成一个对用户不可见的隐藏字段（CSS 定位到屏幕外，`opacity: 0`，`height: 0`）。真实用户不会填写它，但自动化脚本可能会填写。如果检测到 Honeypot 字段有值，系统会：

1. 记录提交日志（标记 `honeypot_triggered=true`）
2. 返回假成功（不暴露检测逻辑）
3. **不创建 CRM 联系人**

### 5.2 IP 速率限制

每个 IP 每小时最多提交 **10 次**（默认）。超出后返回 HTTP 429。

可在表单配置中关闭速率限制：
```json
{
  "enable_rate_limit": false
}
```

> 生产环境建议保持开启。如果预计有大量真实提交，可升级到 Redis 实现（见下文"生产优化"）。

---

## 6. 错误代码

| HTTP 状态码 | 说明 | 常见原因 |
|------------|------|---------|
| `400` | 请求错误 | 必填字段缺失、数据格式错误 |
| `404` | 表单不存在 | form_id 无效 |
| `410` | 表单已禁用 | 管理员关闭了表单 |
| `429` | 请求过多 | 同 IP 超过速率限制 |

---

## 7. 生产优化

### 7.1 替换为 Redis 速率限制

`form_rate_limiter` 默认使用内存存储，多进程/多服务器部署时需要迁移到 Redis：

```python
# services/form_capture.py
# 替换 RateLimiter 类为 Redis 实现

import aioredis

class RedisRateLimiter:
    def __init__(self, redis_client, max_per_hour=10):
        self.redis = redis_client
        self.max_per_hour = max_per_hour
        self.window = 3600  # 1 hour

    async def is_allowed(self, ip: str) -> bool:
        key = f"form_rate_limit:{ip}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.window)
        return count <= self.max_per_hour

    async def get_remaining(self, ip: str) -> int:
        key = f"form_rate_limit:{ip}"
        count = int(await self.redis.get(key) or 0)
        return max(0, self.max_per_hour - count)
```

### 7.2 自定义嵌入样式

嵌入代码的样式通过 `embed_theme` 和 `embed_primary_color` 控制。如需完全自定义样式，可编辑嵌入 HTML 中的 CSS 块。

### 7.3 嵌入多个表单

支持在同一页面嵌入多个表单（每个表单有独立的 `scope_id`，不会冲突）。

---

## 8. 常见问题

**Q: 表单提交后页面跳转到哪里？**
A: 由创建表单时的 `redirect_url` 控制。如未设置，表单区域会显示成功消息。

**Q: 如何知道哪些联系人是通过表单创建的？**
A: 联系人 `source` 字段为 `web_form`，`source_record_id` 为表单 ID。

**Q: 如何测试嵌入代码？**
A: 创建一个测试表单，将嵌入代码粘贴到本地 HTML 文件，用浏览器打开即可测试。

**Q: 嵌入代码是否跨域？**
A: 是的，嵌入代码使用 Fetch API 直接调用后端。确保后端 CORS 配置允许网站域。

**Q: 是否支持文件上传（如附件）？**
A: 当前版本不支持文件上传字段。所有字段均为文本类型。

---

## 9. 数据模型

### CrmForm 表 (`crm_forms`)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int (PK) | 主键 |
| `owner_id` | int (FK) | 所属用户 |
| `name` | string(128) | 表单名称 |
| `title` | string(256) | 表单标题 |
| `description` | text | 表单说明 |
| `fields` | text (JSON) | 字段定义数组 |
| `submit_action` | string(32) | 提交动作 (`create_contact`) |
| `redirect_url` | string(512) | 成功跳转URL |
| `success_message` | string(256) | 成功提示 |
| `enable_honeypot` | bool | 启用蜜罐 |
| `enable_rate_limit` | bool | 启用速率限制 |
| `auto_tags` | text (JSON) | 自动标签 |
| `is_active` | bool | 是否启用 |
| `submission_count` | int | 提交计数 |
| `embed_theme` | string(32) | 主题 (`light`/`dark`) |
| `embed_primary_color` | string(16) | 主色调 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

### FormSubmissionLog 表 (`crm_form_submission_logs`)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int (PK) | 主键 |
| `form_id` | int (FK) | 所属表单 |
| `submitter_ip` | string(45) | 提交者IP |
| `submitter_ua` | text | User-Agent |
| `payload` | text (JSON) | 原始提交数据 |
| `contact_id` | int (nullable) | 创建的CRM联系人ID |
| `honeypot_triggered` | bool | 是否触发蜜罐 |
| `success` | bool | 是否成功 |
| `error_message` | text | 错误信息 |
| `created_at` | datetime | 提交时间 |

---

## 10. 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python) |
| 数据库 | SQLAlchemy + PostgreSQL/SQLite |
| 嵌入方式 | 纯 JavaScript（无外部依赖） |
| 反垃圾 | Honeypot + 内存速率限制 (可替换 Redis) |
| 联系人创建 | 复用 CrmService.create_contact() |

---

> **集成时间**: 5 分钟（创建表单 → 获取代码 → 粘贴到网站）
> **更新日期**: 2026-07-02
