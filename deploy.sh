#!/bin/bash
# AI数字名片 — 一键本地部署启动脚本
# 用法: bash deploy.sh [dev|prod]

set -e

MODE="${1:-dev}"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo " AI数字名片 一键部署"
echo " 模式: $MODE"
echo " 目录: $PROJECT_DIR"
echo "========================================"

echo "[1/4] 检查环境..."
command -v python >/dev/null 2>&1 || { echo "需要Python"; exit 1; }
python -c "import fastapi" 2>/dev/null || { echo "安装依赖..."; pip install -q -r "$PROJECT_DIR/backend/requirements.txt"; }

echo "[2/4] 数据库初始化..."
cd "$PROJECT_DIR/backend"

echo "[3/4] 环境配置..."
[ ! -f .env ] && cp .env.example .env 2>/dev/null || true

echo "[4/4] 启动服务..."
PORT="${PORT:-8002}"
echo "  端口: $PORT"
echo "  健康: http://localhost:$PORT/health"
echo "  页面: http://localhost:$PORT/"
python run.py
