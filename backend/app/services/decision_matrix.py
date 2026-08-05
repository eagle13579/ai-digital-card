"""F21 Agent化任务决策矩阵引擎。

四象限分类: 复杂度 × 重复度
  象限I  (低复杂度 × 高重复度) → ✅ Agent自动化
  象限II (高复杂度 × 高重复度) → ⚠️ Agent辅助/编排
  象限III(低复杂度 × 低重复度) → 🔧 简单脚本
  象限IV (高复杂度 × 低重复度) → ❌ 人工

核心功能:
  - evaluate(): 单任务评估 → 四象限分类 + 适配度评分
  - batch_evaluate(): 批量任务评估 + 汇总统计
  - classify_quadrant(): 根据复杂度/重复度分数定位象限
  - compute_suitability(): 综合适配度评分算法
"""

from __future__ import annotations
import logging
from typing import Any

from app.models.decision_matrix import (
    DecisionQuadrant,
    ComplexityFactors,
    RepetitionFactors,
    TaskEvaluationResult,
    EvaluationRequest,
    BatchEvaluationRequest,
    BatchEvaluationResult,
    MatrixStats,
    AgentReadinessCategory,
)

logger = logging.getLogger(__name__)


# ── 阈值配置 ──────────────────────────────
# 复杂度/重复度在 [0, 100] 区间内的分割点
COMPLEXITY_THRESHOLD = 50.0  # 高于此值为"高复杂度"
REPETITION_THRESHOLD = 50.0  # 高于此值为"高重复度"

# Agent适配度评分权重
# 适配度 = f(重复度 - 复杂度, 象限映射)
SUITABILITY_WEIGHTS = {
    "repetition_bonus": 0.6,     # 重复度越高越适合
    "complexity_penalty": 0.4,   # 复杂度越高越不适合
}

# 象限基准适配度 (0~100)
QUADRANT_BASE_SUITABILITY = {
    DecisionQuadrant.Q1_LOW_COMPLEXITY_HIGH_REPETITION: 90.0,
    DecisionQuadrant.Q2_HIGH_COMPLEXITY_HIGH_REPETITION: 60.0,
    DecisionQuadrant.Q3_LOW_COMPLEXITY_LOW_REPETITION: 45.0,
    DecisionQuadrant.Q4_HIGH_COMPLEXITY_LOW_REPETITION: 15.0,
}

# 预置示例任务 (用于 GET /api/decision-matrix/categories)
EXAMPLE_TASKS_BY_QUADRANT: dict[DecisionQuadrant, list[str]] = {
    DecisionQuadrant.Q1_LOW_COMPLEXITY_HIGH_REPETITION: [
        "客户资料批量录入与去重",
        "日报/周报自动生成",
        "发票信息OCR提取与对账",
        "邮件自动分类与回复模板匹配",
        "日志异常自动告警",
        "定时数据备份与校验",
    ],
    DecisionQuadrant.Q2_HIGH_COMPLEXITY_HIGH_REPETITION: [
        "多源数据智能匹配与融合",
        "合同条款自动审核与风险标记",
        "客户意图分析与智能路由",
        "供应链异常检测与自动调度",
        "大规模A/B测试结果分析",
    ],
    DecisionQuadrant.Q3_LOW_COMPLEXITY_LOW_REPETITION: [
        "一次性数据格式转换",
        "临时报表生成",
        "单次API接口测试",
        "环境部署脚本",
        "一次性文件迁移",
    ],
    DecisionQuadrant.Q4_HIGH_COMPLEXITY_LOW_REPETITION: [
        "战略决策与商业模式设计",
        "复杂商务谈判与关系维护",
        "首次客户需求深度调研",
        "危机公关与舆情处置",
        "新产品定位与定价策略",
    ],
}


# ── 核心引擎 ──────────────────────────────


