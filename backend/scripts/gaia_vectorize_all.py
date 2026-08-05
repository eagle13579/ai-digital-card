#!/usr/bin/env python3
"""gaia_vectorize_all.py — 全量向量化循环 v1.0.0

进化循环每次只处理 500 条待向量化知识（硬编码 limit(500)），
本脚本循环触发直到全部向量化完成。

用法:
  python3 gaia_vectorize_all.py              # 循环触发直到完成
  python3 gaia_vectorize_all.py --max-rounds 3  # 最多跑3轮
"""
from __future__ import annotations

import http.cookiejar
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BACKEND = "/var/www/ai-digital-card/backend"
BASE = "http://127.0.0.1:8201"


def get_pgurl() -> str:
    env_path = Path(BACKEND) / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].replace("+asyncpg", "")
    raise SystemExit("DATABASE_URL not found")


def remaining_count() -> int:
    """未向量化数量"""
    r = subprocess.run(
        ["psql", get_pgurl(), "-t", "-c",
         "SELECT count(*) FROM gaia_knowledge WHERE vector_embedded = false;"],
        capture_output=True, text=True, timeout=15,
    )
    return int((r.stdout or "0").strip())


def trigger_evolution() -> dict:
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    with opener.open(urllib.request.Request(BASE + "/api/csrf/token")) as resp:
        token = json.loads(resp.read().decode())["token"]
    req = urllib.request.Request(
        BASE + "/api/v1/gaia/evolution/trigger",
        data=json.dumps({"trigger": "manual"}).encode(),
        headers={"Content-Type": "application/json", "X-CSRF-Token": token},
        method="POST",
    )
    try:
        with opener.open(req, timeout=240) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"code": 500, "message": str(e)}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="全量向量化循环")
    parser.add_argument("--max-rounds", type=int, default=0, help="最多轮数(0=直到完成)")
    parser.add_argument("--interval", type=float, default=3.0, help="轮间间隔秒")
    args = parser.parse_args()

    print("=== 盖娅全量向量化循环 ===")
    rounds = 0
    while True:
        remain = remaining_count()
        print(f"轮次 {rounds + 1}: 未向量化 {remain} 条")
        if remain <= 0:
            print("✅ 全部向量化完成！")
            break
        if args.max_rounds and rounds >= args.max_rounds:
            print(f"达到最大轮数 {args.max_rounds}，停止。剩余 {remain} 条")
            break

        result = trigger_evolution()
        status = result.get("data", {}).get("status", "unknown")
        idx = result.get("data", {}).get("vector_index_size", 0)
        print(f"  进化循环: {status} (vector_index_size={idx})")
        if result.get("code") != 200:
            print(f"  [✗] {result.get('message')}")
            break
        rounds += 1
        time.sleep(args.interval)

    print(f"\n最终状态: {remaining_count()} 条未向量化")


if __name__ == "__main__":
    main()
