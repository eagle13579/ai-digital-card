"""
出海时光机引擎 v3 — 环境参数迁移匹配引擎
=========================================
核心逻辑（Time Machine Theory 实战化）：

  中国历史成功模式(含当年环境快照)  ↔比对↔  全球各国当前环境参数
  → 发现"环境相似度"高的国家 → 推荐该模式迁移

数据源：世界银行开放 API（合法合规）
模式档案：CHINA_PLAYBOOK（10个中国已验证成功模式）

用法：
  from time_machine_engine import TimeMachineV3Engine
  engine = TimeMachineV3Engine()
  results = engine.run(top_n=15, refresh_cache=False)
"""

import json
import logging
import time
from datetime import datetime, timezone

from .collector import WorldBankCollector
from .dimensions import COUNTRY_CN, ENV_DIMENSIONS
from .matcher import EnvironmentMatcher
from .playbook import CHINA_PLAYBOOK

logger = logging.getLogger("time_machine_v3")

# 中国 ISO3
CHINA_ISO3 = "CHN"

# 当前环境年份窗口（目标国"现在" = 最近 N 年均值）
CURRENT_YEAR_WINDOW = 3
# 国家最小覆盖维度数
MIN_COUNTRY_DIMS = 6
# 报告输出目录
BACKEND_DIR = "/var/www/ai-digital-card/backend"
REPORT_DIR = f"{BACKEND_DIR}/data/time_machine_reports"


