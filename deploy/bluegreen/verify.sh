#!/bin/bash
# ════════════════════════════════════════════════════════════════════
# AI数智名片 — 蓝绿部署一键验证脚本 (verify.sh)
# ════════════════════════════════════════════════════════════════════
#  检查所有端口状态 / Nginx 配置 / 当前活跃环境
#  模拟切换流程 (dry-run 模式，不改写任何文件)
# ════════════════════════════════════════════════════════════════════
# 用法:
#   bash deploy/bluegreen/verify.sh              # 完整验证
#   bash deploy/bluegreen/verify.sh --quick      # 仅端口 + 状态摘要
#   bash deploy/bluegreen/verify.sh --fix        # 提示修复步骤
# ════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── 配置 ────────────────────────────────────────────────────────────
BLUE_PORT=8201
GREEN_PORT=8202
GATEWAY_PORT=8200
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BLUEGREEN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NGINX_CONF_TEMPLATE="${BLUEGREEN_DIR}/nginx-bluegreen.conf"
NGINX_CONF_TARGET="/etc/nginx/conf.d/bluegreen.conf"

# ── 颜色 ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
OK="${GREEN}✔${NC}"; FAIL="${RED}✘${NC}"; WARN="${YELLOW}⚠${NC}"; INFO="${CYAN}ℹ${NC}"

TEST_PASS=0
TEST_FAIL=0
TEST_WARN=0

