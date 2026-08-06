#!/bin/bash
# gaia_flywheel_wrapper.sh — 盖娅进化飞轮服务器调度包装
# 由 systemd timer 每小时调用，执行一轮进化循环（知识聚合→训练→权重部署）
# 日志: /var/www/ai-digital-card/backend/logs/gaia_flywheel.log

set -uo pipefail

cd /var/www/ai-digital-card/backend || exit 1

LOG_DIR="/var/www/ai-digital-card/backend/logs"
mkdir -p "$LOG_DIR"

# 使用项目 venv 的 python（含所有依赖）
PYTHON="/var/www/ai-digital-card/backend/venv/bin/python"

if [ ! -x "$PYTHON" ]; then
    # 回退到系统 python3
    PYTHON="python3"
fi

# 加载 .env 环境变量（命令行运行不会自动加载，systemd 服务才会）
if [ -f "/var/www/ai-digital-card/backend/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "/var/www/ai-digital-card/backend/.env"
    set +a
fi

echo "=== [$(date '+%Y-%m-%d %H:%M:%S')] 盖娅进化飞轮启动 ===" >> "$LOG_DIR/gaia_flywheel.log"

# 1. 运行进化飞轮（单次进化周期）
if "$PYTHON" -m app.ai.gaia_flywheel >> "$LOG_DIR/gaia_flywheel.log" 2>&1; then
    echo "  ✓ 进化飞轮完成" >> "$LOG_DIR/gaia_flywheel.log"
else
    echo "  ✗ 进化飞轮失败 (exit=$?)" >> "$LOG_DIR/gaia_flywheel.log"
fi

echo "---" >> "$LOG_DIR/gaia_flywheel.log"
exit 0
