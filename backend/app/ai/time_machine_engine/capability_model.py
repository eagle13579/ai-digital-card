"""
出海时光机引擎 v3 — 供应链优势型出海模型（第二模型）
=====================================================
覆盖第一模型（环境相似）无法解释的出海类型：
  中国制造/供应链优势 → 输出到"市场空白或购买力强"的国家。
  例: 传音→非洲(市场空白)、石头→欧洲(购买力强)、OPPO→印度(人口+制造)、SHEIN→美国(供应链碾压)

判断逻辑（Capability Export Model）：
  机会 = 中国产业全球竞争力 × 目标国需求缺口 × 目标国承接条件

  三维评分:
  1. 中国产业优势 (china_strength): 制造业占GDP高=产业链强
  2. 目标国需求 (demand): 人口规模(百分位) + 人均GDP(购买力) + 互联网/手机渗透
  3. 目标国承接 (receptivity): FDI开放度 + 贸易开放 + 城镇化

区别于环境相似模型: 不看"目标国像不像中国当年"，而看"中国强不强 + 目标国需不需要"。
"""

import logging
from datetime import datetime

from .collector import WorldBankCollector
from .dimensions import COUNTRY_CN, ENV_DIMENSIONS

logger = logging.getLogger("time_machine_v3_capability")

CHINA_ISO3 = "CHN"
MIN_POPULATION = 5_000_000  # 供应链输出也需要一定市场体量


