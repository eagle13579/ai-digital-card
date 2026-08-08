"""
出海时光机引擎 v3 — 投资决策视图模块（Investment Decision View）
=================================================================
把匹配结果转化为可直接指导投资的决策建议：

  1. 综合每模式 Top 国家的「当前相似度」+「时滞预测窗口」→ 分类:
     - 🔥 现在进场   (当前相似度高 + 窗口已到或 1-2 年内)
     - ⏳ 提前卡位   (当前相似度中 + 窗口 2-5 年 → 布局观察)
     - 👀 观察等待   (当前相似度低 + 窗口 5+ 年 或 趋势不明)
  2. 输出投资机会清单（含建议动作/布局时间/关注指标）

用法:
  from time_machine_engine.investment_view import InvestmentDecisionView
  view = InvestmentDecisionView()
  decisions = view.build(engine_results)
"""

import logging
from datetime import datetime

from .dimensions import COUNTRY_CN

logger = logging.getLogger("time_machine_v3_investment")


class InvestmentDecisionView:
    """投资决策视图"""

    VERSION = "1.0.0"

    def __init__(self):
        pass

    def classify(self, score: float, years_from_now: float | None) -> str:
        """单条机会分类"""
        if years_from_now is None:
            if score >= 0.30:
                return "now"
            if score >= 0.22:
                return "early"
            return "watch"
        if score >= 0.30 and years_from_now <= 2.5:
            return "now"
        if score >= 0.22 and years_from_now <= 6.0:
            return "early"
        return "watch"

    def build(self, engine_results: dict) -> dict:
        """从引擎结果构建投资决策清单"""
        decisions = []
        for r in engine_results.get("results", []):
            playbook_id = r["playbook_id"]
            name = r["name"]
            category = r["category"]
            golden = r["golden_years"]
            forecasts = {f["iso3"]: f for f in r.get("forecasts", [])}

            for c in r.get("top_countries", [])[:5]:
                iso3 = c["iso3"]
                score = c["score"]
                fc = forecasts.get(iso3, {})
                years = fc.get("years_from_now")
                decision = self.classify(score, years)
                decisions.append({
                    "playbook_id": playbook_id,
                    "mode_name": name,
                    "category": category,
                    "golden_years": golden,
                    "iso3": iso3,
                    "country": COUNTRY_CN.get(iso3, iso3),
                    "similarity": score,
                    "window_years": years,
                    "decision": decision,
                    "action": self._action(decision, name, iso3, years),
                })

        summary = {"now": 0, "early": 0, "watch": 0}
        for d in decisions:
            summary[d["decision"]] = summary.get(d["decision"], 0) + 1

        return {
            "mode": "investment_decision_view",
            "built_at": datetime.now().isoformat(),
            "total_opportunities": len(decisions),
            "summary": summary,
            "decisions": decisions,
        }

    def _action(self, decision: str, mode_name: str, iso3: str,
                years: float | None) -> str:
        cn = COUNTRY_CN.get(iso3, iso3)
        if decision == "now":
            win = "已到" if years is None or years < 1 else "%.0f年后" % years
            return "建议进场：%s模式在%s环境已匹配（窗口%s），可启动市场调研/试点/本地化部署" % (mode_name, cn, win)
        if decision == "early":
            yr_t = "%.0f年后" % years if years else "窗口临近"
            return "提前卡位：%s模式在%s%s到窗口期，建议关注政策/基础设施指标，建立观察清单" % (mode_name, cn, yr_t)
        yr_txt = "约%.0f年" % years if years else "趋势不明"
        return "观察等待：%s模式在%s窗口未到（%s），列入长期跟踪" % (mode_name, cn, yr_txt)

    def to_report(self, data: dict) -> str:
        lines = [
            "# 💰 出海投资决策清单（Investment Decision View）",
            "",
            "- 总机会: %d 条" % data["total_opportunities"],
            "- 🔥 现在进场: %d 条" % data["summary"].get("now", 0),
            "- ⏳ 提前卡位: %d 条" % data["summary"].get("early", 0),
            "- 👀 观察等待: %d 条" % data["summary"].get("watch", 0),
            "",
            "## 🔥 现在进场（环境已匹配 + 窗口已到/临近）",
            "",
            "| 模式 | 国家 | 相似度 | 窗口 | 建议 |",
            "|:-----|:-----|:------:|:----:|:-----|",
        ]
        for d in data["decisions"]:
            if d["decision"] != "now":
                continue
            win = "已到" if d["window_years"] is None or d["window_years"] < 1 else "%.0f年" % d["window_years"]
            lines.append("| %s | **%s** | %.0f%% | %s | %s |" % (
                d["mode_name"], d["country"], d["similarity"] * 100, win, d["action"][:40]))
        lines.append("")
        lines.append("## ⏳ 提前卡位（2-5年后窗口）")
        lines.append("")
        lines.append("| 模式 | 国家 | 相似度 | 窗口 | 建议 |")
        lines.append("|:-----|:-----|:------:|:----:|:-----|")
        for d in data["decisions"]:
            if d["decision"] != "early":
                continue
            lines.append("| %s | **%s** | %.0f%% | %.0f年 | %s |" % (
                d["mode_name"], d["country"], d["similarity"] * 100,
                d["window_years"], d["action"][:40]))
        lines.append("")
        lines.append("## 👀 观察等待（长期跟踪）")
        lines.append("")
        lines.append("| 模式 | 国家 | 相似度 | 窗口 | 建议 |")
        lines.append("|:-----|:-----|:------:|:----:|:-----|")
        for d in data["decisions"]:
            if d["decision"] != "watch":
                continue
            win = "%.0f年" % d["window_years"] if d["window_years"] else "—"
            lines.append("| %s | **%s** | %.0f%% | %s | %s |" % (
                d["mode_name"], d["country"], d["similarity"] * 100, win, d["action"][:40]))
        return "\n".join(lines)
