#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# AI数字名片 — 健康监控 wrapper (oneshot, 每5分钟由 timer 触发)
# 检查后端 /health 是否正常；异常时向飞书群发告警
# 重建: 2026-08-04 白泽远程分身 (原脚本缺失导致 status=203/EXEC)
# ═══════════════════════════════════════════════════════════════
set -uo pipefail

BACKEND_URL="http://127.0.0.1:8201/health"
LOG_FILE="/var/log/ai-digital-card/health_monitor.log"
STATE_FILE="/tmp/ai-digital-card-health-state"

# 飞书告警（应用凭证方式，发到海容 DM）
FEISHU_ALERT_PY="/root/legion-watchdog/feishu_alert.py"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }

# 读取上次状态 (0=健康, 1=异常)
last_state=0
[[ -f "$STATE_FILE" ]] && last_state=$(cat "$STATE_FILE" 2>/dev/null || echo 0)

mkdir -p /var/log/ai-digital-card

if curl -sf -m 10 "$BACKEND_URL" >/dev/null 2>&1; then
    log "✅ 健康检查通过: $BACKEND_URL"
    echo 0 > "$STATE_FILE"
    exit 0
fi

# 服务异常
log "❌ 健康检查失败: $BACKEND_URL"
echo 1 > "$STATE_FILE"

# 仅在状态翻转(健康→异常)时告警，避免重复轰炸
if [[ "$last_state" == "0" ]]; then
    MSG="⚠️ AI数字名片健康告警
时间: $(date '+%Y-%m-%d %H:%M:%S')
服务: ai-digital-card (:8201)
状态: 健康检查失败，请检查服务状态
命令: systemctl status ai-digital-card.service"
    if [[ -f "$FEISHU_ALERT_PY" ]]; then
        python3 "$FEISHU_ALERT_PY" "$MSG" >/dev/null 2>&1 && \
            log "📣 飞书告警已发送" || log "⚠️ 飞书告警发送失败"
    else
        log "📣 飞书告警脚本缺失: $FEISHU_ALERT_PY（仅记录）"
    fi
fi

exit 1
