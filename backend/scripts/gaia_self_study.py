#!/usr/bin/env python3
"""gaia_self_study.py — 盖娅大脑自主学习采集器 v1.0.0

在空闲时段运行（由 cron 调度），从以下来源采集学习素材并反哺盖娅大脑:
  1. 本地知识源: 五池Feature库 / 项目docs / analysis（增量扫描）
  2. 全网学习源: GitHub trending、arXiv论文摘要、最佳实践文章（通过 requests 抓取）
  3. 知识模型备份: /opt/hermes-data/backups 下的 brain_daemon 知识库

用法:
  python3 gaia_self_study.py               # 执行一轮学习+反哺
  python3 gaia_self_study.py --dry-run     # 预览不写入
  python3 gaia_self_study.py --only-local  # 只学习本地素材
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

# 全网学习源（HTTP 抓取，轻量级）
WEB_SOURCES = [
    {
        "name": "GitHub Trending",
        "url": "https://api.github.com/search/repositories?q=topic:ai+created:>2026-07-01&sort=stars&order=desc&per_page=10",
        "type": "json",
    },
    {
        "name": "arXiv AI论文",
        "url": "",
        "type": "atom",
        "dynamic": "arxiv",
    },
]

# 本地知识源（与 backfeed 脚本扫描目录一致，增量由 state 文件控制）
LOCAL_SOURCES = [
    ("五池Feature库", "/var/www/liankebao/L5孵化室/五池/Feature库", {"yaml", "yml", "md"}),
    ("项目docs", "/var/www/ai-digital-card/docs", {"md"}),
    ("analysis分析", "/var/www/ai-digital-card/backend/analysis", {"md"}),
]

STATE_FILE = Path(__file__).parent / ".gaia_self_study_state.json"


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {"last_run": "", "web_ingested": {}, "local_ingested": {}}


def _save_state(state: dict):
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _http_get(url: str, timeout: int = 20) -> str | None:
    """安全抓取网页内容"""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) GaiaSelfStudy/1.0",
                "Accept": "application/json,text/xml,*/*",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  [WARN] 抓取失败 {url}: {e}")
        return None


def _parse_arxiv_atom(xml_text: str) -> list[dict]:
    """解析 arXiv Atom feed 提取论文条目（轻量 XML 解析）"""
    import xml.etree.ElementTree as ET

    entries = []
    try:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(xml_text)
        for entry in root.findall("atom:entry", ns):
            title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
            summary = entry.findtext("atom:summary", "", ns).strip().replace("\n", " ")
            published = entry.findtext("atom:published", "", ns)
            authors = [a.findtext("atom:name", "", ns) for a in entry.findall("atom:author", ns)]
            if title:
                entries.append({
                    "title": title[:200],
                    "content": f"[论文摘要] {summary[:1500]}",
                    "tags": ["arxiv", "论文", "AI"],
                    "published": published,
                    "authors": authors[:3],
                    "source_id": hashlib.sha1(title.encode()).hexdigest()[:16],
                })
    except Exception as e:
        print(f"  [WARN] arXiv 解析失败: {e}")
    return entries


def _parse_github_json(data: str) -> list[dict]:
    """解析 GitHub API 响应"""
    try:
        repos = json.loads(data)
        items = []
        for repo in repos if isinstance(repos, list) else repos.get("items", []):
            full_name = repo.get("full_name", "")
            desc = repo.get("description") or ""
            if not full_name:
                continue
            items.append({
                "title": f"[GitHub] {full_name}",
                "content": f"[开源项目] {full_name} — {desc[:1000]}\nStars: {repo.get('stargazers_count', 0)}\nLanguage: {repo.get('language', 'N/A')}",
                "tags": ["github", "开源", "AI"],
                "source_id": hashlib.sha1(full_name.encode()).hexdigest()[:16],
            })
        return items
    except Exception as e:
        print(f"  [WARN] GitHub 解析失败: {e}")
        return []


def _collect_web() -> list[dict]:
    """采集全网学习素材"""
    collected = []
    from datetime import timedelta

    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)

    for src in WEB_SOURCES:
        print(f"  [采集] {src['name']} ...")
        url = src["url"]
        if src.get("dynamic") == "arxiv":
            # 动态生成近 7 天 arXiv 查询
            url = (
                "http://export.arxiv.org/api/query"
                f"?search_query=cat:cs.AI+AND+submittedDate:%5B{week_ago.strftime('%Y%m%d')}+TO+{today.strftime('%Y%m%d')}%5D"
                "&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending"
            )
        raw = _http_get(url)
        if not raw:
            continue
        if src["type"] == "json":
            items = _parse_github_json(raw)
        elif src["type"] == "atom":
            items = _parse_arxiv_atom(raw)
        else:
            items = []
        print(f"    → {len(items)} 条")
        collected.extend(items)
    return collected


def _ingest_via_script(item: dict, source: str = "system") -> dict:
    """通过 gaia_backfeed.py 单条反哺"""
    import subprocess

    cmd = [
        sys.executable, str(BACKFEED), "--ingest",
        "--title", item["title"],
        "--content", item["content"],
        "--type", item.get("knowledge_type", "insight"),
        "--tags", ",".join(item.get("tags", [])),
        "--source-id", item.get("source_id", ""),
        "--source", source,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return json.loads(r.stdout)
        return {"code": 500, "message": r.stderr[-300:]}
    except Exception as e:
        return {"code": 500, "message": str(e)}


def run_self_study(dry_run: bool = False, only_local: bool = False) -> dict:
    """执行一轮自主学习 + 反哺"""
    state = _load_state()
    results = {"web": 0, "local": 0, "failed": 0, "items": []}

    print("=== 盖娅自主学习采集器 ===")
    print(f"时间: {datetime.now(timezone.utc).isoformat()}")
    print()

    # ── 1. 全网学习 ──
    if not only_local:
        print("[阶段1] 全网学习（GitHub/arXiv）")
        web_items = _collect_web()
        for item in web_items:
            sid = f"selfstudy:web:{item['source_id']}"
            if sid in state.get("web_ingested", {}):
                continue
            if dry_run:
                print(f"  [NEW?] {item['title']}")
                results["web"] += 1
                continue
            resp = _ingest_via_script(item, source="system")
            if resp.get("code") == 200:
                state.setdefault("web_ingested", {})[sid] = item["title"]
                results["web"] += 1
                print(f"  [✓] {item['title']}")
            else:
                results["failed"] += 1
                print(f"  [✗] {item['title']}: {resp.get('message')}")

    # ── 2. 本地学习（增量）──
    print()
    print("[阶段2] 本地知识源（五池/项目文档）")
    # 直接复用 backfeed 脚本批量反哺（自带幂等）
    cmd = [sys.executable, str(BACKFEED)] + (["--dry-run"] if dry_run else [])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        print(r.stdout[-2000:])
        # 从输出解析新增数
        for line in r.stdout.splitlines():
            if "新增:" in line:
                results["local"] = int(line.split("新增:")[1].split()[0])
    except Exception as e:
        print(f"  [WARN] 本地反哺失败: {e}")

    # 保存状态
    if not dry_run:
        _save_state(state)

    print()
    print("=== 本轮汇总 ===")
    print(f"全网: {results['web']}  本地: {results['local']}  失败: {results['failed']}")
    return results


def main():
    parser = argparse.ArgumentParser(description="盖娅自主学习采集器")
    parser.add_argument("--dry-run", action="store_true", help="预览不写入")
    parser.add_argument("--only-local", action="store_true", help="只学习本地素材")
    args = parser.parse_args()

    results = run_self_study(dry_run=args.dry_run, only_local=args.only_local)
    # 供 cron 判断：新知识>0 或 失败>0 时非零退出
    if results["failed"] > 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
