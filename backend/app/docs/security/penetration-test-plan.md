# 渗透测试计划 — Penetration Test Plan

> **项目**: AI 数智名片 (AI Digital Business Card)
> **测试范围**: 后端 API 服务 (FastAPI)
> **测试目标**: 覆盖 OWASP Top 10 (2021) 漏洞类别, 验证关键端点的安全性
> **测试类型**: 白盒 + 灰盒 (有源代码和API文档访问权限)
> **测试工具**: Burp Suite Professional / OWASP ZAP / sqlmap / Nuclei / custom scripts

---

## 1. OWASP Top 10 (2021) 覆盖矩阵

| 编号 | 漏洞类别 | 覆盖状态 | 测试方法 | 涉及端点 |
|------|----------|----------|----------|----------|
| A01 | 失效的访问控制 (Broken Access Control) | ✅ 重点 | IDOR测试, 角色越权, 路径遍历 | 全部认证端点 |
| A02 | 加密机制失效 (Cryptographic Failures) | ✅ 重点 | TLS配置检查, PII明文检测, JWT弱密钥 | 全部 |
| A03 | 注入 (Injection) | ✅ 重点 | SQLi, NoSQLi, LDAPi, 命令注入 | 搜索/匹配/创建端点 |
| A04 | 不安全设计 (Insecure Design) | ✅ 覆盖 | 速率限制测试, 配额绕过, 业务逻辑漏洞 | 解锁/支付/匹配 |
| A05 | 安全配置错误 (Security Misconfiguration) | ✅ 覆盖 | 默认凭证, 调试接口, CORS过宽, 信息泄露 | 全部 |
| A06 | 脆弱或过时的组件 (Vulnerable Components) | ⚠️ 扫描 | 依赖版本检查 (pip audit / safety) | N/A |
| A07 | 认证和身份验证失效 (Identification & Auth Failures) | ✅ 重点 | 暴力破解, JWT伪造, Session固定, OAuth绕过 | auth/oauth |
| A08 | 软件和数据完整性故障 (Software & Data Integrity) | ⚠️ 扫描 | CI/CD管道安全, 依赖供应链检查 | N/A |
| A09 | 安全日志和监控不足 (Security Logging & Monitoring) | ✅ 检查 | 审计日志完整性, 日志篡改 | 全部 |
| A10 | 服务端请求伪造 (SSRF) | ✅ 覆盖 | 外部URL调用, 回环地址, 云元数据端点 | AI服务/Webhook |

---

## 2. API 端点测试清单

### 2.1 认证模块 — `/api/auth/*`

| # | 端点 | 方法 | 测试重点 | 优先级 |
|---|------|------|----------|--------|
| 1 | `/api/auth/register` | POST | SQL注入(name/phone), 密码强度绕过, 批量注册 | P0 |
| 2 | `/api/auth/login` | POST | 暴力破解, 凭证填充, 响应差异用户枚举 | P0 |
| 3 | `/api/auth/oauth/*` | GET | OAuth CSRF, state参数验证, redirect_uri开放重定向 | P0 |

### 2.2 用户模块 — `/api/users/*`, `/api/gdpr/*`

| # | 端点 | 方法 | 测试重点 | 优先级 |
|---|------|------|----------|--------|
| 4 | `/api/gdpr/data` | GET | 越权查看他人数据 (IDOR), 数据泄露, 认证绕过 | P0 |
| 5 | `/api/gdpr/account` | DELETE | 账户删除权限校验, 软删除绕过 | P1 |
| 6 | `/api/admin/*` | ANY | 角色提升 (user→admin), 权限绕过 | P0 |

### 2.3 名片模块 — `/api/brochures/*`

| # | 端点 | 方法 | 测试重点 | 优先级 |
|---|------|------|----------|--------|
| 7 | `/api/brochures/` | POST | JSON注入, 文件上传绕过 (SVG/XSS), SQL注入 | P0 |
| 8 | `/api/brochures/{id}` | GET | IDOR: 查看/篡改他人名片 | P0 |
| 9 | `/api/brochures/{id}/publish` | POST | 状态篡改, 未授权发布 | P1 |
| 10 | `/api/brochures/{id}` | PUT | 越权修改他人名片内容 | P0 |

### 2.4 匹配与解锁模块

| # | 端点 | 方法 | 测试重点 | 优先级 |
|---|------|------|----------|--------|
| 11 | `/api/match/*` | POST/GET | SQL注入(标签/评分参数), 越权查看他人匹配 | P0 |
| 12 | `/api/unlock` | POST | 配额绕过, 重复解锁, 解锁他人联系信息 | P0 |

### 2.5 支付模块 — `/api/payment/*`

| # | 端点 | 方法 | 测试重点 | 优先级 |
|---|------|------|----------|--------|
| 13 | `/api/payment/create` | POST | 金额篡改, 优惠券滥用, 重放攻击 | P0 |
| 14 | `/api/payment/webhook` | POST | 签名验证绕过, 重放, SSRF | P0 |

### 2.6 集成与文件模块

