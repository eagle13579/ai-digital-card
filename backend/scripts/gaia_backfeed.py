#!/usr/bin/env python3
"""gaia_backfeed.py — 盖娅大脑 服务器版反哺管道 v1.0.0

功能:
  1. 批量反哺: 扫描服务器学习素材（五池Feature库 / 项目docs / analysis / 盖娅引擎快照）
     → 提炼知识条目 → 写入 gaia_knowledge（source=system, 幂等去重）
  2. 单条反哺: 军团成员完成任务后调用 --ingest，把工作沉淀提炼为知识反哺盖娅（source=retrospective）

用法:
  python3 gaia_backfeed.py                          # 批量扫描服务器素材并反哺
  python3 gaia_backfeed.py --dry-run                # 只扫描预览，不写入
  python3 gaia_backfeed.py --ingest --title "..." --content "..." [--type pattern] [--tags a,b] [--source-id xxx]
  python3 gaia_backfeed.py --check                  # 查看知识库统计

设计要点:
  - 幂等: 用 source_id = sha1(相对路径) 去重，重复执行不产生重复知识
  - CSRF: 自动获取 token 并带 cookie（Double Submit Cookie 模式）
  - 容错: 单个文件失败不影响整体，最后汇总统计
"""
from __future__ import annotations

import argparse
import hashlib
import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get("GAIA_API_BASE", "http://127.0.0.1:8201")
STATE_FILE = Path(__file__).parent / ".gaia_backfeed_state.json"

# 服务器学习素材源（按优先级排序）
SCAN_DIRS = [
    ("五池Feature库", "/var/www/liankebao/L5孵化室/五池/Feature库", {"yaml", "yml", "md"}),
    ("项目docs", "/var/www/ai-digital-card/docs", {"md"}),
    ("analysis分析", "/var/www/ai-digital-card/backend/analysis", {"md"}),
    ("盖娅引擎快照", "/opt/gaia-engines/data/knowledge", {"json"}),
]

# knowledge_type 映射（目录关键词 → 知识类型）
TYPE_MAP = [
    ("场景", "pattern"),
    ("数据", "optimization"),
    ("创造力", "insight"),
    ("体系", "rule"),
    ("Feature", "pattern"),
    ("docs", "insight"),
    ("analysis", "insight"),
]

# 已摄取指纹缓存（source_id -> title），避免重复写入
_fingerprints: set[str] = set()


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_csrf_token() -> tuple[str, http.cookiejar.CookieJar]:
    """获取 CSRF token（Double Submit Cookie 模式）"""
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    req = urllib.request.Request(BASE_URL + "/api/csrf/token")
    with opener.open(req) as resp:
        token = json.loads(resp.read().decode())["token"]
    return token, cj, opener


def _post_json(path: str, payload: dict, token: str, cj: http.cookiejar.CookieJar, opener: urllib.request.OpenerDirector) -> dict:
    """带 CSRF 的 POST 请求"""
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "X-CSRF-Token": token},
        method="POST",
    )
    try:
        with opener.open(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        return {"code": e.code, "message": f"HTTP {e.code}: {body}"}


def _file_to_knowledge(path: str, rel_key: str) -> dict | None:
    """从素材文件提炼知识条目"""
    p = Path(path)
    suffix = p.suffix.lower().lstrip(".")
    try:
        if p.stat().st_size > 200_000:  # 跳过超大文件
            return None
        content = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    if not content.strip():
        return None

    # 内容太短的元数据快照（如 cortex-snapshot 纯时间戳）无提炼价值
    if len(content.strip()) < 300:
        return None

    # 标题: 优先取 YAML name 字段 / Markdown 一级标题 / 文件名
    title = p.stem
    if suffix in ("yaml", "yml"):
        for line in content.splitlines()[:20]:
            if line.startswith("name:"):
                title = line.split(":", 1)[1].strip().strip("'\"")
                break
    else:
        for line in content.splitlines()[:10]:
            if line.startswith("# "):
                title = line[2:].strip()
                break

    # 类型推断
    ktype = "insight"
    rel_lower = rel_key.lower()
    for kw, t in TYPE_MAP:
        if kw.lower() in rel_lower:
            ktype = t
            break

    # 内容裁剪（保留核心）
    body = content.strip()
    if len(body) > 3000:
        body = body[:3000] + "\n...(截断)"

    # 标签: 从路径提取
    tags = [part for part in Path(rel_key).parts if part not in (".", "/")][:5]
    tags = [t for t in tags if t not in ("Feature库", "五池", "docs", "analysis")][:4]
    if not tags:
        tags = [ktype]

    source_id = hashlib.sha1(rel_key.encode()).hexdigest()[:16]

    return {
        "source": "system",
        "source_id": f"backfeed:{source_id}",
        "knowledge_type": ktype,
        "title": title[:200],
        "content": body,
        "tags": tags,
        "confidence": 0.7,
    }


def batch_backfeed(dry_run: bool = False) -> dict:
    """批量扫描服务器素材并反哺"""
    state = _load_state()
    token, cj, opener = _get_csrf_token()

    results = {"scanned": 0, "new": 0, "skipped": 0, "failed": 0, "items": []}
    scanned_ids = set()

    for source_name, base_dir, exts in SCAN_DIRS:
        if not os.path.isdir(base_dir):
            print(f"  [SKIP] 目录不存在: {base_dir}")
            continue
        for root, _dirs, files in os.walk(base_dir):
            for fname in sorted(files):
                if not fname.endswith(tuple(exts)):
                    continue
                if fname.startswith((".", "_index")):
                    continue
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, "/")
                rel_key = f"{source_name}/{rel}"
                results["scanned"] += 1

                knowledge = _file_to_knowledge(fpath, rel_key)
                if knowledge is None:
                    results["skipped"] += 1
                    continue

                sid = knowledge["source_id"]
                scanned_ids.add(sid)
                if sid in state.get("ingested", {}) or sid in _fingerprints:
                    results["skipped"] += 1
                    continue

                if dry_run:
                    print(f"  [NEW?] {knowledge['title']}  ({source_name})")
                    _fingerprints.add(sid)
                    results["new"] += 1
                    continue

                resp = _post_json("/api/v1/gaia/knowledge", knowledge, token, cj, opener)
                if resp.get("code") == 200:
                    _fingerprints.add(sid)
                    state.setdefault("ingested", {})[sid] = knowledge["title"]
                    results["new"] += 1
                    results["items"].append(knowledge["title"])
                    print(f"  [✓] {knowledge['title']}  ({knowledge['knowledge_type']})")
                else:
                    results["failed"] += 1
                    print(f"  [✗] {knowledge['title']}: {resp.get('message')}")

    if not dry_run:
        _save_state(state)
    return results


