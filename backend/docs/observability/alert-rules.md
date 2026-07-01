# 告警规则定义

> **文档版本**: v1.0  
> **最后更新**: 2026-07-01  
> **告警引擎**: Prometheus + Alertmanager  
> **通知渠道**: 企业微信 / 飞书 / 邮件 / PagerDuty（视严重级别）

---

## 1. 告警规则总览

| # | 规则名称 | 指标 | 阈值 | 持续时间 | 严重级别 | 通知渠道 |
|---|----------|------|------|----------|----------|----------|
| 1 | **HighLatency** | `ncard_http_request_duration_seconds` P95 | > 1s | 5 min | **Critical** | 企业微信 + 电话 |
| 2 | **ErrorRateBurst** | `ncard_http_requests_total{status="5xx"}` 速率 | > 1% 总请求 | 3 min | **Critical** | 企业微信 + 邮件 |
| 3 | **ServiceOffline** | up (探活) | = 0 | 30s | **Critical** | 电话 + PagerDuty |
| 4 | **SlowDatabaseQuery** | `ncard_db_query_duration_seconds` P99 | > 2s | 5 min | **Warning** | 企业微信 |
| 5 | **RateLimitHitHigh** | `ratelimit-remaining` → 0 | 匹配率 > 50% | 5 min | **Warning** | 企业微信 |
| 6 | **PaymentFailure** | 支付端点 `ncard_http_requests_total{status="5xx"}` | > 2% | 2 min | **Critical** | 企业微信 + 邮件 + 电话 |

---

## 2. 规则详情

### 规则 1: HighLatency — 高延迟告警

