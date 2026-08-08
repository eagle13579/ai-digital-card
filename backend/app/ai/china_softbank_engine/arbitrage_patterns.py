"""
中国软银套利模式库 (Arbitrage Pattern Library) — 2026-08-08 海容指示建立

从「黑盒调查局」「笨嘴哥财经」等财经深度内容提炼的高级套利/规则模式，
融合进中国软银投资引擎（风险识别 + 机会发现 + 尽调指南）。

模式类型：
  - macro_harvest: 宏观收割（美元潮汐/科技战/组合拳）— 笨嘴哥财经
  - micro_arbitrage: 微观套利/舞弊识别（离岸函证/规则盲区）— 黑盒调查局
  - rule_gap: 规则博弈（审计准则/监管盲区/制度套利）

用法：
  from china_softbank_engine.arbitrage_patterns import load_patterns, match_patterns
  patterns = load_patterns()              # 全部已归档模式
  hits = match_patterns(target)           # 按标的信息匹配适用模式
"""

import os
import json
from datetime import datetime

PATTERNS_FILE = "/var/www/ai-digital-card/backend/data/time_machine_reports/arbitrage_patterns.json"

# ── 内置模式库（初始种子 + 黑盒调查局第1集）──
BUILTIN_PATTERNS = [
    {
        "id": "pattern-001",
        "name": "离岸函证盲区套利",
        "type": "micro_arbitrage",
        "source_account": "黑盒调查局",
        "source_series": "深水区·第二幕·特许控盘",
        "source_episode": 4,
        "source_url": "https://v.douyin.com/WPF-lrFAVdU/",
        "captured_at": "2026-08-08",
        "case": "帕玛拉特财务舞弊案",
        "mechanism": "利用离岸信路的物理盲区：仅靠剪刀/胶水/传真机伪造银行回函，完成对国际审计机构的形式合规收割",
        "key_links": [
            "注册代理人法定免责边界（不承担实质核验义务）",
            "审计流程形式合规惰性（函证发出即视为已核查）",
            "自发自证闭环：离岸空壳→伪造存款证明→函证回函欺瞒",
        ],
        "industry_impact": "直接推动 ISA 505 审计准则重构（外部函证独立性要求）",
        "arbitrage_insight": [
            "尽调必须验证对方是否在自证——离岸架构标的的审计函证不可尽信",
            "识别审计盲区型风险：大量离岸子公司+函证集中=红旗",
            "独立第三方核实离岸实体财务确认，不依赖注册代理人回函",
        ],
        "engine_fusion": "风险引擎新增离岸架构风险因子（离岸子公司占比/函证集中度/注册代理人模式）",
        "confidence": 0.80,
    },
    {
        "id": "pattern-000",
        "name": "美元潮汐五幕收割",
        "type": "macro_harvest",
        "source_account": "笨嘴哥财经",
        "source_series": "金融战火再起",
        "source_episode": "1-6",
        "source_url": "https://v.douyin.com/BYVbxbdKtxs/",
        "captured_at": "2026-08-08",
        "case": "15场历史危机验证",
        "mechanism": "潮涌→加息→组合拳(军事/科技/金融/信息)→目标国崩盘→美元回流抄底→循环",
        "key_links": [
            "降息放水潮涌，美国资本低价建仓",
            "加息抽血+科技封锁+地缘打击共振",
            "恐慌(VIX)是资本回流燃料",
        ],
        "industry_impact": "反周期观察清单+收割信号触发器已接入引擎",
        "arbitrage_insight": [
            "跟美国资本同牌桌：提前锁定脆弱国优质资产，退潮期抄底",
            "科技战=国产替代催化剂窗口",
        ],
        "engine_fusion": "已接入：dollar_tide + tech_warfare + contrarian_watchlist",
        "confidence": 0.90,
    },
]


def load_patterns() -> list[dict]:
    """加载套利模式库（优先读 JSON 文件，否则用内置）"""
    if os.path.exists(PATTERNS_FILE):
        try:
            with open(PATTERNS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("patterns", BUILTIN_PATTERNS)
        except Exception:
            pass
    return BUILTIN_PATTERNS


def save_pattern(pattern: dict) -> bool:
    """新增/更新一个套利模式"""
    patterns = load_patterns()
    for i, p in enumerate(patterns):
        if p["id"] == pattern["id"]:
            patterns[i] = pattern
            break
    else:
        patterns.append(pattern)
    with open(PATTERNS_FILE, "w", encoding="utf-8") as f:
        json.dump({"updated_at": datetime.now().isoformat(),
                   "count": len(patterns), "patterns": patterns},
                  f, ensure_ascii=False, indent=2)
    return True


def match_patterns(target: dict) -> list[dict]:
    """按标的信息匹配适用套利模式

    target: {"country": "...", "industry": "...", "structure": "...", "offshore_ratio": 0.3}
    """
    patterns = load_patterns()
    hits = []
    for p in patterns:
        score = 0
        reasons = []
        t = p["type"]
        # 宏观收割模式：任何新兴市场标的都可能适用（尤其脆弱国）
        if t == "macro_harvest" and target.get("country"):
            score += 1
            reasons.append("宏观收割剧本适用")
        # 微观套利：离岸架构相关
        if t == "micro_arbitrage":
            if target.get("offshore_ratio", 0) > 0.2:
                score += 2
                reasons.append(f"离岸子公司占比{target.get('offshore_ratio', 0):.0%}")
            if target.get("structure") in ("offshore", "trust", "shell"):
                score += 2
                reasons.append(f"离岸结构({target.get('structure')})")
            if target.get("audit") == "concentrated":
                score += 1
                reasons.append("审计函证集中")
        if score > 0:
            hits.append({**p, "match_score": score, "match_reasons": reasons})
    hits.sort(key=lambda x: x["match_score"], reverse=True)
    return hits


if __name__ == "__main__":
    patterns = load_patterns()
    print(f"套利模式库: {len(patterns)} 个模式")
    for p in patterns:
        print(f"  [{p['id']}] {p['name']} ({p['type']}) 来自 {p['source_account']} 置信度{p['confidence']:.0%}")
    print("\n--- 匹配测试 ---")
    test = {"country": "埃及", "structure": "offshore", "offshore_ratio": 0.35, "audit": "concentrated"}
    for h in match_patterns(test):
        print(f"  {h['name']} (匹配分{h['match_score']}): {h['match_reasons']}")