class TimeMachineV3Engine:
    """出海时光机 v3 — 环境迁移匹配引擎"""

    ENGINE_ID = "overseas_time_machine_v3"
    VERSION = "3.0.0"

    def __init__(self, collector: WorldBankCollector | None = None):
        self.collector = collector or WorldBankCollector()
        self.matcher = EnvironmentMatcher()
        self._load_playbook()

    def _load_playbook(self):
        self.playbook = CHINA_PLAYBOOK
        logger.info("模式档案加载: %d 个中国成功模式", len(self.playbook))

    # ── 数据准备 ──────────────────────────────────────────

    def _china_golden_snapshot(self, playbook_item: dict) -> dict | None:
        """拉取中国在模式黄金期的环境快照 {dim: 均值}"""
        years = list(range(playbook_item["golden_years"][0],
                           playbook_item["golden_years"][1] + 1))
        avgs = {}
        for dim_key in ENV_DIMENSIONS:
            val = self.collector.get_country_avg(CHINA_ISO3, dim_key, years)
            if val is not None:
                avgs[dim_key] = val
        if len(avgs) < 3:
            logger.warning("中国黄金期快照维度不足: %s", playbook_item["id"])
            return None
        return avgs

    def _world_current_snapshot(self) -> dict[str, dict]:
        """全球各国当前环境 {iso3: {dim: 均值}}
        含人口硬门槛：排除 <300 万人口的微型国家（避税港/岛国噪声）
        """
        current_year = datetime.now().year
        years = list(range(current_year - CURRENT_YEAR_WINDOW + 1, current_year + 1))
        result = {}
        for iso3 in self.collector.available_countries(MIN_COUNTRY_DIMS):
            pop = self.collector.get_country_avg(iso3, "population", years)
            if pop is None or pop < 3_000_000:
                continue
            avgs = {}
            for dim_key in ENV_DIMENSIONS:
                val = self.collector.get_country_avg(iso3, dim_key, years)
                if val is not None:
                    avgs[dim_key] = val
            if len(avgs) >= MIN_COUNTRY_DIMS:
                result[iso3] = avgs
        return result

    # ── 匹配 ──────────────────────────────────────────────

    def match_playbook(self, playbook_item: dict,
                       world: dict[str, dict], top_n: int = 10) -> list[dict]:
        """单个模式 × 全球匹配"""
        ref = self._china_golden_snapshot(playbook_item)
        if not ref:
            return []
        # 使用模式自定义权重
        weights = playbook_item.get("dim_weights")
        matcher = EnvironmentMatcher(weights) if weights else self.matcher
        # 排除中国自身（找的是"其他国家"的环境相似度）
        world = {iso3: v for iso3, v in world.items() if iso3 != CHINA_ISO3}
        ranked = matcher.rank_countries(ref, world, top_n=top_n)
        return ranked

    def run(self, top_n: int = 10, refresh_cache: bool = False,
            with_forecast: bool = True, sync_lingshu: bool = True) -> dict:
        """执行一轮完整匹配
        返回: {mode, matched_at, results: [{playbook_id, name, top_countries, forecasts}],
               backtest: 历史验证结果, lingshu_synced: int}
        """
        start = time.time()
        # 1. 确保数据缓存
        self.collector.refresh_cache(force=refresh_cache)
        cache_info = self.collector.cache_summary()

        # 2. 全球当前环境快照
        logger.info("构建全球当前环境快照...")
        world = self._world_current_snapshot()
        logger.info("覆盖国家: %d 个", len(world))

        # 3. 逐个模式匹配 + 时滞预测
        results = []
        forecaster = None
        if with_forecast:
            from .forecast import TimeLagForecaster
            forecaster = TimeLagForecaster(self.collector)

        for item in self.playbook:
            ranked = self.match_playbook(item, world, top_n=top_n)
            entry = {
                "playbook_id": item["id"],
                "name": item["name"],
                "name_en": item["name_en"],
                "category": item["category"],
                "golden_years": item["golden_years"],
                "story": item["story"],
                "migration_notes": item.get("migration_notes", ""),
                "top_countries": ranked,
            }
            if forecaster:
                try:
                    fc = forecaster.forecast_playbook(item, world, top_n=5)
                    entry["forecasts"] = fc
                except Exception as e:
                    logger.warning("时滞预测失败 %s: %s", item["id"], e)
                    entry["forecasts"] = []
            results.append(entry)
            time.sleep(0.1)

        # 4. 历史验证（快，秒级）
        backtest_data = None
        try:
            from .backtest import BacktestEngine
            bt = BacktestEngine(self.collector)
            backtest_data = bt.run(top_n=15)
            logger.info("历史验证: %d/%d 案例通过 (%.0f%%)",
                        backtest_data["passed_cases"], backtest_data["total_cases"],
                        backtest_data["pass_rate"] * 100)
        except Exception as e:
            logger.warning("历史验证失败: %s", e)

        # 5. 高分机会 → 灵枢情报中枢
        synced = 0
        if sync_lingshu:
            try:
                synced = self._sync_lingshu(results)
            except Exception as e:
                logger.warning("灵枢同步失败: %s", e)

        # 6. 反向时光机（海外已验证周期 → 中国国内预判）
        reverse_data = None
        try:
            from .reverse_time_machine import ReverseTimeMachine
            rtm = ReverseTimeMachine(self.collector)
            reverse_data = rtm.run()
            logger.info("反向时光机: %d 条周期匹配", len(reverse_data["matches"]))
        except Exception as e:
            logger.warning("反向时光机失败: %s", e)

        # 7. 投资决策视图
        invest_data = None
        try:
            from .investment_view import InvestmentDecisionView
            iv = InvestmentDecisionView()
            invest_data = iv.build({
                "results": results,
            })
            logger.info("投资决策: %d 条机会 (🔥%d/⏳%d/👀%d)",
                        invest_data["total_opportunities"],
                        invest_data["summary"].get("now", 0),
                        invest_data["summary"].get("early", 0),
                        invest_data["summary"].get("watch", 0))
        except Exception as e:
            logger.warning("投资决策视图失败: %s", e)

        # 8. 爬虫增强（电商渗透等实时补充）
        enhance_data = None
        try:
            from .crawler_enhance import CrawlerEnhance
            top_iso3s = list({c["iso3"] for r in results[:6]
                              for c in r.get("top_countries", [])[:3]})[:12]
            ce = CrawlerEnhance()
            enhance_data = ce.enhance(top_iso3s)
        except Exception as e:
            logger.warning("爬虫增强失败: %s", e)

        duration = round(time.time() - start, 2)
        return {
            "mode": "env_migration_match",
            "engine_version": self.VERSION,
            "matched_at": datetime.now(timezone.utc).isoformat(),
            "cache": cache_info,
            "countries_covered": len(world),
            "playbooks": len(self.playbook),
            "results": results,
            "backtest": backtest_data,
            "reverse_time_machine": reverse_data,
            "investment_view": invest_data,
            "crawler_enhance": enhance_data,
            "lingshu_synced": synced,
            "duration_s": duration,
        }

    # ── 灵枢情报中枢联动 ──────────────────────────────────

    def _sync_lingshu(self, results: list[dict]) -> int:
        """把每个模式 Top1 的迁移机会同步到灵枢情报中枢"""
        import hashlib
        import json
        import urllib.request

        LINGSHU_API = "http://127.0.0.1:8555"
        synced = 0
        for r in results:
            if not r.get("top_countries"):
                continue
            top = r["top_countries"][0]
            iso3 = top["iso3"]
            cn = COUNTRY_CN.get(iso3, iso3)
            title = f"[时光机] {r['name']} → {cn}"
            summary = (
                f"中国黄金期{r['golden_years'][0]}-{r['golden_years'][1]}的"
                f"{r['name']}模式，在{cn}环境相似度{top['score']:.0%}。"
                f"{r.get('story', '')[:120]} 迁移要点: {r.get('migration_notes', '')[:100]}"
            )
            payload = json.dumps({
                "title": title[:200],
                "summary": summary[:500],
                "domain": "market",
                "source": f"time_machine_v3:{r['playbook_id']}",
                "region": "global",
                "tags": ["出海", "时光机v3", r["category"], iso3],
                "url": "",
                "score": {"similarity": top["score"], "distance": top["distance"]},
                "confidence": round(top["score"], 2),
            }).encode("utf-8")
            try:
                req = urllib.request.Request(
                    f"{LINGSHU_API}/api/v1/intel/signals",
                    data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    d = json.loads(resp.read().decode())
                if d.get("ok"):
                    synced += 1
            except Exception as e:
                logger.debug("灵枢同步失败 %s: %s", title[:30], e)
        logger.info("灵枢同步 %d 条机会", synced)
        return synced

    # ── 报告生成 ──────────────────────────────────────────

    def to_report(self, data: dict) -> str:
        """生成 Markdown 报告"""
        lines = [
            f"# 🧭 出海时光机 · 全球环境迁移机会报告",
            f"",
            f"- 引擎: v3.0 环境参数迁移匹配（Time Machine Theory）",
            f"- 时间: {data['matched_at']}",
            f"- 数据源: 世界银行开放 API（{data['cache']['fetched_at'] and datetime.fromtimestamp(data['cache']['fetched_at']).strftime('%Y-%m-%d %H:%M') or 'N/A'}）",
            f"- 覆盖: {data['countries_covered']} 国 × {data['cache']['dimensions']} 维度 × {data['playbooks']} 个中国成功模式",
            f"- 耗时: {data['duration_s']}s",
            f"",
            f"## 核心逻辑",
            f"",
            f"> 把中国历史上已验证成功的商业模式，迁移到「当前环境参数与中国当年高度相似」的国家。",
            f"> 相似度 = 中国模式黄金期环境快照 ↔ 目标国最近{CURRENT_YEAR_WINDOW}年均值（加权欧氏距离反映射）。",
            f"",
        ]
        for r in data["results"]:
            lines.append(f"## 🎯 {r['name']}（{r['name_en']}）")
            lines.append(f"")
            lines.append(f"- 中国黄金期: {r['golden_years'][0]}-{r['golden_years'][1]} | 类别: {r['category']}")
            lines.append(f"- 故事: {r['story']}")
            lines.append(f"- 迁移要点: {r.get('migration_notes', '—')}")
            lines.append(f"- Top 迁移目标:")
            lines.append(f"")
            lines.append(f"  | # | 国家 | 相似度 | 匹配维度 | 核心优势维度 |")
            lines.append(f"  |:-:|:-----|:------:|:-------:|:-------------|")
            for i, c in enumerate(r["top_countries"], 1):
                cn = COUNTRY_CN.get(c["iso3"], c["iso3"])
                best_dims = sorted(c.get("dim_scores", {}).items(),
                                   key=lambda x: x[1], reverse=True)[:3]
                best_str = ", ".join(
                    f"{ENV_DIMENSIONS.get(k, {}).get('name', k)}({v:.2f})"
                    for k, v in best_dims if v >= 0.6
                ) or "—"
                lines.append(
                    f"  | {i} | **{cn}** ({c['iso3']}) | {c['score']:.0%} | {c['matched_dims']} | {best_str} |"
                )
            # 时滞预测
            fcs = r.get("forecasts") or []
            if fcs:
                lines.append(f"")
                lines.append(f"  ⏳ 时滞预测（该国环境几年后到达中国当年水平 → 黄金窗口）:")
                lines.append(f"")
                for fc in fcs[:3]:
                    fcn = COUNTRY_CN.get(fc["iso3"], fc["iso3"])
                    if fc.get("years_from_now") is not None:
                        lines.append(
                            f"  - **{fcn}**: 约 **{fc['years_from_now']} 年后**达到中国当年环境"
                            f"（当前相似度{fc['current_score']:.0%}）")
                    else:
                        lines.append(f"  - {fcn}: 窗口未打开或已过（当前相似度{fc['current_score']:.0%}）")
            lines.append("")

        # 历史验证
        bt = data.get("backtest")
        if bt:
            lines.append(f"## ✅ 历史验证（用真实出海案例回测引擎准确度）")
            lines.append(f"")
            lines.append(f"- 案例数: {bt['total_cases']} | 通过: {bt['passed_cases']} | **通过率: {bt['pass_rate']:.0%}**")
            lines.append(f"")
            lines.append(f"  | 案例 | 真实进入 | 回测排名 | 结果 |")
            lines.append(f"  |:-----|:---------|:---------|:----:|")
            for r in bt["results"]:
                c = r["case"]
                hits_str = "、".join(
                    f"{h['name']} 第{h['rank']}名" if h["rank"] else f"{h['name']} 未进Top"
                    for h in r["hits"]
                )
                lines.append(f"  | {c['name']} | {hits_str} | {r.get('top3', '—') and '、'.join(t['name'] for t in r.get('top3', [])[:3])} | {'✅' if r.get('passed') else '❌'} |")
            lines.append("")

        # 反向时光机（海外周期 → 中国国内预判）
        rtm = data.get("reverse_time_machine")
        if rtm and rtm.get("matches"):
            lines.append(f"## 🔄 反向时光机（海外已验证周期 → 中国国内预判）")
            lines.append("")
            lines.append("> 用发达经济体已走完的周期，预判后发市场正在经历的阶段（房地产/金融/产业）。")
            lines.append("")
            by_target = {}
            for r in rtm["matches"]:
                by_target.setdefault(r["target_iso3"], []).append(r)
            for target, items in by_target.items():
                cn = COUNTRY_CN.get(target, target)
                lines.append(f"- **{cn}** ({target}):")
                for r in items:
                    best = r["matched_phase"]
                    next_txt = "、".join(
                        "%d年%s" % (p["phase_year"], p["phase_label"])
                        for p in r["next_phases"])
                    lines.append(f"  - {r['playbook_name']} → 当前 ≈ **{best['phase_year']}年** "
                                 f"({best['phase_label']}, 相似度{best['similarity']:.0%})，"
                                 f"后续参考 {next_txt}")
            lines.append("")

        # 投资决策视图
        iv = data.get("investment_view")
        if iv:
            lines.append(f"## 💰 投资决策清单")
            lines.append("")
            lines.append(f"- 总机会: {iv['total_opportunities']} | "
                         f"🔥现在进场 {iv['summary'].get('now', 0)} | "
                         f"⏳提前卡位 {iv['summary'].get('early', 0)} | "
                         f"👀观察 {iv['summary'].get('watch', 0)}")
            lines.append("")
            lines.append(f"| 分类 | 模式 | 国家 | 相似度 | 窗口 | 建议 |")
            lines.append(f"|:----:|:-----|:-----|:------:|:----:|:-----|")
            for d in iv["decisions"]:
                if d["decision"] not in ("now", "early"):
                    continue
                icon = "🔥" if d["decision"] == "now" else "⏳"
                win = "已到" if d["window_years"] is None or d["window_years"] < 1 else f"{d['window_years']:.0f}年"
                lines.append(f"| {icon} | {d['mode_name']} | {d['country']} | "
                             f"{d['similarity']:.0%} | {win} | {d['action'][:36]} |")
            lines.append("")
        return "\n".join(lines)

    def save_report(self, data: dict) -> str:
        """报告归档"""
        import os
        os.makedirs(REPORT_DIR, exist_ok=True)
        now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = f"{REPORT_DIR}/time_machine_v3_{now}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_report(data))
        return path


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    import argparse
    parser = argparse.ArgumentParser(description="出海时光机 v3 环境匹配引擎")
    parser.add_argument("--top", type=int, default=10, help="每模式 Top N 国家")
    parser.add_argument("--refresh", action="store_true", help="强制刷新世界银行缓存")
    parser.add_argument("--report", action="store_true", help="保存 Markdown 报告")
    args = parser.parse_args()

    engine = TimeMachineV3Engine()
    data = engine.run(top_n=args.top, refresh_cache=args.refresh)
    report = engine.to_report(data)
    print(report)
    if args.report:
        path = engine.save_report(data)
        print(f"\n📄 报告已归档: {path}")


if __name__ == "__main__":
    main()
