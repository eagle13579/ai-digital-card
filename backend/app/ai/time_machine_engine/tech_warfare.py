"""
科技战维度引擎 (Tech Warfare) — 2026-08-08 海容科技参数注入

海容核心认知：美国收割的主赛道不止金融，还有「大科技」——科技战（芯片/半导体/AI/存储/机器人）
是美元潮汐组合拳的现代核心工具。科技风云 → AI → 存储战 → 机器人战 → 美联储毒计，
金融战 + 科技战 + 信息战是串联的收割链条（笨嘴哥财经「金融战火再起」系列，2026-08-08 追踪）。

本引擎把「科技」作为核心投资参数融入出海时光机理论：
  1. 历史科技战事件库（美日半导体战→中美科技战→AI芯片管制→存储战→机器人战）
  2. 科技载体温度计（NASDAQ 指数 = 美国科技市场情绪/泡沫温度）
  3. 科技新闻扫描（半导体/芯片/AI/出口管制/实体清单关键词）
  4. 科技战阶段判定（升级/缓和/常态）+ 承压科技国 + 中国科技出海窗口/风险

数据源（阿里云实测可达）：
  - FRED NASDAQCOM 纳斯达克综合指数（1971起，日频）— 科技股温度计
  - France24 英文 RSS（五区域）— 地缘+科技新闻
  - 韩联社国际 RSS — 亚洲科技新闻
  - HackerNews Algolia — 全球科技动态

三层系统论扩展：本质层(美元潮汐+科技工具箱) → 载体层(科技指数/半导体价格/专利) → 现象层(科技股泡沫/估值)
"""

import re
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

DATA_DIR = "/tmp/tm_data"
NASDAQ_CSV = "/tmp/nasdaq.csv"

# ── 美国科技工具箱 · 历史科技战事件库（金融+科技串联收割）──
TECH_WAR_EVENTS = [
    {
        "year": 1985,
        "event": "美日半导体战争（广场协议前后）",
        "tide": "美元贬值+日本被迫升值",
        "tools": ["广场协议(汇率施压)", "超级301条款", "美日半导体协议(强制市场份额)"],
        "targets": "日本（东芝/日立/富士通）",
        "carrier": "日元升值 → 出口竞争力崩 → 半导体份额被美韩夺走 → 泡沫经济",
        "lesson": "科技霸权+汇率武器组合拳：技术领先国也会被金融手段抽干",
    },
    {
        "year": 2018,
        "event": "中美科技战爆发（中兴事件）",
        "tide": "美联储加息周期",
        "tools": ["出口禁令(芯片断供)", "实体清单", "关税战"],
        "targets": "中国（中兴/华为）",
        "carrier": "芯片断供 → 中兴休克 → 科技股恐慌 → 倒逼国产替代",
        "lesson": "芯片断供是科技战最锋利的工具：断点即痛点，倒逼替代产业",
    },
    {
        "year": 2019,
        "event": "华为实体清单升级（科技战全面化）",
        "tide": "美元走强",
        "tools": ["实体清单升级", "EDA断供", "Google服务禁运"],
        "targets": "中国（华为/海思）",
        "carrier": "供应链断裂 → 华为手机份额崩 → 倒逼鸿蒙/麒麟/国产EDA",
        "lesson": "科技战从芯片延伸到生态：操作系统/EDA/半导体设备全链条封锁",
    },
    {
        "year": 2020,
        "event": "芯片出口管制升级（台积电断供华为）",
        "tide": "疫情流动性危机→QE",
        "tools": ["外国直接产品规则(FDPR)", "台积电/中芯断供", "半导体设备管制"],
        "targets": "中国（先进制程）",
        "carrier": "先进制程归零 → 成熟制程扩产 → 国产设备/材料进口替代提速",
        "lesson": "管制越狠，替代产业补贴越多——科技战是国产替代的催化剂",
    },
    {
        "year": 2022,
        "event": "CHIPS法案 + 对华芯片限制（科技战制度化）",
        "tide": "激进加息 4%+",
        "tools": ["CHIPS法案(527亿补贴)", "对华AI芯片禁售", "半导体设备出口管制(10.7新规)"],
        "targets": "中国（先进制程/AI芯片）",
        "carrier": "英伟达A100/H100禁售 → 中国AI芯片国产化 → 存储/设备国产替代加速",
        "lesson": "科技战+产业补贴双轨：美国用补贴吸引制造业回流，用管制锁死对手升级",
    },
    {
        "year": 2023,
        "event": "AI芯片管制升级（A800/H800禁令）",
        "tide": "加息尾声",
        "tools": ["A800/H800禁售", "先进封装管制", "美日荷三方限制半导体设备"],
        "targets": "中国（AI算力）",
        "carrier": "AI算力断供 → 昇腾/寒武纪爆发 → 算力租赁市场井喷",
        "lesson": "AI是科技战新高地：算力管制反而催生国产算力+智算中心投资热潮",
    },
    {
        "year": 2025,
        "event": "存储芯片战（华尔街狙击韩国）",
        "tide": "降息周期",
        "tools": ["存储涨价周期", "AI服务器需求", "三星/海力士库存博弈"],
        "targets": "韩国（三星/SK海力士）",
        "carrier": "存储涨价 → 韩国存储股波动 → HBM(高带宽存储)成为AI军备核心",
        "lesson": "AI革命把存储变成战略资源：HBM/DRAM/NAND 成为科技战新筹码",
    },
    {
        "year": 2026,
        "event": "机器人/具身智能战（宇树科技被关注）",
        "tide": "降息→宽松周期",
        "tools": ["AI+机器人产业竞赛", "人形机器人量产", "具身智能数据争夺"],
        "targets": "中美科技竞赛（宇树/波士顿动力）",
        "carrier": "人形机器人量产 → 传感器/电机/减速器产业链爆发 → 中国机器人出海窗口",
        "lesson": "科技战下一主战场=具身智能：中国硬件供应链优势+AI算法追赶=窗口期",
    },
]

