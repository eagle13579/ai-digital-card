# AI数智名片 — 蓝绿部署操作手册

> **文档版本**: v1.0  
> **最后更新**: 2026-07-01  
> **适用项目**: AI数字名片 (AI Digital Card)  
> **相关文件**: [bluegreen-deploy.yml](../../.github/workflows/bluegreen-deploy.yml) | [nginx-bluegreen.conf](../../deploy/bluegreen/nginx-bluegreen.conf) | [switch-blue.sh](../../deploy/bluegreen/switch-blue.sh) | [switch-green.sh](../../deploy/bluegreen/switch-green.sh) | [health_check.sh](../../deploy/bluegreen/health_check.sh)

---

## 目录

1. [概述](#1-概述)
2. [架构说明](#2-架构说明)
3. [部署流程](#3-部署流程)
4. [通过 CI 自动部署 (推荐)](#4-通过-ci-自动部署-推荐)
5. [通过脚本手动部署](#5-通过脚本手动部署)
6. [回滚操作](#6-回滚操作)
7. [故障排除](#7-故障排除)
8. [附录: 命令速查](#8-附录-命令速查)

---

## 1. 概述

蓝绿部署是一种**零停机部署策略**，通过维护两套完全独立的生产环境（蓝色和绿色），实现即时切换流量，将部署风险降到最低。

| 特性 | 说明 |
|------|------|
| **零停机** | 流量切换瞬间完成，用户无感知 |
| **即时回滚** | 发现问题秒级切回旧版本 |
| **全量验证** | 新版本部署在完整生产环境中验证，非抽样 |
| **独立隔离** | 两套环境完全隔离，互不影响 |

### 与金丝雀发布的对比

| 对比项 | 蓝绿部署 | 金丝雀发布 |
|--------|----------|------------|
| 流量切换 | 瞬间全量切换 | 逐步放量 (10% → 50% → 100%) |
| 验证范围 | 全量验证 | 抽样验证 |
| 回滚速度 | < 10s | ~2-5 min |
| 资源消耗 | 2x 资源 | 少量额外资源 |
| 适用场景 | 重大版本发布 | 常规迭代更新 |

---

## 2. 架构说明

### 2.1 端口规划

| 组件 | 端口 | 说明 |
|------|------|------|
| Nginx (接入层) | **8200** | 统一入口，根据配置路由到蓝或绿 |
| 蓝色后端 (Blue) | **8201** | 默认生产环境，当前稳定版本 |
| 绿色后端 (Green) | **8202** | 备用环境，新版本部署于此 |
| 前端静态文件 | - | 由 Nginx 直接 serve，不参与蓝绿切换 |

### 2.2 Nginx 路由逻辑

```
用户请求 → Nginx :8200
              │
              ├─ /api/* ─────────────────┐
              │                          ▼
              │              ┌──────────────────────┐
              │              │  $active_backend      │
              │              │  (backend_blue 或     │
              │              │   backend_green)      │
              │              └──────────────────────┘
              │                          │
              │              ┌───────────┴───────────┐
              │              ▼                       ▼
              │     backend_blue           backend_green
              │     (127.0.0.1:8201)      (127.0.0.1:8202)
              │
              ├─ / ─────────────────────────────────────
              │    → 前端静态文件 (/var/www/.../dist/)
              │
              ├─ /health          → $active_backend
              ├─ /health/blue     → backend_blue (强制)
              └─ /health/green    → backend_green (强制)
```

### 2.3 Nginx 配置核心机制

```nginx
# 通过 map 指令实现变量级切换
# 修改 default 的值即可切换整个流量方向
map "" $active_backend {
    default backend_blue;   # ← 切换点: backend_blue → backend_green
}
```

切换时只需修改 `default` 的值，然后执行 `nginx -s reload`（毫秒级完成，不中断连接）。

---

## 3. 部署流程

### 3.1 标准蓝绿部署流程

```
┌─────────────┐
│  当前状态    │  蓝色: v1.0 (活跃, :8201)
│             │  绿色: v0.9 (旧版, :8202 或空)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  ① 部署到   │  拉取新版本 v2.0 镜像
│  非活跃组   │  启动容器在非活跃端口 (绿色 :8202)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  ② 健康检查  │  持续检测非活跃组 /health 端点
│  (60s 超时)  │  必须全部通过
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  ③ 切换流量  │  sed 修改 nginx 配置
│             │  nginx -s reload (毫秒级)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  ④ 验证     │  检查新组 API 响应
│             │  检查 X-Active-Env 响应头
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  ⑤ 清理旧组  │  可选: 停止旧版本容器
│  (可选)     │  保留作为回滚备用
└─────────────┘
```

### 3.2 切换后的状态

```
部署成功后:  蓝色: v1.0 (旧版, 待清理)
            绿色: v2.0 (活跃, :8202) ← 流量在此

回滚后:     蓝色: v1.0 (活跃, :8201) ← 流量切回
            绿色: v2.0 (待清理)
```

---

## 4. 通过 CI 自动部署 (推荐)

### 4.1 触发方式

**GitHub Actions → Blue-Green Deploy → Run workflow**

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `environment` | ✅ | production | `production` 或 `staging` |
| `branch` | ❌ | main | 要部署的 Git 分支 |
| `skip_health_check` | ❌ | false | 紧急部署时跳过健康检查 |
| `cleanup_old` | ❌ | true | 部署成功后清理旧组容器 |

### 4.2 工作流步骤

```
Trigger (workflow_dispatch)
  │
  ├─ [determine-groups]   确定蓝绿状态
  │    ├─ 读取 Nginx 配置判断活跃组
  │    └─ 输出: active_group, inactive_group, ports
  │
  ├─ [build-and-push]     构建 & 推送镜像
  │    ├─ Docker build (backend/)
  │    ├─ Docker push → ghcr.io
  │    └─ 标签: bluegreen-<run_id>, sha-<short>, latest
  │
  ├─ [deploy-inactive]    部署到非活跃组
  │    ├─ docker pull 新镜像
  │    ├─ docker run → 非活跃端口
  │    └─ 保存部署状态 (rollback/bluegreen_state.json)
  │
  ├─ [health-check]       健康检查 (60s)
  │    └─ curl 检查非活跃组 /health 端点
  │
  ├─ [switch-traffic]     切换流量
  │    ├─ 调用 switch-green.sh 或 switch-blue.sh
  │    └─ nginx -s reload
  │
  ├─ [verify-switch]      验证切换
  │    ├─ 检查 Nginx /health
  │    ├─ 检查 API HTTP 状态码
  │    └─ 检查 X-Active-Env 响应头
  │
  ├─ [cleanup]            清理旧组 (可选)
  │    ├─ docker rm -f 旧版本容器
  │    └─ docker image prune
  │
  └─ [auto-rollback]      失败回滚 (自动)
       ├─ 回切 Nginx 到原活跃组
       └─ 清理部署失败的容器
```

### 4.3 成功流程示意

```
✅ Determine Groups               (3s)  → 非活跃组: green
✅ Build & Push Docker Images     (120s)
✅ Deploy to Inactive Group       (10s)  → 绿色 :8202
✅ Health Check (60s)             (15s)  → 通过
✅ Switch Traffic to New Group    (2s)   → 绿色上线
✅ Verify Deployment              (5s)   → 验证通过
✅ Cleanup Old Group                       → 蓝色容器已清理
────────────────────────────────────────────────
🎉 蓝绿部署完成！当前活跃: 绿色 (v2.0)
```

### 4.4 失败自动回滚示意

```
✅ Determine Groups               (3s)
✅ Build & Push                   (120s)
✅ Deploy to Inactive             (10s)
❌ Health Check failed!           (60s)
✅ Auto-Rollback triggered        (3s)   → 回切到蓝色
✅ Cleanup failed deployment      (2s)
────────────────────────────────────────────────
⚠️ 部署失败，已自动回滚
    请查看 GitHub Actions 日志
```

---

## 5. 通过脚本手动部署

### 5.1 SSH 登录服务器

```bash
ssh user@your-server
cd /opt/ai-digital-card
```

### 5.2 部署到非活跃组

```bash
# 1. 确认当前状态
bash deploy/bluegreen/health_check.sh --all

# 2. 拉取新版本镜像
docker pull ghcr.io/org/backend:v2.0.0

# 3. 部署到绿色环境（假设蓝色是活跃组）
docker rm -f ai-digital-card-green 2>/dev/null || true
docker run -d \
  --name ai-digital-card-green \
  --network bridge \
  --restart unless-stopped \
  -p 8202:8201 \
  -v /opt/ai-digital-card/backend/data:/app/data \
  -v /opt/ai-digital-card/backend/uploads:/app/uploads \
  ghcr.io/org/backend:v2.0.0

# 4. 健康检查
bash deploy/bluegreen/health_check.sh --port 8202 --wait 60

# 5. 切换流量到绿色
bash deploy/bluegreen/switch-green.sh

# 6. 验证
curl -sI http://localhost:8200/api/ | grep -i X-Active-Env

# 7. (可选) 清理旧蓝色容器
docker rm -f ai-digital-card-blue

# 8. 验证最终状态
bash deploy/bluegreen/health_check.sh --all
```

### 5.3 切换脚本说明

| 脚本 | 功能 | 用法 |
|------|------|------|
| `switch-blue.sh` | 切换到蓝色环境 | `bash deploy/bluegreen/switch-blue.sh` |
| `switch-green.sh` | 切换到绿色环境 | `bash deploy/bluegreen/switch-green.sh` |
| `health_check.sh` | 健康检查工具 | `bash deploy/bluegreen/health_check.sh --port 8202 --wait 60` |

各脚本功能：
- **switch-blue.sh**: 检查蓝色健康 → 备份当前 Nginx 配置 → sed 修改 default 值为 `backend_blue` → nginx -t 验证 → nginx -s reload → 验证切换结果
- **switch-green.sh**: 同上，切换到 `backend_green`
- **health_check.sh**: 
  - `--port <PORT>`: 检查指定端口
  - `--all`: 检查蓝绿两套
  - `--wait <SEC>`: 等待指定秒数直至健康

---

## 6. 回滚操作

### 6.1 通过 CI 回滚

重新运行 **Blue-Green Deploy** workflow，系统会自动将新版本部署到当前**非活跃组**（即旧版本所在组），然后切换过去。

> **实际上就是再做一次蓝绿部署** — 新版本部署到非活跃组，切换流量即完成回滚。

### 6.2 通过脚本即时回滚

```bash
# 如果当前活跃是绿色 (新版本有问题)
bash deploy/bluegreen/switch-blue.sh

# 如果当前活跃是蓝色
bash deploy/bluegreen/switch-green.sh

# 完成后清理有问题的容器
docker rm -f ai-digital-card-green  # 或 ai-digital-card-blue
```

### 6.3 快速回滚 (< 10秒)

```bash
# 一行命令完成切换
sed -i 's/default backend_green;/default backend_blue;/' /etc/nginx/conf.d/bluegreen.conf \
  && nginx -t && nginx -s reload
```

### 6.4 使用部署状态回滚

如果记录了部署状态，可以精确回滚到上一个版本：

```bash
# 查看部署状态
cat deploy/rollback/bluegreen_state.json

# 拉取上一个版本的镜像
PREV_IMAGE=$(cat deploy/rollback/bluegreen_state.json | grep -oP '"image": "\K[^"]+')
docker pull "$PREV_IMAGE"

# 重新部署并切换回
docker rm -f ai-digital-card-blue 2>/dev/null || true
docker run -d --name ai-digital-card-blue -p 8201:8201 "$PREV_IMAGE"
bash deploy/bluegreen/switch-blue.sh
```

---

## 7. 故障排除

### 7.1 健康检查失败

**现象**: CI 中 `Health Check` 步骤失败，触发自动回滚

**排查步骤**:

```bash
# 1. 查看容器状态
docker ps -a --filter "name=ai-digital-card"

# 2. 查看新容器日志
docker logs ai-digital-card-green --tail 50

# 3. 手动测试
curl -v http://localhost:8202/health

# 4. 检查端口是否冲突
ss -tlnp | grep 8202

# 5. 检查数据库连接
docker exec ai-digital-card-green python -c "
from database import SessionLocal
db = SessionLocal()
db.execute('SELECT 1')
print('DB OK')
"
```

### 7.2 切换后 API 异常

**现象**: 切换后 API 返回 502/503 或响应缓慢

**处理**:

```bash
# 立即回滚
bash deploy/bluegreen/switch-blue.sh  # 或 switch-green.sh

# 检查 Nginx 日志
tail -100 /var/log/nginx/ai-digital-card-error.log
```

### 7.3 Nginx 配置错误

**现象**: `nginx -t` 失败

**原因**: 通常在更换配置模板时出现

**处理**:

```bash
# 查看错误详情
nginx -t 2>&1

# 回滚到备份
ls -la deploy/rollback/bluegreen.conf.bak.*
cp deploy/rollback/bluegreen.conf.bak.20260701_120000 /etc/nginx/conf.d/bluegreen.conf
nginx -t && nginx -s reload
```

### 7.4 蓝绿状态不一致

**现象**: Nginx 指向一组，但无对应容器运行

**处理**:

```bash
# 1. 检查容器
docker ps --filter "name=ai-digital-card"

# 2. 手动启动缺失的环境
docker run -d --name ai-digital-card-blue -p 8201:8201 ghcr.io/org/backend:stable

# 3. 确保健康后切换
bash deploy/bluegreen/health_check.sh --port 8201 --wait 30
bash deploy/bluegreen/switch-blue.sh
```

---

## 8. 附录: 命令速查

### CI 操作

```bash
# 通过 gh CLI 触发蓝绿部署
gh workflow run "Blue-Green Deploy" \
  -f environment=production \
  -f branch=main

# 紧急部署（跳过健康检查）
gh workflow run "Blue-Green Deploy" \
  -f environment=production \
  -f skip_health_check=true

# 部署且保留旧版本（不清理）
gh workflow run "Blue-Green Deploy" \
  -f environment=production \
  -f cleanup_old=false
```

### 脚本操作

```bash
# 查看蓝绿状态
bash deploy/bluegreen/health_check.sh --all

# 检查指定端口
bash deploy/bluegreen/health_check.sh --port 8202

# 等待端口就绪 (60s)
bash deploy/bluegreen/health_check.sh --port 8202 --wait 60

# 切换到蓝色
bash deploy/bluegreen/switch-blue.sh

# 切换到绿色
bash deploy/bluegreen/switch-green.sh
```

### 容器操作

```bash
# 启动蓝色环境
docker run -d --name ai-digital-card-blue -p 8201:8201 ghcr.io/org/backend:tag

# 启动绿色环境
docker run -d --name ai-digital-card-green -p 8202:8201 ghcr.io/org/backend:tag

# 查看蓝绿容器
docker ps --filter "name=ai-digital-card" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 清理旧环境
docker rm -f ai-digital-card-blue   # 或 ai-digital-card-green
```

### Nginx 操作

```bash
# 测试配置
nginx -t

# 重载配置（毫秒级）
nginx -s reload

# 查看当前活跃组
grep -oP 'default\s+\K(backend_blue|backend_green)' /etc/nginx/conf.d/bluegreen.conf

# 手动切换 (一行命令)
sed -i 's/default backend_blue;/default backend_green;/' /etc/nginx/conf.d/bluegreen.conf \
  && nginx -t && nginx -s reload
```

### 部署状态查看

```bash
# 查看最近部署记录
cat /opt/ai-digital-card/deploy/rollback/bluegreen_state.json

# 查看回滚备份
ls -la /opt/ai-digital-card/deploy/rollback/bluegreen.conf.bak.*
```

---

## 版本历史

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-07-01 | 初始版本：Nginx配置 + 切换脚本 + CI + 操作手册 | DevOps |

---

*如有疑问请联系 DevOps 团队或查看 [ROLLBACK.md](./ROLLBACK.md)（回滚操作手册）*
