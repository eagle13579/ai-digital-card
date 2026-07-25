r"""
GBNF Service — JSON Schema → GBNF 语法约束注入服务

将 GBNF 语法约束注入到 LLM 调用层，约束 AI 输出格式。
依赖 baize_libs.gbnf_grammar 包（位于 D:\向海容的知识库\...\baize_libs\gbnf_grammar\）。

使用示例:
    gbnf = GbnfService()
    if gbnf.available():
        prompt = gbnf.enforce_schema(
            schema={
                "type": "object",
                "properties": {
                    "reply": {"type": "string"},
                    "type": {"type": "string", "enum": ["text", "card", "action"]},
                },
                "required": ["reply", "type"],
            },
            prompt="你是一个AI数智名片助手。请按格式回复。",
        )
"""

import sys
from pathlib import Path
from typing import Optional

# ── GBNF 语法约束包的路径 ────────────────────────────────
# 从 baize_libs 知识库路径加载
_GBNF_PACKAGE_DIR = Path(
    r"D:\向海容的知识库\wiki\wiki\记忆宫殿\L3兵器库\代码资产\baize_libs"
)
_GBNF_IMPORTED = False

if _GBNF_PACKAGE_DIR.exists():
    _pkg_str = str(_GBNF_PACKAGE_DIR)
    if _pkg_str not in sys.path:
        sys.path.insert(0, _pkg_str)
    try:
        from baize_libs.gbnf_grammar import json_schema_to_gbnf, GbnfCompiler

        _GBNF_IMPORTED = True
        _compiler = GbnfCompiler()
    except ImportError:
        _compiler = None  # type: ignore[assignment]
else:
    _compiler = None  # type: ignore[assignment]


class GbnfService:
    """GBNF 语法约束服务

    将 JSON Schema 编译为 GBNF 语法字符串，并注入到 system prompt 中，
    使 LLM 遵循指定的输出格式。
    """

    @staticmethod
    def enforce_schema(schema: dict, prompt: str) -> str:
        """将 JSON Schema 编译为 GBNF 语法并附加到 prompt 后。

        Args:
            schema: JSON Schema 字典。
            prompt: 原始的 system prompt 或 user prompt 文本。

        Returns:
            增强后的 prompt 文本（尾部追加 GBNF 语法约束说明）。
            若 schema 不支持或编译失败，返回原 prompt（安全降级）。
        """
        if not GbnfService.available():
            return prompt

        try:
            gbnf_str = json_schema_to_gbnf(schema)
            if not gbnf_str:
                return prompt

            # 将 GBNF 语法约束以可读格式附加到 prompt 末尾
            augmented = (
                f"{prompt}\n\n"
                f"【输出格式约束 (GBNF)】\n"
                f"你必须严格按照以下 GBNF 语法约束来生成输出：\n"
                f"```\n"
                f"{gbnf_str}\n"
                f"```\n"
                f"请确保输出内容完全符合上述语法规则。"
            )
            return augmented
        except Exception:
            return prompt

    @staticmethod
    def available() -> bool:
        """检查 GBNF 语法约束功能是否可用。

        Returns:
            True 若 baize_libs.gbnf_grammar 可正常导入且编译功能正常。
        """
        return _GBNF_IMPORTED and _compiler is not None

    @staticmethod
    def compile(schema: dict) -> Optional[str]:
        """直接将 JSON Schema 编译为 GBNF 语法字符串。

        Args:
            schema: JSON Schema 字典。

        Returns:
            GBNF 语法字符串；若编译失败返回 None。
        """
        if not GbnfService.available():
            return None
        return _compiler.compile(schema)
