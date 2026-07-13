"""CRM 邮件营销 API 路由。

端点前缀: /api/crm

活动管理:
  POST   /api/crm/campaigns          → 创建营销活动
  GET    /api/crm/campaigns           → 活动列表
  GET    /api/crm/campaigns/{id}      → 活动详情
  POST   /api/crm/campaigns/{id}/send → 发送活动

统计数据:
  GET    /api/crm/campaigns/{id}/stats → 统计数据

追踪像素（公开）:
  GET    /api/crm/track/open/{token}  → 追踪像素 (1x1 GIF) + 记录打开

退订（公开）:
  GET    /api/crm/unsubscribe/{token} → 退订页面
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user

from app.crm.crm_models import CrmCampaign, CrmCampaignRecipient
from app.services.email_campaign import EmailCampaignService, get_tracking_pixel_bytes
from app.services.email_templates import unsubscribe_confirmed_html

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crm", tags=["CRM 邮件营销"])


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Schemas
# ═══════════════════════════════════════════════════════════════════════════════


class CampaignCreate(BaseModel):
    name: str = Field(..., max_length=256, description="活动名称")
    subject: str = Field(..., max_length=512, description="邮件主题")
    template_name: str = Field(
        ...,
        description=(
            "模板名称。可选: "
            "welcome_html, trial_expiring_3d_html, trial_expiring_1d_html, "
            "trial_expired_html, crm_new_contact_html, campaign_broadcast_html"
        ),
    )
    template_params: dict = Field(
        default_factory=dict,
        description="模板参数(JSON)，例如 {\"name\": \"用户\"}",
    )
    target_filter: dict = Field(
        default_factory=dict,
        description=(
            "目标筛选条件。支持: "
            '{\"tags\": [\"VIP\", \"潜在客户\"], '
            '\"pipeline_stage_ids\": [1, 2], '
            '\"sources\": [\"manual\", \"match\"], '
            '\"created_after\": \"2025-01-01\", '
            '\"created_before\": \"2025-12-31\"}'
        ),
    )


class CampaignResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    subject: str
    template_name: str
    template_params: dict
    target_filter: dict
    status: str
    total_recipients: int
    sent_count: int
    opened_count: int
    unsubscribed_count: int
    created_at: str | None
    updated_at: str | None

    class Config:
        from_attributes = True


class CampaignStatsResponse(BaseModel):
    campaign_id: int
    name: str
    status: str
    total_recipients: int
    sent_count: int
    opened_count: int
    unsubscribed_count: int
    open_rate: float
    unsubscribe_rate: float
    opened_recipients: list[dict]


class CampaignSendResponse(BaseModel):
    campaign_id: int
    total_recipients: int
    sent_count: int
    failed_count: int
    errors: list[str]


# ═══════════════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════════════


def _get_campaign_service(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmailCampaignService:
    return EmailCampaignService(db, current_user.id)


# ═══════════════════════════════════════════════════════════════════════════════
# 活动管理
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/campaigns", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    data: CampaignCreate,
    svc: EmailCampaignService = Depends(_get_campaign_service),
):
    """创建邮件营销活动。

    创建后为 draft 状态，需要调用 POST /api/crm/campaigns/{id}/send 来发送。
    """
    campaign = await svc.create_campaign(data.model_dump())
    await svc.db.refresh(campaign)
    return _campaign_to_response(campaign)


@router.get("/campaigns", response_model=dict)
async def list_campaigns(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    svc: EmailCampaignService = Depends(_get_campaign_service),
):
    """获取邮件营销活动列表（分页）。"""
    campaigns, total = await svc.list_campaigns(page=page, page_size=page_size)
    items = [c.to_dict() for c in campaigns]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    svc: EmailCampaignService = Depends(_get_campaign_service),
):
    """获取活动详情。"""
    campaign = await svc.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="活动不存在")
    return _campaign_to_response(campaign)


@router.post("/campaigns/{campaign_id}/send", response_model=CampaignSendResponse)
async def send_campaign(
    campaign_id: int,
    svc: EmailCampaignService = Depends(_get_campaign_service),
):
    """发送邮件营销活动。

    仅 draft 状态的活动可以发送。发送过程:
      - 筛选目标联系人（满足 target_filter 条件且有邮箱）
      - 分批发送（每批 50 封，间隔 5 秒）
      - 每封邮件嵌入追踪像素和退订链接
      - 完成后状态更新为 sent
    """
    result = await svc.send_campaign(campaign_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 统计
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/campaigns/{campaign_id}/stats", response_model=CampaignStatsResponse)
async def get_campaign_stats(
    campaign_id: int,
    svc: EmailCampaignService = Depends(_get_campaign_service),
):
    """获取活动统计数据。

    包含:
      - 总数 / 发送数 / 打开数 / 退订数
      - 打开率 / 退订率
      - 已打开的联系人详情（前 50）
    """
    stats = await svc.get_campaign_stats(campaign_id)
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# 追踪像素（公开端点 — 无需认证）
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/track/open/{tracking_token}", include_in_schema=False)
async def track_open(
    tracking_token: str,
    db: AsyncSession = Depends(get_db),
):
    """追踪像素端点。

    返回 1×1 透明 GIF 图片，同时记录打开事件。
    公开访问，无需认证。
    """
    svc = EmailCampaignService(db, user_id=0)  # user_id 不重要，仅用于记录
    await svc.record_open(tracking_token)

    return Response(
        content=get_tracking_pixel_bytes(),
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 退订（公开端点 — 无需认证）
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/unsubscribe/{tracking_token}", include_in_schema=False)
async def unsubscribe(
    tracking_token: str,
    db: AsyncSession = Depends(get_db),
):
    """退订端点。

    访问此链接会记录退订并显示确认页面。
    公开访问，无需认证。
    """
    svc = EmailCampaignService(db, user_id=0)
    ok = await svc.unsubscribe(tracking_token)

    if ok:
        # 查询收件人信息用于展示
        result = await db.execute(
            select(CrmCampaignRecipient).where(
                CrmCampaignRecipient.tracking_token == tracking_token
            )
        )
        recipient = result.scalar_one_or_none()
        email = recipient.email if recipient else ""

        html = unsubscribe_confirmed_html(email=email)
        return HTMLResponse(content=html, status_code=200)
    else:
        return HTMLResponse(
            content="<h1>退订链接无效或已过期</h1>",
            status_code=404,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════════════


def _campaign_to_response(campaign: CrmCampaign) -> dict:
    """将 CrmCampaign ORM 对象转为响应字典。"""
    return campaign.to_dict()
