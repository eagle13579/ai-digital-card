# 结构化日志规范 (Structured Logging Standards)

> **项目**: AI 数智名片 (AI Digital Business Card)
> **版本**: v1.0
> **生效日期**: 2026-07-01
> **适用范围**: 后端 API 服务 (`backend/app`)、AI 服务 (`ai_service`)
> **维护人**: 运维团队

---

## 目录

1. [日志级别定义](#1-日志级别定义)
2. [日志字段 Schema](#2-日志字段-schema)
3. [日志分类与 Logger 命名](#3-日志分类与-logger-命名)
4. [敏感数据脱敏规则](#4-敏感数据脱敏规则)
5. [生产日志配置](#5-生产日志配置)
6. [日志采集与传输](#6-日志采集与传输)
7. [审计日志规范](#7-审计日志规范)
8. [常见场景示例](#8-常见场景示例)
9. [修订历史](#9-修订历史)

---

## 1. 日志级别定义

### 1.1 级别总览

| 级别 | 数值 | 颜色 | 含义 | 典型场景 |
|------|------|------|------|----------|
| **DEBUG** | 10 | 灰色 | 调试信息，仅开发/测试环境 | SQL 语句、变量值、函数入参 |
| **INFO** | 20 | 绿色 | 正常业务事件，生产默认级别 | 请求完成、用户注册、名片创建 |
| **WARNING** | 30 | 黄色 | 非异常但需关注的情况 | 缓慢查询(>500ms)、降级策略触发、重试 |
| **ERROR** | 40 | 红色 | 功能异常但服务可继续运行 | DB 连接失败、第三方 API 错误、业务异常 |
| **CRITICAL** | 50 | 深红 | 严重故障，需立即人工介入 | 应用启动失败、数据完整性损坏 |

### 1.2 使用原则

```
DEBUG → 开发人员调试用，禁止在生产环境频繁输出
INFO  → 业务关键路径（请求进/出、状态变更、数据增删改）
WARNING → 潜在风险（重试、降级、限流触发、慢查询>500ms）
ERROR → 确定异常但可恢复（第三方超时、数据库连接池耗尽）
CRITICAL → 应用级崩溃（初始化失败、配置错误、panic）
```

### 1.3 禁止事项

- ❌ 禁止在 `ERROR` 级别记录业务预期内的"正常异常"（如 401 认证失败用 INFO）
- ❌ 禁止在日志中拼接敏感数据（密码、Token、完整手机号）
- ❌ 禁止在循环中高频输出 DEBUG 日志（频率 > 100条/秒）
- ❌ 禁止使用 `print()` 替代日志框架

---

## 2. 日志字段 Schema

所有日志行采用 **JSON 格式** 输出，统一 schema 如下。

### 2.1 基础字段 (所有日志行必须包含)

```json
{
  "timestamp": "2026-07-01T14:30:00.123Z",
  "level": "INFO",
  "logger": "app.access",
  "message": "request_completed",
  "service": "ai-digital-business-card",
  "environment": "production"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `timestamp` | string | ✅ | ISO 8601 UTC，精确到毫秒 |
| `level` | string | ✅ | `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL` |
| `logger` | string | ✅ | Logger 名称（见 [§3](#3-日志分类与-logger-命名)） |
| `message` | string | ✅ | 事件简述英文 kebab-case（如 `request_completed`） |
| `service` | string | ✅ | 固定为 `ai-digital-business-card` |
| `environment` | string | ✅ | `development`/`staging`/`production` |

### 2.2 HTTP 请求日志 (`app.access`)

对应 `app/middleware/logging_middleware.py` 中的 `LoggingMiddleware`。

```json
{
  "timestamp": "2026-07-01T14:30:00.123Z",
  "level": "INFO",
  "logger": "app.access",
  "message": "request_completed",
  "method": "POST",
  "path": "/api/brochures",
  "status": 201,
  "duration_ms": 45.23,
  "request_id": "abc-123-def",
  "user_id": "42",
  "ip": "10.0.1.5"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `method` | string | ✅ | HTTP 方法 |
| `path` | string | ✅ | 请求路径（不含 query） |
| `status` | int | ✅ | HTTP 状态码 |
| `duration_ms` | float | ✅ | 请求耗时(毫秒) |
| `request_id` | string | ✅ | 全链路追踪 ID（UUID） |
| `user_id` | string | 可选 | 已认证用户 ID，未登录为空 |
| `ip` | string | 可选 | 客户端 IP（中间件按需添加） |

### 2.3 业务审计日志 (`audit`)

对应 `app/models/audit.py` 的 `audit_logs` 数据库表，同时会输出到日志。

```json
{
  "timestamp": "2026-07-01T14:30:00.123Z",
  "level": "INFO",
  "logger": "audit",
  "message": "AUDIT:CREATE /api/brochures",
  "user_id": 42,
  "action": "CREATE",
  "resource": "/api/brochures",
  "detail": "{\"method\":\"POST\",\"status\":201,\"path\":\"/api/brochures\"}",
  "ip": "10.0.1.5",
  "user_agent": "Mozilla/5.0 ..."
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | ✅ | `CREATE`/`READ`/`UPDATE`/`DELETE`/`LOGIN`/`EXPORT`/`DELETE_ACCOUNT` |
| `resource` | string | ✅ | 操作的资源路径 |
| `detail` | string | 可选 | JSON 字符串的详情摘要 |
| `ip` | string | ✅ | 客户端 IP |
| `user_agent` | string | 可选 | 客户端 User-Agent（截断到 512 字符） |

### 2.4 数据库监控日志 (`db_monitor`)

对应 `app/database_monitor.py` 的慢查询检测。

```json
{
  "timestamp": "2026-07-01T14:30:00.123Z",
  "level": "WARNING",
  "logger": "db_monitor",
  "message": "SLOW_QUERY (853.2 ms) | SELECT * FROM brochures WHERE ...",
  "duration_ms": 853.2,
  "query_preview": "SELECT * FROM brochures WHERE ..."
}
```

### 2.5 Web Vitals 日志

对应 `app/routers/web_vitals.py`。

```json
{
  "timestamp": "2026-07-01T14:30:00.123Z",
  "level": "INFO",
  "logger": "app.routers.web_vitals",
  "message": "[Web Vitals][LCP] value=2500.00 rating=poor nav=navigate page=https://liankebao.top/card/abc",
  "metric": "LCP",
  "value": 2500.0,
  "rating": "poor",
  "delta": 100.0,
  "navigation_type": "navigate",
  "page_url": "https://liankebao.top/card/abc"
}
```

### 2.6 OpenTelemetry Span 字段

| 字段 | 说明 |
|------|------|
| `span_id` | Span 唯一 ID (16 字节 hex) |
| `trace_id` | Trace 唯一 ID (32 字节 hex) |
| `parent_span_id` | 父 Span ID |
| `span.kind` | `SERVER`/`CLIENT`/`INTERNAL`/`PRODUCER`/`CONSUMER` |
| `duration` | Span 耗时(微秒) |

---

## 3. 日志分类与 Logger 命名

### 3.1 Logger 约定

| Logger 名称 | 负责模块 | 配置级别 | 说明 |
|-------------|----------|----------|------|
| `app.access` | HTTP 请求日志 | INFO | JSON 格式，始终输出到独立文件 |
| `audit` | 审计日志 | INFO | 所有审计事件，合规保留 180 天 |
| `db_monitor` | 数据库监控 | INFO | 慢查询(>500ms) 和连接池状态 |
| `app.routers.*` | 业务路由 | INFO | 业务模块日志（按模块名自动命名） |
| `app.middleware.*` | 中间件 | INFO | 中间件运行日志（如限流、认证） |
| `app.services.*` | 业务服务 | INFO | 服务层逻辑（CRM 同步、消息推送） |
| `app.ai.*` | AI 能力 | INFO | AI 推理、RAG、向量搜索 |
| `app.cache` | Redis 缓存 | INFO | 缓存命中/未命中、连接状态 |
| `sentry_sdk` | Sentry SDK | WARNING | 仅记录 Sentry 自身问题 |
| `sqlalchemy.engine` | SQLAlchemy | WARNING | 仅生产环境设为 WARNING，开发环境可 DEBUG |
| `uvicorn` | ASGI 服务 | INFO | Uvicorn 访问日志 |
| `root` | 所有其他模块 | WARNING | 兜底配置 |

### 3.2 `logging_middleware.py` JSON 格式化器

现有 `JSONFormatter` 自动将 `logging.LogRecord` 的 `extra` 字段合并到 JSON 输出中。业务代码可通过以下方式添加结构化字段：

```python
logger = logging.getLogger("app.routers.brochure")

# 正确：通过 extra 参数传递结构化字段
logger.info(
    "brochure_created",
    extra={"brochure_id": brochure.id, "user_id": user_id, "duration_ms": 123.4},
)
```

不要将结构化数据拼接到 message 字符串中。

---

## 4. 敏感数据脱敏规则

### 4.1 必须脱敏的字段

| 数据类型 | 脱敏方式 | 示例输入 | 示例输出 |
|----------|----------|----------|----------|
| 密码 | 完全隐藏 | `myp@ss123` | `***` |
| JWT/Token | 保留前 8 位 | `eyJhbGciOiJIUzI1NiIs...` | `eyJhbGci***` |
| 手机号 | 保留前 3 + 后 4 | `13812345678` | `138****5678` |
| 邮箱 | 保留第一个字符 + 域名 | `alice@example.com` | `a***@example.com` |
| 身份证 | 保留前 6 + 后 4 | `110101199001011234` | `110101****1234` |
| 银行卡号 | 保留后 4 | `6222021234567890` | `****7890` |
| 真实姓名 | 保留姓 + `*` | `张三` | `张*` |
| 详细地址 | 保留到市级 | `北京市海淀区中关村大街1号` | `北京市***` |
| IP 地址 | 保留前 3 段 | `10.10.10.5` | `10.10.10.*` |

### 4.2 脱敏工具函数

建议在 `app/utils/logging.py` 中实现：

```python
import re

SENSITIVE_PATTERNS = {
    "password": re.compile(r'"password"\s*:\s*"[^"]+"'),
    "token": re.compile(r'(Bearer\s+)(\S{8})\S+'),
    "phone": re.compile(r'(1[3-9]\d)\d{4}(\d{4})'),
    "email": re.compile(r'(.)[^@]+(@.+)'),
}


def mask_sensitive(value: str, field_type: str) -> str:
    """对敏感字段进行脱敏。"""
    if field_type == "password":
        return "***"
    elif field_type == "token":
        return value[:8] + "***" if len(value) > 8 else "***"
    elif field_type == "phone":
        return value[:3] + "****" + value[-4:] if len(value) == 11 else value
    elif field_type == "email":
        parts = value.split("@")
        return parts[0][0] + "***@" + parts[1] if len(parts) == 2 else value
    return value


def sanitize_log_data(data: dict) -> dict:
    """递归脱敏日志字典中的敏感字段。"""
    sensitive_keys = {"password", "token", "access_token", "refresh_token",
                      "secret", "authorization", "credit_card", "id_card",
                      "phone", "email", "real_name", "address"}
    sanitized = {}
    for k, v in data.items():
        if k.lower() in sensitive_keys:
            sanitized[k] = mask_sensitive(str(v), k.lower())
        elif isinstance(v, dict):
            sanitized[k] = sanitize_log_data(v)
        elif isinstance(v, list):
            sanitized[k] = [
                sanitize_log_data(item) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            sanitized[k] = v
    return sanitized
```

### 4.3 脱敏检查清单

- [ ] 请求/响应体中的密码字段 → `***`
- [ ] `Authorization` 请求头中的 JWT → 保留前 8 位
- [ ] `Set-Cookie` 响应头 → 仅记录 cookie 名称
- [ ] 用户 Profile API 响应中的手机/邮箱 → 必须脱敏后再记录日志
- [ ] 审计日志的 `detail` 字段 → 必须经过 `sanitize_log_data()` 函数

---

## 5. 生产日志配置

### 5.1 推荐配置 (`config/logging.yaml`)

```yaml
version: 1
disable_existing_loggers: false

formatters:
  json:
    class: app.middleware.logging_middleware.JSONFormatter
  console:
    format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

handlers:
  # 结构化 JSON 输出到 stdout（容器环境）
  stdout_json:
    class: logging.StreamHandler
    stream: ext://sys.stdout
    formatter: json
    level: INFO

  # 审计日志独立文件（合规保留 180 天）
  audit_file:
    class: logging.handlers.RotatingFileHandler
    filename: /var/log/app/audit.log
    maxBytes: 104857600  # 100MB
    backupCount: 10
    formatter: json
    level: INFO

  # 错误日志独立文件
  error_file:
    class: logging.handlers.RotatingFileHandler
    filename: /var/log/app/error.log
    maxBytes: 104857600  # 100MB
    backupCount: 30
    formatter: json
    level: WARNING

loggers:
  app.access:
    level: INFO
    handlers: [stdout_json]
    propagate: false
  audit:
    level: INFO
    handlers: [audit_file, stdout_json]
    propagate: false
  db_monitor:
    level: INFO
    handlers: [stdout_json, error_file]
    propagate: false
  app:
    level: INFO
    handlers: [stdout_json]
    propagate: false
  sqlalchemy.engine:
    level: WARNING
    handlers: [error_file]
    propagate: false

root:
  level: WARNING
  handlers: [stdout_json]
```

### 5.2 日志文件保留策略

| 日志类别 | 保留周期 | 存储位置 | 归档策略 |
|----------|----------|----------|----------|
| 访问日志 (access) | 30 天 | stdout (容器) / 日志平台 | 由日志平台管理 |
| 审计日志 (audit) | 180 天（合规要求） | `/var/log/app/audit.log` | 滚动 100MB x 10，归档到 S3 |
| 错误日志 (error) | 90 天 | `/var/log/app/error.log` | 滚动 100MB x 30 |
| 慢查询日志 | 30 天 | 随 error.log | 由 Sentry/Prometheus 辅助 |
| 调试日志 (debug) | 7 天 | `/var/log/app/debug.log` | 仅开发/预发布环境 |

---

## 6. 日志采集与传输

### 6.1 采集架构

```
应用容器 ──stdout──→ 日志代理 (Vector/Fluentd) ──→ 日志存储 (Elasticsearch/Loki)
                    │
                    └──→ 审计日志文件 ──→ S3 归档 (合规)
```

### 6.2 结构化要求

- 所有日志行必须是 **合法的单行 JSON**（一行一条日志）
- 禁止多行日志（Exception traceback 需转为单行或由采集代理处理）
- 日志行尾使用 `\n` 分隔，**不加逗号**（非 JSON Array）

### 6.3 环境变量控制

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LOG_LEVEL` | `INFO` | 全局日志级别 |
| `LOG_FORMAT` | `json` | `json` 或 `console` |
| `ENABLE_OTEL` | `false` | 是否启用 OpenTelemetry 追踪 |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | OTLP gRPC/HTTP 端点地址 |

---

## 7. 审计日志规范

### 7.1 记录原则

- **所有 CREATE / UPDATE / DELETE 操作** → 必须记录审计日志
- **关键 READ 操作**（如导出、查看他人名片、API key 管理）→ 记录审计日志
- **健康检查 `/health`、指标 `/metrics`、静态文件** → 跳过审计（已在 `audit.py` 的 `_should_skip()` 中配置）

### 7.2 Action 枚举

| Action | 说明 | 触发场景 |
|--------|------|----------|
| `CREATE` | 资源创建 | POST 请求、用户注册、名片创建 |
| `READ` | 资源读取 | GET 关键资源（API 调用） |
| `UPDATE` | 资源更新 | PUT/PATCH 请求 |
| `DELETE` | 资源删除 | DELETE 请求 |
| `LOGIN` | 用户登录 | 认证成功 |
| `LOGOUT` | 用户登出 | 主动登出 |
| `EXPORT` | 数据导出 | GDPR 数据导出、CSV 导出 |
| `DELETE_ACCOUNT` | 账户注销 | 用户主动注销 |
| `WEBHOOK` | Webhook 事件 | 第三方通知推送 |

### 7.3 保留与安全

- 审计日志 **禁止删除**（仅可归档）
- 审计日志 **禁止修改**（Append-only）
- 审计日志保留 **180 天**（GDPR 合规要求）
- 审计日志独立于业务数据库，防止业务故障影响审计记录

---

## 8. 常见场景示例

### 8.1 请求成功

```python
# logging_middleware.py (已有)
logger.info(
    "request_completed",
    extra={
        "method": method,
        "path": path,
        "status": status_code,
        "duration_ms": duration_ms,
        "request_id": request_id,
        "user_id": user_id,
    },
)
```

### 8.2 请求异常

```python
# logging_middleware.py (已有)
logger.error(
    "request_failed",
    extra={
        "method": method,
        "path": path,
        "status": 500,
        "duration_ms": duration_ms,
        "request_id": request_id,
        "user_id": user_id,
        "error": str(exc),
    },
)
```

### 8.3 慢查询告警

```python
# database_monitor.py (已有)
logger.warning(
    "SLOW_QUERY (%.1f ms) | %s",
    elapsed_ms,
    stmt_str,
)
```

### 8.4 手动记录审计事件

```python
from app.middleware.audit import record_audit

await record_audit(
    db=db,
    user_id=current_user.id,
    action="EXPORT",
    resource="/api/gdpr/data",
    detail={"export_type": "full", "record_count": 150},
    ip=request.client.host,
    user_agent=request.headers.get("user-agent", ""),
)
```

### 8.5 业务日志（含结构化字段）

```python
logger = logging.getLogger("app.services.crm_bridge")

logger.info(
    "crm_sync_completed",
    extra={
        "crm_type": "salesforce",
        "record_count": 42,
        "duration_ms": 1234.5,
        "errors": 0,
    },
)
```

---

## 9. 修订历史

| 版本 | 日期 | 修改内容 | 修订人 |
|------|------|----------|--------|
| v1.0 | 2026-07-01 | 初始版本 — 结构化日志规范、字段 schema、脱敏规则 | — |

---

*本规范由 AI 数智名片运维团队维护 | 联系: support@liankebao.top | 最后更新: 2026-07-01*
