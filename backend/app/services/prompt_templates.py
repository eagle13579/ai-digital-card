"""F12 Prompt分治模板库 — 模板注册表 + 渲染引擎 + 版本管理。

职责单一模板（F12 架构）:
  1. input_parser        输入解析 — 将原始输入转为结构化数据
  2. info_extractor      信息提取 — 从文本中抽取关键信息
  3. analysis_reasoning  分析推理 — 基于信息进行逻辑推理
  4. formatter           格式化 — 将结果格式化为目标结构
  5. quality_control     质量控制 — 校验输出质量与一致性

架构模式:
  - TemplateRegistry: 全局单例注册表，管理模板的 CRUD 和版本
  - TemplateRenderer: 变量插值渲染引擎
  - VersionManager:   语义版本管理（v1 → v2 升级/降级）
"""

from __future__ import annotations

import json
import logging
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

logger = logging.getLogger(__name__)

# ── 默认 F12 分治模板（内置，DB 无记录时的回退） ─────────────────


# ---- 1. 输入解析 ----
INPUT_PARSER_V1 = {
    "id": "input_parser/v1",
    "name": "输入解析器 v1",
    "category": "input_parser",
    "version": "v1",
    "description": "将原始用户输入解析为结构化字段（意图、实体、上下文）",
    "system_prompt": """你是一个智能输入解析器。你的职责是：
1. 识别用户的意图（intent）
2. 提取关键实体（entities）
3. 捕获上下文信息（context）

请将以下用户输入解析为结构化 JSON 输出。""",
    "user_prompt_template": "用户输入: {input}\n\n历史上下文: {context}\n请输出 JSON 格式的解析结果。",
    "parameters_schema": {
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "用户原始输入"},
            "context": {"type": "string", "description": "历史上下文（可选）"},
        },
        "required": ["input"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "intent": {"type": "string"},
            "entities": {"type": "array", "items": {"type": "object"}},
            "context": {"type": "object"},
        },
    },
    "tags": ["f12", "分治", "输入解析", "parser"],
}

# ---- 2. 信息提取 ----
INFO_EXTRACTOR_V1 = {
    "id": "info_extractor/v1",
    "name": "信息提取器 v1",
    "category": "info_extractor",
    "version": "v1",
    "description": "从文本中提取指定的关键信息字段",
    "system_prompt": """你是一个精准的信息提取器。从给定文本中提取所有符合要求的信息片段。
只提取文本中明确存在的信息，不要编造。""",
    "user_prompt_template": "文本内容: {text}\n\n需要提取的字段: {fields}\n\n请输出 JSON 格式的提取结果。",
    "parameters_schema": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "待提取的文本"},
            "fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "需要提取的字段列表",
            },
        },
        "required": ["text", "fields"],
    },
    "output_schema": {
        "type": "object",
        "additionalProperties": {"type": "string"},
        "description": "字段名到提取值的映射",
    },
    "tags": ["f12", "分治", "信息提取", "extractor"],
}

# ---- 3. 分析推理 ----
ANALYSIS_REASONING_V1 = {
    "id": "analysis_reasoning/v1",
    "name": "分析推理引擎 v1",
    "category": "analysis_reasoning",
    "version": "v1",
    "description": "基于结构化信息进行逻辑推理和分析",
    "system_prompt": """你是一个分析推理引擎。基于提供的事实信息，进行逻辑推理和分析。
请给出你的推理过程（reasoning）和结论（conclusion）。""",
    "user_prompt_template": "事实信息: {facts}\n\n分析目标: {goal}\n\n请输出 JSON，包含 reasoning（推理过程）和 conclusion（结论）。",
    "parameters_schema": {
        "type": "object",
        "properties": {
            "facts": {
                "type": "object",
                "description": "用于分析的事实信息（结构化）",
            },
            "goal": {"type": "string", "description": "分析目标描述"},
        },
        "required": ["facts", "goal"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "reasoning": {"type": "string"},
            "conclusion": {"type": "string"},
            "confidence": {"type": "number"},
        },
    },
    "tags": ["f12", "分治", "分析推理", "reasoning"],
}

