# AI数智名片 — 完整架构扫描报告

> 扫描时间: 2026-08-04 17:15 | 状态: 🟢 全部在线 | 版本: v2.1 生产版
> 扫描执行: 白泽远程分身（阿里云 47.116.116.87）

## 一、总体架构（6 层）

```
┌─────────────────────────────────────────────────────────────┐
│  ① 入口层  Nginx (card.liankebao.top / liankebao.top)         │
│     25+ location 规则 → 反向代理                                │
└──────────────────────────┬──────────────────────────────────┘
                           │ proxy_pass
┌──────────────────────────▼──────────────────────────────────┐
│  ② 服务层  systemd ai-digital-card.service                    │
│     uvicorn main:app :8201 (--workers 4, Restart=always)      │
│     WorkingDir=/var/www/ai-digital-card/backend               │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  ③ 后端应用层  FastAPI (Python, 模块化工业级)                  │
│     ┌─────────┬─────────┬──────────┬───────────┐             │
│     │ 80+ 路由 │ Agents  │Connectors│ MCP Servers│            │
│     │ 模块     │ 19个    │HubSpot/  │ DB/匹配/   │            │
│     │         │ 智能体  │Salesforce│ 分析/日志  │             │
│     └─────────┴─────────┴──────────┴───────────┘             │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  ④ 数据层  PostgreSQL aicard_db (97张表) + Redis(:6379)       │
│     SQLAlchemy asyncpg 连接池 (pool=20, max_overflow=10)      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  ⑤ 前端层  React 19 + Vite + TS + Tailwind v4                 │
│     dist/ 构建产物 → Nginx SPA (/ → index.html)               │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  ⑥ 运维层  Celery异步任务 + 健康监控 Timer + 飞书告警           │
└─────────────────────────────────────────────────────────────┘
```

## 二、后端路由域（80+ 模块）

| 业务域 | 路由模块 | 说明 |
|:-----|:-----|:-----|
| **名片核心** | business-card, brochure, card, share, tag | 名片 CRUD + 分享 + 标签 |
| **商务社交** | match, matching, recommend, network, six_degrees, connection | 匹配/推荐/六度人脉 |
| **AI 能力** | ai_assist, inference_gateway, knowledge_graph, prompt, minimax, ocr, pdf, transphee | AI 写作/推理/OCR/知识图谱 |
| **军团融合** | gaia, learning, knowledge_models, commander, task_slicer | 对接灵枢引擎 |
| **商业化** | payment, subscription, invoice, escrow, app_store, developer | 支付/订阅/托管/应用商店 |
| **企业级** | admin, team, organization, tenant, user, sso, oauth, gdpr | 权限/租户/合规 |
| **工程化** | ab_test, accuracy_gate, circuit_breaker, canary, rate_limit, quality, web_vitals | A/B/精度门禁/熔断/金丝雀 |

## 三、数据层实况（PostgreSQL aicard_db）

- **97 张表**，SQLAlchemy asyncpg 异步引擎（pool=20, max_overflow=10）
- 核心表数据量：

| 表 | 数据 | 状态 |
|:-----|:-----|:-----|
| brochures（名片册） | 109 | 🟢 有数据 |
| platform_members（用户） | 20 | 🟢 有数据 |
| match_records（匹配记录） | 26 | 🟢 有数据 |
| business_card / contact / enterprise / payment_transaction | 0 | ⚪ 空表（待业务跑量） |

- 业务域：CRM 套件(contacts/deals/campaigns)、托管 escrow、企业订阅、gaia 知识/训练、审计日志、API keys、精度门禁

## 四、AI 智能体层（19 个模块）

```
Agents:  architecture_agent / backend_agent / data_agent
         design_qa_agent / growth_agent / knowledge_agent
         gaia_orchestra_daemon（编排守护） + orchestra_pipeline
         动态工厂 dynamic_agent_factory + model_task_matcher
Connectors: HubSpot + Salesforce（真实 + stub 双模）
MCP:       db / match_engine / analytics / log 四个 MCP 服务
```

## 五、基础设施

| 组件 | 状态 | 说明 |
|:-----|:-----|:-----|
| Nginx | 🟢 | 25+ 路由规则，SPA + API 反代 + 军团 /ai/ 转发 |
| PostgreSQL :5432 | 🟢 active | aicard_db |
| Redis :6379 | 🟢 UP | Celery broker |
| Celery | ⚙️ 配置就绪 | broker_url=redis://localhost |
| 健康监控 | 🟢 | Timer 每5分钟 → /health → 异常飞书告警（防轰炸） |

## 六、前端（React 19 + Vite 6）

- **20+ 页面**：Dashboard / 名片列表&编辑器 / 匹配 / 人脉网络 / 分析 / 定价 / 支付 / A/B实验 / API文档 / API Keys / 开发者门户 / GDPR / CRM / OCR
- 技术栈：TS + Tailwind v4 + React Router 7 + Motion + Storybook + Playwright e2e
- 构建产物 dist/ 已就绪（SPA 模式，Nginx 托底 /index.html）

## 七、匹配引擎现状（2026-08-04 核查）

**实际挂载并工作的匹配引擎**：`match_router`（/api/match/*，使用 VectorSearchEngine 向量检索 + brochure.execute_smart_search 智能搜索），挂载于 app/__init__.py 第 270 行。

**未挂载/未接入**：
- `matching.py`（三明治匹配管线 SmartMatcher，DeepSeek LLM 增强）— 文件存在但**未挂载**，/api/matching/* 返回 404
- `k3_match.py`（Kimi K3 1M 上下文匹配）— 依赖 `baize_libs/kimi_k3_service` 库在服务器上**不存在**，纯 CLI 脚本未被后端引用

## 八、架构观察（3 点）

1. **工业级工程完备** — 熔断/金丝雀/精度门禁/A-B/审计/限流全套，远超一般 SaaS 项目
2. **AI 浓度高** — 19 个智能体 + 4 个 MCP + 军团引擎融合，是「AI 原生」架构
3. **数据仍在早期** — 名片册 109 条、用户 20 个，交易表空；架构已就绪，等业务跑量
