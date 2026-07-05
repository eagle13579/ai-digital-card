"""
会员 API — 查询状态 / 升级 / 定价
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.usage_service import get_user_usage, get_limits

router = APIRouter(prefix="/api/membership", tags=["会员"])

# ===================================================================
# 定价配置表
# ===================================================================

PRICING_CONFIG = {
    "free": {
        "name": "免费版",
        "price": 0,
        "currency": "CNY",
        "features": {
            "card": {"limit": 1, "label": "名片创建"},
            "ocr": {"limit": 3, "label": "OCR识别"},
            "visitor": {"limit": 5, "label": "访客记录"},
            "batch_import": {"limit": 10, "label": "批量导入"},
            "api": {"limit": 100, "label": "API调用"},
        },
    },
    "pro": {
        "name": "专业版",
        "price": 99,
        "currency": "CNY",
        "features": {
            "card": {"limit": -1, "label": "名片创建（无限）"},
            "ocr": {"limit": 1000, "label": "OCR识别"},
            "visitor": {"limit": -1, "label": "访客记录（无限）"},
            "batch_import": {"limit": 500, "label": "批量导入"},
            "api": {"limit": 5000, "label": "API调用"},
        },
    },
    "enterprise": {
        "name": "企业版",
        "price": 499,
        "currency": "CNY",
        "features": {
            "card": {"limit": -1, "label": "名片创建（无限）"},
            "ocr": {"limit": -1, "label": "OCR识别（无限）"},
            "visitor": {"limit": -1, "label": "访客记录（无限）"},
            "batch_import": {"limit": -1, "label": "批量导入（无限）"},
            "api": {"limit": -1, "label": "API调用（无限）"},
        },
    },
}

# ===================================================================
# Schemas
# ===================================================================


class MembershipStatusResponse(BaseModel):
    tier: str
    tier_name: str
    usage: dict
    limits: dict


class UpgradeRequest(BaseModel):
    tier: str  # "pro" | "enterprise"


class UpgradeResponse(BaseModel):
    success: bool
    message: str
    new_tier: str
    previous_tier: str


class PricingTierFeature(BaseModel):
    limit: int
    label: str


class PricingTier(BaseModel):
    name: str
    price: int
    currency: str
    features: dict[str, PricingTierFeature]


class PricingResponse(BaseModel):
    tiers: dict[str, PricingTier]


# ===================================================================
# Routes
# ===================================================================


@router.get("/status", response_model=MembershipStatusResponse)
async def get_membership_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的会员层级和使用情况。"""
    from app.services.usage_service import get_user_tier

    tier = get_user_tier(current_user)
    usage_data = await get_user_usage(current_user.id, db)

    tier_name = PRICING_CONFIG.get(tier, PRICING_CONFIG["free"])["name"]

    return MembershipStatusResponse(
        tier=tier,
        tier_name=tier_name,
        usage=usage_data.get("usage", {}),
        limits=usage_data.get("limits", {}),
    )


@router.post("/upgrade", response_model=UpgradeResponse)
async def upgrade_membership(
    req: UpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """升级会员层级（模拟）。（TODO: 接入真实支付流程）"""
    if req.tier not in PRICING_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的层级: {req.tier}。可选: {', '.join(PRICING_CONFIG.keys())}",
        )

    previous_tier = current_user.membership_tier

    # 层级映射: MECE 层级 → 原始层级
    mece_to_raw = {
        "free": "free",
        "pro": "gold",
        "enterprise": "diamond",
    }

    new_raw_tier = mece_to_raw.get(req.tier, "free")

    # 更新用户
    current_user.membership_tier = new_raw_tier
    now = datetime.utcnow()
    current_user.updated_at = now
    await db.commit()

    logger_msg = f"用户 {current_user.id} 升级成功: {previous_tier} → {new_raw_tier}"

    return UpgradeResponse(
        success=True,
        message=logger_msg,
        new_tier=req.tier,
        previous_tier=previous_tier,
    )


@router.get("/pricing", response_model=PricingResponse)
async def get_pricing():
    """返回定价配置表。"""
    return PricingResponse(tiers=PRICING_CONFIG)
