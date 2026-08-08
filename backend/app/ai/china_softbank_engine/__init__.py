"""
中国软银投资引擎 (China SoftBank Investment Engine) — 2026-08-08 海容架构升级

架构定位（海容定义，2026-08-08）：
┌─────────────────────────────────────────────────────┐
│  中国软银投资模型（整体概念层）                          │
│  ├─ 前端: 中国软银投资系统（:8310 投资决策前端）          │
│  └─ 后端: 中国软银投资引擎（本包 = 决策大脑）             │
│      ├─ 出海时光机引擎（独立产品模块，可嵌入任何项目）      │
│      │   └─ /app/ai/time_machine_engine/               │
│      ├─ 美元潮汐收割剧本（五幕式打法）                    │
│      ├─ 科技战维度（美国收割主赛道）                      │
│      ├─ 反周期观察清单（跟美国资本同牌桌）                │
│      ├─ 五千年智慧决策层（心法/风控）                     │
│      └─ 全球机会雷达（前端可视化数据）                    │
└─────────────────────────────────────────────────────┘

核心原则（海容强调）：
1. 出海时光机引擎 = 独立产品，未来切入中韩出海数智港等任何项目 —— 本包只引用它，不修改它
2. 中国软银投资引擎 = 聚合/升级层，把出海时光机 + 后续补充模块组装成「中国软银自己的引擎」
3. 对外统一命名「中国软银投资引擎」，避免「用起来穿帮」（别人看到的是中国软银，不是出海时光机）

本聚合层职责：
- 统一入口: run() 一键聚合所有子引擎（时光机/潮汐/科技/观察/智慧/雷达）
- 对外 API: 中国软银投资系统 (:8310) 直接调用本包，不再散调 time_machine_engine
- 组合决策: 正奇结合（正=模式复制基金 / 奇=反周期抄底基金）
"""

import sys
import os
import json
from datetime import datetime

# 让子模块可独立 import（不依赖 app 包初始化）
_APP_AI = os.path.join(os.path.dirname(__file__), "..")
if _APP_AI not in sys.path:
    sys.path.insert(0, _APP_AI)

VERSION = "1.0.0"
ENGINE_NAME = "中国软银投资引擎 (China SoftBank Investment Engine)"

REPORT_DIR = "/var/www/ai-digital-card/backend/data/china_softbank_reports"
WATCHLIST_JSON = "/var/www/ai-digital-card/backend/data/time_machine_reports/contrarian_watchlist.json"
WATCHLIST_MD = "/var/www/ai-digital-card/backend/data/time_machine_reports/contrarian_watchlist_latest.md"


