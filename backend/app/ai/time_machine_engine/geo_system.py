"""
全球系统论引擎 (Global System Theory) — 2026-08-08 海容认知注入

海容核心认知：美元潮汐不是单一金融动作，而是配合政治/军事/地缘冲突
（包括制裁、冲突、生化危机、病毒等）的「组合拳」——美国为配合美元回流，
会用工具箱手段影响目标国政治 → 逼当地崩盘 → 资本回流美国 → 完成收割。

三层系统架构（本质 → 现象）：
  本质层（因）: 美元潮汐周期 + 地缘政治军事手段（工具箱）
  载体层（通道）: 大宗商品 / 汇率 / 利率 / 股市 / 楼市 / 债市 / 资本市场
  现象层（果）: 金融衍生品（恐慌/波动放大）

数据源：FRED 公开 CSV（免 key）
  - FEDFUNDS 联邦基金利率（1954起）
  - DTWEXBGS 美元指数（2006起）
  - DCOILWTICO WTI原油（1986起）
  - PCOPPUSDM 铜价（1992起）
  - VIXCLS VIX恐慌指数（1990起，现象层代理）
本地缓存: /tmp/tm_data/{wti,copper,vix}.csv + /tmp/{fedfunds,dxy}.csv
"""

import csv
import os
import re
from datetime import datetime

DATA_DIR = "/tmp/tm_data"
FEDFUNDS_CSV = "/tmp/fedfunds.csv"
DXY_CSV = "/tmp/dxy.csv"

