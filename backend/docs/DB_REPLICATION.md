# 多区域数据库复制方案

## 概述

链客宝采用 **PostgreSQL Streaming Replication（1主N从）** 架构实现多区域高可用。

| 区域 | 角色 | 云厂商 | 节点地址 |
|------|------|--------|----------|
| 中国区（上海） | **主库 (Primary)** | 阿里云 | `pg-cn-shanghai.chainke.internal:5432` |
| 亚太区（新加坡） | 从库 (Replica) | AWS Singapore | `pg-ap-singapore.chainke.internal:5432` |
| 北美区（美西） | 从库 (Replica) | AWS us-west-2 | `pg-us-west.chainke.internal:5432` |

## 架构图

```
                         ┌─────────────────────┐
                         │   Patroni / HAProxy  │
                         │   (集群管理 + 读写分离)│
                         └──────┬──────────────┘
                                │
          Write ────────────────┤         Read ───────────────┐
                                │                              │
                    ┌───────────▼──────────┐                  │
                    │  主库 (Primary)      │                  │
                    │  阿里云上海          │                  │
                    │  写 + 强一致读       │                  │
                    └───────┬──────────────┘                  │
                            │ Streaming Replication            │
              ┌─────────────┼────────────────────┐            │
              │             │                     │            │
     ┌────────▼──────┐ ┌───▼──────────┐  ┌──────▼────────┐   │
     │从库 (Replica) │ │从库 (Replica) │  │从库 (Replica) │   │
     │AWS 新加坡     │ │AWS 美西       │  │阿里云上海     │   │
     │就近读         │ │就近读         │  │本地读         │   │
     └───────────────┘ └──────────────┘  └───────────────┘   │
              │                │                 │            │
              └────────────────┼─────────────────┘            │
                               │                              │
                    ┌──────────▼──────────┐                   │
                    │  GeoDNS/GeoLB       │◄──────────────────┘
                    │  按用户IP路由到最近   │
                    └─────────────────────┘
```

## 1. PostgreSQL Streaming Replication 配置

### 1.1 主库配置（阿里云上海）

```ini
# postgresql.conf — 主库
listen_addresses = '*'
wal_level = replica
max_wal_senders = 10
wal_keep_size = 1024           # MB
max_replication_slots = 10
hot_standby = on
synchronous_commit = remote_write
synchronous_standby_names = 'FIRST 1 (replica_cn, replica_ap, replica_us)'
```

```ini
# pg_hba.conf — 复制连接权限
# TYPE  DATABASE  USER       ADDRESS               METHOD
host    replication replicator 10.0.0.0/8            scram-sha-256
host    replication replicator 172.16.0.0/12        scram-sha-256
host    replication replicator 192.168.0.0/16       scram-sha-256
```

### 1.2 从库配置（AWS 新加坡 / 美西）

```ini
# postgresql.conf — 从库
primary_conninfo = 'host=pg-cn-shanghai.chainke.internal port=5432 user=replicator password=**** application_name=replica_ap'
primary_slot_name = 'replica_ap_slot'
hot_standby = on
hot_standby_feedback = on
max_standby_streaming_delay = 30s
wal_receiver_timeout = 60s
wal_receiver_status_interval = 10s
```

### 1.3 复制槽管理

```sql
-- 在主库创建复制槽（每个从库一个）
SELECT * FROM pg_create_physical_replication_slot('replica_cn_slot');
SELECT * FROM pg_create_physical_replication_slot('replica_ap_slot');
SELECT * FROM pg_create_physical_replication_slot('replica_us_slot');

-- 监控复制槽
SELECT slot_name, slot_type, active, restart_lsn, confirmed_flush_lsn
FROM pg_replication_slots;
```

## 2. 读写分离策略

### 2.1 HAProxy 配置

```
# 写请求 → 主库（只有一台）
frontend pg_write
    bind *:5433
    default_backend pg_primary

backend pg_primary
    option pgsql-check user health_checker
    server primary-cn pg-cn-shanghai.chainke.internal:5432 check inter 5s fall 3 rise 2

# 读请求 → 就近从库（由 GeoDNS 决定）
frontend pg_read
    bind *:5434
    default_backend pg_replicas

backend pg_replicas
    option pgsql-check user health_checker
    server replica-cn pg-cn-shanghai-replica.chainke.internal:5432 check inter 5s fall 3 rise 2
    server replica-ap pg-ap-singapore.chainke.internal:5432 check inter 5s fall 3 rise 2
    server replica-us pg-us-west.chainke.internal:5432 check inter 5s fall 3 rise 2
```

### 2.2 应用层读写分离

