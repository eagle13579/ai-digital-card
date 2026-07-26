"""dify_tool_routes.py — AI数智名片 Dify 工具插件 + 应用编排 API

API 端点:
  POST   /api/dify/tool/execute    — 执行工具
  GET    /api/dify/tool/list       — 可用工具列表
  GET    /api/dify/tool/categories — 工具分类
  POST   /api/dify/app/run         — 应用编排运行
  GET    /api/dify/app/scenes      — 场景列表
  GET    /api/dify/app/plan        — 获取场景编排计划
  GET    /api/dify/app/result      — 查询编排结果
  GET    /api/dify/health          — 健康检查

使用方式:
  1. 先初始化:
     curl -X POST http://localhost:8201/api/dify/tool/execute \
       -H "Content-Type: application/json" \
       -d '{"tool_name": "search_company", "args": {"keyword": "示例科技"}}'

  2. 运行场景编排:
     curl -X POST http://localhost:8201/api/dify/app/run \
       -H "Content-Type: application/json" \
       -d '{"scene": "card_collection", "inputs": {"url": "https://example.com"}}'
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.dify_tool_service import (
    dify_tool_manager,
    dify_orchestrator,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dify", tags=["Dify工具插件+应用编排"])


# ======================================================================
# ── 请求/响应模型 ──────────────────────────────────────────────────
# ======================================================================


class ApiResponse(BaseModel):
    """统一API响应"""
    code: int = 0
    message: str = "success"
    data: dict | list | None = None


class ToolExecuteRequest(BaseModel):
    """工具执行请求"""
    tool_name: str = Field(..., description="工具名称 (如 search_company)")
    provider: str = Field(default="builtin", description="提供者名称")
    args: dict[str, Any] = Field(default_factory=dict, description="工具参数")
    timeout: int = Field(default=60, ge=1, le=300, description="超时秒数")
    user_id: str = Field(default="", description="用户ID (可选)")


class AppRunRequest(BaseModel):
    """应用编排运行请求"""
    scene: str = Field(..., description="场景名称 (如 card_collection, customer_analysis, business_matching)")
    inputs: dict[str, Any] = Field(default_factory=dict, description="场景输入参数")
    trace_id: str = Field(default="", description="追踪ID (可选, 自动生成)")


# ======================================================================
# ── 工具相关端点 ──────────────────────────────────────────────────
# ======================================================================


@router.post("/tool/execute", response_model=ApiResponse)
async def execute_tool(req: ToolExecuteRequest):
    """执行Dify工具插件

    执行指定的工具插件，支持内置和自定义工具。
    工具会自动通过插件管理器找到所属提供者。

    Examples:
        search_company: 搜索企业信息
        crm_create_lead: 创建CRM线索
        recommend_connections: 推荐人脉连接
        ai_chat: AI智能问答
    """
    try:
        result = await dify_tool_manager.execute_tool(
            tool_name=req.tool_name,
            args=req.args,
            provider=req.provider,
            timeout=req.timeout,
            user_id=req.user_id,
        )

        if result.get("success"):
            return ApiResponse(
                message=f"工具 '{req.tool_name}' 执行成功",
                data=result,
            )
        else:
            return ApiResponse(
                code=1,
                message=result.get("error", "工具执行失败"),
                data=result,
            )
    except Exception as e:
        logger.exception("工具执行异常 [%s]: %s", req.tool_name, e)
        return ApiResponse(
            code=500,
            message=f"工具执行异常: {str(e)}",
            data={"tool_name": req.tool_name},
        )


@router.get("/tool/list", response_model=ApiResponse)
async def list_tools(
    category: str | None = Query(default=None, description="按分类筛选 (card_search/social_media/crm_integration 等)"),
    provider: str | None = Query(default=None, description="按提供者筛选"),
):
    """获取可用工具列表

    列出所有已注册的Dify工具插件，可选按分类或提供者筛选。

    工具分类:
      - card_search:      名片信息搜索
      - social_media:     社交媒体集成
      - crm_integration:  CRM集成
      - data_collection:  数据采集
      - data_analysis:    数据分析
      - data_export:      数据导出
      - business_match:   商务匹配
      - intelligence:     智能辅助
    """
    try:
        tools = dify_tool_manager.list_tools(category=category, provider=provider)
        providers = dify_tool_manager.list_providers()

        return ApiResponse(data={
            "tools": tools,
            "total": len(tools),
            "categories": dify_tool_manager.get_tool_categories(),
            "providers": providers,
            "filters": {
                "category": category,
                "provider": provider,
            },
        })
    except Exception as e:
        logger.exception("获取工具列表异常: %s", e)
        return ApiResponse(code=500, message=f"获取工具列表失败: {str(e)}")


@router.get("/tool/categories", response_model=ApiResponse)
async def list_tool_categories():
    """获取工具分类信息"""
    try:
        categories = dify_tool_manager.get_tool_categories()
        return ApiResponse(data={
            "categories": categories,
            "total": len(categories),
        })
    except Exception as e:
        logger.exception("获取工具分类异常: %s", e)
        return ApiResponse(code=500, message=f"获取工具分类失败: {str(e)}")


# ======================================================================
# ── 应用编排相关端点 ──────────────────────────────────────────────
# ======================================================================


@router.post("/app/run", response_model=ApiResponse)
async def run_app(req: AppRunRequest):
    """运行应用编排

    根据场景名称执行多Agent编排，自动按预设计划执行工具链。

    场景示例:
      - card_collection:     名片采集 → OCR识别 → 信息结构化
      - customer_analysis:   画像分析 → 匹配分析 → 标签推荐
      - business_matching:   供需匹配 → 人脉推荐 → CRM录入
      - crm_sync:            线索创建 → 查询列表 → 状态更新
      - data_export:         CSV + vCard 多格式导出
      - social_outreach:     企微链接 → 领英搜索 → 摘要生成
      - intelligent_chat:    AI问答 → 工具推荐 → 摘要

    输入参数参考:
      - card_collection:     {"url": "企业网站URL"}
      - customer_analysis:   {"contact_id": "联系人ID"}
      - business_matching:   {"user_profile": "需求描述", "user_id": "用户ID"}
      - intelligent_chat:    {"query": "用户问题"}
    """
    try:
        # 确保编排器已初始化
        if not dify_orchestrator._initialized:
            await dify_orchestrator.initialize()

        result = await dify_orchestrator.run_scene(
            scene_name=req.scene,
            inputs=req.inputs,
            trace_id=req.trace_id,
        )

        status = result.get("status", "unknown")

        if status == "completed":
            return ApiResponse(
                message=f"场景 '{req.scene}' 编排执行完成",
                data=result,
            )
        elif status == "partial":
            return ApiResponse(
                code=2,
                message=f"场景 '{req.scene}' 编排部分成功",
                data=result,
            )
        elif status == "failed":
            return ApiResponse(
                code=1,
                message=result.get("error", f"场景 '{req.scene}' 编排执行失败"),
                data=result,
            )
        elif status in ("timeout",):
            return ApiResponse(
                code=3,
                message=f"场景 '{req.scene}' 编排超时",
                data=result,
            )
        else:
            return ApiResponse(
                message=f"场景 '{req.scene}' 编排运行中",
                data=result,
            )

    except Exception as e:
        logger.exception("场景编排异常 [%s]: %s", req.scene, e)
        return ApiResponse(
            code=500,
            message=f"场景编排异常: {str(e)}",
            data={"scene": req.scene},
        )


@router.get("/app/scenes", response_model=ApiResponse)
async def list_scenes():
    """获取所有可用的应用编排场景列表"""
    try:
        scenes = dify_orchestrator.list_scenes()
        return ApiResponse(data={
            "scenes": scenes,
            "total": len(scenes),
        })
    except Exception as e:
        logger.exception("获取场景列表异常: %s", e)
        return ApiResponse(code=500, message=f"获取场景列表失败: {str(e)}")


@router.get("/app/plan", response_model=ApiResponse)
async def get_scene_plan(
    scene: str = Query(..., description="场景名称 (如 card_collection)"),
):
    """获取指定场景的编排计划详情

    返回场景的完整编排计划，包括Agent定义、执行顺序、并行分组等。
    """
    try:
        plan = dify_orchestrator.get_plan(scene)
        if plan is None:
            return ApiResponse(
                code=404,
                message=f"场景 '{scene}' 不存在",
            )
        return ApiResponse(data={"plan": plan})
    except Exception as e:
        logger.exception("获取场景计划异常: %s", e)
        return ApiResponse(code=500, message=f"获取场景计划失败: {str(e)}")


@router.get("/app/result", response_model=ApiResponse)
async def get_app_result(
    plan_id: str = Query(..., description="编排计划ID (从 run 返回中获取)"),
):
    """查询应用编排执行结果"""
    try:
        result = dify_orchestrator.get_run_result(plan_id)
        if result is None:
            return ApiResponse(
                code=404,
                message=f"编排结果 '{plan_id}' 不存在",
            )
        return ApiResponse(data={"result": result})
    except Exception as e:
        logger.exception("查询编排结果异常: %s", e)
        return ApiResponse(code=500, message=f"查询编排结果失败: {str(e)}")


@router.get("/app/runs", response_model=ApiResponse)
async def list_app_runs():
    """列出所有编排执行记录"""
    try:
        runs = dify_orchestrator.list_runs()
        return ApiResponse(data={
            "runs": runs,
            "total": len(runs),
        })
    except Exception as e:
        logger.exception("列出编排记录异常: %s", e)
        return ApiResponse(code=500, message=str(e))


# ======================================================================
# ── 提供商管理 ──────────────────────────────────────────────────────
# ======================================================================


@router.post("/tool/provider/register", response_model=ApiResponse)
async def register_provider():
    """注册自定义工具提供者 (占位 — 可通过 CustomSearchToolProvider 扩展)

    实际使用中，可通过代码注入:
        from app.services.dify_tool_service import dify_tool_manager, CustomSearchToolProvider
        provider = CustomSearchToolProvider(api_key="your-key")
        dify_tool_manager.register_provider(provider)
    """
    return ApiResponse(
        message="自定义提供者注册通过 Python SDK 实现: dify_tool_manager.register_provider(provider)",
        data={
            "providers": dify_tool_manager.list_providers(),
            "usage": "from app.services.dify_tool_service import dify_tool_manager, CustomSearchToolProvider\n"
                     "provider = CustomSearchToolProvider(api_key='your-key')\n"
                     "dify_tool_manager.register_provider(provider)",
        },
    )


# ======================================================================
# ── 健康检查 ──────────────────────────────────────────────────────
# ======================================================================


@router.get("/health", response_model=ApiResponse)
async def dify_health_check():
    """Dify工具插件+应用编排 健康检查

    检查:
      - 工具管理器状态
      - 编排器状态
      - 注册提供者数量
      - 可用工具总数
    """
    try:
        # 确保已初始化
        if not dify_tool_manager._initialized:
            await dify_tool_manager.initialize()

        tm_health = dify_tool_manager.health_check()
        orch_health = await dify_orchestrator.health_check()

        all_healthy = (
            tm_health.get("healthy", False)
            and orch_health.get("healthy", False)
        )

        return ApiResponse(data={
            "service": "dify_tool_plugin_orchestrator",
            "healthy": all_healthy,
            "tool_manager": tm_health,
            "orchestrator": orch_health,
            "version": "1.0.0",
            "baize_libs_available": __import__(
                "sys"
            ).modules.get("baize_libs.dify_patterns") is not None,
        })
    except Exception as e:
        logger.exception("Dify健康检查异常: %s", e)
        return ApiResponse(
            code=500,
            message=f"Dify服务健康检查异常: {str(e)}",
            data={"healthy": False, "error": str(e)},
        )
