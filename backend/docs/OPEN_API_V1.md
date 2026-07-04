# 链客宝 AI 数字名片 — 开放 API 文档 V1

> **版本**: 1.0.0  
> **更新日期**: 2026-06-26  
> **基础 URL (生产)**: `https://liankebao.top/lkapi/`  
> **基础 URL (开发)**: `http://localhost:8001`  
> **协议**: HTTPS (生产) / HTTP (开发)  
> **数据格式**: JSON (所有请求与响应)  
> **字符编码**: UTF-8  

---

## 目录

1. [接入规范](#1-接入规范)
2. [认证方式](#2-认证方式)
3. [速率限制](#3-速率限制)
4. [名片管理](#4-名片管理)
5. [电子画册桥接](#5-电子画册桥接)
6. [匹配搜索](#6-匹配搜索)
7. [用户认证](#7-用户认证)
8. [微信集成](#8-微信集成)
9. [NFC 写卡](#9-nfc-写卡)
10. [联系人管理 (CRM)](#10-联系人管理-crm)
11. [商机/需求管理](#11-商机需求管理)
12. [产品管理](#12-产品管理)
13. [订单管理](#13-订单管理)
14. [推广分润](#14-推广分润)
15. [信任评分](#15-信任评分)
16. [分析审计](#16-分析审计)
17. [合规审计](#17-合规审计)
18. [AI 对话](#18-ai-对话)
19. [文件存储](#19-文件存储)
20. [冷启动引导](#20-冷启动引导)
21. [开发者门户](#21-开发者门户)
22. [Webhook 事件列表](#22-webhook-事件列表)
23. [错误码说明](#23-错误码说明)
24. [SDK 接入示例](#24-sdk-接入示例)

---

## 1. 接入规范

### 1.1 请求头

| 头部字段 | 必填 | 说明 |
|----------|------|------|
| `Content-Type` | 是 | `application/json` (POST/PUT/PATCH) |
| `Authorization` | 视情况 | `Bearer <JWT_TOKEN>` 或 `X-API-Key <API_KEY>` |
| `Accept-Language` | 否 | 多语言支持: `zh-CN`, `en`, `ko` |

### 1.2 通用响应结构

**成功响应:**

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

**错误响应:**

```json
{
  "detail": "错误描述信息"
}
```

### 1.3 分页参数

所有列表类接口支持以下通用分页参数:

| 参数 | 类型 | 默认 | 范围 | 说明 |
|------|------|------|------|------|
| `page` | int | 1 | ≥1 | 页码 |
| `limit` | int | 20 | 1-100 | 每页条数 |
| `skip` | int | 0 | ≥0 | 偏移量（部分接口使用） |

---

## 2. 认证方式

### 2.1 JWT Bearer Token (推荐)

大多数 API 需要 JWT 认证。通过 `/api/auth/login` 或 `/api/auth/register` 获取 Token。

**请求头:**

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**JWT Payload 结构:**

```json
{
  "sub": "username",
  "user_id": 1,
  "role": "user",
  "iat": 1680000000,
  "exp": 1680086400
}
```

- 算法: HS256
- 过期时间: 24 小时（可通过 `JWT_EXPIRY_HOURS` 环境变量配置）
- Secret: 通过 `JWT_SECRET` 环境变量配置（开发环境默认为 `chainke-dev-secret-key`）

### 2.2 API Key 认证 (开发者)

适用于服务端到服务端的调用。通过开发者门户创建 API Key。

**请求头:**

```
X-API-Key: lk_a1b2c3d4e5f6g7h8...
```

**API Key 等级:**

| 等级 | 速率限制 (次/小时) | 权限范围 | 说明 |
|------|-------------------|----------|------|
| `free` | 100 | read | 免费版 |
| `pro` | 1,000 | read, write | 专业版 |
| `enterprise` | 10,000 | read, write, admin | 企业版 |

---

## 3. 速率限制

| 限制项 | 限制值 | 说明 |
|--------|--------|------|
| API Key 速率 | 依等级 (100~10,000 次/小时) | 按 API Key 维度统计 |
| 匿名访问 | 60 次/分钟 | 未认证请求 |
| 微信登录 | 10 次/分钟 | 防止滥用 |
| AI 生成名片 | 20 次/分钟 | 资源密集型操作 |
| NFC 写卡 | 30 次/分钟 | 物理标签操作 |

超出限制返回 `429 Too Many Requests`:

```json
{
  "detail": "速率限制超限，请稍后重试"
}
```

---

## 4. 名片管理

### 4.1 创建名片

```
POST /api/business-card/cards
```

**请求体 (JSON):**

```json
{
  "user_id": "user_abc123",
  "fields": {
    "name": "张三",
    "company": "链客宝科技有限公司",
    "position": "CEO",
    "phone": "13800138000",
    "email": "zhangsan@liankebao.top",
    "wechat": "zhangsan_wechat",
    "website": "https://liankebao.top",
    "address": "北京市海淀区中关村",
    "description": "专注于企业供需匹配平台",
    "logo": "https://liankebao.top/logo.png",
    "tags": ["科技", "AI", "企业服务"]
  },
  "cover_image": "https://liankebao.top/cover.jpg",
  "album_meta": {}
}
```

**响应示例 (201):**

```json
{
  "id": 1,
  "user_id": "user_abc123",
  "fields": {
    "name": "张三",
    "company": "链客宝科技有限公司",
    "position": "CEO",
    "phone": "13800138000",
    "email": "zhangsan@liankebao.top",
    "wechat": "zhangsan_wechat",
    "website": "https://liankebao.top",
    "address": "北京市海淀区中关村",
    "description": "专注于企业供需匹配平台",
    "logo": "https://liankebao.top/logo.png",
    "tags": ["科技", "AI", "企业服务"]
  },
  "share_token": "a1b2c3d4e5f6g7h8",
  "cover_image": "https://liankebao.top/cover.jpg",
  "album_meta": {},
  "created_at": "2026-06-26T10:00:00Z",
  "updated_at": "2026-06-26T10:00:00Z"
}
```

**错误码:**

| 状态码 | 说明 |
|--------|------|
| 422 | 请求参数校验失败 |

---

### 4.2 获取名片列表

```
GET /api/business-card/cards
```

**查询参数:**

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `user_id` | string | 否 | - | 按用户 ID 筛选 |
| `skip` | int | 否 | 0 | 偏移量 |
| `limit` | int | 否 | 20 | 返回条数 (1-100) |

**响应示例 (200):**

```json
{
  "cards": [
    {
      "id": 1,
      "user_id": "user_abc123",
      "fields": { ... },
      "share_token": "a1b2c3d4e5f6g7h8",
      "cover_image": null,
      "album_meta": {},
      "created_at": "2026-06-26T10:00:00Z",
      "updated_at": "2026-06-26T10:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

---

### 4.3 获取名片详情

```
GET /api/business-card/cards/{card_id}
```

**路径参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `card_id` | int | 是 | 名片 ID |

**响应示例 (200):**

```json
{
  "id": 1,
  "user_id": "user_abc123",
  "fields": { ... },
  "share_token": "a1b2c3d4e5f6g7h8",
  "cover_image": null,
  "album_meta": {},
  "created_at": "2026-06-26T10:00:00Z",
  "updated_at": "2026-06-26T10:00:00Z"
}
```

**错误码:**

| 状态码 | 说明 |
|--------|------|
| 404 | 名片不存在 |

---

### 4.4 更新名片

```
PUT /api/business-card/cards/{card_id}
```

**路径参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `card_id` | int | 是 | 名片 ID |

**请求体 (JSON):**

```json
{
  "fields": {
    "name": "张三(更新)",
    "company": "链客宝科技有限公司",
    "position": "CTO"
  },
  "cover_image": "https://liankebao.top/new-cover.jpg",
  "album_meta": {
    "template": "modern",
    "pages": []
  }
}
```

> 注意: `fields` 为合并更新（仅更新提供的字段，未提供的保留原值）。`cover_image` 和 `album_meta` 为覆盖更新（设为 `null` 可清空）。

**响应示例 (200):**

```json
{
  "id": 1,
  "user_id": "user_abc123",
  "fields": {
    "name": "张三(更新)",
    "company": "链客宝科技有限公司",
    "position": "CTO",
    "phone": "13800138000",
    ...
  },
  "share_token": "a1b2c3d4e5f6g7h8",
  "cover_image": "https://liankebao.top/new-cover.jpg",
  "album_meta": {
    "template": "modern",
    "pages": []
  },
  "created_at": "2026-06-26T10:00:00Z",
  "updated_at": "2026-06-26T12:00:00Z"
}
```

**错误码:**

| 状态码 | 说明 |
|--------|------|
| 404 | 名片不存在 |

---

### 4.5 删除名片

```
DELETE /api/business-card/cards/{card_id}
```

**路径参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `card_id` | int | 是 | 名片 ID |

**响应示例 (200):**

```json
{
  "message": "名片已删除",
  "id": 1
}
```

**错误码:**

| 状态码 | 说明 |
|--------|------|
| 404 | 名片不存在 |

---

### 4.6 AI 生成名片

```
POST /api/business-card/generate-card
```

从用户输入的原始文本中 AI 提取字段，自动生成企业数字名片。

**请求体 (JSON):**

```json
{
  "user_id": "user_abc123",
  "raw_text": "我是张三，链客宝科技有限公司的CEO，电话13800138000，邮箱zhangsan@liankebao.top，我们专注于AI驱动的企业供需匹配平台。公司地址在北京市海淀区中关村。",
  "template": "standard",
  "source": "web_upload"
}
```

**响应示例 (200):**

```json
{
  "card": {
    "id": 2,
    "user_id": "user_abc123",
    "fields": {
      "name": "张三",
      "company": "链客宝科技有限公司",
      "position": "CEO",
      "phone": "13800138000",
      "email": "zhangsan@liankebao.top",
      "wechat": "",
      "website": "",
      "address": "北京市海淀区中关村",
      "description": "专注于AI驱动的企业供需匹配平台",
      "logo": "",
      "tags": []
    },
    "share_token": "b2c3d4e5f6g7h8i9",
    "cover_image": "",
    "album_meta": {
      "template": "standard",
      "auto_generated": true,
      "generated_at": "2026-06-26T10:00:00Z"
    },
    "created_at": "2026-06-26T10:00:00Z",
    "updated_at": "2026-06-26T10:00:00Z"
  },
  "ai_summary": "已从您的输入中提取 6 个字段",
  "suggestions": [
    "建议上传公司 Logo，提升品牌可信度",
    "建议补充微信号，方便客户即时联系"
  ]
}
```

**请求体 Schema:**

```json
{
  "type": "object",
  "required": ["user_id", "raw_text"],
  "properties": {
    "user_id": {
      "type": "string",
      "description": "用户 ID"
    },
    "raw_text": {
      "type": "string",
      "description": "用户输入的原始文本（公司介绍、个人信息等）"
    },
    "template": {
      "type": "string",
      "description": "模板名称",
      "default": "standard"
    },
    "source": {
      "type": "string",
      "description": "来源标识",
      "default": "web_upload"
    }
  }
}
```

**同步钩子:** 生成成功后自动同步至电子画册桥数据存储，`/api/brochures/{userId}` 可立即读取。

---

### 4.7 通过分享令牌获取名片

```
GET /api/business-card/share/{share_token}
```

公开接口，无需认证。用于 H5 分享页面展示名片。

**路径参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `share_token` | string | 是 | 分享令牌 (16 位十六进制字符串) |

**响应示例 (200):**

```json
{
  "id": 1,
  "user_id": "user_abc123",
  "fields": { ... },
  "share_token": "a1b2c3d4e5f6g7h8",
  "created_at": "2026-06-26T10:00:00Z",
  "updated_at": "2026-06-26T10:00:00Z"
}
```

**错误码:**

| 状态码 | 说明 |
|--------|------|
| 404 | 名片不存在或链接已失效 |

---

## 5. 电子画册桥接

### 5.1 获取用户电子画册 (单数路径)

```
GET /api/brochure/{user_id}
```

**路径参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | 是 | 用户 ID |

**响应示例 (200):**

```json
{
  "id": 1,
  "user_id": "user_abc123",
  "title": "链客宝科技有限公司",
  "subtitle": "CEO",
  "contact": {
    "phone": "13800138000",
    "email": "zhangsan@liankebao.top",
    "wechat": "zhangsan_wechat",
    "website": "https://liankebao.top"
  },
  "address": "北京市海淀区中关村",
  "description": "专注于企业供需匹配平台",
  "cover_image": "https://liankebao.top/logo.png",
  "share_token": "a1b2c3d4e5f6g7h8",
  "album_meta": {},
  "pages": [],
  "style": {},
  "created_at": "2026-06-26T10:00:00Z",
  "updated_at": "2026-06-26T10:00:00Z",
  "_source": "sync_store"
}
```

**数据来源优先级:**
1. BROCHURE_SYNC_STORE 内存同步桥（实时同步）
2. 数据库 BusinessCard 表（回退查询）

**错误码:**

| 状态码 | 说明 |
|--------|------|
| 404 | 未找到用户电子画册 |

---

### 5.2 获取用户电子画册 (复数路径, 小程序入口)

```
GET /api/brochures/{user_id}
```

小程序 `brochure/index.js` 调用入口。返回结构与 `/api/brochure/{user_id}` 完全一致。

**路径参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | 是 | 用户 ID |

---

### 5.3 通过分享令牌获取电子画册

```
GET /api/brochure/t/{share_token}
```

公开接口，无需登录。

**路径参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `share_token` | string | 是 | 分享令牌 |

---

## 6. 匹配搜索

### 6.1 需求匹配产品

```
GET /api/matching/needs/{need_id}/products
```

**路径参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `need_id` | int | 是 | 需求名片 ID |

**查询参数:**

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `offset` | int | 否 | 0 | 偏移量 |
| `limit` | int | 否 | 20 | 返回条数 (1-100) |

**响应示例 (200):**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 10,
        "title": "AI 产品经理",
        "description": "负责AI产品设计...",
        "category": "",
        "match_score": 0.85,
        "match_reasons": ["关键词匹配 (3个)"],
        "strategy": "simple"
      }
    ],
    "total": 5,
    "strategy": "simple"
  }
}
```

**匹配策略说明:**

| 策略 | 说明 |
|------|------|
| `dnn` | 三塔 DNN 神经网络匹配（灰度发布） |
| `simple` | 关键词匹配（回退方案） |
| `full_engine` | 完整匹配引擎（旧版兼容） |

---

### 6.2 产品匹配需求

```
GET /api/matching/products/{product_id}/needs
```

**路径参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `product_id` | int | 是 | 产品名片 ID |

查询参数与响应结构与 6.1 一致。

---

### 6.3 刷新匹配索引

```
POST /api/matching/refresh
```

**响应示例 (200):**

```json
{
  "code": 200,
  "message": "匹配索引已刷新",
  "data": {
    "cards_count": 150,
    "status": "ready"
  }
}
```

---

### 6.4 自然语言搜索名片

```
POST /api/matching/search
```

**请求体 (JSON):**

```json
{
  "query": "寻找华东地区的制造业供应商",
  "offset": 0,
  "limit": 20
}
```

**响应示例 (200):**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 15,
        "title": "华东精密制造有限公司",
        "company": "华东精密制造有限公司",
        "position": "销售总监",
        "description": "专业精密零部件制造...",
        "tags": ["制造", "华东"],
        "match_score": 0.92,
        "match_reasons": ["关键词匹配 (4个)"]
      }
    ],
    "total": 12,
    "strategy": "simple",
    "query": "寻找华东地区的制造业供应商"
  }
}
```

---

### 6.5 MMR 多样性匹配

```
POST /api/v1/match/diverse
```

使用 Maximal Marginal Relevance (MMR) 算法在保持相关性的同时最大化结果的多样性。

**请求体 (JSON):**

```json
{
  "query": "寻找AI相关的产品经理",
  "candidates": [
    {
      "id": 1,
      "title": "AI产品经理",
      "description": "负责AI产品设计",
      "category": "科技",
      "fields": {}
    },
    {
      "id": 2,
      "title": "Java开发工程师",
      "description": "后端开发",
      "category": "科技",
      "fields": {}
    },
    {
      "id": 3,
      "title": "AI算法专家",
      "description": "机器学习模型设计",
      "category": "科技",
      "fields": {}
    }
  ],
  "relevance_scores": [0.95, 0.45, 0.88],
  "diversity_weight": 0.3
}
```

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `query` | string | 是 | - | 搜索查询文本 |
| `candidates` | array | 是 | - | 候选匹配项列表 |
| `relevance_scores` | array | 否 | - | 预计算的相关性分数（不提供则自动计算） |
| `diversity_weight` | float | 否 | 0.3 | 多样性权重 λ (0=纯多样性, 1=纯相关性) |

**响应示例 (200):**

```json
{
  "results": [
    {
      "id": 1,
      "title": "AI产品经理",
      "description": "负责AI产品设计",
      "category": "科技",
      "match_score": 0.95,
      "mmr_score": 0.95
    },
    {
      "id": 3,
      "title": "AI算法专家",
      "description": "机器学习模型设计",
      "category": "科技",
      "match_score": 0.88,
      "mmr_score": 0.616
    }
  ],
  "diversity_score": 0.7356,
  "metadata": {
    "strategy": "mmr",
    "total": 3,
    "diversity_weight": 0.3,
    "lambda": 0.3,
    "score_source": "provided",
    "algorithm": "Maximal Marginal Relevance"
  }
}
```

---

## 7. 用户认证

### 7.1 开发环境登录

```
POST /api/auth/login
```

> ⚠️ **开发/测试专用**，生产环境请使用微信小程序登录。

**请求体 (JSON):**

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**预设账号:**

| 用户名 | 密码 | 角色 |
|--------|------|------|
| `admin` | `admin123` | admin |
| `dev` | `dev123` | developer |

**响应示例 (200):**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "username": "admin",
    "role": "admin"
  }
}
```

**错误码:**

| 状态码 | 说明 |
|--------|------|
| 401 | 用户名或密码错误 |

---

### 7.2 用户注册 (H5)

```
POST /api/auth/register
```

**请求体 (JSON):**

```json
{
  "username": "zhangsan",
  "password": "pass123456",
  "name": "张三",
  "phone": "13800138000",
  "company": "链客宝科技有限公司",
  "position": "CEO"
}
```

**参数校验:**

| 字段 | 类型 | 必填 | 长度限制 | 说明 |
|------|------|------|----------|------|
| `username` | string | 是 | 2-64 | 用户名（唯一） |
| `password` | string | 是 | 6-128 | 密码 |
| `name` | string | 否 | ≤64 | 姓名 |
| `phone` | string | 否 | ≤20 | 手机号 |
| `company` | string | 否 | ≤128 | 公司 |
| `position` | string | 否 | ≤64 | 职位 |

**响应示例 (201):**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "zhangsan",
    "name": "张三",
    "phone": "13800138000",
    "company": "链客宝科技有限公司",
    "position": "CEO",
    "role": "user",
    "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=zhangsan",
    "is_deleted": false
  },
  "message": "注册成功"
}
```

**错误码:**

| 状态码 | 说明 |
|--------|------|
| 400 | 用户名已存在 |

---

### 7.3 微信手机号解密

```
POST /api/auth/decrypt-phone
```

**请求体 (JSON):**

```json
{
  "code": "wx_login_code",
  "encrypted_data": "微信加密数据",
  "iv": "加密向量"
}
```

**流程说明:**

1. 小程序端调用 `wx.login()` 获取临时 code
2. 小程序端调用 `wx.getPhoneNumber()` 获取 `encryptedData` 和 `iv`
3. 后端将 code 发送至微信服务器换取 `session_key`
4. 使用 `session_key` AES-CBC 解密得到手机号

**响应示例 (200):**

```json
{
  "phone_number": "+8613800138000",
  "pure_phone_number": "13800138000",
  "country_code": "+86"
}
```

**错误码:**

| 状态码 | 说明 |
|--------|------|
| 400 | 无效 code 或解密失败 |
| 500 | 微信小程序配置缺失 (WX_APPID/WX_SECRET 未设置) |
| 502 | 微信服务请求失败 |

---

## 8. 微信集成

### 8.1 获取 JS-SDK 配置

```
POST /api/wechat/js-config
```

**请求体 (JSON):**

```json
{
  "url": "https://liankebao.top/card/share/abc123"
}
```

> 注意: `url` 需去除 # 及其后面的部分

**响应示例 (200):**

```json
{
  "appid": "wx_appid_xxx",
  "noncestr": "随机字符串",
  "timestamp": 1680000000,
  "signature": "SHA1签名"
}
```

---

### 8.2 网页授权登录

```
POST /api/wechat/oauth/login
```

**请求体 (JSON):**

```json
{
  "code": "微信回调URL中的授权code",
  "state": "自定义状态参数（可选）"
}
```

**响应示例 (200):**

```json
{
  "openid": "oXz8s5x...",
  "nickname": "张三",
  "sex": 1,
  "province": "北京",
  "city": "海淀",
  "country": "中国",
  "headimgurl": "https://wx.qlogo.cn/...",
  "unionid": "oXz8s5..."
}
```

---

### 8.3 小程序登录

```
POST /api/wechat/miniapp/login
```

**请求体 (JSON):**

```json
{
  "code": "wx.login()获取的临时登录code"
}
```

**响应示例 (200):**

```json
{
  "openid": "oXz8s5x...",
  "session_key": "会话密钥",
  "unionid": "开放平台UnionID"
}
```

> ⚠️ `session_key` 属于敏感数据，请勿直接暴露给前端。

---

## 9. NFC 写卡

### 9.1 绑定名片到 NFC 标签

```
POST /api/nfc/write
```

**请求体 (JSON):**

```json
{
  "card_id": 1,
  "nfc_tag_id": "04:AB:CD:EF:01:23:45"
}
```

**约束:**

- `nfc_tag_id` 必须全局唯一，不可重复绑定
- `card_id` 必须指向一个已存在的 BusinessCard

**响应示例 (201):**

```json
{
  "id": 1,
  "card_id": 1,
  "nfc_tag_id": "04:AB:CD:EF:01:23:45",
  "created_at": "2026-06-26T10:00:00Z",
  "activated_at": null,
  "view_count": 0
}
```

**错误码:**

| 状态码 | 说明 |
|--------|------|
| 404 | 名片不存在 |
| 409 | NFC 标签已被绑定 |

---

### 9.2 通过 NFC 标签读取名片

```
GET /api/nfc/{nfc_tag_id}
```

**路径参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `nfc_tag_id` | string | 是 | NFC 标签唯一标识 (UID) |

**响应示例 (200):**

```json
{
  "binding": {
    "id": 1,
    "card_id": 1,
    "nfc_tag_id": "04:AB:CD:EF:01:23:45",
    "created_at": "2026-06-26T10:00:00Z",
    "activated_at": "2026-06-27T08:00:00Z",
    "view_count": 3
  },
  "card": {
    "id": 1,
    "user_id": "user_abc123",
    "fields": { ... },
    "share_token": "a1b2c3d4e5f6g7h8",
    "cover_image": null
  },
  "redirect_url": "/api/business-card/share/a1b2c3d4e5f6g7h8"
}
```

> 首次读取时自动记录 `activated_at`，每次读取 `view_count` 自增。

**错误码:**

| 状态码 | 说明 |
|--------|------|
| 404 | NFC 标签未绑定任何名片 |

---

### 9.3 列出 NFC 绑定记录

```
GET /api/nfc/cards
```

**查询参数:**

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `skip` | int | 否 | 0 | 跳过记录数 |
| `limit` | int | 否 | 20 | 返回条数 (1-100) |

**响应示例 (200):**

```json
{
  "bindings": [
    {
      "binding": {
        "id": 1,
        "card_id": 1,
        "nfc_tag_id": "04:AB:CD:EF:01:23:45",
        "created_at": "...",
        "activated_at": "...",
        "view_count": 3
      },
      "card": {
        "id": 1,
        "user_id": "user_abc123",
        "fields": { ... },
        "share_token": "a1b2c3d4e5f6g7h8"
      }
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

---

## 10. 联系人管理 (CRM)

### 10.1 获取联系人列表

```
GET /api/contacts
```

**查询参数:**

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `owner_id` | int | 是 | - | 所属用户 ID |
| `search` | string | 否 | - | 搜索关键词（姓名/电话/公司） |
| `tags` | string | 否 | - | 按标签筛选（逗号分隔） |
| `tag` | string | 否 | - | 单标签精确匹配（向后兼容） |
| `page` | int | 否 | 1 | 页码 |
| `limit` | int | 否 | 20 | 每页条数 (1-100) |

**响应示例 (200):**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "owner_id": 1,
        "name": "李四",
        "phone": "13900139000",
        "wechat_id": "lisi_wx",
        "company": "某科技有限公司",
        "position": "技术总监",
        "email": "lisi@example.com",
        "notes": "潜在客户",
        "tags": ["科技", "潜在客户"],
        "source": "manual",
        "created_at": "...",
        "updated_at": "..."
      }
    ]
  }
}
```

---

### 10.2 创建联系人

```
POST /api/contacts
```

**请求体 (JSON):**

```json
{
  "name": "李四",
  "owner_id": 1,
  "phone": "13900139000",
  "wechat_id": "lisi_wx",
  "company": "某科技有限公司",
  "position": "技术总监",
  "email": "lisi@example.com",
  "notes": "潜在客户",
  "tags": "科技,潜在客户",
  "source": "manual"
}
```

**响应示例 (201):**

```json
{
  "code": 0,
  "message": "创建成功",
  "data": { ... }
}
```

---

### 10.3 搜索联系人

```
GET /api/contacts/search
```

**查询参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `q` | string | 是 | 搜索关键词 (≥1字符) |
| `owner_id` | int | 是 | 所属用户 ID |
| `page` | int | 否 | 页码 (默认 1) |
| `limit` | int | 否 | 每页条数 (默认 20) |

支持 FTS 搜索: 姓名/电话/微信号/公司/职位/邮箱/备注。

---

### 10.4 获取标签列表

```
GET /api/contacts/tags?owner_id=1
```

**响应示例 (200):**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "tags": ["科技", "潜在客户", "VIP", "战略合作"]
  }
}
```

---

### 10.5 获取联系人详情

```
GET /api/contacts/{contact_id}?owner_id=1
```

**错误码:**

| 状态码 | 说明 |
|--------|------|
| 404 | 联系人不存在 |

---

### 10.6 更新联系人

```
PUT /api/contacts/{contact_id}?owner_id=1
```

---

### 10.7 删除联系人

```
DELETE /api/contacts/{contact_id}?owner_id=1
```

软删除。

---

### 10.8 批量创建联系人

```
POST /api/contacts/batch
```

**请求体 (JSON):**

```json
{
  "owner_id": 1,
  "items": [
    {
      "name": "王五",
      "phone": "13700137000",
      "company": "某贸易公司",
      "position": "经理",
      "tags": "贸易,供应商"
    }
  ]
}
```

最大支持 500 条。

---

### 10.9 生成测试联系人

```
POST /api/contacts/seed
```

**请求体 (JSON):**

```json
{
  "owner_id": 1
}
```

### 10.10 联系人活动列表

```
GET /api/contacts/{contact_id}/activities?owner_id=1&page=1&page_size=20
```

**响应示例 (200):**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 10,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "contact_id": 1,
        "action_type": "call",
        "summary": "电话沟通合作细节",
        "detail": "讨论了...",
        "created_at": "..."
      }
    ]
  }
}
```

### 10.11 创建联系人活动

```
POST /api/contacts/{contact_id}/activities?owner_id=1
```

**请求体 (JSON):**

```json
{
  "action_type": "call",
  "summary": "电话沟通",
  "detail": "详细内容..."
}
```

**action_type 可选值:**

| 值 | 说明 |
|----|------|
| `note` | 备注 |
| `call` | 电话 |
| `meeting` | 会议 |
| `email` | 邮件 |
| `wechat` | 微信 |
| `order` | 订单 |
| `import` | 导入 |

---

## 11. 商机/需求管理

### 11.1 获取需求列表

```
GET /api/needs
```

**查询参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `page` | int | 否 | 页码 (默认 1) |
| `limit` | int | 否 | 每页条数 (默认 20) |
| `owner_id` | int | 否 | 按发布人筛选 |
| `category` | string | 否 | 按分类筛选 |
| `status` | string | 否 | 按状态筛选: open/responding/closed/fulfilled |
| `search` | string | 否 | 搜索关键词 |

---

### 11.2 创建需求

```
POST /api/needs
```

**请求体 (JSON):**

```json
{
  "title": "寻找AI技术合作伙伴",
  "owner_id": 1,
  "description": "我们需要一家专注于NLP技术的AI公司合作",
  "category": "技术合作",
  "budget": 500000.00,
  "contact_name": "张三",
  "contact_phone": "13800138000"
}
```

---

### 11.3 获取需求详情

```
GET /api/needs/{need_id}
```

---

### 11.4 更新需求

```
PUT /api/needs/{need_id}
```

---

### 11.5 删除需求

```
DELETE /api/needs/{need_id}
```

---

### 11.6 响应需求

```
POST /api/needs/{need_id}/respond
```

将状态改为 `responding`。

---

### 11.7 完成需求

```
POST /api/needs/{need_id}/fulfill
```

将状态改为 `fulfilled`。

---

### 11.8 关闭需求

```
POST /api/needs/{need_id}/close
```

将状态改为 `closed`。

---

## 12. 产品管理

### 12.1 创建产品

```
POST /api/products
```

**请求体 (JSON):**

```json
{
  "name": "AI名片定制服务",
  "price": 999.00,
  "owner_id": 1,
  "description": "为企业提供AI数字名片定制服务",
  "category": "企业服务",
  "images": "[\"https://.../img1.jpg\"]",
  "review_note": "审核备注"
}
```

---

### 12.2 获取产品列表

```
GET /api/products
```

**查询参数:** `page`, `limit`, `owner_id`, `category`, `status` (pending/approved/rejected/archived)

---

### 12.3 获取产品详情

```
GET /api/products/{product_id}
```

---

### 12.4 更新产品

```
PUT /api/products/{product_id}
```

---

### 12.5 更新产品状态

```
PUT /api/products/{product_id}/status
```

**请求体 (JSON):**

```json
{
  "status": "approved"
}
```

可选状态: `approved`, `rejected`, `archived`, `pending`

---

### 12.6 删除产品

```
DELETE /api/products/{product_id}
```

---

## 13. 订单管理

### 13.1 创建订单

```
POST /api/orders
```

**请求体 (JSON):**

```json
{
  "product_id": 1,
  "buyer_id": 2,
  "supplier_id": 1,
  "total_price": 999.00,
  "quantity": 1,
  "promoter_id": null,
  "contact_name": "张三",
  "contact_phone": "13800138000",
  "shipping_address": "北京市海淀区...",
  "note": "请尽快发货"
}
```

---

### 13.2 获取订单列表

```
GET /api/orders
```

**查询参数:** `page`, `limit`, `buyer_id`, `supplier_id`, `status` (pending/paid/shipped/received/cancelled/refunded)

---

### 13.3 获取订单详情

```
GET /api/orders/{order_id}
```

---

### 13.4 更新订单状态

```
PUT /api/orders/{order_id}/status
```

**状态流转:** pending → paid → shipped → received → completed / cancelled / refunded

---

### 13.5 删除订单

```
DELETE /api/orders/{order_id}
```

---

## 14. 推广分润

### 14.1 创建提现申请

```
POST /api/promoter/withdrawals
```

**请求体 (JSON):**

```json
{
  "user_id": 1,
  "amount": 500.00,
  "bank_info": "{\"bank\":\"中国银行\",\"account\":\"*****\"}"
}
```

---

### 14.2 获取提现列表

```
GET /api/promoter/withdrawals
```

**查询参数:** `page`, `limit`, `user_id`, `status` (pending/approved/rejected)

---

### 14.3 获取提现详情

```
GET /api/promoter/withdrawals/{withdrawal_id}
```

---

### 14.4 更新提现申请

```
PUT /api/promoter/withdrawals/{withdrawal_id}
```

---

### 14.5 审核提现申请

```
PUT /api/promoter/withdrawals/{withdrawal_id}/review
```

**请求体 (JSON):**

```json
{
  "status": "approved",
  "reviewed_by": 2,
  "review_note": "审核通过"
}
```

---

### 14.6 删除提现申请

```
DELETE /api/promoter/withdrawals/{withdrawal_id}
```

---

## 15. 信任评分

### 15.1 获取信任评分

```
GET /api/trust/score/{user_id}
```

**响应示例 (200):**

```json
{
  "user_id": "user_abc123",
  "total_score": 78.5,
  "tier": "silver",
  "tier_label": "银牌",
  "tier_icon": "🥈",
  "verification_points": 30.0,
  "behavior_points": 35.5,
  "guarantee_points": 13.0,
  "updated_at": "2026-06-26T10:00:00Z"
}
```

**信任等级说明:**

| 等级 | 分值范围 | 匹配级别 |
|------|----------|----------|
| `platinum` | 90-100 | instant (即时匹配) |
| `gold` | 80-89 | instant (即时匹配) |
| `silver` | 60-79 | assisted (辅助匹配) |
| `bronze` | 0-59 | manual (手动匹配) |

---

### 15.2 获取评分细分

```
GET /api/trust/score/{user_id}/breakdown
```

返回三个维度的详细子指标得分。

---

### 15.3 获取行为积分历史

```
GET /api/trust/behavior/{user_id}
```

**查询参数:** `limit`, `offset`, `source`

---

### 15.4 获取担保网络

```
GET /api/trust/network/{user_id}
```

**响应示例 (200):**

```json
{
  "user_id": "user_abc123",
  "as_guarantor": [
    {
      "id": 1,
      "guarantor_id": "user_abc123",
      "guarantee_id": "user_def456",
      "status": "active",
      "weight": 0.8,
      "created_at": "...",
      "expired_at": null
    }
  ],
  "as_guarantee": [],
  "total_score": 78.5,
  "tier": "silver"
}
```

---

### 15.5 创建担保关系

```
POST /api/trust/guarantee
```

**请求体 (JSON):**

```json
{
  "guarantor_id": "user_abc123",
  "guarantee_id": "user_def456",
  "weight": 0.8,
  "expired_at": "2027-12-31T23:59:59"
}
```

创建后状态为 `pending`，需确认后变为 `active`。

---

### 15.6 确认担保

```
PUT /api/trust/guarantee/{guarantee_id}/confirm
```

---

### 15.7 撤销担保

```
PUT /api/trust/guarantee/{guarantee_id}/revoke
```

---

### 15.8 重新计算信任评分

```
POST /api/trust/score/{user_id}/recalculate
```

---

### 15.9 提交互评

```
POST /api/trust/review
```

**请求体 (JSON):**

```json
{
  "reviewee_id": "user_def456",
  "match_id": "match_001",
  "response_speed": 5,
  "cooperation_willingness": 4,
  "info_accuracy": 5,
  "comment": "合作非常愉快，响应迅速"
}
```

---

### 15.10 获取评价列表

```
GET /api/trust/reviews/{user_id}
```

**查询参数:** `page`, `page_size`, `min_rating` (1.0-5.0)

---

### 15.11 提交认证申请

```
POST /api/trust/verify
```

**请求体 (JSON):**

```json
{
  "verify_type": "enterprise",
  "evidence": "营业执照URL..."
}
```

| verify_type | 说明 | 积分 |
|-------------|------|------|
| `email` | 邮箱认证 | +10 |
| `phone` | 手机认证 | +20 |
| `enterprise` | 企业认证 | +50 |
| `wechat` | 微信认证 | +10 |

---

### 15.12 审核认证

```
PUT /api/trust/verify/{verify_id}
```

---

### 15.13 获取匹配级别

```
GET /api/trust/match-level/{user_id}
```

---

### 15.14 批量重算信任评分

```
POST /api/trust/recalculate
```

---

## 16. 分析审计

### 16.1 查询审计日志

```
GET /api/v1/audit/logs
```

**查询参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_id` | string | 按用户 ID 筛选 |
| `action` | string | 按操作类型筛选 |
| `resource_type` | string | 按资源类型筛选 |
| `resource_id` | string | 按资源 ID 筛选 |
| `result` | string | success/failure |
| `date_from` | string | 起始时间 (ISO 格式) |
| `date_to` | string | 截止时间 (ISO 格式) |
| `page` | int | 页码 (默认 1) |
| `page_size` | int | 每页条数 (默认 20) |

---

### 16.2 用户操作历史

```
GET /api/v1/audit/logs/user/{user_id}
```

---

### 16.3 最近操作

```
GET /api/v1/audit/logs/recent
```

**查询参数:** `hours` (默认 24, 最大 720)

---

### 16.4 导出审计日志 CSV

```
GET /api/v1/audit/logs/export
```

返回 `text/csv` 格式文件。

---

### 16.5 清理过期日志

```
DELETE /api/v1/audit/logs/cleanup
```

**查询参数:** `keep_days` (默认 90, 1-365)

---

### 16.6 操作统计

```
GET /api/v1/audit/logs/stats
```

---

## 17. 合规审计

### 17.1 合规检查状态

```
GET /api/compliance/status
```

**响应示例 (200):**

```json
{
  "total": 6,
  "passed": 5,
  "warnings": 1,
  "failed": 0,
  "overall": "warning",
  "items": [
    { "name": "合规报告文件", "status": "pass", "detail": "..." },
    { "name": "微信小程序配置SOP", "status": "pass", "detail": "..." },
    { "name": "微信小程序环境变量", "status": "warning", "detail": "..." }
  ],
  "scanned_at": "2026-06-26T10:00:00Z"
}
```

---

### 17.2 完整合规报告

```
GET /api/compliance/report
```

---

### 17.3 触发合规扫描

```
POST /api/compliance/scan
```

---

## 18. AI 对话

### 18.1 发送消息

```
POST /api/v1/chat
```

**请求体 (JSON):**

```json
{
  "message": "请帮我介绍一下链客宝平台的核心功能",
  "session_id": "session_abc123"
}
```

> `session_id` 可选，不提供时自动生成。

**响应示例 (200):**

```json
{
  "reply": "链客宝平台的核心功能包括：1. AI数字名片...",
  "session_id": "session_abc123"
}
```

**错误码:**

| 状态码 | 说明 |
|--------|------|
| 502 | AI 服务不可用 |
| 504 | AI 服务响应超时 |

---

## 19. 文件存储

### 19.1 上传文件

```
POST /api/storage/upload
```

**请求格式:** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | file | 是 | 要上传的文件 |
| `subdir` | string | 否 | 子目录（如 `user_avatars/`） |

**支持的文件类型:** jpeg/png/gif/webp/svg/bmp, PDF, Office 文档, 纯文本
**文件大小限制:** 10MB

**响应示例 (201):**

```json
{
  "url": "https://storage.liankebao.top/uploads/2026/06/26/abc123.jpg",
  "path": "uploads/2026/06/26/abc123.jpg"
}
```

---

### 19.2 删除文件

```
DELETE /api/storage/{path}
```

### 19.3 获取文件 URL

```
GET /api/storage/{path}
```

---

## 20. 冷启动引导

### 20.1 获取预设模板列表

```
GET /api/v1/onboarding/templates
```

### 20.2 获取三步引导配置

```
GET /api/v1/onboarding/defaults
```

---

## 21. 开发者门户

### 21.1 开发者门户首页

```
GET /api/developer/portal
```

### 21.2 API Key 管理

```
POST   /api/developer/api-keys                  — 创建 API Key
GET    /api/developer/api-keys                  — 查询 API Keys
DELETE /api/developer/api-keys/{key_id}         — 撤销 API Key
POST   /api/developer/api-keys/{key_id}/renew   — 重新生成 API Key
```

**创建 API Key 请求体:**

```json
{
  "name": "我的应用",
  "scopes": ["read", "write"],
  "tier": "pro"
}
```

**创建 API Key 响应:**

```json
{
  "code": 0,
  "message": "API Key 创建成功",
  "data": {
    "key_id": "lk_a1b2c3d4e5f6g7h8",
    "name": "我的应用",
    "key": "raw_api_key_string",
    "key_prefix": "a1b2c3d4",
    "scopes": ["read", "write"],
    "tier": "pro",
    "warning": "请立即保存此Key，之后无法再次查看完整Key"
  }
}
```

> ⚠️ `key` 仅创建时返回一次，请立即保存。

### 21.3 Webhook 订阅管理

```
POST   /api/developer/webhooks                  — 创建 Webhook 订阅
GET    /api/developer/webhooks                  — 查询 Webhook 订阅列表
GET    /api/developer/webhooks/{sub_id}         — 查询单个 Webhook
PUT    /api/developer/webhooks/{sub_id}         — 更新 Webhook
DELETE /api/developer/webhooks/{sub_id}         — 删除 Webhook
POST   /api/developer/webhooks/test             — 发送测试事件
```

**创建 Webhook 请求体:**

```json
{
  "url": "https://your-server.com/webhook/callback",
  "events": ["card.created", "card.viewed", "match.created"],
  "secret": "your_webhook_secret",
  "active": true
}
```

### 21.4 API 文档

```
GET /api/developer/docs             — 返回 OpenAPI 兼容文档
GET /api/developer/docs/swagger     — Swagger UI 交互式页面
```

### 21.5 用量统计

```
GET /api/developer/usage                    — 用量统计
GET /api/developer/usage/timeline           — 用量时间线
GET /api/developer/dashboard                — 开发者控制台概览
```

---

## 22. Webhook 事件列表

### 22.1 事件格式 (CloudEvents v1.0)

所有 Webhook 事件遵循 CloudEvents v1.0 格式:

```json
{
  "specversion": "1.0",
  "id": "evt_a1b2c3d4e5f6g7h8",
  "type": "card.viewed",
  "source": "liankebao/api",
  "time": "2026-06-26T10:00:00.000Z",
  "data": {
    "card_id": 1,
    "user_id": "user_abc123",
    "viewer_id": "user_def456",
    "viewed_at": "2026-06-26T10:00:00Z"
  },
  "datacontenttype": "application/json",
  "subject": "1"
}
```

### 22.2 签名验证

每个 Webhook 请求携带 `X-Liankebao-Signature` 头:

```
X-Liankebao-Signature: sha256=<HMAC-SHA256签名>
```

签名计算方法:

```
signature = HMAC-SHA256(secret, request_body)
```

### 22.3 事件类型完整列表

#### 名片事件

| 事件类型 | 说明 | data 字段 |
|----------|------|-----------|
| `card.created` | 名片创建 | `card_id`, `user_id`, `fields` |
| `card.updated` | 名片更新 | `card_id`, `user_id`, `changes` |
| `card.viewed` | 名片被查看 | `card_id`, `user_id`, `viewer_id`, `viewed_at` |

#### 匹配事件

| 事件类型 | 说明 | data 字段 |
|----------|------|-----------|
| `match.created` | 匹配创建 | `match_id`, `from_user`, `to_user`, `score` |
| `match.accepted` | 匹配接受 | `match_id`, `accepted_by` |
| `match.rejected` | 匹配拒绝 | `match_id`, `rejected_by` |
| `match.completed` | 匹配完成 | `match_id`, `completed_at` |

#### 订单事件

| 事件类型 | 说明 |
|----------|------|
| `order.created` | 订单创建 |
| `order.paid` | 订单支付 |
| `order.shipped` | 订单发货 |
| `order.completed` | 订单完成 |
| `order.cancelled` | 订单取消 |

#### 支付事件

| 事件类型 | 说明 |
|----------|------|
| `payment.succeeded` | 支付成功 |
| `payment.failed` | 支付失败 |
| `payment.refunded` | 支付退款 |

#### 用户事件

| 事件类型 | 说明 |
|----------|------|
| `user.registered` | 用户注册 |
| `user.verified` | 用户认证 |
| `user.trust_changed` | 信任分变更 |

#### 企业事件

| 事件类型 | 说明 |
|----------|------|
| `enterprise.verified` | 企业认证 |
| `enterprise.updated` | 企业信息更新 |

### 22.4 重试策略

| 参数 | 值 |
|------|-----|
| 最大重试次数 | 3 |
| 重试间隔 | 指数退避 (2s, 4s, 8s) |
| 死信队列 | 支持（超过重试次数后投递至死信） |

---

## 23. 错误码说明

### 23.1 HTTP 状态码

| 状态码 | 说明 | 常见原因 |
|--------|------|----------|
| 200 | 请求成功 | - |
| 201 | 创建成功 | POST 资源创建 |
| 400 | 请求参数错误 | 参数校验失败、用户名已存在 |
| 401 | 未认证 | Token 缺失或无效 |
| 403 | 无权限 | API Key 权限不足 |
| 404 | 资源不存在 | 名片/联系人/订单等不存在 |
| 409 | 资源冲突 | NFC 标签重复绑定、重复评价 |
| 422 | 参数校验失败 | 字段格式错误、必填字段缺失 |
| 429 | 速率限制超限 | 请求过于频繁 |
| 500 | 服务器内部错误 | 模块未安装、数据库异常 |
| 502 | 上游服务异常 | 微信服务、AI 服务不可用 |
| 504 | 上游服务超时 | AI 服务响应超时 |

### 23.2 业务错误码

返回在响应体 `detail` 字段中的常见错误消息:

| 错误消息 | 说明 |
|----------|------|
| `名片不存在` | 指定 card_id 无对应记录 |
| `名片不存在或链接已失效` | share_token 无效或已过期 |
| `用户名已存在` | 注册时用户名被占用 |
| `NFC 标签已被绑定` | nfc_tag_id 已被其他名片占用 |
| `您已评价过本次匹配` | 同一 match 不可重复评价 |
| `无效事件类型` | Webhook 订阅的事件类型不存在 |
| `AI服务不可用` | 后端 AI 对话服务连接失败 |
| `contacts 模块未安装` | 对应 feature 模块未加载 |
| `速率限制超限，请稍后重试` | 超出 API Key 或 IP 速率限制 |

---

## 24. SDK 接入示例

### 24.1 cURL

**获取 JWT Token:**

```bash
curl -X POST https://liankebao.top/lkapi/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**创建名片:**

```bash
curl -X POST https://liankebao.top/lkapi/api/business-card/cards \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "user_id": "user_abc123",
    "fields": {
      "name": "张三",
      "company": "链客宝科技有限公司",
      "position": "CEO",
      "phone": "13800138000",
      "email": "zhangsan@liankebao.top"
    }
  }'
```

**AI 生成名片:**

```bash
curl -X POST https://liankebao.top/lkapi/api/business-card/generate-card \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "user_id": "user_abc123",
    "raw_text": "我是张三，链客宝科技有限公司CEO，电话13800138000。"
  }'
```

**通过分享令牌获取名片 (无需认证):**

```bash
curl https://liankebao.top/lkapi/api/business-card/share/a1b2c3d4e5f6g7h8
```

**NFC 绑定:**

```bash
curl -X POST https://liankebao.top/lkapi/api/nfc/write \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{"card_id": 1, "nfc_tag_id": "04:AB:CD:EF:01:23:45"}'
```

**自然语言搜索:**

```bash
curl -X POST https://liankebao.top/lkapi/api/matching/search \
  -H "Content-Type: application/json" \
  -d '{"query": "寻找华东地区的制造业供应商", "offset": 0, "limit": 20}'
```

### 24.2 Python (requests)

```python
import requests

BASE_URL = "https://liankebao.top/lkapi"

# 1. 登录获取 Token
def login(username: str, password: str) -> str:
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": username,
        "password": password,
    })
    resp.raise_for_status()
    return resp.json()["token"]

# 2. 创建名片
def create_business_card(token: str, user_id: str, fields: dict) -> dict:
    resp = requests.post(
        f"{BASE_URL}/api/business-card/cards",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "user_id": user_id,
            "fields": fields,
        },
    )
    resp.raise_for_status()
    return resp.json()

# 3. AI 生成名片
def ai_generate_card(token: str, user_id: str, raw_text: str) -> dict:
    resp = requests.post(
        f"{BASE_URL}/api/business-card/generate-card",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "user_id": user_id,
            "raw_text": raw_text,
        },
    )
    resp.raise_for_status()
    return resp.json()

# 4. NFC 绑定
def bind_nfc_card(token: str, card_id: int, nfc_tag_id: str) -> dict:
    resp = requests.post(
        f"{BASE_URL}/api/nfc/write",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "card_id": card_id,
            "nfc_tag_id": nfc_tag_id,
        },
    )
    resp.raise_for_status()
    return resp.json()

# 5. 通过分享令牌获取名片 (无需认证)
def get_card_by_share_token(share_token: str) -> dict:
    resp = requests.get(f"{BASE_URL}/api/business-card/share/{share_token}")
    resp.raise_for_status()
    return resp.json()

# 6. 自然语言搜索名片
def search_cards(query: str, offset: int = 0, limit: int = 20) -> dict:
    resp = requests.post(
        f"{BASE_URL}/api/matching/search",
        json={
            "query": query,
            "offset": offset,
            "limit": limit,
        },
    )
    resp.raise_for_status()
    return resp.json()

# 7. 获取信任评分
def get_trust_score(user_id: str) -> dict:
    resp = requests.get(f"{BASE_URL}/api/trust/score/{user_id}")
    resp.raise_for_status()
    return resp.json()

# 8. 上传文件
def upload_file(token: str, file_path: str, subdir: str = "") -> dict:
    with open(file_path, "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/api/storage/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": f},
            data={"subdir": subdir},
        )
    resp.raise_for_status()
    return resp.json()

# === 使用示例 ===
if __name__ == "__main__":
    # 登录
    token = login("admin", "admin123")
    print(f"Token: {token[:20]}...")

    # AI 生成名片
    result = ai_generate_card(
        token,
        user_id="user_demo",
        raw_text="我是张三，链客宝科技有限公司CEO，电话13800138000，"
                 "邮箱zhangsan@liankebao.top，"
                 "我们专注于AI驱动的企业供需匹配平台。",
    )
    print(f"AI 生成名片 ID: {result['card']['id']}")
    print(f"AI 摘要: {result['ai_summary']}")
    print(f"建议: {result['suggestions']}")
```

### 24.3 JavaScript (fetch)

```javascript
const BASE_URL = "https://liankebao.top/lkapi";

/**
 * 链客宝 API 客户端
 */
class LiankebaoClient {
  constructor(token = null) {
    this.token = token;
  }

  /** 设置认证头 */
  _headers(extra = {}) {
    const headers = { "Content-Type": "application/json", ...extra };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    return headers;
  }

  /** 登录获取 Token */
  async login(username, password) {
    const resp = await fetch(`${BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: this._headers(),
      body: JSON.stringify({ username, password }),
    });
    const data = await resp.json();
    this.token = data.token;
    return data;
  }

  /** 注册 */
  async register(userInfo) {
    const resp = await fetch(`${BASE_URL}/api/auth/register`, {
      method: "POST",
      headers: this._headers(),
      body: JSON.stringify(userInfo),
    });
    const data = await resp.json();
    this.token = data.token;
    return data;
  }

  /** AI 生成名片 */
  async generateCard(userId, rawText, template = "standard") {
    const resp = await fetch(`${BASE_URL}/api/business-card/generate-card`, {
      method: "POST",
      headers: this._headers(),
      body: JSON.stringify({
        user_id: userId,
        raw_text: rawText,
        template,
      }),
    });
    return resp.json();
  }

  /** 创建名片 */
  async createCard(userId, fields) {
    const resp = await fetch(`${BASE_URL}/api/business-card/cards`, {
      method: "POST",
      headers: this._headers(),
      body: JSON.stringify({ user_id: userId, fields }),
    });
    return resp.json();
  }

  /** 获取名片列表 */
  async listCards(userId = null, skip = 0, limit = 20) {
    const params = new URLSearchParams({ skip, limit });
    if (userId) params.set("user_id", userId);
    const resp = await fetch(`${BASE_URL}/api/business-card/cards?${params}`, {
      headers: this._headers(),
    });
    return resp.json();
  }

  /** 获取名片详情 */
  async getCard(cardId) {
    const resp = await fetch(`${BASE_URL}/api/business-card/cards/${cardId}`, {
      headers: this._headers(),
    });
    return resp.json();
  }

  /** 更新名片 */
  async updateCard(cardId, updates) {
    const resp = await fetch(`${BASE_URL}/api/business-card/cards/${cardId}`, {
      method: "PUT",
      headers: this._headers(),
      body: JSON.stringify(updates),
    });
    return resp.json();
  }

  /** 删除名片 */
  async deleteCard(cardId) {
    const resp = await fetch(`${BASE_URL}/api/business-card/cards/${cardId}`, {
      method: "DELETE",
      headers: this._headers(),
    });
    return resp.json();
  }

  /** 通过分享令牌获取名片 (无需认证) */
  async getCardByShareToken(shareToken) {
    const resp = await fetch(
      `${BASE_URL}/api/business-card/share/${shareToken}`
    );
    return resp.json();
  }

  /** NFC 绑定 */
  async bindNfc(cardId, nfcTagId) {
    const resp = await fetch(`${BASE_URL}/api/nfc/write`, {
      method: "POST",
      headers: this._headers(),
      body: JSON.stringify({ card_id: cardId, nfc_tag_id: nfcTagId }),
    });
    return resp.json();
  }

  /** 自然语言搜索 */
  async search(query, offset = 0, limit = 20) {
    const resp = await fetch(`${BASE_URL}/api/matching/search`, {
      method: "POST",
      headers: this._headers(),
      body: JSON.stringify({ query, offset, limit }),
    });
    return resp.json();
  }

  /** 上传文件 */
  async uploadFile(file, subdir = "") {
    const formData = new FormData();
    formData.append("file", file);
    if (subdir) formData.append("subdir", subdir);
    const resp = await fetch(`${BASE_URL}/api/storage/upload`, {
      method: "POST",
      headers: this.token
        ? { Authorization: `Bearer ${this.token}` }
        : undefined,
      body: formData,
    });
    return resp.json();
  }

  /** AI 对话 */
  async chat(message, sessionId = null) {
    const resp = await fetch(`${BASE_URL}/api/v1/chat`, {
      method: "POST",
      headers: this._headers(),
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    return resp.json();
  }
}

// === 使用示例 ===
async function main() {
  const client = new LiankebaoClient();

  // 登录
  await client.login("admin", "admin123");
  console.log("登录成功");

  // AI 生成名片
  const card = await client.generateCard(
    "user_demo",
    "我是张三，链客宝科技有限公司CEO，电话13800138000"
  );
  console.log(`名片 ID: ${card.card.id}`);
  console.log(`分享链接: ${BASE_URL}/api/business-card/share/${card.card.share_token}`);

  // 搜索
  const results = await client.search("科技公司 CEO");
  console.log(`找到 ${results.data.total} 个结果`);
}

main().catch(console.error);
```

---

## 附录 A: 接口概览表

| 分类 | 方法 | 端点 | 说明 |
|------|------|------|------|
| 名片管理 | POST | `/api/business-card/cards` | 创建名片 |
| 名片管理 | GET | `/api/business-card/cards` | 获取名片列表 |
| 名片管理 | GET | `/api/business-card/cards/{id}` | 获取名片详情 |
| 名片管理 | PUT | `/api/business-card/cards/{id}` | 更新名片 |
| 名片管理 | DELETE | `/api/business-card/cards/{id}` | 删除名片 |
| 名片管理 | POST | `/api/business-card/generate-card` | AI 生成名片 |
| 名片管理 | GET | `/api/business-card/share/{token}` | 分享令牌获取名片 |
| 电子画册 | GET | `/api/brochure/{user_id}` | 获取电子画册 |
| 电子画册 | GET | `/api/brochures/{user_id}` | 电子画册(小程序) |
| 电子画册 | GET | `/api/brochure/t/{token}` | 分享令牌获取画册 |
| 匹配搜索 | GET | `/api/matching/needs/{id}/products` | 需求匹配产品 |
| 匹配搜索 | GET | `/api/matching/products/{id}/needs` | 产品匹配需求 |
| 匹配搜索 | POST | `/api/matching/refresh` | 刷新匹配索引 |
| 匹配搜索 | POST | `/api/matching/search` | 自然语言搜索 |
| 匹配搜索 | POST | `/api/v1/match/diverse` | MMR多样性匹配 |
| 用户认证 | POST | `/api/auth/login` | 开发环境登录 |
| 用户认证 | POST | `/api/auth/register` | 用户注册 |
| 用户认证 | POST | `/api/auth/decrypt-phone` | 微信手机号解密 |
| 微信集成 | POST | `/api/wechat/js-config` | JS-SDK配置 |
| 微信集成 | POST | `/api/wechat/oauth/login` | 网页授权登录 |
| 微信集成 | POST | `/api/wechat/miniapp/login` | 小程序登录 |
| NFC | POST | `/api/nfc/write` | NFC标签绑定 |
| NFC | GET | `/api/nfc/{tag_id}` | NFC读取名片 |
| NFC | GET | `/api/nfc/cards` | NFC绑定列表 |
| CRM | GET | `/api/contacts` | 联系人列表 |
| CRM | POST | `/api/contacts` | 创建联系人 |
| CRM | GET | `/api/contacts/search` | 搜索联系人 |
| CRM | GET | `/api/contacts/tags` | 标签列表 |
| CRM | GET | `/api/contacts/{id}` | 联系人详情 |
| CRM | PUT | `/api/contacts/{id}` | 更新联系人 |
| CRM | DELETE | `/api/contacts/{id}` | 删除联系人 |
| CRM | POST | `/api/contacts/batch` | 批量创建联系人 |
| CRM | POST | `/api/contacts/seed` | 生成测试数据 |
| CRM | GET | `/api/contacts/{id}/activities` | 活动列表 |
| CRM | POST | `/api/contacts/{id}/activities` | 创建活动 |
| 需求 | GET/POST | `/api/needs` | 需求列表/创建 |
| 需求 | GET/PUT/DELETE | `/api/needs/{id}` | 需求详情/更新/删除 |
| 需求 | POST | `/api/needs/{id}/respond` | 响应需求 |
| 需求 | POST | `/api/needs/{id}/fulfill` | 完成需求 |
| 需求 | POST | `/api/needs/{id}/close` | 关闭需求 |
| 产品 | GET/POST | `/api/products` | 产品列表/创建 |
| 产品 | GET/PUT/DELETE | `/api/products/{id}` | 产品详情/更新/删除 |
| 产品 | PUT | `/api/products/{id}/status` | 更新产品状态 |
| 订单 | GET/POST | `/api/orders` | 订单列表/创建 |
| 订单 | GET/DELETE | `/api/orders/{id}` | 订单详情/删除 |
| 订单 | PUT | `/api/orders/{id}/status` | 更新订单状态 |
| 推广 | POST | `/api/promoter/withdrawals` | 创建提现 |
| 推广 | GET | `/api/promoter/withdrawals` | 提现列表 |
| 推广 | GET/PUT/DELETE | `/api/promoter/withdrawals/{id}` | 提现详情/更新/删除 |
| 推广 | PUT | `/api/promoter/withdrawals/{id}/review` | 审核提现 |
| 信任评分 | GET | `/api/trust/score/{user_id}` | 信任评分详情 |
| 信任评分 | GET | `/api/trust/score/{user_id}/breakdown` | 评分细分 |
| 信任评分 | GET | `/api/trust/behavior/{user_id}` | 行为积分历史 |
| 信任评分 | GET | `/api/trust/network/{user_id}` | 担保网络 |
| 信任评分 | POST | `/api/trust/guarantee` | 创建担保 |
| 信任评分 | PUT | `/api/trust/guarantee/{id}/confirm` | 确认担保 |
| 信任评分 | PUT | `/api/trust/guarantee/{id}/revoke` | 撤销担保 |
| 信任评分 | POST | `/api/trust/score/{user_id}/recalculate` | 重算评分 |
| 信任评分 | POST | `/api/trust/review` | 提交互评 |
| 信任评分 | GET | `/api/trust/reviews/{user_id}` | 评价列表 |
| 信任评分 | POST | `/api/trust/verify` | 提交认证 |
| 信任评分 | PUT | `/api/trust/verify/{id}` | 审核认证 |
| 信任评分 | GET | `/api/trust/match-level/{user_id}` | 匹配级别 |
| 信任评分 | POST | `/api/trust/recalculate` | 批量重算 |
| 审计 | GET | `/api/v1/audit/logs` | 查询审计日志 |
| 审计 | GET | `/api/v1/audit/logs/user/{id}` | 用户操作历史 |
| 审计 | GET | `/api/v1/audit/logs/recent` | 最近操作 |
| 审计 | GET | `/api/v1/audit/logs/export` | 导出CSV |
| 审计 | DELETE | `/api/v1/audit/logs/cleanup` | 清理日志 |
| 审计 | GET | `/api/v1/audit/logs/stats` | 操作统计 |
| 合规 | GET | `/api/compliance/status` | 合规状态 |
| 合规 | GET | `/api/compliance/report` | 合规报告 |
| 合规 | POST | `/api/compliance/scan` | 触发扫描 |
| AI对话 | POST | `/api/v1/chat` | 发送消息 |
| 文件存储 | POST | `/api/storage/upload` | 上传文件 |
| 文件存储 | GET/DELETE | `/api/storage/{path}` | 获取/删除文件 |
| 引导 | GET | `/api/v1/onboarding/templates` | 预设模板 |
| 引导 | GET | `/api/v1/onboarding/defaults` | 引导配置 |
| 开发者 | GET | `/api/developer/portal` | 开发者门户 |
| 开发者 | POST/GET | `/api/developer/api-keys` | API Key管理 |
| 开发者 | DELETE | `/api/developer/api-keys/{id}` | 撤销API Key |
| 开发者 | POST | `/api/developer/api-keys/{id}/renew` | 续期API Key |
| 开发者 | CRUD | `/api/developer/webhooks` | Webhook管理 |
| 开发者 | POST | `/api/developer/webhooks/test` | 测试Webhook |
| 开发者 | GET | `/api/developer/docs` | API文档 |
| 开发者 | GET | `/api/developer/usage` | 用量统计 |
| 健康检查 | GET | `GET /api/health` | 健康检查 |
| 健康检查 | GET | `GET /health` | 简化健康检查 |

---

> **文档版本**: 1.0.0  
> **最后更新**: 2026-06-26  
> **维护团队**: 链客宝后端团队  
> **问题反馈**: [developer@liankebao.top](mailto:developer@liankebao.top)
