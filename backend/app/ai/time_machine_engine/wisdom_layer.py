"""
五千年智慧决策层 (Wisdom Layer) — 2026-08-08 海容要求: 融合中国传统智慧

核心定位: 出海时光机引擎的「决策心法层」—— 引擎负责"知"（全球机会雷达），
智慧层负责"止"（该不该打）与"度"（打到什么程度）。知止合一。

五千年智慧映射（v1, 通用国学核心）:
  道德经·道法术器 → 架构分层（道=美元潮汐规律 / 法=九步法 / 术=投资战术 / 器=引擎工具）
  孙子兵法·先胜后战 → 投资硬规则（不满足先胜条件禁止进场）
  孙子兵法·以正合以奇胜 → 组合策略（正=模式复制稳 / 奇=反周期抄底狠）
  易经·周期律 → 美元周期映射（潜龙勿用→见龙在田→飞龙在天→亢龙有悔）
  中庸·过犹不及 → 风险控制（杠杆/敞口/现金储备）
  商道·人弃我取 → 反周期抄底哲学（危机=机会）

⚠️ 本地母体记忆宫殿有「道德经12原子心智模型」+「国学经典100·137原子总库」，
   本 v1 用通用国学核心实现，架构已留 LOCAL_ATOM_PATH 加载接口——
   本地原子库同步过来后无缝替换（见 _load_local_atoms）。
"""

import json
import os
from datetime import datetime

# 本地母体原子库路径（同步后自动加载，未同步则用内置通用版）
LOCAL_ATOM_PATH = "/var/www/ai-digital-card/knowledge-sync/local/五池/模型池"
LOCAL_DAO_FILE = "2026-05-18_道德经12原子心智模型.md"
LOCAL_GUOXUE_FILE = "2026-05-18_国学经典100_137原子总库.md"

# ── 易经 · 美元周期四态映射 ──
YIJING_CYCLE = {
    "easing": {
        "phase": "见龙在田（初现生机）",
        "hexagram": "䷀ 乾卦·九二",
        "meaning": "美元宽松初期，新兴市场刚露头角——机会初现，可小试牛刀",
        "action": "布局早期高增长市场，仓位3-5成试探",
        "confidence": "中高",
    },
    "turning_easing": {
        "phase": "飞龙在天（利见大人）",
        "hexagram": "䷀ 乾卦·九五",
        "meaning": "紧缩转宽松，潮水涌入——正是大展拳脚之时",
        "action": "加大新兴市场布局，仓位可至7-8成",
        "confidence": "高",
    },
    "turning_tightening": {
        "phase": "亢龙有悔（盈不可久）",
        "hexagram": "䷀ 乾卦·上九",
        "meaning": "转向紧缩，潮水将退——亢奋过头必然后悔",
        "action": "减持脆弱国资产，降杠杆，留足现金",
        "confidence": "高",
    },
    "tightening": {
        "phase": "潜龙勿用（阳气潜藏）",
        "hexagram": "䷀ 乾卦·初九",
        "meaning": "美元紧缩，资本回流——不要轻举妄动",
        "action": "现金为王，聚焦低外债高外储安全市场",
        "confidence": "高",
    },
    "waiting": {
        "phase": "或跃在渊（进可攻退可守）",
        "hexagram": "䷀ 乾卦·九四",
        "meaning": "方向未明，进退自如——保持灵活",
        "action": "正常节奏，关注美联储信号",
        "confidence": "中",
    },
}

# ── 孙子兵法 · 先胜后战硬规则 ──
SUNZI_RULES = {
    "first_win": {
        "name": "先胜后战（孙子·形篇）",
        "rule": "胜兵先胜而后求战，败兵先战而后求胜",
        "enforce": {
            "min_similarity": 0.30,   # 环境相似度 ≥30%
            "max_window_years": 2.5,  # 时滞窗口 ≤2.5年
        },
        "action": "不满足先胜条件 → 禁止进场（最多观察/提前卡位）",
    },
    "zhizhi": {
        "name": "知止不殆（道德经·四十四章）",
        "rule": "知足不辱，知止不殆，可以长久",
        "enforce": {
            "risk_score_max": 70,     # 国家风险分 >70 禁止重仓
            "fear_vix_max": 35,       # VIX >35 恐慌期禁止进攻
        },
        "action": "过线即止——风险超限时主动收手，不赌",
    },
    "zhengqi": {
        "name": "以正合以奇胜（孙子·势篇）",
        "rule": "凡战者，以正合，以奇胜",
        "enforce": {
            "zheng_ratio": 0.7,       # 正（模式复制）占 70%
            "qi_ratio": 0.3,          # 奇（反周期抄底）占 30%
        },
        "action": "正奇结合：稳的基本盘 + 狠的抄底机会",
    },
    "guoyou": {
        "name": "过犹不及（中庸）",
        "rule": "过犹不及，执其两端用其中",
        "enforce": {
            "max_single_country": 0.25,  # 单一国家敞口 ≤25%
            "min_cash_reserve": 0.15,    # 现金储备 ≥15%
        },
        "action": "极端不可取：不all-in单一国家，不空仓踏空",
    },
    "renqiwuqu": {
        "name": "人弃我取（史记·货殖列传）",
        "rule": "人弃我取，人取我与",
        "enforce": {
            "crisis_discount": 0.5,   # 危机后资产可打5折买入
            "wait_years": 2,          # 崩盘后等2年再进
        },
        "action": "危机=别人恐惧我贪婪——反周期抄底窗口",
    },
}

# ── 道德经 · 道法术器四层 ──
DAOFA_SHUSHI = {
    "道": "美元潮汐规律 + 全球系统论（本质层：潮汐+地缘组合拳）",
    "法": "九步法工业化流程 + 先胜后战硬规则",
    "术": "模式复制/反周期抄底/供应链卡位/情报中枢 四大战法",
    "器": "出海时光机引擎 + 中国软银系统 + FRED数据 + 地缘预警",
}


