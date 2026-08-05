# 🔒 安全合规检查清单 — AI数智名片

> **对应 OWASP Top 10 (2021)**
> 最后更新: 2026-07-20 | 版本: v2.0

---

## 各项目标签说明

| 标签 | 含义 |
|------|------|
| ✅ **已实现** | 已有完整防护，通过单元/集成测试验证 |
| ⚠️ **部分实现** | 已有基础防护但有待改进 |
| ❌ **未实现** | 尚未实施，需立即处理 |
| 🔲 **不适用** | 架构上不适用 |
| 📋 **已验证** | 已在测试中自动验证 |

---

## A01:2021 — 失效的访问控制 (Broken Access Control)

| # | 检查项 | 状态 | 实现方式 | 位置 |
|---|--------|------|----------|------|
| 1.1 | JWT 认证 — Bearer Token 校验 | ✅ 已实现 | FastAPI Depends(get_current_user) | `app/routers/auth.py`, `app/auth_jwt.py` |
| 1.2 | JWT 双算法支持 (RS256 + HS256 回退) | ✅ 已实现 | 优先 RS256 非对称签名，自动降级 HS256 | `app/auth_jwt.py` |
| 1.3 | JWT_SECRET 三档安全校验 | ✅ 已实现 📋已验证 | 空值/占位值/不足20字符三级拦截 | `app/__init__.py` startup |
| 1.4 | API Key 认证 | ✅ 已实现 | `ApiKeyMiddleware` + `X-API-Key` Header | `app/middleware/api_key.py` |
| 1.5 | RBAC 权限控制 (角色/权限) | ✅ 已实现 | FastAPI 依赖注入 (`require_permission`, `require_role`) + 装饰器 | `app/middleware/rbac.py` |
| 1.6 | 多租户数据隔离 | ⚠️ 部分实现 | `TenantMiddleware` + `TenantSession` 自动 WHERE 过滤 | `app/middleware/tenant.py` |
| 1.7 | 最小权限原则 — 默认拒绝 | ✅ 已实现 | 每个路由显式声明所需权限 | 各 `routers/*.py` |
| 1.8 | 敏感端点限流 (auth/payment 减半) | ✅ 已实现 | RateLimiter 检测敏感路径自动减半配额 | `app/middleware/rate_limiter.py` |

---

## A02:2021 — 加密机制失效 (Cryptographic Failures)

| # | 检查项 | 状态 | 实现方式 | 位置 |
|---|--------|------|----------|------|
| 2.1 | 传输层加密 (HTTPS/TLS) | ✅ 已实现 | 生产环境通过 Nginx/K8s Ingress 强制 TLS | 基础设施层 |
| 2.2 | 敏感数据存储加密 | ✅ 已实现 | 手机号等 PII 使用 Fernet (AES-128-CBC + HMAC) 加密 | `app/services/crypto_service.py` |
| 2.3 | 密码存储使用 bcrypt | ✅ 已实现 | `passlib.context` + bcrypt | `app/routers/auth.py` |
| 2.4 | JWT 使用强签名算法 | ✅ 已实现 | RS256 (非对称, 2048位 RSA) + HS256 回退 | `app/auth_jwt.py` |
| 2.5 | 密钥管理 — 环境变量 | ✅ 已实现 | 所有密钥从环境变量/`.env` 读取，无硬编码 | `app/config.py` |
| 2.6 | Fernet 密钥派生自 JWT_SECRET | ⚠️ 部分实现 | SHA-256(JWT_SECRET) → base64，应使用独立密钥 | `app/services/crypto_service.py` |

---

## A03:2021 — 注入攻击 (Injection)

| # | 检查项 | 状态 | 实现方式 | 位置 |
|---|--------|------|----------|------|
| 3.1 | SQL 注入防护 | ✅ 已实现 | SQLAlchemy ORM + 参数化查询 (所有数据库操作) | `app/repositories/` + 各 service |
| 3.2 | SOQL 注入防护 | ✅ 已实现 | `sanitize_soql_string()`, `sanitize_soql_like()` | `app/utils/security.py` |
| 3.3 | XSS 防护 — 响应头 | ✅ 已实现 📋已验证 | `X-XSS-Protection: 1; mode=block` + CSP | `app/middleware/security_headers.py` |
| 3.4 | XSS 防护 — 输入过滤 | ✅ 已实现 | Pydantic 模型字段校验 | 各 `app/schemas/` + Pydantic |
| 3.5 | 路径遍历防护 | ✅ 已实现 | FastAPI 原生路径参数校验 | 各 `routers/*.py` |
| 3.6 | 输入注入自动化测试 | ✅ 已实现 📋已验证 | SQL注入/XSS/路径遍历/Fuzzing 测试 | `tests/test_injection_input.py`, `tests/fuzzing/` |

