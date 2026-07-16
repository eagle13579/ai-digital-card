"""orchestra_pipeline.py — A Orchestra 统一管线

串联4个核心模块为端到端工作流：
  agent_recipe → dynamic_agent_factory → orchestrator_loop → model_task_matcher
  ↑                                        ↓
  compression_protocol (上下文提纯)     result_protocol (结果整合)

Usage:
    pipeline = OrchestraPipeline()
    result = await pipeline.execute("调研50家公司的董事会结构")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.agents.agent_recipe import AgentRecipe, RecipeRegistry
from app.agents.dynamic_agent_factory import DynamicFactory, SubAgentSpec
from app.agents.orchestrator_loop import OrchestratorLoop, OrchestratorState
from app.agents.model_task_matcher import ModelMatcher, TaskComplexityAnalyzer
from app.agents.compression_protocol import CompressionProtocol, context_distillation

logger = logging.getLogger(__name__)


# ── 结构化结果协议（内嵌）──────────────────────────────────────


@dataclass
class SubResult:
    """单个子智能体的结构化结果。"""
    task_id: str
    agent_id: str
    status: str  # success / failed / timeout
    summary: str
    raw_output: str = ""
    signals: list[dict] = field(default_factory=list)
    cost_estimate: float = 0.0
    error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class FinalResult:
    """编排器最终输出，整合所有子结果。"""
    goal: str
    status: str = "running"  # running / completed / partial / failed
    summary: str = ""
    sub_results: list[SubResult] = field(default_factory=list)
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_cost_estimate: float = 0.0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: str | None = None

    def add_sub_result(self, sr: SubResult) -> None:
        self.sub_results.append(sr)
        self.total_tasks += 1
        if sr.status == "success":
            self.completed_tasks += 1
        else:
            self.failed_tasks += 1
        self.total_cost_estimate += sr.cost_estimate
        self._update_summary()

    def _update_summary(self) -> None:
        done = self.completed_tasks
        total = self.total_tasks
        pct = round(done / total * 100, 1) if total else 0
        self.summary = f"[{done}/{total} {pct}%] 信号密度={self._signal_density():.2f}"

    def _signal_density(self) -> float:
        if not self.sub_results:
            return 0.0
        total_signals = sum(len(sr.signals) for sr in self.sub_results)
        total_raw = sum(len(sr.raw_output) for sr in self.sub_results) or 1
        return total_signals / (total_raw / 1000)

    def close(self) -> FinalResult:
        self.status = "completed" if self.failed_tasks == 0 else "partial"
        self.finished_at = datetime.now().isoformat()
        self._update_summary()
        return self


# ── 范式兼容适配器（内嵌）──────────────────────────────────────


class ParadigmAdapter:
    """范式兼容适配器 — 支持多种执行后端（ReAct/OpenHands/Mini-SWE）。

    A Orchestra 的深度解耦理念：编排器对执行后端完全透明。
    """

    BACKENDS = {"react", "openhands", "mini_swe"}

    def __init__(self, default_backend: str = "react"):
        if default_backend not in self.BACKENDS:
            raise ValueError(f"不支持的执行后端: {default_backend}, 可选: {self.BACKENDS}")
        self._default_backend = default_backend
        self._registry: dict[str, callable] = {}

    def register_backend(self, name: str, executor: callable) -> None:
        """注册自定义执行后端。"""
        self._registry[name] = executor

    async def execute(self, spec: SubAgentSpec, backend: str | None = None) -> SubResult:
        """按指定后端执行子任务。"""
        actual_backend = backend or self._default_backend
        executor = self._registry.get(actual_backend)
        if executor:
            return await executor(spec)

        # 默认 react 风格的模拟执行
        if actual_backend == "react":
            return await self._react_execute(spec)
        elif actual_backend == "openhands":
            return await self._openhands_execute(spec)
        elif actual_backend == "mini_swe":
            return await self._mini_swe_execute(spec)
        else:
            return SubResult(
                task_id=spec.task_id,
                agent_id=spec.agent_id,
                status="failed",
                summary=f"未知后端: {actual_backend}",
                error=f"后端 {actual_backend} 未注册且无默认实现",
            )

    async def _react_execute(self, spec: SubAgentSpec) -> SubResult:
        """ReAct 模式：观察→思考→行动循环。"""
        signals = [
            {"source": "react_planner", "signal": f"规划: {spec.recipe.instruction}", "confidence": "high"},
            {"source": "react_tools", "signal": f"工具: {spec.tools}", "confidence": "medium"},
        ]
        return SubResult(
            task_id=spec.task_id,
            agent_id=spec.agent_id,
            status="success",
            summary=f"[ReAct] {spec.recipe.instruction[:60]}... | 工具={spec.tools}",
            signals=signals,
            cost_estimate=0.5,
        )

    async def _openhands_execute(self, spec: SubAgentSpec) -> SubResult:
        """OpenHands 模式：多模态操作+浏览器交互。"""
        return SubResult(
            task_id=spec.task_id,
            agent_id=spec.agent_id,
            status="success",
            summary=f"[OpenHands] {spec.recipe.instruction[:60]}...",
            signals=[{"source": "openhands", "signal": "多模态执行", "confidence": "high"}],
            cost_estimate=2.0,
        )

    async def _mini_swe_execute(self, spec: SubAgentSpec) -> SubResult:
        """Mini-SWE 模式：代码修复专用。"""
        return SubResult(
            task_id=spec.task_id,
            agent_id=spec.agent_id,
            status="success",
            summary=f"[Mini-SWE] {spec.recipe.instruction[:60]}...",
            signals=[{"source": "mini_swe", "signal": "代码修复", "confidence": "high"}],
            cost_estimate=1.5,
        )


# ── 上下文提纯装饰器 ────────────────────────────────────────────


class ContextDistillation:
    """上下文提纯 — A Orchestra 的核心创新(84%→96%)。

    包装 CompressionProtocol，在委派前对上下文做精准筛选而非堆叠。
    """

    def __init__(self, compression: CompressionProtocol | None = None):
        self._compression = compression or CompressionProtocol(ratio=0.3)

    def distill(self, context: dict | str, task_focus: str) -> str:
        """将上下文提纯为仅与task_focus相关的信号。

        1. 如果是dict，提取关键字段
        2. 通过compression协议压缩
        3. 只保留与task_focus关键词匹配的信号
        """
        raw: str
        if isinstance(context, dict):
            raw = json.dumps(context, ensure_ascii=False, indent=2)
        else:
            raw = context

        # 精确筛选而非堆叠：只保留包含task_focus关键词的行
        focus_keywords = task_focus.lower().split()
        filtered_lines = []
        for line in raw.split("\n"):
            if any(kw in line.lower() for kw in focus_keywords):
                filtered_lines.append(line)
        filtered = "\n".join(filtered_lines) if filtered_lines else raw

        # 压缩
        compressed = self._compression.compress_summary(filtered, max_chars=800)
        return compressed


# ── 统一管线 ────────────────────────────────────────────────────


class OrchestraPipeline:
    """A Orchestra 统一执行管线。

    工作流:
        接收goal → 配方选择 → 任务分析 → 子智能体生成 → 编排器委派
        → 后选择执行 → 结果整合 → 上下文提纯闭环
    """

    def __init__(
        self,
        recipe_registry: RecipeRegistry | None = None,
        factory: DynamicFactory | None = None,
        orchestrator: OrchestratorLoop | None = None,
        matcher: ModelMatcher | None = None,
        adapter: ParadigmAdapter | None = None,
        distillation: ContextDistillation | None = None,
    ):
        self.recipe_registry = recipe_registry or RecipeRegistry()
        self.factory = factory or DynamicFactory(registry=self.recipe_registry)
        self.orchestrator = orchestrator or OrchestratorLoop()
        self.matcher = matcher or ModelMatcher()
        self.adapter = adapter or ParadigmAdapter()
        self.distillation = distillation or ContextDistillation()

    async def execute(
        self,
        goal: str,
        context: dict | str | None = None,
        backend: str = "react",
        max_steps: int = 10,
    ) -> FinalResult:
        """全量执行管线。"""
        result = FinalResult(goal=goal)

        # Phase 1: 编排器拆解任务
        logger.info(f"[Pipeline] 开始执行: {goal[:60]}...")
        self.orchestrator.state = OrchestratorState.INITIAL

        for step in range(max_steps):
            if self.orchestrator.state == OrchestratorState.COMPLETED:
                break

            state = await self.orchestrator.orchestrate(goal)
            if state == OrchestratorState.COMPLETED:
                break

            # Phase 2: 上下文提纯
            distilled_ctx = ""
            if context:
                distilled_ctx = self.distillation.distill(context, goal)

            # Phase 3: 任务分析 + 动态生成子智能体
            analysis = self.factory.analyze_task(goal)
            spec = self.factory.spawn(analysis)

            # Phase 4: 模型匹配
            complexity = TaskComplexityAnalyzer.analyze(spec.recipe.instruction)
            model_profile = self.matcher.select_model(complexity)

            # 装饰spec
            spec.model_config["complexity"] = complexity
            spec.model_config["profile"] = model_profile.name

            # Phase 5: 执行（通过范式适配器）
            sub_result = await self.adapter.execute(spec, backend=backend)

            # Phase 6: 整合结果
            result.add_sub_result(sub_result)

            # Phase 7: 更新编排器状态（反馈闭环）
            if sub_result.status == "success":
                likelihood = len(self.orchestrator.history) / max(step + 1, 1)
                if likelihood > 0.7:
                    self.orchestrator.state = OrchestratorState.FEEDBACK
                else:
                    self.orchestrator.state = OrchestratorState.UPDATE

        return result.close()
