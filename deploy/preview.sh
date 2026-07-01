#!/bin/bash
# ============================================================
# AI数智名片 - 预览环境部署脚本 (Preview Deploy)
# 供 CI (preview.yml) 调用，为每个 PR 创建独立的预览环境
# ============================================================
# 用法:
#   ./deploy/preview.sh \
#     --pr-number <PR_NUMBER> \
#     --image <DOCKER_IMAGE> \
#     --domain <PREVIEW_DOMAIN> \
#     --ssh-host <SSH_HOST> \
#     --ssh-user <SSH_USER> \
#     --repo <GITHUB_REPOSITORY>
# ============================================================
set -euo pipefail

# ---- 参数解析 ----
PR_NUMBER=""
IMAGE=""
DOMAIN=""
SSH_HOST=""
SSH_USER=""
REPO=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --pr-number|-p)     shift; PR_NUMBER="$1" ;;
        --image|-i)         shift; IMAGE="$1" ;;
        --domain|-d)        shift; DOMAIN="$1" ;;
        --ssh-host|-h)      shift; SSH_HOST="$1" ;;
        --ssh-user|-u)      shift; SSH_USER="$1" ;;
        --repo|-r)          shift; REPO="$1" ;;
        --help)             echo "用法见脚本顶部注释"; exit 0 ;;
        *)                  echo "未知参数: $1"; exit 1 ;;
    esac
    shift
done

# ---- 前置检查 ----
if [[ -z "$PR_NUMBER" || -z "$IMAGE" || -z "$DOMAIN" || -z "$SSH_HOST" || -z "$SSH_USER" ]]; then
    echo "❌ 缺少必要参数"
    echo "用法: $0 --pr-number <num> --image <img> --domain <dom> --ssh-host <host> --ssh-user <user>"
    exit 1
fi

PROJECT_DIR="/opt/ai-digital-card-preview/pr-${PR_NUMBER}"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"
NGINX_CONF_DIR="/etc/nginx/sites-enabled"
NGINX_CONF="${NGINX_CONF_DIR}/preview-pr-${PR_NUMBER}.conf"
PREVIEW_PORT_BACKEND=$(( 8300 + PR_NUMBER ))
PREVIEW_PORT_FRONTEND=$(( 8400 + PR_NUMBER ))

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
err()  { log "❌ ERROR: $*"; exit 1; }
warn() { log "⚠️  $*"; }

# ---- 1. 远程服务器准备 ----
prepare_server() {
    log "=== 1/5 准备预览服务器环境 ==="

    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" bash -s << REMOTE_PREP
        set -euo pipefail

        # 创建 PR 专属目录
        mkdir -p "${PROJECT_DIR}/frontend"
        mkdir -p "${PROJECT_DIR}/backend/data"
        mkdir -p "${PROJECT_DIR}/backend/uploads"
        log "  ✓ 目录已创建: ${PROJECT_DIR}"

        # 检查 Docker 是否可用
        command -v docker >/dev/null 2>&1 || { echo "❌ Docker 未安装"; exit 1; }
        log "  ✓ Docker 就绪"
REMOTE_PREP
    log "  ✅ 服务器环境准备完成"
}

# ---- 2. 上传前端静态文件 ----
upload_frontend() {
    log "=== 2/5 上传前端静态文件 ==="

    local frontend_dir="frontend/dist"
    if [[ ! -d "$frontend_dir" ]]; then
        err "前端构建产物不存在: ${frontend_dir}（请先运行 npm run build）"
    fi

    # 通过 rsync 或 scp 上传到远程服务器
    rsync -avz --delete \
        -e "ssh -o StrictHostKeyChecking=no" \
        "${frontend_dir}/" \
        "${SSH_USER}@${SSH_HOST}:${PROJECT_DIR}/frontend/" || {
            # rsync 不可用时回退到 scp
            warn "rsync 失败，回退到 scp"
            scp -o StrictHostKeyChecking=no -r "${frontend_dir}/" \
                "${SSH_USER}@${SSH_HOST}:${PROJECT_DIR}/frontend/"
        }
    log "  ✅ 前端文件已上传"
}

# ---- 3. 部署后端 Docker 容器 ----
deploy_backend() {
    log "=== 3/5 部署后端 Docker 容器 ==="

    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" bash -s << REMOTE_DEPLOY
        set -euo pipefail

        log() { echo "[$(date '+%H:%M:%S')] \$*"; }

        # 拉取 PR 专属镜像
        log "  📥 拉取镜像: ${IMAGE}"
        docker pull "${IMAGE}" || err "拉取镜像失败"

        # 停止并删除旧容器 (同名容器)
        local container_name="ai-card-preview-pr-${PR_NUMBER}"
        docker rm -f "\${container_name}" 2>/dev/null || true

        # 启动新容器
        log "  🚀 启动预览容器 (端口: ${PREVIEW_PORT_BACKEND})"
        docker run -d \
            --name "\${container_name}" \
            --restart unless-stopped \
            -p "127.0.0.1:${PREVIEW_PORT_BACKEND}:8201" \
            -e "ENV=preview" \
            -e "PR_NUMBER=${PR_NUMBER}" \
            -e "PREVIEW_DOMAIN=${DOMAIN}" \
            -v "${PROJECT_DIR}/backend/data:/app/data" \
            -v "${PROJECT_DIR}/backend/uploads:/app/uploads" \
            --label "com.ai-card.preview=true" \
            --label "com.ai-card.pr-number=${PR_NUMBER}" \
            "${IMAGE}" || err "启动容器失败"

        log "  ✅ 后端容器已启动"
        docker ps --filter "name=\${container_name}" --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"
REMOTE_DEPLOY
    log "  ✅ 后端部署完成"
}

