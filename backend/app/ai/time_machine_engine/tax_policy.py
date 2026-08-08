#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全球税收政策影响引擎 (tax_policy.py) — 2026-08-08
==================================================
海容要求新增维度：税收政策对出海操作盘子的影响不可少。

核心场景：
- 中国居民海外投资/资产配置的税收（海外保险个税、信托税、CRS、资本利得）
- 出海目的地的企业所得税/预提税/转让定价
- 税收对「机会评分」的修正（低税负国 = 机会加分，高税负/新增税 = 机会减分）

数据: 静态档案（各国最新税收政策要点）+ 政策变更事件流（可扩展抓取）
输出: {regime, alerts, country_adjust, china_specific, report}
"""
import json, os, time, datetime

# ── 中国税收政策（2026 年要点）──
CHINA_TAX = {
    "country": "中国",
    "iso3": "CHN",
    "notes": [
        {"policy": "境外保险个税", "rate": "2%", "effective": "2026-08",
         "impact": "中国居民境外保单收益/现金价值增值按2%预扣个税（新增），影响海外保险配置",
         "confidence": 80, "source": "2026年个人所得税新政"},
        {"policy": "离岸信托个税", "rate": "20%", "effective": "2026-08",
         "impact": "设立离岸信托时点按信托资产规模预征20%个税（新增），大幅提高信托架构成本",
         "confidence": 80, "source": "2026年个税新政"},
        {"policy": "CRS信息交换", "rate": "申报", "effective": "2018年起",
         "impact": "中国已参与CRS，海外金融账户信息自动交换，逃税空间收窄",
         "confidence": 90, "source": "CRS多边公约"},
        {"policy": "境外所得抵免", "rate": "抵免", "effective": "现行",
         "impact": "境外已缴税可抵免中国个税（综合所得），避免双重征税，但需申报",
         "confidence": 85, "source": "个税法第7条"},
        {"policy": "资本利得/股息", "rate": "20%", "effective": "现行",
         "impact": "境外股息红利按20%征个税（可抵免），转让境外公司股权按财产转让所得20%",
         "confidence": 85, "source": "个税法"},
    ],
}

# ── 出海目的地税收档案（企业所得税/预提税/优惠）──
DESTINATION_TAX = [
    {"country": "越南", "iso3": "VNM", "cit": "20%", "wht_dividend": "0%", "incentive": "高科技园区4年免税+9年减半",
     "note": "2024起全球最低税15%适用于大型跨国企业", "score_adj": +2, "confidence": 85},
    {"country": "印尼", "iso3": "IDN", "cit": "22%", "wht_dividend": "0%", "incentive": "新首都/新能源产业优惠",
     "note": "电商/制造落地活跃", "score_adj": +1, "confidence": 80},
    {"country": "泰国", "iso3": "THA", "cit": "20%", "wht_dividend": "10%", "incentive": "东部经济走廊EEC优惠",
     "note": "BOI审批项目免3-8年企业所得税", "score_adj": +1, "confidence": 85},
    {"country": "马来西亚", "iso3": "MYS", "cit": "24%", "wht_dividend": "0%", "incentive": "数字经济/清真产业",
     "note": "半导体制造税收优惠", "score_adj": +1, "confidence": 80},
    {"country": "菲律宾", "iso3": "PHL", "cit": "25%", "wht_dividend": "15%", "incentive": "CREATE法案优惠",
     "note": "出口企业免税4-6年", "score_adj": 0, "confidence": 75},
    {"country": "印度", "iso3": "IND", "cit": "22%", "wht_dividend": "20%", "incentive": "生产挂钩激励PLI",
     "note": "新制造企业15%优惠税率", "score_adj": 0, "confidence": 80},
    {"country": "墨西哥", "iso3": "MEX", "cit": "30%", "wht_dividend": "10%", "incentive": "近岸外包IMMEX",
     "note": "美墨加协定受益", "score_adj": 0, "confidence": 75},
    {"country": "阿联酋", "iso3": "ARE", "cit": "9%", "wht_dividend": "0%", "incentive": "自贸区0%",
     "note": "2023起一般企业9%税率，自贸区仍免税", "score_adj": +3, "confidence": 90},
    {"country": "新加坡", "iso3": "SGP", "cit": "17%", "wht_dividend": "0%", "incentive": "区域总部/先驱优惠",
     "note": "单层税制，无资本利得税", "score_adj": +3, "confidence": 90},
    {"country": "韩国", "iso3": "KOR", "cit": "24%", "wht_dividend": "15%", "incentive": "中韩FTA+区域总部",
     "note": "2026对中投资新规关注", "score_adj": 0, "confidence": 80},
    {"country": "美国", "iso3": "USA", "cit": "21%", "wht_dividend": "30%(条约降)", "incentive": "IRA清洁能源补贴",
     "note": "州税另计，转让定价严格", "score_adj": -1, "confidence": 90},
    {"country": "日本", "iso3": "JPN", "cit": "30%", "wht_dividend": "20%(条约降)", "incentive": "有限",
     "note": "全球最低税已立法", "score_adj": -1, "confidence": 90},
]

# ── 税收事件流（政策变更，可扩展为抓取）──
TAX_EVENTS = [
    {"date": "2026-08", "country": "中国", "event": "海外保险收益预扣2%个税", "impact": "海外保险配置税负上升",
     "severity": "high", "confidence": 80},
    {"date": "2026-08", "country": "中国", "event": "离岸信托设立预征20%个税", "impact": "信托架构成本大增，家族办公室策略需重估",
     "severity": "high", "confidence": 80},
    {"date": "2026-01", "country": "全球", "event": "全球最低税15%落地(GloBE)", "impact": "大型跨国企业税负下限15%，税收优惠空间收窄",
     "severity": "medium", "confidence": 90},
    {"date": "2025-07", "country": "美国", "event": "IRA清洁能源补贴细则", "impact": "新能源出海美国可获补贴但需合规",
     "severity": "medium", "confidence": 85},
]

def assess(country_iso3: str | None = None) -> dict:
    """评估税收政策对出海操作盘子的影响"""
    now = time.strftime("%Y-%m-%d %H:%M")
    # 1. 中国居民配置影响
    china_high = [n for n in CHINA_TAX["notes"] if n.get("confidence", 0) >= 75]
    # 2. 目的地税收档案
    dest = DESTINATION_TAX
    if country_iso3:
        dest = [d for d in dest if d.get("iso3") == country_iso3] or dest[:1]
    # 3. 政策事件
    events = sorted(TAX_EVENTS, key=lambda e: e["date"], reverse=True)[:6]
    # 4. 操作建议
    advice = []
    advice.append("🇨🇳 中国税务新规：海外保险2%个税 + 离岸信托20%个税 → 配置成本上升，需重新测算净收益")
    advice.append("🌐 全球最低税15%落地 → 跨国架构税收优惠收窄，低税国红利减少，注重实质经营")
    advice.append("💡 建议：出海架构优先考虑与中国有税收协定国家 + 单层税制(新加坡/阿联酋) + 合规申报")
    return {
        "china_tax": CHINA_TAX,
        "destinations": dest,
        "events": events,
        "advice": advice,
        "generated": now,
    }

def to_report(data: dict) -> str:
    L = []
    L.append("## 💰 全球税收政策 · 影响雷达")
    L.append("")
    L.append("### 🇨🇳 中国居民配置（直接影响操作盘子）")
    L.append("")
    L.append("| 政策 | 税率 | 影响 | 置信度 |")
    L.append("|:-----|:-----|:-----|:------|")
    for n in data["china_tax"]["notes"][:5]:
        L.append(f"| {n['policy']} | {n['rate']} | {n['impact']} | {n['confidence']}% |")
    L.append("")
    L.append("### 🌍 出海目的地税负参考（企业所得税/预提税/优惠）")
    L.append("")
    L.append("| 国家 | 企业所得税 | 股息预提税 | 优惠 | 机会修正 |")
    L.append("|:-----|:----------|:----------|:-----|:--------|")
    for d in data["destinations"][:8]:
        adj = f"+{d['score_adj']}" if d["score_adj"] > 0 else str(d["score_adj"])
        L.append(f"| {d['country']} | {d['cit']} | {d['wht_dividend']} | {d['incentive'][:22]} | {adj} |")
    L.append("")
    L.append("### ⚡ 政策变更事件")
    L.append("")
    for e in data["events"][:4]:
        sev = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(e["severity"], "🟡")
        L.append(f"- {sev} [{e['date']}] {e['country']} {e['event']} → {e['impact']}")
    L.append("")
    for a in data["advice"]:
        L.append(a)
    L.append("")
    return "\n".join(L)

def main():
    import sys
    iso3 = sys.argv[1] if len(sys.argv) > 1 else None
    data = assess(iso3)
    if "--json" in sys.argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(to_report(data))

if __name__ == "__main__":
    main()
