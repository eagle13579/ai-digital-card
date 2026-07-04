"""
MCP Protocol Adapter — 使DesignQA Agent兼容Model Context Protocol
让Claude等MCP客户端可以直接调用我们的设计审核工具

MCP规范: https://modelcontextprotocol.io
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── MCP工具定义 ──────────────────────────────────────────────

MCP_TOOLS = [
    {
        "name": "critique_design",
        "description": "设计评审 — 对UI/UX设计进行10条尼尔森启发式评分(0-40分)",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "目标名称（组件/页面）"},
                "context": {"type": "string", "description": "设计上下文描述"},
            },
            "required": ["target"],
        },
    },
    {
        "name": "audit_design",
        "description": "综合审核 — 并行执行无障碍+性能+响应式三维度检查",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "审核目标"},
                "context": {"type": "string", "description": "上下文"},
            },
            "required": ["target"],
        },
    },
    {
        "name": "detect_antipatterns",
        "description": "反模式检测 — 37条AI Slop+质量规则检测",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "检测目标"},
                "context": {"type": "string", "description": "上下文"},
            },
            "required": ["target"],
        },
    },
    {
        "name": "list_commands",
        "description": "列出所有23条设计审核命令，支持按类别过滤",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["build", "evaluate", "refine", "enhance", "fix", ""],
                    "description": "命令类别过滤（留空返回全部）",
                }
            },
        },
    },
    {
        "name": "get_knowledge",
        "description": "获取设计知识 — 按model_id查询盖娅心智模型",
        "input_schema": {
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "模型ID (如 FD-M01)"},
            },
            "required": ["model_id"],
        },
    },
]

MCP_PROMPTS = [
    {
        "name": "design_review",
        "description": "开始一个完整的设计审核流程",
        "arguments": [
            {"name": "target", "description": "审核目标", "required": True},
            {"name": "context", "description": "设计上下文", "required": False},
        ],
    },
    {
        "name": "fix_design_issues",
        "description": "分析并修复设计问题",
        "arguments": [
            {"name": "target", "description": "问题目标", "required": True},
            {"name": "issues", "description": "已知问题列表", "required": False},
        ],
    },
]


class MCPAdapter:
    """MCP协议适配器 — 将DesignQA Agent工具暴露为MCP兼容接口"""

    def __init__(self, design_qa_agent=None):
        self.agent = design_qa_agent
        logger.info("MCPAdapter initialized with %d tools", len(MCP_TOOLS))

    def get_tool_definitions(self) -> list[dict]:
        """返回MCP工具定义列表"""
        return MCP_TOOLS

    def get_prompt_definitions(self) -> list[dict]:
        """返回MCP提示定义列表"""
        return MCP_PROMPTS

    async def handle_tool_call(self, tool_name: str, arguments: dict) -> dict:
        """处理MCP工具调用请求"""
        if not self.agent:
            return {"error": "DesignQA Agent not initialized"}

        try:
            if tool_name == "critique_design":
                result = await self.agent.critique_design(arguments)
            elif tool_name == "audit_design":
                # 并行执行三个审核
                import asyncio
                a11y = await self.agent.audit_accessibility(arguments)
                perf = await self.agent.audit_performance(arguments)
                resp = await self.agent.audit_responsive(arguments)
                result = {"accessibility": a11y, "performance": perf, "responsive": resp}
            elif tool_name == "detect_antipatterns":
                result = await self.agent.detect_antipatterns(arguments)
            elif tool_name == "list_commands":
                result = await self.agent.list_commands(arguments.get("category", ""))
            elif tool_name == "get_knowledge":
                # 从knowledge_models表查询
                from app.database import AsyncSessionLocal
                from app.models.gaia import KnowledgeModel
                from sqlalchemy import select
                async with AsyncSessionLocal() as db:
                    stmt = select(KnowledgeModel).where(
                        KnowledgeModel.model_id == arguments["model_id"]
                    )
                    result = await db.execute(stmt)
                    model = result.scalars().first()
                    if model:
                        result = {"model_id": model.model_id, "name": model.name, "content": model.content[:500]}
                    else:
                        result = {"error": f"Model {arguments['model_id']} not found"}
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            return {"status": "success", "result": result}

        except Exception as e:
            logger.error("MCP tool call failed: %s", e)
            return {"status": "error", "error": str(e)}

    def get_mcp_protocol_json(self) -> dict:
        """返回完整的MCP协议JSON（用于注册到MCP Host）"""
        return {
            "protocolVersion": "2025-03-26",
            "serverInfo": {"name": "design-qa-agent", "version": "1.0.0"},
            "tools": MCP_TOOLS,
            "prompts": MCP_PROMPTS,
        }


# ── MCP Server 入口 ─────────────────────────────────────────

def create_mcp_server():
    """
    创建MCP Server实例 (适用于 stdio 传输)
    
    用法:
        from app.ai.mcp_adapter import create_mcp_server
        server = create_mcp_server()
        server.run()  # 通过stdio
    """
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import (
            CallToolRequest, ListToolsRequest, ListPromptsRequest,
            CallToolResult, ListToolsResult, ListPromptsResult,
        )
    except ImportError:
        logger.warning("MCP SDK not installed. Install with: pip install mcp")
        return None

    adapter = MCPAdapter()
    server = Server("design-qa-agent")

    @server.list_tools()
    async def handle_list_tools() -> ListToolsResult:
        return ListToolsResult(tools=adapter.get_tool_definitions())

    @server.call_tool()
    async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
        result = await adapter.handle_tool_call(
            request.params.name, request.params.arguments or {}
        )
        return CallToolResult(
            content=[{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
        )

    return server


# ── 快捷调用（用于Cron/后台） ─────────────────────────────

async def run_mcp_tool(tool_name: str, args: dict = None) -> dict:
    """无需MCP Server直接调用工具"""
    from app.agents.design_qa_agent import DesignQAAgent
    from app.agents.base_agent import AgentConfig

    agent = DesignQAAgent(config=AgentConfig(agent_name="mcp_runner"))
    await agent.init()
    adapter = MCPAdapter(agent)
    result = await adapter.handle_tool_call(tool_name, args or {})
    await agent.stop()
    return result


if __name__ == "__main__":
    """测试MCP工具定义"""
    adapter = MCPAdapter()
    print(json.dumps(adapter.get_mcp_protocol_json(), ensure_ascii=False, indent=2))
