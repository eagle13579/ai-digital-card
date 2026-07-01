# 安全策略文档

> **项目**: AI 数智名片 (AI Digital Business Card)
> **版本**: v1.0
> **生效日期**: 2026-07-01
> **适用范围**: 后端服务、AI 服务、前端应用、CI/CD 流水线
> **文档状态**: 已批准

---

## 目录

1. [密钥管理与轮换](#1-密钥管理与轮换)
2. [速率限制分级策略](#2-速率限制分级策略)
3. [内容安全策略 (CSP)](#3-内容安全策略-csp)
4. [安全响应头](#4-安全响应头)
5. [认证与授权](#5-认证与授权)
6. [数据安全](#6-数据安全)
7. [审计与监控](#7-审计与监控)
8. [漏洞管理](#8-漏洞管理)
9. [合规参考](#9-合规参考)

---

## 1. 密钥管理与轮换

### 1.1 密钥分类

| 密钥名称 | 来源 | 用途 | 敏感等级 |
|----------|------|------|:--------:|
| `JWT_SECRET` | 环境变量 | JWT 令牌签名 (HS256) | 严重 |
| `DEEPSEEK_API_KEY` | 环境变量 | DeepSeek API 调用 | 高 |
| `EMBEDDING_API_KEY` | 环境变量 | OpenAI / DeepSeek Embedding API | 高 |
| `CHAINKE_AUTH_TOKEN` | 环境变量 | 链客宝 API 认证 | 高 |
| `WECHAT_MINI_SECRET` | 环境变量 | 微信小程序登录 | 严重 |
| `WECHAT_PAY_API_KEY` | 环境变量 | 微信支付 API V2 | 严重 |
| `WECHAT_PAY_V3_KEY` | 环境变量 | 微信支付 API V3 | 严重 |
| `ALIPAY_PRIVATE_KEY` | 环境变量 | 支付宝应用私钥 | 严重 |
| `SENTRY_DSN` | 环境变量 | Sentry 异常上报 | 中 |
| `SSO_*_CLIENT_SECRET` | 环境变量 | OAuth2 / OIDC 客户端密钥 | 高 |

### 1.2 轮换策略

| 密钥类型 | 轮换周期 | 触发条件 | 方法 |
|----------|:--------:|----------|------|
| `JWT_SECRET` | 90 天 | 安全事件、员工离职 | 双密钥发布: 新旧并存 24 小时过渡 |
| `DEEPSEEK_API_KEY` | 180 天 | 疑似泄露 | 通过 DeepSeek 控制台更换 |
| 支付密钥 (微信/支付宝) | 365 天 | 证书到期、安全事件 | 通过对应商户平台更换 |
| SSO Client Secret | 180 天 | 安全事件 | 通过 OAuth 提供商控制台更换 |
| 数据库密码 | 365 天 | 人员变更 | 滚动更新: 修改密码后重启服务 |

### 1.3 轮换流程

```
1. 生成新密钥
   - JWT: openssl rand -hex 32
   - 支付密钥: 在商户平台生成
   - SSO: 在提供商控制台生成

2. 部署新密钥
   - 更新 Kubernetes Secret (kubectl edit secret)
   - 或更新 .env.production 后 docker compose restart
   - JWT 使用双密钥: 旧密钥验证 + 新密钥签发

3. 验证
   - 确认新密钥服务正常
   - 确认旧密钥已停止使用 (JWT: 24h 后移除)
   - 确认审计日志中记录了轮换事件

4. 清理
   - 从所有存储中删除旧密钥明文
   - 回收旧的 Secret 版本
```

### 1.4 密钥存储要求

| 环境 | 存储方式 | 备注 |
|------|----------|------|
| 本地开发 | `.env` 文件 (已加入 `.gitignore`) | 禁止提交到版本控制 |
| CI/CD | GitHub Secrets / Actions Secrets | 只读, 不在日志中暴露 |
| 生产 (K8s) | Kubernetes Secrets (Base64) | 建议启用 ESO (External Secrets Operator) |
| 生产 (Docker) | `.env.production` 文件 | 仅部署人员可读, 权限 600 |

---

## 2. 速率限制分级策略

### 2.1 限流等级

速率限制基于 **滑动窗口算法**，按用户等级和端点类型分级:

| 用户等级 | 默认限制 (req/min) | 敏感端点 (req/min) | 识别方式 |
|:--------:|:-----------------:|:------------------:|----------|
| **匿名** | **100** | **50** | 无 `Authorization` Header |
| **已认证** | **1,000** | **500** | 有效 JWT Bearer Token |
| **企业** | **10,000** | **5,000** | JWT 中 `role` 为 `enterprise` / `admin` |

**敏感端点** (`/api/auth/*`, `/api/payment/*`) 在基础限制上**减半**。

### 2.2 实现位置

- **速率限制中间件**: `backend/app/middleware/rate_limiter.py`
- **默认配置**: 文件顶部 `DEFAULT_LIMITS` 字典定义
- **自定义配置**: 通过 `app.add_middleware(RateLimiterMiddleware, limits={...})` 注入

### 2.3 响应头

所有被限流的请求返回 `HTTP 429 Too Many Requests`，并附带以下响应头:

| Header | 说明 | 示例 |
|--------|------|------|
| `Ratelimit-Limit` | 当前窗口上限 | `100` |
| `Ratelimit-Remaining` | 当前窗口剩余请求数 | `42` |
| `Ratelimit-Reset` | 窗口重置的 Unix 时间戳 | `1721234567` |
| `Retry-After` | 建议重试等待秒数 | `30` |

### 2.4 限流绕过防护

| 防护措施 | 说明 |
|----------|------|
| X-Forwarded-For 信任 | 仅信任内部代理，支持自定义 CIDR 白名单 |
| IP 封禁 | 连续触发限流 >= 10 次/小时 -> 自动封禁 IP 30 分钟 |
| 分布式限流 (规划) | 多实例部署下通过 Redis 共享状态 |

---

## 3. 内容安全策略 (CSP)

### 3.1 当前策略 (生产环境)

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'unsafe-inline' 'unsafe-eval';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self' data:;
  connect-src 'self' https://api.deepseek.com https://oapi.dingtalk.com;
  frame-src 'none';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
```

> **说明**: 当前策略因前端框架 (Vite/React) 需要 `unsafe-inline` 和 `unsafe-eval`。**生产环境应逐步收紧**。

### 3.2 策略收紧路线图 (P1-6)

| 阶段 | 目标 | 措施 | 时间 |
|:----:|------|------|:----:|
| 当前 | 基础保护 | `default-src 'self'` + 必要放宽 | 已实施 |
| 阶段 1 | 移除 unsafe-eval | 升级前端依赖，启用 Trusted Types | P1 (1个月内) |
| 阶段 2 | 引入 nonce | 服务端生成 nonce，模板注入 | P2 (3个月内) |
| 阶段 3 | 移除 unsafe-inline | 全站 nonce/哈希 + 报告端点 | P2 (3个月内) |
| 最终 | 报告模式 | `Content-Security-Policy-Report-Only` + 监控 | 持续 |

### 3.3 实现位置

- **CSP 中间件**: `backend/app/middleware/security_headers.py`
- **当前值**: `SECURITY_HEADERS["Content-Security-Policy"] = "default-src 'self'"`
- **Nginx 覆盖**: `deploy/nginx.conf` 可通过 `add_header` 覆盖

---

## 4. 安全响应头

所有 HTTP 响应默认注入以下安全头:

| 响应头 | 值 | 说明 |
|--------|----|------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | 强制 HTTPS (HSTS) |
| `X-Content-Type-Options` | `nosniff` | 禁止 MIME 嗅探 |
| `X-Frame-Options` | `DENY` | 禁止页面被嵌入 iframe |
| `X-XSS-Protection` | `1; mode=block` | 启用浏览器 XSS 过滤器 |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | 跨域时只发送 origin |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | 禁用敏感 API |

---

## 5. 认证与授权

### 5.1 认证方式

| 方式 | 适用场景 | 实现位置 |
|------|----------|----------|
| JWT Bearer Token | 标准 API 认证 | `routers/auth.py` |
| API Key (X-API-Key) | 机器间 / 第三方集成 | `middleware/api_key.py` |
| OAuth2 / SSO | 用户登录 (Google, GitHub) | `routers/oauth.py` |
| 企业 OIDC | 企业用户单点登录 | `middleware/sso.py` |
| 微信小程序 code 登录 | 小程序用户 | `routers/auth.py` |

### 5.2 密码策略

| 要求 | 值 |
|------|----|
| 最小长度 | 8 位 |
| 字符要求 | 大写字母 + 小写字母 + 数字 + 特殊字符 |
| 哈希算法 | bcrypt (passlib) |
| 盐值 | 自动生成 (bcrypt 内置) |
| 登录失败锁定 | 连续 5 次失败 -> 锁定 15 分钟 |

### 5.3 RBAC 权限模型

| 角色 | 权限范围 |
|------|----------|
| `admin` | 全部权限, 包括用户管理、系统配置 |
| `user` | 个人名片管理、基础功能 |
| `enterprise` | 企业管理、团队成员管理、高级功能 |
| `viewer` | 只读访问 (团队场景) |

---

## 6. 数据安全

### 6.1 传输加密

| 通道 | 加密方式 | 证书 |
|------|----------|------|
| 用户 -> Nginx | TLS 1.2 / 1.3 | Let's Encrypt (自动续期) |
| Nginx -> 后端 | HTTP (内网) | -- |
| 后端 -> Redis | 可选 TLS | 需配置 `REDIS_PASSWORD` |
| 后端 -> DeepSeek API | HTTPS | 平台证书 |
| 后端 -> 支付网关 | HTTPS + 签名 | 商户证书 |

### 6.2 数据分类 (四级)

| 等级 | 定义 | 示例 | 存储要求 |
|:----:|------|------|----------|
| 公开 | 可公开访问 | 公司名、公开名片信息 | 无特殊要求 |
| 内部 | 仅内部可见 | 项目文档、架构图 | 访问控制 |
| 敏感 | 泄露有中等风险 | 手机号、邮箱、微信 openid | 字段级加密 |
| 机密 | 泄露有严重风险 | 密码哈希、支付密钥、JWT_SECRET | bcrypt + 访问审计 |

### 6.3 数据备份

| 备份项 | 频率 | 保留周期 | 存储位置 |
|--------|:----:|:--------:|----------|
| SQLite 数据库 | 每日全量 | 30 天 | 本地 + S3 (规划中) |
| 视频上传 | 增量 | 90 天 | 本地文件系统 |
| 审计日志 | 每日全量 | 365 天 | 本地 + S3 (规划中) |

---

## 7. 审计与监控

### 7.1 审计日志

| 审计项 | 记录内容 | 保留期 |
|--------|----------|:------:|
| API 请求审计 | user_id, action, resource, detail, ip, user_agent, timestamp | 365 天 |
| 认证事件 | 登录、登出、注册、密码修改、登录失败 | 365 天 |
| 权限变更 | 角色分配、权限修改 | 永久 |
| 密钥轮换 | 操作人、操作时间、密钥类型 | 永久 |
| 敏感数据访问 | 谁、何时、为何访问了敏感字段 | 365 天 |

### 7.2 监控告警

| 告警规则 | 阈值 | 通知方式 |
|----------|:----:|----------|
| API 错误率过高 | >= 1% (5 分钟窗口) | 即时通讯 |
| P99 延迟超限 | >= 3s (5 分钟窗口) | 即时通讯 |
| 速率限制命中率 | 匿名用户 >= 50% 被限流 | 邮件 |
| 磁盘使用率 | >= 85% | 即时通讯 |
| TLS 证书到期 | <= 14 天 | 邮件 + 即时通讯 |

---

## 8. 漏洞管理

### 8.1 依赖扫描

| 扫描类型 | 工具 | 频率 | 位置 |
|----------|------|:----:|------|
| Python 依赖安全扫描 | `pip-audit` / Safety | 每次 CI | `backend/` |
| Node 依赖安全扫描 | `npm audit` | 每次 CI | `frontend/` |
| 容器镜像扫描 | Trivy / Docker Scout | 每次构建 | Dockerfile |

### 8.2 处理流程

```
发现漏洞
  |
  - 严重 (CVSS >= 9.0) -> 24 小时内修复 -> 紧急发布
  |
  - 高 (CVSS 7.0-8.9) -> 7 天内修复 -> 包含在下次发布
  |
  - 中 (CVSS 4.0-6.9) -> 30 天内修复 -> 列入迭代计划
  |
  - 低 (CVSS < 4.0) -> 下次大版本修复 -> 记录追踪
```

### 8.3 安全联系人

| 用途 | 联系方式 |
|------|----------|
| 报告安全漏洞 | `security@liankebao.top` |
| PGP 加密密钥 | [下载公钥](https://liankebao.top/.well-known/pgp-key.txt) |
| 预期响应时间 | 紧急漏洞: <= 24 小时; 一般: <= 72 小时 |

---

## 9. 合规参考

| 标准 | 状态 | 相关文档 |
|------|:----:|----------|
| SOC 2 Type I | 进行中 (50%) | `docs/security/soc2-readiness.md` |
| ISO 27001 | 规划中 | -- |
| GDPR | 基本合规 | `routers/gdpr.py` -- 数据导出/删除接口 |
| 个人信息保护法 (PIPL) | 部分 | 需完善数据分类和脱敏 |

---

## 附录: 相关文件索引

| 文件路径 | 说明 |
|----------|------|
| `backend/app/config.py` | 配置加载 (pydantic-settings) |
| `backend/app/middleware/rate_limiter.py` | 速率限制中间件 |
| `backend/app/middleware/security_headers.py` | 安全响应头中间件 |
| `backend/app/middleware/audit.py` | 审计日志中间件 |
| `backend/app/middleware/rbac.py` | RBAC 授权中间件 |
| `backend/app/middleware/api_key.py` | API Key 认证中间件 |
| `backend/app/middleware/otel.py` | OpenTelemetry 追踪 |
| `backend/app/docs/security/soc2-readiness.md` | SOC 2 就绪评估 |
| `backend/app/docs/security/key_rotation_policy.md` | 密钥轮换策略 (扩展) |
| `.github/workflows/ci.yml` | CI 流水线 |
| `.github/workflows/deploy.yml` | 部署流水线 |
| `.github/workflows/canary.yml` | 金丝雀发布 |
| `.github/workflows/e2e.yml` | E2E 测试 |
| `docker-compose.yml` | Docker 编排 |

---

*本安全策略文档由 AI 数智名片安全团队维护 | 联系: security@liankebao.top | 最后更新: 2026-07-01*
