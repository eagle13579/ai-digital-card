"""
AI数字名片 — 知识图谱 API 路由
================================
GET  /api/knowledge-graph/network/{user_id}  — 用户关系网络
GET  /api/knowledge-graph/insights/{user_id}  — 用户洞察分析
GET  /api/knowledge-graph/connect             — 连接推荐
POST /api/knowledge-graph/rebuild             — 重建知识图谱（管理员）
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge-graph", tags=["知识图谱"])


@router.get("/network/{user_id}")
async def get_user_network(
    user_id: int,
    depth: int = Query(2, ge=1, le=5, description="网络深度（跳数）"),
    db: AsyncSession = Depends(get_db),
):
    """获取指定用户的 ego 关系网络（自我中心知识图谱）"""
    graph = KnowledgeGraph(db)
    try:
        result = await graph.get_user_network(user_id, depth=depth)
        if result["central"] is None:
            raise HTTPException(status_code=404, detail="用户不在知识图谱中")
        return result
    except Exception as exc:
        logger.exception("获取用户网络失败 (user_id=%d)", user_id)
        raise HTTPException(status_code=500, detail=f"知识图谱查询失败: {exc}")


@router.get("/insights/{user_id}")
async def get_user_insights(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """分析指定用户在图谱中的位置、关系、影响力等洞察"""
    graph = KnowledgeGraph(db)
    try:
        insights = await graph.get_user_insights(user_id)
        if "error" in insights:
            raise HTTPException(status_code=404, detail=insights["error"])
        return insights
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("获取用户洞察失败 (user_id=%d)", user_id)
        raise HTTPException(status_code=500, detail=f"洞察分析失败: {exc}")


@router.get("/connect")
async def recommend_connections(
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
    min_score: float = Query(0.3, ge=0.0, le=5.0, description="最低推荐分数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """为当前登录用户推荐新的连接（基于知识图谱分析）"""
    graph = KnowledgeGraph(db)
    try:
        results = await graph.recommend_connections(
            user_id=current_user.id,
            limit=limit,
            min_score=min_score,
        )
        return {
            "user_id": current_user.id,
            "name": current_user.name,
            "recommendations": results,
            "total": len(results),
        }
    except Exception as exc:
        logger.exception("推荐连接失败 (user_id=%d)", current_user.id)
        raise HTTPException(status_code=500, detail=f"连接推荐失败: {exc}")


@router.post("/rebuild")
async def rebuild_graph(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """手动触发知识图谱重建（需要管理员权限）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可重建知识图谱")

    graph = KnowledgeGraph(db)
    try:
        result = await graph.build()
        return {
            "message": "知识图谱重建完成",
            "stats": result["stats"],
        }
    except Exception as exc:
        logger.exception("重建知识图谱失败")
        raise HTTPException(status_code=500, detail=f"重建失败: {exc}")
