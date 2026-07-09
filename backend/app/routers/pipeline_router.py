"""
三管道 API 路由 — SAG / Hybrid / Pipeline Router
=====================================================
对外暴露的 API 端点：
  1. POST /api/v1/ai/sag/analyze      — SAG 自我推演（6种推理模式）
  2. POST /api/v1/ai/hybrid/query     — Hybrid RAG+SAG 融合查询
  3. POST /api/v1/ai/pipeline/query   — 三管道自动路由查询
  4. GET  /api/v1/ai/pipeline/status  — 三管道健康状态
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI管道"])


# ======================================================================
# 请求 / 响应模型
# ======================================================================


class SAGAnalyzeRequest(BaseModel):
    """SAG 自我推演请求"""
    mode: str = Field(
        ...,
        description="推理模式: quality_review | matching_reasoning | trust_inference | explain_recommend | contradiction_detect | optimize_suggest",
    )
    content: dict = Field(..., description="推理输入内容")
    depth: str = Field("standard", description="推理深度: fast | standard | deep")
    temperature: float = Field(0.5, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=64, le=8192)


class SAGAnalyzeResponse(BaseModel):
    conclusion: str
    reasoning_chain: list[dict] = []
    confidence: float = 0.0
    score: float | None = None
    suggestions: list[str] = []
    model_used: str = ""
    tokens_used: int = 0


class HybridQueryRequest(BaseModel):
    """Hybrid RAG+SAG 融合查询请求"""
    query: str = Field(..., description="查询文本")
    top_k: int = Field(10, ge=1, le=50)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=64, le=8192)


class HybridQueryResponse(BaseModel):
    answer: str
    sources: list[dict] = []
    analysis: str | None = None
    reasoning_chain: list[dict] | None = None
    confidence: float = 0.0
    suggestions: list[str] = []
    has_correction: bool = False
    tokens_used: dict = {}


class PipelineQueryRequest(BaseModel):
    """三管道自动路由查询请求"""
    query: str = Field(..., description="查询文本")
    force_pipeline: str | None = Field(None, description="强制指定管道: rag | sag | hybrid")
    top_k: int = Field(10, ge=1, le=50)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=64, le=8192)


class PipelineQueryResponse(BaseModel):
    answer: str
    pipeline: str = ""
    confidence: float = 0.0
    sources: list[dict] = []
    sag_analysis: str | None = None
    reasoning_chain: list[dict] | None = None
    score: float | None = None
    suggestions: list[str] = []
    tokens_used: dict = {}
    has_correction: bool = False


class PipelineStatusResponse(BaseModel):
    rag: bool = False
    sag: bool = False
    hybrid: bool = False
    deepseek_api_key_configured: bool = False
    deepseek_reachable: bool | None = None


# ======================================================================
# API 端点
# ======================================================================


@router.post("/sag/analyze", response_model=SAGAnalyzeResponse)
async def sag_analyze(
    request: SAGAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SAG 自我推演 — 不依赖外部检索，纯模型内部推理

    6种推理模式:
      - quality_review: 名片质量评审
      - matching_reasoning: 匹配逻辑推理
      - trust_inference: 信任链推理
      - explain_recommend: 推荐解释生成
      - contradiction_detect: 矛盾检测
      - optimize_suggest: 优化建议
    """
    from app.ai.sag_pipeline import SAGPipeline, SAGMode, SAGDepth

    # 验证 mode
    try:
        mode = SAGMode(request.mode)
    except ValueError:
        valid = [m.value for m in SAGMode]
        raise HTTPException(
            status_code=400,
            detail=f"无效的推理模式: {request.mode}，支持: {', '.join(valid)}",
        )

    # 验证 depth
    try:
        depth = SAGDepth(request.depth)
    except ValueError:
        valid = [d.value for d in SAGDepth]
        raise HTTPException(
            status_code=400,
            detail=f"无效的推理深度: {request.depth}，支持: {', '.join(valid)}",
        )

    sag = SAGPipeline()
    try:
        result = await sag.analyze(
            mode=mode,
            content=request.content,
            user_id=current_user.id,
            depth=depth,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        return SAGAnalyzeResponse(
            conclusion=result.conclusion,
            reasoning_chain=[s.to_dict() for s in result.reasoning_chain],
            confidence=result.confidence,
            score=result.score,
            suggestions=result.suggestions,
            model_used=result.model_used,
            tokens_used=result.tokens_used,
        )
    except Exception as e:
        logger.exception("SAG 推理失败")
        raise HTTPException(status_code=500, detail=f"SAG 推理失败: {str(e)}")
    finally:
        await sag.close()


@router.post("/hybrid/query", response_model=HybridQueryResponse)
async def hybrid_query(
    request: HybridQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hybrid RAG+SAG 融合查询

    先 RAG 检索外部知识（向量搜索+用户画像+知识图谱）
    再 SAG 自校验逻辑一致性，SAG 推理补充
    """
    from app.ai.hybrid_pipeline import HybridPipeline

    hybrid = HybridPipeline(db)
    try:
        result = await hybrid.query(
            user_id=current_user.id,
            query_text=request.query,
            top_k=request.top_k,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        return HybridQueryResponse(
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            analysis=result.get("analysis"),
            reasoning_chain=result.get("reasoning_chain"),
            confidence=result.get("confidence", 0.5),
            suggestions=result.get("suggestions", []),
            has_correction=result.get("has_correction", False),
            tokens_used=result.get("tokens_used", {}),
        )
    except Exception as e:
        logger.exception("Hybrid 查询失败")
        raise HTTPException(status_code=500, detail=f"Hybrid 查询失败: {str(e)}")
    finally:
        await hybrid.close()


@router.post("/pipeline/query", response_model=PipelineQueryResponse)
async def pipeline_query(
    request: PipelineQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """三管道自动路由查询

    根据查询内容自动选择最优管道：
      - 事实类 → RAG（向量搜索+图谱检索）
      - 推理类 → SAG（纯自我推演）
      - 混合类 → Hybrid（RAG+SAG 融合）
    可通过 force_pipeline 强制指定管道。
    """
    from app.ai.pipeline_router import PipelineRouter

    if request.force_pipeline and request.force_pipeline not in ("rag", "sag", "hybrid"):
        raise HTTPException(
            status_code=400,
            detail=f"无效的管道: {request.force_pipeline}，支持: rag, sag, hybrid",
        )

    router = PipelineRouter(db)
    try:
        result = await router.query(
            user_id=current_user.id,
            query_text=request.query,
            top_k=request.top_k,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            force_pipeline=request.force_pipeline,
        )
        return PipelineQueryResponse(
            answer=result.answer,
            pipeline=result.pipeline.value,
            confidence=result.confidence,
            sources=result.sources,
            sag_analysis=result.sag_analysis,
            reasoning_chain=result.reasoning_chain,
            score=result.score,
            suggestions=result.suggestions,
            tokens_used=result.tokens_used,
            has_correction=result.has_correction,
        )
    except Exception as e:
        logger.exception("管道路由查询失败")
        raise HTTPException(status_code=500, detail=f"管道查询失败: {str(e)}")
    finally:
        await router.close()


@router.get("/pipeline/status", response_model=PipelineStatusResponse)
async def pipeline_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """三管道健康状态"""
    from app.ai.pipeline_router import PipelineRouter

    router = PipelineRouter(db)
    try:
        status = await router.get_status()
        return PipelineStatusResponse(
            rag=status.get("rag", False),
            sag=status.get("sag", False),
            hybrid=status.get("hybrid", False),
            deepseek_api_key_configured=status.get("deepseek_api_key_configured", False),
            deepseek_reachable=status.get("deepseek_reachable"),
        )
    except Exception as e:
        logger.exception("管道状态查询失败")
        return PipelineStatusResponse(
            deepseek_api_key_configured=False,
        )
    finally:
        await router.close()
