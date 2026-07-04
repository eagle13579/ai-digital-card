"""CRM API 路由。

端点前缀: /api/crm

联系人:
  POST   /api/crm/contacts            → 创建联系人
  GET    /api/crm/contacts            → 联系人列表(搜索/筛选/分页)
  GET    /api/crm/contacts/{id}       → 联系人详情
  PUT    /api/crm/contacts/{id}       → 更新联系人
  DELETE /api/crm/contacts/{id}       → 删除联系人

时间线:
  GET    /api/crm/contacts/{id}/timeline  → 联系人活动时间线
  POST   /api/crm/activities               → 手动添加活动

笔记:
  GET    /api/crm/contacts/{id}/notes  → 联系人笔记列表
  POST   /api/crm/notes                → 创建笔记
  PUT    /api/crm/notes/{id}           → 更新笔记
  DELETE /api/crm/notes/{id}           → 删除笔记

管道:
  GET    /api/crm/pipeline/stages      → 管道阶段列表
  PUT    /api/crm/pipeline/stages/{id} → 更新管道阶段
  GET    /api/crm/pipeline/deals       → 按阶段分组的机会
  PUT    /api/crm/deals/{id}/stage     → 拖拽变更阶段

机会:
  POST   /api/crm/deals                → 创建机会

报表/分析:
  GET    /api/crm/analytics/pipeline    → Pipeline 分析(阶段汇总+赢单率)
  GET    /api/crm/analytics/conversion  → 转化率(漏斗+各阶段转化)
  GET    /api/crm/analytics/trend       → 趋势(每日活动量+联系人增长)
  GET    /api/crm/analytics/dashboard   → 仪表盘汇总(全部指标)

AI销售预测:
  GET    /api/crm/prediction/deal/{id}  → 单个Deal的AI赢单率预测
  POST   /api/crm/prediction/retrain   → 重新训练预测模型
  GET    /api/crm/prediction/status     → 模型状态(样本数/准确率)

统计:
  GET    /api/crm/stats                → 联系人统计

导入导出:
  GET    /api/crm/export/csv           → 导出CSV
  POST   /api/crm/import/csv           → 导入CSV

自动创建:
  POST   /api/crm/auto/match/{match_id} → 从名片交换创建联系人
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Body
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_standards import PaginatedResponse, paginate_cursor
from app.database import get_db
from app.models.tag import MatchRecord
from app.models.user import User

router = APIRouter(prefix="/api/crm", tags=["CRM"])

from app.crm.crm_models import (
    CrmContact,
    CrmDeal,
    CrmNote,
    CrmActivity,
    CrmPipelineStage,
    CrmWorkflowRule,
    CrmWorkflowLog,
)
from app.crm.crm_service import CrmService
from app.crm.crm_analytics import CrmAnalyticsService
from app.crm.crm_rbac import (
    CONTACTS_VIEW,
    CONTACTS_CREATE,
    CONTACTS_EDIT,
    CONTACTS_DELETE,
    PIPELINE_VIEW,
    PIPELINE_MOVE,
    REPORTS_VIEW,
    WORKFLOW_MANAGE,
    PERMISSIONS_MANAGE,
    CrmRole,
    CRM_ROLE_DISPLAY,
    CRM_PERMISSION_LABELS,
    ALL_CRM_PERMISSIONS,
    get_user_crm_permissions,
    get_crm_permissions_for_role,
    ensure_crm_role_definition,
    assign_crm_role,
    require_permission,
)
from app.crm.workflow_engine import WorkflowEngine, test_rule_execution

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Schemas
# ═══════════════════════════════════════════════════════════════════════════════


class ContactCreate(BaseModel):
    name: str
    phone: str = ""
    email: str = ""
    company: str = ""
    title: str = ""
    department: str = ""
    avatar: str = ""
    intro: str = ""
    user_id: int | None = None
    tags: list[str] = Field(default_factory=list)
    deal_value: float | None = None
    deal_currency: str = "CNY"
    pipeline_stage_id: int | None = None


class ContactUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    company: str | None = None
    title: str | None = None
    department: str | None = None
    avatar: str | None = None
    intro: str | None = None
    tags: list[str] | None = None
    deal_value: float | None = None
    deal_currency: str | None = None
    pipeline_stage_id: int | None = None
    last_contacted_at: str | None = None


class ContactResponse(BaseModel):
    id: int
    owner_id: int
    user_id: int | None
    name: str
    phone: str
    email: str
    company: str
    title: str
    department: str
    avatar: str
    intro: str
    source: str
    source_record_id: int | None
    tags: str
    pipeline_stage_id: int | None
    deal_value: float | None
    deal_currency: str
    stage_name: str | None
    last_contacted_at: str | None
    created_at: str | None
    updated_at: str | None

    class Config:
        from_attributes = True


class ActivityCreate(BaseModel):
    contact_id: int
    activity_type: str
    title: str = ""
    description: str = ""
    deal_id: int | None = None
    activity_date: str | None = None


class ActivityResponse(BaseModel):
    id: int
    owner_id: int
    contact_id: int
    deal_id: int | None
    activity_type: str
    title: str
    description: str
    source_model: str | None
    source_record_id: int | None
    activity_date: str | None
    created_at: str | None

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    contact_id: int | None = None
    deal_id: int | None = None
    content: str
    is_pinned: bool = False


class NoteUpdate(BaseModel):
    content: str | None = None
    is_pinned: bool | None = None


class NoteResponse(BaseModel):
    id: int
    owner_id: int
    contact_id: int | None
    deal_id: int | None
    content: str
    is_pinned: bool
    created_at: str | None
    updated_at: str | None

    class Config:
        from_attributes = True


class DealCreate(BaseModel):
    contact_id: int
    pipeline_stage_id: int
    title: str
    value: float = 0
    currency: str = "CNY"
    probability: float = 0.0
    expected_close_date: str | None = None


class DealStageUpdate(BaseModel):
    pipeline_stage_id: int


class DealResponse(BaseModel):
    id: int
    owner_id: int
    contact_id: int
    pipeline_stage_id: int
    title: str
    value: float
    currency: str
    probability: float
    status: str
    contact_name: str | None
    stage_name: str | None
    created_at: str | None
    updated_at: str | None

    class Config:
        from_attributes = True


class PipelineStageResponse(BaseModel):
    id: int
    name: str
    sort_order: int
    color: str
    is_default: bool
    is_closed: bool
    win_probability: float

    class Config:
        from_attributes = True


class PipelineDealsResponse(BaseModel):
    stages: list[dict]
    deals: dict[str, list[dict]]


class StatsResponse(BaseModel):
    total_contacts: int
    by_source: dict[str, int]
    by_company: dict[str, int]
    by_stage: dict[str, int]
    top_tags: dict[str, int]


class AutoMatchCreate(BaseModel):
    """从名片交换自动创建联系人时，可选择跳过已存在的。"""

    force: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# Analytics Pydantic Schemas
# ═══════════════════════════════════════════════════════════════════════════════


class PipelineSummaryItem(BaseModel):
    stage_id: int
    stage_name: str
    sort_order: int
    color: str
    is_closed: bool
    win_probability: float
    contact_count: int
    deal_count: int
    total_value: float
    avg_probability: float
    won_count: int
    won_rate: float


class TeamPerformanceItem(BaseModel):
    user_id: int
    name: str
    contact_count: int
    deal_count: int
    won_deals: int
    lost_deals: int
    total_value: float
    won_value: float
    close_rate: float


class ConversionStageItem(BaseModel):
    stage_id: int
    stage_name: str
    sort_order: int
    is_closed: bool
    contact_count: int
    deal_count: int
    conversion_rate: float


class ConversionResponse(BaseModel):
    stages: list[ConversionStageItem]
    total_contacts: int
    total_deals: int
    total_won: int
    total_lost: int
    overall_conversion_rate: float


class TrendItem(BaseModel):
    date: str
    count: int


class GrowthItem(BaseModel):
    date: str
    cumulative_count: int
    daily_increment: int


class DashboardSummary(BaseModel):
    total_contacts: int
    total_deals: int
    total_pipeline_value: float
    total_won_deals: int
    overall_conversion_rate: float
    recent_7d_activity: int
    recent_7d_new_contacts: int


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    pipeline: list[PipelineSummaryItem]
    conversion: ConversionResponse
    activity_trend: list[TrendItem]
    contact_growth: list[GrowthItem]
    team_performance: list[TeamPerformanceItem]


# ═══════════════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════════════


def _get_crm_service(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: __import__('app.routers.auth', fromlist=['get_current_user']).get_current_user),
) -> CrmService:
    return CrmService(db, current_user.id)


def _get_analytics_service(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: __import__('app.routers.auth', fromlist=['get_current_user']).get_current_user),
) -> CrmAnalyticsService:
    return CrmAnalyticsService(db, current_user.id)


# ═══════════════════════════════════════════════════════════════════════════════
# 联系人
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/contacts", response_model=ContactResponse, status_code=201)
async def create_contact(
    data: ContactCreate,
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_CREATE)),
):
    """创建 CRM 联系人。"""
    contact = await svc.create_contact(data.model_dump())
    await svc.db.refresh(contact)  # ensure stage loaded
    return contact


@router.get("/contacts", response_model=PaginatedResponse[ContactResponse])
async def list_contacts(
    cursor: str | None = Query(None, description="分页游标（首次请求不传）"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    search: str | None = Query(None, description="按姓名/公司/职位/邮箱/手机搜索"),
    stage_id: int | None = Query(None, description="按管道阶段筛选"),
    source: str | None = Query(None, description="按来源筛选(match/manual/visitor/import)"),
    tag: str | None = Query(None, description="按标签筛选"),
    company: str | None = Query(None, description="按公司筛选"),
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_VIEW)),
):
    """联系人列表（cursor 分页 + 搜索 + 筛选）。"""
    query = await svc.build_contacts_query(
        search=search, stage_id=stage_id, source=source, tag=tag, company=company,
    )
    return await paginate_cursor(
        svc.db, query, cursor=cursor, page_size=page_size,
        cursor_column=CrmContact.id, response_model=ContactResponse,
    )


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_VIEW)),
):
    """联系人详情。"""
    contact = await svc.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")
    return contact


@router.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    data: ContactUpdate,
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_EDIT)),
):
    """更新联系人。"""
    contact = await svc.update_contact(contact_id, data.model_dump(exclude_none=True))
    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")
    return contact


@router.delete("/contacts/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: int,
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_DELETE)),
):
    """删除联系人。"""
    ok = await svc.delete_contact(contact_id)
    if not ok:
        raise HTTPException(status_code=404, detail="联系人不存在")


# ═══════════════════════════════════════════════════════════════════════════════
# 活动 / 时间线
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/activities", response_model=ActivityResponse, status_code=201)
async def create_activity(
    data: ActivityCreate,
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_EDIT)),
):
    """手动添加活动记录。"""
    activity = await svc.add_activity(data.model_dump())
    return activity


@router.get("/contacts/{contact_id}/timeline")
async def get_timeline(
    contact_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_VIEW)),
):
    """联系人时间线。"""
    activities, total = await svc.get_contact_timeline(
        contact_id, page=page, page_size=page_size
    )
    items = [a.to_dict() for a in activities]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 笔记
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/notes", response_model=NoteResponse, status_code=201)
async def create_note(
    data: NoteCreate,
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_EDIT)),
):
    """创建笔记。"""
    note = await svc.create_note(data.model_dump())
    return note


@router.get("/contacts/{contact_id}/notes")
async def get_contact_notes(
    contact_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_VIEW)),
):
    """联系人笔记列表。"""
    notes, total = await svc.get_contact_notes(
        contact_id, page=page, page_size=page_size
    )
    items = [n.to_dict() for n in notes]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.put("/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    data: NoteUpdate,
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_EDIT)),
):
    """更新笔记。"""
    note = await svc.update_note(note_id, data.model_dump(exclude_none=True))
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return note


@router.delete("/notes/{note_id}", status_code=204)
async def delete_note(
    note_id: int,
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_DELETE)),
):
    """删除笔记。"""
    ok = await svc.delete_note(note_id)
    if not ok:
        raise HTTPException(status_code=404, detail="笔记不存在")


# ═══════════════════════════════════════════════════════════════════════════════
# 管道
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/pipeline/stages", response_model=list[PipelineStageResponse])
async def get_pipeline_stages(
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(PIPELINE_VIEW)),
):
    """获取销售管道阶段列表。"""
    stages = await svc.ensure_default_stages()
    return stages


@router.get("/pipeline/deals", response_model=PipelineDealsResponse)
async def get_pipeline_deals(
    svc: CrmService = Depends(_get_crm_service),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(PIPELINE_VIEW)),
):
    """按管道阶段分组的销售机会（看板数据），含 AI 预测赢单率标签。"""
    # 先确保阶段存在
    await svc.ensure_default_stages()
    stages = await svc.get_pipeline_stages()
    grouped = await svc.get_pipeline_deals()

    stages_data = [s.to_dict() for s in stages]
    deals_data: dict[str, list[dict]] = {}

    # 批量预测（仅对 open 状态的 deal）
    from app.services.sales_prediction import get_prediction_service
    pred_svc = get_prediction_service()

    for stage_id, deals in grouped.items():
        enriched = []
        for deal in deals:
            d = deal.to_dict()
            # 添加 AI 预测信息
            if deal.status == "open":
                try:
                    pred = await pred_svc.predict_deal(deal.id, db)
                    if "error" not in pred:
                        d["ai_prediction"] = {
                            "win_probability": pred["predicted_win_probability"],
                            "confidence": pred["confidence"],
                            "label": _prediction_label(
                                pred["predicted_win_probability"], pred["confidence"]
                            ),
                        }
                except Exception:
                    d["ai_prediction"] = None
            else:
                d["ai_prediction"] = None
            enriched.append(d)
        deals_data[str(stage_id)] = enriched

    return {
        "stages": stages_data,
        "deals": deals_data,
    }


def _prediction_label(probability: float, confidence: str) -> str:
    """根据概率和置信度生成预测标签。"""
    if confidence == "low":
        return "待定"
    if probability >= 70:
        return "高概率"
    elif probability >= 40:
        return "中概率"
    else:
        return "低概率"


# ═══════════════════════════════════════════════════════════════════════════════
# 机会 (Deals)
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/deals", response_model=DealResponse, status_code=201)
async def create_deal(
    data: DealCreate,
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_EDIT)),
):
    """创建销售机会。"""
    deal = await svc.create_deal(data.model_dump())
    return deal


@router.put("/deals/{deal_id}/stage", response_model=DealResponse)
async def update_deal_stage(
    deal_id: int,
    data: DealStageUpdate,
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(PIPELINE_MOVE)),
):
    """更新机会的管道阶段（拖拽）。"""
    deal = await svc.update_deal_stage(deal_id, data.pipeline_stage_id)
    if not deal:
        raise HTTPException(status_code=404, detail="机会不存在")
    return deal


# ═══════════════════════════════════════════════════════════════════════════════
# 报表 / 分析
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/analytics/pipeline", response_model=list[PipelineSummaryItem])
async def analytics_pipeline(
    svc: CrmAnalyticsService = Depends(_get_analytics_service),
    _: None = Depends(require_permission(REPORTS_VIEW)),
):
    """Pipeline 分析: 每阶段机会数+金额+赢单率。"""
    return await svc.get_pipeline_summary()


@router.get("/analytics/conversion", response_model=ConversionResponse)
async def analytics_conversion(
    svc: CrmAnalyticsService = Depends(_get_analytics_service),
    _: None = Depends(require_permission(REPORTS_VIEW)),
):
    """转化率: 各阶段转化率和整体漏斗数据。"""
    return await svc.get_conversion_rate()


@router.get("/analytics/trend")
async def analytics_trend(
    days: int = Query(30, ge=1, le=365, description="最近N天"),
    svc: CrmAnalyticsService = Depends(_get_analytics_service),
    _: None = Depends(require_permission(REPORTS_VIEW)),
):
    """趋势数据: 每日活动量趋势 + 联系人增长曲线。"""
    activity_trend = await svc.get_activity_trend(days)
    contact_growth = await svc.get_contact_growth(days)
    return {
        "activity_trend": activity_trend,
        "contact_growth": contact_growth,
    }


@router.get("/analytics/dashboard", response_model=DashboardResponse)
async def analytics_dashboard(
    days: int = Query(30, ge=1, le=365, description="最近N天"),
    svc: CrmAnalyticsService = Depends(_get_analytics_service),
    _: None = Depends(require_permission(REPORTS_VIEW)),
):
    """汇总仪表盘数据: 整合所有分析指标。"""
    return await svc.get_dashboard(days)


# ═══════════════════════════════════════════════════════════════════════════════
# 统计
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(REPORTS_VIEW)),
):
    """联系人统计。"""
    stats = await svc.get_group_stats()
    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# 导入导出
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/export/csv")
async def export_csv(
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_VIEW)),
):
    """导出联系人 CSV。"""
    from fastapi.responses import PlainTextResponse
    csv_content = await svc.export_csv()
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=crm_contacts.csv"},
    )


@router.post("/import/csv")
async def import_csv(
    file: UploadFile = File(...),
    svc: CrmService = Depends(_get_crm_service),
    _: None = Depends(require_permission(CONTACTS_CREATE)),
):
    """从 CSV 文件导入联系人。"""
    content = await file.read()
    csv_text = content.decode("utf-8-sig")  # handle BOM
    result = await svc.import_csv(csv_text)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 自动创建（从名片交换）
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/auto/match/{match_id}", status_code=201)
async def create_from_match(
    match_id: int,
    data: AutoMatchCreate,
    svc: CrmService = Depends(_get_crm_service),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(CONTACTS_CREATE)),
):
    """从名片交换记录自动创建 CRM 联系人。"""
    # 获取匹配记录
    result = await db.execute(
        select(MatchRecord).where(MatchRecord.id == match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="匹配记录不存在")

    # 验证当前用户是参与方
    if svc.user_id not in (match.user_a_id, match.user_b_id):
        raise HTTPException(status_code=403, detail="你不是该匹配的参与方")

    contact = await svc.create_contact_from_match(match)
    if not contact:
        raise HTTPException(status_code=409, detail="联系人已存在或创建失败")

    return {"message": "联系人已自动创建", "contact_id": contact.id}


@router.post("/auto/all-matches")
async def auto_create_from_all_matches(
    svc: CrmService = Depends(_get_crm_service),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(CONTACTS_CREATE)),
):
    """从当前用户所有名片交换记录批量创建 CRM 联系人。"""
    result = await db.execute(
        select(MatchRecord).where(
            (MatchRecord.user_a_id == svc.user_id) | (MatchRecord.user_b_id == svc.user_id)
        ).order_by(MatchRecord.created_at.desc())
    )
    matches = list(result.scalars().all())

    created = 0
    skipped = 0
    for match in matches:
        contact = await svc.create_contact_from_match(match)
        if contact:
            created += 1
        else:
            skipped += 1

    return {
        "message": f"已创建 {created} 个联系人，跳过 {skipped} 个已有联系人",
        "created": created,
        "skipped": skipped,
        "total_matches": len(matches),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 工作流自动化引擎
# ═══════════════════════════════════════════════════════════════════════════════


class WorkflowRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="规则名称")
    description: str = ""
    trigger_event: str = Field(
        ..., pattern=r"^(contact_added|deal_created|stage_changed)$",
        description="触发事件: contact_added | deal_created | stage_changed",
    )
    conditions: list[dict] = Field(
        default_factory=list,
        description="条件列表 [{\"field\":\"source\",\"operator\":\"eq\",\"value\":\"manual\"}]",
    )
    actions: list[dict] = Field(
        ..., min_length=1,
        description="动作列表 [{\"type\":\"send_email\",\"config\":{...}}]",
    )
    enabled: bool = True


class WorkflowRuleResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    description: str
    trigger_event: str
    conditions: list[dict]
    actions: list[dict]
    enabled: bool
    created_at: str | None
    updated_at: str | None

    class Config:
        from_attributes = True


class WorkflowToggleResponse(BaseModel):
    id: int
    name: str
    enabled: bool
    message: str


class WorkflowTestRequest(BaseModel):
    rule_data: dict = Field(..., description="要测试的规则 JSON (无需保存)")
    context: dict = Field(
        default_factory=lambda: {
            "contact": {"id": 1, "name": "测试用户", "email": "test@example.com", "company": "测试公司"},
            "deal": {"id": 1, "title": "测试商机", "value": 100000},
            "stage": {"id": 1, "name": "谈判中"},
        },
        description="测试上下文 (模拟触发时的数据)",
    )


class WorkflowTestResult(BaseModel):
    success: bool
    action_results: list[dict]
    total_actions: int
    succeeded: int
    failed: int


def _get_workflow_engine(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: __import__('app.routers.auth', fromlist=['get_current_user']).get_current_user),
) -> WorkflowEngine:
    return WorkflowEngine(db, current_user.id)


@router.post(
    "/workflow/rules",
    response_model=WorkflowRuleResponse,
    status_code=201,
    summary="创建工作流规则",
)
async def create_workflow_rule(
    data: WorkflowRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: __import__('app.routers.auth', fromlist=['get_current_user']).get_current_user),
    _: None = Depends(require_permission(WORKFLOW_MANAGE)),
):
    """创建一条新的工作流自动化规则。"""
    rule = await WorkflowEngine.create_rule(
        db, current_user.id, data.model_dump()
    )
    return rule


@router.get(
    "/workflow/rules",
    response_model=list[WorkflowRuleResponse],
    summary="工作流规则列表",
)
async def list_workflow_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: __import__('app.routers.auth', fromlist=['get_current_user']).get_current_user),
    _: None = Depends(require_permission(WORKFLOW_MANAGE)),
):
    """获取当前用户的所有工作流规则。"""
    rules = await WorkflowEngine.get_rules(db, current_user.id)
    return rules


@router.put(
    "/workflow/rules/{rule_id}/toggle",
    response_model=WorkflowToggleResponse,
    summary="启用/禁用规则",
)
async def toggle_workflow_rule(
    rule_id: int,
    enabled: bool | None = Query(None, description="指定 true/false 切换，不传则取反"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: __import__('app.routers.auth', fromlist=['get_current_user']).get_current_user),
    _: None = Depends(require_permission(WORKFLOW_MANAGE)),
):
    """启用或禁用一条工作流规则。"""
    rule = await WorkflowEngine.update_rule_toggle(
        db, current_user.id, rule_id, enabled=enabled
    )
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    status = "启用" if rule.enabled else "禁用"
    return WorkflowToggleResponse(
        id=rule.id,
        name=rule.name,
        enabled=rule.enabled,
        message=f"规则「{rule.name}」已{status}",
    )


@router.delete(
    "/workflow/rules/{rule_id}",
    status_code=204,
    summary="删除工作流规则",
)
async def delete_workflow_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: __import__('app.routers.auth', fromlist=['get_current_user']).get_current_user),
    _: None = Depends(require_permission(WORKFLOW_MANAGE)),
):
    """删除一条工作流规则。"""
    ok = await WorkflowEngine.delete_rule(db, current_user.id, rule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="规则不存在")


@router.post(
    "/workflow/rules/{rule_id}/test",
    response_model=WorkflowTestResult,
    summary="测试工作流规则",
)
async def test_workflow_rule(
    rule_id: int,
    context: dict | None = Body(None, description="模拟触发时的上下文数据"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: __import__('app.routers.auth', fromlist=['get_current_user']).get_current_user),
    _: None = Depends(require_permission(WORKFLOW_MANAGE)),
):
    """测试一条已有的规则（不操作数据库）。"""
    # 加载规则
    result = await db.execute(
        select(CrmWorkflowRule).where(
            CrmWorkflowRule.id == rule_id,
            CrmWorkflowRule.owner_id == current_user.id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    rule_data = rule.to_dict()
    test_ctx = context or {
        "contact": {"id": 1, "name": "测试用户", "email": "test@example.com", "company": "测试公司"},
        "deal": {"id": 1, "title": "测试商机", "value": 100000},
        "stage": {"id": 1, "name": "谈判中"},
    }

    action_results = await test_rule_execution(rule_data, test_ctx)
    succeeded = sum(1 for r in action_results if r.get("success"))
    return WorkflowTestResult(
        success=succeeded == len(action_results),
        action_results=action_results,
        total_actions=len(action_results),
        succeeded=succeeded,
        failed=len(action_results) - succeeded,
    )


@router.post(
    "/workflow/test",
    response_model=WorkflowTestResult,
    summary="测试自定义规则（不保存）",
)
async def test_custom_rule(
    data: WorkflowTestRequest,
    _: None = Depends(require_permission(WORKFLOW_MANAGE)),
):
    """测试自定义的规则配置（不保存到数据库）。"""
    action_results = await test_rule_execution(
        data.rule_data, data.context
    )
    succeeded = sum(1 for r in action_results if r.get("success"))
    return WorkflowTestResult(
        success=succeeded == len(action_results),
        action_results=action_results,
        total_actions=len(action_results),
        succeeded=succeeded,
        failed=len(action_results) - succeeded,
    )


@router.post(
    "/workflow/init-presets",
    response_model=list[WorkflowRuleResponse],
    summary="初始化预置规则",
)
async def init_preset_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: __import__('app.routers.auth', fromlist=['get_current_user']).get_current_user),
    _: None = Depends(require_permission(WORKFLOW_MANAGE)),
):
    """为用户初始化 3 条预置工作流规则（无规则时创建，已有则返回现有）。"""
    rules = await WorkflowEngine.init_preset_rules(db, current_user.id)
    return rules


@router.get(
    "/workflow/logs",
    response_model=list[dict],
    summary="工作流执行日志",
)
async def get_workflow_logs(
    rule_id: int | None = Query(None, description="按规则 ID 筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: __import__('app.routers.auth', fromlist=['get_current_user']).get_current_user),
    _: None = Depends(require_permission(WORKFLOW_MANAGE)),
):
    """获取工作流执行日志。"""
    query = select(CrmWorkflowLog).where(
        CrmWorkflowLog.owner_id == current_user.id,
    )
    if rule_id:
        query = query.where(CrmWorkflowLog.rule_id == rule_id)

    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(CrmWorkflowLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = list(result.scalars().all())

    return {
        "items": [log.to_dict() for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (page + page_size - 1) // page_size if total > 0 else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# RBAC 角色权限管理
# ═══════════════════════════════════════════════════════════════════════════════


class RoleCreateRequest(BaseModel):
    """创建角色请求（暂只支持内置角色同步到数据库）。"""

    name: str = Field(..., description="角色标识 (admin|manager|sales|viewer)")


class RoleInfo(BaseModel):
    """角色信息响应。"""

    name: str
    display_name: str
    description: str
    permissions: list[dict[str, str]]


class RoleAssignRequest(BaseModel):
    """分配角色请求。"""

    user_id: int = Field(..., description="目标用户 ID")
    role: str = Field(..., description="角色名 (admin|manager|sales|viewer)")


class MyPermissionsResponse(BaseModel):
    """当前用户权限响应。"""

    user_id: int
    role: str
    role_display: str
    permissions: list[str]
    permission_labels: list[dict[str, str]]


@router.post(
    "/rbac/roles",
    response_model=RoleInfo,
    status_code=201,
    summary="创建/同步 CRM 角色到数据库",
)
async def create_rbac_role(
    data: RoleCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: __import__('app.routers.auth', fromlist=['get_current_user']).get_current_user),
    _: None = Depends(require_permission(PERMISSIONS_MANAGE)),
):
    """创建或同步一个 CRM 角色到数据库（需要 permissions.manage 权限）。"""
    if data.name not in CrmRole._value2member_:
        raise HTTPException(
            status_code=400,
            detail=f"无效角色名: {data.name}，可选: {list(CrmRole._value2member_.keys())}",
        )

    role_ids = await ensure_crm_role_definition(db)
    role_id = role_ids[data.name]

    # 获取角色的完整信息
    perms = get_crm_permissions_for_role(data.name)
    return RoleInfo(
        name=data.name,
        display_name=CRM_ROLE_DISPLAY.get(CrmRole(data.name), data.name),
        description=f"CRM {CRM_ROLE_DISPLAY.get(CrmRole(data.name), data.name)}",
        permissions=[
            {"key": p, "label": CRM_PERMISSION_LABELS.get(p, p)}
            for p in sorted(perms)
        ],
    )


@router.get(
    "/rbac/roles",
    response_model=list[RoleInfo],
    summary="获取所有 CRM 角色及权限",
)
async def list_rbac_roles(
    _: None = Depends(require_permission(PERMISSIONS_MANAGE)),
):
    """返回所有 CRM 角色及其权限矩阵（需要 permissions.manage 权限）。"""
    roles = []
    for role_enum in CrmRole:
        perms = get_crm_permissions_for_role(role_enum.value)
        roles.append(RoleInfo(
            name=role_enum.value,
            display_name=CRM_ROLE_DISPLAY.get(role_enum, role_enum.value),
            description=f"CRM {CRM_ROLE_DISPLAY.get(role_enum, role_enum.value)}",
            permissions=[
                {"key": p, "label": CRM_PERMISSION_LABELS.get(p, p)}
                for p in sorted(perms)
            ],
        ))
    return roles


@router.post(
    "/rbac/assign",
    response_model=dict,
    status_code=200,
    summary="分配 CRM 角色给用户",
)
async def assign_role_to_user(
    data: RoleAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: __import__('app.routers.auth', fromlist=['get_current_user']).get_current_user),
    _: None = Depends(require_permission(PERMISSIONS_MANAGE)),
):
    """为指定用户分配 CRM 角色（需要 permissions.manage 权限）。"""
    try:
        await assign_crm_role(
            db,
            target_user_id=data.user_id,
            role_name=data.role,
            granted_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 返回角色分配后的权限信息
    perms = await get_user_crm_permissions(db, data.user_id)
    return {
        "message": f"用户 {data.user_id} 已分配角色「{perms['role_display']}」",
        **perms,
    }


@router.get(
    "/rbac/my-permissions",
    response_model=MyPermissionsResponse,
    summary="获取当前用户的权限",
)
async def get_my_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: __import__('app.routers.auth', fromlist=['get_current_user']).get_current_user),
):
    """返回当前用户的 CRM 角色和所有权限。"""
    perms = await get_user_crm_permissions(db, current_user.id)
    return MyPermissionsResponse(**perms)
