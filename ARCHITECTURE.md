# AI数智名片 — 架构文档

> 这是 AI 数字名片的**唯一核心代码库**。
> 其他冗余目录和旧副本已归档到 `_archive/`。

---

## 一、技术栈总览

| 层级 | 技术 | 说明 |
|:-----|:-----|:------|
| **后端框架** | FastAPI (Python 3.12+) | 异步高性能 API 框架 |
| **数据库** | SQLite (dev) / PostgreSQL (prod) | 异步 SQLAlchemy 2.0 ORM |
| **前端** | React 19 + TypeScript + Vite 6 + **Tailwind CSS v4** | 现代 SPA 应用 |
| **小程序** | 微信小程序原生开发 | 链客宝 · 企业家智能商务厅 |
| **AI 引擎** | PaddleOCR + DeepSeek API + M3E Embedding | OCR 识别 / NLP / 向量搜索 |
| **认证** | JWT (RS256 + HS256 双算法) | 无状态认证，支持手机号/微信登录 |
| **容器编排** | Docker Compose / Kubernetes | 开发与生产部署 |
| **监控** | Prometheus + OpenTelemetry + Sentry | 指标采集 / 链路追踪 / 错误监控 |
| **网关** | Nginx | 统一接入层（生产） |
| **缓存** | Redis | 会话缓存 / 速率限制 / 数据缓存 |

---

## 二、六层架构图

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        接入层 (Nginx :8200)                               │
│           反向代理 · SSL 终端 · 静态资源 · 速率限制 · 灰度分发             │
├───────────────────────────────────────────────────────────────────────────┤
│                         API 层 (FastAPI :8201)                            │
│              41 个路由模块 · 418+ 端点 · OpenAPI 3.1 文档                 │
├───────────────────────────────────────────────────────────────────────────┤
│                        中间件链 (10 层)                                    │
│  RequestID → Metrics → ApiKey → RateLimiter → I18n →                     │
│  SecurityHeaders → APIVersionRedirect → CORS → CSRF → Logging            │
├───────────────────────────────────────────────────────────────────────────┤
│                        业务服务层                                         │
│  画册 CRUD · 供需匹配 · 信任网络 · AI 提取 · 图册渲染 · 支付 · 标签       │
│  CRM · 团队 · 消息 · 访客 · 推荐 · A/B 测试 · 审批 · Webhook ·            │
│  日历 · SSO/OAuth · GDPR · 集成 · API Key · 知识图谱 · 六度人脉           │
├───────────────────────────────────────────────────────────────────────────┤
│                        数据层                                             │
│  SQLAlchemy 2.0 ORM · 53 个模型 · Redis 缓存 · SQLite/PostgreSQL         │
├───────────────────────────────────────────────────────────────────────────┤
│                        基础设施层                                         │
│  文件存储 · 媒体处理 · 日志收集 · 指标采集 · CI/CD · K8s 编排 · 监控告警  │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 三、路由统计 (418+ 端点)

后端 API 按功能划分为 **41 个路由模块**，共计 **418+ 个端点**（含 7 个内置端点 + 411 个 router 端点）：

| 模块 | 文件 | 端点数 | 功能 |
|:-----|:-----|:------:|:-----|
| auth | `routers/auth.py` | ~15 | 注册/登录/微信登录/令牌刷新 |
| user | `routers/user.py` | ~12 | 用户信息 CRUD、密码修改 |
| brochure | `routers/brochure.py` | ~18 | 画册 CRUD、模板、发布、分享 |
| tag | `routers/tag.py` | ~8 | 标签管理（供需标签） |
| match | `routers/match.py` | ~10 | 供需匹配、匹配记录 |
| recommend | `routers/recommend.py` | ~8 | 推荐引擎（RAG + 相似度） |
| admin | `routers/admin.py` | ~15 | 管理后台接口 |
| payment | `routers/payment.py` | ~12 | 支付/订单/退款 |
| subscription | `routers/subscription_router.py` | ~8 | 会员订阅管理 |
| visitor | `routers/visitor.py` | ~6 | 访客记录/统计 |
| trust | `routers/trust.py` | ~8 | 信任关系 CRUD |
| team | `routers/team.py` | ~15 | 团队管理/邀请/角色 |
| message | `routers/messages.py` | ~8 | 站内消息 |
| i18n | `routers/i18n.py` | ~3 | 国际化翻译/配置 API |
| crm | `crm/*.py` | ~20 | CRM 集成/营销活动/预测 |
| 其他 | 26 个模块 | ~240 | SSO/OAuth/GDPR/知识图谱/六度人脉等 |

