#!/bin/bash
# ═══════════════════════════════════════════════════════
# AI数智名片 — 蓝绿切换：切换到绿色环境 (Green)
# ═══════════════════════════════════════════════════════
# 将 Nginx 流量从蓝色环境切到绿色环境
# 绿色 = 端口 8202 (新版本环境)
# ═══════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
NGINX_CONF="/etc/nginx/conf.d/bluegreen.conf"
ROLLBACK_DIR="${PROJECT_ROOT}/deploy/rollback"
GREEN_PORT=8202

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
err()  { log "❌ ERROR: $*"; exit 1; }

# ── 前置检查 ──────────────────────────────────────
preflight() {
    command -v curl >/dev/null 2>&1      || err "curl 未安装"
    command -v nginx >/dev/null 2>&1     || err "nginx 未安装"
    [[ -f "$NGINX_CONF" ]]               || err "Nginx 配置不存在: $NGINX_CONF"
    mkdir -p "$ROLLBACK_DIR"
}

# ── 检查绿色环境健康 ──────────────────────────────
health_check_green() {
    log "🏥 检查绿色环境 (端口 ${GREEN_PORT})..."
    for i in $(seq 1 12); do
        if curl -sf "http://127.0.0.1:${GREEN_PORT}/health" >/dev/null 2>&1; then
            log "✅ 绿色环境就绪 (第 ${i} 次检查)"
            return 0
        fi
        log "⏳ 等待绿色环境... ($((60 - i*5))s 剩余)"
        sleep 5
    done
    err "绿色环境健康检查失败，切换中止"
}

# ── 切换 Nginx 配置到绿色 ──────────────────────────
switch_to_green() {
    log "=== 切换流量 → 绿色环境 ==="

    # 备份当前配置
    cp "$NGINX_CONF" "${ROLLBACK_DIR}/bluegreen.conf.bak.$(date +%Y%m%d_%H%M%S)"

    # 修改 map 块中的 default 值为 backend_green
    sed -i 's/^\(    default \)backend_blue;/\1backend_green;/' "$NGINX_CONF"

    # 验证 Nginx 配置
    nginx -t || err "Nginx 配置测试失败"

    # 重载 Nginx
    nginx -s reload || err "Nginx 重载失败"
    log "✅ 流量已切换到绿色环境 (端口 ${GREEN_PORT})"
}

# ── 验证切换 ──────────────────────────────────────
verify_switch() {
    log "🔍 验证切换结果..."
    sleep 2
    local active_env
    active_env=$(grep -oP 'default\s+\K(backend_blue|backend_green)' "$NGINX_CONF" 2>/dev/null || echo "unknown")
    if [[ "$active_env" == "backend_green" ]]; then
        log "✅ 验证通过: Nginx 当前指向 backend_green"
    else
        err "验证失败: Nginx 指向 ${active_env}，期望 backend_green"
    fi
}

# ── 主流程 ─────────────────────────────────────────
main() {
    log "🟢 === 切换到绿色环境 (Green) ==="
    preflight
    health_check_green
    switch_to_green
    verify_switch
    log "🎉 切换完成！当前活跃: 绿色 (端口 ${GREEN_PORT})"
    log "   蓝色容器可以保留作为回滚: docker rm -f ai-digital-card-blue (如需要)"
}

main "$@"
