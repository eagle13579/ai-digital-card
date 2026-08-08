"""
出海时光机引擎 v3 — 反向时光机模块（Reverse Time Machine）
==========================================================
核心洞察（海容 2026-08-08 提出）：
  时光机是双向的。正向=中国模式→海外（出海投资）；反向=海外已验证周期→中国国内预判。

反向时光机 = 用"发达经济体已经走完的周期"预判"中国/其他后发市场正在经历或即将经历的阶段"。

典型应用（用户举例——房地产）：
  日本 1980s 房地产泡沫 → 1991 崩盘 → 资产负债表衰退 30 年
  中国房地产 2010s-2020s 周期 → 对比日本当年数据 → 预判"中国现在处于日本哪一年"
  → 指导投资决策（何时买房/何时撤离/何时抄底）

实现：
  1. 定义"基准周期档案"（日本房地产/美国次贷/香港楼市等已完成周期）
  2. 每个档案含"关键指标时间序列"（房价指数/城镇化率/人均GDP/利率等）
  3. 对比目标国当前指标 vs 基准国历史轨迹 → 找到"最相似的历史年份"
  4. 输出: 目标国当前 ≈ 基准国 X 年 → 未来走势参考基准国 X+1, X+2... 年
"""

import logging
from datetime import datetime

from .collector import WorldBankCollector

logger = logging.getLogger("time_machine_v3_reverse")

# ── 基准周期档案（发达经济体已走完的完整周期）──────────────
# 每个档案记录"关键阶段的指标快照"，用于与目标国当前状态比对。
# 指标值 = 公开历史数据（世界银行/官方统计）
# phase_year: 该阶段对应日历年份
# phase_label: 阶段名称（周期定位）

