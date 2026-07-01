# Preview Deploy 启动检查清单

> **项目**: AI数智名片 (AI Digital Business Card)
> **文档版本**: v1.0
> **最后更新**: 2026-07-02
> **相关文件**:
>   - `../.github/workflows/preview.yml` — CI 工作流
>   - `../../deploy/preview.sh` — 部署脚本
>   - `./PREVIEW_DEPLOY.md` — 操作手册
>
> **前置依赖**: 完成 [production_readiness.md](./production_readiness.md) 中生产就绪检查

---

## 目录

1. [前置条件](#1-前置条件)
2. [DNS 配置](#2-dns-配置)
3. [GitHub Secrets 配置](#3-github-secrets-配置)
4. [服务器初始化](#4-服务器初始化)
5. [CI 工作流验证](#5-ci-工作流验证)
6. [功能验证步骤](#6-功能验证步骤)
7. [清理验证](#7-清理验证)
8. [回滚方案](#8-回滚方案)
9. [附录: 快速启动命令集](#9-附录-快速启动命令集)

---

## 1. 前置条件

### 1.1 总体检查

- [ ] Preview Deploy CI 工作流已就绪: `.github/workflows/preview.yml`
- [ ] 部署脚本已就绪: `deploy/preview.sh`
- [ ] 操作手册已就绪: `docs/ops/PREVIEW_DEPLOY.md`
- [ ] 已确定预览服务器硬件规格 (建议: 2C4G, 10GB+ 磁盘)
- [ ] 已确定预览域名 (建议: `*.preview.ai-card.com`)
- [ ] GitHub 仓库已配置好权限 (Actions 读写、packages 写入)

### 1.2 预览服务器硬件要求

| 项目 | 最低要求 | 建议配置 |
|------|---------|---------|
| **CPU** | 2 核 | 4 核 |
| **内存** | 2 GB | 4 GB |
| **磁盘** | 10 GB | 20 GB (SSD) |
| **带宽** | 100 Mbps | 500 Mbps |
| **操作系统** | Ubuntu 22.04+ / Debian 12+ | Ubuntu 24.04 LTS |
| **Docker** | 24+ (含 compose 插件) | 最新稳定版 |
| **Nginx** | 1.24+ | 1.26+ |
| **开放端口** | 80/tcp, 443/tcp, 22/tcp | 同上 |

---

## 2. DNS 配置

### 2.1 通配符 DNS 记录

在域名 DNS 管理面板中添加以下记录：

| 记录类型 | 名称 | 值 | TTL |
|---------|------|----|:---:|
| **A** | `*.preview.ai-card.com` | `<预览服务器公网 IP>` | 300 |
| **A** | `api-preview-*.ai-card.com` | `<预览服务器公网 IP>` | 300 |

> **注意**: 如果 DNS 服务商不支持通配符 A 记录，可改为：
> - 配置 Nginx 使用 `$host` 变量动态路由（推荐）
> - 或每部署一个新 PR 时手动添加 DNS 记录（不推荐，不可扩展）

### 2.2 DNS 验证

```bash
# 验证通配符解析
nslookup preview-42.ai-card.com
nslookup preview-99.ai-card.com
nslookup api-preview-42.ai-card.com

# 预期输出: 所有域名解析到同一服务器 IP

# 备选: 使用 dig 命令
dig +short preview-42.ai-card.com A

# 配置完成标记
```

- [ ] 通配符 A 记录 `*.preview.ai-card.com` 已配置
- [ ] 通配符 A 记录 `api-preview-*.ai-card.com` 已配置
- [ ] DNS 传播已生效 (TTL 过期后测试解析)

---

## 3. GitHub Secrets 配置

### 3.1 需要配置的 Secrets

在 **GitHub 仓库 → Settings → Secrets and variables → Actions** 中添加以下 Secrets：

| Secret 名称 | 必需 | 说明 | 示例值 |
|------------|:----:|------|--------|
| `PREVIEW_SSH_HOST` | ✅ | 预览服务器主机名或 IP | `203.0.113.10` |
| `PREVIEW_SSH_USER` | ✅ | SSH 登录用户名 | `deploy` |
| `PREVIEW_SSH_KEY` | ✅ | SSH 私钥 (ed25519 推荐) | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `GITHUB_TOKEN` | ✅ | 自动提供，无需手动配置 | — |

> ⚠️ **安全警告**: 
> - 私钥使用 `ed25519` 算法生成: `ssh-keygen -t ed25519 -f preview-deploy -C "preview@ai-card.com"`
> - 私钥权限必须为 `600`: `chmod 600 preview-deploy`
> - 私钥内容通过 `cat preview-deploy` 复制后粘贴至 Secret
> - 配置完成后安全删除本地私钥文件: `shred -u preview-deploy preview-deploy.pub`
> - 每 180 天轮换一次密钥对

### 3.2 Secrets 配置命令

```bash
# 使用 GitHub CLI 快速配置
gh secret set PREVIEW_SSH_HOST --body "203.0.113.10"
gh secret set PREVIEW_SSH_USER --body "deploy"
gh secret set PREVIEW_SSH_KEY < ./preview-deploy
```

### 3.3 验证 Secrets

- [ ] `PREVIEW_SSH_HOST` 已配置且值正确
- [ ] `PREVIEW_SSH_USER` 已配置且值正确
- [ ] `PREVIEW_SSH_KEY` 已配置且包含完整私钥内容
- [ ] 所有 Secrets 被正确隐藏 (在 Actions 日志中显示为 `***`)

---

## 4. 服务器初始化

### 4.1 操作系统安装

- [ ] 操作系统已安装 (Ubuntu 22.04+ / Debian 12+)
- [ ] 系统已更新: `sudo apt update && sudo apt upgrade -y`
- [ ] 系统时区已配置: `sudo timedatectl set-timezone Asia/Shanghai`
- [ ] 主机名已设置: `sudo hostnamectl set-hostname ai-card-preview`

### 4.2 创建部署用户

```bash
# 创建 deploy 用户
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG sudo deploy

# 配置 SSH 公钥认证
sudo -u deploy mkdir -p ~deploy/.ssh
sudo -u deploy chmod 700 ~deploy/.ssh

# 将公钥添加到 authorized_keys
echo "<公钥内容>" | sudo tee -a ~deploy/.ssh/authorized_keys
sudo chmod 600 ~deploy/.ssh/authorized_keys
sudo chown -R deploy:deploy ~deploy/.ssh
```

- [ ] 部署用户 `deploy` 已创建
- [ ] SSH 公钥认证已配置
- [ ] `ssh deploy@<服务器IP>` 可无密码登录

### 4.3 安装 Docker

```bash
# 安装 Docker (官方源)
curl -fsSL https://get.docker.com | sudo bash

# 将 deploy 用户加入 docker 组 (避免每次 sudo)
sudo usermod -aG docker deploy

# 验证安装
docker --version          # 预期: Docker version 24+ 
docker compose version    # 预期: Docker Compose version v2+

# 验证非 root 用户可用
# 退出重新登录后执行:
docker ps    # 预期: 无错误
```

- [ ] Docker 已安装 (版本 24+)
- [ ] Docker Compose 插件已安装
- [ ] deploy 用户可免 sudo 运行 docker 命令

### 4.4 安装 Nginx 与辅助工具

```bash
sudo apt-get install -y nginx rsync curl
sudo nginx -v          # 预期: nginx version: nginx/1.24+ 
rsync --version | head -1  # 预期: rsync  version 3.2+
```

- [ ] Nginx 已安装 (版本 1.24+)
- [ ] rsync 已安装 (用于高效前端文件上传)
- [ ] curl 已安装

### 4.5 防火墙配置

```bash
# 如果使用 ufw
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (如果使用)
sudo ufw --force enable
sudo ufw status          # 确认规则生效
```

- [ ] SSH 端口 (22) 已放行
- [ ] HTTP 端口 (80) 已放行
- [ ] HTTPS 端口 (443) 已放行 (如适用)
- [ ] 防火墙已启用并验证

### 4.6 创建预览基础目录

```bash
sudo mkdir -p /opt/ai-digital-card-preview
sudo chown -R deploy:deploy /opt/ai-digital-card-preview
```

- [ ] 预览基础目录 `/opt/ai-digital-card-preview` 已创建
- [ ] 目录属主为 `deploy:deploy`

### 4.7 SSH 严格主机密钥检查配置 (CI 兼容)

```bash
# 在 deploy 用户的 ~/.ssh/config 中添加 (或全局)
echo "Host *
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null" | sudo -u deploy tee -a ~deploy/.ssh/config
sudo chmod 600 ~deploy/.ssh/config
```

> ⚠️ 这是 CI 场景下的常见做法。生产环境建议使用已知主机文件。

- [ ] SSH 严格主机密钥检查已关闭 (用于 CI 自动化)

### 4.8 服务器初始化检查清单

- [ ] 操作系统安装与基础配置完成
- [ ] Docker 安装并验证
- [ ] Nginx 安装并验证
- [ ] 部署用户创建与 SSH 认证
- [ ] 防火墙配置完成
- [ ] 预览目录创建完成
- [ ] SSH 配置完成
- [ ] 服务器可通过网络正常访问

---

## 5. CI 工作流验证

### 5.1 手动触发测试

```bash
# 方式一: 通过 gh CLI
gh workflow run "Preview Deploy" --ref main

# 方式二: 创建测试 PR
# 在 GitHub 上创建一个临时分支并提交 PR
```

### 5.2 验证 CI 各阶段

| 阶段 | 预期结果 | 验证方法 |
|------|---------|---------|
| **build-frontend** | npm ci + build 成功 | Actions 日志: 绿色 ✓ |
| **build-backend** | Docker 构建并推送到 ghcr.io | Actions 日志 + ghcr.io 仓库验证 |
| **deploy-preview** | SSH 连接 → 创建目录 → 上传文件 → 启动容器 → 配置 Nginx | Actions 日志: 步骤日志完整 |
| **health check** | 后端 `/health` 返回 200 | Actions 日志: "✅ 健康检查通过" |
| **PR comment** | PR 中出现预览链接评论 | PR 页面: 底部评论包含 URL |

### 5.3 CI 配置确认

- [ ] `preview.yml` 工作流语法正确 (通过 `gh workflow view` 确认)
- [ ] `concurrency.cancel-in-progress: true` 已设置 (防止重复部署)
- [ ] 构建产物 retention-days 已设置 (建议 7 天)
- [ ] 部署 Job 的 environment 配置了 URL
- [ ] PR 评论 Job 使用 `actions/github-script@v7` 正确

### 5.4 Docker 镜像验证

```bash
# 验证镜像已推送到 ghcr.io
# 在 GitHub Packages 页面查看，或使用:
gh api /user/packages/container/backend/versions --jq '.[].metadata.container.tags[]' | grep "pr-"

# 或登录 ghcr.io 查看
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$USER" --password-stdin
docker pull ghcr.io/<org>/ai-digital-card/backend:pr-<number>-<sha>
```

- [ ] 后端 Docker 镜像已成功推送到 ghcr.io
- [ ] 镜像标签格式正确: `pr-{number}-{sha7}`

---

## 6. 功能验证步骤

### 6.1 基础访问验证

```bash
# 获取 PR 评论中的预览 URL
# 或根据 PR 编号构造
PR_NUMBER=42
PREVIEW_HOST="preview-${PR_NUMBER}.ai-card.com"
API_HOST="api-preview-${PR_NUMBER}.ai-card.com"

# 验证前端可访问
curl -sI "https://${PREVIEW_HOST}" | head -n 5
# 预期: HTTP/2 200 或 304

# 验证安全头
curl -sI "https://${PREVIEW_HOST}" | grep -i "strict-transport-security\|x-frame-options\|x-content-type-options"
# 预期: 各安全头存在

# 验证 API 健康检查
curl -s "https://${PREVIEW_HOST}/health"
# 预期: {"status":"ok",...}

# 验证 API 可访问
curl -s "https://${PREVIEW_HOST}/api/v1/..."
# 预期: 正常业务响应
```

### 6.2 多 PR 并行验证

| 测试场景 | 步骤 | 预期结果 |
|---------|------|---------|
| 单 PR 部署 | 创建 PR → 等待部署完成 | 预览 URL 可访问 |
| 同时部署多个 PR | 同时创建 2-3 个 PR | 每个独立 URL 可访问 |
| PR 更新 | 在已有 PR 上推送新 commit | 旧环境被取消，新环境部署 |
| PR 重新打开 | 关闭 PR 后重新打开 | 环境重建 |

### 6.3 安全验证

```bash
# 验证无直接端口暴露
curl -sI "http://<服务器IP>:8342"   # 预期: 拒绝连接或超时

# 验证只能通过域名访问
curl -sI "http://<服务器IP>"        # 预期: 返回 Nginx 默认页或 400

# 确保无法绕过反向代理
curl -s "http://<服务器IP>/health" -H "Host: preview-42.ai-card.com"
# 预期: 正常响应 (通过域名路由)
```

### 6.4 异常场景验证

| 场景 | 验证方法 | 预期行为 |
|------|---------|---------|
| 构建失败 | 提交有语法错误的代码 | CI 报告失败，PR 评论显示 ❌ |
| 健康检查失败 | 关闭后端端口 | CI 重试 12 次后标记失败 |
| SSH 连接失败 | 移除公钥 | CI 立即失败 |
| 端口冲突 | 手动占用 PR 端口 | 端口冲突→容器启动失败→健康检查失败 |

### 6.5 验证检查清单

- [ ] 前端页面可正常加载 (无白屏、无 JS 错误)
- [ ] API 健康检查返回 200
- [ ] 安全 HTTP 头存在 (HSTS, XFO, XCTO)
- [ ] API 请求可正常代理到后端
- [ ] 多个 PR 可同时拥有独立的预览环境
- [ ] PR 更新时旧部署自动取消
- [ ] HTTPS 强制跳转生效

---

## 7. 清理验证

### 7.1 手动清理测试

```bash
# SSH 到预览服务器
ssh deploy@<服务器IP>

# 查看当前预览容器
docker ps --filter "label=com.ai-card.preview=true"

# 手动清理特定 PR 环境
cd /opt/ai-digital-card-preview
ls -la
docker rm -f ai-card-preview-pr-42
rm -f /etc/nginx/sites-enabled/preview-pr-42.conf
nginx -s reload
rm -rf pr-42/
```

```bash
# 通过脚本清理 (推荐)
bash deploy/preview.sh cleanup 42 \
  --ssh-host <服务器IP> \
  --ssh-user deploy
```

### 7.2 自动清理确认

- [ ] PR 关闭时清理流程已配置 (建议创建独立的 cleanup workflow 或 cron TTL 脚本)
- [ ] TTL 清理 cron 脚本已就绪 (详见 [PREVIEW_DEPLOY.md](./PREVIEW_DEPLOY.md) §7.1)

### 7.3 清理验证清单

- [ ] `docker rm -f` 可成功停止并删除容器
- [ ] Nginx 配置删除后 `nginx -t` 测试通过
- [ ] 项目目录删除后磁盘空间释放
- [ ] Docker 镜像清理可正常执行

---

## 8. 回滚方案

### 8.1 部署回滚

如果预览部署失败，回滚步骤：

```bash
# 1. 确认失败原因
# 查看 Actions 日志 → deploy-preview Job

# 2. 手动 SSH 到服务器排查
ssh deploy@<服务器IP>
docker ps -a | grep "preview-pr-${PR_NUMBER}"
docker logs ai-card-preview-pr-${PR_NUMBER} --tail 50
cat /etc/nginx/sites-enabled/preview-pr-${PR_NUMBER}.conf

# 3. 手动清理
bash deploy/preview.sh cleanup ${PR_NUMBER} \
  --ssh-host <服务器IP> \
  --ssh-user deploy

# 4. 在 PR 中修复后重新触发 (推送新 commit 或关闭后重新打开)
```

### 8.2 服务器回滚

如果预览服务器配置出现问题：

```bash
# 重建预览目录
sudo rm -rf /opt/ai-digital-card-preview
sudo mkdir -p /opt/ai-digital-card-preview
sudo chown -R deploy:deploy /opt/ai-digital-card-preview

# 重启 Nginx
sudo nginx -s reload

# 重启 Docker
sudo systemctl restart docker
```

### 8.3 回滚检查清单

- [ ] 手动清理脚本可用: `deploy/preview.sh cleanup <PR_NUMBER> ...`
- [ ] Nginx 回退配置已验证
- [ ] 服务器级回滚步骤已记录

---

## 9. 附录: 快速启动命令集

### 9.1 一条命令完成服务器初始化

```bash
# 请在 root 或 sudo 用户下执行
# 替换 <YOUR_PUBLIC_KEY> 为实际公钥

PUBKEY="<YOUR_PUBLIC_KEY>"

apt update && apt upgrade -y
apt install -y curl nginx rsync
curl -fsSL https://get.docker.com | bash
useradd -m -s /bin/bash deploy
usermod -aG docker deploy
mkdir -p ~deploy/.ssh
echo "$PUBKEY" > ~deploy/.ssh/authorized_keys
chmod 600 ~deploy/.ssh/authorized_keys
chown -R deploy:deploy ~deploy/.ssh
mkdir -p /opt/ai-digital-card-preview
chown -R deploy:deploy /opt/ai-digital-card-preview
ufw allow 22/tcp && ufw allow 80/tcp && ufw --force enable
echo "✅ 预览服务器初始化完成"
```

### 9.2 Secrets 配置 (一鍵完成)

```bash
gh secret set PREVIEW_SSH_HOST --body "$(cat PREVIEW_SSH_HOST.txt)"
gh secret set PREVIEW_SSH_USER --body "deploy"
gh secret set PREVIEW_SSH_KEY < ./preview-deploy
```

### 9.3 端到端验证 (部署后)

```bash
PR_NUMBER=42
echo "=== 前端 ==="
curl -sI "https://preview-${PR_NUMBER}.ai-card.com" | head -3
echo ""
echo "=== 安全头 ==="
curl -sI "https://preview-${PR_NUMBER}.ai-card.com" | grep -iE "strict-transport-security|x-frame-options|x-content-type-options"
echo ""
echo "=== API 健康 ==="
curl -s "https://preview-${PR_NUMBER}.ai-card.com/health"
echo ""
echo "=== 服务器验证 ==="
ssh deploy@<服务器IP> "docker ps --filter 'label=com.ai-card.preview=true' --format 'table {{.Names}}\t{{.Status}}'"
```

### 9.4 监控建议

| 监控项 | 工具/方式 | 告警阈值 |
|--------|----------|---------|
| 磁盘使用率 | Prometheus Node Exporter | > 80% |
| 内存使用率 | Prometheus Node Exporter | > 80% |
| Docker 容器状态 | docker events / Healthcheck | 容器退出 |
| Nginx 状态 | Nginx status module | 5xx > 1% |
| 预览环境数量 | 自定义脚本 | > 50 (建议人工清理) |

---

## 最终签署

| 检查阶段 | 负责人 | 完成日期 | 签名 |
|---------|--------|---------|------|
| DNS 配置 | (待填写) | (待填写) | (待填写) |
| GitHub Secrets | (待填写) | (待填写) | (待填写) |
| 服务器初始化 | (待填写) | (待填写) | (待填写) |
| CI 工作流验证 | (待填写) | (待填写) | (待填写) |
| 功能验证 | (待填写) | (待填写) | (待填写) |
| 清理验证 | (待填写) | (待填写) | (待填写) |

> **全部检查项通过后，Preview Deploy 即可正式投入使用。**
>
> 如有疑问请联系 DevOps 团队。
> **最后更新**: 2026-07-02
