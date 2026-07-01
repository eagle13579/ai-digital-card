#!/bin/bash
# ──────────────────────────────────────────────────────────────
#  灾难恢复脚本集 — AI数字名片 (AI Digital Business Card)
#  版本: v1.0
#  功能: backup / restore / check
#  用法:
#     ./disaster_recovery.sh backup [full|wal|config]   # 执行备份
#     ./disaster_recovery.sh restore [latest|FILE]      # 恢复备份
#     ./disaster_recovery.sh check                       # 系统完整性检查
#     ./disaster_recovery.sh list                        # 列出可用备份
#     ./disaster_recovery.sh help                        # 显示帮助
# ──────────────────────────────────────────────────────────────

set -euo pipefail

# ==============================================================
# 配置区 — 根据实际环境修改
# ==============================================================

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 数据库配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-ai_digital_business_card}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"

# 备份目录
BACKUP_DIR="${BACKUP_DIR:-${PROJECT_ROOT}/backups}"
BACKUP_DB_DIR="${BACKUP_DIR}/db"
BACKUP_CODE_DIR="${BACKUP_DIR}/code"
BACKUP_CONFIG_DIR="${BACKUP_DIR}/config"
BACKUP_LOG_DIR="${BACKUP_DIR}/logs"

# 异地存储 (对象存储) — 可选，用于异地容灾
REMOTE_BACKUP_ENABLED="${REMOTE_BACKUP_ENABLED:-false}"
REMOTE_BACKUP_URL="${REMOTE_BACKUP_URL:-s3://my-bucket/backups}"

# 加密密钥 (AES-256-GCM)
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"

# 保留策略
RETENTION_DAYS_FULL=30
RETENTION_DAYS_WAL=7
RETENTION_DAYS_CODE=90

# 应用配置
APP_DIR="${PROJECT_ROOT}/backend"
ENV_FILE="${PROJECT_ROOT}/.env.production"
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

# 时间戳
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DATE_TAG="$(date +%Y-%m-%d)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================
# 工具函数
# ==============================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $*"
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &>/dev/null; then
        log_error "缺少必要命令: $1，请先安装"
        exit 1
    fi
}

# 创建备份目录
ensure_dir() {
    mkdir -p "$1"
    log_info "目录已就绪: $1"
}

# 加密文件 (使用 OpenSSL AES-256-GCM)
encrypt_file() {
    local src="$1" dst="$2"
    if [[ -n "$ENCRYPTION_KEY" ]]; then
        openssl enc -aes-256-gcm -salt -pbkdf2 -iter 100000 \
            -pass "pass:${ENCRYPTION_KEY}" -in "$src" -out "$dst"
        rm -f "$src"
        log_info "文件已加密: $dst"
    else
        mv "$src" "$dst"
        log_warn "加密密钥未设置，备份文件未加密: $dst"
    fi
}

# 解密文件
decrypt_file() {
    local src="$1" dst="$2"
    if [[ -n "$ENCRYPTION_KEY" ]]; then
        openssl enc -d -aes-256-gcm -pbkdf2 -iter 100000 \
            -pass "pass:${ENCRYPTION_KEY}" -in "$src" -out "$dst"
        log_info "文件已解密: $dst"
    else
        cp "$src" "$dst"
    fi
}

# 清理过期备份
cleanup_old_backups() {
    local dir="$1" days="$2"
    if [[ -d "$dir" ]]; then
        find "$dir" -name "*.sql.gz*" -type f -mtime "+${days}" -delete 2>/dev/null || true
        find "$dir" -name "*.tar.gz*" -type f -mtime "+${days}" -delete 2>/dev/null || true
        log_info "已清理 ${dir} 中超过 ${days} 天的备份"
    fi
}

# 同步到异地存储
sync_to_remote() {
    if [[ "$REMOTE_BACKUP_ENABLED" != "true" ]]; then
        return 0
    fi

    local src="$1"
    local dest="${REMOTE_BACKUP_URL}/$(basename "$src")"

    log_step "同步到异地存储: ${dest}"

    # 支持 aws s3、rclone、azure copy 等方式
    if command -v aws &>/dev/null; then
        aws s3 cp "$src" "$dest" --storage-class STANDARD_IA
    elif command -v rclone &>/dev/null; then
        rclone copy "$src" "$dest"
    else
        log_warn "未找到 aws-cli 或 rclone，跳过异地同步"
        return 0
    fi

    log_info "异地同步完成: ${dest}"
}

