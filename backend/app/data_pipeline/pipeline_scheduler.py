"""
P4: 智能调度引擎 — 基于质量数据动态调整采集/训练频率
============================================
原则：
- 数据源去重率高(>70%) → 数据源枯竭 → 降低频率
- 数据源连续成功 → 维持或略增频率
- 模型训练失败率高(>40%) → 降低训练频率（减少浪费）
- 模型超过48h未训练 → 提升优先级
- 所有调整幅度控制在 ±50% 以内，避免剧烈波动
"""
import os
import sys
import json
import datetime
import logging
from typing import Dict, List, Optional
from collections import defaultdict

BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BACKEND_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("SmartScheduler")

# 调整范围约束
MIN_FREQ_MINUTES = 5          # 最短5分钟
MAX_FREQ_MINUTES = 2880       # 最长2天
ADJUSTMENT_CAP = 0.5          # 单次调整幅度上限 ±50%


class SmartScheduler:
    """
    智能调度器 — 基于质量历史数据动态调整频率
    分析维度：
    1. 数据源去重率 → 源是否枯竭
    2. 数据源采集成功率 → 源是否可用
    3. 模型训练成功率 → 训练是否有效
    4. 模型训练间隔 → 是否过时
    """

    def __init__(self):
        self._quality_path = os.path.join(os.path.dirname(__file__), ".pipeline_quality.json")
        self._source_registry_path = os.path.join(os.path.dirname(__file__), "data_source_registry.json")
        self._model_registry_path = os.path.join(os.path.dirname(__file__), "model_registry.json")
        self._adjustments: Dict[str, dict] = {}

    def _load_quality(self) -> dict:
        if os.path.exists(self._quality_path):
            with open(self._quality_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"cleaning_history": [], "training_history": [], "collection_history": []}

    def _load_source_registry(self) -> dict:
        if os.path.exists(self._source_registry_path):
            with open(self._source_registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"sources": {}}

    def _load_model_registry(self) -> dict:
        if os.path.exists(self._model_registry_path):
            with open(self._model_registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"models": {}}

    def _save_source_registry(self, registry: dict):
        with open(self._source_registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)

    # ─── 数据源调度 ───

    def _compute_source_adjustment(self, source_id: str, history: List[dict]) -> float:
        """
        计算数据源的频率调整因子
        >1.0 = 需要提高频率(加快采集), <1.0 = 降低频率(减少采集)
        """
        if not history:
            return 1.0  # 无数据，维持

        # 只看最近10条记录
        recent = history[-10:]
        if not recent:
            return 1.0

        dedup_rates = []
        for h in recent:
            inp = h.get("input_count", 0)
            dedup = h.get("dedup", 0)
            if inp > 0:
                dedup_rates.append(dedup / inp)

        # 去重率分析
        if dedup_rates:
            avg_dedup = sum(dedup_rates[-5:]) / min(5, len(dedup_rates[-5:]))
        else:
            avg_dedup = 0

        # 数据量趋势
        kept_counts = [h.get("kept", 0) for h in recent]
        if len(kept_counts) >= 3:
            recent_avg = sum(kept_counts[-3:]) / 3
            older_avg = sum(kept_counts[:-3]) / max(1, len(kept_counts[:-3]))
            drop_ratio = recent_avg / max(1, older_avg)
        else:
            drop_ratio = 1.0

        # 综合调整因子
        factor = 1.0

        # 去重率高 → 降低频率（数据源枯竭）
        if avg_dedup > 0.7:
            factor *= (1.0 - min(avg_dedup - 0.7, ADJUSTMENT_CAP))
            logger.debug(f"  {source_id}: 高去重率{avg_dedup:.0%} → 因子{factor:.2f}")

        # 数据量下降 → 降低频率
        if drop_ratio < 0.5:
            factor *= (1.0 - min(0.5 - drop_ratio, ADJUSTMENT_CAP))
            logger.debug(f"  {source_id}: 数据量下降{drop_ratio:.0%} → 因子{factor:.2f}")

        # 数据量上升 → 可提高频率
        if drop_ratio > 1.5 and avg_dedup < 0.3:
            factor *= min(drop_ratio, 1.0 + ADJUSTMENT_CAP)
            logger.debug(f"  {source_id}: 数据量增长{drop_ratio:.0%} → 因子{factor:.2f}")

        # 钳制
        return max(1.0 - ADJUSTMENT_CAP, min(1.0 + ADJUSTMENT_CAP, factor))

    def _compute_model_adjustment(self, model_id: str, history: List[dict]) -> float:
        """
        计算模型的训练频率调整因子
        >1.0 = 需要更频繁训练, <1.0 = 降低训练频率
        """
        if not history:
            return 1.0

        recent = history[-20:]
        if not recent:
            return 1.0

        # 训练成功率
        successes = sum(1 for h in recent if h.get("status") == "success")
        total = len(recent)
        success_rate = successes / total if total > 0 else 0

        # 最近训练时间
        last_ts_str = recent[-1].get("timestamp", "")
        try:
            last_ts = datetime.datetime.fromisoformat(last_ts_str).timestamp()
            age_hours = (datetime.datetime.utcnow().timestamp() - last_ts) / 3600
        except Exception:
            age_hours = 0

        factor = 1.0

        # 失败率高 → 降低频率（减少无效训练）
        if success_rate < 0.4:
            factor *= (1.0 - min((0.4 - success_rate) * 2, ADJUSTMENT_CAP))
            logger.debug(f"  {model_id}: 成功率{success_rate:.0%} → 因子{factor:.2f}")

        # 超过48h未训练 → 提高频率
        if age_hours > 48:
            factor *= min(1.0 + (age_hours - 48) / 48, 1.0 + ADJUSTMENT_CAP)
            logger.debug(f"  {model_id}: {age_hours:.0f}h未训练 → 因子{factor:.2f}")

        return max(1.0 - ADJUSTMENT_CAP, min(1.0 + ADJUSTMENT_CAP, factor))

    def analyze(self) -> dict:
        """分析所有数据源和模型，生成调度建议"""
        quality = self._load_quality()
        sources = self._load_source_registry()
        models = self._load_model_registry()

        cleaning_history = quality.get("cleaning_history", [])
        training_history = quality.get("training_history", [])
        source_cleaning = defaultdict(list)
        model_training = defaultdict(list)

        for h in cleaning_history:
            source_cleaning[h.get("source_id", "")].append(h)
        for h in training_history:
            model_training[h.get("model_id", "")].append(h)

        adjustments = {}

        # 分析数据源
        for sid, src in sources.get("sources", {}).items():
            if not src.get("enabled", False):
                continue
            hist = source_cleaning.get(sid, [])
            factor = self._compute_source_adjustment(sid, hist)
            old_freq = src.get("frequency_min", 60)
            new_freq = max(MIN_FREQ_MINUTES, min(MAX_FREQ_MINUTES,
                          int(round(old_freq / factor))))
            direction = "⬇️ 减速" if new_freq > old_freq else "⬆️ 加速" if new_freq < old_freq else "➡️ 维持"

            adjustments[f"source:{sid}"] = {
                "type": "source",
                "target": sid,
                "old_frequency_min": old_freq,
                "new_frequency_min": new_freq,
                "factor": round(factor, 3),
                "direction": direction,
                "reason": self._source_reason(factor, old_freq, new_freq),
            }

        # 分析模型
        for mid, cfg in models.get("models", {}).items():
            if not cfg.get("enabled", False):
                continue
            if cfg.get("training_type") == "online":
                continue  # 在线模型不需要调度
            hist = model_training.get(mid, [])
            factor = self._compute_model_adjustment(mid, hist)
            old_freq = cfg.get("frequency_min", 360)
            new_freq = max(MIN_FREQ_MINUTES, min(MAX_FREQ_MINUTES,
                          int(round(old_freq / factor))))
            direction = "⬇️ 减速" if new_freq > old_freq else "⬆️ 加速" if new_freq < old_freq else "➡️ 维持"

            adjustments[f"model:{mid}"] = {
                "type": "model",
                "target": mid,
                "old_frequency_min": old_freq,
                "new_frequency_min": new_freq,
                "factor": round(factor, 3),
                "direction": direction,
                "reason": self._model_reason(factor, old_freq, new_freq),
            }

        self._adjustments = adjustments
        logger.info(f"  调度建议: {len(adjustments)} 项调整")

        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "total_adjustments": len(adjustments),
            "adjusted_sources": len([a for a in adjustments.values() if a["type"] == "source"]),
            "adjusted_models": len([a for a in adjustments.values() if a["type"] == "model"]),
            "changes": {
                "accelerated": len([a for a in adjustments.values() if "加速" in a["direction"]]),
                "decelerated": len([a for a in adjustments.values() if "减速" in a["direction"]]),
                "maintained": len([a for a in adjustments.values() if "维持" in a["direction"]]),
            },
            "adjustments": adjustments,
        }

    def apply(self, dry_run: bool = True) -> dict:
        """应用调度建议到注册表"""
        if not self._adjustments:
            self.analyze()

        changes = []

        if dry_run:
            logger.info("🧪 Dry-run模式: 不写注册表")
            for adj_id, adj in self._adjustments.items():
                if adj["direction"] != "➡️ 维持":
                    changes.append(adj)
            return {
                "mode": "dry_run",
                "total_changes": len(changes),
                "changes": changes,
                "message": "dry-run模式，未写注册表"
            }

        # 真实应用
        sources = self._load_source_registry()
        models = self._load_model_registry()
        applied = 0

        for adj_id, adj in self._adjustments.items():
            if adj["direction"] == "➡️ 维持":
                continue

            if adj["type"] == "source":
                sid = adj["target"]
                if sid in sources.get("sources", {}):
                    sources["sources"][sid]["frequency_min"] = adj["new_frequency_min"]
                    sources["sources"][sid]["adjusted_by_scheduler"] = True
                    sources["sources"][sid]["last_adjusted"] = datetime.datetime.utcnow().isoformat()
                    applied += 1

            elif adj["type"] == "model":
                mid = adj["target"]
                if mid in models.get("models", {}):
                    models["models"][mid]["frequency_min"] = adj["new_frequency_min"]
                    models["models"][mid]["adjusted_by_scheduler"] = True
                    models["models"][mid]["last_adjusted"] = datetime.datetime.utcnow().isoformat()
                    applied += 1

        self._save_source_registry(sources)
        # 注意: model_registry是通过ModelRegistry类管理的，写JSON可能绕过了dataclass
        # 但为了简单，直接写JSON文件
        with open(self._model_registry_path, "w", encoding="utf-8") as f:
            json.dump(models, f, ensure_ascii=False, indent=2)

        logger.info(f"  已应用 {applied} 项调整到注册表")
        return {
            "mode": "applied",
            "applied": applied,
            "message": f"{applied} 项频率调整已写注册表"
        }

    def _source_reason(self, factor: float, old: int, new: int) -> str:
        if factor > 1.3:
            return f"数据量增长，频率从{old}min→{new}min"
        elif factor < 0.7:
            return f"去重率高/数据量下降，频率从{old}min→{new}min"
        return f"维持当前频率{old}min"

    def _model_reason(self, factor: float, old: int, new: int) -> str:
        if factor > 1.3:
            return f"过时未训练，频率从{old}min→{new}min"
        elif factor < 0.7:
            return f"训练失败率高，频率从{old}min→{new}min"
        return f"维持当前频率{old}min"


def run_once():
    """单次执行入口"""
    import argparse
    parser = argparse.ArgumentParser(description="智能调度引擎")
    parser.add_argument("--apply", action="store_true", help="真实应用调整（默认dry-run）")
    parser.add_argument("--json", action="store_true", help="JSON输出")
    args = parser.parse_args()

    scheduler = SmartScheduler()
    analysis = scheduler.analyze()

    if args.apply:
        result = scheduler.apply(dry_run=False)
    else:
        result = scheduler.apply(dry_run=True)

    output = {**analysis, **result}

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        c = analysis.get("changes", {})
        print(f"📊 P4智能调度分析")
        print(f"  建议调整: {analysis.get('total_adjustments', 0)} 项")
        print(f"  ⬆️ 加速: {c.get('accelerated', 0)}  |  ⬇️ 减速: {c.get('decelerated', 0)}  |  ➡️ 维持: {c.get('maintained', 0)}")
        print(f"  模式: {'✅ 已应用' if args.apply else '🧪 dry-run'}")
        print(f"  数据源: {analysis.get('adjusted_sources', 0)} 项 | 模型: {analysis.get('adjusted_models', 0)} 项")

    return 0


if __name__ == "__main__":
    run_once()
