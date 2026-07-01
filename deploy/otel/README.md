# OpenTelemetry 可观测性部署指南

## 概述

本文档说明如何为 AI 数智名片部署 OpenTelemetry Collector，实现分布式追踪 (Traces) 和指标 (Metrics) 的可观测性。

### 架构

```
┌─────────────────┐     OTLP (gRPC:4317 / HTTP:4318)     ┌──────────────────────┐
│  AI 数智名片     │ ──────────────────────────────────→ │  OpenTelemetry        │
│  FastAPI 后端    │                                      │  Collector            │
│  (otel.py)       │     Prometheus /metrics (pull)       │  (otel-collector)     │
│  prometheus_client│ ←────────────────────────────────── │                      │
└─────────────────┘                                      │  Exporters:           │
                                                         │   → Prometheus :8889  │
┌─────────────────┐                                      │   → Logging (控制台)  │
│  Prometheus      │ ◄──── scrape :8889 ───────────────── │   → Jaeger (可选)    │
│  :9090           │                                      └──────────────────────┘
└────────┬────────┘                                                
         │                                                         
         ▼                                                         
┌─────────────────┐                                                
│  Grafana         │ ◄──── datasource: Prometheus                  
│  :3000           │                                                
└─────────────────┘                                                
```

---

## 快速启动

### 1. 启动 OpenTelemetry Collector

```bash
# 进入 deploy 目录
cd deploy

# 使用 docker-compose (推荐 — 包含全部组件)
docker compose -f docker-compose.otel.yml up -d

# 或者直接使用 docker run (仅 Collector)
docker run -d \
  --name ai-card-otel-collector \
  --restart unless-stopped \
  -v $(pwd)/otel-collector-config.yml:/etc/otel/config.yaml \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 8889:8889 \
  -p 13133:13133 \
  otel/opentelemetry-collector-contrib:0.108.0 \
  --config=/etc/otel/config.yaml
```

### 2. 验证 Collector 运行状态

```bash
# 健康检查 (端口 13133)
curl -s http://localhost:13133 | jq .

# 检查 Collector 自暴露的指标
curl -s http://localhost:8889/metrics | head -20

# 查看 Collector 日志
docker logs ai-card-otel-collector --tail 50
```

### 3. 配置后端启用 OTLP 导出

编辑 `.env` 文件，添加以下配置：

```bash
# 启用 OpenTelemetry
ENABLE_OTEL=true

# 设置 OTLP 端点 (Collector HTTP 地址)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318

# (可选) 指定服务名称
OTEL_SERVICE_NAME=ai-digital-business-card
```

重启后端应用：

```bash
# 如果使用 uvicorn 开发模式
# 重新启动应用即可
```

### 4. 运行诊断工具

确认连通性：

```bash
python scripts/check_otel.py
```

正常输出示例：

```
══════════════════════════════════════════════════════
  AI 数智名片 — OTel 可观测性连通性诊断
══════════════════════════════════════════════════════

[1] OTLP 端点 - HTTP (localhost:4318/v1/traces)
  ✓ OTLP HTTP (端口 4318)
       Collector 可达 (返回 405, 符合预期)

[2] OTLP 端点 - gRPC (localhost:4317)
  ✓ OTLP gRPC (端口 4317)
       TCP 端口可达 (gRPC 握手需 grpcio 库进一步验证)

[3] Prometheus 指标端点 (localhost:8000/metrics)
  ✓ Prometheus /metrics (localhost:8000)
       可达, 返回 42 个指标行

──── 综合诊断 ────
  ✓ 状态: 全部可达 — OTel 可观测性链路完整
       建议: Collector 已就绪，可启用 OTLP 导出
```

---

## docker-compose 配置

创建一个 `docker-compose.otel.yml` 文件，统一管理可观测性组件：

```yaml
version: "3.8"

services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.108.0
    container_name: ai-card-otel-collector
    restart: unless-stopped
    volumes:
      - ./otel-collector-config.yml:/etc/otel/config.yaml
    ports:
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
      - "8889:8889"    # Prometheus exporter
      - "13133:13133"  # Health check
    command:
      - "--config=/etc/otel/config.yaml"
    networks:
      - ai-card-otel

  # 可选: Jaeger 用于分布式追踪可视化
  jaeger:
    image: jaegertracing/all-in-one:1.58
    container_name: ai-card-jaeger
    restart: unless-stopped
    ports:
      - "16686:16686"  # UI
      - "4317:4317"    # OTLP gRPC ingress
      - "4318:4318"    # OTLP HTTP ingress
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - ai-card-otel

networks:
  ai-card-otel:
    name: ai-card-otel-network
    driver: bridge
```

