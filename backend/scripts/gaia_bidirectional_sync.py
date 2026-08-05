#!/usr/bin/env python3
"""gaia_bidirectional_sync.py — 盖娅知识库双向增量同步（服务器侧）v2.0.0

架构: 复用 ai-digital-card 仓库的 knowledge-sync/ 目录作双向中转
  - 本地(Windows) → GitHub: 本地脚本 push 记忆宫殿最新知识 → knowledge-sync/local/
  - 服务器 cron → GitHub pull: 检测新增 → 增量导入盖娅 gaia_knowledge
  - 服务器 → GitHub: 导出盖娅新知识 → knowledge-sync/gaia_export/ → push
  - 本地开机: 本地脚本 pull → 拿回服务器新知识

目录约定 (仓库内 knowledge-sync/):
  local/        本地记忆宫殿/五池知识 (本地 push)
  gaia_export/  盖娅导出知识 (服务器 push)

用法:
  python3 gaia_bidirectional_sync.py --pull          # 拉取并增量导入盖娅
  python3 gaia_bidirectional_sync.py --export        # 导出盖娅新知识并推送
  python3 gaia_bidirectional_sync.py --check         # 检查同步状态
  python3 gaia_bidirectional_sync.py --install-cron  # 注册服务器定时任务
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_DIR = Path("/var/www/ai-digital-card")
SYNC_SUBDIR = "knowledge-sync"
BACKEND = REPO_DIR / "backend"
IMPORT_SCRIPT = BACKEND / "scripts" / "gaia_backfeed.py"


def run(cmd, timeout=180, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)


def get_pgurl() -> str:
    for line in (BACKEND / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].replace("+asyncpg", "").strip()
    raise SystemExit("DATABASE_URL not found")


def psql_query(sql: str, timeout: int = 60) -> subprocess.CompletedProcess:
    """执行 psql 查询（用 -c 参数避免特殊字符问题）"""
    import os
    import re as _re
    from urllib.parse import urlparse

    pgurl = get_pgurl()
    u = urlparse(pgurl)
    env = dict(os.environ)
    env["PGPASSWORD"] = u.password or ""
    return subprocess.run(
        ["psql", "-h", u.hostname or "localhost", "-p", str(u.port or 5432),
         "-U", u.username or "postgres", "-d", u.path.lstrip("/"),
         "-t", "-A", "-F", "|", "-c", sql],
        capture_output=True, text=True, timeout=timeout, env=env,
    )


def git_pull():
    """从 GitHub 拉取仓库最新（含本地推送的知识）"""
    # 先 stash 未提交的脚本改动（避免 pull rebase 冲突）
    run(["git", "-C", str(REPO_DIR), "stash", "--include-untracked"], timeout=60)
    r = run(["git", "-C", str(REPO_DIR), "pull", "origin", "master", "--rebase"])
    if r.returncode != 0:
        r = run(["git", "-C", str(REPO_DIR), "pull", "origin", "main", "--rebase"])
    run(["git", "-C", str(REPO_DIR), "stash", "pop"], timeout=60)
    return r


def git_push(message: str):
    """提交并推送服务器侧变更"""
    run(["git", "-C", str(REPO_DIR), "add", "-A", SYNC_SUBDIR])
    r = run(["git", "-C", str(REPO_DIR), "commit", "-m", message], timeout=60)
    if r.returncode != 0 and "nothing to commit" not in r.stdout + r.stderr:
        return r
    r = run(["git", "-C", str(REPO_DIR), "push", "origin", "HEAD"], timeout=120)
    return r


def sync_pull():
    """拉取本地推送的知识 → 增量导入盖娅"""
    print("=== [1/2] 从 GitHub 拉取 ===")
    r = git_pull()
    print(r.stdout[-400:] or r.stderr[-300:])

    local_dir = REPO_DIR / SYNC_SUBDIR / "local"
    if not local_dir.exists():
        print("[SKIP] 本地知识目录不存在: %s" % local_dir)
        return

    n_files = sum(1 for _ in local_dir.rglob("*") if _.is_file() and _.suffix.lower() in (".md", ".yaml", ".yml"))
    print(f"=== [2/2] 增量导入盖娅 (本地知识 {n_files} 文件) ===")
    if n_files == 0:
        print("无新知识文件")
        return

    # 逐文件调用 gaia_reflect 导入（幂等，source_id=文件路径hash）
    imported = 0
    failed = 0
    skipped = 0
    # 预查已存在的 source_id，避免唯一约束冲突
    existing = set()
    r_exist = psql_query("SELECT source_id FROM gaia_knowledge WHERE source_id LIKE 'sync:%'")
    if r_exist.returncode == 0:
        for line in r_exist.stdout.strip().splitlines():
            if line.strip():
                existing.add(line.strip())
    for f in sorted(local_dir.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in (".md", ".yaml", ".yml"):
            continue
        if f.name.startswith((".", "_index")):
            continue
        rel = str(f.relative_to(local_dir))
        sid = "sync:%s" % rel
        if sid in existing:
            skipped += 1
            continue
        content = f.read_text(encoding="utf-8", errors="ignore")
        if len(content.strip()) < 50:
            skipped += 1
            continue
        title = f.stem
        for line in content.splitlines()[:10]:
            if line.startswith("# "):
                title = line[2:].strip()
                break
        cmd = [
            sys.executable, str(IMPORT_SCRIPT), "--ingest",
            "--title", title[:200],
            "--content", content[:3000],
            "--type", "insight",
            "--tags", "同步,本地知识," + rel.split("/")[0],
            "--source-id", sid,
            "--source", "system",
        ]
        rr = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        try:
            resp = json.loads(rr.stdout) if rr.stdout.strip() else {"code": 500}
        except json.JSONDecodeError:
            resp = {"code": 500}
        if resp.get("code") == 200:
            imported += 1
            existing.add(sid)
            print(f"  [✓] {rel}")
        else:
            failed += 1
            print(f"  [✗] {rel}: {resp.get('message', 'unknown')}")
        if imported >= 100:
            print("  ...达到单轮上限100条，剩余下轮同步")
            break

    print(f"\n导入完成: {imported} 成功, {skipped} 跳过(已存在), {failed} 失败")


def sync_export():
    """导出盖娅最近新知识 → push 到 GitHub → 本地 pull 拿回"""
    print("=== [1/2] 导出盖娅新知识 ===")
    # 只导出 id + 标题（内容多行会导致 -F 分隔错乱，内容单独查）
    r = psql_query(
        "SELECT id, knowledge_type, title FROM gaia_knowledge "
        "WHERE created_at > now() - interval '2 days' ORDER BY id",
        timeout=60,
    )
    if r.returncode != 0:
        print("[WARN] 查询失败: %s" % r.stderr[-200:])
        return

    export_dir = REPO_DIR / SYNC_SUBDIR / "gaia_export"
    export_dir.mkdir(parents=True, exist_ok=True)

    state_file = REPO_DIR / SYNC_SUBDIR / ".export_state.json"
    state = {"last_id": 0}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    out_file = export_dir / ("gaia_export_%s.yaml" % ts)
    count = 0
    pending_ids = []
    for line in (l for l in r.stdout.strip().splitlines() if l.strip()):
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        try:
            kid = int(parts[0])
        except ValueError:
            continue
        if kid <= state.get("last_id", 0):
            continue
        pending_ids.append((kid, parts[1], parts[2][:200]))

    if pending_ids:
        # 批量查内容（用 chr(10) 占位避免换行干扰）
        ids_csv = ",".join(str(k) for k, _, _ in pending_ids[:200])
        r2 = psql_query(
            "SELECT id, replace(content, chr(10), ' / ') FROM gaia_knowledge "
            "WHERE id IN (%s)" % ids_csv,
            timeout=60,
        )
        content_map = {}
        if r2.returncode == 0:
            for line in r2.stdout.strip().splitlines():
                parts = line.split("|", 1)
                if len(parts) == 2:
                    try:
                        content_map[int(parts[0])] = parts[1]
                    except ValueError:
                        pass

        with open(out_file, "w", encoding="utf-8") as f:
            f.write("# 盖娅知识导出 %s\n# 来源: gaia_knowledge\n\n" % ts)
            for kid, ktype, title in pending_ids:
                content = content_map.get(kid, "")
                f.write("- id: %d\n  type: %s\n  title: %s\n  content: |\n    %s\n" % (
                    kid, ktype, title, content[:1200].replace("\n", "\n    ")
                ))
                count += 1
                state["last_id"] = max(state.get("last_id", 0), kid)
    state_file.write_text(json.dumps(state), encoding="utf-8")
    print(f"导出 {count} 条")

    if count > 0:
        print("=== [2/2] 推送到 GitHub ===")
        r = git_push("chore: 盖娅知识导出 %s (%d条)" % (ts, count))
        print(r.stdout[-300:] or r.stderr[-200:])
    else:
        print("无新知识，跳过推送")


def sync_check():
    """检查同步状态"""
    r = run(["git", "-C", str(REPO_DIR), "log", "--oneline", "-3"])
    print("=== 仓库最近提交 ===")
    print(r.stdout)
    r = run(["git", "-C", str(REPO_DIR), "status", "--short"])
    print("=== 工作区状态 ===")
    print(r.stdout or "  干净")

    local_dir = REPO_DIR / SYNC_SUBDIR / "local"
    if local_dir.exists():
        n = sum(1 for _ in local_dir.rglob("*") if _.is_file())
        print(f"=== 本地知识同步区: {n} 文件 ===")

    pgurl = get_pgurl()
    r = psql_query("SELECT count(*) FROM gaia_knowledge")
    print(f"=== 盖娅知识量: {r.stdout.strip()} ===")


def install_cron():
    """注册服务器定时任务 (系统 crontab)"""
    script = "/var/www/ai-digital-card/backend/scripts/gaia_bidirectional_sync.py"
    python = sys.executable
    lines = [
        "# 盖娅双向同步: 每15分钟拉取本地推送知识并导入",
        f"*/15 * * * * {python} {script} --pull >> /var/www/ai-digital-card/backend/logs/gaia_sync.log 2>&1",
        "# 盖娅双向同步: 每小时导出新知识推送",
        f"0 * * * * {python} {script} --export >> /var/www/ai-digital-card/backend/logs/gaia_sync.log 2>&1",
    ]
    try:
        existing = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    except Exception:
        existing = ""
    new_cron = existing + "\n" + "\n".join(lines) + "\n"
    p = subprocess.run(["crontab", "-"], input=new_cron, text=True, capture_output=True)
    if p.returncode == 0:
        print("✅ 定时任务已注册（每15分钟pull导入 + 每小时export推送）")
    else:
        print("❌ 注册失败: %s" % p.stderr[-300:])


def main():
    parser = argparse.ArgumentParser(description="盖娅知识库双向同步")
    parser.add_argument("--pull", action="store_true", help="拉取并导入")
    parser.add_argument("--export", action="store_true", help="导出并推送")
    parser.add_argument("--check", action="store_true", help="检查状态")
    parser.add_argument("--install-cron", action="store_true", help="注册定时任务")
    args = parser.parse_args()

    if args.check:
        sync_check()
    elif args.pull:
        sync_pull()
    elif args.export:
        sync_export()
    elif args.install_cron:
        install_cron()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