class WisdomLayer:
    """五千年智慧决策层：把国学心法变成可执行的硬规则"""

    def __init__(self):
        self._local_atoms = None
        self._try_load_local()

    def _try_load_local(self):
        """尝试加载本地母体原子库（同步后生效，未同步返回 False）"""
        try:
            daofile = os.path.join(LOCAL_ATOM_PATH, LOCAL_DAO_FILE)
            if os.path.isfile(daofile):
                with open(daofile, "r", encoding="utf-8") as f:
                    content = f.read()
                self._local_atoms = {"dao": content[:3000]}
                return True
        except Exception:
            pass
        return False

    # ── 易经周期映射 ──

    def yijing_phase(self, tide_stage: str) -> dict:
        """美元周期 → 易经卦象"""
        return YIJING_CYCLE.get(tide_stage, YIJING_CYCLE["waiting"])

    # ── 先胜后战校验 ──

    def first_win_check(self, similarity: float, window_years: float | None) -> dict:
        """孙子·先胜后战：满足条件才允许进场"""
        rule = SUNZI_RULES["first_win"]["enforce"]
        ok = similarity >= rule["min_similarity"]
        if window_years is not None:
            ok = ok and window_years <= rule["max_window_years"]
        return {
            "ok": ok,
            "similarity": similarity,
            "window_years": window_years,
            "min_similarity": rule["min_similarity"],
            "max_window_years": rule["max_window_years"],
            "verdict": "✅ 先胜后可战" if ok else "❌ 先胜未足，禁止进场（只观察/卡位）",
        }

    def risk_gate(self, risk_score: float, vix: float) -> dict:
        """道德经·知止：风险超限主动收手"""
        r = SUNZI_RULES["zhizhi"]["enforce"]
        issues = []
        if risk_score > r["risk_score_max"]:
            issues.append(f"国家风险 {risk_score} > {r['risk_score_max']} 禁止重仓")
        if vix > r["fear_vix_max"]:
            issues.append(f"VIX {vix} > {r['fear_vix_max']} 恐慌期禁止进攻")
        return {
            "ok": len(issues) == 0,
            "issues": issues,
            "verdict": "✅ 知止而行" if not issues else "⚠️ " + "；".join(issues),
        }

    def portfolio_advice(self, tide_stage: str, regime: str) -> dict:
        """综合投资组合建议（正奇结合 + 仓位）"""
        yj = self.yijing_phase(tide_stage)
        # 基础仓位：见龙3-5成 / 飞龙7-8成 / 亢龙降杠杆 / 潜龙现金为王
        if tide_stage in ("easing", "turning_easing"):
            position = "6-8成" if tide_stage == "turning_easing" else "4-6成"
        elif tide_stage == "turning_tightening":
            position = "2-3成"
        elif tide_stage == "tightening":
            position = "1-2成"
        else:
            position = "3-5成"
        return {
            "yijing": yj["phase"],
            "hexagram": yj["hexagram"],
            "position": position,
            "zheng_qi": f"正(模式复制)70% + 奇(反周期抄底)30%",
            "cash": "≥15%",
            "action": yj["action"],
        }

    def crisis_opportunity(self, regime: str, alerts: list) -> dict:
        """人弃我取：危机 → 未来抄底清单"""
        if regime in ("harvest_crisis", "harvest"):
            targets = [a.get("name") for a in alerts[:3]]
            return {
                "window": "抄底观察期",
                "strategy": "人弃我取——记录承压国，2年后资产打5折时进场",
                "watchlist": targets,
            }
        return {"window": "非危机期", "strategy": "正常布局，危机清单待更新", "watchlist": []}

    def to_report(self, tide_stage: str, regime: str, risk_score: float,
                  vix: float, alerts: list) -> str:
        """心法层完整报告"""
        yj = self.yijing_phase(tide_stage)
        pa = self.portfolio_advice(tide_stage, regime)
        co = self.crisis_opportunity(regime, alerts)
        lines = [
            "# ☯️ 五千年智慧决策层",
            "",
            "> 道法术器：引擎知机会，智慧定取舍——知止行合一",
            "",
            f"## ① 道法术器",
            f"- 道: {DAOFA_SHUSHI['道']}",
            f"- 法: {DAOFA_SHUSHI['法']}",
            f"- 术: {DAOFA_SHUSHI['术']}",
            f"- 器: {DAOFA_SHUSHI['器']}",
            "",
            f"## ② 易经周期定位: {yj['phase']} {yj['hexagram']}",
            f"- {yj['meaning']}",
            f"- 建议: {yj['action']}",
            "",
            f"## ③ 仓位与组合",
            f"- 建议仓位: {pa['position']}",
            f"- 正奇结合: {pa['zheng_qi']}",
            f"- 现金储备: {pa['cash']}",
            "",
            f"## ④ 先胜后战校验 (国家风险 {risk_score}分 / VIX {vix})",
            f"- 知止: {'✅ 可战' if risk_score <= 70 and vix <= 35 else '⚠️ 触发收手条件'}",
            f"- 人弃我取: {co['strategy']}",
        ]
        if co.get("watchlist"):
            lines.append(f"  - 抄底观察清单: {'、'.join(co['watchlist'])}")
        return "\n".join(lines)


if __name__ == "__main__":
    wl = WisdomLayer()
    print("本地原子库加载:", "✅ 已加载" if wl._local_atoms else "❌ 未同步(用通用版)")
    print(wl.to_report("turning_easing", "pump", 17.6, 15.15,
                       [{"name": "以色列"}, {"name": "伊朗"}, {"name": "俄罗斯"}]))
