"""
加密货币/黄金套利维度 (Crypto & Metals Arbitrage) — 2026-08-08 海容方向3

美元退潮期的另类资产路径：黄金/白银/比特币是美元收割的对冲品——
美元贬值/恐慌期它们逆势上涨，是「跟美国资本同牌桌」的另类武器。

数据源（阿里云实测可达）：
  - blockchain.info/ticker — BTC 实时价格（多币种，免key）✅
  - gold-api.com — 黄金实时（已接入 gold_silver_fetch.py）
  - /tmp/tm_data/{gold,silver}.csv — 贵金属历史（每日自动追加）

信号设计：
  1. 黄金/白银趋势（1日/7日/30日/YTD）
  2. BTC 价格 + 波动
  3. 避险共振信号：美元弱 + 贵金属涨 + BTC 涨 = 美元退潮确认
  4. 套利路径建议：黄金ETF/白银/比特币/矿业股
"""

import os
import json
import urllib.request
from datetime import datetime

DATA_DIR = "/tmp/tm_data"
BTC_CACHE = "/tmp/tm_data/btc.json"


class CryptoMetalsEngine:
    """加密货币/黄金套利维度引擎"""

    def __init__(self):
        self.name = "crypto_metals_arbitrage"

    # ── 数据获取 ──────────────────────────────────────────

    def _fetch_btc(self) -> dict | None:
        """从 blockchain.info 抓 BTC 价格（USD 计价）"""
        try:
            url = "https://blockchain.info/ticker"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            usd = data.get("USD", {})
            cny = data.get("CNY", {})
            return {
                "available": True,
                "usd": usd.get("last"),
                "cny": cny.get("last"),
                "usd_15m": usd.get("15m"),
                "ts": datetime.now().isoformat(),
            }
        except Exception:
            return None

    def _load_metals(self) -> dict:
        """读取贵金属 CSV 历史"""
        def load(path):
            if not os.path.exists(path):
                return []
            rows = []
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if "," in line and line.strip()[0].isdigit():
                        parts = line.split(",")
                        try:
                            rows.append((parts[0].strip(), float(parts[1])))
                        except (ValueError, IndexError):
                            pass
            return rows
        return {"gold": load(f"{DATA_DIR}/gold.csv"), "silver": load(f"{DATA_DIR}/silver.csv")}

    def _stats(self, rows: list) -> dict | None:
        if not rows:
            return None
        vals = [v for _, v in rows]
        last = vals[-1]
        def pct(idx):
            if idx < 0 or idx >= len(vals):
                return 0.0
            return round((last / vals[idx] - 1) * 100, 1) if vals[idx] else 0.0
        return {
            "last": last,
            "d1": pct(-2),
            "d7": pct(-8),
            "d30": pct(-30),
            "ytd": pct(0),
        }

    # ── 信号判定 ──────────────────────────────────────────

    def assess(self, dollar_stage: str | None = None) -> dict:
        """美元退潮期另类资产套利评估"""
        metals = self._load_metals()
        gold = self._stats(metals.get("gold", []))
        silver = self._stats(metals.get("silver", []))
        btc = self._fetch_btc()

        signals = []
        # 黄金/白银趋势
        if gold:
            if gold["ytd"] > 30:
                signals.append("黄金YTD>30%：去美元化+避险交易活跃")
            if gold["d30"] > 10:
                signals.append("⚠️ 黄金30日加速：短期过热防回调")
        if silver:
            if silver["ytd"] > 60:
                signals.append("白银翻倍级：贵金属牛市放大器")
            if silver["d1"] > 5:
                signals.append(f"⚠️ 白银单日+{silver['d1']}%：异动预警")
        # BTC
        if btc and btc.get("usd"):
            btc_usd = btc["usd"]
            signals.append(f"BTC {btc_usd:,.0f} USD")
        # 避险共振
        resonance = 0
        if gold and gold["ytd"] > 30:
            resonance += 1
        if silver and silver["ytd"] > 60:
            resonance += 1
        if dollar_stage in ("easing", "turning_easing"):
            resonance += 1
        if resonance >= 3:
            signals.append("🟢 避险共振确认：美元退潮 + 贵金属牛市 + 宽松周期 = 另类资产窗口")
        elif resonance >= 2:
            signals.append("🟡 避险共振初现：关注贵金属/加密对冲配置")

        # 套利路径
        paths = []
        if gold and gold["ytd"] > 20:
            paths.append("黄金ETF/纸黄金（趋势跟随）")
        if silver and silver["ytd"] > 50:
            paths.append("白银（牛市放大器，波动大于黄金）")
        if btc and btc.get("usd") and btc["usd"] > 50000:
            paths.append("比特币（数字黄金，美元贬值对冲）")
        if gold and gold["ytd"] > 30:
            paths.append("黄金矿业股（杠杆放大金价）")

        return {
            "gold": gold,
            "silver": silver,
            "btc": btc,
            "signals": signals,
            "resonance": resonance,
            "paths": paths,
            "window": "另类资产窗口开启" if resonance >= 2 else "另类资产观望",
        }

    # ── 报告 ──────────────────────────────────────────────

    def to_report(self, data: dict) -> str:
        lines = ["### 💎 加密货币/黄金套利（美元退潮另类资产）"]
        g = data.get("gold")
        s = data.get("silver")
        b = data.get("btc")
        if g:
            lines.append(f"- 🥇 黄金 {g['last']:.0f} USD/oz (1日{g['d1']:+.1f}% · 7日{g['d7']:+.1f}% · 30日{g['d30']:+.1f}% · YTD{g['ytd']:+.1f}%)")
        if s:
            lines.append(f"- 🥈 白银 {s['last']:.1f} USD/oz (1日{s['d1']:+.1f}% · 7日{s['d7']:+.1f}% · 30日{s['d30']:+.1f}% · YTD{s['ytd']:+.1f}%)")
        if b and b.get("usd"):
            lines.append(f"- ₿ BTC {b['usd']:,.0f} USD ({b.get('cny', 0):,.0f} CNY)")
        for sig in data.get("signals", []):
            lines.append(f"  💡 {sig}")
        if data.get("paths"):
            lines.append(f"- 🛣️ 套利路径: {'；'.join(data.get('paths', []))}")
        lines.append(f"- 🚪 窗口: {data.get('window', '')}")
        return "\n".join(lines)


if __name__ == "__main__":
    eng = CryptoMetalsEngine()
    data = eng.assess()
    print(eng.to_report(data))
