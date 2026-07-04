# 链客宝 故障恢复手册

> 版本: v1.0 | 最后更新: 2026-06-26
> 适用环境: 阿里云 ECS (47.116.116.87) — Docker Compose 部署

---

## 目录

1. [快速诊断命令速查](#1-快速诊断命令速查)
2. [502/504 错误诊断流程](#2-502504-错误诊断流程)
3. [数据库损坏恢复步骤](#3-数据库损坏恢复步骤)
4. [蓝绿部署回滚步骤](#4-蓝绿部署回滚步骤)
5. [服务进程僵死恢复](#5-服务进程僵死恢复)
6. [断网/服务器重启后自愈流程](#6-断网服务器重启后自愈流程)
7. [常见故障处理矩阵](#7-常见故障处理矩阵)

---

## 1. 快速诊断命令速查

```bash
# ─── 服务状态 ──────────────────────────────────────────
docker ps                              # 查看所有运行中容器
docker ps -a                           # 查看所有容器（含已停止）
docker stats                           # 实时资源占用 (CPU/内存/网络)

# ─── 容器日志 ──────────────────────────────────────────
docker logs chainke-backend --tail=100   # 后端最近 100 行日志
docker logs chainke-nginx --tail=50      # Nginx 最近 50 行日志
docker logs chainke-postgres --tail=50   # PostgreSQL 最近 50 行日志
docker compose logs -f backend          # 实时跟踪后端日志

# ─── 健康检查 ──────────────────────────────────────────
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8001/health  # 后端直连
curl -s -o /dev/null -w '%{http_code}' https://liankebao.top/health  # 通过 Nginx
curl -s http://127.0.0.1:8001/health    # 查看完整响应

# ─── 数据库检查 ──────────────────────────────────────────
docker exec chainke-postgres pg_isready -U chainke -d chainke  # PostgreSQL 状态
docker exec chainke-postgres psql -U chainke -c "SELECT count(*) FROM pg_stat_activity;"  # 活跃连接数

# ─── Redis 检查 ──────────────────────────────────────────
docker exec chainke-redis redis-cli ping       # Redis 连通性
docker exec chainke-redis redis-cli info stats # Redis 统计信息

# ─── Nginx 检查 ──────────────────────────────────────────
docker exec chainke-nginx nginx -t            # Nginx 配置测试
docker exec chainke-nginx nginx -s reload     # Nginx 平滑重载
docker exec chainke-nginx cat /etc/nginx/upstream-active.conf  # 查看当前 upstream

# ─── 系统资源 ──────────────────────────────────────────
df -h                   # 磁盘空间
free -h                 # 内存使用
top -b -n 1 | head -20  # CPU 负载
```

---

## 2. 502/504 错误诊断流程

### 2.1 502 Bad Gateway

**含义**: Nginx 无法连接到上游后端 (FastAPI)。

```
  开始: 用户报 502 错误
       │
       ▼
  ① 确认 Nginx 运行状态
       │
       ├─ docker ps | grep chainke-nginx
       │   ├─ 未运行 → docker compose up -d nginx
       │   └─ 已运行 → 继续
       │
       ▼
  ② 检查 upstream 配置
       │
       ├─ docker exec chainke-nginx cat /etc/nginx/upstream-active.conf
       │   ├─ 指向 backend-blue:8001 还是 backend-green:8001 ?
       │   └─ 确认对应的后端容器是否运行
       │
       ▼
  ③ 检查后端容器状态
       │
       ├─ docker ps | grep chainke-backend
       │   ├─ 无输出 → 后端未运行
       │   │     ├─ docker compose logs backend --tail=30  # 查看退出原因
       │   │     └─ docker compose up -d backend           # 重启
       │   └─ 已运行 → 继续
       │
       ▼
  ④ 测试后端直连
       │
       ├─ curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8001/health
       │   ├─ 200 → Nginx 到后端网络问题 (检查 docker network)
       │   │     └─ docker network inspect chainke-net
       │   ├─ 000 → 后端进程僵死 (走第 5 节)
       │   └─ 其他 → 后端应用错误
       │
       ▼
  ⑤ 查看后端日志定位具体错误
       │
       ├─ docker logs chainke-backend --tail=100
       │   ├─ "Connection refused" → 数据库连接问题 (检查 postgres)
       │   ├─ "Address already in use" → 端口冲突
       │   ├─ "ModuleNotFoundError" → 依赖缺失 → pip install -r requirements.txt
       │   └─ "Worker failed to boot" → 应用启动错误
       │
       ▼
  ⑥ 检查数据库连接
       │
       ├─ docker ps | grep chainke-postgres
       │   ├─ 未运行 → docker compose up -d postgres
       │   └─ 已运行 → docker exec chainke-postgres pg_isready -U chainke -d chainke
       │
       ▼
  ⑦ 最终手段
       ├─ docker compose restart backend    # 重启后端
       └─ docker compose restart nginx      # 重启 Nginx
```

### 2.2 504 Gateway Timeout

**含义**: Nginx 等后端响应超时 (默认 120s)。

```
  可能原因及排查步骤:
       │
       ├─ 慢查询: 检查数据库连接数和查询性能
       │     ├─ docker exec chainke-postgres psql -U chainke -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC;"
       │     └─ 长时间运行的查询 → 考虑添加索引或优化查询
       │
       ├─ 上游服务阻塞: 外部 API (支付网关等) 响应慢
       │     └─ docker logs chainke-backend --tail=100 | grep -i "timeout"
       │
       ├─ 工作进程耗尽: uvicorn workers 不足
       │     └─ docker logs chainke-backend --tail=50 | grep -i "max_workers\|queue\|timeout"
       │
       └─ 解决方案:
             ├─ docker compose restart backend          # 临时恢复
             ├─ 调整 uvicorn --workers 参数 (生产推荐 4-8) 
             └─ 考虑添加超时保护和熔断机制
```

---

## 3. 数据库损坏恢复步骤

### 3.1 前置条件

```bash
# 确认数据库容器名称和 volume
DB_CONTAINER="chainke-postgres"
DB_VOLUME="chainke-full_pg-data"  # docker volume ls 确认
DB_NAME="chainke"
DB_USER="chainke"
```

### 3.2 恢复流程

#### 场景 A: 数据表损坏但容器可运行

```bash
# 1. 停止前端和后端服务（防止写入）
docker compose stop backend nginx

# 2. 备份当前数据库（即使已损坏，尽可能保留）
docker exec -t $DB_CONTAINER pg_dump -U $DB_USER -d $DB_NAME > /tmp/db_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. 连接数据库并执行修复
docker exec -it $DB_CONTAINER psql -U $DB_USER -d $DB_NAME

# 在 psql 中执行:
#   REINDEX DATABASE chainke;          -- 重建索引
#   VACUUM FULL ANALYZE;              -- 清理并更新统计信息
#   \q

# 4. 重启服务
docker compose up -d backend nginx

# 5. 验证恢复
curl -s http://127.0.0.1:8001/health
```

#### 场景 B: 数据库无法启动 / volume 损坏

```bash
# 1. 尝试从备份恢复 volume
#    前提: 有定期的 pg_dump 备份文件

# 2. 重新创建数据库容器（自动拉取新 volume）
docker compose rm -fsv postgres
docker volume rm $DB_VOLUME
docker compose up -d postgres

# 3. 等待 PostgreSQL 初始化完成
sleep 15

# 4. 从最新备份恢复
cat /path/to/latest_backup.sql | docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME

# 5. 验证数据完整性
docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "\dt"
docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "SELECT count(*) FROM users;"

# 6. 重启后端
docker compose up -d backend nginx
```

#### 场景 C: 无备份 (紧急恢复)

```bash
# 最后一搏 — 尝试从 PostgreSQL 数据目录直接恢复
# 数据存放在: /var/lib/docker/volumes/chainke-full_pg-data/_data

# 1. 停止数据库容器
docker compose stop postgres

# 2. 尝试使用 pg_resetwal 重置 WAL
#    注意: 这可能会导致数据丢失，但可以使数据库重新上线
docker run --rm -v chainke-full_pg-data:/var/lib/postgresql/data postgres:16-alpine \
  bash -c "pg_resetwal -f /var/lib/postgresql/data/pgdata"

# 3. 启动数据库并立即备份
docker compose up -d postgres
docker exec -t $DB_CONTAINER pg_dump -U $DB_USER -d $DB_NAME > /tmp/emergency_backup.sql

# 4. 重建干净数据库
docker compose rm -fsv postgres
docker volume rm $DB_VOLUME
docker compose up -d postgres
sleep 15
cat /tmp/emergency_backup.sql | docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME
```

### 3.3 定期备份建议

```bash
# 每日备份脚本 (建议添加到 crontab)
# 0 3 * * * /var/www/chainke-full/deploy/scripts/backup_db.sh

# backup_db.sh 内容:
#!/bin/bash
BACKUP_DIR="/data/backups/postgres"
DATE=$(date +%Y%m%d)
mkdir -p $BACKUP_DIR
docker exec chainke-postgres pg_dump -U chainke -d chainke -Fc \
  -f /tmp/chainke_$DATE.dump
docker cp chainke-postgres:/tmp/chainke_$DATE.dump $BACKUP_DIR/
docker exec chainke-postgres rm -f /tmp/chainke_$DATE.dump
# 保留最近 30 天
find $BACKUP_DIR -name "chainke_*.dump" -mtime +30 -delete
```

---

## 4. 蓝绿部署回滚步骤

### 4.1 使用回滚脚本 (推荐)

```bash
# 全自动回滚 — 切换到上一个已知良好版本
bash deploy/rollback.sh
```

如果 `rollback.sh` 不存在，手动执行以下步骤。

### 4.2 手动回滚 (通用)

```bash
# 1. 确定当前环境和目标回滚环境
cat deploy/.blue-green-state              # 查看当前环境: blue 或 green
# 如果当前是 blue, 回滚到 green; 反之亦然

# 2. 检查目标环境的容器是否仍在运行
docker ps | grep chainke-backend-<target>  # 例如 chainke-backend-green
# 如果目标环境容器已停止:
docker compose -f docker-compose.yml -f deploy/docker-compose.<target>.yml up -d backend-<target>

# 3. 切换 Nginx upstream
cp deploy/nginx/upstream-<target>.conf deploy/nginx/upstream-active.conf
docker exec chainke-nginx nginx -s reload

# 4. 验证健康检查
curl -s http://127.0.0.1:8001/health

# 5. 更新状态文件
echo "<target>" > deploy/.blue-green-state

# 6. 停止新版本环境（可选）
docker compose -f docker-compose.yml -f deploy/docker-compose.<old>.yml rm -fsv backend-<old>
```

### 4.3 紧急回滚 (容器 Tag 方式)

如果部署时给镜像打了 tag:

```bash
# 直接运行上一个 tag 的版本
docker compose -f docker-compose.yml -f deploy/docker-compose.blue.yml \
  run --rm backend-blue /bin/bash -c "echo rollback"
# 或者修改 docker-compose.blue.yml 中的 image 标签指向上一个版本
```

---

## 5. 服务进程僵死恢复

### 5.1 诊断僵死

```bash
# 查看容器进程状态
docker stats chainke-backend --no-stream
# CPU = 0% 且长时间无响应 → 进程僵死

# 查看进程信号响应
docker exec chainke-backend ps aux
# D 状态 → 不可中断睡眠 (通常是 I/O 阻塞)
# Z 状态 → 僵尸进程
```

### 5.2 恢复步骤

```bash
# 级别 1: 优雅重启 (优先)
docker compose restart backend
# 或
docker restart chainke-backend

# 级别 2: 强制停止 + 启动
docker compose stop backend --timeout 10    # 10秒后强制 kill
docker compose up -d backend

# 级别 3: 重建容器 (清除可能的内存泄漏)
docker compose rm -fsv backend
docker compose up -d backend

# 级别 4: 如果同一容器反复僵死
# 检查系统资源:
#   - 内存不足? → free -h; dmesg | tail -20 (看 OOM Killer)
#   - 磁盘 I/O 阻塞? → iostat -x 1 5
#   - 文件描述符耗尽? → lsof -p $(docker inspect -f '{{.State.Pid}}' chainke-backend) | wc -l
# 考虑增加 docker compose 中的资源限制:
#   deploy:
#     resources:
#       limits:
#         memory: 1G
#       reservations:
#         memory: 512M
```

### 5.3 防止进程僵死的措施

```bash
# 1. 在 Docker Compose 中启用自动重启 (已配置 restart: unless-stopped)
# 2. 配置健康检查 (已配置 healthcheck 每 30s)
# 3. 在应用层添加:
#    - asyncio 超时: asyncio.wait_for()
#    - 数据库连接池超时: pool_timeout=30
#    - HTTP 客户端超时: httpx.Timeout(30.0)
# 4. 外部监控: 
#    docker events --filter 'event=health_status'  # 监控健康检查事件
```

---

## 6. 断网/服务器重启后自愈流程

### 6.1 Docker 自愈机制

当前部署已配置的自愈特性:

| 特性 | 配置 | 说明 |
|------|------|------|
| `restart: unless-stopped` | 所有服务 | 容器崩溃后自动重启 |
| `healthcheck` | backend, postgres, redis | 定期检查服务健康 |
| `depends_on` + `condition` | backend 依赖 DB/Redis | 按依赖顺序启动 |

### 6.2 服务器重启后完全恢复步骤

```bash
# 1. 确认 Docker 守护进程已启动
systemctl status docker
# 如果未启动:
systemctl start docker
systemctl enable docker  # 确保开机自启

# 2. 确认所有容器自动恢复
cd /var/www/chainke-full
docker compose ps
# 预期输出: 所有服务状态应为 "Up"

# 3. 等待各组件就绪 (Docker 自动按 depends_on 顺序启动)
#    postgres → redis → backend → frontend-builder → nginx
#    内置健康检查会自动等待

# 4. 验证完整链路的健康
echo "=== 后端直连 ==="
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8001/health
echo ""

echo "=== 通过 Nginx ==="
curl -s -o /dev/null -w '%{http_code}' https://liankebao.top/health
echo ""

echo "=== 数据库 ==="
docker exec chainke-postgres pg_isready -U chainke -d chainke

echo "=== Redis ==="
docker exec chainke-redis redis-cli ping

echo "=== Nginx ==="
docker exec chainke-nginx nginx -t 2>&1

# 5. 如果有容器未自动恢复
docker compose up -d   # 启动所有定义的服务

# 6. 检查蓝绿状态文件
cat deploy/.blue-green-state
# 如果状态文件丢失 → 默认 blue 环境
# 手动重建: echo "blue" > deploy/.blue-green-state
```

### 6.3 断网后恢复 (外部依赖不可用)

```bash
# 场景: 数据库/Redis 连接超时
# 后端已配置 database connection pool (SQLAlchemy)
# 会自动重连, 不需要手动干预

# 但需要注意:
# - 支付回调可能在断网期间丢失
# - 建议实现支付回调补偿机制:
#   1. 记录回调到本地队列 (Redis list)
#   2. 恢复网络后自动重放

# 手动检查是否有积压的支付回调:
docker logs chainke-backend --tail=200 | grep -i "callback\|payment"
```

### 6.4 服务器启动脚本 (建议)

创建 `/etc/systemd/system/chainke-docker.service`:

```ini
[Unit]
Description=链客宝 Docker Compose 自启动
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/var/www/chainke-full
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
StandardOutput=journal

[Install]
WantedBy=multi-user.target
```

启用:
```bash
systemctl daemon-reload
systemctl enable chainke-docker.service
```

---

## 7. 常见故障处理矩阵

| 症状 | 可能原因 | 诊断命令 | 解决方案 |
|------|---------|---------|---------|
| 502 Bad Gateway | 后端未运行 | `docker ps \| grep backend` | `docker compose up -d backend` |
| 504 Gateway Timeout | 后端响应慢 | `docker logs backend --tail=50` | 检查慢查询, 增加 workers |
| Connection Refused | 端口未监听 | `curl -v http://127.0.0.1:8001` | `docker compose restart backend` |
| 无法解析域名 | DNS 问题 | `nslookup liankebao.top` | 检查 DNS 记录, 等待传播 |
| 证书过期 | SSL 证书 | `openssl s_client -connect liankebao.top:443` | 续期 Let's Encrypt 证书 |
| 磁盘空间满 | 日志/数据过多 | `df -h` | `docker system prune`, 清理日志 |
| OOM Kill | 内存不足 | `dmesg \| grep -i oom` | 增加内存限制, 优化内存使用 |
| 数据库连接满 | 连接泄漏 | `docker exec postgres psql -c "SELECT count(*) FROM pg_stat_activity"` | 减少连接池, 重启后端 |
| Nginx 配置错误 | 语法错误 | `docker exec nginx nginx -t` | 修正 Nginx 配置 |
| 前端白屏 | SPA 路由问题 | 浏览器 F12 Console | 检查 index.html 资源加载 |
| 支付回调失败 | 验签失败 | `docker logs backend \| grep callback` | 检查回调 IP 白名单和密钥 |

---

## 附录: 紧急联系人

| 角色 | 职责 | 联系方式 |
|------|------|---------|
| 系统管理员 | 服务器/基础设施 | 见团队通讯录 |
| 后端开发 | API/数据库 | 见团队通讯录 |
| 前端开发 | SPA/UI | 见团队通讯录 |
| 阿里云支持 | 云资源 | 95187 (阿里云客服) |

---

> 文档维护: 请根据实际部署环境调整 IP 地址和路径。更新后通知运维团队。
