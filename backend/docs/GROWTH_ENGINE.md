# 增长飞轮引擎 — 内容营销 + SEO + 增长分析

> 链客宝增长飞轮（Growth Flywheel）：自动化的内容营销、SEO健康检查和增长分析闭环。
>
> 文档版本: v1.0 | 更新日期: 2026-07-04

---

## 目录

1. [架构概览](#1-架构概览)
2. [内容营销自动化引擎](#2-内容营销自动化引擎)
3. [SEO 健康检查面板](#3-seo-健康检查面板)
4. [增长分析 API](#4-增长分析-api)
5. [与现有系统集成](#5-与现有系统集成)
6. [使用场景与工作流](#6-使用场景与工作流)
7. [扩展指南](#7-扩展指南)
8. [API 参考](#8-api-参考)

---

## 1. 架构概览

增长飞轮由三个核心组件构成，形成「内容生产 → SEO 验证 → 数据反馈」的闭环。

```
┌─────────────────────────────────────────────────────────┐
│                   增长飞轮 (Growth Flywheel)              │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │  内容营销引擎  │ ──▶│  SEO 检查面板 │ ──▶│ 增长分析API │ │
│  │  (自动生产)   │    │  (健康验证)   │    │  (数据度量)  │ │
│  └──────┬───────┘    └──────┬───────┘    └─────┬──────┘ │
│         │                   │                   │        │
│         ▼                   ▼                   ▼        │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │  geo-content/ │    │  sitemap.xml │    │  DAU/MAU   │ │
│  │  Markdown文章  │    │  JSON-LD     │    │  留存/来源  │ │
│  └──────────────┘    └──────────────┘    └────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 文件映射

| 组件 | 文件路径 | 说明 |
|------|---------|------|
| 内容营销引擎 | `backend/app/services/content_marketing_engine.py` | 自动化内容生产服务 |
| SEO 健康检查面板 | `backend/templates/seo_dashboard.html` | SEO 诊断 HTML 面板 |
| 增长分析 API | `backend/app/routers/growth.py` | 增长指标 REST API |
| 本文档 | `backend/docs/GROWTH_ENGINE.md` | 使用说明与架构文档 |

---

## 2. 内容营销自动化引擎

### 2.1 概述

`ContentMarketingEngine` 是一个模板驱动的自动化内容生成服务，支持三大主题：

- **数字名片趋势** (`digital_card_trends`) — AI、NFC、AR 技术在商务对接中的应用趋势
- **企业匹配技巧** (`matching_tips`) — 供需对接实操方法论
- **行业洞察** (`industry_insights`) — 各行业 B2B 合作趋势分析

### 2.2 快速使用

```python
from app.services.content_marketing_engine import ContentMarketingEngine, quick_generate

# 方式一：一键生成
result = quick_generate(topics=["digital_card_trends"], count=2, submit_geo=True)
print(f"生成 {result['generated']} 篇文章")

# 方式二：使用引擎对象
engine = ContentMarketingEngine()
articles = engine.generate_batch(
    topics=["matching_tips", "industry_insights"],
    count_per_topic=1,
    industry="AI",
)
# 保存到 geo-content/
for a in articles:
    print(f"已保存: {a['title']} → {a['filepath']}")

# 提交到 GEO 索引
geo_result = engine.submit_to_geo(articles)
print(f"GEO 索引更新: {geo_result['total_indexed']} 篇")

# 查看统计
stats = engine.get_stats()
print(f"geo-content 目录共 {stats['total_articles']} 篇文章")
```

### 2.3 模板机制

每个主题包含：
- `title_template` — 可包含 `{year}`, `{industry}`, `{count}` 占位符
- `sections` — 6 节结构化正文模板
- `seo_keywords_base` — 基础 SEO 关键词
- `slug_prefix` — URL 友好的 slug 前缀

模板在生成时自动填充：
- 随机行业（从 15 个行业中选取）
- 来自数据库的真实企业案例（或模拟数据）
- 产品特性数据（10 个链客宝核心功能）
- 年份、数字等动态占位符

### 2.4 输出

- 文章以 Markdown 格式写入 `geo-content/` 目录
- 文件名格式: `YYYY-MM-DD-{slug}.md`
- 同时更新 GEO 内容索引 (`data/geo/content/index.json`)

---

## 3. SEO 健康检查面板

### 3.1 概述

SEO 健康检查面板是一个全功能的前端诊断工具，通过浏览器端直接调用端点进行实时检查。

### 3.2 访问方式

```
GET /seo/dashboard
```

返回一个完整的 HTML 页面，无需任何权限认证。

### 3.3 检查项及权重

| 检查项 | ID | 权重 | 检查内容 |
|--------|----|------|---------|
| Sitemap 可访问性 | `sitemap` | 25 | URL 数量、XML 格式、hreflang 链接 |
| Hreflang 正确性 | `hreflang` | 20 | 语言覆盖率 (zh-CN/en/ko) |
| JSON-LD 覆盖率 | `jsonld` | 20 | Organization + WebSite 实体 |
| 核心页面索引状态 | `pages` | 20 | 6 个预渲染页面的 HTTP 状态与 meta 标签 |
| Robots.txt 配置 | `robots` | 15 | Allow/Disallow/Sitemap 声明 |

### 3.4 面板功能

1. **总分显示** — 加权评分 (0-100) + 等级评价 (优秀/良好/一般/较差)
2. **单项详情** — 每项检查的状态、数值、详细说明
3. **改进建议** — 每个检查项的具体优化建议
4. **建议汇总表** — 按优先级排列的待办事项
5. **可视化图表** — 雷达图 + 通过率饼图

---

## 4. 增长分析 API

### 4.1 端点一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/growth/metrics` | 核心增长指标 (DAU/MAU/名片/匹配) |
| GET | `/api/v1/growth/trends` | 增长趋势 (7日/30日/自定义) |
| GET | `/api/v1/growth/sources` | 获客来源分析 |
| GET | `/api/v1/growth/retention` | 留存分析 (月度 Cohort) |
| GET | `/api/v1/growth/overview` | 增长飞轮综合概览 |

### 4.2 指标说明

#### GET /api/v1/growth/metrics

返回当前核心指标及变化率：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "dau": { "value": 1320, "change_rate": 3.2, "series": [...] },
    "mau": { "value": 5600, "change_rate": 1.8, "series": [...] },
    "dau_mau_ratio": 0.236,
    "total_cards": { "value": 2850, "today": 95, "change_rate": 2.1 },
    "total_matches": { "value": 7200, "today": 240, "change_rate": 4.5 }
  }
}
```

#### GET /api/v1/growth/trends?days=30

返回指定天数的趋势序列 + 汇总统计：

- `dau`: 日活跃用户序列
- `card_creations`: 每日名片创建数
- `matches`: 每日匹配数
- `summary`: 总值、日均值、峰值

#### GET /api/v1/growth/sources?days=30

返回获客渠道分布：

| 渠道 | 说明 | 典型占比 |
|------|------|---------|
| organic | 自然搜索 | 32% |
| direct | 直接访问 | 21% |
| social | 社交媒体 | 18% |
| referral | 推荐邀请 | 15% |
| paid | 付费广告 | 8% |
| email | 邮件营销 | 4% |

#### GET /api/v1/growth/retention?months=6

返回月度 Cohort 留存率数据，包含：

- `cohorts`: 每个月的 cohort 数据 (D1/D3/D7/D14/D30)
- `average_retention`: 所有 cohort 平均留存率
- `period`: 分析周期类型 (monthly_cohort)

---

## 5. 与现有系统集成

### 5.1 路由注册

增长分析路由已通过 `domain_routes.py` 注册（在 `get_growth_routers()` 中自动版本化到 `/api/v1/*`）。

SEO 仪表盘路由直接在 `main.py` 注册。

### 5.2 与 GEO 引擎联动

内容营销引擎 (`ContentMarketingEngine`) 与现有 GEO 内容工厂 (`geo_content_generator.py`) 的关系：

```
ContentMarketingEngine           GeoContentFactory
       │                              │
       │  generate_batch()            │
       │  ──── 生成模板文章 ─────────▶ │
       │                              │
       │  submit_to_geo()             │
       │  ──── 更新 index.json ─────▶ │
       │                              │
       │  get_stats()                 │
       │  ──── 查询统计 ──────────────▶│
```

引擎自动将生成的文章写入 `geo-content/` 目录，并同步更新 GEO 的 `index.json` 索引文件。

### 5.3 与 A/B 测试框架集成

增长分析 API 可与 `ab_testing.py` 框架配合使用：

- `growth/metrics` 提供整体增长基线
- `ABTestManager` 提供实验级数据
- 两者结合可评估 A/B 实验对整体增长指标的影响

---

## 6. 使用场景与工作流

### 场景一：每日内容自动化

```
cron job (每日 08:00)
  └─▶ ContentMarketingEngine.generate_batch()  → 3 篇新文章
      └─▶ submit_to_geo()                      → 更新 GEO 索引
          └─▶ SEO 面板检查                      → 确认 sitemap/hreflang 正常
              └─▶ growth/metrics                → 记录当日增长基线
```

### 场景二：SEO 月度审计

```
每月 1 日
  └─▶ 访问 /seo/dashboard                       → 获取完整 SEO 报告
  └─▶ 根据建议汇总表优化                         → 修复发现问题
  └─▶ 重新检查确认                               → 评分提升追踪
```

### 场景三：增长周报

```
每周一
  └─▶ GET /api/v1/growth/trends?days=7          → 周增长趋势
  └─▶ GET /api/v1/growth/sources                → 获客渠道周报
  └─▶ GET /api/v1/growth/retention              → 留存变化
  └─▶ 汇总生成本周增长报告
```

---

## 7. 扩展指南

### 7.1 添加新内容模板

在 `TOPIC_TEMPLATES` 字典中添加新条目：

```python
TOPIC_TEMPLATES["new_topic"] = {
    "title_template": "{industry}行业数字化转型的{count}个关键策略",
    "slug_prefix": "digital-transformation",
    "type": "strategy_guide",
    "description": "...",
    "seo_keywords_base": ["关键词1", "关键词2"],
    "sections": ["## 一、{industry}现状分析", "## 二、...", "## 总结"],
}
```

### 7.2 添加新行业

在 `INDUSTRIES` 列表和 `INDUSTRIES_TO_CN` 映射中同时添加。

### 7.3 扩展增长 API

在 `backend/app/routers/growth.py` 中添加新端点，遵循现有模式（模拟数据 + 清晰文档）。

### 7.4 添加 SEO 检查项

在 `seo_dashboard.html` 的 `CHECKS` 数组中添加新检查项对象：

```javascript
{
    id: 'new_check',
    name: '新检查项名称',
    description: '...',
    endpoint: '/api/...',
    weight: 15,
    test: async () => { /* 实现检查逻辑 */ },
    suggestions: ['建议1', '建议2'],
}
```

---

## 8. API 参考

### 内容营销引擎

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `generate_batch(topics, count_per_topic, industry)` | 主题列表、每主题篇数、行业 | `List[Dict]` 文章元数据 | 批量生成文章 |
| `submit_to_geo(articles)` | 文章列表 | `Dict` 提交结果 | 更新 GEO 索引 |
| `get_stats()` | — | `Dict` 统计信息 | 引擎运行状态 |
| `quick_generate(topics, count, industry, submit_geo)` | 同上 | `Dict` 综合结果 | 一键生成 + 提交 |

### 增长 API (REST)

| 端点 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `GET /api/v1/growth/metrics` | — | DAU/MAU/名片/匹配 | 核心指标 |
| `GET /api/v1/growth/trends` | `days` (7-90) | 时间序列 + 汇总 | 趋势数据 |
| `GET /api/v1/growth/sources` | `days` (1-90) | 渠道分布 | 获客来源 |
| `GET /api/v1/growth/retention` | `months` (3-24) | Cohort 留存 | 留存分析 |
| `GET /api/v1/growth/overview` | — | 综合概览 | 聚合看板 |

### SEO 面板

| 端点 | 说明 |
|------|------|
| `GET /seo/dashboard` | SEO 健康检查 HTML 面板 |

---

*本文档由链客宝增长飞轮引擎自动维护。*
*文档路径: `backend/docs/GROWTH_ENGINE.md`*
