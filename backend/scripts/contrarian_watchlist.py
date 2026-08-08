#!/usr/bin/env python3
"""
反周期观察清单生成器 (Contrarian Watchlist) — 2026-08-08 海容指示

核心思想（海容原话）：跟美国资本站在同一个牌桌上，利用收割剧本的「确定性规律」赚钱。
美元潮汐收割有剧本（五幕式：潮涌→诱多→组合拳→回流抄底→循环），我们提前建观察清单，
等美国资本动手收割（VIX>25/美元转强/地缘打击）→ 目标国资产暴跌 → 我们与华尔街同场抄底。

多维追踪：
  1. 六维风险评分（外债/通胀/双赤字/主权债/房产/储蓄缓冲）→ 脆弱国排名
  2. 美元潮汐脆弱国（紧缩期高外债+双赤字加权）
  3. 地缘预警（当前被组合拳瞄准的国家）
  4. 科技战承压国（CHN先进制程/KOR存储）
  5. 贵金属信号（黄金/白银 = 去美元化+恐慌对冲）
  6. 反向时光机（中国≈日本1989泡沫顶点的警示定位）

输出: 观察清单 JSON + 报告 MD，含「收割剧本阶段」「抄底信号触发条件」「猎物池分层」
"""

import sys
import json
import os
from datetime import datetime

sys.path.insert(0, "/var/www/ai-digital-card/backend/app/ai")

OUT_DIR = "/var/www/ai-digital-card/backend/data/time_machine_reports"
JSON_OUT = os.path.join(OUT_DIR, "contrarian_watchlist.json")
MD_OUT = os.path.join(OUT_DIR, "contrarian_watchlist_latest.md")