# ── 科技战新闻关键词 ──
TECH_KEYWORDS = [
    "semiconductor", "chip", "chipmaker", "chipset", "microchip", "fab",
    "export control", "export ban", "entity list", "tariff", "sanction",
    "nvidia", "tsmc", "samsung", "intel", "amd", "asml", "hbm", "dram",
    "ai", "artificial intelligence", "gpu", "large language model",
    "robot", "robotics", "humanoid", "drone",
    "quantum", "5g", "6g", "telecom", "internet",
    "cyber", "hack", "cyberattack", "data", "software",
    "半导体", "芯片", "晶圆", "光刻", "出口管制", "实体清单", "制裁",
    "人工智能", "大模型", "机器人", "人形机器人", "无人机", "量子",
]

# ── 科技强信号关键词（科技战升级信号）──
TECH_STRONG_KEYWORDS = [
    "export control", "export ban", "entity list", "sanction",
    "nvidia", "tsmc", "asml", "hbm", "semiconductor", "chip",
    "芯片", "半导体", "出口管制", "实体清单", "禁售",
]

# 科技新闻源（复用地缘引擎可达源）
TECH_FEEDS = {
    "france24_main": "https://www.france24.com/en/rss",
    "france24_asia": "https://www.france24.com/en/asia-pacific/rss",
    "france24_americas": "https://www.france24.com/en/americas/rss",
    "yna_international": "https://www.yna.co.kr/rss/international.xml",
    "yna_industry": "https://www.yna.co.kr/rss/industry.xml",
}
HN_API = "https://hn.algolia.com/api/v1/search_by_date?query=%s&tags=story&hitsPerPage=12"
HN_QUERIES = ["semiconductor", "chip", "AI", "robot", "Nvidia", "TSMC", "export control", "humanoid"]
TIMEOUT = 12

# ── 核心科技词（必须命中才算有效科技信号，弱词只加分）──
TECH_CORE_KEYWORDS = [
    "semiconductor", "chip", "chipmaker", "chipset", "microchip", "fab",
    "export control", "export ban", "entity list", "sanction",
    "nvidia", "tsmc", "samsung", "intel", "amd", "asml", "hbm", "dram", "foundry",
    "artificial intelligence", "gpu", "large language model",
    "humanoid", "robotics",
    "半导体", "芯片", "晶圆", "光刻", "出口管制", "实体清单", "制裁",
    "人工智能", "大模型", "机器人", "人形机器人",
]


