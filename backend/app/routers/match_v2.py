"""
AI数字名片 — 匹配引擎 V2 API 路由
===================================

V2 升级功能:
  - 五层综合评分：标签重叠 + 语义相似 + 标签权重 + 行业互补 + 注意力匹配
  - 协同过滤推荐 (ItemBasedCF / UserBasedCF)
  - MMR 多样性重排序
  - 匹配理由解释（四头注意力细节）
  - 反馈闭环集成

路由前缀: /api/v2/match
"""

from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.attention_matcher import AttentionMatcher, UserFeatures
from app.ai.mmr_diversity import MMRDiversityEngine
from app.database import get_db
from app.models.tag import MatchRecord
from app.models.user import User
from app.models.brochure import Brochure
from app.routers.auth import get_current_user
from app.services.cf_engine import ItemBasedCF, UserBasedCF
from app.services.feedback_service import FeedbackService
from app.services.matching_engine_v2 import MatchEngineV2

router = APIRouter(prefix="/api/v2/match", tags=["匹配V2"])


# ======================================================================
# 请求/响应模型
# ======================================================================


class RecommendRequest(BaseModel):
    """推荐请求"""
    limit: int = Field(10, ge=1, le=50, description="返回结果数量上限")
    min_score: float = Field(0.1, ge=0.0, le=1.0, description="最低匹配分数阈值")
    include_cf: bool = Field(True, description="是否包含协同过滤结果")


class DiverseRecommendRequest(BaseModel):
    """多样性推荐请求"""
    query: str = Field(..., min_length=1, max_length=200, description="搜索关键词")
    limit: int = Field(10, ge=1, le=50, description="返回结果数量上限")
    lambda_param: float = Field(0.5, ge=0.0, le=1.0, description="MMR 多样性参数，1=完全相关性，0=完全多样性")
    keyword_weight: float = Field(0.3, ge=0.0, le=1.0, description="关键词搜索权重")
    vector_weight: float = Field(0.7, ge=0.0, le=1.0, description="向量搜索权重")


class ExplainRequest(BaseModel):
    """匹配解释请求"""
    target_user_id: int = Field(..., ge=1, description="目标用户ID")


class ExplainDetail(BaseModel):
    """单头注意力详情"""
    attention: float = Field(..., description="注意力分数 [0, 1]")
    weight: float = Field(..., description="权重系数")
    contribution: float = Field(..., description="对综合得分的贡献")


class ExplainResponse(BaseModel):
    """匹配解释响应"""
    score: float = Field(..., description="综合匹配度")
    details: dict[str, ExplainDetail] = Field(..., description="各头注意力详情")
    availability: float = Field(..., description="可用性调节系数")
    features: dict[str, Any] = Field(..., description="双方特征信息")
    v2_scores: dict[str, float] = Field(..., description="V2五层评分明细")


class RecommendItem(BaseModel):
    """单条推荐结果"""
    user_id: int
    user_name: str = ""
    user_company: str = ""
    user_title: str = ""
    user_avatar: str = ""
    score: float = 0.0
    tag_overlap: float = 0.0
    vector_semantic: float = 0.0
    tag_weight: float = 0.0
    industry_complement: float = 0.0
    attention_score: float = 0.0
    common_tags: list[dict] = Field(default_factory=list)
    source: str = "v2_engine"


class RecommendResponse(BaseModel):
    """推荐响应"""
    data: list[dict[str, Any]]
    total: int
    has_more: bool
    engine_version: str = "v2.0"
    timestamp: str = ""


class DiverseRecommendResponse(BaseModel):
    """多样性推荐响应"""
    data: list[dict[str, Any]]
    total: int
    diversity_score: float = 0.0
    engine_version: str = "v2.0"


class EngineStatusResponse(BaseModel):
    """引擎状态响应"""
    engine_version: str = "v2.0"
    status: str = "running"
    layers: list[dict[str, Any]]
    cf_engines: dict[str, Any]
    capabilities: list[str]
    stats: dict[str, Any]


# ======================================================================
# 工具函数
# ======================================================================


