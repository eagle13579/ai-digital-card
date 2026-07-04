# 链客宝 Backend — 数据库启动日志观察指南

> 本文档用于在 Docker / 本地环境下观察数据库连接池的启动与运行日志，帮助快速
> 定位「连接耗尽」「MySQL/PostgreSQL 不可达」「连接泄露」等常见问题。
>
> 适用版本: `backend/app/database.py` V2
> 相关文档: `backend/docs/adr/ADR-001-FastAPI-SQLAlchemy-三驱动数据库架构.md`

---

## 1. 快速开启 DEBUG 日志

### 1.1 Docker Compose 方式（推荐）

```bash
# 启动时临时打开 DEBUG 级别 (仅用于排查, 不要长期保留)
LOG_LEVEL=DEBUG docker compose up -d backend

# 持续观察数据库相关日志
docker compose logs -f backend | grep -E "\[Database\]|checkout|checkin|ping|dispose"
```

或者在容器运行时直接注入：

```bash
docker compose exec -e LOG_LEVEL=DEBUG backend python -c "from app import database; database.ping()"
```

### 1.2 本地方式

```powershell
# PowerShell
$env:LOG_LEVEL="DEBUG"
$env:DATABASE_URL="sqlite:///:memory:"
python -m app.main
```

### 1.3 启动时一次性打印连接池快照

```bash
# 容器内
docker compose exec backend python -c "from app.database import log_pool_snapshot; print(log_pool_snapshot(tag='manual-check'))"
```

---

## 2. 启动时的正常日志序列

以 `LOG_LEVEL=DEBUG` 为例，一个健康的 PostgreSQL 启动流程如下：

```
INFO  chainke.database [Database] 驱动: postgresql (URL: postgresql+asyncpg://chainke:***@postgres:5432/chainke)
DEBUG chainke.database [Database] 新连接建立 (conn_id=140234567890, record_id=140234567912)
INFO  chainke.database [Database] checkout 连接池: type=QueuePool active=1 idle=0 overflow=0 (pool_size=10, max_overflow=20, driver=postgresql, conn_id=140234567890, record_id=140234567912)
DEBUG chainke.database [Database] checkin 连接池: type=QueuePool active=0 idle=1 (driver=postgresql, conn_id=140234567890, record_id=140234567912)
INFO  chainke.database [Database] ping 开始 (driver=postgresql)
INFO  chainke.database [Database] ping 成功 (driver=postgresql)
```

字段解读：

| 字段 | 含义 |
|------|------|
| `conn_id` | `id(dbapi_connection)`，同一个物理连接在 checkout/checkin 间保持一致 |
| `record_id` | `id(ConnectionRecord)`，SQLAlchemy 的连接记录对象 ID |
| `type` | 连接池类型：`QueuePool`(MySQL/PG) / `NullPool`(SQLite) |
| `active` | 正在被业务占用的连接数（= 已 checkout 未 checkin） |
| `idle` | 空闲连接数（= 已 checkout 但已 checkin 回池） |
| `overflow` | 超过 `pool_size` 的溢出连接数 |
| `driver` | 自动识别：`sqlite` / `mysql` / `postgresql` / `mssql` / `unknown` |

---

## 3. 常见异常日志与排查

### 3.1 MySQL / PostgreSQL 不可达

```
INFO  chainke.database [Database] ping 开始 (driver=mysql)
WARNING chainke.database [Database] ping 失败: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server on 'mysql' ([WinError 10061] 由于目标计算机积极拒绝，无法连接。)") (driver=mysql, pool={'size': 0, 'checked_in': 0, 'checked_out': 0, 'overflow': 0, 'driver': 'mysql', 'pool_size': 10, 'max_overflow': 20})
```

**排查步骤**：

1. 检查容器网络与主机名：
   ```bash
   docker compose exec backend python -c "import socket; print(socket.gethostbyname('mysql'))"
   ```
2. 确认数据库服务健康：
   ```bash
   docker compose ps
   docker compose logs postgres --tail=100
   ```
3. 手动验证：
   ```bash
   docker compose exec postgres pg_isready -U chainke -d chainke
   ```

### 3.2 连接池耗尽

```
INFO  chainke.database [Database] checkout 连接池: type=QueuePool active=30 idle=0 overflow=20 (pool_size=10, max_overflow=20, driver=postgresql, conn_id=..., record_id=...)
```

**判断**：
- `active` 持续接近 `pool_size + max_overflow`，且没有对应数量的 `checkin` 日志 → **连接泄露**
- `overflow` > 0 且持续增长 → **流量突增或 SQL 慢查询**