# ---- 4. 格式化 ----
FORMATTER_V1 = {
    "id": "formatter/v1",
    "name": "格式化器 v1",
    "category": "formatter",
    "version": "v1",
    "description": "将中间结果格式化为目标结构（JSON/文本/卡片等）",
    "system_prompt": """你是一个数据格式化器。将输入数据按照指定的格式要求进行格式化输出。
确保输出符合目标结构的规范。""",
    "user_prompt_template": "输入数据: {data}\n\n目标格式: {target_format}\n输出规范: {schema}\n\n请输出格式化后的结果。",
    "parameters_schema": {
        "type": "object",
        "properties": {
            "data": {"description": "待格式化的中间数据"},
            "target_format": {
                "type": "string",
                "enum": ["json", "text", "markdown", "html", "card"],
                "description": "目标输出格式",
            },
            "schema": {
                "type": "object",
                "description": "输出结构规范（可选）",
            },
        },
        "required": ["data", "target_format"],
    },
    "output_schema": {
        "type": "object",
        "description": "格式化后的结果",
    },
    "tags": ["f12", "分治", "格式化", "formatter"],
}

# ---- 5. 质量控制 ----
QUALITY_CONTROL_V1 = {
    "id": "quality_control/v1",
    "name": "质量控制 v1",
    "category": "quality_control",
    "version": "v1",
    "description": "校验输出质量：完整性、一致性、格式合规性",
    "system_prompt": """你是一个质量控制审查员。审查输出结果的质量：

审核维度:
1. 完整性 — 是否缺少必要字段
2. 一致性 — 内部是否矛盾
3. 格式合规性 — 是否符合输出 schema 规范
4. 合理性 — 内容是否合理可行

请给出审核报告。""",
    "user_prompt_template": "原始输入: {original_input}\n\n输出结果: {output}\n\n预期 schema: {expected_schema}\n\n请输出 JSON 格式的审核报告。",
    "parameters_schema": {
        "type": "object",
        "properties": {
            "original_input": {"description": "原始的输入内容"},
            "output": {"description": "待审核的输出结果"},
            "expected_schema": {
                "type": "object",
                "description": "期望的输出 schema（可选）",
            },
        },
        "required": ["original_input", "output"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "passed": {"type": "boolean"},
            "score": {"type": "number"},
            "issues": {"type": "array", "items": {"type": "object"}},
            "suggestions": {"type": "array", "items": {"type": "string"}},
        },
    },
    "tags": ["f12", "分治", "质量控制", "quality"],
}

# ── 内置模板注册表 ────────────────────────────────────────────

_BUILTIN_TEMPLATES: dict[str, dict] = {
    "input_parser/v1": INPUT_PARSER_V1,
    "info_extractor/v1": INFO_EXTRACTOR_V1,
    "analysis_reasoning/v1": ANALYSIS_REASONING_V1,
    "formatter/v1": FORMATTER_V1,
    "quality_control/v1": QUALITY_CONTROL_V1,
}


# ======================================================================
# VersionManager — 语义版本管理
# ======================================================================


class VersionManager:
    """语义版本管理 — 模板版本比较与升级/降级。"""

    @staticmethod
    def parse_version(version: str) -> tuple[int, ...]:
        """将 'v1', 'v2', 'v1.2' 等版本号解析为可比较的元组。"""
        v = version.lstrip("v").strip()
        parts = v.split(".")
        return tuple(int(p) if p.isdigit() else 0 for p in parts)

    @staticmethod
    def compare(v1: str, v2: str) -> int:
        """比较两个版本：返回 -1 (v1<v2), 0 (v1==v2), 1 (v1>v2)"""
        a = VersionManager.parse_version(v1)
        b = VersionManager.parse_version(v2)
        if a < b:
            return -1
        if a > b:
            return 1
        return 0

    @staticmethod
    def next_version(current: str, bump: str = "minor") -> str:
        """生成下一个版本号。
        bump: 'major' → v2, 'minor' → v1.1
        """
        v = current.lstrip("v").strip()
        parts = v.split(".")
        if bump == "major":
            major = (int(parts[0]) if parts[0].isdigit() else 1) + 1
            return f"v{major}"
        # minor bump
        major = int(parts[0]) if parts[0].isdigit() else 1
        minor = (int(parts[1]) + 1) if len(parts) > 1 and parts[1].isdigit() else 1
        return f"v{major}.{minor}"


# ======================================================================
# TemplateRenderer — 变量插值渲染引擎
# ======================================================================


class TemplateRenderError(Exception):
    """模板渲染异常。"""


