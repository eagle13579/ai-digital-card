#!/usr/bin/env bash
# ============================================================
# Mac mini — MLX 推理服务一键启动脚本 (v1.0)
# 用途: 启动 MLX OpenAI 兼容推理服务于 127.0.0.1:9091
#       供 mac_mini_models_report.py 上报模型列表
# 用法: bash mac_start_mlx_server.sh [模型名]
# 默认模型: Qwen/Qwen2.5-0.5B-Instruct (可换 Llama-3.2-3B 等)
# ============================================================
set -e

MODEL="${1:-Qwen/Qwen2.5-0.5B-Instruct}"
PORT="${PORT:-9091}"
LOG="${HOME}/mlx_server.log"

echo "▶ 启动 MLX 推理服务..."
echo "  模型: ${MODEL}"
echo "  端口: ${PORT}"

# 1. 确认 mlx-lm 已安装
if ! python3 -c "import mlx_lm" 2>/dev/null; then
    echo "  检测到 mlx-lm 未安装，正在安装 (pip install mlx-lm)..."
    pip3 install -q mlx-lm 2>&1 | tail -3
fi

# 2. 若已有进程占用 9091 则提示
if lsof -i :${PORT} >/dev/null 2>&1; then
    echo "⚠️ 端口 ${PORT} 已被占用，检查是否已在运行:"
    lsof -i :${PORT} | head -5
    echo "  若需重启: kill 上述进程后重新运行本脚本"
    exit 1
fi

# 3. 后台启动 (nohup 防 SSH 断开被杀)
nohup python3 -m mlx_lm.server --model "${MODEL}" --port "${PORT}" \
    > "${LOG}" 2>&1 &

PID=$!
echo "✅ MLX 服务已后台启动 (PID=${PID})"
echo "  日志: ${LOG}"

# 4. 等待就绪 (最多 60 秒)
for i in $(seq 1 12); do
    sleep 5
    if curl -s http://127.0.0.1:${PORT}/v1/models >/dev/null 2>&1; then
        echo "🎉 MLX 服务就绪: http://127.0.0.1:${PORT}/v1/models"
        curl -s http://127.0.0.1:${PORT}/v1/models | python3 -m json.tool 2>/dev/null | head -20
        exit 0
    fi
    echo "  等待模型加载... (${i}/12)"
done

echo "⚠️ 服务未就绪，请查看日志: tail -50 ${LOG}"
exit 1
