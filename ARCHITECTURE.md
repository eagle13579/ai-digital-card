# AI数智名片 — 架构文档

> 最后更新: 2026-07-10
> 代码量: 118K Python + 172K TS + 33K测试 + 其他 = 327K+行

---

## 目录结构

```
D:\AI数智名片\
├── _archive/               ← 已归档的旧副本（备份、小程序、WebComponent、App）
├── backend/                ← FastAPI 后端 API 服务（378+ 文件）
│   ├── run.py              FastAPI 入口（主力，端口 8002）
│   ├── main.py             已废弃，保留向后兼容跳转
│   ├── app/
│   │   ├── __init__.py     create_app() — 中间件注册 + 路由装载
│   │   ├── agents/         Agent 体系（10 AI 员工）
│   │   ├── ai/             AI 引擎（RAG/SAG/Hybrid/Gaia/ModelRegistry）
│   │   ├── crm/            CRM 模块（营销自动化 + 客户旅程 + 报表）
│   │   ├── models/         数据模型（User/Tenant/AppStore 等）
│   │   ├── routers/        路由层（66+ 文件）
│   │   ├── middleware/     中间件链（15 层）
│   │   ├── services/       服务层
│   │   ├── schemas/        Pydantic 模式
│   │   ├── config.py       全局配置
│   │   ├── database.py     数据库引擎（SQLite/PostgreSQL 自动检测）
│   │   ├── auth_jwt.py     JWT 认证（RS256+HS256 双算法）
│   │   └── i18n/           国际化后端
│   ├── tests/              后端测试（64+ 测试文件, 1100+ 测试函数）
│   ├── scripts/            LLM 微调管线
│   ├── alembic/            数据库迁移
│   └── requirements.txt    依赖
├── frontend/               ← React 19 + Vite 6 前端
│   ├── src/
│   │   ├── __tests__/      Vitest 测试（34 测试）
│   │   ├── api/            API 客户端
│   │   ├── components/     组件库
│   │   ├── hooks/          钩子（useAuth 集中认证）
│   │   ├── i18n/           国际化（14 语言）
│   │   ├── pages/          页面
│   │   ├── styles/         样式（65 行 Token 设计体系）
│   │   └── utils/          工具函数
│   ├── package.json        React 19 + Vite 6 + Tailwind CSS v4
│   └── nginx_html/         Nginx 静态资源
├── mobile/                 ← React Native 脚手架（5 页面 + 导航 + 认证）
│   ├── src/
│   │   ├── screens/        Home / Login / CardDetail / Profile / Settings
│   │   ├── components/     跨平台组件
│   │   ├── hooks/          认证 & 网络
│   │   └── navigation/     React Navigation 路由
│   └── package.json
├── training_data/          ← LLM 微调数据（1,319 条 ChatML）
│   ├── train_data_chatml.jsonl
│   └── train_data_stats.json
├── deploy/                 Nginx 配置 + 部署脚本
├── k8s/                    Kubernetes 编排（10 YAML）
├── k6/                     性能测试
├── e2e/                    E2E 测试（Playwright）
├── docs/                   文档
├── .github/workflows/      GitHub Actions CI（16 工作流）
├── docker-compose.yml      4 服务编排
├── Dockerfile              Docker 构建
└── Makefile                构建命令
```

---

## 端口

| 端口 | 服务 | 说明 |
|:----:|:-----|:------|
| 8002 | FastAPI (run.py) | 后端 API 主力入口 |
| 8200 | Nginx | 统一接入层（生产） |
| 8202 | AI 微服务 | 画册/AI 推理服务（规划） |
| 6379 | Redis | 限流后端 + 缓存 |
| 5173 | Vite Dev Server | 前端开发服务器（备用） |
| 3000 | Vite Dev Server | 前端开发服务器（vite.config 配置） |

---

## 后端架构 (FastAPI :8002)

### 框架 & 基础设施

| 组件 | 技术栈 |
|:-----|:--------|
| Web 框架 | FastAPI + Pydantic v2 |
| ORM | SQLAlchemy 2.0 (async) |
| 数据库驱动 | aiosqlite (开发) / asyncpg (生产) |
| 认证 | JWT RS256+HS256 双算法, 生产启动强校验 |
| 中间件 | 15 层链式处理 |
| 限流 | Redis 三级分流 (anonymous/standard/enterprise) |
| 测试 | pytest (64+ 测试文件, 1100+ 测试函数) |

