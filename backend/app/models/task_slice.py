"""
task_slice.py — 任务切片数据模型

定义 TaskSlice（单个切片）和 SlicePlan（切片计划）模型。
支持按 Token / 步骤 / 语义三种切片模式。
"""

from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any


class SliceMode(str, Enum):
    """切片模式"""
    TOKEN_BUDGET = "token_budget"   # 按 Token 预算
    STEP = "step"                   # 按步骤
    SEMANTIC = "semantic"           # 按语义段落


class SliceStatus(str, Enum):
    """切片状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskSlice:
    """
    单个任务切片。

    Attributes:
        id: 切片唯一标识
        task_id: 所属任务 ID
        index: 切片序号（从 0 开始）
        content: 切片内容（原任务文本的子集）
        metadata: 切片元数据（模式、预算、总结等）
        token_estimate: 估计 Token 数
        status: 切片状态
        dependencies: 依赖的切片 ID 列表（按序依赖）
        created_at: 创建时间
        completed_at: 完成时间
    """

    def __init__(
        self,
        content: str,
        index: int = 0,
        task_id: str | None = None,
        slice_id: str | None = None,
        metadata: dict | None = None,
        token_estimate: int = 0,
        status: SliceStatus = SliceStatus.PENDING,
        dependencies: list[str] | None = None,
    ):
        self.id: str = slice_id or f"slice_{uuid.uuid4().hex[:12]}"
        self.task_id: str = task_id or ""
        self.index: int = index
        self.content: str = content
        self.metadata: dict[str, Any] = metadata or {}
        self.token_estimate: int = token_estimate
        self.status: SliceStatus = status
        self.dependencies: list[str] = dependencies or []
        self.created_at: float = time.time()
        self.completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "index": self.index,
            "content": self.content,
            "metadata": self.metadata,
            "token_estimate": self.token_estimate,
            "status": self.status.value if isinstance(self.status, SliceStatus) else self.status,
            "dependencies": self.dependencies,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> TaskSlice:
        return TaskSlice(
            content=data["content"],
            index=data.get("index", 0),
            task_id=data.get("task_id"),
            slice_id=data.get("id"),
            metadata=data.get("metadata", {}),
            token_estimate=data.get("token_estimate", 0),
            status=SliceStatus(data.get("status", "pending")),
            dependencies=data.get("dependencies", []),
        )

    def __repr__(self) -> str:
        return (
            f"<TaskSlice id={self.id} index={self.index} "
            f"status={self.status.value} tokens={self.token_estimate}>"
        )


class SlicePlan:
    """
    切片计划 — 一个大任务被分解后的完整切片集合。

    Attributes:
        task_id: 原始任务 ID
        original_content: 原始任务完整内容
        mode: 切片模式
        slices: 切片列表
        metadata: 计划级元数据（总 Token 估计、参数等）
        created_at: 创建时间
    """

    def __init__(
        self,
        original_content: str,
        mode: SliceMode,
        task_id: str | None = None,
        slices: list[TaskSlice] | None = None,
        metadata: dict | None = None,
    ):
        self.task_id: str = task_id or f"task_{uuid.uuid4().hex[:12]}"
        self.original_content: str = original_content
        self.mode: SliceMode = mode
        self.slices: list[TaskSlice] = slices or []
        self.metadata: dict[str, Any] = metadata or {}
        self.created_at: float = time.time()

    @property
    def slice_count(self) -> int:
        return len(self.slices)

    @property
    def total_token_estimate(self) -> int:
        return sum(s.token_estimate for s in self.slices)

    def add_slice(self, task_slice: TaskSlice) -> None:
        task_slice.task_id = self.task_id
        task_slice.index = len(self.slices)
        self.slices.append(task_slice)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "original_content": self.original_content,
            "mode": self.mode.value if isinstance(self.mode, SliceMode) else self.mode,
            "slices": [s.to_dict() for s in self.slices],
            "metadata": self.metadata,
            "slice_count": self.slice_count,
            "total_token_estimate": self.total_token_estimate,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> SlicePlan:
        slices = [TaskSlice.from_dict(s) for s in data.get("slices", [])]
        return SlicePlan(
            original_content=data["original_content"],
            mode=SliceMode(data.get("mode", "token_budget")),
            task_id=data.get("task_id"),
            slices=slices,
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        return (
            f"<SlicePlan task_id={self.task_id} slices={self.slice_count} "
            f"mode={self.mode.value} total_tokens={self.total_token_estimate}>"
        )
