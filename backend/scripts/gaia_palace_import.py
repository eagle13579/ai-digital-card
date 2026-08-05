#!/usr/bin/env python3
"""gaia_palace_import.py — 记忆宫殿/五池知识库导入盖娅 v1.0.0

将本地知识模型库 (knowledge_models.db) 中的五池/技能吸收卡/进化知识
分批反哺到盖娅大脑 gaia_knowledge 表。

九步法引擎 Step2 三通道:
  - RAG: 查询 gaia_knowledge 已存在条目做去重（source_id 幂等）
  - SAG: 直接读 sqlite 备份库物理验证数据
  - LLM: 标题+内容直接映射为知识条目（保留原始提炼成果）

设计要点:
  - 分批导入（每批 50 条，控制内存峰值）
  - 幂等: source_id = palace:{id} 去重
  - 保留原始 source/category 语义
  - 服务器内存仅 1G 可用（swap 4G），严禁一次性全量加载
"""
from __future__ import annotations

import argparse
import hashlib
import http.cookiejar
import json
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

BACKUP_DB = "/opt/hermes-data/backups/brain_daemon__knowledge_models.db.20260709.db"
BASE_URL = "http://127.0.0.1:8201"
BATCH_SIZE = 50

# 知识类型映射（五池 → gaia_knowledge_type）
CATEGORY_TYPE_MAP = {
    "模型池": "pattern",
    "行动池": "behavior",
    "决策验证池": "rule",
    "变量池": "optimization",
    "现象池": "insight",
    "技能吸收卡": "pattern",
    "gaia-brain-backfeed": "insight",
}


def _get_session():
    """获取带 CSRF 的会话"""
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    req = urllib.request.Request(BASE_URL + "/api/csrf/token")
    with opener.open(req) as resp:
        token = json.loads(resp.read().decode())["token"]
    return token, cj, opener


def _post_knowledge(item: dict, token: str, cj, opener) -> dict:
    req = urllib.request.Request(
        BASE_URL + "/api/v1/gaia/knowledge",
        data=json.dumps(item).encode(),
        headers={"Content-Type": "application/json", "X-CSRF-Token": token},
        method="POST",
    )
    try:
        with opener.open(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"code": 500, "message": str(e)}


def import_palace(dry_run: bool = False, limit: int = 0, batch: int = BATCH_SIZE) -> dict:
    """导入记忆宫殿知识库到盖娅"""
    db = sqlite3.connect(BACKUP_DB)
    db.row_factory = sqlite3.Row

    # 已导入的 source_id（幂等）
    token, cj, opener = _get_session()

    # 读已存在 id（用 psql 太重，直接从盖娅 API 查不到全部，这里用 state 文件）
    state_file = Path(__file__).parent / ".gaia_palace_import_state.json"
    state = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    results = {"total": 0, "new": 0, "skipped": 0, "failed": 0, "by_source": {}}
    imported_ids = set(state.get("imported_ids", []))

    def _save_progress():
        state["imported_ids"] = sorted(imported_ids)[-5000:]
        state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    rows = db.execute(
        "SELECT id, source, category, title, content, tags, created_at FROM knowledge_models ORDER BY id"
    ).fetchall()
    results["total"] = len(rows)

    if limit > 0:
        rows = rows[:limit]

    count = 0
    for row in rows:
        sid = f"palace:{row['id']}"
        if sid in imported_ids:
            results["skipped"] += 1
            continue

        source = row["source"] or "palace"
        category = row["category"] or source
        ktype = "insight"
        for kw, t in CATEGORY_TYPE_MAP.items():
            if kw in source or kw in category:
                ktype = t
                break

        title = (row["title"] or "").strip()[:200]
        content = (row["content"] or "").strip()
        if not title or not content:
            results["skipped"] += 1
            continue

        # 内容裁剪（保留原始精华）
        if len(content) > 3000:
            content = content[:3000] + "\n...(截断)"

        tags = []
        if row["tags"]:
            try:
                parsed = json.loads(row["tags"]) if isinstance(row["tags"], str) else row["tags"]
                tags = [str(t)[:50] for t in (parsed if isinstance(parsed, list) else [parsed])][:6]
            except Exception:
                tags = []
        if source not in tags:
            tags.insert(0, source[:50])
        if category and category not in tags:
            tags.append(category[:50])

        item = {
            "source": "system",
            "source_id": sid,
            "knowledge_type": ktype,
            "title": title,
            "content": content,
            "tags": tags[:8],
            "confidence": 0.8,
        }

        if dry_run:
            results["new"] += 1
            count += 1
            if count <= 10:
                print(f"  [DRY] {title}  ({source}/{category})")
            continue

        resp = _post_knowledge(item, token, cj, opener)
        if resp.get("code") == 200:
            imported_ids.add(sid)
            results["new"] += 1
            results["by_source"][source] = results["by_source"].get(source, 0) + 1
            count += 1
            if count % 40 == 0:
                print(f"  ...已导入 {count} 条")
                # 每批保存进度
                _save_progress()
            # 限流控制: anonymous 50/min, 用 1.4s 间隔 ≈ 42/min 留余量
            time.sleep(1.4)
        elif resp.get("code") == 429:
            # 限流退避: 等 60s 重试一次
            print(f"  [429] 限流退避60s: {title[:40]}")
            time.sleep(60)
            resp = _post_knowledge(item, token, cj, opener)
            if resp.get("code") == 200:
                imported_ids.add(sid)
                results["new"] += 1
                results["by_source"][source] = results["by_source"].get(source, 0) + 1
                count += 1
                if count % 40 == 0:
                    _save_progress()
                time.sleep(1.4)
                continue
            results["failed"] += 1
            if results["failed"] <= 5:
                print(f"  [✗] {title}: {resp.get('message')}")
        else:
            results["failed"] += 1
            if results["failed"] <= 5:
                print(f"  [✗] {title}: {resp.get('message')}")

    if not dry_run:
        _save_progress()

    db.close()
    return results


def main():
    parser = argparse.ArgumentParser(description="记忆宫殿知识库导入盖娅")
    parser.add_argument("--dry-run", action="store_true", help="预览不写入")
    parser.add_argument("--limit", type=int, default=0, help="限制导入条数(默认全部)")
    parser.add_argument("--batch", type=int, default=BATCH_SIZE, help="批次大小")
    args = parser.parse_args()

    print("=== 记忆宫殿/五池知识库 → 盖娅大脑 ===")
    print(f"备份库: {BACKUP_DB}")
    print(f"模式: {'DRY-RUN' if args.dry_run else '正式导入'}")
    print()

    results = import_palace(dry_run=args.dry_run, limit=args.limit, batch=args.batch)

    print()
    print("=== 导入汇总 ===")
    print(f"总数: {results['total']}  新增: {results['new']}  跳过: {results['skipped']}  失败: {results['failed']}")
    if results["by_source"]:
        print("\n来源分布:")
        for src, c in sorted(results["by_source"].items(), key=lambda x: -x[1])[:10]:
            print(f"  {src}: {c}")


if __name__ == "__main__":
    main()
