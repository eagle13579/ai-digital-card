# 链客宝 灾难恢复计划 (DR Plan)

> **版本**: 1.0.0  
> **更新日期**: 2026-07-04  
> **负责团队**: SRE / 基础架构  
> **审批人**: [待定]  

---

## 1. 概述

### 1.1 目的

本灾难恢复计划定义了链客宝在生产环境发生灾难性故障时的恢复流程、角色职责和验证机制，确保在 **RTO ≤ 15 分钟** 内恢复服务，且数据丢失不超过 **RPO ≤ 5 分钟**。

### 1.2 适用范围

- 主站 API 服务 (FastAPI + Uvicorn)
- 数据库 (PostgreSQL / SQLite)
- 缓存 (Redis)
- 前端静态资源 (Nginx + React SPA)
- ML 推理引擎
- 消息队列与事件总线

### 1.3 关键指标

| 指标 | 目标 | 说明 |
|:-----|:-----|:------|
| **RTO** (恢复时间目标) | ≤ 15 min | 从灾难发生到服务完全恢复 |
| **RPO** (恢复点目标) | ≤ 5 min | 最多允许丢失 5 分钟数据 |
| **MTBF** (平均故障间隔) | ≥ 720 h | 目标 30 天无计划外宕机 |
| **MTTR** (平均修复时间) | ≤ 30 min | 从发现到修复平均时间 |
| **可用性目标** | ≥ 99.9% | 月度 SLA 可用性 |

---

## 2. 灾难场景分类

### 2.1 故障等级定义

| 等级 | 描述 | 示例 | RTO 要求 |
|:-----|:------|:------|:----------|
| **P0** (严重) | 完全不可用，影响所有用户 | 主区宕机 / 数据库损坏 | ≤ 15 min |
| **P1** (高) | 核心功能受损 | Redis 宕机 / ML 引擎故障 | ≤ 30 min |
| **P2** (中) | 非核心功能受损 | 支付网关超时 / 部分 API 降级 | ≤ 2 h |
| **P3** (低) | 轻微影响 | 部分页面样式异常 / 日志延迟 | ≤ 24 h |

### 2.2 灾难场景

| 场景 | 等级 | 典型原因 |
|:-----|:------|:----------|
| 主可用区宕机 | P0 | 云服务商故障 / 网络分区 / 电力中断 |
| 数据库损坏/丢失 | P0 | 磁盘损坏 / 误操作 / 勒索软件 |
| Redis 缓存雪崩 | P1 | 大量 key 同时过期 / 内存耗尽 |
| 应用层 OOM | P1 | 内存泄漏 / 流量突增 |
| 证书过期 | P2 | SSL/TLS 证书未及时续期 |
| DNS 解析失败 | P2 | DNS 服务商故障 / 配置错误 |

---

## 3. 备份策略

### 3.1 数据库备份

#### PostgreSQL (主数据库)

| 类型 | 频率 | 保留策略 | 存储位置 |
|:-----|:------|:----------|:----------|
| **全量备份** | 每日 03:00 (UTC) | 保留 30 天 | 对象存储 (OSS/S3) + 本地 |
| **增量备份** | 每小时 | 保留 7 天 | 对象存储 (OSS/S3) |
| **WAL 归档** | 连续 (实时) | 保留 3 天 | 本地 + 远程存储 |
| **逻辑备份** (pg_dump) | 每日 04:00 (UTC) | 保留 7 天 | 对象存储 |

```bash
# 全量备份 (pg_basebackup)
pg_basebackup -D /backup/postgres/full/$(date +%Y%m%d) \
  -F t -z -P -v \
  -h localhost -p 5432 -U replicator

# 逻辑备份 (pg_dump)
pg_dump -h localhost -U chainke -d chainke_prod \
  -F c -f /backup/postgres/logical/chainke_$(date +%Y%m%d).dump
```

#### Redis 缓存

| 类型 | 频率 | 保留策略 | 存储位置 |
|:-----|:------|:----------|:----------|
| RDB 快照 | 每 60 分钟 | 保留 7 天 | 本地磁盘 |
| AOF 日志 | 每秒 (always) | 保留 3 天 | 本地磁盘 |
| 备份导出 | 每日 05:00 (UTC) | 保留 30 天 | 对象存储 |

