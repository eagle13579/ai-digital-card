#!/usr/bin/env python3
"""local_master_sync_check.py — 检测服务器(白泽)新成果回流（本地侧）

版本管理闭环的一环：白泽在服务器上开发的提交（feature→merge master→push）
通过 GitHub master 回流。本脚本检测漂移并通知，防止本地 develop 与
服务器 master 长期分叉（当前曾漂移 53 提交）。

逻辑:
  1. 主仓库 fetch origin（更新引用）
  2. 比较 develop vs origin/master 漂移
  3. 服务器领先>0 → 输出"需回流"通知（cron no_agent: 有输出才投递）
     --quiet: 无漂移时零输出（看门狗模式）

用法:
  python local_master_sync_check.py          # 检测+输出
  python local_master_sync_check.py --quiet  # cron 模式
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(r"D:\AI数智名片")


def _run(cmd, timeout=120) -> subprocess.CompletedProcess:
    kw = {"capture_output": True, "text": True, "timeout": timeout}
    if os.name == "nt":
        kw["creationflags"] = 0x08000000
    return subprocess.run(cmd, **kw)


def main():
    quiet = "--quiet" in sys.argv
    if not (REPO / ".git").exists():
        if not quiet:
            print(f"❌ 仓库不存在: {REPO}")
        return

    # 1. 更新远端引用（主仓库已配 core.sshCommand）
    r = _run(["git", "-C", str(REPO), "fetch", "origin"])
    if r.returncode != 0:
        if not quiet:
            print(f"❌ fetch 失败: {r.stderr[-200:]}")
        return

    # 2. 漂移统计
    ahead_server = _run(["git", "-C", str(REPO), "rev-list", "--count", "develop..origin/master"])
    ahead_local = _run(["git", "-C", str(REPO), "rev-list", "--count", "origin/master..develop"])
    try:
        n_server = int(ahead_server.stdout.strip() or "0")
        n_local = int(ahead_local.stdout.strip() or "0")
    except ValueError:
        return

    if n_server == 0:
        if not quiet:
            print(f"✅ 无漂移：develop 与 master 同步（本地领先 {n_local}）")
        return  # 服务器无新成果 → 静默

    # 3. 有漂移 → 输出回流提示（cron 会投递）
    recent = _run(["git", "-C", str(REPO), "log", "--oneline", "-3", "develop..origin/master"])
    print("🔔 白泽在服务器有新成果，需要回流本地：")
    print(f"   服务器 master 领先本地 develop {n_server} 个提交（本地领先 {n_local}）")
    print("   最近提交:")
    for line in (recent.stdout or "").strip().splitlines()[:3]:
        print(f"     {line}")
    print("   回流操作: git checkout develop && git merge origin/master")
    print("   (或: git merge origin/master --no-edit，冲突时人工解决)")


if __name__ == "__main__":
    main()