**内置端点** (7 个): `/` · `/card-editor` · `/offline` · `/view/{token}` · `/health` · `/api/health` · `/metrics`

---

## 四、中间件链 (10 层)

中间件按注册顺序组成处理管道，每个请求依次经过：

| 序号 | 中间件 | 功能 | 文件 |
|:----:|:-------|:-----|:-----|
| 1 | **RequestIDMiddleware** | 为每个请求生成唯一 `request_id`，注入日志与响应头 | `middleware/request_id.py` |
| 2 | **MetricsMiddleware** | APM 指标采集（请求数/延迟/活跃请求/DB 查询数） | `middleware/metrics.py` |
| 3 | **ApiKeyMiddleware** | API Key 认证（兼容第三方开发者） | `middleware/api_key.py` |
| 4 | **RateLimiterMiddleware** | 速率限制（匿名 500/min / 标准 2000/min / 企业 20000/min） | `middleware/rate_limiter.py` |
| 5 | **I18nMiddleware** | 语言检测与翻译上下文（12 种语言） | `middleware/i18n_middleware.py` |
| 6 | **SecurityHeadersMiddleware** | 安全头（HSTS/CSP/XSS/Frame 等） | `middleware/security_headers.py` |
| 7 | **APIVersionRedirectMiddleware** | `/api/v1/xxx` → `/api/xxx` 路径重写（ASGI 级别） | `middleware/api_version.py` |
| 8 | **CORSMiddleware** | 跨域资源共享 (FastAPI 内置) | FastAPI 内置 |
| 9 | **CsrfMiddleware** | CSRF 防护（Cookie 双提交模式） | `middleware/csrf_middleware.py` |
| 10 | **LoggingMiddleware** | 请求/响应日志（JSON 格式） | `middleware/logging_middleware.py` |

此外通过 OpenTelemetry FastAPIInstrumentor 注入链路追踪。

---

## 五、认证流程

```
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ 客户端   │────▶│ FastAPI  │────▶│ 认证中间件│────▶│ 路由处理   │
│ (Web/小程│     │ Nginx    │     │ ApiKey/   │     │           │
│  序)    │     │          │     │ JWT       │     │           │
└─────────┘     └──────────┘     └──────────┘     └──────────┘
     │               │               │
     │ 1. 注册/登录   │               │
     │───────────────▶│               │
     │               │ 2. 验证凭证   │
     │               │──────────────▶│
     │               │               │ 3. 签发 JWT
     │ 4. 返回 Token │               │  (RS256 + HS256)
     │◀──────────────│               │
     │               │               │
     │ 5. 携带 Bearer │               │
     │   Token 请求   │               │
     │───────────────▶│──────────────▶│
     │               │               │ 6. 验证 JWT
     │               │               │  → get_current_user
     │ 7. 返回响应   │               │
     │◀──────────────│◀──────────────│
```

### 认证方式

1. **手机号 + 密码注册/登录**: bcrypt 哈希密码 → JWT (RS256)
2. **微信登录**: `wx.login()` code → jscode2session → openid → JWT
3. **微信小程序登录**: 真实/降级模式 → openid → 查/创建用户 → JWT
4. **SSO/OAuth2**: Google / GitHub / 企业 OIDC → 授权码交换 → JWT
5. **API Key**: 第三方开发者 → Header 认证 → 限流

