"""dify_tool_service.py — AI数智名片 Dify 工具插件 + 应用编排服务

基于 baize_libs.dify_patterns 构建，为名片场景提供：
  1. 工具插件系统：工具注册/发现/执行
  2. 应用编排引擎：多Agent场景编排

架构：
  ToolProvider (提供者) → ToolPlugin (插件包装) → ToolPluginManager (管理器)
  SceneComposer (场景编排) + MultiAgentCoordinator (多Agent协调) → AppOrchestrator (编排入口)

使用方式：
    from app.services.dify_tool_service import dify_tool_manager, dify_orchestrator

    # 执行工具
    result = await dify_tool_manager.execute_tool(ToolExecuteRequest(tool_name="search_company", args={"keyword": "示例"}))

    # 运行场景
    result = await dify_orchestrator.run_scene("card_collection", {"url": "https://example.com"})
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import os
import sys
import time
import uuid
from typing import Any

logger = logging.getLogger(__name__)


# ======================================================================
# ── baize_libs 路径注入 ──────────────────────────────────────────────
# ======================================================================

_BAIZE_LIBS_PATHS = [
    os.path.abspath(
        r"D:\向海容的知识库\wiki\wiki\记忆宫殿\L3兵器库\代码资产\baize_libs"
    ),
]

for _p in _BAIZE_LIBS_PATHS:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

logger.info("baize_libs 路径已注入: %s", _BAIZE_LIBS_PATHS)


# ======================================================================
# ── 从 baize_libs.dify_patterns 导入 ─────────────────────────────────
# ======================================================================

try:
    from baize_libs.dify_patterns import (
        BaseToolProvider,
        BuiltinToolProvider,
        ToolPlugin,
        ToolPluginManager,
        ToolExecuteRequest,
        ToolExecuteResponse,
        ToolListEntry,
        BaseAppOrchestrator,
        AppScene,
        AgentConfig,
        OrchestrationPlan,
        OrchestrationResult,
        SceneComposer,
        MultiAgentCoordinator,
    )
    from baize_libs.dify_patterns.tool_plugin import ToolProviderType, ToolExecuteMode, create_default_tool_manager
    from baize_libs.dify_patterns.app_orchestrator import OrchestrationStatus, AgentRole

    _BAIZE_DIFY_AVAILABLE = True
    logger.info("baize_libs.dify_patterns 加载成功")
except ImportError as exc:
    logger.warning("baize_libs.dify_patterns 不可用, 使用内联实现: %s", exc)
    _BAIZE_DIFY_AVAILABLE = False
    # ── 内联Fallback定义 ────────────────────────────────────
    from dataclasses import dataclass, field
    from enum import Enum

    class ToolProviderType(str, Enum):
        BUILTIN = "builtin"
        CUSTOM = "custom"
        API = "api"
        PLUGIN = "plugin"

    class ToolExecuteMode(str, Enum):
        SYNC = "sync"
        ASYNC = "async"
        STREAM = "stream"

    @dataclass
    class ToolExecuteRequest:
        tool_name: str
        provider: str = "builtin"
        args: dict[str, Any] = field(default_factory=dict)
        mode: ToolExecuteMode = ToolExecuteMode.SYNC
        timeout: int = 60
        trace_id: str = ""
        user_id: str = ""

    @dataclass
    class ToolExecuteResponse:
        success: bool
        output: Any = None
        error: str | None = None
        duration_ms: int = 0
        tool_name: str = ""
        trace_id: str = ""
        metadata: dict[str, Any] = field(default_factory=dict)

        def to_dict(self) -> dict[str, Any]:
            return {
                "success": self.success,
                "output": self.output,
                "error": self.error,
                "duration_ms": self.duration_ms,
                "tool_name": self.tool_name,
                "trace_id": self.trace_id,
                "metadata": self.metadata,
            }

    @dataclass
    class ToolListEntry:
        name: str
        description: str
        provider: str
        category: str
        parameters: list[dict[str, Any]]
        enabled: bool = True
        version: str = "0.1.0"
        tags: list[str] = field(default_factory=list)
        metadata: dict[str, Any] = field(default_factory=dict)

        def to_dict(self) -> dict[str, Any]:
            return {
                "name": self.name,
                "description": self.description,
                "provider": self.provider,
                "category": self.category,
                "parameters": self.parameters,
                "enabled": self.enabled,
                "version": self.version,
                "tags": self.tags,
                "metadata": self.metadata,
            }

    class AppScene(str, Enum):
        CARD_COLLECTION = "card_collection"
        CUSTOMER_ANALYSIS = "customer_analysis"
        BUSINESS_MATCHING = "business_matching"
        CRM_SYNC = "crm_sync"
        DATA_EXPORT = "data_export"
        SOCIAL_OUTREACH = "social_outreach"
        INTELLIGENT_CHAT = "intelligent_chat"
        CUSTOM = "custom"

    class OrchestrationStatus(str, Enum):
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        PARTIAL = "partial"
        TIMEOUT = "timeout"

    class AgentRole(str, Enum):
        COORDINATOR = "coordinator"
        COLLECTOR = "collector"
        ANALYZER = "analyzer"
        EXECUTOR = "executor"
        VALIDATOR = "validator"
        RENDERER = "renderer"

    @dataclass
    class AgentConfig:
        agent_id: str
        name: str
        role: AgentRole = AgentRole.EXECUTOR
        description: str = ""
        tools: list[str] = field(default_factory=list)
        max_retries: int = 2
        timeout: int = 120
        depends_on: list[str] = field(default_factory=list)
        config: dict[str, Any] = field(default_factory=dict)

        def to_dict(self) -> dict[str, Any]:
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "role": self.role.value,
                "description": self.description,
                "tools": self.tools,
                "max_retries": self.max_retries,
                "timeout": self.timeout,
                "depends_on": self.depends_on,
                "config": self.config,
            }

    @dataclass
    class OrchestrationPlan:
        plan_id: str
        scene: AppScene
        agents: list[AgentConfig]
        execution_order: list[str]
        parallel_groups: list[list[str]]
        input_schema: dict[str, Any] = field(default_factory=dict)
        output_schema: dict[str, Any] = field(default_factory=dict)
        max_total_timeout: int = 300
        metadata: dict[str, Any] = field(default_factory=dict)

        def to_dict(self) -> dict[str, Any]:
            return {
                "plan_id": self.plan_id,
                "scene": self.scene.value,
                "agents": [a.to_dict() for a in self.agents],
                "execution_order": self.execution_order,
                "parallel_groups": self.parallel_groups,
                "input_schema": self.input_schema,
                "output_schema": self.output_schema,
                "max_total_timeout": self.max_total_timeout,
                "metadata": self.metadata,
            }

    @dataclass
    class AgentResult:
        agent_id: str
        success: bool
        output: Any = None
        error: str | None = None
        duration_ms: int = 0
        tool_calls: list[dict[str, Any]] = field(default_factory=list)
        retry_count: int = 0
        metadata: dict[str, Any] = field(default_factory=dict)

    @dataclass
    class OrchestrationResult:
        plan_id: str
        scene: AppScene
        status: OrchestrationStatus
        agent_results: dict[str, AgentResult] = field(default_factory=dict)
        final_output: Any = None
        error: str | None = None
        total_duration_ms: int = 0
        trace_id: str = ""

        def to_dict(self) -> dict[str, Any]:
            return {
                "plan_id": self.plan_id,
                "scene": self.scene.value,
                "status": self.status.value,
                "agent_results": {
                    aid: {
                        "agent_id": r.agent_id,
                        "success": r.success,
                        "output": r.output,
                        "error": r.error,
                        "duration_ms": r.duration_ms,
                        "tool_calls": r.tool_calls,
                        "retry_count": r.retry_count,
                    }
                    for aid, r in self.agent_results.items()
                },
                "final_output": self.final_output,
                "error": self.error,
                "total_duration_ms": self.total_duration_ms,
                "trace_id": self.trace_id,
            }


# ======================================================================
# ── DifyToolManager — 名片工具管理器 ─────────────────────────────────
# ======================================================================


class DifyToolManager:
    """AI数智名片 Dify 工具管理器

    功能:
      - 工具插件注册/注销/发现
      - 统一工具执行入口
      - 跨插件工具路由
      - 内置名片场景工具集

    单例: dify_tool_manager
    """

    def __init__(self) -> None:
        self._initialized = False
        self._manager: ToolPluginManager | None = None
        self._providers: dict[str, BaseToolProvider] = {}

    async def initialize(self) -> None:
        """初始化管理器并注册内置工具"""
        if self._initialized:
            return

        if _BAIZE_DIFY_AVAILABLE:
            self._manager = create_default_tool_manager()
        else:
            self._manager = ToolPluginManager()
            # 注册内置工具
            try:
                builtin = BuiltinToolProvider()
                self._manager.register_provider(builtin)
                self._providers[builtin.provider_name] = builtin
                logger.info("内置BuiltinToolProvider注册完成 (%d 工具)", len(builtin.get_tools()))
            except Exception as e:
                logger.warning("BuiltinToolProvider注册失败: %s", e)

        await self._manager.initialize()
        self._initialized = True
        logger.info("DifyToolManager 初始化完成")

    async def shutdown(self) -> None:
        """关闭管理器"""
        if self._manager:
            await self._manager.shutdown()
        self._initialized = False
        logger.info("DifyToolManager 已关闭")

    def register_provider(self, provider: BaseToolProvider) -> str:
        """注册自定义工具提供者"""
        if not self._manager:
            raise RuntimeError("DifyToolManager 未初始化")
        plugin_id = self._manager.register_provider(provider)
        self._providers[provider.provider_name] = provider
        return plugin_id

    def unregister_provider(self, provider_name: str) -> bool:
        """注销工具提供者"""
        if not self._manager:
            return False
        result = self._manager.unregister_provider(provider_name)
        self._providers.pop(provider_name, None)
        return result

    def list_providers(self) -> list[dict[str, Any]]:
        """列出所有提供者"""
        if not self._manager:
            return []
        return self._manager.list_providers()

    def list_tools(
        self,
        category: str | None = None,
        provider: str | None = None,
    ) -> list[dict[str, Any]]:
        """列出可用工具"""
        if not self._manager:
            return []
        return [t.to_dict() for t in self._manager.list_tools(category, provider)]

    def get_tool_categories(self) -> list[dict[str, Any]]:
        """获取工具分类信息"""
        if not self._manager:
            return []

        tools = self._manager.list_tools()
        categories: dict[str, dict[str, Any]] = {}

        for tool in tools:
            cat = tool.category
            if cat not in categories:
                categories[cat] = {
                    "category": cat,
                    "tool_count": 0,
                    "tools": [],
                }
            categories[cat]["tool_count"] += 1
            categories[cat]["tools"].append({
                "name": tool.name,
                "description": tool.description,
            })

        return list(categories.values())

    async def execute_tool(
        self,
        tool_name: str,
        args: dict[str, Any],
        provider: str = "builtin",
        timeout: int = 60,
        user_id: str = "",
    ) -> dict[str, Any]:
        """执行工具

        Args:
            tool_name: 工具名称
            args: 参数
            provider: 提供者名称
            timeout: 超时秒数
            user_id: 用户ID

        Returns:
            dict: 执行结果
        """
        if not self._manager:
            return ToolExecuteResponse(
                success=False,
                error="DifyToolManager 未初始化",
                tool_name=tool_name,
            ).to_dict()

        request = ToolExecuteRequest(
            tool_name=tool_name,
            provider=provider,
            args=args,
            timeout=timeout,
            user_id=user_id,
        )

        result = await self._manager.execute_tool(request)
        return result.to_dict()

    def health_check(self) -> dict[str, Any]:
        """健康检查"""
        if not self._manager:
            return {
                "service": "dify_tool_manager",
                "initialized": self._initialized,
                "healthy": False,
                "error": "管理器未初始化",
            }
        base = self._manager.health_check()
        base["service"] = "dify_tool_manager"
        return base


# ======================================================================
# ── DifyOrchestrator — 应用编排器 ────────────────────────────────────
# ======================================================================


class DifyOrchestrator(BaseAppOrchestrator if _BAIZE_DIFY_AVAILABLE else object):
    """AI数智名片 Dify 应用编排器

    在 BaseAppOrchestrator 基础上包装，自动注入真实 tool_executor。

    功能:
      - 7个预设名片场景编排
      - 多Agent并行/串行执行
      - 场景计划生成
      - 执行结果查询

    单例: dify_orchestrator
    """

    def __init__(self, tool_manager: DifyToolManager | None = None) -> None:
        self._tool_manager = tool_manager or dify_tool_manager

        if _BAIZE_DIFY_AVAILABLE:
            super().__init__(tool_executor=self._tool_executor)
        else:
            self._composer = None
            self._coordinator = None
            self._active_runs: dict[str, "OrchestrationResult"] = {}

        self._initialized = False

    async def _tool_executor(self, tool_name: str, args: dict[str, Any]) -> Any:
        """将工具调用转发给 DifyToolManager"""
        return await self._tool_manager.execute_tool(tool_name, args)

    async def initialize(self) -> None:
        """初始化编排器"""
        if self._initialized:
            return

        # 确保工具管理器已初始化
        if not self._tool_manager._initialized:
            await self._tool_manager.initialize()

        self._initialized = True
        logger.info("DifyOrchestrator 初始化完成")

    def list_scenes(self) -> list[dict[str, Any]]:
        """列出所有可用场景"""
        return self._composer.list_scenes()

    def get_plan(self, scene_name: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """获取场景编排计划"""
        try:
            scene = AppScene(scene_name)
        except ValueError:
            return None
        plan = self._composer.get_plan(scene, params)
        if plan is None:
            return None
        return plan.to_dict()

    async def run_scene(
        self,
        scene_name: str,
        inputs: dict[str, Any],
        trace_id: str = "",
    ) -> dict[str, Any]:
        """运行场景编排

        Args:
            scene_name: 场景名称 (如 "card_collection")
            inputs: 输入参数
            trace_id: 追踪ID

        Returns:
            dict: 编排结果
        """
        if not self._initialized:
            return OrchestrationResult(
                plan_id="",
                scene=AppScene.CUSTOM,
                status=OrchestrationStatus.FAILED,
                error="DifyOrchestrator 未初始化",
                trace_id=trace_id or f"err-{uuid.uuid4().hex[:8]}",
            ).to_dict()

        try:
            scene = AppScene(scene_name)
        except ValueError:
            return OrchestrationResult(
                plan_id="",
                scene=AppScene.CUSTOM,
                status=OrchestrationStatus.FAILED,
                error=f"未知场景: {scene_name}",
                trace_id=trace_id or f"err-{uuid.uuid4().hex[:8]}",
            ).to_dict()

        result = await super().run_scene(scene, inputs, trace_id) if _BAIZE_DIFY_AVAILABLE else await self._run_scene_fallback(scene, inputs, trace_id)

        if not trace_id:
            trace_id = result.trace_id if hasattr(result, 'trace_id') else f"orch-{uuid.uuid4().hex[:12]}"
        self._active_runs[result.plan_id] = result
        return result.to_dict()

    async def _run_scene_fallback(
        self,
        scene: AppScene,
        inputs: dict[str, Any],
        trace_id: str = "",
    ) -> OrchestrationResult:
        """内联的 run_scene 实现 (当 baize_libs 不可用时)"""
        if not trace_id:
            trace_id = f"orch-{uuid.uuid4().hex[:12]}"

        plan = self._composer.get_plan(scene, inputs)
        if plan is None:
            return OrchestrationResult(
                plan_id="",
                scene=scene,
                status=OrchestrationStatus.FAILED,
                error=f"场景 '{scene.value}' 未定义",
                trace_id=trace_id,
            )

        result = await self._coordinator.execute_plan(plan, inputs, trace_id)
        return result

    def get_run_result(self, plan_id: str) -> dict[str, Any] | None:
        """获取编排执行结果"""
        result = self._active_runs.get(plan_id)
        if result is None:
            return None
        return result.to_dict()

    def list_runs(self) -> list[dict[str, Any]]:
        """列出所有编排执行记录"""
        return [
            {
                "plan_id": r.plan_id,
                "scene": r.scene.value,
                "status": r.status.value,
                "total_duration_ms": r.total_duration_ms,
                "trace_id": r.trace_id,
            }
            for r in self._active_runs.values()
        ]

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        tm_health = self._tool_manager.health_check()
        return {
            "service": "dify_orchestrator",
            "initialized": self._initialized,
            "healthy": self._initialized,
            "scenes": len(self._composer.list_scenes()),
            "active_runs": len(self._active_runs),
            "tool_manager": tm_health,
        }


# ======================================================================
# ── 自定义工具提供者示例 ──────────────────────────────────────────────
# ======================================================================


class CustomSearchToolProvider(BaseToolProvider if _BAIZE_DIFY_AVAILABLE else object):
    """自定义搜索工具提供者 — 外部API集成示例"""

    provider_name: str = "custom_search"
    provider_version: str = "1.0.0"
    provider_description: str = "自定义搜索集成 — 对接外部企业数据API"
    provider_type: ToolProviderType = ToolProviderType.API

    def __init__(self, api_key: str = "") -> None:
        if _BAIZE_DIFY_AVAILABLE:
            super().__init__()
        self._api_key = api_key
        self._tool_handlers: dict[str, tuple] = {}
        self._register_tools()

    def _register_tools(self) -> None:
        """注册自定义工具"""
        from dataclasses import dataclass

        # 使用简单函数而非类方法 — 保持独立
        async def _search_external(req: ToolExecuteRequest) -> ToolExecuteResponse:
            keyword = req.args.get("keyword", "")
            if not keyword:
                return ToolExecuteResponse(success=False, error="keyword 不能为空", trace_id=req.trace_id)
            # 模拟外部API调用
            await asyncio.sleep(0.1)
            return ToolExecuteResponse(
                success=True,
                output={
                    "source": "external_api",
                    "keyword": keyword,
                    "results": [
                        {"name": f"{keyword}集团", "score": 0.95},
                        {"name": f"{keyword}股份", "score": 0.88},
                    ],
                },
                trace_id=req.trace_id,
                metadata={"api_key_configured": bool(self._api_key)},
            )

        self._tool_handlers["external_company_search"] = (
            _search_external,
            ToolListEntry(
                name="external_company_search",
                description="外部企业数据搜索 — 对接三方API的企业信息查询",
                provider=self.provider_name,
                category="card_search",
                parameters=[
                    {"name": "keyword", "type": "string", "required": True, "description": "企业关键词"},
                    {"name": "page", "type": "number", "required": False, "description": "页码"},
                ],
                enabled=bool(self._api_key),
                version=self.provider_version,
                tags=["外部API", "企业搜索"],
            ),
        )

    def get_tools(self) -> list:
        return [entry for _, entry in self._tool_handlers.values()]

    async def execute_tool(self, request) -> ToolExecuteResponse:
        handler_info = self._tool_handlers.get(request.tool_name)
        if handler_info is None:
            return ToolExecuteResponse(
                success=False,
                error=f"自定义工具 '{request.tool_name}' 不存在",
                trace_id=request.trace_id,
            )
        handler, _ = handler_info
        return await handler(request)

    def health_check(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "initialized": True,
            "healthy": bool(self._api_key),
            "tool_count": len(self._tool_handlers),
            "api_key_configured": bool(self._api_key),
        }


# ======================================================================
# ── 场景编排补充 — 特征模块组合 ─────────────────────────────────────
# ======================================================================


class SceneComposer:
    """场景编排器 — 组合多个工具/Agent形成完整特征模块

    名片场景特征模块:
      - 采集模块: 网站采集 → OCR识别 → 信息结构化
      - 分析模块: 画像分析 → 匹配分析 → 标签推荐
      - 匹配模块: 供需匹配 → 人脉推荐 → CRM录入
      - 导出模块: CSV/vCard/PDF多格式导出
    """

    def __init__(self, tool_executor):
        if _BAIZE_DIFY_AVAILABLE:
            self._composer = SceneComposer(tool_executor)
        else:
            self._tool_executor = tool_executor
            self._scene_plans: dict[AppScene, Any] = {}
            self._register_default_scenes()

    def _register_default_scenes(self) -> None:
        """注册默认场景 (与 baize_libs.dify_patterns 同步)"""
        # 这些场景在 app_orchestrator 中已有完整定义
        # 此处为独立运行时的兜底
        pass

    def list_scenes(self) -> list[dict[str, Any]]:
        if _BAIZE_DIFY_AVAILABLE:
            return self._composer.list_scenes()
        return [
            {"scene": "card_collection", "description": "名片信息采集: 网页→OCR→结构化数据"},
            {"scene": "customer_analysis", "description": "客户分析: 画像→匹配→标签推荐"},
            {"scene": "business_matching", "description": "商务匹配: 供需分析→人脉推荐→CRM录入"},
            {"scene": "crm_sync", "description": "CRM同步: 线索创建→更新→列表查询"},
            {"scene": "data_export", "description": "数据导出: CSV/vCard 格式导出"},
            {"scene": "social_outreach", "description": "社交触达: 企微链接→领英搜索→摘要生成"},
            {"scene": "intelligent_chat", "description": "智能对话: AI问答→工具推荐→摘要生成"},
        ]


# ======================================================================
# ── 全局单例 ─────────────────────────────────────────────────────────
# ======================================================================

# 全局 Dify 工具管理器
dify_tool_manager = DifyToolManager()

# 全局 Dify 应用编排器
try:
    dify_orchestrator = DifyOrchestrator(tool_manager=dify_tool_manager)
except Exception as e:
    dify_orchestrator = None
    import logging
    logger = logging.getLogger("dify_tool_service")
    logger.warning("DifyOrchestrator init failed: %s", e)

__all__ = [
    # 单例
    "dify_tool_manager",
    "dify_orchestrator",
    # 管理器/编排器
    "DifyToolManager",
    "DifyOrchestrator",
    # 自定义提供者
    "CustomSearchToolProvider",
    # 场景相关
    "SceneComposer",
    # 核心类型 (从 baize_libs 转发)
    "ToolExecuteRequest",
    "ToolExecuteResponse",
    "ToolListEntry",
    "AppScene",
    "OrchestrationResult",
    "OrchestrationPlan",
    "AgentConfig",
    "AgentRole",
]
