#!/usr/bin/env python3
"""
立体事件网络 (news_network.py)
==============================
2026-08-08 海容核心方法论：
「一条新闻不是孤立的，是一个立体网络——纵向时间线（事件链延展）+
 横向产业链影响（传导）+ 美元潮汐整体水位（宏观背景）。
 千万不能按照单一新闻来看，要的是整体的网络。」

三层架构:
  纵轴 (事件链): EventChainTracker — 同一事件多新闻累积成时间线演化
  横轴 (产业链): NewsImpactEngine — 每条新闻 → 产业链双向传导 → 受益/受损环节
  背景层 (美元潮汐): DollarTideEngine — 宏观水位（降息=潮涌/加息=退潮），
      宏观新闻（美联储/利率/CPI）不推产业链，而是更新整体水位 → 所有链条修正

输出:
  - news_network.json     立体网络数据（前端可消费）
  - news_network_report.md  Markdown 报告
用法:
  python3 news_network.py            # 全流程
  python3 news_network.py --no-fetch # 用上次采集的缓存（快速重推演）
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta

BACKEND = "/var/www/ai-digital-card/backend"
sys.path.insert(0, os.path.join(BACKEND, "scripts"))
sys.path.insert(0, os.path.join(BACKEND, "app", "ai"))
sys.path.insert(0, os.path.join(BACKEND, "app", "ai", "china_softbank_engine"))

REPORT_DIR = os.path.join(BACKEND, "data", "time_machine_reports")
CACHE_FILE = os.path.join(REPORT_DIR, "news_network_raw_cache.json")
NETWORK_FILE = os.path.join(REPORT_DIR, "news_network.json")
REPORT_FILE = os.path.join(REPORT_DIR, "news_network_report.md")

from news_sources import fetch_all_sources
from news_chain import EventChainTracker, extract_entities

# ============================================================
# 宏观新闻识别（美联储/美元/利率/通胀 → 背景层，不推产业链）
# ============================================================
MACRO_KEYWORDS = [
    "美联储", "fed", "federal reserve", "鲍威尔", "powell", "加息", "降息", "利率决议",
    "美元指数", "dxy", "美元走强", "美元走弱", "通胀", "inflation", "cpi", "ppi",
    "非农", "失业率", "国债收益率", "美债", "收益率曲线", "缩表", "qe", "qt",
    "fed rate", "rate cut", "rate hike", "美联储主席", "fomc",
]
# 宏观新闻的实体也进事件链（如「美联储降息」单独成链，便于时间线）
MACRO_ENTITIES = {"美联储", "加息", "降息", "美元", "通胀", "关税", "制裁", "非农", "国债"}

# 排除关键词（政治/犯罪/天气/体育等非产业新闻）
EXCLUDE_KW = [
    "足球", "世界杯", "奥运会", "选举", "投票", "议会", "总统", "总理", "首相",
    "犯罪", "枪击", "爆炸", "袭击", "天气", "台风", "地震", "洪水", "彩票",
    "娱乐", "明星", "电影", "音乐", "sport", "football", "world cup", "olympics",
    "election", "vote", "crime", "murder", "weather", "typhoon", "earthquake",
    "hollywood", "celebrity", "festival", "concert", "联赛", "冠军",
    "核试验", "阅兵", "军演", "人质", "绑架",
]


def is_relevant(title: str, desc: str) -> bool:
    """过滤：保留财经/产业/宏观相关，排除政治犯罪天气娱乐"""
    text = f"{title} {desc}".lower()
    finance_kw = [
        "半导体", "芯片", "出口", "进口", "关税", "投资", "工厂", "产能",
        "涨价", "降价", "供应链", "市场", "股价", "经济", "产业", "制造",
        "电池", "汽车", "能源", "矿产", "铜", "稀土", "石油", "天然气",
        "AI", "人工智能", "机器人", "数据中心", "光伏", "存储",
        "银行", "利率", "通胀", "GDP", "贸易", "收购", "合并", "IPO",
        "chip", "semiconductor", "export", "tariff", "investment", "factory",
        "supply", "market", "economy", "industry", "battery", "auto", "energy",
        "mining", "copper", "oil", "gas", "robot", "data center", "solar",
        "bank", "rate", "inflation", "trade", "merger", "fed", "美元",
        "美联储", "降息", "加息", "黄金", "白银", "钴", "锂", "刚果",
    ]
    if any(kw.lower() in text for kw in finance_kw):
        return not any(kw in text for kw in EXCLUDE_KW)
    return False


def is_macro_news(title: str, desc: str) -> bool:
    """判断是否为宏观背景新闻（美联储/美元/利率/通胀）"""
    text = f"{title} {desc}".lower()
    return any(kw.lower() in text for kw in MACRO_KEYWORDS)


# ============================================================
# 立体网络构建
# ============================================================
class NewsNetworkBuilder:
    """立体网络：纵轴事件链 + 横轴产业链 + 背景层美元潮汐"""

    def __init__(self, chain_file: str = None):
        self.tracker = EventChainTracker(chain_file or os.path.join(REPORT_DIR, "news_chains.json"))
        self.macro_state = {"regime": "unknown", "direction": "观望", "signal_count": 0, "news": []}
        self.chains_data = []
        self.hot_chains = []

    # ---------- 1. 宏观水位（美元潮汐背景层） ----------
    def _load_macro_background(self) -> dict:
        """读最近美元潮汐引擎状态作为背景层水位"""
        try:
            sys.path.insert(0, os.path.join(BACKEND, "app", "ai", "time_machine_engine"))
            from dollar_tide import DollarTideEngine
            tide = DollarTideEngine()
            cycle = tide.cycle_stage()
            stage = cycle.get("stage", "unknown")
            direction = {
                "easing": "🌊降息周期·潮水涌出·新兴市场窗口",
                "turning_easing": "🌊转向宽松·潮水开始涌出",
                "tightening": "🏜️加息周期·潮水退去·新兴市场承压",
                "turning_tightening": "🏜️转向紧缩·潮水开始退去",
                "waiting": "⏳等待期·方向未明",
            }.get(stage, "⏳等待期")
            # 宏观网络修正层：美元周期 → 产业链全局修正系数（海容「整体网络」方法论）
            # 降息/宽松 = 潮涌 → 商品需求向上、成长股受益、新兴市场重估
            # 加息/紧缩 = 退潮 → 商品承压、避险资产受益、新兴市场风险升
            modifiers = {
                "easing": {"commodity": 1.15, "growth": 1.10, "defensive": 0.95,
                           "label": "降息潮涌：商品/成长/新兴市场全面受益"},
                "turning_easing": {"commodity": 1.10, "growth": 1.08, "defensive": 0.97,
                                   "label": "转向宽松：潮水初涌，商品与成长先行"},
                "tightening": {"commodity": 0.90, "growth": 0.92, "defensive": 1.10,
                               "label": "加息退潮：商品承压，避险/防御受益"},
                "turning_tightening": {"commodity": 0.93, "growth": 0.94, "defensive": 1.06,
                                       "label": "转向紧缩：潮水初退，风险资产警惕"},
                "waiting": {"commodity": 1.0, "growth": 1.0, "defensive": 1.0,
                            "label": "方向未明：观望为主"},
            }
            return {
                "regime": stage,
                "direction": direction,
                "rate": cycle.get("fed_funds_current", 0),
                "rate_trend": cycle.get("fed_funds_trend", 0),
                "dxy": cycle.get("dxy_current", 0),
                "dxy_trend": cycle.get("dxy_trend", 0),
                "risk_mode": cycle.get("risk_mode", ""),
                "modifiers": modifiers.get(stage, modifiers["waiting"]),
                "source": "dollar_tide.DollarTideEngine",
            }
        except Exception as e:
            return {"regime": "unknown", "direction": f"⚠️宏观引擎不可用: {e}", "rate": 0,
                    "rate_trend": 0, "dxy": 0, "dxy_trend": 0, "risk_mode": "",
                    "modifiers": {"commodity": 1.0, "growth": 1.0, "defensive": 1.0, "label": "宏观引擎不可用"},
                    "source": "fallback"}

    def _apply_macro_news(self, news: dict, macro: dict):
        """宏观新闻更新背景层（不推产业链，累积信号 + 方向佐证）"""
        macro["signal_count"] += 1
        macro["news"].append({
            "title": news.get("title", "")[:60],
            "ts": news.get("ts", ""),
            "source": news.get("source", ""),
        })
        # 方向信号判断（注意「押注降温/爆冷/暂停/分歧」等否定语义）
        text = f"{news.get('title','')} {news.get('desc','')}".lower()
        # 否定词：降温/暂停/分歧/爆冷/意外/推迟/取消 → 不触发反向
        neg = ["降温", "暂停", "分歧", "爆冷", "意外", "推迟", "取消", "降温", "没意义", "押注降温", "opino"]
        def _has_neg():
            return any(n in text for n in neg)
        if any(k in text for k in ["降息", "rate cut", "放水", "宽松"]) and not _has_neg():
            macro["direction"] = "🌊降息/宽松信号 · 潮水涌出（利好新兴市场+商品）"
        elif any(k in text for k in ["加息", "rate hike", "缩表", "紧缩"]) and not _has_neg():
            macro["direction"] = "🏜️加息/紧缩信号 · 潮水退去（利空新兴市场+商品承压）"
        elif any(k in text for k in ["通胀", "inflation", "cpi"]) and not _has_neg():
            macro["direction"] = "🔥通胀信号 · 加息预期升温（商品多空分歧）"

    # ---------- 2. 主流程 ----------
    def build(self, items: list, max_analyze: int = 200) -> dict:
        """输入新闻流 → 立体网络"""
        from china_softbank_engine.news_impact import NewsImpactEngine
        engine = NewsImpactEngine()
        macro = self._load_macro_background()
        macro.setdefault("signal_count", 0)
        macro.setdefault("news", [])

        analyzed, macro_news, skipped = [], [], 0
        for it in items:
            if not is_relevant(it.get("title", ""), it.get("desc", "")):
                skipped += 1
                continue
            # 宏观新闻 → 背景层
            if is_macro_news(it.get("title", ""), it.get("desc", "")):
                self._apply_macro_news(it, macro)
                macro_news.append(it)
                # 宏观新闻也进事件链（背景事件时间线）
                self.tracker.feed(it)
                continue
            # 普通产业新闻 → 产业链推演 + 事件链
            try:
                result = engine.analyze(it.get("title", ""), it.get("desc", ""))
            except Exception:
                continue
            if (result.get("detected") or {}).get("confidence", 0) < 0.3:
                skipped += 1
                continue
            chain_id = self.tracker.feed(it, result)
            analyzed.append({
                "title": it.get("title", ""),
                "source": it.get("source", ""),
                "chain_id": chain_id,
                "detected": result["detected"],
                "opportunities": (result.get("opportunities") or [])[:5],
                "propagation": (result.get("propagation") or {}).get("results", [])[:8],
            })
            if len(analyzed) >= max_analyze:
                break

        self.tracker.save()
        self.macro_state = macro
        chains = self.tracker.snapshot()
        # 只取有实际影响链的活跃链（至少2条新闻 或 高置信）
        # 地缘军事类链降权（Houthi/Iran/Turkey 等霸榜但推演价值低于产业链）
        GEO_KW = ["胡塞", "霍乱", "空袭", "打击", "军事", "袭击", "houthi", "strike", "kills",
                  "导弹", "drone", "轰炸", "冲突", "停火", "伤亡", "爆炸", "rescue", "dead"]
        def _geo_penalty(c):
            t = c.get("title", "")
            ents = c.get("entities", [])
            if any(k.lower() in t.lower() for k in GEO_KW):
                return 0.5
            if "地缘" in ents:
                return 0.8
            return 1.0
        scored = []
        for c in chains:
            if c.get("status") not in ("active", "dormant"):
                continue
            if c.get("news_count", 0) < 2 and c.get("max_confidence", 0) < 0.5:
                continue
            score = c.get("news_count", 0) * 0.6 + c.get("max_confidence", 0) * 10
            score *= _geo_penalty(c)
            scored.append((score, c))
        scored.sort(key=lambda x: -x[0])
        self.hot_chains = [c for _, c in scored[:15]]

        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "stats": {
                "total_items": len(items),
                "analyzed": len(analyzed),
                "macro_news": len(macro_news),
                "skipped": skipped,
                "active_chains": len([c for c in chains if c.get("status") == "active"]),
            },
            "macro_background": macro,
            "chains": [self._chain_public(c) for c in chains[:30]],
            "hot_chains": [self._chain_public(c) for c in self.hot_chains],
            "impact_pool": self._aggregate_impacts(analyzed),
            "recent_analyzed": analyzed[:20],
        }

    def _chain_public(self, chain: dict) -> dict:
        """链数据精简版（前端可消费）"""
        return {
            "chain_id": chain.get("chain_id"),
            "title": chain.get("title"),
            "entities": chain.get("entities"),
            "status": chain.get("status"),
            "news_count": chain.get("news_count"),
            "created_ts": chain.get("created_ts"),
            "last_ts": chain.get("last_ts"),
            "max_confidence": round(chain.get("max_confidence", 0), 2),
            "timeline": [
                {"ts": it.get("ts"), "title": it.get("title", "")[:80],
                 "source": it.get("source", ""), "impact": it.get("impact", ""),
                 "confidence": it.get("confidence", 0)}
                for it in sorted(chain.get("timeline", []), key=lambda x: str(x.get("ts", "")))[-10:]
            ],
        }

    def _aggregate_impacts(self, analyzed: list) -> dict:
        """横轴聚合：所有新闻的产业链影响 → 环节受益/受损计数"""
        agg = {}
        for a in analyzed:
            for r in a.get("propagation", []):
                node = r.get("name", "")
                d = r.get("direction", "")
                if not node:
                    continue
                key = f"{node}|{d}"
                agg.setdefault(key, {"node": node, "direction": d, "count": 0, "score_sum": 0.0})
                agg[key]["count"] += 1
                agg[key]["score_sum"] += r.get("score", 0)
        # 排序输出 Top
        items = sorted(agg.values(), key=lambda x: (-x["count"], -x["score_sum"]))
        return {
            "top_beneficiaries": [i for i in items if "受益" in i["direction"] or "相对受益" in i["direction"]][:10],
            "top_hit": [i for i in items if "受损" in i["direction"]][:8],
            "all": items[:20],
        }

    # ---------- 3. 报告 ----------
    def to_report(self, data: dict) -> str:
        macro = data.get("macro_background", {})
        stats = data.get("stats", {})
        lines = [
            "# 🌐 立体事件网络日报",
            "",
            f"> 生成时间: {data.get('generated_at')}",
            f"> 采集 {stats.get('total_items', 0)} 条 → 推演 {stats.get('analyzed', 0)} 条 | 宏观 {stats.get('macro_news', 0)} 条 | 活跃链 {stats.get('active_chains', 0)} 条",
            "",
            "## 🌊 背景层：美元潮汐宏观水位（整体网络）",
            "",
            f"- **当前周期**: {macro.get('regime')} | {macro.get('direction')}",
            f"- **宏观修正**: {macro.get('modifiers', {}).get('label', '')}",
            f"- **利率**: {macro.get('rate', 0)}%（趋势 {macro.get('rate_trend', 0):+.2f}pp） | **美元指数**: {macro.get('dxy', 0)}（{macro.get('dxy_trend', 0):+.2f}） | **风险**: {macro.get('risk_mode', '')}",
            f"- **宏观信号数**: {macro.get('signal_count', 0)} 条（本期）",
        ]
        for n in macro.get("news", [])[-5:]:
            lines.append(f"  - 🏷️ {n.get('title', '')[:50]} ({n.get('source', '')})")
        lines.append("")

        # 横轴：产业链影响聚合
        ip = data.get("impact_pool", {})
        lines.append("## 🔗 横轴：产业链影响聚合（本期新闻）")
        lines.append("")
        if ip.get("top_beneficiaries"):
            lines.append("**✅ 受益环节 Top**")
            for i in ip["top_beneficiaries"][:8]:
                lines.append(f"- {i['node']} {i['direction']} ×{i['count']} (平均冲击 {i['score_sum']/max(i['count'],1):.2f})")
        else:
            lines.append("- 本期无明显受益环节")
        lines.append("")
        if ip.get("top_hit"):
            lines.append("**⚠️ 受损环节 Top**")
            for i in ip["top_hit"][:5]:
                lines.append(f"- {i['node']} {i['direction']} ×{i['count']}")
        lines.append("")

        # 纵轴：事件链
        lines.append("## 📈 纵轴：事件链追踪（纵向时间线）")
        lines.append("")
        hot = data.get("hot_chains", [])
        if not hot:
            lines.append("- 暂无成熟事件链（继续积累）")
        for c in hot[:10]:
            st = {"active": "🟢活跃", "dormant": "🟡沉睡", "archived": "⚪归档"}.get(c.get("status"), c.get("status"))
            lines.append(f"### {st} {c.get('title', '')[:50]}")
            lines.append(f"`{c.get('chain_id')}` | 实体: {'/'.join(c.get('entities', [])[:6])} | {c.get('news_count')}条 | 最高置信 {c.get('max_confidence')*100:.0f}%")
            lines.append("")
            lines.append("| 时间 | 标题 | 来源 | 影响 |")
            lines.append("|:-----|:-----|:-----|:-----|")
            for t in c.get("timeline", [])[-6:]:
                ts = (t.get("ts") or "")[5:16]
                lines.append(f"| {ts} | {t.get('title','')[:36]} | {t.get('source','')[:10]} | {t.get('impact','')} |")
            lines.append("")

        # 本期高置信新闻
        lines.append("## 🎯 本期高置信推演")
        lines.append("")
        lines.append("| 置信 | 标题 | 事件类型 | Top机会 |")
        lines.append("|:----|:-----|:---------|:--------|")
        for a in data.get("recent_analyzed", [])[:12]:
            det = a.get("detected", {})
            conf = det.get("confidence", 0)
            if conf < 0.4:
                continue
            opp = ""
            if a.get("opportunities"):
                opp = a["opportunities"][0].get("company", "")
            lines.append(f"| {conf*100:.0f}% | {a.get('title','')[:34]} | {det.get('event_type','')} | {opp} |")
        lines.append("")
        lines.append("---")
        lines.append("*立体事件网络引擎 v1.0 | 纵轴事件链 × 横轴产业链 × 美元潮汐背景层*")
        return "\n".join(lines)

    def save(self, data: dict):
        with open(NETWORK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(self.to_report(data))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-fetch", action="store_true", help="用缓存不重新采集")
    parser.add_argument("--max", type=int, default=200, help="最大推演条数")
    args = parser.parse_args()

    items = []
    if args.no_fetch and os.path.isfile(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            items = json.load(f)
        print(f"📦 使用缓存 {len(items)} 条")
    else:
        print("📡 采集多源新闻...")
        items = fetch_all_sources()
        os.makedirs(REPORT_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"✅ 采集 {len(items)} 条")

    builder = NewsNetworkBuilder()
    print("🕸️ 构建立体网络...")
    data = builder.build(items, max_analyze=args.max)
    builder.save(data)

    print(f"\n📊 立体网络完成: 推演{data['stats']['analyzed']}条 | 宏观{data['stats']['macro_news']}条 | "
          f"活跃链{data['stats']['active_chains']}条")
    print(f"📄 报告: {REPORT_FILE}")
    print(f"📄 JSON: {NETWORK_FILE}")
    if data["hot_chains"]:
        print("\n🔥 热门事件链:")
        for c in data["hot_chains"][:5]:
            print(f"  [{c['status']}] {c['title'][:40]} ({c['news_count']}条)")


if __name__ == "__main__":
    main()