class TemplateRenderer:
    """模板渲染引擎 — 支持 {placeholder} 变量插值与安全检查。"""

    _PLACEHOLDER_PATTERN = re.compile(r"\{(\w+)\}")

    @classmethod
    def render_system(cls, template: str, params: dict[str, Any]) -> str:
        """渲染 system prompt 模板。"""
        return cls._render(template, params)

    @classmethod
    def render_user(cls, template: str, params: dict[str, Any]) -> str:
        """渲染 user prompt 模板。"""
        return cls._render(template, params)

    @classmethod
    def _render(cls, template: str, params: dict[str, Any]) -> str:
        """通用渲染方法，支持复杂类型自动 JSON 序列化。"""
        if not template:
            return ""

        def _replacer(match: re.Match) -> str:
            key = match.group(1)
            if key not in params:
                # 保留未提供的占位符
                return match.group(0)
            val = params[key]
            if isinstance(val, (dict, list)):
                return json.dumps(val, ensure_ascii=False, default=str)
            return str(val)

        try:
            result = cls._PLACEHOLDER_PATTERN.sub(_replacer, template)
            return result
        except Exception as exc:
            raise TemplateRenderError(f"模板渲染失败: {exc}") from exc

    @classmethod
    def render_full(
        cls,
        template_def: dict,
        params: dict[str, Any],
    ) -> dict[str, str]:
        """完整渲染 system + user prompt 并返回。"""
        system = cls.render_system(template_def.get("system_prompt", ""), params)
        user = cls.render_user(template_def.get("user_prompt_template", ""), params)
        return {"system": system, "user": user}

    @classmethod
    def validate_parameters(
        cls, template_def: dict, params: dict[str, Any]
    ) -> list[str]:
        """校验入参是否符合 parameters_schema 定义。返回缺失/不匹配字段列表。"""
        schema = template_def.get("parameters_schema")
        if not schema:
            return []

        errors: list[str] = []
        required = schema.get("required", [])
        for field in required:
            if field not in params or params[field] is None:
                errors.append(f"缺少必填字段: {field}")

        props = schema.get("properties", {})
        for key, val in params.items():
            prop = props.get(key)
            if prop and prop.get("type") == "array" and not isinstance(val, list):
                errors.append(f"字段 '{key}' 应为 array 类型")
            if prop and prop.get("type") == "object" and not isinstance(val, dict):
                errors.append(f"字段 '{key}' 应为 object 类型")
            if prop and prop.get("type") == "string" and not isinstance(val, str):
                errors.append(f"字段 '{key}' 应为 string 类型")

        return errors


# ======================================================================
# TemplateRegistry — 全局模板注册表（单例模式）
# ======================================================================