class DecisionMatrixEngine:
    """Agent化任务决策矩阵引擎。"""

    def __init__(self) -> None:
        self._history: list[TaskEvaluationResult] = []
        self._stats: MatrixStats = MatrixStats()

    # ── 公开接口 ──

    def evaluate(self, request: EvaluationRequest) -> TaskEvaluationResult:
        """单任务评估: 基于复杂度/重复度因子计算象限与适配度。"""
        complexity_score = request.complexity_factors.compute_score()
        repetition_score = request.repetition_factors.compute_score()

        quadrant = self.classify_quadrant(complexity_score, repetition_score)
        suitability = self.compute_suitability(
            complexity_score, repetition_score, quadrant
        )

        result = TaskEvaluationResult(
            task_name=request.task_name,
            task_description=request.task_description,
            complexity_score=complexity_score,
            repetition_score=repetition_score,
            quadrant=quadrant,
            agent_suitability_score=suitability,
            recommendation=quadrant.recommendation,
            complexity_factors=request.complexity_factors,
            repetition_factors=request.repetition_factors,
            metadata=request.metadata,
        )

        self._record(result)
        return result

    def batch_evaluate(self, request: BatchEvaluationRequest) -> BatchEvaluationResult:
        """批量任务评估。"""
        results = [self.evaluate(task_req) for task_req in request.tasks]
        summary: dict[str, int] = {q.value: 0 for q in DecisionQuadrant}
        for r in results:
            summary[r.quadrant.value] = summary.get(r.quadrant.value, 0) + 1
        return BatchEvaluationResult(results=results, summary=summary)

    def get_stats(self) -> MatrixStats:
        """获取累计统计。"""
        return self._stats

    def reset_stats(self) -> None:
        """重置累计统计。"""
        self._history.clear()
        self._stats = MatrixStats()

    def get_categories(self) -> list[AgentReadinessCategory]:
        """获取四象限分类定义及示例。"""
        ranges: dict[DecisionQuadrant, tuple[tuple[float, float], tuple[float, float]]] = {
            DecisionQuadrant.Q1_LOW_COMPLEXITY_HIGH_REPETITION: (
                (0.0, COMPLEXITY_THRESHOLD),
                (REPETITION_THRESHOLD, 100.0),
            ),
            DecisionQuadrant.Q2_HIGH_COMPLEXITY_HIGH_REPETITION: (
                (COMPLEXITY_THRESHOLD, 100.0),
                (REPETITION_THRESHOLD, 100.0),
            ),
            DecisionQuadrant.Q3_LOW_COMPLEXITY_LOW_REPETITION: (
                (0.0, COMPLEXITY_THRESHOLD),
                (0.0, REPETITION_THRESHOLD),
            ),
            DecisionQuadrant.Q4_HIGH_COMPLEXITY_LOW_REPETITION: (
                (COMPLEXITY_THRESHOLD, 100.0),
                (0.0, REPETITION_THRESHOLD),
            ),
        }
        categories: list[AgentReadinessCategory] = []
        for quad in DecisionQuadrant:
            c_range, r_range = ranges[quad]
            categories.append(
                AgentReadinessCategory(
                    quadrant=quad,
                    label_cn=quad.label_cn,
                    suitability_label=quad.suitability_label,
                    recommendation=quad.recommendation,
                    complexity_range=c_range,
                    repetition_range=r_range,
                    example_tasks=EXAMPLE_TASKS_BY_QUADRANT.get(quad, []),
                )
            )
        return categories

    # ── 内部方法 ──

    def classify_quadrant(self, complexity: float, repetition: float) -> DecisionQuadrant:
        """根据复杂度/重复度分数定位四象限。"""
        is_high_complexity = complexity >= COMPLEXITY_THRESHOLD
        is_high_repetition = repetition >= REPETITION_THRESHOLD

        if not is_high_complexity and is_high_repetition:
            return DecisionQuadrant.Q1_LOW_COMPLEXITY_HIGH_REPETITION
        elif is_high_complexity and is_high_repetition:
            return DecisionQuadrant.Q2_HIGH_COMPLEXITY_HIGH_REPETITION
        elif not is_high_complexity and not is_high_repetition:
            return DecisionQuadrant.Q3_LOW_COMPLEXITY_LOW_REPETITION
        else:
            return DecisionQuadrant.Q4_HIGH_COMPLEXITY_LOW_REPETITION

    def compute_suitability(
        self,
        complexity: float,
        repetition: float,
        quadrant: DecisionQuadrant,
    ) -> float:
        """计算Agent适配度评分 (0~100)。

        算法:
          1. 以象限基准分起步
          2. 重复度正向调节: 每高1分加0.15
          3. 复杂度反向调节: 每高1分减0.10
          4. 边界裁剪到[0, 100]
        """
        base = QUADRANT_BASE_SUITABILITY.get(quadrant, 50.0)

        repetition_bonus = (repetition - 50.0) * 0.15
        complexity_penalty = (complexity - 50.0) * 0.10

        score = base + repetition_bonus - complexity_penalty
        score = max(0.0, min(100.0, score))
        return round(score, 2)

    def _record(self, result: TaskEvaluationResult) -> None:
        """记录评估结果到历史与统计。"""
        self._history.append(result)

        n = len(self._history)
        prev_avg_c = self._stats.avg_complexity
        prev_avg_r = self._stats.avg_repetition
        prev_avg_s = self._stats.avg_suitability

        # 增量更新平均值
        self._stats.avg_complexity = round(
            prev_avg_c + (result.complexity_score - prev_avg_c) / n, 2
        )
        self._stats.avg_repetition = round(
            prev_avg_r + (result.repetition_score - prev_avg_r) / n, 2
        )
        self._stats.avg_suitability = round(
            prev_avg_s + (result.agent_suitability_score - prev_avg_s) / n, 2
        )
        self._stats.total_tasks_evaluated = n

        quad_key = result.quadrant.value
        self._stats.quadrant_distribution[quad_key] = (
            self._stats.quadrant_distribution.get(quad_key, 0) + 1
        )

    def get_history(self) -> list[TaskEvaluationResult]:
        """获取历史评估记录。"""
        return list(self._history)


# ── 全局单例 ──────────────────────────────

_engine: DecisionMatrixEngine | None = None


def get_decision_matrix() -> DecisionMatrixEngine:
    """获取全局决策矩阵引擎单例。"""
    global _engine
    if _engine is None:
        _engine = DecisionMatrixEngine()
    return _engine


__all__ = [
    "DecisionMatrixEngine",
    "get_decision_matrix",
    "COMPLEXITY_THRESHOLD",
    "REPETITION_THRESHOLD",
    "EXAMPLE_TASKS_BY_QUADRANT",
]
