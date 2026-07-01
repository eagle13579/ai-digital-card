# 邮件服务配置文档

> AI 数字名片 — 邮件发送服务(SMTP)配置与运维手册
> 最后更新: 2026-07-01

---

## 目录

1. [概述](#1-概述)
2. [环境变量配置](#2-环境变量配置)
3. [SMTP 服务商推荐](#3-smtp-服务商推荐)
4. [服务降级策略](#4-服务降级策略)
5. [邮件模板系统](#5-邮件模板系统)
6. [代码结构](#6-代码结构)
7. [使用示例](#7-使用示例)
8. [运维与监控](#8-运维与监控)
9. [常见问题](#9-常见问题)

---

## 1. 概述

邮件服务用于发送系统通知邮件，包括：

| 邮件类型 | 触发时机 | 模板 |
|----------|----------|------|
| **新用户欢迎** | 用户注册成功 | `welcome_html()` |
| **试用 3 天到期** | 试用到期前 3 天 | `trial_expiring_3d_html()` |
| **试用 1 天到期** | 试用到期前 1 天 | `trial_expiring_1d_html()` |
| **试用已到期** | 试用到期当天 | `trial_expired_html()` |
| **CRM 新联系人** | CRM 自动创建/手动添加联系人 | `crm_new_contact_html()` |

核心设计原则：

- **纯标准库实现**：仅依赖 `smtplib` + `email` 模块，无第三方邮件库
- **自动降级**：SMTP 未配置时自动降级为日志输出，不影响业务流程
- **异步友好**：SMTP 发送在线程池中执行，不阻塞事件循环
- **模板无依赖**：邮件模板使用 Python f-string 渲染，无 Jinja2 等外部模板引擎

---

## 2. 环境变量配置

### 2.1 配置项列表

所有配置项在 `backend/app/config.py` 的 `Settings` 类中定义，从 `.env` 文件读取：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `SMTP_HOST` | `""` | SMTP 服务器地址。**为空则邮件服务降级为日志输出** |
| `SMTP_PORT` | `587` | SMTP 端口 (587=TLS, 465=SSL) |
| `SMTP_USER` | `""` | SMTP 登录用户名 |
| `SMTP_PASSWORD` | `""` | SMTP 登录密码 |
| `SMTP_USE_TLS` | `True` | 是否使用 TLS (True=端口587, False=端口465 SSL) |
| `SMTP_FROM` | `noreply@aibizcard.com` | 发件人邮箱地址 |
| `SMTP_FROM_NAME` | `AI数智名片` | 发件人显示名称 |

### 2.2 `.env` 配置示例

```bash
# ── 邮件服务 (SMTP) ─────────────────────────────────────────────────────────
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@aibizcard.com
SMTP_PASSWORD=your-smtp-password
SMTP_USE_TLS=true
SMTP_FROM=noreply@aibizcard.com
SMTP_FROM_NAME=AI数智名片
```

### 2.3 配置加载机制

```
.env 文件 → pydantic-settings (Settings类) → EmailService.__init__()
```

配置在 `EmailService` 实例化时（模块加载时）读取，之后全局共享。如需运行时重载，需重启应用。

---

## 3. SMTP 服务商推荐

### 3.1 国内服务商

| 服务商 | SMTP 地址 | 端口 | TLS/SSL | 免费额度 | 备注 |
|--------|-----------|------|---------|----------|------|
| **阿里云邮件推送** | `smtpdm.aliyun.com` | 465 | SSL | 1000封/日 | 需域名备案 |
| **腾讯云邮件推送** | `ses.smtp.tencent.com` | 587 | TLS | 1000封/月 | 需域名备案 |
| **SendCloud** | `smtp.sendcloud.net` | 587 | TLS | 100封/日 | 注册送试用 |

### 3.2 国际服务商

| 服务商 | SMTP 地址 | 端口 | TLS/SSL | 免费额度 |
|--------|-----------|------|---------|----------|
| **SendGrid** | `smtp.sendgrid.net` | 587 | TLS | 100封/日 |
| **Mailgun** | `smtp.mailgun.org` | 587 | TLS | 5000封/月 |
| **Amazon SES** | `email-smtp.region.amazonaws.com` | 587 | TLS | 200封/日 |
| **Gmail SMTP** | `smtp.gmail.com` | 587 | TLS | 500封/日 (有限制) |

> **建议**：生产环境推荐使用 **阿里云邮件推送** 或 **SendGrid**，支持高并发、有完善的送达率和反垃圾机制。

---

## 4. 服务降级策略

### 4.1 无配置降级

当 `SMTP_HOST` 为空（或全部 SMTP 配置缺失）时：

- `email_service.enabled` → `False`
- `email_service.send()` → 仅输出日志，返回 `{"success": True, "sent": False}`
- **业务流程不受影响**：订阅通知、CRM 通知等所有业务逻辑正常执行

日志示例：
```
[EmailService/DEGRADED] to=user@example.com subject=试用到期提醒 body_preview=⚠️ 试用到期提醒...
```

### 4.2 SMTP 连接失败降级

当 SMTP 配置存在但连接失败时：

- `email_service.send()` → 捕获异常，记录错误日志
- 返回 `{"success": False, "sent": False, "error": "..."}`
- **不抛出异常**，调用方无需 try-catch

### 4.3 用户无邮箱降级

当 `User.email` 字段不存在或为空时：

- `subscription_notifier._send_trial_email()` → 跳过邮件发送
- 记录 `[TrialNotify/Email] 用户 xxx 无邮箱，跳过邮件发送`
- 日志通道（`[TrialNotify]`）始终正常输出

---

## 5. 邮件模板系统

### 5.1 模板文件

所有模板集中定义在 `backend/app/services/email_templates.py`，无需额外模板目录。

### 5.2 模板函数签名

| 函数 | 参数 | 返回 |
|------|------|------|
| `welcome_html(name, login_url)` | 用户姓名、登录链接 | 完整 HTML |
| `trial_expiring_3d_html(name, company_name, end_date, upgrade_url)` | 姓名、企业名、到期日、升级链接 | 完整 HTML |
| `trial_expiring_1d_html(name, company_name, end_date, upgrade_url)` | 同上 | 完整 HTML |
| `trial_expired_html(name, company_name, end_date, upgrade_url)` | 同上 | 完整 HTML |
| `crm_new_contact_html(owner_name, contact_name, contact_company, contact_title, contact_email, contact_phone, source, crm_url)` | 联系人信息 | 完整 HTML |

### 5.3 模板框架

所有模板使用统一的 HTML 邮件框架：

- **响应式布局**：`max-width: 600px`，适配移动端
- **品牌色**：蓝色系 `#1890ff` / `#096dd9`
- **中文友好**：PingFang SC / Microsoft YaHei 字体栈
- **内联样式**：兼容主流邮件客户端（Outlook、Gmail、QQ邮箱）

### 5.4 添加新模板

```python
# 1. 在 email_templates.py 中添加模板函数
def my_new_template(*, name: str, ...) -> str:
    body = """..."""
    return _render(subject="...", header_title="...", body=body)

# 2. 在 services/__init__.py 中导出
# 3. 在业务代码中调用
from app.services.email_templates import my_new_template
html = my_new_template(name="张三", ...)
await email_service.send(to="user@example.com", subject="...", html=html)
```

---

## 6. 代码结构

```
backend/app/services/
├── email_service.py        # 📧 邮件发送核心服务
│   ├── EmailService        # 类：send(), _build_message(), _send_smtp()
│   └── email_service       # 全局单例实例
│
├── email_templates.py      # 📝 邮件 HTML 模板
│   ├── welcome_html()
│   ├── trial_expiring_3d_html()
│   ├── trial_expiring_1d_html()
│   ├── trial_expired_html()
│   ├── crm_new_contact_html()
│   ├── _render()           # 统一框架包裹
│   ├── _btn()              # CTA 按钮组件
│   └── _info_row()         # 信息行组件
│
└── subscription_notifier.py # 🔔 试用通知（已集成邮件）
    ├── _get_user_email()   # 用户邮箱查询
    ├── _get_user_name()    # 用户姓名查询
    ├── _send_trial_email() # 试用邮件发送
    └── check_and_notify()  # 入口（日志+邮件）

backend/app/config.py       # ⚙️ SMTP 配置项定义
```

### 6.1 核心类 `EmailService`

```python
class EmailService:
    enabled: bool           # 是否已配置 SMTP
    send(to, subject, body, html, cc, bcc, reply_to) → dict
    # 返回: {"success": bool, "sent": bool, "to": str, "subject": str, "error": str | None}
```

---

## 7. 使用示例

### 7.1 在业务代码中直接使用

```python
from app.services.email_service import email_service
from app.services.email_templates import welcome_html

# 发送欢迎邮件
html = welcome_html(
    name="张三",
    login_url="https://aibizcard.com/login",
)
result = await email_service.send(
    to="zhangsan@example.com",
    subject="欢迎加入 AI数智名片",
    body="欢迎加入...",   # 纯文本 fallback
    html=html,           # HTML 版本
)

if result["success"]:
    print(f"邮件已{'发送' if result['sent'] else '记录日志'}")
```

### 7.2 发送纯文本邮件

```python
await email_service.send(
    to="user@example.com",
    subject="通知标题",
    body="这是一条纯文本通知。",
)
```

### 7.3 发送含附件邮件

当前 `send()` 不支持附件参数。如需附件，可直接使用 `MIMEMultipart` + `smtplib` 组合，或扩展 `EmailService` 类。

---

## 8. 运维与监控

### 8.1 日志查看

邮件服务的日志以 `[EmailService]` 为前缀：

```bash
# 查看所有邮件相关日志
grep "\[EmailService\]" /var/log/app/app.log

# 查看发送失败的邮件
grep "\[EmailService\] 邮件发送失败" /var/log/app/app.log

# 查看降级模式
grep "\[EmailService/DEGRADED\]" /var/log/app/app.log
```

试用通知的邮件日志以 `[TrialNotify/Email]` 为前缀：

```bash
grep "\[TrialNotify/Email\]" /var/log/app/app.log
```

### 8.2 健康检查

可通过发送测试邮件验证配置：

```python
# 在 Python shell 中测试
import asyncio
from app.services.email_service import email_service

async def test():
    result = await email_service.send(
        to="admin@example.com",
        subject="测试邮件 - AI数智名片",
        body="这是一封测试邮件，用于验证 SMTP 配置。",
    )
    print(result)

asyncio.run(test())
```

### 8.3 监控指标

建议监控以下指标：

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| `email.send.success` | 发送成功计数 | — |
| `email.send.failure` | 发送失败计数 | > 5 次/小时 |
| `email.send.degraded` | 降级次数（无配置） | > 0（提示未配置） |
| `email.smtp.latency` | SMTP 连接耗时 | > 5 秒 |

---

## 9. 常见问题

### Q1: 邮件发送失败怎么办？

1. 检查 `.env` 中 SMTP 配置是否正确
2. 检查 SMTP 端口是否被防火墙阻断
3. 检查 SMTP 账户是否有发送权限
4. 查看应用日志中的错误信息：
   ```
   [EmailService] 邮件发送失败 to=xxx error=...
   ```
5. 常见错误：
   - `(535, b'Login failed')` — 用户名或密码错误
   - `(504, b'...')` — SMTP 服务器拒绝连接
   - `TimeoutError` — 网络不通或端口被屏蔽

### Q2: 如何切换邮件服务商？

只需更新 `.env` 中的 SMTP 配置项，重启应用即可。无需修改代码。

### Q3: 为什么用户收不到邮件？

可能原因：
1. SMTP 未配置（检查 `SMTP_HOST` 是否为空）
2. 用户没有邮箱（User 模型无 `email` 字段）
3. 邮件被收件方标记为垃圾邮件（建议配置 SPF/DKIM）
4. SMTP 发送频率限制（部分服务商有每日配额）

### Q4: 用户模型是否需要添加 email 字段？

是的。当前 `User` 模型只有 `phone`，没有 `email` 字段。如需完整邮件支持，请在 `User` 模型中添加：

```python
email: Mapped[str] = mapped_column(String(128), default="", comment="邮箱")
```

或通过订阅的 `features` JSON 字段存储联系邮箱。

### Q5: 支持批量发送吗？

当前 `send()` 方法每次发送一封邮件。如需批量发送，循环调用即可：

```python
for user in users:
    await email_service.send(to=user.email, subject="...", body="...")
```

性能优化建议：可扩展 `EmailService` 添加 `send_bulk()` 方法使用 SMTP 的 `sendmail()` 多收件人能力。
