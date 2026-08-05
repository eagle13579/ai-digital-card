#!/bin/bash
# ============================================================
# Mac Mini 数据管道一键部署脚本
# 用法: bash deploy_to_mac.sh [MAC_IP] [MAC_USER]
#   MAC_IP    - Mac Mini IP (默认 192.168.31.237)
#   MAC_USER  - SSH用户名 (默认 eagle)
# ============================================================
set -e

MAC_IP="${1:-192.168.31.237}"
MAC_USER="${2:-eagle}"
WIN_PIPELINE="D:/AI数智名片/backend/data_pipeline"
WIN_DATA="D:/AI数智名片/backend/data"

echo "=========================================="
echo " Mac Mini 数据管道部署"
echo "=========================================="
echo "  目标: ${MAC_USER}@${MAC_IP}"
echo "  管道: ${WIN_PIPELINE}"
echo ""

# 检查 SSH 连通性
echo "🔍 检查 SSH 连接..."
if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "${MAC_USER}@${MAC_IP}" "echo connected" 2>/dev/null; then
    echo "❌ SSH 无法连接！请确认:"
    echo "   1. Mac Mini 已开机"
    echo "   2. 已开启 SSH (设置→通用→共享→远程登录)"
    echo "   3. 网络互通 (同一局域网)"
    echo "   4. IP 是否正确 (当前: ${MAC_IP})"
    exit 1
fi
echo "✅ SSH 连接正常"
echo ""

# Step 1: 创建目录结构
echo "📁 Step 1: 创建目录结构..."
ssh "${MAC_USER}@${MAC_IP}" "mkdir -p ~/pipeline/logs ~/pipeline_data/models ~/pipeline_data/raw ~/pipeline_data/curated"
echo "✅ 目录已创建"

# Step 2: 同步管道代码
echo "📦 Step 2: 同步管道代码..."
rsync -avz --delete \
    "${WIN_PIPELINE}/" \
    "${MAC_USER}@${MAC_IP}:~/pipeline/"
echo "✅ 管道代码已同步"

# Step 3: 同步训练数据
echo "📊 Step 3: 同步训练数据..."
rsync -avz \
    --include="training_data.json" \
    --include="v2_training_data.json" \
    --include="online_weights.json" \
    --include="learning_log.jsonl" \
    --include="models/" \
    --include="raw/" \
    --include="curated/" \
    --exclude="*" \
    "${WIN_DATA}/" \
    "${MAC_USER}@${MAC_IP}:~/pipeline_data/"
echo "✅ 训练数据已同步"

# Step 4: 安装 launchd plist
echo "⚡ Step 4: 安装 launchd 7×24服务..."
PLIST_SRC="~/pipeline/mac/mac_pipeline_trainer.plist"
PLIST_DST="~/Library/LaunchAgents/mac_pipeline_trainer.plist"

ssh "${MAC_USER}@${MAC_IP}" "cp ${PLIST_SRC} ${PLIST_DST} && launchctl unload ${PLIST_DST} 2>/dev/null; launchctl load ${PLIST_DST}"
echo "✅ launchd 已安装"

# Step 5: 首次验证
echo "🧪 Step 5: 首次 dry-run 验证..."
ssh "${MAC_USER}@${MAC_IP}" "cd ~/pipeline && python3 mac_pipeline_trainer.py --dry-run"
echo "✅ 首次验证完成"

echo ""
echo "=========================================="
echo " 🎉 部署完成!"
echo "=========================================="
echo ""
echo "  Mac Mini 上已安装:"
echo "    ~/pipeline/            - 数据管道代码"
echo "    ~/pipeline_data/       - 训练数据"
echo "    ~/pipeline/logs/       - 运行日志"
echo "    launchd: com.gaia.pipeline.trainer - 每30分钟训练"
echo ""
echo "  常用命令:"
echo "    ssh ${MAC_USER}@${MAC_IP}"
echo "    # 查看状态"
echo "    launchctl list | grep pipeline"
echo "    # 手动触发一次"
echo "    cd ~/pipeline && python3 mac_pipeline_trainer.py"
echo "    # 查看日志"
echo "    tail -f ~/pipeline/logs/trainer.log"
echo ""
echo "  Windows 上的 cron 保持不变 (采集+清洗+质量)"
echo "  Mac Mini 负责训练 (7×24)"
echo ""
