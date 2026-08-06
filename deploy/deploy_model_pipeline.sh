#!/bin/bash
# ============================================================
# AI数智名片 — 自动ML模型部署管线 (供 CI/CD 调用)
#
# 用法:
#   ./deploy/deploy_model_pipeline.sh <model_name>
#   ./deploy/deploy_model_pipeline.sh <model_name> --rollback
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOY_LOG="${SCRIPT_DIR}/deploy_model.log"
DEPLOY_SCRIPT="${SCRIPT_DIR}/deploy_model.py"

# ---- 工具函数 ----
log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
err()  { log "❌ ERROR: $*"; exit 1; }

# ---- 前置检查 ----
preflight_check() {
    command -v python3 >/dev/null 2>&1 || python3="python"
    command -v "${python3:-python}" >/dev/null 2>&1 || err "python3 未安装"
    [[ -f "$DEPLOY_SCRIPT" ]] || err "deploy_model.py 不存在: $DEPLOY_SCRIPT"
    mkdir -p "$(dirname "$DEPLOY_LOG")"
}

# ---- 部署入口 ----
main() {
    preflight_check

    local model_name="${1:-}"
    [[ -n "$model_name" ]] || {
        echo "用法: $0 <model_name> [--rollback]"
        echo ""
        echo "示例:"
        echo "  $0 intent_classifier"
        echo "  $0 intent_classifier --rollback"
        exit 1
    }

    shift
    local extra_args="$*"

    log "=========================================="
    log "ML 模型部署管线启动"
    log "  模型: ${model_name}"
    log "  模式: ${extra_args:-auto}"
    log "  日志: ${DEPLOY_LOG}"
    log "=========================================="

    # 执行部署, 同时输出到终端和日志文件
    local start_time
    start_time=$(date +%s)

    if [[ "$extra_args" == *"--rollback"* ]]; then
        # 回滚模式
        python3 "$DEPLOY_SCRIPT" promote "$model_name" --rollback 2>&1 | tee -a "$DEPLOY_LOG"
    else
        # 自动模式 (默认)
        python3 "$DEPLOY_SCRIPT" promote "$model_name" --auto 2>&1 | tee -a "$DEPLOY_LOG"
    fi

    local exit_code="${PIPESTATUS[0]}"
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # 记录部署日志
    if [[ $exit_code -eq 0 ]]; then
        log "✅ 部署成功! 耗时 ${duration}s" | tee -a "$DEPLOY_LOG"
    else
        log "❌ 部署失败 (退出码: ${exit_code})" | tee -a "$DEPLOY_LOG"
        exit $exit_code
    fi

    # 清理旧日志 (保留最近 100 条)
    local log_lines
    log_lines=$(wc -l < "$DEPLOY_LOG" 2>/dev/null || echo "0")
    if [[ "$log_lines" -gt 5000 ]]; then
        tail -n 2000 "$DEPLOY_LOG" > "${DEPLOY_LOG}.tmp" && mv "${DEPLOY_LOG}.tmp" "$DEPLOY_LOG"
        log "日志已裁剪 (保留最近 2000 行)"
    fi

    log "=========================================="
    log "部署管线完成"
    log "=========================================="
}

main "$@"
