#!/usr/bin/env python3
"""memory_pruner.py — 军团记忆修剪与去重（P2-5 工程健壮性）

全员 158 个 memory.db 的定期健康维护：
  1. 去重：删除完全重复的 memories 行（保留最早一条）
  2. 限长：content 超过 MAX_LEN 的截断（防止单条记忆无限膨胀）
  3. 限条：每个员工记忆超过 MAX_ROWS 时，按 created_at 裁剪最旧
  4. 压缩：VACUUM 回收空间
  5. 报告：输出修剪统计（供 cron 汇报）

用法:
    python3 memory_pruner.py            # 全量修剪
    python3 memory_pruner.py --dry      # 只预览不动数据
"""
from __future__ import annotations

import argparse
import glob
import os
import sqlite3
import time
from pathlib import Path

SOUL_BASE = Path("/app/gaia-commercial/apps/services/ai_legion/employees")
MAX_CONTENT_LEN = 2000   # 单条记忆最大字符数（超出截断）
MAX_ROWS_PER_DB = 200    # 每个员工记忆上限（超出删最旧）
MIN_ROWS_KEEP = 20       # 即使超限也至少保留的条数


def prune_db(db_path: Path, dry: bool) -> dict:
    """修剪单个 memory.db，返回统计。"""
    stats = {"db": str(db_path), "dup_removed": 0, "truncated": 0, "pruned_old": 0, "rows": 0}
    try:
        conn = sqlite3.connect(str(db_path), timeout=10)
        cur = conn.cursor()

        # 1. 去重（保留最小 id = 最早）
        cur.execute("SELECT COUNT(*) FROM memories")
        stats["rows"] = cur.fetchone()[0]
        if stats["rows"] == 0:
            conn.close()
            return stats

        if not dry:
            cur.execute("""
                DELETE FROM memories
                WHERE id NOT IN (
                    SELECT MIN(id) FROM memories GROUP BY content
                )
            """)
            stats["dup_removed"] = cur.rowcount

        # 2. 限长截断
        cur.execute("SELECT id, content FROM memories")
        rows = cur.fetchall()
        for rid, content in rows:
            if content and len(content) > MAX_CONTENT_LEN:
                stats["truncated"] += 1
                if not dry:
                    cur.execute(
                        "UPDATE memories SET content=? WHERE id=?",
                        (content[:MAX_CONTENT_LEN] + "\n…[截断]", rid),
                    )

        # 3. 限条裁剪（保留最新 MIN_ROWS_KEEP..MAX_ROWS_PER_DB 条）
        total = stats["rows"] - stats["dup_removed"]
        if total > MAX_ROWS_PER_DB:
            keep = max(MIN_ROWS_KEEP, MAX_ROWS_PER_DB)
            stats["pruned_old"] = total - keep
            if not dry:
                cur.execute("""
                    DELETE FROM memories WHERE id IN (
                        SELECT id FROM memories
                        ORDER BY created_at ASC
                        LIMIT ?
                    )
                """, (total - keep,))

        if not dry:
            conn.commit()
            cur.execute("VACUUM")
        conn.close()
    except Exception as exc:  # noqa: BLE001
        # 缺表/空库等无害错误 → 跳过不报错
        if "no such table" in str(exc):
            stats["skipped"] = True
        else:
            stats["error"] = repr(exc)
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description="军团记忆修剪与去重")
    ap.add_argument("--dry", action="store_true", help="预览模式")
    args = ap.parse_args()

    dbs = sorted(glob.glob(str(SOUL_BASE / "*" / "memory" / "memory.db")))

    total = {"dup_removed": 0, "truncated": 0, "pruned_old": 0}
    errors: list[str] = []
    for db in dbs:
        s = prune_db(Path(db), args.dry)
        for k in ("dup_removed", "truncated", "pruned_old"):
            total[k] += s.get(k, 0)
        if s.get("error"):
            errors.append(f"  ⚠️ {db}: {s['error']}")
    mode = "预览(dry)" if args.dry else "完成"

    # 静默策略：无修剪、无错误 → 不输出（cron 空输出=不推送）
    did_work = total["dup_removed"] or total["truncated"] or total["pruned_old"]
    if not did_work and not errors:
        return 0

    if errors:
        print("\n".join(errors))
    print(f"🧹 修剪{mode}: 去重 {total['dup_removed']} | 截断 {total['truncated']} | 裁剪 {total['pruned_old']}（扫描 {len(dbs)} 库）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
