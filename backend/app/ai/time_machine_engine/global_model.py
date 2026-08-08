"""
出海时光机引擎 v3 — 全球化品牌/内容出海模型（第三模型）
=========================================================
覆盖第一模型（环境相似·发展中市场）和第二模型（供应链·空白市场）无法解释的出海类型：
  中国品牌/内容 → 输出到"成熟发达市场"（发达国家/高收入经济体）。
  例: 海底捞→美国、原神→日本、瑞幸→美国、比亚迪→以色列/澳洲。

判断逻辑（Global Export Model）：
  机会 = 目标国购买力 × 数字化成熟度 × 市场规模 × 开放度

  三维评分:
  1. 购买力 (affluence): 人均GDP 高 = 客单价/ARPU 空间
  2. 数字化成熟 (digital): 互联网/手机渗透 = 内容与线上消费渠道
  3. 市场规模 (scale): 人口 + 中产占比（高收入人口基数）

区别于环境相似模型: 不看"目标国像不像中国当年"（那会排斥发达国家），
而看"目标国是否足够有钱+数字化+大体量，足以承接中国品牌/内容全球化输出"。
"""
import logging
from datetime import datetime

from .collector import WorldBankCollector
from .dimensions import COUNTRY_CN

logger = logging.getLogger("time_machine_v3_global")

CHINA_ISO3 = "CHN"
MIN_POPULATION = 3_000_000  # 高购买力小国（新加坡/挪威）也参与


class GlobalExportModel:
    """全球化品牌/内容出海模型"""

    ENGINE_ID = "overseas_time_machine_global"
    VERSION = "1.0.0"

    def __init__(self, collector: WorldBankCollector | None = None):
        self.collector = collector or WorldBankCollector()

    def score_country(self, iso3: str, years: list[int]) -> dict | None:
        """对目标国做全球化输出机会评分"""
        if iso3 == CHINA_ISO3:
            return None

        pop = self.collector.get_country_avg(iso3, "population", years)
        if pop is None or pop < MIN_POPULATION:
            return None
        gdp_pc = self.collector.get_country_avg(iso3, "gdp_pc", years)
        if gdp_pc is None or gdp_pc < 8_000:
            # 全球化输出需要目标国有足够购买力（人均GDP 8000 以下走环境/供应链模型）
            return None
        internet = self.collector.get_country_avg(iso3, "internet", years)
        mobile = self.collector.get_country_avg(iso3, "mobile", years)
        urbanization = self.collector.get_country_avg(iso3, "urbanization", years)

        # 1. 购买力：人均GDP 对数压缩（1万=0.4, 2.5万=0.7, 5万=0.9, 8万=1.0）
        gdp_v = gdp_pc or 0
        affluence = min(1.0, (gdp_v - 8000) / 80_000) * 1.2
        affluence = min(1.0, affluence)

        # 2. 数字化成熟：互联网渗透 + 手机渗透
        int_v = internet or 0
        mob_v = mobile or 0
        digital = min(1.0, (int_v / 90) * 0.6 + (mob_v / 120) * 0.4)

        # 3. 市场规模：人口百分位 × 0.6 + 高收入人口基数(人口×购买力) × 0.4
        pop_pct = self.collector.percentile_of(iso3, "population", years) or 0
        aff_pop = min(1.0, (pop or 0) / 200_000_000)          # 2亿人口封顶
        aff_gdp = min(1.0, gdp_v / 40_000)                     # 4万美元封顶
        affluent_base = aff_pop * aff_gdp                       # 高收入人口基数
        scale = pop_pct * 0.6 + affluent_base * 0.4

        # 4. 开放度：城镇化 + FDI
        urb_v = urbanization or 0
        fdi = self.collector.get_country_avg(iso3, "fdi", years) or 0
        openness = min(1.0, (urb_v / 90) * 0.7 + min(1.0, fdi / 10) * 0.3)

        total = affluence * 0.35 + digital * 0.25 + scale * 0.25 + openness * 0.15
        return {
            "iso3": iso3,
            "affluence": round(affluence, 4),
            "digital": round(digital, 4),
            "scale": round(scale, 4),
            "openness": round(openness, 4),
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
            "model": "global",
            "hits": hits,
            "passed": passed,
            "top3": [
                {"iso3": r["iso3"], "name": COUNTRY_CN.get(r["iso3"], r["iso3"]),
                 "total": r["total"]}
                for r in top_ranked[:3]
            ],
        }
