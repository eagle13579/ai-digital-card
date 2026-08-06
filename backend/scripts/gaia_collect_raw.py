#!/usr/bin/env python3
"""gaia_collect_raw.py — 盖娅自主学习原始素材采集器 v1.0.0

仅采集原始素材，不做提炼（提炼交给 Hermes LLM 九步法引擎）。
输出 JSON 到 stdout（供 cron LLM 模式读取），同时落盘到数据目录。

用法:
  python3 gaia_collect_raw.py                    # 采集本轮素材，输出JSON
  python3 gaia_collect_raw.py --sources web      # 只采全网
  python3 gaia_collect_raw.py --sources local    # 只采本地
  python3 gaia_collect_raw.py --out /tmp/raw.json  # 指定输出文件
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT_DIR = Path("/var/www/ai-digital-card/backend/data/self_study")
BACKUP_DB = "/opt/hermes-data/backups/brain_daemon__knowledge_models.db.20260709.db"


def _http_get(url: str, timeout: int = 25) -> str | None:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) GaiaSelfStudy/2.0",
                "Accept": "application/json,text/xml,*/*",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  [WARN] 抓取失败 {url[:80]}: {e}", file=sys.stderr)
        return None


def _collect_github() -> list[dict]:
    raw = _http_get("https://api.github.com/search/repositories?q=topic:ai+created:>2026-07-01&sort=stars&order=desc&per_page=15")
    if not raw:
        return []
    try:
        repos = json.loads(raw)
        items = []
        for r in repos.get("items", [])[:15]:
            items.append({
                "source": "github",
                "title": f"[GitHub] {r.get('full_name', '')}",
                "content": f"描述: {r.get('description') or ''}\nStars: {r.get('stargazers_count', 0)}\n语言: {r.get('language') or 'N/A'}\nURL: {r.get('html_url', '')}",
                "tags": ["github", "开源", "AI"],
                "raw": {"full_name": r.get("full_name"), "desc": r.get("description"), "stars": r.get("stargazers_count"), "lang": r.get("language"), "url": r.get("html_url")},
            })
        return items
    except Exception as e:
        print(f"  [WARN] GitHub 解析失败: {e}", file=sys.stderr)
        return []


def _collect_arxiv() -> list[dict]:
    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)
    url = (
        "http://export.arxiv.org/api/query"
        f"?search_query=cat:cs.AI+AND+submittedDate:%5B{week_ago.strftime('%Y%m%d')}+TO+{today.strftime('%Y%m%d')}%5D"
        "&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending"
    )
    raw = _http_get(url)
    if not raw:
        return []
    try:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(raw)
        items = []
        for entry in root.findall("atom:entry", ns)[:10]:
            title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
            summary = entry.findtext("atom:summary", "", ns).strip().replace("\n", " ")
            authors = [a.findtext("atom:name", "", ns) for a in entry.findall("atom:author", ns)][:3]
            link = entry.findtext("atom:id", "", ns)
            if title:
                items.append({
                    "source": "arxiv",
                    "title": title[:250],
                    "content": f"[论文摘要] {summary[:1800]}",
                    "tags": ["arxiv", "论文", "AI"],
                    "raw": {"title": title, "authors": authors, "link": link, "summary": summary[:1800]},
                })
        return items
    except Exception as e:
        print(f"  [WARN] arXiv 解析失败: {e}", file=sys.stderr)
        return []


def _collect_local() -> list[dict]:
    """采集本地知识源（五池/文档/知识模型库增量）"""
    items = []

    # 1. 五池 Feature库
    pool_dir = Path("/var/www/liankebao/L5孵化室/五池/Feature库")
    if pool_dir.is_dir():
        for yaml_file in sorted(pool_dir.rglob("*.yaml")) + sorted(pool_dir.rglob("*.yml")):
            if yaml_file.name.startswith((".", "_index")):
                continue
            try:
                content = yaml_file.read_text(encoding="utf-8", errors="ignore")
                title = yaml_file.stem
                for line in content.splitlines()[:20]:
                    if line.startswith("name:"):
                        title = line.split(":", 1)[1].strip().strip("'\"")
                        break
                items.append({
                    "source": "local_pool",
                    "title": f"[五池] {title}",
                    "content": content[:2000],
                    "tags": ["五池", "Feature"],
                    "raw": {"path": str(yaml_file), "content": content[:2000]},
                })
            except Exception:
                continue

    # 2. 知识模型库抽样（最新 30 条）
    if Path(BACKUP_DB).exists():
        try:
            db = sqlite3.connect(BACKUP_DB)
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT id, source, category, title, content, tags, created_at FROM knowledge_models ORDER BY created_at DESC LIMIT 30"
            ).fetchall()
            for row in rows:
                items.append({
                    "source": "palace",
                    "title": f"[知识库] {row['title']}",
                    "content": row["content"][:2000],
                    "tags": ["五池", row["source"] or "知识库"],
                    "raw": {"id": row["id"], "source": row["source"], "category": row["category"], "content": row["content"][:2000]},
                })
            db.close()
        except Exception as e:
            print(f"  [WARN] 知识模型库读取失败: {e}", file=sys.stderr)

    return items


def collect(sources: list[str]) -> dict:
    result = {"collected_at": datetime.now(timezone.utc).isoformat(), "items": []}
    if "web" in sources or "all" in sources:
        print("  [采集] GitHub...", file=sys.stderr)
        result["items"].extend(_collect_github())
        print("  [采集] arXiv...", file=sys.stderr)
        result["items"].extend(_collect_arxiv())
    if "local" in sources or "all" in sources:
        print("  [采集] 本地知识源...", file=sys.stderr)
        result["items"].extend(_collect_local())

    # 去重
    seen = set()
    unique = []
    for item in result["items"]:
        h = hashlib.sha1((item["source"] + item["title"]).encode()).hexdigest()[:16]
        if h not in seen:
            seen.add(h)
            item["item_id"] = h
            unique.append(item)
    result["items"] = unique
    result["count"] = len(unique)
    return result


def main():
    parser = argparse.ArgumentParser(description="盖娅自主学习原始素材采集器")
    parser.add_argument("--sources", default="all", help="all|web|local")
    parser.add_argument("--out", default="", help="输出JSON文件路径(默认stdout)")
    args = parser.parse_args()

    sources = args.sources.split(",")
    result = collect(sources)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    out_file = Path(args.out) if args.out else OUT_DIR / f"raw_{ts}.json"
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    print(f"\n[素材已保存] {out_file} ({result['count']} 条)", file=sys.stderr)


if __name__ == "__main__":
    main()