---

## A04:2021 — 不安全的设计 (Insecure Design)

| # | 检查项 | 状态 | 实现方式 | 位置 |
|---|--------|------|----------|------|
| 4.1 | 速率限制 (Rate Limiting) | ✅ 已实现 📋已验证 | 三级分层: anonymous=100, standard=1000, enterprise=10000 req/min | `app/middleware/rate_limiter.py` |
| 4.2 | 请求大小限制 | ✅ 已实现 | FastAPI 默认 + 文件上传 size limit (100MB 视频限制) | `app/config.py` |
| 4.3 | 安全响应头 | ✅ 已实现 📋已验证 | 7 个安全响应头 (CSP/HSTS/XFO/XXP/X-CTO/RP/PP) | `app/middleware/security_headers.py` |
| 4.4 | 认证失败延迟 | ❌ 未实现 | 登录失败无人工延迟，需添加指数退避 | — |
| 4.5 | 账户锁定策略 | ❌ 未实现 | 多次失败登录未锁定账户 | — |

---

## A05:2021 — 安全配置错误 (Security Misconfiguration)

| # | 检查项 | 状态 | 实现方式 | 位置 |
|---|--------|------|----------|------|
| 5.1 | CORS 白名单 | ✅ 已实现 📋已验证 | 具体域名列表，无通配符 `*` | `app/__init__.py`, `app/config.py` |
| 5.2 | CSRF 保护 | ✅ 已实现 📋已验证 | Double Submit Cookie 模式 | `app/middleware/csrf_middleware.py` |
| 5.3 | 调试模式关闭 | ✅ 已实现 | 生产环境 `debug=False` | 部署配置 |
| 5.4 | 错误信息不泄露内部细节 | ✅ 已实现 | 自定义 Exception Handler，不暴露 stack trace | `app/routers/` |
| 5.5 | 最小化 CORS 方法 | ⚠️ 部分实现 | 当前 `allow_methods=["*"]`，应限定为实际使用的方法 | `app/__init__.py` |
| 5.6 | 安全相关环境变量检查 | ✅ 已实现 📋已验证 | `test_security_gates.py` 覆盖 | `tests/test_security_gates.py` |

---

## A06:2021 — 易受攻击和过时的组件 (Vulnerable and Outdated Components)

| # | 检查项 | 状态 | 实现方式 | 位置 |
|---|--------|------|----------|------|
| 6.1 | 依赖安全检查 | ✅ 已实现 | 定期 `pip audit` / `safety check` | CI/CD 管道 |
| 6.2 | 依赖版本锁定 | ✅ 已实现 | `requirements.txt` + `pyproject.toml` 版本锁定 | 项目根目录 |
| 6.3 | Bandit 安全扫描 | ✅ 已实现 | `.bandit.yml` 配置，白名单已知误报 | `.bandit.yml` |
| 6.4 | 底层依赖更新机制 | ⚠️ 部分实现 | Dependabot/Renovate 未配置 | — |

---

## A07:2021 — 身份认证和会话管理失效 (Identification and Authentication Failures)

| # | 检查项 | 状态 | 实现方式 | 位置 |
|---|--------|------|----------|------|
| 7.1 | JWT 过期时间 | ✅ 已实现 | `ACCESS_TOKEN_EXPIRE_MINUTES=10080` (7天) | `app/config.py` |
| 7.2 | Token 吊销 | ✅ 已实现 | `revoked_tokens` 表 + 黑名单检查 | `app/models/revoked_token.py` |
| 7.3 | OAuth2/SSO 支持 | ✅ 已实现 | Google/GitHub 登录 + 企业 OIDC | `app/routers/oauth.py`, `app/middleware/sso.py` |
| 7.4 | 微信小程序登录 | ✅ 已实现 | code2session 换取 openid | `app/routers/auth.py` |
| 7.5 | 密码复杂度要求 | ❌ 未实现 | 当前无最小密码长度/复杂度校验 | — |

---

