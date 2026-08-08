"""
出海时光机引擎 v3 — 美元潮汐引擎（Dollar Tide Engine）
=========================================================
全球经济的总钥匙（海容 2026-08-08 指导）：
  每一次金融危机都踩在美元周期的节拍上。

核心机制（Dollar Tide Theory）：
  🔽 美联储降息（宽松潮）→ 美元走弱 → 资本涌向新兴市场
     → 新兴市场繁荣（借便宜美元扩产/炒资产）→ 外债累积 + 资产泡沫
  🔼 美联储加息（紧缩潮）→ 美元走强 → 资本回流美国
     → 新兴市场外储流失 + 本币贬值 + 偿债压力 → 脆弱国崩盘

历史铁证:
  1980-82 沃尔克暴力加息 → 拉美债务危机（墨西哥违约）
  1994-95 加息+强美元     → 墨西哥比索危机
  1997-98 加息+强美元     → 亚洲金融危机（泰铢崩盘传染全亚洲）
  2004-06 连续加息        → 2008 全球金融危机
  2015-18 加息周期        → 土耳其里拉/阿根廷比索危机
  2022-23 激进加息        → 全球资金紧缩、斯里兰卡违约

模块功能:
  1. 采集联邦基金利率(1954-) + 美元指数(2006-) → 识别当前周期阶段
  2. 周期阶段: 宽松(easing) / 紧缩(tightening) / 转向(turning) / 观望(waiting)
  3. 国家脆弱性: 加息退潮期哪些国家最脆弱（高外债+双赤字+外储薄）
  4. 融合: 风险预警加权 + 投资机会窗口调整

数据源: FRED 公开 CSV（fred.stlouisfed.org/graph/fredgraph.csv）
"""
import json
import logging
import os
import time
import urllib.request
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("time_machine_v3_dollar_tide")

DATA_DIR = Path("/var/www/ai-digital-card/backend/data/time_machine_engine")
CACHE_FILE = DATA_DIR / "dollar_tide_cache.json"

FRED_URLS = {
    "fed_funds": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS",
    "dxy": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTWEXBGS",
}
CACHE_TTL_HOURS = 72  # 3天刷新（利率决议每6周一次）


