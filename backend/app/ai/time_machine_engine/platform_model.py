"""
出海时光机引擎 v3 — 平台型互联网出海模型（第五模型）
=========================================================
覆盖 env/capability/global/homeland 都解释不了的出海类型：
  中国互联网平台/产品 → 输出到"数字化起量窗口"的新兴市场。
  例: 速卖通→俄罗斯/巴西、快手→巴西、欢聚BIGO→中东、蚂蚁→印度、TikTok Shop→东南亚。

判断逻辑（Platform Export Model）：
  机会 = 数字化渗透窗口 × 人口规模 × 增长动能 × 移动渗透

  与 env(环境相似)区别: 不要求"目标国像中国当年"，只要求数字化刚起量（平台可以跨越发展阶段直接进入）
  与 capability(供应链)区别: 输出的是软件/平台/内容，不是实物制造
  与 global(品牌内容)区别: 不要求高购买力，低ARPU×海量用户也可以（快手巴西、速卖通俄罗斯）

  四维评分:
  1. 数字化窗口 (digital_window): 互联网渗透 15-70% 是最佳起量区（太高=红海，太低=基建不足）
  2. 人口规模 (scale): 人口百分位 —— 互联网产品边际成本趋零，用户即资产
  3. 增长动能 (growth): GDP增速 + 互联网渗透增速(用手机渗透近似) —— 增量市场比存量重要
  4. 移动渗透 (mobile): 手机普及率 —— 新兴市场是 mobile-first
"""
import logging
from datetime import datetime

from .collector import WorldBankCollector
from .dimensions import COUNTRY_CN

logger = logging.getLogger("time_machine_v3_platform")

CHINA_ISO3 = "CHN"
MIN_POPULATION = 10_000_000  # 平台型需要足够用户规模


class PlatformExportModel:
    """平台型互联网出海模型"""

    ENGINE_ID = "overseas_time_machine_platform"
    VERSION = "1.0.0"

    def __init__(self, collector: WorldBankCollector | None = None):
        self.collector = collector or WorldBankCollector()

    def score_country(self, iso3: str, years: list[int]) -> dict | None:
        """对目标国做平台型互联网出海机会评分"""
        if iso3 == CHINA_ISO3:
            return None

        pop = self.collector.get_country_avg(iso3, "population", years)
        if pop is None or pop < MIN_POPULATION:
            return None
        internet = self.collector.get_country_avg(iso3, "internet", years)
        if internet is None:
            return None
        mobile = self.collector.get_country_avg(iso3, "mobile", years)
        gdp_growth = self.collector.get_country_avg(iso3, "gdp_growth", years)
        gdp_pc = self.collector.get_country_avg(iso3, "gdp_pc", years)

        # 1. 数字化窗口: 互联网渗透 15-70% 最佳（15以下基建不足，70以上红海）
        int_v = internet or 0
        if int_v < 8:
            return None  # 基建太差，平台无法落地
        if int_v <= 45:
            digital_window = 0.4 + (int_v - 8) / 45 * 0.6   # 8→0.4, 45→1.0
        elif int_v <= 70:
            digital_window = 1.0 - (int_v - 45) / 25 * 0.3   # 45→1.0, 70→0.7
        else:
            digital_window = max(0.4, 0.7 - (int_v - 70) / 30 * 0.3)  # 70→0.7, 100→0.4

        # 2. 人口规模
        pop_pct = self.collector.percentile_of(iso3, "population", years) or 0

        # 3. 增长动能: GDP增速(0-8%线性) + 手机渗透爬升(60-120线性)
        growth_v = (gdp_growth or 0)
        growth_score = min(1.0, max(0.0, growth_v / 8))
        mob_v = mobile or 0
        mobile_score = min(1.0, max(0.0, (mob_v - 20) / 80))
        growth = growth_score * 0.6 + mobile_score * 0.4

        # 4. 购买力轻微加成（不是主因子，但完全赤贫国平台变现难）
        gdp_v = gdp_pc or 0
        aff_min = min(1.0, gdp_v / 8000) if gdp_v > 0 else 0.3

        total = digital_window * 0.35 + pop_pct * 0.3 + growth * 0.25 + aff_min * 0.1
        return {
            "iso3": iso3,
            "digital_window": round(digital_window, 4),
            "scale": round(pop_pct, 4),
            "growth": round(growth, 4),
            "affluence": round(aff_min, 4),
            "total": round(total, 4),
        }

    def rank_world(self, top_n: int = 15) -> list[dict]:
        current_year = datetime.now().year
        years = list(range(current_year - 3, current_year + 1))
        results = []
        for iso3 in self.collector.available_countries():
            s = self.score_country(iso3, years)
            if s:
                results.append(s)
        results.sort(key=lambda x: x["total"], reverse=True)
        return results[:top_n]

    def backtest_case(self, case: dict, top_n: int = 15) -> dict:
        entry_year = case["entry_year"]
        years = list(range(entry_year - 1, entry_year + 2))
        scores = {}
        for iso3 in self.collector.available_countries():
            s = self.score_country(iso3, years)
            if s:
                scores[s["iso3"]] = s
        ranked = sorted(scores.values(), key=lambda x: x["total"], reverse=True)
        top_ranked = ranked[:top_n]
        ranks = {r["iso3"]: i + 1 for i, r in enumerate(top_ranked)}

        hits = []
        for iso3 in case["entry_countries"]:
            hits.append({
                "iso3": iso3,
                "name": COUNTRY_CN.get(iso3, iso3),
                "rank": ranks.get(iso3),
                "total": scores.get(iso3, {}).get("total"),
                "in_top": iso3 in ranks,
            })
        passed = any(h["in_top"] for h in hits)
        return {
            "case": case,
            "model": "platform",
            "hits": hits,
            "passed": passed,
            "top3": [
                {"iso3": r["iso3"], "name": COUNTRY_CN.get(r["iso3"], r["iso3"]),
                 "total": r["total"]}
                for r in top_ranked[:3]
            ],
        }
