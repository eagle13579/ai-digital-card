#!/bin/bash
# ============================================================
# backup.sh — AI Digital Card 数据库 + 文件备份脚本
# 功能: 备份 SQLite 数据库 & uploads 目录, 保留最近 7 天
# 用法: ./scripts/backup.sh [backup_dir]
# 默认备份目录: /app/backups
# ============================================================

set -euo pipefail

# ---------- 配置 ----------
APP_DIR="/app"
DATA_DIR="${APP_DIR}/data"
UPLOADS_DIR="${APP_DIR}/uploads"
DB_FILE="${DATA_DIR}/digital_card.db"

BACKUP_BASE="${1:-/app/backups}"
BACKUP_DIR="${BACKUP_BASE}/$(date +%Y%m%d_%H%M%S)"
RETENTION_DAYS=7

TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
LOG_FILE="${BACKUP_BASE}/backup.log"

# ---------- 工具函数 ----------
log() {
    echo "[${TIMESTAMP}] $*" | tee -a "${LOG_FILE}"
}

cleanup_old_backups() {
    log "清理 ${RETENTION_DAYS} 天前的备份..."
    find "${BACKUP_BASE}" -maxdepth 1 -type d -name "????????_??????" -mtime +${RETENTION_DAYS} -exec rm -rf {} \; -exec log "  已删除: {}" \;
    log "清理完成"
}

# ---------- 主流程 ----------
mkdir -p "${BACKUP_DIR}"
log "=== 备份开始: ${BACKUP_DIR} ==="

# ---- 1. 备份 SQLite 数据库 ----
if [ -f "${DB_FILE}" ]; then
    DB_BACKUP="${BACKUP_DIR}/digital_card.db"
    # 使用 sqlite3 的 .backup 命令确保一致性备份
    if command -v sqlite3 &>/dev/null; then
        sqlite3 "${DB_FILE}" ".backup '${DB_BACKUP}'"
        log "数据库备份完成 (sqlite3 .backup): ${DB_BACKUP}"
    else
        # 降级: 直接拷贝 (要求应用不在写入)
        cp -p "${DB_FILE}" "${DB_BACKUP}"
        log "数据库备份完成 (cp): ${DB_BACKUP} (未安装 sqlite3, 使用文件拷贝)"
    fi
else
    log "警告: 数据库文件不存在: ${DB_FILE}"
fi

# ---- 2. 备份 uploads 目录 ----
if [ -d "${UPLOADS_DIR}" ] && [ "$(ls -A "${UPLOADS_DIR}" 2>/dev/null)" ]; then
    UPLOADS_BACKUP="${BACKUP_DIR}/uploads.tar.gz"
    tar -czf "${UPLOADS_BACKUP}" -C "$(dirname "${UPLOADS_DIR}")" "$(basename "${UPLOADS_DIR}")"
    log "上传文件备份完成: ${UPLOADS_BACKUP}"
else
    log "上传目录为空或不存在, 跳过: ${UPLOADS_DIR}"
fi

# ---- 3. 生成备份清单 ----
MANIFEST="${BACKUP_DIR}/MANIFEST.txt"
{
    echo "备份时间: ${TIMESTAMP}"
    echo "备份目录: ${BACKUP_DIR}"
    echo ""
    echo "内容清单:"
    ls -lh "${BACKUP_DIR}/" 2>/dev/null | tail -n +2
} > "${MANIFEST}"
log "备份清单生成: ${MANIFEST}"

# ---- 4. 清理过期备份 ----
cleanup_old_backups

# ---- 5. 完成 ----
log "=== 备份完成: ${BACKUP_DIR} ==="
echo ""
echo "备份总计:"
du -sh "${BACKUP_DIR}"
echo ""
echo "现有备份列表:"
ls -1d "${BACKUP_BASE}"/????????_?????? 2>/dev/null | sort || echo "  (无)"

exit 0
