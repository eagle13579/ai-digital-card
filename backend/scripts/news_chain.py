#!/usr/bin/env python3
"""
事件链追踪器 (news_chain.py)
=============================
2026-08-08 海容要求：新闻不能只看单条——一条新闻成立后（如刚果金铜矿出口暂停），
后续「铜价创新高」「刚果金恢复出口」「紫金矿业回应」等都要捕捉并挂到同一链条上，
形成纵向时间线演化 → 立体网络的「纵轴」。

核心设计:
  1. 实体提取: 从标题提取实体（国家/商品/产业/公司/宏观因子）→ 事件指纹
  2. 事件链匹配: 新新闻与已有链的指纹 Jaccard 相似度 ≥ 阈值 → 归入该链，否则新建
  3. 链演化: 每条链维护 timeline（时间线），状态机 active→dormant→archived
  4. 持久化: data/time_machine_reports/news_chains.json

用法:
  from news_chain import EventChainTracker
  tracker = EventChainTracker()
  chain_id = tracker.feed({"title": "...", "desc": "...", "ts": "..."})
  tracker.save()
"""

import hashlib
import json
import os
import re
from datetime import datetime, timedelta

REPORT_DIR = "/var/www/ai-digital-card/backend/data/time_machine_reports"
CHAIN_FILE = os.path.join(REPORT_DIR, "news_chains.json")

# ============================================================
# 实体词典：国家/商品/产业/公司/宏观因子 → 事件指纹元素
# ============================================================
ENTITY_COUNTRIES = {
    "刚果金": "刚果金", "刚果": "刚果金", "刚果民主共和国": "刚果金", "congo": "刚果金",
    "智利": "智利", "chile": "智利", "秘鲁": "秘鲁", "peru": "秘鲁",
    "印尼": "印尼", "indonesia": "印尼", "印度尼西亚": "印尼",
    "中国": "中国", "china": "中国", "美国": "美国", "usa": "美国", "us": "美国",
    "日本": "日本", "japan": "日本", "韩国": "韩国", "korea": "韩国", "south korea": "韩国",
    "俄罗斯": "俄罗斯", "russia": "俄罗斯", "乌克兰": "乌克兰", "ukraine": "乌克兰",
    "澳大利亚": "澳大利亚", "australia": "澳大利亚", "巴西": "巴西", "brazil": "巴西",
    "沙特": "沙特", "saudi": "沙特", "伊朗": "伊朗", "iran": "伊朗",
    "阿联酋": "阿联酋", "uae": "阿联酋", "卡塔尔": "卡塔尔", "qatar": "卡塔尔",
    "阿根廷": "阿根廷", "argentina": "阿根廷", "土耳其": "土耳其", "turkey": "土耳其",
    "印度": "印度", "india": "印度", "越南": "越南", "vietnam": "越南",
    "泰国": "泰国", "thailand": "泰国", "马来西亚": "马来西亚", "malaysia": "马来西亚",
    "新加坡": "新加坡", "singapore": "新加坡", "德国": "德国", "germany": "德国",
    "法国": "法国", "france": "法国", "英国": "英国", "uk": "英国", "britain": "英国",
    "墨西哥": "墨西哥", "mexico": "墨西哥", "加拿大": "加拿大", "canada": "加拿大",
    "哈萨克": "哈萨克", "kazakhstan": "哈萨克", "蒙古": "蒙古", "mongolia": "蒙古",
    "波兰": "波兰", "poland": "波兰", "荷兰": "荷兰", "荷兰": "荷兰",
    "台湾": "台湾", "taiwan": "台湾", "香港": "香港", "hong kong": "香港",
}

