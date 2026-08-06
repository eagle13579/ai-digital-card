#!/bin/bash
# ──────────────────────────────────────────────
# 本地部署脚本 — AI数字名片
# 通过 rsync + SSH (密码认证) 推送前端 dist 到服务器
# 用法:
#   export DEPLOY_HOST="47.116.116.87"
#   export DEPLOY_USERNAME="root"
#   export DEPLOY_PASSWORD="your-password"
#   bash deploy-local.sh
#
# 也可以直接编辑下方变量
# ──────────────────────────────────────────────
set -euo pipefail

# ── 配置（可从环境变量覆盖）────────────────────────
HOST="${DEPLOY_HOST:-47.116.116.87}"
USERNAME="${DEPLOY_USERNAME:-root}"
PASSWORD="${DEPLOY_PASSWORD:-}"
REMOTE_DIST_DIR="/var/www/ai-digital-card/frontend/dist"
SERVICE_NAME="ai-digital-card-8201"
HEALTH_URL="http://127.0.0.1:8201/health"

# ── 颜色输出 ────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ── 前置检查 ────────────────────────────────────────
if ! command -v rsync &>/dev/null; then
  err "rsync 未安装，请先安装 rsync"
  exit 1
fi

if ! command -v sshpass &>/dev/null; then
  err "sshpass 未安装，请先安装 sshpass"
  err "  macOS: brew install hudochenkov/sshpass/sshpass"
  err "  Ubuntu: apt install sshpass"
  err "  Windows: 可从 https://sourceforge.net/projects/sshpass/ 下载"
  exit 1
fi

if [ -z "$PASSWORD" ]; then
  err "DEPLOY_PASSWORD 未设置！"
  err "请通过环境变量或直接编辑脚本设置密码"
  exit 1
fi

SSHPASS_OPTIONS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$PROJECT_DIR/frontend"
DIST_DIR="$FRONTEND_DIR/dist"

# ── Step 1: 构建前端 ────────────────────────────────
echo ""
echo "============================================"
echo " AI数字名片 — 本地部署脚本"
echo "============================================"
echo ""

info "[1/4] 构建前端 (Vite)..."

cd "$FRONTEND_DIR"

if [ ! -f "package.json" ]; then
  err "未找到 frontend/package.json，请确认在项目根目录运行"
  exit 1
fi

if [ ! -d "node_modules" ]; then
  info "安装依赖..."
  npm ci
fi

npm run build
ok "前端构建完成: $DIST_DIR"

# ── Step 2: rsync 到服务器 ─────────────────────────
info "[2/4] 同步 dist 到服务器..."
echo "     目标: $USERNAME@$HOST:$REMOTE_DIST_DIR"

SSHPASS="$PASSWORD" rsync -avz --delete \
  $SSHPASS_OPTIONS \
  -e "sshpass -e ssh $SSHPASS_OPTIONS" \
  "$DIST_DIR/" \
  "$USERNAME@$HOST:$REMOTE_DIST_DIR"

ok "前端文件同步完成"

# ── Step 3: 检测 backend 变更 + 重启 ────────────────
info "[3/4] 检测 backend 变更..."

# 通过 git diff 检测上一次提交中 backend/ 是否有变更
BACKEND_CHANGED=false
if git -C "$PROJECT_DIR" rev-parse --git-dir &>/dev/null; then
  # 如果是 git 仓库，检查 HEAD~1 对比 HEAD
  if git -C "$PROJECT_DIR" diff --name-only HEAD~1 HEAD 2>/dev/null | grep -q "^backend/"; then
    BACKEND_CHANGED=true
  fi
  # 也检查 working tree 是否有未提交的 backend 变更
  if git -C "$PROJECT_DIR" diff --name-only HEAD 2>/dev/null | grep -q "^backend/"; then
    BACKEND_CHANGED=true
  fi
fi

if [ "$BACKEND_CHANGED" = true ]; then
  info "backend 有变更，重启后端服务..."
  SSHPASS="$PASSWORD" sshpass -e ssh $SSHPASS_OPTIONS "$USERNAME@$HOST" \
    "systemctl restart ${SERVICE_NAME}.service"
  ok "后端服务已重启: $SERVICE_NAME"
  sleep 3
else
  warn "backend 无变更，跳过服务重启"
fi

# ── Step 4: 健康检查 ────────────────────────────────
info "[4/4] 健康检查..."

HTTP_CODE=$(SSHPASS="$PASSWORD" sshpass -e ssh $SSHPASS_OPTIONS "$USERNAME@$HOST" \
  "curl -s -o /dev/null -w '%{http_code}' $HEALTH_URL" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
  ok "健康检查通过 (HTTP $HTTP_CODE)"
  echo ""
  echo "============================================"
  echo -e " ${GREEN}✅ 部署成功！${NC}"
  echo "============================================"
else
  err "健康检查失败 (HTTP $HTTP_CODE)"
  err "请手动检查服务器服务状态:"
  err "  ssh $USERNAME@$HOST 'systemctl status ${SERVICE_NAME}.service'"
  exit 1
fi
