# 链客宝 ARQ 异步任务队列系统

## 概述

链客宝使用 [**ARQ**](https://arq-docs.helpmanual.io/) 作为异步任务队列系统。  
ARQ 是一个基于 Redis 的轻量级 Python 异步任务队列，支持：

- 异步任务入队与消费
- 任务重试与超时控制
- Cron 定时任务
- Job 进度追踪
- 零外部依赖（仅需 Redis + Python 3.9+）

---

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                   FastAPI App (main.py)                  │
│                                                         │
│   Route Handler                                         │
│     │                                                   │
│     ├─ await enqueue_task("enterprise_enrich", ...)     │
│     └─ 立即返回 HTTP 200 + job_id                        │
│                                                         │
└──────────────────────┬──────────────────────────────────┘
                       │  enqueue_job()
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    Redis (消息队列)                       │
│                                                         │
│   chainke-tasks: [job1, job2, job3, ...]                │
│                                                         │
└──────────────────────┬──────────────────────────────────┘
                       │  dequeue / poll
                       ▼
┌─────────────────────────────────────────────────────────┐
│               ARQ Worker (run_worker.py)                 │
│                                                         │
│   ┌─────────────────────────────────────────┐           │
│   │  Worker (并发处理队列任务)                │           │
│   │  ├─ enterprise_enrich_task              │           │
│   │  ├─ matching_async_task                 │           │
│   │  ├─ email_notification_task             │           │
│   │  ├─ data_cleanup_task                   │           │
│   │  └─ report_generation_task              │           │
│   └─────────────────────────────────────────┘           │
│   ┌─────────────────────────────────────────┐           │
│   │  Scheduler (cron 定时任务)               │           │
│   │  ├─ daily_cleanup      (03:00 daily)    │           │
│   │  ├─ weekly_report      (Mon 08:00)      │           │
│   │  ├─ monthly_report     (1st 09:00)      │           │
│   │  └─ hourly_cleanup     (:30 hourly)     │           │
│   └─────────────────────────────────────────┘           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 目录结构

```
backend/
├── app/
│   └── tasks/
│       ├── __init__.py     # 包入口，导出关键符号
│       ├── worker.py       # Redis 连接池 + WorkerSettings + enqueue_task
│       ├── tasks.py        # 5 个业务任务函数 + TASK_FUNCTIONS 注册表
│       └── scheduler.py    # Cron 定时任务定义 + 独立调度器
├── run_worker.py           # Worker CLI 启动入口
└── docs/
    └── async-tasks/
        └── ARQ_SETUP.md    # 本文档
```

---

## 环境要求

| 组件     | 版本要求       | 说明                     |
| -------- | -------------- | ------------------------ |
| Python   | ≥ 3.9          | 异步支持                 |
| Redis    | ≥ 6.0          | 消息队列存储             |
| arq      | ≥ 0.26         | pip install arq          |

### 安装

```bash
cd D:/chainke-full/backend
pip install arq
```

或更新 requirements.txt 后：

```bash
pip install -r requirements.txt
```

---

## 快速上手

### 1. 确保 Redis 运行

```bash
# Windows (使用 WSL 或 Docker)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 验证
redis-cli ping
# → PONG
```

### 2. 启动 Worker

```bash
cd D:/chainke-full/backend

# 仅处理队列任务
python run_worker.py

# Worker + 定时调度器
python run_worker.py --scheduler

# 指定并发数
ARQ_CONCURRENCY=20 python run_worker.py

# 处理完现有任务后退出
python run_worker.py --burst
```

### 3. 在路由中入队任务

```python
from app.tasks import enqueue_task

@router.post("/api/enterprise/{id}/enrich")
async def enrich_enterprise(id: int):
    job_id = await enqueue_task("enterprise_enrich", enterprise_id=id)
    return {"status": "accepted", "job_id": job_id}
```

---

## 任务详解

### 任务注册表 (`tasks.py`)

所有业务任务在 `TASK_FUNCTIONS` 字典中注册：

| 任务名              | 函数                       | 说明                     |
| ------------------- | -------------------------- | ------------------------ |
| `enterprise_enrich` | `enterprise_enrich_task`   | 企业信息丰富（天眼查等） |
| `matching_async`    | `matching_async_task`      | 异步匹配计算             |
| `email_notification`| `email_notification_task`  | 多渠道通知推送           |
| `data_cleanup`      | `data_cleanup_task`        | 过期数据清理             |
| `report_generation` | `report_generation_task`   | 报告生成（PDF/Excel）    |

### 入队方式

```python
# 方式 1: 使用便捷函数 (推荐)
from app.tasks import enqueue_task

job_id = await enqueue_task(
    "enterprise_enrich",
    enterprise_id=42,
    source="tianyancha",
    depth=2,
)

# 方式 2: 直接操作 Redis pool
from app.tasks import get_redis_pool

redis = await get_redis_pool()
job = await redis.enqueue_job("enterprise_enrich", enterprise_id=42)
job_id = job.job_id
```

### 任务参数

| 任务               | 参数                                           | 返回                                |
| ------------------ | ---------------------------------------------- | ----------------------------------- |
| enterprise_enrich  | `enterprise_id`, `source`, `depth`             | `{status, enterprise_id, fields}`   |
| matching_async     | `user_id`, `top_n`, `strategy`, `include_self` | `{status, user_id, match_count}`    |
| email_notification | `user_id`, `subject`, `template`, `channel`    | `{status, delivery_id, channels}`   |
| data_cleanup       | `cleanup_type`, `dry_run`, `older_than`        | `{status, records_affected}`        |
| report_generation  | `report_type`, `user_id`, `format`             | `{status, report_id, file_url}`     |

---

## 定时任务 (Cron)

在 `scheduler.py` 中定义，使用 ARQ 内置 cron 支持：

| 任务                  | Cron 表达式      | 说明           |
| --------------------- | ---------------- | -------------- |
| `daily_cleanup`       | `0 3 * * *`      | 每日 03:00     |
| `weekly_report`       | `0 8 * * 1`      | 每周一 08:00   |
| `monthly_report`      | `0 9 1 * *`      | 每月 1 日 09:00|
| `hourly_cleanup_temp` | `30 * * * *`     | 每小时 30 分   |

启动调度器：

```bash
# 方式 1: run_worker.py --scheduler
python run_worker.py --scheduler

# 方式 2: 独立调度器进程
python -m app.tasks.scheduler
```

---

## 配置参考

| 环境变量          | 默认值           | 说明                         |
| ----------------- | ---------------- | ---------------------------- |
| `REDIS_HOST`      | `localhost`      | Redis 地址                   |
| `REDIS_PORT`      | `6379`           | Redis 端口                   |
| `REDIS_DB`        | `0`              | Redis 数据库编号             |
| `REDIS_PASSWORD`  | _(空)_            | Redis 密码                   |
| `REDIS_POOL_SIZE` | `10`             | 连接池大小                   |
| `ARQ_QUEUE`       | `chainke-tasks`  | 队列名称                     |
| `ARQ_CONCURRENCY` | `10`             | 并发 Worker 数               |
| `ARQ_POLL_DELAY`  | `0.5`            | 轮询间隔（秒）               |
| `ARQ_JOB_TIMEOUT` | `300`            | 任务超时（秒）               |
| `ARQ_BURST`       | `0`              | 处理完现有任务后退出         |
| `ARQ_MAX_JOBS`    | `500`            | 每个 Worker 最大任务处理数   |

---

## 部署

### 生产环境启动

```bash
# 终端 1: Worker (带调度器)
cd /app/backend
REDIS_HOST=10.0.0.5 REDIS_PASSWORD=secret \
  ARQ_CONCURRENCY=20 \
  python run_worker.py --scheduler

# 终端 2: FastAPI (保持不变)
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Supervisor 配置

```ini
[program:chainke-worker]
command=/path/to/venv/bin/python run_worker.py --scheduler
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/chainke/worker.log
stderr_logfile=/var/log/chainke/worker.err
environment=REDIS_HOST="10.0.0.5",REDIS_PASSWORD="secret"
```

### Docker Compose

```yaml
version: "3.8"
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: .
    ports:
      - "8001:8001"
    depends_on: [redis]

  worker:
    build: .
    command: python run_worker.py --scheduler
    environment:
      - REDIS_HOST=redis
    depends_on: [redis]
```

---

## 监控与调试

### Job 状态查询

```python
from app.tasks import get_redis_pool

redis = await get_redis_pool()
job = await redis.get_job(job_id)
print(job.status)      # "queued" / "deferred" / "in_progress" / "complete" / "failed"
print(job.result)      # 任务返回结果
print(job.enqueue_time) # 入队时间
```

### Redis 中查看队列

```bash
# 查看队列长度
redis-cli LLEN chainke-tasks

# 查看队列内容
redis-cli LRANGE chainke-tasks 0 -1

# 查看失败任务
redis-cli KEYS "arq:job:*"
```

### 日志

Worker 日志使用链客宝统一的 `chainke.tasks` logger，JSON 结构化输出：

```json
{"timestamp": "2026-06-26T14:30:00+00:00", "level": "INFO",
 "logger": "chainke.tasks", "message": "任务入队成功: enterprise_enrich job_id=abc123"}
```

---

## 从 Celery 迁移

项目原有 `celery[redis]>=5.4.0` 依赖（requirements.txt 中注释部分）。  
如需从 Celery 迁移到 ARQ：

1. 移除 celery 相关代码
2. 替换 `from celery import Celery` 为 `from arq import create_pool`
3. 替换 `@app.task` 装饰器为 `TASK_FUNCTIONS` 注册表
4. 替换 `task.delay(...)` 为 `await enqueue_task(...)`
5. 替换 Celery Beat 为 `scheduler.py` 中的 `cron` 定义

ARQ 优势：无外部依赖（除 Redis）、原生 asyncio 支持、
更轻量的序列化（默认 msgpack）、更低的内存占用。

---

## 常见问题

**Q: Worker 无法连接到 Redis？**  
A: 检查 REDIS_HOST / REDIS_PORT / REDIS_PASSWORD 环境变量，  
   确保 Redis 服务正在运行：`redis-cli ping`

**Q: 任务执行超时？**  
A: 增大 ARQ_JOB_TIMEOUT（默认 300 秒），或将长任务拆分为多个子任务。

**Q: Worker 占用过高 CPU？**  
A: 调低 ARQ_CONCURRENCY（默认 10），或增加 ARQ_POLL_DELAY（默认 0.5s）。

**Q: 如何优雅关闭 Worker？**  
A: 发送 SIGINT (Ctrl+C)，Worker 会在处理完当前任务后退出。
