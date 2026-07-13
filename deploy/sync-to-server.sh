#!/bin/bash
# AI数智名片 服务器同步脚本
# 用法: bash deploy/sync-to-server.sh
# 将本地最新代码同步到 47.116.116.87

set -e

SERVER="root@47.116.116.87"
REMOTE_DIR="/var/www/ai-digital-card"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "🔄 同步代码到 $SERVER:$REMOTE_DIR ..."
echo "  本地目录: $LOCAL_DIR"

# Step 1: 同步 backend（排除不必要的目录）
echo ""
echo "[1/5] 同步 backend/ ..."
rsync -avz --delete --progress \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='venv' \
  --exclude='.coverage' \
  --exclude='.benchmarks' \
  --exclude='*.pyc' \
  "$LOCAL_DIR/backend/" "$SERVER:$REMOTE_DIR/backend/"

# Step 2: 同步 miniapp（小程序代码，服务器上不需要运行，但保留参考）
echo ""
echo "[2/5] 同步 miniapp/ ..."
rsync -avz --delete --progress \
  --exclude='node_modules' \
  --exclude='.git' \
  "$LOCAL_DIR/miniapp/" "$SERVER:$REMOTE_DIR/miniapp/"

# Step 3: 同步 deploy/ 配置
echo ""
echo "[3/5] 同步 deploy/ 配置 ..."
rsync -avz --progress \
  "$LOCAL_DIR/deploy/card.liankebao.top.nginx.conf" \
  "$LOCAL_DIR/deploy/ai-digital-card.service" \
  "$SERVER:$REMOTE_DIR/deploy/"

# Step 4: 同步 .env.production
echo ""
echo "[4/5] 同步 .env.production ..."
rsync -avz --progress \
  "$LOCAL_DIR/deploy/.env.production" "$SERVER:$REMOTE_DIR/backend/.env.production"

echo ""
echo "✅ 同步完成！"
echo ""
echo "接下来 SSH 到服务器执行:"
echo "  1. cd $REMOTE_DIR/backend"
echo "  2. source venv/bin/activate && pip install -r requirements.txt -q"
echo "  3. sudo cp deploy/ai-digital-card.service /etc/systemd/system/"
echo "  4. sudo systemctl daemon-reload && sudo systemctl enable --now ai-digital-card"
echo "  5. sudo nginx -t && sudo systemctl reload nginx"
