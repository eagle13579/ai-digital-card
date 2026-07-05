"""订阅管理路由 — 试用/升级/降级/套餐查询完整漏斗 + 到期通知 + 自助取消/退款。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.subscription_service import (
    PLANS,
    PlanConfig,
    TRIAL_DAYS,
    TRIAL_TIER,
    can_downgrade,
    can_upgrade,
    downgrade_subscription,
    get_current_subscription,
    get_plan,
    get_trial_status,
    start_trial,
    upgrade_subscription,
)
from app.services.subscription_notifier import check_and_notify
from app.services.subscription_cancel import (
    CANCEL_REASON_LABELS,
    CancelReason,
    cancel_at_period_end,
    cancel_immediate,
)
from app.services.ab_pricing import (
    get_experiment_status,
    list_experiments,
    start_experiment,
)

router = APIRouter(prefix="/api/v1/subscription", tags=["订阅管理"])


# ── 响应模型 ─────────────────────────────────────────────────────────────


class PlanFeatureResponse(BaseModel):
    name: str
    description: str
    enabled: bool = True


class PlanResponse(BaseModel):
    tier: str
    name_cn: str
    name_en: str
    price_cents: int
    price_yuan: str
    interval: str
    features: list[PlanFeatureResponse]
    feature_tags: list[str]
    quota_per_month: int
    max_seats: int
    trial_days_allowed: bool
    is_recommended: bool = False


class CurrentSubscriptionResponse(BaseModel):
    id: int
    company_name: str
    seats: int
    tier: str
    start_date: datetime
    end_date: datetime
    auto_renew: bool
    status: str
    features: dict
    days_remaining: int = 0
    is_trial: bool = False

    class Config:
        from_attributes = True


class UpgradeRequest(BaseModel):
    target_tier: str = Field(..., description="目标套餐: standard / enterprise")
    company_name: str = Field(default="", description="企业名称（可选）")
    seats: int = Field(default=1, ge=1, le=100, description="席位数量")


class DowngradeRequest(BaseModel):
    target_tier: str = Field(..., description="目标套餐: free / standard")


class TrialStartRequest(BaseModel):
    company_name: str = Field(default="", description="企业名称（可选）")


class TrialStatusResponse(BaseModel):
    has_used_trial: bool
    is_active_trial: bool
    trial_start: Optional[str] = None
    trial_end: Optional[str] = None
    status: str = "none"
    tier: Optional[str] = None
    remaining_days: int = 0
    features: Optional[dict] = None
    converted_to: Optional[str] = None
    trial_ended_at: Optional[str] = None


class SubscriptionActionResponse(BaseModel):
    success: bool
    message: str
    subscription: CurrentSubscriptionResponse


# ── 到期通知模型 ─────────────────────────────────────────────────────────


class NotifyCheckResponse(BaseModel):
    checked: bool
    total_trials_count: int
    notifications_found: int
    notifications_sent: int
    notifications: list[dict]


# ── 取消/退款模型 ────────────────────────────────────────────────────────


class CancelRequest(BaseModel):
    reason: str = Field(default="", description="取消原因（CancelReason 枚举值）")
    reason_detail: str = Field(default="", description="补充说明（可选）")


class CancelReasonsResponse(BaseModel):
    reasons: list[dict]


class RefundInfo(BaseModel):
    refund_cents: int
    used_days: int
    total_days: int
    refund_ratio: float
    message: str


class CancelResponse(BaseModel):
    success: bool
    message: str
    subscription: CurrentSubscriptionResponse
    refund: Optional[RefundInfo] = None


# ── API ─────────────────────────────────────────────────────────────────


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(
    user: User = Depends(get_current_user),
):
    """获取所有套餐列表（含定价与功能对比）"""
    result = []
    for tier, plan in PLANS.items():
        is_recommended = tier == "standard"   # 推荐标准版
        result.append(
            PlanResponse(
                tier=plan.tier,
                name_cn=plan.name_cn,
                name_en=plan.name_en,
                price_cents=plan.price_cents,
                price_yuan=plan.price_yuan,
                interval=plan.interval,
                features=[
                    PlanFeatureResponse(
                        name=f.name,
                        description=f.description,
                        enabled=f.enabled,
                    )
                    for f in plan.features
                ],
                feature_tags=plan.feature_tags,
                quota_per_month=plan.quota_per_month,
                max_seats=plan.max_seats,
                trial_days_allowed=plan.trial_days_allowed,
                is_recommended=is_recommended,
            )
        )
    return result


@router.get("/current", response_model=CurrentSubscriptionResponse)
async def get_current(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询当前用户的订阅信息"""
    # 首先尝试获取 EnterpriseSubscription
    sub = await get_current_subscription(user, db)

    now = datetime.utcnow()

    if sub:
        days_remaining = max(0, (sub.end_date - now).days) if sub.end_date else 0
        is_trial = sub.status == "trial" or sub.features.get("is_trial", False)
        return CurrentSubscriptionResponse(
            id=sub.id,
            company_name=sub.company_name,
            seats=sub.seats,
            tier=sub.tier,
            start_date=sub.start_date,
            end_date=sub.end_date,
            auto_renew=sub.auto_renew,
            status=sub.status,
            features=sub.features,
            days_remaining=days_remaining,
            is_trial=is_trial,
        )

    # 没有订阅记录 — 返回基于 user.membership_tier 的免费版信息
    return CurrentSubscriptionResponse(
        id=0,
        company_name="",
        seats=1,
        tier=user.membership_tier or "free",
        start_date=now,
        end_date=now,
        auto_renew=False,
        status="free",
        features={
            "plan_tier": "free",
            "features": [f.description for f in PLANS["free"].features],
            "quota": PLANS["free"].quota_per_month,
        },
        days_remaining=0,
        is_trial=False,
    )