def _desensitize_user(user: User, viewer_is_free: bool = True) -> dict:
    """对用户信息脱敏处理（复用 match.py 逻辑的简化版）"""
    if not viewer_is_free:
        return {
            "name": user.name,
            "phone": user.phone,
            "company": user.company,
            "title": user.title,
            "avatar": user.avatar,
        }
    name_masked = user.name[:1] + "**" if user.name and len(user.name) >= 1 else user.name
    company = user.company or ""
    company_masked = company[:2] + "**" if len(company) >= 2 else company
    return {
        "name": name_masked,
        "phone": "",
        "company": company_masked,
        "title": user.title,
        "avatar": user.avatar or "",
    }


def _is_paid_member(user: User) -> bool:
    """检查用户是否为付费会员"""
    from datetime import datetime
    if user.membership_tier in ("gold", "diamond", "board"):
        if user.membership_expires_at is None:
            return True
        return user.membership_expires_at > datetime.utcnow()
    return False


# ======================================================================
# API 端点
# ======================================================================


@router.post("/recommend", response_model=RecommendResponse)
async def v2_recommend(
    request: RecommendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """V2 每日推荐 — 使用五层综合评分

    基于 MatchEngineV2.get_daily_recommendations_v2()，
    可选集成协同过滤推荐结果。
    """
    # 1. V2 引擎推荐（五层评分）
    v2_results = await MatchEngineV2.get_daily_recommendations_v2(
        db=db,
        user_id=current_user.id,
        limit=request.limit,
        min_score=request.min_score,
    )

    results = []
    for item in v2_results:
        results.append({
            "user_id": item["user_id"],
            "user_name": item["user_name"],
            "user_company": item["user_company"],
            "user_title": item["user_title"],
            "user_avatar": item["user_avatar"],
            "score": item["score"],
            "tag_overlap": item["tag_overlap"],
            "vector_semantic": item["vector_semantic"],
            "tag_weight": item["tag_weight"],
            "industry_complement": item["industry_complement"],
            "attention_score": item["attention_score"],
            "common_tags": item.get("common_tags", []),
            "source": "v2_engine",
        })

    # 2. 可选：协同过滤推荐
    cf_results = []
    if request.include_cf:
        try:
            # ItemBasedCF
            item_cf = ItemBasedCF(min_interactions=1)
            await item_cf.build_similarity_matrix(db)
            cf_recs = await item_cf.recommend(
                user_id=current_user.id,
                limit=request.limit,
            )

            cf_user_ids = set(r.user_id for r in results)
            for rec in cf_recs:
                if rec.target_id not in cf_user_ids:
                    result_db = await db.execute(
                        __import__("sqlalchemy").select(User).where(User.id == rec.target_id)
                    )
                    user_obj = result_db.scalars().first()
                    if user_obj:
                        desensitized = _desensitize_user(
                            user_obj, not _is_paid_member(current_user)
                        )
                        cf_results.append({
                            "user_id": rec.target_id,
                            "user_name": desensitized["name"],
                            "user_company": desensitized["company"],
                            "user_title": user_obj.title,
                            "user_avatar": user_obj.avatar or "",
                            "score": rec.score,
                            "tag_overlap": 0.0,
                            "vector_semantic": 0.0,
                            "tag_weight": 0.0,
                            "industry_complement": 0.0,
                            "attention_score": 0.0,
                            "common_tags": [],
                            "source": "collaborative_filtering",
                            "reason": rec.reason,
                        })
        except Exception:
            # 协同过滤失败时静默降级
            pass

    # 合并结果
    all_results = results + cf_results
    all_results.sort(key=lambda x: x["score"], reverse=True)

    from datetime import datetime
    return {
        "data": all_results[:request.limit],
        "total": len(all_results),
        "has_more": len(all_results) > request.limit,
        "engine_version": "v2.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/diverse", response_model=DiverseRecommendResponse)
async def v2_diverse_recommend(
    request: DiverseRecommendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """多样性推荐 — V2混合搜索 + MMR多样性重排序

    使用 MatchEngineV2.hybrid_search_v2() 进行混合搜索，
    然后通过 MMR 算法对结果进行多样性重排序。
    """
    results = await MatchEngineV2.hybrid_search_v2(
        db=db,
        query_text=request.query,
        current_user_id=current_user.id,
        top_k=request.limit * 2,  # 先取更多候选，再MMR排序
        keyword_weight=request.keyword_weight,
        vector_weight=request.vector_weight,
        mmr_lambda=request.lambda_param,
        mmr_enabled=True,
    )

    # 脱敏处理
    viewer_is_free = not _is_paid_member(current_user)
    if viewer_is_free:
        for item in results:
            result_db = await db.execute(
                __import__("sqlalchemy").select(User).where(User.id == item["user_id"])
            )
            user_obj = result_db.scalars().first()
            if user_obj:
                masked = _desensitize_user(user_obj, viewer_is_free=True)
                item["user_name"] = masked["name"]
                item["user_company"] = masked["company"]

    # 计算多样性分数
    diversity_score = 0.0
    if results:
        mmr_engine = MMRDiversityEngine()
        diversity_score = await mmr_engine.compute_diversity(
            [r for r in results if "embedding" in r]
        )

    return {
        "data": results[:request.limit],
        "total": len(results),
        "diversity_score": round(diversity_score, 4),
        "engine_version": "v2.0",
    }


@router.post("/explain", response_model=ExplainResponse)
async def v2_explain_match(
    request: ExplainRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """匹配理由解释 — 返回四头注意力匹配详情

    调用 MatchEngineV2.compute_similarity_v2() 获取五层评分，
    同时使用 AttentionMatcher.explain() 获取各头注意力细节。
    """
    # 1. 检查目标用户存在
    result = await db.execute(
        __import__("sqlalchemy").select(User).where(User.id == request.target_user_id)
    )
    target_user = result.scalars().first()
    if target_user is None:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    # 2. V2 综合评分
    v2_result = await MatchEngineV2.compute_similarity_v2(
        db, current_user.id, request.target_user_id,
    )

    # 3. 构建 UserFeatures 用于 AttentionMatcher.explain()
    provide_current = await MatchEngineV2._build_user_features(
        *(await _get_tag_vectors(db, current_user.id, request.target_user_id))
    )

    # 手动构建 AttentionMatcher 解释
    from app.services.matching_engine import MatchEngine

    provide_a = await MatchEngine._build_tag_vector(db, current_user.id, "provide")
    need_a = await MatchEngine._build_tag_vector(db, current_user.id, "need")
    provide_b = await MatchEngine._build_tag_vector(db, request.target_user_id, "provide")
    need_b = await MatchEngine._build_tag_vector(db, request.target_user_id, "need")

    features_a, features_b = MatchEngineV2._build_user_features(
        provide_a, need_a, provide_b, need_b
    )

    matcher = AttentionMatcher(temperature=0.8)
    explanation = await matcher.explain(features_a, features_b)

    # 4. 构建响应
    details = {
        head_name: ExplainDetail(
            attention=info["attention"],
            weight=info["weight"],
            contribution=info["contribution"],
        )
        for head_name, info in explanation["details"].items()
    }

    return ExplainResponse(
        score=v2_result["score"],
        details=details,
        availability=explanation["availability"],
        features={
            "user_a": {
                "id": current_user.id,
                "name": current_user.name,
                "industries": features_a.industries,
                "capabilities": features_a.capabilities,
                "regions": features_a.regions,
                "hotness": features_a.hotness,
            },
            "user_b": {
                "id": request.target_user_id,
                "name": target_user.name,
                "industries": features_b.industries,
                "capabilities": features_b.capabilities,
                "regions": features_b.regions,
                "hotness": features_b.hotness,
            },
        },
        v2_scores={
            "score": v2_result["score"],
            "tag_overlap": v2_result["tag_overlap"],
            "vector_semantic": v2_result["vector_semantic"],
            "tag_weight": v2_result["tag_weight"],
            "industry_complement": v2_result["industry_complement"],
            "attention_score": v2_result["attention_score"],
        },
    )


@router.get("/stats", response_model=EngineStatusResponse)
async def v2_engine_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """匹配引擎 V2 状态查询

    返回引擎各层能力状态、协同过滤引擎状态、能力清单等。
    """
    from datetime import datetime

    # 1. 五层评分权重
    layers = [
        {
            "name": "tag_overlap",
            "weight": 0.35,
            "description": "标签重叠评分 — 供需标签匹配度",
            "status": "active",
        },
        {
            "name": "vector_semantic",
            "weight": 0.25,
            "description": "语义相似度 — 向量语义匹配",
            "status": "active",
        },
        {
            "name": "tag_weight",
            "weight": 0.10,
            "description": "标签权重评分 — 标签兴趣强度匹配",
            "status": "active",
        },
        {
            "name": "industry_complement",
            "weight": 0.20,
            "description": "行业互补分析 — 10类行业供需映射",
            "status": "active",
        },
        {
            "name": "attention_score",
            "weight": 0.10,
            "description": "多头注意力匹配 — 行业/能力/地区/热度四头",
            "status": "active",
        },
    ]

    # 2. 协同过滤引擎状态
    cf_engines = {}
    try:
        item_cf = ItemBasedCF(min_interactions=1)
        await item_cf.build_similarity_matrix(db)
        cf_engines["item_based_cf"] = {
            "status": "active",
            "stats": item_cf.get_stats(),
        }
    except Exception as e:
        cf_engines["item_based_cf"] = {"status": "error", "message": str(e)}

    try:
        user_cf = UserBasedCF()
        matrix = await user_cf.build_similarity_matrix(db)
        cf_engines["user_based_cf"] = {
            "status": "active",
            "num_users": len(matrix.target_ids),
            "built_at": matrix.built_at,
        }
    except Exception as e:
        cf_engines["user_based_cf"] = {"status": "error", "message": str(e)}

    # 3. 能力清单
    capabilities = [
        "五层综合评分引擎 (V2)",
        "头部注意力匹配 (四头: 行业/能力/地区/热度)",
        "MMR 多样性重排序 (最大边际相关性)",
        "ItemBasedCF 协同过滤 (基于匹配历史)",
        "UserBasedCF 协同过滤 (基于标签相似度)",
        "行业互补分析 (10类行业供需映射)",
        "混合搜索 (关键词 + 向量语义)",
        "反馈闭环 (click/unlock/ignore/rate)",
        "在线学习 (Online Learning Pipeline)",
        "三塔模型推理 (User/Enterprise/Behavior Tower)",
        "向量语义搜索 (VectorSearchEngine)",
        "匹配理由可解释性 (Explain API)",
    ]

    # 4. 统计数据
    try:
        result_count = await db.execute(
            __import__("sqlalchemy").select(__import__("sqlalchemy").func.count(MatchRecord.id))
        )
        total_records = result_count.scalar() or 0
    except Exception:
        total_records = 0

    stats = {
        "total_match_records": total_records,
        "engine_layers": len(layers),
        "cf_engines_available": sum(
            1 for v in cf_engines.values() if v.get("status") == "active"
        ),
        "industry_categories": 10,
        "attention_heads": 4,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return {
        "engine_version": "v2.0",
        "status": "running",
        "layers": layers,
        "cf_engines": cf_engines,
        "capabilities": capabilities,
        "stats": stats,
    }


# ======================================================================
# 内部帮助函数
# ======================================================================


async def _get_tag_vectors(
    db: AsyncSession,
    user_a_id: int,
    user_b_id: int,
) -> tuple[dict[str, float], dict[str, float], dict[str, float], dict[str, float]]:
    """获取两个用户的标签向量"""
    from app.services.matching_engine import MatchEngine

    provide_a = await MatchEngine._build_tag_vector(db, user_a_id, "provide")
    need_a = await MatchEngine._build_tag_vector(db, user_a_id, "need")
    provide_b = await MatchEngine._build_tag_vector(db, user_b_id, "provide")
    need_b = await MatchEngine._build_tag_vector(db, user_b_id, "need")
    return provide_a, need_a, provide_b, need_b