ENTITY_COMMODITIES = {
    "铜": "铜", "铜价": "铜", "铜矿": "铜", "copper": "铜", "铜精矿": "铜",
    "钴": "钴", "cobalt": "钴", "钴矿": "钴",
    "锂": "锂", "锂矿": "锂", "锂价": "锂", "碳酸锂": "锂", "lithium": "锂",
    "稀土": "稀土", "rare earth": "稀土", "镓": "镓", "锗": "锗",
    "原油": "原油", "石油": "原油", "油价": "原油", "oil": "原油", "wti": "原油", "布伦特": "原油",
    "天然气": "天然气", "gas": "天然气", "lng": "天然气", "液化天然气": "天然气",
    "黄金": "黄金", "金价": "黄金", "gold": "黄金",
    "白银": "白银", "silver": "白银", "银价": "白银",
    "镍": "镍", "nickel": "镍", "锡": "锡", "锌": "锌", "铝": "铝", "钢铁": "钢铁",
    "煤炭": "煤炭", "coal": "煤炭", "铁矿石": "铁矿石", "iron ore": "铁矿石",
    "粮食": "粮食", "小麦": "粮食", "玉米": "粮食", "大豆": "粮食",
    "棉花": "棉花", "cotton": "棉花", "棕榈油": "棕榈油",
    "半导体": "半导体", "semiconductor": "半导体", "芯片": "芯片", "chip": "芯片", "chips": "芯片",
    "存储": "存储", "hbm": "存储", "dram": "存储", "nand": "存储", "闪存": "存储",
    "光伏": "光伏", "solar": "光伏", "多晶硅": "光伏", "硅料": "光伏",
    "电池": "电池", "battery": "电池", "动力电池": "电池",
    "稀土磁材": "稀土", "铀": "铀", "uranium": "铀", "核能": "核能",
}

ENTITY_INDUSTRIES = {
    "AI": "AI", "人工智能": "AI", "artificial intelligence": "AI", "大模型": "AI", "GPT": "AI",
    "机器人": "机器人", "robot": "机器人", "humanoid": "机器人", "人形机器人": "机器人",
    "数据中心": "数据中心", "data center": "数据中心", "算力": "数据中心", "服务器": "数据中心",
    "新能源车": "新能源车", "电动车": "新能源车", "ev": "新能源车", "electric vehicle": "新能源车",
    "汽车": "汽车", "auto": "汽车",
    "光伏产业": "光伏",
    "风电": "风电", "wind": "风电", "核电": "核电", "氢能": "氢能",
    "医药": "医药", "创新药": "医药", "pharma": "医药", "生物医药": "医药",
    "军工": "军工", "defense": "军工", "导弹": "军工", "无人机": "军工", "drones": "军工",
    "卫星": "卫星", "satellite": "卫星", "航天": "卫星",
    "通信": "通信", "5G": "通信", "6G": "通信",
    "光模块": "光模块", "光通信": "光模块", "光芯片": "光模块",
    "PCB": "PCB", "电路板": "PCB", "铜箔": "铜箔",
    "消费电子": "消费电子", "手机": "消费电子", "iphone": "消费电子", "苹果": "消费电子",
    "房地产": "房地产", "楼市": "房地产", "房价": "房地产", "property": "房地产", "real estate": "房地产",
    "电商": "电商", "e-commerce": "电商", "跨境电商": "电商", "直播电商": "电商",
    "白酒": "白酒", "乳业": "乳业", "家电": "家电", "食品": "食品",
    "航运": "航运", "shipping": "航运", "海运": "航运", "集装箱": "航运",
    "造船": "造船", "shipbuilding": "造船", "港口": "港口",
}

ENTITY_COMPANIES = {
    "英伟达": "英伟达", "nvidia": "英伟达", "台积电": "台积电", "tsmc": "台积电",
    "三星": "三星", "samsung": "三星", "SK海力士": "SK海力士", "sk hynix": "SK海力士", "海力士": "SK海力士",
    "中芯国际": "中芯国际", "smic": "中芯国际", "华为": "华为", "huawei": "华为",
    "紫金矿业": "紫金矿业", "洛阳钼业": "洛阳钼业", "铜陵有色": "铜陵有色",
    "北方稀土": "北方稀土", "赣锋锂业": "赣锋锂业", "天齐锂业": "天齐锂业", "华友钴业": "华友钴业",
    "宁德时代": "宁德时代", "catl": "宁德时代", "比亚迪": "比亚迪", "byd": "比亚迪",
    "特斯拉": "特斯拉", "tesla": "特斯拉", "宇树": "宇树", "unitree": "宇树",
    "苹果": "苹果", "apple": "苹果", "微软": "微软", "microsoft": "微软",
    "谷歌": "谷歌", "google": "谷歌", "亚马逊": "亚马逊", "amazon": "亚马逊",
    "OpenAI": "OpenAI", "meta": "Meta", "脸书": "Meta",
    "隆基": "隆基", "通威": "通威", "阳光电源": "阳光电源",
    "中国石油": "中石油", "中石化": "中石化", "沙特阿美": "沙特阿美", "aramco": "沙特阿美",
    "中远海控": "中远海控", "马士基": "马士基", "maersk": "马士基",
}

