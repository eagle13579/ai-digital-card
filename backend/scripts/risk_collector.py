"""
出海时光机引擎 v3 — 风险指标采集器（Risk Data Collector）
==========================================================
从世界银行采集风险预警所需指标，独立缓存避免污染环境数据缓存。

指标（6 维）:
  debt_gni        外债占GNI%       DT.DOD.DECT.GN.ZS   → 债务违约风险
  inflation       通胀率%          FP.CPI.TOTL.ZG      → 货币贬值风险
  current_account 经常账户占GDP%   BN.CAB.XOKA.GD.ZS   → 双赤字风险
  reserves        外储(美元)       FI.RES.TOTL.CD      → 外储脆弱性
  gov_debt        政府债务占GDP%   GC.DOD.TOTL.GD.ZS   → 主权债务风险
  savings         总储蓄占GDP%     NY.GNS.ICTR.ZS      → 缓冲垫
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/var/www/ai-digital-card/backend/app/ai")
from time_machine_engine.collector import WorldBankCollector

DATA_DIR = Path("/var/www/ai-digital-card/backend/data/time_machine_engine")
OUT_FILE = DATA_DIR / "risk_cache.json"

RISK_INDICATORS = {
    "debt_gni": "DT.DOD.DECT.GN.ZS",
    "inflation": "FP.CPI.TOTL.ZG",
    "current_account": "BN.CAB.XOKA.GD.ZS",
    "reserves": "FI.RES.TOTL.CD",
    "gov_debt": "GC.DOD.TOTL.GD.ZS",
    "savings": "NY.GNS.ICTR.ZS",
}


def collect(force: bool = False) -> dict:
    """采集全部风险指标 → risk_cache.json"""
    if os.path.exists(OUT_FILE) and not force:
        with open(OUT_FILE, encoding="utf-8") as f:
            cache = json.load(f)
        age_h = (time.time() - cache.get("fetched_at", 0)) / 3600
        if age_h < 168:  # 7 天缓存
            print(f"缓存仍有效 ({age_h:.0f}h)，--force 强制刷新")
            return cache

    c = WorldBankCollector()
    data = {}
    for key, ind in RISK_INDICATORS.items():
        print(f"  抓取 {key} ({ind})...")
        data[key] = c.fetch_indicator(ind, start_year=2010)
        total = sum(len(v) for v in data[key].values())
        print(f"    → {total} 条")
        time.sleep(0.4)

    payload = {
        "source": "worldbank",
        "metrics": list(RISK_INDICATORS.keys()),
        "fetched_at": time.time(),
        "data": data,
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"✅ 风险指标缓存已保存: {OUT_FILE}")
    return payload


if __name__ == "__main__":
    force = "--force" in sys.argv
    collect(force=force)
