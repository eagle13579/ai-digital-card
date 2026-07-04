# 链客宝 — 生态运营文档

> 本文档涵盖 App Store 上线运营、开发者奖励计划、审核流程及社区运营指南。

---

## 目录

1. [App Store 上线运营](#1-app-store-上线运营)
2. [审核流程](#2-审核流程)
3. [开发者奖励计划](#3-开发者奖励计划)
4. [积分兑换规则](#4-积分兑换规则)
5. [社区运营指南](#5-社区运营指南)
6. [API 参考](#6-api-参考)

---

## 1. App Store 上线运营

### 1.1 核心页面

| 页面 | 路由 | 说明 |
|------|------|------|
| 插件市场 | `GET /app-store` | 用户浏览、搜索、安装插件的市场首页 |
| 审核工作台 | `GET /admin/app-store/review` | 管理员审核插件的管理后台 |
| 社区看板 | `GET /community/dashboard` | 社区统计概览、趋势图、排行榜 |

### 1.2 插件生命周期

```
draft → pending → review → published
                     ↓
                  rejected
```

- **draft**: 开发者创建后未提交审核
- **pending**: 开发者提交新版本后自动进入待审核
- **review**: 管理员标记为审核中
- **published**: 审核通过后自动发布
- **rejected**: 审核不通过，开发者可修改后重新提交

### 1.3 插件分类

| 分类 slug | 名称 | 说明 |
|-----------|------|------|
| `tools` | Tools | 工具类插件 |
| `analytics` | Analytics | 数据分析插件 |
| `automation` | Automation | 自动化插件 |
| `communication` | Communication | 通讯类插件 |
| `ai` | AI | AI 能力插件 |
| `custom` | Custom | 自定义插件 |

### 1.4 市场前端功能

- **搜索**: 按名称、描述、标签模糊搜索
- **分类筛选**: 按六大分类过滤
- **排序**: 最新发布 / 最多安装 / 最高评分 / 价格
- **插件详情**: 展示描述、评分、安装量、版本历史、链接
- **一键安装**: 用户输入 ID 即可安装插件

---

## 2. 审核流程

### 2.1 审核入口

管理员访问 `GET /admin/app-store/review` 进入审核工作台。

### 2.2 审核操作

| 操作 | 效果 | 说明 |
|------|------|------|
| **通过** | 插件状态 → `published` | 自动发布最新版本 |
| **拒绝** | 插件状态 → `rejected` | 驳回并记录原因 |
| **要求修改** | 插件状态 → `rejected` | 附带修改意见，开发者可重新提交 |

### 2.3 审核标准检查清单

审核员在审核时应逐项检查以下标准：

- [x] **安全性** — 无恶意代码、无敏感权限滥用、无数据泄露风险
- [x] **功能完整性** — 功能描述与实际一致，核心功能可正常使用
- [x] **文档** — 有基本使用说明和配置文档（README / 文档链接）
- [x] **兼容性** — 满足最低 API 版本要求，兼容主流运行环境
- [x] **版权** — 无版权/商标侵权问题，不侵犯第三方知识产权

### 2.4 审核统计

审核工作台实时展示统计概览：
- 待审核数量
- 审核中数量
- 今日已审数量
- 审核通过率

---

## 3. 开发者奖励计划

### 3.1 奖励类型

| 类型 | 触发条件 | 积分 | 说明 |
|------|----------|------|------|
| **安装奖励** | 每次用户安装插件 | 10 积分/次 | 鼓励插件推广 |
| **质量奖励** | 插件评分 ≥ 4.5 | 100 积分 (一次性) | 鼓励高质量开发 |
| **活动奖励** | 月度最佳插件评选 | 500 积分 (第1名) | 月度社区活动 |
| **额外奖励** | 特殊贡献/活动 | 自定义 | 管理员手动发放 |

### 3.2 积分发放流程

1. 奖励记录被创建时状态为 `pending`（待发放）
2. 开发者可手动触发发放（一键领取）
3. 后台定时任务可批量发放所有待处理奖励
4. 发放后积分进入开发者余额

### 3.3 排行榜

排行榜 `GET /api/app-store/leaderboard` 根据开发者累计积分排序，展示：

| 字段 | 说明 |
|------|------|
| `rank` | 排名 |
| `developer_id` | 开发者 ID |
| `developer_name` | 开发者名称 |
| `total_points` | 总获得积分 |
| `balance` | 可用余额 |
| `plugin_count` | 插件数量 |

---

## 4. 积分兑换规则

### 4.1 兑换选项

| 兑换类型 | 消耗积分 | 获得 | 说明 |
|----------|----------|------|------|
| `api_quota` | 100 积分 | 1,000 次 API 调用 | 用于调用平台 API |
| `promotion` | 100 积分 | 5,000 次推广曝光 | 在平台获得曝光展示 |

### 4.2 兑换 API

```http
POST /api/app-store/developers/{developer_id}/redeem
Content-Type: application/json

{
  "points_spent": 100,
  "redemption_type": "api_quota",
  "description": "兑换 API 调用额度"
}
```

### 4.3 兑换约束

- 积分余额不足时返回 400 错误
- 兑换后积分即时扣除
- 兑换记录永久保存供审计

---

## 5. 社区运营指南

### 5.1 社区看板

社区看板 (`GET /community/dashboard`) 展示以下数据：

**统计卡片:**
- 总插件数 + 本月新增
- 总安装量 + 月增长率
- 活跃开发者数 + 本月新增
- 月度活跃用户数（安装过插件的用户）

**趋势图:**
- 30 天安装量趋势线图（支持 7/30/90 天切换）

**热门插件 Top10:**
- 按安装量排序
- 显示排名、名称、分类、安装量、评分

**开发者排行榜:**
- 积分排行榜 Top 10

**分类分布:**
- 各分类插件数量及进度条

### 5.2 运营 KPI 建议

| 指标 | 建议目标 | 采集方式 |
|------|----------|----------|
| 月活开发者 | ≥ 10 人 | API `GET /api/app-store/stats/community` |
| 月新增插件 | ≥ 5 个 | API 统计 |
| 安装转化率 | ≥ 20% | 安装量 / 浏览量 |
| 平均评分 | ≥ 4.0 | 插件评分均值 |
| 积分活跃率 | ≥ 30% | 有过兑换的开发者占比 |

### 5.3 月度最佳插件评选

评选流程:
1. 每月 1 日系统自动统计上月所有已发布插件
2. 评分标准：安装量 × 0.3 + 评分 × 0.4 + 增长率 × 0.3
3. 前 3 名获得活动奖励积分
4. 结果在社区看板公示

---

## 6. API 参考

### 6.1 App Store API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/app-store/plugins` | 插件列表（搜索+分类+排序） |
| GET | `/api/app-store/plugins/{id}` | 插件详情（含版本） |
| POST | `/api/app-store/plugins` | 提交插件 |
| PUT | `/api/app-store/plugins/{id}` | 更新插件 |
| DELETE | `/api/app-store/plugins/{id}` | 删除插件 |
| POST | `/api/app-store/plugins/{id}/versions` | 发布新版本 |
| POST | `/api/app-store/plugins/{id}/install` | 安装插件 |
| POST | `/api/app-store/plugins/{id}/uninstall` | 卸载插件 |
| POST | `/api/app-store/plugins/{id}/reviews` | 审核插件 |
| GET | `/api/app-store/categories` | 分类列表 |

### 6.2 开发者奖励 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/app-store/leaderboard` | 开发者积分排行榜 |
| GET | `/api/app-store/developers/{id}/rewards` | 开发者奖励记录 |
| GET | `/api/app-store/developers/{id}/redemptions` | 兑换记录 |
| POST | `/api/app-store/developers/{id}/redeem` | 积分兑换 |
| POST | `/api/app-store/developers/{id}/rewards/issue` | 发放奖励 |
| GET | `/api/app-store/developers/{id}/plugins` | 开发者插件列表 |

### 6.3 社区 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/app-store/stats/community` | 社区统计概览 |

### 6.4 HTML 页面

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/app-store` | 插件市场前端 |
| GET | `/admin/app-store/review` | 审核工作台 |
| GET | `/community/dashboard` | 社区看板 |
| GET | `/developer/dashboard` | 开发者仪表盘 |

---

## 附录

### A. 数据库表结构

| 表名 | 说明 |
|------|------|
| `app_store_plugins` | 插件主表 |
| `app_store_plugin_versions` | 插件版本表 |
| `app_store_plugin_reviews` | 插件审核记录 |
| `app_store_plugin_installs` | 插件安装记录 |
| `developer_rewards` | 开发者奖励记录 |
| `developer_reward_balances` | 开发者积分余额 |
| `reward_redemptions` | 积分兑换记录 |

### B. 常量参考

| 常量 | 值 | 说明 |
|------|-----|------|
| 安装奖励积分 | 10 | 每次安装 |
| 质量奖励阈值 | 4.5 | 评分 ≥ 4.5 |
| 质量奖励积分 | 100 | 一次性奖励 |
| 月度最佳积分 | 500 | 第一名 |
| API 兑换比例 | 1000 次/100 积分 | |
| 曝光兑换比例 | 5000 次/100 积分 | |