# ── 美国工具箱 · 历史组合拳事件库（每个危机 = 潮汐 + 地缘手段的合力）──
# 2026-08-08 扩充 7→15：补墨西哥1994/俄罗斯1998/阿根廷2001/欧债2010/印度2013/巴西2015/委内瑞拉2016/阿根廷2019
TOOLKIT_EVENTS = [
    {
        "year": 1982,
        "event": "拉美债务危机（墨西哥违约）",
        "tide": "暴力加息 14%+",
        "tools": ["沃尔克激进加息", "美元走强", "马岛战争(地缘冲突)", "油价回落冲击产油国"],
        "targets": "墨西哥/阿根廷/巴西",
        "carrier": "主权债违约 → 汇率崩 → 股市崩",
        "lesson": "加息+地缘摩擦组合拳下，高外债新兴市场最先崩",
    },
    {
        "year": 1994,
        "event": "墨西哥比索危机（龙舌兰酒危机）",
        "tide": "加息周期 5.5%",
        "tools": ["美元走强", "美联储连续加息", "比索贬值+资本外逃"],
        "targets": "墨西哥",
        "carrier": "比索崩 → 股市崩 → 蔓延拉美(龙舌兰效应)",
        "lesson": "固定汇率+短期外债高企，加息初期就顶不住",
    },
    {
        "year": 1997,
        "event": "亚洲金融危机（泰铢崩盘）",
        "tide": "加息周期 5.5%",
        "tools": ["美元持续走强", "国际资本做空泰铢", "热钱撤离"],
        "targets": "泰国/印尼/韩国/马来西亚",
        "carrier": "汇率崩 → 股市崩 → 楼市崩 → 外储耗尽",
        "lesson": "固定汇率+高外债+资产泡沫 = 退潮期最脆弱组合",
    },
    {
        "year": 1998,
        "event": "俄罗斯国债违约（+LTCM崩盘）",
        "tide": "加息周期中段",
        "tools": ["亚洲危机传染", "油价低迷", "政治动荡(政府换血)", "债务违约+卢布贬值"],
        "targets": "俄罗斯→美国对冲基金",
        "carrier": "国债违约 → 卢布崩 → LTCM连锁爆仓 → 全球信用恐慌",
        "lesson": "地缘+政治动荡放大债务危机，衍生品杠杆把危机传到华尔街",
    },
    {
        "year": 2001,
        "event": "阿根廷债务危机",
        "tide": "宽松末期/紧缩担忧",
        "tools": ["美元走强", "比索联系汇率僵化", "IMF救助反复", "政治动荡(5换总统)"],
        "targets": "阿根廷",
        "carrier": "债务违约(史上最大主权违约) → 比索崩 → 银行挤兑 → 骚乱",
        "lesson": "联系汇率+财政失控+政治不稳 = 违约教科书案例",
    },
    {
        "year": 2008,
        "event": "全球金融危机",
        "tide": "加息至 5.25% 后泡沫破裂",
        "tools": ["连续17次加息", "美元升值", "次贷衍生品杠杆放大"],
        "targets": "美国→全球",
        "carrier": "楼市崩 → 衍生品(CDO/CDS)连环炸 → 全球股市崩",
        "lesson": "衍生品层是放大器：底层资产崩,现象层炸得最响",
    },
    {
        "year": 2010,
        "event": "欧洲主权债务危机（希腊引爆）",
        "tide": "零利率时代/欧债分化",
        "tools": ["美元避险回流", "希腊财政造假曝光", "评级下调", "欧元区政治博弈"],
        "targets": "希腊/爱尔兰/葡萄牙/西班牙/意大利",
        "carrier": "国债利差飙升 → 银行危机 → 紧缩动荡",
        "lesson": "主权债+政治博弈：财政弱国在避险潮中先被抛售",
    },
    {
        "year": 2013,
        "event": "印度卢比危机（Taper Tantrum）",
        "tide": "QE退出信号(紧缩预期)",
        "tools": ["伯南克暗示缩减QE", "美元转强", "热钱撤离", "经常账户赤字暴露"],
        "targets": "印度/印尼/南非/巴西(脆弱五国)",
        "carrier": "卢比崩 → 股市外资撤离 → 债券收益率飙升",
        "lesson": "只靠一句话(taper信号)就够抽血——脆弱五国同日被抛售",
    },
    {
        "year": 2014,
        "event": "俄罗斯卢布危机",
        "tide": "宽松尾声转向紧缩",
        "tools": ["乌克兰冲突+克里米亚制裁", "油价$110→$50", "资本外逃"],
        "targets": "俄罗斯",
        "carrier": "油价崩(大宗) → 卢布崩 → 资本管制",
        "lesson": "地缘制裁+大宗商品双杀：资源国在美元退潮期尤其脆弱",
    },
    {
        "year": 2015,
        "event": "巴西经济危机（衰退+政治风暴）",
        "tide": "美元走强/大宗商品熊市",
        "tools": ["大宗商品崩盘(铁矿石/大豆)", "美元走强", "反腐风暴(洗车行动)", "政治僵局"],
        "targets": "巴西",
        "carrier": "雷亚尔崩 → 股市崩 → 衰退+通胀(滞胀)",
        "lesson": "资源依赖+政治动荡叠加：商品熊市+美元走强=双重抽血",
    },
    {
        "year": 2016,
        "event": "委内瑞拉崩溃（恶性通胀）",
        "tide": "美元走强/油价暴跌",
        "tools": ["油价$100→$30", "美国制裁升级", "政治极权+经济管制", "外汇储备耗尽"],
        "targets": "委内瑞拉",
        "carrier": "油价崩 → 外储耗尽 → 恶性通胀(1000000%+) → 人道危机",
        "lesson": "制裁+油价+治理失败三连击：主权信用彻底崩塌",
    },
    {
        "year": 2018,
        "event": "土耳其里拉/阿根廷比索危机",
        "tide": "加息周期 2.4%",
        "tools": ["美元走强", "美土关系恶化(制裁施压)", "高外债+双赤字暴露"],
        "targets": "土耳其/阿根廷",
        "carrier": "里拉崩 → 外债偿付危机 → 股市崩",
        "lesson": "宏观看着健康的国家，美元退潮+地缘施压也会被抽干",
    },
    {
        "year": 2019,
        "event": "阿根廷比索危机（二次爆发）",
        "tide": "美联储转鸽/美元仍强",
        "tools": ["IMF救助失败", "政治风险(初选爆冷)", "外汇管制", "比索再度崩盘"],
        "targets": "阿根廷",
        "carrier": "比索崩 → 违约预期 → 资本管制 → 经济衰退",
        "lesson": "救助拖延+政治冲击：同一国家可被组合拳反复收割",
    },
    {
        "year": 2020,
        "event": "COVID-19 全球流动性危机",
        "tide": "危机紧急降息至 0（恐慌救急）",
        "tools": ["病毒(生化)冲击全球", "供应链断裂", "恐慌性抛售"],
        "targets": "全球",
        "carrier": "股市暴跌 → 流动性枯竭 → 美联储无限QE救市",
        "lesson": "生化危机也是工具箱一环：制造恐慌→资本寻求美元避险→回流",
    },
    {
        "year": 2022,
        "event": "斯里兰卡违约/全球紧缩",
        "tide": "激进加息 4%+",
        "tools": ["俄乌冲突(地缘)", "粮食/能源价格暴涨", "美元指数20年新高"],
        "targets": "斯里兰卡/巴基斯坦/埃及",
        "carrier": "外储耗尽 → 主权违约 → 汇率崩",
        "lesson": "加息潮+地缘冲突叠加,最脆弱的债务国率先倒下",
    },
]

