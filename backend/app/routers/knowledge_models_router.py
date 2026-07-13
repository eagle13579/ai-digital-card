"""
心智模型 (Knowledge Models) — RESTful API 路由
=============================================
GET    /api/knowledge-models           — 获取所有心智模型（支持 ?category= 过滤）
GET    /api/knowledge-models/categories — 分类统计
GET    /api/knowledge-models/{model_id} — 按 model_id 获取单个模型
POST   /api/knowledge-models/sync       — 同步到 gaia_knowledge 表
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.ai.knowledge_model_service import get_knowledge_model_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge-models", tags=["心智模型"])


# ======================================================================
# Pydantic Schemas
# ======================================================================


class KnowledgeModelResponse(BaseModel):
    """心智模型响应模型"""
    id: int
    model_id: str
    category: str
    name: str
    source: str
    source_ref: str | None = None
    content: str
    tags: dict | None = None
    confidence: float
    version: str
    is_active: bool
    vector_embedded: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CategoryStatsItem(BaseModel):
    """分类统计项"""
    category: str
    count: int
    avg_confidence: float


class SyncResult(BaseModel):
    """同步结果"""
    synced: int
    skipped: int
    total: int


class ListResponse(BaseModel):
    """列表响应包装"""
    code: int = 200
    message: str = "ok"
    data: list[KnowledgeModelResponse]
    total: int


class CategoryResponse(BaseModel):
    """分类统计响应包装"""
    code: int = 200
    message: str = "ok"
    data: list[CategoryStatsItem]


class DetailResponse(BaseModel):
    """单个模型响应包装"""
    code: int = 200
    message: str = "ok"
    data: KnowledgeModelResponse


class SyncResponse(BaseModel):
    """同步响应包装"""
    code: int = 200
    message: str = "ok"
    data: SyncResult


# ======================================================================
# Helper: 将 ORM 模型转为 dict（兼容 Pydantic v2）
# ======================================================================


def _model_to_dict(model: Any) -> dict[str, Any]:
    """将 SQLAlchemy 模型转为可序列化的字典"""
    return {
        "id": model.id,
        "model_id": model.model_id,
        "category": model.category,
        "name": model.name,
        "source": model.source,
        "source_ref": model.source_ref,
        "content": model.content,
        "tags": model.tags,
        "confidence": model.confidence,
        "version": model.version,
        "is_active": model.is_active,
        "vector_embedded": model.vector_embedded,
        "created_at": str(model.created_at) if model.created_at else "",
        "updated_at": str(model.updated_at) if model.updated_at else "",
    }


# ======================================================================
# API Endpoints
# ======================================================================


@router.get("", response_model=ListResponse)
async def list_knowledge_models(
    category: str | None = Query(None, description="按分类过滤（可选）"),
    db: AsyncSession = Depends(get_db),
):
    """获取所有心智模型列表

    支持可选的 ?category= 参数按分类过滤，默认只返回激活状态的模型。

    Args:
        category: 分类过滤（可选），如 design_system、ui_principle 等
        db: 数据库会话

    Returns:
        心智模型列表及总数
    """
    service = get_knowledge_model_service()
    try:
        models = await service.get_all_models(db, category=category, active_only=True)
        items = [_model_to_dict(m) for m in models]
        return {
            "code": 200,
            "message": "ok",
            "data": items,
            "total": len(items),
        }
    except Exception as exc:
        logger.exception("获取心智模型列表失败")
        raise HTTPException(status_code=500, detail=f"查询失败: {exc}")


@router.get("/categories", response_model=CategoryResponse)
async def list_categories(
    db: AsyncSession = Depends(get_db),
):
    """获取心智模型的分类统计

    返回每个分类下的模型数量和平均置信度。

    Args:
        db: 数据库会话

    Returns:
        分类统计列表
    """
    service = get_knowledge_model_service()
    try:
        stats = await service.get_categories(db)
        return {
            "code": 200,
            "message": "ok",
            "data": stats,
        }
    except Exception as exc:
        logger.exception("获取分类统计失败")
        raise HTTPException(status_code=500, detail=f"分类统计查询失败: {exc}")


@router.get("/{model_id}", response_model=DetailResponse)
async def get_knowledge_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
):
    """按 model_id 获取单个心智模型

    Args:
        model_id: 模型编码，如 FD-M01
        db: 数据库会话

    Returns:
        心智模型详情

    Raises:
        HTTPException 404: 模型不存在
        HTTPException 500: 查询异常
    """
    service = get_knowledge_model_service()
    try:
        model = await service.get_model_by_id(db, model_id)
        if model is None:
            raise HTTPException(
                status_code=404,
                detail=f"心智模型 '{model_id}' 不存在",
            )
        return {
            "code": 200,
            "message": "ok",
            "data": _model_to_dict(model),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("获取心智模型失败 (model_id=%s)", model_id)
        raise HTTPException(status_code=500, detail=f"查询失败: {exc}")


@router.post("/sync", response_model=SyncResponse)
async def sync_knowledge_models(
    db: AsyncSession = Depends(get_db),
):
    """将心智模型同步到 gaia_knowledge 表

    将 knowledge_models 表中激活的模型同步到 gaia_knowledge 表，
    供盖娅进化大脑进行向量化和训练使用。已同步的记录不会重复添加。

    Args:
        db: 数据库会话

    Returns:
        同步结果：新增数、跳过数、总计
    """
    service = get_knowledge_model_service()
    try:
        result = await service.sync_to_gaia_knowledge(db)
        await db.commit()
        logger.info(
            "心智模型同步完成: synced=%d, skipped=%d, total=%d",
            result["synced"],
            result["skipped"],
            result["total"],
        )
        return {
            "code": 200,
            "message": "同步完成",
            "data": result,
        }
    except Exception as exc:
        await db.rollback()
        logger.exception("心智模型同步失败")
        raise HTTPException(status_code=500, detail=f"同步失败: {exc}")