| 字段 | 值 |
|------|-----|
| **规则名** | `HighLatency` |
| **指标** | `ncard_http_request_duration_seconds` P95 分位数 |
| **阈值** | P95 > 1 秒 |
| **持续时间** | 5 分钟 |
| **严重级别** | **Critical** |
| **通知渠道** | 企业微信机器人 + 值班电话 |
| **Runbook** | [延迟排查手册](https://wiki.internal/runbooks/high-latency) |
| **描述** | 当 P95 请求延迟连续 5 分钟超过 1s 时触发。可能原因：数据库慢查询、外部 API 超时、计算资源不足。 |

### 规则 2: ErrorRateBurst — 错误率突增

| 字段 | 值 |
|------|-----|
| **规则名** | `ErrorRateBurst` |
| **指标** | `rate(ncard_http_requests_total{status="5xx"}[5m]) / rate(ncard_http_requests_total[5m])` |
| **阈值** | > 1%（即错误率超过总请求的 1%） |
| **持续时间** | 3 分钟 |
| **严重级别** | **Critical** |
| **通知渠道** | 企业微信机器人 + 邮件（团队 aliases） |
| **描述** | 5xx 错误率突增，可能为代码缺陷、依赖服务故障或配置错误。立即检查近期发布。 |

### 规则 3: ServiceOffline — 服务离线

| 字段 | 值 |
|------|-----|
| **规则名** | `ServiceOffline` |
| **指标** | `up{job="ncard-api"}`（Prometheus 探活） |
| **阈值** | = 0（连续探活失败） |
| **持续时间** | 30 秒 |
| **严重级别** | **Critical** |
| **通知渠道** | 电话 + PagerDuty（24/7 值班） |
| **描述** | API 服务端点完全不可达。需立即重启服务实例或回滚部署。 |

### 规则 4: SlowDatabaseQuery — 慢查询告警

| 字段 | 值 |
|------|-----|
| **规则名** | `SlowDatabaseQuery` |
| **指标** | `histogram_quantile(0.99, rate(ncard_db_query_duration_seconds_bucket[5m]))` |
| **阈值** | P99 > 2 秒 |
| **持续时间** | 5 分钟 |
| **严重级别** | **Warning** |
| **通知渠道** | 企业微信机器人（DBA 频道） |
| **描述** | 数据库查询 P99 延迟超过 2s。可能需要检查慢查询日志、索引优化或连接池配置。 |

### 规则 5: RateLimitHitHigh — 速率限制高命中率

| 字段 | 值 |
|------|-----|
| **规则名** | `RateLimitHitHigh` |
| **指标** | `sum(rate(ncard_http_requests_total{status="429"}[5m])) / sum(rate(ncard_http_requests_total[5m]))` |
| **阈值** | > 50%（即超过一半的请求被限流） |
| **持续时间** | 5 分钟 |
| **严重级别** | **Warning** |
| **通知渠道** | 企业微信机器人（业务运营频道） |
| **描述** | 大量用户请求被速率限制阻挡。可能原因：异常爬虫、客户端重试风暴或限流配置过严。需联系业务方确认。 |

### 规则 6: PaymentFailure — 支付失败告警

| 字段 | 值 |
|------|-----|
| **规则名** | `PaymentFailure` |
| **指标** | `rate(ncard_http_requests_total{status="5xx", path=~".*/payment/.*"}[2m])` |
| **阈值** | > 2% 支付请求失败 |
| **持续时间** | 2 分钟 |
| **严重级别** | **Critical** |
| **通知渠道** | 企业微信机器人 + 邮件（支付团队）+ 值班电话 |
| **描述** | 支付接口错误率超过 2%。可能原因：微信/支付宝网关故障、证书过期、支付配置变更。立即联系支付服务商确认。 |

---

## 3. Prometheus 告警规则 YAML

将以下内容保存至 `prometheus/rules/ncard-alerts.yml`：

```yaml
groups:
  - name: ncard-api-critical
    interval: 30s
    rules:
      # ── 规则 1: 高延迟 ──────────────────────────────────────────
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(ncard_http_request_duration_seconds_bucket[5m])
          ) > 1.0
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "API 响应延迟超过 SLO (P95 > 1s)"
          description: >
            P95 延迟 {{ $value | humanizeDuration }} 持续 5 分钟。
            请检查慢查询、外部依赖和计算资源。
          runbook: "https://wiki.internal/runbooks/high-latency"

      # ── 规则 2: 错误率突增 ──────────────────────────────────────
      - alert: ErrorRateBurst
        expr: |
          (
            rate(ncard_http_requests_total{status="5xx"}[5m])
            /
            rate(ncard_http_requests_total[5m])
          ) > 0.01
        for: 3m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "5xx 错误率超过 1%"
          description: >
            错误率 {{ $value | humanizePercentage }}，持续 3 分钟。
            请检查近期部署和日志。
          runbook: "https://wiki.internal/runbooks/error-burst"

      # ── 规则 3: 服务离线 ────────────────────────────────────────
      - alert: ServiceOffline
        expr: up{job="ncard-api"} == 0
        for: 30s
        labels:
          severity: critical
          team: oncall
        annotations:
          summary: "ncard-api 服务离线"
          description: >
            ncard-api 实例已下线超过 30 秒。
            立即检查服务器状态和部署流水线。
          runbook: "https://wiki.internal/runbooks/service-offline"

  - name: ncard-api-warning
    interval: 60s
    rules:
      # ── 规则 4: 慢查询 ──────────────────────────────────────────
      - alert: SlowDatabaseQuery
        expr: |
          histogram_quantile(0.99,
            rate(ncard_db_query_duration_seconds_bucket[5m])
          ) > 2.0
        for: 5m
        labels:
          severity: warning
          team: dba
        annotations:
          summary: "DB 查询 P99 延迟超过 2s"
          description: >
            DB 查询 P99 延迟 {{ $value | humanizeDuration }}。
            请检查慢查询日志、索引和连接池。
          runbook: "https://wiki.internal/runbooks/slow-query"

      # ── 规则 5: 速率限制高命中 ──────────────────────────────────
      - alert: RateLimitHitHigh
        expr: |
          (
            rate(ncard_http_requests_total{status="429"}[5m])
            /
            rate(ncard_http_requests_total[5m])
          ) > 0.5
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "速率限制命中率超过 50%"
          description: >
            限流比例 {{ $value | humanizePercentage }}，持续 5 分钟。
            可能存在异常爬虫或客户端风暴。
          runbook: "https://wiki.internal/runbooks/rate-limit"

      # ── 规则 6: 支付失败 ────────────────────────────────────────
      - alert: PaymentFailure
        expr: |
          (
            rate(ncard_http_requests_total{status="5xx", path=~".*/payment/.*"}[2m])
            /
            rate(ncard_http_requests_total{path=~".*/payment/.*"}[2m])
          ) > 0.02
        for: 2m
        labels:
          severity: critical
          team: payment
        annotations:
          summary: "支付接口错误率超过 2%"
          description: >
            支付失败率 {{ $value | humanizePercentage }}。
            请立即联系微信/支付宝网关确认。
          runbook: "https://wiki.internal/runbooks/payment-failure"
```

---

## 4. 告警通知路由

### 4.1 按严重级别路由

```yaml
# alertmanager.yml 片段
route:
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: pagerduty-critical
      repeat_interval: 5m
      group_wait: 30s
      group_interval: 3m

    - match:
        severity: warning
      receiver: wechat-warning
      repeat_interval: 30m
      group_wait: 1m
      group_interval: 5m

receivers:
  - name: pagerduty-critical
    pagerduty_configs:
      - routing_key: '<PAGERDUTY_KEY>'
        severity: critical

  - name: wechat-warning
    webhook_configs:
      - url: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=<WEBHOOK_KEY>'
        send_resolved: true
```

### 4.2 静默期

- **Critical** 告警：7×24 全天候通知
- **Warning** 告警：08:00–23:00 通知，夜间静默

---

## 5. 告警接收人矩阵

| 严重级别 | 渠道 | 接收人 | 响应时间要求 |
|----------|------|--------|-------------|
| **Critical** | PagerDuty + 电话 | 值班 SRE + 后端团队 | ≤ 15 分钟 |
| **Warning** | 企业微信 | 对应团队 | ≤ 1 小时 |
| **Info** | 邮件 | 全技术团队 | 下一个工作日 |

---

## 6. 关联文档

| 文档 | 路径 |
|------|------|
| SLA 定义 | `docs/observability/sla-definitions.md` |
| 指标中间件 | `app/middleware/metrics.py` |
| 速率限制中间件 | `app/middleware/rate_limiter.py` |
| OpenTelemetry | `app/middleware/otel.py` |
