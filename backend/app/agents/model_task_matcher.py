"""model_task_matcher.py — 任务-模型动态匹配器 (Task-Model Dynamic Matcher)

A Orchestra 成本优化策略：根据子任务难度在轻量与深度推理模型间动态切换。
每次委派都重新匹配模型，避免将复杂任务分配给轻量模型导致重试。

三层模型池：
    Tier 1 (轻量):    低成本、低延迟 — 简单/分类/提取
    Tier 2 (中等):    平衡成本与能力 — 分析/代码/中等推理
    Tier 3 (深度推理): 高成本、高能力 — 战略/设计/复杂推理

Usage:
    analyzer = TaskComplexityAnalyzer()
    matcher = ModelMatcher()

    complexity = analyzer.analyze("分析用户行为数据")
    model = matcher.match("分析用户行为数据", context={"size": 1000})
    fallback = matcher.get_fallback_chain(model.name)

纯标准库 + dataclasses + typing。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


# ── 复杂度等级常量 ──────────────────────────────────────────────────────────

SIMPLE = 1       # 简单 — 提取/分类/格式化
MEDIUM = 2       # 中等 — 分析/代码/解释
COMPLEX = 3      # 复杂 — 战略/设计/推理

COMPLEXITY_LABELS: dict[int, str] = {
    SIMPLE: "简单",
    MEDIUM: "中等",
    COMPLEX: "复杂",
}


# ── 模型配置 ────────────────────────────────────────────────────────────────


@dataclass
class ModelProfile:
    """模型档案 — 描述一个可用的模型。

    Attributes:
        name: 模型唯一名称标识。
        tier: 模型层级（1=轻量, 2=中等, 3=深度推理）。
        cost_per_1k_input: 每千输入 token 的成本（美元）。
        cost_per_1k_output: 每千输出 token 的成本（美元）。
        max_tokens: 最大输出 token 数。
        capabilities: 能力标签列表，用于细粒度匹配。
        priority: 同一 tier 内的优先级（数值越小越优先）。
    """

    name: str
    tier: int
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    max_tokens: int = 4096
    capabilities: list[str] = field(default_factory=list)
    priority: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "tier": self.tier,
            "cost_per_1k_input": self.cost_per_1k_input,
            "cost_per_1k_output": self.cost_per_1k_output,
            "max_tokens": self.max_tokens,
            "capabilities": list(self.capabilities),
            "priority": self.priority,
        }

    @classmethod
    def lightweight(cls, name: str = "lightweight-model") -> ModelProfile:
        """创建轻量模型档案。"""
        return cls(
            name=name,
            tier=SIMPLE,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
            max_tokens=2048,
            capabilities=["extraction", "classification", "formatting", "parsing"],
        )

    @classmethod
    def medium(cls, name: str = "medium-model") -> ModelProfile:
        """创建中等模型档案。"""
        return cls(
            name=name,
            tier=MEDIUM,
            cost_per_1k_input=0.00014,
            cost_per_1k_output=0.00028,
            max_tokens=4096,
            capabilities=["analysis", "code", "explanation", "reasoning"],
        )

    @classmethod
    def deep_reasoning(cls, name: str = "deep-reasoning-model") -> ModelProfile:
        """创建深度推理模型档案。"""
        return cls(
            name=name,
            tier=COMPLEX,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            max_tokens=8192,
            capabilities=[
                "complex-reasoning", "strategy", "architecture",
                "creative", "multi-step-planning",
            ],
        )


# ── 复杂度分析器 ────────────────────────────────────────────────────────────


class TaskComplexityAnalyzer:
    """任务复杂度分析器 — 评估子任务的复杂度等级。

    评估维度：
        1. 关键词匹配（主要）：根据任务描述中的关键词判断
        2. 上下文规模（辅助）：大上下文自动升级复杂度
        3. 目标长度（辅助）：超长目标视为更复杂
    """

    # 各层级的复杂度关键词
    TIER_KEYWORDS: dict[int, set[str]] = {
        COMPLEX: {
            # 中文
            "推理", "战略", "设计", "架构", "创造", "创新",
            "复杂", "体系", "系统设计", "分布式", "并发",
            "机器学习", "深度学习", "优化算法",
            "商业模式", "战略规划", "长期规划",
            # 英文
            "reason", "strategic", "architecture", "design",
            "complex", "complicated", "multi-step", "innovative",
            "deep", "research", "synthesis",
        },
        MEDIUM: {
            # 中文
            "分析", "解释", "重构", "优化", "实现",
            "生成", "修改", "对比", "评估", "测试",
            "调试", "开发", "编写", "构建", "部署",
            # 英文
            "analyze", "explain", "refactor", "optimize", "implement",
            "generate", "modify", "compare", "evaluate", "test",
            "debug", "develop", "build", "deploy", "migrate",
        },
        SIMPLE: {
            # 中文
            "提取", "分类", "翻译", "格式化", "总结",
            "转换", "查询", "列举", "列出", "查找",
            "复制", "粘贴", "重命名",
            # 英文
            "extract", "classify", "translate", "format", "summarize",
            "convert", "query", "list", "find", "lookup",
            "parse", "sort", "filter",
        },
    }

    def __init__(self) -> None:
        """初始化复杂度分析器。"""
        self._custom_keywords: dict[int, set[str]] = {}

    def analyze(
        self,
        goal: str,
        context_size: int = 0,
        goal_length: int = 0,
    ) -> int:
        """评估任务复杂度等级。

        Args:
            goal: 任务目标描述文本。
            context_size: 上下文数据大小（字符数），用于辅助判断。
            goal_length: 目标文本长度（字符数），0 表示自动计算。

        Returns:
            复杂度等级：SIMPLE(1) / MEDIUM(2) / COMPLEX(3)。
        """
        goal_lower = goal.lower()
        length = goal_length or len(goal)

        # 优先级 1: 自定义关键词（优先级最高）
        for tier in [COMPLEX, MEDIUM, SIMPLE]:
            if tier in self._custom_keywords:
                for kw in self._custom_keywords[tier]:
                    if kw in goal_lower:
                        return tier

        # 优先级 2: 内置关键词匹配（从高到低）
        for tier in [COMPLEX, MEDIUM, SIMPLE]:
            for kw in self.TIER_KEYWORDS[tier]:
                if kw in goal_lower:
                    return tier

        # 优先级 3: 上下文规模辅助判断
        if context_size > 8000:
            return MEDIUM
        if context_size > 20000:
            return COMPLEX

        # 优先级 4: 目标长度回退
        if length > 500:
            return MEDIUM
        if length > 2000:
            return COMPLEX

        # 默认：简单
        return SIMPLE

    def analyze_detailed(self, goal: str) -> dict[str, Any]:
        """详细的复杂度分析，返回结构化结果。

        Args:
            goal: 任务目标文本。

        Returns:
            包含详细分析信息的字典。
        """
        goal_lower = goal.lower()
        level = self.analyze(goal)

        matched_keywords: list[dict[str, Any]] = []
        for tier in [COMPLEX, MEDIUM, SIMPLE]:
            for kw in self.TIER_KEYWORDS[tier]:
                if kw in goal_lower:
                    matched_keywords.append({
                        "keyword": kw,
                        "tier": tier,
                        "label": COMPLEXITY_LABELS[tier],
                    })

        return {
            "complexity": level,
            "label": COMPLEXITY_LABELS[level],
            "matched_keywords": matched_keywords,
            "keyword_count": len(matched_keywords),
            "goal_length": len(goal),
        }

    def register_custom_keywords(self, tier: int, keywords: set[str]) -> None:
        """注册自定义复杂度关键词。

        Args:
            tier: 目标层级（SIMPLE/MEDIUM/COMPLEX）。
            keywords: 关键词集合。
        """
        if tier not in (SIMPLE, MEDIUM, COMPLEX):
            raise ValueError(f"tier 必须是 {SIMPLE}/{MEDIUM}/{COMPLEX}")
        if tier not in self._custom_keywords:
            self._custom_keywords[tier] = set()
        self._custom_keywords[tier].update(keywords)

    def estimate_tokens(self, instruction: str, context: dict[str, Any]) -> int:
        """估算任务所需 token 数。

        Args:
            instruction: 指令文本。
            context: 上下文字典。

        Returns:
            估算的 token 数。
        """
        total = len(instruction.split())
        for value in context.values():
            if isinstance(value, str):
                total += len(value.split())
            elif isinstance(value, (list, dict)):
                total += len(str(value).split())
        return int(total * 1.3)  # 估算系数


# ── 模型匹配器 ──────────────────────────────────────────────────────────────


class ModelMatcher:
    """任务-模型动态匹配器。

    根据子任务复杂度在模型层级间动态切换。支持：
        - 按复杂度匹配最适模型
        - 模型回退链（主模型失败时自动回退）
        - 可配置的模型层级
        - 使用统计追踪

    Args:
        models: 可选的模型层级配置字典。
                格式: {tier_int: [ModelProfile, ...]}
                若不提供，使用默认三层配置。
    """

    # 默认回退链：每个模型的备选链
    DEFAULT_FALLBACK_CHAINS: dict[str, list[str]] = {
        "mlx-local": ["deepseek-chat", "claude-sonnet"],
        "deepseek-chat": ["claude-sonnet", "mlx-local"],
        "claude-sonnet": ["deepseek-chat", "mlx-local"],
        "gpt-4o-mini": ["gpt-4o", "claude-sonnet"],
        "gpt-4o": ["claude-sonnet", "deepseek-chat"],
    }

    def __init__(
        self,
        models: Optional[dict[int, list[ModelProfile]]] = None,
    ) -> None:
        self._analyzer = TaskComplexityAnalyzer()
        self._models: dict[int, list[ModelProfile]] = (
            models or self._default_models()
        )
        # 按 priority 排序
        for tier in self._models:
            self._models[tier].sort(key=lambda m: (m.priority, m.cost_per_1k_input))
        # 使用统计
        self._usage_log: list[dict[str, Any]] = []

    def match(self, goal: str, context: Optional[dict[str, Any]] = None) -> ModelProfile:
        """根据任务目标和上下文匹配最适合的模型。

        Args:
            goal: 任务目标描述。
            context: 上下文字典（可选），用于上下文规模辅助判断。

        Returns:
            匹配到的模型档案。
        """
        context_size = len(str(context)) if context else 0
        complexity = self._analyzer.analyze(goal, context_size=context_size)

        # 大上下文强制升级
        if context_size > 8000 and complexity == SIMPLE:
            complexity = MEDIUM
        if context_size > 20000 and complexity == MEDIUM:
            complexity = COMPLEX

        candidates = self._models.get(complexity, self._models[MEDIUM])
        model = candidates[0] if candidates else self._get_default_model()

        self._log_usage(model, goal, complexity, context_size)
        return model

    def match_with_context(
        self,
        goal: str,
        instruction: str = "",
        context: Optional[dict[str, Any]] = None,
    ) -> ModelProfile:
        """更完整的模型匹配，考虑指令和上下文规模。

        Args:
            goal: 任务目标。
            instruction: 指令文本（可选）。
            context: 上下文字典（可选）。

        Returns:
            匹配到的模型档案。
        """
        context_size = len(str(context)) if context else 0

        # 如果有 instruction，将其内容也纳入复杂度分析
        combined_goal = goal
        if instruction:
            combined_goal = f"{goal} {instruction[:200]}"

            # 如果 instruction 很长，提升复杂度
            if len(instruction) > 2000:
                context_size += len(instruction)

        return self.match(combined_goal, context or {})

    def get_fallback_chain(self, model_name: str) -> list[str]:
        """获取指定模型的回退链。

        回退链是当主模型调用失败时依次尝试的备选模型名列表。

        Args:
            model_name: 主模型名称。

        Returns:
            按优先级排列的回退链模型名列表。
        """
        chain = self.DEFAULT_FALLBACK_CHAINS.get(model_name, [])
        # 补充：如果某个回退模型不在可用模型中，跳过
        known_names = self._all_model_names()
        return [m for m in chain if m in known_names]

    def match_with_fallback(
        self,
        goal: str,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """匹配模型并构建回退方案。

        Returns:
            {
                "primary": ModelProfile,     # 主选模型
                "complexity": int,           # 复杂度等级
                "fallback_chain": [str],     # 回退模型名列表
                "context_size": int,         # 上下文大小
            }
        """
        model = self.match(goal, context)
        fallback_chain = self.get_fallback_chain(model.name)

        return {
            "primary": model,
            "complexity": model.tier,
            "complexity_label": COMPLEXITY_LABELS.get(model.tier, "未知"),
            "fallback_chain": fallback_chain,
            "context_size": len(str(context)) if context else 0,
        }

    def get_usage_summary(self) -> dict[str, Any]:
        """返回使用统计摘要。

        Returns:
            {
                "total_calls": int,
                "models": {model_name: {"count": int, "complexities": [int]}},
            }
        """
        summary: dict[str, dict[str, Any]] = {}
        for entry in self._usage_log:
            m = entry["model"]
            if m not in summary:
                summary[m] = {"count": 0, "complexities": set()}
            summary[m]["count"] += 1
            summary[m]["complexities"].add(entry["complexity"])

        return {
            "total_calls": len(self._usage_log),
            "models": {
                m: {
                    "count": info["count"],
                    "complexities": sorted(info["complexities"]),
                }
                for m, info in summary.items()
            },
        }

    def estimate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """估算单次调用的成本（美元）。

        Args:
            model_name: 模型名称。
            input_tokens: 输入 token 数。
            output_tokens: 输出 token 数。

        Returns:
            估算成本（美元）。
        """
        profile = self._find_model(model_name)
        if profile is None:
            return 0.0
        input_cost = (input_tokens / 1000) * profile.cost_per_1k_input
        output_cost = (output_tokens / 1000) * profile.cost_per_1k_output
        return round(input_cost + output_cost, 6)

    # ── 模型管理 ────────────────────────────────────────────────────────

    def register_model(self, tier: int, profile: ModelProfile) -> None:
        """注册一个新的模型到指定层级。

        Args:
            tier: 模型层级（SIMPLE/MEDIUM/COMPLEX）。
            profile: 模型档案。
        """
        if tier not in self._models:
            self._models[tier] = []
        self._models[tier].append(profile)
        # 按优先级和成本排序
        self._models[tier].sort(key=lambda m: (m.priority, m.cost_per_1k_input))

    def unregister_model(self, model_name: str) -> bool:
        """注销一个模型。

        Args:
            model_name: 要注销的模型名称。

        Returns:
            是否成功注销。
        """
        for tier in list(self._models.keys()):
            before = len(self._models[tier])
            self._models[tier] = [m for m in self._models[tier] if m.name != model_name]
            if len(self._models[tier]) < before:
                return True
        return False

    def get_model(self, model_name: str) -> Optional[ModelProfile]:
        """通过名称查找模型档案。"""
        return self._find_model(model_name)

    def list_models_by_tier(self, tier: int) -> list[ModelProfile]:
        """列出指定层级的所有模型。"""
        return list(self._models.get(tier, []))

    def list_all_models(self) -> list[ModelProfile]:
        """列出所有已注册的模型。"""
        result: list[ModelProfile] = []
        for models in self._models.values():
            result.extend(models)
        return result

    def set_default_models(self, models: dict[int, list[ModelProfile]]) -> None:
        """替换整个模型配置。"""
        self._models = models
        for tier in self._models:
            self._models[tier].sort(key=lambda m: (m.priority, m.cost_per_1k_input))

    # ── 内部方法 ────────────────────────────────────────────────────────

    def _default_models(self) -> dict[int, list[ModelProfile]]:
        """创建默认三层模型配置。"""
        return {
            SIMPLE: [
                ModelProfile.lightweight("mlx-local"),
            ],
            MEDIUM: [
                ModelProfile.medium("deepseek-chat"),
            ],
            COMPLEX: [
                ModelProfile.deep_reasoning("claude-sonnet"),
            ],
        }

    def _get_default_model(self) -> ModelProfile:
        """获取默认模型（MEDIUM 层第一个）。"""
        medium = self._models.get(MEDIUM)
        if medium:
            return medium[0]
        # 兜底：返回第一个可用模型
        for models in self._models.values():
            if models:
                return models[0]
        return ModelProfile.medium("fallback-default")

    def _find_model(self, model_name: str) -> Optional[ModelProfile]:
        """按名称查找模型。"""
        for models in self._models.values():
            for m in models:
                if m.name == model_name:
                    return m
        return None

    def _all_model_names(self) -> set[str]:
        """获取所有已注册模型名称集合。"""
        names: set[str] = set()
        for models in self._models.values():
            for m in models:
                names.add(m.name)
        return names

    def _log_usage(
        self,
        model: ModelProfile,
        goal: str,
        complexity: int,
        context_size: int,
    ) -> None:
        """记录一次模型使用。"""
        self._usage_log.append({
            "model": model.name,
            "tier": model.tier,
            "complexity": complexity,
            "context_size": context_size,
            "goal_preview": goal[:60],
        })
