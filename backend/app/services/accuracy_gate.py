"""
accuracy_gate.py — F20 名片Agent准确率门禁引擎

核心能力:
  1. 基线对比 — 当前准确率 vs 活跃基线
  2. 门禁检查 — CI/CD自动阻断决策
  3. CI阻断 — 完整阻断信息
  4. 月/季度基线校准
  5. 校准通知

依赖:
  - F18 quality_evaluator: 读取 QualityBaseline / EvalResult
  - 底层: SQLAlchemy ORM + AsyncSession

初始基线: 90.2% (UTC 2024-07-01)
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, func, desc, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.accuracy_gate import (
    AccuracyBaseline,
    AccuracyCheckRecord,
    AccuracyCalibrationRecord,
    AccuracyGateConfig,
    GateDecision,
    CalibrationType,
    CalibrationStatus,
    GateCheckSource,
)
from app.models.quality import QualityBaseline, QualitySample, QualityDimension, EvalStatus

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 默认常量
# ──────────────────────────────────────────────

INITIAL_ACCURACY_THRESHOLD = 90.2        # 初始基线: 90.2%
INITIAL_PASS_IMMEDIATELY = 95.0          # 立即通过: 95%
INITIAL_WARN_THRESHOLD = 85.0            # 告警阈值: 85%
DEFAULT_CI_REQUIRED_SAMPLES = 20         # CI/CD最低样本数
BASELINE_VERSION = "v1.0"                # 初始基线版本号
INITIAL_BASELINE_NAME = "v1.0 初始基线"   # 初始基线名称


# ──────────────────────────────────────────────
# 异常
# ──────────────────────────────────────────────

class AccuracyGateError(Exception):
    """准确率门禁异常"""
    pass


class BaselineNotFoundError(AccuracyGateError):
    """基线不存在"""
    pass


class GateConfigNotFoundError(AccuracyGateError):
    """门禁配置不存在"""
    pass


class InsufficientSamplesError(AccuracyGateError):
    """样本数不足，无法执行门禁检查"""
    pass


class CalibrationError(AccuracyGateError):
    """校准过程异常"""
    pass


# ──────────────────────────────────────────────
# 数据类
# ──────────────────────────────────────────────

@dataclass
class GateCheckResult:
    """门禁检查结果"""
    check_id: str
    decision: str                 # "pass" / "block" / "warn" / "error"
    passed: bool
    blocked: bool
    current_accuracy: float
    baseline_threshold: float
    deviation: float | None
    deviation_percent: float | None
    sample_count: int
    block_reason: str | None = None
    block_details: dict[str, Any] | None = None
    quality_avg_total: float | None = None
    quality_baseline_total: float | None = None
    source: str = "api"

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "decision": self.decision,
            "passed": self.passed,
            "blocked": self.blocked,
            "current_accuracy": self.current_accuracy,
            "baseline_threshold": self.baseline_threshold,
            "deviation": self.deviation,
            "deviation_percent": self.deviation_percent,
            "sample_count": self.sample_count,
            "block_reason": self.block_reason,
            "block_details": self.block_details,
            "quality_avg_total": self.quality_avg_total,
            "quality_baseline_total": self.quality_baseline_total,
            "source": self.source,
        }


@dataclass
class CalibrationResult:
    """基线校准结果"""
    calibration_id: str
    calibration_type: str
    status: str
    old_threshold: float | None
    new_threshold: float
    delta: float | None
    sample_count: int
    passing_rate: float | None
    quality_avg_total: float | None
    notification_sent: bool
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "calibration_id": self.calibration_id,
            "calibration_type": self.calibration_type,
            "status": self.status,
            "old_threshold": self.old_threshold,
            "new_threshold": self.new_threshold,
            "delta": self.delta,
            "sample_count": self.sample_count,
            "passing_rate": self.passing_rate,
            "quality_avg_total": self.quality_avg_total,
            "notification_sent": self.notification_sent,
            "error_message": self.error_message,
        }


# ──────────────────────────────────────────────
# 准确率门禁引擎
# ──────────────────────────────────────────────

class AccuracyGate:
    """
    F20 名片Agent准确率门禁引擎。

    核心职责:
      1. 维持准确率基线（初始90.2%），与F18质量基线联动
      2. 执行门禁检查，对比当前准确率 vs 基线
      3. CI/CD自动阻断 — 低于基线则阻断流水线
      4. 月/季度基线校准 — 自动更新基线阈值
      5. 校准通知 — 校准完成后通知相关方
    """

    def __init__(self):
        logger.info("F20 名片Agent准确率门禁引擎初始化完成")

    # ══════════════════════════════════════════
    # 基线管理
    # ══════════════════════════════════════════

    async def initialize_default_baseline(
        self,
        db: AsyncSession | None = None,
    ) -> AccuracyBaseline:
        """初始化默认基线（90.2%）。如已有活跃基线则跳过。"""
        async with self._get_session(db) as session:
            # 检查是否已有活跃基线
            result = await session.execute(
                select(AccuracyBaseline).where(
                    AccuracyBaseline.is_active == True,
                    AccuracyBaseline.is_archived == False,
                ).limit(1)
            )
            existing = result.scalar_one_or_none()
            if existing:
                logger.info("活跃基线已存在: %s (threshold=%s%%)",
                            existing.name, existing.accuracy_threshold)
                return existing

            # 查找F18的活跃质量基线作为参考
            quality_baseline = await self._get_active_quality_baseline(session)

            baseline = AccuracyBaseline(
                baseline_id=f"ab_{uuid.uuid4().hex[:16]}",
                name=INITIAL_BASELINE_NAME,
                description="名片Agent初始准确率基线（来自F20门禁系统）",
                accuracy_threshold=INITIAL_ACCURACY_THRESHOLD,
                pass_immediately=INITIAL_PASS_IMMEDIATELY,
                warn_threshold=INITIAL_WARN_THRESHOLD,
                quality_baseline_id=quality_baseline.baseline_id if quality_baseline else None,
                quality_avg_total=quality_baseline.avg_total if quality_baseline else None,
                sample_count=0,
                passing_count=0,
                passing_rate=None,
                agent_version=BASELINE_VERSION,
                calibration_type="manual",
                is_active=True,
                is_archived=False,
                metadata={
                    "source": "F20_initialization",
                    "initial_quality_baseline": quality_baseline.to_dict() if quality_baseline else None,
                },
                effective_from=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(baseline)
            await session.commit()
            await session.refresh(baseline)
            logger.info("初始基线已创建: %s (threshold=%s%%)",
                        baseline.name, baseline.accuracy_threshold)

            # 同时初始化默认门禁配置
            await self._ensure_gate_config(session)

            return baseline

    async def get_active_baseline(
        self,
        db: AsyncSession | None = None,
    ) -> AccuracyBaseline | None:
        """获取当前活跃基线"""
        async with self._get_session(db) as session:
            result = await session.execute(
                select(AccuracyBaseline).where(
                    AccuracyBaseline.is_active == True,
                    AccuracyBaseline.is_archived == False,
                ).order_by(desc(AccuracyBaseline.effective_from)).limit(1)
            )
            return result.scalar_one_or_none()

    async def get_baseline_by_id(
        self,
        baseline_id: str,
        db: AsyncSession | None = None,
    ) -> AccuracyBaseline | None:
        """按ID获取基线"""
        async with self._get_session(db) as session:
            result = await session.execute(
                select(AccuracyBaseline).where(AccuracyBaseline.baseline_id == baseline_id)
            )
            return result.scalar_one_or_none()

    async def list_baselines(
        self,
        include_archived: bool = False,
        limit: int = 20,
        offset: int = 0,
        db: AsyncSession | None = None,
    ) -> tuple[list[AccuracyBaseline], int]:
        """列出所有基线"""
        async with self._get_session(db) as session:
            query = select(AccuracyBaseline)
            count_query = select(func.count(AccuracyBaseline.id))
            if not include_archived:
                query = query.where(AccuracyBaseline.is_archived == False)
                count_query = count_query.where(AccuracyBaseline.is_archived == False)
            query = query.order_by(desc(AccuracyBaseline.effective_from)).offset(offset).limit(limit)

            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0

            result = await session.execute(query)
            baselines = list(result.scalars().all())
            return baselines, total

    # ══════════════════════════════════════════
    # 门禁检查
    # ══════════════════════════════════════════

    async def run_gate_check(
        self,
        source: str = "api",
        accuracy_override: float | None = None,
        sample_count_override: int | None = None,
        ci_context: dict[str, Any] | None = None,
        db: AsyncSession | None = None,
    ) -> GateCheckResult:
        """执行门禁检查

        Args:
            source: 检查来源
            accuracy_override: 直接传入准确率（不自动计算）
            sample_count_override: 样本数覆盖
            ci_context: CI/CD上下文（pipeline_id, build_number, commit_sha, branch）
            db: 数据库会话

        Returns:
            GateCheckResult: 门禁检查结果
        """
        check_id = f"gc_{uuid.uuid4().hex[:16]}"
        async with self._get_session(db) as session:
            # 1. 获取活跃基线
            baseline = await self.get_active_baseline(session)
            if not baseline:
                raise BaselineNotFoundError("没有活跃基线，请先初始化基线")

            # 2. 获取门禁配置
            config = await self._get_gate_config(session)

            # 3. 计算当前准确率
            if accuracy_override is not None:
                current_accuracy = accuracy_override
                current_sample_count = sample_count_override or 0
                current_passing_count = 0
            else:
                current_accuracy, current_sample_count, current_passing_count = (
                    await self._compute_current_accuracy(session, config)
                )

            # 4. 获取F18质量参考
            quality_baseline = await self._get_active_quality_baseline(session)
            quality_total = quality_baseline.avg_total if quality_baseline else None

            # 5. 计算偏差
            threshold = baseline.accuracy_threshold
            deviation = round(current_accuracy - threshold, 2)
            deviation_percent = (
                round((deviation / threshold) * 100, 2) if threshold > 0 else None
            )

            # 6. 门禁决策
            pass_immediately = baseline.pass_immediately or config.default_pass_immediately
            warn_threshold = baseline.warn_threshold or config.default_warn_threshold
            ci_required = config.ci_required_samples

            # 6a. 样本数不足检查
            if current_sample_count < ci_required:
                decision = GateDecision.WARN.value
                block_reason = (
                    f"评估样本数不足: {current_sample_count}/{ci_required}，"
                    f"无法做出可靠的门禁决策"
                )
                block_details = {
                    "required_samples": ci_required,
                    "actual_samples": current_sample_count,
                    "suggestion": "请增加评估样本数量后再检查",
                }
                result_passed = False
                result_blocked = False
            # 6b. 立即通过
            elif current_accuracy >= pass_immediately:
                decision = GateDecision.PASS.value
                block_reason = None
                block_details = None
                result_passed = True
                result_blocked = False
            # 6c. 高于基线，通过
            elif current_accuracy >= threshold:
                decision = GateDecision.PASS.value
                block_reason = None
                block_details = None
                result_passed = True
                result_blocked = False
            # 6d. 低于告警阈值 — 阻断
            elif current_accuracy < warn_threshold:
                decision = GateDecision.BLOCK.value
                result_passed = False
                result_blocked = True
                block_reason = (
                    f"准确率 {current_accuracy}% 低于告警阈值 {warn_threshold}%，"
                    f"CI/CD自动阻断！基线阈值: {threshold}%"
                )
                block_details = {
                    "current_accuracy": current_accuracy,
                    "baseline_threshold": threshold,
                    "warn_threshold": warn_threshold,
                    "deviation": deviation,
                    "dimension_breakdown": await self._get_dimension_breakdown(session),
                    "suggestion": "请检查Agent最新变更是否引入了准确率退化",
                }
            # 6e. 低于基线但高于告警阈值 — 根据配置决定是否阻断
            elif current_accuracy < threshold:
                if config.ci_block_enabled and source == GateCheckSource.CI_CD.value:
                    decision = GateDecision.BLOCK.value if config.ci_block_on_warn else GateDecision.WARN.value
                else:
                    decision = GateDecision.WARN.value
                result_passed = decision == GateDecision.PASS.value
                result_blocked = decision == GateDecision.BLOCK.value
                block_reason = (
                    f"准确率 {current_accuracy}% 低于基线 {threshold}% "
                    f"(偏差: {deviation:+.2f}%)"
                    if decision == GateDecision.BLOCK.value or decision == GateDecision.WARN.value
                    else None
                )
                block_details = {
                    "current_accuracy": current_accuracy,
                    "baseline_threshold": threshold,
                    "deviation": deviation,
                    "decision_level": decision,
                } if decision != GateDecision.PASS.value else None
            else:
                decision = GateDecision.PASS.value
                result_passed = True
                result_blocked = False
                block_reason = None
                block_details = None

            # 7. 保存检查记录
            ci_pipeline_id = None
            ci_build_number = None
            ci_commit_sha = None
            ci_branch = None
            if ci_context:
                ci_pipeline_id = ci_context.get("pipeline_id")
                ci_build_number = ci_context.get("build_number")
                ci_commit_sha = ci_context.get("commit_sha")
                ci_branch = ci_context.get("branch")

            record = AccuracyCheckRecord(
                check_id=check_id,
                source=source,
                baseline_id=baseline.baseline_id,
                baseline_threshold=threshold,
                baseline_name=baseline.name,
                current_accuracy=current_accuracy,
                current_sample_count=current_sample_count,
                current_passing_count=current_passing_count,
                deviation=deviation,
                deviation_percent=deviation_percent,
                decision=decision,
                passed=result_passed,
                blocked=result_blocked,
                quality_avg_total=quality_total,
                quality_baseline_total=quality_baseline.avg_total if quality_baseline else None,
                block_reason=block_reason,
                block_details=block_details,
                ci_pipeline_id=ci_pipeline_id,
                ci_build_number=ci_build_number,
                ci_commit_sha=ci_commit_sha,
                ci_branch=ci_branch,
                checked_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)

            logger.info(
                "门禁检查完成: %s | decision=%s | acc=%s%% vs baseline=%s%% | deviation=%s",
                check_id, decision, current_accuracy, threshold, deviation,
            )

            return GateCheckResult(
                check_id=check_id,
                decision=decision,
                passed=result_passed,
                blocked=result_blocked,
                current_accuracy=current_accuracy,
                baseline_threshold=threshold,
                deviation=deviation,
                deviation_percent=deviation_percent,
                sample_count=current_sample_count,
                block_reason=block_reason,
                block_details=block_details,
                quality_avg_total=quality_total,
                quality_baseline_total=quality_baseline.avg_total if quality_baseline else None,
                source=source,
            )

    async def get_check_history(
        self,
        limit: int = 50,
        offset: int = 0,
        source: str | None = None,
        decision: str | None = None,
        db: AsyncSession | None = None,
    ) -> tuple[list[AccuracyCheckRecord], int]:
        """获取门禁检查历史"""
        async with self._get_session(db) as session:
            query = select(AccuracyCheckRecord)
            count_query = select(func.count(AccuracyCheckRecord.id))

            if source:
                query = query.where(AccuracyCheckRecord.source == source)
                count_query = count_query.where(AccuracyCheckRecord.source == source)
            if decision:
                query = query.where(AccuracyCheckRecord.decision == decision)
                count_query = count_query.where(AccuracyCheckRecord.decision == decision)

            query = query.order_by(desc(AccuracyCheckRecord.checked_at)).offset(offset).limit(limit)

            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0

            result = await session.execute(query)
            records = list(result.scalars().all())
            return records, total

    async def get_gate_status(
        self,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """获取门禁系统状态概览"""
        async with self._get_session(db) as session:
            baseline = await self.get_active_baseline(session)
            config = await self._get_gate_config(session)

            # 最近24小时检查统计
            since = datetime.utcnow() - timedelta(hours=24)
            stats_query = select(
                func.count(AccuracyCheckRecord.id).label("total"),
                func.sum(
                    case((AccuracyCheckRecord.decision == "pass", 1), else_=0)
                ).label("pass_count"),
                func.sum(
                    case((AccuracyCheckRecord.decision == "block", 1), else_=0)
                ).label("block_count"),
                func.sum(
                    case((AccuracyCheckRecord.decision == "warn", 1), else_=0)
                ).label("warn_count"),
            ).where(AccuracyCheckRecord.checked_at >= since)

            # 使用原始SQL聚合替代
            total_result = await session.execute(
                select(func.count(AccuracyCheckRecord.id)).where(
                    AccuracyCheckRecord.checked_at >= since
                )
            )
            total_24h = total_result.scalar() or 0

            pass_result = await session.execute(
                select(func.count(AccuracyCheckRecord.id)).where(
                    and_(
                        AccuracyCheckRecord.checked_at >= since,
                        AccuracyCheckRecord.decision == "pass",
                    )
                )
            )
            pass_24h = pass_result.scalar() or 0

            block_result = await session.execute(
                select(func.count(AccuracyCheckRecord.id)).where(
                    and_(
                        AccuracyCheckRecord.checked_at >= since,
                        AccuracyCheckRecord.decision == "block",
                    )
                )
            )
            block_24h = block_result.scalar() or 0

            warn_result = await session.execute(
                select(func.count(AccuracyCheckRecord.id)).where(
                    and_(
                        AccuracyCheckRecord.checked_at >= since,
                        AccuracyCheckRecord.decision == "warn",
                    )
                )
            )
            warn_24h = warn_result.scalar() or 0

            return {
                "gate_enabled": config.enabled if config else True,
                "ci_block_enabled": config.ci_block_enabled if config else True,
                "active_baseline": baseline.to_dict() if baseline else None,
                "default_threshold": INITIAL_ACCURACY_THRESHOLD,
                "checks_last_24h": {
                    "total": total_24h,
                    "pass": pass_24h,
                    "block": block_24h,
                    "warn": warn_24h,
                },
                "health": {
                    "has_active_baseline": baseline is not None,
                    "has_config": config is not None,
                    "status": "healthy" if (baseline and config) else "degraded",
                },
            }

    # ══════════════════════════════════════════
    # 基线校准
    # ══════════════════════════════════════════

    async def calibrate_baseline(
        self,
        calibration_type: str = "manual",
        db: AsyncSession | None = None,
    ) -> CalibrationResult:
        """执行基线校准

        校准逻辑:
          1. 读取当前活跃基线和F18质量基线
          2. 计算当前样本的准确率统计
          3. 生成新基线阈值（基于当前统计数据）
          4. 归档旧基线，激活新基线
          5. 发送校准通知

        Args:
            calibration_type: 校准类型 (monthly/quarterly/manual/ci_triggered)
            db: 数据库会话

        Returns:
            CalibrationResult: 校准结果
        """
        cal_id = f"cal_{uuid.uuid4().hex[:16]}"
        async with self._get_session(db) as session:
            try:
                # 1. 获取当前活跃基线和配置
                old_baseline = await self.get_active_baseline(session)
                config = await self._get_gate_config(session)

                if not old_baseline:
                    raise BaselineNotFoundError("无可用的活跃基线进行校准")

                old_threshold = old_baseline.accuracy_threshold

                # 2. 获取F18质量参考
                quality_baseline = await self._get_active_quality_baseline(session)

                # 3. 计算当前准确率
                current_accuracy, sample_count, passing_count = (
                    await self._compute_current_accuracy(session, config)
                )
                passing_rate = round(
                    (passing_count / sample_count * 100), 2
                ) if sample_count > 0 else 0.0

                # 4. 确定新阈值
                #    策略: 新阈值 = max(当前准确率 - 1% 缓冲, 旧阈值)
                #    确保基线不会因为单次波动大幅下降
                candidate_threshold = round(max(current_accuracy - 1.0, old_threshold), 1)

                # 对于手动校准，使用当前准确率的95%作为新阈值（保留安全余量）
                if calibration_type == CalibrationType.MANUAL.value:
                    candidate_threshold = round(current_accuracy * 0.95, 1)

                # 对于月度校准，使用加权平均（60%当前 + 40%旧）
                if calibration_type == CalibrationType.MONTHLY.value:
                    candidate_threshold = round(current_accuracy * 0.6 + old_threshold * 0.4, 1)

                # 对于季度校准，更保守（50%当前 + 50%旧）
                if calibration_type == CalibrationType.QUARTERLY.value:
                    candidate_threshold = round(current_accuracy * 0.5 + old_threshold * 0.5, 1)

                new_threshold = candidate_threshold
                delta = round(new_threshold - old_threshold, 2)
                delta_percent = round(
                    (delta / old_threshold) * 100, 2
                ) if old_threshold > 0 else None

                # 5. 创建新基线
                new_baseline = AccuracyBaseline(
                    baseline_id=f"ab_{uuid.uuid4().hex[:16]}",
                    name=self._generate_baseline_name(calibration_type, new_threshold),
                    description=f"{calibration_type.capitalize()}校准基线 (从 {old_threshold}% → {new_threshold}%)",
                    accuracy_threshold=new_threshold,
                    pass_immediately=min(new_threshold + 5.0, 100.0),
                    warn_threshold=max(new_threshold - 5.0, 0.0),
                    quality_baseline_id=quality_baseline.baseline_id if quality_baseline else None,
                    quality_avg_total=quality_baseline.avg_total if quality_baseline else None,
                    sample_count=sample_count,
                    passing_count=passing_count,
                    passing_rate=passing_rate,
                    agent_version=f"v{new_threshold:.1f}",
                    model_name=quality_baseline.model_name if quality_baseline else None,
                    calibration_type=calibration_type,
                    is_active=True,
                    is_archived=False,
                    metadata={
                        "calibration_type": calibration_type,
                        "old_threshold": old_threshold,
                        "current_accuracy": current_accuracy,
                        "quality_avg_total": quality_baseline.avg_total if quality_baseline else None,
                    },
                    effective_from=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(new_baseline)
                await session.flush()

                # 6. 归档旧基线
                old_baseline.is_active = False
                old_baseline.effective_until = datetime.utcnow()
                old_baseline.updated_at = datetime.utcnow()

                # 7. 创建校准记录
                cal_record = AccuracyCalibrationRecord(
                    calibration_id=cal_id,
                    calibration_type=calibration_type,
                    status=CalibrationStatus.COMPLETED.value,
                    old_baseline_id=old_baseline.baseline_id,
                    old_accuracy_threshold=old_threshold,
                    new_baseline_id=new_baseline.baseline_id,
                    new_accuracy_threshold=new_threshold,
                    new_pass_immediately=min(new_threshold + 5.0, 100.0),
                    new_warn_threshold=max(new_threshold - 5.0, 0.0),
                    delta=delta,
                    delta_percent=delta_percent,
                    quality_baseline_id=quality_baseline.baseline_id if quality_baseline else None,
                    quality_avg_total=quality_baseline.avg_total if quality_baseline else None,
                    sample_count=sample_count,
                    passing_count=passing_count,
                    passing_rate=passing_rate,
                    details={
                        "dimension_breakdown": await self._get_dimension_breakdown(session),
                        "calibration_strategy": self._get_calibration_strategy(calibration_type),
                        "candidate_threshold": candidate_threshold,
                    },
                    notification_sent=False,
                    notification_channels=config.notification_channels if config else None,
                    calibrated_at=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                )
                session.add(cal_record)
                await session.commit()

                logger.info(
                    "基线校准完成: %s | %s | %s%% → %s%% (delta=%s%%)",
                    cal_id, calibration_type, old_threshold, new_threshold, delta,
                )

                # 8. 发送校准通知（异步任务）
                notification_sent = await self._send_calibration_notification(
                    new_baseline, old_baseline, cal_record, config,
                )
                if notification_sent:
                    cal_record.notification_sent = True
                    await session.commit()

                return CalibrationResult(
                    calibration_id=cal_id,
                    calibration_type=calibration_type,
                    status=CalibrationStatus.COMPLETED.value,
                    old_threshold=old_threshold,
                    new_threshold=new_threshold,
                    delta=delta,
                    sample_count=sample_count,
                    passing_rate=passing_rate,
                    quality_avg_total=quality_baseline.avg_total if quality_baseline else None,
                    notification_sent=notification_sent,
                )

            except Exception as e:
                logger.error("基线校准失败: %s", str(e), exc_info=True)
                # 写入错误校准记录
                try:
                    cal_record_error = AccuracyCalibrationRecord(
                        calibration_id=cal_id,
                        calibration_type=calibration_type,
                        status=CalibrationStatus.FAILED.value,
                        error_message=str(e),
                        calibrated_at=datetime.utcnow(),
                        created_at=datetime.utcnow(),
                    )
                    session.add(cal_record_error)
                    await session.commit()
                except Exception:
                    pass
                raise CalibrationError(f"基线校准失败: {e}") from e

    async def list_calibrations(
        self,
        limit: int = 20,
        offset: int = 0,
        calibration_type: str | None = None,
        db: AsyncSession | None = None,
    ) -> tuple[list[AccuracyCalibrationRecord], int]:
        """获取校准历史"""
        async with self._get_session(db) as session:
            query = select(AccuracyCalibrationRecord)
            count_query = select(func.count(AccuracyCalibrationRecord.id))

            if calibration_type:
                query = query.where(AccuracyCalibrationRecord.calibration_type == calibration_type)
                count_query = count_query.where(
                    AccuracyCalibrationRecord.calibration_type == calibration_type
                )

            query = query.order_by(desc(AccuracyCalibrationRecord.calibrated_at)).offset(offset).limit(limit)

            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0

            result = await session.execute(query)
            records = list(result.scalars().all())
            return records, total

    # ══════════════════════════════════════════
    # 内部方法
    # ══════════════════════════════════════════

    async def _compute_current_accuracy(
        self,
        session: AsyncSession,
        config: AccuracyGateConfig | None = None,
    ) -> tuple[float, int, int]:
        """计算当前准确率（基于F18 QualitySample的已评估数据）

        Returns:
            (准确率百分比, 样本总数, 达标样本数)
        """
        # 查询所有已完成的评估样本
        result = await session.execute(
            select(QualitySample).where(
                QualitySample.status == EvalStatus.COMPLETED.value,
                QualitySample.score_total.isnot(None),
            )
        )
        samples = list(result.scalars().all())

        if not samples:
            logger.warning("没有已完成的评估样本用于计算准确率")
            return 0.0, 0, 0

        total = len(samples)
        # 将5分制转换为百分比: score_total / 5.0 * 100
        # 准确率 = 得分 >= 3.0 (60%) 的样本占比
        passing_threshold = 3.0  # 5分制里的及格线
        passing = [s for s in samples if s.score_total is not None and s.score_total >= passing_threshold]
        passing_count = len(passing)

        accuracy = round((passing_count / total) * 100, 2) if total > 0 else 0.0
        logger.debug(
            "当前准确率计算: %s%% (%d/%d samples, threshold=%s/5.0)",
            accuracy, passing_count, total, passing_threshold,
        )
        return accuracy, total, passing_count

    async def _get_active_quality_baseline(
        self,
        session: AsyncSession,
    ) -> QualityBaseline | None:
        """获取F18当前活跃质量基线"""
        try:
            result = await session.execute(
                select(QualityBaseline).where(
                    QualityBaseline.is_active == True,
                ).order_by(desc(QualityBaseline.created_at)).limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.warning("获取F18活跃质量基线失败: %s", e)
            return None

    async def _get_dimension_breakdown(
        self,
        session: AsyncSession,
    ) -> dict[str, Any]:
        """获取各维度的准确率分解"""
        result = await session.execute(
            select(QualitySample).where(
                QualitySample.status == EvalStatus.COMPLETED.value,
                QualitySample.score_total.isnot(None),
            )
        )
        samples = list(result.scalars().all())

        if not samples:
            return {}

        dimensions = ["usefulness", "accuracy", "completeness", "coherence", "harmlessness"]
        breakdown = {}
        for dim in dimensions:
            dim_scores = [
                getattr(s, f"score_{dim}")
                for s in samples
                if getattr(s, f"score_{dim}") is not None
            ]
            if dim_scores:
                avg = round(sum(dim_scores) / len(dim_scores), 2)
                # 将5分制转换为百分比精度
                accuracy_pct = round((avg / 5.0) * 100, 2)
                passing = len([s for s in dim_scores if s >= 3.0])
                breakdown[dim] = {
                    "avg_score": avg,
                    "accuracy_pct": accuracy_pct,
                    "passing_count": passing,
                    "total_count": len(dim_scores),
                }
        return breakdown

    async def _ensure_gate_config(
        self,
        session: AsyncSession,
    ) -> AccuracyGateConfig:
        """确保门禁配置存在，如无则创建默认配置"""
        result = await session.execute(
            select(AccuracyGateConfig).where(
                AccuracyGateConfig.gate_config_id == "default"
            ).limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        config = AccuracyGateConfig(
            gate_config_id="default",
            enabled=True,
            ci_block_enabled=True,
            default_accuracy_threshold=INITIAL_ACCURACY_THRESHOLD,
            default_pass_immediately=INITIAL_PASS_IMMEDIATELY,
            default_warn_threshold=INITIAL_WARN_THRESHOLD,
            ci_block_on_warn=False,
            ci_required_samples=DEFAULT_CI_REQUIRED_SAMPLES,
            ci_auto_calibrate_on_degradation=False,
            auto_calibrate=True,
            monthly_calibration_day=1,
            quarterly_calibration_month=1,
            notify_on_calibration=True,
            notification_channels=["webhook"],
            metadata={"description": "F20默认门禁配置"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(config)
        await session.commit()
        await session.refresh(config)
        logger.info("默认门禁配置已创建")
        return config

    async def _get_gate_config(
        self,
        session: AsyncSession,
    ) -> AccuracyGateConfig | None:
        """获取门禁配置"""
        result = await session.execute(
            select(AccuracyGateConfig).where(
                AccuracyGateConfig.gate_config_id == "default"
            ).limit(1)
        )
        return result.scalar_one_or_none()

    def _generate_baseline_name(
        self,
        calibration_type: str,
        threshold: float,
    ) -> str:
        """生成基线名称"""
        now = datetime.utcnow()
        if calibration_type == CalibrationType.MONTHLY.value:
            return f"{now.year}年{now.month}月月度校准基线 ({threshold}%)"
        elif calibration_type == CalibrationType.QUARTERLY.value:
            quarter = (now.month - 1) // 3 + 1
            return f"{now.year}年Q{quarter}季度校准基线 ({threshold}%)"
        elif calibration_type == CalibrationType.CI_TRIGGERED.value:
            return f"CI触发校准基线 ({threshold}%)"
        else:
            return f"手动校准基线 ({threshold}%)"

    def _get_calibration_strategy(self, calibration_type: str) -> str:
        """返回校准策略说明"""
        strategies = {
            CalibrationType.MONTHLY.value: "月度校准: 新阈值 = 当前准确率×0.6 + 旧阈值×0.4",
            CalibrationType.QUARTERLY.value: "季度校准: 新阈值 = 当前准确率×0.5 + 旧阈值×0.5",
            CalibrationType.MANUAL.value: "手动校准: 新阈值 = 当前准确率×0.95",
            CalibrationType.CI_TRIGGERED.value: "CI触发校准: 新阈值 = max(当前准确率-1%, 旧阈值)",
        }
        return strategies.get(calibration_type, "未知校准策略")

    async def _send_calibration_notification(
        self,
        new_baseline: AccuracyBaseline,
        old_baseline: AccuracyBaseline,
        cal_record: AccuracyCalibrationRecord,
        config: AccuracyGateConfig | None,
    ) -> bool:
        """发送校准通知

        通知渠道（按配置）:
          - webhook: POST到配置的webhook URL
          - 日志: 始终记录

        Returns:
            bool: 是否发送成功
        """
        try:
            notification_data = {
                "event": "baseline_calibration",
                "calibration_id": cal_record.calibration_id,
                "calibration_type": cal_record.calibration_type,
                "old_threshold": old_baseline.accuracy_threshold,
                "new_threshold": new_baseline.accuracy_threshold,
                "delta": cal_record.delta,
                "sample_count": cal_record.sample_count,
                "passing_rate": cal_record.passing_rate,
                "quality_avg_total": cal_record.quality_avg_total,
                "calibrated_at": cal_record.calibrated_at.isoformat(),
                "agent_version": new_baseline.agent_version,
            }

            logger.info(
                "校准通知: [%s] %s%% → %s%% (delta=%s%%)",
                cal_record.calibration_type,
                old_baseline.accuracy_threshold,
                new_baseline.accuracy_threshold,
                cal_record.delta,
            )

            # BUG-018 修复：webhook 渠道真实发送（config.notification_channels 为
            # JSON，支持 dict 形式 {"webhook": {"url": "https://..."}} 或字符串列表）
            channels = config.notification_channels if config else None
            if channels and "webhook" in channels:
                webhook_conf = channels["webhook"]
                webhook_url = ""
                if isinstance(webhook_conf, str):
                    webhook_url = webhook_conf
                elif isinstance(webhook_conf, dict):
                    webhook_url = webhook_conf.get("url", "") or ""
                if webhook_url:
                    try:
                        import httpx
                        async with httpx.AsyncClient(timeout=10) as client:
                            resp = await client.post(
                                webhook_url,
                                json=notification_data,
                                headers={"Content-Type": "application/json"},
                            )
                        if resp.status_code < 400:
                            logger.info("校准通知 webhook 发送成功: %s", webhook_url)
                            cal_record.notification_sent = True
                        else:
                            logger.warning(
                                "校准通知 webhook 发送失败 HTTP %s: %s",
                                resp.status_code, webhook_url,
                            )
                    except Exception as e:  # noqa: BLE001
                        logger.warning("校准通知 webhook 发送异常: %s", e)
                else:
                    logger.warning("校准通知 webhook 渠道已配置但缺少 url，跳过发送")
            else:
                logger.debug("校准通知未配置 webhook 渠道，仅记录日志")

            return True

        except Exception as e:
            logger.warning("发送校准通知失败: %s", e)
            return False

    def _get_session(self, db: AsyncSession | None) -> "_SessionContext":
        """获取数据库会话"""
        if db is not None:
            return _SessionContext(db)
        return _SessionContext(AsyncSessionLocal())


class _SessionContext:
    """异步会话上下文管理器"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._external = hasattr(session, "execute") and not isinstance(session, _SessionContext)

    async def __aenter__(self) -> AsyncSession:
        if not self._external:
            self._session = await self._session.__aenter__()  # type: ignore
        return self._session

    async def __aexit__(self, *args, **kwargs) -> None:
        if not self._external:
            await self._session.__aexit__(*args, **kwargs)  # type: ignore


# ──────────────────────────────────────────────
# 单例
# ──────────────────────────────────────────────

accuracy_gate = AccuracyGate()