### JWT 设计

- **双算法签名**: RS256（非对称，优先）+ HS256（对称，降级）
- **载荷**: `sub`(user_id) + `iat` + `exp`
- **过期时间**: 7 天
- **RSA 密钥**: 自动生成（开发环境），PEM 文件存储

---

## 六、数据库 ER 图要点

### 核心表关系

```
users (1) ──< brochures (1) ──< pages (N)
  │              │
  │              ├──< visitors
  │              ├──< trust_network
  │              ├──< match_records
  │              └──< user_tags
  │
  ├──< api_keys
  ├──< webhook_subscriptions
  ├──< team_members
  ├──< subscriptions
  └──< orders
```

### 关键表

| 表 | 记录数 | 关键字段 |
|:---|:------:|:---------|
| `users` | ~1,000+ | id, phone, name, password_hash, wechat_openid, membership_tier, avatar |
| `brochures` | ~1,000+ | id, user_id(FK), title, purpose, status, share_token, visibility, view_count, album_meta |
| `pages` | ~4,000+ | id, brochure_id(FK), sort_order, content_type, content, image_url, ai_summary |
| `user_tags` | ~2,000+ | id, user_id(FK), tag, tag_type(provide/demand), weight |
| `match_records` | ~10,000+ | id, user_id_a, user_id_b, score, status, matched_at |
| `trust_network` | ~1,000+ | id, user_id(FK), target_user_id, trust_level, created_at |
| `visitors` | ~5,000+ | id, brochure_id(FK), visitor_id, ip, user_agent, interest_tags |

### 索引策略

- `brochures.user_id`: 加速用户画册查询
- `brochures.share_token`: 唯一索引，加速分享链接解析
- `match_records.(user_id_a, user_id_b)`: 复合唯一索引
- `user_tags.(user_id, tag_type)`: 复合索引
- `visitors.brochure_id`: 加速访客记录统计

---

## 七、部署拓扑

### 开发环境

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Vite Dev │     │ FastAPI  │     │ SQLite   │
│ :5173    │────▶│ :8201    │────▶│ .db file │
└──────────┘     └──────────┘     └──────────┘
```

### Docker Compose 生产

```
┌───────────────────────────────────────────────┐
│              Docker Host                       │
│                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  Nginx   │  │  Backend  │  │ AI 服务   │    │
│  │ :8200    │─▶│ :8201     │  │ :8202     │    │
│  │ (反向代理) │  │ (FastAPI) │  │ (OCR/NLP) │    │
│  └──────────┘  └────┬─────┘  └──────────┘    │
│                      │                        │
│               ┌──────┴──────┐                │
│               │  SQLite DB  │                 │
│               │  /app/data  │                 │
│               └─────────────┘                 │
└───────────────────────────────────────────────┘
```

### Kubernetes 生产 (AWS/GCP)

```
┌─────────────────────────────────────────────────────────────┐
│                      K8s Cluster                            │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐              │
│  │ Ingress   │  │ Service  │  │ Deployment   │              │
│  │ (Global)  │─▶│ :8201    │─▶│ 2+ replicas  │              │
│  └──────────┘  └──────────┘  │ FastAPI pods │              │
│                              └──────┬───────┘              │
│  ┌──────────┐  ┌──────────┐         │                      │
│  │ HPA      │  │ ConfigMap│         ▼                      │
│  │ (CPU 80%)│  │ .env     │  ┌─────────────┐               │
│  └──────────┘  └──────────┘  │ PostgreSQL  │               │
│                              │ (RDS/Aurora) │               │
│  ┌──────────┐               └─────────────┘               │
│  │ Redis    │                                             │
│  │ (Elasti)│                                             │
│  └──────────┘                                             │
│                                                             │
│  ┌──────────┐  ┌────────────┐  ┌───────────┐              │
│  │ Prometheus│  │ OpenTelemetry│  │ Sentry    │              │
│  │ + Grafana │  │ Collector   │  │ Error     │              │
│  └──────────┘  └────────────┘  │ Tracking   │              │
│                                └───────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### 服务组件

