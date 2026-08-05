r"""
工具调用解析服务 — 用于AI数智名片对话功能

注入来源: ds2api_toolkit/tool_call_pipeline.py
原架构: Go internal/toolcall/toolcalls_parse.go 翻译

核心能力:
  - 支持三种工具调用格式: DSML / XML / JSON
  - DSML 归一化 → XML 解析 → filter + schema 校验
  - OpenAI 格式互转 (format_openai / format_openai_stream)
  - 损坏 JSON 修复
  - 高层 ToolCallService 面向名片场景

独立导入:
    from services.tool_call_service import ToolCallService, ToolCallPipeline
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ==============================================================================
# 数据类型
# ==============================================================================

@dataclass
class ParsedToolCall:
    """解析后的工具调用"""
    name: str = ""
    input: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCallParseResult:
    """工具调用解析结果"""
    calls: list[ParsedToolCall] = field(default_factory=list)
    saw_tool_call_syntax: bool = False
    rejected_by_policy: bool = False
    rejected_tool_names: list[str] = field(default_factory=list)


# ==============================================================================
# 工具调用解析管道
# ==============================================================================

class ToolCallPipeline:
    """
    工具调用解析管道

    支持三种格式:
    1. DSML (DeepSeek Markup Language): <|DSML|tool_calls><|DSML|invoke name="...">
    2. Canonical XML: <tool_calls><invoke name="..."><parameter name="...">
    3. JSON (loose array): [{"name": "...", "input": {...}}]

    处理流程:
    DSML/XML/JSON 输入 → 格式检测 → DSML归一化 → XML解析 → filter → 结果
    """

    DSML_TOOL_CALLS_RE = re.compile(
        r'<\|DSML\|tool_calls\s*>'
    )
    DSML_INVOKE_RE = re.compile(
        r'<\|DSML\|invoke\s+name\s*=\s*["\']([^"\']+)["\']\s*>'
    )
    DSML_PARAMETER_RE = re.compile(
        r'<\|DSML\|parameter\s+name\s*=\s*["\']([^"\']+)["\']\s*>(.*?)</?\|DSML\|parameter\s*>',
        re.DOTALL
    )
    XML_TOOL_CALLS_RE = re.compile(
        r'<(?:tool_calls|tools|tool_call)\s*>'
    )
    XML_INVOKE_RE = re.compile(
        r'<(?:invoke|function|tool_use)\s+name\s*=\s*["\']([^"\']+)["\']\s*>'
    )
    XML_PARAMETER_RE = re.compile(
        r'<parameter\s+name\s*=\s*["\']([^"\']+)["\']\s*>(.*?)</parameter\s*>',
        re.DOTALL
    )

    def __init__(self, available_tools: list[str] | None = None):
        self.available_tools = set(available_tools or [])

    def parse(self, text: str) -> list[ParsedToolCall]:
        """解析工具调用, 返回列表"""
        return self.parse_detailed(text).calls

    def parse_detailed(self, text: str) -> ToolCallParseResult:
        """解析工具调用, 返回详细结果"""
        trimmed = text.strip()
        if not trimmed:
            return ToolCallParseResult()

        result = ToolCallParseResult()
        result.saw_tool_call_syntax = self._looks_like_tool_call(trimmed)

        trimmed = self._strip_fenced_code_blocks(trimmed)
        trimmed = trimmed.strip()
        if not trimmed:
            return result

        # 1. 检测并归一化 DSML
        normalized, is_dsml = self._normalize_dsml(trimmed)

        # 2. 用 XML 解析器解析
        if is_dsml or self._looks_like_xml(normalized):
            result.saw_tool_call_syntax = True
            calls = self._parse_xml_tool_calls(normalized)

            if not calls and "<![cdata[" in normalized.lower():
                recovered = self._sanitize_cdata(normalized)
                if recovered != normalized:
                    calls = self._parse_xml_tool_calls(recovered)

            if calls:
                result.calls = calls
        else:
            # 3. 尝试 JSON 解析
            calls = self._parse_json_tool_calls(trimmed)
            if calls:
                result.saw_tool_call_syntax = True
                result.calls = calls

        return result

    def parse_assistant_detailed(self, text: str, thinking: str = "",
                                  available_tools: list[str] | None = None
                                  ) -> ToolCallParseResult:
        """
        解析 assistant 响应中的工具调用

        先查主文本, 如果为空再查 thinking 段
        """
        if available_tools is not None:
            self.available_tools = set(available_tools)

        text_parsed = self.parse_detailed(text)
        if text_parsed.calls:
            return text_parsed

        if text.strip():
            return text_parsed

        # 从 thinking 段解析
        thinking_parsed = self.parse_detailed(thinking)
        if thinking_parsed.calls:
            return thinking_parsed

        return text_parsed

    def format_openai(self, calls: list[ParsedToolCall]) -> list[dict]:
        """格式化为 OpenAI tool_calls 格式"""
        return [
            {
                "id": f"call_{i}",
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.input, ensure_ascii=False),
                }
            }
            for i, tc in enumerate(calls)
        ]

    def format_openai_stream(self, calls: list[ParsedToolCall]) -> list[dict]:
        """格式化为 OpenAI 流式 delta.tool_calls 格式"""
        result = []
        for i, tc in enumerate(calls):
            args_str = json.dumps(tc.input, ensure_ascii=False)
            result.append({
                "index": i,
                "id": f"call_{i}",
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": args_str,
                }
            })
        return result

    # ===== 内部方法 =====

    def _looks_like_tool_call(self, text: str) -> bool:
        """检测文本是否包含工具调用语法"""
        return bool(
            self.DSML_TOOL_CALLS_RE.search(text) or
            self.XML_TOOL_CALLS_RE.search(text) or
            "tool_calls" in text.lower()
        )

    def _looks_like_xml(self, text: str) -> bool:
        """检测文本是否包含 XML 结构"""
        return bool(re.search(r'<[a-zA-Z_]+\s+[a-zA-Z_]+=', text)) or "<" in text

    def _strip_fenced_code_blocks(self, text: str) -> str:
        """去掉 fenced code blocks"""
        return re.sub(
            r'```(?:json|xml|tool_call|dsml)?\s*\n(.*?)\n```',
            r'\1',
            text,
            flags=re.DOTALL
        )

    def _normalize_dsml(self, text: str) -> tuple[str, bool]:
        """将 DSML 标记归一化为标准 XML"""
        if "<|DSML|" not in text:
            return text, False

        result = text
        result = re.sub(r'<\|DSML\|tool_calls\s*>', '<tool_calls>', result)
        result = re.sub(r'</?\|DSML\|tool_calls\s*>', '', result)

        result = re.sub(
            r'<\|DSML\|invoke\s+name\s*=\s*["\']([^"\']+)["\']\s*>',
            r'<invoke name="\1">',
            result
        )
        result = re.sub(r'</?\|DSML\|invoke\s*>', '</invoke>', result)

        result = re.sub(
            r'<\|DSML\|parameter\s+name\s*=\s*["\']([^"\']+)["\']\s*>(.*?)</?\|DSML\|parameter\s*>',
            r'<parameter name="\1">\2</parameter>',
            result,
            flags=re.DOTALL
        )

        return result, True

    def _sanitize_cdata(self, text: str) -> str:
        """清理松散 CDATA 标记"""
        return re.sub(
            r'<!?\s*\[CDATA\[(.*?)\]\]\s*>',
            r'\1',
            text,
            flags=re.DOTALL
        )

    def _parse_xml_tool_calls(self, text: str) -> list[ParsedToolCall]:
        """XML 格式工具调用解析"""
        calls = []
        invoke_pattern = re.compile(
            r'<(?:invoke|function|tool_use)\s+name\s*=\s*["\']([^"\']+)["\']\s*>(.*?)</(?:invoke|function|tool_use)\s*>',
            re.DOTALL
        )

        for match in invoke_pattern.finditer(text):
            name = match.group(1)
            body = match.group(2).strip()

            if not name:
                continue

            params = {}
            param_pattern = re.compile(
                r'<parameter\s+name\s*=\s*["\']([^"\']+)["\']\s*>(.*?)</parameter\s*>',
                re.DOTALL
            )
            for pm in param_pattern.finditer(body):
                pname = pm.group(1)
                pvalue = pm.group(2).strip()
                try:
                    params[pname] = json.loads(pvalue)
                except (json.JSONDecodeError, ValueError):
                    params[pname] = pvalue

            if not params and body:
                try:
                    parsed = json.loads(body)
                    if isinstance(parsed, dict):
                        params = parsed
                except (json.JSONDecodeError, ValueError):
                    params = {"value": body}

            calls.append(ParsedToolCall(name=name, input=params))

        return calls

    def _parse_json_tool_calls(self, text: str) -> list[ParsedToolCall]:
        """JSON 格式工具调用解析 (支持松散数组)"""
        try:
            data = json.loads(text)
            if isinstance(data, list):
                calls = []
                for item in data:
                    if isinstance(item, dict) and "name" in item:
                        calls.append(ParsedToolCall(
                            name=str(item["name"]),
                            input=item.get("input", {}) or item.get("arguments", {}),
                        ))
                return calls
            elif isinstance(data, dict):
                name = data.get("name", "")
                if name:
                    return [ParsedToolCall(
                        name=str(name),
                        input=data.get("input", {}) or data.get("arguments", {}),
                    )]
        except json.JSONDecodeError:
            pass

        return self._parse_loose_json_array(text)

    def _parse_loose_json_array(self, text: str) -> list[ParsedToolCall]:
        """解析松散 JSON 数组"""
        parts = re.split(r'(?=\{)"name"', text)
        calls = []
        for part in parts:
            if not part.strip():
                continue
            if not part.startswith("{"):
                part = "{" + part
            try:
                obj = json.loads(part)
                if isinstance(obj, dict) and "name" in obj:
                    calls.append(ParsedToolCall(
                        name=str(obj["name"]),
                        input=obj.get("input", {}) or obj.get("arguments", {}),
                    ))
            except json.JSONDecodeError:
                pass
        return calls

    def repair_json(self, text: str) -> str:
        """
        修复损坏的 JSON

        处理:
        - 末尾多余的逗号
        - 未闭合的引号
        - 缺少结束括号
        """
        result = text.strip()
        result = re.sub(r',\s*([}\]])', r'\1', result)
        result = re.sub(r"(\w+)(?=\s*:)", r'"\1"', result)
        return result


# ==============================================================================
# 高层服务接口 — 面向名片对话场景
# ==============================================================================

# 名片场景的可用工具列表 (供 AI 调用)
DEFAULT_BUSINESS_CARD_TOOLS = [
    "search_knowledge",      # 搜索知识库
    "query_contacts",        # 查询联系人
    "get_brochure",          # 获取电子名片
    "schedule_meeting",      # 安排会议
    "send_email",            # 发送邮件
    "get_team_info",         # 获取团队信息
    "recommend_products",    # 推荐产品/服务
    "check_inventory",       # 检查库存
    "create_order",          # 创建订单
]


class ToolCallService:
    """
    工具调用服务 — AI数智名片 对话功能专用

    提供:
      - parse: 从 AI 对话文本中解析工具调用
      - parse_with_thinking: 支持思考段的工具调用解析
      - format_response: 格式化工具调用为 OpenAI 兼容格式
      - validate_tools: 校验工具调用是否在白名单内
    """

    def __init__(self, available_tools: Optional[list[str]] = None):
        tools = available_tools or DEFAULT_BUSINESS_CARD_TOOLS
        self._pipeline = ToolCallPipeline(available_tools=tools)

    @property
    def pipeline(self) -> ToolCallPipeline:
        return self._pipeline

    @property
    def available_tools(self) -> set[str]:
        return self._pipeline.available_tools

    def parse(self, text: str) -> list[ParsedToolCall]:
        """从文本解析工具调用"""
        return self._pipeline.parse(text)

    def parse_detailed(self, text: str) -> ToolCallParseResult:
        """从文本解析工具调用, 返回详细结果"""
        return self._pipeline.parse_detailed(text)

    def parse_with_thinking(self, text: str, thinking: str = "") -> ToolCallParseResult:
        """
        从 assistant 响应中解析工具调用 (含思考段备用)

        流程:
        1. 先解析主文本
        2. 如主文本无工具调用且非空, 返回空结果
        3. 如主文本为空, 尝试从 thinking 段解析
        """
        return self._pipeline.parse_assistant_detailed(
            text, thinking=thinking,
            available_tools=list(self._pipeline.available_tools),
        )

    def format_openai(self, calls: list[ParsedToolCall]) -> list[dict]:
        """格式化为 OpenAI tool_calls 格式"""
        return self._pipeline.format_openai(calls)

    def format_openai_stream(self, calls: list[ParsedToolCall]) -> list[dict]:
        """格式化为 OpenAI 流式 delta.tool_calls 格式"""
        return self._pipeline.format_openai_stream(calls)

    def validate_tools(self, calls: list[ParsedToolCall]) -> ToolCallParseResult:
        """
        校验工具调用是否在白名单内

        Returns:
            ToolCallParseResult with rejected_tool_names if any
        """
        result = ToolCallParseResult(calls=calls, saw_tool_call_syntax=True)
        rejected = []
        for tc in calls:
            if self._pipeline.available_tools and tc.name not in self._pipeline.available_tools:
                rejected.append(tc.name)
        if rejected:
            result.rejected_by_policy = True
            result.rejected_tool_names = rejected
            result.calls = [tc for tc in calls if tc.name not in rejected]
        return result

    def set_available_tools(self, tools: list[str]):
        """更新可用工具列表"""
        self._pipeline.available_tools = set(tools)

    def add_tool(self, tool_name: str):
        """添加一个可用工具"""
        self._pipeline.available_tools.add(tool_name)

    def remove_tool(self, tool_name: str):
        """移除一个可用工具"""
        self._pipeline.available_tools.discard(tool_name)


# ===== 全局单例 (名片场景默认工具集) =====
default_tool_call_service = ToolCallService()


# ===== 简易测试 =====
if __name__ == "__main__":
    pipe = ToolCallPipeline()

    # DSML 格式
    dsml = '<|DSML|tool_calls><|DSML|invoke name="search_knowledge"><|DSML|parameter name="query">hello</parameter>'
    result = pipe.parse(dsml)
    print(f"DSML: {result}")

    # XML 格式
    xml = '<tool_calls><invoke name="search_knowledge"><parameter name="query">world</parameter></invoke></tool_calls>'
    result = pipe.parse(xml)
    print(f"XML: {result}")

    # JSON 格式
    json_input = '[{"name": "search_knowledge", "input": {"query": "test"}}]'
    result = pipe.parse(json_input)
    print(f"JSON: {result}")

    print(f"\nToolCallService ready: {default_tool_call_service is not None}")
    print(f"Available tools: {default_tool_call_service.available_tools}")
