# AI数智名片 — 架构全量扫描与审计报告

> 审计日期: 2026-07-07  
> 审计范围: 全项目代码扫描  
> 严重程度分级: **P0** (紧急/阻塞) | **P1** (高/需优先修复) | **P2** (中/需规划修复) | **P3** (低/建议优化)

---

## 目录

1. [项目总体结构与目录职责](#1-项目总体结构与目录职责)
2. [关键配置文件审计](#2-关键配置文件审计)
3. [依赖分析](#3-依赖分析)
4. [数据库模型审计](#4-数据库模型审计)
5. [中间件审计](#5-中间件审计)
6. [路由全景审计](#6-路由全景审计)
7. [AI模块分析](#7-ai模块分析)
8. [前端结构审计](#8-前端结构审计)
9. [小程序结构审计](#9-小程序结构审计)
10. [架构缺陷汇总](#10-架构缺陷汇总)

---

## 1. 项目总体结构与目录职责

```
D:\AI数智名片\
├── backend/           ← FastAPI 后端 API 服务 (378 文件)
│   ├── run.py         ← 入口1: uvicorn → :8002 (ALIAS: "主力入口")
│   ├── main.py        ← 入口2: uvicorn → :8201 (ALIAS: "备用入口")
│   ├── ai_service/    ← 独立 AI 微服务 (Docker 独立部署)
│   ├── alembic/       ← 数据库迁移 (仅2次迁移)
│   ├── app/
│   │   ├── __init__.py    ← create_app() 工厂函数 (434行)
│   │   ├── ai/            ← AI 引擎 (32 文件)
│   │   ├── agents/        ← 多智能体系统 (13 文件)
│   │   ├── broker/        ← 消息代理抽象层
│   │   ├── cache/         ← 缓存抽象层 (Redis/Memory)
│   │   ├── config.py      ← Pydantic Settings (233行)
│   │   ├── connectors/    ← CRM 连接器 (Salesforce/HubSpot + Stub)
│   │   ├── crm/           ← CRM 模块 (11 文件)
│   │   ├── middleware/    ← 中间件 (18 文件)
│   │   ├── models/        ← ORM 模型 (23 文件)
│   │   ├── routers/       ← 路由层 (50+ 文件)
│   │   ├── services/      ← 业务服务层
│   │   └── payment/       ← 支付模块
│   ├── requirements.txt  ← 精简依赖 (41行)
│   └── Dockerfile
├── frontend/          ← React 19 + Vite 6 (7745 文件)
├── miniapp/           ← 微信小程序
├── deploy/            ← 部署配置 (22 文件)
├── k8s/               ← Kubernetes 编排
├── k6/                ← 性能测试
├── e2e/               ← E2E 测试
├── docs/              ← 文档
├── scripts/           ← 工具脚本
├── data/              ← 运行时数据
├── _archive/          ← 已归档旧副本
├── tests/             ← 集成测试
├── .github/           ← GitHub Actions CI
├── docker-compose.yml ← Docker 编排
├── Dockerfile         ← Docker 构建
├── Makefile           ← 构建命令
└── ARCHITECTURE.md    ← 架构文档
```

### 问题

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **P1** | **两个入口点混淆** | `run.py`(:8002) 与 `main.py`(:8201) 功能相同，文档称 8002 为主力、8201 为备用，但 docker-compose.yml 用的是 8201。Makefile 中 `make dev-backend` 启动 8201。架构文档指出 8002 为"实际后端 API（主力入口）"。两条路径产生了维护歧义。 |
| **P2** | ARCHITECTURE.md 落后于代码 | 文档声明 8002 为主力入口，但实际 Docker 和 Makefile 均使用 8201。文档缺少对 Agents 模块、CRM 模块、Gaia 进化大脑等新模块的描述。 |
| **P2** | backend/tests/ 目录未见 | ARCHITECTURE.md 声称有 `backend/tests/`，但项目根有 `tests/`，`backend/` 内无 tests 目录。pytest 配置指向 `backend/tests`，该路径不存在。 |
| **P3** | _archive/ 内容与 miniapp/ 重复 | `_archive/AI数字名片小程序/` 与当前 `miniapp/` 内容重叠，容易混淆。 |

---

## 2. 关键配置文件审计

### 2.1 `.env.example`

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **P0** | **JWT_SECRET 默认值为明文占位符** | `JWT_SECRET=change-me-to-a-random-256-bit-key` — 若开发者忘记修改，JWT 可被任意伪造。 |
| **P1** | `CORS_ORIGINS` 硬编码多个来源 | 包含 `https://liankebao.top` 等多来源，但 `config.py` 中已用 `env` 读取，.env.example 中的硬编码还算可接受；但生产环境确认不足。 |
| **P2** | 多个敏感服务配置为空但仍有 Mock 降级 | 微信支付、支付宝、Sentry DSN 等留空。核心安全隐患在于支付配置缺失时是否有充分的降级处理。 |
| **P3** | `SF_*` 和 `SALESFORCE_*` 双前缀兼容 | 文档中声明双前缀兼容，但仅注释形式存在，缺少自动检测逻辑。 |

### 2.2 `pyproject.toml`

只有 pytest 配置，缺少 `[tool.ruff]` 或 `[mypy]` 配置。42 个 Python 文件但有 0 类型检查配置。

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **P3** | 类型检查配置缺失 | 项目使用 `Mapped`/`mapped_column` 类型注解，但 pyproject.toml 未配置 mypy/pyright。 |

### 2.3 `docker-compose.yml`

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **P1** | **缺少 Redis 和 PostgreSQL 服务** | compose 定义了 backend、ai_service、nginx，但 `volumes` 声明了 `postgres_data` 和 `redis_data` 却没有任何服务使用它们。后端实际使用 SQLite (`sqlite+aiosqlite`)，与声明的 volume 不匹配。 |
| **P2** | ai_service 无 healthcheck | backend 和 nginx 有健康检查，但 AI 微服务没有。 |
| **P2** | backend 无 depends_on 约束 | 没有等待 ai_service 或 redis 就绪的依赖声明。 |
| **P3** | 生产环境使用 SQLite | SQLite 不适合生产并发场景。docker-compose 中有 `postgres_data` volume 暗示意图使用 PostgreSQL，但 DATABASE_URL 未配置。 |

### 2.4 `Makefile`

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **P2** | `make test` 可能失败 | 运行 `cd backend && python -m pytest` 但 `backend/tests/` 目录不存在。 |
| **P3** | 缺少 `make lint-backend` 中 ruff 配置路径 | 直接 `ruff check .` 但未提供 `pyproject.toml` 中的 ruff 配置。 |
| **P3** | `clean-backend` 使用 `find` 命令 | Windows git-bash 下可用，但真实 Linux 环境无问题。 |

### 2.5 `ARCHITECTURE.md`

见第1节问题。

---

## 3. 依赖分析

### 3.1 后端 `requirements.txt` (41行 — 官方依赖)

核心依赖合理：FastAPI, SQLAlchemy, uvicorn, alembic, PyJWT, passlib, pydantic, redis, scikit-learn, numpy, sentence-transformers, strawberry-graphql, opentelemetry。

### 3.2 `requirements_full.txt` (450行 — 严重膨胀)

这是 `pip freeze` 的完整输出，包含了大量与项目无关的包：

| 类别 | 示例包 | 问题 |
|------|--------|------|
| **完全无关** | `akshare`, `tdxpy`, `xtquant`, `yfinance` | 金融/股票数据 API，与本名片项目无关 |
| **完全无关** | `kubernetes` | K8s Python 客户端，项目已有独立 k8s/ 目录，不应是应用依赖 |
| **完全无关** | `mistralai`, `anthropic`, `openai` | 多个 LLM SDK，但项目只用 DeepSeek |
| **完全无关** | `flask*`, `Werkzeug`, `quart` | 使用 FastAPI 但依赖了 Flask 及其生态全家桶 |
| **完全无关** | `sphinx*`, `furo` | 文档生成工具，非运行时依赖 |
| **完全无关** | `ccxt`, `coincurve` | 加密货币交易库 |
| **大量测试工具** | `bandit`, `safety`, `flake8`, `mutmut` | 应放在 dev 依赖 |
| **内部包** | `chainke-auth-service==0.1.0`, `chainke-common==0.1.0` | 这些包在 PyPI 上不存在（私有包），会导致 pip install 失败 |
| **冲突** | `fastapi==0.115.0` vs `strawberry-graphql==0.320.0` | strawberry-graphql 可能需要更新的 FastAPI |

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **P1** | **依赖膨胀 10x** | 实际需要 ≈40 个包，`requirements_full.txt` 列出了 450 个包。这是一个 pip freeze 快照，不是可安装的依赖文件。 |
| **P1** | **私有包不可安装** | `chainke-auth-service==0.1.0`, `liankebao-payment-sdk==0.1.0` 等包在公开 PyPI 不存在，新开发者无法复现环境。 |
| **P1** | **requirements_full.txt 与 requirements.txt 不一致** | 两个文件定义了不同的依赖集，哪个是真实的？ |
| **P2** | **opentelemetry 依赖过重** | 引入了 8+ 个 opentelemetry 子包，但配置文件中有条件导入（try/except），可能最终未被使用。 |
| **P2** | **paddlepaddle 和 paddleocr 体积巨大** | PaddleOCR 需要 PaddlePaddle（~800MB+），但 OCR 模块有完整的骨架保护（`_PADDLE_AVAILABLE` 检测），说明它是可选的，但仍在依赖列表中。 |

---

## 4. 数据库模型审计

### 4.1 ORM 模型清单 (23 个模型文件)

| 模型文件 | 表名 | 用途 |
|---------|------|------|
| `user.py` | `users`, `unlock_records` | 用户 + 解锁记录 |
| `brochure.py` | `brochures`, `pages` | 核心画册 + 页面 |
| `tag.py` | `user_tags`, `match_records` | 用户标签 + 匹配记录 |
| `visitor.py` | `visitor_logs` | 访客日志 |
| `trust.py` | `trust_network` | 信任网络 |
| `payment.py` | `payment_orders`, `enterprise_subscriptions`, `trial_records` | 支付/订阅 |
| `ab_test.py` | `ab_tests`, `ab_test_variants`, `ab_test_events`, `ab_test_decision_logs` | A/B 测试 |
| `team.py` | `teams`, `team_members`, `team_invites`, `approval_requests` | 团队管理 |
| `tenant.py` | `tenants` (+ `TenantBase` 抽象基类) | 多租户 |
| `message.py` | `messages` | 消息 |
| `document.py` | `documents` | 文档 |
| `integration.py` | `integrations` | 外部集成 |
| `invoice.py` | `invoices` | 发票 |
| `api_key.py` | `api_keys`, `api_key_usage` | API 密钥 |
| `audit.py` | `audit_logs` | 审计日志 |
| `webhook.py` | `webhook_subscriptions` | Webhook |
| `gaia.py` | `gaia_knowledge`, `gaia_evolution_events`, `gaia_training_runs`, `gaia_model_weights`, `knowledge_models` | AI 进化知识库 |
| `rbac.py` | RBAC 相关表 | 权限控制 |
| `usage_counter.py` | `usage_counters` | 用量计数 |
| `developer_app.py` | `developer_apps` | 开发者应用 |
| `webhook_subscription.py` | `webhook_subscriptions` | Webhook 订阅 |
| `app_store.py` | `app_store_*` | 应用商店 |
| `crm/crm_models.py` | `crm_pipeline_stages`, `crm_contacts`, `crm_deals`, `crm_activities`, `crm_notes` | CRM |

### 4.2 问题

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **P1** | **Model–Migration 漂移** | 只有2次 Alembic 迁移，但 `create_app()` 中使用 `Base.metadata.create_all` 直接创建表。多次模型变更后未生成新迁移。Alembic 形同虚设。 |
| **P1** | **CRM 模型循环导入风险** | `models/__init__.py` 注释明确指出 CRM 模型循环导入问题（注释 block 了 `CrmContact` 等 import），改为直接引用方式。这是架构耦合信号。 |
| **P1** | **TenantBase 定义了但几乎未使用** | `TenantBase` 设计用于多租户隔离，但业务模型（Brochure、User 等）继承的是 `Base` 而非 `TenantBase`。多租户方案形同虚设。 |
| **P2** | **payment.py 使用了 PostgreSQL 方言** | `from sqlalchemy.dialects.postgresql import JSON` — 若使用 SQLite 会报错。SQLite 没有原生的 JSON 列类型。 |
| **P2** | **模型缺少级联删除约束** | `UnlockRecord`、`PaymentOrder` 等表的 `user_id` 外键没有 ON DELETE CASCADE 或 SET NULL。 |
| **P2** | **Tag 和 MatchRecord 在同一个 model 文件中** | `tag.py` 同时包含 `UserTag` 和 `MatchRecord`，命名与内容不匹配，应拆分为独立的 `match.py`。 |
| **P3** | `EnterpriseSubscription.features` 使用 `JSON` 类型 | 非结构化的 JSON 字段使查询和迁移困难。 |
| **P3** | 缺少 `updated_at` 触发器的显式测试 | `onupdate=func.now()` 依赖 SQLAlchemy 层面，若直接 SQL 更新则不会触发。 |

### 4.3 迁移状态

```
db2fd0f53768 (Head) — 初始迁移 (2026-06-26)
  └── a1b2c3d4e5f6 — 添加索引 (2026-06-28)
```
| 严重度 | 问题 |
|--------|------|
| **P1** | 项目自6月28日后经历了大量模型变更（Gaia、CRM、Webhook、UsageCounter 等），但无对应迁移。`create_all` 绕过迁移。 |

---

## 5. 中间件审计

18 个中间件文件，架构清晰，分层合理。

### 5.1 注册在 `create_app()` 中的中间件（按注册顺序）

```
MetricsMiddleware → ApiKeyMiddleware → RateLimiterMiddleware → I18nMiddleware
→ RequestIDMiddleware → SecurityHeadersMiddleware → APIVersionRedirectMiddleware
→ CORSMiddleware → CsrfMiddleware → LoggingMiddleware → UsageLimitMiddleware
```

### 5.2 中间件矩阵

| 中间件 | 注册状态 | 功能 | 评价 |
|--------|---------|------|------|
| `RequestIDMiddleware` | ✅ | 注入 X-Request-ID | 正确，推荐生产 |
| `RateLimiterMiddleware` | ✅ | 三级限流 (100/1000/10000 rpm) | 优秀设计，滑动窗口算法 |
| `MetricsMiddleware` | ✅ | Prometheus APM 指标 | 生产标准 |
| `I18nMiddleware` | ✅ | 国际化上下文 | 正确 |
| `SecurityHeadersMiddleware` | ✅ | 7安全头 (CSP/HSTS/XFO...) | 优秀 |
| `CORSMiddleware` | ✅ | CORS | 标准实现 |
| `CsrfMiddleware` | ✅ | CSRF 保护 | 对于 API 可能多余（JWT 已有保护） |
| `LoggingMiddleware` | ✅ | 结构化 JSON 日志 | 正确 |
| `ApiKeyMiddleware` | ✅ | API Key 认证 | 生产标准 |
| `UsageLimitMiddleware` | ✅ | 用量限制 | 正确 |
| `AuditMiddleware` | ❌ 未注册 | 审计日志 | 类已定义但未注册 |
| `TenantMiddleware` | ❌ 未注册 | 多租户 | 类已定义但未注册 |
| `SSOMiddleware` | ❌ 未注册 | SSO/OAuth | 类已定义但未注册 |
| `OTelMiddleware` | ❌ (init_otel() 单独调用) | OpenTelemetry | 通过工厂函数 init 而非中间件 |
| `RBACMiddleware` | ❌ 未注册 | 权限控制 | 类已定义但未注册 |
| `APIKeyMiddleware` (2) | ✅ api_key.py | API Key 认证 | 与 api_key.py 同名但不同文件 |

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **P1** | **AuditMiddleware 未注册** | `audit.py` 实现了完整的审计日志中间件但从未在 `create_app()` 中注册，审计功能形同虚设。 |
| **P1** | **TenantMiddleware 未注册** | 多租户隔离中间件已实现但未启用，导致所有 tenant 数据混杂。 |
| **P2** | **中间件顺序可能有问题** | `RateLimiterMiddleware` 在 `RequestIDMiddleware` 之前注册，但自身未生成 request_id；`ApiKeyMiddleware` 在 `RateLimiterMiddleware` 之前，但限流器需要 JWT 上下文。 |
| **P2** | **CSRF 中间件对纯 API 是反模式** | REST API 使用 JWT Bearer token，CSRF 保护不适用且可能干扰移动端/小程序调用。 |
| **P2** | **RateLimiter 为内存实现** | 重启会丢失状态，多实例部署会失效。生产应使用 Redis。 |

---

## 6. 路由全景审计

### 6.1 路由注册概览（50+ 路由文件）

路由器通过 `create_app()` 统一注册，部分路由有条件导入（try/except），实现优雅降级。

**按功能分类：**

| 类别 | 路由文件 | 前缀 |
|------|---------|------|
| **认证** | `auth.py` | `/api/v1/auth` |
| **用户** | `user.py` | `/api/v1/users` |
| **画册** | `brochure.py` | `/api/v1/brochures` |
| **标签/匹配** | `tag.py`, `match.py` | `/api/v1/tags`, `/api/v1/match` |
| **访客** | `visitor.py` | `/api/v1/visitors` |
| **信任** | `trust.py` | `/api/v1/trust` |
| **支付** | `payment.py` | `/api/v1/payments` |
| **会员** | `membership.py`, `subscription_router.py` | `/api/v1/membership` |
| **AI 助手** | `ai_assist.py` (try/except) | `/api/v1/ai/assist` |
| **AI 对话** | `ai_chat.py` (try/except) | `/api/v1/ai/chat` |
| **AI 配置** | `ai_config.py` | `/api/v1/ai/config` |
| **DeepSeek 代理** | `ai_deepseek.py` (try/except) | `/api/v1/ai/deepseek` |
| **三管道 (SAG/Hybrid)** | `pipeline_router.py` (try/except) | `/api/v1/ai/sag`, `/hybrid`, `/pipeline` |
| **A/B 测试** | `ab_test.py`, `ab_test_router.py` | `/api/v1/ab-test` |
| **CRM** | `crm_router.py`, `campaign_router.py`, `prediction_router.py` | `/api/v1/crm` |
| **团队** | `team.py` | `/api/v1/teams` |
| **租户** | `tenant_api.py` | `/api/v1/tenants` |
| **AI 学习** | `learning_router.py` | `/api/v1/learning` |
| **知识图谱** | `knowledge_graph.py` | `/api/v1/knowledge-graph` |
| **Gaia 进化** | `gaia_router.py` | `/api/v1/ai/gaia` |
| **集成** | `integrations.py` | `/api/v1/integrations` |
| **导出** | `export.py` | `/api/v1/export` |
| **Webhook** | `webhooks.py` | `/api/v1/webhooks` |
| **SSO/OAuth** | `sso.py` | `/api/v1/auth/sso` |
| **GraphQL** | `graphql_route.py` | `/graphql` |
| **API Keys** | `api_keys.py` | `/api/v1/api-keys` |
| **发票** | `invoice.py` | `/api/v1/invoices` |
| **消息** | `messages.py` | `/api/v1/messages` |
| **文档** | `document.py` | `/api/v1/documents` |
| **分析** | `analytics.py` | `/api/v1/analytics` |
| **健康检查** | `health.py` | `/health`, `/api/health` |
| **MINI 程序** | `miniapp_router.py` | `/api/v1/miniapp/*` |
| **开发者** | `developer.py` | `/api/v1/developer` |
| **机器人** | `bot_router.py` | `/api/v1/bot` |
| **分享** | `share.py` | `/api/v1/share` |
| **v1 废弃** | `v1_deprecated.py` | `/api/v1/deprecated` |
| **表单捕获** | `form_capture_router.py` | `/api/v1/crm/forms` |
| **营销** | `growth.py` | `/api/v1/growth` |
| **小程序** | `miniapp_router.py` (3个路由器) | `/api/v1/miniapp/*` |

### 6.2 问题

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **P1** | **API 版本前缀不一致** | 部分路由硬编码 `/api/v1/xxx` 前缀，部分无前缀（如 `health.py` 的 `/health`）。`APIVersionRedirectMiddleware` 做了 `/api/v1/xxx → /api/xxx` 重写，但 `/health` 和 `/api/health` 重复。 |
| **P1** | **重复的健康检查端点** | `health.py` 提供 `/health`（JSON），`create_app()` 中的 `@app.get("/health")` 返回 `"OK"`（PlainText），`@app.get("/api/health")` 返回 JSON。三个端点功能重复。 |
| **P1** | **两个 A/B 测试路由文件** | `ab_test.py` (732行) 和 `ab_test_router.py` 同时存在。前者完整实现 CRUD，后者可能冗余。 |
| **P2** | **v1_deprecated.py 仍被注册** | 废弃路由仍然在 `create_app` 中注册，未禁用或标记弃用。 |
| **P2** | **try/except 路由注册过多** | `ai_assist`、`ai_chat`、`pipeline_router`、`ai_deepseek` 等 4 个路由器使用 try/except 注册，静默失败导致调用者收到 404，调试困难。 |
| **P2** | **缺少 API 文档注解** | 虽然 FastAPI 自动生成 Swagger，但部分路由（如 `analytics.py`、`usage_router.py`）缺少 `response_model` 或清晰的操作描述。 |
| **P2** | **认证方式不统一** | 部分路由使用 `get_current_user`（JWT Bearer），部分使用 `ApiKeyMiddleware`，部分无认证（public）。缺少清晰的权限注解。 |
| **P3** | `bot_router.py` 和 `learning_router.py` 在 `create_app()` 中注册位置与注释不符 | 它们在中间件区域之后注册，但注释标注模糊。 |

---

## 7. AI 模块分析

### 7.1 AI 模块全景 (32 文件)

```
backend/app/ai/
├── ocr.py                   ← OCR 扫描器 (PaddleOCR骨架 + 正则提取)
├── extractor.py             ← 信息提取器
├── vector_search.py         ← 向量搜索引擎 (M3E/numpy/OpenAI/DeepSeek)
├── rag_pipeline.py          ← RAG 管道 (680行)
├── sag_pipeline.py          ← SAG 管道
├── hybrid_pipeline.py       ← 混合管道
├── pipeline_router.py       ← 三管道路由器
├── writing_assistant.py     ← 写作助手
├── recommendation.py        ← 推荐引擎
├── feedback_loop.py         ← 反馈闭环 (583行)
├── bandit_engine.py         ← 多臂老虎机 (Thompson Sampling)
├── ab_testing.py            ← A/B 测试引擎
├── knowledge_graph.py       ← 知识图谱
├── knowledge_model_service.py ← 知识模型服务
├── model_registry.py        ← 模型注册表
├── model_serving.py         ← 模型服务
├── training_pipeline.py     ← 训练管道
├── online_learning.py       ← 在线学习
├── optimization.py          ← 优化引擎
├── mcp_adapter.py           ← MCP 协议适配器
├── gaia_evolution_brain.py  ← 盖娅进化大脑 (874行)
├── gaia_flywheel.py         ← 盖娅飞轮
├── gaia_trainer.py          ← 盖娅训练器
├── cron/
│   ├── design_qa_cron.py    ← 定时设计QA
│   └── learning_cron.py     ← 定时学习
└── gateway/
    ├── interfaces.py
    └── adapters/
        ├── direct_api_adapter.py
        ├── cached_gateway_adapter.py
        └── fallback_gateway_adapter.py
```

### 7.2 AI 能力输入/输出/状态矩阵

| 模块 | 输入 | 输出 | 当前状态 | 备注 |
|------|------|------|---------|------|
| **OCR** | 图像路径/PIL Image | OCR 文本 + 提取的联系信息 | ✅ 可用 | 骨架设计：PaddleOCR 未安装时返回提示 |
| **向量搜索** | 查询文本 | Top-K 排序结果 | ✅ 可用 | 4 种后端可切换，带 SQLite 持久化索引 |
| **RAG 管道** | 用户查询 + 上下文 | 带源引用的 AI 回答 | ✅ 可用 | 依赖 DeepSeek API（SPOF） |
| **SAG 管道** | 结构化查询 | 结构化分析结果 | ⚠️ 未验证 | 文档不完整 |
| **混合管道** | 多模态查询 | 综合结果 | ⚠️ 未验证 | Pipeline router 实现 |
| **推荐引擎** | 用户画像 + 候选列表 | 排序后的推荐结果 | ✅ 可用 | 标签+向量混合排序 |
| **反馈闭环** | 用户评分/反馈 | 权重调整 | ✅ 可用 | SQLite 持久化 |
| **多臂老虎机** | 候选列表 + 用户 ID | Thompson 采样排序结果 | ✅ 可用 | 纯内存，重启丢失 |
| **A/B 测试** | 实验配置 + 事件 | 统计显著性结果 | ✅ 可用 | 支持卡方/贝叶斯 |
| **知识图谱** | 用户/名片数据 | 关系图谱 | ⚠️ 开发中 | 模块接口已定义 |
| **Gaia 进化大脑** | 知识/反馈/A/B 结果 | 进化权重 | ⚠️ 概念验证 | 874 行，功能复杂但价值存疑 |
| **写作助手** | 写作提示 | AI 生成文案 | ✅ 可用 | 调用 DeepSeek |
| **MCP 适配器** | MCP 协议消息 | 适配后的 AI 响应 | ⚠️ 开发中 | 实验性功能 |

### 7.3 问题

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **P0** | **DeepSeek API 为单点故障 (SPOF)** | RAG、SAG、写作助手、AI 对话等核心 AI 功能均依赖 `api.deepseek.com`。无自动故障转移/回退策略。若 DeepSeek 不可用，所有 AI 功能瘫痪。 |
| **P1** | **Gaia 模块过度工程** | `gaia_evolution_brain.py` (874行) + `gaia_flywheel.py` + `gaia_trainer.py` = ~1500 行代码实现"进化大脑"，但对于一个名片应用来说，其价值/复杂度比存疑。这是典型的"AI 炫技"风险。 |
| **P1** | **三管道 (RAG/SAG/Hybrid) 设计冗余** | 三个管道功能重叠，实现分散在 4 个文件中（~1200行）。实际可能只需 RAG 管道。 |
| **P2** | **向量搜索索引直接使用 SQLite** | `vector_search.py` 直接使用 `sqlite3` 模块而非 SQLAlchemy，与项目数据库层不一致。 |
| **P2** | **反馈闭环使用独立 SQLite 路径** | `feedback_loop.py` 也直接操作自家 SQLite 数据库，与主数据库脱离。数据一致性风险。 |
| **P2** | **多臂老虎机为纯内存状态** | `bandit_engine.py` 的 `user_arms` 存储在内存 dict 中，服务重启后所有学习数据丢失。 |
| **P2** | **OCR 骨架模式在无 PaddleOCR 时返回提示而非错误** | 返回的提示文本会作为正常结果传递给前端，可能导致前端显示"请安装 PaddleOCR"这样的意外内容。 |
| **P2** | **Gateway 适配器未集成** | 设计了 3 个网关适配器（direct/cached/fallback），但未在管道中实际使用。 |
| **P3** | **AI 模块缺乏统一错误码** | 不同模块的异常处理风格不一致，有的返回空字符串，有的返回提示文本，有的抛出异常。 |
| **P3** | **缺少 AI 调用耗时/Token 用量监控** | `rag_pipeline.py` 中 `tokens_used` 字段存在但实际未统计。 |

---

## 8. 前端结构审计

### 8.1 结构全景

```
frontend/src/
├── App.tsx               ← 根组件 (Router + I18n + RTL + ErrorBoundary)
├── main.tsx              ← 入口
├── router.tsx            ← 路由配置 (259行)
├── registerSW.ts         ← Service Worker 注册
├── api/
│   ├── client.ts         ← API 客户端
├── components/
│   ├── AIAssistant.tsx, Avatar.tsx, Button.tsx, CardNetworkGraph.tsx
│   ├── CardPreview.tsx, ErrorBoundary.tsx, Footer.tsx, Header.tsx
│   ├── KnowledgeGraphEmbed.tsx, LanguageSwitcher.tsx, Layout.tsx
│   ├── LoadingSkeleton.tsx, LoadingSpinner.tsx, Pagination.tsx
│   ├── SearchBar.tsx, ShareSheet.tsx, Sidebar.tsx, UploadZone.tsx
├── hooks/
│   └── useAsync.ts       ← 自定义 Hook
├── i18n/                 ← 国际化 (14种语言)
│   ├── index.tsx, RTLProvider.tsx
│   ├── zh.ts, en.ts, fr.ts, de.ts, es.ts, ...
├── lib/
│   └── api-client.ts     ← 另一个 API 客户端
├── pages/                ← 页面组件 (20+)
│   ├── DashboardPage.tsx, CardEditorPage.tsx, SettingsPage.tsx
│   ├── NetworkPage.tsx, NetworkGraphPage.tsx, MatchingPage.tsx
│   ├── ApiKeysPage.tsx, BusinessCardList.tsx, BusinessCardPage.tsx
│   ├── AnalyticsPage.tsx, PricingPage.tsx, PaymentCallback.tsx
│   ├── ABTestingPage.tsx, AIAnalyticsPage.tsx, TeamPage.tsx
│   ├── TeamSettings.tsx, GDPRSettings.tsx, ApiDocs.tsx
│   ├── DeveloperPortal.tsx
│   ├── crm/
│   │   ├── CrmListPage.tsx, CrmContactDetailPage.tsx
│   │   ├── CrmPipelinePage.tsx, CrmDashboardPage.tsx
│   └── ocr/
│       └── OcrReviewPage.tsx
└── stories/              ← Storybook 组件故事 (16文件)
```

### 8.2 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| React | 19.0.0 | 最新版 |
| Vite | 6.2.0 | 最新版 |
| Tailwind CSS | v4 (via @tailwindcss/vite) | 最新版 |
| react-router-dom | 7.14.2 | v7 支持 loaders/actions |
| motion | 12.23.24 | 动画库 (framer-motion 替代) |
| lucide-react | 0.546.0 | 图标 |
| clsx | 2.1.1 | CSS 类名工具 |
| TypeScript | 项目内 | 全 TS 代码 |

### 8.3 问题

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **P1** | **两个 API 客户端** | `api/client.ts` 和 `lib/api-client.ts` 共存，职责重复，可能导致 API 调用方式不一致。 |
| **P1** | **缺少认证状态管理** | 没有集中认证状态管理（无 Redux/Zustand/Context auth provider），各页面各自处理 token。 |
| **P2** | **API 基础 URL 硬编码风险** | `client.ts` 和 `api-client.ts` 中可能硬编码 API 地址，而不是从环境变量读取。需要检查。 |
| **P2** | **Storybook 故事与实际组件不同步风险** | 16 个故事文件可能随组件变化而过期。 |
| **P2** | **页面组件全部在单一目录** | 22 个页面文件都在 `pages/` 下（除 CRM 和 OCR 外），缺少子目录组织。 |
| **P3** | **PWA 注册但可能未完整配置** | `registerSW.ts` 存在但需要确认 manifest.json 和 Service Worker 是否完整。 |
| **P3** | **缺少 E2E 测试配置验证** | `test:e2e` 脚本指向 `e2e/playwright.config.ts`，但该目录 `e2e/` 在项目根目录。 |

---

## 9. 小程序结构审计

### 9.1 结构全景

```
miniapp/
├── app.js, app.json, app.wxss    ← 小程序入口
├── config/
│   ├── config.js                  ← API 配置
│   └── design-tokens.js           ← 设计令牌
├── components/
│   ├── card-item/                 ← 名片卡片组件 (js/json/wxml/wxss)
│   ├── empty-state/               ← 空状态组件
│   └── loading/                   ← 加载组件
├── pages/
│   ├── index/index                ← 首页 (名片列表)
│   ├── card/card                  ← 名片详情
│   ├── login/index                ← 登录
│   ├── profile/profile            ← 个人中心
│   ├── brochure/create/           ← 创建画册
│   ├── brochure/preview/          ← 预览画册
│   ├── platform/create/           ← 创建平台内容
│   ├── agreement/user             ← 用户协议
│   ├── agreement/privacy/         ← 隐私政策
│   ├── ai/chat/                   ← AI 对话
│   ├── ai/index                   ← AI 功能入口
│   ├── ai/generate/               ← AI 生成
│   ├── ai/scan/                   ← AI 扫描
│   ├── ai/match/                  ← AI 匹配
│   ├── ai/insight/                ← AI 洞察
│   ├── ai/config/                 ← AI 配置
│   ├── membership/membership      ← 会员中心
│   └── network/graph/             ← 关系图谱
├── images/                        ← 图标资源
└── docs/                          ← 内部文档
```

### 9.2 问题

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **P1** | **API 端点硬编码** | `config/config.js` 中 API 地址可能硬编码，需要在构建时或通过环境变量注入。 |
| **P1** | **无状态管理方案** | 微信小程序无标准的全局状态管理（如 mobx/wechat-state），各页面间数据共享困难。 |
| **P2** | **无自动化测试** | 小程序缺少单元测试和 E2E 测试配置。 |
| **P2** | **AI 页面分散在多个目录** | `ai/chat/`（子目录结构）与 `ai/` 下直接的文件（abtest.js, chat.js, feedback.js, gaia.js）混用，路径不一致。 |
| **P2** | **版本管理缺失** | 无 `miniprogram-ci` 或 CI/CD 上传配置。 |
| **P3** | **图片资源可优化** | `images/` 下 PNG 图标未使用 SVG 或 WebP 格式压缩。 |
| **P3** | **缺少请求重试/降级逻辑** | 小程序对 API 调用没有统一的超时重试和错误处理。 |

---

## 10. 架构缺陷汇总

### 10.1 按严重程度汇总

| 严重度 | 数量 | 关键项 |
|--------|------|--------|
| **P0** | 2 | JWT_SECRET 默认明文、DeepSeek API 单点故障 |
| **P1** | 20 | 双入口混淆、依赖膨胀、无迁移、模型漂移、Tenant 未启用、Audit 未注册、两个 API 客户端、DeepSeek SPOF、Gaia 过度工程、三管道冗余等 |
| **P2** | 18 | 中间件顺序问题、内存限流、SQLite 生产、CSRF 反模式、API 版本不一致、前端无状态管理等 |
| **P3** | 12 | 文档过时、类型检查缺失、AI 模块缺少监控等 |

### 10.2 单点故障 (SPOF)

| # | SPOF | 影响范围 | 严重度 |
|---|------|---------|--------|
| 1 | **DeepSeek API (api.deepseek.com)** | AI 对话、RAG、写作助手、DeepSeek 代理 | **P0** |
| 2 | **SQLite 单文件数据库** | 所有数据（高并发时文件锁） | **P1** |
| 3 | **JWT_SECRET 若泄漏** | 全部用户认证安全 | **P0** |
| 4 | **单实例 RateLimiter（内存）** | 多实例部署时限流失效 | **P2** |
| 5 | **BanditEngine 纯内存** | 服务重启后推荐学习数据丢失 | **P2** |

### 10.3 缺乏降级机制

| # | 组件 | 降级现状 | 严重度 |
|---|------|---------|--------|
| 1 | **DeepSeek API** | ❌ 无降级。失败则 AI 功能全部不可用 | **P0** |
| 2 | **Redis 缓存** | ⚠️ 有降级（try/except → log warning），但无降级后仍可用的保证 | **P1** |
| 3 | **任务队列** | ⚠️ 有降级（try/except），但异步任务无法执行 | **P1** |
| 4 | **微信小程序登录** | ✅ 有 Mock 降级 | 良好 |
| 5 | **CRM 连接器** | ✅ 有 Stub 降级 (SalesforceStub/HubSpotStub) | 良好 |
| 6 | **Sentry 监控** | ✅ 有 try/except 降级 | 良好 |
| 7 | **OCR** | ✅ 骨架降级（无 PaddleOCR 时返回提示） | 良好但处理可改进 |

### 10.4 硬编码问题

| # | 位置 | 内容 | 严重度 |
|---|------|------|--------|
| 1 | `.env.example` | `JWT_SECRET=change-me-to-a-random-256-bit-key` | **P0** |
| 2 | `config.py` | `CORS_ORIGINS` 默认值含多个来源 | **P2** |
| 3 | `create_app()` | 错误页面 HTML/CSS 内联硬编码（/view/ 页面） | **P3** |
| 4 | `miniapp/config/config.js` | API 基础 URL 可能硬编码 | **P1** |
| 5 | `frontend/src/api/client.ts` | API 地址可能硬编码 | **P1** |

### 10.5 配置漂移

| # | 配置项 | 所在文件 | 实际行为 | 严重度 |
|---|--------|---------|---------|--------|
| 1 | 服务端口 | 8002 (run.py) vs 8201 (main.py + Docker) | ARCHITECTURE.md 说 8002 主力，docker-compose 用 8201 | **P1** |
| 2 | 数据库类型 | SQLite (代码默认) vs PostgreSQL (docker-compose volume) | 声明了 pg volume 但使用 SQLite | **P1** |
| 3 | 迁移状态 | Alembic 只有 2 次迁移 | `create_all` 直接创建新表 | **P1** |
| 4 | 多租户 | TenantBase 已定义 | 业务模型未继承，中间件未注册 | **P1** |
| 5 | `SENTRY_DSN` | `config.py` 双路径：Settings 中 SENTRY_DSN + 模块级 os.getenv | 两个来源可能冲突 | **P3** |

---

## 10.6 综合评分

| 维度 | 评分 (1-10) | 说明 |
|------|------------|------|
| **架构清晰度** | 7/10 | 整体模块划分合理，但双入口和多中间件未注册降低清晰度 |
| **安全性** | 5/10 | 有安全头/限流/审计设计，但 JWT 默认密钥、CSRF 反模式、无 Tenant 隔离是大问题 |
| **可维护性** | 6/10 | 代码结构好但依赖膨胀（450 包）、AI 模块过度工程、模型迁移漂移 |
| **可扩展性** | 5/10 | 内存限流、SQLite 数据库、无 Redis/PostgreSQL 的生产配置限制扩展 |
| **可靠性** | 4/10 | DeepSeek API SPOF、无故障转移、AI 功能无降级、内存状态易失 |
| **可观测性** | 7/10 | Sentry + OpenTelemetry + JSON 日志 + Prometheus 指标，但审计日志未启用 |
| **总体** | **5.7/10** | 功能丰富但存在多个 P0/P1 级架构缺陷需优先修复 |

---

## 10.7 优先级修复建议

### 🔴 立即修复 (P0)
1. **强制 JWT_SECRET 为非默认值** — 在 `config.py` 中添加启动时验证，若值为 `change-me-...` 则报错退出
2. **DeepSeek API 降级** — 添加本地 LLM 回退（如 ollama）或缓存层，确保 AI 功能有离线兜底

### 🟠 优先修复 (P1)
3. **统一服务入口** — 删除 `run.py` 或 `main.py` 其中之一，统一端口为 8201
4. **清理依赖** — 删除 `requirements_full.txt`，只保留 `requirements.txt`（41行）
5. **生成缺失的 Alembic 迁移** — 停止使用 `create_all`，启用正式迁移管理
6. **启用 AuditMiddleware 和 TenantMiddleware**
7. **删除冗余的 A/B 测试路由**（`ab_test.py` 或 `ab_test_router.py`）
8. **统一前端 API 客户端** — 删除 `lib/api-client.ts`，只保留 `api/client.ts`
9. **修复 `backend/tests/` 目录缺失** — 创建并迁移测试
10. **统一 API 版本前缀** — 所有路由使用 `/api/v1/` 前缀

### 🟡 规划修复 (P2)
11. 迁移到 PostgreSQL（生产）
12. 添加 Redis 限流后端
13. 添加 AI 模块 Token 用量和延迟监控
14. 添加前端认证状态管理
15. 简化 AI 管道（合并 RAG/SAG/Hybrid）
16. 持久化 BanditEngine 状态

### 🟢 建议优化 (P3)
17. 更新 ARCHITECTURE.md
18. 添加 pyproject.toml 中的 type-checking 配置
19. 统一错误码规范
20. 小程序图片优化

---

*报告结束 — 共扫描 52 个配置/模型/中间件/路由/AI 模块文件，覆盖 10 个审计维度，识别 52 项架构问题。*
