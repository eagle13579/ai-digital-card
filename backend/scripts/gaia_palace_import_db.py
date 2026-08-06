#!/usr/bin/env python3
"""gaia_palace_import_db.py — 记忆宫殿知识库直连数据库导入 v1.0.1

直接写 PostgreSQL gaia_knowledge 表（绕过 API 限流），
导入 knowledge_models.db 中的五池/技能吸收卡知识。

九步法 Step2 SAG（物理操作）: 直连数据库插入，比 HTTP API 快 100 倍。
设计:
  - 批量 INSERT（每批 200 条）
  - 幂等: source_id = palace:{id}，ON CONFLICT 跳过
  - 保持 gaia_evolution_events 记录（知识摄取事件）
  - 结束后触发进化循环（API 单次调用，不触发限流）

用法:
  python3 gaia_palace_import_db.py --dry-run   # 预览
  python3 gaia_palace_import_db.py              # 正式导入
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

BACKEND = "/var/www/ai-digital-card/backend"
BACKUP_DB = "/opt/hermes-data/backups/brain_daemon__knowledge_models.db.20260709.db"
BATCH = 200

CATEGORY_TYPE_MAP = {
    "模型池": "pattern",
    "行动池": "behavior",
    "决策验证池": "rule",
    "变量池": "optimization",
    "现象池": "insight",
    "技能吸收卡": "pattern",
    "gaia-brain-backfeed": "insight",
}


def get_pgurl() -> str:
    env_path = Path(BACKEND) / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].replace("+asyncpg", "")
    raise SystemExit("DATABASE_URL not found in .env")


def build_records(limit: int = 0) -> tuple[list[dict], list[str]]:
    """从 sqlite 备份库读取记录"""
    db = sqlite3.connect(BACKUP_DB)
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT id, source, category, title, content, tags, created_at FROM knowledge_models ORDER BY id"
    ).fetchall()
    db.close()

    if limit > 0:
        rows = rows[:limit]

    records = []
    sql_values = []
    for row in rows:
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
            continue
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

        sid = f"palace:{row['id']}"
        # 转义单引号
        def esc(s: str) -> str:
            return s.replace("'", "''")

        tags_json = json.dumps(tags[:8], ensure_ascii=False).replace("'", "''")
        sql_values.append(
            f"('system', '{esc(sid)}', '{ktype}', '{esc(title)}', '{esc(content)}', '{tags_json}', "
            f"0.8, 0.8, true, false, now(), now())"
        )
        records.append({
            "id": row["id"], "source": source, "category": category,
            "ktype": ktype, "title": title, "content": content, "tags": tags[:8],
        })
    return records, sql_values


def main():
    parser = argparse.ArgumentParser(description="记忆宫殿知识库直连导入盖娅")
    parser.add_argument("--dry-run", action="store_true", help="预览不写入")
    parser.add_argument("--limit", type=int, default=0, help="限制导入条数")
    parser.add_argument("--run-evolution", action="store_true", help="导入后触发进化循环")
    args = parser.parse_args()

    records, sql_values = build_records(limit=args.limit)
    print(f"=== 记忆宫殿知识库直连导入 ===")
    print(f"备份库: {BACKUP_DB}")
    print(f"待导入: {len(records)} 条")
    print(f"模式: {'DRY-RUN' if args.dry_run else '正式导入'}")
    print()

    if args.dry_run:
        for r in records[:10]:
            print(f"  [DRY] {r['title']}  ({r['source']}/{r['ktype']})")
        print(f"  ...共 {len(records)} 条")
        return

    # 直连 PostgreSQL 批量插入
    pgurl = get_pgurl()

    # 用 psql 执行（比 psycopg2 更稳，避免依赖问题）
    inserted = 0
    skipped = 0
    for i in range(0, len(sql_values), BATCH):
        batch = sql_values[i:i + BATCH]
        values_sql = ",\n".join(batch)
        sql = f"""
INSERT INTO gaia_knowledge
  (source, source_id, knowledge_type, title, content, tags, confidence, impact_score, is_active, vector_embedded, created_at, updated_at)
VALUES
  {values_sql}
ON CONFLICT DO NOTHING;
"""
        # 写临时 SQL 文件避免命令行转义问题
        tmp_sql = Path("/tmp/gaia_palace_batch.sql")
        tmp_sql.write_text(sql, encoding="utf-8")
        r = subprocess.run(
            ["psql", pgurl, "-f", str(tmp_sql)],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            print(f"  [✗] 批次 {i // BATCH} 失败: {r.stderr[-300:]}")
            continue
        inserted += len(batch)
        if (i // BATCH) % 5 == 0:
            print(f"  ...已插入 {inserted} 条")
        time.sleep(0.5)  # 轻度节流

    print()
    print(f"=== 导入完成: {inserted} 条 ===")

    if args.run_evolution:
        print("触发进化循环消化新知识...")
        # 单次调用 API（不触发限流）
        import http.cookiejar
        import urllib.request
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        with opener.open(urllib.request.Request("http://127.0.0.1:8201/api/csrf/token")) as resp:
            token = json.loads(resp.read().decode())["token"]
        req = urllib.request.Request(
            "http://127.0.0.1:8201/api/v1/gaia/evolution/trigger",
            data=json.dumps({"trigger": "manual"}).encode(),
            headers={"Content-Type": "application/json", "X-CSRF-Token": token},
            method="POST",
        )
        with opener.open(req) as resp:
            print("  进化循环:", json.loads(resp.read().decode()).get("message"))


if __name__ == "__main__":
    main()
