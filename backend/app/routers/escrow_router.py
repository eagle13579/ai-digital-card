"""
交易保障路由 — 对标 Alibaba Trade Assurance

API路径: /api/business-card/escrow/*
响应格式: {code: number, message: string, data: any}

功能清单:
  - POST   /api/business-card/escrow/deals               — 创建交易
  - GET    /api/business-card/escrow/deals                — 交易列表
  - GET    /api/business-card/escrow/deals/{id}           — 交易详情
  - PUT    /api/business-card/escrow/deals/{id}/status    — 更新状态
  - POST   /api/business-card/escrow/deals/{id}/release   — 释放付款
  - POST   /api/business-card/escrow/deals/{id}/dispute   — 发起争议
  - GET    /api/business-card/escrow/deals/{id}/disputes  — 争议列表
"""
import asyncio
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.api_standards import raise_http_error, ErrorCode
from app.services.escrow_service import (
    create_deal as escrow_create_deal,
    update_deal_status as escrow_update_deal_status,
    release_payment as escrow_release_payment,
    create_dispute as escrow_create_dispute,
    get_deal as escrow_get_deal,
    list_deals as escrow_list_deals,
    list_disputes as escrow_list_disputes,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/business-card/escrow", tags=["交易保障"])


# ── 辅助函数 ──────────────────────────────────────────────────────────────────


def success(data: Any = None, message: str = "操作成功") -> dict:
    """统一成功响应"""
    return {"code": 0, "message": message, "data": data}


async def _run_sync(fn, *args, **kwargs):
    """在 executor 中运行同步 escrow_service 函数"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


# ── Pydantic 模型 ──────────────────────────────────────────────────────────────


class DealCreate(BaseModel):
    buyer_id: int = Field(..., description="买方用户ID")
    seller_id: int = Field(..., description="卖方用户ID")
    amount: float = Field(..., gt=0, description="交易金额")
    title: str = Field("", max_length=255, description="交易标题/商品名称")
    description: str = Field("", max_length=2048, description="交易描述")
    milestones: Optional[list[dict[str, Any]]] = Field(
        None, description="里程碑列表，每项含 name(必填), due_date(可选), description(可选)"
    )


class DealStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=20, description="目标状态")


class DisputeCreate(BaseModel):
    initiator_id: int = Field(..., description="发起人用户ID")
    reason: str = Field(..., min_length=1, max_length=500, description="争议原因")
    description: str = Field("", max_length=2048, description="详细描述")
    evidence: Optional[list[str]] = Field(None, description="证据文件URL列表")


# ── API 端点 ────────────────────────────────────────────────────────────────────


@router.post("/deals")
async def create_deal(
    data: DealCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建交易保障订单"""
    sync_session = db.sync_session
    try:
        deal = await _run_sync(
            escrow_create_deal,
            sync_session,
            buyer_id=data.buyer_id,
            seller_id=data.seller_id,
            amount=data.amount,
            title=data.title,
            description=data.description,
            milestones=data.milestones,
        )
    except ValueError as e:
        raise_http_error(400, ErrorCode.VALIDATION_ERROR, str(e))

    logger.info("交易创建: id=%d, buyer=%d, seller=%d", deal.id, data.buyer_id, data.seller_id)
    return success(deal.to_dict(), message="交易创建成功")


@router.get("/deals")
async def list_deals(
    status: Optional[str] = Query(None, description="按状态过滤（pending/paid/fulfilled/completed/disputed/resolved/refunded/cancelled）"),
    skip: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页条数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的交易列表（作为买方或卖方）"""
    sync_session = db.sync_session
    deals = await _run_sync(
        escrow_list_deals,
        sync_session,
        user_id=current_user.id,
        status=status,
    )

    total = len(deals)
    paged = deals[skip : skip + limit]

    return success(
        {
            "items": [d.to_dict() for d in paged],
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    )


@router.get("/deals/{deal_id}")
async def get_deal(
    deal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取交易详情"""
    sync_session = db.sync_session
    deal = await _run_sync(escrow_get_deal, sync_session, deal_id=deal_id)
    if deal is None:
        raise_http_error(404, ErrorCode.NOT_FOUND, "交易不存在")

    # 权限校验：仅交易参与方可查看
    if deal.buyer_id != current_user.id and deal.seller_id != current_user.id:
        raise_http_error(403, ErrorCode.FORBIDDEN, "无权查看此交易")

    return success(deal.to_dict())


@router.put("/deals/{deal_id}/status")
async def update_deal_status(
    deal_id: int,
    data: DealStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新交易状态（含状态机校验）"""
    sync_session = db.sync_session
    try:
        deal = await _run_sync(
            escrow_update_deal_status,
            sync_session,
            deal_id=deal_id,
            new_status=data.status,
        )
    except ValueError as e:
        raise_http_error(400, ErrorCode.VALIDATION_ERROR, str(e))

    logger.info("交易状态更新: id=%d, status=%s", deal_id, data.status)
    return success(deal.to_dict(), message="交易状态已更新")


@router.post("/deals/{deal_id}/release")
async def release_payment(
    deal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """买方确认释放付款（状态机: fulfilled → completed）"""
    sync_session = db.sync_session
    try:
        deal = await _run_sync(
            escrow_release_payment,
            sync_session,
            deal_id=deal_id,
            actor_id=current_user.id,
        )
    except ValueError as e:
        raise_http_error(400, ErrorCode.VALIDATION_ERROR, str(e))

    logger.info("付款释放: deal_id=%d, buyer=%d", deal_id, current_user.id)
    return success(deal.to_dict(), message="付款已释放")


@router.post("/deals/{deal_id}/dispute")
async def create_dispute(
    deal_id: int,
    data: DisputeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发起争议"""
    sync_session = db.sync_session
    try:
        dispute = await _run_sync(
            escrow_create_dispute,
            sync_session,
            deal_id=deal_id,
            initiator_id=data.initiator_id,
            reason=data.reason,
            description=data.description,
            evidence=data.evidence,
        )
    except ValueError as e:
        raise_http_error(400, ErrorCode.VALIDATION_ERROR, str(e))

    logger.info("争议创建: dispute_id=%d, deal_id=%d", dispute.id, deal_id)
    return success(dispute.to_dict(), message="争议已发起")


@router.get("/deals/{deal_id}/disputes")
async def list_disputes(
    deal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定交易的所有争议列表"""
    sync_session = db.sync_session
    disputes = await _run_sync(
        escrow_list_disputes,
        sync_session,
        deal_id=deal_id,
    )

    return success([d.to_dict() for d in disputes])
