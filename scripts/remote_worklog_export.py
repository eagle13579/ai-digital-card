#!/usr/bin/env python3
"""remote_worklog_export.py — 飞书白泽工作日志增量导出（远程侧）

从 /opt/hermes-remote/home/state.db 只读导出新增会话消息（feishu/cli/cron），
追加写入 sync_out/worklog_YYYYMMDD.jsonl，供本地每30分钟拉取。
幂等：游标文件 sync_out/.cursor 记录最后导出的 message id。

用法:
  python3 remote_worklog_export.py             # 增量导出（默认）
  python3 remote_worklog_export.py --full      # 全量导出（首次）
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/opt/hermes-remote/home")
DB = HOME / "state.db"
SYNC_OUT = HOME / "sync_out"
CURSOR = SYNC_OUT / ".cursor"
FULL = "--full" in sys.argv

BATCH = 500  # 单轮上限（防一次导出过多）

def main():
    SYNC_OUT.mkdir(parents=True, exist_ok=True)
    cursor = 0
    if not FULL and CURSOR.exists():
        try:
            cursor = int(CURSOR.read_text().strip() or "0")
        except ValueError:
            cursor = 0

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # 取新增消息（id 单调递增）
    rows = cur.execute(
        """SELECT m.id, m.session_id, m.role, m.content, m.tool_name, m.timestamp,
                  s.source, s.user_id
           FROM messages m JOIN sessions s ON m.session_id = s.id
           WHERE m.id > ? ORDER BY m.id LIMIT ?""",
        (cursor, BATCH),
    ).fetchall()

    if not rows:
        print(f"[worklog] 无新增 (cursor={cursor})")
        con.close()
        return

    # 按日期分文件追加
    by_day: dict[str, list] = {}
    for r in rows:
        ts = r["timestamp"] or time.time()
        day = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%d")
        by_day.setdefault(day, []).append({
            "id": r["id"],
            "session_id": r["session_id"],
            "source": r["source"],
            "user_id": r["user_id"],
            "role": r["role"],
            "tool_name": r["tool_name"],
            "ts": ts,
            "content": (r["content"] or "")[:4000],
        })

    for day, items in by_day.items():
        out = SYNC_OUT / f"worklog_{day}.jsonl"
        with out.open("a", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        print(f"[worklog] {day}: +{len(items)} 条 → {out.name}")

    new_cursor = rows[-1]["id"]
    CURSOR.write_text(str(new_cursor))
    print(f"[worklog] 游标 {cursor} → {new_cursor}")
    con.close()

if __name__ == "__main__":
    main()