# ── 载体层名称映射 ──
CARRIER_CN = {
    "wti": "原油WTI", "copper": "铜", "vix": "VIX恐慌指数",
    "fed_funds": "联邦基金利率", "dxy": "美元指数",
}


class GeoSystemEngine:
    """全球系统论引擎：本质层(潮汐+地缘) → 载体层(商品/汇率/利率) → 现象层(衍生品/恐慌)"""

    def __init__(self):
        self._carrier = {}
        self._load_carriers()

    # ── 数据加载 ──────────────────────────────────────────

    def _load_carriers(self):
        """加载载体层 CSV（FRED 数据）"""
        for name in ("wti", "copper", "vix"):
            path = os.path.join(DATA_DIR, f"{name}.csv")
            rows = []
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("observation_date"):
                            continue
                        parts = line.split(",")
                        if len(parts) < 2:
                            continue
                        date, val = parts[0], parts[1]
                        if val in ("", ".", "."):
                            continue
                        try:
                            rows.append((date, float(val)))
                        except ValueError:
                            continue
            self._carrier[name] = rows
        # 利率/美元指数
        for name, path in (("fed_funds", FEDFUNDS_CSV), ("dxy", DXY_CSV)):
            rows = []
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("observation_date"):
                            continue
                        parts = line.split(",")
                        if len(parts) < 2:
                            continue
                        try:
                            rows.append((parts[0], float(parts[1])))
                        except ValueError:
                            continue
            self._carrier[name] = rows

    def _recent(self, name: str, years: int = 3) -> list:
        """取最近 N 年的日/月频数据"""
        rows = self._carrier.get(name, [])
        if not rows:
            return []
        cutoff = datetime.now().year - years
        return [r for r in rows if r[0][:4].isdigit() and int(r[0][:4]) >= cutoff]

    # ── 载体层状态 ────────────────────────────────────────

    def carrier_status(self) -> dict:
        """载体层当前状态：趋势 + 异常"""
        status = {}
        for name, label in CARRIER_CN.items():
            rows = self._recent(name, years=2)
            if len(rows) < 4:
                status[name] = {"label": label, "ok": False}
                continue
            # 一年前均值 vs 当前值
            cur = rows[-1][1]
            one_year_ago = [r[1] for r in rows if r[0] < f"{datetime.now().year - 1}-12-31"]
            base = sum(one_year_ago[-60:]) / max(1, len(one_year_ago[-60:])) if one_year_ago else cur
            chg = (cur - base) / base * 100 if base else 0
            # 12个月窗口内最大摆动（波动性）
            window = rows[-252:] if name in ("wti", "vix", "dxy") else rows[-12:]
            vals = [r[1] for r in window]
            vol = (max(vals) - min(vals)) / (sum(vals) / max(1, len(vals))) * 100 if vals else 0
            status[name] = {
                "label": label,
                "current": round(cur, 2),
                "yoy_change_pct": round(chg, 1),
                "volatility_pct": round(vol, 1),
                "date": rows[-1][0],
                "ok": True,
            }
        return status

    # ── 系统阶段判定（本质层+载体层 → 系统状态）──────────────

    def system_regime(self, dollar_stage: dict | None = None) -> dict:
        """
        判定全球系统当前所处阶段：
          regime: harvest(收割期·潮退) / pump(注水期·潮涌) / transition(转向) / calm(平静)
        输入 dollar_stage: DollarTideEngine.cycle_stage() 输出（可选）
        """
        carrier = self.carrier_status()
        vix = carrier.get("vix", {})
        wti = carrier.get("wti", {})
        dxy = carrier.get("dxy", {})

        # 恐慌度：VIX > 25 恐慌 / > 35 极度恐慌 / < 15 平静
        vix_cur = vix.get("current", 15.0)
        fear = "extreme" if vix_cur > 35 else "high" if vix_cur > 25 else "low" if vix_cur < 15 else "normal"

        # 美元趋势（来自载体）
        dxy_chg = dxy.get("yoy_change_pct", 0)

        # 结合美元潮汐阶段
        tide_stage = (dollar_stage or {}).get("stage", "waiting")
        risk_mode = (dollar_stage or {}).get("risk_mode", "neutral")

        # 系统阶段判定
        if risk_mode == "risk_off" or (tide_stage in ("tightening", "turning_tightening")):
            if fear in ("extreme", "high"):
                regime = "harvest_crisis"   # 退潮+恐慌 = 收割/危机共振
            else:
                regime = "harvest"          # 退潮但未恐慌 = 缓慢抽血
        elif risk_mode == "risk_on" or tide_stage in ("easing", "turning_easing"):
            regime = "pump" if vix_cur < 20 else "pump_wary"
        else:
            regime = "calm"

        # 大宗商品信号（通胀/需求代理）
        commodity_up = (wti.get("yoy_change_pct", 0) > 10) or (carrier.get("copper", {}).get("yoy_change_pct", 0) > 10)

        return {
            "regime": regime,
            "fear": fear,
            "vix_current": vix_cur,
            "dxy_yoy_pct": dxy_chg,
            "commodity_up": commodity_up,
            "tide_stage": tide_stage,
            "risk_mode": risk_mode,
            "carrier": carrier,
        }

    # ── 历史工具箱匹配（当前最像哪个历史阶段）──────────────

    def toolkit_match(self, regime: dict) -> list[dict]:
        """把当前系统状态与历史组合拳事件对比，找出最相似的 3 个"""
        vix = regime.get("vix_current", 15)
        fear = regime.get("fear", "normal")
        tide = regime.get("tide_stage", "waiting")

        scored = []
        for ev in TOOLKIT_EVENTS:
            s = 0
            # 潮汐相似（权重最高：当前阶段最像哪个历史潮汐）
            is_crisis_easing = "危机" in ev["tide"]
            if "加息" in ev["tide"] and tide in ("tightening", "turning_tightening"):
                s += 5
            if "降息" in ev["tide"] and tide in ("easing", "turning_easing"):
                # 危机式降息只有恐慌时才匹配，正常宽松不匹配危机
                if is_crisis_easing and fear in ("extreme", "high"):
                    s += 5
                elif not is_crisis_easing:
                    s += 5
                else:
                    s -= 3
            if "加息" in ev["tide"] and tide in ("easing", "turning_easing"):
                s -= 2
            # 美元走强 vs 当前美元趋势
            if "走强" in ev["tide"] and regime.get("dxy_yoy_pct", 0) > 0:
                s += 2
            if "走强" in ev["tide"] and regime.get("dxy_yoy_pct", 0) < 0:
                s -= 1
            # 恐慌匹配（次级信号）
            if "恐慌" in ev["event"] and fear in ("extreme", "high"):
                s += 2
            if "危机" in ev["event"] and fear == "low":
                s -= 1
            # 大宗商品共振（油价崩=资源国危机类）
            if "油价" in ev["carrier"] and regime.get("commodity_up"):
                s += 1
            scored.append({**ev, "_score": s})
        scored.sort(key=lambda x: -x["_score"])
        return scored[:3]

    # ── 机会校准（系统论 → 投资建议修正）──────────────────

    def adjust_opportunity(self, regime: dict) -> dict:
        """
        系统论机会校准：本质层(潮汐+地缘) + 现象层(恐慌) → 综合建议
        """
        r = regime.get("regime")
        if r == "harvest_crisis":
            return {
                "window": "crash",
                "multiplier": 0.5,
                "advice": "🌪️ 收割共振期：美元退潮+恐慌蔓延，全球资产承压。"
                          "这是现金为王阶段，但也是 2-3 年后抄底优质新兴市场的起点。"
                          "建议：撤离脆弱国 → 留现金/美元资产 → 观察猎物清单",
                "strategy": "避险保本",
            }
        if r == "harvest":
            return {
                "window": "tightening",
                "multiplier": 0.75,
                "advice": "🩸 缓慢抽血期：美元走强+流动性收缩，新兴市场资金外流。"
                          "机会集中在低外债/高外储/内需强的国家，避开高双赤字国。"
                          "建议：聚焦安全边际高的市场，控制杠杆",
                "strategy": "精挑细选",
            }
        if r == "pump":
            return {
                "window": "open",
                "multiplier": 1.15,
                "advice": "🌊 潮水涌入期：美元宽松+恐慌低位，资本涌向新兴市场。"
                          "这是出海布局的黄金窗口，历史经验：降息初期进场的回报最高。"
                          "建议：加大力度布局高增长新兴市场",
                "strategy": "积极进攻",
            }
        if r == "pump_wary":
            return {
                "window": "open_cautious",
                "multiplier": 1.0,
                "advice": "🌊 潮水涌入但需警惕：美元宽松但市场仍有波动。"
                          "建议：正常布局，但关注地缘风险事件",
                "strategy": "进攻+对冲",
            }
        return {
            "window": "neutral",
            "multiplier": 1.0,
            "advice": "⏳ 系统平静期：各层无明显共振信号，按基本面正常布局。"
                      "建议：维持正常节奏，关注美联储动向",
            "strategy": "按兵观望",
        }

    # ── 报告 ──────────────────────────────────────────────

    def to_report(self, regime: dict, adjust: dict, matches: list[dict]) -> str:
        lines = [
            "# 🌍 全球系统论 · 三层透视",
            "",
            "> 海容系统观：美元潮汐不是单一动作，是配合地缘政治/军事/生化手段的",
            "> 组合拳。本质层(潮汐+地缘) → 载体层(商品/汇率/利率/股楼债) → 现象层(衍生品)",
            "",
            "## ① 本质层 · 美元潮汐 + 地缘工具箱",
            f"- 潮汐阶段: **{regime.get('tide_stage')}**（风险模式 {regime.get('risk_mode')}）",
            f"- 美元指数: {regime.get('dxy_yoy_pct'):+.1f}% (同比)",
            f"- 恐慌指数 VIX: **{regime.get('vix_current')}** → {regime.get('fear')}",
            f"- 大宗商品: {'📈 上行(通胀压力/需求旺)' if regime.get('commodity_up') else '➡️ 平稳'}",
            "",
            "## ② 载体层 · 五大通道状态",
            "",
        ]
        carrier = regime.get("carrier", {})
        for name in ("fed_funds", "dxy", "wti", "copper", "vix"):
            c = carrier.get(name)
            if not c or not c.get("ok"):
                lines.append(f"- {CARRIER_CN.get(name, name)}: 数据不足")
                continue
            lines.append(
                f"- **{c['label']}** {c['current']} (同比 {c['yoy_change_pct']:+.1f}%, "
                f"波动 {c['volatility_pct']:.0f}%)"
            )
        lines.append("")
        lines.append(f"## ③ 系统阶段判定: **{regime.get('regime')}** — {adjust.get('strategy')}")
        lines.append("")
        lines.append(f"> {adjust.get('advice')}")
        lines.append("")
        lines.append("## 📜 历史组合拳对照（当前最像）")
        lines.append("")
        for m in matches:
            tools = " + ".join(m["tools"][:3])
            lines.append(
                f"- **{m['year']} {m['event']}** — 潮汐[{m['tide']}] "
                f"工具箱[{tools}] → {m['carrier']}"
            )
            lines.append(f"  - 启示: {m['lesson']}")
        lines.append("")
        return "\n".join(lines)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/var/www/ai-digital-card/backend/app/ai")
    from time_machine_engine.dollar_tide import DollarTideEngine

    gse = GeoSystemEngine()
    dte = DollarTideEngine()
    stage = dte.cycle_stage()
    regime = gse.system_regime(stage)
    adjust = gse.adjust_opportunity(regime)
    matches = gse.toolkit_match(regime)
    print(gse.to_report(regime, adjust, matches))
