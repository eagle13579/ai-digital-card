"""营销自动化 API 路由。

端点前缀: /api/crm

营销活动管理:
  POST   /api/crm/campaigns          → 创建营销活动(含目标人群segment过滤)
  GET    /api/crm/campaigns/{id}/stats → 活动统计(发送/打开/点击率)

客户旅程:
  GET    /api/crm/contacts/{id}/journey → 客户旅程时间线
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user

from app.crm.crm_models import CrmContact, CrmPipelineStage
from app.crm.customer_journey import CustomerJourneyStage
from app.crm.email_campaign import EmailCampaign

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crm", tags=["CRM 营销自动化"])


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Schemas
# ═══════════════════════════════════════════════════════════════════════════════


class CampaignCreateRequest(BaseModel):
    """创建营销活动请求体。"""

    name: str = Field(..., max_length=256, description="活动名称")
    subject: str = Field(..., max_length=512, description="邮件主题")
    content_template: str = Field(
        "", description="邮件内容模板(HTML/纯文本)"
    )
    target_segment: dict = Field(
        default_factory=dict,
        description=(
            "目标人群段(JSON): "
            '{"tags": ["VIP"], '
            '"pipeline_stage_ids": [1, 2], '
            '"sources": ["manual", "match"], '
            '"created_after": "2025-01-01", '
            '"created_before": "2025-12-31"}'
        ),
    )
    scheduled_at: str | None = Field(
        None, description="计划发送时间(ISO 8601)"
    )


class CampaignStatsResponse(BaseModel):
    """活动统计响应。"""
    id: int
    name: str
    sent_count: int
    open_count: int
    click_count: int
    open_rate: float
    click_rate: float
    status: str


class JourneyStageOut(BaseModel):
    """客户旅程阶段输出。"""
    id: int
    contact_id: int
    stage: str
    entered_at: str | None
    duration_days: int
    actions_taken: list
    score: float
    next_action: str
    pipeline_id: int | None


class JourneyTimelineResponse(BaseModel):
    """客户旅程时间线响应。"""
    contact_id: int
    contact_name: str
    stages: list[JourneyStageOut]


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/campaigns", response_model=dict, summary="创建营销活动(含目标人群segment过滤)")
async def create_campaign(
    req: CampaignCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新的邮件营销活动。

    - 将 target_segment 存储为 JSON 字符串
    - 可选 scheduled_at 设置计划发送时间
    """
    scheduled_dt = None
    if req.scheduled_at:
        try:
            scheduled_dt = datetime.fromisoformat(req.scheduled_at)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="scheduled_at 格式无效，请使用 ISO 8601 格式 (如 2025-06-01T10:00:00)",
            )

    campaign = EmailCampaign(
        name=req.name,
        subject=req.subject,
        content_template=req.content_template,
        target_segment=json.dumps(req.target_segment, ensure_ascii=False),
        scheduled_at=scheduled_dt,
        status="draft",
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    logger.info(
        "营销活动已创建: id=%d name=%s", campaign.id, campaign.name
    )
    return {"success": True, "data": campaign.to_dict()}


@router.get(
    "/campaigns/{campaign_id}/stats",
    response_model=dict,
    summary="活动统计(发送/打开/点击率)",
)
async def get_campaign_stats(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定营销活动的统计信息，包括发送数、打开数、点击数及对应比率。"""
    result = await db.execute(
        select(EmailCampaign).where(EmailCampaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="活动不存在")

    sent = campaign.sent_count or 0
    opened = campaign.open_count or 0
    clicked = campaign.click_count or 0

    open_rate = round((opened / sent * 100), 2) if sent > 0 else 0.0
    click_rate = round((clicked / sent * 100), 2) if sent > 0 else 0.0

    return {
        "success": True,
        "data": {
            "id": campaign.id,
            "name": campaign.name,
            "subject": campaign.subject,
            "sent_count": sent,
            "open_count": opened,
            "click_count": clicked,
            "open_rate": open_rate,
            "click_rate": click_rate,
            "status": campaign.status,
            "created_at": campaign.created_at.isoformat()
            if campaign.created_at
            else None,
        },
    }


@router.get(
    "/contacts/{contact_id}/journey",
    response_model=dict,
    summary="客户旅程时间线",
)
async def get_contact_journey(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定联系人的客户旅程时间线，按进入时间降序排列。"""
    # 验证联系人存在
    contact_result = await db.execute(
        select(CrmContact).where(CrmContact.id == contact_id)
    )
    contact = contact_result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")

    # 查询客户旅程阶段
    stages_result = await db.execute(
        select(CustomerJourneyStage)
        .where(CustomerJourneyStage.contact_id == contact_id)
        .order_by(CustomerJourneyStage.entered_at.desc())
    )
    stages = stages_result.scalars().all()

    stages_out = []
    for s in stages:
        stages_out.append(
            {
                "id": s.id,
                "contact_id": s.contact_id,
                "stage": s.stage,
                "entered_at": s.entered_at.isoformat()
                if s.entered_at
                else None,
                "duration_days": s.duration_days,
                "actions_taken": json.loads(s.actions_taken)
                if s.actions_taken
                else [],
                "score": s.score,
                "next_action": s.next_action,
                "pipeline_id": s.pipeline_id,
            }
        )

    return {
        "success": True,
        "data": {
            "contact_id": contact.id,
            "contact_name": contact.name,
            "stages": stages_out,
        },
    }
