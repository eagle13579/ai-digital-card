"""orchestrator_loop.py — 编排器委派循环 (Orchestrator Delegate Loop)

A Orchestra 最核心的架构模式：编排器(Orchestrator) 拥有极简动作集——
  1. delegate(sub_task, recipe) → 委派子智能体执行
  2. finish(result) → 整合结构化结果

编排器从不亲自调用工具，只做拆解和委派。子智能体通过动态工厂生成。

状态闭环：初始 → 拆解 → 执行 → 反馈 → 更新 → 完成

Usage:
    async def my_delegate(sub_task, recipe):
        # 调用子智能体执行
        return {"status": "completed", "output": ...}

    loop = OrchestratorLoop(delegate_fn=my_delegate)
    result = await loop.orchestrate("完成数据分析任务")

纯标准库 + dataclasses + typing，不直接调用任何工具/API。
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Optional


# ── 状态定义 ────────────────────────────────────────────────────────────────


class Phase(Enum):
    """编排器阶段枚举 — 完整的状态闭环。"""

    INITIAL = auto()          # 初始：接收目标
    DECOMPOSE = auto()        # 拆解：将目标拆解为子任务
    EXECUTE = auto()          # 执行：委派子智能体
    FEEDBACK = auto()         # 反馈：吸收子智能体结果
    UPDATE = auto()           # 更新：根据反馈更新状态/任务队列
    COMPLETED = auto()        # 完成：所有子任务已完成


class DelegateStatus(str, Enum):
    """委派结果状态。"""
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_DECOMPOSITION = "needs_decomposition"
    PARTIAL = "partial"
    BLOCKED = "blocked"


# ── 数据结构 ────────────────────────────────────────────────────────────────


@dataclass
class SubTask:
    """子任务单元 — 编排器委派的工作单元。

    Attributes:
        task_id: 任务唯一标识。
        goal: 子任务目标描述。
        recipe: 四元组配方（含 instruction/context/tools/model_spec）。
        parent_task_id: 父任务ID，用于溯源。
        status: 当前状态。
        created_at: 创建时间戳。
    """

    task_id: str
    goal: str
    recipe: dict[str, Any]
    parent_task_id: Optional[str] = None
    status: str = "pending"
    created_at: float = 0.0

    def __post_init__(self) -> None:
        if not self.task_id:
            self.task_id = f"task_{uuid.uuid4().hex[:8]}"
        if not self.created_at:
            self.created_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "recipe": dict(self.recipe),
            "parent_task_id": self.parent_task_id,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class DelegateResult:
    """委派执行结果。

    Attributes:
        task_id: 对应子任务的 ID。
        status: 执行状态（completed/failed/needs_decomposition 等）。
        output: 结构化输出（主要产出物）。
        summary: 人工可读的摘要。
        error: 错误信息（若有）。
        artifacts: 附产物（文件路径、数据等）。
        duration: 执行耗时（秒）。
        sub_goals: 当 status=needs_decomposition 时，建议拆解的子目标。
        suggested_tools: 建议子任务使用的工具。
        suggested_model: 建议子任务使用的模型。
    """

    task_id: str
    status: DelegateStatus = DelegateStatus.COMPLETED
    output: Any = None
    summary: str = ""
    error: Optional[str] = None
    artifacts: dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0
    sub_goals: list[str] = field(default_factory=list)
    suggested_tools: list[str] = field(default_factory=list)
    suggested_model: Optional[str] = None

    def is_success(self) -> bool:
        """是否成功完成。"""
        return self.status == DelegateStatus.COMPLETED

    def is_failure(self) -> bool:
        """是否失败。"""
        return self.status == DelegateStatus.FAILED

    def needs_decomposition(self) -> bool:
        """是否需要继续拆解。"""
        return self.status == DelegateStatus.NEEDS_DECOMPOSITION

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "output": self.output,
            "summary": self.summary,
            "error": self.error,
            "artifacts": dict(self.artifacts),
            "duration": self.duration,
            "sub_goals": list(self.sub_goals),
            "suggested_tools": list(self.suggested_tools),
            "suggested_model": self.suggested_model,
        }

    @classmethod
    def completed(
        cls,
        task_id: str,
        output: Any = None,
        summary: str = "",
        artifacts: Optional[dict[str, Any]] = None,
        duration: float = 0.0,
    ) -> DelegateResult:
        """快速创建成功结果。"""
        return cls(
            task_id=task_id,
            status=DelegateStatus.COMPLETED,
            output=output,
            summary=summary,
            artifacts=artifacts or {},
            duration=duration,
        )

    @classmethod
    def failed(
        cls,
        task_id: str,
        error: str,
        duration: float = 0.0,
    ) -> DelegateResult:
        """快速创建失败结果。"""
        return cls(
            task_id=task_id,
            status=DelegateStatus.FAILED,
            error=error,
            summary=f"失败: {error[:80]}",
            duration=duration,
        )

    @classmethod
    def needs_decomposition(
        cls,
        task_id: str,
        sub_goals: list[str],
        suggested_tools: Optional[list[str]] = None,
        suggested_model: Optional[str] = None,
        duration: float = 0.0,
    ) -> DelegateResult:
        """快速创建需要继续拆解的结果。"""
        return cls(
            task_id=task_id,
            status=DelegateStatus.NEEDS_DECOMPOSITION,
            sub_goals=sub_goals,
            suggested_tools=suggested_tools or [],
            suggested_model=suggested_model,
            summary=f"需要拆解为 {len(sub_goals)} 个子任务",
            duration=duration,
        )


# ── 编排器状态 ──────────────────────────────────────────────────────────────


@dataclass
class OrchestratorState:
    """编排器运行时状态。

    维护编排器委派循环的全部状态：
        - phase: 当前阶段
        - goal: 原始目标
        - task_tree: 所有任务（含父子关系）
        - result_tree: 所有执行结果
        - completed_count / failed_count: 统计
        - start_time: 开始时间
        - delegation_count: 委派次数

    状态闭环：INITIAL → DECOMPOSE → EXECUTE → FEEDBACK → UPDATE → COMPLETED
    """

    phase: Phase = Phase.INITIAL
    goal: str = ""
    task_tree: dict[str, SubTask] = field(default_factory=dict)
    result_tree: dict[str, DelegateResult] = field(default_factory=dict)
    completed_count: int = 0
    failed_count: int = 0
    start_time: float = 0.0
    delegation_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase.name,
            "goal": self.goal,
            "total_tasks": len(self.task_tree),
            "completed_results": len(self.result_tree),
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "delegation_count": self.delegation_count,
            "elapsed": round(time.time() - self.start_time, 2) if self.start_time else 0.0,
        }

    def elapsed(self) -> float:
        """返回已消耗时间（秒）。"""
        return round(time.time() - self.start_time, 2) if self.start_time else 0.0


# ── 编排器主循环 ────────────────────────────────────────────────────────────


class OrchestratorLoop:
    """编排器委派循环。

    编排器只有两个动作：
        1. delegate(sub_task, recipe) — 委派子智能体
        2. finish(result) — 整合结构化结果

    主循环 orchestrat() 不断执行：拆解 → 委派 → 吸收反馈 → 更新 → 继续/完成。

    Args:
        delegate_fn: 委派函数，签名 async (sub_task: SubTask, recipe: dict) -> dict
                     返回字典必须包含 "status" 键（"completed"/"failed"/"needs_decomposition"）。
        max_delegations: 最大委派次数，防止委派爆炸。
        decompose_fn: 可选的自定义拆解函数。默认为基于关键词的简单拆解。
    """

    def __init__(
        self,
        delegate_fn: Callable[[SubTask, dict[str, Any]], Any],
        max_delegations: int = 20,
        decompose_fn: Optional[Callable[[str], list[SubTask]]] = None,
    ) -> None:
        self._delegate_fn = delegate_fn
        self._max_delegations = max_delegations
        self._decompose_fn = decompose_fn or self._default_decompose
        self.state = OrchestratorState()

    async def orchestrate(self, goal: str) -> dict[str, Any]:
        """编排器主循环 — 执行一个完整目标。

        流程：
            1. 初始化状态
            2. 拆解目标为子任务
            3. 委派子任务（delegate）
            4. 吸收反馈
            5. 更新状态（继续拆解或进入下一任务）
            6. 重复直到所有任务完成
            7. 整合结果（finish）

        Args:
            goal: 目标任务描述。

        Returns:
            最终整合结果字典。
        """
        self.state = OrchestratorState(
            phase=Phase.INITIAL,
            goal=goal,
            start_time=time.time(),
        )

        # Phase 1: 拆解初始目标
        self.state.phase = Phase.DECOMPOSE
        root_task = SubTask(
            task_id=f"root_{uuid.uuid4().hex[:8]}",
            goal=goal,
            recipe={"instruction": f"请完成以下任务：{goal}", "context_spec": {}, "tools": [], "model_spec": {"model": "default"}},
        )
        self.state.task_tree[root_task.task_id] = root_task

        # 初始拆解
        initial_subtasks = self._decompose_fn(goal)
        pending: list[str] = []
        for st in initial_subtasks:
            st.parent_task_id = root_task.task_id
            self.state.task_tree[st.task_id] = st
            pending.append(st.task_id)

        if not pending:
            pending.append(root_task.task_id)

        # 主委派循环
        all_results: list[DelegateResult] = []

        while pending and self.state.delegation_count < self._max_delegations:
            task_id = pending.pop(0)
            task = self.state.task_tree.get(task_id)
            if task is None:
                continue

            # Phase 2: 执行 — 委派
            self.state.phase = Phase.EXECUTE
            self.state.delegation_count += 1
            task.status = "running"

            result = await self._delegate(task)

            # Phase 3: 反馈 — 吸收结果
            self.state.phase = Phase.FEEDBACK
            self.state.result_tree[task_id] = result
            task.status = result.status.value if isinstance(result.status, DelegateStatus) else result.status
            all_results.append(result)

            # 更新统计
            if result.is_success():
                self.state.completed_count += 1
            elif result.is_failure():
                self.state.failed_count += 1

            # Phase 4: 更新 — 决策下一步
            self.state.phase = Phase.UPDATE

            if result.needs_decomposition() and result.sub_goals:
                # 需要继续拆解：为每个子目标生成新的子任务
                for sub_goal in result.sub_goals:
                    sub_task = SubTask(
                        task_id=f"sub_{uuid.uuid4().hex[:8]}",
                        goal=sub_goal,
                        recipe={
                            "instruction": f"请完成子任务：{sub_goal}",
                            "context_spec": task.recipe.get("context_spec", {}),
                            "tools": result.suggested_tools or task.recipe.get("tools", []),
                            "model_spec": (
                                {"model": result.suggested_model}
                                if result.suggested_model
                                else task.recipe.get("model_spec", {"model": "default"})
                            ),
                        },
                        parent_task_id=task_id,
                    )
                    self.state.task_tree[sub_task.task_id] = sub_task
                    pending.append(sub_task.task_id)

        # Phase 5: 完成 — 整合结果
        self.state.phase = Phase.COMPLETED
        final_result = await self._finish(all_results)

        final_result["total_delegations"] = self.state.delegation_count
        final_result["total_duration"] = self.state.elapsed()
        final_result["state_summary"] = self.state.to_dict()

        return final_result

    async def delegate(self, sub_task: SubTask, recipe: dict[str, Any]) -> DelegateResult:
        """动作1: 委派 — 将子任务交给执行方。

        Args:
            sub_task: 子任务单元。
            recipe: 四元组配方字典。

        Returns:
            委派执行结果。
        """
        raw = await self._delegate_fn(sub_task, recipe)
        return self._normalize_result(raw, sub_task.task_id)

    async def _delegate(self, sub_task: SubTask) -> DelegateResult:
        """内部委派方法，包装 delegate_fn 调用。"""
        start = time.time()
        try:
            raw = await self._delegate_fn(sub_task, sub_task.recipe)
            result = self._normalize_result(raw, sub_task.task_id)
            result.duration = time.time() - start
            return result
        except Exception as e:
            return DelegateResult.failed(
                task_id=sub_task.task_id,
                error=str(e),
                duration=time.time() - start,
            )

    async def finish(self, result: dict[str, Any]) -> dict[str, Any]:
        """动作2: 整合 — 将原始整合结果加工为标准化输出。

        Args:
            result: 原始整合结果字典。

        Returns:
            标准化后的最终结果。
        """
        return self._normalize_final(result)

    async def _finish(self, results: list[DelegateResult]) -> dict[str, Any]:
        """内部整合方法，合并所有子结果。"""
        successful = [r for r in results if r.is_success()]
        failed = [r for r in results if r.is_failure()]

        # 合并输出
        merged_output: dict[str, Any] = {}
        for r in successful:
            if isinstance(r.output, dict):
                merged_output.update(r.output)
            elif r.output is not None:
                merged_output[r.task_id] = r.output

        # 构建摘要
        summary_lines: list[str] = []
        for r in results:
            icon = "✓" if r.is_success() else ("✗" if r.is_failure() else "…")
            summary_lines.append(f"[{icon}] {r.task_id}: {r.summary[:80]}")

        return {
            "status": "completed" if not failed else ("partial" if successful else "failed"),
            "summary": "\n".join(summary_lines),
            "outputs": [r.to_dict() for r in results],
            "merged_output": merged_output,
            "total_tasks": len(results),
            "success_count": len(successful),
            "failed_count": len(failed),
            "has_decomposition": any(r.needs_decomposition() for r in results),
        }

    # ── 辅助方法 ────────────────────────────────────────────────────────

    def _normalize_result(self, raw: Any, task_id: str) -> DelegateResult:
        """将任意格式的原始结果标准化为 DelegateResult。"""
        if isinstance(raw, DelegateResult):
            return raw
        if isinstance(raw, dict):
            status_raw = raw.get("status", "completed")
            if isinstance(status_raw, str):
                status = DelegateStatus(status_raw)
            elif isinstance(status_raw, DelegateStatus):
                status = status_raw
            else:
                status = DelegateStatus.COMPLETED

            return DelegateResult(
                task_id=raw.get("task_id", task_id),
                status=status,
                output=raw.get("output"),
                summary=raw.get("summary", ""),
                error=raw.get("error"),
                artifacts=raw.get("artifacts", {}),
                duration=raw.get("duration", 0.0),
                sub_goals=raw.get("sub_goals", []),
                suggested_tools=raw.get("suggested_tools", []),
                suggested_model=raw.get("suggested_model"),
            )
        return DelegateResult(
            task_id=task_id,
            status=DelegateStatus.COMPLETED,
            output=raw,
            summary=str(raw)[:100],
        )

    def _normalize_final(self, result: dict[str, Any]) -> dict[str, Any]:
        """标准化最终输出格式。"""
        return {
            "status": result.get("status", "completed"),
            "summary": result.get("summary", ""),
            "outputs": result.get("outputs", []),
            "merged_output": result.get("merged_output", {}),
            "total_tasks": result.get("total_tasks", 0),
            "success_count": result.get("success_count", 0),
            "failed_count": result.get("failed_count", 0),
            "total_duration": result.get("total_duration", 0.0),
            "total_delegations": result.get("total_delegations", 0),
        }

    @staticmethod
    def _default_decompose(goal: str) -> list[SubTask]:
        """默认拆解策略：将目标按关键分隔符拆分为子任务列表。

        如果目标包含「且」「并且」「同时」「步骤」等词，拆分为多个子任务。
        否则返回单个子任务。

        Args:
            goal: 目标文本。

        Returns:
            子任务列表。
        """
        import re

        # 尝试按序号或分隔符拆分
        separators = [
            r"\d+[\.、．]\s*",  # "1. " / "1、" / "1．"
            r"(?:且|并且|同时|然后|接着|下一步)\s*",
            r"\n{2,}",  # 空行分隔
        ]

        for sep in separators:
            parts = re.split(sep, goal)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) > 1:
                return [
                    SubTask(
                        task_id=f"task_{uuid.uuid4().hex[:8]}",
                        goal=part,
                        recipe={
                            "instruction": f"请完成以下子任务：{part}",
                            "context_spec": {},
                            "tools": [],
                            "model_spec": {"model": "default"},
                        },
                    )
                    for part in parts
                ]

        # 默认：整个目标作为一个任务
        return [
            SubTask(
                task_id=f"task_{uuid.uuid4().hex[:8]}",
                goal=goal,
                recipe={
                    "instruction": f"请完成以下任务：{goal}",
                    "context_spec": {},
                    "tools": [],
                    "model_spec": {"model": "default"},
                },
            )
        ]