### 中间件链 (15 层已注册)

```
Metrics → Tenant → ApiKey → RBAC → RateLimit → I18n →
RequestID → SecurityHeaders → APIVersionRewrite → IPRateLimit →
CORS → Csrf → Logging → Audit → UsageLimit
```

| # | 中间件 | 作用 |
|:-:|:-------|:-----|
| 1 | MetricsMiddleware | APM / Prometheus 监控指标 |
| 2 | TenantMiddleware | 多租户数据隔离（ContextVar 注入） |
| 3 | ApiKeyMiddleware | API Key 认证 |
| 4 | RBACMiddleware | 基于角色的访问控制 |
| 5 | RateLimiterMiddleware | 三级分层限流（Redis 后端） |
| 6 | I18nMiddleware | 国际化语言检测 |
| 7 | RequestIDMiddleware | 请求追踪 ID 注入 |
| 8 | SecurityHeadersMiddleware | 安全响应头（7 头） |
| 9 | APIVersionRedirectMiddleware | /api/v1/xxx → /api/xxx 重写 |
| 10 | IPRateLimitMiddleware | 基于 IP 的限流（60 req/min） |
| 11 | CORSMiddleware | 跨域资源共享 |
| 12 | CsrfMiddleware | CSRF 防护 |
| 13 | LoggingMiddleware | 请求日志 |
| 14 | AuditMiddleware | 操作审计 |
| 15 | UsageLimitMiddleware | 用量限制 |

### 路由 (66+ 文件)

```
Auth / User / Brochure / CRM / AI / Payment / Match / Team /
Tenant / Webhook / GraphQL / AppStore / AppStoreMarketplace /
Gaia / DesignQA / Developer / Invoice / Message / KnowledgeGraph /
Subscription / Membership / Social / Resource / Analytics /
MetricsDashboard / Health / I18n / Admin / V1 Deprecated /
MiniApp / OAuth / Bridge / Feedback / Bot / Learning / ...
```

### AI 引擎 (23 模块)

| 模块 | 路径 | 说明 |
|:-----|:-----|:------|
| RAG 管道 | `app/ai/rag_pipeline.py` | 检索增强生成 |
| SAG 管道 | `app/ai/sag_pipeline.py` | 语义增强生成 |
| Hybrid 管道 | `app/ai/hybrid_pipeline.py` | RAG + SAG 混合 |
| 管道路由器 | `app/ai/pipeline_router.py` | 三管道智能路由 |
| **盖娅进化大脑** | `app/ai/gaia_evolution_brain.py` | 复盘提炼 + 权重进化 |
| 盖娅飞轮 | `app/ai/gaia_flywheel.py` | 持续学习循环 |
| 盖娅训练器 | `app/ai/gaia_trainer.py` | 模型训练管理 |
| ModelRegistry | `app/ai/gateway/model_registry.py` | 多模型降级链 (DeepSeek→Ollama→Cache) |
| 向量搜索 | `app/ai/vector_search.py` | M3E Embedding 向量检索 |
| OCR | `app/ai/ocr.py` | PaddleOCR 文字识别 |
| 知识图谱 | `app/ai/knowledge_graph.py` | 知识图谱推理 |
| 推荐引擎 | `app/ai/recommendation.py` | 智能推荐 |
| 写作助手 | `app/ai/writing_assistant.py` | AI 文案生成 |
| MCP 适配器 | `app/ai/mcp_adapter.py` | MCP 协议集成 |
| 在线学习 | `app/ai/online_learning.py` | 在线学习反馈 |
| 反馈闭环 | `app/ai/feedback_loop.py` | 用户反馈处理 |
| A/B 测试 | `app/ai/ab_testing.py` | 实验引擎 |
| 优化引擎 | `app/ai/optimization.py` | 参数优化 |
| 模型服务 | `app/ai/model_serving.py` | 模型部署 |
| Token 定价 | `app/ai/token_pricing.py` | Token 经济 |
| 训练管线 | `app/ai/training_pipeline.py` | 训练流程编排 |
| 提取器 | `app/ai/extractor.py` | 信息提取 |
| Bandit 引擎 | `app/ai/bandit_engine.py` | 多臂赌博机策略 |

