"""dynamic_agent_factory.py — 动态子智能体工厂 (Dynamic Sub-Agent Factory)

A Orchestra 核心能力：接收输入 → 现场分析任务 → 动态拼装四元组 → 生成子智能体。
子智能体携带专属 recipe 和 tools 独立执行，不预设固定角色。

流程：
    1. analyze_task(goal) → 分析任务需要的四元组配置
    2. spawn(analysis) → 现场装配子智能体
    3. 缓存常用 recipe 避免重复创建

Usage:
    factory = DynamicFactory(instruction_templates={...}, tool_map={...})
    analysis = factory.analyze_task("分析用户行为数据并生成报告")
    spec = factory.spawn(analysis)
    # spec.recipe, spec.tools 可用于实例化子智能体

纯标准库 + dataclasses + typing。
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# ── 子智能体规格 ────────────────────────────────────────────────────────────


@dataclass
class SubAgentSpec:
    """子智能体规格 — 描述一个动态生成的子智能体实例。

    Attributes:
        agent_id: 全局唯一智能体ID。
        goal: 子智能体要完成的任务目标。
        recipe: 四元组配置字典（含 instruction/context_spec/tools/model_spec）。
        name: 智能体名称（自动生成）。
        status: 状态（created/running/completed/failed）。
        created_at: 创建时间戳。
        parent_agent_id: 父智能体ID（溯源用）。
    """

    agent_id: str
    goal: str
    recipe: dict[str, Any]
    name: str = ""
    status: str = "created"
    created_at: float = 0.0
    parent_agent_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.agent_id:
            self.agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        if not self.name:
            self.name = f"subagent_{self.goal[:20]}"
        if not self.created_at:
            self.created_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "goal": self.goal,
            "recipe": dict(self.recipe),
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at,
            "parent_agent_id": self.parent_agent_id,
        }

    @property
    def instruction(self) -> str:
        """便捷访问配方中的 instruction。"""
        return self.recipe.get("instruction", "")

    @property
    def tools(self) -> list[str]:
        """便捷访问配方中的 tools。"""
        return self.recipe.get("tools", [])

    @property
    def model_spec(self) -> dict[str, Any]:
        """便捷访问配方中的 model_spec。"""
        return self.recipe.get("model_spec", {"model": "default"})

    @property
    def context_spec(self) -> dict[str, Any]:
        """便捷访问配方中的 context_spec。"""
        return self.recipe.get("context_spec", {})


# ── 任务分析器 ──────────────────────────────────────────────────────────────


class TaskAnalyzer:
    """任务分析器 — 分析任务目标，提取关键特征。

    分析维度：
        - task_type: 任务类型（分析/代码/写作/搜索/设计/默认）
        - complexity: 复杂度评估（1-5）
        - keywords: 提取的关键词
        - suggested_tools: 建议的工具
        - suggested_model_tier: 建议的模型层级
    """

    # 任务类型 → 关键词映射
    TASK_PATTERNS: dict[str, set[str]] = {
        "分析": {
            "分析", "评估", "诊断", "审查", "review", "analyze",
            "总结", "摘要", "对比", "比较", "summarize",
            "分类", "归类", "classify", "categorize",
            "提取", "抽离", "extract", "parse",
        },
        "代码": {
            "代码", "编程", "开发", "实现", "implement",
            "重构", "优化", "refactor", "optimize",
            "调试", "debug", "修复", "fix", "bug",
            "测试", "test", "单元测试", "unittest",
            "部署", "deploy", "build",
        },
        "写作": {
            "写作", "撰写", "起草", "draft", "write",
            "报告", "report", "文档", "documentation",
            "文案", "copywriting", "内容", "content",
            "翻译", "translate", "本地化",
        },
        "搜索": {
            "搜索", "查找", "查询", "search", "find",
            "检索", "召回", "retrieve", "lookup",
            "调研", "研究", "research", "investigate",
        },
        "设计": {
            "设计", "架构", "方案", "design", "architecture",
            "规划", "计划", "plan", "strategy",
            "建模", "modeling", "原型", "prototype",
        },
    }

    def analyze(self, goal: str) -> dict[str, Any]:
        """分析任务目标。

        Args:
            goal: 任务目标文本。

        Returns:
            分析结果字典，包含 task_type、complexity、keywords、suggested_tools、suggested_model_tier。
        """
        goal_lower = goal.lower()

        # 1. 识别任务类型
        task_type = self._detect_task_type(goal_lower)

        # 2. 提取关键词
        keywords = self._extract_keywords(goal_lower)

        # 3. 评估复杂度
        complexity = self._evaluate_complexity(goal, keywords)

        # 4. 建议工具
        suggested_tools = self._suggest_tools(task_type, keywords)

        # 5. 建议模型层级
        suggested_model_tier = self._suggest_model_tier(complexity)

        return {
            "task_type": task_type,
            "complexity": complexity,
            "complexity_label": self._complexity_label(complexity),
            "keywords": keywords,
            "suggested_tools": suggested_tools,
            "suggested_model_tier": suggested_model_tier,
            "estimated_subtasks": self._estimate_subtasks(goal_lower, keywords),
        }

    def _detect_task_type(self, goal_lower: str) -> str:
        """基于关键词检测任务类型。"""
        scores: dict[str, int] = {}
        for task_type, patterns in self.TASK_PATTERNS.items():
            score = sum(1 for p in patterns if p in goal_lower)
            if score > 0:
                scores[task_type] = score

        if not scores:
            return "默认"

        return max(scores, key=scores.get)

    def _extract_keywords(self, goal_lower: str) -> list[str]:
        """提取有意义的单/双字词作为关键词。"""
        import re

        # 提取双字以上词组
        words = re.findall(r"[\u4e00-\u9fff]{2,5}", goal_lower)
        # 过滤无意义词
        stop_words = {
            "一个", "这个", "那个", "什么", "怎么", "如何",
            "可以", "需要", "进行", "使用", "通过", "并且",
        }
        return [w for w in words if w not in stop_words and len(w) >= 2][:10]

    def _evaluate_complexity(self, goal: str, keywords: list[str]) -> int:
        """评估任务复杂度（1-5）。

        评估因素：
            - 关键词数量
            - 目标长度
            - 包含复杂词汇
        """
        goal_lower = goal.lower()
        score = 1  # 基础分

        # 长度因素
        length = len(goal)
        if length > 200:
            score += 1
        if length > 500:
            score += 1

        # 关键词多样性
        if len(keywords) >= 5:
            score += 1
        if len(keywords) >= 8:
            score += 1

        # 复杂词汇
        complex_indicators = {
            "推理", "战略", "架构", "创新", "设计模式",
            "分布式", "并发", "机器学习", "深度学习",
            "优化算法", "系统设计", "架构设计",
        }
        for ci in complex_indicators:
            if ci in goal_lower:
                score += 1
                break

        return min(score, 5)

    @staticmethod
    def _complexity_label(complexity: int) -> str:
        """将复杂度数值转为标签。"""
        if complexity <= 2:
            return "简单"
        if complexity <= 3:
            return "中等"
        return "复杂"

    def _suggest_tools(self, task_type: str, keywords: list[str]) -> list[str]:
        """根据任务类型和关键词建议工具。"""
        tool_map: dict[str, list[str]] = {
            "分析": ["data-analyzer", "statistics", "visualizer"],
            "代码": ["shell", "file-reader", "code-analyzer", "debugger"],
            "写作": ["text-editor", "markdown-formatter", "spell-checker"],
            "搜索": ["web-search", "knowledge-base", "document-retriever"],
            "设计": ["diagram-tool", "markdown-formatter", "code-analyzer"],
            "默认": ["shell", "file-reader"],
        }

        tools = list(tool_map.get(task_type, tool_map["默认"]))

        # 额外关键词匹配
        keyword_tool_map = {
            "数据": "data-analyzer",
            "搜索": "web-search",
            "代码": "code-analyzer",
            "报告": "markdown-formatter",
            "图": "visualizer",
            "性能": "profiler",
        }
        for kw, tool in keyword_tool_map.items():
            if kw in " ".join(keywords) and tool not in tools:
                tools.append(tool)

        return tools

    @staticmethod
    def _suggest_model_tier(complexity: int) -> int:
        """根据复杂度建议模型层级。"""
        if complexity <= 2:
            return 1  # 轻量
        if complexity <= 3:
            return 2  # 中等
        return 3  # 深度推理

    @staticmethod
    def _estimate_subtasks(goal_lower: str, keywords: list[str]) -> int:
        """估算可能的子任务数量。"""
        count = 1
        separators = ["且", "并且", "同时", "以及", "、", "，", "。"]
        for sep in separators:
            count += goal_lower.count(sep)
        # 限制范围
        return max(1, min(count, 10))


# ── 指令模板解析器 ──────────────────────────────────────────────────────────


class InstructionResolver:
    """指令模板解析器 — 根据任务类型选择/构建指令。"""

    def __init__(
        self,
        templates: Optional[dict[str, str]] = None,
    ) -> None:
        """初始化指令解析器。

        Args:
            templates: 任务类型到指令模板的映射。
                       若不提供，使用默认模板。
        """
        self._templates = templates or self._default_templates()

    def resolve(self, task_type: str, goal: str) -> str:
        """根据任务类型和目标解析指令。

        Args:
            task_type: 任务类型（分析/代码/写作/搜索/设计/默认）。
            goal: 任务目标文本。

        Returns:
            构建好的指令字符串。
        """
        template = self._templates.get(task_type) or self._templates["默认"]
        return template.format(goal=goal)

    def register_template(self, task_type: str, template: str) -> None:
        """注册新的指令模板。"""
        self._templates[task_type] = template

    @staticmethod
    def _default_templates() -> dict[str, str]:
        return {
            "分析": (
                "你是一名数据分析专家。请对以下目标进行全面分析：\n\n"
                "目标：{goal}\n\n"
                "要求：\n"
                "1. 识别核心模式和趋势\n"
                "2. 提供结构化分析结果\n"
                "3. 给出明确结论和建议"
            ),
            "代码": (
                "你是一名资深软件工程师。请完成以下编程任务：\n\n"
                "任务：{goal}\n\n"
                "要求：\n"
                "1. 编写高质量、可维护的代码\n"
                "2. 包含必要的错误处理\n"
                "3. 提供使用说明"
            ),
            "写作": (
                "你是一名专业作家。请完成以下写作任务：\n\n"
                "任务：{goal}\n\n"
                "要求：\n"
                "1. 语言简洁准确\n"
                "2. 结构清晰逻辑严谨\n"
                "3. 符合目标受众需求"
            ),
            "搜索": (
                "你是一名信息检索专家。请完成以下搜索任务：\n\n"
                "任务：{goal}\n\n"
                "要求：\n"
                "1. 从多个角度搜集信息\n"
                "2. 筛选高相关性结果\n"
                "3. 整理为结构化报告"
            ),
            "设计": (
                "你是一名系统架构师。请完成以下设计任务：\n\n"
                "任务：{goal}\n\n"
                "要求：\n"
                "1. 给出完整的方案设计\n"
                "2. 分析权衡取舍\n"
                "3. 提供可落地实施路径"
            ),
            "默认": (
                "你是一名通用AI助手。请完成以下任务：\n\n"
                "任务：{goal}\n\n"
                "请提供高质量的结构化输出。"
            ),
        }


# ── 动态工厂 ────────────────────────────────────────────────────────────────


class DynamicFactory:
    """动态子智能体工厂。

    按需生成子智能体实例，不预设固定角色。核心能力：
        1. analyze_task(goal) → 分析任务需要的四元组配置
        2. spawn(analysis) → 现场装配子智能体
        3. 缓存常用 recipe，避免重复创建

    Args:
        instruction_templates: 任务类型到指令模板的映射。
        tool_map: 任务类型到工具列表的映射。
        context_provider: 可选的上下文提供函数（接收 goal，返回上下文字典）。
        model_router: 可选的模型路由函数（接收 goal，返回模型名）。
        cache_enabled: 是否启用 recipe 缓存（默认 True）。
    """

    def __init__(
        self,
        instruction_templates: Optional[dict[str, str]] = None,
        tool_map: Optional[dict[str, list[str]]] = None,
        context_provider: Optional[Callable[[str], dict[str, Any]]] = None,
        model_router: Optional[Callable[[str], str]] = None,
        cache_enabled: bool = True,
    ) -> None:
        self._task_analyzer = TaskAnalyzer()
        self._instruction_resolver = InstructionResolver(instruction_templates)
        self._tool_map = tool_map or {}
        self._context_provider = context_provider or (lambda goal: {})
        self._model_router = model_router or (lambda goal: "default")
        self._cache_enabled = cache_enabled
        self._recipe_cache: dict[str, dict[str, Any]] = {}
        self._agents: dict[str, SubAgentSpec] = {}

    def analyze_task(self, goal: str) -> dict[str, Any]:
        """分析任务目标，返回四元组配置分析结果。

        Args:
            goal: 任务目标文本。

        Returns:
            分析结果字典，包含：
                - task_type: 任务类型
                - complexity: 复杂度数值
                - complexity_label: 复杂度标签
                - keywords: 关键词列表
                - suggested_tools: 建议工具列表
                - suggested_model_tier: 建议模型层级
                - instruction: 构建好的指令
                - context: 上下文数据
                - model: 模型名
        """
        analysis = self._task_analyzer.analyze(goal)

        # 构建指令
        instruction = self._instruction_resolver.resolve(
            analysis["task_type"], goal
        )

        # 获取上下文
        context = self._context_provider(goal)

        # 获取模型
        model = self._model_router(goal)

        # 合并到分析结果
        analysis["instruction"] = instruction
        analysis["context"] = context
        analysis["model"] = model

        return analysis

    def spawn(self, analysis: dict[str, Any]) -> SubAgentSpec:
        """现场装配子智能体规格。

        根据任务分析结果，动态拼装四元组并生成 SubAgentSpec。

        Args:
            analysis: analyze_task() 返回的分析结果。

        Returns:
            生成的子智能体规格。
        """
        goal = analysis.get("goal", "")
        task_type = analysis.get("task_type", "默认")
        tools = analysis.get("suggested_tools", [])
        # 优先使用 analysis 中的 instruction，否则重新构建
        instruction = analysis.get("instruction", "")
        if not instruction:
            instruction = self._instruction_resolver.resolve(task_type, goal)
        context = analysis.get("context", {})
        model = analysis.get("model", "default")

        # 构建四元组
        recipe = {
            "instruction": instruction,
            "context_spec": context,
            "tools": tools,
            "model_spec": {"model": model, "tier": analysis.get("suggested_model_tier", 1)},
        }

        spec = SubAgentSpec(
            agent_id=f"agent_{uuid.uuid4().hex[:12]}",
            goal=goal,
            recipe=recipe,
            name=f"subagent_{task_type}_{goal[:12]}",
        )

        self._agents[spec.agent_id] = spec
        return spec

    def spawn_from_goal(self, goal: str) -> SubAgentSpec:
        """一键接口：分析目标 → 生成子智能体。

        Args:
            goal: 任务目标。

        Returns:
            生成的子智能体规格。
        """
        analysis = self.analyze_task(goal)
        analysis["goal"] = goal
        return self.spawn(analysis)

    def get_cached_recipe(self, task_type: str) -> Optional[dict[str, Any]]:
        """获取缓存的 recipe。"""
        return self._recipe_cache.get(task_type)

    def cache_recipe(self, task_type: str, recipe: dict[str, Any]) -> None:
        """缓存一个 recipe。"""
        if self._cache_enabled:
            self._recipe_cache[task_type] = recipe

    def get_agent(self, agent_id: str) -> Optional[SubAgentSpec]:
        """通过 agent_id 获取已创建的子智能体规格。"""
        return self._agents.get(agent_id)

    def get_children(self, parent_agent_id: str) -> list[SubAgentSpec]:
        """获取指定父智能体的所有子智能体。"""
        return [
            a for a in self._agents.values()
            if a.parent_agent_id == parent_agent_id
        ]

    def list_agents(self) -> list[SubAgentSpec]:
        """列出所有已创建的子智能体。"""
        return list(self._agents.values())

    def clear_agents(self) -> None:
        """清空所有已创建的子智能体记录。"""
        self._agents.clear()
