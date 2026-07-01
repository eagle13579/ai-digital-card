# 可观测性文档 (Observability Guide)

> **项目**: AI 数智名片 (AI Digital Business Card)
> **版本**: v1.0
> **生效日期**: 2026-07-01
> **适用范围**: 后端 API (`backend/app`)、AI 服务 (`ai_service`)、前端 (Web Vitals)
> **维护人**: 运维团队

---

## 目录

1. [可观测性架构总览](#1-可观测性架构总览)
2. [SLA / SLO / SLI 定义](#2-sla--slo--sli-定义)
3. [指标 (Metrics)](#3-指标-metrics)
4. [追踪 (Tracing)](#4-追踪-tracing)
5. [日志 (Logging)](#5-日志-logging)
6. [告警规则模板](#6-告警规则模板)
7. [仪表盘设计](#7-仪表盘设计)
8. [运行检查清单](#8-运行检查清单)
9. [修订历史](#9-修订历史)

---

## 1. 可观测性架构总览

### 1.1 三大支柱

```
┌─────────────────────────────────────────────────────────┐
│                  AI 数智名片 — 可观测性                   │
├─────────────────┬─────────────────┬─────────────────────┤
│     Metrics     │     Tracing     │      Logging         │
│  (Prometheus)   │ (OpenTelemetry) │  (JSON Structured)  │
├─────────────────┼─────────────────┼─────────────────────┤
│ • HTTP 请求指标  │ • 分布式追踪    │ • 访问日志(JSON)    │
│ • DB 查询延迟    │ • Span 链路     │ • 审计日志          │
│ • AI 推理延迟    │ • 依赖服务追踪   │ • 慢查询日志        │
│ • 缓存命中率     │ • 错误追踪      │ • 业务日志          │
│ • 活跃连接数     │                 │                     │
├─────────────────┴─────────────────┴─────────────────────┤
│                   采集与存储                              │
│  Prometheus ← MetricsMiddleware → /metrics 端点          │
│  OTLP Collector ← OpenTelemetry → Jaeger/Tempo           │
│  Vector/Fluentd ← stdout → Loki/Elasticsearch            │
└─────────────────────────────────────────────────────────┘
```

### 1.2 组件关系图

```
┌──────────┐    ┌──────────────────┐    ┌─────────────┐
│  用户/   │───→│  FastAPI 应用    │───→│  Prometheus  │
│  客户端   │    │                  │    │  (/metrics)  │
└──────────┘    │  ┌────────────┐  │    └──────┬──────┘
                │  │ Metrics    │  │           │
                │  │ Middleware │  │           ▼
                │  └────────────┘  │    ┌─────────────┐
                │  ┌────────────┐  │    │  Grafana     │
                │  │ Logging    │──┼───→│  Dashboard   │
                │  │ Middleware │  │    └─────────────┘
                │  └────────────┘  │
                │  ┌────────────┐  │    ┌─────────────┐
                │  │ OTEL       │──┼───→│  Jaeger /   │
                │  │ Middleware │  │    │  Tempo      │
                │  └────────────┘  │    └─────────────┘
                │  ┌────────────┐  │
                │  │ Audit      │──┼───→ 审计日志文件
                │  │ Middleware │  │
                │  └────────────┘  │    ┌─────────────┐
                │  ┌────────────┐  │    │  Web Vitals │
                │  │ Web Vitals │←─┼───│  (前端上报)  │
                │  │ Endpoint   │  │    └─────────────┘
                │  └────────────┘  │
                │  ┌────────────┐  │
                │  │ DB Monitor │──┼───→ 慢查询日志
                │  └────────────┘  │
                │  ┌────────────┐  │
                │  │ SLO Tracker│──┼───→ 实时 SLO 状态
                │  └────────────┘  │
                └──────────────────┘
```

---

## 2. SLA / SLO / SLI 定义

### 2.1 术语说明

| 术语 | 定义 | 本服务值 |
|------|------|----------|
| **SLA** | Service Level Agreement — 对外承诺的服务等级协议 | 99.9% 月度可用性（详见 [SLA.md](./SLA.md)） |
| **SLO** | Service Level Objective — 内部服务质量目标 | 可用性 ≥ 99.9%，P99 延迟 < 1s |
| **SLI** | Service Level Indicator — 实际服务质量指标 | 由 `slo_tracker.py` 实时计算 |

### 2.2 SLO 定义

#### 2.2.1 可用性 SLO

| 指标 | SLO 目标 | 测量窗口 | 计算方式 |
|------|----------|----------|----------|
| API 可用性 | ≥ **99.9%** | 滚动 1 小时 | `(总请求 - 5xx) / 总请求 × 100%` |
| AI 服务可用性 | ≥ **99.5%** | 滚动 1 小时 | `(AI 调用成功数) / (AI 调用总数) × 100%` |
| 数据库可用性 | ≥ **99.95%** | 滚动 1 小时 | 健康检查成功率达 ≥ 99.95% |

#### 2.2.2 延迟 SLO

| 指标 | P50 | P95 | P99 | 测量窗口 |
|------|:---:|:---:|:---:|:--------:|
| 轻量查询 API | ≤ 200ms | ≤ 500ms | ≤ 1s | 5 分钟 |
| 写入 API | ≤ 500ms | ≤ 1s | ≤ 3s | 5 分钟 |
| AI 流式 (首字) | ≤ 1s | ≤ 2s | ≤ 5s | 5 分钟 |
| DB 查询 | ≤ 50ms | ≤ 200ms | ≤ 500ms | 5 分钟 |

#### 2.2.3 错误预算 (Error Budget)

```
错误预算 = (1 - SLO) × 总请求量

示例（月度 99.9% SLO，月均 100 万请求）:
  错误预算 = (1 - 0.999) × 1,000,000 = 1,000 次错误/月

消耗规则:
  - 每发生一次 5xx 错误 → 消耗 1 个错误预算
  - 当错误预算剩余 < 20% → 触发 P2 告警
  - 当错误预算耗尽 (0%) → 停止所有非关键部署
```

#### 2.2.4 燃烧速率告警 (Burn Rate Alerts)

| 燃烧速率 | 时间窗口 | 触发条件 | 告警级别 |
|----------|----------|----------|----------|
| 2× (快速燃烧) | 1 小时 | 1 小时内消耗 5% 月度错误预算 | P1 |
| 6× (严重燃烧) | 10 分钟 | 10 分钟内消耗 2% 月度错误预算 | P0 |
| 1× (慢速燃烧) | 6 小时 | 6 小时内消耗 10% 月度错误预算 | P2 |

### 2.3 SLI 测量方式

参见 `app/slo_tracker.py` 的 `SLOTracker` 实现：

```python
# 现有代码 (slo_tracker.py)
slo_tracker.record_request(status_code=200, duration_ms=45.2)
sli = slo_tracker.get_sli()
# 返回: {"availability": 0.9995, "latency_p50": 0.12, ...}
```

**SLI 指标采集点：**

| SLI | 采集位置 | 数据源 | 频率 |
|-----|----------|--------|------|
| 请求成功率 | `LoggingMiddleware` + `slo_tracker` | HTTP 响应状态码 | 每次请求 |
| 请求延迟 | `LoggingMiddleware` + `metrics.py` | 请求开始/结束时间戳 | 每次请求 |
| DB 查询延迟 | `database_monitor.py` + `metrics.py` | SQL 执行计时 | 每次查询 |
| AI 推理延迟 | `metrics.py` (`track_ai_inference`) | 模型调用计时 | 每次推理 |
| 缓存命中率 | `metrics.py` (`record_cache_hit/miss`) | Redis 操作结果 | 每次缓存操作 |
| Web Vitals | `web_vitals.py` 端点 | 前端浏览器 API | 每次页面加载 |
| 错误率 | `metrics.py` + Sentry | HTTP 5xx + 未捕获异常 | 实时 |

---

## 3. 指标 (Metrics)

### 3.1 指标总览

所有指标由 `app/middleware/metrics.py` 中的 `MetricsMiddleware` 采集，通过 `GET /metrics` 端点以 Prometheus 文本格式暴露。

| 指标名称 | 类型 | 标签 | 说明 |
|----------|------|------|------|
| `ncard_http_requests_total` | Counter | `status` (2xx/4xx/5xx) | HTTP 请求总数 |
| `ncard_http_request_duration_seconds` | Histogram | `le` bucket 边界 | HTTP 请求延迟分布 |
| `ncard_http_active_requests` | Gauge | — | 当前活跃请求数 |
| `ncard_db_query_duration_seconds` | Histogram | `le` bucket 边界 | DB 查询延迟分布 |
| `ncard_ai_inference_duration_seconds` | Histogram | `le` bucket 边界 (加宽) | AI 推理延迟分布 |
| `ncard_cache_operations_total` | Counter | `type` (hit/miss) | 缓存操作总数 |

### 3.2 指标详情

#### `ncard_http_requests_total`

```
# HELP ncard_http_requests_total Total HTTP requests by status class
# TYPE ncard_http_requests_total counter
ncard_http_requests_total{status="2xx"} 15234
ncard_http_requests_total{status="4xx"} 231
ncard_http_requests_total{status="5xx"} 12
```

#### `ncard_http_request_duration_seconds`

```
# HELP ncard_http_request_duration_seconds HTTP request duration distribution in seconds
# TYPE ncard_http_request_duration_seconds histogram
ncard_http_request_duration_seconds_bucket{le="0.005"} 1234
ncard_http_request_duration_seconds_bucket{le="0.01"} 4567
ncard_http_request_duration_seconds_bucket{le="0.025"} 8901
ncard_http_request_duration_seconds_bucket{le="0.05"} 12000
ncard_http_request_duration_seconds_bucket{le="0.1"} 14500
ncard_http_request_duration_seconds_bucket{le="0.25"} 15200
ncard_http_request_duration_seconds_bucket{le="0.5"} 15300
ncard_http_request_duration_seconds_bucket{le="1.0"} 15330
ncard_http_request_duration_seconds_bucket{le="2.5"} 15334
ncard_http_request_duration_seconds_bucket{le="5.0"} 15334
ncard_http_request_duration_seconds_bucket{le="+Inf"} 15334
ncard_http_request_duration_seconds_count 15334
ncard_http_request_duration_seconds_sum 2345.678
```

**Bucket 边界：** `[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]` 秒

#### `ncard_http_active_requests`

```
# HELP ncard_http_active_requests Currently active HTTP requests
# TYPE ncard_http_active_requests gauge
ncard_http_active_requests 3
```

#### `ncard_db_query_duration_seconds`

```
# HELP ncard_db_query_duration_seconds Database query duration distribution in seconds
# TYPE ncard_db_query_duration_seconds histogram
ncard_db_query_duration_seconds_bucket{le="0.005"} 5000
...
ncard_db_query_duration_seconds_count 8000
ncard_db_query_duration_seconds_sum 120.5
```

#### `ncard_ai_inference_duration_seconds`

```
# HELP ncard_ai_inference_duration_seconds AI inference duration distribution in seconds
# TYPE ncard_ai_inference_duration_seconds histogram
ncard_ai_inference_duration_seconds_bucket{le="0.05"} 10
...
# AI 推理使用更宽的 bucket 边界:
# [0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0] 秒
ncard_ai_inference_duration_seconds_count 150
ncard_ai_inference_duration_seconds_sum 450.2
```

#### `ncard_cache_operations_total`

```
# HELP ncard_cache_operations_total Cache hit/miss operations total
# TYPE ncard_cache_operations_total counter
ncard_cache_operations_total{type="hit"} 9000
ncard_cache_operations_total{type="miss"} 1000
```

### 3.3 Prometheus 采集配置

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "ai-digital-business-card"
    scrape_interval: 15s
    scrape_timeout: 10s
    metrics_path: /metrics
    static_configs:
      - targets:
          - "localhost:8201"    # 后端 API
          - "localhost:8202"    # AI 服务
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
```

---

## 4. 追踪 (Tracing)

### 4.1 OpenTelemetry 配置

由 `app/middleware/otel.py` 的 `init_otel()` 初始化。

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| 启用/禁用 | `ENABLE_OTEL` | `false` | 设置 `true` 启用分布式追踪 |
| OTLP 端点 | `OTEL_EXPORTER_OTLP_ENDPOINT` | — | 设置后启用 OTLP 导出（否则使用 ConsoleSpanExporter） |
| 服务名 | 代码中硬编码 | `ai-digital-business-card` | Resource 中的 service.name |

### 4.2 Span 属性

每个 HTTP 请求自动生成以下 Span 属性：

| 属性 | 示例值 | 来源 |
|------|--------|------|
| `http.method` | `POST` | FastAPI Instrumentation |
| `http.url` | `/api/brochures` | FastAPI Instrumentation |
| `http.status_code` | `201` | FastAPI Instrumentation |
| `http.host` | `api.liankebao.top` | FastAPI Instrumentation |
| `enduser.id` | `42` | 手动注入（中间件） |
| `request_id` | `abc-123` | 手动注入（中间件） |

### 4.3 Trace 采样策略

| 环境 | 采样率 | 说明 |
|------|--------|------|
| 开发 | 1.0 (100%) | 开发环境完整采样 |
| 预发布 | 0.5 (50%) | 预发布环境 50% 采样 |
| 生产 | 0.1 (10%) | 生产环境 10% 采样，错误 Span 强制全采样 |

### 4.4 导出目标

| 方式 | 条件 | 目标 |
|------|------|------|
| ConsoleSpanExporter | `OTEL_EXPORTER_OTLP_ENDPOINT` 未设置 | 标准输出 |
| OTLP HTTP | `OTEL_EXPORTER_OTLP_ENDPOINT` 已设置 | Jaeger / Grafana Tempo / SigNoz |

### 4.5 FastAPI 集成

```python
# 在 create_app() 中 (现有代码)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)
```

自动追踪：
- 所有 HTTP 请求的生命周期
- 请求/响应头
- 异常捕获

---

## 5. 日志 (Logging)

日志规范详见 [LOGGING.md](./LOGGING.md)。本文档仅列出与可观测性相关的日志关键点。

### 5.1 关键日志流

| 日志流 | Logger | 输出目标 | 可观测性用途 |
|--------|--------|----------|-------------|
| 访问日志 | `app.access` | stdout → Loki | 请求量/延迟/错误率分析 |
| 审计日志 | `audit` | 文件 + stdout | 合规/SOC2 审计 |
| 慢查询日志 | `db_monitor` | stdout → Loki | DB 性能瓶颈定位 |
| Web Vitals | `app.routers.web_vitals` | stdout → Loki | 真实用户体验监控 |
| 业务日志 | `app.*` | stdout → Loki | 业务指标和问题定位 |

### 5.2 日志 ↔ 指标 ↔ 追踪关联

```
请求进入
  │
  ├── RequestIDMiddleware → 生成 request_id (UUID)
  │
  ├── LoggingMiddleware → 输出 JSON 日志 (含 request_id)
  │
  ├── MetricsMiddleware → 更新 Prometheus 指标 (含 status/duration)
  │
  ├── OpenTelemetry → 创建 Span (含 trace_id)
  │
  └── 业务处理
       ├── AuditMiddleware → 记录审计日志 (含 user_id)
       ├── DB Monitor → 慢查询日志 (含 request_id)
       └── Cache → 更新缓存指标 (hit/miss)
```

**关联查询：**

| 场景 | Prometheus | 日志 (Loki) | 追踪 (Jaeger) |
|------|-----------|-------------|---------------|
| 高延迟请求 | 检查 `ncard_http_request_duration_seconds` 直方图 | 搜索 `duration_ms > 1000` 的访问日志 | 查看对应 span 详情 |
| 5xx 错误 | 检查 `ncard_http_requests_total{status="5xx"}` | 搜索 `status>=500` 的错误日志 | 查看错误 span 链路 |
| 慢查询 | 检查 `ncard_db_query_duration_seconds` | 搜索 `SLOW_QUERY` 日志 | 查看 DB span 耗时 |

---

## 6. 告警规则模板

### 6.1 Prometheus Alerting Rules

```yaml
# /etc/prometheus/rules/ncard_alerts.yml
groups:
  - name: ncard_availability
    interval: 30s
    rules:
      # ── 服务可用性 ────────────────────────────────────────────
      - alert: HighErrorRate
        expr: |
          rate(ncard_http_requests_total{status="5xx"}[5m])
          /
          rate(ncard_http_requests_total[5m])
          > 0.001
        for: 2m
        labels:
          severity: p1
          team: backend
        annotations:
          summary: "5xx 错误率超过 0.1% (当前 {{ $value | humanizePercentage }})"
          description: "后端 API 5xx 错误率在 5 分钟窗口内超过阈值，请立即排查。"

      - alert: CriticalErrorRate
        expr: |
          rate(ncard_http_requests_total{status="5xx"}[1m])
          /
          rate(ncard_http_requests_total[1m])
          > 0.05
        for: 1m
        labels:
          severity: p0
          team: backend
        annotations:
          summary: "🔥 严重错误率超过 5% (当前 {{ $value | humanizePercentage }})"
          description: "后端 API 严重错误率高，可能为服务故障。"

      - alert: NoTraffic
        expr: rate(ncard_http_requests_total[5m]) == 0
        for: 5m
        labels:
          severity: p0
          team: backend
        annotations:
          summary: "服务无流量 (5 分钟内零请求)"
          description: "后端 API 在 5 分钟内无任何请求，服务可能已宕机。"

      # ── 延迟告警 ───────────────────────────────────────────────
      - alert: HighLatencyP99
        expr: |
          histogram_quantile(
            0.99,
            rate(ncard_http_request_duration_seconds_bucket[5m])
          ) > 1.0
        for: 3m
        labels:
          severity: p1
          team: backend
        annotations:
          summary: "P99 延迟超过 1s (当前 {{ $value }}s)"
          description: "P99 延迟在过去 5 分钟内持续超过 1 秒。"

      - alert: HighLatencyP95
        expr: |
          histogram_quantile(
            0.95,
            rate(ncard_http_request_duration_seconds_bucket[5m])
          ) > 5.0
        for: 3m
        labels:
          severity: p2
          team: backend
        annotations:
          summary: "P95 延迟超过 5s (当前 {{ $value }}s)"
          description: "P95 延迟异常升高，可能存在性能瓶颈。"

      # ── 活跃连接 ───────────────────────────────────────────────
      - alert: HighConcurrency
        expr: ncard_http_active_requests > 100
        for: 1m
        labels:
          severity: p2
          team: backend
        annotations:
          summary: "高并发: {{ $value }} 个活跃请求"
          description: "当前活跃请求数超过 100，可能需要扩容。"

      # ── AI 推理延迟 ────────────────────────────────────────────
      - alert: SlowAIInference
        expr: |
          histogram_quantile(
            0.95,
            rate(ncard_ai_inference_duration_seconds_bucket[5m])
          ) > 10.0
        for: 3m
        labels:
          severity: p2
          team: ai
        annotations:
          summary: "AI 推理 P95 延迟超过 10s (当前 {{ $value }}s)"
          description: "AI 推理模型响应缓慢，可能需要检查模型或 API 提供商状态。"

      # ── 缓存命中率 ──────────────────────────────────────────────
      - alert: LowCacheHitRate
        expr: |
          rate(ncard_cache_operations_total{type="miss"}[5m])
          /
          (rate(ncard_cache_operations_total{type="hit"}[5m]) + rate(ncard_cache_operations_total{type="miss"}[5m]))
          > 0.3
        for: 5m
        labels:
          severity: p2
          team: backend
        annotations:
          summary: "缓存命中率低于 70% (当前 {{ $value | humanizePercentage }})"
          description: "缓存命中率偏低，可能导致数据库负载升高。"

      # ── DB 查询延迟 ────────────────────────────────────────────
      - alert: SlowDBQueries
        expr: |
          histogram_quantile(
            0.95,
            rate(ncard_db_query_duration_seconds_bucket[5m])
          ) > 0.5
        for: 3m
        labels:
          severity: p2
          team: backend
        annotations:
          summary: "DB 查询 P95 延迟超过 500ms (当前 {{ $value }}s)"
          description: "数据库查询延迟异常升高，可能存在慢查询或连接池瓶颈。"

      # ── SLO 燃烧速率 ───────────────────────────────────────────
      - alert: FastBurnRate
        expr: |
          (
            1 - (
              sum(rate(ncard_http_requests_total{status=~"5.."}[1h]))
              /
              sum(rate(ncard_http_requests_total[1h]))
            )
          ) < 0.999
        for: 5m
        labels:
          severity: p1
          team: backend
        annotations:
          summary: "SLO 快速燃烧 — 可用性低于 99.9% (当前 {{ $value | humanizePercentage }})"
          description: "过去 1 小时可用性低于 SLO，当前正在快速消耗错误预算。"

      - alert: CriticalBurnRate
        expr: |
          (
            1 - (
              sum(rate(ncard_http_requests_total{status=~"5.."}[10m]))
              /
              sum(rate(ncard_http_requests_total[10m]))
            )
          ) < 0.99
        for: 2m
        labels:
          severity: p0
          team: backend
        annotations:
          summary: "🔥 SLO 严重燃烧 — 可用性低于 99% (当前 {{ $value | humanizePercentage }})"
          description: "过去 10 分钟可用性急剧下降，错误预算正在快速耗尽。"

  - name: ncard_infrastructure
    interval: 30s
    rules:
      - alert: InstanceDown
        expr: up{job="ai-digital-business-card"} == 0
        for: 1m
        labels:
          severity: p0
          team: ops
        annotations:
          summary: "实例 {{ $labels.instance }} 下线"
          description: "Prometheus 无法抓取实例 {{ $labels.instance }} 的指标。"
```

### 6.2 告警通知路由

```yaml
# alertmanager.yml
route:
  receiver: "default"
  routes:
    - match:
        severity: p0
      receiver: "pagerduty-critical"
      repeat_interval: 5m
      group_interval: 1m

    - match:
        severity: p1
      receiver: "slack-backend"
      repeat_interval: 15m
      group_interval: 5m

    - match:
        severity: p2
      receiver: "slack-backend"
      repeat_interval: 1h
      group_interval: 30m

receivers:
  - name: "pagerduty-critical"
    pagerduty_configs:
      - routing_key: "<PAGERDUTY_KEY>"
        severity: critical
        description: "{{ .GroupLabels.alertname }} — 需立即响应"

  - name: "slack-backend"
    slack_configs:
      - api_url: "<SLACK_WEBHOOK_URL>"
        channel: "#alerts-backend"
        title: "{{ .GroupLabels.alertname }}"
        text: "{{ .CommonAnnotations.description }}"
```

### 6.3 告警通知矩阵

| 告警名称 | 严重级别 | 通知渠道 | 响应时限 | 恢复时限 |
|----------|----------|----------|---------|---------|
| CriticalErrorRate | P0 | 电话 + 短信 + IM | 15 min | 1 hr |
| InstanceDown | P0 | 电话 + 短信 + IM | 15 min | 1 hr |
| CriticalBurnRate | P0 | 电话 + 短信 + IM | 15 min | 1 hr |
| HighErrorRate | P1 | IM + 短信 | 30 min | 4 hr |
| HighLatencyP99 | P1 | IM + 短信 | 30 min | 4 hr |
| FastBurnRate | P1 | IM | 30 min | 4 hr |
| HighLatencyP95 | P2 | IM | 2 hr | 24 hr |
| HighConcurrency | P2 | IM | 2 hr | 24 hr |
| SlowAIInference | P2 | IM | 2 hr | 24 hr |
| LowCacheHitRate | P2 | IM | 2 hr | 24 hr |
| SlowDBQueries | P2 | IM | 2 hr | 24 hr |
| NoTraffic | P0 | 电话 + IM | 15 min | 1 hr |

### 6.4 告警响应 Runbook

#### P0 — CriticalErrorRate / CriticalBurnRate

1. **确认** (2 min): 确认告警非误报，检查 `/health` 和 `/metrics` 端点
2. **隔离** (5 min): 检查最近部署、配置变更、依赖服务状态
3. **排查** (10 min):
   - `journalctl -u app -n 200 --no-pager` 查看最新日志
   - 检查 Prometheus 面板中的错误率图表
   - 查看 Sentry 最新 Error 事件
4. **恢复** (30 min):
   - 回滚最近部署
   - 扩容容器实例
   - 重启服务
5. **复盘** (24 hr): 撰写故障报告 (PIR)

#### P1 — HighErrorRate / HighLatencyP99

1. **确认** (5 min): 确认告警影响范围
2. **排查** (20 min):
   - 检查 APM 面板 (Jaeger/Grafana)
   - 检查数据库连接池状态
   - 检查第三方 API (DeepSeek) 状态
3. **恢复** (4 hr): 根据根因采取相应措施
4. **复盘** (48 hr): 更新 Runbook

---

## 7. 仪表盘设计

### 7.1 Grafana 仪表盘概览

#### 仪表盘 1: 服务总览 (Service Overview)

```json
{
  "title": "AI数字名片 — 服务总览",
  "description": "全局服务健康状态和关键指标一览",
  "refresh": "30s",
  "time": {"from": "now-6h", "to": "now"},
  "panels": [
    {
      "title": "请求速率 (RPS)",
      "type": "stat",
      "query": "rate(ncard_http_requests_total[5m])",
      "unit": "req/s"
    },
    {
      "title": "错误率",
      "type": "stat",
      "query": "(rate(ncard_http_requests_total{status=\"5xx\"}[5m]) / rate(ncard_http_requests_total[5m])) * 100",
      "unit": "%",
      "thresholds": {"critical": 1, "warning": 0.1}
    },
    {
      "title": "当前活跃请求",
      "type": "stat",
      "query": "ncard_http_active_requests",
      "unit": "count"
    },
    {
      "title": "P99 延迟",
      "type": "stat",
      "query": "histogram_quantile(0.99, rate(ncard_http_request_duration_seconds_bucket[5m]))",
      "unit": "s",
      "thresholds": {"critical": 5, "warning": 1}
    },
    {
      "title": "SLO 达标状态",
      "type": "stat",
      "description": "当前 SLO 是否达标（可用性 ≥ 99.9%, P99 < 1s）",
      "query": "text",
      "text": "slo_tracker.get_slo_status() 结果",
      "thresholds": {"ok": true, "critical": false}
    },
    {
      "title": "错误预算剩余",
      "type": "gauge",
      "query": "1 - (sum(rate(ncard_http_requests_total{status=\"5xx\"}[30d])) / sum(rate(ncard_http_requests_total[30d]))) / 0.001",
      "unit": "%",
      "thresholds": {"critical": 20, "warning": 50}
    }
  ]
}
```

**布局示意：**

```
┌──────────┬──────────┬──────────┬──────────┐
│ RPS      │ 错误率   │ 活跃请求  │ P99 延迟 │
│ 45.2/s   │ 0.08%    │ 7        │ 0.89s    │
├──────────┴──────────┴──────────┴──────────┤
│              SLO 达标状态   错误预算: 87%   │
├────────────────────────────────────────────┤
│  HTTP 请求速率 (时间序列)                   │
│  ┌────────────────────────────────────────┐ │
│  │ ╱╲   ╱╲   ╱╲   ╱╲   ╱╲   ╱╲   ╱╲   │ │
│  └────────────────────────────────────────┘ │
├────────────────────────────────────────────┤
│  延迟分布 (P50 / P95 / P99)                 │
│  ┌────────────────────────────────────────┐ │
│  │ ╱╲   ╱╲   ╱╲   ╱╲   ╱╲   ╱╲   ╱╲   │ │
│  └────────────────────────────────────────┘ │
└────────────────────────────────────────────┘
```

#### 仪表盘 2: API 详细监控 (API Details)

| Panel | 类型 | PromQL 查询 | 目的 |
|-------|------|-------------|------|
| 请求速率 (按状态码) | Stacked Bar | `rate(ncard_http_requests_total[1m])` | 区分 2xx/4xx/5xx 趋势 |
| 延迟热力图 | Heatmap | `rate(ncard_http_request_duration_seconds_bucket[5m])` | 延迟分布可视化 |
| 错误率时序 | Time Series | `rate(ncard_http_requests_total{status="5xx"}[5m])` | 5xx 错误变化趋势 |
| DB 查询 P99 | Time Series | `histogram_quantile(0.99, rate(ncard_db_query_duration_seconds_bucket[5m]))` | 数据库延迟监控 |
| AI 推理 P95 | Time Series | `histogram_quantile(0.95, rate(ncard_ai_inference_duration_seconds_bucket[5m]))` | AI 延迟监控 |
| 缓存命中率 | Time Series | `rate(ncard_cache_operations_total{type="hit"}[5m]) / (rate(ncard_cache_operations_total[5m]))` | 缓存效率监控 |
| 活跃请求 | Time Series | `ncard_http_active_requests` | 并发量趋势 |

#### 仪表盘 3: 用户体验 (RUM Dashboard)

| Panel | 数据源 | 指标 | 说明 |
|-------|--------|------|------|
| LCP 分布 | Web Vitals 日志 | LCP P50/P75/P95 | 最大内容绘制时间 |
| FID 分布 | Web Vitals 日志 | FID P50/P75/P95 | 首次输入延迟 |
| CLS 分布 | Web Vitals 日志 | CLS P50/P75/P95 | 累计布局偏移 |
| TTFB 分布 | Web Vitals 日志 | TTFB P50/P75/P95 | 首字节时间 |
| 评级分布 | Web Vitals 日志 | good/needs-improvement/poor 占比 | 用户体验评级 |
| Core Web Vitals 达标率 | Web Vitals 日志 | 所有指标均为 good 的会话占比 | 整体 Web Vitals 健康度 |

#### 仪表盘 4: SLO 仪表盘 (SLO Dashboard)

| Panel | 类型 | 指标 | 说明 |
|-------|------|------|------|
| 可用性 SLI | Time Series | `1 - (5xx 率)` | 当前可用性走势 |
| 延迟 SLI (P99) | Time Series | `histogram_quantile(0.99, ...)` | P99 延迟走势 |
| 错误预算燃烧率 | Time Series | `(错误预算消耗 / 时间)` | 燃烧速率监控 |
| 错误预算剩余 | Gauge | 月度剩余百分比 | 实时错误预算状态 |
| SLO 达标日历 | State Timeline | 每 5 分钟 SLO 达标状态 | 故障时间可视化 |

### 7.2 仪表盘变量定义

```
变量名: $env
  类型: query
  数据源: Prometheus
  查询: label_values(ncard_http_requests_total, environment)
  默认: production

变量名: $instance
  类型: query
  数据源: Prometheus
  查询: label_values(ncard_http_requests_total{environment="$env"}, instance)
  默认: all
```

### 7.3 关键告警面板阈值色标

| 指标 | 绿色 (Good) | 黄色 (Warning) | 红色 (Critical) |
|------|:-----------:|:--------------:|:---------------:|
| 错误率 | < 0.1% | 0.1% ~ 1% | > 1% |
| P99 延迟 | < 1s | 1s ~ 5s | > 5s |
| 缓存命中率 | > 90% | 70% ~ 90% | < 70% |
| 错误预算剩余 | > 50% | 20% ~ 50% | < 20% |
| 活跃请求 | < 50 | 50 ~ 100 | > 100 |

---

## 8. 运行检查清单

### 每日检查

- [ ] Grafana 仪表盘无告警（检查告警面板和通知）
- [ ] 错误预算剩余 > 50%（SLO 仪表盘）
- [ ] 审计日志正常写入（检查 audit.log 文件大小和时间戳）

### 每周检查

- [ ] 回顾错误预算消耗趋势
- [ ] 检查 Web Vitals 数据质量（前端上报是否正常）
- [ ] 检查慢查询日志，识别需要优化的 SQL
- [ ] 验证告警规则触发是否正常（对测试端点手动触发测试）

### 每月检查

- [ ] 生成月度 SLA 报告（可用性、MTTR、MTBF）
- [ ] 检查日志保留策略是否正常（审计日志 180 天保留）
- [ ] 评审告警规则，去除噪声告警
- [ ] 更新仪表盘和告警阈值（根据业务增长调整）

### 部署前检查

- [ ] 确认 `/metrics` 端点可访问且返回 Prometheus 文本格式
- [ ] 确认 `request_id` 在日志中正确传递
- [ ] 确认无敏感数据泄露到日志中（使用脱敏检查清单）
- [ ] 确认 OpenTelemetry 已按环境正确配置（采样率）

---

## 9. 修订历史

| 版本 | 日期 | 修改内容 | 修订人 |
|------|------|----------|--------|
| v1.0 | 2026-07-01 | 初始版本 — 可观测性架构、SLO/SLI、告警规则、仪表盘设计 | — |

---

*本文档由 AI 数智名片运维团队维护 | 联系: support@liankebao.top | 最后更新: 2026-07-01*
