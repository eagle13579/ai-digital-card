#!/bin/bash
# ═══════════════════════════════════════════════════════
# AI数智名片 — 蓝绿部署健康检查脚本
# ═══════════════════════════════════════════════════════
# 检查指定端口的后端/health 是否正常响应
# 用法:
#   ./deploy/bluegreen/health_check.sh              # 检查当前活跃后端 (端口自动检测)
#   ./deploy/bluegreen/health_check.sh --port 8202  # 检查指定端口
#   ./deploy/bluegreen/health_check.sh --all        # 检查蓝绿两套
#   ./deploy/bluegreen/health_check.sh --wait 60    # 等待最多 60s 直到健康
# ═══════════════════════════════════════════════════════
set -euo pipefail

BLUE_PORT=8201
GREEN_PORT=8202
HEALTH_PATH="/health"

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
err()  { log "❌ ERROR: $*"; exit 1; }

# ── 健康检查单个端口 ───────────────────────────────
check_port() {
    local port="$1"
    local url="http://127.0.0.1:${port}${HEALTH_PATH}"
    if curl -sf "$url" >/dev/null 2>&1; then
        log "✅ 端口 ${port}: 健康"
        return 0
    else
        log "❌ 端口 ${port}: 不健康"
        return 1
    fi
}

# ── 等待健康检查通过 ──────────────────────────────
wait_for_health() {
    local port="$1"
    local timeout="${2:-60}"
    local url="http://127.0.0.1:${port}${HEALTH_PATH}"
    log "⏳ 等待端口 ${port} 就绪 (${timeout}s 超时)..."
    for i in $(seq 1 $((timeout / 5))); do
        if curl -sf "$url" >/dev/null 2>&1; then
            log "✅ 端口 ${port}: 就绪 (第 ${i} 次检查)"
            return 0
        fi
        log "  等待中... ($((timeout - i*5))s 剩余)"
        sleep 5
    done
    err "端口 ${port} 健康检查超时 (${timeout}s)"
}

# ── 获取当前活跃后端 ──────────────────────────────
get_active_env() {
    # 通过 Nginx 当前配置判断活跃环境
    local nginx_conf="/etc/nginx/conf.d/bluegreen.conf"
    if [[ -f "$nginx_conf" ]]; then
        if grep -q "backend_blue" "$nginx_conf" 2>/dev/null | grep -v "map\|upstream" | head -1; then
            # 更精确：检查 map 块中的 default 值
            local active=$(grep -oP 'default\s+\K(backend_blue|backend_green)' "$nginx_conf" 2>/dev/null || echo "unknown")
            echo "$active"
        else
            echo "unknown"
        fi
    else
        # 通过健康端点推断
        if check_port "$BLUE_PORT" >/dev/null 2>&1; then
            echo "backend_blue"
        elif check_port "$GREEN_PORT" >/dev/null 2>&1; then
            echo "backend_green"
        else
            echo "unknown"
        fi
    fi
}

# ── 主入口 ─────────────────────────────────────────
main() {
    local port="" wait="false" all="false" timeout=60

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --port|-p)    shift; port="$1" ;;
            --wait|-w)    shift; timeout="${1:-60}"; wait="true" ;;
            --all|-a)     all="true" ;;
            --help|-h)    echo "用法: $0 [--port <端口>|--all] [--wait <秒>]"; exit 0 ;;
            *)            err "未知参数: $1" ;;
        esac
        shift
    done

    if [[ "$all" == "true" ]]; then
        log "=== 检查蓝绿两套环境 ==="
        check_port "$BLUE_PORT"
        check_port "$GREEN_PORT"
        return 0
    fi

    if [[ -n "$port" ]]; then
        if [[ "$wait" == "true" ]]; then
            wait_for_health "$port" "$timeout"
        else
            check_port "$port"
        fi
        return $?
    fi

    # 默认：检查当前活跃环境和备用环境
    local active
    active=$(get_active_env)
    log "当前活跃后端: ${active:-unknown}"
    check_port "$BLUE_PORT"
    check_port "$GREEN_PORT"
}

main "$@"
