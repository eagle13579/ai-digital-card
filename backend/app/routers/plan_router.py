"""定价表 + 订阅状态路由。

API路径（无 /api/v1/ 前缀）:
  - GET /api/plans              返回三档套餐: 划线价 + 年付价 + 权益列表
  - GET /api/me/subscription    返回当前用户套餐状态

响应格式: {code: number, message: string, data: any}（与 organization_router 一致）
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services import plan_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["定价-订阅"])


def success(data=None, message: str = "操作成功") -> dict:
    """统一成功响应"""
    return {"code": 0, "message": message, "data": data}


# ── 套餐列表 ─────────────────────────────────────────────────────────────


@router.get("/plans")
async def list_plans(db: AsyncSession = Depends(get_db)):
    """获取定价表 — 三档套餐（免费/Pro/企业），含划线价 + 年付价 + 权益列表。

    定价页公开访问，无需登录。
    """
    plans = await plan_service.get_plans(db)

    result = []
    for plan in plans:
        info = plan_service.plan_to_dict(plan)
        # 前端友好字段: 原价(划线价)与年付价、权益列表
        info["price_monthly_yuan"] = round(info["price_monthly"], 2)
        info["price_annual_yuan"] = round(info["price_annual"], 2)
        info["original_annual_yuan"] = round(info["original_annual"], 2)
        info["features"] = info.get("features") or []
        result.append(info)

    return success(
        {
            "plans": result,
            "currency": "CNY",
            "annual_discount_label": "年付8折",
            "annual_discount_ratio": plan_service.ANNUAL_DISCOUNT_RATIO,
        },
        message="获取套餐列表成功",
    )


# ── 我的订阅状态 ─────────────────────────────────────────────────────────


@router.get("/me/subscription")
async def my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的套餐状态。

    返回当前订阅关系 + 套餐信息；无订阅记录时返回免费套餐兜底。
    """
    sub, plan = await plan_service.get_user_plan(db, current_user.id)

    now = datetime.utcnow()
    plan_info = plan_service.plan_to_dict(plan) if plan else None

    if sub is not None:
        status = sub.status
        days_remaining = max(0, (sub.end_date - now).days) if sub.end_date else 0
        data = {
            "subscription_id": sub.id,
            "user_id": sub.user_id,
            "plan_id": sub.plan_id,
            "status": status,
            "start_date": sub.start_date.isoformat() if sub.start_date else None,
            "end_date": sub.end_date.isoformat() if sub.end_date else None,
            "days_remaining": days_remaining,
            "is_active": status == "active",
            "plan": plan_info,
        }
        return success(data, message="获取订阅状态成功")

    # 无订阅记录 — 免费套餐兜底
    return success(
        {
            "subscription_id": None,
            "user_id": current_user.id,
            "plan_id": plan.id if plan else None,
            "status": "free",
            "start_date": None,
            "end_date": None,
            "days_remaining": 0,
            "is_active": True,
            "plan": plan_info,
        },
        message="当前为免费套餐",
    )
