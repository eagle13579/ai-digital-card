#!/usr/bin/env python3
"""
git-auto-save.py — 定时自动保存工作区改动

功能：
  1. 检查项目目录是否有未提交的改动
  2. 有改动则自动 git add -A + git commit（提交信息含"auto-save: 改动简述"）
  3. commit 后会触发 post-commit hook 自动 push
  4. .gitignore 已涵盖 __pycache__/、.env、node_modules/ 等

安全：
  - 不硬编码任何密钥或密码
  - 只处理受 .gitignore 过滤后的文件
  - 仅用于 develop/feature/*/fix/* 分支
"""

import os
import subprocess
import sys
from datetime import datetime

# ===========================================================================
# 配置
# ===========================================================================
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DRY_RUN = "--dry-run" in sys.argv  # 安全测试模式


def run_git(args: list[str], cwd: str = PROJECT_DIR) -> subprocess.CompletedProcess:
    """执行 git 命令，返回 CompletedProcess"""
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def get_current_branch() -> str | None:
    """获取当前分支名"""
    r = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    if r.returncode != 0:
        print(f"  [ERROR] 无法获取当前分支: {r.stderr.strip()}")
        return None
    return r.stdout.strip()


def has_uncommitted_changes() -> bool:
    """检查工作区是否有未提交的改动（包括未跟踪文件）"""
    # 检查 tracked 文件改动
    r1 = run_git(["status", "--porcelain"])
    if r1.returncode != 0:
        print(f"  [ERROR] git status 失败: {r1.stderr.strip()}")
        return False
    return bool(r1.stdout.strip())


def get_change_summary() -> str:
    """生成改动简述（用于 commit message）"""
    r = run_git(["status", "--porcelain"])
    if r.returncode != 0 or not r.stdout.strip():
        return "no changes"
    
    lines = r.stdout.strip().split("\n")
    # 统计文件数量和改动类型
    modified = sum(1 for l in lines if l.startswith(" M") or l.startswith("M "))
    added = sum(1 for l in lines if l.startswith("??") or l.startswith("A "))
    deleted = sum(1 for l in lines if l.startswith(" D") or l.startswith("D "))
    renamed = sum(1 for l in lines if l.startswith(" R") or l.startswith("R "))
    
    parts = []
    if added:
        parts.append(f"+{added} file(s)")
    if modified:
        parts.append(f"~{modified} file(s)")
    if deleted:
        parts.append(f"-{deleted} file(s)")
    if renamed:
        parts.append(f">{renamed} file(s)")
    
    return ", ".join(parts) if parts else f"{len(lines)} change(s)"


def auto_save() -> int:
    """主流程：检查→add→commit→（触发自动push）"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"╔══════════════════════════════════════════════╗")
    print(f"║  git-auto-save  @ {timestamp}  ║")
    print(f"╚══════════════════════════════════════════════╝")
    print(f"  Project: {PROJECT_DIR}")

    # 1. 检查所在目录是否为 git 仓库
    if not os.path.isdir(os.path.join(PROJECT_DIR, ".git")):
        print(f"  [ERROR] {PROJECT_DIR} 不是 git 仓库")
        return 1

    # 2. 检查未提交改动
    if not has_uncommitted_changes():
        print(f"  [INFO]  工作区干净，无需自动保存")
        return 0

    # 3. 获取分支信息
    branch = get_current_branch()
    if branch is None:
        return 1
    
    print(f"  Branch:  {branch}")

    # 4. 分支安全检查：只允许 develop/feature/*/fix/*
    if branch not in ("develop",) and not branch.startswith("feature/") and not branch.startswith("fix/"):
        print(f"  [SKIP]  分支 '{branch}' 不在自动保存范围内")
        print(f"          仅自动保存 develop / feature/* / fix/* 分支")
        return 0

    # 5. git add -A
    summary = get_change_summary()
    print(f"  Changes: {summary}")
    print(f"  ────────────────────────────────────────────")

    if DRY_RUN:
        print(f"  [DRY-RUN] 跳过 add + commit")
        print(f"  [DRY-RUN] 模拟 commit message: auto-save: {summary}")
        return 0

    r_add = run_git(["add", "-A"])
    if r_add.returncode != 0:
        print(f"  [ERROR] git add 失败: {r_add.stderr.strip()}")
        return 1
    print(f"  [OK]     git add -A")

    # 6. git commit
    commit_msg = f"auto-save: {summary}"
    r_commit = run_git(["commit", "-m", commit_msg])
    if r_commit.returncode != 0:
        stderr = r_commit.stderr.strip()
        if "nothing to commit" in stderr:
            print(f"  [INFO]  没有需要提交的内容")
            return 0
        print(f"  [ERROR] git commit 失败: {stderr}")
        return 1
    print(f"  [OK]     git commit -m \"{commit_msg}\"")
    print(f"  [INFO]  post-commit hook 将自动推送...")
    return 0


if __name__ == "__main__":
    sys.exit(auto_save())