REVERSE_PLAYBOOKS = [
    {
        "id": "japan_property_cycle",
        "name": "日本房地产周期（1980s-2020s）",
        "name_en": "Japan Property Cycle",
        "benchmark": "JPN",
        "category": "房地产",
        "story": "日本1985-1991资产泡沫→1991崩盘→资产负债表衰退30年，全球最经典的房地产周期教科书",
        "phases": [
            {
                "phase_year": 1985,
                "phase_label": "泡沫前期（上涨加速）",
                "gdp_pc": 11330, "gdp_growth": 6.2, "urbanization": 76.7,
                "working_age": 68.4, "inequality": 0.30,
                "price_income": 10.0,  # 房价收入比（历史估算，Numbeo口径）
            },
            {
                "phase_year": 1989,
                "phase_label": "泡沫顶点（全民炒房）",
                "gdp_pc": 24590, "gdp_growth": 5.4, "urbanization": 77.3,
                "working_age": 69.0, "inequality": 0.33,
                "price_income": 18.0,
            },
            {
                "phase_year": 1992,
                "phase_label": "崩盘初期（价格崩塌）",
                "gdp_pc": 31000, "gdp_growth": 0.8, "urbanization": 77.6,
                "working_age": 69.5, "inequality": 0.34,
                "price_income": 15.0,
            },
            {
                "phase_year": 1998,
                "phase_label": "资产负债表衰退（深度调整）",
                "gdp_pc": 31680, "gdp_growth": -1.3, "urbanization": 78.1,
                "working_age": 68.8, "inequality": 0.38,
                "price_income": 10.0,
            },
            {
                "phase_year": 2003,
                "phase_label": "长期停滞（通缩+老龄化）",
                "gdp_pc": 33760, "gdp_growth": 0.5, "urbanization": 78.8,
                "working_age": 66.0, "inequality": 0.38,
                "price_income": 8.0,
            },
        ],
        "targets": ["CHN", "VNM", "IND"],  # 可对比的后发市场
        "note": "中国2021-2025房地产调整被广泛类比日本1991后，用本模块量化『现在处于日本哪一年』",
    },
    {
        "id": "us_subprime_cycle",
        "name": "美国次贷周期（2001-2012）",
        "name_en": "US Subprime Cycle",
        "benchmark": "USA",
        "category": "房地产/金融",
        "story": "美国2001-2007房价泡沫→2008次贷崩盘→2012触底，金融杠杆型周期",
        "phases": [
            {
                "phase_year": 2003,
                "phase_label": "泡沫启动（低利率+杠杆）",
                "gdp_pc": 39680, "gdp_growth": 2.8, "urbanization": 80.3,
                "working_age": 66.8, "inequality": 0.47,
                "price_income": 5.0,
            },
            {
                "phase_year": 2006,
                "phase_label": "泡沫顶点（次级贷泛滥）",
                "gdp_pc": 44760, "gdp_growth": 2.7, "urbanization": 80.7,
                "working_age": 66.6, "inequality": 0.47,
                "price_income": 7.2,
            },
            {
                "phase_year": 2009,
                "phase_label": "崩盘（金融危机）",
                "gdp_pc": 47000, "gdp_growth": -2.6, "urbanization": 81.3,
                "working_age": 66.7, "inequality": 0.48,
                "price_income": 5.5,
            },
            {
                "phase_year": 2012,
                "phase_label": "触底复苏（去杠杆完成）",
                "gdp_pc": 51740, "gdp_growth": 2.3, "urbanization": 81.6,
                "working_age": 66.2, "inequality": 0.47,
                "price_income": 3.5,
            },
        ],
        "targets": ["CHN", "BRA", "TUR", "SAU"],
        "note": "新兴市场信贷扩张期可对比美国2003-2006",
    },
    {
        "id": "hk_property_cycle",
        "name": "香港楼市周期（1997-2020）",
        "name_en": "HK Property Cycle",
        "benchmark": "HKG",
        "category": "房地产",
        "story": "香港1997楼市崩盘（-60%）→2003SARS触底→2010s暴涨→2019回落，高密度城市楼市经典",
        "phases": [
            {
                "phase_year": 1997,
                "phase_label": "泡沫顶点（回归前狂潮）",
                "gdp_pc": 25000, "gdp_growth": 5.1, "urbanization": 100.0,
                "working_age": 71.0, "inequality": 0.43,
                "price_income": 18.0,
            },
            {
                "phase_year": 2003,
                "phase_label": "崩盘触底（SARS+通缩）",
                "gdp_pc": 23500, "gdp_growth": 3.1, "urbanization": 100.0,
                "working_age": 70.5, "inequality": 0.43,
                "price_income": 8.0,
            },
            {
                "phase_year": 2010,
                "phase_label": "复苏暴涨（内地资金涌入）",
                "gdp_pc": 32400, "gdp_growth": 6.8, "urbanization": 100.0,
                "working_age": 70.0, "inequality": 0.44,
                "price_income": 12.0,
            },
            {
                "phase_year": 2019,
                "phase_label": "高位震荡（需求见顶）",
                "gdp_pc": 48300, "gdp_growth": -1.7, "urbanization": 100.0,
                "working_age": 69.0, "inequality": 0.45,
                "price_income": 20.0,
            },
        ],
        "targets": ["CHN", "SGP", "KOR"],
        "note": "高密度城市/中国都市圈楼市可比香港",
    },
    {
        "id": "kr_chaebol_cycle",
        "name": "韩国财阀周期（1997-2015）",
        "name_en": "Korea Chaebol Cycle",
        "benchmark": "KOR",
        "category": "产业/金融",
        "story": "韩国1997亚洲金融危机→财阀改革→2000s电子/娱乐崛起，出口导向型经济转型经典",
        "phases": [
            {
                "phase_year": 1997,
                "phase_label": "危机前（财阀过度扩张）",
                "gdp_pc": 12190, "gdp_growth": 5.8, "urbanization": 78.0,
                "working_age": 71.2, "inequality": 0.34,
            },
            {
                "phase_year": 1998,
                "phase_label": "金融危机（IMF救助）",
                "gdp_pc": 8190, "gdp_growth": -5.1, "urbanization": 78.3,
                "working_age": 71.0, "inequality": 0.35,
            },
            {
                "phase_year": 2005,
                "phase_label": "转型成功（电子/汽车/娱乐）",
                "gdp_pc": 18680, "gdp_growth": 4.3, "urbanization": 80.8,
                "working_age": 71.5, "inequality": 0.34,
            },
            {
                "phase_year": 2015,
                "phase_label": "成熟期（韩流/半导体全球）",
                "gdp_pc": 28640, "gdp_growth": 2.8, "urbanization": 81.5,
                "working_age": 72.3, "inequality": 0.35,
            },
        ],
        "targets": ["CHN", "VNM", "IND"],
        "note": "出口导向型后发市场可对比韩国转型路径",
    },
]