class ChinaSoftBankEngine:
    """中国软银投资引擎：聚合出海时光机 + 潮汐 + 科技 + 观察清单 + 智慧层"""

    def __init__(self):
        self.name = ENGINE_NAME
        self.version = VERSION
        self._dte = None
        self._gse = None
        self._rwe = None

    # ── 子引擎懒加载 ──────────────────────────────────────

    def _dollar_tide(self):
        if self._dte is None:
            from time_machine_engine.dollar_tide import DollarTideEngine
            self._dte = DollarTideEngine()
        return self._dte

    def _geo_system(self):
        if self._gse is None:
            from time_machine_engine.geo_system import GeoSystemEngine
            self._gse = GeoSystemEngine()
        return self._gse

    def _risk_warning(self):
        if self._rwe is None:
            from time_machine_engine.risk_warning import RiskWarningEngine
            self._rwe = RiskWarningEngine()
        return self._rwe

    # ── 统一决策入口 ──────────────────────────────────────

    def run(self, refresh_watchlist: bool = False) -> dict:
        """
        一键聚合所有子引擎 → 中国软银统一决策数据
        """
        result = {
            "engine": self.name,
            "engine_version": self.version,
            "generated_at": datetime.now().isoformat(),
        }

        # 1. 美元潮汐（收割剧本定位）
        try:
            cyc = self._dollar_tide().cycle_stage() or {}
            act_map = {
                "easing": "第一幕：潮水涌出（布局窗口）",
                "turning_easing": "第一幕→第二幕过渡（最后布局期）",
                "waiting": "第二幕：信号切换（诱多期）",
                "turning_tightening": "第三幕前奏：组合拳预备",
                "tightening": "第三幕：加息抽血（收割期）",
            }
            result["tide"] = {
                "stage": cyc.get("stage"),
                "act": act_map.get(cyc.get("stage"), "未知幕"),
                "reason": str(cyc.get("reason", ""))[:100],
            }
        except Exception as e:
            result["tide"] = {"error": str(e)}

        # 2. 全球系统阶段 + 载体
        try:
            regime = self._geo_system().system_regime(self._dollar_tide().cycle_stage())
            carrier = regime.get("carrier") or {}
            result["system"] = {
                "regime": regime.get("regime"),
                "fear": regime.get("fear"),
                "hint": regime.get("regime_hint"),
                "vix": regime.get("vix_current"),
                "carrier": {k: v.get("current") for k, v in carrier.items()},
            }
        except Exception as e:
            result["system"] = {"error": str(e)}

        # 3. 科技战维度
        try:
            from time_machine_engine.tech_warfare import TechWarfareEngine
            tw = TechWarfareEngine().run()
            result["tech_warfare"] = {
                "regime": tw.get("regime", {}).get("label"),
                "score": tw.get("regime", {}).get("score"),
                "window": tw.get("opportunity", {}).get("window"),
                "nasdaq": tw.get("nasdaq", {}).get("bubble"),
            }
        except Exception as e:
            result["tech_warfare"] = {"error": str(e)}

        # 4. 反周期观察清单（猎物池）
        try:
            if refresh_watchlist or not os.path.exists(WATCHLIST_JSON):
                os.makedirs(os.path.dirname(WATCHLIST_JSON), exist_ok=True)
                import subprocess
                subprocess.run(
                    [sys.executable, "/var/www/ai-digital-card/backend/scripts/contrarian_watchlist.py"],
                    capture_output=True, timeout=300)
            with open(WATCHLIST_JSON, encoding="utf-8") as f:
                wl = json.load(f)
            result["watchlist"] = {
                "prey_pool": wl.get("prey_pool", []),
                "trigger": wl.get("trigger", {}),
                "generated_at": wl.get("generated_at"),
            }
        except Exception as e:
            result["watchlist"] = {"error": str(e)}

        # 4.5 套利模式匹配（2026-08-08 融合：猎物池国家 → 适用套利模式警示）
        try:
            from china_softbank_engine.arbitrage_patterns import load_patterns
            from time_machine_engine.risk_warning import RiskWarningEngine
            all_patterns = load_patterns()
            # 按猎物池国家匹配宏观/规则模式
            prey = (result.get("watchlist") or {}).get("prey_pool") or []
            matched = []
            for p in all_patterns:
                p_type = p.get("type", "")
                if p_type in ("macro_harvest", "rule_gap"):
                    # 宏观模式对脆弱国普遍适用，记录适用提示
                    matched.append({"id": p["id"], "name": p["name"],
                                    "type": p_type,
                                    "apply_hint": f"猎物池{len(prey)}国可走此路径",
                                    "insight": p.get("arbitrage_insight", [])[:2]})
            # 离岸风险因子（对标的做尽调时用）
            rwe = RiskWarningEngine()
            offshore_demo = rwe.offshore_risk({
                "offshore_ratio": 0.35, "structure": "offshore",
                "audit": "concentrated", "agent_model": "registered",
                "related_party": 0.3})
            result["arbitrage_patterns"] = {
                "total": len(all_patterns),
                "matched": matched,
                "offshore_risk_demo": offshore_demo,
                "offshore_note": "对具体标的尽调时用 offshore_risk() 评估（离岸占比/函证集中度/注册代理人）",
            }
        except Exception as e:
            result["arbitrage_patterns"] = {"error": str(e)}

        # 5. 五千年智慧（心法）
        try:
            from time_machine_engine.wisdom_layer import WisdomLayer
            wl_layer = WisdomLayer()
            cyc = self._dollar_tide().cycle_stage() or {}
            regime = self._geo_system().system_regime(cyc)
            result["wisdom"] = {
                "yijing": wl_layer.yijing_phase(cyc.get("stage", "")),
                "portfolio": wl_layer.portfolio_advice(cyc.get("stage", ""), regime.get("regime", "")),
            }
        except Exception as e:
            result["wisdom"] = {"error": str(e)}

        # 6. 加密货币/黄金套利（2026-08-08 方向3：美元退潮另类资产）
        try:
            from time_machine_engine.crypto_metals import CryptoMetalsEngine
            cme = CryptoMetalsEngine()
            tide_stage = (result.get("tide") or {}).get("stage")
            result["crypto_metals"] = cme.assess(dollar_stage=tide_stage)
        except Exception as e:
            result["crypto_metals"] = {"error": str(e)}

        # 7. 出海时光机（模式复制机会 Top）—— 轻量：读最近报告，不跑全量 run()
        try:
            import glob
            tm_reports = sorted(
                glob.glob("/var/www/ai-digital-card/backend/data/time_machine_reports/time_machine_v3_*.md"),
                reverse=True)
            if tm_reports:
                with open(tm_reports[0], encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                import re
                # 投资决策清单机会表格式: | 🔥 | 模式 | 国家 | 相似度 | ...
                opps = re.findall(r'^\|\s*(?:🔥|⏳|👀)\s*\|[^|]*\|\s*([^|]+?)\s*\|', content, re.M)
                tm_count = len(opps)
                result["time_machine"] = {
                    "sub_engine": "出海时光机引擎（最近报告快照）",
                    "report": os.path.basename(tm_reports[0]),
                    "opportunity_count": tm_count,
                }
            else:
                result["time_machine"] = {"note": "暂无时光机报告（周报生成后自动填充）"}
        except Exception as e:
            result["time_machine"] = {"error": str(e)}

        return result

    # ── 中国软银统一决策报告 ──────────────────────────────

    def to_report(self, data: dict) -> str:
        lines = ["# 🏦 中国软银投资引擎 · 综合决策报告", ""]
        lines.append(f"- 引擎: {self.name} v{self.version}")
        lines.append(f"- 时间: {data.get('generated_at', '')[:19]}")
        lines.append(f"- 组成: 出海时光机(子引擎) + 美元潮汐剧本 + 科技战 + 反周期观察清单 + 五千年智慧")
        lines.append("")

        tide = data.get("tide") or {}
        lines.append("## 🌊 美元潮汐（收割剧本）")
        if tide.get("stage"):
            lines.append(f"- 潮汐: **{tide.get('stage')}** → {tide.get('act')}")
            lines.append(f"- 依据: {tide.get('reason')}")
        else:
            lines.append(f"- ⚠️ {tide.get('error')}")
        lines.append("")

        sys_ = data.get("system") or {}
        lines.append("## 🌍 全球系统阶段")
        if sys_.get("regime"):
            carrier = sys_.get("carrier") or {}
            lines.append(f"- 阶段: **{sys_.get('regime')}** (VIX {sys_.get('vix')} · {sys_.get('hint')})")
            lines.append(f"- 载体: " + " · ".join(
                f"{k}={v}" for k, v in carrier.items() if v is not None))
        else:
            lines.append(f"- ⚠️ {sys_.get('error')}")
        lines.append("")

        tw = data.get("tech_warfare") or {}
        lines.append("## 🛰️ 科技战维度")
        if tw.get("regime"):
            lines.append(f"- 阶段: **{tw.get('regime')}** (信号分 {tw.get('score')})")
            lines.append(f"- 窗口: {tw.get('window')}")
            if tw.get("nasdaq"):
                lines.append(f"- NASDAQ: {tw.get('nasdaq')}")
        else:
            lines.append(f"- ⚠️ {tw.get('error')}")
        lines.append("")

        wl = data.get("watchlist") or {}
        lines.append("## 🎯 反周期观察清单")
        if wl.get("prey_pool"):
            lines.append(f"- 猎物池: **{len(wl.get('prey_pool', []))} 国** 进入观察")
            top = ", ".join(f"{p.get('country')}({p.get('score', 0):.0f})" for p in wl.get("prey_pool", [])[:8])
            lines.append(f"- 脆弱 Top: {top}")
            trig = wl.get("trigger") or {}
            if trig.get("vix_threshold"):
                lines.append(f"- 抄底触发器: VIX>{trig.get('vix_threshold')} / 美元转强 / 地缘打击 / 贵金属异动")
        else:
            lines.append(f"- ⚠️ {wl.get('error')}")
        lines.append("")

        ap = data.get("arbitrage_patterns") or {}
        lines.append("## 🧩 套利模式（融合警示）")
        if ap.get("matched"):
            lines.append(f"- 模式库: {ap.get('total')} 个模式，{len(ap.get('matched', []))} 个适用于当前猎物池")
            for m in ap.get("matched", []):
                ins = "；".join(m.get("insight", []))
                lines.append(f"  - **{m.get('name')}** — {ins}")
        else:
            lines.append(f"- ⚠️ {ap.get('error')}")
        lines.append("")

        wd = data.get("wisdom") or {}
        lines.append("## ☯️ 五千年智慧（心法）")
        if wd.get("yijing"):
            yj = wd.get("yijing") or {}
            pf = wd.get("portfolio") or {}
            lines.append(f"- 易经: **{yj.get('phase')}** ({yj.get('hexagram')}) → {yj.get('action')}")
            if pf.get("position"):
                lines.append(f"- 组合: 仓位 {pf.get('position')} · 正奇 {pf.get('zheng_qi')} · 现金 {pf.get('cash')}")
        else:
            lines.append(f"- ⚠️ {wd.get('error')}")
        lines.append("")

        tm = data.get("time_machine") or {}
        lines.append("## 🚀 出海时光机（子引擎：模式复制机会）")
        if tm.get("sub_engine"):
            lines.append(f"- 子引擎: {tm.get('sub_engine')}")
            if tm.get("opportunity_count") is not None:
                lines.append(f"- 机会池: {tm.get('opportunity_count')} 条（来自最近报告 {tm.get('report')}）")
        elif tm.get("note"):
            lines.append(f"- {tm.get('note')}")
        else:
            lines.append(f"- ⚠️ {tm.get('error')}")
        lines.append("")

        cm = data.get("crypto_metals") or {}
        lines.append("## 💎 加密货币/黄金套利（另类资产）")
        if cm.get("window"):
            from time_machine_engine.crypto_metals import CryptoMetalsEngine
            lines.append(CryptoMetalsEngine().to_report(cm))
        else:
            lines.append(f"- ⚠️ {cm.get('error')}")
        lines.append("")

        lines.append("---")
        lines.append("*中国软银投资引擎 · 聚合决策 | 出海时光机为独立子模块 | 不构成投资建议*")
        return "\n".join(lines)

    def save_report(self, data: dict) -> str:
        import os as _os
        _os.makedirs(REPORT_DIR, exist_ok=True)
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"{REPORT_DIR}/china_softbank_report_{now}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_report(data))
        return path


if __name__ == "__main__":
    eng = ChinaSoftBankEngine()
    data = eng.run(refresh_watchlist=False)
    print(eng.to_report(data))
    path = eng.save_report(data)
    print(f"\n✅ 报告已保存: {path}")
