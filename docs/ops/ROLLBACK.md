# AI数智名片 — 回滚操作手册

> **文档版本**: v1.0  
> **最后更新**: 2026-07-01  
> **适用项目**: AI数字名片 (AI Digital Card)  
> **相关文件**: [rollback.yml](../../.github/workflows/rollback.yml) | [rollback.sh](../../deploy/rollback.sh)

---

## 目录

1. [概述](#1-概述)
2. [回滚场景](#2-回滚场景)
3. [通过 CI 自动回滚 (推荐)](#3-通过-ci-自动回滚-推荐)
4. [通过脚本手动回滚](#4-通过脚本手动回滚)
5. [回滚策略详解](#5-回滚策略详解)
6. [故障排除](#6-故障排除)
7. [附录: 命令速查](#7-附录-命令速查)

---

## 1. 概述

回滚是当新版本部署后出现严重问题时，快速恢复到上一个稳定版本的关键操作。  
AI数字名片 提供 **三层回滚机制**：

| 层级 | 方式 | 速度 | 适用场景 |
|------|------|------|----------|
| L1 | CI 自动回滚 | ~2-5 min | Git revert + 重新构建 + 部署 |
| L2 | 已有镜像回滚 | ~30s-2min | 使用已有 Docker 镜像直接部署 |
| L3 | 蓝绿切换 | < 30s | 蓝绿部署环境瞬时切换 |
| L4 | 脚本手动回滚 | ~1-3 min | 本地运维或 CI 不可用时 |

---

## 2. 回滚场景

### 2.1 金丝雀发布失败 → 自动回滚

金丝雀工作流 (`canary-ci.yml`) 内置监控与判定逻辑：

- 错误率 > **1%** 持续 **5 分钟** → 判定为"回滚"
- 自动移除金丝雀容器 + 恢复 Nginx 分流
- 无需人工干预

### 2.2 全量发布失败 → 执行 rollback.yml

当 `deploy.yml` 或手动发布后发现问题（API 错误率飙升、页面白屏、延迟暴增）：

1. **决定回滚目标**：回滚到哪个版本？
   - 上一个 Git commit（默认）
   - 指定的 commit hash
   - 指定的 Docker 镜像标签
2. **触发 CI 回滚工作流**（见第 3 节）
3. **验证服务健康**

### 2.3 紧急回滚（跳过健康检查）

当服务完全不可用且需要最快速度恢复时：

- 设置 `skip_health_check: true`
- 直接部署上一个已知稳定版本
- **事后必须手动验证健康**

---

## 3. 通过 CI 自动回滚 (推荐)

### 3.1 触发方式

**GitHub Actions → Rollback → Run workflow**

| 参数 | 必填 | 说明 |
|------|------|------|
| `environment` | ✅ | `production` 或 `canary` |
| `target_tag` | ❌ | 已有 Docker 镜像标签（如 `abc1234`） |
| `commit` | ❌ | Git commit hash（如 `a1b2c3d4e5f6...`） |
| `skip_health_check` | ❌ | 紧急回滚时跳过健康检查 |

> **注意**: `target_tag` 和 `commit` 二选一，不能同时指定。都不指定时自动使用上一个 commit。

### 3.2 工作流步骤

```
Trigger (workflow_dispatch)
  │
  ├─ [resolve-target]  确定回滚目标镜像
  │    ├─ target_tag 指定 → 直接使用已有镜像
  │    ├─ commit 指定     → 标记为需 git revert + 构建
  │    └─ 都未指定         → 自动选择上一个 commit
  │
  ├─ [revert-and-build]  (仅 commit 模式)
  │    ├─ git revert --no-commit TARGET..HEAD
  │    ├─ git commit -m "rollback: revert to TARGET"
  │    ├─ git push
  │    └─ docker build + push
  │
  ├─ [deploy-rollback]  部署回滚镜像
  │    ├─ 保存当前版本状态
  │    ├─ docker pull + compose up -d
  │    └─ 健康检查 (60s 超时)
  │
  └─ [auto-recover]     (失败时触发)
       ├─ 读取上一版本状态
       └─ 恢复稳定版本 + 通知
```

### 3.3 成功流程示意

```
✅ Resolve Rollback Target       (5s)
✅ Git Revert & Build Image      (120s)
✅ Deploy Rollback               (30s)
✅ Health check (60s timeout)    (15s)
─────────────────────────────────
🎉 回滚成功！
```

### 3.4 失败自动恢复示意

```
✅ Resolve Rollback Target       (5s)
✅ Git Revert & Build Image      (120s)
✅ Deploy Rollback               (30s)
❌ Health check failed!          (60s)
✅ Auto-Recover triggered        (20s)
✅ Restored previous version
─────────────────────────────────
⚠️ 回滚失败，已自动恢复
    请查看 GitHub Actions 日志
```

---

## 4. 通过脚本手动回滚

### 4.1 SSH 登录服务器

```bash
ssh user@your-server
cd /opt/ai-digital-card
```

### 4.2 使用 rollback.sh

```bash
# 查看当前状态
bash deploy/rollback.sh --status

# 用已有镜像回滚
bash deploy/rollback.sh --target ghcr.io/org/backend:v1.2.3 --env production

# 通过 Git commit 回滚 (会重新构建)
bash deploy/rollback.sh --commit a1b2c3d4 --env production

# 恢复到上一个版本
bash deploy/rollback.sh --restore-previous

# 模拟执行 (不实际部署)
bash deploy/rollback.sh --target ghcr.io/org/backend:v1.2.3 --dry-run
```

### 4.3 手动操作步骤

如果脚本不可用，可以手动执行回滚：

```bash
# 1. 记录当前版本
docker inspect ai-digital-card-backend \
  --format '{{.Config.Image}}' > /tmp/pre_rollback.txt

# 2. 拉取目标镜像
docker pull ghcr.io/org/backend:v1.2.3

# 3. 更新 docker-compose.yml
sed -i.bak 's|image: .*backend.*|image: ghcr.io/org/backend:v1.2.3|g' docker-compose.yml

# 4. 重启服务
docker compose up -d --remove-orphans

# 5. 健康检查
curl -sf http://localhost:8201/health && echo "OK" || echo "FAIL"

# 6. 如果失败，恢复上一个版本
if [ $? -ne 0 ]; then
  PREV=$(cat /tmp/pre_rollback.txt)
  sed -i.bak "s|image: .*backend.*|image: ${PREV}|g" docker-compose.yml
  docker compose up -d --remove-orphans
fi
```

---

## 5. 回滚策略详解

### 5.1 镜像回滚 vs Git Revert

| 对比项 | 镜像回滚 | Git Revert |
|--------|----------|------------|
| 速度 | 快 (30s-2min) | 慢 (2-5min，含构建) |
| 代码一致性 | 使用之前构建的镜像 | 重新构建，可能引入新依赖问题 |
| 适用场景 | 回退到最近版本 | 回退到较老版本 |
| 推荐度 | ⭐ 优先使用 | ⭐ 仅当需要回退到较老版本 |

### 5.2 金丝雀回滚

金丝雀回滚由 `canary-ci.yml` 的 `monitor-and-decide` 步骤自动处理：

```
错误率 > 阈值 持续 5分钟
  → 标记 decision=rollback
  → 移除金丝雀容器
  → 恢复 Nginx 分流配置
  → nginx -s reload
  → 完成回滚
```

如果金丝雀回滚失败，使用 `rollback.yml` 指定 `environment: canary` 手动回滚。

### 5.3 蓝绿回滚

如果使用蓝绿部署模式：

```bash
# 切换回蓝色环境（绿色是新版本）
bash deploy/blue_green_deploy.sh rollback
```

---

## 6. 故障排除

### 6.1 健康检查失败

**现象**: CI 中 `Health check` 步骤失败 → 自动恢复触发  
**排查步骤**:

```bash
# 1. 检查容器状态
docker ps -a --filter "name=ai-digital-card"

# 2. 查看容器日志
docker logs ai-digital-card-backend --tail 50

# 3. 手动测试端点
curl -v http://localhost:8201/health

# 4. 检查数据库连接
docker exec ai-digital-card-backend python -c "
from database import SessionLocal
db = SessionLocal()
db.execute('SELECT 1')
print('DB OK')
"
```

### 6.2 Git Revert 冲突

**现象**: CI 中 `Git revert` 步骤显示冲突警告  
**处理**: CI 会自动使用 `git reset --soft` 替代，无需人工干预。  
如果 CI 失败：

```bash
cd /opt/ai-digital-card
git log --oneline -10       # 查看历史
git revert --no-commit TARGET..HEAD
# 手动解决冲突
git add .
git commit -m "rollback: manual conflict resolution"
git push
```

### 6.3 自动恢复连续失败

**现象**: 恢复后的版本仍然不健康  
**处理**: 这是严重状态，需要人工介入：

```bash
# 1. 查看恢复日志
cat deploy/rollback/pre_rollback_image.txt

# 2. 手动拉取更早的稳定版本
docker pull ghcr.io/org/backend:last-known-good

# 3. 强制替换
sed -i.bak "s|image: .*backend.*|image: ghcr.io/org/backend:last-known-good|g" docker-compose.yml
docker compose up -d --remove-orphans

# 4. 如果仍然失败，回滚到数据库快照
docker compose down
# 从备份恢复: 参考 docs/ops/production_readiness.md
```

### 6.4 CI 无法触发

**原因**: GitHub Actions 异常、Secret 过期、SSH 密钥失效  
**替代方案**: SSH 登录服务器手动执行回滚（见第 4 节）

---

## 7. 附录: 命令速查

### CI 操作

```bash
# 通过 gh CLI 触发回滚
gh workflow run Rollback \
  -f environment=production \
  -f commit=a1b2c3d4

# 使用已有镜像回滚
gh workflow run Rollback \
  -f environment=production \
  -f target_tag=v1.2.3

# 紧急回滚（跳过健康检查）
gh workflow run Rollback \
  -f environment=production \
  -f target_tag=v1.2.3 \
  -f skip_health_check=true
```

### 脚本操作

```bash
# 查看状态
bash deploy/rollback.sh --status

# 镜像回滚
bash deploy/rollback.sh --target ghcr.io/org/backend:v1.2.3

# Git commit 回滚
bash deploy/rollback.sh --commit a1b2c3d4

# 恢复上一个版本
bash deploy/rollback.sh --restore-previous
```

### 容器操作

```bash
# 重启服务
docker compose up -d --remove-orphans

# 查看日志
docker compose logs --tail=100 -f

# 查看健康状态
curl -sf http://localhost:8201/health | jq .
```

---

## 版本历史

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-07-01 | 初始版本：CI 自动回滚 + 脚本 + 操作手册 | DevOps |

---

*如有疑问请联系 DevOps 团队或查看 [production_readiness.md](./production_readiness.md)*
