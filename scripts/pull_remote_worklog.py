#!/usr/bin/env python3
"""pull_remote_worklog.py — 拉取飞书白泽工作日志到本地（本地侧）

从远程 /opt/hermes-remote/home/sync_out/ 增量拉取 worklog_*.jsonl，
落盘 记忆宫殿/远程白泽工作存档/，并生成当日人读摘要 .md。
幂等：.pulled_state.json 记录 文件名→大小，只拉新增/变更。

用法:
  python pull_remote_worklog.py          # 增量拉取
  python pull_remote_worklog.py --md     # 拉取后生成当日摘要
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REMOTE = "root@47.116.116.87"
REMOTE_DIR = "/opt/hermes-remote/home/sync_out"
LOCAL_DIR = Path(r"D:\向海容的知识库\wiki\wiki\记忆宫殿\远程白泽工作存档")
STATE_FILE = LOCAL_DIR / ".pulled_state.json"


def _run(cmd, timeout=120) -> subprocess.CompletedProcess:
    kw = {"capture_output": True, "text": True, "timeout": timeout}
    if os.name == "nt":
        kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    return subprocess.run(cmd, **kw)


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(st: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    quiet = "--quiet" in sys.argv
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    state = load_state()

    # 列出远程 jsonl 文件（大小+名）
    r = _run(["ssh", "-o", "ConnectTimeout=8", "-o", "StrictHostKeyChecking=no",
              REMOTE, f"ls -l {REMOTE_DIR}/worklog_*.jsonl"])
    if r.returncode != 0:
        if not quiet:
            print(f"❌ 远程列表失败: {r.stderr[-200:]}")
        return

    pulled = 0
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        size, name = int(parts[4]), parts[-1].split("/")[-1]
        if not name.endswith(".jsonl"):
            continue
        if state.get(name) == size:
            continue  # 已拉取且大小一致
        dest = LOCAL_DIR / name
        rr = _run(["scp", "-o", "ConnectTimeout=8", "-o", "StrictHostKeyChecking=no",
                   f"{REMOTE}:{REMOTE_DIR}/{name}", str(dest)], timeout=180)
        if rr.returncode == 0:
            state[name] = size
            pulled += 1
            print(f"  [拉取] {name} ({size}B)")
        else:
            if not quiet:
                print(f"  [失败] {name}: {rr.stderr[-150:]}")

    save_state(state)
    if pulled > 0:
        print(f"✅ 本次拉取 {pulled} 个文件，存档: {LOCAL_DIR}")
    elif not quiet:
        print("✅ 无新工作日志")

    # 生成当日可读摘要
    gen_md(LOCAL_DIR)


def gen_md(directory: Path):
    """把当天 jsonl 汇总为人读摘要 md"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    src = directory / f"worklog_{today}.jsonl"
    if not src.exists():
        return
    out = directory / f"白泽工作摘要_{today}.md"
    entries = []
    for line in src.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not entries:
        return

    lines = [f"# 飞书白泽工作摘要 {today}（{len(entries)} 条）\n"]
    for e in entries:
        ts = datetime.fromtimestamp(e.get("ts", 0), tz=timezone.utc).strftime("%H:%M")
        role = e.get("role", "?")
        src_name = e.get("source", "?")
        content = (e.get("content") or "").replace("\n", " ")[:160]
        tool = f" [tool:{e.get('tool_name')}]" if e.get("tool_name") else ""
        lines.append(f"- `{ts}` [{src_name}/{role}]{tool} {content}")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ 摘要生成: {out.name}")


if __name__ == "__main__":
    main()