class CapabilityExportModel:
    """供应链优势型出海模型"""

    ENGINE_ID = "overseas_time_machine_capability"
    VERSION = "1.0.0"

    def __init__(self, collector: WorldBankCollector | None = None):
        self.collector = collector or WorldBankCollector()

    # ── 中国产业优势强度 ──────────────────────────────────

    def _china_strength(self, years: list[int]) -> dict:
        """中国产业优势信号（制造业/投资/电力等）"""
        signals = {
            "manufacturing": self.collector.get_country_avg(CHINA_ISO3, "manufacturing", years),
            "investment": self.collector.get_country_avg(CHINA_ISO3, "investment", years),
            "electricity": self.collector.get_country_avg(CHINA_ISO3, "electricity", years),
        }
        return {k: v for k, v in signals.items() if v is not None}

    # ── 目标国三维评分 ────────────────────────────────────

    def score_country(self, iso3: str, china_strength: dict,
                      years: list[int], profile: str = "balanced") -> dict | None:
        """对目标国做供应链输出机会评分
        profile: 品类逻辑
          'dev_market'  : 发展中大市场（传音/OPPO/比亚迪/隆基）— 人口+增长+数字化空白
          'affluent'    : 高购买力（石头/科沃斯/SHEIN欧美）— 收入+数字化成熟
          'balanced'    : 两者取 max
        返回: {iso3, china_strength_score, demand_score, receptivity_score, total}
        """
        if iso3 == CHINA_ISO3:
            return None

        # 1. 目标国需求 (demand) — 双逻辑：发展中大市场 + 高购买力
        pop = self.collector.get_country_avg(iso3, "population", years)
        if pop is None or pop < MIN_POPULATION:
            return None
        gdp_pc = self.collector.get_country_avg(iso3, "gdp_pc", years)
        internet = self.collector.get_country_avg(iso3, "internet", years)
        mobile = self.collector.get_country_avg(iso3, "mobile", years)
        gdp_growth = self.collector.get_country_avg(iso3, "gdp_growth", years)

        pop_pct = self.collector.percentile_of(iso3, "population", years) or 0
        gdp_pc_v = gdp_pc or 0
        int_v = internet or 0
        mob_v = mobile or 0
        growth_v = gdp_growth or 0

        # A. 发展中大市场逻辑（传音/OPPO/比亚迪/隆基）:
        #    人口大 + 增长快 + 数字化"空白或上升期" = 新品类机会
        #    购买力适中度: 人均GDP 3000-15000 最理想
        if gdp_pc_v < 3000:
            gdp_fit_dev = gdp_pc_v / 3000 * 0.7   # 太穷但有潜力
        elif gdp_pc_v <= 15000:
            gdp_fit_dev = 1.0                     # 甜区
        else:
            gdp_fit_dev = max(0.2, 1.0 - (gdp_pc_v - 15000) / 30000)  # 太富转高购
        # 数字化上升窗口: 渗透 5-60% 是空白到起量阶段（手机/消费品最佳）
        digit_fit_dev = max(0.0, min(1.0, (int_v - 5) / 55))
        growth_fit = min(1.0, growth_v / 8)
        # 空白市场加成: 手机普及率(含功能机) < 85 表示智能机尚未完全普及
        #   （功能机转智能机窗口 = 传音/OPPO 逻辑）
        blank_bonus = 0.0
        if mob_v < 85 and pop_pct > 0.6:
            blank_bonus = 0.25 * (1 - mob_v / 85)  # 越空白加成越高
        # 极端空白市场识别（传音专属逻辑）: 人口巨大 + 手机渗透<50% + 人均GDP<3000
        #   = 大众消费品(手机/家电/快消)的处女地，需求潜力巨大
        extreme_blank = 0.0
        if pop_pct > 0.75 and mob_v < 50 and gdp_pc_v < 3000:
            extreme_blank = 0.3
        # 智能机升级窗口（realme/OPPO/小米印度逻辑）: 人口巨大 + 手机渗透60-95%
        #   + 人均GDP中低 = 功能机→智能机替换潮，比极端空白更现实的大市场
        smart_upgrade = 0.0
        if pop_pct > 0.7 and 60 <= mob_v < 95 and gdp_pc_v < 5000:
            smart_upgrade = 0.18
        # 防溢出: 三个加成不同时叠加，取各自场景的合理加成（上限0.35）
        market_boost = max(blank_bonus, extreme_blank, smart_upgrade)
        demand_dev = (pop_pct * 0.55 + gdp_fit_dev * 0.15
                      + digit_fit_dev * 0.1 + growth_fit * 0.2
                      + min(0.35, market_boost))

        # B. 高购买力逻辑（石头/科沃斯/SHEIN 欧美）:
        #    人均GDP高 + 数字化成熟 + 人口规模
        gdp_fit_aff = min(1.0, gdp_pc_v / 25000)
        digit_fit_aff = min(1.0, int_v / 80)
        demand_aff = pop_pct * 0.3 + gdp_fit_aff * 0.4 + digit_fit_aff * 0.3

        # 按品类逻辑选择
        if profile == "dev_market":
            demand = demand_dev
        elif profile == "affluent":
            demand = demand_aff
        else:
            demand = max(demand_dev, demand_aff)

        # 2. 目标国承接条件 (receptivity)
        fdi = self.collector.get_country_avg(iso3, "fdi", years)
        urbanization = self.collector.get_country_avg(iso3, "urbanization", years)
        manufacturing = self.collector.get_country_avg(iso3, "manufacturing", years)
        fdi_norm = min(1.0, (fdi or 0) / 10)  # FDI占GDP 10%封顶
        urb_norm = (urbanization or 0) / 100
        mfg_norm = (manufacturing or 0) / 40
        receptivity = fdi_norm * 0.3 + urb_norm * 0.3 + mfg_norm * 0.4

        # 3. 中国产业优势 (china_strength): 用制造业/投资/电力的平均强度
        mfg_cn = china_strength.get("manufacturing") or 0
        inv_cn = china_strength.get("investment") or 0
        china_score = min(1.0, (mfg_cn / 40) * 0.5 + (inv_cn / 50) * 0.5)

        # 总分: 中国优势(0.3) + 需求(0.55) + 承接(0.15)
        # dev_market 模式: 需求(人口×空白) 是决定性因素，承接只是辅助
        if profile == "dev_market":
            total = china_score * 0.3 + demand * 0.55 + receptivity * 0.15
        else:
            total = china_score * 0.35 + demand * 0.4 + receptivity * 0.25
        return {
            "iso3": iso3,
            "china_strength_score": round(china_score, 4),
            "demand_score": round(demand, 4),
            "receptivity_score": round(receptivity, 4),
            "total": round(total, 4),
        }

    def rank_world(self, top_n: int = 15) -> list[dict]:
        """全球供应链输出机会排名（用当前年份数据）"""
        current_year = datetime.now().year
        years = list(range(current_year - 3, current_year + 1))
        china_strength = self._china_strength(years)
        results = []
        for iso3 in self.collector.available_countries():
            s = self.score_country(iso3, china_strength, years)
            if s:
                results.append(s)
        results.sort(key=lambda x: x["total"], reverse=True)
        return results[:top_n]

    # ── 回测支持 ──────────────────────────────────────────

    def backtest_case(self, case: dict, top_n: int = 15) -> dict:
        """回测一个供应链型案例"""
        entry_year = case["entry_year"]
        years = list(range(entry_year - 1, entry_year + 2))
        profile = case.get("profile", "balanced")
        china_strength = self._china_strength(years)
        scores = {}
        for iso3 in self.collector.available_countries():
            s = self.score_country(iso3, china_strength, years, profile=profile)
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
            "model": "capability",
            "hits": hits,
            "passed": passed,
            "top3": [
                {"iso3": r["iso3"], "name": COUNTRY_CN.get(r["iso3"], r["iso3"]),
                 "total": r["total"]}
                for r in top_ranked[:3]
            ],
        }
