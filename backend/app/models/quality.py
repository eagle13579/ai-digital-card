"""
quality.py — F18 Agent质量评估看板 数据模型

5维度评分模型 / 评测样本管理 / 基线追踪
依赖: F17 Canary (灰度发布) — 用于关联灰度部署版本的质量评估
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Text, Boolean, JSON, ForeignKey, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ──────────────────────────────────────────────
# 枚举
# ──────────────────────────────────────────────

class QualityDimension(str, Enum):
    """5个质量评估维度"""
    USEFULNESS = "usefulness"          # 有用性 — 回答是否满足用户需求
    ACCURACY = "accuracy"              # 准确性 — 事实是否正确
    COMPLETENESS = "completeness"      # 完整性 — 是否全面覆盖问题
    COHERENCE = "coherence"            # 连贯性 — 逻辑和表达是否流畅
    HARMLESSNESS = "harmlessness"      # 无害性 — 是否安全无风险

    @classmethod
    def all_dimensions(cls) -> list[QualityDimension]:
        return list(cls)

    @classmethod
    def display_names(cls) -> dict[str, str]:
        return {
            "usefulness": "有用性",
            "accuracy": "准确性",
            "completeness": "完整性",
            "coherence": "连贯性",
            "harmlessness": "无害性",
        }


class EvalMethod(str, Enum):
    """评估方法"""
    LM_AS_JUDGE = "lm_as_judge"       # LM-as-Judge 自动评估
    HUMAN = "human"                    # 人工评估
    HYBRID = "hybrid"                  # 混合评估


class EvalStatus(str, Enum):
    """评估状态"""
    PENDING = "pending"                # 待评估
    RUNNING = "running"                # 评估中
    COMPLETED = "completed"            # 已完成
    FAILED = "failed"                  # 评估失败


# ──────────────────────────────────────────────
# 数据库模型
# ──────────────────────────────────────────────

class QualitySample(Base):
    """评测样本 — 代表一次完整的评估单元（输入 + Agent输出 + 评分）"""

    __tablename__ = "quality_samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_id = Column(String(64), unique=True, nullable=False, index=True, comment="样本唯一标识")

    # 样本内容
    input_text = Column(Text, nullable=False, comment="用户输入/问题")
    agent_output = Column(Text, nullable=False, comment="Agent 输出/回答")
    expected_output = Column(Text, nullable=True, comment="预期输出（可选，用于参考）")
    category = Column(String(64), nullable=True, index=True, comment="样本分类（如：问答/任务/推理）")
    tags = Column(JSON, nullable=True, comment="样本标签")
    sample_meta = Column(JSON, nullable=True, comment="附加元数据")

    # 关联信息
    canary_deployment_id = Column(String(64), nullable=True, comment="关联的灰度部署ID（F17）")
    agent_version = Column(String(64), nullable=True, comment="Agent版本号")
    model_name = Column(String(128), nullable=True, comment="使用的模型名称")

    # 评估状态
    status = Column(String(32), default="pending", nullable=False, comment="评估状态")
    eval_method = Column(String(32), default="lm_as_judge", nullable=False, comment="评估方法")

    # 5维度评分 (0.0 - 5.0)
    score_usefulness = Column(Float, nullable=True, comment="有用性评分")
    score_accuracy = Column(Float, nullable=True, comment="准确性评分")
    score_completeness = Column(Float, nullable=True, comment="完整性评分")
    score_coherence = Column(Float, nullable=True, comment="连贯性评分")
    score_harmlessness = Column(Float, nullable=True, comment="无害性评分")

    # 总分（平均分）
    score_total = Column(Float, nullable=True, comment="总分（5维度平均）")

    # 评估详情
    eval_detail = Column(JSON, nullable=True, comment="每维度评估详情（含评语/推理）")
    eval_log = Column(Text, nullable=True, comment="评估日志")
    error_message = Column(Text, nullable=True, comment="评估失败原因")

    # 评估时间
    evaluated_at = Column(DateTime, nullable=True, comment="评估完成时间")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 索引
    __table_args__ = (
        Index("idx_quality_sample_status", "status"),
        Index("idx_quality_sample_category", "category"),
        Index("idx_quality_sample_created", "created_at"),
    )

    def get_scores(self) -> dict[str, float | None]:
        """获取5维度评分字典"""
        return {
            "usefulness": self.score_usefulness,
            "accuracy": self.score_accuracy,
            "completeness": self.score_completeness,
            "coherence": self.score_coherence,
            "harmlessness": self.score_harmlessness,
        }

    def set_score(self, dimension: str, score: float, detail: dict[str, Any] | None = None) -> None:
        """设置指定维度的评分"""
        dimension_map = {
            "usefulness": "score_usefulness",
            "accuracy": "score_accuracy",
            "completeness": "score_completeness",
            "coherence": "score_coherence",
            "harmlessness": "score_harmlessness",
        }
        col = dimension_map.get(dimension)
        if col:
            setattr(self, col, round(max(0.0, min(5.0, score)), 2))

    def get_total_score(self) -> float | None:
        """计算5维度平均分"""
        scores = [getattr(self, f"score_{d.value}") for d in QualityDimension]
        valid = [s for s in scores if s is not None]
        if valid:
            return round(sum(valid) / len(valid), 2)
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sample_id": self.sample_id,
            "input_text": self.input_text,
            "agent_output": self.agent_output,
            "expected_output": self.expected_output,
            "category": self.category,
            "tags": self.tags,
            "sample_meta": self.sample_meta,
            "canary_deployment_id": self.canary_deployment_id,
            "agent_version": self.agent_version,
            "model_name": self.model_name,
            "status": self.status,
            "eval_method": self.eval_method,
            "scores": self.get_scores(),
            "score_total": self.score_total or self.get_total_score(),
            "eval_detail": self.eval_detail,
            "eval_log": self.eval_log,
            "error_message": self.error_message,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<QualitySample '{self.sample_id}' "
            f"cat={self.category} "
            f"status={self.status} "
            f"score={self.score_total}>"
        )


class QualityBaseline(Base):
    """质量基线 — 追踪不同版本/模型的质量变化趋势"""

    __tablename__ = "quality_baselines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    baseline_id = Column(String(64), unique=True, nullable=False, index=True, comment="基线唯一标识")

    # 基线标识
    name = Column(String(128), nullable=False, comment="基线名称")
    description = Column(Text, nullable=True, comment="基线描述")
    agent_version = Column(String(64), nullable=True, index=True, comment="Agent版本号")
    model_name = Column(String(128), nullable=True, index=True, comment="模型名称")

    # 关联灰度部署
    canary_deployment_id = Column(String(64), nullable=True, comment="关联灰度部署ID")

    # 5维度平均分
    avg_usefulness = Column(Float, nullable=True, comment="平均有用性")
    avg_accuracy = Column(Float, nullable=True, comment="平均准确性")
    avg_completeness = Column(Float, nullable=True, comment="平均完整性")
    avg_coherence = Column(Float, nullable=True, comment="平均连贯性")
    avg_harmlessness = Column(Float, nullable=True, comment="平均无害性")
    avg_total = Column(Float, nullable=True, comment="总体平均分")

    # 统计信息
    sample_count = Column(Integer, default=0, comment="评测样本数")
    passing_count = Column(Integer, default=0, comment="达标样本数（总分 >= passing_threshold）")
    passing_rate = Column(Float, nullable=True, comment="达标率")
    passing_threshold = Column(Float, default=3.0, comment="达标阈值")

    # 维度明细（各维度评分分布）
    score_distribution = Column(JSON, nullable=True, comment="评分分布统计")

    # 元数据
    tags = Column(JSON, nullable=True, comment="基线标签")
    sample_meta = Column(JSON, nullable=True, comment="附加元数据")
    is_active = Column(Boolean, default=True, comment="是否为当前活跃基线")
    is_archived = Column(Boolean, default=False, comment="是否已归档")

    # 时间
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    evaluated_at = Column(DateTime, nullable=True, comment="基线评估时间")

    __table_args__ = (
        Index("idx_quality_baseline_version", "agent_version", "model_name"),
        Index("idx_quality_baseline_active", "is_active"),
    )

    def get_avg_scores(self) -> dict[str, float | None]:
        return {
            "usefulness": self.avg_usefulness,
            "accuracy": self.avg_accuracy,
            "completeness": self.avg_completeness,
            "coherence": self.avg_coherence,
            "harmlessness": self.avg_harmlessness,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "baseline_id": self.baseline_id,
            "name": self.name,
            "description": self.description,
            "agent_version": self.agent_version,
            "model_name": self.model_name,
            "canary_deployment_id": self.canary_deployment_id,
            "avg_scores": self.get_avg_scores(),
            "avg_total": self.avg_total,
            "sample_count": self.sample_count,
            "passing_count": self.passing_count,
            "passing_rate": self.passing_rate,
            "passing_threshold": self.passing_threshold,
            "score_distribution": self.score_distribution,
            "tags": self.tags,
            "sample_meta": self.sample_meta,
            "is_active": self.is_active,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<QualityBaseline '{self.name}' "
            f"v={self.agent_version} "
            f"samples={self.sample_count} "
            f"avg={self.avg_total}>"
        )


class QualityEvalJob(Base):
    """批量评估任务 — 一次完整的评估执行记录"""

    __tablename__ = "quality_eval_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(64), unique=True, nullable=False, index=True, comment="任务唯一标识")

    # 任务配置
    status = Column(String(32), default="pending", nullable=False, comment="任务状态")
    eval_method = Column(String(32), default="lm_as_judge", comment="评估方法")
    sample_ids = Column(JSON, nullable=True, comment="关联样本ID列表")
    model_config = Column(JSON, nullable=True, comment="评估模型配置")

    # 统计
    total_samples = Column(Integer, default=0, comment="总样本数")
    completed_samples = Column(Integer, default=0, comment="已完成数")
    failed_samples = Column(Integer, default=0, comment="失败数")

    # 基线关联
    baseline_id = Column(String(64), nullable=True, comment="关联基线ID")

    # 结果摘要
    summary = Column(JSON, nullable=True, comment="评估结果摘要")

    # 时间
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "status": self.status,
            "eval_method": self.eval_method,
            "sample_ids": self.sample_ids,
            "model_config": self.model_config,
            "total_samples": self.total_samples,
            "completed_samples": self.completed_samples,
            "failed_samples": self.failed_samples,
            "baseline_id": self.baseline_id,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<QualityEvalJob '{self.job_id}' "
            f"status={self.status} "
            f"{self.completed_samples}/{self.total_samples}>"
        )
