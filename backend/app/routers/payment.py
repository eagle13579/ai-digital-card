"""支付 API — 下单 / 回调 / 查询。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.payment import PaymentOrder, EnterpriseSubscription
from app.models.user import User
from app.utils.formatting import format_currency, format_date
from app.payment import (
    CallbackParams,
    MembershipTier,
    OrderRequest,
    PaymentChannel,
    PaymentProvider,
    PaymentStatus,
    ProductConfig,
    get_product,
)
from app.payment.alipay import AlipayProvider
from app.payment.wechat import WeChatPayProvider
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/payment", tags=["支付"])


# ── 支付渠道注册 ─────────────────────────────────────────────────────

_providers: dict[PaymentChannel, PaymentProvider] = {}


def _get_provider(channel: PaymentChannel) -> PaymentProvider:
    """获取支付渠道实例（懒加载）"""
    if channel not in _providers:
        if channel == PaymentChannel.WECHAT:
            _providers[channel] = WeChatPayProvider()
        elif channel == PaymentChannel.ALIPAY:
            _providers[channel] = AlipayProvider()
        else:
            raise HTTPException(status_code=400, detail=f"不支持的支付渠道: {channel}")
    return _providers[channel]


# ── Schemas ─────────────────────────────────────────────────────────

class CreateOrderRequest(BaseModel):
    tier: MembershipTier = Field(..., description="会员等级: gold / diamond / board")
    channel: PaymentChannel = Field(..., description="支付渠道: wechat / alipay")
    openid: str = Field(default="", description="微信 openid（微信支付必填）")


class CreateOrderResponse(BaseModel):
    order_no: str
    pay_info: dict
    status: str
    total_cents: int
    total_formatted: str = ""


class OrderStatusResponse(BaseModel):
    order_no: str
    channel: str
    channel_order_no: str
    status: str
    total_cents: int
    total_formatted: str = ""
    tier: str
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


# ── API ─────────────────────────────────────────────────────────────

@router.post("/create", response_model=CreateOrderResponse)
async def create_order(
    req: CreateOrderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建支付订单"""
    # 验证会员等级
    if req.tier == MembershipTier.FREE:
        raise HTTPException(status_code=400, detail="免费会员无需购买")

    # 检查是否有未支付的相同等级订单
    existing = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.user_id == user.id,
            PaymentOrder.membership_tier == req.tier.value,
            PaymentOrder.status == PaymentStatus.PENDING.value,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"您已有未支付的{req.tier.value}订单，请先完成支付")

    product = get_product(req.tier)

    # 调用支付渠道
    provider = _get_provider(req.channel)
    order_req = OrderRequest(
        user_id=user.id,
        tier=req.tier,
        channel=req.channel,
        openid=req.openid,
    )

    order_resp = await provider.create_order(order_req)

    if order_resp.status == PaymentStatus.FAILED:
        raise HTTPException(
            status_code=502,
            detail=order_resp.pay_info.get("error", "支付渠道下单失败"),
        )

    # 保存订单到数据库
    pay_order = PaymentOrder(
        order_no=order_resp.order_no,
        user_id=user.id,
        membership_tier=req.tier.value,
        channel=req.channel.value,
        channel_order_no=order_resp.channel_order_no,
        status=order_resp.status.value,
        total_cents=order_resp.total_cents or product.price_cents,
    )
    db.add(pay_order)
    await db.commit()

    return CreateOrderResponse(
        order_no=order_resp.order_no,
        pay_info=order_resp.pay_info,
        status=order_resp.status.value,
        total_cents=pay_order.total_cents,
        total_formatted=format_currency(pay_order.total_cents / 100, "CNY", "zh-CN"),
    )


