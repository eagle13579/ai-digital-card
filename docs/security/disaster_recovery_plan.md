# 灾难恢复计划 — Disaster Recovery Plan (DRP)

> **项目**: AI数智名片 (AI Digital Business Card)
> **文档编号**: SEC-DRP-001
> **版本**: v1.0(初稿)
> **创建日期**: 2026-08-06
> **状态**: 初稿待评审
> **策略所有者**: 安全与合规团队 (诸犍_CISO) / 运维团队
> **依据**: SOC 2 可用性 (Availability) 信任原则 · 附录 A「灾难恢复计划」缺失项
> **适用场景**: 数据中心故障、数据库损坏、服务器宕机、误操作删除、勒索软件攻击等导致服务不可用的事件

---

## 1. 恢复目标 (RTO / RPO)

| 指标 | 目标值 | 说明 | 当前状态 |
|------|--------|------|----------|
| **RTO**(恢复时间目标) | **≤ 4 小时** | 从灾难发生到核心服务(名片展示/匹配/解锁/支付回调)恢复可用 | ⚠️ 待演练验证 |
| **RPO**(恢复点目标) | **≤ 15 分钟** | 最多丢失 15 分钟内的数据变更 | ⚠️ 需启用 WAL 连续归档达标 |
| 恢复优先级 | P0 → P1 → P2 | P0:数据库+API 核心服务;P1:名片/匹配/支付;P2:报表/管理后台 | — |

### 1.1 RPO 达标路径(现状差距说明)

现有备份体系以**全量备份**为主(`deploy/disaster_recovery.sh backup full`),全量备份本身的 RPO 无法达到 15 分钟。达标措施:

1. 启用 PostgreSQL **WAL 连续归档**(`archive_mode = on`, `archive_command` 指向备份目录),每 15 分钟内的 WAL 段可持续归档 → RPO ≤ 15 分钟;
2. 或配置 PITR(时间点恢复):全量备份 + WAL 归档回放;
3. 全量备份频率:每日 1 次(凌晨),WAL 归档:持续/每 15 分钟。

---

## 2. 备份策略

### 2.1 现有备份资产(已部署)

| 资产 | 路径 | 功能 | 说明 |
|------|------|------|------|
| 灾难恢复脚本集 | `deploy/disaster_recovery.sh` | backup / restore / check / list | PostgreSQL 版,支持全量/ WAL / 代码 / 配置四种备份,支持 AES-256-GCM 加密、SHA-256 校验、异地同步、保留策略(全量30天/WAL7天/代码90天) |
| SQLite 每日备份脚本 | `deploy/backup-ai-card.sh` | 每日 03:00 sqlite3 .backup + gzip,保留 30 天 | 早期 SQLite 数据版(如仍在使用需保留,与 PostgreSQL 版二选一) |
| 备份同步脚本 | `deploy/sync-backup.py` | 备份文件同步 | 异地/对象存储同步辅助 |

### 2.2 备份执行配置

| 项 | 配置 |
|----|------|
| 全量备份命令 | `./deploy/disaster_recovery.sh backup full` |
| WAL 归档命令 | `./deploy/disaster_recovery.sh backup wal`(需 PostgreSQL 开启 archive_mode) |
| 配置/代码备份 | `./deploy/disaster_recovery.sh backup config` / `backup code` |
| 调度建议 | 全量:每日 03:00(cron);WAL:持续归档(每 15 分钟内);配置:每周 |
| 备份目录 | `${PROJECT_ROOT}/backups/db/{full,wal}`, `backups/code`, `backups/config` |
| 加密 | AES-256-GCM(`ENCRYPTION_KEY` 环境变量),校验和 `.sha256` |
| 保留策略 | 全量 30 天 / WAL 7 天 / 代码 90 天 |
| 异地容灾 | `REMOTE_BACKUP_ENABLED=true` + `REMOTE_BACKUP_URL`(S3/rclone),建议强制开启 |

### 2.3 备份内容范围

- **数据库**:PostgreSQL `ai_digital_business_card`(pg_dump custom 格式 + WAL 归档);
- **代码**:Git bundle 全量(`git bundle create --all --tags`);
- **配置**:`.env.production`、`.env.example`、`docker-compose.yml`、`deploy/nginx.conf`(加密打包);
- **文件存储**:头像/媒体对象存储(如使用云对象存储,由云服务商冗余策略保障)。

---

## 3. 恢复流程

> 前置条件:确认灾难现场已隔离(断网/停服),备份文件可用且校验和通过(`sha256sum -c`)。