```bash
# Redis 手动备份
redis-cli SAVE
cp /data/redis/dump.rdb /backup/redis/$(date +%Y%m%d)_dump.rdb

# 导出到对象存储
aws s3 cp /backup/redis/ s3://chainke-backup/redis/ --recursive
```

### 3.2 配置与代码备份

- 所有配置文件通过 Git 管理，自动推送到 GitHub
- Docker Compose / K8s 资源配置存储于 `deploy/` 目录
- 敏感信息 (密钥/密码) 通过 vault/环境变量管理，定期导出加密备份
- 数据库迁移脚本存储于 `backend/migrations/`

### 3.3 备份验证

- **每日**: 自动验证备份文件完整性 (checksum)
- **每周**: 在测试环境执行一次恢复演练
- **每月**: 全流程 DR 演练 (参见第 7 节)

---

## 4. 容灾架构

### 4.1 多可用区部署

```
                    ┌──────────────────────────────┐
                    │     DNS / 负载均衡 (多活)      │
                    │   liankebao.top → A: 47.116.116.87  │
                    │  备: 47.116.116.88 (备用服务器)│
                    └──────┬───────────────┬───────┘
                           │               │
              ┌────────────▼────┐   ┌──────▼────────────┐
              │  主可用区 (AZ-A)  │   │  备可用区 (AZ-B)   │
              │  47.116.116.87   │   │  47.116.116.88    │
              │                  │   │                   │
              │  ┌──────────┐   │   │  ┌──────────┐    │
              │  │ Nginx    │   │   │  │ Nginx    │    │
              │  │ Backend  │   │   │  │ Backend  │    │
              │  │ Postgres │   │   │  │ Postgres │    │
              │  │ Redis    │   │   │  │ Redis    │    │
              │  └──────────┘   │   │  └──────────┘    │
              └─────────────────┘   └──────────────────┘
```

### 4.2 数据库同步

- **流复制**: PostgreSQL 主从异步流复制 (synchronous_commit = remote_write)
- **Redis 主从**: Redis Sentinel 自动故障转移
- **备份同步**: 对象存储跨区域复制

### 4.3 DNS 故障切换

```mermaid
sequenceDiagram
    participant User
    participant DNS
    participant AZ_A as 主可用区 (AZ-A)
    participant AZ_B as 备可用区 (AZ-B)
    participant SRE as SRE 值班

    User->>DNS: 请求 liankebao.top
    DNS->>AZ_A: 解析到主区 IP
    AZ_A-->>SRE: ❌ 宕机告警 (P0)
    SRE->>DNS: 手动切换 DNS A 记录
    Note over DNS: TTL = 60s (快速生效)
    DNS->>AZ_B: 解析到备区 IP
    User->>AZ_B: 请求到达备区
    AZ_B-->>SRE: ✅ 服务恢复确认
```

---

## 5. 恢复步骤 (Runbook)

### 5.1 P0: 主区完全宕机

```bash
# ════════════════════════════════════════════════════════════════
# 链客宝 DR — P0 恢复 Runbook
# 场景: 主可用区完全不可用 (47.116.116.87 无响应)
# ════════════════════════════════════════════════════════════════

# Step 1: 确认灾难 (30s)
# ── 检查主服务器可达性
ping -c 3 47.116.116.87
curl -s -o /dev/null -w "%{http_code}" http://47.116.116.87:8001/health

# Step 2: 切换到备服务器 (2min)
# ── SSH 到备服务器
ssh root@47.116.116.88

# ── 启动数据库 (如果未运行)
docker start chainke-postgres
docker start chainke-redis

# ── 恢复最近的备份 (如果需要)
# 从对象存储拉取最新全量备份 + WAL
aws s3 sync s3://chainke-backup/postgres/ /backup/postgres/
cd /backup/postgres/full/
LATEST=$(ls -t | head -1)
pg_ctl -D /var/lib/postgresql/data stop
rm -rf /var/lib/postgresql/data/*
pg_basebackup -D /var/lib/postgresql/data -X stream -P -v \
  -h 47.116.116.87 -U replicator  # 如果主区 DB 还可读
# 如果主区完全不可用，从备份恢复:
tar xzf /backup/postgres/full/$LATEST -C /var/lib/postgresql/data/

# ── 启动后端服务
cd /var/www/liankebao
docker compose up -d backend

# Step 3: DNS 切换 (2min)
# ── 修改 DNS A 记录指向备服务器 IP
# 在 DNS 控制台将 liankebao.top → 47.116.116.88
# TTL 设置 60s 以加速切换

# Step 4: 验证恢复 (1min)
# ── 检查服务健康
curl -s http://localhost:8001/health
curl -s http://localhost:8001/api/v1/monitor/health
curl -s http://localhost:8001/api/v1/sla/status

# ── 检查外部可达性
curl -s https://liankebao.top/health

# Step 5: 通知团队 (并行)
# ── 在飞书/钉钉群发送恢复确认
echo "✅ [DR] 主区故障已切换至备区，服务已恢复"
echo "   切换耗时: $(date -d @$(( $(date +%s) - START_TIME )) +%M分%S秒)"

# Step 6: 事后复盘
# ── 记录故障时间线
# ── 分析根本原因
# ── 更新 DR 计划
```