# ---- 4. 配置 Nginx 反向代理 ----
configure_nginx() {
    log "=== 4/5 配置 Nginx 反向代理 ==="

    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" bash -s << REMOTE_NGINX
        set -euo pipefail

        log() { echo "[$(date '+%H:%M:%S')] \$*"; }

        NGINX_CONF="${NGINX_CONF}"

        log "  📝 生成 Nginx 配置: ${NGINX_CONF}"
        cat > "\${NGINX_CONF}" << 'NGINX_EOF'
server {
    listen 80;
    server_name ${DOMAIN};

    # 前端静态文件
    root ${PROJECT_DIR}/frontend;
    index index.html;

    # gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml;
    gzip_min_length 1000;

    # 前端静态资源
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header X-Frame-Options "DENY";
        add_header X-Content-Type-Options "nosniff";
    }

    # 静态资源缓存（构建产物带 hash）
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API 反向代理到后端
    location /api/ {
        proxy_pass http://127.0.0.1:${PREVIEW_PORT_BACKEND};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
    }

    # 健康检查端点
    location /health {
        proxy_pass http://127.0.0.1:${PREVIEW_PORT_BACKEND}/health;
        proxy_set_header Host \$host;
        access_log off;
    }

    # API 文档
    location /docs {
        proxy_pass http://127.0.0.1:${PREVIEW_PORT_BACKEND}/docs;
        proxy_set_header Host \$host;
    }
}
NGINX_EOF

        # 替换模板变量
        sed -i "s/\${DOMAIN}/${DOMAIN}/g" "\${NGINX_CONF}"
        sed -i "s|\${PROJECT_DIR}|${PROJECT_DIR}|g" "\${NGINX_CONF}"
        sed -i "s/\${PREVIEW_PORT_BACKEND}/${PREVIEW_PORT_BACKEND}/g" "\${NGINX_CONF}"

        log "  ✅ Nginx 配置已生成"

        # 测试并重载 Nginx
        nginx -t || err "Nginx 配置测试失败"
        nginx -s reload || err "Nginx 重载失败"
        log "  ✅ Nginx 已重载"
REMOTE_NGINX
    log "  ✅ Nginx 配置完成"
}

# ---- 5. 健康检查 ----
health_check() {
    log "=== 5/5 健康检查 ==="

    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" bash -s << REMOTE_CHECK
        set -euo pipefail

        log() { echo "[$(date '+%H:%M:%S')] \$*"; }

        local url="http://127.0.0.1:${PREVIEW_PORT_BACKEND}/health"
        log "  🏥 检查后端健康: \${url}"

        for i in \$(seq 1 12); do
            if curl -sf "\${url}" > /dev/null 2>&1; then
                log "  ✅ 健康检查通过 (第 \${i} 次)"
                exit 0
            fi
            log "  ⏳ 等待服务就绪... (\$((12 - i)) 次剩余)"
            sleep 5
        done

        log "  ❌ 健康检查失败"
        # 输出容器日志以便排查
        docker logs "ai-card-preview-pr-${PR_NUMBER}" --tail 30 2>/dev/null || true
        exit 1
REMOTE_CHECK
    log "  ✅ 预览环境健康检查通过"
}

# ---- 6. 输出部署摘要 ----
print_summary() {
    log ""
    log "=========================================="
    log "  🎉 Preview Deploy 完成！"
    log "=========================================="
    log "  PR #${PR_NUMBER}"
    log "  前端: https://${DOMAIN}"
    log "  API:  https://api-${DOMAIN}"
    log "  后端端口: ${PREVIEW_PORT_BACKEND} (内网)"
    log "  镜像: ${IMAGE}"
    log "  服务器: ${SSH_USER}@${SSH_HOST}"
    log "  项目目录: ${PROJECT_DIR}"
    log "=========================================="
    log ""
}

# ---- 清理函数 (用于 PR 关闭时调用) ----
cleanup_preview() {
    log "=== 清理预览环境 PR #${PR_NUMBER} ==="

    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" bash -s << REMOTE_CLEANUP
        set -euo pipefail

        local container_name="ai-card-preview-pr-${PR_NUMBER}"

        # 停止并删除容器
        docker rm -f "\${container_name}" 2>/dev/null || true
        log "  ✓ 容器已删除"

        # 删除 Nginx 配置
        rm -f "${NGINX_CONF}" 2>/dev/null || true
        nginx -t && nginx -s reload || true
        log "  ✓ Nginx 配置已清理"

        # 删除项目目录
        rm -rf "${PROJECT_DIR}" 2>/dev/null || true
        log "  ✓ 项目目录已删除"

        # 删除 Docker 镜像
        docker rmi "${IMAGE}" 2>/dev/null || true
        log "  ✓ 镜像已删除"

        log "  ✅ 预览环境已清理"
REMOTE_CLEANUP
}

# ---- 主入口 ----
main() {
    log "=========================================="
    log "  🚀 AI数智名片 Preview Deploy"
    log "  PR #${PR_NUMBER}"
    log "=========================================="
    log ""

    # 检查 rsync 可用性
    if ! command -v rsync &>/dev/null; then
        warn "rsync 未安装，使用 scp 替代（可能较慢）"
    fi

    prepare_server
    upload_frontend
    deploy_backend
    configure_nginx
    health_check
    print_summary
}

# 如果作为独立脚本运行且第一个参数是 cleanup，则执行清理
if [[ "${1:-}" == "cleanup" ]]; then
    shift
    PR_NUMBER="${1:-}"
    [[ -z "$PR_NUMBER" ]] && { echo "用法: $0 cleanup <PR_NUMBER>"; exit 1; }
    cleanup_preview
    exit $?
fi

main "$@"