将此文件保存为 `deploy/docker-compose.otel.yml`，然后运行：

```bash
docker compose -f deploy/docker-compose.otel.yml up -d
```

---

## 集成 Jaeger (可选)

启用 Jaeger 后，可以在 `http://localhost:16686` 查看分布式追踪数据。

### 配置步骤

1. 取消注释 `otel-collector-config.yml` 中的 Jaeger 导出器配置
2. 取消注释 traces 流水线中的 `otlp/jaeger` 导出器
3. 在 `docker-compose.otel.yml` 中取消 Jaeger 服务的注释
4. 重新启动 Collector

```bash
docker compose -f deploy/docker-compose.otel.yml restart otel-collector
```

### 验证 Jaeger

访问 http://localhost:16686，选择服务 `ai-digital-business-card`，搜索 traces。

---

## 故障排除 (Troubleshooting)

### Collector 无法启动

```bash
# 查看详细日志
docker logs ai-card-otel-collector

# 验证配置格式
docker run --rm -v $(pwd)/otel-collector-config.yml:/etc/otel/config.yaml \
  otel/opentelemetry-collector-contrib:0.108.0 \
  --config=/etc/otel/config.yaml --dry-run
```

### 连接被拒绝 (Connection Refused)

```bash
# 端口是否已占用
netstat -ano | grep -E "4317|4318"

# Docker 容器是否正确暴露端口
docker port ai-card-otel-collector

# Windows (WSL2) 用户: 使用 host.docker.internal 而不是 localhost
# 如果后端运行在 WSL2 中，Collector 在 Docker Desktop 中:
#   设置 OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4318
```

### OTLP 导出失败但不阻塞启动 (预期行为)

- `otel.py` 中的 OTLP 导出带有 5 秒连接超时
- 如果 OTLP 端点不可达，自动降级为 `ConsoleSpanExporter`
- 应用仍然正常启动，不会因为 OTel 而崩溃
- 日志中会看到 `OTLP 端点不可达，已降级为 ConsoleSpanExporter`

### 指标重复

如果同时运行 Prometheus 自抓取接收器和 Prometheus 导出器，指标可能重复。
解决方案：只使用 Prometheus 导出器，禁用 Prometheus 接收器中的后端自抓取，
让独立的 Prometheus 实例直接抓取后端的 `/metrics` 端点。

---

## 环境变量参考

| 变量名 | 默认值 | 说明 |
|---|---|---|
| `ENABLE_OTEL` | `false` | 启用/禁用 OpenTelemetry |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | (空) | OTLP Collector 地址 (如 `http://localhost:4318`) |
| `OTEL_EXPORTER_OTLP_TIMEOUT` | `5` | OTLP 连接超时 (秒) |
| `OTEL_SERVICE_NAME` | `ai-digital-business-card` | 服务名称 |
| `OTEL_EXPORTER_OTLP_HEADERS` | (空) | 自定义请求头 (如 `Authorization=Bearer xxx`) |

---

## 指标一览

### 后端直接暴露 (Prometheus 格式)

路径: `GET /metrics`

| 指标名 | 类型 | 说明 |
|---|---|---|
| `ncard_users_created_total` | Counter | 注册用户总数 |
| `ncard_users_active_24h` | Gauge | 24 小时活跃用户数 |
| `ncard_brochures_created_total` | Counter | 名片创建总数 |
| `ncard_matches_total` | Counter | 匹配总数 |
| `ncard_billing_revenue_cents_total` | Counter | 交易收入（分） |
| `ncard_trial_conversion_ratio` | Gauge | 试用转化率 |

### Collector 暴露 (Prometheus 格式)

路径: `http://localhost:8889/metrics`

| 指标名 | 说明 |
|---|---|
| `otel_otlp_receiver_spans_received` | OTLP 接收的 spans 数 |
| `otel_otlp_receiver_metrics_received` | OTLP 接收的 metric 数 |
| `otel_exporter_send_completed` | 导出成功计数 |
| `otel_processor_batch_batch_size` | 批处理大小 |

---

## 相关文件

| 文件 | 说明 |
|---|---|
| `deploy/otel-collector-config.yml` | Collector 配置模板 |
| `deploy/docker-compose.otel.yml` | OTel 组件编排 (需自行创建) |
| `scripts/check_otel.py` | 连通性诊断工具 |
| `backend/app/middleware/otel.py` | OTel SDK 初始化 & 降级逻辑 |
| `backend/app/business_metrics.py` | 业务指标定义 (prometheus_client) |
| `deploy/prometheus/prometheus.yml` | Prometheus 抓取配置 |