class TemplateRegistry:
    """F12 分治模板注册表 — 全局单例，管理模板 CRUD 与版本。

    使用方式:
        registry = TemplateRegistry.get_instance()
        tmpl = registry.get("input_parser/v1")
        rendered = registry.render("input_parser/v1", {"input": "你好"})
    """

    _instance: Optional["TemplateRegistry"] = None

    def __init__(self) -> None:
        self._templates: dict[str, dict] = {}
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "TemplateRegistry":
        """获取全局单例。"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── 初始化 ──────────────────────────────────────────────────

    def load_builtins(self) -> None:
        """加载内置 F12 分治模板到内存注册表。"""
        for tid, tmpl in _BUILTIN_TEMPLATES.items():
            self._templates[tid] = deepcopy(tmpl)
        self._initialized = True
        logger.info("F12 分治模板库加载完成: %d 个内置模板", len(_BUILTIN_TEMPLATES))

    async def load_from_db(self, db: AsyncSession) -> int:
        """从数据库加载模板（覆盖同 id 的内置模板）。"""
        from app.models.prompt import PromptTemplate

        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.is_active == True)
        )
        rows = result.scalars().all()
        for row in rows:
            self._templates[row.id] = {
                "id": row.id,
                "name": row.name,
                "category": row.category.value
                if hasattr(row.category, "value")
                else row.category,
                "version": row.version,
                "description": row.description,
                "system_prompt": row.system_prompt,
                "user_prompt_template": row.user_prompt_template,
                "parameters_schema": row.parameters_schema,
                "output_schema": row.output_schema,
                "tags": row.tags or [],
            }
        self._initialized = True
        logger.info(
            "从数据库加载了 %d 个模板（含内置模板覆盖）", len(rows)
        )
        return len(rows)

    # ── CRUD ────────────────────────────────────────────────────

    def get(self, template_id: str) -> Optional[dict]:
        """按 ID 获取模板定义。"""
        return deepcopy(self._templates.get(template_id))

    def list(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        active_only: bool = True,
    ) -> list[dict]:
        """列出模板，支持按类别和标签过滤。"""
        results = []
        for tmpl in self._templates.values():
            if active_only and not tmpl.get("is_active", True):
                continue
            if category and tmpl.get("category") != category:
                continue
            if tag and tag not in tmpl.get("tags", []):
                continue
            results.append(deepcopy(tmpl))
        return results

    def register(self, template_def: dict) -> str:
        """注册/更新模板。返回模板 ID。"""
        tid = template_def.get("id")
        if not tid:
            raise ValueError("模板定义必须包含 'id' 字段")
        self._templates[tid] = deepcopy(template_def)
        logger.info("模板注册/更新: %s (v%s)", tid, template_def.get("version", "?"))
        return tid

    def delete(self, template_id: str) -> bool:
        """删除模板（仅从内存，DB 删除通过 API）。"""
        if template_id in self._templates:
            del self._templates[template_id]
            logger.info("模板已删除: %s", template_id)
            return True
        return False

    def exists(self, template_id: str) -> bool:
        """检查模板是否存在。"""
        return template_id in self._templates

    # ── 版本管理 ────────────────────────────────────────────────

    def get_version(self, template_id: str) -> Optional[str]:
        """获取指定模板的版本号。"""
        tmpl = self._templates.get(template_id)
        return tmpl.get("version") if tmpl else None

    def list_versions(self, base_id: str) -> list[dict]:
        """列出同一基础模板的所有版本。
        base_id 格式: 'input_parser'（无 /v1 后缀）
        """
        results = []
        prefix = f"{base_id}/"
        for tid, tmpl in self._templates.items():
            if tid.startswith(prefix):
                results.append(
                    {
                        "id": tid,
                        "version": tmpl.get("version"),
                        "name": tmpl.get("name"),
                    }
                )
        results.sort(key=lambda x: VersionManager.parse_version(x["version"]))
        return results

    def promote_version(self, template_id: str) -> Optional[str]:
        """将当前版本提升为下一个版本。返回新模板 ID。"""
        tmpl = self.get(template_id)
        if not tmpl:
            return None

        base_id = template_id.rsplit("/", 1)[0]
        current_ver = tmpl.get("version", "v1")
        next_ver = VersionManager.next_version(current_ver)
        new_id = f"{base_id}/{next_ver}"

        tmpl["id"] = new_id
        tmpl["version"] = next_ver
        self.register(tmpl)
        return new_id

    # ── 渲染 ────────────────────────────────────────────────────

    def render(
        self,
        template_id: str,
        params: dict[str, Any],
        validate: bool = True,
    ) -> dict[str, str]:
        """获取并渲染指定模板。"""
        tmpl = self.get(template_id)
        if not tmpl:
            raise KeyError(f"模板不存在: {template_id}")

        if validate:
            errors = TemplateRenderer.validate_parameters(tmpl, params)
            if errors:
                raise ValueError(f"参数校验失败: {'; '.join(errors)}")

        return TemplateRenderer.render_full(tmpl, params)

    def render_chain(
        self,
        chain: list[dict],
        initial_params: dict[str, Any],
    ) -> list[dict[str, str]]:
        """链式渲染 — 按顺序执行多个模板，前一个输出作为后一个输入。
        chain: [{"template_id": "input_parser/v1", "output_key": "parsed"},
                {"template_id": "analysis_reasoning/v1", "output_key": "analysis"}]
        initial_params: 初始参数
        """
        results = []
        params = dict(initial_params)

        for step in chain:
            tid = step["template_id"]
            output_key = step.get("output_key", tid)
            try:
                rendered = self.render(tid, params, validate=True)
                results.append({"template_id": tid, "rendered": rendered})
                params[output_key] = rendered
            except (KeyError, ValueError) as exc:
                logger.warning("链式渲染步骤失败 [%s]: %s", tid, exc)
                results.append({"template_id": tid, "error": str(exc)})
                break

        return results

    # ── 辅助 ────────────────────────────────────────────────────

    def get_categories(self) -> list[str]:
        """获取所有模板类别。"""
        categories: set[str] = set()
        for tmpl in self._templates.values():
            cat = tmpl.get("category")
            if cat:
                categories.add(cat)
        return sorted(categories)

    def count_by_category(self) -> dict[str, int]:
        """统计各类别模板数量。"""
        counts: dict[str, int] = {}
        for tmpl in self._templates.values():
            cat = tmpl.get("category", "unknown")
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    @property
    def initialized(self) -> bool:
        return self._initialized


# ── 全局便利函数 ────────────────────────────────────────────────

_registry: Optional[TemplateRegistry] = None


def get_template_registry() -> TemplateRegistry:
    """获取/初始化全局模板注册表。"""
    global _registry
    if _registry is None:
        _registry = TemplateRegistry.get_instance()
        _registry.load_builtins()
    return _registry