# ==============================================================
# 备份功能
# ==============================================================

# 数据库全量备份
backup_db_full() {
    log_step "===== 数据库全量备份 ====="

    check_command pg_dump
    ensure_dir "${BACKUP_DB_DIR}/full"

    local backup_file="${BACKUP_DB_DIR}/full/${DB_NAME}_${TIMESTAMP}.sql"
    local backup_gz="${backup_file}.gz"

    log_info "开始备份数据库: ${DB_NAME} (主机: ${DB_HOST}:${DB_PORT})"

    # 导出数据库
    export PGPASSWORD="${DB_PASSWORD}"
    pg_dump \
        -h "${DB_HOST}" -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --no-owner --no-acl \
        --format=custom \
        --file="${backup_file}" \
        --verbose 2>&1 | tail -5

    log_info "数据库导出完成: $(du -h "${backup_file}" | cut -f1)"

    # 压缩
    gzip -f "${backup_file}"
    log_info "备份压缩完成: ${backup_gz}"

    # 加密
    local encrypted_file="${backup_gz}.enc"
    encrypt_file "${backup_gz}" "${encrypted_file}"

    # 写入校验和
    sha256sum "${encrypted_file}" > "${encrypted_file}.sha256"

    log_info "数据库全量备份完成: ${encrypted_file}"

    # 同步到异地
    sync_to_remote "${encrypted_file}"
    sync_to_remote "${encrypted_file}.sha256"

    # 记录备份元信息
    local meta_file="${BACKUP_DB_DIR}/backup_meta_${TIMESTAMP}.json"
    cat > "${meta_file}" <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "date": "${DATE_TAG}",
  "type": "full",
  "database": "${DB_NAME}",
  "host": "${DB_HOST}",
  "file": "${encrypted_file}",
  "size_bytes": $(stat -c%s "${encrypted_file}" 2>/dev/null || stat -f%z "${encrypted_file}" 2>/dev/null || echo 0),
  "sha256": "$(cat "${encrypted_file}.sha256" | cut -d' ' -f1)"
}
EOF
    log_info "备份元信息已保存: ${meta_file}"

    # 清理过期备份
    cleanup_old_backups "${BACKUP_DB_DIR}/full" "${RETENTION_DAYS_FULL}"
}

# WAL 归档备份
backup_db_wal() {
    log_step "===== WAL 归档备份 ====="

    check_command psql
    ensure_dir "${BACKUP_DB_DIR}/wal"

    # 切换到归档模式（如果 PostgreSQL 已配置 archive_command）
    log_info "执行 WAL 归档 (pg_switch_wal) ..."

    export PGPASSWORD="${DB_PASSWORD}"
    local wal_file="${BACKUP_DB_DIR}/wal/${DB_NAME}_wal_${TIMESTAMP}.tar.gz"

    # 通过 pg_basebackup 获取当前 WAL
    pg_basebackup \
        -h "${DB_HOST}" -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -D "${BACKUP_DB_DIR}/wal/pg_basebackup_${TIMESTAMP}" \
        --wal-method=fetch \
        --progress --verbose 2>&1 | tail -3

    # 打包 WAL
    cd "${BACKUP_DB_DIR}/wal"
    tar -czf "${wal_file}" "pg_basebackup_${TIMESTAMP}"
    rm -rf "pg_basebackup_${TIMESTAMP}"

    log_info "WAL 归档完成: ${wal_file} ($(du -h "${wal_file}" | cut -f1))"

    # 加密
    local encrypted_file="${wal_file}.enc"
    encrypt_file "${wal_file}" "${encrypted_file}"

    # 同步到异地
    sync_to_remote "${encrypted_file}"

    cleanup_old_backups "${BACKUP_DB_DIR}/wal" "${RETENTION_DAYS_WAL}"
}

