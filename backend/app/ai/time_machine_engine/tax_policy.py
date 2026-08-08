#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全球税收政策影响引擎 (tax_policy.py) — 2026-08-08 v2（数据准确性修正）
==================================================
海容要求新增维度：税收政策对出海操作盘子的影响不可少。

⚠️ v2 修正（2026-08-08）：上一版将「境外保险预扣2%个税」「离岸信托设立预征20%个税」
当作已落地的 2026 新政写入，经核实**无公开政策文号支持**（中国现行个税法下保险赔款免征，
保单收益/信托装入资产的征管存在争议且以申报为主），属不准确数据。v2 改为：
- 区分「现行法律规定（可信）」与「监管趋势/传闻（低置信度标注）」
- 每条注明 confidence 与来源，绝不把未证实政策当事实输出

核心场景：
- 中国居民海外投资/资产配置的税收（境外保单收益、信托架构、CRS、资本利得）
- 出海目的地的企业所得税/预提税/转让定价
- 税收对「机会评分」的修正（低税负国 = 机会加分，高税负/新增税 = 机会减分）

数据: 静态档案（各国税收政策要点，带置信度）+ 政策变更事件流（可扩展抓取）
输出: {regime, alerts, country_adjust, china_specific, report}
"""
import json, os, time

# ── 中国税收政策（2026 年核实版）──
# confidence: 高=有法律明文/文号; 中=征管实践/官方表态; 低=传闻/未证实
CHINA_TAX = {
    "country": "中国",
    "iso3": "CHN",
    "notes": [
        {"policy": "保险赔款免征个税", "rate": "0%（免征）", "effective": "现行（个税法§4）",
         "impact": "理赔性质保险赔款依法免征个税；但境外储蓄/投资型保单的现金价值增值与退保收益征管存在争议",
         "confidence": 90, "source": "《个人所得税法》第四条第三项"},
        {"policy": "境外保单收益征管", "rate": "按20%（有争议）", "effective": "现行",
         "impact": "境外投资型保单收益是否按『利息股息红利/财产转让』20%征税，实务执行不一，以自行申报为主",
         "confidence": 55, "source": "个税法第3条+征管实践（无2%预扣政策）"},
        {"policy": "离岸信托税务处理", "rate": "视同转让按20%（有争议）", "effective": "现行",
         "impact": "装入境外信托资产是否视同财产转让征税，无明确文号；监管趋势加强境外所得申报",
         "confidence": 50, "source": "个税法+监管动向（无20%预征文号）"},
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
     "note": "对中投资税务需关注中韩税收协定", "score_adj": 0, "confidence": 80},
    {"country": "美国", "iso3": "USA", "cit": "21%", "wht_dividend": "30%(条约降)", "incentive": "IRA清洁能源补贴",
     "note": "州税另计，转让定价严格", "score_adj": -1, "confidence": 90},
    {"country": "日本", "iso3": "JPN", "cit": "30%", "wht_dividend": "20%(条约降)", "incentive": "有限",
     "note": "全球最低税已立法", "score_adj": -1, "confidence": 90},
]

# ── 税收事件流（政策变更/监管动向，区分已落地与传闻）──
TAX_EVENTS = [
    {"date": "2026-01", "country": "全球", "event": "全球最低税15%落地(GloBE)", "impact": "大型跨国企业税负下限15%，税收优惠空间收窄",
     "severity": "medium", "confidence": 90, "confirmed": True},
    {"date": "2025-07", "country": "美国", "event": "IRA清洁能源补贴细则", "impact": "新能源出海美国可获补贴但需合规",
     "severity": "medium", "confidence": 85, "confirmed": True},
    {"date": "2026-08", "country": "中国", "event": "【传闻】境外保单收益预扣2%个税", "impact": "未获官方文件证实，若落地将影响海外保险配置",
     "severity": "low", "confidence": 20, "confirmed": False},
    {"date": "2026-08", "country": "中国", "event": "【传闻】离岸信托设立预征20%个税", "impact": "未获官方文件证实，若落地将大幅提高信托架构成本",
     "severity": "low", "confidence": 20, "confirmed": False},
]

def assess(country_iso3: str | None = None) -> dict:
    """评估税收政策对出海操作盘子的影响"""
    now = time.strftime("%Y-%m-%d %H:%M")
    # 1. 中国居民配置影响（按置信度排序，高置信在前）
    china_notes = sorted(CHINA_TAX["notes"], key=lambda n: -n.get("confidence", 0))
    # 2. 目的地税收档案
    dest = DESTINATION_TAX
    if country_iso3:
        dest = [d for d in dest if d.get("iso3") == country_iso3] or dest[:1]
    # 3. 政策事件（已落地在前，传闻在后并低置信标注）
    events = sorted(TAX_EVENTS, key=lambda e: (not e.get("confirmed", False), e["date"]), reverse=True)
    # 4. 操作建议
    advice = [
        "🇨🇳 中国个税要点：保险赔款免征（个税法§4）；境外保单收益/信托装入资产征管有争议，以自行申报为主",
        "🌐 全球最低税15%落地 → 跨国架构税收优惠收窄，低税国红利减少，注重实质经营",
        "💡 出海架构优先考虑与中国有税收协定国家 + 单层税制(新加坡/阿联酋) + 合规申报",
    ]
    return {
        "china_tax": {"country": CHINA_TAX["country"], "notes": china_notes},
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
    L.append("| 政策 | 税率 | 状态 | 置信度 |")
    L.append("|:-----|:-----|:-----|:------|")
    for n in data["china_tax"]["notes"][:6]:
        L.append(f"| {n['policy']} | {n['rate']} | {n['effective']} | {n['confidence']}% |")
    L.append("")
    L.append("### 🌍 出海目的地税负参考（企业所得税/股息预提税/优惠）")
    L.append("")
    L.append("| 国家 | 企业所得税 | 股息预提税 | 优惠 | 机会修正 |")
    L.append("|:-----|:----------|:----------|:-----|:--------|")
    for d in data["destinations"][:8]:
        adj = f"+{d['score_adj']}" if d["score_adj"] > 0 else str(d["score_adj"])
        L.append(f"| {d['country']} | {d['cit']} | {d['wht_dividend']} | {d['incentive'][:22]} | {adj} |")
    L.append("")
    L.append("### ⚡ 政策变更/监管动向")
    L.append("")
    for e in data["events"][:4]:
        sev = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(e["severity"], "🟡")
        conf = f"(置信度{e['confidence']}%)"
        L.append(f"- {sev} [{e['date']}] {e['country']} {e['event']} → {e['impact']} {conf}")
    L.append("")
    for a in data["advice"]:
        L.append(a)
    L.append("")
    L.append("*税收数据以官方文件为准，本板块为策略参考非税务意见*")
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
