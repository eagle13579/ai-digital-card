#!/usr/bin/env python3
"""gaia_sync_local.py — 盖娅知识库双向同步（本地 Windows 侧）v1.1.0

v1.1 改进（远程分身修复）:
  - 复用本地已有 AI数智名片 开发仓库做 git 工作区（凭据已缓存，避免重新
    clone 卡 SSH 认证 / 大仓库下载），仅在无仓库时才独立 clone
  - push/pull 强制在 master 分支操作，避免误推开发分支

用法 (Windows):
  python gaia_sync_local.py --push     # 推送本地知识到 GitHub
  python gaia_sync_local.py --pull     # 拉取服务器知识回本地
  python gaia_sync_local.py --both     # 先push再pull (推荐, 开机时运行)
  python gaia_sync_local.py --check    # 检查状态

本地知识库源目录:
  D:\\向海容的知识库\\wiki\\wiki\\记忆宫殿  (profiles/ 各项目知识)
  D:\\AI数智名片\\backend\\analysis       (项目分析文档)
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── 本地路径配置（按需修改）──
LOCAL_PALACE = Path(r"D:\向海容的知识库\wiki\wiki\记忆宫殿")
LOCAL_ANALYSIS = Path(r"D:\AI数智名片\backend\analysis")
LOCAL_PROJECT = Path(r"D:\AI数智名片")
GITHUB_REPO = "git@github.com:eagle13579/ai-digital-card.git"

# 服务器同步区在仓库中的路径
SYNC_DIR_IN_REPO = "knowledge-sync"
LOCAL_DEST = "knowledge-sync/local"
EXPORT_SRC = "knowledge-sync/gaia_export"


def resolve_cache_dir() -> Path:
    """优先复用本地已有开发仓库（凭据已缓存，避免重新 clone 卡认证）"""
    if (LOCAL_PROJECT / ".git").exists():
        return LOCAL_PROJECT
    return LOCAL_PROJECT / "knowledge-sync"


def run(cmd, timeout=600, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)


def check_env() -> bool:
    """检查环境"""
    ok = True
    if not shutil.which("git"):
        print("❌ git 未安装")
        ok = False
    if not LOCAL_PALACE.exists():
        print(f"⚠️ 记忆宫殿目录不存在: {LOCAL_PALACE}")
    else:
        print(f"✅ 记忆宫殿: {LOCAL_PALACE}")
    if not LOCAL_PROJECT.exists():
        print(f"⚠️ 项目目录不存在: {LOCAL_PROJECT}")
    else:
        print(f"✅ 项目: {LOCAL_PROJECT}")
    cache = resolve_cache_dir()
    if (cache / ".git").exists():
        print(f"✅ 复用开发仓库: {cache} (分支: {run(['git', '-C', str(cache), 'branch', '--show-current']).stdout.strip()})")
    else:
        print(f"⚠️ 无本地仓库，将 clone 到: {cache}")
    return ok


def ensure_master(cache: Path) -> bool:
    """确保在 master 分支操作，避免误推开发分支"""
    r = run(["git", "-C", str(cache), "branch", "--show-current"])
    branch = r.stdout.strip()
    if branch == "master":
        return True
    if branch:
        print(f"  [分支] 当前在 {branch}，切换 master ...")
    r = run(["git", "-C", str(cache), "checkout", "master"])
    if r.returncode != 0:
        print(f"  ⚠️ 切换 master 失败（可能有未提交改动）: {r.stderr[-200:]}")
        return False
    # 拉取最新 master 并同步远端
    run(["git", "-C", str(cache), "pull", "origin", "master", "--rebase"], timeout=300)
    return True


def sync_push():
    """推送本地知识到 GitHub"""
    print("=== 推送本地知识 → GitHub ===")
    cache = resolve_cache_dir()
    if not (cache / ".git").exists():
        cache.mkdir(parents=True, exist_ok=True)
        print("clone 开发仓库（首次，需要网络与 GitHub 凭据）...")
        r = run(["git", "clone", "--depth", "50", GITHUB_REPO, str(cache)])
        if r.returncode != 0:
            print("clone 失败: %s" % r.stderr[-300:])
            return
    else:
        # 复用仓库：拉取最新（含服务器导出的知识）
        r = run(["git", "-C", str(cache), "pull", "origin", "master", "--rebase"], timeout=300)
        print("pull:", (r.stdout or r.stderr)[-200:])

    if not ensure_master(cache):
        return

    # 复制本地知识到同步区
    dest = cache / LOCAL_DEST
    dest.mkdir(parents=True, exist_ok=True)

    copied = 0
    # 1. 记忆宫殿 profiles（关键 profile）
    profiles_dir = LOCAL_PALACE / "profiles"
    if profiles_dir.exists():
        for profile in ["ai-digital-card", "ai-digital-legion", "china-softbank", "matching-engine", "gaia-city"]:
            src = profiles_dir / profile
            if src.exists():
                shutil.copytree(src, dest / ("profile_" + profile), dirs_exist_ok=True)
                copied += 1
                print(f"  [profile] {profile}")

    # 2. 五池
    pool_src = LOCAL_PALACE / "L5孵化室" / "五池"
    if pool_src.exists():
        shutil.copytree(pool_src, dest / "五池", dirs_exist_ok=True)
        copied += 1
        print("  [五池]")

    # 3. 项目 analysis 文档
    if LOCAL_ANALYSIS.exists():
        shutil.copytree(LOCAL_ANALYSIS, dest / "analysis", dirs_exist_ok=True)
        copied += 1
        print("  [analysis]")

    if copied == 0:
        print("⚠️ 没有可同步的知识（请检查路径）")
        return

    # 提交推送（仅同步区）
    r = run(["git", "-C", str(cache), "add", "-A", LOCAL_DEST])
    r = run(["git", "-C", str(cache), "commit", "-m",
             "sync: 本地知识 %s (%d源)" % (datetime.now().strftime("%Y-%m-%d %H:%M"), copied)])
    if r.returncode != 0 and "nothing to commit" not in r.stdout + r.stderr:
        print("commit 失败: %s" % r.stderr[-300:])
        return
    r = run(["git", "-C", str(cache), "push", "origin", "master"], timeout=300)
    print("push:", (r.stdout or r.stderr)[-300:])
    print("✅ 本地知识已推送到 GitHub")


def sync_pull():
    """拉取服务器知识回本地"""
    print("=== 从 GitHub 拉取服务器知识 → 本地 ===")
    cache = resolve_cache_dir()
    if not (cache / ".git").exists():
        print("❌ 仓库不存在，请先运行 --push")
        return
    if not ensure_master(cache):
        return
    r = run(["git", "-C", str(cache), "pull", "origin", "master", "--rebase"], timeout=300)
    print("pull:", (r.stdout or r.stderr)[-300:])

    export_src = cache / EXPORT_SRC
    if not export_src.exists():
        print("⚠️ 没有服务器导出知识")
        return

    # 复制到本地记忆宫殿
    dest_palace = LOCAL_PALACE / "gaia_exports"
    dest_palace.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in export_src.glob("*.yaml"):
        shutil.copy2(f, dest_palace / f.name)
        n += 1
        print(f"  [导入] {f.name}")
    print(f"✅ 服务器知识已拉取到本地记忆宫殿/gaia_exports ({n} 个)")


def sync_check():
    """检查状态"""
    print("=== 本地同步状态 ===")
    check_env()
    cache = resolve_cache_dir()
    if (cache / ".git").exists():
        r = run(["git", "-C", str(cache), "log", "--oneline", "-3"])
        print("最近同步提交:")
        print(r.stdout)
        r = run(["git", "-C", str(cache), "status", "--short"])
        print("待同步变更:")
        print(r.stdout or "  无")
    else:
        print("缓存目录未创建（首次请运行 --push）")


def main():
    parser = argparse.ArgumentParser(description="盖娅知识库双向同步（本地）")
    parser.add_argument("--push", action="store_true", help="推送本地知识")
    parser.add_argument("--pull", action="store_true", help="拉取服务器知识")
    parser.add_argument("--both", action="store_true", help="先push再pull")
    parser.add_argument("--check", action="store_true", help="检查状态")
    args = parser.parse_args()

    if args.check:
        sync_check()
    elif args.both:
        sync_push()
        sync_pull()
    elif args.push:
        sync_push()
    elif args.pull:
        sync_pull()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