@router.post("/notify/{channel}")
async def payment_callback(
    channel: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """支付渠道异步回调"""
    if channel not in ("wechat", "alipay"):
        raise HTTPException(status_code=400, detail="不支持的支付渠道")

    pay_channel = PaymentChannel(channel)
    provider = _get_provider(pay_channel)

    raw_body = await request.body()
    callback_params = CallbackParams(
        channel=pay_channel,
        raw_body=raw_body,
        raw_headers=dict(request.headers),
        query_params=dict(request.query_params),
    )

    result = await provider.verify_callback(callback_params)

    if not result.valid:
        # 支付宝要求返回 success 字符串
        if channel == "alipay":
            return {"code": "FAIL", "msg": result.error_msg or "签名验证失败"}
        return {"return_code": "FAIL", "return_msg": result.error_msg or "签名验证失败"}

    # 更新订单状态
    order_no = result.order_no
    order_query = select(PaymentOrder).where(PaymentOrder.order_no == order_no)
    order_result = await db.execute(order_query)
    pay_order = order_result.scalar_one_or_none()

    if pay_order and pay_order.status != PaymentStatus.SUCCESS.value:
        pay_order.status = PaymentStatus.SUCCESS.value
        pay_order.channel_order_no = result.channel_order_no or pay_order.channel_order_no
        pay_order.paid_at = result.paid_at or datetime.utcnow()
        pay_order.raw_callback = json.dumps(
            {"body": raw_body.decode("utf-8", errors="replace"), "headers": dict(request.headers)},
            ensure_ascii=False,
        )

        # 更新用户会员信息
        user_query = select(User).where(User.id == pay_order.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if user:
            tier = MembershipTier(pay_order.membership_tier)
            product = get_product(tier)
            user.membership_tier = tier.value
            user.membership_expires_at = datetime.utcnow() + timedelta(days=product.duration_days)
            user.unlock_quota = product.quota
            user.quota_reset_at = datetime.utcnow() + timedelta(days=30)

        await db.commit()

    # 返回渠道要求的成功响应
    if channel == "alipay":
        return {"code": "SUCCESS", "msg": "支付通知处理成功"}
    return {"return_code": "SUCCESS", "return_msg": "OK"}


@router.get("/query/{order_no}", response_model=OrderStatusResponse)
async def query_order(
    order_no: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询订单状态"""
    order_query = select(PaymentOrder).where(PaymentOrder.order_no == order_no)
    result = await db.execute(order_query)
    pay_order = result.scalar_one_or_none()

    if not pay_order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if pay_order.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权查看该订单")

    return OrderStatusResponse(
        order_no=pay_order.order_no,
        channel=pay_order.channel,
        channel_order_no=pay_order.channel_order_no,
        status=pay_order.status,
        total_cents=pay_order.total_cents,
        total_formatted=format_currency(pay_order.total_cents / 100, "CNY", "zh-CN"),
        tier=pay_order.membership_tier,
        paid_at=pay_order.paid_at,
        created_at=pay_order.created_at,
    )


@router.get("/orders", response_model=list[OrderStatusResponse])
async def list_orders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询当前用户的订单列表"""
    result = await db.execute(
        select(PaymentOrder)
        .where(PaymentOrder.user_id == user.id)
        .order_by(PaymentOrder.created_at.desc())
    )
    orders = result.scalars().all()

    return [
        OrderStatusResponse(
            order_no=o.order_no,
            channel=o.channel,
            channel_order_no=o.channel_order_no,
            status=o.status,
            total_cents=o.total_cents,
            total_formatted=format_currency(o.total_cents / 100, "CNY", "zh-CN"),
            tier=o.membership_tier,
            paid_at=o.paid_at,
            created_at=o.created_at,
        )
        for o in orders
    ]


@router.get("/products")
async def list_products():
    """获取定价列表"""
    from app.payment import PRODUCTS

    return {
        "products": [
            {
                "tier": p.tier.value,
                "name_cn": p.name_cn,
                "name_en": p.name_en,
                "price_cents": p.price_cents,
                "price_yuan": f"{p.price_cents / 100:.2f}",
                "price_formatted": format_currency(p.price_cents / 100, "CNY", "zh-CN"),
                "duration_days": p.duration_days,
                "description_cn": p.description_cn,
                "description_en": p.description_en,
                "quota": p.quota,
            }
            for p in PRODUCTS.values()
        ]
    }


# ── 企业版 API ──────────────────────────────────────────────────────────


class EnterprisePlanResponse(BaseModel):
    tier: str
    name_cn: str
    name_en: str
    price: int | str
    price_yuan: str
    price_formatted: str = ""
    seats: int | str
    features: list[str]


class SubscribeEnterpriseRequest(BaseModel):
    tier: str = Field(..., description="企业版等级: starter/business/enterprise")
    company_name: str = Field(..., description="企业名称")
    seats: int = Field(default=5, description="席位数量")
    auto_renew: bool = Field(default=True, description="是否自动续费")


class EnterpriseSubscriptionResponse(BaseModel):
    id: int
    company_name: str
    seats: int
    tier: str
    start_date: datetime
    end_date: datetime
    auto_renew: bool
    status: str
    features: dict

    class Config:
        from_attributes = True


@router.get("/enterprise/plans", response_model=list[EnterprisePlanResponse])
async def list_enterprise_plans():
    """获取企业版定价列表"""
    from app.payment import ENTERPRISE_PRODUCT

    result = []
    for tier, plan in ENTERPRISE_PRODUCT.items():
        item = EnterprisePlanResponse(tier=tier, **plan)
        if isinstance(plan["price"], int):
            item.price_formatted = format_currency(plan["price"] / 100, "CNY", "zh-CN")
        else:
            item.price_formatted = plan["price"]
        result.append(item)
    return result


@router.post("/enterprise/subscribe", response_model=EnterpriseSubscriptionResponse)
async def subscribe_enterprise(
    req: SubscribeEnterpriseRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """开通/升级企业版订阅"""
    from app.payment import ENTERPRISE_PRODUCT

    # 验证等级
    if req.tier not in ENTERPRISE_PRODUCT:
        raise HTTPException(status_code=400, detail=f"不支持的企业版等级: {req.tier}")

    plan = ENTERPRISE_PRODUCT[req.tier]
    if isinstance(plan["seats"], int) and req.seats > plan["seats"]:
        raise HTTPException(
            status_code=400,
            detail=f"{req.tier} 版本最多 {plan['seats']} 个席位，如需更多请升级企业版",
        )

    # 检查是否已有订阅
    existing_result = await db.execute(
        select(EnterpriseSubscription).where(
            EnterpriseSubscription.user_id == user.id,
            EnterpriseSubscription.status.in_(["active", "cancelled"]),
        ).order_by(EnterpriseSubscription.created_at.desc())
    )
    existing = existing_result.scalars().first()

    now = datetime.utcnow()
    end_date = now.replace(year=now.year + 1)  # 默认1年

    if existing:
        # 升级现有订阅
        existing.tier = req.tier
        existing.company_name = req.company_name
        existing.seats = req.seats
        existing.auto_renew = req.auto_renew
        existing.end_date = end_date
        existing.status = "active"
        existing.features = {
            "features": plan["features"],
            "sso": True,
            "custom_domain": True,
            "api_quota": "advanced",
            "dedicated_support": True,
            "sla": True,
        }
        sub = existing
    else:
        # 新建订阅
        sub = EnterpriseSubscription(
            user_id=user.id,
            company_name=req.company_name,
            seats=req.seats,
            tier=req.tier,
            start_date=now,
            end_date=end_date,
            auto_renew=req.auto_renew,
            status="active",
            features={
                "features": plan["features"],
                "sso": True,
                "custom_domain": True,
                "api_quota": "advanced",
                "dedicated_support": True,
                "sla": True,
            },
        )
        db.add(sub)

    await db.commit()
    await db.refresh(sub)
    return sub


@router.get("/enterprise/subscription", response_model=EnterpriseSubscriptionResponse)
async def get_enterprise_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询当前用户的企业版订阅"""
    result = await db.execute(
        select(EnterpriseSubscription).where(
            EnterpriseSubscription.user_id == user.id,
            EnterpriseSubscription.status == "active",
        ).order_by(EnterpriseSubscription.created_at.desc())
    )
    sub = result.scalars().first()
    if not sub:
        raise HTTPException(status_code=404, detail="未找到活跃的企业版订阅")
    return sub


@router.put("/enterprise/cancel", response_model=EnterpriseSubscriptionResponse)
async def cancel_enterprise_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消企业版订阅"""
    result = await db.execute(
        select(EnterpriseSubscription).where(
            EnterpriseSubscription.user_id == user.id,
            EnterpriseSubscription.status == "active",
        ).order_by(EnterpriseSubscription.created_at.desc())
    )
    sub = result.scalars().first()
    if not sub:
        raise HTTPException(status_code=404, detail="未找到活跃的企业版订阅")

    sub.status = "cancelled"
    sub.auto_renew = False
    await db.commit()
    await db.refresh(sub)
    return sub