# 代码备份 (Git bundle)
backup_code() {
    log_step "===== 代码备份 ====="

    check_command git
    ensure_dir "${BACKUP_CODE_DIR}"

    local code_backup="${BACKUP_CODE_DIR}/code_${TIMESTAMP}.bundle"

    log_info "创建 Git bundle: ${code_backup}"
    cd "${PROJECT_ROOT}"
    git bundle create "${code_backup}" --all --tags 2>&1

    if [[ $? -eq 0 ]]; then
        log_info "Git bundle 创建成功: $(du -h "${code_backup}" | cut -f1)"
    else
        log_error "Git bundle 创建失败"
        return 1
    fi

    # 拷贝 .env 文件 (加密)
    if [[ -f "${ENV_FILE}" ]]; then
        local env_backup="${BACKUP_CONFIG_DIR}/env_${TIMESTAMP}.tar.gz"
        cd "${PROJECT_ROOT}"
        tar -czf "${env_backup}" \
            ".env.production" ".env.example" \
            "docker-compose.yml" \
            "deploy/nginx.conf" 2>/dev/null || true

        local encrypted_env="${env_backup}.enc"
        encrypt_file "${env_backup}" "${encrypted_env}"
        log_info "环境配置已备份: ${encrypted_env}"
    fi

    # 同步到异地
    sync_to_remote "${code_backup}"
    cleanup_old_backups "${BACKUP_CODE_DIR}" "${RETENTION_DAYS_CODE}"
}

# 配置备份
backup_config() {
    log_step "===== 配置备份 ====="

    ensure_dir "${BACKUP_CONFIG_DIR}"

    local config_file="${BACKUP_CONFIG_DIR}/config_${TIMESTAMP}.tar.gz"

    cd "${PROJECT_ROOT}"
    tar -czf "${config_file}" \
        "backend/.env" "backend/app/" \
        "deploy/" \
        "docker-compose.yml" \
        "k8s/" \
        ".github/" 2>/dev/null || true

    log_info "配置打包完成: ${config_file} ($(du -h "${config_file}" | cut -f1))"

    # 加密
    local encrypted_file="${config_file}.enc"
    encrypt_file "${config_file}" "${encrypted_file}"

    sync_to_remote "${encrypted_file}"
}

# ==============================================================
# 恢复功能
# ==============================================================

# 从 SQL 文件恢复数据库
restore_db() {
    local backup_file="$1"

    log_step "===== 数据库恢复 ====="

    check_command pg_restore
    check_command psql

    if [[ ! -f "${backup_file}" ]]; then
        log_error "备份文件不存在: ${backup_file}"
        return 1
    fi

    # 如果是加密文件，先解密
    local restore_file="${backup_file}"
    if [[ "${backup_file}" == *.enc ]]; then
        log_info "检测到加密备份，正在解密..."
        restore_file="${backup_file%.enc}"
        decrypt_file "${backup_file}" "${restore_file}"

        # 验证校验和
        local sha_file="${backup_file}.sha256"
        if [[ -f "${sha_file}" ]]; then
            cd "$(dirname "${sha_file}")"
            if sha256sum -c "${sha_file}" &>/dev/null; then
                log_info "校验和验证通过"
            else
                log_error "校验和验证失败，备份文件可能已损坏"
                return 1
            fi
        fi
    fi

    # 如果是 gz 压缩，解压
    local sql_file="${restore_file}"
    if [[ "${restore_file}" == *.gz ]]; then
        sql_file="${restore_file%.gz}"
        gunzip -f -k "${restore_file}" 2>/dev/null || true
    fi

    log_info "开始恢复数据库: ${DB_NAME}"
    log_warn "!!! 此操作将覆盖当前数据库 !!!"
    log_warn "!!! 请在 5 秒内按 Ctrl+C 取消操作 !!!"

    if [[ "${FORCE_RESTORE:-false}" != "true" ]]; then
        sleep 5
    fi

    # 断开所有连接并重建数据库
    export PGPASSWORD="${DB_PASSWORD}"

    log_info "断开所有数据库连接..."
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres <<-EOSQL
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '${DB_NAME}'
          AND pid <> pg_backend_pid();
EOSQL

    log_info "重建数据库..."
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres <<-EOSQL
        DROP DATABASE IF EXISTS ${DB_NAME};
        CREATE DATABASE ${DB_NAME};
EOSQL

    # 恢复
    log_info "执行数据恢复..."
    pg_restore \
        -h "${DB_HOST}" -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --no-owner --no-acl \
        --verbose \
        "${sql_file}" 2>&1 | tail -20

    if [[ $? -eq 0 ]]; then
        log_info "数据库恢复成功!"
    else
        log_error "数据库恢复失败，请检查日志"
        return 1
    fi

    # 验证恢复
    log_info "验证恢复结果..."
    local table_count
    table_count=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')

    log_info "恢复后数据库表数量: ${table_count}"

    # 清理临时文件
    if [[ "${sql_file}" != "${restore_file}" ]]; then
        rm -f "${sql_file}"
    fi
    rm -f "${restore_file}"
}

