"""资源平台商业化路由 — 平台创建/加入/商机/商业报告 API"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.resource_platform_service import ResourcePlatformService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/platforms", tags=["资源平台"])


# ======================================================================
# 请求 / 响应模型
# ======================================================================


class CreatePlatformRequest(BaseModel):
    """创建平台请求体"""
    name: str = Field(..., min_length=1, max_length=100, description="平台名称")
    annual_fee: int = Field(0, ge=0, description="年费(分)")
    description: str = Field("", max_length=2000, description="平台描述")
    member_limit: int = Field(1000, ge=1, le=100000, description="成员上限")


class UpdatePlatformRequest(BaseModel):
    """更新平台请求体"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="平台名称")
    description: Optional[str] = Field(None, max_length=2000, description="平台描述")
    annual_fee: Optional[int] = Field(None, ge=0, description="年费(分)")
    member_limit: Optional[int] = Field(None, ge=1, le=100000, description="成员上限")


class JoinPlatformResponse(BaseModel):
    """加入平台响应"""
    id: int
    platform_id: int
    user_id: int
    role: str
    joined_at: int
    annual_fee: int = 0
    annual_fee_required: bool = False


class CreateOpportunityRequest(BaseModel):
    """发布商机请求体"""
    title: str = Field(..., min_length=1, max_length=200, description="商机标题")
    description: str = Field("", max_length=5000, description="商机描述")
    industry: str = Field("", max_length=50, description="行业")
    city: str = Field("", max_length=50, description="城市")
    budget: int = Field(0, ge=0, description="预算(分)")


class AnnualFeeOrderRequest(BaseModel):
    """年费支付订单请求体"""
    channel: str = Field("wechat", description="支付渠道: wechat/alipay")


class AnnualFeeConfirmRequest(BaseModel):
    """年费支付确认请求体"""
    order_no: str = Field(..., description="内部订单号")
    channel_order_no: str = Field("", description="渠道订单号（模拟）")


# ======================================================================
# 统一响应包装
# ======================================================================


def ok(data=None, message="ok"):
    """统一成功响应"""
    return {"code": 0, "data": data, "message": message}


def fail(message: str, status_code: int = 400):
    """统一错误响应（抛出 HTTPException）"""
    raise HTTPException(status_code=status_code, detail={"code": -1, "data": None, "message": message})


# ======================================================================
# 路由
# ======================================================================


@router.post("")
async def create_platform(
    body: CreatePlatformRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建资源平台（创建者自动成为秘书长）"""
    try:
        result = await ResourcePlatformService.create_platform(
            db=db,
            name=body.name,
            annual_fee=body.annual_fee,
            creator_id=current_user.id,
            description=body.description,
            member_limit=body.member_limit,
        )
        return ok(data=result, message="平台创建成功")
    except ValueError as e:
        fail(str(e))


@router.get("")
async def list_platforms(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """平台推荐列表（按成员数排序）"""
    result = await ResourcePlatformService.get_platforms(
        db=db,
        page=page,
        page_size=page_size,
    )
    return ok(data=result)


@router.get("/{platform_id}")
async def get_platform(
    platform_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """平台详情（含成员数/商机数统计）"""
    result = await ResourcePlatformService.get_platform(db=db, platform_id=platform_id)
    if result is None:
        fail("平台不存在", status_code=404)
    return ok(data=result)


@router.put("/{platform_id}")
async def update_platform(
    platform_id: int,
    body: UpdatePlatformRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新平台信息（仅秘书长可操作）"""
    try:
        update_kwargs = body.model_dump(exclude_none=True)
        if not update_kwargs:
            fail("没有要更新的字段")

        result = await ResourcePlatformService.update_platform(
            db=db,
            platform_id=platform_id,
            user_id=current_user.id,
            **update_kwargs,
        )
        if result is None:
            fail("平台不存在", status_code=404)
        return ok(data=result, message="平台更新成功")
    except PermissionError as e:
        fail(str(e), status_code=403)
    except ValueError as e:
        fail(str(e))


@router.post("/{platform_id}/join")
async def join_platform(
    platform_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """加入平台"""
    try:
        result = await ResourcePlatformService.join_platform(
            db=db,
            platform_id=platform_id,
            user_id=current_user.id,
        )
        return ok(data=result, message="加入平台成功")
    except ValueError as e:
        fail(str(e))


@router.get("/{platform_id}/members")
async def list_members(
    platform_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """成员列表（按角色排序）"""
    result = await ResourcePlatformService.get_members(
        db=db,
        platform_id=platform_id,
        page=page,
        page_size=page_size,
    )
    return ok(data=result)


@router.get("/{platform_id}/report")
async def get_platform_report(
    platform_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """商业报告（城市/行业覆盖率 + 成员资源排名）"""
    result = await ResourcePlatformService.get_management_data(
        db=db,
        platform_id=platform_id,
    )
    if result is None:
        fail("平台不存在", status_code=404)
    return ok(data=result)


@router.post("/{platform_id}/opportunities")
async def create_opportunity(
    platform_id: int,
    body: CreateOpportunityRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发布商机（仅平台成员可发布）"""
    try:
        result = await ResourcePlatformService.create_opportunity(
            db=db,
            platform_id=platform_id,
            creator_id=current_user.id,
            title=body.title,
            description=body.description,
            industry=body.industry,
            city=body.city,
            budget=body.budget,
        )
        return ok(data=result, message="商机发布成功")
    except ValueError as e:
        fail(str(e))


@router.get("/{platform_id}/opportunities")
async def list_opportunities(
    platform_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    city: Optional[str] = Query(None, description="城市筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """商机列表（支持行业/城市/状态筛选）"""
    result = await ResourcePlatformService.get_opportunities(
        db=db,
        platform_id=platform_id,
        page=page,
        page_size=page_size,
        industry=industry,
        city=city,
        status=status,
    )
    return ok(data=result)


# ══════════════════════════════════════════════════════════════════════════
# 年费支付（资源平台→AI名片订阅打通）
# ══════════════════════════════════════════════════════════════════════════


@router.post("/{platform_id}/annual-fee/order")
async def create_annual_fee_order(
    platform_id: int,
    body: AnnualFeeOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建年费支付订单 — 加入付费资源平台后，通过此接口支付年费

    支付完成后，用户获得该资源平台为期1年的付费会员身份。
    """
    try:
        result = await ResourcePlatformService.create_annual_fee_order(
            db=db,
            platform_id=platform_id,
            user_id=current_user.id,
            channel=body.channel,
        )
        return ok(data=result, message="年费订单创建成功")
    except ValueError as e:
        fail(str(e))


@router.post("/{platform_id}/annual-fee/confirm")
async def confirm_annual_fee_payment(
    platform_id: int,
    body: AnnualFeeConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """确认年费支付（模拟支付回调）

    支付成功后自动创建 EnterpriseSubscription 记录。
    """
    try:
        result = await ResourcePlatformService.confirm_annual_fee_payment(
            db=db,
            order_no=body.order_no,
            channel_order_no=body.channel_order_no,
        )
        return ok(data=result, message="年费支付确认成功")
    except ValueError as e:
        fail(str(e))
