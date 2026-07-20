#!/bin/bash
# AI数智名片 → 盖娅大脑反哺管道
# 功能: 扫描心智模型文档(analysis/ docs/ L5孵化室/) → 复制到profile → 反哺到母体
# 用法: bash backfeed_to_gaia.sh
set -euo pipefail

# ── 配置 ──
GAIA_ENGINE="C:/Users/56867/.local/bin/backfeed_engine.py"
MOTHER_SYNC="C:/Users/56867/.local/bin/mother_sync.py"
PROFILE="ai-digital-card"
PROJECT_DIR="D:/AI数智名片/backend"
PALACE_BASE="D:/向海容的知识库/wiki/wiki/记忆宫殿"
MENTAL_MODELS_DIR="${PALACE_BASE}/profiles/${PROFILE}/mental_models"

echo "============================================"
echo "  AI数智名片 → 盖娅大脑反哺管道"
echo "  Profile: ${PROFILE}"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo ""

# Step 1: 确保目标目录存在
mkdir -p "${MENTAL_MODELS_DIR}" || {
  echo "FAIL: 无法创建目录 ${MENTAL_MODELS_DIR}"
  exit 1
}
echo "[STEP 1/4] 目标目录就绪: ${MENTAL_MODELS_DIR}"

# Step 2: 扫描并复制心智模型文档
echo ""
echo "[STEP 2/4] 扫描心智模型文档..."

# 定义扫描目录
SCAN_DIRS=(
  "${PROJECT_DIR}/analysis"
  "${PROJECT_DIR}/docs"
  "${PROJECT_DIR}/L5孵化室"
)

new_count=0
for src_dir in "${SCAN_DIRS[@]}"; do
  if [ ! -d "${src_dir}" ]; then
    echo "  [SKIP] 源目录不存在: ${src_dir}"
    continue
  fi

  echo "  扫描: ${src_dir}"
  while IFS= read -r -d '' md_file; do
    [ -f "${md_file}" ] || continue

    # 生成目标文件名: 用相对路径替换分隔符
    rel_path="${md_file#$PROJECT_DIR/}"
    model_name=$(echo "${rel_path}" | tr '/\\' '_')
    target="${MENTAL_MODELS_DIR}/${model_name}"

    if [ ! -f "${target}" ]; then
      if ! cp "${md_file}" "${target}"; then
        echo "  FAIL: 复制失败 ${md_file}"
        exit 1
      fi
      echo "  [NEW] ${model_name}"
      new_count=$((new_count + 1))
    else
      echo "  [SKIP] 已存在: ${model_name}"
    fi
  done < <(find "${src_dir}" -name "*.md" -type f -print0 2>/dev/null)
done

echo "  新增: ${new_count} 个文件"
total_md=$(find "${MENTAL_MODELS_DIR}" -name "*.md" -type f 2>/dev/null | wc -l)
echo "  心智模型总数: ${total_md}"

# Step 3: 反哺到母体
echo ""
echo "[STEP 3/4] 反哺到母体记忆宫殿..."

backfeed_count=0
for model_file in "${MENTAL_MODELS_DIR}"/*.md; do
  [ -f "${model_file}" ] || continue
  model_name=$(basename "${model_file}")

  if ! python "${GAIA_ENGINE}" --backfeed-model "${PROFILE}" "${model_name}" "${model_file}"; then
    echo "  FAIL: 反哺失败 ${model_name}"
    exit 1
  fi
  echo "  [反哺] ${model_name}"
  backfeed_count=$((backfeed_count + 1))
done
echo "  反哺完成: ${backfeed_count} 个心智模型"

# Step 4: 增量同步
echo ""
echo "[STEP 4/4] 母体增量同步..."

if ! python "${MOTHER_SYNC}" --incremental; then
  echo "FAIL: mother_sync --incremental 失败"
  exit 1
fi
echo "  [OK] 增量同步完成"

echo ""
echo "============================================"
echo "  ✅ 反哺管道执行完毕"
echo "  Profile: ${PROFILE}"
echo "  心智模型: ${backfeed_count} 个"
echo "============================================"