**排查**：
- 通过 `conn_id` 关联该连接的完整生命周期，在 `checkout` 与 `checkin` 之间是否有异常堆栈
- 检查所有 `async with session:` / `with SessionLocal() as db:` 是否被妥善关闭（尤其是 `try/finally`）
- 临时增大 `DATABASE_POOL_SIZE` 缓解，同时修复泄露代码

### 3.3 连接被服务端主动断开（detach）

```
WARNING chainke.database [Database] 连接已 detach (可能因回收或异常关闭, conn_id=140234567890, record_id=140234567912)
```

**常见原因**：
- MySQL `wait_timeout` (默认 28800s) 到期
- PostgreSQL `idle_in_transaction_session_timeout` / TCP keepalive
- 负载均衡器（如 PgBouncer/ProxySQL）主动断开

**处理**：
- 已启用 `pool_pre_ping=True`（在 MySQL/PG 下）可自动规避大部分 "连接已死" 问题
- 调整 `DATABASE_POOL_RECYCLE` 小于服务端 `wait_timeout`
- detach 本身不会让业务请求失败：SQLAlchemy 会重新 checkout 新连接

### 3.4 SQLite NullPool 下的正常日志

```
INFO  chainke.database [Database] checkout 连接池: type=NullPool active=0 idle=0 overflow=0 (pool_size=10, max_overflow=20, driver=sqlite, conn_id=140234567890, record_id=140234567912)
```

`NullPool` 下没有真正的连接池，`active/idle` 永远显示 0 是正常的，主要用于本地开发调试。

---

## 4. 常用诊断命令

### 4.1 实时过滤数据库日志

```bash
# 所有数据库相关
docker compose logs -f backend | grep -E "\[Database\]"

# 只看连接事件
docker compose logs -f backend | grep -E "checkout|checkin|connect|detach"

# 只看警告与错误
docker compose logs -f backend | grep -E "WARNING|ERROR" | grep -E "\[Database\]"

# 只看 ping 健康检查
docker compose logs -f backend | grep -E "ping"
```

### 4.2 查看 Prometheus 连接池指标

```bash
# 暴露的指标
curl -s http://localhost:8001/metrics | grep -E "db_pool|sqlalchemy"
```

关键指标：
- `db_pool_active_connections`：活跃连接
- `db_pool_idle_connections`：空闲连接
- `db_pool_overflow_connections`：溢出连接

### 4.3 强制释放连接（排查时可用）

```bash
docker compose exec backend python -c "
from app.database import dispose_engine, log_pool_snapshot
log_pool_snapshot(tag='before-dispose')
dispose_engine()
log_pool_snapshot(tag='after-dispose')
"
```

---

## 5. 推荐生产配置

在 `docker-compose.yml` 的 backend environment 中推荐：

```yaml
environment:
  - LOG_LEVEL=INFO            # 默认 INFO; 排查时改为 DEBUG
  - LOG_JSON=1                # ELK/Loki/Grafana 友好
  - DATABASE_POOL_SIZE=10      # 常驻连接
  - DATABASE_MAX_OVERFLOW=20  # 峰值溢出
  - DATABASE_POOL_RECYCLE=1800  # 30 分钟回收一次, 规避 wait_timeout
```

日志采集侧建议：

```json
// logback / filebeat 过滤 pattern (conn_id 可作为 trace 关联键)
{ "match": {"message": {"regexp": "conn_id=([0-9]+)"}}, "extract": {"conn_id": "\\1"} }
```

---

## 6. 连接 ID 追踪原理

`conn_id` 使用 Python 内置 `id()` 函数获取 `dbapi_connection` 对象的内存地址。
在单次数据库会话中，`conn_id` 是稳定的：

```
connect → conn_id=A   # 创建底层驱动连接
checkout → conn_id=A  # 从池中取出
   ... 业务使用 ...
checkin → conn_id=A   # 归还池
detach  → conn_id=A   # 连接被剥离 (可选)
```

通过 `conn_id` 可在海量日志中还原单条连接的完整生命周期，快速定位泄露、慢查询、
异常断连等问题。

---

## 7. 附录：完整日志字段

每条 `[Database]` 日志均采用 `[Database] <子系统> <动作>` 的统一前缀：

| 前缀 | 触发时机 |
|------|----------|
| `[Database] 驱动:` | 引擎初始化 |
| `[Database] 新连接建立` | 物理连接建立（DEBUG） |
| `[Database] checkout 连接池:` | 业务取连接（INFO/DEBUG） |
| `[Database] checkin 连接池:` | 业务归还连接（DEBUG） |
| `[Database] 连接已 detach` | 连接被剥离（WARNING） |
| `[Database] get_db 会话发生异常` | 会话回滚（WARNING） |
| `[Database] dispose_engine` | 引擎释放（WARNING） |
| `[Database] ping 开始/成功/失败` | 健康检查 |
| `[Database][<tag>] pool snapshot` | 主动快照 |
