# 业务指标文档 — Business Metrics

> **文档版本**: v1.0  
> **最后更新**: 2026-07-01  
> **适用范围**: AI 数字名片 API 服务 (ncard-api)  
> **采集模块**: `app/business_metrics.py`  
> **暴露路径**: `GET /metrics` (Prometheus 文本格式)

---

## 1. 指标总览

| 指标名 | 类型 | 标签 | 说明 |
|--------|------|------|------|
| `ncard_users_created_total` | Counter | `source` | 累计注册用户总数，按来源分片 |
| `ncard_users_active_24h` | Gauge | 无 | 过去 24 小时活跃用户数 |
| `ncard_brochures_created_total` | Counter | `purpose` | 累计名片创建总数，按用途分片 |
| `ncard_matches_total` | Counter | `source` | 累计匹配总数，按匹配来源分片 |
| `ncard_billing_revenue_cents_total` | Counter | `channel`, `tier` | 累计交易收入（人民币分） |
| `ncard_trial_conversion_ratio` | Gauge | 无 | 试用转付费转化率（0.0 ~ 1.0） |

### 1.1 标签说明

| 标签 | 可选值 | 说明 |
|------|--------|------|
| `source`（用户） | `wechat` / `phone` / `oauth` / `admin` | 注册来源 |
| `source`（匹配） | `auto` / `manual` | 匹配来源：自动匹配 vs 手动匹配 |
| `purpose` | `partner` / `client` / `investor` / `supplier` / `""` | 名片用途 |
| `channel` | `wechat` / `alipay` | 支付渠道 |
| `tier` | `gold` / `diamond` / `board` / `enterprise` | 会员等级 |

---

## 2. 指标定义与采集方式

### 2.1 注册用户数 — `ncard_users_created_total`

```
# TYPE ncard_users_created_total counter
ncard_users_created_total{source="phone"} 1234
ncard_users_created_total{source="wechat"} 567
ncard_users_created_total{source="oauth"} 89
```

**采集点**: `app/routers/auth.py` — 用户注册成功回调中调用 `inc_users_created(source=...)`  
**SQL 对照**:
```sql
SELECT source, COUNT(*) FROM users GROUP BY source;
```

### 2.2 活跃用户数 — `ncard_users_active_24h`

```
# TYPE ncard_users_active_24h gauge
ncard_users_active_24h 342
```

**采集方式**: 定时任务（cron / schedule）每 5 分钟执行一次：  
```sql
SELECT COUNT(DISTINCT user_id) FROM visitors
WHERE created_at >= NOW() - INTERVAL '24 hours';
```
**API**: `set_users_active_24h(count)`

### 2.3 名片创建数 — `ncard_brochures_created_total`

```
# TYPE ncard_brochures_created_total counter
ncard_brochures_created_total{purpose="partner"} 890
ncard_brochures_created_total{purpose="client"} 345
ncard_brochures_created_total{purpose="investor"} 123
ncard_brochures_created_total{purpose="supplier"} 67
ncard_brochures_created_total{purpose=""} 432
```

**采集点**: `app/routers/brochure.py` — 名片发布/创建成功时调用 `inc_brochures_created(purpose=...)`  
**SQL 对照**:
```sql
SELECT purpose, COUNT(*) FROM brochures GROUP BY purpose;
```

### 2.4 匹配数 — `ncard_matches_total`

```
# TYPE ncard_matches_total counter
ncard_matches_total{source="auto"} 1567
ncard_matches_total{source="manual"} 234
```

**采集点**: `app/routers/match_router.py` / `app/services/match_service.py` — 匹配事件记录时调用 `inc_matches(source=...)`  
**SQL 对照**:
```sql
SELECT source, COUNT(*) FROM match_records GROUP BY source;
```

### 2.5 交易收入 — `ncard_billing_revenue_cents_total`

```
# TYPE ncard_billing_revenue_cents_total counter
ncard_billing_revenue_cents_total{channel="wechat",tier="gold"} 199000
ncard_billing_revenue_cents_total{channel="wechat",tier="diamond"} 598000
ncard_billing_revenue_cents_total{channel="alipay",tier="gold"} 89000
ncard_billing_revenue_cents_total{channel="wechat",tier="enterprise"} 5000000
```

**采集点**: `app/routers/payment_router.py` — 支付成功回调中调用 `inc_billing_revenue(cents, channel, tier)`  
**SQL 对照**:
```sql
SELECT channel, membership_tier, SUM(total_cents)
FROM payment_orders
WHERE status = 'paid'
GROUP BY channel, membership_tier;
```

### 2.6 试用转付费转化率 — `ncard_trial_conversion_ratio`