### 步骤 1:启动恢复脚本,从备份恢复数据库

```bash
# 1. 列出可用备份,确认最新全量备份时间点
./deploy/disaster_recovery.sh list

# 2. 恢复最新备份(自动完成: 解密 → 校验和验证 → 断连 → 重建库 → pg_restore → 表数量验证)
./deploy/disaster_recovery.sh restore latest

# 或指定备份文件
./deploy/disaster_recovery.sh restore backups/db/full/ai_digital_business_card_20260806_030000.sql.gz.enc

# 3. 如启用 WAL 归档,回放 WAL 至灾难前最近时间点(实现 RPO ≤ 15 分钟)
#    psql -c "SELECT pg_wal_replay_pause();" ... (按 PITR 流程执行)
```

### 步骤 2:重启服务

```bash
# 4. 启动全部服务(应用 + 数据库 + Nginx + 监控)
docker-compose -f docker-compose.yml up -d

# 5. 确认数据库连接与迁移状态
docker-compose exec backend python -m app.cli migrate  # 如存在迁移入口
```

### 步骤 3:验证恢复结果

```bash
# 6. 健康检查(必须全部通过)
curl -f http://localhost:8201/health          # 或生产域名 /health
./deploy/bluegreen/health_check.sh            # 蓝绿部署健康检查脚本

# 7. 数据完整性抽查
./deploy/disaster_recovery.sh check           # 系统完整性检查
#     - 用户数 / 名片数 / 订单数 与备份元信息(backup_meta_*.json)对比
#     - 抽样核对 3-5 个用户的名片、匹配记录、支付记录

# 8. 业务冒烟测试
#     - 名片分享链接可打开 (GET /api/brochure/share/{token})
#     - 登录/注册可用, 匹配推荐可返回, 访客统计可写入
```

### 3.1 恢复时限分工(目标 RTO ≤ 4 小时)

| 阶段 | 负责角色 | 目标时限 |
|------|----------|----------|
| 灾难确认与通报 | 值班运维 → CISO | ≤ 15 分钟 |
| 备份可用性确认 | 运维团队 | ≤ 30 分钟 |
| 数据库恢复 | 运维团队 / DBA | ≤ 60 分钟 |
| 服务重启 | 运维团队 / 开发 | ≤ 30 分钟 |
| 验证与冒烟测试 | 开发 + 运维 | ≤ 45 分钟 |
| 对外通告与复盘 | CISO / 客服 | ≤ 30 分钟(并行) |

---

## 4. 演练计划(季度)

| 演练项 | 频率 | 内容 | 通过标准 | 记录 |
|--------|------|------|----------|------|
| 备份完整性演练 | 每月 | 随机抽取 1 份备份执行 restore 到隔离环境 | 恢复成功,表数量与元信息一致 | `backups/logs/` + 演练报告 |
| 数据库恢复演练 | **每季度** | 在隔离环境执行完整恢复流程(步骤 1-3) | RTO ≤ 4 小时,RPO ≤ 15 分钟(实测) | 季度演练报告 |
| 全流程灾难演练 | 每半年 | 模拟机房故障:切换异地备份 + 全流程恢复 | 核心服务 4 小时内可用 | 半年度演练报告 |
| 备份恢复自动检查 | 每日 | `disaster_recovery.sh check` + 备份文件存在性/大小校验 | 无告警 | 监控系统(Prometheus 告警) |

> 每次演练后需输出:演练记录(时间/参与人/步骤/结果)、发现的改进项、整改责任人。首次演练应在本季度内完成,以验证本计划可行性。

---

## 5. 责任分工与联系方式

| 角色 | 职责 | 备注 |
|------|------|------|
| 值班运维 | 灾难发现、初步处置、通报 | 7×24 |
| 运维负责人 | 备份恢复执行 | 恢复步骤 1-2 |
| 后端开发 | 服务重启、数据验证、冒烟测试 | 恢复步骤 2-3 |
| CISO | 应急指挥、对外通报、合规记录 | 全程 |
| 客服 | 用户通知与安抚 | 事件后 |

---

## 6. 相关文档

- 备份脚本: `deploy/disaster_recovery.sh`、`deploy/backup-ai-card.sh`、`deploy/sync-backup.py`
- 服务部署: `deploy/deploy.sh`、`deploy/rollback.sh`、`docker-compose.yml`
- SOC 2 就绪评估: `docs/security/soc2_readiness.md`(可用性「备份恢复」「灾难恢复计划」控制项)

---

*文档版本: v1.0 | 创建: 2026-08-06 | 审核人: [待定] | 状态: 初稿待评审*
