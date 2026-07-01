#!/bin/bash
# AI数智名片 - 蓝绿部署脚本
set -euo pipefail

PROJECT_ROOT="/opt/ai-digital-card"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
HEALTH_URL="http://localhost:8201/health"
ROLLBACK_DIR="${PROJECT_ROOT}/deploy/rollback"
BACKEND_PORT=8201; GREEN_PORT=8202

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
err()  { log "❌ ERROR: $*"; exit 1; }

preflight_check() {
    command -v docker >/dev/null 2>&1 || err "docker 未安装"
    command -v curl   >/dev/null 2>&1 || err "curl 未安装"
    mkdir -p "$ROLLBACK_DIR"
}

health_check() {
    local port="${1:-$BACKEND_PORT}"
    local url="http://localhost:${port}/health"
    log "健康检查: $url"
    for i in $(seq 1 12); do
        if curl -sf "$url" >/dev/null 2>&1; then
            log "✅ 通过 (第 ${i} 次)"; return 0
        fi
        sleep 5
    done
    err "健康检查失败: $url"
}

deploy_green() {
    local image_tag="$1"
    local image="${image_tag}"
    log "=== 部署绿色环境 ==="
    log "镜像: $image"
    docker pull "$image" || err "拉取镜像失败"
    docker rm -f ai-digital-card-green 2>/dev/null || true
    docker run -d --name ai-digital-card-green \
        --network bridge --restart unless-stopped \
        -p "${GREEN_PORT}:${BACKEND_PORT}" \
        "$image" || err "启动绿色容器失败"
    log "绿色容器已启动, 端口: ${GREEN_PORT}"
}

switch_traffic_to_green() {
    log "=== 切换流量 → 绿色 ==="
    local conf="/etc/nginx/conf.d/ai-digital-card-upstream.conf"
    [[ -f "$conf" ]] && cp "$conf" "${ROLLBACK_DIR}/upstream.conf.bak"
    cat > "$conf" <<- 'EOF'
upstream backend {
    server 127.0.0.1:8202;
    keepalive 32;
}
EOF
    nginx -t || err "Nginx 配置测试失败"
    nginx -s reload || err "Nginx 重载失败"
    log "✅ 流量已切换到绿色环境 (端口 ${GREEN_PORT})"
}

rollback_to_blue() {
    log "=== 回滚 → 蓝色环境 ==="
    local conf="/etc/nginx/conf.d/ai-digital-card-upstream.conf"
    if [[ -f "${ROLLBACK_DIR}/upstream.conf.bak" ]]; then
        cp "${ROLLBACK_DIR}/upstream.conf.bak" "$conf"
    else
        cat > "$conf" <<- 'EOF'
upstream backend {
    server 127.0.0.1:8201;
    keepalive 32;
}
EOF
    fi
    nginx -t && nginx -s reload || err "Nginx 重载失败"
    docker rm -f ai-digital-card-green 2>/dev/null || true
    log "✅ 已回滚到蓝色环境"
}

show_status() {
    echo "=== AI数智名片 - 蓝绿部署状态 ==="
    docker ps --filter "name=ai-digital-card" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null
    echo "--- Nginx Upstream ---"
    grep -E "server " /etc/nginx/conf.d/ai-digital-card-upstream.conf 2>/dev/null || echo "(未配置)"
    echo "--- 回滚备份 ---"
    ls -la "${ROLLBACK_DIR}/" 2>/dev/null || echo "(无备份)"
}

main() {
    preflight_check
    case "${1:-help}" in
        deploy)
            [[ -n "${2:-}" ]] || err "用法: $0 deploy <image>"
            deploy_green "$2"
            health_check "$GREEN_PORT"
            switch_traffic_to_green
            log "🎉 蓝绿部署完成! 绿色已上线, 蓝色保留回滚"
            ;;
        rollback)
            rollback_to_blue
            health_check "$BACKEND_PORT"
            log "✅ 回滚完成! 蓝色环境已恢复"
            ;;
        status) show_status ;;
        *)
            echo "用法: $0 deploy <image> | rollback | status"
            ;;
    esac
}
main "$@"
