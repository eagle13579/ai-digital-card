# 链客宝 App Store — 插件市场开发指南

## 概述

App Store（插件市场）是链客宝平台的插件分发中心，支持开发者提交插件、管理员审核、用户安装卸载的全流程管理。

### 核心流程

```
开发者提交 → 待审核(pending) → 管理员审核 → 通过(published) / 驳回(rejected)
                ↑                                    |
                └────────── 修改后重新提交 ─────────────┘
```

---

## 一、开发者提交指南

### 1.1 提交插件

**POST /api/v1/app-store/plugins**

请求示例：

```json
{
  "name": "智能数据分析助手",
  "description": "基于 AI 的数据分析插件，自动生成报表",
  "category": "analytics",
  "price": 0,
  "icon_url": "https://cdn.example.com/plugins/analytics-icon.png",
  "tags": "数据分析, AI, 报表",
  "homepage_url": "https://github.com/example/analytics-plugin"
}
```

参数说明：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 插件名称（1-128字符） |
| description | string | 否 | 插件描述 |
| category | string | 是 | 分类: tools/analytics/automation/communication/ai/custom |
| price | float | 否 | 价格（0=免费，默认0） |
| icon_url | string | 否 | 图标 URL |
| tags | string | 否 | 标签（逗号分隔） |
| homepage_url | string | 否 | 项目主页 |

### 1.2 发布新版本

**POST /api/v1/app-store/plugins/{id}/versions**

```json
{
  "version": "1.2.0",
  "changelog": "新增：数据导出功能\n修复：图表渲染 Bug",
  "download_url": "https://cdn.example.com/plugins/v1.2.0.zip",
  "required_api_version": "1.0.0",
  "file_size": 2048576,
  "checksum": "a1b2c3d4e5f6..."
}
```

> 发布新版本后，插件状态自动变为 `pending`，需要重新审核。

### 1.3 更新插件信息

**PUT /api/v1/app-store/plugins/{id}**

仅允许修改 `draft` 或 `rejected` 状态的插件。修改后状态不变。

---

## 二、审核标准

### 2.1 审核流程

1. 开发者提交插件 → 状态变为 `pending`
2. 管理员调用审核接口 → 通过(`approved`) 或 驳回(`rejected`)
3. 通过后状态变为 `published`，驳回后状态变为 `rejected`

### 2.2 审核接口

**POST /api/v1/app-store/plugins/{id}/reviews**

```json
{
  "status": "approved",
  "comments": "功能完整，文档齐全，通过审核"
}
```

### 2.3 审核标准（建议）

| 审核项 | 要求 |
|--------|------|
| 功能完整性 | 插件核心功能可正常运行 |
| 安全性 | 无恶意代码、无数据泄露风险 |
| 兼容性 | 与平台 API 版本兼容 |
| 文档 | 提供基本使用说明 |
| 命名规范 | 名称不侵权、不含敏感词 |

---

## 三、安装与使用

### 3.1 用户安装

**POST /api/v1/app-store/plugins/{id}/install?user_id={userId}**

- 仅能安装 `published` 状态的插件
- 同一用户不能重复安装同个插件

### 3.2 用户卸载

**POST /api/v1/app-store/plugins/{id}/uninstall?user_id={userId}**

- 软删除：标记 `is_active=0`，保留安装记录

### 3.3 沙箱机制

每个插件运行在独立的配置空间：

```
data/plugins/{plugin_id}/{version}/
├── config/
│   └── feature_flags.json   # Feature Flag 配置
├── data/                     # 插件数据
├── cache/                    # 缓存
└── logs/                     # 日志
```

---

## 四、定价与分成说明

### 4.1 定价规则

- **免费插件**: `price=0`，无分成
- **付费插件**: `price>0`，按金额设置（单位：元）

### 4.2 分成说明（骨架实现，未接入支付）

> **注意**: 当前为骨架级实现，**未实现支付与分成功能**。付费插件的价格字段仅用于展示。

计划中的分成比例：

| 角色 | 比例 | 说明 |
|------|------|------|
| 平台 | 30% | 平台运营与技术支撑 |
| 开发者 | 70% | 插件开发收入 |

---

## 五、API 端点速查

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | /api/v1/app-store/plugins | 插件列表 | 公开 |
| GET | /api/v1/app-store/plugins/{id} | 插件详情 | 公开 |
| POST | /api/v1/app-store/plugins | 提交插件 | 开发者 |
| PUT | /api/v1/app-store/plugins/{id} | 更新插件 | 开发者本人 |
| DELETE | /api/v1/app-store/plugins/{id} | 删除插件 | 开发者/管理员 |
| POST | /api/v1/app-store/plugins/{id}/versions | 发布新版本 | 开发者 |
| POST | /api/v1/app-store/plugins/{id}/install | 安装 | 用户 |
| POST | /api/v1/app-store/plugins/{id}/uninstall | 卸载 | 用户 |
| POST | /api/v1/app-store/plugins/{id}/reviews | 审核 | 管理员 |
| GET | /api/v1/app-store/categories | 分类列表 | 公开 |

---

## 六、数据模型

### Plugin （插件主表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| developer_id | Integer | 开发者 ID (FK → users.id) |
| name | String(128) | 插件名称 |
| description | Text | 描述 |
| icon_url | String(512) | 图标 |
| category | String(64) | 分类 |
| version | String(32) | 当前版本 |
| price | Float | 价格 |
| status | String(20) | draft/pending/review/published/rejected |
| install_count | Integer | 安装次数 |
| rating | Float | 评分 |
| rating_count | Integer | 评分人数 |

### PluginVersion （版本表）

| 字段 | 类型 | 说明 |
|------|------|------|
| plugin_id | Integer | FK |
| version | String(32) | 版本号 |
| changelog | Text | 更新日志 |
| download_url | String(512) | 下载地址 |
| required_api_version | String(32) | 最低 API 版本 |
| checksum | String(128) | SHA256 校验和 |

### PluginReview （审核记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| plugin_id | Integer | FK |
| reviewer_id | Integer | 审核员 ID |
| status | String(20) | approved/rejected |
| comments | Text | 审核意见 |

### PluginInstall （安装记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| plugin_id | Integer | FK |
| user_id | Integer | 用户 ID |
| is_active | Integer | 是否已安装 |
| installed_at | DateTime | 安装时间 |
| uninstalled_at | DateTime | 卸载时间 |

---

## 七、开发计划

### 已完成 (骨架)
- [x] 数据模型 (Plugin, PluginVersion, PluginReview, PluginInstall)
- [x] CRUD API（完整插件生命周期）
- [x] 审核流程（提交→审核→发布）
- [x] 安装/卸载 API
- [x] 前端页面（Tailwind CSS）
- [x] 安装引擎（验证+沙箱+Webhook）
- [x] 开发者文档

### 待实现 (后续迭代)
- [ ] 支付与分成系统
- [ ] 插件评分/评论功能（用户评价）
- [ ] OAuth 2.0 认证集成
- [ ] 插件依赖管理
- [ ] CDN 插件分发
- [ ] 插件沙箱运行时（Docker/WebAssembly）
- [ ] 统计看板（安装趋势、收入分析）
- [ ] 插件搜索优化（全文索引）
