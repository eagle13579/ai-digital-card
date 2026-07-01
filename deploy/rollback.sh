#!/bin/bash
# ============================================================
# AI数智名片 - 自动回滚脚本
# 供 CI (rollback.yml) 调用，也可独立使用
# ============================================================
# 用法:
#   ./deploy/rollback.sh --target <镜像标签> --env <production|canary>
#   ./deploy/rollback.sh --commit <git-hash> --env <production|canary>
#   ./deploy/rollback.sh --restore-previous              # 恢复上一个版本
#   ./deploy/rollback.sh --status                        # 查看回滚状态
# ============================================================
set -euo pipefail

PROJECT_ROOT="/opt/ai-digital-card"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
HEALTH_URL="http://localhost:8201/health"
ROLLBACK_DIR="${PROJECT_ROOT}/deploy/rollback"
STATE_FILE="${ROLLBACK_DIR}/pre_rollback_image.txt"
DEPLOY_LOG="${ROLLBACK_DIR}/deploy-history.log"
REGISTRY="ghcr.io"
IMAGE_BACKEND="${REGISTRY}/${GITHUB_REPOSITORY:-unknown}/backend"

# ---- 工具函数 ----
log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
err()  { log "❌ ERROR: $*"; exit 1; }
warn() { log "⚠️  $*"; }

# ---- 前置检查 ----
preflight_check() {
    command -v docker >/dev/null 2>&1 || err "docker 未安装"
    command -v curl   >/dev/null 2>&1 || err "curl 未安装"
    command -v git    >/dev/null 2>&1 || warn "git 未安装 (如果使用 --commit 会失败)"
    mkdir -p "$ROLLBACK_DIR"
}

# ---- 健康检查 (60s 超时) ----
health_check() {
    local timeout="${1:-60}"
    log "🏥 健康检查中 (${timeout}s 超时)..."
    for i in $(seq 1 $((timeout / 5))); do
        if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
            log "✅ 健康检查通过 (第 ${i} 次)"
            return 0
        fi
        log "⏳ 等待服务就绪... ($((timeout - i*5))s 剩余)"
        sleep 5
    done
    err "健康检查失败: ${HEALTH_URL} (${timeout}s 超时)"
    return 1
}

# ---- 保存当前状态 ----
save_state() {
    log "💾 保存当前版本状态..."
    docker inspect ai-digital-card-backend \
        --format '{{.Config.Image}}' \
        2>/dev/null > "$STATE_FILE" || warn "无法获取当前镜像信息"
    log "   ✓ 已保存到 ${STATE_FILE}"
}

# ---- 部署指定镜像 ----
deploy_image() {
    local image="$1"
    local env="$2"

    log "=== 回滚部署 ==="
    log "   镜像: ${image}"
    log "   环境: ${env}"

    # 拉取镜像
    log "📥 拉取镜像: ${image}"
    docker pull "$image" || err "拉取镜像失败: ${image}"

    # 更新 compose 文件
    log "🔄 更新 docker-compose.yml..."
    sed -i.bak "s|image: .*backend.*|image: ${image}|g" "$COMPOSE_FILE"

    # 重启服务
    log "🔁 重启服务..."
    docker compose -f "$COMPOSE_FILE" up -d --remove-orphans || err "服务重启失败"

    # 清理旧镜像
    docker image prune -f 2>/dev/null || true

    log "✅ 镜像部署完成"
}

# ---- 恢复到上一个版本 ----
restore_previous() {
    log "=== 恢复到上一个版本 ==="
    if [[ -f "$STATE_FILE" ]]; then
        local prev_image
        prev_image=$(cat "$STATE_FILE")
        log "📥 恢复镜像: ${prev_image}"
        docker pull "$prev_image" 2>/dev/null || warn "拉取旧镜像失败"
        sed -i.bak "s|image: .*backend.*|image: ${prev_image}|g" "$COMPOSE_FILE"
        docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
        log "✅ 已恢复到上一个版本: ${prev_image}"
    else
        warn "无状态记录，尝试 docker compose 直接重启..."
        docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
    fi
    health_check 60
}

# ---- 通过 git commit 回滚 ----
rollback_to_commit() {
    local commit="$1"
    local env="$2"

    log "=== Git 回滚到 commit: ${commit::8} ==="
    cd "${PROJECT_ROOT}"

    # 检查 commit 是否存在
    git cat-file -e "${commit}" 2>/dev/null || err "commit ${commit::8} 不存在"

    # Revert 或 reset
    git revert --no-commit "${commit}..HEAD" 2>/dev/null || {
        warn "revert 产生冲突，改用 git reset --soft"
        git reset --soft "${commit}"
    }

    git commit -m "rollback: revert to ${commit::8}

Manual rollback via deploy/rollback.sh
Commit: ${commit}
Environment: ${env}
Date: $(date '+%Y-%m-%d %H:%M:%S')"

    # 构建新镜像
    local tag="rollback-${commit::8}-$(date +%s)"
    local image="${IMAGE_BACKEND}:${tag}"

    log "🔨 构建镜像: ${image}"
    cd "${PROJECT_ROOT}/backend"
    docker build -t "$image" . || err "镜像构建失败"

    # 推送
    log "📤 推送镜像..."
    docker push "$image" || warn "镜像推送失败 (非致命)"

    # 部署
    deploy_image "$image" "$env"
}

# ---- 显示状态 ----
show_status() {
    echo "=== AI数智名片 - 回滚状态 ==="
    echo ""
    echo "--- 当前运行容器 ---"
    docker ps --filter "name=ai-digital-card" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "(无)"
    echo ""
    echo "--- 状态文件 ---"
    if [[ -f "$STATE_FILE" ]]; then
        echo "  上一个镜像: $(cat "$STATE_FILE")"
    else
        echo "  (无历史记录)"
    fi
    echo ""
    echo "--- 回滚目录 ---"
    ls -la "${ROLLBACK_DIR}/" 2>/dev/null || echo "  (空)"
    echo ""
    echo "--- 健康状态 ---"
    if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
        echo "  ✅ 服务健康"
    else
        echo "  ❌ 服务异常"
    fi
}

# ---- 主入口 ----
main() {
    preflight_check

    local target="" env="" commit=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target|-t)    shift; target="$1" ;;
            --env|-e)       shift; env="${1:-production}" ;;
            --commit|-c)    shift; commit="$1" ;;
            --restore-previous|-r) restore_previous; exit $? ;;
            --status|-s)    show_status; exit 0 ;;
            --help|-h)      echo "用法: $0 [--target <镜像>|--commit <hash>] [--env <环境>]"; exit 0 ;;
            *)              err "未知参数: $1 (使用 --help 查看帮助)" ;;
        esac
        shift
    done

    # 校验
    if [[ -n "$commit" && -n "$target" ]]; then
        err "不能同时指定 --commit 和 --target，请二选一"
    fi

    # 保存当前状态
    save_state

    if [[ -n "$target" ]]; then
        deploy_image "$target" "$env"
    elif [[ -n "$commit" ]]; then
        rollback_to_commit "$commit" "$env"
    else
        # 默认：自动回退到上一个版本
        log "ℹ️  未指定目标，自动恢复上一个版本..."
        restore_previous
        exit $?
    fi

    # 健康检查
    health_check 60
    log "🎉 回滚成功！"
}

main "$@"
