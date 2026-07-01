# SOC 2 Type I 就绪评估报告

> **项目**: AI 数智名片 (AI Digital Business Card)
> **评估日期**: 2026-07-01
> **评估范围**: 后端服务 (FastAPI) — 认证、授权、加密、审计、运维
> **评估标准**: AICPA SOC 2 Trust Services Criteria — Security (Common Criteria CC1–CC9)

---

## 1. 现有安全控制盘点

### 1.1 认证 (Authentication) ✅

| 控制项 | 状态 | 实现位置 | 备注 |
|--------|------|----------|------|
| JWT Bearer Token | ✅ 已实现 | `routers/auth.py` | HS256, 7天过期, sub=user_id |
| 密码强度验证 | ✅ 已实现 | `routers/auth.py` | ≥8位, 含大小写/数字/特殊字符 |
| bcrypt 密码哈希 | ✅ 已实现 | `routers/auth.py` | passlib + bcrypt |
| API Key 认证 | ✅ 已实现 | `middleware/api_key.py` | X-API-Key Header, 支持启用/吊销 |
| OAuth2 / SSO | ✅ 已实现 | `routers/oauth.py`, `middleware/sso.py` | Google, GitHub, 企业 OIDC |
| 微信小程序登录 | ✅ 已实现 | `routers/auth.py` | code 换取 openid |
| 会话续期 | ⚠️ 部分 | JWT 固定过期, 无 refresh token | 建议增加 refresh token 机制 |

### 1.2 授权 (Authorization) ✅

| 控制项 | 状态 | 实现位置 | 备注 |
|--------|------|----------|------|
| RBAC 角色控制 | ✅ 已实现 | `middleware/rbac.py`, `models/rbac.py` | 角色: admin/user; 细粒度权限 permission |
| 路由级权限装饰器 | ✅ 已实现 | `middleware/rbac.py` | `@require_permissions()`, `@require_roles()` |
| FastAPI 依赖注入 | ✅ 已实现 | `middleware/rbac.py` | `Depends(require_permission("perm"))` |
| 团队级角色 | ✅ 已实现 | `models/team.py` | Owner / Admin / Member / Viewer |
| API Key 权限限定 | ✅ 已实现 | `middleware/api_key.py` | API Key 可绑定权限列表 |
| 全局路径拦截 | ✅ 已实现 | `middleware/rbac.py` | RBACMiddleware 可选启用 |

### 1.3 加密 (Encryption) ✅

| 控制项 | 状态 | 实现位置 | 备注 |
|--------|------|----------|------|
| 传输加密 (HSTS) | ✅ 已实现 | `middleware/security_headers.py` | `Strict-Transport-Security: max-age=31536000; includeSubDomains` |
| 密码存储加密 | ✅ 已实现 | `routers/auth.py` | bcrypt, salt 自动 |
| JWT 签名 | ✅ 已实现 | `routers/auth.py` | HS256, 密钥来自环境变量 `JWT_SECRET` |
| 数据库加密 | ❌ 未实现 | — | SQLite 默认无加密, 建议启用 SQLCipher 或转 PostgreSQL + TDE |
| 字段级加密 | ❌ 未实现 | — | PII 字段 (phone, wechat_openid) 明文存储 |
| 密钥轮换策略 | ✅ 已实现 | `docs/security/key_rotation_policy.md` | 已建立文档策略 |

### 1.4 审计 (Auditing) ✅

| 控制项 | 状态 | 实现位置 | 备注 |
|--------|------|----------|------|
| API 审计日志 | ✅ 已实现 | `middleware/audit.py` | 自动记录所有 HTTP 请求到 `audit_logs` 表 |
| 审计日志模型 | ✅ 已实现 | `models/audit.py` | 字段: user_id, action, resource, detail, ip, user_agent, timestamp |
| 索引优化 | ✅ 已实现 | `models/audit.py` | 4 个复合索引 (user_id, action, timestamp, user+timestamp) |
| 手动审计记录 | ✅ 已实现 | `middleware/audit.py` | `record_audit()` 函数供业务代码调用 |
| GDPR 审计查询 | ✅ 已实现 | `routers/gdpr.py` | `GET /api/gdpr/logs` 查看用户审计日志 |
| 日志跳过规则 | ✅ 已实现 | `middleware/audit.py` | 健康检查/静态文件自动跳过 |

