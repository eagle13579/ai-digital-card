"""checkpoint.py — Checkpoint 数据模型

F16 异步任务 Checkpoint 恢复。
定义 Checkpoint 状态、步骤记录、任务检查点。

依赖:
  - F08 task_slicer: 已交付, tasks 可被 checkpoint 追踪每步骤进度
"""

from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any


class StepStatus(str, Enum):
    """单步执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class CheckpointStatus(str, Enum):
    """任务级 Checkpoint 状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class StepRecord:
    """
    单步执行记录。

    Attributes:
        step_id: 步骤唯一 ID
        step_name: 步骤名称 / 标识
        index: 步骤序号（从 0 开始）
        status: 执行状态
        data: 该步骤产出的中间数据（可序列化 dict）
        metadata: 附加元数据（耗时、重试次数等）
        error: 失败时的错误信息
        created_at: 创建时间戳
        started_at: 开始执行时间戳
        completed_at: 完成时间戳
    """

    def __init__(
        self,
        step_name: str,
        index: int = 0,
        step_id: str | None = None,
        status: StepStatus = StepStatus.PENDING,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        error: str | None = None,
    ):
        self.step_id: str = step_id or f"step_{uuid.uuid4().hex[:12]}"
        self.step_name: str = step_name
        self.index: int = index
        self.status: StepStatus = status
        self.data: dict[str, Any] = data or {}
        self.metadata: dict[str, Any] = metadata or {}
        self.error: str | None = error
        self.created_at: float = time.time()
        self.started_at: float | None = None
        self.completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "index": self.index,
            "status": self.status.value if isinstance(self.status, StepStatus) else self.status,
            "data": self.data,
            "metadata": self.metadata,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> StepRecord:
        rec = StepRecord(
            step_name=data["step_name"],
            index=data.get("index", 0),
            step_id=data.get("step_id"),
            status=StepStatus(data.get("status", "pending")),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            error=data.get("error"),
        )
        rec.created_at = data.get("created_at", time.time())
        rec.started_at = data.get("started_at")
        rec.completed_at = data.get("completed_at")
        return rec

    def to_snapshot(self) -> dict[str, Any]:
        """精简快照（不含 data，避免序列化过大）"""
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "index": self.index,
            "status": self.status.value if isinstance(self.status, StepStatus) else self.status,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    def __repr__(self) -> str:
        return f"<StepRecord {self.step_name}[{self.index}] status={self.status.value}>"


