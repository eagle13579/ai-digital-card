"""
accuracy_gate.py — F20 名片Agent准确率门禁 数据模型

核心实体:
  1. AccuracyBaseline      — 准确率基线（初始90.2%）
  2. AccuracyCheckRecord   — 门禁检查记录（CI/CD阻断决策）
  3. AccuracyCalibrationRecord — 基线校准记录（月/季度）
  4. AccuracyGateConfig    — 门禁全局配置

依赖: F18 quality_evaluator — 读取 QualityBaseline 数据作为参考基线
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Text, Boolean, JSON, Index,
)
from app.database import Base


# ──────────────────────────────────────────────
# 枚举
# ──────────────────────────────────────────────

class GateDecision(str, Enum):
    """门禁决策结果"""
    PASS = "pass"                    # 通过门禁
    BLOCK = "block"                  # 阻断（CI/CD阻断）
    WARN = "warn"                    # 告警（接近阈值，需人工确认）
    ERROR = "error"                  # 检查过程出错

    @classmethod
    def display_names(cls) -> dict[str, str]:
        return {
            "pass": "通过",
            "block": "阻断",
            "warn": "告警",
            "error": "出错",
        }


class CalibrationType(str, Enum):
    """校准类型"""
    MONTHLY = "monthly"              # 月度校准
    QUARTERLY = "quarterly"          # 季度校准
    MANUAL = "manual"                # 手动触发校准
    CI_TRIGGERED = "ci_triggered"    # CI/CD触发自动校准

    @classmethod
    def display_names(cls) -> dict[str, str]:
        return {
            "monthly": "月度校准",
            "quarterly": "季度校准",
            "manual": "手动校准",
            "ci_triggered": "CI触发校准",
        }


class CalibrationStatus(str, Enum):
    """校准状态"""
    PENDING = "pending"              # 待校准
    IN_PROGRESS = "in_progress"      # 校准中
    COMPLETED = "completed"          # 校准完成
    FAILED = "failed"                # 校准失败
    SKIPPED = "skipped"              # 跳过校准


class GateCheckSource(str, Enum):
    """门禁检查来源"""
    CI_CD = "ci_cd"                  # CI/CD流水线触发
    API = "api"                      # API手动触发
    SCHEDULED = "scheduled"          # 定时任务触发
    CALIBRATION = "calibration"      # 校准过程触发


# ──────────────────────────────────────────────
# 数据库模型
# ──────────────────────────────────────────────

class AccuracyBaseline(Base):
    """准确率基线 — 追踪名片Agent准确率标准的演化历史

    初始基线: 90.2% (2024-07-01)
    后续通过月/季度校准自动更新。
    """

    __tablename__ = "accuracy_baselines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    baseline_id = Column(String(64), unique=True, nullable=False, index=True, comment="基线唯一标识")

    # 基线标识
    name = Column(String(128), nullable=False, comment="基线名称（如: v1.0初始基线 / 2024Q3季度基线）")
    description = Column(Text, nullable=True, comment="基线描述")

    # 准确率阈值 — 核心指标
    accuracy_threshold = Column(Float, nullable=False, comment="准确率阈值（百分比，如90.2）")
    pass_immediately = Column(Float, nullable=True, comment="立即通过阈值（高于此值直接通过，百分比）")
    warn_threshold = Column(Float, nullable=True, comment="告警阈值（低于此值触发告警，百分比）")

    # 关联F18质量基线
    quality_baseline_id = Column(String(64), nullable=True, comment="关联的F18 QualityBaseline ID")
    quality_avg_total = Column(Float, nullable=True, comment="关联的F18质量评估平均分（5分制）")

    # 统计信息
    sample_count = Column(Integer, default=0, comment="参与基线计算的样本数")
    passing_count = Column(Integer, default=0, comment="达标样本数")
    passing_rate = Column(Float, nullable=True, comment="达标率（百分比）")

    # 版本信息
    agent_version = Column(String(64), nullable=True, index=True, comment="Agent版本号")
    model_name = Column(String(128), nullable=True, comment="评估模型名称")

    # 校准信息
    calibration_type = Column(String(32), default="manual", comment="校准类型")
    calibration_id = Column(String(64), nullable=True, comment="关联校准记录ID")
    is_active = Column(Boolean, default=True, comment="是否为当前活跃基线")
    is_archived = Column(Boolean, default=False, comment="是否已归档")

    # 元数据
    meta_data = Column(JSON, nullable=True, comment="附加元数据（包含F18数据快照等）")

    # 时间
    effective_from = Column(DateTime, nullable=False, comment="基线生效时间")
    effective_until = Column(DateTime, nullable=True, comment="基线失效时间（被新基线取代时设置）")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_accuracy_baseline_active", "is_active"),
        Index("idx_accuracy_baseline_version", "agent_version"),
        Index("idx_accuracy_baseline_effective", "effective_from"),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "baseline_id": self.baseline_id,
            "name": self.name,
            "description": self.description,
            "accuracy_threshold": self.accuracy_threshold,
            "pass_immediately": self.pass_immediately,
            "warn_threshold": self.warn_threshold,
            "quality_baseline_id": self.quality_baseline_id,
            "quality_avg_total": self.quality_avg_total,
            "sample_count": self.sample_count,
            "passing_count": self.passing_count,
            "passing_rate": self.passing_rate,
            "agent_version": self.agent_version,
            "model_name": self.model_name,
            "calibration_type": self.calibration_type,
            "calibration_id": self.calibration_id,
            "is_active": self.is_active,
            "is_archived": self.is_archived,
            "meta_data": self.meta_data,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "effective_until": self.effective_until.isoformat() if self.effective_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<AccuracyBaseline '{self.name}' "
            f"threshold={self.accuracy_threshold}% "
            f"active={self.is_active}>"
        )


class AccuracyCheckRecord(Base):
    """门禁检查记录 — 每次CI/CD或API触发的门禁检查

    记录:
      - 当前准确率 vs 基线对比结果
      - 门禁决策（通过/阻断/告警）
      - 阻断详情和上下文
    """

    __tablename__ = "accuracy_check_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    check_id = Column(String(64), unique=True, nullable=False, index=True, comment="检查唯一标识")

    # 检查来源
    source = Column(String(32), nullable=False, default="api", comment="检查来源（ci_cd/api/scheduled/calibration）")

    # 基线信息（检查时快照）
    baseline_id = Column(String(64), nullable=False, comment="检查时使用的基线ID")
    baseline_threshold = Column(Float, nullable=False, comment="检查时基线的准确率阈值")
    baseline_name = Column(String(128), nullable=True, comment="检查时基线名称")

    # 当前准确率
    current_accuracy = Column(Float, nullable=False, comment="当前准确率（百分比）")
    current_sample_count = Column(Integer, default=0, comment="当前评估样本数")
    current_passing_count = Column(Integer, default=0, comment="当前达标样本数")

    # 偏差
    deviation = Column(Float, nullable=True, comment="与基线偏差（当前 - 基线阈值，百分比）")
    deviation_percent = Column(Float, nullable=True, comment="偏差百分比（相对基线的变化率）")

    # 门禁决策
    decision = Column(String(32), nullable=False, comment="门禁决策（pass/block/warn/error）")
    passed = Column(Boolean, nullable=False, comment="是否通过门禁")
    blocked = Column(Boolean, default=False, comment="是否被阻断")

    # F18 质量评估参考
    quality_avg_total = Column(Float, nullable=True, comment="F18质量评估平均分（参考）")
    quality_baseline_total = Column(Float, nullable=True, comment="F18质量基线平均分（参考）")

    # 阻断详情
    block_reason = Column(Text, nullable=True, comment="阻断原因描述")
    block_details = Column(JSON, nullable=True, comment="阻断详细数据（维度明细、建议等）")

    # CI/CD 上下文
    ci_pipeline_id = Column(String(128), nullable=True, comment="CI/CD流水线ID")
    ci_build_number = Column(String(64), nullable=True, comment="CI/CD构建编号")
    ci_commit_sha = Column(String(64), nullable=True, comment="CI/CD提交SHA")
    ci_branch = Column(String(128), nullable=True, comment="CI/CD分支名")

    # 元数据
    meta_data = Column(JSON, nullable=True, comment="附加元数据")

    # 时间
    checked_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="检查时间")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")

    __table_args__ = (
        Index("idx_accuracy_check_source", "source"),
        Index("idx_accuracy_check_decision", "decision"),
        Index("idx_accuracy_check_time", "checked_at"),
        Index("idx_accuracy_check_baseline", "baseline_id"),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "check_id": self.check_id,
            "source": self.source,
            "baseline_id": self.baseline_id,
            "baseline_threshold": self.baseline_threshold,
            "baseline_name": self.baseline_name,
            "current_accuracy": self.current_accuracy,
            "current_sample_count": self.current_sample_count,
            "current_passing_count": self.current_passing_count,
            "deviation": self.deviation,
            "deviation_percent": self.deviation_percent,
            "decision": self.decision,
            "passed": self.passed,
            "blocked": self.blocked,
            "quality_avg_total": self.quality_avg_total,
            "quality_baseline_total": self.quality_baseline_total,
            "block_reason": self.block_reason,
            "block_details": self.block_details,
            "ci_pipeline_id": self.ci_pipeline_id,
            "ci_build_number": self.ci_build_number,
            "ci_commit_sha": self.ci_commit_sha,
            "ci_branch": self.ci_branch,
            "meta_data": self.meta_data,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<AccuracyCheckRecord '{self.check_id}' "
            f"decision={self.decision} "
            f"acc={self.current_accuracy}% "
            f"baseline={self.baseline_threshold}%>"
        )


class AccuracyCalibrationRecord(Base):
    """基线校准记录 — 月/季度基线校准事件

    校准流程:
      1. 读取F18 QualityBaseline的最新数据
      2. 计算当前准确率统计
      3. 对比旧基线，生成新基线
      4. 发送校准通知
    """

    __tablename__ = "accuracy_calibration_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    calibration_id = Column(String(64), unique=True, nullable=False, index=True, comment="校准唯一标识")

    # 校准信息
    calibration_type = Column(String(32), nullable=False, comment="校准类型（monthly/quarterly/manual/ci_triggered）")
    status = Column(String(32), nullable=False, default="completed", comment="校准状态")

    # 旧基线（校准前）
    old_baseline_id = Column(String(64), nullable=True, comment="旧基线ID")
    old_accuracy_threshold = Column(Float, nullable=True, comment="旧基线阈值")

    # 新基线（校准后）
    new_baseline_id = Column(String(64), nullable=True, comment="新基线ID")
    new_accuracy_threshold = Column(Float, nullable=True, comment="新基线阈值")
    new_pass_immediately = Column(Float, nullable=True, comment="新立即通过阈值")
    new_warn_threshold = Column(Float, nullable=True, comment="新告警阈值")

    # 变化量
    delta = Column(Float, nullable=True, comment="阈值变化量（新-旧，百分比）")
    delta_percent = Column(Float, nullable=True, comment="变化百分比")

    # F18数据参考
    quality_baseline_id = Column(String(64), nullable=True, comment="参考的F18 QualityBaseline ID")
    quality_avg_total = Column(Float, nullable=True, comment="F18质量评估平均分")

    # 统计
    sample_count = Column(Integer, default=0, comment="参与校准的样本数")
    passing_count = Column(Integer, default=0, comment="达标样本数")
    passing_rate = Column(Float, nullable=True, comment="达标率")

    # 校准详情
    details = Column(JSON, nullable=True, comment="校准详细数据")
    error_message = Column(Text, nullable=True, comment="校准失败原因")
    notification_sent = Column(Boolean, default=False, comment="是否已发送校准通知")
    notification_channels = Column(JSON, nullable=True, comment="通知渠道（如: [\"email\", \"webhook\", \"slack\"]）")

    # 元数据
    meta_data = Column(JSON, nullable=True, comment="附加元数据")

    # 时间
    calibrated_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="校准完成时间")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")

    __table_args__ = (
        Index("idx_accuracy_calib_type", "calibration_type"),
        Index("idx_accuracy_calib_status", "status"),
        Index("idx_accuracy_calib_time", "calibrated_at"),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "calibration_id": self.calibration_id,
            "calibration_type": self.calibration_type,
            "status": self.status,
            "old_baseline_id": self.old_baseline_id,
            "old_accuracy_threshold": self.old_accuracy_threshold,
            "new_baseline_id": self.new_baseline_id,
            "new_accuracy_threshold": self.new_accuracy_threshold,
            "new_pass_immediately": self.new_pass_immediately,
            "new_warn_threshold": self.new_warn_threshold,
            "delta": self.delta,
            "delta_percent": self.delta_percent,
            "quality_baseline_id": self.quality_baseline_id,
            "quality_avg_total": self.quality_avg_total,
            "sample_count": self.sample_count,
            "passing_count": self.passing_count,
            "passing_rate": self.passing_rate,
            "details": self.details,
            "error_message": self.error_message,
            "notification_sent": self.notification_sent,
            "notification_channels": self.notification_channels,
            "meta_data": self.meta_data,
            "calibrated_at": self.calibrated_at.isoformat() if self.calibrated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<AccuracyCalibrationRecord '{self.calibration_id}' "
            f"type={self.calibration_type} "
            f"delta={self.delta}%>"
        )


class AccuracyGateConfig(Base):
    """门禁全局配置 — 控制门禁行为

    Singleton行模式：实际使用时通过gate_config_id='default'获取配置。
    """

    __tablename__ = "accuracy_gate_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gate_config_id = Column(String(64), unique=True, nullable=False, index=True, comment="配置唯一标识")

    # 门禁开关
    enabled = Column(Boolean, default=True, comment="门禁总开关")
    ci_block_enabled = Column(Boolean, default=True, comment="CI/CD自动阻断开关")

    # 默认阈值
    default_accuracy_threshold = Column(Float, default=90.2, comment="默认准确率阈值（百分比）")
    default_pass_immediately = Column(Float, default=95.0, comment="默认立即通过阈值（高于此值直接通过）")
    default_warn_threshold = Column(Float, default=85.0, comment="默认告警阈值（低于此值触发告警）")

    # CI/CD配置
    ci_block_on_warn = Column(Boolean, default=False, comment="告警级别是否阻断CI/CD")
    ci_required_samples = Column(Integer, default=20, comment="CI/CD检查最低样本数要求")
    ci_auto_calibrate_on_degradation = Column(Boolean, default=False, comment="持续降级时自动触发校准")

    # 校准配置
    auto_calibrate = Column(Boolean, default=True, comment="自动校准开关")
    monthly_calibration_day = Column(Integer, default=1, comment="月度校准日期（1-28）")
    quarterly_calibration_month = Column(Integer, default=1, comment="季度校准起始月份（1-12）")
    notify_on_calibration = Column(Boolean, default=True, comment="校准后是否发送通知")

    # 通知渠道
    notification_channels = Column(JSON, nullable=True, comment="通知渠道配置")

    # 元数据
    meta_data = Column(JSON, nullable=True, comment="附加元数据")

    # 时间
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "gate_config_id": self.gate_config_id,
            "enabled": self.enabled,
            "ci_block_enabled": self.ci_block_enabled,
            "default_accuracy_threshold": self.default_accuracy_threshold,
            "default_pass_immediately": self.default_pass_immediately,
            "default_warn_threshold": self.default_warn_threshold,
            "ci_block_on_warn": self.ci_block_on_warn,
            "ci_required_samples": self.ci_required_samples,
            "ci_auto_calibrate_on_degradation": self.ci_auto_calibrate_on_degradation,
            "auto_calibrate": self.auto_calibrate,
            "monthly_calibration_day": self.monthly_calibration_day,
            "quarterly_calibration_month": self.quarterly_calibration_month,
            "notify_on_calibration": self.notify_on_calibration,
            "notification_channels": self.notification_channels,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<AccuracyGateConfig '{self.gate_config_id}' "
            f"enabled={self.enabled} "
            f"threshold={self.default_accuracy_threshold}%>"
        )