### 1.5 补充安全控制

| 控制项 | 状态 | 实现位置 | 备注 |
|--------|------|----------|------|
| 速率限制 | ✅ 已实现 | `middleware/rate_limiter.py` | 分级限流: 匿名100/认证1000/企业10000 req/min |
| 安全响应头 | ✅ 已实现 | `middleware/security_headers.py` | CSP, HSTS, XFO, XXP, X-CTO, Referrer-Policy, Permissions-Policy |
| 请求追踪 (OTel) | ✅ 已实现 | `middleware/otel.py` | OpenTelemetry 分布式追踪 (可选) |
| 异常监控 (Sentry) | ✅ 已实现 | `config.py` | Sentry DSN 配置 |
| 优雅关闭 | ✅ 已实现 | `graceful_shutdown.py` | 信号处理, 连接池清理 |
| 数据库查询监控 | ✅ 已实现 | `middleware/db_query_monitor.py` | 慢查询检测 |
| 请求 ID 追踪 | ✅ 已实现 | `middleware/request_id.py` | 每个请求分配唯一 request_id |
| CORS 配置 | ⚠️ 部分 | `config.py` | 白名单列表, 但未做细粒度 origin 验证 |
| 日志脱敏 | ❌ 未实现 | — | 审计日志中 PII 未脱敏 |

---

## 2. 待补充控制项 (Gap Analysis)

根据 SOC 2 CC 标准, 以下 5 个控制域需要补充实施:

### 2.1 ⬜ 渗透测试 (Penetration Testing) — CC3.4 / CC5.2

| 项目 | 说明 |
|------|------|
| **差距** | 尚无定期渗透测试流程和报告 |
| **要求** | SOC 2 要求至少每年一次全面的渗透测试, 以及重大变更后的针对性测试 |
| **建议** | 建立渗透测试计划文档, 覆盖 OWASP Top 10; 每季度内部扫描, 每年第三方测试 |
| **参考** | 见 `penetration-test-plan.md` |

### 2.2 ⬜ 数据分类与分级 (Data Classification) — CC6.1 / CC6.7

| 项目 | 说明 |
|------|------|
| **差距** | 无正式的数据分类策略, PII 字段未标记分级 |
| **要求** | SOC 2 要求组织建立并维护数据分类方案, 按敏感度实施差异化保护 |
| **建议** | 建立四级分类体系 (公开/内部/敏感/机密), 制定每级加密和访问控制要求 |
| **参考** | 见 `data-classification.md` |

### 2.3 ⬜ 供应商风险评估 (Vendor Risk Assessment) — CC3.2 / CC9.1

| 项目 | 说明 |
|------|------|
| **差距** | 无正式的供应商评估流程 |
| **涉及供应商** | DeepSeek API, 微信支付/支付宝, 链客宝, Sentry, Redis |
| **要求** | SOC 2 要求对处理客户数据的第三方进行安全评估和持续监控 |
| **建议** | 建立供应商准入问卷 (SAQ), 每年评估, 确保合同中包含数据保护条款 |

### 2.4 ⬜ 事件响应计划 (Incident Response Plan) — CC7.1 / CC7.2 / CC7.3

| 项目 | 说明 |
|------|------|
| **差距** | 尚无正式的事件响应流程文档 |
| **要求** | SOC 2 要求建立安全事件的检测、响应、报告和改进的闭环流程 |
| **建议** | 建立 IR 计划, 包含: 检测→分级→响应→恢复→事后复盘 |
| **关键指标** | MTTR < 4h (严重), < 24h (高), < 72h (中) |

### 2.5 ⬜ 安全培训与意识 (Security Training) — CC1.2 / CC2.1

| 项目 | 说明 |
|------|------|
| **差距** | 无正式的安全培训计划和记录 |
| **要求** | SOC 2 要求组织对所有人员进行安全意识和职责培训 |
| **建议** | 建立年度安全培训计划, 包含: 安全编码, 数据保护, 钓鱼识别, 事件报告 |
| **记录** | 培训记录 (参加人员, 时间, 内容, 考核结果) 需保留至少 2 年 |

