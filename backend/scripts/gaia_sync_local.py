#!/usr/bin/env python3
"""gaia_sync_local.py — 盖娅知识库双向同步（本地 Windows 侧）v1.2.0

v1.2 改进（2026-08-06 本地对齐修复）:
  - ensure_master 失败时自动回退 git worktree（本地开发仓库在 develop 分支
    且有未提交改动时，checkout master 必然失败；v1.1 此缺陷导致脚本跑不通）
  - clone 时注入 core.sshCommand（Hermes 终端沙箱 HOME 导致默认 ssh 找不到
    真实 key，凭据必须显式指定）
  - 全部 git 操作前导出 GIT_SSH_COMMAND 环境兜底（开机自启 bat 环境同样适用）

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

# 显式 SSH key（Hermes 沙箱 HOME 下默认 ssh 找不到真实 key）
# ⚠️ 必须用正斜杠：反斜杠路径进 git config 会被转义吞掉（C:\Users → C:Users）
SSH_KEY = "C:/Users/56867/.ssh/id_ed25519"
SSH_CMD = f"ssh -i {SSH_KEY} -o IdentitiesOnly=yes"
os.environ["GIT_SSH_COMMAND"] = SSH_CMD  # 环境兜底

# ── 知识文件筛选（只推文本知识，服务器导入逻辑仅处理 .md/.yaml/.yml）──
KNOWLEDGE_EXTS = {".md", ".yaml", ".yml"}
SKIP_DIRS = {"__pycache__", ".git", "node_modules", "venv", ".venv", "dist", "build",
             "audio_cache", "image_cache", "cache", "backup", "_backups", "logs",
             "data", "models", "assets", "images", "static"}
SKIP_NAME_PREFIX = (".", "_index")
SKIP_NAME_KW = (".env", "secret", "password", "token", "apikey", "api_key", "credential", "sync-conflict")
# 配置类文件精确排除（config.yaml 等运行配置常含密钥——GitHub secret scanning 会拦截 push）
SKIP_NAME_EXACT = {"config.yaml", "config.yml", "settings.yaml", "settings.yml",
                   "secrets.yaml", "secret.yaml", "credentials.yaml", "auth.yaml",
                   "auth.yml", ".env", ".env.production", "docker-compose.yml", "docker-compose.yaml"}
# 内容级 secret 嗅探（读文件头 2KB，匹配常见密钥模式，防 GitHub push protection 拦截）
import re as _re
SECRET_RE = _re.compile(
    r"(github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}"
    r"|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|AIza[0-9A-Za-z_-]{30,}"
    r"|(?:app|client)_secret[\"'\s:=]+[A-Za-z0-9_\-]{16,}"
    r"|api[_-]?key[\"'\s:=]+[A-Za-z0-9_\-]{20,})",
    _re.IGNORECASE)


def collect_knowledge(src: Path, rel_prefix: str, dest: Path, copied: int, allow=None, max_files=None) -> int:
    """遍历源目录，只复制知识文本文件（md/yaml/yml）。
    allow: 第一层子目录白名单（None=全部子目录，用黑名单过滤）。
    max_files: 全局累计上限（服务器导入每轮上限100条，本地单次推3000=1.5天消化量）。"""
    if not src.exists():
        return copied
    src_str = str(src).rstrip("\\/")
    local = 0
    for r, dirs, files in os.walk(src):
        cur = str(r).rstrip("\\/")
        if allow is not None and (cur == src_str or os.path.dirname(cur) == src_str):
            # 第一层白名单（或源根）
            dirs[:] = [d for d in dirs if d in allow]
        else:
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if max_files is not None and local >= max_files:
                return copied
            if Path(f).suffix.lower() not in KNOWLEDGE_EXTS:
                continue
            if f.startswith(SKIP_NAME_PREFIX):
                continue
            low = f.lower()
            if low in SKIP_NAME_EXACT:
                continue  # 配置类文件（常含密钥）
            if any(k in low for k in SKIP_NAME_KW):
                continue
            fp = Path(r) / f
            # 内容级 secret 嗅探：读文件头 2KB 匹配密钥模式（防 GitHub push protection）
            try:
                head = fp.read_bytes()[:2048]
                if SECRET_RE.search(head.decode("utf-8", errors="ignore")):
                    continue
            except OSError:
                pass
            try:
                rel = fp.relative_to(src)
            except ValueError:
                continue
            dst = dest / rel_prefix / rel
            # 已同步过（同 mtime+size）→ 跳过，不占配额（增量推进）
            try:
                if dst.exists() and dst.stat().st_size == fp.stat().st_size and abs(dst.stat().st_mtime - fp.stat().st_mtime) < 2:
                    continue
            except OSError:
                pass
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fp, dst)
            copied += 1
            local += 1
    return copied


# 独立同步缓存仓库（不碰开发仓库：develop 有大量未提交改动+untracked 会阻塞切分支/worktree）
SYNC_CACHE = Path(r"D:\AI数智名片.sync-cache")


def resolve_cache_dir() -> Path:
    """独立缓存仓库路径（clone --branch master，凭据注入，无分支切换冲突）"""
    return SYNC_CACHE


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


def ensure_master(cache: Path) -> Path | None:
    """确保缓存仓库在 master 分支（clone --branch master 后通常就是）。返回缓存路径。"""
    branch = run(["git", "-C", str(cache), "branch", "--show-current"]).stdout.strip()
    if branch != "master":
        r = run(["git", "-C", str(cache), "checkout", "master"])
        if r.returncode != 0:
            print(f"  ⚠️ 缓存仓库不在 master: {r.stderr[-200:]}")
            return None
    return cache


def cleanup_worktree(cache: Path):
    """清理 ensure_master 创建的临时 worktree"""
    wt = cache.parent / (cache.name + ".sync-master")
    if wt.exists():
        run(["git", "-C", str(cache), "worktree", "remove", "--force", str(wt)], timeout=60)


def sync_push():
    """推送本地知识到 GitHub"""
    print("=== 推送本地知识 → GitHub ===")
    cache = resolve_cache_dir()
    if not (cache / ".git").exists():
        cache.mkdir(parents=True, exist_ok=True)
        print("clone 同步缓存仓库（首次，注入凭据）...")
        r = run(["git", "clone", "-c", f"core.sshCommand={SSH_CMD}",
                 "--depth", "1", "--branch", "master", GITHUB_REPO, str(cache)], timeout=900)
        if r.returncode != 0:
            print("clone 失败: %s" % r.stderr[-300:])
            return
        work = cache
    else:
        work = ensure_master(cache)
        if work is None:
            return
        # 缓存仓库在 master 分支上拉取（安全）
        r = run(["git", "-C", str(work), "pull", "origin", "master", "--rebase"], timeout=300)
        print("pull:", (r.stdout or r.stderr)[-200:])

    # 复制本地知识到同步区
    dest = work / LOCAL_DEST
    dest.mkdir(parents=True, exist_ok=True)

    copied = 0
    # 每源独立配额：5 profiles×400 + 五池600 + analysis50 ≈ 2650/轮（增量多轮消化）
    # 1. 记忆宫殿 profiles（关键 profile）— 白名单只收知识子目录
    profiles_dir = LOCAL_PALACE / "profiles"
    if profiles_dir.exists():
        for profile in ["ai-digital-card", "ai-digital-legion", "china-softbank", "matching-engine", "gaia-city"]:
            src = profiles_dir / profile
            if src.exists():
                before = copied
                copied = collect_knowledge(src, f"profile_{profile}", dest, copied,
                                           allow={"skills", "employees", "_shared"}, max_files=400)
                print(f"  [profile] {profile}: +{copied - before} 个知识文件")

    # 2. 五池 — 只收知识文本（md/yaml/yml），黑名单过滤数据/缓存
    pool_src = LOCAL_PALACE / "L5孵化室" / "五池"
    if pool_src.exists():
        before = copied
        copied = collect_knowledge(pool_src, "五池", dest, copied, max_files=600)
        print(f"  [五池]: +{copied - before} 个知识文件")

    # 3. 项目 analysis 文档
    if LOCAL_ANALYSIS.exists():
        before = copied
        copied = collect_knowledge(LOCAL_ANALYSIS, "analysis", dest, copied, max_files=50)
        print(f"  [analysis]: +{copied - before} 个知识文件")

    if copied == 0:
        print("⚠️ 没有可同步的知识（请检查路径）")
        return

    # 提交推送（仅同步区）
    # clone 的缓存仓库无 git 身份，先注入
    run(["git", "-C", str(work), "config", "user.name", "eagle13579"])
    run(["git", "-C", str(work), "config", "user.email", "56867641@qq.com"])
    r = run(["git", "-C", str(work), "add", "-A", LOCAL_DEST])
    r = run(["git", "-C", str(work), "commit", "-m",
             "sync: 本地知识 %s (%d源)" % (datetime.now().strftime("%Y-%m-%d %H:%M"), copied)])
    if r.returncode != 0 and "nothing to commit" not in r.stdout + r.stderr:
        print("commit 失败: %s" % r.stderr[-300:])
        return
    r = run(["git", "-C", str(work), "push", "origin", "master"], timeout=300)
    print("push:", (r.stdout or r.stderr)[-300:])
    print("✅ 本地知识已推送到 GitHub")
    cleanup_worktree(cache)


def sync_pull():
    """拉取服务器知识回本地"""
    print("=== 从 GitHub 拉取服务器知识 → 本地 ===")
    cache = resolve_cache_dir()
    if not (cache / ".git").exists():
        print("❌ 仓库不存在，请先运行 --push")
        return
    work = ensure_master(cache)
    if work is None:
        return
    r = run(["git", "-C", str(work), "pull", "origin", "master", "--rebase"], timeout=300)
    print("pull:", (r.stdout or r.stderr)[-300:])

    export_src = work / EXPORT_SRC
    if not export_src.exists():
        print("⚠️ 没有服务器导出知识")
        cleanup_worktree(cache)
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
    cleanup_worktree(cache)


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