def ingest_one(
    title: str,
    content: str,
    ktype: str = "insight",
    tags: list[str] | None = None,
    source_id: str = "",
    source: str = "retrospective",
    confidence: float = 0.9,
) -> dict:
    """单条反哺（军团成员工作沉淀用）"""
    token, cj, opener = _get_csrf_token()
    payload = {
        "source": source,
        "source_id": source_id or f"ingest:{hashlib.sha1(title.encode()).hexdigest()[:12]}",
        "knowledge_type": ktype,
        "title": title[:200],
        "content": content[:5000],
        "tags": tags or [],
        "confidence": confidence,
    }
    resp = _post_json("/api/v1/gaia/knowledge", payload, token, cj, opener)
    return resp


def check_stats() -> dict:
    """查看知识库统计"""
    token, cj, opener = _get_csrf_token()
    cj2 = cj
    req = urllib.request.Request(BASE_URL + "/api/v1/gaia/knowledge?query=盖娅&limit=1")
    try:
        with opener.open(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        # 直接查库统计用 psql
        return {}


def main():
    parser = argparse.ArgumentParser(description="盖娅大脑服务器版反哺管道")
    parser.add_argument("--dry-run", action="store_true", help="只预览不写入")
    parser.add_argument("--check", action="store_true", help="查看知识库状态")
    parser.add_argument("--ingest", action="store_true", help="单条反哺模式")
    parser.add_argument("--title", default="", help="知识标题")
    parser.add_argument("--content", default="", help="知识内容")
    parser.add_argument("--type", default="insight", help="知识类型")
    parser.add_argument("--tags", default="", help="逗号分隔标签")
    parser.add_argument("--source-id", default="", help="来源标识")
    parser.add_argument("--source", default="retrospective", help="来源: retrospective|system|manual|feedback|ab_test")
    args = parser.parse_args()

    if args.check:
        # 查询数据库统计
        import subprocess
        env_path = "/var/www/ai-digital-card/backend/.env"
        db_url = ""
        if os.path.exists(env_path):
            for line in Path(env_path).read_text().splitlines():
                if line.startswith("DATABASE_URL="):
                    db_url = line.split("=", 1)[1].replace("+asyncpg", "")
        if db_url:
            r = subprocess.run(
                ["psql", db_url, "-t", "-c",
                 "SELECT source, count(*) FROM gaia_knowledge GROUP BY source ORDER BY count DESC;"],
                capture_output=True, text=True, timeout=15,
            )
            print("=== gaia_knowledge 统计 ===")
            print(r.stdout or r.stderr)
        return

    if args.ingest:
        if not args.title or not args.content:
            print("ERROR: --ingest 需要 --title 和 --content")
            sys.exit(1)
        resp = ingest_one(
            title=args.title,
            content=args.content,
            ktype=args.type,
            tags=[t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else None,
            source_id=args.source_id,
            source=args.source,
        )
        print(json.dumps(resp, ensure_ascii=False, indent=2))
        if resp.get("code") != 200:
            sys.exit(1)
        return

    print("=== 盖娅大脑 服务器版反哺管道 ===")
    print(f"模式: {'DRY-RUN 预览' if args.dry_run else '正式写入'}")
    print()
    results = batch_backfeed(dry_run=args.dry_run)
    print()
    print("=== 汇总 ===")
    print(f"扫描: {results['scanned']}  新增: {results['new']}  跳过: {results['skipped']}  失败: {results['failed']}")


if __name__ == "__main__":
    main()