class TechWarfareEngine:
    """科技战维度引擎：历史事件库 + NASDAQ温度计 + 科技新闻扫描 → 科技战阶段判定"""

    def __init__(self):
        self.events = TECH_WAR_EVENTS

    # ── NASDAQ 科技股温度计 ──────────────────────────────
    def _load_nasdaq(self) -> list[float]:
        """读取本地 NASDAQ 指数 CSV（FRED 预抓），返回收盘序列"""
        if not os.path.exists(NASDAQ_CSV):
            self._fetch_nasdaq()
        series = []
        try:
            with open(NASDAQ_CSV, encoding="utf-8") as f:
                next(f, None)  # 表头
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(",")
                    if len(parts) >= 2:
                        try:
                            series.append(float(parts[1]))
                        except ValueError:
                            pass
        except Exception:
            return []
        return series

    def _fetch_nasdaq(self) -> bool:
        """从 FRED 抓 NASDAQCOM（1971起，日频）"""
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQCOM"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read().decode()
            with open(NASDAQ_CSV, "w", encoding="utf-8") as f:
                f.write(data)
            return True
        except Exception:
            return False

    def nasdaq_status(self) -> dict:
        """NASDAQ 温度计：1年/6月/3月/1月涨跌幅 + 泡沫判断"""
        s = self._load_nasdaq()
        if len(s) < 30:
            return {"available": False}
        n = len(s)
        def pct(idx):
            if idx < 0 or idx >= n:
                return 0.0
            base = s[idx]
            return round((s[-1] / base - 1) * 100, 1) if base else 0.0
        y1 = max(0, n - 252)
        m6 = max(0, n - 126)
        m3 = max(0, n - 63)
        m1 = max(0, n - 21)
        status = {
            "available": True,
            "last": s[-1],
            "y1_pct": pct(y1),
            "m6_pct": pct(m6),
            "m3_pct": pct(m3),
            "m1_pct": pct(m1),
        }
        # 泡沫判断：1年涨幅>25% = 科技过热；>40% = 泡沫预警
        if status["y1_pct"] > 40:
            status["bubble"] = "🫧 科技泡沫预警 (1年+40%以上)"
        elif status["y1_pct"] > 25:
            status["bubble"] = "⚠️ 科技过热 (1年+25%以上)"
        elif status["y1_pct"] < -20:
            status["bubble"] = "🧊 科技寒冬 (1年-20%以上)"
        else:
            status["bubble"] = "✅ 科技市场常态"
        return status

    # ── 科技新闻扫描 ─────────────────────────────────────
    def _fetch_feed(self, url: str) -> list[dict]:
        items = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            root = ET.fromstring(raw)
            for item in root.iter("item"):
                title = ""
                for t in item.findall("title"):
                    title = (t.text or "").strip()
                if title:
                    items.append({"title": title, "source": url})
        except Exception:
            pass
        return items

    def _fetch_hn(self) -> list[dict]:
        items = []
        import json
        for q in HN_QUERIES:
            try:
                url = HN_API % urllib.parse.quote(q)
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    data = resp.read().decode()
                d = json.loads(data)
                for hit in d.get("hits", [])[:8]:
                    t = hit.get("title") or ""
                    if t:
                        items.append({"title": t, "source": f"HN:{q}"})
            except Exception:
                pass
        return items

    def scan_news(self) -> list[dict]:
        """扫描科技新闻，返回命中科技关键词的条目"""
        all_items = []
        for name, url in TECH_FEEDS.items():
            all_items.extend(self._fetch_feed(url))
        all_items.extend(self._fetch_hn())
        hits = []
        seen = set()
        for item in all_items:
            title = item["title"]
            if title in seen:
                continue
            seen.add(title)
            low = title.lower()
            core = [k for k in TECH_CORE_KEYWORDS if k in low]
            if not core:
                # 无核心词：弱词命中不算有效科技信号，跳过（避免 "drones fire" 类碰瓷）
                continue
            strong = [k for k in TECH_STRONG_KEYWORDS if k in low]
            hits.append({
                "title": title[:200],
                "source": item["source"],
                "matched": core[:5],
                "strong": strong[:5],
                "score": 2.0 if strong else 1.0,
            })
        return hits

    # ── 科技战阶段判定 ───────────────────────────────────
    def tech_regime(self, hits: list[dict], nasdaq: dict) -> dict:
        """科技战阶段：升级(tech_war) / 缓和(de-escalation) / 常态(tech_normal)"""
        strong_hits = [h for h in hits if h.get("strong")]
        # 信号强度
        escal_score = min(len(strong_hits), 10) * 2 + min(len(hits), 15)
        # 载体联动：NASDAQ 1年跌幅大 + 科技战新闻多 = 战争升级
        if nasdaq.get("available"):
            if nasdaq.get("y1_pct", 0) < -10:
                escal_score += 3
            if nasdaq.get("y1_pct", 0) < -25:
                escal_score += 3
        if escal_score >= 20:
            regime = "tech_war"
            label = "🔴 科技战升级"
        elif escal_score >= 10:
            regime = "tech_tension"
            label = "🟠 科技博弈加剧"
        else:
            regime = "tech_normal"
            label = "🟢 科技常态"
        return {
            "regime": regime,
            "label": label,
            "score": escal_score,
            "strong_hits": len(strong_hits),
            "total_hits": len(hits),
            "nasdaq": nasdaq,
            "hot_topics": sorted(set(h.get("matched", [""])[0] for h in hits if h.get("matched")))[:8],
        }

    def tech_opportunity(self, regime: dict) -> dict:
        """科技战对出海机会的影响：承压国 + 替代机会 + 窗口"""
        tech = regime.get("regime")
        opp = {"window": "normal", "pressed_countries": [], "opportunities": []}
        if tech in ("tech_war", "tech_tension"):
            opp["window"] = "国产替代加速" if tech == "tech_war" else "博弈中布局"
            opp["pressed_countries"] = ["CHN(先进制程/AI芯片)", "KOR(存储/HBM)"]
            opp["opportunities"] = [
                "半导体设备/材料国产替代（管制越狠替代越快）",
                "AI芯片国产化（昇腾/寒武纪 → 算力租赁）",
                "成熟制程产能扩张（28nm+不受限）",
                "存储/HBM 涨价周期（AI服务器刚需）",
                "人形机器人产业链（中国供应链优势）",
                "中东/东南亚承接科技产业转移（避管制）",
            ]
        else:
            opp["window"] = "科技合作常态"
            opp["pressed_countries"] = []
            opp["opportunities"] = [
                "科技出海正常窗口（数字化/电商/移动支付）",
                "AI应用出海（软件/工具/SaaS）",
            ]
        return opp

    def run(self) -> dict:
        """主入口：NASDAQ + 新闻扫描 → 科技战阶段 → 机会/风险"""
        nasdaq = self.nasdaq_status()
        hits = self.scan_news()
        regime = self.tech_regime(hits, nasdaq)
        opp = self.tech_opportunity(regime)
        return {
            "regime": regime,
            "opportunity": opp,
            "events": self.events,
            "news_hits": hits[:15],
            "nasdaq": nasdaq,
        }

    # ── 报告段落 ─────────────────────────────────────────
    def to_report(self, data: dict) -> str:
        regime = data.get("regime", {})
        opp = data.get("opportunity", {})
        nasdaq = regime.get("nasdaq", {})
        lines = []
        lines.append("### 🛰️ 科技战维度（美国收割主赛道）")
        lines.append(f"- **科技战阶段**: {regime.get('label', 'N/A')}（信号分 {regime.get('score', 0)}，"
                     f"强信号 {regime.get('strong_hits', 0)} 条/新闻命中 {regime.get('total_hits', 0)} 条）")
        if nasdaq.get("available"):
            lines.append(f"- **NASDAQ 温度计**: 收于 {nasdaq.get('last', 0):,.0f} ｜ 1年 {nasdaq.get('y1_pct', 0)}% ｜ "
                         f"6月 {nasdaq.get('m6_pct', 0)}% ｜ 3月 {nasdaq.get('m3_pct', 0)}% ｜ 1月 {nasdaq.get('m1_pct', 0)}%")
            lines.append(f"  - {nasdaq.get('bubble', '')}")
        if opp.get("window"):
            lines.append(f"- **科技出海窗口**: {opp.get('window', '')}")
        if opp.get("pressed_countries"):
            lines.append(f"- **承压科技国**: {', '.join(opp.get('pressed_countries', []))}")
        if opp.get("opportunities"):
            lines.append(f"- **科技机会**: {'；'.join(opp.get('opportunities', [])[:4])}")
        topics = regime.get("hot_topics", [])
        if topics:
            lines.append(f"- **当前热点**: {', '.join(topics[:5])}")
        # 历史科技战事件（最近 3 个）
        lines.append(f"- **历史科技战链**（最近3场）:")
        for ev in data.get("events", [])[-3:]:
            lines.append(f"  - {ev['year']} {ev['event']} → {ev['lesson'][:60]}")
        return "\n".join(lines)


if __name__ == "__main__":
    eng = TechWarfareEngine()
    out = eng.run()
    print(eng.to_report(out))
    print("\n--- 新闻命中示例 ---")
    for h in out.get("news_hits", [])[:8]:
        print(f"  [{h['score']}] {h['title'][:100]}")
