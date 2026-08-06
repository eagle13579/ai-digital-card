"""
芯森态 · P1: ML评分框架 — 规则→ML迁移
当前为规则评分的ML包装器，积累足够数据后可切换为LightGBM/XGBoost
"""
import json
import logging
import math
from typing import Optional

logger = logging.getLogger("MLScorer")


class MLScorer:
    """
    ML评分框架 — 从规则评分到ML评分的渐进式迁移

    当前阶段 (Phase 1): 规则评分 + 权重校准
    Phase 2: 历史数据训练 LightGBM 模型
    Phase 3: 实时ML推理 + A/B测试
    """

    def __init__(self):
        self.model_ready = False
        self.feature_weights = {
            "active_score": 0.20,
            "purchase_score": 0.20,
            "content_score": 0.20,
            "influence_score": 0.15,
            "city_score": 0.15,
            "trust_score": 0.10,
        }

    def calibrate_weights(self, historical_data: list[dict]) -> dict:
        """
        基于历史数据校准权重（Phase 1→2过渡）
        输入: [{"features": {...}, "actual_conversion": 0/1}, ...]
        输出: 校准后的权重
        """
        if len(historical_data) < 30:
            return {"status": "need_more_data", "samples": len(historical_data), "required": 30}

        # 计算各特征与转化率的相关性
        correlations = {}
        for dim in self.feature_weights:
            scores = []
            conversions = []
            for d in historical_data:
                f = d.get("features", {})
                if dim in f:
                    scores.append(f[dim])
                    conversions.append(d.get("actual_conversion", 0))

            if len(scores) > 5 and sum(conversions) > 0:
                # 简化相关性计算（Pearson近似）
                n = len(scores)
                mean_s = sum(scores) / n
                mean_c = sum(conversions) / n
                num = sum((s - mean_s) * (c - mean_c) for s, c in zip(scores, conversions))
                den = math.sqrt(sum((s - mean_s) ** 2 for s in scores)) * \
                      math.sqrt(sum((c - mean_c) ** 2 for c in conversions))
                correlations[dim] = num / den if den > 0 else 0
            else:
                correlations[dim] = 0

        # 基于相关性调整权重
        total_corr = sum(abs(v) for v in correlations.values())
        if total_corr > 0:
            for dim in self.feature_weights:
                self.feature_weights[dim] = max(0.05, abs(correlations.get(dim, 0)) / total_corr)

            # 归一化
            total = sum(self.feature_weights.values())
            for dim in self.feature_weights:
                self.feature_weights[dim] /= total

        self.model_ready = len(historical_data) >= 100
        return {
            "status": "calibrated",
            "weights": self.feature_weights,
            "correlations": correlations,
            "model_ready": self.model_ready,
            "samples": len(historical_data),
        }

    def predict(self, features: dict) -> dict:
        """
        ML预测评分（当前为加权规则，后续替换为模型推理）
        """
        if self.model_ready:
            return self._ml_predict(features)
        return self._rule_predict(features)

    def _rule_predict(self, features: dict) -> dict:
        """规则评分（当前默认）"""
        total = 0
        details = {}
        for dim, weight in self.feature_weights.items():
            score = features.get(dim, 0)
            total += score * weight
            details[dim] = {"raw": score, "weighted": round(score * weight, 2)}
        return {
            "total_score": round(total, 2),
            "details": details,
            "method": "rule_weighted",
            "model_ready": False,
        }

    def _ml_predict(self, features: dict) -> dict:
        """ML评分（Phase 2+: 需要模型训练后才能启用）"""
        # 预留：加载LightGBM模型 → model.predict(features)
        # 当前fallback到规则评分
        result = self._rule_predict(features)
        result["method"] = "ml_fallback_to_rule"
        result["model_ready"] = True
        result["note"] = "ML模型未加载，当前使用规则评分。积累100+转化数据后自动训练。"
        return result


# 全局单例
scorer = MLScorer()


def get_scorer() -> MLScorer:
    return scorer
