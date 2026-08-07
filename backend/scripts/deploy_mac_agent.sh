#!/usr/bin/env bash
# Mac mini 上报脚本自动部署器 (v1.0)
# 由 本地Windows 自举触发, SSH 到 Mac mini(192.168.1.233) 部署上报脚本 + 注册 crontab
# 用法: bash deploy_mac_agent.sh
set -e

MAC_HOST="eagle@192.168.1.233"
MAC_HOME="/Users/eagle"
AGENT_DIR="$MAC_HOME/mac-report-agent"
SCRIPT_URL="https://raw.githubusercontent.com/eagle13579/ai-digital-card/feature/trust-engine-merge/backend/scripts/mac_mini_models_report.py"

echo "[1/3] 测试 Mac SSH 连通性..."
if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$MAC_HOST" "echo ok" 2>/dev/null; then
    echo "❌ Mac SSH 不通: $MAC_HOST"
    echo "   检查: ①Mac是否开机 ②Windows能否ssh eagle@192.168.1.233 ③免密是否配置"
    exit 1
fi

echo "[2/3] 部署上报脚本到 Mac..."
ssh -o StrictHostKeyChecking=no "$MAC_HOST" "mkdir -p $AGENT_DIR"
ssh -o StrictHostKeyChecking=no "$MAC_HOST" "curl -fsSL '$SCRIPT_URL' -o $AGENT_DIR/mac_mini_models_report.py && chmod +x $AGENT_DIR/mac_mini_models_report.py && echo '脚本已下载'"

echo "[3/3] 注册 crontab (每30分钟)..."
ssh -o StrictHostKeyChecking=no "$MAC_HOST" "
    (crontab -l 2>/dev/null | grep -v 'mac_mini_models_report'; echo '*/30 * * * * /usr/bin/python3 $AGENT_DIR/mac_mini_models_report.py >> $MAC_HOME/mac_mini_report.log 2>&1') | crontab -
    crontab -l | grep mac_mini_models_report && echo '✅ crontab 已注册'
"

echo "[验证] 立即手动跑一次..."
ssh -o StrictHostKeyChecking=no "$MAC_HOST" "/usr/bin/python3 $AGENT_DIR/mac_mini_models_report.py"

echo "🎉 Mac mini 上报代理部署完成!"
