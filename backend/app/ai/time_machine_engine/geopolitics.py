"""
地缘政治实时预警引擎 (Geopolitics Alert) — 2026-08-08 海容系统观落地

海容认知：美元潮汐配合政治/军事/地缘手段（制裁/冲突/生化/病毒）形成「组合拳」。
本模块实时扫描地缘新闻源 + 载体层异动信号，识别「当前被组合拳瞄准的国家」，
提前给出风险预警与机会提示（危机=崩盘风险，也是未来抄底窗口）。

数据源（阿里云实测可达，免 key）：
  - France24 英文 RSS（五区域）: 主站 /europe /americas /africa /asia-pacific /middle-east
  - 韩联社国际频道（备用，韩文）
  - FRED 载体数据（VIX/美元指数/原油/铜）异动信号

信号设计：
  1. 新闻信号: 标题关键词匹配（制裁/冲突/危机/违约/贬值/动荡/大选/抗议/罢工/袭击/军事/病毒/疫情）
  2. 载体信号: VIX 飙升 / 美元走强 / 大宗商品暴跌（对应历史组合拳模式）
  3. 国家识别: 从标题中提取国家名/ISO3（内置主要国家映射表）
  4. 综合评分: 新闻命中×权重 + 载体异动×权重 → 预警清单
"""

import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# ── 数据源 ──
FRANCE24_FEEDS = {
    "main": "https://www.france24.com/en/rss",
    "europe": "https://www.france24.com/en/europe/rss",
    "americas": "https://www.france24.com/en/americas/rss",
    "africa": "https://www.france24.com/en/africa/rss",
    "asia_pacific": "https://www.france24.com/en/asia-pacific/rss",
    "middle_east": "https://www.france24.com/en/middle-east/rss",
}
YNA_WORLD = "https://www.yna.co.kr/rss/international.xml"
TIMEOUT = 15

# ── 地缘/金融风险关键词（组合拳手段）──
RISK_KEYWORDS = [
    # 地缘冲突/军事
    "sanction", "sanctions", "制裁", "war", "conflict", "attack", "strike",
    "missile", "military", "invasion", "ceasefire", "truce", "coup", "rebel",
    "insurgent", "militia", "strike", "border", "escalat", "tense", "tension",
    # 政治动荡
    "protest", "riot", "unrest", "protesters", "election", "vote", "impeach",
    "resign", "government", "president", "crisis", "political", "trial",
    # 经济金融风险
    "default", "debt", "bankrupt", "collapse", "plunge", "slump", "crash",
    "devaluation", "depreciation", "inflation", "hyperinflation", "currency",
    "reserve", "foreign exchange", "bailout", "IMF", "rating", "downgrade",
    "capital flight", "outflow", "liquidity",
    # 生化/病毒
    "virus", "outbreak", "ebola", "pandemic", "epidemic", "disease", "cholera",
    "bioweapon", "biological",
]
# 危机/风险强关键词（权重更高）
STRONG_KEYWORDS = [
    "sanction", "default", "collapse", "crash", "devaluation", "hyperinflation",
    "coup", "invasion", "war", "outbreak", "pandemic", "military", "bailout",
    "downgrade", "capital flight", "insurgent",
]