# 恢复代码
restore_code() {
    local backup_file="$1"

    log_step "===== 代码恢复 ====="

    check_command git

    if [[ ! -f "${backup_file}" ]]; then
        log_error "代码备份文件不存在: ${backup_file}"
        return 1
    fi

    local restore_dir="${PROJECT_ROOT}_restored_${TIMESTAMP}"

    log_info "从 Git bundle 恢复代码: ${backup_file}"
    mkdir -p "${restore_dir}"
    cd "${restore_dir}"
    git clone "${backup_file}" .

    if [[ $? -eq 0 ]]; then
        log_info "代码已恢复到: ${restore_dir}"
        log_info "请手动检查后复制到生产目录: cp -a ${restore_dir}/* ${PROJECT_ROOT}/"
    else
        log_error "代码恢复失败"
        return 1
    fi
}

# 恢复最新备份
restore_latest() {
    log_step "===== 恢复最新备份 ====="

    local latest_full

    # 查找最新的全量数据库备份
    latest_full=$(ls -t "${BACKUP_DB_DIR}/full"/*.enc 2>/dev/null | head -1)

    if [[ -z "${latest_full}" ]]; then
        latest_full=$(ls -t "${BACKUP_DB_DIR}/full"/*.sql.gz* 2>/dev/null | head -1)
    fi

    if [[ -z "${latest_full}" ]]; then
        log_error "未找到任何数据库备份"
        return 1
    fi

    log_info "找到最新备份: ${latest_full}"

    # 恢复数据库
    restore_db "${latest_full}"

    # 检查代码备份并恢复
    local latest_code
    latest_code=$(ls -t "${BACKUP_CODE_DIR}"/*.bundle 2>/dev/null | head -1)
    if [[ -n "${latest_code}" ]]; then
        log_info "找到最新代码备份: ${latest_code}"
        log_info "代码备份可随时手动恢复: restore_code ${latest_code}"
    fi

    # 检查配置备份
    local latest_config
    latest_config=$(ls -t "${BACKUP_CONFIG_DIR}"/*.enc 2>/dev/null | head -1)
    if [[ -n "${latest_config}" ]]; then
        log_info "找到最新配置备份: ${latest_config}"
    fi

    log_info "数据库恢复完成！请按以下步骤继续："
    echo "  1. 启动服务: docker-compose -f ${DOCKER_COMPOSE_FILE} up -d"
    echo "  2. 检查健康: curl http://localhost:8000/health"
    echo "  3. 验证功能: 运行集成测试"
}

# ==============================================================
# 完整性检查功能
# ==============================================================

check_system() {
    local exit_code=0

    log_step "===== 系统完整性检查 ====="
    echo ""

    # ─── 1. 检查必要命令 ───
    log_step "1/8 检查必要命令..."
    local required_commands=("pg_isready" "psql" "curl" "docker" "git" "python3")
    for cmd in "${required_commands[@]}"; do
        if command -v "${cmd}" &>/dev/null; then
            echo "  ✓ ${cmd} 可用"
        else
            echo "  ✗ ${cmd} 不可用 (非致命)"
        fi
    done

    # ─── 2. 数据库连接检查 ───
    echo ""
    log_step "2/8 检查数据库连接..."
    if command -v pg_isready &>/dev/null; then
        export PGPASSWORD="${DB_PASSWORD}"
        if pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" &>/dev/null; then
            echo "  ✓ 数据库连接正常 (${DB_HOST}:${DB_PORT})"
        else
            echo "  ✗ 数据库连接失败 (${DB_HOST}:${DB_PORT})"
            exit_code=1
        fi
    else
        echo "  - 跳过 (pg_isready 不可用)"
    fi

    # ─── 3. 磁盘空间检查 ───
    echo ""
    log_step "3/8 检查磁盘空间..."
    local threshold_pct=85
    local usage_pct
    usage_pct=$(df "${BACKUP_DIR}" | awk 'NR==2 {print $5}' | tr -d '%')
    if [[ "${usage_pct}" -le "${threshold_pct}" ]]; then
        echo "  ✓ 磁盘使用率: ${usage_pct}% (阈值: ${threshold_pct}%)"
    else
        echo "  ✗ 磁盘使用率: ${usage_pct}% (超过阈值: ${threshold_pct}%)"
        exit_code=1
    fi

    # ─── 4. 备份文件完整性 ───
    echo ""
    log_step "4/8 检查备份文件完整性..."
    local backup_count
    backup_count=$(find "${BACKUP_DB_DIR}" -name "*.enc" -o -name "*.sql.gz" 2>/dev/null | wc -l)
    if [[ "${backup_count}" -gt 0 ]]; then
        echo "  ✓ 数据库备份文件数量: ${backup_count}"
        # 检查最近一次备份是否超过 24 小时
        local latest_backup
        latest_backup=$(find "${BACKUP_DB_DIR}" -name "*.enc" -o -name "*.sql.gz" -type f 2>/dev/null \
            -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | awk '{print $2}')
        if [[ -n "${latest_backup}" ]]; then
            local backup_age=$(( ($(date +%s) - $(stat -c %Y "${latest_backup}" 2>/dev/null || stat -f%m "${latest_backup}" 2>/dev/null)) / 3600 ))
            if [[ "${backup_age}" -le 24 ]]; then
                echo "  ✓ 最近备份距今 ${backup_age} 小时 (在 24 小时窗口内)"
            else
                echo "  ✗ 最近备份距今 ${backup_age} 小时 (超过 24 小时窗口)"
                exit_code=1
            fi
        fi
    else
        echo "  ✗ 未找到数据库备份文件"
        exit_code=1
    fi

    # ─── 5. 应用健康检查 ───
    echo ""
    log_step "5/8 检查应用健康..."
    if curl -sf http://localhost:8000/health &>/dev/null; then
        echo "  ✓ API 健康检查通过"
    else
        echo "  - API 健康检查跳过 (服务可能未运行)"
    fi

    # ─── 6. Docker 容器检查 ───
    echo ""
    log_step "6/8 检查 Docker 容器状态..."
    if command -v docker &>/dev/null; then
        local running_containers
        running_containers=$(docker ps --format '{{.Names}}' 2>/dev/null | wc -l)
        echo "  ✓ 运行中容器数量: ${running_containers}"
        # 列出所有运行中的容器
        if [[ "${running_containers}" -gt 0 ]]; then
            docker ps --format '  - {{.Names}} ({{.Image}}, {{.Status}})' 2>/dev/null
        fi
    else
        echo "  - Docker 不可用"
    fi

    # ─── 7. 异地备份状态 ───
    echo ""
    log_step "7/8 检查异地备份状态..."
    if [[ "${REMOTE_BACKUP_ENABLED}" == "true" ]]; then
        echo "  ✓ 异地备份已启用: ${REMOTE_BACKUP_URL}"
    else
        echo "  - 异地备份未启用 (REMOTE_BACKUP_ENABLED=false)"
    fi

    # ─── 8. 加密密钥 ───
    echo ""
    log_step "8/8 检查加密配置..."
    if [[ -n "${ENCRYPTION_KEY}" ]]; then
        echo "  ✓ 备份加密密钥已配置"
    else
        echo "  - 备份加密密钥未配置 (备份将以明文存储)"
    fi

    # ─── 总结 ───
    echo ""
    echo "═══════════════════════════════════════════"
    if [[ "${exit_code}" -eq 0 ]]; then
        echo -e "${GREEN}  系统完整性检查: 通过${NC}"
    else
        echo -e "${RED}  系统完整性检查: 未通过 (存在需关注的问题)${NC}"
    fi
    echo "═══════════════════════════════════════════"

    return "${exit_code}"
}

# ==============================================================
# 列出备份
# ==============================================================

list_backups() {
    log_step "===== 备份列表 ====="

    echo ""
    echo "── 数据库全量备份 ──"
    if [[ -d "${BACKUP_DB_DIR}/full" ]]; then
        ls -lh "${BACKUP_DB_DIR}/full"/*.enc 2>/dev/null || echo "  (无加密备份)"
        ls -lh "${BACKUP_DB_DIR}/full"/*.sql.gz 2>/dev/null || echo "  (无未加密备份)"
    else
        echo "  (目录不存在)"
    fi

    echo ""
    echo "── 代码备份 ──"
    if [[ -d "${BACKUP_CODE_DIR}" ]]; then
        ls -lh "${BACKUP_CODE_DIR}"/*.bundle 2>/dev/null || echo "  (无备份)"
    else
        echo "  (目录不存在)"
    fi

    echo ""
    echo "── 配置备份 ──"
    if [[ -d "${BACKUP_CONFIG_DIR}" ]]; then
        ls -lh "${BACKUP_CONFIG_DIR}"/*.enc 2>/dev/null || echo "  (无加密备份)"
        ls -lh "${BACKUP_CONFIG_DIR}"/*.tar.gz 2>/dev/null || echo "  (无未加密备份)"
    else
        echo "  (目录不存在)"
    fi

    echo ""
    echo "── 备份元信息 (最近 5 条) ──"
    if [[ -d "${BACKUP_DB_DIR}" ]]; then
        ls -lt "${BACKUP_DB_DIR}"/backup_meta_*.json 2>/dev/null | head -5 || echo "  (无元信息文件)"
    fi
}

# ==============================================================
# 帮助信息
# ==============================================================

show_help() {
    cat <<EOF
AI数字名片 — 灾难恢复脚本

用法:
  $(basename "$0") backup   [full|wal|config|code]   执行备份
  $(basename "$0") restore  [latest|FILE]             执行恢复
  $(basename "$0") check                              完整性检查
  $(basename "$0") list                               列出备份
  $(basename "$0") help                               显示帮助

备份子命令:
  full        数据库全量备份 (默认)
  wal         WAL 归档备份
  config      配置与环境文件备份
  code        Git 代码仓库备份

恢复子命令:
  latest      从最新备份恢复数据库
  FILE        从指定备份文件恢复

环境变量:
  DB_HOST         数据库主机 (default: localhost)
  DB_PORT         数据库端口 (default: 5432)
  DB_NAME         数据库名 (default: ai_digital_business_card)
  DB_USER         数据库用户 (default: postgres)
  DB_PASSWORD     数据库密码
  BACKUP_DIR      备份根目录 (default: ./backups)
  ENCRYPTION_KEY  备份加密密钥 (AES-256-GCM)
  FORCE_RESTORE   跳过恢复等待 (true)
  REMOTE_BACKUP_ENABLED  启用异地同步 (true/false)
  REMOTE_BACKUP_URL      异地存储 URL

示例:
  ./disaster_recovery.sh backup full
  ./disaster_recovery.sh backup config
  ./disaster_recovery.sh restore latest
  ./disaster_recovery.sh restore /path/to/backup.enc
  FORCE_RESTORE=true ./disaster_recovery.sh restore latest
  ./disaster_recovery.sh check
  ./disaster_recovery.sh list
EOF
}

# ==============================================================
# 主入口
# ==============================================================

main() {
    local command="${1:-help}"
    local subcommand="${2:-}"

    # 确保基础目录存在
    ensure_dir "${BACKUP_DIR}"
    ensure_dir "${BACKUP_DB_DIR}"
    ensure_dir "${BACKUP_CODE_DIR}"
    ensure_dir "${BACKUP_CONFIG_DIR}"
    ensure_dir "${BACKUP_LOG_DIR}"

    case "${command}" in
        backup)
            case "${subcommand}" in
                full|"")
                    backup_db_full
                    ;;
                wal)
                    backup_db_wal
                    ;;
                config)
                    backup_config
                    ;;
                code)
                    backup_code
                    ;;
                *)
                    log_error "未知备份类型: ${subcommand}"
                    echo "可用类型: full, wal, config, code"
                    exit 1
                    ;;
            esac
            ;;
        restore)
            case "${subcommand}" in
                latest|"")
                    restore_latest
                    ;;
                *)
                    if [[ -f "${subcommand}" ]]; then
                        restore_db "${subcommand}"
                    else
                        log_error "备份文件不存在: ${subcommand}"
                        exit 1
                    fi
                    ;;
            esac
            ;;
        check)
            check_system
            ;;
        list)
            list_backups
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: ${command}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
