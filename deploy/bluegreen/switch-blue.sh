#!/bin/bash
# ═══════════════════════════════════════════════════════
# AI数智名片 — 蓝绿切换：切换到蓝色环境 (Blue)
# ═══════════════════════════════════════════════════════
# 将 Nginx 流量从绿色环境切回蓝色环境
# 蓝色 = 端口 8201 (默认生产环境)
# ═══════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
NGINX_CONF="/etc/nginx/conf.d/bluegreen.conf"
ROLLBACK_DIR="${PROJECT_ROOT}/deploy/rollback"
BLUE_PORT=8201

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
err()  { log "❌ ERROR: $*"; exit 1; }

# ── 前置检查 ──────────────────────────────────────
preflight() {
    command -v curl >/dev/null 2>&1      || err "curl 未安装"
    command -v nginx >/dev/null 2>&1     || err "nginx 未安装"
    [[ -f "$NGINX_CONF" ]]               || err "Nginx 配置不存在: $NGINX_CONF"
    mkdir -p "$ROLLBACK_DIR"
}

# ── 检查蓝色环境健康 ──────────────────────────────
health_check_blue() {
    log "🏥 检查蓝色环境 (端口 ${BLUE_PORT})..."
    for i in $(seq 1 12); do
        if curl -sf "http://127.0.0.1:${BLUE_PORT}/health" >/dev/null 2>&1; then
            log "✅ 蓝色环境就绪 (第 ${i} 次检查)"
            return 0
        fi
        log "⏳ 等待蓝色环境... ($((60 - i*5))s 剩余)"
        sleep 5
    done
    err "蓝色环境健康检查失败，切换中止"
}

# ── 切换 Nginx 配置到蓝色 ──────────────────────────
switch_to_blue() {
    log "=== 切换流量 → 蓝色环境 ==="

    # 备份当前配置
    cp "$NGINX_CONF" "${ROLLBACK_DIR}/bluegreen.conf.bak.$(date +%Y%m%d_%H%M%S)"

    # 修改 map 块中的 default 值为 backend_blue
    # 使用 sed 替换 map 块的 default 行
    sed -i 's/^\(    default \)backend_green;/\1backend_blue;/' "$NGINX_CONF"

    # 验证 Nginx 配置
    nginx -t || err "Nginx 配置测试失败"

    # 重载 Nginx
    nginx -s reload || err "Nginx 重载失败"
    log "✅ 流量已切换到蓝色环境 (端口 ${BLUE_PORT})"
}

# ── 验证切换 ──────────────────────────────────────
verify_switch() {
    log "🔍 验证切换结果..."
    sleep 2
    local active_env
    active_env=$(grep -oP 'default\s+\K(backend_blue|backend_green)' "$NGINX_CONF" 2>/dev/null || echo "unknown")
    if [[ "$active_env" == "backend_blue" ]]; then
        log "✅ 验证通过: Nginx 当前指向 backend_blue"
    else
        err "验证失败: Nginx 指向 ${active_env}，期望 backend_blue"
    fi
}

# ── 主流程 ─────────────────────────────────────────
main() {
    log "🔵 === 切换到蓝色环境 (Blue) ==="
    preflight
    health_check_blue
    switch_to_blue
    verify_switch
    log "🎉 切换完成！当前活跃: 蓝色 (端口 ${BLUE_PORT})"
    log "   绿色容器可以安全移除: docker rm -f ai-digital-card-green"
}

main "$@"
