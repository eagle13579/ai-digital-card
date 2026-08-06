"""
DesignQA Agent — RESTful API 路由
===================================
POST   /api/design-qa/critique       — 设计评审 (Nielsen 10 启发式)
POST   /api/design-qa/audit          — 综合审核 (无障碍 + 性能 + 响应式)
POST   /api/design-qa/antipatterns   — 反模式检测 (37条规则)
GET    /api/design-qa/commands       — 列出所有可用的设计审查命令
GET    /api/design-qa/commands/{id}  — 单个命令详情

使用惰性注册策略：不在 routers/__init__.py 中导入，
而是由 main.py 手动 include_router。
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.design_qa_agent import DesignQAAgent
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/design-qa", tags=["DesignQA 设计审核"])


# ======================================================================
# Pydantic Schemas — 请求/响应模型
# ======================================================================


class CritiqueRequest(BaseModel):
    """设计评审请求"""
    target: str = Field(..., description="审核目标（组件/页面名称/URL）", examples=["用户登录页", "Dashboard"])
    context: str | None = Field(None, description="额外上下文信息，如项目类型、技术栈、目标用户等")

    class Config:
        json_schema_extra = {
            "example": {
                "target": "用户注册页面",
                "context": "移动端 H5 页面，面向 C 端用户，需满足 WCAG AA",
            }
        }


class AuditRequest(BaseModel):
    """综合审核请求"""
    target: str = Field(..., description="审核目标（组件/页面名称/URL）", examples=["产品详情页", "Settings"])
    context: str | None = Field(None, description="额外上下文信息")

    class Config:
        json_schema_extra = {
            "example": {
                "target": "产品详情页",
                "context": "电商类应用，需覆盖桌面端和移动端",
            }
        }


class AntipatternRequest(BaseModel):
    """反模式检测请求"""
    target: str = Field(..., description="检测目标（组件/页面名称/URL）", examples=["Landing Page", "导航栏"])
    context: str | None = Field(None, description="额外上下文信息")

    class Config:
        json_schema_extra = {
            "example": {
                "target": "Landing Page",
                "context": "SaaS 产品主页，检查 AI 生成痕迹",
            }
        }


# ── 响应模型 ──────────────────────────────────────────────────


class ApiResponse(BaseModel):
    """通用 API 响应包装"""
    code: int = 200
    message: str = "ok"
    data: dict[str, Any] | list[Any] | None = None


class ApiError(BaseModel):
    """通用错误响应"""
    code: int
    message: str
    detail: str


# ======================================================================
# Helper — 创建 DesignQAAgent 实例
# ======================================================================


async def _create_agent(db: AsyncSession | None = None) -> DesignQAAgent:
    """惰性创建 DesignQAAgent 实例。

    Args:
        db: 可选的数据库会话（目前 agent 可独立运行）。

    Returns:
        已初始化的 DesignQAAgent 实例。
    """
    agent = DesignQAAgent()
    await agent.init()
    return agent


def _make_error_response(status_code: int, message: str, detail: str) -> dict[str, Any]:
    """构造统一的错误响应结构。"""
    return {
        "code": status_code,
        "message": message,
        "detail": detail,
    }


async def _run_agent_method(
    agent: DesignQAAgent,
    method_name: str,
    target: str,
    context: str | None = None,
) -> dict[str, Any]:
    """通用 agent 方法调用包装。

    Args:
        agent: DesignQAAgent 实例。
        method_name: 要调用的方法名。
        target: 审核目标名称。
        context: 可选的上下文信息。

    Returns:
        结构化的审核报告。

    Raises:
        HTTPException: 当方法不存在或调用失败时。
    """
    method = getattr(agent, method_name, None)
    if method is None:
        raise HTTPException(
            status_code=500,
            detail=f"Agent 方法 '{method_name}' 不存在",
        )

    input_data: dict[str, Any] = {"target": target}
    if context:
        input_data["context"] = context

    try:
        result = await method(input_data)
        if not isinstance(result, dict):
            result = {"result": result}
        return result
    except Exception as exc:
        logger.exception("DesignQAAgent.%s 执行失败: target=%s", method_name, target)
        raise HTTPException(
            status_code=500,
            detail=f"审核执行失败: {exc}",
        )


# ======================================================================
# API Endpoints
# ======================================================================


@router.post(
    "/critique",
    response_model=ApiResponse,
    summary="设计评审 — Nielsen 10 启发式评估",
    description="""
    基于 Nielsen 10 项可用性启发式对目标设计进行定量评分（0-40分）。
    
    评估维度：
    - 系统状态可见性
    - 系统与现实世界的匹配
    - 用户控制和自由
    - 一致性和标准
    - 错误预防
    - 识别而非回忆
    - 灵活性和效率
    - 美学和极简主义设计
    - 帮助用户识别/诊断/恢复错误
    - 帮助和文档
    
    同时自动运行 37 条反模式检测规则。
    """,
    responses={
        200: {"description": "设计评审报告（含评分、发现项、推荐建议）"},
        500: {"description": "评审执行失败", "model": ApiError},
    },
)
async def critique_design(
    request: CritiqueRequest,
    db: AsyncSession = Depends(get_db),
):
    """对目标设计进行启发式评审。

    Args:
        request: 评审请求体，包含 target（目标名称）和可选的 context。
        db: 数据库会话（注入，当前用于扩展兼容）。

    Returns:
        结构化评审报告，含 Nielsen 10 项评分、P0-P3 严重性问题列表、推荐建议。
    """
    agent = await _create_agent(db)
    try:
        result = await _run_agent_method(
            agent, "critique_design",
            request.target, request.context,
        )
        return ApiResponse(code=200, message="设计评审完成", data=result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("critique_design 未预期异常")
        raise HTTPException(status_code=500, detail=f"设计评审失败: {exc}")
    finally:
        await agent.stop()


@router.post(
    "/audit",
    response_model=ApiResponse,
    summary="综合审核 — 无障碍 + 性能 + 响应式",
    description="""
    对目标进行全面的技术质量审核，整合三个维度：
    
    1. **无障碍审核 (Accessibility)** — WCAG AA 标准
       - 颜色对比度、ARIA 标签、键盘导航、语义 HTML、alt 文本、表单标签
    
    2. **性能审核 (Performance)** — Core Web Vitals
       - LCP（Largest Contentful Paint）、CLS（Cumulative Layout Shift）
       - INP（Interaction to Next Paint）、布局动画、图片优化、打包体积
    
    3. **响应式审核 (Responsive)** — 多端适配
       - 固定宽度、触摸目标（44x44px）、水平滚动、文本缩放、断点缺失
    
    返回合并后的综合评分和按严重性分组的发现项。
    """,
    responses={
        200: {"description": "综合审核报告（三个维度合并）"},
        500: {"description": "审核执行失败", "model": ApiError},
    },
)
async def audit_design(
    request: AuditRequest,
    db: AsyncSession = Depends(get_db),
):
    """对目标进行综合技术质量审核。

    同时运行无障碍、性能和响应式三个维度的检查，
    并将结果合并为一份综合报告。

    Args:
        request: 审核请求体，包含 target 和可选的 context。
        db: 数据库会话。

    Returns:
        合并的综合审核报告，包含三个维度的评分、发现项和推荐建议。
    """
    agent = await _create_agent(db)
    try:
        input_data: dict[str, Any] = {"target": request.target}
        if request.context:
            input_data["context"] = request.context

        # 并行运行三个维度的审核
        import asyncio

        a11y, perf, responsive = await asyncio.gather(
            agent.audit_accessibility(input_data),
            agent.audit_performance(input_data),
            agent.audit_responsive(input_data),
        )

        # 合并报告
        combined = _merge_audit_reports(a11y, perf, responsive)
        return ApiResponse(code=200, message="综合审核完成", data=combined)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("audit_design 未预期异常")
        raise HTTPException(status_code=500, detail=f"综合审核失败: {exc}")
    finally:
        await agent.stop()


@router.post(
    "/antipatterns",
    response_model=ApiResponse,
    summary="反模式检测 — 37条规则全面扫描",
    description="""
    运行全部 37 条反模式检测规则，分为两大类：
    
    **AI 生成痕迹 (Slop)** — P0-P3 严重性
    - 侧边彩色边框、渐变文字、AI 配色方案、奶油色背景
    - 嵌套卡片、单一字体、弹跳缓动、反光暗色模式
    - 图标磁砖堆叠、斜体衬线标题、营销词汇等
    
    **通用质量问题 (Quality)** — P0-P3 严重性
    - 低对比度文字、灰色文本/彩色背景、布局过渡动画
    - 行过长、内边距不足、跳过头层级、两端对齐文本等
    
    返回按严重性（P0→P3）分组的检测结果。
    """,
    responses={
        200: {"description": "反模式检测报告（按严重性分组）"},
        500: {"description": "检测执行失败", "model": ApiError},
    },
)
async def detect_antipatterns(
    request: AntipatternRequest,
    db: AsyncSession = Depends(get_db),
):
    """对目标进行 37 条反模式规则扫描。

    Args:
        request: 检测请求体，包含 target 和可选的 context。
        db: 数据库会话。

    Returns:
        结构化的反模式检测报告，按 P0-P3 严重性分组。
    """
    agent = await _create_agent(db)
    try:
        result = await _run_agent_method(
            agent, "detect_antipatterns",
            request.target, request.context,
        )
        return ApiResponse(code=200, message="反模式检测完成", data=result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("detect_antipatterns 未预期异常")
        raise HTTPException(status_code=500, detail=f"反模式检测失败: {exc}")
    finally:
        await agent.stop()


@router.get(
    "/commands",
    response_model=ApiResponse,
    summary="列出所有设计审查命令（23条）",
    description="""
    返回 Impeccable 的 23 条设计审查命令列表。
    
    支持可选的 ?category= 参数按分类过滤：
    - create    — 创建类命令（craft, live, onboard, overdrive, shape）
    - refine    — 优化类命令（extract, adapt, animate, bolder, clarify 等）
    - evaluate  — 评估类命令（critique, audit）
    - system    — 系统类命令（init, document）
    - simplify  — 简化类命令（distill, quieter）
    - harden    — 加固类命令（harden, optimize）
    """,
    responses={
        200: {"description": "命令列表"},
        500: {"description": "获取失败", "model": ApiError},
    },
)
async def list_commands(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """获取所有可用的 Impeccable 设计审查命令。

    Args:
        category: 可选的分分类过滤器（create / refine / evaluate / system / simplify / harden）。
        db: 数据库会话。

    Returns:
        命令元数据列表，每条包含 id、name、description、category 等。
    """
    agent = await _create_agent(db)
    try:
        commands = await agent._list_commands(category)
        return ApiResponse(code=200, message="ok", data=commands)
    except Exception as exc:
        logger.exception("list_commands 获取失败")
        raise HTTPException(status_code=500, detail=f"获取命令列表失败: {exc}")
    finally:
        await agent.stop()


@router.get(
    "/commands/{command_id}",
    response_model=ApiResponse,
    summary="获取单个命令详情",
    description="""
    按命令 ID 获取某个 Impeccable 审查命令的详细信息。
    
    可用命令 ID 示例：
    - craft — 端到端功能构建
    - critique — 设计评审
    - audit — 技术质量审核
    - detect_antipatterns — 反模式检测
    - polish — 上线前最终质量检查
    - layout — 布局审核
    - typeset — 排版审核
    - colorize — 色彩审核
    - animate — 动效审核
    - adapt — 响应式适配
    """,
    responses={
        200: {"description": "命令详细信息"},
        404: {"description": "命令不存在", "model": ApiError},
        500: {"description": "查询失败", "model": ApiError},
    },
)
async def get_command_detail(
    command_id: str = Path(..., description="命令 ID，如 'critique'、'audit'、'polish'"),
    db: AsyncSession = Depends(get_db),
):
    """按 ID 获取指定审查命令的详细信息。

    Args:
        command_id: 命令唯一标识（如 critique、audit、polish）。
        db: 数据库会话。

    Returns:
        命令的完整元数据，包括描述、分类、参数提示等。

    Raises:
        HTTPException 404: 指定命令不存在。
    """
    agent = await _create_agent(db)
    try:
        command = await agent._get_command_knowledge(command_id)
        if command is None:
            raise HTTPException(
                status_code=404,
                detail=f"命令 '{command_id}' 不存在。可用命令列表请 GET /api/design-qa/commands",
            )
        return ApiResponse(code=200, message="ok", data=command)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_command_detail 查询失败 (command_id=%s)", command_id)
        raise HTTPException(status_code=500, detail=f"查询命令详情失败: {exc}")
    finally:
        await agent.stop()


# ======================================================================
# Internal Helpers
# ======================================================================


def _merge_audit_reports(
    a11y: dict[str, Any],
    perf: dict[str, Any],
    responsive: dict[str, Any],
) -> dict[str, Any]:
    """将三个维度的审核报告合并为一份综合报告。

    Args:
        a11y: 无障碍审核报告。
        perf: 性能审核报告。
        responsive: 响应式审核报告。

    Returns:
        合并后的综合审核报告。
    """
    total_score = a11y.get("score", 0) + perf.get("score", 0) + responsive.get("score", 0)
    total_max = a11y.get("max_score", 0) + perf.get("max_score", 0) + responsive.get("max_score", 0)

    all_findings = []
    for report in [a11y, perf, responsive]:
        findings = report.get("findings", [])
        if findings:
            all_findings.extend(findings)

    all_recommendations = []
    for report in [a11y, perf, responsive]:
        recs = report.get("recommendations", [])
        if recs:
            all_recommendations.extend(recs)

    # 合并严重性分组
    severity: dict[str, list[dict[str, Any]]] = {"P0": [], "P1": [], "P2": [], "P3": []}
    for f in all_findings:
        sev = f.get("severity", "P2")
        if sev in severity:
            severity[sev].append(f)

    from datetime import datetime, timezone

    return {
        "command": "comprehensive_audit",
        "dimensions": [
            {"name": "accessibility", "score": a11y.get("score", 0), "max_score": a11y.get("max_score", 0)},
            {"name": "performance", "score": perf.get("score", 0), "max_score": perf.get("max_score", 0)},
            {"name": "responsive", "score": responsive.get("score", 0), "max_score": responsive.get("max_score", 0)},
        ],
        "score": total_score,
        "max_score": total_max,
        "score_pct": round(total_score / total_max * 100, 1) if total_max > 0 else 0,
        "severity": severity,
        "total_findings": len(all_findings),
        "findings": all_findings,
        "recommendations": all_recommendations,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
