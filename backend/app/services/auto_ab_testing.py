"""
链客宝 — 自动 A/B 测试引擎 (自进化闭环)
========================================
在通用 ABTestManager 基础上构建的自动化 A/B 测试引擎。

核心流程:
    1. 自动创建实验 → 2. 分配流量 → 3. 收集数据 → 4. 统计分析 → 5. 宣布胜者

支持:
    - 匹配算法版本 A/B
    - 推荐策略 (协同过滤 / 内容推荐 / 混合推荐)
    - 定价方案
    - UI 变体
    - 置信度 ≥ 95% 自动宣布胜者

用法:
    engine = AutoABTestEngine()
    result = engine.create_and_run_experiment(
        name="rec_strategy_v2",
        experiment_type="recommendation",
        variants={"hybrid": 50, "collaborative": 50},
    )
    engine.auto_declare_winner()  # 自动检查所有运行中的实验
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.services.ab_testing import ABTestManager

logger = logging.getLogger("chainke.auto_ab_testing")


# ===================================================================
# 枚举与数据模型
# ===================================================================

class ExperimentType(str, Enum):
    """实验类型"""
    MATCHING_ALGORITHM = "matching_algorithm"       # 匹配算法版本
    RECOMMENDATION = "recommendation"                # 推荐策略
    PRICING_PLAN = "pricing_plan"                    # 定价方案
    UI_VARIANT = "ui_variant"                        # UI 变体
    SCORING_MODEL = "scoring_model"                  # 评分模型


class ExperimentStatus(str, Enum):
    """实验状态"""
    DRAFT = "draft"                 # 草稿，未启动
    RUNNING = "running"             # 运行中，收集数据
    PAUSED = "paused"              # 暂停
    COMPLETED = "completed"         # 已完成，有胜者
    DECLARED_WINNER = "declared_winner"  # 已宣布胜者并部署
    CANCELLED = "cancelled"         # 取消
    INCONCLUSIVE = "inconclusive"   # 无明确胜者


@dataclass
class AutoExperiment:
    """自动实验配置与状态"""
    name: str
    experiment_type: ExperimentType
    variants: Dict[str, float]          # variant_name -> traffic_percentage
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    min_sample_size: int = 50           # 最小样本量
    confidence_threshold: float = 0.95  # 置信度阈值
    max_duration_days: int = 14         # 最大运行天数
    metadata: Dict[str, Any] = field(default_factory=dict)
    winner: Optional[str] = None        # 胜者 variant
    stats: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "experiment_type": self.experiment_type.value,
            "variants": self.variants,
            "status": self.status.value,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "started_at": datetime.fromtimestamp(self.started_at).isoformat()
                if self.started_at else None,
            "completed_at": datetime.fromtimestamp(self.completed_at).isoformat()
                if self.completed_at else None,
            "min_sample_size": self.min_sample_size,
            "confidence_threshold": self.confidence_threshold,
            "max_duration_days": self.max_duration_days,
            "metadata": self.metadata,
            "winner": self.winner,
            "stats": self.stats,
        }


# ===================================================================
# 自动 A/B 测试引擎
# ===================================================================

class AutoABTestEngine:
    """自动 A/B 测试引擎

    特性:
        - 自动创建实验并分配流量
        - 自动收集转化数据
        - 自动统计分析 (Z 检验)
        - 置信度 ≥ 95% 自动宣布胜者
        - 支持多种实验类型
        - 实验仪表盘 API
    """

    def __init__(self):
        self._ab_manager = ABTestManager()
        self._experiments: Dict[str, AutoExperiment] = {}
        self._conversion_log: Dict[str, List[Dict[str, Any]]] = {}
        # conversion_log[experiment_name] = [
        #     {"user_id": "u1", "variant": "A", "converted": True, "timestamp": ...},
        # ]

    # ── 实验生命周期 ──────────────────────────────────────────────

    def create_experiment(
        self,
        name: str,
        experiment_type: ExperimentType,
        variants: Dict[str, float],
        min_sample_size: int = 50,
        confidence_threshold: float = 0.95,
        max_duration_days: int = 14,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AutoExperiment:
        """创建一个新的自动实验

        Args:
            name: 实验名称 (唯一)
            experiment_type: 实验类型
            variants: variant_name -> 流量百分比
            min_sample_size: 最小样本量 (低于此不宣布胜者)
            confidence_threshold: 置信度阈值 (默认 0.95)
            max_duration_days: 最大运行天数
            metadata: 附加元数据

        Returns:
            AutoExperiment
        """
        if name in self._experiments:
            raise ValueError(f"Experiment '{name}' already exists")
        if not variants:
            raise ValueError("At least one variant is required")

        # 归一化流量百分比
        total = sum(variants.values())
        if total <= 0:
            raise ValueError("Traffic percentages must sum to > 0")
        normalized = {k: v / total for k, v in variants.items()}

        exp = AutoExperiment(
            name=name,
            experiment_type=experiment_type,
            variants=normalized,
            min_sample_size=min_sample_size,
            confidence_threshold=confidence_threshold,
            max_duration_days=max_duration_days,
            metadata=metadata or {},
        )
        self._experiments[name] = exp
        self._conversion_log[name] = []

        logger.info(
            "[AutoAB] 创建实验: %s (type=%s, variants=%s)",
            name, experiment_type.value, list(variants.keys()),
        )
        return exp

    def start_experiment(self, name: str) -> bool:
        """启动实验"""
        exp = self._get_or_raise(name)
        if exp.status not in (ExperimentStatus.DRAFT, ExperimentStatus.PAUSED):
            logger.warning("[AutoAB] 实验 %s 状态为 %s，无法启动", name, exp.status)
            return False

        exp.status = ExperimentStatus.RUNNING
        exp.started_at = time.time()

        # 在底层 ABTestManager 中创建同名实验
        try:
            self._ab_manager.create_experiment(name, exp.variants, metadata=exp.metadata)
        except ValueError:
            # 已存在则忽略
            pass

        logger.info("[AutoAB] 启动实验: %s", name)
        return True

    def pause_experiment(self, name: str) -> bool:
        """暂停实验"""
        exp = self._get_or_raise(name)
        if exp.status != ExperimentStatus.RUNNING:
            return False
        exp.status = ExperimentStatus.PAUSED
        self._ab_manager.disable_experiment(name)
        logger.info("[AutoAB] 暂停实验: %s", name)
        return True

    def cancel_experiment(self, name: str) -> bool:
        """取消实验"""
        exp = self._get_or_raise(name)
        exp.status = ExperimentStatus.CANCELLED
        exp.completed_at = time.time()
        try:
            self._ab_manager.delete_experiment(name)
        except ValueError:
            pass
        self._experiments.pop(name, None)
        self._conversion_log.pop(name, None)
        logger.info("[AutoAB] 取消实验: %s", name)
        return True

    def create_and_run_experiment(
        self,
        name: str,
        experiment_type: ExperimentType,
        variants: Dict[str, float],
        **kwargs,
    ) -> AutoExperiment:
        """创建并立即启动实验"""
        exp = self.create_experiment(name, experiment_type, variants, **kwargs)
        self.start_experiment(name)
        return exp

    # ── 用户分配 ──────────────────────────────────────────────────

    def assign(self, experiment_name: str, user_id: str) -> Optional[str]:
        """将用户分配到实验变体

        自动跟踪分配 (impression)
        """
        exp = self._experiments.get(experiment_name)
        if not exp or exp.status != ExperimentStatus.RUNNING:
            return None

        variant = self._ab_manager.assign(experiment_name, user_id)
        if variant:
            self._log_event(experiment_name, user_id, variant, converted=False)
        return variant

    def get_assignment(self, experiment_name: str, user_id: str) -> Optional[str]:
        """查询用户已有分配"""
        exp = self._experiments.get(experiment_name)
        if not exp:
            return None
        return self._ab_manager.get_assignment(experiment_name, user_id)

    # ── 转化跟踪 ──────────────────────────────────────────────────

    def track_conversion(
        self,
        experiment_name: str,
        user_id: str,
        variant: Optional[str] = None,
    ) -> None:
        """记录一次转化事件"""
        exp = self._get_or_raise(experiment_name)
        if exp.status != ExperimentStatus.RUNNING:
            return

        try:
            self._ab_manager.track_conversion(experiment_name, user_id, variant)
        except ValueError:
            return

        if variant is None:
            variant = self._ab_manager.get_assignment(experiment_name, user_id)
        if variant:
            self._log_event(experiment_name, user_id, variant, converted=True)

    def track_non_conversion(
        self,
        experiment_name: str,
        user_id: str,
        variant: Optional[str] = None,
    ) -> None:
        """记录一次非转化事件"""
        exp = self._get_or_raise(experiment_name)
        if exp.status != ExperimentStatus.RUNNING:
            return

        try:
            self._ab_manager.track_non_conversion(experiment_name, user_id, variant)
        except ValueError:
            pass

    def _log_event(
        self,
        experiment_name: str,
        user_id: str,
        variant: str,
        converted: bool,
    ) -> None:
        """记录原始事件日志"""
        log = self._conversion_log.setdefault(experiment_name, [])
        log.append({
            "user_id": user_id,
            "variant": variant,
            "converted": converted,
            "timestamp": time.time(),
        })

    # ── 统计分析 ──────────────────────────────────────────────────

    def analyze(self, experiment_name: str) -> Dict[str, Any]:
        """分析实验统计结果

        Returns:
            {
                "experiment_name": "...",
                "status": "...",
                "variants": [...],
                "total_impressions": int,
                "total_conversions": int,
                "winner": str or None,
                "significant": bool,
                "confidence_level": float,
                "recommendation": "..."
            }
        """
        exp = self._get_or_raise(experiment_name)

        stats = self._ab_manager.get_stats(experiment_name)
        winner = self._ab_manager.get_winner(experiment_name)

        total_impressions = sum(s.impressions for s in stats)
        total_conversions = sum(s.conversions for s in stats)

        # 判断是否达到最小样本量
        min_reached = all(s.impressions >= exp.min_sample_size for s in stats)

        # 判断置信度是否达标
        significant_results = [s for s in stats if s.significant]
        all_significant = len(significant_results) == len(stats)

        # 检查时间限制
        if exp.started_at:
            elapsed_days = (time.time() - exp.started_at) / 86400
            time_expired = elapsed_days >= exp.max_duration_days
        else:
            time_expired = False

        # 判断是否可宣布胜者
        can_declare = (
            winner is not None
            and total_impressions >= exp.min_sample_size * len(exp.variants)
            and min_reached
        )

        result = {
            "experiment_name": experiment_name,
            "experiment_type": exp.experiment_type.value,
            "status": exp.status.value,
            "variants": [
                {
                    "name": s.variant,
                    "impressions": s.impressions,
                    "conversions": s.conversions,
                    "conversion_rate": round(s.conversion_rate, 4),
                    "significant": s.significant,
                    "p_value": round(s.p_value, 4),
                    "confidence_interval": [
                        round(s.confidence_interval[0], 4),
                        round(s.confidence_interval[1], 4),
                    ],
                }
                for s in stats
            ],
            "total_impressions": total_impressions,
            "total_conversions": total_conversions,
            "overall_rate": round(total_conversions / max(total_impressions, 1), 4),
            "winner": winner,
            "significant": all_significant and winner is not None,
            "confidence_level": 0.95 if all_significant else None,
            "min_sample_reached": min_reached,
            "time_expired": time_expired,
            "can_declare": can_declare,
            "recommendation": self._get_recommendation(exp, winner, min_reached, time_expired),
        }

        exp.stats = result
        return result

    def _get_recommendation(
        self,
        exp: AutoExperiment,
        winner: Optional[str],
        min_reached: bool,
        time_expired: bool,
    ) -> str:
        """生成建议"""
        if winner and min_reached:
            return (
                f"胜者已出: '{winner}'。置信度 ≥ {exp.confidence_threshold*100:.0f}%，"
                f"建议部署 '{winner}' 到生产。"
            )
        if time_expired:
            return (
                f"实验已运行 {exp.max_duration_days} 天，最大时限已到。"
                f"{'建议部署 ' + winner + ' (虽不足最小样本量)' if winner else '结论: 无显著胜者。'}"
            )
        if winner and not min_reached:
            return (
                f"'{winner}' 当前领先但未达最小样本量 ({exp.min_sample_size})，"
                f"建议继续收集数据。"
            )
        return "数据收集中，尚未达到统计显著。"

    # ── 自动宣布胜者 ──────────────────────────────────────────────

    def auto_declare_winner(self, experiment_name: str) -> Optional[str]:
        """自动检查并宣布胜者

        条件:
            1. 所有变体样本量 ≥ min_sample_size
            2. 置信度 ≥ 95%
            3. 存在统计显著的胜者

        Args:
            experiment_name: 实验名称

        Returns:
            胜者 variant 名称，或 None
        """
        exp = self._get_or_raise(experiment_name)
        if exp.status != ExperimentStatus.RUNNING:
            return None

        analysis = self.analyze(experiment_name)
        winner = analysis.get("winner")

        if analysis["can_declare"]:
            exp.status = ExperimentStatus.DECLARED_WINNER
            exp.winner = winner
            exp.completed_at = time.time()

            logger.info(
                "[AutoAB] 🏆 实验 '%s' 宣布胜者: '%s' (置信度≥95%%)",
                experiment_name, winner,
            )

            # 更新元数据
            exp.metadata["deployed_at"] = datetime.utcnow().isoformat()
            exp.metadata["analysis"] = analysis
            return winner

        # 检查是否超时
        if analysis.get("time_expired"):
            exp.status = ExperimentStatus.COMPLETED
            exp.winner = winner
            exp.completed_at = time.time()

            if winner:
                logger.info(
                    "[AutoAB] ⏰ 实验 '%s' 超时，胜者: '%s'",
                    experiment_name, winner,
                )
            else:
                exp.status = ExperimentStatus.INCONCLUSIVE
                logger.info(
                    "[AutoAB] ⏰ 实验 '%s' 超时，无显著胜者",
                    experiment_name,
                )
            return winner

        return None

    def auto_declare_all_winners(self) -> List[Tuple[str, Optional[str]]]:
        """自动检查所有运行中的实验并宣布胜者"""
        results: List[Tuple[str, Optional[str]]] = []
        for name, exp in self._experiments.items():
            if exp.status == ExperimentStatus.RUNNING:
                winner = self.auto_declare_winner(name)
                results.append((name, winner))
        return results

    # ── 查询接口 ──────────────────────────────────────────────────

    def get_experiment(self, name: str) -> Optional[AutoExperiment]:
        """获取实验详情"""
        return self._experiments.get(name)

    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
        experiment_type: Optional[ExperimentType] = None,
    ) -> List[AutoExperiment]:
        """列出实验，支持筛选"""
        results = list(self._experiments.values())
        if status:
            results = [e for e in results if e.status == status]
        if experiment_type:
            results = [e for e in results if e.experiment_type == experiment_type]
        return sorted(results, key=lambda e: e.created_at, reverse=True)

    def get_ab_manager(self) -> ABTestManager:
        """获取底层 ABTestManager (用于直接集成)"""
        return self._ab_manager

    # ── 内部辅助 ──────────────────────────────────────────────────

    def _get_or_raise(self, name: str) -> AutoExperiment:
        if name not in self._experiments:
            raise ValueError(f"Experiment '{name}' not found")
        return self._experiments[name]


# ===================================================================
# 单例
# ===================================================================

engine = AutoABTestEngine()

__all__ = [
    "AutoABTestEngine",
    "AutoExperiment",
    "ExperimentType",
    "ExperimentStatus",
    "engine",
]
