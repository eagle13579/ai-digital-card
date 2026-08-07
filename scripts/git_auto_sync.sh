#!/bin/bash
# ============================================================
# git_auto_sync.sh — 代码双向自动同步（服务器侧）
# 设计原则:
#   1. 只 fetch + --ff-only 快进（绝不 merge，避免自动冲突）
#   2. feature/* 分支: 本地领先自动 push（feature 天生为 push 而生）
#   3. master/develop/releaseV1.0: 只 pull 不 push（master 只进不出=合规铁律）
#   4. 工作区有未提交改动时跳过 pull（不碰用户 WIP）
#   5. 静默原则: 有变化才输出，无变化零输出（供 cron no_agent）
# ============================================================
set -u

REPO="/var/www/ai-digital-card"
LOG="/opt/hermes-remote/home/state/git_auto_sync.log"
CHANGES=""

for dir in "$REPO" /var/www/liankebao; do
  [ -d "$dir/.git" ] || continue
  cd "$dir" || continue
  REPO_NAME=$(basename "$dir")

  # 1. fetch 远端
  git fetch origin --prune 2>/dev/null

  # 2. 当前分支工作区检查
  DIRTY=$(git status --porcelain 2>/dev/null | wc -l)

  # 3. 遍历本地分支
  while read -r BRANCH; do
    [ -z "$BRANCH" ] && continue
    # 跳过非跟踪分支
    UPSTREAM=$(git for-each-ref --format='%(upstream:short)' "refs/heads/$BRANCH" 2>/dev/null)
    [ -z "$UPSTREAM" ] && continue

    AHEAD=$(git rev-list --count "$UPSTREAM..$BRANCH" 2>/dev/null || echo 0)
    BEHIND=$(git rev-list --count "$BRANCH..$UPSTREAM" 2>/dev/null || echo 0)
    AHEAD=${AHEAD:-0}; BEHIND=${BEHIND:-0}

    # --- 推送方向: feature/* 本地领先 → push（服务器开发成果自动上 GitHub）---
    if [ "$AHEAD" -gt 0 ] && [[ "$BRANCH" == feature/* ]]; then
      OUT=$(git push origin "$BRANCH" 2>&1)
      if [ $? -eq 0 ]; then
        CHANGES="${CHANGES}[$REPO_NAME] PUSH $BRANCH (+$AHEAD)\n"
        echo "$(date '+%F %T') PUSH $BRANCH (+$AHEAD) $OUT" >> "$LOG"
      else
        CHANGES="${CHANGES}[$REPO_NAME] PUSH_FAIL $BRANCH: $OUT\n"
        echo "$(date '+%F %T') PUSH_FAIL $BRANCH $OUT" >> "$LOG"
      fi
    fi

    # --- 拉取方向: 落后且工作区干净 → ff-only 快进（只对当前分支 pull）---
    if [ "$BEHIND" -gt 0 ]; then
      CUR=$(git branch --show-current 2>/dev/null)
      if [ "$BRANCH" = "$CUR" ]; then
        if [ "$DIRTY" -eq 0 ]; then
          OUT=$(git pull --ff-only 2>&1)
          if [ $? -eq 0 ]; then
            CHANGES="${CHANGES}[$REPO_NAME] PULL $BRANCH (-$BEHIND)\n"
            echo "$(date '+%F %T') PULL $BRANCH (-$BEHIND) $OUT" >> "$LOG"
          else
            CHANGES="${CHANGES}[$REPO_NAME] PULL_FAIL $BRANCH: $OUT\n"
            echo "$(date '+%F %T') PULL_FAIL $BRANCH $OUT" >> "$LOG"
          fi
        else
          CHANGES="${CHANGES}[$REPO_NAME] SKIP $BRANCH (工作区有WIP，-${BEHIND}待拉)\n"
          echo "$(date '+%F %T') SKIP $BRANCH (WIP) behind=$BEHIND" >> "$LOG"
        fi
      fi
    fi
  done < <(git for-each-ref --format='%(refname:short)' refs/heads/)
done

# 4. 输出变化（供 cron no_agent: 空=静默）
if [ -n "$CHANGES" ]; then
  echo -e "🔄 代码自动同步完成:"
  echo -e "$CHANGES"
fi
exit 0
