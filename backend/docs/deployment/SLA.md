# 链客宝 服务等级协议 (SLA)

> 版本: v1.0 | 生效日期: 2026-07-01
> 适用范围: 链客宝生产环境 (liankebao.top)
> 审批人: [待定]

---

## 目录

1. [协议概述](#1-协议概述)
2. [服务等级指标 (SLO)](#2-服务等级指标-slo)
3. [错误预算策略](#3-错误预算策略)
4. [告警响应时间分级](#4-告警响应时间分级)
5. [维护窗口规范](#5-维护窗口规范)
6. [SLA 例外条款](#6-sla-例外条款)
7. [度量与报告](#7-度量与报告)
8. [附录: Prometheus 告警规则](#8-附录-prometheus-告警规则)

---

## 1. 协议概述

### 1.1 目的

本 SLA 文档定义了链客宝平台对终端用户的服务质量承诺，包括可用性、性能和响应时间的量化指标，以及未达标时的处理流程。

### 1.2 服务描述

链客宝是基于 FastAPI + React 的 B2B 商务社交平台，部署在阿里云 ECS 单节点，通过 Docker Compose 编排。核心服务包括:

| 服务组件 | 描述 | 对可用性的影响 |
|---------|------|--------------|
| Web 前端 | React SPA (Nginx 静态资源) | 前端不可用 → 用户无法访问 |
| API 后端 | FastAPI (Python 3.12) | API 不可用 → 所有业务中断 |
| PostgreSQL | 主数据库 (PostgreSQL 16) | 数据库不可用 → API 不可用 |
| Redis | 缓存/会话 (Redis 7) | Redis 降级 → 部分功能受影响 |
| 支付模块 | 微信/支付宝集成 | 不可用 → 交易中断 |

### 1.3 服务时间

- **生产环境**: 7×24 小时
- **维护窗口**: 每月非高峰时段（详见第 5 节）

---

## 2. 服务等级指标 (SLO)

### 2.1 可用性 (Uptime)

| 指标 | 目标 (SLO) | 测量方式 | 测量周期 |
|------|-----------|---------|---------|
| 整体可用性 | **≥ 99.5%** | 外部健康检查成功率 | 月度 |
| API 可用性 | **≥ 99.7%** | /health 端点检测 | 月度 |
| 数据库可用性 | **≥ 99.9%** | pg_isready 探针 | 月度 |
| 支付模块可用性 | **≥ 99.0%** | 支付回调成功率 | 月度 |

**99.5% 可用性对应的月度不可用时间:**

| 周期 | 允许不可用时间 |
|------|--------------|
| 每日 | ≤ 7.2 分钟 |
| 每周 | ≤ 50.4 分钟 |
| 月度 (30天) | ≤ 3 小时 39 分钟 |
| 年度 (365天) | ≤ 1 天 19 小时 48 分钟 |

### 2.2 性能指标

| 指标 | 目标 (SLO) | 测量方式 | 说明 |
|------|-----------|---------|------|
| API 响应时间 P50 | **< 200ms** | 后端日志/APM | 一半请求在 200ms 内完成 |
| API 响应时间 P95 | **< 500ms** | 后端日志/APM | 95% 请求在 500ms 内完成 |
| API 响应时间 P99 | **< 1500ms** | 后端日志/APM | 99% 请求在 1.5s 内完成 |
| 前端首屏加载 | **< 2s** | Lighthouse | 首次内容绘制 (FCP) |
| 前端交互时间 | **< 3s** | Lighthouse | 最大内容绘制 (LCP) |
| 支付回调处理 | **< 5s** | 后端日志 | 支付平台通知到处理完成 |

### 2.3 吞吐量指标

| 指标 | 目标 (SLO) | 说明 |
|------|-----------|------|
| 并发用户数 | **≥ 500** | 同时在线 |
| API 吞吐量 | **≥ 100 req/s** | 每秒请求数 |
| 日活用户 (DAU) | **≥ 10,000** | 日活跃用户 |
| 日请求量 | **≥ 500,000** | 每日 API 调用 |

### 2.4 数据持久性

| 指标 | 目标 (SLO) | 说明 |
|------|-----------|------|
| 数据持久性 | **≥ 99.999%** | 已持久化数据不丢失 |
| RPO (恢复点目标) | **≤ 24 小时** | 可接受数据丢失窗口 |
| RTO (恢复时间目标) | **≤ 2 小时** | 完全恢复所需时间 |

---

## 3. 错误预算策略

### 3.1 错误预算定义

**错误预算 = 100% - SLO%**，即系统在 SLO 周期内允许不可用的总时间。

对于 99.5% 可用性 SLO:

| 周期 | 总时间 | 错误预算 (0.5%) |
|------|-------|----------------|
| 每日 | 86,400 秒 | 432 秒 (7.2 分钟) |
| 月度 (30天) | 2,592,000 秒 | 12,960 秒 (3.6 小时) |
| 季度 (90天) | 7,776,000 秒 | 38,880 秒 (10.8 小时) |

### 3.2 错误预算消耗规则

```
  错误预算剩余
       │
       ├─ ≥ 80% → 🟢 正常部署节奏
       │     可以按正常频率部署新功能
       │
       ├─ 50% - 80% → 🟡 谨慎模式
       │     仅在低峰时段部署
       │     部署前必须通过完整测试
       │     蓝绿部署必须保留足够回滚时间
       │
       ├─ 20% - 50% → 🟠 限制模式
       │     仅允许紧急修复 (hotfix) 部署
       │     所有部署需 CTO 审批
       │     启用 feature flags 关闭非核心功能
       │
       └─ < 20% → 🔴 冻结模式
             停止所有非关键变更
             成立稳定性专项组
             轮值 on-call 增加至 2 人
             每日复盘会议
```

### 3.3 错误预算消耗记录

```bash
# 错误预算消耗追踪表 (示例)
# 由监控系统自动记录, 月度报告人工复核

| 日期       | 事件               | 消耗时间 | 累计消耗 | 剩余预算 | 状态 |
|-----------|-------------------|---------|---------|---------|------|
| 2026-07-05 | 数据库主从延迟      | 2min    | 2min    | 97.4%   | 🟢   |
| 2026-07-12 | 502 故障 (后端OOM)  | 15min   | 17min   | 84.5%   | 🟢   |
| 2026-07-20 | SSL 证书过期        | 8min    | 25min   | 88.6%   | 🟢   |
| 2026-07-28 | Nginx 配置错误      | 45min   | 70min   | 68.1%   | 🟡   |
```

### 3.4 错误预算消耗告警

| 触发条件 | 通知渠道 | 响应要求 |
|---------|---------|---------|
| 月消耗 > 50% | 飞书群通知 + @on-call | 4 小时内响应 |
| 月消耗 > 80% | 飞书群通知 + @所有人 | 1 小时内响应 |
| 单次故障 > 15min | 飞书群通知 + @on-call | 15 分钟内响应 |

---

## 4. 告警响应时间分级

### 4.1 告警等级定义

| 等级 | 标签 | 定义 | 示例 |
|------|------|------|------|
| **P0** | 🔴 紧急 | 服务完全不可用,影响所有用户 | 网站 502, 数据库宕机 |
| **P1** | 🟠 高 | 主要功能不可用,影响大部分用户 | 支付故障, 登录失败 |
| **P2** | 🟡 中 | 次要功能异常,影响部分用户 | 搜索加载慢, 页面样式错乱 |
| **P3** | 🔵 低 | 用户体验轻微影响,无功能损失 | 日志告警, 非关键错误 |

### 4.2 响应时间要求

| 等级 | 响应时间 (Acknowledge) | 处理时间 (TTR) | 升级时间 | 通知渠道 |
|------|----------------------|----------------|---------|---------|
| **P0** | **≤ 5 分钟** | **≤ 30 分钟** | 15 分钟未响应 → 升级至 CTO | 电话 + 飞书 @所有人 |
| **P1** | **≤ 15 分钟** | **≤ 2 小时** | 1 小时未响应 → 升级至技术负责人 | 飞书 @on-call + 群通知 |
| **P2** | **≤ 1 小时** | **≤ 8 小时** | 4 小时未响应 → 升级至组长 | 飞书工单 |
| **P3** | **≤ 24 小时** | **≤ 72 小时** | 48 小时未响应 → 升级 | 飞书工单 (跟踪) |

### 4.3 On-Call 轮值制度

```
  轮值安排:
    每周一 10:00 交接
    每班 1 名主 on-call + 1 名备份 on-call
  
  响应要求:
    - P0/P1: 必须立即响应
    - 其他时段: 15 分钟内响应 P0, 30 分钟内响应 P1
  
  轮值表:
    | 周次 | 主 on-call | 备份 on-call |
    |------|-----------|-------------|
    | 第1周 | [姓名]    | [姓名]       |
    | 第2周 | [姓名]    | [姓名]       |
    | 第3周 | [姓名]    | [姓名]       |
    | 第4周 | [姓名]    | [姓名]       |
```

### 4.4 告警升级路径

```
  P0 事件升级树:
  
  [事件触发]
       │
       ▼
  主 on-call (5分钟)
       │
       ├─ 已响应 ✔ → 处理事件
       │
       └─ 未响应 ✘ → 
              │
              ▼
      备份 on-call (5分钟)
              │
              ├─ 已响应 ✔ → 处理事件
              │
              └─ 未响应 ✘ →
                      │
                      ▼
              CTO / 技术负责人 (立即)
                      │
                      └─ 协调全体团队处理
```

---

## 5. 维护窗口规范

### 5.1 常规维护窗口

| 维护类型 | 频率 | 窗口时间 | 最大影响时长 | 通知要求 |
|---------|------|---------|-------------|---------|
| 常规维护 | 每月 1 次 | 周四 03:00-05:00 (UTC+8) | **≤ 30 分钟** | 提前 72 小时通知 |
| 紧急维护 | 按需 | 任何时间 | **按需** | 立即通知 + 事后复盘 |
| 安全更新 | 按需 | 任何时间 | **≤ 15 分钟** | 立即通知 |

### 5.2 维护期间服务影响

```
  常规维护窗口:
  03:00 ───────────────────────────────────── 05:00
       │                                         │
       ├─ 蓝绿部署无感切换 (0 停机)
       ├─ 数据库 schema 迁移 (只读降级, 不可写)
       ├─ 配置更新 (Nginx reload < 1s)
       └─ 容器更新 (滚动更新, 逐个重启)

  数据库迁移影响:
    - 添加列/索引: 无影响 (Online DDL)
    - 修改表结构: 短暂锁表 (< 5s)
    - 大数据量迁移: 需要更长维护窗口
```

### 5.3 维护通知模板

```markdown
## 链客宝 计划维护通知

**维护时间**: 2026-07-15 03:00 - 05:00 (UTC+8)
**影响范围**: 
  - API 服务: 无影响 (蓝绿切换)
  - 数据库: 暂停写入约 5 分钟
  - 前端: 无影响
**维护内容**: 
  1. 发布 v2.1.0 版本
  2. 数据库 schema 迁移 (orders 表添加索引)
  3. Nginx 配置优化
**预计总停机时间**: < 5 分钟
**回滚方案**: 执行 bash deploy/rollback.sh 可 2 分钟内回滚
```

### 5.4 维护窗口例外

以下情况可在无提前通知的情况下执行紧急维护:

- 安全漏洞修复 (CVE 评分 ≥ 7.0)
- 数据丢失风险 (存储故障、硬件异常)
- 第三方 API 变更导致服务中断
- DDoS 攻击等安全事件

---

## 6. SLA 例外条款

以下情况不计入可用性/性能 SLO 计算:

### 6.1 不可抗力

- 自然灾害 (地震、洪水、台风等)
- 大规模网络中断 (阿里云区域故障)
- 政府行为 (网络管制、域名封锁)
- 电力中断 (非阿里云侧原因)

### 6.2 第三方服务故障

- 阿里云 ECS 自身故障 (由阿里云 SLA 覆盖)
- CDN 服务故障
- DNS 解析故障
- 微信/支付宝支付网关故障
- 短信/邮件发送服务故障

### 6.3 计划内维护

- 常规维护窗口内 (已提前 72 小时通知)
- 紧急安全更新 (已通知)
- 经用户同意的临时维护

### 6.4 用户侧问题

- 用户本地网络问题
- 用户浏览器兼容性问题
- 用户 API 调用错误 (如错误的请求参数)
- 超出限流策略后的请求被拒绝 (429)

---

## 7. 度量与报告

### 7.1 度量方法

| 指标 | 数据来源 | 收集方式 | 报告频率 |
|------|---------|---------|---------|
| 可用性 | Prometheus + Blackbox Exporter | 外部探测 (每 30s) | 实时 |
| 响应时间 | 后端结构化日志 | OpenTelemetry / 日志解析 | 实时 |
| 错误率 | Nginx 日志 + 后端日志 | 4xx/5xx 计数 | 实时 |
| 吞吐量 | Nginx 日志 | 请求数/秒 | 实时 |
| 数据库性能 | pg_stat_statements | 慢查询日志 | 实时 |
| 前端性能 | Lighthouse CI / RUM | 合成监控 + 真实用户监控 | 每日 |

### 7.2 报告模板

```markdown
## 链客宝 月度 SLO 报告 — 2026年07月

### 一、可用性
| 组件 | SLO 目标 | 本月实际 | 是否达标 |
|------|---------|---------|---------|
| 整体可用性 | ≥ 99.5%  | 99.78%  | ✅      |
| API 可用性  | ≥ 99.7%  | 99.92%  | ✅      |
| 数据库可用性 | ≥ 99.9%  | 100.00% | ✅      |
| 支付模块    | ≥ 99.0%  | 99.45%  | ✅      |

### 二、性能
| 指标 | SLO 目标 | P50 | P95 | P99 | 是否达标 |
|------|---------|-----|-----|-----|---------|
| API 响应时间 | P95 < 500ms | 120ms | 340ms | 890ms | ✅ |

### 三、错误预算
| 项目 | 数值 |
|------|------|
| 月度总预算 | 3.6 小时 |
| 本月消耗 | 47 分钟 |
| 剩余预算 | 64.4% |
| 状态 | 🟢 正常 |

### 四、重大事件
| 日期 | 事件 | 等级 | 影响时长 | 根本原因 | 改进措施 |
|------|------|------|---------|---------|---------|
| 07-12 | 502 故障 | P0 | 15min | 后端 OOM | 增加内存限制 + 告警 |

### 五、改进计划
1. 添加 P99 响应时间告警
2. 实现数据库查询超时熔断
3. 优化支付回调重试机制
```

### 7.3 SLO 违规补偿

如果连续两个月 SLO 未达标, 触发以下补偿机制:

| 违规程度 | 补偿措施 |
|---------|---------|
| 可用性 < 99.0% | 全量复盘, 增加 2 倍 On-Call 人力 |
| 可用性 < 98.0% | 成立稳定性专项组, 暂停新功能开发 |
| P95 > 1000ms | 性能优化专项, 增加资源投入 |
| 数据丢失 | 按实际损失协商补偿 |

---

## 8. 附录: Prometheus 告警规则

### 8.1 核心告警规则

```yaml
# prometheus 告警规则 — 链客宝生产环境
groups:
  - name: chainke-alerts
    interval: 30s
    rules:

      # ── 可用性告警 ──────────────────────────────────
      - alert: ServiceDown
        expr: up{job="chainke-backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "后端服务不可用 ({{ $labels.instance }})"

      - alert: HealthCheckFailed
        expr: probe_success{target="https://liankebao.top/health"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "健康检查连续失败超过 2 分钟"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "API 错误率超过 5%"

      # ── 性能告警 ─────────────────────────────────────
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 响应时间超过 500ms (当前: {{ $value }}s)"

      - alert: CriticalSlowResponse
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 1.5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "P99 响应时间超过 1.5s (当前: {{ $value }}s)"

      # ── 数据库告警 ───────────────────────────────────
      - alert: PostgresDown
        expr: pg_up == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL 数据库不可用"

      - alert: PostgresHighConnections
        expr: pg_stat_activity_count > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "数据库连接数超过 80"

      - alert: PostgresSlowQueries
        expr: rate(pg_stat_activity_max_timestamp[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "慢查询数量超过阈值"

      # ── 系统资源告警 ─────────────────────────────────
      - alert: HighCPUUsage
        expr: rate(container_cpu_usage_seconds_total{name="chainke-backend"}[1m]) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "后端 CPU 使用率超过 80%"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes{name="chainke-backend"} / container_spec_memory_limit_bytes{name="chainke-backend"} > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "后端内存使用率超过 85%"

      - alert: DiskSpaceFull
        expr: (1 - (node_filesystem_avail_bytes{fstype=~"ext4|xfs"} / node_filesystem_size_bytes{fstype=~"ext4|xfs"})) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "磁盘使用率超过 85%"

      # ── 支付告警 ─────────────────────────────────────
      - alert: PaymentCallbackFailure
        expr: rate(payment_callback_failures_total[10m]) > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "支付回调失败率过高 (10分钟内超过5次)"
```

### 8.2 告警路由配置

```yaml
# Alertmanager 路由配置
route:
  receiver: "feishu-critical"
  group_by: ["alertname", "severity"]
  group_wait: 30s
  group_interval: 1m
  repeat_interval: 30m

  routes:
    - match:
        severity: critical
      receiver: "feishu-critical"
      repeat_interval: 10m

    - match:
        severity: warning
      receiver: "feishu-warning"
      repeat_interval: 1h

receivers:
  - name: "feishu-critical"
    webhook_configs:
      - url: "https://open.feishu.cn/open-apis/bot/v2/hook/..."  # 替换为实际 webhook
        send_resolved: true

  - name: "feishu-warning"
    webhook_configs:
      - url: "https://open.feishu.cn/open-apis/bot/v2/hook/..."  # 替换为实际 webhook
        send_resolved: true
```

---

## 修订历史

| 版本 | 日期 | 修订人 | 变更内容 |
|------|------|-------|---------|
| v1.0 | 2026-06-26 | [待定] | 初始版本 |

---

> 本文档由开发和运维团队共同维护。每季度评审更新一次。