---

## 3. 实施路线图

### 🔴 P0 — 2 周内 (高优先级, SOC 2 关键控制)

| 编号 | 任务 | 负责人 | 预计工时 | 依赖 |
|------|------|--------|----------|------|
| P0-1 | 数据分类策略制定 | 安全/合规 | 2天 | — |
| P0-2 | PII 字段加密存储 (phone, wechat_openid) | 后端 | 3天 | P0-1 |
| P0-3 | 审计日志脱敏 (日志中 mask PII) | 后端 | 1天 | P0-1 |
| P0-4 | 渗透测试计划文档 + 首次内测 | 安全 | 3天 | — |
| P0-5 | 事件响应计划文档 (IR Playbook) | 安全/运维 | 2天 | — |
| P0-6 | 数据库静态加密 (SQLite→PostgreSQL+TDE) | 后端/运维 | 5天 | — |

### 🟡 P1 — 1 个月内 (中优先级, 合规增强)

| 编号 | 任务 | 负责人 | 预计工时 |
|------|------|--------|----------|
| P1-1 | 供应商风险评估 (DeepSeek, WeChat, Alipay, Sentry) | 合规 | 3天 |
| P1-2 | JWT refresh token 机制 (缩短 access token 有效期) | 后端 | 2天 |
| P1-3 | 速率限制告警 + 自动封禁 (IP/用户级) | 后端 | 2天 |
| P1-4 | 首次第三方渗透测试 (选择合格厂商) | 安全 | 5天 |
| P1-5 | 安全培训材料制作 + 首次全员培训 | 安全/HR | 3天 |
| P1-6 | CSP 策略收紧 (nonce/哈希 + 报告端点) | 后端 | 1天 |

### 🟢 P2 — 3 个月内 (低优先级, 持续改进)

| 编号 | 任务 | 负责人 | 预计工时 |
|------|------|--------|----------|
| P2-1 | 自动化漏洞扫描集成 (CI/CD 流水线) | DevOps | 3天 |
| P2-2 | SIEM 集成 (审计日志→安全事件平台) | 运维 | 5天 |
| P2-3 | 供应商 SOC2 / ISO 27001 证书审核 | 合规 | 5天 |
| P2-4 | 红蓝对抗演练 | 安全 | 3天 |
| P2-5 | SOC 2 Type II 就绪审计 (3 个月运行证据) | 合规/审计 | — |
| P2-6 | Bug Bounty 计划 (邀请制) | 安全 | 2天 |

---

## 4. SOC 2 准备情况总结

```
┌──────────────────────────────────────────────┐
│          SOC 2 Type I 准备度评估               │
├──────────────────────────────────────────────┤
│  认证 (Authentication)      ██████████  100% │
│  授权 (Authorization)       ██████████  100% │
│  加密 (Encryption)          ██████░░░░   60% │
│  审计 (Auditing)            ██████████  100% │
│  渗透测试                    ██░░░░░░░░   20% │
│  数据分类                    ░░░░░░░░░░    0% │
│  供应商评估                  ░░░░░░░░░░    0% │
│  事件响应                    ░░░░░░░░░░    0% │
│  安全培训                    ░░░░░░░░░░    0% │
├──────────────────────────────────────────────┤
│  整体就绪进度                █████░░░░░   50% │
└──────────────────────────────────────────────┘
```

### 关键里程碑

| 里程碑 | 目标日期 | 交付物 |
|--------|----------|--------|
| P0 完成 (控制基础) | 2026-07-15 | 数据分类文档, PII加密, 渗透测试报告, IR计划 |
| P1 完成 (合规增强) | 2026-08-01 | 供应商评估, 三方渗透, 安全培训 |
| P2 完成 (持续运营) | 2026-10-01 | 自动化扫描, SIEM, SOC2 Type II 就绪 |

---

*文档版本: v1.0 | 最后更新: 2026-07-01 | 审核人: [待定]*