### 5.2 P1: 数据库故障

```bash
# 场景: PostgreSQL 宕机 / 数据损坏

# Step 1: 尝试快速重启
docker restart chainke-postgres
# 检查日志
docker logs --tail 50 chainke-postgres

# Step 2: 如果无法恢复，切换到从库
# 将从库提升为主库
psql -h slave-host -U postgres -c "SELECT pg_promote();"

# Step 3: 更新应用连接字符串
export DATABASE_URL="postgresql://user:password@slave-host:5432/chainke_prod"

# Step 4: 修复原主库后重建复制
```

### 5.3 P2: Redis 缓存雪崩

```bash
# 场景: Redis 大量 key 同时过期 / 内存耗尽

# Step 1: 重启 Redis
docker restart chainke-redis

# Step 2: 如果内存不足，调整配置
redis-cli CONFIG SET maxmemory 1gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Step 3: 清理过期 key
redis-cli --eval scripts/cleanup_expired.lua

# Step 4: 检查缓存命中率
redis-cli INFO stats | grep hits
```

---

## 6. 监控与告警

### 6.1 DR 相关告警

| 告警规则 | 触发条件 | 严重级别 | 响应时间 |
|:---------|:----------|:----------|:----------|
| 服务宕机 | up == 0 持续 1min | **P0-Critical** | ≤ 5 min |
| 健康检查失败 | /health 失败 2min | **P0-Critical** | ≤ 5 min |
| 5xx 错误率 > 1% | 5xx rate > 1% 持续 5min | **P1-Warning** | ≤ 15 min |
| 数据库连接池耗尽 | 连接数 > 90% | **P1-Warning** | ≤ 15 min |
| 磁盘空间 < 10% | 磁盘使用率 > 90% | **P1-Warning** | ≤ 30 min |
| 备份失败 | 自动备份脚本退出码非 0 | **P1-Warning** | ≤ 1 h |
| SSL 证书即将过期 | 剩余天数 < 30 | **P2-Info** | ≤ 7 天 |

### 6.2 告警通知渠道

| 级别 | 通知渠道 | 值班人员 |
|:-----|:----------|:----------|
| P0-Critical | 飞书 + 电话 + 短信 | SRE 值班 + 技术负责人 |
| P1-Warning | 飞书 + 钉钉 | SRE 值班 |
| P2-Info | 飞书群 | 团队 |

---

## 7. DR 演练计划

### 7.1 演练频率

| 演练类型 | 频率 | 参与人员 | 持续时间 |
|:----------|:------|:----------|:----------|
| 桌面推演 | 每周 | SRE 团队 | 30 min |
| 组件级演练 | 每两周 | SRE + 开发 | 1 h |
| **全流程 DR 演练** | **每月** | **全员** | **2 h** |

### 7.2 全流程 DR 演练步骤

