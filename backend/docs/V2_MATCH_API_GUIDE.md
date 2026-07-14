# AI数字名片 — 匹配引擎 V2 前端接入指南

> 本文档面向前端开发者，描述 V2 匹配引擎的 4 个 API 端点的接入方式、请求/响应格式、前端调用示例及常见问题。

---

## 目录

1. [概述](#1-概述)
2. [认证方式](#2-认证方式)
3. [端点速览](#3-端点速览)
4. [① 每日推荐](#1--每日推荐-post-apiv2matchrecommend)
5. [② 多样性推荐](#2--多样性推荐-post-apiv2matchdiverse)
6. [③ 匹配理由解释](#3--匹配理由解释-post-apiv2matchexplain)
7. [④ 引擎状态查询](#4--引擎状态查询-get-apiv2matchstats)
8. [前端调用示例](#8-前端调用示例)
9. [匹配理由解读指南](#9-匹配理由解读指南)
10. [错误码说明](#10-错误码说明)
11. [注意事项](#11-注意事项)

---

## 1. 概述

匹配引擎 V2 相比 V1 的核心升级：

| 能力 | V1 | V2 |
|------|----|----|
| 评分维度 | 单层标签匹配 | **五层综合评分** |
| 评分层 | 标签重叠 | 标签重叠 + 语义相似 + 标签权重 + 行业互补 + 注意力 |
| 协同过滤 | — | ItemBasedCF + UserBasedCF |
| 多样性排序 | — | MMR 算法重排序 |
| 匹配解释 | 无 | 四头注意力可解释性 |
| 推荐源头 | — | 支持标记 `v2_engine` / `collaborative_filtering` |

**五层评分权重：**

| 层名称 | 权重 | 说明 |
|--------|------|------|
| `tag_overlap` | 0.35 | 供需标签重叠度 |
| `vector_semantic` | 0.25 | 语义向量相似度 |
| `tag_weight` | 0.10 | 标签兴趣强度 |
| `industry_complement` | 0.20 | 行业互补分析（10 类供需映射） |
| `attention_score` | 0.10 | 多头注意力匹配（四头） |

**基础 URL：** `https://api.liankebao.top`（生产） / `http://localhost:8201`（开发）

---

## 2. 认证方式

所有 V2 端点均需 Bearer Token 认证。

### 获取 Token

```javascript
// 手机号密码登录
POST /api/auth/login
{
  "phone": "138xxxxxxxx",
  "password": "your_password"
}

// 或微信模拟登录（开发/演示）
POST /api/auth/wx-login
{
  "code": "wx_code_from_miniprogram"
}
```

响应示例：

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "bearer",
  "user": { "id": 1, "name": "张三", ... }
}
```

### 在请求中携带 Token

```http
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
Content-Type: application/json
```

### CSRF 保护

V2 的 `POST` 端点受 CSRF 中间件保护。每次请求前需先获取 CSRF Token 并带上 Cookie。

```javascript
// 1) 获取 CSRF Token
const csrfResp = await fetch('/api/csrf/token');
const { token } = await csrfResp.json();
// CSRF Token 会自动设置在 cookie 中

// 2) 在后续 POST 请求中，cookie 会自动带上
```

> **注意：** CSRF Token 通过 Cookie 自动传递（`Set-Cookie: csrf_token=...`），前端无需手动处理 Header。确保 `credentials: 'include'` 或 `withCredentials: true`。

---

## 3. 端点速览

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v2/match/recommend` | 每日推荐（五层评分 + 协同过滤） |
| `POST` | `/api/v2/match/diverse` | 多样性推荐（关键词 + 向量 + MMR） |
| `POST` | `/api/v2/match/explain` | 匹配理由解释（四头注意力详情） |
| `GET` | `/api/v2/match/stats` | 引擎状态查询 |

---

## ① 每日推荐 — `POST /api/v2/match/recommend`

获取针对当前用户的每日推荐列表，包含五层综合评分和可选的协同过滤结果。

### 请求

```json
{
  "limit": 10,
  "min_score": 0.1,
  "include_cf": true
}
```

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `limit` | integer | 10 | 返回结果数量上限（1–50） |
| `min_score` | float | 0.1 | 最低匹配分数阈值（0.0–1.0） |
| `include_cf` | boolean | true | 是否包含协同过滤推荐结果 |

### 响应

```json
{
  "data": [
    {
      "user_id": 5,
      "user_name": "李**",
      "user_company": "字节**",
      "user_title": "技术总监",
      "user_avatar": "https://...",
      "score": 0.8572,
      "tag_overlap": 0.82,
      "vector_semantic": 0.71,
      "tag_weight": 0.65,
      "industry_complement": 0.90,
      "attention_score": 0.78,
      "common_tags": [
        { "tag": "Python", "type": "provide" },
        { "tag": "AI产品", "type": "need" }
      ],
      "source": "v2_engine"
    }
  ],
  "total": 15,
  "has_more": true,
  "engine_version": "v2.0",
  "timestamp": "2026-07-13T14:22:26.123456"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].user_id` | int | 推荐用户 ID |
| `data[].user_name` | string | 用户名（免费用户脱敏显示：`李**`） |
| `data[].user_company` | string | 公司名（免费用户脱敏显示：`字节**`） |
| `data[].user_title` | string | 职位 |
| `data[].user_avatar` | string | 头像 URL |
| `data[].score` | float | 综合匹配度（0–1） |
| `data[].tag_overlap` | float | 标签重叠评分 |
| `data[].vector_semantic` | float | 语义相似度 |
| `data[].tag_weight` | float | 标签权重评分 |
| `data[].industry_complement` | float | 行业互补评分 |
| `data[].attention_score` | float | 注意力匹配评分 |
| `data[].common_tags` | array | 共同标签列表（tag + type） |
| `data[].source` | string | 推荐来源：`v2_engine` / `collaborative_filtering` |
| `total` | int | 总结果数 |
| `has_more` | bool | 是否有更多结果 |

> ⚠️ **免费用户脱敏规则：** `name` 显示首字+`**`（如`张**`），`company` 显示前两字+`**`（如`阿里**`），`phone` 不显示，`avatar` 可选。

---

## ② 多样性推荐 — `POST /api/v2/match/diverse`

基于关键词+向量的混合搜索，再通过 MMR 算法确保推荐结果的多样性。

### 请求

```json
{
  "query": "技术开发",
  "limit": 10,
  "lambda_param": 0.5,
  "keyword_weight": 0.3,
  "vector_weight": 0.7
}
```

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `query` | string | **必填** | 搜索关键词（1–200 字） |
| `limit` | int | 10 | 返回结果上限（1–50） |
| `lambda_param` | float | 0.5 | MMR 多样性参数：1=完全相关，0=完全多样 |
| `keyword_weight` | float | 0.3 | 关键词搜索权重（0–1） |
| `vector_weight` | float | 0.7 | 向量语义搜索权重（0–1） |

> **lambda_param 使用建议：**
> - `0.5` — 平衡多样性（默认，推荐）
> - `0.2–0.4` — 重视多样性（适合"发现新人脉"页面）
> - `0.6–0.8` — 重视相关性（适合"精准搜索"页面）
> - `1.0` — 完全按相关性（相当于关闭 MMR）

### 响应

```json
{
  "data": [
    {
      "user_id": 8,
      "user_name": "王**",
      "user_company": "腾讯**",
      "user_title": "高级工程师",
      "user_avatar": "https://...",
      "score": 0.6234,
      "keyword_score": 0.5,
      "vector_score": 0.6789,
      "source": "hybrid",
      "tag_overlap": 0.45,
      "vector_semantic": 0.67,
      "tag_weight": 0.30,
      "industry_complement": 0.80,
      "attention_score": 0.55
    }
  ],
  "total": 12,
  "diversity_score": 0.3245,
  "engine_version": "v2.0"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].source` | string | 匹配来源：`hybrid` / `vector_only` |
| `data[].keyword_score` | float | 关键词匹配得分 |
| `data[].vector_score` | float | 向量语义匹配得分 |
| `diversity_score` | float | 整体多样性评价（0–1，越高越多样） |
| `engine_version` | string | 引擎版本 |

---

## ③ 匹配理由解释 — `POST /api/v2/match/explain`

对已推荐的两个用户之间的匹配给出详细的五层评分和四头注意力解释。

### 请求

```json
{
  "target_user_id": 5
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `target_user_id` | int | **必填**，需要解释匹配理由的目标用户 ID |

### 响应

```json
{
  "score": 0.8572,
  "details": {
    "industry_head": {
      "attention": 0.82,
      "weight": 0.40,
      "contribution": 0.328
    },
    "capability_head": {
      "attention": 0.71,
      "weight": 0.30,
      "contribution": 0.213
    },
    "region_head": {
      "attention": 0.65,
      "weight": 0.20,
      "contribution": 0.130
    },
    "hotness_head": {
      "attention": 0.55,
      "weight": 0.10,
      "contribution": 0.055
    }
  },
  "availability": 0.85,
  "features": {
    "user_a": {
      "id": 1,
      "name": "张三",
      "industries": ["互联网", "企业服务"],
      "capabilities": ["Python", "AI", "产品设计"],
      "regions": ["北京"],
      "hotness": 0.75
    },
    "user_b": {
      "id": 5,
      "name": "李四",
      "industries": ["互联网", "金融科技"],
      "capabilities": ["Java", "风控", "数据分析"],
      "regions": ["上海"],
      "hotness": 0.60
    }
  },
  "v2_scores": {
    "score": 0.8572,
    "tag_overlap": 0.82,
    "vector_semantic": 0.71,
    "tag_weight": 0.65,
    "industry_complement": 0.90,
    "attention_score": 0.78
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `score` | float | 综合匹配度 |
| `details` | object | 四头注意力详情（见下表） |
| `availability` | float | 可用性调节系数（0–1） |
| `features` | object | 双方用户特征信息 |
| `v2_scores` | object | V2 五层评分明细 |

**四头注意力（`details`）：**

| 头部名称 | 权重 | 聚焦维度 |
|----------|------|----------|
| `industry_head` | 0.40 | 行业匹配度 |
| `capability_head` | 0.30 | 能力/技能互补度 |
| `region_head` | 0.20 | 地区匹配度 |
| `hotness_head` | 0.10 | 活跃度/热度匹配 |

每头包含：
- `attention` — 该维度的注意力分数（0–1）
- `weight` — 该头在综合注意力中的权重
- `contribution` — 对综合得分的贡献值 = attention × weight

---

## ④ 引擎状态查询 — `GET /api/v2/match/stats`

查询匹配引擎 V2 的当前状态、各层权重、协同过滤引擎状态、能力清单等。

### 请求

```
GET /api/v2/match/stats
Authorization: Bearer <token>
```

无请求体。

### 响应

```json
{
  "engine_version": "v2.0",
  "status": "running",
  "layers": [
    {
      "name": "tag_overlap",
      "weight": 0.35,
      "description": "标签重叠评分 — 供需标签匹配度",
      "status": "active"
    },
    {
      "name": "vector_semantic",
      "weight": 0.25,
      "description": "语义相似度 — 向量语义匹配",
      "status": "active"
    },
    {
      "name": "tag_weight",
      "weight": 0.10,
      "description": "标签权重评分 — 标签兴趣强度匹配",
      "status": "active"
    },
    {
      "name": "industry_complement",
      "weight": 0.20,
      "description": "行业互补分析 — 10类行业供需映射",
      "status": "active"
    },
    {
      "name": "attention_score",
      "weight": 0.10,
      "description": "多头注意力匹配 — 行业/能力/地区/热度四头",
      "status": "active"
    }
  ],
  "cf_engines": {
    "item_based_cf": {
      "status": "active",
      "stats": {
        "num_targets": 9,
        "num_interactions": 18,
        "num_similar_pairs": 72
      }
    },
    "user_based_cf": {
      "status": "active",
      "num_users": 15
    }
  },
  "capabilities": [
    "五层综合评分引擎 (V2)",
    "头部注意力匹配 (四头: 行业/能力/地区/热度)",
    "MMR 多样性重排序 (最大边际相关性)",
    "ItemBasedCF 协同过滤 (基于匹配历史)",
    "UserBasedCF 协同过滤 (基于标签相似度)",
    "行业互补分析 (10类行业供需映射)",
    "混合搜索 (关键词 + 向量语义)",
    "反馈闭环 (click/unlock/ignore/rate)",
    "在线学习 (Online Learning Pipeline)",
    "三塔模型推理 (User/Enterprise/Behavior Tower)",
    "向量语义搜索 (VectorSearchEngine)",
    "匹配理由可解释性 (Explain API)"
  ],
  "stats": {
    "total_match_records": 180,
    "engine_layers": 5,
    "cf_engines_available": 2,
    "industry_categories": 10,
    "attention_heads": 4,
    "timestamp": "2026-07-13T14:23:36.488620"
  }
}
```

> 此端点常用于前端展示「推荐引擎能力面板」或调试时确认引擎配置。

---

## 8. 前端调用示例

### 每日推荐页面

```javascript
const API_BASE = 'https://api.liankebao.top';

async function getDailyRecommendations() {
  const response = await fetch(`${API_BASE}/api/v2/match/recommend`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getToken()}`,
      'Content-Type': 'application/json',
    },
    credentials: 'include',           // ← 重要：携带 CSRF Cookie
    body: JSON.stringify({
      limit: 20,
      min_score: 0.1,
      include_cf: true,
    }),
  });

  if (!response.ok) {
    handleError(response.status);
    return;
  }

  const data = await response.json();
  renderRecommendations(data.data);
}

function renderRecommendations(items) {
  items.forEach(item => {
    // 五层评分可视化
    const layers = {
      '标签匹配': item.tag_overlap,
      '语义相似': item.vector_semantic,
      '行业互补': item.industry_complement,
      '活跃匹配': item.attention_score,
    };

    console.log(`${item.user_name} — 综合得分: ${(item.score * 100).toFixed(1)}%`);

    // 标记推荐来源
    if (item.source === 'collaborative_filtering') {
      console.log('  ↳ 基于协同过滤推荐（和你匹配过的人有共同偏好）');
    }
  });
}
```

### 多样性搜索页

```javascript
async function searchWithDiversity(query) {
  const response = await fetch(`${API_BASE}/api/v2/match/diverse`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getToken()}`,
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      query,
      limit: 20,
      lambda_param: 0.4,    // 偏多样性
      keyword_weight: 0.3,
      vector_weight: 0.7,
    }),
  });

  const data = await response.json();
  return data;
}
```

### 匹配理由弹窗

```javascript
async function showMatchReason(targetUserId) {
  const response = await fetch(`${API_BASE}/api/v2/match/explain`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getToken()}`,
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ target_user_id: targetUserId }),
  });

  const data = await response.json();

  // 四头注意力可视化
  const attentionHeads = [
    { name: '行业匹配', key: 'industry_head', icon: '🏢' },
    { name: '能力互补', key: 'capability_head', icon: '🔧' },
    { name: '地区匹配', key: 'region_head', icon: '📍' },
    { name: '热度匹配', key: 'hotness_head', icon: '🔥' },
  ];

  const reasonHTML = attentionHeads
    .map(h => {
      const d = data.details[h.key];
      if (!d) return '';
      const pct = (d.contribution * 100).toFixed(0);
      return `<div class="reason-bar">
        <span>${h.icon} ${h.name}</span>
        <div class="bar-bg">
          <div class="bar-fill" style="width:${pct}%"></div>
        </div>
        <span>${pct}%</span>
      </div>`;
    })
    .join('');

  showDialog(`
    <h3>匹配理由 · ${(data.score * 100).toFixed(0)}% 匹配</h3>
    ${reasonHTML}
    <p class="note">可用性系数: ${(data.availability * 100).toFixed(0)}%
    (对方活跃状态对匹配结果的影响)</p>
  `);
}
```

---

## 9. 匹配理由解读指南

### 如何向用户解释「为什么推荐这个人」

| 维度 | 前端文案模板 | 条件 |
|------|-------------|------|
| 标签重叠 | "你们都有 **{标签}** 的标签，兴趣高度契合" | `tag_overlap > 0.5` |
| 语义相似 | "你们的名片描述风格和方向很接近" | `vector_semantic > 0.5` |
| 行业互补 | "你在 **{行业A}**，他/她在 **{行业B}**，正好可以互补合作" | `industry_complement > 0.6` |
| 注意力匹配 | "你们的行业/能力/地区/活跃度全方位匹配" | `attention_score > 0.6` |
| 协同过滤 | "和你交换名片的人也关注了他/她" | `source === 'collaborative_filtering'` |

### 评分区间释义

| 综合得分 | 评级 | 前端展示 |
|----------|------|----------|
| 0.8–1.0 | ⭐ 极佳匹配 | 强烈推荐 |
| 0.6–0.8 | 👍 良好匹配 | 值得了解 |
| 0.4–0.6 | 🔍 普通匹配 | 可能感兴趣 |
| 0.1–0.4 | 👀 弱匹配 | 探索发现 |
| < 0.1 | — | 不展示（低于阈值） |

### 四头注意力解读

- **行业头（40%权重）**：双方是否在同行业或上下游行业。如果此头部 attention 高，说明行业方向上高度匹配。
- **能力头（30%权重）**：双方的技能标签是互补还是重叠。互补型匹配（你的需要 = 对方提供）比重叠型更有价值。
- **地区头（20%权重）**：同一地区或相近地区的匹配，有利于线下见面合作。
- **热度头（10%权重）**：双方在平台上的活跃程度是否匹配。活跃度差距过大会降低匹配质量。

---

## 10. 错误码说明

| HTTP 状态码 | 错误详情 | 原因 | 前端处理 |
|------------|----------|------|----------|
| `401` | 未认证 | Token 缺失或过期 | 重定向到登录页 |
| `403` | CSRF token missing | CSRF Cookie 未携带 | 先调用 `/api/csrf/token` |
| `404` | 目标用户不存在 | `target_user_id` 无效 | 提示"该用户不存在" |
| `422` | 请求体验证失败 | 参数类型/范围错误 | 根据 `detail` 字段提示具体字段 |
| `429` | 请求频率超限 | 超出资费配额 | 提示"请求过多，请稍后再试" |
| `500` | Internal Server Error | 服务端异常 | 提示"系统繁忙，请稍后重试" |

### 常见 422 错误

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "query"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

> 端点 `/api/v2/match/diverse` 的 `query` 字段为必填，为空时返回 422。

---

## 11. 注意事项

### 免费/付费会员差异

| 行为 | 免费用户 | 付费会员（gold / diamond / board） |
|------|---------|-----------------------------------|
| 姓名显示 | 脱敏（张**） | 完整显示 |
| 公司显示 | 脱敏（字节**） | 完整显示 |
| 手机号 | 不可见 | 可见 |

### 数据脱敏

免费用户看到的推荐结果中的 `user_name` 和 `user_company` 会自动脱敏：

```
张三 → 张**
字节跳动 → 字节**
```

> 后端在响应中自动处理，前端**无需自行脱敏**。

### 性能建议

- **recommend 端点**：建议页面加载时调用，结果可缓存 5–10 分钟
- **diverse 端点**：建议用户主动搜索时调用，不预加载
- **explain 端点**：建议点击"查看匹配理由"时触发，不要批量调用
- **stats 端点**：建议只在管理后台或首次加载时调用，结果可缓存 30 分钟

### 已知问题

> ⚡ **当前（2026-07-13）:** POST 端点存在服务端运行时异常、
> 主要表现为 `vector_search.py` 中 AsyncSession 兼容性问题。
> 不影响 API 契约设计；GET `/api/v2/match/stats` 端点已验证可正常工作。
> 修复中，完成后将同步更新。

---

## 修订记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-13 | v1.0 | 初版 — 匹配引擎 V2 前端接入指南 |
