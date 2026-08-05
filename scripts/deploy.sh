#!/bin/bash
# =============================================
# 部署脚本 - AI数智名片
# 三件事: 同步 -> 重启 -> 验证
# 用法: bash scripts/deploy.sh
# =============================================

set -e

SERVER="root@47.116.116.87"
PROJECT_DIR="/var/www/ai-digital-card"
SERVICE="ai-digital-card"
DOMAIN="https://card.liankebao.top"

echo "========================================"
echo "  AI数智名片 部署脚本"
echo "  版本: $(git log --oneline -1 2>/dev/null || echo 'unknown')"
echo "========================================"

# ---- Step 1: 同步代码到服务器 ----
echo ""
echo "=== [1/3] 同步代码到服务器 ==="
rsync -avz --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.git' \
  --exclude 'venv' \
  --exclude 'node_modules' \
  --exclude 'data/*.db' \
  --exclude '.env' \
  ./backend/ $SERVER:$PROJECT_DIR/backend/

echo "✅ 同步完成"

# ---- Step 2: 重启服务 ----
echo ""
echo "=== [2/3] 重启服务 ==="
ssh $SERVER "systemctl restart $SERVICE"
sleep 3

# 检查服务状态
STATUS=$(ssh $SERVER "systemctl is-active $SERVICE" 2>/dev/null)
if [ "$STATUS" != "active" ]; then
  echo "❌ 服务启动失败 (状态: $STATUS)"
  ssh $SERVER "systemctl status $SERVICE --no-pager | tail -10"
  exit 1
fi
echo "✅ 服务运行中 (active)"

# ---- Step 3: 验证核心路由 ----
echo ""
echo "=== [3/3] 验证核心路由 ==="
ALL_OK=true

verify() {
  local path=$1
  local expect_not_404=$2
  local code=$(curl -s -o /dev/null -w '%{http_code}' "${DOMAIN}${path}" 2>/dev/null || echo "000")
  
  if [ "$code" = "404" ]; then
    echo "❌ $path -> $code (路由未注册)"
    ALL_OK=false
  elif [ "$code" = "000" ]; then
    echo "❌ $path -> 连接失败"
    ALL_OK=false
  else
    echo "✅ $path -> $code"
  fi
}

verify "/api/health"
verify "/api/brochures"
verify "/api/brochures/visible"
verify "/api/users/me"
verify "/api/tags/me"
verify "/api/match/recommend?page=1&size=10"

echo ""
if [ "$ALL_OK" = true ]; then
  echo "✅ 全部路由验证通过"
else
  echo "⚠️  部分路由异常，请检查"
fi

echo "========================================"
echo "  部署完成"
echo "  版本: $(git log --oneline -1 2>/dev/null || echo 'unknown')"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
