# AI数智名片 — 预览部署操作手册 (Preview Deploy)

> **文档版本**: v1.0  
> **最后更新**: 2026-07-01  
> **适用项目**: AI数字名片 (AI Digital Card)  
> **相关文件**: [preview.yml](../../.github/workflows/preview.yml) | [preview.sh](../../deploy/preview.sh)

---

## 目录

1. [概述](#1-概述)
2. [工作流程](#2-工作流程)
3. [前置条件](#3-前置条件)
4. [自动触发 — PR 预览部署（推荐）](#4-自动触发--pr-预览部署推荐)
5. [手动触发 — 通过脚本部署](#5-手动触发--通过脚本部署)
6. [预览环境管理](#6-预览环境管理)
7. [预览环境清理](#7-预览环境清理)
8. [故障排除](#8-故障排除)
9. [附录](#9-附录)

---

## 1. 概述

Preview Deploy（PR 预览部署）允许开发者在 Pull Request 阶段获得一个 **独立的、可访问的预览环境**，方便团队和产品经理在实际部署到生产环境之前审查变更效果。

### 核心特性

| 特性 | 说明 |
|------|------|
| **自动触发** | 每次 PR 打开或更新时自动部署 |
| **独立环境** | 每个 PR 拥有独立的子域名和端口 |
| **自动评论** | PR 上自动添加预览链接和构建状态 |
| **自动清理** | PR 关闭后自动销毁预览环境 |
| **并行部署** | 多个 PR 可同时拥有独立的预览环境 |

### 环境规格

| 项目 | 值 |
|------|-----|
| **前端** | 静态文件通过 Nginx 提供服务 |
| **后端** | Docker 容器，端口动态分配 |
| **域名** | `https://preview-{PR_NUMBER}.ai-card.com` |
| **API** | `https://api-preview-{PR_NUMBER}.ai-card.com` |
| **服务器** | 独立预览服务器（与生产隔离） |

---

## 2. 工作流程

```
PR Opened / Synchronized / Reopened
  │
  ├─ [preview.yml] GitHub Actions
  │    │
  │    ├─ [build-frontend]   npm ci → npm run build
  │    │    └─ 产物: frontend/dist (上传 Artifact)
  │    │
  │    ├─ [build-backend]    Docker build & push (tag: pr-{number}-{sha})
  │    │    └─ 产物: ghcr.io/org/backend:pr-{number}-{sha}
  │    │
  │    ├─ [deploy-preview]   调用 deploy/preview.sh
  │    │    ├─ 1. 准备服务器环境
  │    │    ├─ 2. 上传前端静态文件
  │    │    ├─ 3. 部署后端 Docker 容器
  │    │    ├─ 4. 配置 Nginx 反向代理
  │    │    └─ 5. 健康检查
  │    │
  │    └─ [add-pr-comment]   在 PR 上添加评论
  │         ├─ 预览链接
  │         ├─ 后端镜像信息
  │         └─ 构建状态徽章
  │
PR Closed / Merged
  └─ (可选) 手动清理或等待自动清理 (TTL)
```

---

## 3. 前置条件

### 3.1 GitHub Secrets

以下 Secrets 必须在 GitHub 仓库中配置：

| Secret 名称 | 说明 | 示例 |
|-------------|------|------|
| `PREVIEW_SSH_HOST` | 预览服务器主机名/IP | `preview.example.com` |
| `PREVIEW_SSH_USER` | 预览服务器 SSH 用户名 | `deploy` |
| `PREVIEW_SSH_KEY` | 预览服务器 SSH 私钥 | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `GITHUB_TOKEN` | 自动提供（用于 PR 评论） | — |

### 3.2 预览服务器要求

| 要求 | 版本/说明 |
|------|-----------|
| **操作系统** | Ubuntu 22.04+ / Debian 12+ |
| **Docker** | 24+ (含 docker compose 插件) |
| **Nginx** | 1.24+ |
| **rsync** | 3.2+（可选，用于快速上传） |
| **curl** | 7.68+ |
| **磁盘** | 至少 10GB 空闲 |
| **内存** | 至少 2GB |

### 3.3 服务器初始配置

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker deploy

# 2. 安装 Nginx
sudo apt-get update && sudo apt-get install -y nginx rsync

# 3. 创建基础目录
sudo mkdir -p /opt/ai-digital-card-preview

# 4. 防火墙配置（如有）
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp    # 如果使用 HTTPS

# 5. 配置 SSH 公钥认证
# 将 GitHub Actions 使用的公钥添加到 ~/.ssh/authorized_keys
```

### 3.4 DNS 配置

为预览环境配置通配符 DNS 解析：

```
*.preview.ai-card.com  A  <预览服务器 IP>
api-preview-*.ai-card.com  A  <预览服务器 IP>
```

或配置 Nginx 使用 `$host` 变量动态路由。

---

## 4. 自动触发 — PR 预览部署（推荐）

### 4.1 触发方式

Preview Deploy 在以下事件 **自动触发**：

| 事件 | 触发条件 |
|------|----------|
| `pull_request` opened | PR 创建时 |
| `pull_request` synchronize | PR 推送新 commit 时 |
| `pull_request` reopened | PR 重新打开时 |

无需手动操作。每次 PR 更新时，**旧的预览环境会被自动取消并重新部署**（由 `concurrency.cancel-in-progress: true` 控制）。

### 4.2 查看部署状态

1. 打开 PR → 在 **Conversation** 标签页底部找到评论
2. 或打开 PR → **Checks** 标签页 → 查看 `Preview Deploy` 工作流
3. 评论中包含：
   - **预览链接**：可直接点击访问
   - **后端镜像**：构建的 Docker 镜像名称
   - **Commit**：当前部署的 commit
   - **状态徽章**：显示部署成功/失败
   - **工作流日志链接**：查看详细日志

### 4.3 工作流参数

| 环境变量 | 值 | 说明 |
|----------|-----|------|
| `PR_NUMBER` | 自动 | PR 编号，用于端口和域名分配 |
| `PREVIEW_HOST` | `preview-{PR_NUMBER}.ai-card.com` | 预览域名 |
| `IMAGE_BACKEND` | `ghcr.io/org/backend` | 基础镜像名称 |
| `REGISTRY` | `ghcr.io` | 镜像仓库 |

### 4.4 PR 评论示例

```
## ✅ Preview Deploy - PR #42

| Item | Value |
|------|-------|
| **Preview URL** | https://preview-42.ai-card.com |
| **Backend Image** | ghcr.io/org/backend:pr-42-abc1234 |
| **Commit** | abc1234 |
| **Status** | ![status](https://img.shields.io/badge/status-部署成功-brightgreen) |
| **Triggered By** | developer |

---

### Quick Links

| Service | URL |
|---------|-----|
| Frontend | https://preview-42.ai-card.com |
| API Docs | https://api-preview-42.ai-card.com/docs |
| Health   | https://preview-42.ai-card.com/health |
```

---

## 5. 手动触发 — 通过脚本部署

### 5.1 本地执行

在本地开发环境执行预览部署：

```bash
# 1. 先构建前端
cd frontend && npm ci && npm run build && cd ..

# 2. 执行预览部署脚本
bash deploy/preview.sh \
  --pr-number 42 \
  --image ghcr.io/org/backend:pr-42-abc1234 \
  --domain preview-42.ai-card.com \
  --ssh-host preview.example.com \
  --ssh-user deploy \
  --repo org/ai-digital-card
```

### 5.2 通过 gh CLI 触发 CI 工作流

```bash
# 从现有 PR 触发预览部署
gh workflow run "Preview Deploy" \
  --ref refs/pull/42/head

# 查看运行状态
gh run list --workflow="Preview Deploy"
```

---

## 6. 预览环境管理

### 6.1 环境隔离

每个 PR 的预览环境完全隔离：

| 维度 | 隔离方式 |
|------|----------|
| **域名** | `preview-{PR_NUMBER}.ai-card.com` |
| **后端端口** | `8300 + PR_NUMBER`（每个 PR 独立端口） |
| **容器名** | `ai-card-preview-pr-{PR_NUMBER}` |
| **文件目录** | `/opt/ai-digital-card-preview/pr-{PR_NUMBER}/` |
| **Docker 镜像** | 标签包含 PR 编号 |

### 6.2 访问预览环境

```bash
# 前端
curl https://preview-42.ai-card.com

# API 健康检查
curl https://preview-42.ai-card.com/health

# API 文档
curl https://api-preview-42.ai-card.com/docs
```

### 6.3 查看服务器状态

```bash
# SSH 登录后
# 查看所有预览容器
docker ps --filter "label=com.ai-card.preview=true"

# 查看特定 PR 的容器
docker ps --filter "name=ai-card-preview-pr-42"

# 查看 Nginx 预览配置
ls -la /etc/nginx/sites-enabled/preview-*.conf

# 查看预览目录列表
ls -la /opt/ai-digital-card-preview/
```

### 6.4 查看容器日志

```bash
# 实时日志
ssh deploy@preview.example.com
docker logs ai-card-preview-pr-42 --tail 100 -f

# Nginx 访问日志
tail -f /var/log/nginx/preview-42.access.log

# Nginx 错误日志
tail -f /var/log/nginx/error.log | grep preview-42
```

---

## 7. 预览环境清理

### 7.1 自动清理（推荐）

PR 关闭（merged/closed）后，应配置清理流程。

**方案 A：使用单独的 cleanup workflow**

创建 `.github/workflows/preview-cleanup.yml`：

```yaml
name: Preview Cleanup

on:
  pull_request:
    types: [closed]

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.PREVIEW_SSH_KEY }}
      - name: Run cleanup
        run: |
          bash deploy/preview.sh cleanup ${{ github.event.pull_request.number }} \
            --ssh-host "${{ secrets.PREVIEW_SSH_HOST }}" \
            --ssh-user "${{ secrets.PREVIEW_SSH_USER }}"
```

**方案 B：定时清理（TTL）**

在预览服务器上配置 cron 任务，清理超过指定天数的预览环境：

```bash
# /etc/cron.daily/cleanup-preview-envs
#!/bin/bash
# 清理超过 7 天的预览环境
find /opt/ai-digital-card-preview -maxdepth 1 -type d -name "pr-*" -mtime +7 | while read dir; do
    PR_NUM=$(basename "$dir" | sed 's/pr-//')
    echo "清理过期预览环境 PR #${PR_NUM}"
    docker rm -f "ai-card-preview-pr-${PR_NUM}" 2>/dev/null || true
    rm -f "/etc/nginx/sites-enabled/preview-pr-${PR_NUM}.conf" 2>/dev/null || true
    rm -rf "$dir"
done
nginx -t && nginx -s reload || true
```

### 7.2 手动清理

```bash
# 通过脚本清理指定 PR
bash deploy/preview.sh cleanup 42 \
  --ssh-host preview.example.com \
  --ssh-user deploy

# 或直接 SSH 到服务器手动清理
ssh deploy@preview.example.com

# 停止并删除容器
docker rm -f ai-card-preview-pr-42

# 删除 Nginx 配置
rm -f /etc/nginx/sites-enabled/preview-pr-42.conf
nginx -s reload

# 删除项目目录
rm -rf /opt/ai-digital-card-preview/pr-42/

# 删除镜像（可选）
docker rmi ghcr.io/org/backend:pr-42-abc1234
```

---

## 8. 故障排除

### 8.1 预览链接无法访问

**现象**: 点击 PR 评论中的预览链接显示 502/503/连接失败

**排查步骤**:

```bash
# 1. 检查容器是否运行
ssh deploy@preview.example.com
docker ps --filter "name=ai-card-preview-pr-42"

# 2. 如果容器未运行，查看日志
docker logs ai-card-preview-pr-42 --tail 50

# 3. 检查 Nginx 配置
cat /etc/nginx/sites-enabled/preview-pr-42.conf
nginx -t

# 4. 检查端口冲突
ss -tlnp | grep 8342  # 8300 + PR_NUMBER

# 5. 直接测试后端
curl -v http://127.0.0.1:8342/health
```

### 8.2 前端空白页

**现象**: 页面加载但显示空白

**排查步骤**:

```bash
# 1. 检查浏览器控制台 → 网络请求
# 2. 检查 API 基础 URL 配置
ssh deploy@preview.example.com
cat /opt/ai-digital-card-preview/pr-42/frontend/.env.preview 2>/dev/null || true

# 3. 验证 API 可访问
curl -v https://api-preview-42.ai-card.com/health

# 4. 检查 Nginx 静态文件
ls -la /opt/ai-digital-card-preview/pr-42/frontend/
```

### 8.3 构建失败

**现象**: GitHub Actions 中 `build-frontend` 或 `build-backend` 步骤失败

**排查步骤**:

```bash
# 1. 查看完整构建日志
# GitHub Actions → Preview Deploy → 对应 Job → Step

# 2. 本地重现构建
cd frontend && npm ci && npm run build
cd backend && docker build -t test .

# 3. 常见原因
# - package-lock.json 冲突 → 重新生成 npm install
# - Node.js 版本不兼容 → 检查 .nvmrc
# - Python 依赖问题 → 检查 requirements.txt
```

### 8.4 SSH 连接失败

**现象**: `deploy-preview` Job 中 SSH 相关步骤失败

**排查步骤**:

```bash
# 1. 检查 Secret 是否已配置
# GitHub → Settings → Secrets and variables → Actions

# 2. 测试 SSH 连接
ssh -i /path/to/private-key -o StrictHostKeyChecking=no deploy@preview.example.com

# 3. 检查服务器 SSH 配置
sudo cat /etc/ssh/sshd_config | grep -E "PubkeyAuthentication|PasswordAuthentication"

# 4. 检查 authorized_keys
cat ~/.ssh/authorized_keys
```

### 8.5 域名解析失败

**现象**: `preview-42.ai-card.com` 无法解析

**排查步骤**:

```bash
# 1. 检查 DNS 解析
nslookup preview-42.ai-card.com
dig preview-42.ai-card.com

# 2. 检查 Nginx 配置中 server_name 是否匹配
ssh deploy@preview.example.com
grep server_name /etc/nginx/sites-enabled/preview-pr-42.conf

# 3. 直接使用 IP 访问测试
curl -H "Host: preview-42.ai-card.com" http://<服务器IP>
```

---

## 9. 附录

### 9.1 端口分配规则

预览环境后端端口按 PR 编号分配：

```
后端端口 = 8300 + PR_NUMBER
  前端 Nginx 监听 80 端口，通过 server_name 路由
```

| PR # | 后端端口 | 容器名 |
|------|----------|--------|
| 1 | 8301 | `ai-card-preview-pr-1` |
| 42 | 8342 | `ai-card-preview-pr-42` |
| 100 | 8400 | `ai-card-preview-pr-100` |

> **注意**: 理论上最多支持 299 个并发预览环境（端口 8301-8599）。

### 9.2 Docker 镜像命名规范

```
ghcr.io/{owner}/{repo}/backend:pr-{PR_NUMBER}-{commit_sha7}
```

示例: `ghcr.io/my-org/ai-digital-card/backend:pr-42-abc1234`

### 9.3 文件结构

预览服务器上每个 PR 的目录结构：

```
/opt/ai-digital-card-preview/
├── pr-42/
│   ├── frontend/          # 前端静态文件
│   │   ├── index.html
│   │   ├── assets/
│   │   └── .env.preview   # 构建时的环境变量
│   └── backend/
│       ├── data/           # 持久化数据（挂载到容器）
│       └── uploads/        # 上传文件（挂载到容器）
└── pr-43/
    └── ...
```

### 9.4 所需 Secrets 快速配置

```bash
# 使用 gh CLI 配置 Secrets
gh secret set PREVIEW_SSH_HOST --body "preview.example.com"
gh secret set PREVIEW_SSH_USER --body "deploy"
gh secret set PREVIEW_SSH_KEY < ~/.ssh/id_ed25519_preview
```

### 9.5 监控与告警建议

- 为预览服务器配置基础监控（CPU、内存、磁盘）
- 设置磁盘告警阈值（预览环境可能占用大量磁盘空间）
- 定期清理长时间未关闭 PR 的预览环境
- 记录预览部署日志，便于问题排查

---

## 版本历史

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-07-01 | 初始版本：预览部署 CI + 脚本 + 操作手册 | DevOps |

---

*如有疑问请联系 DevOps 团队或查看 [CI_SECURITY.md](./CI_SECURITY.md)*
