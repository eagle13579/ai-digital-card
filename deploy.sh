#!/usr/bin/env bash
# =============================================================================
# deploy.sh — AI数字名片 自动部署脚本
# 用法:  sudo ./deploy.sh               # 生产部署
#        ./deploy.sh --dry-run          # 模拟运行，不实际重启容器
#        ./deploy.sh --skip-pull        # 跳过 git pull，直接重建
#        ./deploy.sh --project-dir /path  # 指定项目目录
# =============================================================================
set -euo pipefail

# ── 颜色输出 ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# ── 参数解析 ─────────────────────────────────────────────────────────────────
DRY_RUN=false
SKIP_PULL=false
PROJECT_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)    DRY_RUN=true;    shift ;;
    --skip-pull)  SKIP_PULL=true;  shift ;;
    --project-dir) PROJECT_DIR="$2"; shift 2 ;;
    *)            err "未知参数: $1"; exit 1 ;;
  esac
done

# ── 项目目录 ─────────────────────────────────────────────────────────────────
if [[ -z "$PROJECT_DIR" ]]; then
  # 自动推断脚本所在目录
  PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

info "项目目录: ${PROJECT_DIR}"
cd "$PROJECT_DIR"

# ── 检查 docker-compose.yml ──────────────────────────────────────────────────
if [[ ! -f "docker-compose.yml" ]]; then
  err "未在 ${PROJECT_DIR} 下找到 docker-compose.yml"
  exit 1
fi

# ── 前置检查 ─────────────────────────────────────────────────────────────────
command -v docker >/dev/null 2>&1 || { err "docker 未安装"; exit 1; }
command -v curl   >/dev/null 2>&1 || { err "curl 未安装";   exit 1; }

info "docker 版本: $(docker --version)"
info "docker compose 版本: $(docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || echo '未检测到')"

# ── Step 1: 拉取最新代码 ─────────────────────────────────────────────────────
if [[ "$SKIP_PULL" == false ]]; then
  info "正在从 Git 拉取最新代码..."
  if [[ -d ".git" ]]; then
    if $DRY_RUN; then
      info "[DRY-RUN] git pull origin main"
    else
      git pull origin main
      ok "Git pull 完成"
    fi
  else
    warn "当前目录不是 Git 仓库，跳过 git pull"
  fi
else
  info "已跳过 git pull (--skip-pull)"
fi

# ── Step 2: 停止并移除旧容器 ─────────────────────────────────────────────────
info "正在停止旧容器..."
if $DRY_RUN; then
  info "[DRY-RUN] docker compose down --remove-orphans"
else
  docker compose down --remove-orphans 2>/dev/null || docker-compose down --remove-orphans
  ok "旧容器已停止"
fi

# ── Step 3: 重建并启动 ───────────────────────────────────────────────────────
info "正在构建并启动新容器..."
if $DRY_RUN; then
  info "[DRY-RUN] docker compose up -d --build"
else
  docker compose up -d --build 2>/dev/null || docker-compose up -d --build
  ok "新容器已启动"
fi

# ── Step 4: 健康检查 ─────────────────────────────────────────────────────────
info "等待服务就绪..."

MAX_RETRIES=15
RETRY_INTERVAL=3
HEALTH_URL="http://localhost:8003/health"

health_check() {
  local response
  response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
  echo "$response"
}

for ((i=1; i<=MAX_RETRIES; i++)); do
  if $DRY_RUN; then
    info "[DRY-RUN] curl -sSf $HEALTH_URL → 模拟返回 200"
    ok "✅ 健康检查通过 (dry-run)"
    exit 0
  fi

  status=$(health_check)
  if [[ "$status" == "200" ]]; then
    ok "✅ 健康检查通过 — ${HEALTH_URL} 返回 200"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║       🚀  部署成功！                            ║${NC}"
    echo -e "${GREEN}║       服务: digital-brochure                     ║${NC}"
    echo -e "${GREEN}║       端口: 8003                                 ║${NC}"
    echo -e "${GREEN}║       项目: ${PROJECT_DIR}  ${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
    exit 0
  fi

  if [[ "$i" -eq "$MAX_RETRIES" ]]; then
    err "❌ 健康检查失败 — ${HEALTH_URL} 未返回 200（已重试 ${MAX_RETRIES} 次）"
    echo ""
    warn "最近容器日志:"
    docker logs --tail 20 digital-brochure 2>/dev/null || true
    exit 1
  fi

  info "等待服务启动... (${i}/${MAX_RETRIES}, HTTP ${status})"
  sleep "$RETRY_INTERVAL"
done
