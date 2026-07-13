"""
六度人脉网络路由 — 关系图与信任传递

API路径: /api/business-card/six-degrees/*
响应格式: {code: number, message: string, data: any}

功能清单:
  - GET    /api/business-card/six-degrees/{user_id}/network         — 用户的人脉网络
  - GET    /api/business-card/six-degrees/path/{from_id}/{to_id}    — 两人之间的最短路径
  - POST   /api/business-card/six-degrees/relations                 — 创建关系
  - GET    /api/business-card/six-degrees/relations/{user_id}       — 用户的关系列表
  - PUT    /api/business-card/six-degrees/relations/{id}/trust       — 更新信任度
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.six_degrees import UserRelation, RelationEvent
from app.models.user import User
from app.routers.auth import get_current_user
from app.api_standards import raise_http_error, ErrorCode
from app.services.six_degrees import (
    find_shortest_path,
    find_network,
    create_relation,
    update_trust_score,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/business-card/six-degrees", tags=["六度人脉"])


# ── Pydantic 模型 ──────────────────────────────────────────────────────────────


class CreateRelationRequest(BaseModel):
    from_user_id: int = Field(..., description="关系发起方用户ID")
    to_user_id: int = Field(..., description="关系接收方用户ID")
    relation_type: str = Field("invite", description="关系类型: invite/contact/brochure/coop/refer")
    trust_score: float = Field(0.5, ge=0.0, le=1.0, description="初始信任度 0.0~1.0")
    bidirectional: bool = Field(False, description="是否为双向关系")
    source: str = Field("invite", description="来源: invite/import/wechat/manual")


class UpdateTrustRequest(BaseModel):
    trust_score: float = Field(..., ge=0.0, le=1.0, description="新的信任度 0.0~1.0")
    reason: str = Field("", max_length=200, description="变更原因")


class RelationResponse(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    relation_type: str
    label: Optional[str] = None
    trust_score: float
    interaction_count: int
    bidirectional: bool
    is_active: bool
    source: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class RelationEventResponse(BaseModel):
    id: int
    relation_id: int
    from_user_id: int
    to_user_id: int
    event_type: str
    old_trust_score: Optional[float] = None
    new_trust_score: Optional[float] = None
    reason: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


# ── 辅助函数 ──────────────────────────────────────────────────────────────────


def success(data: any = None, message: str = "操作成功") -> dict:
    """统一成功响应"""
    return {"code": 0, "message": message, "data": data}


def _serialize_relation(rel: UserRelation) -> dict:
    """序列化用户关系对象"""
    return {
        "id": rel.id,
        "from_user_id": rel.from_user_id,
        "to_user_id": rel.to_user_id,
        "relation_type": rel.relation_type,
        "label": rel.label,
        "trust_score": rel.trust_score,
        "interaction_count": rel.interaction_count,
        "bidirectional": rel.bidirectional,
        "is_active": rel.is_active,
        "source": rel.source,
        "source_detail": rel.source_detail,
        "created_at": rel.created_at.isoformat() if rel.created_at else "",
        "updated_at": rel.updated_at.isoformat() if rel.updated_at else "",
    }


def _serialize_event(event: RelationEvent) -> dict:
    """序列化关系事件对象"""
    return {
        "id": event.id,
        "relation_id": event.relation_id,
        "from_user_id": event.from_user_id,
        "to_user_id": event.to_user_id,
        "event_type": event.event_type,
        "old_trust_score": event.old_trust_score,
        "new_trust_score": event.new_trust_score,
        "reason": event.reason,
        "created_at": event.created_at.isoformat() if event.created_at else "",
    }


# ── API 端点 ────────────────────────────────────────────────────────────────────


@router.get("/{user_id}/network")
async def get_user_network(
    user_id: int,
    max_depth: int = Query(3, ge=1, le=6, description="人脉深度（1~6）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    min_trust: float = Query(0.0, ge=0.0, le=1.0, description="最小信任度阈值"),
    db: AsyncSession = Depends(get_db),
):
    """获取用户 N 度人脉网络"""
    result = await db.run_sync(
        lambda s: find_network(
            s,
            user_id=user_id,
            degree=max_depth,
            page=page,
            page_size=page_size,
            min_trust=min_trust,
        )
    )
    return success(result)


@router.get("/path/{from_user_id}/{to_user_id}")
async def get_path(
    from_user_id: int,
    to_user_id: int,
    max_depth: int = Query(6, ge=1, le=6, description="最大搜索深度（1~6）"),
    db: AsyncSession = Depends(get_db),
):
    """查找两个用户之间的最短六度路径"""
    if from_user_id == to_user_id:
        return success({
            "path": [from_user_id],
            "nodes": [],
            "length": 0,
            "trust_score": 1.0,
        })

    result = await db.run_sync(
        lambda s: find_shortest_path(
            s,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            max_depth=max_depth,
            use_cache=True,
        )
    )

    if result is None:
        raise_http_error(404, ErrorCode.NOT_FOUND, f"未找到 {from_user_id} 到 {to_user_id} 的人脉路径")

    return success(result)


@router.post("/relations")
async def create_user_relation(
    data: CreateRelationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建用户关系边（信任连接）"""
    if data.from_user_id == data.to_user_id:
        raise_http_error(400, ErrorCode.VALIDATION_ERROR, "不能与自己建立关系")

    # 检查目标用户是否存在
    result = await db.execute(select(User).where(User.id == data.to_user_id))
    if result.scalar_one_or_none() is None:
        raise_http_error(404, ErrorCode.NOT_FOUND, "目标用户不存在")

    relation = await db.run_sync(
        lambda s: create_relation(
            s,
            from_user_id=data.from_user_id,
            to_user_id=data.to_user_id,
            relation_type=data.relation_type,
            trust_score=data.trust_score,
            bidirectional=data.bidirectional,
            source=data.source,
        )
    )

    logger.info(
        "关系创建: id=%d, %d -> %d, type=%s, trust=%.2f",
        relation.id, data.from_user_id, data.to_user_id,
        data.relation_type, data.trust_score,
    )

    return success(_serialize_relation(relation), message="关系创建成功")


