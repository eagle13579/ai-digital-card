"""F21 Agent化任务决策矩阵 — 数据模型。

四象限分类: 复杂度 × 重复度
  象限I  (低复杂度 × 高重复度) → ✅ 适合Agent自动化
  象限II (高复杂度 × 高重复度) → ⚠️ Agent辅助/编排
  象限III(低复杂度 × 低重复度) → 🔧 简单脚本自动化
  象限IV (高复杂度 × 低重复度) → ❌ 不适合Agent化

评分维度:
  - 复杂度评分 (0~100): 任务复杂度、决策点数量、异常率、所需专业度
  - 重复度评分 (0~100): 执行频率、批量规模、相似度、模式稳定度
  - Agent适配度评分 (0~100): 综合评分, 越高越适合Agent化
"""

from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


# ── 象限枚举 ──────────────────────────────


class DecisionQuadrant(str, Enum):
    """决策矩阵四象限枚举。"""
    Q1_LOW_COMPLEXITY_HIGH_REPETITION = "Q1"       # 低复杂度 × 高重复度 → Agent自动化
    Q2_HIGH_COMPLEXITY_HIGH_REPETITION = "Q2"      # 高复杂度 × 高重复度 → Agent辅助
    Q3_LOW_COMPLEXITY_LOW_REPETITION = "Q3"        # 低复杂度 × 低重复度 → 脚本自动化
    Q4_HIGH_COMPLEXITY_LOW_REPETITION = "Q4"       # 高复杂度 × 低重复度 → 人工

    @property
    def label_cn(self) -> str:
        labels = {
            "Q1": "低复杂度·高重复度",
            "Q2": "高复杂度·高重复度",
            "Q3": "低复杂度·低重复度",
            "Q4": "高复杂度·低重复度",
        }
        return labels[self.value]

    @property
    def recommendation(self) -> str:
        recs = {
            "Q1": "✅ 强烈推荐Agent化 — 规则明确、频次高、收益显著",
            "Q2": "⚠️ 建议Agent辅助 — 需人工编排或引入决策智能体",
            "Q3": "🔧 适合脚本自动化 — 简单任务可用 CLI/SDK 批量处理",
            "Q4": "❌ 不建议Agent化 — 人工处理效率更高、风险更低",
        }
        return recs[self.value]

    @property
    def suitability_label(self) -> str:
        labels = {
            "Q1": "agent_ready",
            "Q2": "agent_assisted",
            "Q3": "script_ready",
            "Q4": "human_only",
        }
        return labels[self.value]


# ── 评分因子模型 ──────────────────────────


class ComplexityFactors(BaseModel):
    """复杂度评分因子。"""
    task_complexity: float = Field(
        default=50.0, ge=0, le=100,
        description="任务复杂度 (0=简单重复, 100=高度复杂)",
    )
    decision_points: float = Field(
        default=50.0, ge=0, le=100,
        description="决策点数量/密度 (0=无需决策, 100=大量分支判断)",
    )
    exception_rate: float = Field(
        default=50.0, ge=0, le=100,
        description="异常率 (0=极少异常, 100=频繁异常)",
    )
    required_expertise: float = Field(
        default=50.0, ge=0, le=100,
        description="所需专业度 (0=无需专业, 100=高度专业)",
    )

    def compute_score(self) -> float:
        """加权计算复杂度总分。"""
        weights = {
            "task_complexity": 0.35,
            "decision_points": 0.30,
            "exception_rate": 0.20,
            "required_expertise": 0.15,
        }
        score = (
            self.task_complexity * weights["task_complexity"]
            + self.decision_points * weights["decision_points"]
            + self.exception_rate * weights["exception_rate"]
            + self.required_expertise * weights["required_expertise"]
        )
        return round(score, 2)