## A08:2021 — 软件和数据完整性失效 (Software and Data Integrity Failures)

| # | 检查项 | 状态 | 实现方式 | 位置 |
|---|--------|------|----------|------|
| 8.1 | Webhook 签名验证 | ✅ 已实现 | HMAC-SHA256 签名 + 验证 | `app/services/webhook_signer.py` |
| 8.2 | API 响应签名 | ✅ 已实现 | `webhook_signer` 签名可信回调 | `app/services/webhook_signer.py` |
| 8.3 | CI/CD 管道安全 | ✅ 已实现 | GitHub Actions + 代码审查 | `.github/` |
| 8.4 | 软件供应链验证 | ⚠️ 部分实现 | 无 `pyproject.toml` hash 锁定 | — |

---

## A09:2021 — 安全日志记录和监控失效 (Security Logging and Monitoring Failures)

| # | 检查项 | 状态 | 实现方式 | 位置 |
|---|--------|------|----------|------|
| 9.1 | 审计日志 | ⚠️ **部分实现** | ✅ `AuditMiddleware` 已编写，❌ 未在 `create_app()` 中注册 | `app/middleware/audit.py` |
| 9.2 | 请求日志 | ✅ 已实现 | `LoggingMiddleware` — JSON 结构化日志 | `app/middleware/logging_middleware.py` |
| 9.3 | 请求追踪 (Request ID) | ✅ 已实现 | `RequestIDMiddleware` — UUID 注入响应头 | `app/middleware/request_id.py` |
| 9.4 | APM 监控 | ✅ 已实现 | `MetricsMiddleware` — Prometheus 指标 | `app/middleware/metrics.py` |
| 9.5 | Sentry 错误追踪 | ✅ 已实现 | Sentry SDK 集成 + 请求 ID 注入 | `app/__init__.py` |
| 9.6 | OpenTelemetry 链路追踪 | ✅ 已实现 | OTel + FastAPIInstrumentor | `app/middleware/otel.py` |
| 9.7 | 慢查询监控 | ✅ 已实现 | `DBQueryMonitor` — 装饰器/上下文管理器 | `app/middleware/db_query_monitor.py` |

---

## A10:2021 — 服务端请求伪造 (Server-Side Request Forgery, SSRF)

| # | 检查项 | 状态 | 实现方式 | 位置 |
|---|--------|------|----------|------|
| 10.1 | 外部 URL 白名单 | ⚠️ 部分实现 | 链客宝/QCC API 有固定基地址，但无统一 URL 白名单 | `app/config.py` |
| 10.2 | Webhook URL 验证 | ✅ 已实现 | Webhook 订阅有 URL 格式校验 | `app/services/webhook_dispatcher.py` |
| 10.3 | 内部网络隔离 | ✅ 已实现 | 服务部署在 K8s 内部，外部无法直接访问内部服务 | 基础设施层 |

---

## 📊 合规评分

| 类别 | 覆盖率 | 关键差距 |
|------|--------|----------|
| 访问控制 (A01) | 90% | TenantMiddleware 未完全集成至所有路由 |
| 加密 (A02) | 85% | Fernet 密钥应从独立密钥派生，非 JWT_SECRET |
| 注入 (A03) | 95% | 已有完整 Pydantic 校验 + ORM + 安全测试 |
| 设计 (A04) | 70% | 缺少认证失败延迟和账户锁定 |
| 配置 (A05) | 85% | CORS allowed_methods 应缩小范围 |
| 组件 (A06) | 75% | 缺少自动依赖更新机制 |
| 身份认证 (A07) | 80% | 缺少密码复杂度校验 |
| 完整性 (A08) | 80% | 缺少 CI/CD 依赖完整性锁定 |
| 日志监控 (A09) | 85% | **AuditMiddleware 未注册** — 已在 middleware/__init__ 导出但未在 app 加载 |
| SSRF (A10) | 70% | 缺少统一外部 URL 白名单校验 |

> **总体评分: 8.5 / 10**
> 上次评估: 2026-07-20
>
> **待修复优先级:**
> 1. ⚠️ [A09] 注册 AuditMiddleware 到 create_app()
> 2. ⚠️ [A04] 添加登录失败延迟 + 账户锁定
> 3. ⚠️ [A05] 缩小 CORS allowed_methods 范围
> 4. ⚠️ [A02] 分离 Fernet 加密密钥
