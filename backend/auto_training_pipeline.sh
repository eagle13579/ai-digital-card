#!/bin/bash
# ==============================================================
# auto_training_pipeline.sh — 用户增长驱动模型自动训练管道
# 每15分钟运行一次，自动完成:
#   Step 1: 用户数据增强（更新match_records匹配对）
#   Step 2: 准备训练数据（构建V2特征集 → v2_training_data.json）
#   Step 3: 训练V2三塔匹配模型（防过拟合版）
#   Step 4: 输出训练报告摘要
# ==============================================================

set -e

BACKEND_DIR="/d/AI数智名片/backend"
REPORT_PATH="$BACKEND_DIR/models/training_report_v2.json"
START_TIME=$(date +%s)

cd "$BACKEND_DIR"

echo ""
echo "=========================================="
echo "  🔄 自动训练管道开始"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# ── Step 1: 用户数据增强 ────────────────────────────────────
echo ""
echo "━━━ [Step 1/4] 用户数据增强（更新匹配对） ━━━"

ENHANCE_OUTPUT=$(python scripts/enhance_user_data.py 2>&1)
ENHANCE_EXIT=$?

if [ $ENHANCE_EXIT -ne 0 ]; then
    echo "❌ 用户数据增强失败 (exit=$ENHANCE_EXIT)"
    echo "$ENHANCE_OUTPUT" | tail -20
    echo ""
    echo "⚠️  管道暂停，等待下次触发"
    echo "=========================================="
    exit 1
fi

echo "$ENHANCE_OUTPUT"

# 提取新增匹配对数用于报告
NEW_PAIRS=$(echo "$ENHANCE_OUTPUT" | grep "新生成匹配对" | grep -oP '\d+' | head -1)
TOTAL_PAIRS=$(echo "$ENHANCE_OUTPUT" | grep "全量用户对" | grep -oP '\d+' | head -1)
echo "✅ Step 1 完成: 新增 $NEW_PAIRS 匹配对"

# ── Step 2: 准备训练数据 ────────────────────────────────────
echo ""
echo "━━━ [Step 2/4] 准备训练数据（V2特征集） ━━━"

PREPARE_OUTPUT=$(python scripts/prepare_v2_training_data.py 2>&1)
PREPARE_EXIT=$?

if [ $PREPARE_EXIT -ne 0 ]; then
    echo "❌ 训练数据准备失败 (exit=$PREPARE_EXIT)"
    echo "$PREPARE_OUTPUT" | tail -20
    echo ""
    echo "⚠️  管道暂停，等待下次触发"
    echo "=========================================="
    exit 1
fi

echo "$PREPARE_OUTPUT"

TOTAL_SAMPLES=$(echo "$PREPARE_OUTPUT" | grep "总样本数" | grep -oP '\d+' | head -1)
echo "✅ Step 2 完成: $TOTAL_SAMPLES 训练样本"

# ── Step 3: 训练匹配模型 ────────────────────────────────────
echo ""
echo "━━━ [Step 3/4] 训练V2三塔匹配模型 ━━━"

# 基础设施层保护：Step 3 训练耗时可能 >30s，加 timeout 防卡死
TIMEOUT_SEC=55
echo "  ⏱️  训练超时保护: ${TIMEOUT_SEC}秒"
TRAIN_OUTPUT=$(timeout $TIMEOUT_SEC python scripts/train_matching_model_v2.py 2>&1)
TRAIN_EXIT=$?

if [ $TRAIN_EXIT -ne 0 ]; then
    echo "❌ 模型训练失败 (exit=$TRAIN_EXIT)"
    echo "$TRAIN_OUTPUT" | tail -20
    echo ""
    echo "⚠️  管道暂停，等待下次触发"
    echo "=========================================="
    exit 1
fi

echo "$TRAIN_OUTPUT"
echo "✅ Step 3 完成: 模型已保存"

# ── Step 4: 训练报告 ────────────────────────────────────────
echo ""
echo "━━━ [Step 4/4] 训练报告摘要 ━━━"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
DURATION_MIN=$(echo "scale=1; $DURATION / 60" | bc)

if [ -f "$REPORT_PATH" ]; then
    echo "📊 训练报告有效: $REPORT_PATH"
    python -c "
import json
with open('$REPORT_PATH', 'r', encoding='utf-8') as f:
    r = json.load(f)

train_m = r.get('metrics', {}).get('train', {})
val_m = r.get('metrics', {}).get('val', {})
hist = r.get('training_history', {})

print(f'  ┌─ 训练集 ─────────────────────────────┐')
print(f'  │  准确率 (Accuracy):  {train_m.get(\"accuracy\", \"N/A\"):>10s}          │' if isinstance(train_m.get('accuracy'), str) else f'  │  准确率 (Accuracy):  {train_m.get(\"accuracy\", 0):>10.4f}          │')
print(f'  │  AUC:               {train_m.get(\"auc\", \"N/A\"):>10s}          │' if isinstance(train_m.get('auc'), str) else f'  │  AUC:               {train_m.get(\"auc\", 0):>10.4f}          │')
print(f'  └─────────────────────────────────────────┘')
print(f'  ┌─ 验证集 ─────────────────────────────┐')
print(f'  │  准确率 (Accuracy):  {val_m.get(\"accuracy\", \"N/A\"):>10s}          │' if isinstance(val_m.get('accuracy'), str) else f'  │  准确率 (Accuracy):  {val_m.get(\"accuracy\", 0):>10.4f}          │')
print(f'  │  AUC:               {val_m.get(\"auc\", \"N/A\"):>10s}          │' if isinstance(val_m.get('auc'), str) else f'  │  AUC:               {val_m.get(\"auc\", 0):>10.4f}          │')
print(f'  └─────────────────────────────────────────┘')
print(f'  训练轮数: {hist.get(\"epochs_trained\", \"N/A\")}')
print(f'  样本总数: {r.get(\"data_summary\", {}).get(\"total_samples\", \"N/A\")}')
print(f'  总耗时:   ${DURATION_MIN} 分钟')
"
else
    echo "⚠️  训练报告未找到（首次运行或训练失败）"
    echo "  路径: $REPORT_PATH"
fi

echo ""
echo "=========================================="
echo "  ✅ 自动训练管道完成"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  总耗时: ${DURATION_MIN} 分钟"
echo "  新增匹配对: $NEW_PAIRS"
echo "  训练样本: $TOTAL_SAMPLES"
echo "=========================================="
