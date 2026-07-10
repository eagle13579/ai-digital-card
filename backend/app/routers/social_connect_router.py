"""A08 扫码建联路由 — 社交连接API端点

所有端点均以 /api/v1/scan/ 为前缀。
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.social_connect_service import SocialConnectService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scan", tags=["扫码建联"])


# ======================================================================
# 请求 / 响应模型
# ======================================================================


class ConnectRequest(BaseModel):
    """发起建联请求体"""
    target_user_id: int = Field(..., description="目标用户ID")
    message: str = Field("", description="附言消息")
    source: str = Field("qrcode", description="来源: qrcode / manual / share")


class ReviewRequest(BaseModel):
    """审核建联请求体"""
    approved: bool = Field(..., description="True=通过, False=拒绝")


class StrengthUpdateRequest(BaseModel):
    """更新关系强度请求体"""
    interaction_score: float = Field(1.0, ge=0.0, le=1.0, description="交互分数 (0.0 ~ 1.0)")


# ======================================================================
# 路由
# ======================================================================


@router.post("/connect")
async def request_connection(
    body: ConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发起扫码建联"""
    try:
        result = await SocialConnectService.request_connection(
            db=db,
            user_id=current_user.id,
            target_user_id=body.target_user_id,
            message=body.message,
            source=body.source,
        )
        return {
            "code": 0,
            "data": result,
            "message": "建联请求已发送",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/connect/{connection_id}/review")
async def review_connection(
    connection_id: str,
    body: ReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """审核建联请求"""
    try:
        result = await SocialConnectService.review_connection(
            db=db,
            connection_id=connection_id,
            user_id=current_user.id,
            approved=body.approved,
        )
        return {
            "code": 0,
            "data": result,
            "message": result["message"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/connections")
async def get_my_connections(
    status: str = Query("approved", description="筛选状态: approved / pending / rejected"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取我的连接列表"""
    result = await SocialConnectService.get_my_connections(
        db=db,
        user_id=current_user.id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return {
        "code": 0,
        "data": result,
        "message": "success",
    }


@router.get("/connections/pending")
async def get_pending_requests(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取待审核的建联请求（别人发给我的）"""
    result = await SocialConnectService.get_pending_requests(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return {
        "code": 0,
        "data": result,
        "message": "success",
    }


@router.get("/connections/path/{target_user_id}")
async def find_path(
    target_user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询到目标用户的触达路径（BFS，最多3度人脉）"""
    result = await SocialConnectService.find_path(
        db=db,
        user_id=current_user.id,
        target_user_id=target_user_id,
    )
    return {
        "code": 0,
        "data": result,
        "message": "success",
    }


# ======================================================================
# 人脉推荐 & 图谱统计 & 关系强度
# ======================================================================


@router.get("/connections/recommendations")
async def get_connection_recommendations(
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取可能认识的人推荐（二度人脉推荐）"""
    result = await SocialConnectService.get_connection_recommendations(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )
    return {
        "code": 0,
        "data": result,
        "message": "success",
    }


@router.get("/connections/stats")
async def get_social_graph_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取社交图谱统计（好友数、人脉覆盖、行业覆盖等）"""
    result = await SocialConnectService.get_social_graph_stats(
        db=db,
        user_id=current_user.id,
    )
    return {
        "code": 0,
        "data": result,
        "message": "success",
    }


@router.put("/connections/{connection_id}/strength")
async def update_connection_strength(
    connection_id: str = Path(..., description="建联记录ID"),
    body: StrengthUpdateRequest = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新关系强度"""
    try:
        result = await SocialConnectService.update_connection_strength(
            db=db,
            connection_id=connection_id,
            interaction_score=body.interaction_score,
        )
        return {
            "code": 0,
            "data": result,
            "message": "关系强度已更新",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
