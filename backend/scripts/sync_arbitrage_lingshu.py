#!/usr/bin/env python3
"""
套利模式 → 灵枢情报中枢同步 — 2026-08-08 方向2
把中国软银套利模式库的最新模式同步到灵枢情报中枢（:8555 /api/v1/intel/signals），
让军团看板/其他部门也能看到套利模式洞察。

复用模式：time_machine_engine/_sync_lingshu 的灵枢信号投递方式
"""
import sys
import json
import time
import hashlib
import urllib.request
import os

sys.path.insert(0, "/var/www/ai-digital-card/backend/app/ai")

LINGSHU_API = "http://127.0.0.1:8555"
STATE_FILE = "/var/www/ai-digital-card/backend/data/time_machine_reports/arbitrage_lingshu_state.json"


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"pushed": []}


def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def push_signal(payload: dict) -> bool:
    try:
        req = urllib.request.Request(
            f"{LINGSHU_API}/api/v1/intel/signals",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            d = json.loads(resp.read().decode())
        return d.get("ok", False)
    except Exception as e:
        print(f"  推送失败: {e}")
        return False


def main():
    from china_softbank_engine.arbitrage_patterns import load_patterns
    patterns = load_patterns()
    state = load_state()
    pushed = state.get("pushed", [])
    synced = 0

    for p in patterns:
        pid = p["id"]
        if pid in pushed:
            continue  # 已推送去重
        title = f"[套利模式] {p['name']}"
        summary = (
            f"模式类型: {'宏观收割' if p.get('type') == 'macro_harvest' else '微观套利' if p.get('type') == 'micro_arbitrage' else '规则博弈'} | "
            f"来源: {p.get('source_account', '')}《{p.get('source_series', '')}》 | "
            f"案例: {p.get('case', '')} | "
            f"机制: {p.get('mechanism', '')[:150]} | "
            f"启示: {'；'.join(p.get('arbitrage_insight', [])[:2])}"
        )
        payload = {
            "title": title[:200],
            "summary": summary[:500],
            "domain": "market",
            "source": f"arbitrage_patterns:{pid}",
            "region": "global",
            "tags": ["套利模式", p.get("type", ""), p.get("source_account", "")],
            "url": p.get("source_url", ""),
            "score": {"confidence": p.get("confidence", 0.5)},
            "confidence": p.get("confidence", 0.5),
        }
        if push_signal(payload):
            pushed.append(pid)
            synced += 1
            print(f"  ✅ {pid} {p['name']}")
        time.sleep(0.3)  # 防抖

    state["pushed"] = pushed[-200:]  # 最近200条
    state["last_sync"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_state(state)
    print(f"\n套利模式同步灵枢完成: {synced} 条新信号（累计 {len(pushed)} 条）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
