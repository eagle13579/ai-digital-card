"""
AI数智名片 三明治匹配管线 — 在线层 API 端点
============================================

提供基于向量语义的智能匹配 API。

端点:
  POST /api/matching/search         — 语义搜索匹配
  POST /api/matching/batch-embed    — 批量嵌入索引
  GET  /api/matching/collections    — 查看所有集合状态
  DELETE /api/matching/collections/{name} — 删除集合
"""

import logging
import time
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.smart_matcher import SmartMatcher, get_smart_matcher
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/matching", tags=["三明治匹配"])

# ── 请求/响应模型 ──────────────────────────────────────────────────────


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="搜索文本，如'找做跨境支付的供应商'")
    type: str = Field("supplier", description="匹配类型: supplier|customer|dealer")
    top_k: int = Field(10, ge=1, le=100, description="返回结果数量上限")


class SearchResponseItem(BaseModel):
    id: str
    name: str = ""
    score: float
    summary: str = ""


class SearchResponse(BaseModel):
    results: list[SearchResponseItem]
    latency_ms: float


class BatchEmbedItem(BaseModel):
    id: str | int
    text: str = Field(..., min_length=1, description="需要嵌入的文本内容")


class BatchEmbedRequest(BaseModel):
    items: list[BatchEmbedItem] = Field(..., min_length=1, max_length=1000)
    collection: str = Field("suppliers", description="目标 collection: customers|suppliers|dealers")


class BatchEmbedResponse(BaseModel):
    embedded_count: int
    latency_ms: float


class CollectionStatus(BaseModel):
    name: str
    label: str
    count: int


class CollectionsResponse(BaseModel):
    collections: list[CollectionStatus]


# ── API 端点 ──────────────────────────────────────────────────────────


@router.post("/search", response_model=SearchResponse)
async def matching_search(data: SearchRequest):
    """语义搜索匹配

    使用向量数据库搜索语义相似的内容。
    支持三种业务类型: supplier(供应商), customer(客户), dealer(经销商).
    """
    t0 = time.time()

    # 类型映射
    type_map = {
        "supplier": "suppliers",
        "customer": "customers",
        "dealer": "dealers",
    }
    col_name = type_map.get(data.type)
    if col_name is None:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的匹配类型: {data.type}，可用: {list(type_map.keys())}",
        )

    try:
        # 获取 embedding
        from app.ai.embedding_service import get_embedding_service
        emb_svc = get_embedding_service()
        query_vec = emb_svc.embed_text(data.query)

        # 向量搜索
        from app.ai.vector_store import get_vector_store
        store = get_vector_store()
        results = store.search(
            collection_name=col_name,
            query_embedding=query_vec,
            top_k=data.top_k,
            include_metadata=True,
        )

        # 格式化响应
        items = []
        for r in results:
            meta = r.get("metadata", {})
            name = meta.get("name", meta.get("text", r.get("text", "")))
            summary = meta.get("summary", meta.get("description", ""))
            items.append(SearchResponseItem(
                id=r["id"],
                name=name[:100] if name else "",
                score=r["score"],
                summary=summary[:500] if summary else "",
            ))

        latency = round((time.time() - t0) * 1000, 2)
        return SearchResponse(results=items, latency_ms=latency)

    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"AI 模块未就绪: {e}")
    except Exception as e:
        logger.error(f"[Matching] search 失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {e}")


@router.post("/batch-embed", response_model=BatchEmbedResponse)
async def batch_embed(data: BatchEmbedRequest):
    """批量嵌入并索引内容到向量数据库

    将一批文本内容生成 embedding 并存入指定 collection。
    """
    t0 = time.time()

    col_name = data.collection
    if col_name not in ("customers", "suppliers", "dealers"):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的 collection: {col_name}，可用: customers|suppliers|dealers",
        )

    try:
        from app.ai.embedding_service import get_embedding_service
        from app.ai.vector_store import get_vector_store

        emb_svc = get_embedding_service()
        store = get_vector_store()

        texts = [item.text for item in data.items]
        embeddings = emb_svc.embed_batch(texts)

        batch_items = []
        for i, item in enumerate(data.items):
            batch_items.append({
                "id": str(item.id),
                "text": item.text,
                "embedding": embeddings[i],
                "metadata": {"name": item.text[:100], "source": "batch-embed"},
            })

        count = store.add_batch(col_name, batch_items)

        latency = round((time.time() - t0) * 1000, 2)
        return BatchEmbedResponse(embedded_count=count, latency_ms=latency)

    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"AI 模块未就绪: {e}")
    except Exception as e:
        logger.error(f"[Matching] batch-embed 失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量嵌入失败: {e}")


@router.get("/collections", response_model=CollectionsResponse)
async def list_collections():
    """列出所有向量集合及其状态"""
    try:
        from app.ai.vector_store import get_vector_store
        store = get_vector_store()
        cols = store.list_collections()
        return CollectionsResponse(collections=[
            CollectionStatus(name=c["name"], label=c["label"], count=c["count"])
            for c in cols
        ])
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"向量数据库模块未就绪: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取集合列表失败: {e}")


