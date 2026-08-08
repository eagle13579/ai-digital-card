"""
出海时光机引擎 v3 — 风险预警引擎（Risk Warning Engine）
=========================================================
时光机理论的另一半：历史风险也会重演。
  投资机会 = 找到"环境像中国当年的后发市场"去复制成功
  风险预警 = 找到"指标像历史危机爆发前"的国家提前警告

六维风险评分（0-100，越高越危险）:
  1. 房产泡沫  (housing)   房价收入比 > 12 警戒, > 20 高危 (Numbeo)
  2. 债务违约  (debt)      外债占GNI% > 60 警戒, > 100 高危
  3. 通胀失控  (inflation) 通胀 > 15% 警戒, > 40% 高危
  4. 双赤字    (twin_def)  经常账户 < -5% 警戒, < -10% 高危
  5. 主权债务  (sovereign) 政府债务占GDP > 80% 警戒, > 120% 高危
  6. 储蓄缓冲  (buffer)    总储蓄占GDP < 15% 警戒, < 8% 高危 (反向)

风险等级: 🟢低(<25) / 🟡中(25-45) / 🔴高(45-70) / 🟣极危(>70)

用法:
  from time_machine_engine.risk_warning import RiskWarningEngine
  rwe = RiskWarningEngine()
  r = rwe.rank_world()        # 全球风险排名
  c = rwe.assess('CHN')       # 单国风险档案
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from .dimensions import COUNTRY_CN

logger = logging.getLogger("time_machine_v3_risk")

DATA_DIR = Path("/var/www/ai-digital-card/backend/data/time_machine_engine")
RISK_CACHE = DATA_DIR / "risk_cache.json"
NUMBEO_CACHE = DATA_DIR / "numbeo_price_income.json"

# 风险阈值（历史危机经验校准）
THRESHOLDS = {
    "housing":  {"warn": 12.0, "high": 20.0},   # 房价收入比
    "debt":     {"warn": 60.0, "high": 100.0},  # 外债占GNI%
    "inflation": {"warn": 15.0, "high": 40.0},  # 通胀率%
    "twin_def": {"warn": -5.0, "high": -10.0},  # 经常账户占GDP%（负值危险）
    "sovereign": {"warn": 80.0, "high": 120.0}, # 政府债务占GDP%
    "buffer":   {"warn": 15.0, "high": 8.0},    # 总储蓄占GDP%（反向）
}


class RiskWarningEngine:
    """风险预警引擎"""

    ENGINE_ID = "risk_warning_engine"
    VERSION = "1.0.0"

    def __init__(self):
        self._risk = self._load_risk()
        self._numbeo = self._load_numbeo()

    # ── 数据加载 ──────────────────────────────────────────

    def _load_risk(self) -> dict:
        try:
            if RISK_CACHE.exists():
                with open(RISK_CACHE, encoding="utf-8") as f:
                    return json.load(f).get("data", {})
        except Exception as e:
            logger.warning("风险缓存加载失败: %s", e)
        return {}

    def _load_numbeo(self) -> dict:
        try:
            if NUMBEO_CACHE.exists():
                with open(NUMBEO_CACHE, encoding="utf-8") as f:
                    return json.load(f).get("values", {})
        except Exception as e:
            logger.warning("Numbeo 加载失败: %s", e)
        return {}

    def _series_avg(self, metric: str, iso3: str, years: list[int]) -> float | None:
        """风险指标某国均值（近N年）"""
        series = self._risk.get(metric, {}).get(iso3, {})
        vals = [v for y, v in series.items()
                if v is not None and int(y) in years]
        if not vals:
            return None
        return sum(vals) / len(vals)

    # ── 单国评估 ──────────────────────────────────────────

    def assess(self, iso3: str, years: list[int] | None = None) -> dict | None:
        """单国风险档案 {iso3, name, dims, total, level, top_risks}"""
        years = years or list(range(datetime.now().year - 2, datetime.now().year + 1))

        dims = {}

        # 1. 房产泡沫（Numbeo 当前房价收入比）
        pi = self._numbeo.get(iso3)
        if pi is not None:
            dims["housing"] = self._score_housing(pi)
            dims["housing_value"] = pi

        # 2. 债务违约（外债占GNI%）
        debt = self._series_avg("debt_gni", iso3, years)
        if debt is not None:
            dims["debt"] = self._score_debt(debt)
            dims["debt_value"] = round(debt, 1)

        # 3. 通胀失控
        inf = self._series_avg("inflation", iso3, years)
        if inf is not None:
            dims["inflation"] = self._score_inflation(inf)
            dims["inflation_value"] = round(inf, 1)

        # 4. 双赤字
        ca = self._series_avg("current_account", iso3, years)
        if ca is not None:
            dims["twin_def"] = self._score_twin_def(ca)
            dims["twin_def_value"] = round(ca, 1)

        # 5. 主权债务
        gd = self._series_avg("gov_debt", iso3, years)
        if gd is not None:
            dims["sovereign"] = self._score_sovereign(gd)
            dims["sovereign_value"] = round(gd, 1)

        # 6. 储蓄缓冲（反向）
        sv = self._series_avg("savings", iso3, years)
        if sv is not None:
            dims["buffer"] = self._score_buffer(sv)
            dims["buffer_value"] = round(sv, 1)

        if len(dims) < 3:
            return None

        score_dims = {k: v for k, v in dims.items() if isinstance(v, (int, float)) and k.endswith(("housing", "debt", "inflation", "twin_def", "sovereign", "buffer"))}
        total = round(sum(score_dims.values()) / len(score_dims), 1)
        # 单维高危升级: 任一维度 ≥60 分即使总分不高也要升级预警
        # （如中国: 房产68分但其他维健康 → 总分低但必须亮房产红灯）
        max_dim = max(score_dims.values()) if score_dims else 0
        level = self._level(total)
        if max_dim >= 60:
            # 单维 ≥60 = 该维度已进入高危区，预警等级至少 high
            level = "high" if level in ("low", "medium") else level
        if max_dim >= 75:
            level = "extreme" if level in ("low", "medium", "high") else level
        top = sorted(
            [(k, v) for k, v in score_dims.items()],
            key=lambda x: x[1], reverse=True)[:3]
        return {
            "iso3": iso3,
            "name": COUNTRY_CN.get(iso3, iso3),
            "total": total,
            "level": level,
            "max_dim": max_dim,
            "dims": dims,
            "top_risks": [{"dim": k, "score": v} for k, v in top],
        }

    # ── 各维评分（0-100）────────────────────────────────

    def _score_housing(self, pi: float) -> float:
        if pi <= 8:
            return pi / 8 * 20
        if pi <= 12:
            return 20 + (pi - 8) / 4 * 25
        if pi <= 20:
            return 45 + (pi - 12) / 8 * 35
        return min(100, 80 + (pi - 20) * 3)

    def _score_debt(self, v: float) -> float:
        if v <= 30:
            return v / 30 * 20
        if v <= 60:
            return 20 + (v - 30) / 30 * 25
        if v <= 100:
            return 45 + (v - 60) / 40 * 35
        return min(100, 80 + (v - 100) * 0.4)

    def _score_inflation(self, v: float) -> float:
        if v <= 5:
            return v / 5 * 15
        if v <= 15:
            return 15 + (v - 5) / 10 * 30
        if v <= 40:
            return 45 + (v - 15) / 25 * 35
        return min(100, 80 + (v - 40) * 0.5)

    def _score_twin_def(self, v: float) -> float:
        # 经常账户占GDP%：正值=顺差（健康，0分），负值=逆差（危险）
        if v >= 0:
            return 0.0
        v = -v  # 负值危险 → 转正
        if v <= 3:
            return v / 3 * 20
        if v <= 5:
            return 20 + (v - 3) / 2 * 25
        if v <= 10:
            return 45 + (v - 5) / 5 * 35
        return min(100, 80 + (v - 10) * 4)

    def _score_sovereign(self, v: float) -> float:
        if v <= 40:
            return v / 40 * 20
        if v <= 80:
            return 20 + (v - 40) / 40 * 25
        if v <= 120:
            return 45 + (v - 80) / 40 * 35
        return min(100, 80 + (v - 120) * 0.5)

    def _score_buffer(self, v: float) -> float:
        if v >= 30:
            return (30 / v) * 15 if v > 0 else 15
        if v >= 15:
            return 15 + (30 - v) / 15 * 30
        if v >= 8:
            return 45 + (15 - v) / 7 * 35
        return min(100, 80 + (8 - v) * 5)

    # ── 等级与汇总 ───────────────────────────────────────

    def _level(self, total: float) -> str:
        if total >= 70:
            return "extreme"
        if total >= 45:
            return "high"
        if total >= 25:
            return "medium"
        return "low"

    def rank_world(self, top_n: int = 20) -> list[dict]:
        """全球风险排名（按风险分降序）"""
        results = []
        for iso3 in self._all_countries():
            r = self.assess(iso3)
            if r:
                results.append(r)
        results.sort(key=lambda x: x["total"], reverse=True)
        return results[:top_n]

    def _all_countries(self) -> set:
        countries = set()
        for metric, cdata in self._risk.items():
            countries |= set(cdata.keys())
        countries |= set(self._numbeo.keys())
        return countries

    # ── 报告 ─────────────────────────────────────────────

    def to_report(self, ranked: list[dict], top_n: int = 15) -> str:
        lines = [
            "# 🚨 出海时光机 · 全球风险预警（Risk Warning）",
            "",
            f"> 六维评分(0-100): 房产泡沫/外债/通胀/双赤字/主权债务/储蓄缓冲",
            f"> 等级: 🟢低(<25) 🟡中(25-45) 🔴高(45-70) 🟣极危(>70)",
            "",
            "## 🚨 全球高风险国家 Top{}".format(top_n),
            "",
        ]
        for i, r in enumerate(ranked[:top_n], 1):
            icon = {"extreme": "🟣", "high": "🔴", "medium": "🟡", "low": "🟢"}[r["level"]]
            dims_str = ", ".join(
                "{} {}".format(self._dim_cn(d["dim"]), d["score"])
                for d in r["top_risks"])
            lines.append(f"{i}. {icon} **{r['name']}** 风险 {r['total']}")
            lines.append(f"   主要风险: {dims_str}")
            lines.append("")
        return "\n".join(lines)

    def _dim_cn(self, dim: str) -> str:
        return {
            "housing": "🏠房产", "debt": "💸外债", "inflation": "📈通胀",
            "twin_def": "💱双赤字", "sovereign": "🏛️主权债", "buffer": "🛟储蓄",
            "offshore": "🏝️离岸", "audit": "📋审计", "structure": "🏗️架构",
        }.get(dim, dim)

    # ── 离岸架构风险因子（2026-08-08 套利模式库融合）──
    # 源自「黑盒调查局」帕玛拉特离岸函证盲区套利模式：
    # 离岸子公司占比高 + 审计函证集中 + 注册代理人模式 = 财务舞弊红旗

    def offshore_risk(self, target: dict | None = None) -> dict:
        """标的企业离岸架构风险评分（0-100）

        target: {
            "offshore_ratio": 0.35,      # 离岸子公司占比（0-1）
            "structure": "offshore",     # offshore/trust/shell/normal
            "audit": "concentrated",     # concentrated/scattered/unknown
            "agent_model": "registered", # registered(注册代理人)/direct
            "related_party": 0.5,        # 关联交易占比（0-1）
        }
        返回: {score, level, flags, patterns}
        """
        t = target or {}
        score = 0.0
        flags = []

        # 1. 离岸子公司占比（核心）
        ratio = t.get("offshore_ratio", 0)
        if ratio > 0.5:
            score += 40
            flags.append(f"离岸子公司占比 {ratio:.0%}（极高）")
        elif ratio > 0.3:
            score += 25
            flags.append(f"离岸子公司占比 {ratio:.0%}（偏高）")
        elif ratio > 0.15:
            score += 12
            flags.append(f"离岸子公司占比 {ratio:.0%}（需关注）")

        # 2. 离岸架构类型
        structure = t.get("structure", "")
        if structure in ("shell", "trust"):
            score += 20
            flags.append(f"离岸架构类型: {structure}（空壳/信托，信息不透明）")
        elif structure == "offshore":
            score += 10
            flags.append("离岸架构（信息披露弱）")

        # 3. 审计函证集中度
        audit = t.get("audit", "")
        if audit == "concentrated":
            score += 15
            flags.append("审计函证集中（单点造假风险，ISA 505 警示）")
        elif audit == "scattered":
            score += 5

        # 4. 注册代理人模式
        if t.get("agent_model") == "registered":
            score += 10
            flags.append("注册代理人模式（不承担实质核验义务）")

        # 5. 关联交易占比
        rp = t.get("related_party", 0)
        if rp > 0.4:
            score += 15
            flags.append(f"关联交易占比 {rp:.0%}（资金腾挪风险）")
        elif rp > 0.2:
            score += 8
            flags.append(f"关联交易占比 {rp:.0%}（偏高）")

        score = min(100, round(score, 1))
        if score >= 70:
            level = "extreme"
        elif score >= 45:
            level = "high"
        elif score >= 25:
            level = "medium"
        else:
            level = "low"

        return {
            "score": score,
            "level": level,
            "flags": flags,
            "patterns": ["离岸函证盲区套利"] if score >= 25 else [],
            "advice": (
                "🚨 离岸架构风险高：独立第三方核实离岸实体财务，不依赖注册代理人回函"
                if score >= 45 else
                "⚠️ 离岸架构需关注：核查审计函证独立性与离岸子公司实质经营"
                if score >= 25 else
                "✅ 离岸架构风险低"
            ),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rwe = RiskWarningEngine()
    ranked = rwe.rank_world(top_n=25)
    print(rwe.to_report(ranked, top_n=20))
    print("--- 中国风险档案 ---")
    cn = rwe.assess("CHN")
    if cn:
        print(json.dumps(cn, ensure_ascii=False, indent=1))