log()      { echo -e "$*"; }
pass()     { echo -e "  ${OK} $*"; TEST_PASS=$((TEST_PASS + 1)); }
fail()     { echo -e "  ${FAIL} $*"; TEST_FAIL=$((TEST_FAIL + 1)); }
warn()     { echo -e "  ${WARN} $*"; TEST_WARN=$((TEST_WARN + 1)); }
info()     { echo -e "  ${INFO} $*"; }
header()   { echo -e "\n${CYAN}═══════════════════════════════════════════════════${NC}"; echo -e "${CYAN} $*${NC}"; echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"; }

# ── 检测工具 ────────────────────────────────────────────────────────
check_port() {
    local port="$1" label="$2"
    if netstat -ano 2>/dev/null | grep -qE "[:.]${port}\b.*LISTENING"; then
        pass "端口 ${port} (${label}): 监听中"
        return 0
    fi
    fail "端口 ${port} (${label}): 未监听"
    return 1
}

check_http() {
    local port="$1" label="$2"
    local url="http://127.0.0.1:${port}/health"
    if curl -sf "${url}" >/dev/null 2>&1; then
        pass "HTTP ${port} (${label}): /health 响应正常"
        return 0
    fi
    warn "HTTP ${port} (${label}): /health 无响应 (可能非后端服务)"
    return 1
}

# ── 获取当前活跃环境 (从 Nginx 配置推断) ──────────────────────────
get_active_env() {
    if [[ -f "$NGINX_CONF_TARGET" ]]; then
        local active
        active=$(grep -oP 'default\s+\K(backend_blue|backend_green)' "$NGINX_CONF_TARGET" 2>/dev/null || echo "unknown")
        echo "$active"
    elif curl -sf "http://127.0.0.1:${GATEWAY_PORT}/api/" -o /dev/null 2>&1; then
        local header
        header=$(curl -sI "http://127.0.0.1:${GATEWAY_PORT}/api/" 2>/dev/null | grep -i X-Active-Env || true)
        if [[ "$header" =~ backend_blue ]]; then
            echo "backend_blue"
        elif [[ "$header" =~ backend_green ]]; then
            echo "backend_green"
        else
            echo "inferred_from_gateway"
        fi
    else
        echo "unknown"
    fi
}

# ── 检测 Nginx ──────────────────────────────────────────────────────
check_nginx() {
    local nginx_found=false

    # 检查 nginx 命令
    if command -v nginx &>/dev/null; then
        pass "nginx 命令可用: $(nginx -v 2>&1)"
        nginx_found=true
    else
        # 检查常见的 Windows 安装路径
        for p in \
            "/c/Program Files/nginx" \
            "/c/nginx" \
            "/c/tools/nginx" \
            "/c/ProgramData/chocolatey/bin/nginx" \
            "C:/Program Files/nginx/nginx.exe" \
            "C:/nginx/nginx.exe"; do
            if [[ -f "$p" ]] || [[ -f "${p}.exe" ]]; then
                warn "nginx 在 PATH 外发现: $p (需加入 PATH)"
                nginx_found=true
                break
            fi
        done
        if ! $nginx_found; then
            # 检查端口 8200 是否由 nginx 进程监听
            if netstat -ano 2>/dev/null | grep -qE "[:.]${GATEWAY_PORT}\b.*LISTENING"; then
                local pid
                pid=$(netstat -ano 2>/dev/null | grep -E "[:.]${GATEWAY_PORT}\b" | head -1 | awk '{print $NF}')
                local pname=""
                if command -v tasklist.exe &>/dev/null; then
                    pname=$(tasklist.exe //FI "PID eq $pid" 2>/dev/null | tail -n +4 | awk '{print $1}' | tr -d '\r')
                fi
                warn "端口 ${GATEWAY_PORT} 由进程 ${pname:-$pid} 监听 (非 nginx)"
            fi
        fi
    fi

    if ! $nginx_found; then
        warn "nginx 未安装 — 蓝绿切换需要 nginx 流量代理"
        info "  安装参考: https://nginx.org/en/download.html"
        info "  或使用 Docker: docker run -d -p 8200:80 nginx:alpine"
    fi

    return 0
}

# ── 检查 Nginx 配置语法 ─────────────────────────────────────────────
check_nginx_config() {
    # 检查配置模板是否存在
    if [[ ! -f "$NGINX_CONF_TEMPLATE" ]]; then
        fail "Nginx 配置模板不存在: ${NGINX_CONF_TEMPLATE}"
        return 1
    fi
    pass "Nginx 配置模板存在: $(basename "$NGINX_CONF_TEMPLATE")"

    # 尝试用 nginx -t 检查语法
    if command -v nginx &>/dev/null; then
        # 创建临时配置测试目录
        local tmpdir
        tmpdir=$(mktemp -d)
        mkdir -p "${tmpdir}/conf.d"
        cp "$NGINX_CONF_TEMPLATE" "${tmpdir}/conf.d/bluegreen.conf"

        if nginx -t -p "$tmpdir" -c /dev/null -g "daemon off; error_log ${tmpdir}/error.log warn; pid ${tmpdir}/nginx.pid; http { include ${tmpdir}/conf.d/*.conf; }" 2>&1; then
            pass "Nginx 配置语法: 正确"
        else
            fail "Nginx 配置语法: 有错误"
            nginx -t -p "$tmpdir" -c /dev/null -g "daemon off; error_log ${tmpdir}/error.log warn; pid ${tmpdir}/nginx.pid; http { include ${tmpdir}/conf.d/*.conf; }" 2>&1
        fi
        rm -rf "$tmpdir"
    else
        # 本地语法检查 fallback (仅检查结构)
        warn "nginx 命令不可用，跳过配置语法检查"
        info "  部署后记得运行: nginx -t"
    fi
}

# ── 检查切换脚本 ────────────────────────────────────────────────────
check_switch_scripts() {
    for script in "switch-blue.sh" "switch-green.sh"; do
        local path="${BLUEGREEN_DIR}/${script}"
        if [[ -f "$path" ]]; then
            if [[ -x "$path" ]]; then
                pass "切换脚本可执行: ${script}"
            else
                warn "切换脚本存在但不可执行: ${script} (运行 chmod +x)"
            fi
        else
            fail "切换脚本缺失: ${script}"
        fi
    done
}

# ── 模拟切换 (dry-run) ─────────────────────────────────────────────
dry_run_switch() {
    echo
    header "模拟切换流程 (dry-run 模式 — 不做任何实际修改)"

    local active
    active=$(get_active_env)
    echo -e "  当前活跃后端: ${YELLOW}${active}${NC}"

    echo -e "\n  ${CYAN}步骤 1${NC}: 部署新版本至备用端口"
    info "    蓝色端口 8201 → 当前活跃"
    info "    绿色端口 8202 → 新版本部署目标"
    echo -e "  ${CYAN}步骤 2${NC}: 确认备用端口健康"
    echo -e "    运行: bash ${BLUEGREEN_DIR}/health_check.sh --port GREEN_PORT"
    echo -e "  ${CYAN}步骤 3${NC}: 执行切换"
    if [[ "$active" == "backend_blue" || "$active" == "unknown" ]]; then
        echo -e "    运行: bash ${BLUEGREEN_DIR}/switch-green.sh"
        echo -e "    → 流量从 ${YELLOW}蓝色:8201${NC} 切至 ${GREEN}绿色:8202${NC}"
        echo -e "  ${CYAN}步骤 4${NC}: 验证"
        echo -e "    运行: bash ${BLUEGREEN_DIR}/health_check.sh --all"
        echo -e "  ${CYAN}步骤 5${NC}: 旧版本保留 (如需回滚)"
        info "    回滚命令: bash ${BLUEGREEN_DIR}/switch-blue.sh"
    else
        echo -e "    运行: bash ${BLUEGREEN_DIR}/switch-blue.sh"
        echo -e "    → 流量从 ${YELLOW}绿色:8202${NC} 切回 ${GREEN}蓝色:8201${NC}"
    fi
}

# ── 显示摘要 ────────────────────────────────────────────────────────
show_summary() {
    echo
    header "验证摘要"
    local total=$((TEST_PASS + TEST_FAIL + TEST_WARN))
    echo -e "  通过: ${GREEN}${TEST_PASS}${NC}  |  失败: ${RED}${TEST_FAIL}${NC}  |  警告: ${YELLOW}${TEST_WARN}${NC}  |  总计: ${total}"

    if [[ $TEST_FAIL -gt 0 ]]; then
        echo -e "\n  ${RED}⚠  存在失败项，请修复后重试${NC}"
    elif [[ $TEST_WARN -gt 0 ]]; then
        echo -e "\n  ${YELLOW}⚠  存在警告项，建议查看${NC}"
    else
        echo -e "\n  ${GREEN}✓  所有检查通过！蓝绿部署就绪${NC}"
    fi
}

# ── 主流程 ──────────────────────────────────────────────────────────
main() {
    local mode="${1:-full}"

    echo -e "${CYAN}"
    echo "  ╔═══════════════════════════════════════════════╗"
    echo "  ║      AI数智名片 — 蓝绿部署验证脚本            ║"
    echo "  ║      Blue-Green Deployment Verification       ║"
    echo "  ╚═══════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo "  项目路径: ${PROJECT_ROOT}"
    echo "  检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "  运行模式: ${mode}"

    # ────── 1. 端口检查 ──────
    header "端口状态检查"
    check_port "$BLUE_PORT"   "蓝色后端 Blue"
    check_port "$GREEN_PORT"  "绿色后端 Green"
    check_port "$GATEWAY_PORT" "网关 Gateway"

    # ────── 2. HTTP 健康检查 ──────
    header "HTTP 健康检查"
    check_http "$BLUE_PORT"   "蓝色后端"
    check_http "$GREEN_PORT"  "绿色后端"

    # ────── 3. 当前活跃环境 ──────
    header "当前活跃环境"
    local active
    active=$(get_active_env)
    case "$active" in
        backend_blue)
            echo -e "  ${GREEN}●${NC} 蓝色环境 (Blue) - 端口 ${BLUE_PORT}"
            ;;
        backend_green)
            echo -e "  ${GREEN}●${NC} 绿色环境 (Green) - 端口 ${GREEN_PORT}"
            ;;
        *)
            echo -e "  ${YELLOW}●${NC} 无法确定活跃环境 (${active})"
            echo -e "    Nginx 配置: $( [[ -f "$NGINX_CONF_TARGET" ]] && echo '存在' || echo '不存在' )"
            ;;
    esac

    # ────── 4. Nginx 检查 ──────
    header "Nginx 状态"
    check_nginx

    # ────── 5. Nginx 配置语法 ──────
    header "Nginx 配置检查"
    check_nginx_config

    # ────── 6. 切换脚本检查 ──────
    header "切换脚本检查"
    check_switch_scripts

    # ────── 7. Nginx 配置是否已部署 ──────
    header "蓝绿配置文件部署状态"
    if [[ -f "$NGINX_CONF_TARGET" ]]; then
        pass "Nginx 蓝绿配置已部署: ${NGINX_CONF_TARGET}"
        local tmpl_mod=$(stat -c "%Y" "$NGINX_CONF_TEMPLATE" 2>/dev/null || echo 0)
        local targ_mod=$(stat -c "%Y" "$NGINX_CONF_TARGET" 2>/dev/null || echo 0)
        if [[ "$tmpl_mod" -gt "$targ_mod" ]]; then
            warn "配置模板比已部署配置更新 — 建议重新部署"
        fi
    else
        warn "Nginx 蓝绿配置未部署"
        info "  部署命令:"
        info "    sudo cp ${NGINX_CONF_TEMPLATE} ${NGINX_CONF_TARGET}"
        info "    sudo nginx -t && sudo nginx -s reload"
    fi

    # ────── 8. 健康检查脚本 ──────
    if [[ -f "${BLUEGREEN_DIR}/health_check.sh" ]]; then
        if [[ -x "${BLUEGREEN_DIR}/health_check.sh" ]]; then
            pass "健康检查脚本可执行: health_check.sh"
        else
            warn "健康检查脚本不可执行: health_check.sh"
        fi
    else
        fail "健康检查脚本缺失: health_check.sh"
    fi

    # ────── quick 模式到此结束 ──────
    if [[ "$mode" == "--quick" ]]; then
        show_summary
        exit $TEST_FAIL
    fi

    # ────── 9. 模拟切换 ──────
    dry_run_switch

    # ────── 10. 摘要 ──────
    show_summary

    if [[ $TEST_FAIL -gt 0 ]]; then
        echo -e "\n  ${RED}修复建议:${NC}"
        echo -e "    1. 确保 nginx 已安装并运行"
        echo -e "    2. 确保后端服务在端口 8201 运行"
        echo -e "    3. 部署 nginx 配置: cp ${NGINX_CONF_TEMPLATE} ${NGINX_CONF_TARGET}"
        echo -e "    4. 运行 nginx -t && nginx -s reload"
        echo -e "    5. 再次运行本脚本确认"
        exit 1
    fi

    echo -e "\n${GREEN}✓ 验证完成！蓝绿部署一切就绪。${NC}"
}

main "$@"