# ── 国家名 → ISO3 映射（覆盖主要新兴市场/危机高发区）──
COUNTRY_MAP = {
    # 中文
    "中国": "CHN", "美国": "USA", "印度": "IND", "巴西": "BRA", "俄罗斯": "RUS",
    "土耳其": "TUR", "阿根廷": "ARG", "墨西哥": "MEX", "南非": "ZAF", "印度尼西亚": "IDN",
    "印尼": "IDN", "泰国": "THA", "韩国": "KOR", "日本": "JPN", "越南": "VNM",
    "菲律宾": "PHL", "马来西亚": "MYS", "巴基斯坦": "PAK", "斯里兰卡": "LKA",
    "埃及": "EGY", "尼日利亚": "NGA", "肯尼亚": "KEN", "埃塞俄比亚": "ETH",
    "委内瑞拉": "VEN", "智利": "CHL", "哥伦比亚": "COL", "秘鲁": "PER",
    "乌克兰": "UKR", "伊朗": "IRN", "以色列": "ISR", "沙特阿拉伯": "SAU",
    "沙特": "SAU", "卡塔尔": "QAT", "阿联酋": "ARE", "叙利亚": "SYR",
    "黎巴嫩": "LBN", "约旦": "JOR", "伊拉克": "IRQ", "也门": "YEM", "阿富汗": "AFG",
    "缅甸": "MMR", "老挝": "LAO", "柬埔寨": "KHM", "孟加拉": "BGD", "尼泊尔": "NPL",
    "希腊": "GRC", "意大利": "ITA", "西班牙": "ESP", "葡萄牙": "PRT", "爱尔兰": "IRL",
    "法国": "FRA", "德国": "DEU", "英国": "GBR", "波兰": "POL", "罗马尼亚": "ROU",
    "匈牙利": "HUN", "塞尔维亚": "SRB", "白俄罗斯": "BLR", "哈萨克斯坦": "KAZ",
    "乌兹别克斯坦": "UZB", "蒙古": "MNG", "朝鲜": "PRK", "古巴": "CUB",
    # 英文
    "china": "CHN", "india": "IND", "brazil": "BRA", "russia": "RUS",
    "turkey": "TUR", "argentina": "ARG", "mexico": "MEX", "south africa": "ZAF",
    "indonesia": "IDN", "thailand": "THA", "south korea": "KOR", "japan": "JPN",
    "vietnam": "VNM", "philippines": "PHL", "malaysia": "MYS", "pakistan": "PAK",
    "sri lanka": "LKA", "egypt": "EGY", "nigeria": "NGA", "kenya": "KEN",
    "ethiopia": "ETH", "venezuela": "VEN", "chile": "CHL", "colombia": "COL",
    "peru": "PER", "ukraine": "UKR", "iran": "IRN", "israel": "ISR",
    "saudi arabia": "SAU", "qatar": "QAT", "uae": "ARE", "syria": "SYR",
    "lebanon": "LBN", "jordan": "JOR", "iraq": "IRQ", "yemen": "YEM",
    "afghanistan": "AFG", "myanmar": "MMR", "laos": "LAO", "cambodia": "KHM",
    "bangladesh": "BGD", "nepal": "NPL", "greece": "GRC", "italy": "ITA",
    "spain": "ESP", "portugal": "PRT", "ireland": "IRL", "france": "FRA",
    "germany": "DEU", "britain": "GBR", "uk": "GBR", "poland": "POL",
    "romania": "ROU", "hungary": "HUN", "serbia": "SRB", "belarus": "BLR",
    "kazakhstan": "KAZ", "uzbekistan": "UZB", "mongolia": "MNG",
    "north korea": "PRK", "cuba": "CUB", "burundi": "BDI", "rwanda": "RWA",
    "sudan": "SDN", "south sudan": "SSD", "somali": "SOM", "mali": "MLI",
    "niger": "NER", "burkina faso": "BFA", "haiti": "HTI", "tunisia": "TUN",
    "algeria": "DZA", "morocco": "MAR", "libya": "LBY", "jamaica": "JAM",
    "taiwan": "TWN", "hong kong": "HKG", "macau": "MAC", "singapore": "SGP",
    "malawi": "MWI", "mozambique": "MOZ", "zambia": "ZMB", "zimbabwe": "ZWE",
    "mongolia": "MNG", "georgia": "GEO", "armenia": "ARM", "azerbaijan": "AZE",
}
# ISO3 → 中文名（报告展示用）
ISO3_CN = {
    "CHN": "中国", "USA": "美国", "IND": "印度", "BRA": "巴西", "RUS": "俄罗斯",
    "TUR": "土耳其", "ARG": "阿根廷", "MEX": "墨西哥", "ZAF": "南非", "IDN": "印尼",
    "THA": "泰国", "KOR": "韩国", "JPN": "日本", "VNM": "越南", "PHL": "菲律宾",
    "MYS": "马来西亚", "PAK": "巴基斯坦", "LKA": "斯里兰卡", "EGY": "埃及",
    "NGA": "尼日利亚", "KEN": "肯尼亚", "ETH": "埃塞俄比亚", "VEN": "委内瑞拉",
    "CHL": "智利", "COL": "哥伦比亚", "PER": "秘鲁", "UKR": "乌克兰", "IRN": "伊朗",
    "ISR": "以色列", "SAU": "沙特", "QAT": "卡塔尔", "ARE": "阿联酋", "SYR": "叙利亚",
    "LBN": "黎巴嫩", "JOR": "约旦", "IRQ": "伊拉克", "YEM": "也门", "AFG": "阿富汗",
    "MMR": "缅甸", "LAO": "老挝", "KHM": "柬埔寨", "BGD": "孟加拉", "NPL": "尼泊尔",
    "GRC": "希腊", "ITA": "意大利", "ESP": "西班牙", "PRT": "葡萄牙", "IRL": "爱尔兰",
    "FRA": "法国", "DEU": "德国", "GBR": "英国", "POL": "波兰", "ROU": "罗马尼亚",
    "HUN": "匈牙利", "SRB": "塞尔维亚", "BLR": "白俄罗斯", "KAZ": "哈萨克斯坦",
    "UZB": "乌兹别克斯坦", "MNG": "蒙古", "PRK": "朝鲜", "CUB": "古巴",
    "SDN": "苏丹", "SSD": "南苏丹", "SOM": "索马里", "MLI": "马里", "NER": "尼日尔",
    "HTI": "海地", "TUN": "突尼斯", "DZA": "阿尔及利亚", "MAR": "摩洛哥",
    "LBY": "利比亚", "TWN": "台湾", "HKG": "香港", "SGP": "新加坡",
    "MWI": "马拉维", "MOZ": "莫桑比克", "ZMB": "赞比亚", "ZWE": "津巴布韦",
    "GEO": "格鲁吉亚", "ARM": "亚美尼亚", "AZE": "阿塞拜疆", "TUN": "突尼斯",
    "BDI": "布隆迪", "RWA": "卢旺达", "BFA": "布基纳法索", "ZAF": "南非",
}