```
# TYPE ncard_trial_conversion_ratio gauge
ncard_trial_conversion_ratio 0.326
```

**采集方式**: 定时任务每日统计一次：  
```sql
SELECT
    COUNT(DISTINCT CASE WHEN converted_at IS NOT NULL THEN user_id END) * 1.0 /
    NULLIF(COUNT(DISTINCT user_id), 0) AS conversion_ratio
FROM trial_records
WHERE started_at >= NOW() - INTERVAL '30 days';
```
**API**: `set_trial_conversion_ratio(ratio)`

---

## 3. PromQL 查询示例

### 3.1 运营看板

```promql
// 总注册用户数（累计）
ncard_users_created_total

// 今日新增注册
increase(ncard_users_created_total[24h])

// 按来源分片 — 今日新增
sum by (source) (increase(ncard_users_created_total[24h]))

// 当前活跃用户
ncard_users_active_24h

// 总名片数
ncard_brochures_created_total

// 今日创建名片数
increase(ncard_brochures_created_total[24h])

// 总匹配数
ncard_matches_total

// 累计总收入（人民币元）
ncard_billing_revenue_cents_total / 100

// 今日收入（元）
increase(ncard_billing_revenue_cents_total[24h]) / 100
```

### 3.2 转化漏斗

```promql
// Step 1: 注册 → 创建名片转化
rate(ncard_brochures_created_total[7d]) / rate(ncard_users_created_total[7d])

// Step 2: 创建名片 → 产生匹配
rate(ncard_matches_total[7d]) / rate(ncard_brochures_created_total[7d])

// Step 3: 匹配 → 付费转化
rate(ncard_billing_revenue_cents_total[7d]) / rate(ncard_matches_total[7d])

// 试用 → 付费整体转化率
ncard_trial_conversion_ratio
```

### 3.3 增长趋势

```promql
// 周环比增长（注册）
(
  increase(ncard_users_created_total[7d])
  -
  increase(ncard_users_created_total[14d] offset 7d)
)
/ increase(ncard_users_created_total[14d] offset 7d) * 100

// 月累计收入（本月至今）
ncard_billing_revenue_cents_total - ncard_billing_revenue_cents_total offset 30d

// 收入年同比
(
  increase(ncard_billing_revenue_cents_total[30d])
  -
  increase(ncard_billing_revenue_cents_total[30d] offset 365d)
)
/ increase(ncard_billing_revenue_cents_total[30d] offset 365d) * 100
```

### 3.4 告警规则

```promql
// 注册量异常下降（较昨日同期下降 50%）
(
  increase(ncard_users_created_total[1h])
  /
  increase(ncard_users_created_total[1h] offset 24h)
) < 0.5

// 活跃用户骤降（较上一小时下降 80%）
ncard_users_active_24h / ncard_users_active_24h offset 1h < 0.2

// 转化率低于阈值
ncard_trial_conversion_ratio < 0.15
```

---

## 4. Grafana 仪表盘设计

### 4.1 仪表盘: 「AI 数字名片 — 业务运营看板」

| 面板 | 指标 / 查询 | 可视化类型 | 说明 |
|------|------------|-----------|------|
| **总注册用户** | `ncard_users_created_total` | Stat（大数字） | 累计值 |
| **今日注册** | `increase(ncard_users_created_total[24h])` | Stat | 24h 增量 |
| **注册趋势** | `sum by (source)(increase(ncard_users_created_total[$__interval]))` | Stacked Bar | 按来源堆叠 |
| **活跃用户** | `ncard_users_active_24h` | Stat + Time Series | 当前值 + 历史曲线 |
| **总名片数** | `ncard_brochures_created_total` | Stat | 累计值 |
| **今日创建名片** | `increase(ncard_brochures_created_total[24h])` | Stat | 24h 增量 |
| **名片趋势** | `sum by (purpose)(increase(ncard_brochures_created_total[$__interval]))` | Stacked Bar | 按用途堆叠 |
| **总匹配数** | `ncard_matches_total` | Stat | 累计值 |
| **匹配趋势** | `sum by (source)(increase(ncard_matches_total[$__interval]))` | Stacked Bar | 按来源堆叠 |
| **累计收入** | `ncard_billing_revenue_cents_total / 100` | Stat（货币格式 ¥） | 累计元 |
| **今日收入** | `increase(ncard_billing_revenue_cents_total[24h]) / 100` | Stat（货币格式 ¥） | 24h 收入 |
| **收入趋势** | `sum by (channel)(increase(ncard_billing_revenue_cents_total[$__interval])) / 100` | Stacked Bar | 按渠道堆叠 |
| **转化率** | `ncard_trial_conversion_ratio` | Gauge (0~1) | 即时值 |
| **转化漏斗** | 见 §3.2 漏斗查询 | Gauge / Bar Gauge | 四阶段转化 |
| **增长概览** | 见 §3.3 增长趋势 | Table | 周环比、月累计 |

