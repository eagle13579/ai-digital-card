#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
git_auto_sync_local.py — 代码自动双向同步（本地 Windows 侧）
与服务器侧 git_auto_sync.sh 配对，实现「本地 ↔ GitHub ↔ 服务器」三地自动同步。

设计原则（与服务器侧一致）:
  1. 只 fetch + --ff-only 快进（绝不 merge，避免自动冲突）
  2. feature/* 分支: 本地领先自动 push（feature 天生为 push 而生）
  3. master/develop/releaseV1.0: 只 pull 不 push（master 只进不出=合规铁律）
  4. 工作区有未提交改动时跳过 pull（不碰用户 WIP）
  5. 静默原则: 有变化才输出，无变化零输出

用法:
  python git_auto_sync_local.py               # 同步默认仓库 D:/AI数智名片
  python git_auto_sync_local.py --repo <dir>  # 指定仓库
  python git_auto_sync_local.py --setup       # 注册 Windows 计划任务（每15分钟，静默）
"""
import argparse
import os
import subprocess
import sys
import time

DEFAULT_REPO = r"D:\AI数智名片"
LOG = os.path.join(os.environ.get("TEMP", "."), "git_auto_sync_local.log")


def run(cmd, cwd, timeout=60):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, cwd=cwd)
        return p.returncode, p.stdout.strip()
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except Exception as e:
        return -1, str(e)


def sync_repo(repo):
    changes = []
    if not os.path.isdir(os.path.join(repo, ".git")):
        return ["[SKIP] 不是 git 仓库: %s" % repo]
    rc, _ = run("git fetch origin --prune", repo)
    if rc != 0:
        return ["[%s] fetch 失败" % repo]

    # 工作区脏文件数
    rc, dirty = run("git status --porcelain | find /c /v \"\"", repo)
    try:
        dirty_n = int(dirty or 0)
    except ValueError:
        dirty_n = 999

    # 遍历本地分支
    rc, out = run("git for-each-ref --format=%(refname:short)", repo)
    for branch in (out.splitlines() if out else []):
        branch = branch.strip()
        if not branch:
            continue
        rc, upstream = run(
            'git for-each-ref --format=%%(upstream:short) refs/heads/%s' % branch, repo)
        if not upstream or upstream == " ":
            continue
        rc, ahead_s = run('git rev-list --count "%s..%s"' % (upstream, branch), repo)
        rc2, behind_s = run('git rev-list --count "%s..%s"' % (branch, upstream), repo)
        try:
            ahead, behind = int(ahead_s or 0), int(behind_s or 0)
        except ValueError:
            ahead = behind = 0

        # feature/* 领先 → push
        if ahead > 0 and branch.startswith("feature/"):
            rc, o = run('git push origin "%s"' % branch, repo)
            if rc == 0:
                changes.append("[%s] PUSH %s (+%d)" % (os.path.basename(repo), branch, ahead))
            else:
                changes.append("[%s] PUSH_FAIL %s: %s" % (os.path.basename(repo), branch, o[:80]))

        # 落后且工作区干净 → ff-only
        if behind > 0:
            rc, cur = run("git branch --show-current", repo)
            if dirty_n == 0 or branch != cur.strip():
                rc, o = run('git pull --ff-only origin "%s"' % branch, repo)
                if rc == 0:
                    changes.append("[%s] PULL %s (-%d)" % (os.path.basename(repo), branch, behind))
                else:
                    changes.append("[%s] PULL_FAIL %s: %s" % (os.path.basename(repo), branch, o[:80]))
            else:
                changes.append("[%s] SKIP %s (工作区有WIP，-%d待拉)" % (os.path.basename(repo), branch, behind))
    return changes


def setup_task(repo):
    """注册 Windows 计划任务：每15分钟静默运行"""
    script = os.path.abspath(__file__)
    python = sys.executable
    cmd = (
        'schtasks /Create /F /TN "Hermes-GitAutoSync" '
        '/SC MINUTE /MO 15 '
        '/TR "\\"%s\\" \\"%s\\" --repo \\"%s\\" --quiet"' % (python, script, repo)
    )
    rc, out = run(cmd, os.path.dirname(script))
    if rc == 0:
        print("✅ 已注册计划任务 Hermes-GitAutoSync（每15分钟自动双向同步）")
        print("   脚本: %s" % script)
    else:
        print("❌ 注册失败: %s" % out)
        print("   请尝试以管理员身份运行: %s --setup" % script)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if args.setup:
        setup_task(args.repo)
        return

    changes = sync_repo(args.repo)
    if changes and not args.quiet:
        print("🔄 本地代码自动同步完成:")
        for c in changes:
            print(" - " + c)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("%s %s\n" % (time.strftime("%F %T"), " | ".join(changes) if changes else "(无变化)"))


if __name__ == "__main__":
    main()
