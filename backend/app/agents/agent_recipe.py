"""agent_recipe.py — 四元组智能体配方 (Agent Quadruple Recipe)

A Orchestra 核心数据模型：将智能体实例标准化为
    Agent = (Instruction, Context, Tools, Model)
四元组配方，实现智能体的工厂化生产。

Usage:
    recipe = AgentRecipe(
        instruction="你是一个资深Python工程师",
        context={"project": "MyApp", "lang": "python"},
        tools=["shell", "file-reader"],
        model_spec={"model": "deepseek", "tier": 2},
    )
    registry = RecipeRegistry()
    rid = registry.register(recipe)
    agent_config = compose_agent(recipe)

纯标准库，无外部依赖。
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


# ── 四元组核心数据结构 ──────────────────────────────────────────────────────


@dataclass
class AgentRecipe:
    """四元组智能体配方。

    将智能体拆解为四个标准化要素：
        instruction  — 系统指令 / 角色定义（永恒不变）
        context_spec — 上下文规格（任务特有输入数据）
        tools        — 允许使用的工具列表
        model_spec   — 模型规格（模型名、层级、参数等）

    Attributes:
        instruction: 系统指令/角色定义。这是智能体的「人格」，不随任务变化。
        context_spec: 上下文规格。键值对形式存储任务输入数据。
        tools: 允许该智能体使用的工具名称列表。
        model_spec: 模型规格字典，至少包含 "model" 键。
        recipe_id: 配方唯一标识。自动生成或手动指定。
        parent_id: 父级配方ID，用于委派链路溯源。
        max_iterations: 最大迭代/执行步数上限。
        created_at: 创建时间戳（Unix时间）。
        tags: 标签列表，用于分类检索。
    """

    instruction: str
    context_spec: dict[str, Any] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    model_spec: dict[str, Any] = field(default_factory=lambda: {"model": "default"})

    # 元数据
    recipe_id: str = ""
    parent_id: Optional[str] = None
    max_iterations: int = 30
    created_at: Optional[float] = None
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """初始化后自动补充 recipe_id 和 created_at。"""
        if not self.recipe_id:
            self.recipe_id = f"recipe_{uuid.uuid4().hex[:12]}"
        if self.created_at is None:
            self.created_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        """将配方导出为纯字典（JSON 友好）。"""
        return {
            "instruction": self.instruction,
            "context_spec": dict(self.context_spec),
            "tools": list(self.tools),
            "model_spec": dict(self.model_spec),
            "recipe_id": self.recipe_id,
            "parent_id": self.parent_id,
            "max_iterations": self.max_iterations,
            "created_at": self.created_at,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentRecipe:
        """从字典重建配方。"""
        return cls(
            instruction=data["instruction"],
            context_spec=data.get("context_spec", {}),
            tools=data.get("tools", []),
            model_spec=data.get("model_spec", {"model": "default"}),
            recipe_id=data.get("recipe_id", ""),
            parent_id=data.get("parent_id"),
            max_iterations=data.get("max_iterations", 30),
            created_at=data.get("created_at"),
            tags=data.get("tags", []),
        )

    def freeze(self) -> str:
        """冻结配方为不可变哈希标识，用于缓存去重。

        Returns:
            16字符的十六进制哈希字符串。
        """
        raw = (
            f"{self.instruction}|"
            f"{sorted(self.context_spec.keys())}|"
            f"{sorted(self.tools)}|"
            f"{self.model_spec}"
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def with_context(self, **extra_context: Any) -> AgentRecipe:
        """返回一个附加额外上下文的配方副本（不修改原配方）。"""
        new_context = dict(self.context_spec)
        new_context.update(extra_context)
        return AgentRecipe(
            instruction=self.instruction,
            context_spec=new_context,
            tools=list(self.tools),
            model_spec=dict(self.model_spec),
            parent_id=self.parent_id or self.recipe_id,
            max_iterations=self.max_iterations,
            tags=list(self.tags),
        )

    def with_tools(self, *extra_tools: str) -> AgentRecipe:
        """返回一个附加额外工具的配方副本。"""
        return AgentRecipe(
            instruction=self.instruction,
            context_spec=dict(self.context_spec),
            tools=list(self.tools) + list(extra_tools),
            model_spec=dict(self.model_spec),
            parent_id=self.parent_id or self.recipe_id,
            max_iterations=self.max_iterations,
            tags=list(self.tags),
        )


# ── 配方注册表 ──────────────────────────────────────────────────────────────


class RecipeRegistry:
    """配方注册表 — 按 recipe_id 存储和检索配方。

    支持：
        - 注册新配方
        - 按 ID 检索
        - 按父配方 ID 查找子配方
        - 按标签分类查找
        - 根据目标文本选择最佳匹配配方
    """

    def __init__(self) -> None:
        self._store: dict[str, AgentRecipe] = {}

    def register(self, recipe: AgentRecipe) -> str:
        """注册一个配方。

        Args:
            recipe: 要注册的配方实例。

        Returns:
            配方的 recipe_id。
        """
        self._store[recipe.recipe_id] = recipe
        return recipe.recipe_id

    def get(self, recipe_id: str) -> Optional[AgentRecipe]:
        """按 recipe_id 获取配方。"""
        return self._store.get(recipe_id)

    def find_by_parent(self, parent_id: str) -> list[AgentRecipe]:
        """查找所有指定父配方的子配方。"""
        return [r for r in self._store.values() if r.parent_id == parent_id]

    def find_by_tag(self, tag: str) -> list[AgentRecipe]:
        """查找包含指定标签的所有配方。"""
        return [r for r in self._store.values() if tag in r.tags]

    def find_by_goal(self, goal: str) -> list[AgentRecipe]:
        """根据任务目标文本关键词匹配配方（基于 instruction 和 tags）。

        Args:
            goal: 任务目标文本。

        Returns:
            按匹配分数降序排列的配方列表。
        """
        goal_lower = goal.lower()
        scored: list[tuple[int, AgentRecipe]] = []

        for recipe in self._store.values():
            score = 0
            # instruction 关键词匹配
            for word in recipe.instruction.split():
                if word.lower() in goal_lower:
                    score += 1
            # tags 精准匹配
            for tag in recipe.tags:
                if tag.lower() in goal_lower:
                    score += 3
            if score > 0:
                scored.append((score, recipe))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored]

    def select_best(self, goal: str) -> Optional[AgentRecipe]:
        """根据目标选择最佳匹配配方。

        Args:
            goal: 任务目标文本。

        Returns:
            最佳匹配配方，若无匹配则返回 None。
        """
        candidates = self.find_by_goal(goal)
        return candidates[0] if candidates else None

    def remove(self, recipe_id: str) -> bool:
        """删除指定 recipe_id 的配方。"""
        return self._store.pop(recipe_id, None) is not None

    def list_all(self) -> list[AgentRecipe]:
        """返回所有已注册配方。"""
        return list(self._store.values())

    def count(self) -> int:
        """返回已注册配方数量。"""
        return len(self._store)

    def clear(self) -> None:
        """清空注册表。"""
        self._store.clear()


# ── 配方装配器 ──────────────────────────────────────────────────────────────


def compose_agent(recipe: AgentRecipe) -> dict[str, Any]:
    """从配方装配智能体配置字典，供运行时消费。

    将四元组配方转换为包含 system_prompt（instruction + context）、
    tools 列表、model 标识和运行时配置的统一字典。

    Args:
        recipe: 四元组配方。

    Returns:
        智能体配置字典，包含以下键：
            - system_prompt: 组装后的系统提示词
            - context: 上下文规格的原始副本
            - tools: 工具名称列表
            - model_spec: 模型规格
            - config: 运行时配置（max_iterations 等）
    """
    system_prompt = _build_system_prompt(recipe)
    return {
        "system_prompt": system_prompt,
        "context": dict(recipe.context_spec),
        "tools": list(recipe.tools),
        "model_spec": dict(recipe.model_spec),
        "config": {
            "max_iterations": recipe.max_iterations,
            "recipe_id": recipe.recipe_id,
            "parent_id": recipe.parent_id,
        },
    }


def _build_system_prompt(recipe: AgentRecipe) -> str:
    """从 instruction 和 context 组装系统提示词。

    instruction 在前（角色定义），context 在后（任务数据），
    中间用标记分隔以明确边界。

    Args:
        recipe: 四元组配方。

    Returns:
        组装后的系统提示词字符串。
    """
    parts: list[str] = [recipe.instruction]

    if recipe.context_spec:
        context_lines: list[str] = []
        for key, value in recipe.context_spec.items():
            context_lines.append(f"## {key}")
            context_lines.append(str(value))
        parts.append("[上下文]\n" + "\n".join(context_lines))

    return "\n\n".join(parts)


# ── 便捷工厂函数 ────────────────────────────────────────────────────────────


def make_recipe(
    instruction: str,
    *,
    context: Optional[dict[str, Any]] = None,
    tools: Optional[list[str]] = None,
    model: str = "default",
    model_params: Optional[dict[str, Any]] = None,
    recipe_id: str = "",
    parent_id: Optional[str] = None,
    max_iterations: int = 30,
    tags: Optional[list[str]] = None,
) -> AgentRecipe:
    """快速创建 AgentRecipe 的便捷函数。

    Args:
        instruction: 系统指令/角色定义。
        context: 上下文规格字典。
        tools: 工具名称列表。
        model: 模型名称（简写，自动构建 model_spec）。
        model_params: 额外的模型参数。
        recipe_id: 配方ID（可选，自动生成）。
        parent_id: 父配方ID。
        max_iterations: 最大迭代次数。
        tags: 标签列表。

    Returns:
        构造好的 AgentRecipe 实例。
    """
    model_spec: dict[str, Any] = {"model": model}
    if model_params:
        model_spec.update(model_params)

    return AgentRecipe(
        instruction=instruction,
        context_spec=context or {},
        tools=tools or [],
        model_spec=model_spec,
        recipe_id=recipe_id,
        parent_id=parent_id,
        max_iterations=max_iterations,
        tags=tags or [],
    )
