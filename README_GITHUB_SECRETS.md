# AI数字名片 — GitHub Secrets 配置指南

以下是为 14 个 GitHub Actions 工作流需要配置的密钥。
在 GitHub 仓库 → Settings → Secrets and variables → Actions 中配置。

---
## 需要配置的密钥清单
| 密钥名 | 来源 | 用途 | 涉及workflow |
|--------|------|------|-------------|
| `DEEPSEEK_API_KEY` | 已有 (.env) | CI/CD 认证 | learning-cron.yml |
| `DEPLOY_HOST` | 需自行确认 | CI/CD 认证 | bluegreen-deploy.yml · canary-ci.yml · deploy-ssh.yml |
| `DEPLOY_SSH_KEY` | 需自行确认 | CI/CD 认证 | bluegreen-deploy.yml · canary-ci.yml · deploy-ssh.yml |
| `DEPLOY_USER` | 需自行确认 | CI/CD 认证 | bluegreen-deploy.yml · canary-ci.yml · deploy-ssh.yml |
| `GITHUB_TOKEN` | 需自行确认 | CI/CD 认证 | bluegreen-deploy.yml · canary-ci.yml · canary.yml |
| `KUBE_CONFIG` | 需自行确认 | CI/CD 认证 | canary.yml |
| `PREVIEW_SSH_HOST` | 需自行确认 | CI/CD 认证 | preview.yml |
| `PREVIEW_SSH_KEY` | 需自行确认 | CI/CD 认证 | preview.yml |
| `PREVIEW_SSH_USER` | 需自行确认 | CI/CD 认证 | preview.yml |
| `PREVIOUS_STABLE_IMAGE` | 需自行确认 | CI/CD 认证 | canary.yml |

---
## 核心 workflow 状态

| Workflow | 状态 | 说明 |
|----------|------|------|
| a11y.yml | ✅ 无密钥依赖 | a11y |
| bluegreen-deploy.yml | ❌ 需密钥 | ═══════════════════════════════════════════════════════════════════ |
| canary-ci.yml | ❌ 需密钥 | ─────────────────────────────────────────────────────── |
| canary.yml | ❌ 需密钥 | ───────────────────────────────────────────────────── |
| ci.yml | ✅ 无密钥依赖 | ────────────────────────────────────────────── |
| deploy-model.yml | ✅ 无密钥依赖 | ============================================================ |
| deploy-ssh.yml | ❌ 需密钥 | ────────────────────────────────────────────── |
| deploy.yml | ❌ 需密钥 | ────────────────────────────────────────────── |
| e2e.yml | ✅ 无密钥依赖 | ────────────────────────────────────────────── |
| learning-cron.yml | ❌ 需密钥 | ────────────────────────────────────────────── |
| performance.yml | ✅ 无密钥依赖 | ────────────────────────────────────────────── |
| preview.yml | ❌ 需密钥 | ─────────────────────────────────────────────────────── |
| rollback.yml | ❌ 需密钥 | ─────────────────────────────────────────────────────── |
| security-scan.yml | ✅ 无密钥依赖 | ────────────────────────────────────────────── |