### Agent 体系 (10 AI 员工)

| 角色 | 员工代号 | 专长 |
|:-----|:---------|:-----|
| BackendAgent | emp-烛龙 🔥 | 代码审查、API 生成、调试 |
| QAAgent | emp-狴犴 🔍 | 测试生成、覆盖率分析、回归检测 |
| SecurityAgent | emp-獬豸 ⚖️ | 漏洞扫描、合规监控 |
| GrowthAgent | emp-乘黄 📈 | A/B 测试分析、用户行为洞察 |
| KnowledgeAgent | emp-文鳐 📝 | 文档管理、知识库维护 |
| ArchitectureAgent | emp-开明兽 🏛️ | 架构评审、容量规划 |
| DataAgent | emp-计然 📊 | 数据迁移、ETL、数据质量 |
| SREAgent | emp-䑏疏 🔧 | 监控、修复、容量预测 |
| SupportAgent | emp-白泽 👑 | 工单处理、FAQ、问题解答 |
| DesignQAAgent | emp-狴犴 🎨 | 设计评审、无障碍审计、反模式检测 |

架构：BaseAgent → 具体 Agent → Gaia Evolution Brain 集成 → 工具注册器 → 事件处理 → 跨 Agent 委托

已嵌入 3 个核心业务 API: `match/ai_assist/brochure`

### CRM 模块 (5 端点)

| 文件 | 功能 |
|:-----|:------|
| `crm_router.py` | CRM 核心路由 |
| `campaign_router.py` | 营销活动管理 |
| `prediction_router.py` | 销售预测 |
| `marketing_router.py` | 营销自动化（EmailCampaign） |
| `report_router.py` | 管道报表 |
| `crm_service.py` | CRM 服务层 |
| `crm_models.py` | CRM 数据模型 |
| `crm_analytics.py` | CRM 分析 |
| `crm_rbac.py` | CRM 权限控制 |
| `customer_journey.py` | 客户旅程映射 |
| `email_campaign.py` | 邮件营销引擎 |
| `workflow_engine.py` | 工作流引擎 |
| `match_hook.py` | 匹配挂钩 |

### 多租户

- **TenantBase**: 业务模型继承基类（User/Brochure/Page 等）
- **TenantMiddleware**: 从 JWT payload 提取 tenant_id → ContextVar 注入
- **TenantSession**: 自动为所有查询添加 `WHERE tenant_id = ?`
- 支持的套餐: FREE / PRO / ENTERPRISE

### 应用市场

| 端点 | 方法 | 说明 |
|:-----|:-----|:------|
| 1 | `GET /plugins` | 插件列表（分类/搜索/分页） |
| 2 | `GET /plugins/{id}` | 插件详情 + 版本列表 |
| 3 | `POST /plugins` | 开发者提交插件 |
| 4 | `PUT /plugins/{id}` | 更新插件 |
| 5 | `POST /plugins/{id}/install` | 用户安装插件 |
| 6 | `DELETE /plugins/{id}/install` | 卸载插件 |
| 7 | `GET /my-installs` | 当前用户已安装列表 |
| 8 | `POST /plugins/{id}/review` | 用户评价 |
| 9 | `GET /categories` | 分类列表 |

模型: `Plugin` / `PluginVersion` / `PluginReview` / `PluginInstall`

---

## 前端架构 (React 19 + Vite 6)

### 技术栈

| 组件 | 技术 |
|:-----|:-----|
| 框架 | React 19 + TypeScript |
| 构建 | Vite 6（proxy /api → localhost:8002） |
| 样式 | Tailwind CSS v4 + motion（动画） |
| 路由 | react-router-dom v7 |
| 图标 | lucide-react |
| 测试 | vitest + @testing-library/react（34 测试） |
| PWA | Service Worker + manifest.json |

### 设计体系

- **442 行 Token 设计体系**（`styles/design-tokens.ts` 65 行 + `global.css` 174 行 + `rtl.css` 383 行）
- **AI 原生暗色主题** — 冷峻轻奢（Cold Luxury）深蓝黑 + 青绿
- 9 种名片模板（经典/深海/玫瑰金/翡翠/星云/暖阳/烟灰/糖果/森林）

### 国际化