@router.post("/upgrade", response_model=SubscriptionActionResponse)
async def upgrade(
    req: UpgradeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """升级订阅套餐（免费→标准→企业）"""
    target = req.target_tier.lower()

    if target not in PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的套餐: {target}。可选: {', '.join(PLANS.keys())}",
        )

    plan = get_plan(target)
    if plan.price_cents == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="免费套餐无需升级",
        )

    # 检查当前订阅状态
    current = await get_current_subscription(user, db)
    current_tier = current.tier if current else "free"

    if current_tier == target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前已是 {plan.name_cn}，无需重复升级",
        )

    if not can_upgrade(current_tier, target):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持从 {current_tier} 升级到 {target}。升级路径: free → standard → enterprise",
        )

    try:
        sub = await upgrade_subscription(
            user=user,
            db=db,
            target_tier=target,
            company_name=req.company_name,
            seats=req.seats,
        )
        now = datetime.utcnow()
        days_remaining = max(0, (sub.end_date - now).days) if sub.end_date else 0
        return SubscriptionActionResponse(
            success=True,
            message=f"成功升级至 {plan.name_cn}！",
            subscription=CurrentSubscriptionResponse(
                id=sub.id,
                company_name=sub.company_name,
                seats=sub.seats,
                tier=sub.tier,
                start_date=sub.start_date,
                end_date=sub.end_date,
                auto_renew=sub.auto_renew,
                status=sub.status,
                features=sub.features,
                days_remaining=days_remaining,
                is_trial=False,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/downgrade", response_model=SubscriptionActionResponse)
async def downgrade(
    req: DowngradeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """降级订阅套餐"""
    target = req.target_tier.lower()

    if target not in PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的套餐: {target}",
        )

    current = await get_current_subscription(user, db)
    if not current:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有活跃的订阅可降级",
        )

    if not can_downgrade(current.tier, target):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持从 {current.tier} 降级到 {target}",
        )

    try:
        sub = await downgrade_subscription(
            user=user,
            db=db,
            target_tier=target,
        )
        now = datetime.utcnow()
        days_remaining = max(0, (sub.end_date - now).days) if sub.end_date else 0
        plan = get_plan(target)
        msg = f"已降级至 {plan.name_cn}，当前服务可用至 {sub.end_date.strftime('%Y-%m-%d')}" if target == "free" else f"已降级至 {plan.name_cn}"
        return SubscriptionActionResponse(
            success=True,
            message=msg,
            subscription=CurrentSubscriptionResponse(
                id=sub.id,
                company_name=sub.company_name,
                seats=sub.seats,
                tier=sub.tier,
                start_date=sub.start_date,
                end_date=sub.end_date,
                auto_renew=sub.auto_renew,
                status=sub.status,
                features=sub.features,
                days_remaining=days_remaining,
                is_trial=False,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/trial/start", response_model=SubscriptionActionResponse)
async def start_free_trial(
    req: TrialStartRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """开通14天免费试用（标准版）"""
    try:
        sub = await start_trial(
            user=user,
            db=db,
            company_name=req.company_name,
        )
        now = datetime.utcnow()
        days_remaining = max(0, (sub.end_date - now).days) if sub.end_date else 0
        return SubscriptionActionResponse(
            success=True,
            message=f"🎉 恭喜！您已成功开通 {TRIAL_DAYS} 天免费试用（标准版），截至 {sub.end_date.strftime('%Y-%m-%d')}",
            subscription=CurrentSubscriptionResponse(
                id=sub.id,
                company_name=sub.company_name,
                seats=sub.seats,
                tier=sub.tier,
                start_date=sub.start_date,
                end_date=sub.end_date,
                auto_renew=sub.auto_renew,
                status=sub.status,
                features=sub.features,
                days_remaining=days_remaining,
                is_trial=True,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/trial/status", response_model=TrialStatusResponse)
async def trial_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询当前用户的试用状态"""
    status_data = await get_trial_status(user, db)
    return TrialStatusResponse(
        has_used_trial=status_data.get("has_used_trial", False),
        is_active_trial=status_data.get("is_active_trial", False),
        trial_start=status_data.get("trial_start"),
        trial_end=status_data.get("trial_end"),
        status=status_data.get("status", "none"),
        tier=status_data.get("tier"),
        remaining_days=status_data.get("remaining_days", 0),
        features=status_data.get("features"),
        converted_to=status_data.get("converted_to"),
        trial_ended_at=status_data.get("trial_ended_at"),
    )


# ══════════════════════════════════════════════════════════════════════════
# 到期通知
# ══════════════════════════════════════════════════════════════════════════


@router.post("/notify/check", response_model=NotifyCheckResponse)
async def check_trial_notifications(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """手动触发试用到期检查，返回需要发送的通知列表。
    
    此端点支持:
      - 管理员/后台手动触发试用到期提醒
      - 返回所有即将到期的试用通知摘要
      - 通知会输出到日志（可对接站内信/邮件/短信通道）
    """
    # 仅允许管理员或特定角色触发
    if user.role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可执行到期检查",
        )

    result = await check_and_notify(db)
    return NotifyCheckResponse(
        checked=result["checked"],
        total_trials_count=result.get("total_trials_count", 0),
        notifications_found=result["notifications_found"],
        notifications_sent=result["notifications_sent"],
        notifications=result.get("notifications", []),
    )


# ══════════════════════════════════════════════════════════════════════════
# 自助取消/退款
# ══════════════════════════════════════════════════════════════════════════


@router.get("/cancel/reasons", response_model=CancelReasonsResponse)
async def list_cancel_reasons():
    """获取取消原因列表（前端下拉选择用）"""
    reasons = [
        {
            "value": r.value,
            "label": CANCEL_REASON_LABELS[r],
        }
        for r in CancelReason
    ]
    return CancelReasonsResponse(reasons=reasons)


@router.post("/cancel", response_model=CancelResponse)
async def cancel_subscription(
    req: CancelRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消订阅 — 当前周期结束后停止续费，服务可用至到期日。
    
    已付费用户可继续使用服务至当前计费周期结束，到期后自动降级为免费版。
    """
    try:
        sub = await cancel_at_period_end(
            user=user,
            db=db,
            reason=req.reason,
            reason_detail=req.reason_detail,
        )
        now = datetime.utcnow()
        days_remaining = max(0, (sub.end_date - now).days) if sub.end_date else 0
        is_trial = sub.status == "trial" or sub.features.get("is_trial", False)

        end_str = sub.end_date.strftime("%Y-%m-%d") if sub.end_date else "未知"
        return CancelResponse(
            success=True,
            message=f"订阅已取消，服务可用至 {end_str}，到期后自动降级为免费版",
            subscription=CurrentSubscriptionResponse(
                id=sub.id,
                company_name=sub.company_name,
                seats=sub.seats,
                tier=sub.tier,
                start_date=sub.start_date,
                end_date=sub.end_date,
                auto_renew=sub.auto_renew,
                status=sub.status,
                features=sub.features,
                days_remaining=days_remaining,
                is_trial=is_trial,
            ),
            refund=None,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/cancel-immediate", response_model=CancelResponse)
async def cancel_subscription_immediate(
    req: CancelRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """立即取消订阅 + 按比例退款。
    
    立即终止服务，并按已使用天数比例计算退款金额（向下取整到分）。
    试用订阅不产生退款。
    """
    try:
        result = await cancel_immediate(
            user=user,
            db=db,
            reason=req.reason,
            reason_detail=req.reason_detail,
        )
        sub = result["subscription"]
        refund = result["refund"]
        now = datetime.utcnow()
        days_remaining = 0
        is_trial = sub.status == "trial" or sub.features.get("is_trial", False)

        refund_msg = refund.get("message", "不产生退款")
        return CancelResponse(
            success=True,
            message=f"订阅已立即取消。{refund_msg}",
            subscription=CurrentSubscriptionResponse(
                id=sub.id,
                company_name=sub.company_name,
                seats=sub.seats,
                tier=sub.tier,
                start_date=sub.start_date,
                end_date=sub.end_date,
                auto_renew=sub.auto_renew,
                status=sub.status,
                features=sub.features,
                days_remaining=days_remaining,
                is_trial=is_trial,
            ),
            refund=RefundInfo(
                refund_cents=refund["refund_cents"],
                used_days=refund["used_days"],
                total_days=refund["total_days"],
                refund_ratio=refund["refund_ratio"],
                message=refund["message"],
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════
# A/B 定价实验
# ══════════════════════════════════════════════════════════════════════════


class ABTestStartResponse(BaseModel):
    success: bool
    message: str
    experiment: dict


@router.post("/ab-test/start", response_model=ABTestStartResponse)
async def start_ab_test():
    """启动 A/B 定价实验（草稿→运行中）

    默认实验: standard_v2_2026Q3
      对照组: ¥99/月 (当前定价)
      实验组: ¥79/月 (新定价策略)
      流量分配: 50:50
    """
    try:
        experiment = start_experiment("standard_v2_2026Q3")
        return ABTestStartResponse(
            success=True,
            message="A/B 定价实验已启动",
            experiment=get_experiment_status(experiment.name),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/ab-test/status")
async def get_ab_test_status():
    """查询 A/B 定价实验运行状态与 metrics"""
    try:
        return get_experiment_status("standard_v2_2026Q3")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