class DollarTideEngine:
    """美元潮汐引擎"""

    ENGINE_ID = "dollar_tide_engine"
    VERSION = "1.0.0"

    def __init__(self):
        self._cache = self._load_cache()

    # ── 数据 ──────────────────────────────────────────────

    def _load_cache(self) -> dict:
        if CACHE_FILE.exists():
            try:
                cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
                age_h = (time.time() - cache.get("fetched_at", 0)) / 3600
                if age_h < CACHE_TTL_HOURS:
                    return cache
            except Exception:
                pass
        return {"fetched_at": 0, "fed_funds": {}, "dxy": {}}

    def _save_cache(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(self._cache, ensure_ascii=False), encoding="utf-8")

    def _fetch_csv(self, url: str, local_path: str | None = None) -> dict:
        """抓 FRED CSV → {year: avg_value}
        优先读本地已下载文件（curl 更稳），否则 urllib 抓取
        """
        text = None
        if local_path and os.path.exists(local_path):
            with open(local_path, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        if text is None:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
        yearly: dict = {}
        counts: dict = {}
        for line in text.strip().splitlines()[1:]:
            parts = line.split(",")
            if len(parts) < 2:
                continue
            date, val = parts[0], parts[1]
            if not val or val in (".", ""):
                continue
            try:
                year = int(date[:4])
                v = float(val)
                yearly[year] = yearly.get(year, 0) + v
                counts[year] = counts.get(year, 0) + 1
            except (ValueError, IndexError):
                continue
        return {y: round(yearly[y] / counts[y], 4) for y in yearly}

    def refresh(self, force: bool = False) -> dict:
        """刷新美元周期数据（优先读本地 CSV，失败再网络抓）"""
        if self._cache.get("fetched_at") and not force:
            age_h = (time.time() - self._cache["fetched_at"]) / 3600
            if age_h < CACHE_TTL_HOURS:
                return self._cache
        local_files = {
            "fed_funds": "/tmp/fedfunds.csv",
            "dxy": "/tmp/dxy.csv",
        }
        for key, url in FRED_URLS.items():
            try:
                self._cache[key] = self._fetch_csv(url, local_path=local_files.get(key))
                logger.info("%s 加载成功: %d 年", key, len(self._cache[key]))
            except Exception as e:
                logger.warning("%s 加载失败: %s", key, e)
            time.sleep(0.5)
        self._cache["fetched_at"] = time.time()
        self._save_cache()
        return self._cache

    # ── 周期识别 ──────────────────────────────────────────

    def cycle_stage(self, current_year: int | None = None) -> dict:
        """识别当前美元周期阶段
        规则（基于利率方向 + 变化幅度）:
          - 利率 < 2% 且下行/低位  → easing（宽松）
          - 利率 > 4% 且上行/高位  → tightening（紧缩）
          - 从高位快速回落 (>1.5pp/年) → turning_easing（转向宽松）
          - 从低位快速抬升 (>1pp/年) → turning_tightening（转向紧缩）
          - 其他 → waiting（观望）
        """
        current_year = current_year or datetime.now().year
        ff = self._cache.get("fed_funds", {})
        # JSON 缓存后年份 int 变 str，统一转 int（坑：与 wb_cache 同理）
        ff = {int(y): v for y, v in ff.items()}
        years = sorted(ff.keys())
        if not years:
            return {"stage": "unknown", "reason": "无利率数据"}

        latest = years[-1]
        cur = ff[latest]
        prev = ff.get(latest - 1)
        prev2 = ff.get(latest - 2)

        # 最近1年/2年变化
        trend = (cur - prev) if prev else 0
        trend2 = (prev - prev2) if (prev and prev2) else 0
        # 距峰值累计回落（紧缩转宽松的关键信号：从高位连续降息）
        peak_rate = max(ff.get(y, 0) for y in years[-8:]) if len(years) >= 8 else max(ff.values())
        peak_drop = peak_rate - cur

        if cur >= 4.5 and trend >= 0:
            stage = "tightening"
            reason = f"利率{cur}%高位且上行 → 紧缩潮（美元回流，新兴市场承压）"
        elif cur <= 2.5 and trend <= 0:
            stage = "easing"
            reason = f"利率{cur}%低位且下行 → 宽松潮（资本涌向新兴市场）"
        elif peak_drop >= 1.0 and trend <= 0:
            # 从峰值累计回落超1pp且仍在降 → 紧缩转宽松
            stage = "turning_easing"
            reason = f"利率{cur}%距峰值{peak_rate}%已回落{peak_drop:.1f}pp且仍下行 → 紧缩转宽松（新兴市场喘息）"
        elif cur <= 3.5 and trend >= 1.0:
            stage = "turning_tightening"
            reason = f"利率{cur}%从低位快速抬升({trend:+.1f}pp) → 宽松转紧缩（警惕退潮）"
        else:
            stage = "waiting"
            reason = f"利率{cur}%变化温和({trend:+.1f}pp) → 观望期"

        # 美元指数趋势
        dxy = self._cache.get("dxy", {})
        dxy = {int(y): v for y, v in dxy.items()}
        dxy_years = sorted(dxy.keys())
        dxy_trend = None
        dxy_now = None
        if len(dxy_years) >= 2:
            dxy_now = dxy[dxy_years[-1]]
            dxy_prev = dxy[dxy_years[-2]]
            dxy_trend = round(dxy_now - dxy_prev, 2)

        return {
            "stage": stage,
            "reason": reason,
            "fed_funds_current": cur,
            "fed_funds_year": latest,
            "fed_funds_trend": round(trend, 2) if trend else None,
            "dxy_current": dxy_now,
            "dxy_trend": dxy_trend,
            "risk_mode": "risk_on" if stage in ("easing", "turning_easing") else "risk_off",
        }

    # ── 国家脆弱性（退潮期谁先崩）────────────────────────

    def vulnerable_countries(self, risk_engine, top_n: int = 10) -> list[dict]:
        """加息退潮期最脆弱的国家的排名
        脆弱性 = 基础风险分 × 美元敏感度加成
        美元敏感度: 高外债 + 双赤字 + 外储不足（无外储数据用经常账户代理）
        """
        stage = self.cycle_stage()
        # 仅紧缩/转向紧缩时评估脆弱性（宽松期风险被美元掩盖）
        if stage["stage"] in ("waiting", "easing", "turning_easing", "unknown"):
            return []

        results = []
        for iso3 in risk_engine._all_countries():
            r = risk_engine.assess(iso3)
            if not r:
                continue
            # 美元敏感度: 外债分 + 双赤字分（这两个维度直接反映美元债务压力）
            dims = r.get("dims", {})
            debt_s = dims.get("debt", 0) or 0
            twindef_s = dims.get("twin_def", 0) or 0
            dollar_sensitivity = (debt_s + twindef_s) / 2
            # 脆弱性 = 基础风险 × (1 + 美元敏感度加权)
            fragility = r["total"] * (0.6 + dollar_sensitivity / 100 * 1.5)
            results.append({
                "iso3": r["iso3"],
                "name": r["name"],
                "base_risk": r["total"],
                "dollar_sensitivity": round(dollar_sensitivity, 1),
                "fragility": round(fragility, 1),
                "level": r["level"],
                "top_risks": r["top_risks"],
            })
        results.sort(key=lambda x: x["fragility"], reverse=True)
        return results[:top_n]

    # ── 投资窗口调整 ──────────────────────────────────────

    def adjust_opportunity(self, stage: str) -> dict:
        """根据美元周期调整投资建议"""
        if stage in ("easing", "turning_easing"):
            return {
                "window": "open",
                "advice": "美元宽松期 → 新兴市场资金涌入，🔥现在进场机会增多，可加大布局力度",
                "multiplier": 1.2,
            }
        if stage == "tightening":
            return {
                "window": "tight",
                "advice": "美元紧缩期 → 资金回流美国，新兴市场承压，建议聚焦低外债/高外储的安全市场，控制杠杆",
                "multiplier": 0.8,
            }
        if stage == "turning_tightening":
            return {
                "window": "closing",
                "advice": "美元转向紧缩 → 潮水开始退去，警惕高外债新兴市场，减持脆弱国资产",
                "multiplier": 0.9,
            }
        return {
            "window": "neutral",
            "advice": "美元观望期 → 正常节奏布局，关注美联储下次决议",
            "multiplier": 1.0,
        }

    # ── 历史周期档案（验证用）────────────────────────────

    # 历史危机对应的美元周期阶段（公开数据标注）
    HISTORIC_CYCLES = [
        {"year": 1982, "phase": "tightening", "event": "拉美债务危机(墨西哥违约)", "fed_funds": 14.0},
        {"year": 1995, "phase": "tightening", "event": "墨西哥比索危机", "fed_funds": 5.5},
        {"year": 1998, "phase": "tightening", "event": "亚洲金融危机(泰铢崩盘)", "fed_funds": 5.5},
        {"year": 2008, "phase": "tightening", "event": "全球金融危机", "fed_funds": 2.0},
        {"year": 2018, "phase": "tightening", "event": "土耳其里拉/阿根廷比索危机", "fed_funds": 2.4},
        {"year": 2022, "phase": "tightening", "event": "斯里兰卡违约/全球紧缩", "fed_funds": 4.0},
    ]

    def to_report(self, stage: dict, vulnerable: list[dict]) -> str:
        lines = [
            "# 🌊 美元潮汐 · 全球周期雷达",
            "",
            f"> 联邦基金利率: {stage.get('fed_funds_current')}% ({stage.get('fed_funds_year')}年)",
            f"> 美元指数: {stage.get('dxy_current')} (趋势 {stage.get('dxy_trend')})",
            f"> **当前阶段: {stage.get('stage')}** — {stage.get('reason')}",
            "",
            "## 历史铁证（每次金融危机都踩在同一节拍）",
            "",
        ]
        for c in self.HISTORIC_CYCLES:
            lines.append(f"- {c['year']} {c['phase']}: {c['event']} (利率{c['fed_funds']}%)")
        lines.append("")
        if vulnerable:
            lines.append("## 🚨 紧缩期最脆弱国家（退潮先崩）")
            lines.append("")
            for i, v in enumerate(vulnerable, 1):
                icon = {"extreme": "🟣", "high": "🔴", "medium": "🟡", "low": "🟢"}[v["level"]]
                lines.append(f"{i}. {icon} **{v['name']}** 脆弱度 {v['fragility']} "
                             f"(基础风险 {v['base_risk']} + 美元敏感 {v['dollar_sensitivity']})")
            lines.append("")
        return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dt = DollarTideEngine()
    dt.refresh(force="--force" in __import__("sys").argv)
    stage = dt.cycle_stage()
    print(json.dumps(stage, ensure_ascii=False, indent=1))