class GeopoliticsAlertEngine:
    """实时地缘预警引擎：新闻信号 + 载体异动 → 被组合拳瞄准的国家清单"""

    def __init__(self):
        self._last_articles = []

    # ── 新闻抓取 ──────────────────────────────────────────

    def fetch_news(self, hours: int = 48) -> list[dict]:
        """抓取 France24 五区域 + 韩联社国际频道新闻"""
        articles = []
        for name, url in FRANCE24_FEEDS.items():
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    data = resp.read().decode("utf-8", errors="ignore")
                root = ET.fromstring(data)
                for item in root.iter("item"):
                    title = ""
                    desc = ""
                    pub = ""
                    for child in item:
                        tag = child.tag.split("}")[-1]
                        if tag == "title":
                            title = (child.text or "").strip()
                        elif tag == "description":
                            desc = re.sub(r"<[^>]+>", "", child.text or "").strip()
                        elif tag == "pubDate":
                            pub = (child.text or "").strip()
                    if title:
                        articles.append({
                            "title": title,
                            "desc": desc,
                            "pub": pub,
                            "source": f"france24/{name}",
                        })
            except Exception as e:
                print(f"[geopolitics] fetch {name} failed: {e}", file=sys.stderr)
        # 韩联社国际（备用）
        try:
            req = urllib.request.Request(YNA_WORLD, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read().decode("utf-8", errors="ignore")
            root = ET.fromstring(data)
            for item in root.iter("item"):
                title = ""
                for child in item:
                    tag = child.tag.split("}")[-1]
                    if tag == "title":
                        title = (child.text or "").strip()
                if title:
                    articles.append({"title": title, "desc": "", "pub": "", "source": "yna"})
        except Exception as e:
            print(f"[geopolitics] fetch yna failed: {e}", file=sys.stderr)
        self._last_articles = articles
        return articles

    # ── 信号提取 ──────────────────────────────────────────

    def _match_keywords(self, text: str) -> tuple[list, list]:
        """返回 (命中关键词列表, 强关键词列表)"""
        low = text.lower()
        hits = [k for k in RISK_KEYWORDS if k in low]
        strong = [k for k in STRONG_KEYWORDS if k in low]
        return hits, strong

    def _extract_country(self, text: str) -> list[str]:
        """从文本中提取国家 ISO3"""
        low = text.lower()
        found = []
        for name, iso3 in COUNTRY_MAP.items():
            if name in low:
                found.append(iso3)
        # 去重保序
        return list(dict.fromkeys(found))

    # ── 载体异动信号（结合 geo_system 的载体数据）──────────

    def _carrier_signals(self, geo_regime: dict | None = None) -> dict:
        """载体层异动信号：VIX/美元/商品 → 预警加分"""
        signals = {}
        if not geo_regime:
            return signals
        carrier = geo_regime.get("carrier", {})
        vix = carrier.get("vix", {})
        dxy = carrier.get("dxy", {})
        wti = carrier.get("wti", {})
        # VIX 恐慌
        vix_cur = vix.get("current", 15)
        if vix_cur > 35:
            signals["vix"] = {"level": "extreme", "note": f"VIX {vix_cur} 极度恐慌"}
        elif vix_cur > 25:
            signals["vix"] = {"level": "high", "note": f"VIX {vix_cur} 恐慌"}
        elif vix_cur < 15:
            signals["vix"] = {"level": "calm", "note": f"VIX {vix_cur} 平静"}
        # 美元走强（退潮）
        dxy_chg = dxy.get("yoy_change_pct", 0)
        if dxy_chg > 3:
            signals["dxy"] = {"level": "tight", "note": f"美元指数同比+{dxy_chg:.1f}% 走强抽血"}
        elif dxy_chg < -3:
            signals["dxy"] = {"level": "ease", "note": f"美元指数同比{dxy_chg:.1f}% 走弱放水"}
        # 大宗商品暴跌
        wti_chg = wti.get("yoy_change_pct", 0)
        if wti_chg < -15:
            signals["commodity"] = {"level": "crash", "note": f"原油同比{wti_chg:.1f}% 暴跌(资源国承压)"}
        elif wti_chg > 15:
            signals["commodity"] = {"level": "boom", "note": f"原油同比+{wti_chg:.1f}% 上行(产油国受益/进口国承压)"}
        return signals

    # ── 综合预警 ──────────────────────────────────────────

    def run(self, geo_regime: dict | None = None, top_n: int = 8) -> dict:
        """
        综合预警：新闻信号 + 载体异动 → 被瞄准国家清单
        geo_regime: geo_system.GeoSystemEngine.system_regime() 输出（可选）
        """
        articles = self.fetch_news()
        carrier_sig = self._carrier_signals(geo_regime)

        # 1. 新闻按国家聚合
        country_score = {}  # iso3 -> {score, count, articles[]}
        for a in articles:
            text = a["title"] + " " + a["desc"]
            hits, strong = self._match_keywords(text)
            if not hits:
                continue
            iso3s = self._extract_country(text)
            if not iso3s:
                continue
            # 无国家名但强金融词（default/crisis），标记"全球"
            if "global" in text.lower() or "world" in text.lower():
                iso3s.append("GLOBAL")
            base = 1.0 + 2.0 * len(strong) + 0.5 * len(hits)
            for iso3 in iso3s:
                # 新闻中心国（美/法/英）是事件发生地而非承压目标，降权
                if iso3 in ("USA", "FRA", "GBR", "DEU"):
                    if not strong:
                        continue  # 无强信号直接跳过
                    base *= 0.4  # 有强信号也大幅降权
                entry = country_score.setdefault(iso3, {"score": 0.0, "count": 0, "articles": []})
                entry["score"] += base
                entry["count"] += 1
                entry["articles"].append({"title": a["title"], "source": a["source"]})
                entry["articles"] = entry["articles"][:3]

        # 2. 载体异动附加到高外债/脆弱国（用 geo 的脆弱名单若可用）
        #    简化：载体恐慌时整体提高预警烈度
        vix_sig = carrier_sig.get("vix", {})
        if vix_sig.get("level") == "extreme":
            for iso3 in country_score:
                country_score[iso3]["score"] += 3
        elif vix_sig.get("level") == "high":
            for iso3 in country_score:
                country_score[iso3]["score"] += 1.5

        # 3. 排序输出
        ranked = sorted(country_score.items(), key=lambda x: -x[1]["score"])[:top_n]
        result = []
        for iso3, info in ranked:
            result.append({
                "iso3": iso3,
                "name": ISO3_CN.get(iso3, iso3),
                "score": round(info["score"], 1),
                "count": info["count"],
                "articles": info["articles"],
            })

        return {
            "signals": carrier_sig,
            "articles_scanned": len(articles),
            "alerts": result,
            "generated_at": datetime.now().isoformat(),
        }

    # ── 报告 ──────────────────────────────────────────────

    def to_report(self, result: dict, adjust: dict | None = None) -> str:
        lines = [
            "# 🎯 地缘组合拳 · 实时预警",
            "",
            f"> 扫描 {result.get('articles_scanned', 0)} 条新闻 (France24 五区域+韩联社国际)",
            "",
        ]
        # 载体信号
        sig = result.get("signals", {})
        if sig:
            lines.append("## 载体层信号")
            for k, v in sig.items():
                lines.append(f"- {v['note']}")
            lines.append("")
        # 预警清单
        alerts = result.get("alerts", [])
        if not alerts:
            lines.append("## ✅ 当前无高危组合拳目标")
            lines.append("")
            lines.append("> 新闻与载体信号均未出现显著地缘/金融风险共振，系统处于平静期。")
        else:
            lines.append("## 🚨 当前被组合拳瞄准/承压的国家")
            lines.append("")
            for i, a in enumerate(alerts, 1):
                articles = a.get("articles", [])
                art_str = " | ".join(x["title"][:50] for x in articles[:2])
                lines.append(f"{i}. **{a['name']}** ({a['score']}分, {a['count']}条信号)")
                if art_str:
                    lines.append(f"   → {art_str}")
            lines.append("")
        return "\n".join(lines)


if __name__ == "__main__":
    sys.path.insert(0, "/var/www/ai-digital-card/backend/app/ai")
    from time_machine_engine.geo_system import GeoSystemEngine

    gse = GeoSystemEngine()
    regime = gse.system_regime()
    engine = GeopoliticsAlertEngine()
    result = engine.run(geo_regime=regime, top_n=8)
    print(engine.to_report(result))