| 组件 | 规格 | 说明 |
|:-----|:-----|:------|
| **Backend Pod** | 2+ 副本, 250m CPU / 512Mi 内存 | 滚动更新, maxSurge=1, maxUnavailable=0 |
| **PostgreSQL** | RDS/Aurora 实例 | 异步连接池 (pool_size=20) |
| **Redis** | ElastiCache / 自建 | 缓存 + 速率限制 + 会话 |
| **Nginx** | Alpine 镜像 | 反向代理 + SSL + 静态资源 |
| **File Storage** | S3 / 本地卷 | 用户上传文件 |
| **CI/CD** | GitHub Actions | Blue-Green 部署 + 灰度发布 |

---

## 八、文件统计

| 目录 | 文件数 | 说明 |
|:-----|:------:|:------|
| `backend/` | ~378 | Python 后端 (FastAPI) |
| `frontend/` | ~7,745 | React + TypeScript 前端 |
| `deploy/` | ~22 | 部署配置 (Nginx/Docker/脚本) |
| `k8s/` | ~11 | Kubernetes 编排 |
| `k6/` | — | 性能测试脚本 |
| `e2e/` | — | E2E 测试 |
| `tests/` | — | 集成测试 |
| `docs/` | — | 文档 |
| `scripts/` | — | 工具脚本 |

---

## 九、项目文件树

```
D:\AI数智名片\
├── _archive/               ← 已归档的旧副本
├── backend/                ← FastAPI 后端 API 服务（378 文件）
│   ├── main.py             入口文件 (uvicorn, port 8201)
│   ├── app/
│   │   ├── __init__.py     应用工厂 (create_app)
│   │   ├── config.py       配置 (Pydantic Settings)
│   │   ├── database.py     异步引擎 (SQLite/PostgreSQL)
│   │   ├── auth_jwt.py     JWT 工具 (RS256 + HS256)
│   │   ├── api_standards.py 统一错误码/分页/错误响应
│   │   ├── routers/        41 个路由模块
│   │   ├── models/         53 个数据模型 (SQLAlchemy)
│   │   ├── services/       63 个服务模块
│   │   ├── middleware/     10 个中间件
│   │   ├── ai/             AI 引擎 (OCR + LLM + 向量搜索)
│   │   ├── i18n/           国际化翻译 (12 种语言)
│   │   ├── payment/        支付模块 (微信/支付宝)
│   │   ├── crm/            CRM 集成 (HubSpot/Salesforce)
│   │   └── templates/      HTML 模板 (首页/编辑器/查看器)
│   ├── tests/              测试
│   └── requirements.txt    依赖
├── frontend/               ← React 19 + Vite 6 前端（7745 文件）
│   ├── index.html          HTML 入口
│   ├── vite.config.ts      Vite 配置（代理 /api → :8201）
│   ├── package.json        依赖 (React 19, Vite 6, Tailwind CSS v4)
│   ├── src/                源码
│   ├── dist/               构建输出
│   └── nginx_html/         Nginx 静态资源
├── deploy/                 ← 部署配置（22 文件）
├── docs/                   文档
├── k8s/                    Kubernetes 编排
├── k6/                     性能测试
├── e2e/                    E2E 测试
├── scripts/                工具脚本
├── data/                   数据
├── tests/                  集成测试
├── training_data/          训练数据
├── backups/                备份
├── .github/                GitHub Actions CI
├── docker-compose.yml      Docker Compose 编排
├── Dockerfile              Docker 构建
├── Makefile                构建命令
└── ARCHITECTURE.md         ← 本文档
```

---

> 最后更新: 2026-07-13 · 代码版本: `472d453` · 技术栈: FastAPI+SQLite+React 19+Tailwind CSS v4+微信小程序
