#!/usr/bin/env python3
"""gaia_reflect.py — 军团成员工作反哺工具 v1.0.0

数字军团成员（Hermes 分身/子代理）完成任务后，调用本工具把工作沉淀
提炼为知识，反哺盖娅大脑。支持三种输入:
  1. 直接文本: --title/--content
  2. 会话文件: --session-file <md/json> (读取内容自动提炼标题)
  3. 目录扫描: --dir <path> (扫描新增 md 文件，提取精华反哺)

用法:
  python3 gaia_reflect.py --title "修复了X" --content "问题: ... 方案: ... 教训: ..."
  python3 gaia_reflect.py --session-file /tmp/session_summary.md --type pattern
  python3 gaia_reflect.py --dir /var/www/ai-digital-card/backend/analysis --new-only

知识类型: insight(洞察) | pattern(模式) | rule(规则) | preference(偏好) | behavior(行为) | optimization(优化)
来源: retrospective(复盘) | system(系统学习) | manual(人工)
"""
from __future__ import annotations

import argparse
import hashlib
import http.cookiejar
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BACKEND = "/var/www/ai-digital-card/backend"
BACKFEED = Path(BACKEND) / "scripts" / "gaia_backfeed.py"
BASE_URL = os.environ.get("GAIA_API_BASE", "http://127.0.0.1:8201")


def reflect_work(
    title: str,
    content: str,
    ktype: str = "insight",
    tags: list[str] | None = None,
    source_id: str = "",
    source: str = "retrospective",
    confidence: float = 0.9,
) -> dict:
    """工作沉淀反哺（委托给 gaia_backfeed.py --ingest）"""
    cmd = [
        sys.executable, str(BACKFEED), "--ingest",
        "--title", title,
        "--content", content,
        "--type", ktype,
        "--tags", ",".join(tags or []),
        "--source-id", source_id or f"reflect:{hashlib.sha1(title.encode()).hexdigest()[:12]}",
        "--source", source,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode == 0 and r.stdout.strip():
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            return {"code": 500, "message": r.stdout[:300]}
    return {"code": 500, "message": (r.stderr or r.stdout)[-300:]}


def reflect_session_file(path: str, ktype: str) -> dict:
    """从会话/报告文件提炼反哺"""
    p = Path(path)
    if not p.exists():
        return {"code": 404, "message": f"文件不存在: {path}"}
    content = p.read_text(encoding="utf-8", errors="ignore")

    # 标题: 一级标题或文件名
    title = p.stem
    for line in content.splitlines()[:10]:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # 提炼精华: 取文件中部最有信息量的段落（跳过标题区）
    lines = content.splitlines()
    body_lines = [l for l in lines if l.strip() and not l.startswith("#")][:60]
    body = "\n".join(body_lines)[:3000]

    tags = ["复盘", ktype]
    if "修复" in title or "fix" in title.lower():
        tags.append("bugfix")
    if "报告" in title or "report" in title.lower():
        tags.append("report")

    return reflect_work(
        title=title,
        content=body,
        ktype=ktype,
        tags=tags,
        source_id=f"reflect:file:{hashlib.sha1(str(p).encode()).hexdigest()[:12]}",
    )


def reflect_dir(path: str, new_only: bool = False) -> dict:
    """扫描目录中的 md 文件，逐个反哺"""
    d = Path(path)
    if not d.is_dir():
        return {"code": 404, "message": f"目录不存在: {path}"}

    # 幂等状态
    state_file = Path(__file__).parent / ".gaia_reflect_state.json"
    state = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    results = {"files": 0, "ingested": 0, "skipped": 0, "failed": 0}
    for md in sorted(d.rglob("*.md")):
        results["files"] += 1
        rel = str(md.relative_to(d))
        sid = f"reflect:dir:{hashlib.sha1(str(md).encode()).hexdigest()[:12]}"
        if sid in state.get("ingested", {}):
            results["skipped"] += 1
            continue

        resp = reflect_session_file(str(md), "insight")
        if resp.get("code") == 200:
            state.setdefault("ingested", {})[sid] = rel
            results["ingested"] += 1
            print(f"  [✓] {rel}")
        else:
            results["failed"] += 1
            print(f"  [✗] {rel}: {resp.get('message')}")

    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


def main():
    parser = argparse.ArgumentParser(description="军团成员工作反哺工具")
    parser.add_argument("--title", default="", help="知识标题")
    parser.add_argument("--content", default="", help="知识内容")
    parser.add_argument("--type", default="insight", help="知识类型: insight|pattern|rule|preference|behavior|optimization")
    parser.add_argument("--tags", default="", help="逗号分隔标签")
    parser.add_argument("--source-id", default="", help="来源标识")
    parser.add_argument("--source", default="retrospective", help="来源: retrospective|system|manual|feedback|ab_test")
    parser.add_argument("--session-file", default="", help="从文件提炼反哺")
    parser.add_argument("--dir", default="", help="扫描目录反哺")
    args = parser.parse_args()

    if args.session_file:
        resp = reflect_session_file(args.session_file, args.type)
        print(json.dumps(resp, ensure_ascii=False, indent=2))
        sys.exit(0 if resp.get("code") == 200 else 1)

    if args.dir:
        results = reflect_dir(args.dir)
        print(f"\n文件: {results['files']}  反哺: {results['ingested']}  跳过: {results['skipped']}  失败: {results['failed']}")
        sys.exit(0 if results["failed"] == 0 else 2)

    if not args.title or not args.content:
        parser.print_help()
        sys.exit(1)

    resp = reflect_work(
        title=args.title,
        content=args.content,
        ktype=args.type,
        tags=[t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else None,
        source_id=args.source_id,
        source=args.source,
    )
    print(json.dumps(resp, ensure_ascii=False, indent=2))
    sys.exit(0 if resp.get("code") == 200 else 1)


if __name__ == "__main__":
    main()
