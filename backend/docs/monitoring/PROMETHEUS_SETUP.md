# 链客宝 Prometheus + Grafana 监控部署指南

## 目录

- [1. 架构概览](#1-架构概览)
- [2. 快速部署（docker-compose）](#2-快速部署docker-compose)
- [3. Prometheus 配置](#3-prometheus-配置)
- [4. Grafana 配置](#4-grafana-配置)
- [5. 推荐仪表盘面板](#5-推荐仪表盘面板)
- [6. 告警规则](#6-告警规则)
- [7. 指标一览](#7-指标一览)
- [8. 业务代码接入示例](#8-业务代码接入示例)

---

## 1. 架构概览

```
┌──────────────┐     scrape      ┌──────────────┐     visualise    ┌──────────┐
│  链客宝 API   │ ──────────────→ │  Prometheus   │ ──────────────→ │  Grafana  │
│  :8001/metrics│                 │  :9090        │                 │  :3000    │
└──────────────┘                 └──────────────┘                 └──────────┘
       │                                │
       │ expose                         │ alert
       ▼                                ▼
   prometheus_client.json        Alertmanager (可选)
```

- **链客宝后端** 在 `/metrics` 端点暴露 Prometheus 格式指标
- **Prometheus** 定期抓取指标并存储时间序列
- **Grafana** 从 Prometheus 读取数据并展示仪表盘
- **Alertmanager**（可选）基于告警规则发送通知

---

## 2. 快速部署（docker-compose）

在项目根目录 `D:/chainke-full/` 下创建 `docker-compose.monitoring.yml`：

### docker-compose.monitoring.yml

```yaml
version: "3.9"

services:
  prometheus:
    image: prom/prometheus:v2.53.0
    container_name: chainke-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--storage.tsdb.retention.time=30d"
      - "--web.console.libraries=/usr/share/prometheus/console_libraries"
      - "--web.console.templates=/usr/share/prometheus/consoles"
    networks:
      - chainke-net

  grafana:
    image: grafana/grafana:11.1.0
    container_name: chainke-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    depends_on:
      - prometheus
    networks:
      - chainke-net

  # --- 可选: Node Exporter（主机级指标） ---
  node-exporter:
    image: prom/node-exporter:v1.8.0
    container_name: chainke-node-exporter
    restart: unless-stopped
    ports:
      - "9100:9100"
    networks:
      - chainke-net

volumes:
  prometheus_data:
  grafana_data:

networks:
  chainke-net:
    driver: bridge
```

### 启动

```bash
cd D:/chainke-full/
docker compose -f docker-compose.monitoring.yml up -d
```

验证：

| 服务        | 地址                        |
| ----------- | --------------------------- |
| Prometheus  | http://localhost:9090       |
| Grafana     | http://localhost:3000       |
| 后端指标    | http://localhost:8001/metrics |

---

## 3. Prometheus 配置

### 目录结构

```
D:/chainke-full/prometheus/
├── prometheus.yml          # 主配置
├── rules/
│   └── chainke_alerts.yml  # 告警规则
```

### prometheus.yml

```yaml
global:
  scrape_interval:     15s
  evaluation_interval: 15s
  scrape_timeout:      10s

# 告警规则文件
rule_files:
  - "rules/chainke_alerts.yml"

scrape_configs:
  # ── 链客宝后端 API ──────────────────────────────────────────
  - job_name: "chainke-backend"
    metrics_path: "/metrics"
    scheme: http
    static_configs:
      - targets:
          - "host.docker.internal:8001"   # Windows/Mac Docker Desktop
          # - "192.168.1.100:8001"        # 替换为实际内网 IP
        labels:
          service: "chainke-backend"
          env: "production"

  # ── Node Exporter（主机级别） ─────────────────────────────────
  - job_name: "node-exporter"
    static_configs:
      - targets: ["node-exporter:9100"]
        labels:
          service: "host-metrics"

  # ── Prometheus 自身 ──────────────────────────────────────────
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
```

> **注意**：Docker Desktop for Windows 使用 `host.docker.internal` 访问宿主机端口。
> 若后端直接运行在宿主机而非容器中，请使用此地址。
> 若后端也在容器中，可将两个容器加入同一 network，直接用服务名访问。

---

## 4. Grafana 配置

### 4.1 初始登录

1. 打开 http://localhost:3000
2. 用户名: `admin`  密码: `admin123`
3. 首次登录后会提示修改密码（可跳过）

### 4.2 添加 Prometheus 数据源

- **方法 A：通过 UI 手动添加**
  1. Configuration → Data Sources → Add
  2. 选择 Prometheus
  3. URL: `http://prometheus:9090`
  4. 点击 Save & Test

- **方法 B：自动预配（推荐）**

创建 `D:/chainke-full/grafana/provisioning/datasources/datasources.yml`：

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

### 4.3 导入仪表盘

- **方法 A：通过 UI 导入**
  1. Dashboards → New → Import
  2. 输入仪表盘 ID 或粘贴 JSON

- **方法 B：自动预配**

创建 `D:/chainke-full/grafana/provisioning/dashboards/dashboards.yml`：

```yaml
apiVersion: 1

providers:
  - name: "ChainKe Default"
    orgId: 1
    folder: "链客宝"
    type: file
    disableDeletion: false
    editable: true
    updateIntervalSeconds: 30
    options:
      path: /etc/grafana/provisioning/dashboards/json
```

仪表盘 JSON 文件存放至 `D:/chainke-full/grafana/provisioning/dashboards/json/`。

---

## 5. 推荐仪表盘面板

### 5.1 通用面板（建议导入）

| 面板名称                                 | 说明               | Grafana ID |
| ---------------------------------------- | ------------------ | ---------- |
| Node Exporter Full                       | 主机级 CPU/内存/网络 | 1860       |
| Spring Boot Statistics (适配 FastAPI)     | JVM/请求/延迟/错误  | 6756       |
| 1. Alertmanager                          | 告警总览           | 9578       |

### 5.2 自定义链客宝仪表盘面板

以下为一个完整仪表盘的建议布局（共 6 行，每行 2~3 面板）：

#### 第 1 行：服务概览

| 面板 | 查询 PromQL | 类型 | 单位 |
|------|-------------|------|------|
| **请求率 (QPS)** | `rate(chainke_http_requests_total[1m])` | Time series | ops |
| **P99 延迟** | `histogram_quantile(0.99, rate(chainke_http_request_duration_seconds_bucket[5m]))` | Stat / Gauge | s |
| **错误率** | `rate(chainke_http_requests_total{status=~"5.."}[5m]) / rate(chainke_http_requests_total[5m]) * 100` | Stat / Gauge | % |

#### 第 2 行：资源

| 面板 | 查询 PromQL | 类型 | 单位 |
|------|-------------|------|------|
| **活跃连接数** | `chainke_active_connections` | Stat | count |
| **处理中请求** | `chainke_http_inflight_requests` | Stat | count |
| **CPU 使用率** | `rate(node_cpu_seconds_total{mode="user"}[1m]) * 100` (Node Exporter) | Time series | % |

#### 第 3 行：数据库

| 面板 | 查询 PromQL | 类型 | 单位 |
|------|-------------|------|------|
| **数据库查询率** | `rate(chainke_db_queries_total[1m])` | Time series | ops |
| **DB P99 延迟** | `histogram_quantile(0.99, rate(chainke_db_query_duration_seconds_bucket[5m]))` | Stat | s |
| **数据库错误** | `rate(chainke_db_connection_errors_total[5m])` | Time series | count |

#### 第 4 行：请求详情

| 面板 | 查询 PromQL | 类型 | 单位 |
|------|-------------|------|------|
| **请求量（按方法）** | `sum by(method)(rate(chainke_http_requests_total[1m]))` | Bar gauge | ops |
| **请求量（按路径）** | `topk(10, sum by(path)(rate(chainke_http_requests_total[5m])))` | Table | ops |
| **状态码分布** | `sum by(status)(rate(chainke_http_requests_total[1m]))` | Pie chart | ops |

#### 第 5 行：业务指标

| 面板 | 查询 PromQL | 类型 | 单位 |
|------|-------------|------|------|
| **累计注册数** | `chainke_registrations_total` | Stat | count |
| **注册率** | `rate(chainke_registrations_total[24h])` | Stat | /day |
| **匹配数** | `chainke_matches_total` | Stat | count |
| **订单数** | `chainke_orders_created_total` | Stat | count |
| **总收入** | `chainke_orders_revenue_total` | Stat | ¥ |

#### 第 6 行：延迟热力图/直方图

| 面板 | 查询 PromQL | 类型 | 单位 |
|------|-------------|------|------|
| **请求延迟热力图** | `rate(chainke_http_request_duration_seconds_bucket[5m])` | Heatmap | s |
| **请求延迟分位数** | `histogram_quantile(0.5, ...), histogram_quantile(0.9, ...), histogram_quantile(0.99, ...)` | Time series | s |

### 5.3 完整 Grafana Dashboard JSON

请参考 `D:/chainke-full/grafana/provisioning/dashboards/json/chainke_overview.json` 获取可导入的完整 JSON。

---

## 6. 告警规则

创建 `D:/chainke-full/prometheus/rules/chainke_alerts.yml`：

```yaml
groups:
  - name: chainke-backend
    interval: 30s
    rules:
      # ── 服务可用性 ──────────────────────────────────────────
      - alert: ChainKeBackendDown
        expr: up{job="chainke-backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "链客宝后端服务不可用"
          description: "实例 {{ $labels.instance }} 已离线超过 1 分钟"

      # ── 请求错误率 ──────────────────────────────────────────
      - alert: ChainKeHighErrorRate
        expr: |
          rate(chainke_http_requests_total{status=~"5.."}[5m])
          /
          rate(chainke_http_requests_total[5m])
          > 0.05
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "链客宝后端错误率超过 5%"
          description: "当前错误率: {{ $value | humanizePercentage }}"

      # ── P99 延迟 ────────────────────────────────────────────
      - alert: ChainKeHighLatency
        expr: |
          histogram_quantile(0.99, rate(chainke_http_request_duration_seconds_bucket[5m]))
          > 3.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "链客宝 P99 延迟超过 3s"
          description: "P99 延迟当前为 {{ $value | humanizeDuration }}"

      # ── 数据库错误 ──────────────────────────────────────────
      - alert: ChainKeDatabaseErrors
        expr: rate(chainke_db_connection_errors_total[5m]) > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "链客宝数据库连接错误"
          description: "最近 5 分钟数据库连接错误率: {{ $value | humanize }}"

      # ── 内存使用 (需要 Node Exporter) ──────────────────────
      - alert: ChainKeHighMemoryUsage
        expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "主机内存使用率超过 90%"
          description: "当前内存使用率: {{ $value | humanizePercentage }}"

      # ── 磁盘使用 (需要 Node Exporter) ──────────────────────
      - alert: ChainKeHighDiskUsage
        expr: (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "主机磁盘使用率超过 85%"
          description: "当前磁盘使用率: {{ $value | humanizePercentage }}"

  - name: chainke-business
    interval: 1m
    rules:
      # ── 注册量异常下降 ────────────────────────────────────
      - alert: ChainKeRegistrationDrop
        expr: rate(chainke_registrations_total[1h]) < 0.5 * rate(chainke_registrations_total[24h] offset 1h)
        for: 1h
        labels:
          severity: info
        annotations:
          summary: "注册量异常下降"
          description: "1 小时注册率环比下降超过 50%"

      # ── 订单失败率 ─────────────────────────────────────────
      - alert: ChainKeOrderFailureRate
        expr: |
          rate(chainke_orders_created_total{status="fail"}[5m])
          /
          rate(chainke_orders_created_total[5m])
          > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "订单失败率超过 10%"
          description: "当前订单失败率: {{ $value | humanizePercentage }}"
```

### Alertmanager 配置（可选）

如需发送告警通知（钉钉/飞书/邮件），创建 `prometheus/alertmanager.yml`：

```yaml
route:
  receiver: "default"
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: "default"
    webhook_configs:
      - url: "http://your-alert-webhook:8080/alert"
```

在 docker-compose 中添加 Alertmanager 服务。

---

## 7. 指标一览

### 7.1 HTTP 层（由 middleware/metrics_middleware.py 自动采集）

| 指标名称                               | 类型      | 标签                              | 说明                 |
| -------------------------------------- | --------- | --------------------------------- | -------------------- |
| `chainke_http_requests_total`          | Counter   | `method`, `path`, `status`        | HTTP 请求总数        |
| `chainke_http_request_duration_seconds` | Histogram | `method`, `path`                  | 请求耗时（秒）       |
| `chainke_active_users`                 | Gauge     | —                                 | 当前活跃用户数       |

### 7.2 数据库层（由 app/metrics.py 提供）

| 指标名称                                | 类型      | 标签          | 说明                 |
| --------------------------------------- | --------- | ------------- | -------------------- |
| `chainke_db_queries_total`              | Counter   | `operation`   | 数据库查询总数       |
| `chainke_db_query_duration_seconds`     | Histogram | `operation`   | 查询耗时（秒）       |
| `chainke_db_connection_errors_total`    | Counter   | `error_type`  | 连接错误数           |

### 7.3 连接层

| 指标名称                       | 类型  | 标签 | 说明                   |
| ------------------------------ | ----- | ---- | ---------------------- |
| `chainke_active_connections`   | Gauge | —    | 当前活跃 WebSocket/SSE 连接 |
| `chainke_http_inflight_requests` | Gauge | —    | 当前处理中的 HTTP 请求 |

### 7.4 业务层

| 指标名称                               | 类型      | 标签                                            | 说明                 |
| -------------------------------------- | --------- | ----------------------------------------------- | -------------------- |
| `chainke_registrations_total`          | Counter   | `source`, `status`                              | 注册总数             |
| `chainke_registration_duration_seconds` | Histogram | `source`                                        | 注册流程耗时         |
| `chainke_matches_total`                | Counter   | `match_type`, `status`                          | 匹配总数             |
| `chainke_match_duration_seconds`       | Histogram | `match_type`                                    | 匹配耗时             |
| `chainke_orders_created_total`         | Counter   | `product_type`, `payment_method`, `status`      | 订单创建总数         |
| `chainke_orders_revenue_total`         | Counter   | `product_type`, `payment_method`                | 总收入（元）         |
| `chainke_order_processing_duration_seconds` | Histogram | `product_type`                            | 订单处理耗时         |
| `chainke_app_info`                     | Gauge     | `version`, `environment`                        | 应用元数据（值=1）   |

---

## 8. 业务代码接入示例

### 8.1 在路由中埋点

```python
# app/routers/auth.py
from app.metrics import inc_registrations, observe_registration_duration

@router.post("/api/auth/register")
async def register(body: RegisterBody):
    start = time.perf_counter()
    try:
        user = await create_user(body)
        inc_registrations(source=body.source or "manual", status="success")
        return {"user_id": user.id}
    except Exception:
        inc_registrations(source=body.source or "manual", status="fail")
        raise
    finally:
        observe_registration_duration(time.perf_counter() - start)
```

### 8.2 在匹配引擎中埋点

```python
# app/routers/matching_engine.py
from app.metrics import inc_matches, observe_match_duration

@router.post("/api/matching/match")
async def create_match(req: MatchRequest):
    start = time.perf_counter()
    result = await matching_engine.match(req)
    inc_matches(match_type=req.type or "auto", status="success" if result else "fail")
    observe_match_duration(time.perf_counter() - start, match_type=req.type or "auto")
    return result
```

### 8.3 在订单路由中埋点

```python
# app/routers/orders.py
from app.metrics import inc_orders_created, inc_order_revenue

@router.post("/api/orders")
async def create_order(order: OrderCreate):
    new_order = await order_service.create(order)
    inc_orders_created(
        product_type=order.product_type,
        payment_method=order.payment_method,
        status="paid" if order.auto_pay else "pending",
    )
    if order.amount:
        inc_order_revenue(order.amount, product_type=order.product_type, payment_method=order.payment_method)
    return new_order
```

### 8.4 数据库查询监控（装饰器版）

```python
# app/database.py 或 app/db_monitor.py
import time
from functools import wraps
from app.metrics import inc_db_query, observe_db_query

def monitor_db(operation: str):
    """装饰器：监控数据库查询耗时"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start
                inc_db_query(operation)
                observe_db_query(operation, duration)
        return wrapper
    return decorator

# 使用示例
# @monitor_db("find_user")
# def find_user_by_id(user_id: int):
#     return db.query(User).filter(User.id == user_id).first()
```

### 8.5 应用启动时设置元数据

在 `main.py` 中添加：

```python
# main.py
from app.metrics import set_app_info

set_app_info(version="1.0.0", environment=os.getenv("ENV", "production"))
```

---

## Prometheus 查询速查表

| 查询目的 | PromQL |
|----------|--------|
| 每秒请求数 (QPS) | `rate(chainke_http_requests_total[1m])` |
| 错误率 | `rate(chainke_http_requests_total{status=~"5.."}[5m]) / rate(chainke_http_requests_total[5m])` |
| P99 延迟 | `histogram_quantile(0.99, rate(chainke_http_request_duration_seconds_bucket[5m]))` |
| 平均延迟 | `rate(chainke_http_request_duration_seconds_sum[5m]) / rate(chainke_http_request_duration_seconds_count[5m])` |
| 最慢的 5 条路径 | `topk(5, sum by(path)(rate(chainke_http_request_duration_seconds_sum[5m])) / sum by(path)(rate(chainke_http_request_duration_seconds_count[5m])))` |
| 活跃连接趋势 | `chainke_active_connections` |
| 24h 注册量 | `increase(chainke_registrations_total[24h])` |
| 累计订单数 | `chainke_orders_created_total` |
| 数据库 QPS | `rate(chainke_db_queries_total[1m])` |
| DB 慢查询 (P99) | `histogram_quantile(0.99, rate(chainke_db_query_duration_seconds_bucket[5m]))` |
