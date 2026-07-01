#!/bin/bash
# 开发环境启动脚本

echo "===== AI数智名片 开发环境 ====="

cd "$(dirname "$0")"

# 检查 Python
if ! command -v python &>/dev/null; then
    echo "❌ Python 未安装"
    exit 1
fi

# 安装依赖
echo "[1/2] 安装依赖..."
cd backend
pip install -r requirements.txt -q

# 创建数据目录
mkdir -p data uploads

# 启动后端
echo "[2/2] 启动后端 (端口 8201)..."
echo "访问: http://localhost:8201"
python main.py