```
月 DR 演练计划 — 示例: 主区宕机场景

┌────────────────────────────────────────────────────┐
│  DR 演练 #202607                                   │
│  场景: 模拟主可用区 (AZ-A) 完全不可用                │
│  日期: 2026-07-15 14:00 UTC                        │
│  预计耗时: 2 小时                                   │
└────────────────────────────────────────────────────┘

Phase 1: 准备 (15 min)
  ① 通知团队演练即将开始
  ② 记录当前基线指标 (延迟/错误率/吞吐量)
  ③ 确保备区环境已同步最新代码

Phase 2: 模拟故障 (5 min)
  ① 在主服务器执行: iptables -A INPUT -j DROP
  ② 确认监控告警触发 (P0-Critical)

Phase 3: 故障切换 (15 min)
  ① SRE 确认灾难并切换到备区
  ② 执行 DNS 切换
  ③ 验证备区服务正常

Phase 4: 恢复与回切 (30 min)
  ① 修复主区环境
  ② 数据同步回主区
  ③ DNS 切回主区
  ④ 最终确认所有指标恢复

Phase 5: 复盘 (15 min)
  ① 记录实际 RTO/RPO
  ② 识别改进点
  ③ 更新 DR 文档

Phase 6: 清理 (10 min)
  ① 清除所有模拟故障注入
  ② 恢复防火墙规则
  ③ 确认生产环境完全正常
```

### 7.3 演练评分标准

| 指标 | 合格 | 良好 | 优秀 |
|:-----|:------|:------|:------|
| RTO | ≤ 30 min | ≤ 20 min | ≤ 10 min |
| RPO | ≤ 10 min | ≤ 5 min | ≤ 2 min |
| 数据完整性 | 100% | 100% | 100% |
| 无人工干预步骤 | < 5 步 | < 3 步 | ≤ 1 步 |

---

## 8. 职责矩阵 (RACI)

| 活动 | SRE 值班 | SRE 负责人 | 后端开发 | 运维 | 产品 |
|:-----|:----------|:------------|:----------|:------|:------|
| 监控告警 | **R** | A | I | I | I |
| 灾难确认 | **R** | **R** | I | I | I |
| 故障切换执行 | **R** | A | C | C | I |
| 数据恢复 | **R** | A | C | I | I |
| 通知用户 | I | **R** | I | A | C |
| 根因分析 | C | **R** | **R** | C | I |
| DR 演练计划 | C | **R** | C | C | A |
| 备份验证 | **R** | A | I | I | I |

> R = 执行者, A = 审批者, C = 咨询者, I = 通知对象

---

## 9. 附录

### 9.1 快速参考卡

```text
┌────────────────────────────────────────────────────────┐
│ 🔴 链客宝 DR 快速参考卡                                │
├────────────────────────────────────────────────────────┤
│                                                        │
│  P0 主区宕机 → 执行: DR_RUNBOOK_P0.md                   │
│                                                        │
│  ① SSH 到备服务器                                       │
│     ssh root@47.116.116.88                              │
│                                                        │
│  ② 启动服务                                             │
│     docker start chainke-postgres chainke-redis         │
│     cd /var/www/liankebao && docker compose up -d       │
│                                                        │
│  ③ DNS 切换 → liankebao.top → 47.116.116.88            │
│                                                        │
│  ④ 验证                                                │
│     curl https://liankebao.top/health                   │
│                                                        │
│  ⑤ 通知                                                │
│     #P0-DR 群: "服务已切换至备区, 请关注"                │
│                                                        │
│  SRE 值班电话: [待填写]                                 │
└────────────────────────────────────────────────────────┘
```

### 9.2 关键联系信息

| 角色 | 姓名 | 电话 | 飞书 |
|:-----|:------|:------|:------|
| SRE 值班 | [待填写] | [待填写] | @sre-oncall |
| 技术负责人 | [待填写] | [待填写] | @tech-lead |
| 运维 | [待填写] | [待填写] | @ops |
| 数据库管理员 | [待填写] | [待填写] | @dba |

### 9.3 修订历史

| 版本 | 日期 | 修订内容 | 修订人 |
|:-----|:------|:----------|:--------|
| 1.0.0 | 2026-07-04 | 初始版本 — 完整 DR 计划 | SRE 团队 |

---

> **本文件为链客宝核心运维文档，请妥善保管。**  
> 每次 DR 演练后需更新演练记录章节。