ENTITY_MACRO = {
    "美联储": "美联储", "fed": "美联储", "federal reserve": "美联储", "鲍威尔": "美联储", "powell": "美联储",
    "加息": "加息", "hike": "加息", "降息": "降息", "cut": "降息", "rate cut": "降息",
    "美元指数": "美元", "dxy": "美元", "美元走强": "美元", "美元走弱": "美元", "dollar": "美元",
    "通胀": "通胀", "inflation": "通胀", "CPI": "通胀", "cpi": "通胀", "PPI": "通胀",
    "非农": "非农", "nonfarm": "非农", "失业率": "非农", "unemployment": "非农",
    "国债": "国债", "收益率": "国债", "yield": "国债", "美债": "国债",
    "关税": "关税", "tariff": "关税", "贸易战": "关税", "贸易摩擦": "关税",
    "制裁": "制裁", "sanction": "制裁", "出口管制": "制裁", "禁售": "制裁", "断供": "制裁",
    "缩表": "缩表", "qt": "缩表", "qe": "QE", "量化宽松": "QE", "流动性": "流动性",
    "VIX": "VIX", "恐慌": "VIX", "避险": "VIX", "risk off": "VIX",
    "地缘": "地缘", "冲突": "地缘", "战争": "地缘", "war": "地缘", "危机": "地缘",
}

ALL_ENTITY_DICTS = [ENTITY_COUNTRIES, ENTITY_COMMODITIES, ENTITY_INDUSTRIES, ENTITY_COMPANIES, ENTITY_MACRO]

# ============================================================
# 事件链状态机
# ============================================================
CHAIN_STATUS = {
    "active": "活跃",      # 3天内有新新闻
    "dormant": "沉睡",     # 3-14天无更新
    "archived": "已归档",  # 14天+无更新
}

MATCH_THRESHOLD = 0.25   # Jaccard 相似度阈值（含宏观因子的链可放宽）
MAX_CHAINS = 200


def extract_entities(text: str) -> set:
    """从文本提取实体集合（国家/商品/产业/公司/宏观因子）
    英文关键词必须词边界匹配（\b），避免 'ai' 撞进 taiwan/said/main 等词
    """
    entities = set()
    if not text:
        return entities
    low = text.lower()
    for d in ALL_ENTITY_DICTS:
        for kw, ent in d.items():
            k = kw.lower()
            # 纯英文关键词 → 词边界匹配；含中文 → 子串匹配
            if re.search(r"^[a-z0-9 ]+$", k):
                if re.search(rf"\b{re.escape(k)}\b", low):
                    entities.add(ent)
            else:
                if k in low:
                    entities.add(ent)
    return entities


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def chain_fingerprint(entities: set, title: str = "") -> str:
    """事件链指纹：实体集合的哈希；空实体用标题哈希（避免空实体全部同链）"""
    if entities:
        return hashlib.md5(",".join(sorted(entities)).encode()).hexdigest()[:16]
    return hashlib.md5(f"title:{title}".encode()).hexdigest()[:16]