### 4.2 推荐的 Grafana 设置

- **刷新频率**: `30s`（运营看板）/ `5m`（趋势面板）
- **时间范围默认**: `Last 7 days`
- **变量**:
  - `$source`: `label_values(ncard_users_created_total, source)` — 注册来源筛选
  - `$purpose`: `label_values(ncard_brochures_created_total, purpose)` — 名片用途筛选
  - `$channel`: `label_values(ncard_billing_revenue_cents_total, channel)` — 支付渠道筛选
- **单位**:
  - 收入相关面板: `currency (CNY)` / `short`
  - 计数面板: `short`
  - 转化率: `0.0-1.0` / `percentunit (0.0-1.0)`

### 4.3 仪表盘 JSON Model 示例片段

```json
{
  "title": "AI 数字名片 — 业务运营看板",
  "tags": ["ncard", "business-metrics", "production"],
  "timezone": "Asia/Shanghai",
  "panels": [
    {
      "title": "累计注册用户",
      "type": "stat",
      "targets": [{"expr": "ncard_users_created_total", "legendFormat": "总注册"}],
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "color": {"mode": "fixed"},
          "thresholds": {"mode": "absolute", "steps": [{"value": null, "color": "green"}]}
        }
      }
    }
  ]
}
```

---

## 5. 采集器 Python API

在业务代码中直接调用 `app/business_metrics` 提供的便捷函数：

```python
from app.business_metrics import (
    inc_users_created,         # 注册事件
    set_users_active_24h,      # 活跃用户数更新
    inc_brochures_created,     # 名片创建事件
    inc_matches,               # 匹配事件
    inc_billing_revenue,       # 支付成功事件
    set_trial_conversion_ratio,# 试用转化率更新
    generate_business_metrics, # 手动生成 Prometheus 文本
)

# 示例 — 注册成功
inc_users_created(source="wechat")

# 示例 — 支付成功回调
inc_billing_revenue(cents=19900, channel="wechat", tier="gold")

# 示例 — 定时任务更新活跃用户
set_users_active_24h(active_count)
```

---

## 6. 集成方式

### 6.1 与现有 /metrics 端点的关系

`/metrics` 端点同时输出两类指标：

```
# ── APM 基础指标（源自 app/middleware/metrics.py） ──
ncard_http_requests_total{status="2xx"} 15000
ncard_http_request_duration_seconds_bucket{le="0.5"} 14000
...

# ── 业务指标（源自 app/business_metrics.py） ──
ncard_users_created_total{source="phone"} 1234
ncard_brochures_created_total{purpose="partner"} 890
...
```

Prometheus 配置中只需一个 job 即可采集全部指标：

```yaml
scrape_configs:
  - job_name: 'ncard-api'
    scrape_interval: 15s
    metrics_path: /metrics
    static_configs:
      - targets: ['localhost:8000']
```

### 6.2 与 OpenTelemetry 的关系

当前 OpenTelemetry OTLP（4318 端口）不可达，业务指标通过 Prometheus pull 模式暴露。
未来如需桥接到 OpenTemeletry，可通过 `otel-collector` 的 `prometheusreceiver` 采集 `/metrics` 后导出。

### 6.3 与 Sentry 的关系

Sentry 用于错误追踪（不可用于指标聚合），业务指标不经过 Sentry。

---

## 7. 常见问题

| 问题 | 解答 |
|------|------|
| 指标是否会在应用重启后丢失？ | 是的，Counter / Gauge 是内存中的。生产环境应配置 Prometheus Server 长期存储。 |
| 如何添加新标签？ | 修改 `app/business_metrics.py` 中的 `labelnames` 参数，并更新 `inc_*` 函数签名。 |
| 如何添加全新指标？ | 在 `app/business_metrics.py` 顶部定义新的 `Counter`/`Gauge`/`Histogram`，编写对应的便捷函数。 |
| 指标名冲突如何处理？ | 所有业务指标使用 `ncard_` 前缀，与 APM 指标（`ncard_http_*`）统一命名空间。 |
| 如何验证指标是否正确暴露？ | `curl http://localhost:8000/metrics \| grep ncard_users` |

---

## 8. 关联文档

| 文档 | 路径 |
|------|------|
| SLA 定义 | `docs/observability/sla-definitions.md` |
| 告警规则 | `docs/observability/alert-rules.md` |
| 指标中间件 | `app/middleware/metrics.py` |
| 业务指标采集器 | `app/business_metrics.py` |