class ReverseTimeMachine:
    """反向时光机引擎"""

    ENGINE_ID = "reverse_time_machine"
    VERSION = "1.0.0"

    def __init__(self, collector: WorldBankCollector | None = None):
        self.collector = collector or WorldBankCollector()
        self._numbeo = self._load_numbeo()

    # ── Numbeo 房价收入比（实时抓取缓存）──────────────

    def _load_numbeo(self) -> dict:
        """加载 Numbeo 房价收入比缓存（93国）"""
        try:
            import os
            import json
            path = os.path.join(
                "/var/www/ai-digital-card/backend/data/time_machine_engine",
                "numbeo_price_income.json")
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                values = data.get("values", {})
                logger.info("Numbeo 房价收入比已加载: %d 国 (%s)",
                            len(values), data.get("fetched_at", "?"))
                return values
        except Exception as e:
            logger.warning("Numbeo 加载失败: %s", e)
        return {}

    def _target_price_income(self, iso3: str) -> float | None:
        """目标国当前房价收入比（Numbeo）"""
        return self._numbeo.get(iso3)

    # ── 匹配目标国当前 ≈ 基准国哪一年 ────────────────────

    def match_target_to_phase(self, target_iso3: str,
                              playbook: dict) -> dict | None:
        """把目标国当前环境与基准周期各阶段比对，找最相似的阶段
        返回: {target, matched_phase, matched_year, similarity, all_phases}
        """
        current_year = datetime.now().year
        years = list(range(current_year - 3, current_year + 1))
        # 目标国当前指标
        target = {}
        for dim in ["gdp_pc", "gdp_growth", "urbanization", "working_age", "inequality"]:
            v = self.collector.get_country_avg(target_iso3, dim, years)
            if v is not None:
                target[dim] = v
        # 房价收入比（房地产类档案加维度，Numbeo 当前值）
        is_property = "房地产" in playbook.get("category", "")
        price_income = self._target_price_income(target_iso3) if is_property else None
        if price_income is not None:
            target["price_income"] = price_income
        if len(target) < 3:
            return None

        # 与各阶段比对（归一化相对距离；房价维度权重翻倍=周期核心指标）
        results = []
        for phase in playbook["phases"]:
            common = [d for d in phase if d in target and d not in ("phase_year", "phase_label")]
            if len(common) < 3:
                continue
            diffs = []
            for d in common:
                base = max(abs(phase[d]), 1.0)
                weight = 2.0 if d == "price_income" else 1.0
                diffs.append(((target[d] - phase[d]) / base) ** 2 * weight)
            dist = (sum(diffs) / sum(1 for d in common if d != "price_income" or is_property)) ** 0.5
            sim = 1.0 / (1.0 + dist * 2.0)
            results.append({
                "phase_year": phase["phase_year"],
                "phase_label": phase["phase_label"],
                "distance": round(dist, 4),
                "similarity": round(sim, 4),
                "matched_dims": len(common),
                "price_income": phase.get("price_income"),
            })

        if not results:
            return None
        results.sort(key=lambda x: x["similarity"], reverse=True)
        best = results[0]
        return {
            "target_iso3": target_iso3,
            "playbook_id": playbook["id"],
            "matched_phase": best,
            "next_phases": [r for r in results[1:3]],
            "all_phases": results,
            "target_snapshot": target,
        }

    # ── 完整运行 ──────────────────────────────────────────

    def run(self) -> dict:
        results = []
        for pb in REVERSE_PLAYBOOKS:
            for target in pb["targets"]:
                r = self.match_target_to_phase(target, pb)
                if r:
                    r["playbook_name"] = pb["name"]
                    r["playbook_note"] = pb.get("note", "")
                    results.append(r)
        return {
            "mode": "reverse_time_machine",
            "run_at": datetime.now().isoformat(),
            "playbooks": len(REVERSE_PLAYBOOKS),
            "matches": results,
        }

    # ── 报告 ──────────────────────────────────────────────

    def to_report(self, data: dict) -> str:
        lines = [
            "# 🔄 反向时光机 · 海外已验证周期 → 中国国内预判",
            "",
            "> 用发达经济体已经走完的周期，预判中国/后发市场正在经历的阶段。",
            "> 核心应用：房地产周期定位（日本泡沫/美国次贷/香港楼市）、产业转型（韩国财阀）。",
            "",
        ]
        # 按目标国分组
        by_target = {}
        for r in data["matches"]:
            by_target.setdefault(r["target_iso3"], []).append(r)
        for target, items in by_target.items():
            lines.append(f"## 🎯 {target}")
            lines.append("")
            for r in items:
                best = r["matched_phase"]
                price_line = ""
                target_pi = r.get("target_snapshot", {}).get("price_income")
                if best.get("price_income") is not None:
                    price_line = (f"  → 房价收入比: 目标国当前 **{target_pi}** "
                                  f"vs 基准国{best['phase_year']}年 **{best['price_income']}** "
                                  f"(Numbeo实时, 房产周期核心指标)\n")
                lines.append(f"- **{r['playbook_name']}**")
                lines.append(f"  → 当前环境 ≈ 基准国 **{best['phase_year']}年**（{best['phase_label']}），"
                             f"相似度 {best['similarity']:.0%}")
                if price_line:
                    lines.append(price_line.rstrip("\n"))
                nexts = "、".join(
                    f"{p['phase_year']}年({p['phase_label']})" for p in r["next_phases"])
                lines.append(f"  → 后续阶段参考: {nexts}")
                lines.append(f"  → 参考意义: {r['playbook_note']}")
                lines.append("")
        return "\n".join(lines)
