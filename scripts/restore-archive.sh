#!/usr/bin/env bash
# 恢复存档版本到 miniapp/
# 用法: ./scripts/restore-archive.sh <存档目录名>
# 示例: ./scripts/restore-archive.sh miniapp_current_20260704_193345

set -e

ARCHIVE_NAME="$1"
BASE_DIR="D:/AI数智名片"
ARCHIVE_DIR="$BASE_DIR/_archive/$ARCHIVE_NAME"
TARGET_DIR="$BASE_DIR/miniapp"

if [ -z "$ARCHIVE_NAME" ]; then
  echo "用法: ./scripts/restore-archive.sh <存档目录名>"
  echo "可用存档:"
  ls -1 "$BASE_DIR/_archive/"
  exit 1
fi

if [ ! -d "$ARCHIVE_DIR" ]; then
  echo "错误: 存档目录不存在: $ARCHIVE_DIR"
  exit 1
fi

echo "恢复 $ARCHIVE_NAME → miniapp/ ..."

# 清空目标目录
rm -rf "$TARGET_DIR"/*

# 复制存档
cp -r "$ARCHIVE_DIR"/* "$TARGET_DIR/"

echo "✅ 恢复完成！当前 miniapp/ 内容:"
ls -la "$TARGET_DIR/"
