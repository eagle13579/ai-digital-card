# AI数字名片 — 1000人内测生产升级方案

> 生成时间: 2026-07-20
> 基于: 当前系统审计 + 架构评估

---

## 已完成的P0修复

| 项目 | 状态 | 详情 |
|:-----|:----:|:------|
| 7个空页面 + 匹配页 | ✅ | 8页面32文件已创建，app.json已更新(37→45页) |
| 匹配Tab | ✅ | 第4个Tab已插入TabBar |
| 连接数数据不一致 | ✅ | db_mcp_server.py: status='approved'→'accepted'修复 |

## 待完成的P0-P2

### P0 (内测前必须完成)

#### P0-D: 数据库生产化 (SQLite→PostgreSQL)

**当前**: SQLite (单文件,并发写入锁)
**目标**: PostgreSQL 16
**方案**:
1. docker-compose 增加 postgres:16-alpine 服务
2. 运行迁移脚本: `scripts/migrate_sqlite_to_postgres.py`
3. 切换 DATABASE_URL 环境变量
4. 验证所有API功能正常
**风险**: 低(当前数据量<15MB,迁移窗口<3分钟)
**回滚**: 恢复环境变量+SQLite备份

#### P0-E: 批量邀请机制

需新增:
- `invitation_codes` 表 (code VARCHAR(8), batch_id, max_uses, expires_at)
- API: POST /api/invite/generate, POST /api/invite/verify
- 内测码格式: 8位字母数字(排除O/I/L/0/1)
- 前端: 邀请码输入页面

### P1 (工业化生产)

| 项目 | 方案 | 优先级 | 工作量 |
|:-----|:-----|:------:|:------|
| PostgreSQL | docker-compose + 迁移脚本 | P1 | 1天 |
| 异步队列 | Celery 5.4 + Redis 7, 8 workers | P1 | 2天 |
| 多Worker | Gunicorn + gevent, workers=4-8 | P1 | 0.5天 |
| CDN | 阿里云CDN(静态) + OSS(上传) | P1 | 1天 |
| 错误监控 | Sentry免费版 (5000 events/月) | P1 | 0.5天 |
| Nginx配置归git | 从生产服务器拉取并提交 | P1 | 0.5天 |
| 备份策略 | pg_dump每天3:00 + 保留30天 | P1 | 0.5天 |

### P2 (产品体验)

| 项目 | 方案 | 优先级 | 状态 |
|:-----|:-----|:------:|:----|
| Admin后台 | Flask-admin或自定义页面 | P2 | 未开始 |
| 用户反馈 | 内置反馈表单 → API → 飞书通知 | P2 | 未开始 |
| 新手指引 | 首次登录引导页 + 空状态提示 | P2 | 未开始(空状态已创建) |
| 内测标识 | 页面顶部"内测版"标签 | P2 | 未开始 |
| 画册+分析+消息+团队 | 空壳已创建,需填充功能 | P2 | 空壳已创建 |

## 架构升级总图

```
用户 → CDN(阿里云) → Nginx → Gunicorn(4-8 workers)
                                      ├→ PostgreSQL(主库)
                                      ├→ Redis(缓存+队列)
                                      └→ Celery(异步任务:匹配/通知/图片处理)
                                          └→ Sentry(错误监控)
```

## 关键指标 (1000人规模预估)

| 指标 | 当前(104人) | 预估(1000人) | 考量 |
|:-----|:----------:|:-----------:|:-----|
| 用户表 | 104行 | 1000行 | ✅ PB级别 |
| 匹配记录 | 7337条 | ~50万条 | ⚠️ 需要索引优化 |
| 连接 | 120条 | ~3000条 | ✅ 无压力 |
| 标签 | 806个 | ~5000个 | ✅ 可扩展 |
| QPS峰值 | <10 | ~50 | ⚠️ 需gunicorn多worker |
| 存储 | ~15MB | ~150MB | ✅ PostgreSQL毫无压力 |

---

## 建议执行顺序

**波1 (立即实施)**: P0-D PostgreSQL迁移 + P0-E 邀请码
**波2 (1周内)**: P1 gunicorn + Celery + Nginx归git + 备份
**波3 (2周内)**: P1 CDN + Sentry
**波4 (并行)**: P2 Admin后台 + 反馈 + 新手引导 + 内测标识