- **14 语言支持**: 中文、英文、法文、德文、西班牙文、葡萄牙文、日文、韩文、俄文、泰文、阿拉伯文、越南文
- 后端 i18n 集成 + RTL 布局支持

### 认证

- `useAuth` Context Provider — 集中认证管理
- JWT 令牌存储、自动刷新、角色控制

---

## 移动端 (React Native)

```
mobile/
├── App.tsx                    入口组件
├── src/
│   ├── screens/               5 页面
│   │   ├── HomeScreen.tsx     首页名片展示
│   │   ├── LoginScreen.tsx    登录
│   │   ├── CardDetailScreen.tsx 名片详情
│   │   ├── ProfileScreen.tsx  个人中心
│   │   └── SettingsScreen.tsx 设置
│   ├── components/            跨平台组件
│   ├── hooks/                 认证 & 网络
│   ├── navigation/            React Navigation
│   ├── api/                   API 客户端
│   └── utils/                 工具函数
├── android/                   Android 原生
├── ios/                       iOS 原生
└── package.json
```

---

## 数据库

### 开发环境
- **SQLite** (`sqlite+aiosqlite:///./data/digital_brochure.db`)
- 不支持并发写入，仅用于本地开发

### 生产环境
- **PostgreSQL** (`postgresql+asyncpg://`)
- 自动检测，基于 `DATABASE_URL` 前缀判断
- 连接池: `pool_size=20`, `max_overflow=10`, `pool_pre_ping=True`
- 连接回收: 3600 秒

### ORM 模型 (26+ 模型)

| 模块 | 模型 |
|:-----|:------|
| 用户 | User, Visitor |
| 名片 | Brochure, Page, Tag |
| 租户 | Tenant (TenantBase) |
| 应用市场 | Plugin, PluginVersion, PluginReview, PluginInstall |
| CRM | Customer, Deal, Campaign, EmailLog |
| AI | GaiaKnowledge, Feedback, ABTest |
| 支付 | Payment, Invoice |
| 团队 | Team, Membership |
| 系统 | Webhook, ApiKey, AuditLog, SocialConnection, UsageCounter |

---

## 部署

### Docker Compose (4 服务)

| 服务 | 镜像 | 端口 | 说明 |
|:-----|:-----|:----:|:-----|
| backend | Dockerfile | 8002 | FastAPI 后端 |
| ai_service | 自定义 | 8202 | AI 推理服务 |
| nginx | nginx:alpine | 8200 | 统一接入层 |
| redis | redis:alpine | 6379 | 限流 + 缓存 |

### Kubernetes (10 YAML)

| 文件 | 说明 |
|:-----|:------|
| `deployment.yaml` | 主部署 |
| `hpa.yaml` | 水平自动扩缩容 |
| `service.yaml` | 服务暴露 |
| `ingress.yaml` | 入口路由 |
| `global-ingress.yaml` | 全局入口 |
| `service-mesh.yaml` | 服务网格 |
| `multi-region.yaml` | 多区域部署 |
| `read-replica.yaml` | 只读副本 |
| `rollback-test.yaml` | 回滚测试 |
| `chaos_experiment.yaml` | 混沌实验 |

### CI/CD (16 GitHub Actions 工作流)

| 工作流 | 说明 |
|:-------|:------|
| `ci.yml` | 持续集成 |
| `deploy.yml` | 部署 |
| `bluegreen-deploy.yml` | 蓝绿部署 |
| `canary.yml` + `canary-ci.yml` | 金丝雀发布 |
| `rollback.yml` | 回滚 |
| `security-scan.yml` | 安全扫描 |
| `soc2-compliance-check.yml` | SOC2 合规检查 |
| `preview.yml` | 预览环境 |
| `e2e.yml` | E2E 测试 |
| `performance.yml` | 性能测试 |
| `a11y.yml` | 无障碍检查 |
| `bizops-ab-deploy.yml` | 业务运营部署 |
| `deploy-model.yml` | 模型部署 |
| `deploy-ssh.yml` | SSH 部署 |
| `learning-cron.yml` | 学习定时任务 |

---

## 安全

### 认证
- JWT RS256+HS256 双算法支持
- 生产环境启动时强制校验 JWT 配置
- API Key 认证（ApiKeyMiddleware）