@router.get("/relations/{user_id}")
async def get_user_relations(
    user_id: int,
    is_active: Optional[bool] = Query(None, description="筛选有效/无效关系"),
    relation_type: Optional[str] = Query(None, description="筛选关系类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的关系列表（作为发起方或接收方）"""
    # 构建查询：用户作为 from_user_id 或 to_user_id 的关系
    conditions = [
        (UserRelation.from_user_id == user_id) | (UserRelation.to_user_id == user_id),
        not UserRelation.is_deleted,
    ]

    if is_active is not None:
        conditions.append(UserRelation.is_active == is_active)

    if relation_type:
        conditions.append(UserRelation.relation_type == relation_type)

    # 总数
    count_query = select(UserRelation.id).where(*conditions)
    total_result = await db.execute(count_query)
    total = len(total_result.all())

    # 分页
    query = (
        select(UserRelation)
        .where(*conditions)
        .order_by(UserRelation.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    relations = result.scalars().all()

    items = [_serialize_relation(rel) for rel in relations]

    return success({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.put("/relations/{relation_id}/trust")
async def update_relation_trust(
    relation_id: int,
    data: UpdateTrustRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新关系信任度"""
    try:
        relation = await db.run_sync(
            lambda s: update_trust_score(
                s,
                relation_id=relation_id,
                new_score=data.trust_score,
                reason=data.reason,
            )
        )
    except ValueError:
        raise_http_error(404, ErrorCode.NOT_FOUND, f"关系 {relation_id} 不存在")

    logger.info(
        "信任度更新: relation=%d, new_score=%.2f, reason=%s",
        relation_id, data.trust_score, data.reason or "无",
    )

    return success(_serialize_relation(relation), message="信任度更新成功")