class TaskCheckpoint:
    """
    异步任务检查点 — 每步骤持久化状态，支持断点恢复。

    Attributes:
        task_id: 任务唯一 ID
        steps: 步骤记录列表
        current_step_index: 当前执行到的步骤索引
        status: 任务级 Checkpoint 状态
        metadata: 任务级元数据（来源、参数、关联 task_slicer 的 plan_id 等）
        created_at: 创建时间
        updated_at: 最后更新时间
        expires_at: 过期时间（超时清理用）
        error: 任务级错误信息
    """

    def __init__(
        self,
        task_id: str | None = None,
        steps: list[StepRecord] | None = None,
        status: CheckpointStatus = CheckpointStatus.PENDING,
        metadata: dict[str, Any] | None = None,
        ttl_seconds: int = 3600,  # 默认 1 小时过期
    ):
        self.task_id: str = task_id or f"ckpt_{uuid.uuid4().hex[:12]}"
        self.steps: list[StepRecord] = steps or []
        self.current_step_index: int = 0
        self.status: CheckpointStatus = status
        self.metadata: dict[str, Any] = metadata or {}
        self.created_at: float = time.time()
        self.updated_at: float = self.created_at
        self.expires_at: float = self.created_at + ttl_seconds
        self.error: str | None = None

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def current_step(self) -> StepRecord | None:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def completed_step_count(self) -> int:
        return sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)

    @property
    def failed_step_count(self) -> int:
        return sum(1 for s in self.steps if s.status == StepStatus.FAILED)

    @property
    def progress_pct(self) -> float:
        """进度百分比 0.0 ~ 100.0"""
        if not self.steps:
            return 0.0
        return (self.completed_step_count / len(self.steps)) * 100.0

    def add_step(self, step: StepRecord) -> None:
        """添加步骤记录"""
        step.index = len(self.steps)
        self.steps.append(step)
        self.updated_at = time.time()

    def add_steps_from_plan(self, step_names: list[str]) -> None:
        """从步骤名称列表批量添加 PENDING 步骤"""
        for name in step_names:
            self.add_step(StepRecord(step_name=name))

    def update_step_status(
        self,
        step_index: int,
        status: StepStatus,
        data: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """更新单个步骤状态"""
        if step_index < 0 or step_index >= len(self.steps):
            raise IndexError(f"step_index {step_index} 超出 [0, {len(self.steps)})")
        step = self.steps[step_index]
        step.status = status
        if data is not None:
            step.data.update(data)
        if error is not None:
            step.error = error
        if status == StepStatus.RUNNING:
            step.started_at = time.time()
        elif status in (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.TIMEOUT):
            step.completed_at = time.time()
        self.current_step_index = step_index + 1
        self.updated_at = time.time()

    def mark_step_completed(self, step_index: int, data: dict[str, Any] | None = None) -> None:
        """标记步骤完成"""
        self.update_step_status(step_index, StepStatus.COMPLETED, data=data)

    def mark_step_failed(self, step_index: int, error: str, data: dict[str, Any] | None = None) -> None:
        """标记步骤失败"""
        self.update_step_status(step_index, StepStatus.FAILED, data=data, error=error)

    def is_expired(self, now: float | None = None) -> bool:
        """检查是否过期"""
        return (now or time.time()) > self.expires_at

    def get_recovery_point(self) -> int:
        """
        获取恢复点 — 从最后一个 FAILED 步骤开始恢复；
        如果没有失败步骤，从第一个非 COMPLETED 步骤开始。
        """
        # 找第一个失败的步骤
        for i, step in enumerate(self.steps):
            if step.status == StepStatus.FAILED:
                return i
        # 找第一个未完成的步骤
        for i, step in enumerate(self.steps):
            if step.status not in (StepStatus.COMPLETED, StepStatus.SKIPPED):
                return i
        # 所有步骤已完成
        return len(self.steps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "steps": [s.to_dict() for s in self.steps],
            "current_step_index": self.current_step_index,
            "status": self.status.value if isinstance(self.status, CheckpointStatus) else self.status,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "error": self.error,
            "step_count": self.step_count,
            "completed_step_count": self.completed_step_count,
            "failed_step_count": self.failed_step_count,
            "progress_pct": self.progress_pct,
            "recovery_point": self.get_recovery_point(),
        }

    def to_snapshot(self) -> dict[str, Any]:
        """精简快照（不含步骤 data，用于列表/状态查询）"""
        return {
            "task_id": self.task_id,
            "status": self.status.value if isinstance(self.status, CheckpointStatus) else self.status,
            "current_step_index": self.current_step_index,
            "progress_pct": self.progress_pct,
            "step_count": self.step_count,
            "completed_step_count": self.completed_step_count,
            "failed_step_count": self.failed_step_count,
            "recovery_point": self.get_recovery_point(),
            "steps": [s.to_snapshot() for s in self.steps],
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
        }

    @staticmethod
    def from_dict(data: dict[str, Any], ttl_seconds: int = 3600) -> TaskCheckpoint:
        steps_data = data.get("steps", [])
        steps = [StepRecord.from_dict(s) for s in steps_data]
        ckpt = TaskCheckpoint(
            task_id=data.get("task_id"),
            steps=steps,
            status=CheckpointStatus(data.get("status", "pending")),
            metadata=data.get("metadata", {}),
            ttl_seconds=ttl_seconds,
        )
        ckpt.current_step_index = data.get("current_step_index", 0)
        ckpt.created_at = data.get("created_at", time.time())
        ckpt.updated_at = data.get("updated_at", time.time())
        ckpt.expires_at = data.get("expires_at", ckpt.created_at + ttl_seconds)
        ckpt.error = data.get("error")
        return ckpt

    def __repr__(self) -> str:
        return (
            f"<TaskCheckpoint task_id={self.task_id} "
            f"steps={self.step_count} completed={self.completed_step_count} "
            f"status={self.status.value} progress={self.progress_pct:.1f}%>"
        )