| # | 端点 | 方法 | 测试重点 | 优先级 |
|---|------|------|----------|--------|
| 15 | `/api/webhooks/*` | POST | SSRF (回调任意URL), 签名验证, 注入payload | P0 |
| 16 | `/api/export/*` | GET | 路径遍历, 文件泄露, 批量数据导出 | P1 |
| 17 | `/api/ai/*` | POST | Prompt注入 (AI Assist), 敏感数据泄露 via AI | P1 |
| 18 | `/api/integrations/*` | POST | OAuth token泄露, 第三方API密钥泄露 | P1 |

### 2.7 公开与分享模块

| # | 端点 | 方法 | 测试重点 | 优先级 |
|---|------|------|----------|--------|
| 19 | `/api/public/brochures/{share_token}` | GET | share_token可预测性, 越权浏览 | P1 |
| 20 | `/api/public/*` | ANY | 敏感信息泄露 (用户列表, 统计数据) | P2 |

---

## 3. 测试用例详情

### 3.1 认证绕过测试用例

| ID | 名称 | 步骤 | 预期 | 验证方式 |
|----|------|------|------|----------|
| AUTH-01 | JWT alg=none 攻击 | 将 JWT header alg 改为 `none`, 移除签名部分 | 服务端应拒绝, 返回 401 | 手动构造 JWT |
| AUTH-02 | JWT 弱密钥爆破 | 使用 jwt_tool / hashcat 爆破 JWT 密钥 | 密钥应 ≥256位随机, 不可爆破 | 抓取 token 测试 |
| AUTH-03 | JWT 过期token重用 | 使用过期 JWT 访问受保护端点 | 应返回 401 Token expired | 修改 exp 声明 |
| AUTH-04 | 未认证访问 | 不携带 Authorization header 访问受保护端点 | 应返回 401 | 遍历所有端点 |
| AUTH-05 | API Key 枚举 | 使用随机字符串作为 X-API-Key | 应返回 401, 无信息泄露 | 批量测试 |
| AUTH-06 | 密码暴力破解 | 对 `/api/auth/login` 发送大量错误密码 | 应触发速率限制/账户锁定 | 脚本自动化 |
| AUTH-07 | OAuth CSRF 绕过 | 修改 OAuth state 参数或省略 | 应验证 state 一致性 | 手动测试 |
| AUTH-08 | Session 固定攻击 | 登录前后 session ID 应变更 | 成功登录后应签发新 token | 比较前后 token |

### 3.2 注入测试用例

| ID | 名称 | 步骤 | 预期 | 验证方式 |
|----|------|------|------|----------|
| INJ-01 | SQLi — 搜索参数 | 在 `name`, `company`, `title` 参数中注入 `' OR 1=1--` | 不应返回异常数据 | sqlmap 自动化 |
| INJ-02 | SQLi — 数字型 ID | 在 `brochure_id`, `user_id`, `match_record_id` 注入 `1 UNION SELECT ...` | 应拒绝或参数化处理 | 手动 + sqlmap |
| INJ-03 | NoSQLi — JSON 参数 | 在 JSON body 注入 `$ne`, `$gt`, `$where` 操作符 | 应过滤操作符 | 手动构造 |
| INJ-04 | JSON 注入 | 在 `detail`, `intro` 等文本字段注入 JSON 特殊字符 | 应正确转义 | Burp 测试 |
| INJ-05 | XSS — 名片内容 | 在 `title`, `content`, `intro` 注入 `<script>alert(1)</script>` | 应 HTML 编码后输出 | 浏览器验证 |
| INJ-06 | 命令注入 | 在文件路径/URL参数注入 `; ls` / `| whoami` | 应拒绝 | 手动测试 |

### 3.3 越权测试用例 (IDOR / Privilege Escalation)

| ID | 名称 | 步骤 | 预期 | 验证方式 |
|----|------|------|------|----------|
| IDOR-01 | 横向越权 — 名片 | 用户A修改 URL 中的 user_id/brochure_id 为用户B的 | 应返回 403, 不允许访问他人资源 | 双账户测试 |
| IDOR-02 | 横向越权 — 用户资料 | 用户A修改 `/api/users/{id}` 中的 id 为用户B的 | 应只能访问自己的资料 | 双账户测试 |
| IDOR-03 | 横向越权 — 解锁信息 | 用户A尝试解锁用户B已经解锁的联系信息 | 应只允许解锁自己的匹配 | 双账户测试 |
| IDOR-04 | 纵向越权 — 角色提升 | 普通用户调用 `/api/admin/*` 端点 | 应返回 403 | 角色切换测试 |
| IDOR-05 | 纵向越权 — API Key 提升 | 普通API Key尝试调用管理员API | 应校验权限 | 创建不同权限key测试 |
| IDOR-06 | 团队数据越权 | 团队成员A查看非本团队数据 | 应校验 tenant_id / team_id | 多团队测试 |

### 3.4 敏感数据泄露测试用例