class RepetitionFactors(BaseModel):
    """重复度评分因子。"""
    frequency: float = Field(
        default=50.0, ge=0, le=100,
        description="执行频率 (0=极低频, 100=高频重复)",
    )
    batch_volume: float = Field(
        default=50.0, ge=0, le=100,
        description="批量规模 (0=单笔, 100=大规模批量)",
    )
    similarity_rate: float = Field(
        default=50.0, ge=0, le=100,
        description="任务相似度 (0=每次不同, 100=高度相似)",
    )
    pattern_stability: float = Field(
        default=50.0, ge=0, le=100,
        description="模式稳定度 (0=频繁变化, 100=长期稳定)",
    )

    def compute_score(self) -> float:
        """加权计算重复度总分。"""
        weights = {
            "frequency": 0.30,
            "batch_volume": 0.25,
            "similarity_rate": 0.25,
            "pattern_stability": 0.20,
        }
        score = (
            self.frequency * weights["frequency"]
            + self.batch_volume * weights["batch_volume"]
            + self.similarity_rate * weights["similarity_rate"]
            + self.pattern_stability * weights["pattern_stability"]
        )
        return round(score, 2)


# ── 评估结果模型 ──────────────────────────


class TaskEvaluationResult(BaseModel):
    """单个任务的Agent化评估结果。"""
    task_name: str = Field(..., description="任务名称")
    task_description: str = Field(default="", description="任务描述")
    complexity_score: float = Field(..., ge=0, le=100, description="复杂度评分")
    repetition_score: float = Field(..., ge=0, le=100, description="重复度评分")
    quadrant: DecisionQuadrant = Field(..., description="所属象限")
    agent_suitability_score: float = Field(..., ge=0, le=100, description="Agent适配度评分 (0~100)")
    recommendation: str = Field(..., description="建议说明")
    complexity_factors: ComplexityFactors = Field(
        default_factory=ComplexityFactors,
        description="复杂度各因子详情",
    )
    repetition_factors: RepetitionFactors = Field(
        default_factory=RepetitionFactors,
        description="重复度各因子详情",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class EvaluationRequest(BaseModel):
    """评估请求体。"""
    task_name: str = Field(..., description="任务名称", examples=["客户资料录入"])
    task_description: str = Field(default="", description="任务描述")
    complexity_factors: ComplexityFactors = Field(
        default_factory=ComplexityFactors,
        description="复杂度因子 (各维度 0~100)",
    )
    repetition_factors: RepetitionFactors = Field(
        default_factory=RepetitionFactors,
        description="重复度因子 (各维度 0~100)",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class BatchEvaluationRequest(BaseModel):
    """批量评估请求体。"""
    tasks: list[EvaluationRequest] = Field(..., description="待评估任务列表", min_length=1)


class BatchEvaluationResult(BaseModel):
    """批量评估结果。"""
    results: list[TaskEvaluationResult] = Field(..., description="评估结果列表")
    summary: dict[str, int] = Field(..., description="各象限任务数统计")


class MatrixStats(BaseModel):
    """矩阵全局统计。"""
    total_tasks_evaluated: int = Field(default=0, description="累计评估任务数")
    quadrant_distribution: dict[str, int] = Field(
        default_factory=lambda: {q.value: 0 for q in DecisionQuadrant},
        description="象限分布",
    )
    avg_complexity: float = Field(default=0.0, description="平均复杂度")
    avg_repetition: float = Field(default=0.0, description="平均重复度")
    avg_suitability: float = Field(default=0.0, description="平均适配度")


class AgentReadinessCategory(BaseModel):
    """Agent化准备度分类输出。"""
    quadrant: DecisionQuadrant = Field(..., description="象限")
    label_cn: str = Field(..., description="中文标签")
    suitability_label: str = Field(..., description="适配标签")
    recommendation: str = Field(..., description="建议")
    complexity_range: tuple[float, float] = Field(..., description="复杂度范围")
    repetition_range: tuple[float, float] = Field(..., description="重复度范围")
    example_tasks: list[str] = Field(default_factory=list, description="示例任务")


__all__ = [
    "DecisionQuadrant",
    "ComplexityFactors",
    "RepetitionFactors",
    "TaskEvaluationResult",
    "EvaluationRequest",
    "BatchEvaluationRequest",
    "BatchEvaluationResult",
    "MatrixStats",
    "AgentReadinessCategory",
]
