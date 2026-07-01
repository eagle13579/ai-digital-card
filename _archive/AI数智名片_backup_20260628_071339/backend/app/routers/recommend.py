"""
AI数字名片 推荐 API
===================
提供三种推荐接口:
  1. POST /api/recommend/personal   - 个性化推荐（基于用户行为+图谱+语义）
  2. POST /api/recommend/discover   - 发现推荐（全局发现页）
  3. POST /api/recommend/similar    - 相似名片推荐
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.recommendation import RecommendEngine
from app.ai.rag_pipeline import RAGPipeline
from app.database import get_db
from app.models.tag import MatchRecord
from app.models.user import User
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recommend", tags=["推荐"])


# ======================================================================
# 请求 / 响应模型
# ======================================================================


class PersonalRecommendRequest(BaseModel):
    top_k: int = Field(20, ge=1, le=100, description="返回数量")
    strategy: str = Field("hybrid", description="推荐策略: tag | graph | semantic | hybrid")
    exclude_user_ids: list[int] = Field(default_factory=list, description="排除的用户 ID")


class DiscoverRequest(BaseModel):
    top_k: int = Field(30, ge=1, le=100, description="返回数量")
    purpose: Optional[str] = Field(None, description="筛选用途: partner/client/investor/supplier")


class SimilarUsersRequest(BaseModel):
    target_user_id: int = Field(..., description="目标用户 ID（参考用户）")
    top_k: int = Field(10, ge=1, le=50, description="返回数量")


class RecommendItemResponse(BaseModel):
    user_id: int
    name: str
    company: str = ""
    title: str = ""
    avatar: str = ""
    intro: str = ""
    score: float = 0.0
    tag_match_score: float = 0.0
    graph_score: float = 0.0
    semantic_score: float = 0.0
    reasons: list[str] = []
    common_tags: list[str] = []
    match_type: str = "mixed"


class RecommendResponse(BaseModel):
    items: list[RecommendItemResponse]
    total: int
    strategy_used: str = ""


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="查询文本")
    top_k: int = Field(10, ge=1, le=50, description="向量搜索返回数量")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="LLM 温度")
    max_tokens: int = Field(2048, ge=64, le=8192, description="最大 token 数")


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[dict] = []
    confidence: float = 0.0
    model_used: str = "deepseek-chat"
    tokens_used: int = 0


# ======================================================================
# 推荐 API 端点
# ======================================================================


@router.post("/personal", response_model=RecommendResponse)
async def personal_recommend(
    data: PersonalRecommendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """个性化推荐 - 基于标签匹配 + 关系图谱 + 语义相似度"""
    engine = RecommendEngine(db)

    if data.strategy not in ("tag", "graph", "semantic", "hybrid"):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的推荐策略: {data.strategy}，可选: tag, graph, semantic, hybrid",
        )

    # 获取已匹配用户 ID 列表（排除已 match 的用户）
    result = await db.execute(
        select(MatchRecord).where(
            (MatchRecord.user_a_id == current_user.id) | (MatchRecord.user_b_id == current_user.id)
        )
    )
    matched_records = result.scalars().all()
    matched_ids = set()
    for mr in matched_records:
        matched_ids.add(mr.user_b_id if mr.user_a_id == current_user.id else mr.user_a_id)

    exclude_ids = list(matched_ids | set(data.exclude_user_ids))

    result = await engine.personalize_recommend(
        user_id=current_user.id,
        top_k=data.top_k,
        exclude_ids=exclude_ids,
        strategy=data.strategy,
    )

    return RecommendResponse(
        items=[RecommendItemResponse(**i.to_dict()) for i in result.items],
        total=result.total,
        strategy_used=result.strategy_used,
    )


@router.post("/discover", response_model=RecommendResponse)
async def discover_recommend(
    data: DiscoverRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发现推荐 - 发现页全局推荐"""
    engine = RecommendEngine(db)

    valid_purposes = (None, "partner", "client", "investor", "supplier")
    if data.purpose not in valid_purposes:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的用途: {data.purpose}，可选: partner, client, investor, supplier",
        )

    result = await engine.discover(
        user_id=current_user.id,
        top_k=data.top_k,
        purpose=data.purpose,
    )

    return RecommendResponse(
        items=[RecommendItemResponse(**i.to_dict()) for i in result.items],
        total=result.total,
        strategy_used=result.strategy_used,
    )


@router.post("/similar", response_model=RecommendResponse)
async def similar_users(
    data: SimilarUsersRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """相似名片推荐 - 基于指定用户查找相似用户"""
    engine = RecommendEngine(db)

    # 验证目标用户存在
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == data.target_user_id))
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    result = await engine.similar_users(
        target_user_id=data.target_user_id,
        current_user_id=current_user.id,
        top_k=data.top_k,
    )

    return RecommendResponse(
        items=[RecommendItemResponse(**i.to_dict()) for i in result.items],
        total=result.total,
        strategy_used=result.strategy_used,
    )


@router.post("/rag-query", response_model=RAGQueryResponse)
async def rag_query(
    data: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """RAG 智能问答 - 基于检索增强生成回答用户问题

    结合向量搜索 + 用户画像 + 关系图谱上下文，使用 DeepSeek 大模型生成回答。
    """
    pipeline = RAGPipeline(db)
    try:
        response = await pipeline.query(
            user_id=current_user.id,
            query_text=data.query,
            top_k=data.top_k,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
        )

        return RAGQueryResponse(
            answer=response.answer,
            sources=response.sources,
            confidence=response.confidence,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
        )
    except Exception as e:
        logger.error(f"RAG query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RAG 查询失败: {str(e)}")
    finally:
        await pipeline.close()


@router.get("/graph-summary")
async def graph_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的关系图谱摘要"""
    from app.ai.knowledge_graph import CachedKnowledgeGraphBuilder
    builder = CachedKnowledgeGraphBuilder(db)
    summary = await builder.get_graph_summary(current_user.id)
    return summary


@router.get("/graph")
async def get_graph(
    depth: int = Query(1, ge=1, le=3, description="关系深度"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的完整关系图谱"""
    from app.ai.knowledge_graph import CachedKnowledgeGraphBuilder
    builder = CachedKnowledgeGraphBuilder(db)
    kg = await builder.build_user_graph(current_user.id, max_depth=depth)
    return kg.to_dict()
