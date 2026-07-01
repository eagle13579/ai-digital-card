# OpenTelemetry 部署前检查清单

> 项目: AI数字名片
> 相关文件: `backend/app/middleware/otel.py`
> 部署资源: `deploy/otel/`
> 创建日期: 2026-07-01

---

## 使用说明

在 **首次部署 OTel** 或 **修改 OTel 配置后上线** 前逐项检查以下清单。
每项完成后在 `[ ]` 中打 `[x]`。

---

## 1. 代码层就绪

### 1.1 模块加载验证
- [x] `python -c "from app.middleware.otel import *"` — 无 ImportError
- [x] 三级降级链路已实现:
  - [x] **Level 1**: OTLP 端点超时 → ConsoleSpanExporter (代码 `_create_otlp_exporter`)
  - [x] **Level 2**: opentelemetry-exporter-otlp-proto-http 未安装 → ConsoleSpanExporter
  - [x] **Level 3**: 任意未预期异常 → 静默跳过，不阻塞应用启动
- [x] 环境变量开关: `ENABLE_OTEL=true` / `false` (默认 `false`)

### 1.2 应用集成
- [ ] `create_app()` 中已调用 `init_otel()`
- [ ] `FastAPIInstrumentor.instrument_app(app)` 已注册（位于 `init_otel` 或 `create_app`）
- [ ] 不影响现有路由/中间件顺序

---

## 2. 依赖就绪

### 2.1 Python 依赖
- [ ] 生产环境安装以下包:

```bash
pip install \
  opentelemetry-api \
  opentelemetry-sdk \
  opentelemetry-instrumentation-fastapi \
  opentelemetry-exporter-otlp-proto-http
```

### 2.2 版本兼容性
- [ ] opentelemetry-api >= 1.20
- [ ] opentelemetry-sdk >= 1.20
- [ ] opentelemetry-instrumentation-fastapi >= 0.40b
- [ ] opentelemetry-exporter-otlp-proto-http >= 1.20

### 2.3 可选依赖
- [ ] `opentelemetry-instrumentation-requests` — HTTP 客户端追踪
- [ ] `opentelemetry-instrumentation-sqlite3` — 数据库追踪
- [ ] `opentelemetry-instrumentation-logging` — 日志关联

---

## 3. 基础设施就绪

### 3.1 OTel Collector（如果使用）
- [ ] `deploy/otel/otel-collector-config.yml` 已配置接收器 (receiver)
- [ ] OTel Collector 服务已部署并运行
- [ ] Collector 端口可达（默认 gRPC:4317 / HTTP:4318）
- [ ] Collector 后端导出目标已配置（Jaeger / Tempo / 自建）

### 3.2 网络连通性
- [ ] 应用实例 → OTel Collector 网络可达
- [ ] Collector → 后端存储网络可达
- [ ] 防火墙规则已放行 OTLP 端口
- [ ] 跨 AZ/Region 延迟 < 50ms（避免 span 丢失）

### 3.3 后端存储
- [ ] 追踪数据存储（Jaeger / Tempo / SigNoz）已部署
- [ ] 存储容量规划完成（预估: ~1GB/天/100万 span）
- [ ] 数据保留策略已配置（建议: 生产 30 天, 开发 7 天）

---

## 4. 环境变量配置

### 4.1 必需变量
```env
ENABLE_OTEL=true                      # 开启追踪
```

### 4.2 OTLP 导出变量（可选，不设置则使用 ConsoleSpanExporter）
```env
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318   # OTLP HTTP 端点
OTEL_EXPORTER_OTLP_TIMEOUT=5                              # 连接超时秒数 (默认5)
OTEL_SERVICE_NAME=ai-digital-business-card                # 服务名 (默认)
```

### 4.3 生产环境安全检查
- [ ] `OTEL_EXPORTER_OTLP_ENDPOINT` 不含明文凭证
- [ ] OTel Collector 端开启认证（如有）
- [ ] 内网通信不经过公网

---

## 5. 配置验证（部署前执行）

### 5.1 连通性诊断
```bash
# 检查模块加载
cd D:/AI数智名片/backend
PYTHONPATH=. python -c "from app.middleware.otel import *; print('OK')"

# 运行完整诊断
python scripts/check_otel.py
python scripts/check_otel.py --timeout 5
python scripts/check_otel.py --quiet
```

### 5.2 预期输出
```
OTel module loads OK
[TracerProvider initialized]
[FastAPI instrumentation registered]
```

### 5.3 日志确认（应用启动后）
```
INFO: OpenTelemetry 初始化完成: service=ai-digital-business-card, export_mode=OTLP
```
或（降级模式）:
```
INFO: OpenTelemetry 初始化完成: service=ai-digital-business-card, export_mode=Console
```

---

## 6. 性能与容量

### 6.1 性能基准
- [ ] 无 OTel 时 P50/P95 响应时间已记录
- [ ] 开启 OTel 后响应时间增加 < 5%
- [ ] Span 导出为异步（BatchSpanProcessor），不阻塞请求

### 6.2 容量规划
| 指标 | 预估 | 备注 |
|------|------|------|
| 每日请求量 | 10万+ | 按业务增长 |
| 每日 span 数 | 30万+ | 每个请求 ~3 span |
| 每日存储量 | ~300 MB | 压缩前 |
| 每月存储量 | ~9 GB | 保留30天 |

---

## 7. 降级验证

### 7.1 场景测试

| # | 场景 | 预期行为 | 测试结果 |
|---|------|---------|---------|
| 1 | `ENABLE_OTEL` 未设置或 false | 静默跳过，不初始化 | [ ] |
| 2 | OTLP 端点不可达 | 降级为 ConsoleSpanExporter，日志警告 | [ ] |
| 3 | 依赖包未安装 | 降级为 ConsoleSpanExporter，日志提示安装 | [ ] |
| 4 | 任意运行时异常 | 静默降级，不阻塞应用 | [ ] |

### 7.2 降级确认命令
```bash
# 模拟 OTLP 不可达
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:19999 ENABLE_OTEL=true \
  python -c "from app.middleware.otel import init_otel; init_otel()"
# 预期: warning 日志 + ConsoleSpanExporter
```

---

## 8. 生产上线检查

- [ ] 代码已合并到生产分支
- [ ] 依赖已安装到生产环境
- [ ] OTel Collector 已部署并健康
- [ ] 环境变量已注入（ENABLE_OTEL=true）
- [ ] 灰度发布: 先 10% 流量验证
- [ ] 监控: 确认 span 数据到达后端
- [ ] 回滚: 设置 ENABLE_OTEL=false 即可完全关闭
- [ ] 文档: OTel 相关文档已更新
- [ ] 告警: 若 span 丢失超阈值，触发告警

---

## 9. 快速回滚方案

```bash
# 方法 A: 环境变量关闭 (最快，无需重启代码)
export ENABLE_OTEL=false

# 方法 B: 重启应用
docker-compose restart backend

# 方法 C: 全量回滚
git revert HEAD~1
docker-compose up -d --build backend
```

---

> **检查人**: ______________  **日期**: ______________
> 全部 [x] 后即可部署上线。
