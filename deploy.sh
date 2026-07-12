#!/bin/bash
# AI数智名片 一键构建+部署脚本
# 用法: bash deploy.sh [env]
#   env: dev (默认) | staging | prod

set -e

ENV=${1:-dev}
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

echo "============================================"
echo " AI数智名片 部署脚本"
echo " 环境: $ENV"
echo " 时间: $TIMESTAMP"
echo "============================================"

# Step 1: 检查环境
echo ""
echo "[1/4] 检查环境..."
command -v node >/dev/null 2>&1 || { echo "❌ 需要Node.js"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ 需要npm"; exit 1; }
command -v python >/dev/null 2>&1 || { echo "❌ 需要Python"; exit 1; }

echo "  ✅ Node $(node -v)"
echo "  ✅ npm $(npm -v)"
echo "  ✅ Python $(python --version)"

# Step 2: 后端部署
echo ""
echo "[2/4] 部署后端..."
cd "$ROOT_DIR/backend"
if [ ! -d "venv" ]; then
  python -m venv venv
fi
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
pip install -r requirements.txt -q 2>/dev/null || pip install uvicorn fastapi sqlalchemy -q

if [ "$ENV" = "prod" ] || [ "$ENV" = "staging" ]; then
  echo "  生产模式: 启动uvicorn服务"
  nohup uvicorn app.main:app --host 0.0.0.0 --port 8201 --workers 2 > ../logs/backend_${TIMESTAMP}.log 2>&1 &
  echo "  ✅ 后端已启动 (PID: $!)"
else
  echo "  开发模式: 后端手动启动 → uvicorn app.main:app --port 8201 --reload"
fi

# Step 3: 前端构建
echo ""
echo "[3/4] 前端构建..."
cd "$ROOT_DIR/miniapp"
echo "  微信小程序: 请在微信开发者工具中手动上传"
echo "  ✅ 前端代码已就绪"

# Step 4: 健康检查
echo ""
echo "[4/4] 健康检查..."
sleep 2
curl -s http://localhost:8201/health > /dev/null 2>&1 && \
  echo "  ✅ 后端健康检查通过 (localhost:8201)" || \
  echo "  ⚠️ 健康检查未通过 (服务可能还在启动中)"

echo ""
echo "============================================"
echo " ✅ 部署完成"
echo " 后端: http://localhost:8201"
echo " 前端: 微信开发者工具导入 miniapp/"
echo " API文档: http://localhost:8201/docs"
echo "============================================"