class EventChainTracker:
    """事件链追踪器：feed 一条新闻 → 归入已有链 or 新建链"""

    def __init__(self, filepath: str = CHAIN_FILE):
        self.filepath = filepath
        self.chains = []
        self._load()

    def _load(self):
        if os.path.isfile(self.filepath):
            try:
                with open(self.filepath, encoding="utf-8") as f:
                    self.chains = json.load(f)
            except Exception:
                self.chains = []
        if not isinstance(self.chains, list):
            self.chains = []

    def save(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        # 限制链数量
        self.chains = self.chains[:MAX_CHAINS]
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.chains, f, ensure_ascii=False, indent=2)

    # ---------- 查询 ----------
    def _update_status(self, chain: dict, now: datetime):
        """按最后新闻时间更新链状态"""
        try:
            last = datetime.fromisoformat(chain.get("last_ts", chain.get("created_ts", "")))
        except Exception:
            last = now
        days = (now - last).days
        if days >= 14:
            chain["status"] = "archived"
        elif days >= 3:
            chain["status"] = "dormant"
        else:
            chain["status"] = "active"

    def find_chain(self, entities: set, title: str = "") -> dict:
        """找最适合的已有链（Jaccard 相似度 × 聚焦度，最高且 ≥ 阈值）"""
        best, best_score = None, 0.0
        for chain in self.chains:
            chain_ents = set(chain.get("entities", []))
            score = jaccard(entities, chain_ents)
            # 聚焦度因子：链实体越少越聚焦（专链优先），泛链（速递/调研/速览/汇总）降权
            if chain_ents:
                focus = 1.0 / (1.0 + 0.15 * max(len(chain_ents) - 2, 0))
            else:
                focus = 0.8
            chain_title = chain.get("title", "")
            if any(k in chain_title for k in ["速递", "调研", "速览", "汇总", "盘点", "回顾", "直播"]):
                focus *= 0.7
            score_f = score * focus
            # 有宏观因子的链放宽匹配（宏观是背景不是主题）
            has_macro = any(e in chain_ents for e in
                            ["美联储", "加息", "降息", "美元", "通胀", "关税", "制裁"])
            threshold = MATCH_THRESHOLD * 0.6 if has_macro else MATCH_THRESHOLD
            if score_f >= threshold and score_f > best_score:
                best, best_score = chain, score_f
        return best

    def feed(self, news: dict, analysis: dict = None) -> str:
        """
        喂一条新闻 → 归入链/新建链 → 返回 chain_id
        news: {title, desc, link, source, ts}
        analysis: NewsImpactEngine.analyze 结果（可选，存进时间线）
        """
        title = news.get("title", "")
        desc = news.get("desc", "")
        ts = news.get("ts") or datetime.now().isoformat(timespec="seconds")
        entities = extract_entities(f"{title} {desc}")
        chain = self.find_chain(entities, title)

        item = {
            "title": title,
            "ts": ts,
            "source": news.get("source", ""),
            "link": news.get("link", ""),
            "entities": sorted(entities),
            "impact": (analysis or {}).get("detected", {}).get("event_type", "")
                      or (analysis or {}).get("event_type", ""),
            "confidence": (analysis or {}).get("detected", {}).get("confidence", 0)
                         or (analysis or {}).get("confidence", 0),
        }

        if chain is None:
            # 新建链（空实体新闻也建独立链，避免全部塞进同一条）
            chain = {
                "chain_id": chain_fingerprint(entities, title),
                "title": title[:60],
                "entities": sorted(entities),
                "created_ts": ts,
                "last_ts": ts,
                "news_count": 0,
                "status": "active",
                "timeline": [],
                "max_confidence": 0.0,
            }
            self.chains.insert(0, chain)

        chain["timeline"].append(item)
        chain["last_ts"] = ts
        chain["news_count"] = len(chain["timeline"])
        chain["max_confidence"] = max(chain.get("max_confidence", 0), item["confidence"])
        # 更新实体集合（累积）
        merged = set(chain.get("entities", [])) | entities
        chain["entities"] = sorted(merged)
        # 标题用最新/最有信息量的
        if len(item["title"]) > len(chain.get("title", "")):
            chain["title"] = item["title"][:60]
        now = datetime.now()
        self._update_status(chain, now)
        return chain["chain_id"]

    def snapshot(self) -> list:
        """返回当前所有链（按最后更新时间排序）"""
        def _key(c):
            try:
                return datetime.fromisoformat(c.get("last_ts", c.get("created_ts", "")))
            except Exception:
                return datetime.min
        return sorted(self.chains, key=_key, reverse=True)


if __name__ == "__main__":
    # 自测：刚果金铜矿事件链纵向延展
    tracker = EventChainTracker()
    t1 = {"title": "刚果金暂停铜矿出口 铜供给面临收紧", "desc": "刚果民主共和国宣布暂停铜矿出口", "ts": "2026-08-06T10:00:00", "source": "测试"}
    t2 = {"title": "铜价创历史新高 紫金矿业股价大涨", "desc": "受刚果金出口暂停影响，铜价突破新高", "ts": "2026-08-07T14:00:00", "source": "测试"}
    t3 = {"title": "刚果金宣布恢复铜矿出口 铜价回落", "desc": "官方表示谈判达成，铜矿出口恢复", "ts": "2026-08-08T09:00:00", "source": "测试"}
    for t in [t1, t2, t3]:
        cid = tracker.feed(t)
        print(f"→ {t['title'][:30]}  → chain={cid}")
    print("\n快照:")
    for c in tracker.snapshot()[:5]:
        print(f"  [{c['status']}] {c['title'][:40]} | 实体={c['entities']} | {c['news_count']}条")