def main():
    from time_machine_engine.risk_warning import RiskWarningEngine
    from time_machine_engine.dollar_tide import DollarTideEngine
    from time_machine_engine.geo_system import GeoSystemEngine
    from time_machine_engine.geopolitics import GeopoliticsAlertEngine
    from time_machine_engine.tech_warfare import TechWarfareEngine
    from time_machine_engine.dimensions import COUNTRY_CN

    # 补充中文名（COUNTRY_CN 缺失的国家）
    EXTRA_CN = {
        "MWI": "马拉维", "SUR": "苏里南", "NAM": "纳米比亚", "KGZ": "吉尔吉斯",
        "BDI": "布隆迪", "SLE": "塞拉利昂", "PSE": "巴勒斯坦", "SOM": "索马里",
        "VCT": "圣文森特", "TLS": "东帝汶", "KIR": "基里巴斯", "DMA": "多米尼克",
        "GRD": "格林纳达", "MDA": "摩尔多瓦", "ISR": "以色列", "SAU": "沙特",
        "SDN": "苏丹", "PAK": "巴基斯坦", "MNE": "黑山", "SYC": "塞舌尔",
        "MDV": "马尔代夫", "KWT": "科威特", "QAT": "卡塔尔", "BRN": "文莱",
        "FRA": "法国", "UKR": "乌克兰", "MOZ": "莫桑比克", "LBN": "黎巴嫩",
        "MUS": "毛里求斯", "CYP": "塞浦路斯", "LUX": "卢森堡", "BTN": "不丹",
    }
    def cn_name(iso3):
        return COUNTRY_CN.get(iso3) or EXTRA_CN.get(iso3, iso3)

    # 明显非猎物（发达国家/避风港，单维拉高分但非退潮目标）→ 从猎物池剔除
    NOT_PREY = {"SGP", "GRC", "ISR", "FRA", "SAU", "QAT", "KWT", "BRN", "ARE"}

    # 微型国家过滤（人口<300万：环境数据稀疏，非可投资标的；skill 坑7）
    MICRO_STATES = {
        "ABW", "AND", "ATG", "BMU", "BRB", "BHR", "BTN", "COM", "CPV", "CYP",
        "DMA", "FJI", "GRD", "KIR", "LCA", "LIE", "LUX", "MDV", "MLT", "MCO",
        "MUS", "NRU", "PLW", "SMR", "SYC", "TLS", "TON", "TUV", "VCT", "VUT",
        "WSM", "MHL", "KNA", "VGB", "CYM", "GIB", "GGY", "JEY", "IMN", "SXM",
        "CUW", "ABW", "PSE", "KWT", "QAT", "BRN",
    }

    lines = ["# 🎯 反周期观察清单（跟美国资本同牌桌）", ""]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(f"> {now} | 核心逻辑：美元收割有剧本，提前建观察清单，退潮期与华尔街同场抄底")
    lines.append("")

    data = {"generated_at": now, "prey_pool": [], "trigger": {}, "tide": {}, "geo": {}, "tech": {}, "metals": {}}

    # ── 1. 六维风险评分（脆弱国排名）──
    lines.append("## 1️⃣ 猎物池（六维风险评分 Top 脆弱国）")
    lines.append("")
    lines.append("> 评分 0-100：🟢低(<25) 🟡中(25-45) 🔴高(45-70) 🟣极危(>70)；单维≥60 升级预警")
    lines.append("")
    lines.append("| # | 国家 | 总分 | 等级 | 房产 | 外债 | 通胀 | 双赤字 | 主权债 | 缓冲 |")
    lines.append("|:-:|:-----|:----:|:----:|:----:|:----:|:----:|:------:|:------:|:----:|")
    try:
        rwe = RiskWarningEngine()
        ranked = rwe.rank_world(top_n=60)
        prey_pool = []
        shown = 0
        for i, r in enumerate(ranked, 1):
            iso = r["iso3"]
            if iso in MICRO_STATES:
                continue  # 过滤微型国家/非投资标的
            cn = cn_name(iso)
            dims = r.get("dims", {})
            total = r.get("total", 0)
            level = r.get("level", "?")
            icon = {"low": "🟢", "medium": "🟡", "high": "🔴", "extreme": "🟣"}.get(level, "❓")
            shown += 1
            lines.append(
                f"| {shown} | **{cn}** ({iso}) | {total:.0f} | {icon}{level} | "
                f"{dims.get('housing', 0):.0f} | {dims.get('debt', 0):.0f} | {dims.get('inflation', 0):.0f} | "
                f"{dims.get('twin_def', 0):.0f} | {dims.get('sovereign', 0):.0f} | {dims.get('buffer', 0):.0f} |"
            )
            if level in ("high", "extreme") and iso not in NOT_PREY:
                prey_pool.append({"iso3": iso, "country": cn, "score": total, "level": level,
                                  "trigger": "VIX>25 或 美元转强 或 地缘打击"})
            if shown >= 25:
                break
        data["prey_pool"] = prey_pool
        lines.append("")
        lines.append(f"🔫 **猎物池：{len(prey_pool)} 国进入观察**（高/极危风险，退潮期第一波倒下候选）")
        lines.append("")
    except Exception as e:
        lines.append(f"⚠️ 风险引擎失败: {e}")
        lines.append("")

    # ── 2. 美元潮汐 ──
    lines.append("## 2️⃣ 美元潮汐（收割剧本当前幕）")
    lines.append("")
    try:
        dte = DollarTideEngine()
        cyc = dte.cycle_stage() or {}
        stage = cyc.get("stage", "?")
        reason = str(cyc.get("reason", ""))[:80]
        tide_icon = {"easing": "🔽", "tightening": "🔼", "turning_easing": "↘️",
                     "turning_tightening": "↗️", "waiting": "➡️"}.get(stage, "➡️")
        # 五幕剧本定位
        act_map = {
            "easing": "第一幕：潮水涌出（布局窗口）",
            "turning_easing": "第一幕→第二幕过渡（最后布局期）",
            "waiting": "第二幕：信号切换（诱多期）",
            "turning_tightening": "第三幕前奏：组合拳预备",
            "tightening": "第三幕：加息抽血（收割期）",
        }
        act = act_map.get(stage, "未知幕")
        lines.append(f"- 潮汐: {tide_icon} **{stage}** — {reason}")
        lines.append(f"- **剧本定位: {act}**")
        data["tide"] = {"stage": stage, "act": act, "reason": reason}
        # 脆弱国
        try:
            vuln = dte.vulnerable_countries(rwe, top_n=8)
            if vuln:
                lines.append(f"- 美元退潮先崩者: {'、'.join(COUNTRY_CN.get(v.get('iso3', ''), v.get('iso3', '?')) for v in vuln)}")
        except Exception:
            pass
        lines.append("")
    except Exception as e:
        lines.append(f"⚠️ 美元潮汐失败: {e}")
        lines.append("")

    # ── 3. 地缘预警（被组合拳瞄准的国家）──
    lines.append("## 3️⃣ 地缘预警（当前被组合拳瞄准）")
    lines.append("")
    try:
        gae = GeopoliticsAlertEngine()
        geo_alert = gae.run(top_n=8)
        alerts = geo_alert.get("alerts", [])
        if alerts:
            lines.append("| 国家 | 预警分 | 等级 | 命中信号 |")
            lines.append("|:-----|:------:|:----:|:---------|")
            for a in alerts[:8]:
                a_iso = a.get("iso3", "?")
                a_cn = cn_name(a_iso) if a_iso != "?" else a.get("country_cn", "?")
                lines.append(f"| {a_cn} | {a.get('score', 0):.0f} | "
                             f"{a.get('level', '?')} | {str(a.get('hits', ''))[:40]} |")
            data["geo"] = {"alerts": [a.get("iso3") for a in alerts[:8]], "count": len(alerts)}
        else:
            lines.append("- 当前无强地缘预警（良性期）")
            data["geo"] = {"alerts": [], "count": 0}
        lines.append("")
    except Exception as e:
        lines.append(f"⚠️ 地缘预警失败: {e}")
        lines.append("")

    # ── 4. 科技战承压 ──
    lines.append("## 4️⃣ 科技战承压国")
    lines.append("")
    try:
        twe = TechWarfareEngine()
        tw = twe.run()
        tw_regime = tw.get("regime", {})
        tw_opp = tw.get("opportunity", {})
        lines.append(f"- 科技战阶段: {tw_regime.get('label', '?')} (信号分 {tw_regime.get('score', 0)})")
        nas = tw_regime.get("nasdaq", {})
        if nas.get("available"):
            lines.append(f"- NASDAQ: {nas.get('last', 0):,.0f} (1年 {nas.get('y1_pct', 0)}%) {nas.get('bubble', '')}")
        if tw_opp.get("pressed_countries"):
            lines.append(f"- 承压: {'、'.join(tw_opp.get('pressed_countries', []))}")
        lines.append(f"- 科技窗口: {tw_opp.get('window', '')}")
        data["tech"] = {"regime": tw_regime.get("regime"), "pressed": tw_opp.get("pressed_countries")}
        lines.append("")
    except Exception as e:
        lines.append(f"⚠️ 科技战失败: {e}")
        lines.append("")

    # ── 5. 贵金属信号 ──
    lines.append("## 5️⃣ 贵金属（去美元化+恐慌对冲）")
    lines.append("")
    try:
        import csv as csv_mod
        def last_stats(path):
            if not os.path.exists(path):
                return None
            rows = []
            with open(path, encoding="utf-8") as f:
                for l in f:
                    if "," in l and l.strip()[0].isdigit():
                        p = l.split(",")
                        try:
                            rows.append(float(p[1]))
                        except (ValueError, IndexError):
                            pass
            if not rows:
                return None
            return {"last": rows[-1], "ytd": (rows[-1] / rows[0] - 1) * 100 if rows else 0,
                    "30d": (rows[-1] / rows[-30] - 1) * 100 if len(rows) >= 30 else 0}
        g = last_stats("/tmp/tm_data/gold.csv")
        s = last_stats("/tmp/tm_data/silver.csv")
        if g:
            lines.append(f"- 黄金 {g['last']:.0f} USD/oz (YTD {g['ytd']:+.1f}% · 30日 {g['30d']:+.1f}%)")
        if s:
            lines.append(f"- 白银 {s['last']:.1f} USD/oz (YTD {s['ytd']:+.1f}% · 30日 {s['30d']:+.1f}%)")
        if g and g.get("ytd", 0) > 30:
            lines.append("- 💡 黄金YTD>30% = 去美元化+避险交易活跃（收割期对冲品）")
        data["metals"] = {"gold": g, "silver": s}
        lines.append("")
    except Exception as e:
        lines.append(f"⚠️ 贵金属失败: {e}")
        lines.append("")

    # ── 6. 抄底信号触发条件 ──
    lines.append("## 6️⃣ 收割信号触发器（什么时候动手）")
    lines.append("")
    lines.append("| 信号 | 触发条件 | 动作 |")
    lines.append("|:-----|:---------|:-----|")
    lines.append("| 🔴 VIX 恐慌 | VIX > 25 | 观察清单 → 抄底池，开始分批建仓 |")
    lines.append("| 🔴 美元转强 | DXY 同比 +3% | 目标国汇率承压，加速观察 |")
    lines.append("| 🟠 地缘打击 | 猎物国被制裁/冲突 | 直接列入急抄名单 |")
    lines.append("| 🟠 科技封锁 | 猎物国芯片/产业被禁 | 该国科技资产打折 → 抄底 |")
    lines.append("| 🟢 贵金属异动 | 黄金单日+3%/白银+5% | 恐慌确认 → 全面防御+抄底预备 |")
    lines.append("")
    data["trigger"] = {
        "vix_threshold": 25,
        "dxy_yoy": 3.0,
        "gold_daily": 3.0,
        "silver_daily": 5.0,
        "note": "触发后引擎自动升档：观察→急抄"
    }

    # ── 7. 完整打法 ──
    lines.append("## 7️⃣ 完整打法（跟美国资本同牌桌）")
    lines.append("")
    lines.append("**牌桌规则：美国资本收割=确定性规律，我们提前坐在猎物对面，等它崩了捡便宜。**")
    lines.append("")
    lines.append("### 阶段 A：观察期（现在）— 建清单，不重仓")
    lines.append("- 每周刷新观察清单（风险/潮汐/地缘/科技/贵金属五维）")
    lines.append("- 猎物池国家逐个做尽调：外债结构/政治风险/优质资产清单")
    lines.append("- 保留 30%+ 现金，等待收割信号")
    lines.append("")
    lines.append("### 阶段 B：收割信号触发（VIX>25 或 美元转强）— 急抄期")
    lines.append("- 第一波抄底（资产打折 30-50%）：流动性好的主权债/龙头股/货币")
    lines.append("- 与美国资本同步进场（他们收割我们也收割）")
    lines.append("")
    lines.append("### 阶段 C：崩盘确认（目标国汇率/股市腰斩）— 重仓期")
    lines.append("- 第二波抄底（打折 50-80%）：优质实体资产/股权/地产")
    lines.append("- 这是孙正义 2000 抄阿里、2008 抄全球的模式")
    lines.append("")
    lines.append("### 阶段 D：修复上行（1-3年后）— 持有套现")
    lines.append("- 目标国经济修复 → 资产升值 3-5 倍 → 高位套现")
    lines.append("- 下一个潮涌周期前退出，等待下一轮")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*观察清单自动刷新 | 引擎生成 | 不构成投资建议*")

    # 保存
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(MD_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n".join(lines[:40]))
    print(f"\n... (共 {len(lines)} 行)")
    print(f"\n✅ 已保存: {MD_OUT}")
    print(f"✅ 已保存: {JSON_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