```python
# 在数据库连接中根据请求类型分发
DATABASE_URLS = {
    "write": "postgresql+asyncpg://chainke:****@pg-primary:5432/chainke",
    "read_cn": "postgresql+asyncpg://chainke:****@pg-cn-read:5432/chainke",
    "read_ap": "postgresql+asyncpg://chainke:****@pg-ap-read:5432/chainke",
    "read_us": "postgresql+asyncpg://chainke:****@pg-us-read:5432/chainke",
}
```

## 3. 故障转移 — Patroni

### 3.1 Patroni 配置

```yaml
# patroni.yml
scope: chainke
namespace: /db/
name: pg-cn-shanghai

restapi:
  listen: 0.0.0.0:8008
  connect_address: pg-cn-shanghai.chainke.internal:8008

etcd:
  host: etcd.chainke.internal:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576  # 1MB
    postgresql:
      use_pg_rewind: true
      use_slots: true
      parameters:
        wal_level: replica
        hot_standby: "on"
        max_connections: 200
        max_wal_senders: 10
        wal_keep_size: 1024

  initdb:
  - encoding: UTF8
  - data-checksums

  pg_hba:
  - host replication replicator 0.0.0.0/0 scram-sha-256
  - host all all 0.0.0.0/0 scram-sha-256

postgresql:
  listen: 0.0.0.0:5432
  connect_address: pg-cn-shanghai.chainke.internal:5432
  data_dir: /var/lib/postgresql/data/pgdata
  bin_dir: /usr/lib/postgresql/16/bin
  authentication:
    replication:
      username: replicator
      password: ****
    superuser:
      username: postgres
      password: ****
    rewind:
      username: rewind_user
      password: ****

tags:
  nofailover: false
  noloadbalance: false
  clonefrom: false
  replicatefrom: null
```

### 3.2 故障转移过程

1. **检测**: Patroni 通过 etcd 分布式锁检测主库心跳丢失（`ttl: 30s`）
2. **选主**: 剩余从库中选一个 `lag < 1MB` 且 LSN 最新的升为主库
3. **切换**: 新主库提升，HAProxy 自动更新后端，应用层连接池重连
4. **恢复**: 原主库恢复后，通过 `pg_rewind` 作为从库自动加入集群

### 3.3 手动触发切换

```bash
# 优雅切换（计划内维护）
patronictl -c patroni.yml switchover --master pg-cn-shanghai --candidate pg-ap-singapore

# 强制切换（主库彻底宕机）
patronictl -c patroni.yml failover --master pg-cn-shanghai --candidate pg-ap-singapore
```

## 4. 数据同步延迟监控

### 4.1 延迟查询

```sql
-- 主库上查看所有从库延迟
SELECT
    client_addr,
    application_name,
    state,
    write_lag,
    flush_lag,
    replay_lag
FROM pg_stat_replication;

-- 从库上查看回放延迟
SELECT
    pg_last_wal_receive_lsn(),
    pg_last_wal_replay_lsn(),
    pg_wal_lsn_diff(pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn()) AS replay_lag_bytes;
```

### 4.2 自动告警阈值

| 指标 | 警告阈值 | 严重阈值 | 操作 |
|------|---------|---------|------|
| 复制延迟 | > 500ms | > 1s | 通知运维，检查网络/IO |
| 复制槽活跃 | 非活跃 | - | 检查从库连接状态 |
| WAL 归档延迟 | > 10min | > 30min | 检查归档存储 |

## 5. 同步拓扑

```
主库(上海) ──sync──▶ 从库_A(上海, 同城)
   │
   ├──async──▶ 从库_B(新加坡, 跨区域)
   │
   └──async──▶ 从库_C(美西, 跨区域)
```

- **同城从库**: 使用 `synchronous_commit = on`，保证关键事务的强一致性
- **跨区域从库**: 使用 `synchronous_commit = remote_write`，平衡延迟与数据安全

## 6. 连接池配置

```python
# SQLAlchemy 连接池（主库写）
PRIMARY_POOL = {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_recycle": 1800,
    "pool_pre_ping": True,
}

# SQLAlchemy 连接池（从库读）
REPLICA_POOL = {
    "pool_size": 50,
    "max_overflow": 100,
    "pool_recycle": 1800,
    "pool_pre_ping": True,
}
```

## 7. 恢复演练

每月自动执行故障转移演练（参见 `deploy/scripts/failover.py`），验证:
- 主库宕机后从库自动接管时间 < 30s
- 数据零丢失（同步复制模式）
- 应用层自动重连成功
- 演练完成后自动回切

## 8. 安全性

- 复制链路使用 TLS 加密
- 复制用户 `replicator` 仅授予 `REPLICATION` 权限
- 所有节点间通信在 VPC 内网进行
- 敏感凭据通过 Vault 管理，不写入配置文件