### 防护
- **CSRF** 中间件防护
- **SecurityHeaders**: 7 个安全响应头 (X-Content-Type-Options, X-Frame-Options, CSP, HSTS, etc.)
- **三级限流**: anonymous (100/min), standard (1000/min), enterprise (10000/min)
- **敏感端点减半**: /auth/*, /payment/* 在上述基础上减半

### 审计
- AuditMiddleware 记录所有 API 操作
- UsageLimitMiddleware 用量限制追踪

### SAST
- Bandit 安全静态分析
- Safety 依赖漏洞扫描
- SOC2 合规自动检查

---

## LLM 微调管线

### 数据准备

| 阶段 | 脚本 | 说明 |
|:-----|:-----|:------|
| 数据提取 | `scripts/prepare_training_data.py` | 从多源提取训练数据 |
| 模型微调 | `scripts/train_lora.py` | LoRA 微调（通过 SSH 在 Mac Mini 上 MLX 训练） |
| 模型部署 | `scripts/deploy_model.py` | 注册到 ModelRegistry |

### 训练数据 (1,319 条 ChatML 记录)

| 来源 | 数量 | 类型 |
|:-----|:----:|:-----|
| uiux_pro_max.jsonl | 714 | instruction |
| components.jsonl | 315 | instruction |
| code_assets_v1.jsonl | 126 | chatml |
| darwin_skill.jsonl | 99 | instruction |
| stripe_clone.jsonl | 47 | instruction |
| design_system.jsonl | 12 | instruction |
| component_library.jsonl | 6 | instruction |

---

## 测试

### 后端测试
- **框架**: pytest
- **范围**: 64+ 测试文件, 1100+ 测试函数
- **覆盖模块**: 认证、API、模型、中间件、AI 引擎、Agent、CRM、支付、多租户、OAuth、限流、向量搜索、Webhook、性能

### 前端测试
- **框架**: vitest + @testing-library/react
- **范围**: 34 测试
- **文件**: api.test.ts, CardPreview.test.tsx, ErrorBoundary.test.tsx, LoadingSkeleton.test.tsx, utils.test.ts

### E2E 测试
- **框架**: Playwright
- **状态**: 已就绪（`e2e/` 目录）

---

## 数据流

### 请求处理流程

```
客户端 → Nginx(:8200) → FastAPI(:8002)
  → [15 层中间件链]
    → Metrics → Tenant → ApiKey → RBAC → RateLimit → I18n
    → RequestID → SecurityHeaders → APIVersionRewrite → IPRateLimit
    → CORS → Csrf → Logging → Audit → UsageLimit
  → 路由器分发 → 服务层
    → AI 引擎 (Gaia/ModelRegistry/RAG/SAG/Hybrid)
    → 数据库 (SQLite/PG)
    → Redis (限流/缓存)
  → 响应返回
```

### AI 请求链路

```
请求 → PipelineRouter
  ├→ RAG Pipeline  (知识库检索 + LLM 生成)
  ├→ SAG Pipeline  (语义增强 + LLM 生成)
  └→ Hybrid Pipeline (RAG + SAG 混合)
      ↓
ModelRegistry (多模型降级)
  ├→ DeepSeek API (primary)
  ├→ Ollama (first fallback)
  └→ Cache (last resort)
      ↓
Gaia Evolution Brain
  ├→ ingest_knowledge() → 知识入库
  ├→ ingest_feedback() → 反馈吸收
  └→ process_evolution_cycle() → 权重进化
```

---

## 架构原则

1. **模块化**: 每个功能域独立模块，循环依赖通过惰性注册避免
2. **可观测性**: Metrics + Audit + Logging + OpenTelemetry
3. **多租户**: TenantBase 继承 + TenantMiddleware 自动隔离
4. **AI 原生**: 10 Agent 员工 + Gaia 进化大脑 + ModelRegistry 降级
5. **安全优先**: JWT 双算法 + CSRF + 三级限流 + Bandit SAST
6. **渐进式增强**: SQLite 开发 → PostgreSQL 生产，自动切换
7. **国际化**: 14 语言前端 + i18n 后端中间件
8. **持续学习**: 反馈闭环 → 在线学习 → LLM 微调管线

---

> 本文档由架构师（emp-开明兽）维护，随代码库演进持续更新。