@router.delete("/collections/{name}")
async def delete_collection(name: str):
    """删除指定向量集合"""
    if name not in ("customers", "suppliers", "dealers"):
        raise HTTPException(status_code=400, detail=f"不支持的 collection: {name}")
    try:
        from app.ai.vector_store import get_vector_store
        store = get_vector_store()
        store.delete_collection(name)
        return {"detail": f"Collection '{name}' 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")


@router.get("/health")
async def matching_health():
    """匹配服务健康检查"""
    status = {"service": "matching", "status": "ok"}
    try:
        from app.ai.embedding_service import get_embedding_service
        svc = get_embedding_service()
        status["embedding_model"] = svc.model_name
        status["embedding_dim"] = svc.dimension
        status["cache_size"] = svc.cache_size
    except Exception as e:
        status["embedding"] = f"unavailable: {e}"
        status["status"] = "degraded"
    try:
        from app.ai.vector_store import get_vector_store
        store = get_vector_store()
        status["vector_store"] = store.persist_dir
    except Exception as e:
        status["vector_store"] = f"unavailable: {e}"
        status["status"] = "degraded"
    return status


# ── 语义分析请求/响应模型 ──────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    user_ids: list[int] = Field(..., min_length=1, max_length=50, description="需要分析的用户ID列表")


class MatchAnalysis(BaseModel):
    user_a: dict = Field(..., description="用户A概要信息")
    user_b: dict = Field(..., description="用户B概要信息")
    match_score: float = Field(..., description="综合匹配度 (0~1)")
    matched_pairs: list[dict] = Field(default_factory=list, description="语义匹配的标签对")
    explanation: str = Field("", description="自然语言匹配解释")


class AnalyzeResponse(BaseModel):
    analyses: list[MatchAnalysis]
    total_pairs: int


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_matches(
    data: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """语义配对分析 — 对指定的用户列表进行两两语义匹配分析

    输入: 用户ID列表
    输出: 每对用户的语义匹配分析和解释

    使用 DeepSeek LLM 理解标签之间的语义关系，而不是简单的字符串匹配。
    """
    from sqlalchemy import select
    from app.models.user import User
    from app.models.tag import UserTag

    # 1. 获取所有指定用户
    result = await db.execute(
        select(User).where(User.id.in_(data.user_ids))
    )
    users = {u.id: u for u in result.scalars().all()}

    if len(users) < 2:
        raise HTTPException(status_code=400, detail="至少需要2个用户才能进行配对分析")

    # 2. 获取所有用户的标签
    result = await db.execute(
        select(UserTag).where(UserTag.user_id.in_(data.user_ids))
    )
    all_tags = result.scalars().all()

    # 按 user_id 分组标签
    user_tags: dict[int, list[dict]] = {}
    for t in all_tags:
        if t.user_id not in user_tags:
            user_tags[t.user_id] = []
        user_tags[t.user_id].append({
            "tag": t.tag,
            "type": t.tag_type,
            "weight": t.weight or 0.5,
        })

    # 3. 初始化智能匹配器
    matcher = get_smart_matcher()

    # 4. 两两分析
    user_ids = list(users.keys())
    analyses = []

    for i in range(len(user_ids)):
        for j in range(i + 1, len(user_ids)):
            uid_a = user_ids[i]
            uid_b = user_ids[j]

            user_a = users[uid_a]
            user_b = users[uid_b]

            # 用户的标签
            tags_a = user_tags.get(uid_a, [])
            tags_b = user_tags.get(uid_b, [])

            # 用户画像
            profile_a = {
                "name": user_a.name,
                "company": user_a.company,
                "title": user_a.title,
                "intro": user_a.intro or "",
            }
            profile_b = {
                "name": user_b.name,
                "company": user_b.company,
                "title": user_b.title,
                "intro": user_b.intro or "",
            }

            # 语义匹配分析
            analysis = await matcher.semantic_match_score(
                my_tags=tags_a,
                other_tags=tags_b,
                my_profile=profile_a,
                other_profile=profile_b,
            )

            # 生成自然语言解释（如果 LLM 没有提供）
            explanation = analysis.get("explanation", "")
            if not explanation:
                try:
                    explanation = await matcher.generate_match_explanation(
                        user_a=profile_a,
                        user_b=profile_b,
                        matched_pairs=analysis.get("matched_pairs", []),
                    )
                except Exception:
                    explanation = "暂无匹配解释"

            analyses.append(MatchAnalysis(
                user_a={
                    "id": user_a.id,
                    "name": user_a.name,
                    "company": user_a.company,
                    "title": user_a.title,
                },
                user_b={
                    "id": user_b.id,
                    "name": user_b.name,
                    "company": user_b.company,
                    "title": user_b.title,
                },
                match_score=analysis.get("score", 0.0),
                matched_pairs=analysis.get("matched_pairs", []),
                explanation=explanation,
            ))

    # 按匹配度降序排列
    analyses.sort(key=lambda x: x.match_score, reverse=True)

    return AnalyzeResponse(
        analyses=analyses,
        total_pairs=len(analyses),
    )
