"""
出海时光机引擎 v3 — 时滞预测模块（Time-Lag Forecast）
======================================================
投资引擎核心功能：预测「目标国还要几年，环境参数才会到达中国当年水平」。

原理：
  中国在模式黄金期的环境 = 目标值。
  目标国各维度按历史趋势（近N年线性回归/年均增速）外推，
  预测未来第几年该维度达到中国的目标值 → 取各关键维度的到达年份中位数
  = "该模式在这个国家的黄金窗口何时到来"。

用途：
  1. 当前相似度高 → 现在就该进场（蜜雪冰城式）
  2. 当前相似度低但趋势快 → 提前 2-3 年布局，卡位
  3. 当前相似度高但趋势倒退 → 谨慎（窗口在关闭）

依赖: collector（世界银行缓存数据）
"""

import math
import logging
from datetime import datetime

from .dimensions import ENV_DIMENSIONS
from .matcher import EnvironmentMatcher

logger = logging.getLogger("time_machine_v3_forecast")

CHINA_ISO3 = "CHN"
MAX_FORECAST_YEARS = 15  # 最多预测15年


def _linear_trend(series: dict[int, float], min_points: int = 4) -> dict | None:
    """对年度序列做线性回归，返回 {slope, intercept, last_year, last_value}"""
    pts = [(y, v) for y, v in sorted(series.items()) if v is not None]
    if len(pts) < min_points:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    slope = num / den
    intercept = my - slope * mx
    return {
        "slope": slope,
        "intercept": intercept,
        "last_year": xs[-1],
        "last_value": ys[-1],
    }


class TimeLagForecaster:
    """时滞预测器"""

    def __init__(self, collector):
        self.collector = collector
        self.matcher = EnvironmentMatcher()

    def _china_ref(self, playbook_item: dict) -> dict[str, float]:
        """中国模式黄金期快照 {dim: value}"""
        years = list(range(playbook_item["golden_years"][0],
                           playbook_item["golden_years"][1] + 1))
        ref = {}
        for dim_key in ENV_DIMENSIONS:
            v = self.collector.get_country_avg(CHINA_ISO3, dim_key, years)
            if v is not None:
                ref[dim_key] = v
        return ref

    def country_reach_year(self, iso3: str, dim_key: str,
                           target_value: float,
                           trend_years: int = 10) -> dict:
        """预测某国某维度到达目标值的时间
        返回: {reach_year, years_from_now, trend, direction}
        """
        current_year = datetime.now().year
        series = self.collector.get_country_series(
            iso3, dim_key,
            years=list(range(current_year - trend_years, current_year + 1)))
        trend = _linear_trend(series)
        if not trend or trend["slope"] == 0:
            return {"reach_year": None, "years_from_now": None, "trend": trend}

        # 当前值
        current = trend["last_value"] or 0
        slope = trend["slope"]

        # 目标方向：target 在 current 之上 → 需要增长；反之需要下降
        if target_value >= current:
            if slope <= 0:
                return {"reach_year": None, "years_from_now": None,
                        "trend": trend, "note": "趋势未上升，窗口不在打开"}
            years_needed = (target_value - current) / slope
        else:
            if slope >= 0:
                return {"reach_year": None, "years_from_now": None,
                        "trend": trend, "note": "已超过目标"}
            years_needed = (current - target_value) / abs(slope)

        years_needed = max(0, years_needed)
        if years_needed > MAX_FORECAST_YEARS:
            return {"reach_year": None, "years_from_now": None,
                    "trend": trend, "note": f"超过{MAX_FORECAST_YEARS}年窗口"}

        reach_year = current_year + years_needed
        return {
            "reach_year": round(reach_year, 1),
            "years_from_now": round(years_needed, 1),
            "trend": {
                "slope": round(slope, 4),
                "last_value": round(current, 4),
                "last_year": trend["last_year"],
            },
            "target_value": round(target_value, 4),
        }

    def forecast_playbook(self, playbook_item: dict,
                          countries: dict[str, dict],
                          top_n: int = 10) -> list[dict]:
        """对一个模式预测各国到达时间
        对每个国家的关键维度（该模式权重≥1.0）做时滞预测，
        取"到达年份的中位数"作为该国整体窗口年份。
        """
        ref = self._china_ref(playbook_item)
        if not ref:
            return []

        weights = playbook_item.get("dim_weights") or {}
        key_dims = [k for k, w in weights.items() if w >= 1.0 and k in ref]

        results = []
        for iso3, cand in countries.items():
            if iso3 == CHINA_ISO3:
                continue
            reach_years = []
            dim_details = []
            for dim_key in key_dims:
                if dim_key not in cand:
                    continue
                r = self.country_reach_year(iso3, dim_key, ref[dim_key])
                if r.get("reach_year"):
                    reach_years.append(r["reach_year"])
                    dim_details.append({
                        "dim": dim_key,
                        "dim_name": ENV_DIMENSIONS.get(dim_key, {}).get("name", dim_key),
                        "reach_year": r["reach_year"],
                        "years_from_now": r["years_from_now"],
                        "current": r.get("trend", {}).get("last_value"),
                        "target": r.get("target_value"),
                    })
            if not reach_years:
                continue
            reach_years.sort()
            median_year = reach_years[len(reach_years) // 2]
            # 当前相似度（用最近数据）
            sim = self.matcher.similarity(ref, cand)
            results.append({
                "iso3": iso3,
                "median_reach_year": round(median_year, 1),
                "years_from_now": round(median_year - datetime.now().year, 1),
                "current_score": sim["score"],
                "key_dims_analyzed": len(dim_details),
                "dim_details": sorted(dim_details, key=lambda x: x["years_from_now"])[:5],
            })

        # 排序：优先当前已相似 + 未来窗口近的（黄金窗口）
        results.sort(key=lambda x: (x["years_from_now"] < 3, -x["current_score"], x["years_from_now"]))
        return results[:top_n]
