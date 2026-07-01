#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# learning_cron.sh — 在线学习cron定时器包装脚本
# ════════════════════════════════════════════════════════════
# 用法:
#   bash scripts/cron/learning_cron.sh              # 单次检查
#   bash scripts/cron/learning_cron.sh --force      # 强制学习
#   bash scripts/cron/learning_cron.sh --watch      # 持续监视
#
# 配合 cron 使用 (每天凌晨2点):
#   0 2 * * * cd /path/to/project && bash backend/scripts/cron/learning_cron.sh >> /var/log/learning_cron.log 2>&1
#
# 配合 systemd timer / GitHub Actions 使用
# ════════════════════════════════════════════════════════════

set -euo pipefail

# ── 项目根目录 (脚本所在目录的父级的父级) ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# ── 配置 ──
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/learning_cron_$(date '+%Y%m%d').log"
PYTHON="${PYTHON:-python}"

# ── 创建日志目录 ──
mkdir -p "$LOG_DIR"

# ── 日志函数 ──
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# ── 主逻辑 ──
main() {
    log "=========================================="
    log "在线学习 cron 启动"
    log "工作目录: $BACKEND_DIR"
    log "参数: $*"

    # 检查 Python 模块是否存在
    MODULE="app.ai.cron.learning_cron"
    if ! cd "$BACKEND_DIR" && $PYTHON -c "import $MODULE" 2>/dev/null; then
        log "[ERROR] 模块 $MODULE 不存在或语法错误，跳过本次执行"
        exit 1
    fi

    # 执行学习脚本
    cd "$BACKEND_DIR"

    ARGS=()
    if [ $# -gt 0 ]; then
        ARGS=("$@")
    else
        ARGS=("--once")
    fi

    log "执行: $PYTHON -m $MODULE ${ARGS[*]}"
    if $PYTHON -m "$MODULE" "${ARGS[@]}" 2>&1 | tee -a "$LOG_FILE"; then
        log "[OK] 在线学习脚本执行成功"
    else
        local exit_code=$?
        log "[ERROR] 在线学习脚本执行失败 (exit=$exit_code)"
        return $exit_code
    fi
}

main "$@"
