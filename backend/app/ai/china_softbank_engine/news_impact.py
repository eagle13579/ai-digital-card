"""
新闻→产业链影响链自动生成引擎 (News Impact Engine)
===================================================
2026-08-08 海容核心需求:
「我以后看到一条新闻，首先会自然地生成一条它背后影响的产业链条，
 然后这个新闻类型相关的一些你就可以推导出来，然后可以去推演和预判。
 这种效果的话你就有预测性的价值，就不光是一个信息，而是一套活的系统」

设计:
  1. 新闻输入（标题+正文）→ 关键词匹配 → 事件类型识别（制裁/涨价/投产/政策/地缘/需求爆发...）
  2. 事件类型 → 冲击环节 + 方向 + 强度（从 51 节点图谱定位）
  3. 产业链影响链生成（SupplyChainEngine.propagate 双向传导）
  4. 群体智能推演（DualLinkEngine.swarm_forecast 多轮演化）
  5. 预测报告（影响链 + 受益/受损标的 + 时间轴 + 置信度）

版本: v1.0.0
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from .supply_chain import CHAIN_GRAPH, EVENT_TEMPLATES, SupplyChainEngine
from .dual_link import DualLinkEngine

# ============================================================
# 新闻关键词 → 事件类型 识别规则
# ============================================================
# 每个规则: 命中关键词 → 事件类型 + 冲击环节 + 方向 + 基础强度
# direction: supply=供给冲击(涨价/受限) / demand=需求爆发(景气)
NEWS_RULES: List[Dict[str, Any]] = [
    # ---- 芯片/科技制裁 ----
    {
        "event_type": "科技制裁/出口管制", "impact_node": "ai_chip", "direction": "supply",
        "strength": 0.8, "policy_weight_scale": 1.3, "window_months": 12,
        "keywords": ["芯片", "半导体", "出口管制", "制裁", "禁售", "断供", "实体清单", "光刻机",
                     "chips", "export control", "sanction", "semiconductor", "nvidia", "tsmc",
                     "芯片管制", "封锁", "围堵", "科技战"],
    },
    # ---- AI 数据中心 ----
    {
        "event_type": "AI算力/数据中心", "impact_node": "data_center", "direction": "demand",
        "strength": 0.8, "policy_weight_scale": 1.0, "window_months": 24,
        "keywords": ["AI", "人工智能", "数据中心", "算力", "大模型", "GPT", "云计算", "服务器",
                     "资本开支", "capex", "data center", "artificial intelligence", "cloud",
                     "英伟达订单", "算力需求", "智能算力"],
    },
    # ---- 铜价 ----
    {
        "event_type": "铜价/资源涨价", "impact_node": "copper", "direction": "supply",
        "strength": 0.7, "policy_weight_scale": 1.0, "window_months": 18,
        "keywords": ["铜价", "铜矿", "铜供给", "铜库存", "copper", "铜需求", "电解铜", "铜箔涨价"],
    },
    # ---- 稀土管制 ----
    {
        "event_type": "稀土/稀有金属管制", "impact_node": "rare_metal", "direction": "supply",
        "strength": 0.75, "policy_weight_scale": 1.2, "window_months": 12,
        "keywords": ["稀土", "稀有金属", "锂矿", "钴", "镍", "出口配额", "rare earth", "lithium",
                     "锂价", "碳酸锂", "锂电材料", "资源管制"],
    },
    # ---- 新能源车 ----
    {
        "event_type": "新能源车景气", "impact_node": "ev", "direction": "demand",
        "strength": 0.6, "policy_weight_scale": 1.0, "window_months": 36,
        "keywords": ["新能源车", "电动车", "渗透率", "汽车销量", "ev", "electric vehicle",
                     "电池装机", "动力电池", "充电桩", "车企"],
    },
    # ---- 光伏 ----
    {
        "event_type": "光伏景气/装机", "impact_node": "solar", "direction": "demand",
        "strength": 0.6, "policy_weight_scale": 1.0, "window_months": 24,
        "keywords": ["光伏", "装机", "组件", "光伏玻璃", "逆变器", "solar", "硅料", "硅片",
                     "新能源装机", "绿电"],
    },
    # ---- 石油/能源 ----
    {
        "event_type": "能源/油价", "impact_node": "oil_gas", "direction": "supply",
        "strength": 0.7, "policy_weight_scale": 1.1, "window_months": 12,
        "keywords": ["油价", "石油", "原油", "OPEC", "能源危机", "天然气", "oil", "energy",
                     "页岩油", "俄油", "制裁俄罗斯"],
    },
    # ---- 地缘冲突 ----
    {
        "event_type": "地缘冲突", "impact_node": "gold", "direction": "demand",
        "strength": 0.7, "policy_weight_scale": 1.3, "window_months": 12,
        "keywords": ["战争", "冲突", "导弹", "军事", "霍尔木兹", "war", "conflict", "military",
                     "台海", "半岛", "中东", "黑海", "地缘"],
    },
    # ---- 军工 ----
    {
        "event_type": "军工订单", "impact_node": "defense", "direction": "demand",
        "strength": 0.6, "policy_weight_scale": 1.0, "window_months": 18,
        "keywords": ["军工", "国防预算", "军费", "导弹订单", "战斗机", "defense", "military budget"],
    },
    # ---- 存储 ----
    {
        "event_type": "存储涨价/存储周期", "impact_node": "memory", "direction": "supply",
        "strength": 0.65, "policy_weight_scale": 1.1, "window_months": 12,
        "keywords": ["存储", "DRAM", "HBM", "内存涨价", "NAND", "memory", "存储芯片",
                     "美光", "三星存储", "海力士"],
    },
    # ---- 医药 ----
    {
        "event_type": "医药政策/创新药", "impact_node": "innov_drug", "direction": "demand",
        "strength": 0.55, "policy_weight_scale": 1.0, "window_months": 24,
        "keywords": ["创新药", "医药集采", "医保", "FDA", "临床", "药企", "biotech",
                     "药品审批", "license out"],
    },
    # ---- 人形机器人 ----
    {
        "event_type": "机器人产业", "impact_node": "robot", "direction": "demand",
        "strength": 0.6, "policy_weight_scale": 1.0, "window_months": 24,
        "keywords": ["机器人", "人形机器人", "具身智能", "robot", "humanoid", "宇树", "优必选",
                     "灵巧手", "减速器", "伺服"],
    },
    # ---- 美联储/降息 ----
    {
        "event_type": "美联储/利率", "impact_node": "copper", "direction": "demand",
        "strength": 0.5, "policy_weight_scale": 1.2, "window_months": 18,
        "keywords": ["美联储", "降息", "加息", "利率", "FED", "fed", "鲍威尔", "通胀",
                     "货币政策", "QT", "QE"],
    },
    # ---- 白酒/消费 ----
    {
        "event_type": "消费/白酒", "impact_node": "white_wine", "direction": "demand",
        "strength": 0.5, "policy_weight_scale": 0.8, "window_months": 24,
        "keywords": ["白酒", "消费", "零售", "社零", "消费复苏", "白酒提价", "宴席", "消费降级"],
    },
]

# 默认兜底规则
DEFAULT_RULE = {
    "event_type": "综合产业动态", "impact_node": "ai_chip", "direction": "demand",
    "strength": 0.5, "policy_weight_scale": 1.0, "window_months": 12,
    "keywords": [],
}


class NewsImpactEngine:
    """新闻 → 产业链影响链 → 推演预判"""

    def __init__(self):
        self.sce = SupplyChainEngine()
        self.dle = DualLinkEngine()

    # ---------- 1. 事件识别 ----------
    def detect_event(self, text: str) -> Dict[str, Any]:
        """关键词匹配 → 事件类型 + 冲击环节 + 强度（多规则命中取最强）"""
        text_lower = text.lower()
        best = None
        best_score = 0
        for rule in NEWS_RULES:
            hits = [kw for kw in rule["keywords"] if kw.lower() in text_lower]
            if hits:
                # 命中数 × 关键词权重 → 匹配置信
                score = len(hits) * 0.5
                # 核心词（前3个）额外加权
                core_hits = [kw for kw in rule["keywords"][:3] if kw.lower() in text_lower]
                score += len(core_hits) * 0.3
                if score > best_score:
                    best_score = score
                    best = dict(rule)
                    best["matched_keywords"] = hits[:8]
                    best["confidence"] = min(0.95, 0.4 + score * 0.08)
        if best is None:
            best = dict(DEFAULT_RULE)
            best["matched_keywords"] = []
            best["confidence"] = 0.25
        return best

    # ---------- 2. 新闻 → 完整影响链推演 ----------
    def analyze(self, title: str, body: str = "") -> Dict[str, Any]:
        """核心入口：新闻 → 影响链 + 群体智能预判 + 报告"""
        text = f"{title} {body}"
        ev = self.detect_event(text)
        if ev["impact_node"] not in CHAIN_GRAPH:
            ev["impact_node"] = "ai_chip"

        event = {
            "id": f"news_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": f"新闻事件: {title[:30]}",
            "description": f"识别类型「{ev['event_type']}」，命中关键词: {', '.join(ev['matched_keywords'][:5]) or '综合兜底'}",
            "impact_node": ev["impact_node"],
            "direction": ev["direction"],
            "strength": ev["strength"],
            "policy_weight_scale": ev["policy_weight_scale"],
            "window_months": ev["window_months"],
        }

        # 影响链（双向传导）
        propagation = self.sce.propagate(event)
        # 群体智能预判（MiroFish）
        swarm = self.dle.swarm_forecast(event)
        # 机会清单
        opportunities = self.sce.extract_opportunities(event, top_n=8)
        # 时间轴
        forecast = self.sce.forecast(event)

        return {
            "title": title,
            "body": body[:200],
            "detected": {
                "event_type": ev["event_type"],
                "impact_node": CHAIN_GRAPH[ev["impact_node"]]["name"],
                "direction": "供给冲击" if ev["direction"] == "supply" else "需求爆发",
                "confidence": round(ev["confidence"], 2),
                "matched_keywords": ev["matched_keywords"],
            },
            "event": event,
            "propagation": propagation,
            "swarm": swarm,
            "opportunities": opportunities,
            "forecast": forecast,
            "generated_at": datetime.now().isoformat(),
        }

    # ---------- 3. 报告 ----------
    def to_report(self, result: Dict[str, Any]) -> str:
        det = result.get("detected") or {}
        prop = result.get("propagation") or {}
        swarm = result.get("swarm") or {}
        opps = result.get("opportunities") or []
        fc = result.get("forecast") or {}

        lines = [
            "## 📰 新闻 → 产业链影响链推演",
            "",
            f"**新闻**: {result.get('title', '')}",
            f"**识别**: {det.get('event_type')} → 冲击 **{det.get('impact_node')}**（{det.get('direction')}）",
            f"**置信度**: {det.get('confidence') * 100:.0f}% | 命中: {', '.join(det.get('matched_keywords') or []) or '综合兜底'}",
            "",
            "### 🔗 产业链影响链（双向传导）",
            "",
            "| 环节 | 方向 | 冲击分 | 传导路径 | 代表公司 |",
            "|:-----|:-----|:------|:---------|:---------|",
        ]
        for r in (prop.get("results") or [])[:10]:
            comps = " / ".join(c["name"] for c in r.get("companies", [])[:2])
            lines.append(f"| {r.get('name')} | {r.get('direction')} | {r.get('score')} | {'→'.join(r.get('path', [])[-3:])} | {comps} |")

        lines.append("")
        lines.append("### 🧠 群体智能预判（多环节智能体演化）")
        lines.append("")
        lines.append("| 环节 | 预判 | 价格压力 | 需求 | 供给 | 情绪 | 代表公司 |")
        lines.append("|:-----|:-----|:--------|:-----|:-----|:-----|:---------|")
        for r in (swarm.get("results") or [])[:10]:
            comps = " / ".join(c["name"] for c in r.get("companies", [])[:2])
            lines.append(f"| {r.get('name')} | {r.get('label')} | {r.get('price_pressure', 0):.2f} | {r.get('demand_change', 0):+.2f} | {r.get('supply_change', 0):+.2f} | {r.get('sentiment', 0):+.2f} | {comps} |")

        if opps:
            lines.append("")
            lines.append("### 🎯 机会清单（受益标的 Top）")
            for o in opps[:6]:
                lines.append(f"- 🎯 {o.get('company')}({o.get('ticker')}) — {o.get('node')} 冲击分{o.get('score')} | {o.get('path')}")

        lines.append("")
        lines.append("### ⏱️ 预测时间轴")
        for ph in (fc.get("phases") or []):
            lines.append(f"- {ph.get('phase')}: {ph.get('desc')}")

        return "\n".join(lines)


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    eng = NewsImpactEngine()
    test_news = [
        ("美国商务部宣布对华芯片出口新管制，光刻机列入禁售清单",
         "美国政府最新宣布扩大对华半导体出口管制范围，先进制程光刻机及EDA软件列入禁售，多家中国芯片企业面临断供风险"),
        ("全球AI资本开支爆发，微软谷歌宣布千亿级数据中心投资",
         "微软和谷歌先后宣布未来两年将投入超千亿美元建设AI数据中心，GPU服务器订单激增，光模块需求旺盛"),
        ("新能源汽车渗透率突破50%，动力电池产业链景气上行",
         "最新数据显示国内新能源车渗透率突破50%，动力电池排产环比大增，碳酸锂价格企稳回升"),
    ]
    for t, b in test_news:
        print("=" * 70)
        r = eng.analyze(t, b)
        print(eng.to_report(r)[:1200])
        print()