| ID | 名称 | 步骤 | 预期 | 验证方式 |
|----|------|------|----------|------|
| LEAK-01 | PII 明文泄露 | 检查 API 响应中 phone, wechat_openid 是否被脱敏 | 应 mask 中间 4 位 | 遍历响应字段 |
| LEAK-02 | 错误信息泄露 | 触发错误观察返回信息 (traceback, DB schema) | 应返回通用错误信息 | 触发各类错误 |
| LEAK-03 | 调试接口暴露 | 访问 /docs, /redoc, /debug, /test 等端点 | 生产环境应禁用 | 扫描 |
| LEAK-04 | CORS 过宽 | 检查 CORS header 是否允许不受信任的 origin | 应限制白名单 | 修改 Origin header |
| LEAK-05 | 响应头信息泄露 | 检查 Server, X-Powered-By 等 header | 应移除或伪装 | 响应头检查 |
| LEAK-06 | 目录遍历 | URL path 尝试 `../../etc/passwd`, `../../.env` | 应拒绝路径遍历 | manual |
| LEAK-07 | 批量数据导出 | 多次调用导出接口, 观察是否无限制 | 应有速率限制和验证 | 脚本测试 |
| LEAK-08 | 审计日志泄露 | 非管理员查看他人审计日志 | 应只显示自己的日志 | 越权测试 |

### 3.5 SSRF 测试用例

| ID | 名称 | 步骤 | 预期 | 验证方式 |
|----|------|------|----------|------|
| SSRF-01 | 内网回环 | 在 webhook/AI 服务 URL 传入 `http://127.0.0.1:8000` | 应禁止内网地址 | 手动 |
| SSRF-02 | 云元数据 | 传入 `http://169.254.169.254/latest/meta-data/` | 应禁止 | 手动 |
| SSRF-03 | DNS 重绑定 | 使用域名轮换解析至内网 IP | 应验证 IP 而非域名 | 专业工具 |

### 3.6 业务逻辑漏洞测试用例

| ID | 名称 | 步骤 | 预期 | 验证方式 |
|----|------|------|----------|------|
| BIZ-01 | 解锁配额绕过 | 多次调用 unlock 超出 quota | 应拒绝并返回配额耗尽 | 脚本测试 |
| BIZ-02 | 支付金额篡改 | 修改支付请求中的金额参数 | 金额应以服务端为准 | 中间人测试 |
| BIZ-03 | 优惠券重放 | 同一优惠券码多次使用 | 应标记已使用 | 测试 |
| BIZ-04 | 匹配次数耗尽 | 频繁调用匹配接口超限 | 应受速率限制控制 | 脚本测试 |
| BIZ-05 | share_token 碰撞 | 枚举 share_token 获取非公开名片 | token 应高熵不可预测 | 统计分析 |

---

## 4. 测试工具与环境

### 4.1 推荐工具链

| 工具 | 用途 | 命令示例 |
|------|------|----------|
| **Burp Suite Professional** | 全面拦截/重放/扫描 | 手动操作 |
| **OWASP ZAP** | 自动化被动扫描 | `zap.sh -daemon -port 8080` |
| **sqlmap** | SQL 注入自动化 | `sqlmap -u "http://target/api/brochures?id=1" --batch` |
| **jwt_tool** | JWT 安全测试 | `python jwt_tool.py <token> -T` |
| **Nuclei** | 漏洞模板扫描 | `nuclei -u https://api-staging.example.com` |
| **nikto** | Web 服务器扫描 | `nikto -h https://api-staging.example.com` |
| **Trivy** | 容器/依赖扫描 | `trivy fs --severity HIGH,CRITICAL .` |

### 4.2 测试环境

| 项目 | 配置 |
|------|------|
| 测试目标 | `https://api-staging.example.com` (staging 环境) |
| 测试账户 | 预置: user_a (普通), user_b (普通), admin (管理员), enterprise (企业) |
| 测试数据 | 隔离数据库, 预填充 100+ 条模拟数据 |
| 网络隔离 | 测试环境与生产环境独立 VPC, 无数据交叉 |
| 测试窗口 | 2026-07-07 ~ 2026-07-14 |

---

## 5. 报告与修复流程

```
发现漏洞 → 分级 → 报告 → 修复 → 复测 → 关闭
  │         │        │       │       │
  ├─ Critical  → 24h → 24h → 即时  → 48h
  ├─ High      → 48h → 48h → 72h  → 1周
  ├─ Medium    → 1周 → 1周 → 2周  → 2周
  └─ Low       → 1月 → 1月 → 1月  → 1月
```

### 漏洞等级定义

| 等级 | 定义 | 示例 |
|------|------|------|
| **Critical** | 可直接导致系统完全受损或数据批量泄露 | RCE, SQLi(写), 认证完全绕过 |
| **High** | 可导致单个用户数据泄露或权限提升 | IDOR, SQLi(读), JWT伪造 |
| **Medium** | 有限的信息泄露或配置问题 | XSS (非持久), 信息泄露, CSRF |
| **Low** | 低风险或需要复杂前提条件 | 缺少安全头, 版本信息泄露 |

---

*文档版本: v1.0 | 最后更新: 2026-07-01 | 审核人: [待定]*
