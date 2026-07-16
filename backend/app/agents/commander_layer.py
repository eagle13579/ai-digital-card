"""commander_layer.py — F10 智能 Agent 指挥官调度层 (Commander Dispatch Layer)

A Orchestra 对外暴露的指挥官 API。提供五合一调度能力：
    1. decompose(goal)   → 自然语言目标拆解为子任务
    2. dispatch(spec)    → 委派子任务给对应 Agent 执行
    3. monitor(task_id)  → 监控子任务执行状态
    4. aggregate(results) → 整合所有子结果
    5. orchestrate(goal) → 端到端执行（拆解→委派→监控→整合）

底层自动复用已有组件，无需额外配置即可投入生产使用：
    - DynamicFactory.analyze_task()      → 任务分析拆解
    - OrchestratorLoop.delegate()        → 任务委派
    - OrchestraPipeline.execute()        → 端到端管线底层实现
    - FinalResult / SubResult            → 结构化结果协议
    - CompressionProtocol / context_distillation → 上下文压缩

Usage:
    # 快速上手
    from app.agents.commander_layer import CommanderLayer, CommanderConfig

    commander = CommanderLayer()
    result = await commander.orchestrate("调研50家公司的董事会结构")

    # 分步执行
    tasks = commander.decompose("分析用户行为数据")
    for t in tasks:
        sr = await commander.dispatch(t)
        status = commander.monitor(t.task_id)
    final = commander.aggregate([sr])

纯标准库 + dataclasses + typing，不修改现有代码。
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from app.agents.orchestrator_loop import (
    OrchestratorLoop,
    SubTask,
    DelegateResult,
    DelegateStatus,
)
from app.agents.dynamic_agent_factory import DynamicFactory, SubAgentSpec
from app.agents.model_task_matcher import ModelMatcher, TaskComplexityAnalyzer
from app.agents.compression_protocol import context_distillation, CompressionProtocol
from app.agents.orchestra_pipeline import (
    OrchestraPipeline,
    FinalResult,
    SubResult,
    ParadigmAdapter,
    ContextDistillation,
)


# ── 指挥官配置 ────────────────────────────────────────────────────────────────


@dataclass
class CommanderConfig:
    """指挥官可配置参数。

    Attributes:
        max_workers: 最大并发工作数，默认 5。
        default_backend: 默认执行后端，默认 "react"。
        compression_ratio: 上下文压缩率，默认 0.3。
        enable_monitoring: 是否启用任务监控，默认 True。
    """

    max_workers: int = 5
    default_backend: str = "react"
    compression_ratio: float = 0.3
    enable_monitoring: bool = True


# ── 指挥官调度层 ──────────────────────────────────────────────────────────────


class CommanderLayer:
    """F10 智能 Agent 指挥官调度层。

    对外暴露的指挥官 API，提供五合一调度能力：
        1. decompose(goal)    — 自然语言目标拆解为子任务列表
        2. dispatch(spec)     — 委派子任务给对应 Agent 执行
        3. monitor(task_id)   — 监控子任务执行状态
        4. aggregate(results) — 整合所有子结果
        5. orchestrate(goal)  — 端到端执行（拆解→委派→监控→整合）

    底层自动利用已有组件：
        - decompose()  内部调用 DynamicFactory.analyze_task()
        - dispatch()   内部调用 OrchestratorLoop.delegate()
        - aggregate()  内部调用 FinalResult 协议
        - orchestrate() 直接复用 OrchestraPipeline.execute() 作为底层实现

    Args:
        config: 可选的指挥官配置。若不提供，使用默认配置。
        factory: 可选的 DynamicFactory 实例。若不提供，自动创建。
        orchestrator: 可选的 OrchestratorLoop 实例。若不提供，自动创建。
        pipeline: 可选的 OrchestraPipeline 实例。若不提供，自动创建。
        matcher: 可选的 ModelMatcher 实例。若不提供，自动创建。
    """

    def __init__(
        self,
        config: Optional[CommanderConfig] = None,
        factory: Optional[DynamicFactory] = None,
        orchestrator: Optional[OrchestratorLoop] = None,
        pipeline: Optional[OrchestraPipeline] = None,
        matcher: Optional[ModelMatcher] = None,
    ) -> None:
        self.config = config or CommanderConfig()

        # 组件初始化
        self._matcher = matcher or ModelMatcher()
        self._factory = factory or DynamicFactory()
        self._compressor = CompressionProtocol(
            compression_ratio=self.config.compression_ratio,
        )

        # 编排器需要委派函数，使用默认委派
        self._orchestrator = orchestrator or OrchestratorLoop(
            delegate_fn=self._default_delegate_fn,
        )

        # 管线需要注入编排器以避免 OrchestratorLoop() 无参构造失败
        self._pipeline = pipeline or OrchestraPipeline(
            factory=self._factory,
            orchestrator=self._orchestrator,
            matcher=self._matcher,
            adapter=ParadigmAdapter(default_backend=self.config.default_backend),
            distillation=ContextDistillation(
                compression=CompressionProtocol(ratio=self.config.compression_ratio),
            ),
        )

        # ── 内部状态跟踪 ──────────────────────────────────────────────
        self._tasks: dict[str, SubTask] = {}
        """task_id → SubTask 映射。"""

        self._task_status: dict[str, str] = {}
        """task_id → 状态字符串（pending/running/success/failed）。"""

        self._task_results: dict[str, SubResult] = {}
        """task_id → SubResult 映射（仅已完成的任务）。"""

        self._task_start_time: dict[str, float] = {}
        """task_id → 开始时间戳。"""

    # ── 指挥官五合一 API ──────────────────────────────────────────────────

    def decompose(self, goal: str) -> list[SubTask]:
        """将自然语言目标拆解为子任务列表。

        内部调用 DynamicFactory.analyze_task() 进行任务分析，
        根据分析结果（task_type、keywords、suggested_tools 等）
        动态生成多个结构化的 SubTask 实例。

        Args:
            goal: 自然语言描述的目标字符串。

        Returns:
            拆解后的子任务列表。每个 SubTask 包含完整的 recipe 四元组。
        """
        # Step 1: 通过 DynamicFactory 分析任务
        analysis = self._factory.analyze_task(goal)
        task_type: str = analysis.get("task_type", "默认")
        keywords: list[str] = analysis.get("keywords", [])
        suggested_tools: list[str] = analysis.get("suggested_tools", [])
        instruction: str = analysis.get("instruction", "")
        estimated_subtasks: int = analysis.get("estimated_subtasks", 1)

        # Step 2: 构建基础四元组配方
        base_recipe: dict[str, Any] = {
            "instruction": instruction or f"请完成以下任务：{goal}",
            "context_spec": analysis.get("context", {}),
            "tools": suggested_tools,
            "model_spec": {
                "model": analysis.get("model", "default"),
                "tier": analysis.get("suggested_model_tier", 1),
            },
        }

        # Step 3: 生成子任务
        subtasks: list[SubTask] = []

        if estimated_subtasks > 1 and keywords:
            # 多子任务模式：基于关键词分片拆解
            chunk_size = max(1, len(keywords) // estimated_subtasks)
            for i in range(estimated_subtasks):
                chunk_keywords = keywords[
                    i * chunk_size : (i + 1) * chunk_size
                ]
                if chunk_keywords:
                    sub_goal = f"{task_type}子任务{i + 1}：{' '.join(chunk_keywords)}"
                else:
                    sub_goal = f"{goal} — 子任务{i + 1}"

                sub_recipe = dict(base_recipe)
                sub_recipe["instruction"] = (
                    f"子任务{i + 1}/{estimated_subtasks}：{sub_goal}"
                )

                sub_task = SubTask(
                    task_id=f"cmd_{uuid.uuid4().hex[:8]}",
                    goal=sub_goal,
                    recipe=sub_recipe,
                    status="pending",
                )
                subtasks.append(sub_task)
                self._register_task(sub_task)
        else:
            # 单一子任务模式
            sub_task = SubTask(
                task_id=f"cmd_{uuid.uuid4().hex[:8]}",
                goal=goal,
                recipe=base_recipe,
                status="pending",
            )
            subtasks.append(sub_task)
            self._register_task(sub_task)

        return subtasks

    async def dispatch(self, spec: SubAgentSpec | SubTask) -> SubResult:
        """委派子任务给对应的 Agent 执行。

        内部调用 OrchestratorLoop.delegate() 进行实际委派。
        支持两种输入格式：
            - SubAgentSpec（来自 DynamicFactory.spawn()）
            - SubTask（来自 CommanderLayer.decompose()）

        Args:
            spec: 子任务规格。

        Returns:
            子任务执行结果（SubResult 格式）。

        Raises:
            TypeError: 当 spec 类型不支持时。
        """
        # Step 1: 统一为 SubTask 格式
        if isinstance(spec, SubAgentSpec):
            sub_task = SubTask(
                task_id=spec.agent_id,
                goal=spec.goal,
                recipe=spec.recipe,
                parent_task_id=spec.parent_agent_id,
                status="running",
            )
        elif isinstance(spec, SubTask):
            sub_task = spec
            sub_task.status = "running"
        else:
            raise TypeError(
                f"不支持的规格类型: {type(spec).__name__}，"
                f"需要 SubAgentSpec 或 SubTask"
            )

        # Step 2: 记录开始状态
        task_id = sub_task.task_id
        self._task_status[task_id] = "running"
        self._task_start_time[task_id] = time.time()
        if task_id not in self._tasks:
            self._tasks[task_id] = sub_task

        # Step 3: 通过 OrchestratorLoop.delegate() 执行委派
        delegate_result = await self._orchestrator.delegate(
            sub_task, sub_task.recipe
        )

        # Step 4: 将 DelegateResult 转换为 SubResult 格式
        sub_result = SubResult(
            task_id=task_id,
            agent_id=task_id,
            status=(
                "success"
                if delegate_result.is_success()
                else "failed"
            ),
            summary=delegate_result.summary
            or str(delegate_result.output or "")[:120],
            raw_output=str(delegate_result.output or ""),
            signals=[
                {
                    "source": "commander_dispatch",
                    "signal": delegate_result.summary,
                    "confidence": "high",
                }
            ],
            cost_estimate=round(delegate_result.duration * 0.01, 6),
            error=delegate_result.error,
        )

        # Step 5: 更新内部状态
        self._task_status[task_id] = sub_result.status
        self._task_results[task_id] = sub_result

        # 若需要分解，递归分解子任务
        if delegate_result.needs_decomposition() and delegate_result.sub_goals:
            for sub_goal in delegate_result.sub_goals:
                child_task = SubTask(
                    task_id=f"sub_{uuid.uuid4().hex[:8]}",
                    goal=sub_goal,
                    recipe={
                        "instruction": f"子任务：{sub_goal}",
                        "context_spec": sub_task.recipe.get("context_spec", {}),
                        "tools": delegate_result.suggested_tools
                        or sub_task.recipe.get("tools", []),
                        "model_spec": (
                            {"model": delegate_result.suggested_model}
                            if delegate_result.suggested_model
                            else sub_task.recipe.get("model_spec", {"model": "default"})
                        ),
                    },
                    parent_task_id=task_id,
                    status="pending",
                )
                self._register_task(child_task)

        return sub_result

    def monitor(self, task_id: str) -> dict[str, Any]:
        """监控指定子任务的执行状态。

        返回包含以下信息的字典：
            - task_id: 任务唯一标识
            - status: 当前状态（pending/running/success/failed/unknown）
            - elapsed: 已消耗时间（秒）
            - goal: 任务目标描述（若存在）
            - summary: 执行摘要（若已完成）
            - error: 错误信息（若有）
            - exists: 任务是否存在
            - cost_estimate: 成本估计（若已完成）

        Args:
            task_id: 子任务的唯一标识。

        Returns:
            包含任务状态信息的字典。
        """
        if task_id not in self._task_status:
            return {
                "task_id": task_id,
                "status": "unknown",
                "error": f"任务 {task_id} 不存在",
                "exists": False,
            }

        status = self._task_status[task_id]
        elapsed = 0.0
        if task_id in self._task_start_time:
            elapsed = round(time.time() - self._task_start_time[task_id], 2)

        result: dict[str, Any] = {
            "task_id": task_id,
            "status": status,
            "elapsed": elapsed,
            "exists": True,
        }

        # 添加目标信息
        if task_id in self._tasks:
            result["goal"] = self._tasks[task_id].goal

        # 添加结果信息（若已完成）
        if status in ("success", "failed") and task_id in self._task_results:
            sr = self._task_results[task_id]
            result["summary"] = sr.summary
            result["error"] = sr.error
            result["cost_estimate"] = sr.cost_estimate

        # 运行中的进度提示
        if status == "running" and self.config.enable_monitoring:
            result["progress_note"] = "任务正在执行中..."

        return result

    def aggregate(self, results: list[SubResult]) -> FinalResult:
        """整合所有子任务执行结果。

        将多个 SubResult 合并为单一的 FinalResult，并自动：
            - 应用压缩协议精简每个子结果的信号和摘要
            - 计算执行统计（总数/成功/失败）
            - 生成可读的执行摘要
            - 标记最终状态（completed/partial/failed）

        Args:
            results: 子任务结果列表。

        Returns:
            整合后的最终结果。
        """
        # Step 1: 从跟踪数据中推断目标
        goal = ""
        for task in self._tasks.values():
            goal = task.goal
            break

        final = FinalResult(goal=goal)

        # Step 2: 逐个处理子结果，应用压缩
        for sr in results:
            # 应用压缩协议精简信号
            raw_signals = sr.signals if sr.signals else [
                {
                    "source": "commander",
                    "content": sr.summary,
                    "confidence": "high",
                }
            ]
            compressed_signal = self._compressor.distill(
                raw_signals,
                max_signals=max(1, int(self.config.compression_ratio * 10)),
            )

            # 构建压缩后的 SubResult
            compressed_sr = SubResult(
                task_id=sr.task_id,
                agent_id=sr.agent_id,
                status=sr.status,
                summary=self._compressor.compress(sr.summary, max_chars=200),
                raw_output=sr.raw_output[:500] if sr.raw_output else "",
                signals=[{"distilled": compressed_signal}],
                cost_estimate=sr.cost_estimate,
                error=sr.error,
            )
            final.add_sub_result(compressed_sr)

        # Step 3: 生成人类可读的执行摘要
        summary_parts: list[str] = []
        for sr in final.sub_results:
            icon = (
                "✓"
                if sr.status == "success"
                else "✗" if sr.status == "failed" else "…"
            )
            summary_parts.append(f"[{icon}] {sr.task_id}: {sr.summary[:50]}")
        final.summary = (
            " | ".join(summary_parts)
            + f" | 压缩率={self.config.compression_ratio:.0%}"
        )

        return final.close()

    async def orchestrate(self, goal: str) -> FinalResult:
        """端到端执行：拆解→委派→监控→整合。

        直接复用 OrchestraPipeline.execute() 作为底层实现，
        将目标完整执行一遍并返回最终结构化结果。

        管线内部流程：
            1. 编排器拆解任务
            2. 上下文提纯（压缩协议）
            3. 任务分析 + 动态生成子智能体
            4. 模型匹配（复杂度分析 + 模型选择）
            5. 范式适配器执行
            6. 结果整合
            7. 反馈闭环

        Args:
            goal: 自然语言描述的目标。

        Returns:
            最终整合的执行结果。
        """
        # 直接复用底层管线
        final = await self._pipeline.execute(
            goal=goal,
            backend=self.config.default_backend,
        )

        # 将管线结果同步到本地状态跟踪
        for sr in final.sub_results:
            task_id = sr.task_id
            self._task_results[task_id] = sr
            self._task_status[task_id] = sr.status

        # 对最终摘要应用压缩
        if final.summary:
            final.summary = self._compressor.compress(
                final.summary, max_chars=500
            )

        return final

    # ── 辅助方法 ──────────────────────────────────────────────────────────

    async def _default_delegate_fn(
        self, sub_task: SubTask, recipe: dict[str, Any]
    ) -> dict[str, Any]:
        """默认委派函数 — 通过 Pipeline 的 ParadigmAdapter 执行子任务。

        当 OrchestratorLoop 需要实际执行任务时调用此方法。

        Args:
            sub_task: 子任务单元。
            recipe: 四元组配方字典。

        Returns:
            标准化结果字典，包含 status / output / summary / error / artifacts。
        """
        spec = SubAgentSpec(
            agent_id=sub_task.task_id,
            goal=sub_task.goal,
            recipe=recipe,
            name=f"subagent_{sub_task.task_id}",
        )
        try:
            sub_result = await self._pipeline.adapter.execute(
                spec, backend=self.config.default_backend
            )
            return {
                "status": (
                    "completed"
                    if sub_result.status == "success"
                    else "failed"
                ),
                "output": sub_result.raw_output,
                "summary": sub_result.summary,
                "error": sub_result.error,
                "artifacts": {},
            }
        except Exception as exc:
            return {
                "status": "failed",
                "output": "",
                "summary": f"委派执行异常: {exc}",
                "error": str(exc),
                "artifacts": {},
            }

    def _register_task(self, task: SubTask) -> None:
        """在内部状态中注册一个子任务。"""
        self._tasks[task.task_id] = task
        self._task_status[task.task_id] = task.status

    # ── 查询与工具方法 ────────────────────────────────────────────────────

    def list_tasks(self) -> list[dict[str, Any]]:
        """列出所有已跟踪的任务状态快照。

        Returns:
            任务状态字典列表，按 task_id 排序。
        """
        return [
            {
                "task_id": tid,
                "status": self._task_status.get(tid, "unknown"),
                "goal": (
                    self._tasks[tid].goal[:60] + "..." if len(self._tasks[tid].goal) > 60
                    else self._tasks[tid].goal
                )
                if tid in self._tasks
                else "",
            }
            for tid in sorted(self._task_status.keys())
        ]

    def get_summary(self) -> dict[str, Any]:
        """获取指挥官整体执行摘要。

        Returns:
            包含配置和统计信息的摘要字典：
                - config: 当前配置参数快照
                - stats: 执行统计（总数/成功/失败/运行中/待处理）
                - overall_status: 整体状态（completed/failed/in_progress/idle）
        """
        total = len(self._task_status)
        completed = sum(1 for s in self._task_status.values() if s == "success")
        failed = sum(1 for s in self._task_status.values() if s == "failed")
        running = sum(1 for s in self._task_status.values() if s == "running")
        pending = sum(1 for s in self._task_status.values() if s == "pending")

        # 推断整体状态
        if total == 0:
            overall = "idle"
        elif failed == 0 and completed == total:
            overall = "completed"
        elif completed == 0 and failed > 0:
            overall = "failed"
        elif running > 0:
            overall = "in_progress"
        else:
            overall = "partial"

        return {
            "config": {
                "max_workers": self.config.max_workers,
                "default_backend": self.config.default_backend,
                "compression_ratio": self.config.compression_ratio,
                "enable_monitoring": self.config.enable_monitoring,
            },
            "stats": {
                "total_tasks": total,
                "completed": completed,
                "failed": failed,
                "running": running,
                "pending": pending,
            },
            "overall_status": overall,
        }

    def get_task(self, task_id: str) -> Optional[SubTask]:
        """通过 task_id 获取 SubTask 对象。

        Args:
            task_id: 任务唯一标识。

        Returns:
            SubTask 对象，若不存在则返回 None。
        """
        return self._tasks.get(task_id)

    def get_result(self, task_id: str) -> Optional[SubResult]:
        """通过 task_id 获取执行结果。

        Args:
            task_id: 任务唯一标识。

        Returns:
            SubResult 对象，若任务未完成或不存在则返回 None。
        """
        return self._task_results.get(task_id)

    def reset(self) -> None:
        """重置指挥官内部状态，清空所有跟踪数据。

        调用后所有已注册的任务和结果都将丢失。
        新的执行将从干净的状态开始。
        """
        self._tasks.clear()
        self._task_status.clear()
        self._task_results.clear()
        self._task_start_time.clear()
