"""信任体系 API — 链客宝 trust_api 迁移适配（异步版）

API 路径: /api/v1/trust/*
功能:
  GET    /api/v1/trust/score/{user_id}           — 获取信任评分（公开）
  GET    /api/v1/trust/score/{user_id}/history   — 评分历史走势
  POST   /api/v1/trust/score/{user_id}/recalc    — 触发评分重算
  GET    /api/v1/trust/qualifications            — 我的资质列表
  POST   /api/v1/trust/qualifications            — 新增资质
  GET    /api/v1/trust/reviews/{user_id}         — 用户收到的评价
  POST   /api/v1/trust/reviews                   — 发表评价
"""
import logging
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.services.trust_score_service import TrustScoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/trust", tags=["信任体系"])


# ── 请求/响应模型 ──────────────────────────────────────────────────────────

class QualificationCreate(BaseModel):
    qualification_type: str = Field(..., description="资质类型: business_license/iso_cert/icp/patent/trademark")
    qualification_name: str = Field(..., description="资质名称")
    cert_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: date = Field(..., description="发证日期 YYYY-MM-DD")
    expiry_date: Optional[date] = None
    file_url: str = ""
    file_hash: str = ""


class ReviewCreate(BaseModel):
    to_user_id: int = Field(..., description="被评价用户ID")
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    content: Optional[str] = None
    order_id: Optional[str] = None
    is_anonymous: bool = False


class TrustScoreOut(BaseModel):
    user_id: int
    total_score: float
    tier: str
    tier_label_cn: str
    snapshot_date: str
    breakdown: dict[str, Any] = {}


# ── 评分端点 ──────────────────────────────────────────────────────────────

@router.get("/score/{user_id}", summary="获取用户信任评分（公开）")
async def get_trust_score(
    user_id: int = Path(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """H08 阳光下行走: 评分完全公开透明"""
    snapshot = await TrustScoreService.get_current(db, user_id)
    if snapshot:
        return TrustScoreOut(
            user_id=user_id,
            total_score=snapshot.score_total,
            tier=snapshot.trust_level,
            tier_label_cn=_tier_label(snapshot.trust_level),
            snapshot_date=snapshot.snapshot_date.isoformat(),
            breakdown=snapshot.calc_metadata or {},
        )
    # 冷启动：无快照返回默认
    return TrustScoreOut(
        user_id=user_id,
        total_score=0.0,
        tier="pending",
        tier_label_cn="待完善",
        snapshot_date=date.today().isoformat(),
        breakdown={"qualification": {"raw_total": 0, "weighted": 0},
                    "transaction": {"raw_total": 0, "weighted": 0},
                    "compliance": {"raw_total": 0, "weighted": 0}},
    )


@router.get("/score/{user_id}/history", summary="评分历史走势（近12月）")
async def get_trust_score_history(
    user_id: int = Path(...),
    months: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
):
    snaps = await TrustScoreService.get_history(db, user_id, months)
    return {
        "user_id": user_id,
        "history": [
            {
                "date": s.snapshot_date.isoformat(),
                "score": s.score_total,
                "tier": s.trust_level,
            }
            for s in snaps
        ],
    }


@router.post("/score/{user_id}/recalc", summary="触发评分重算（登录用户可触发自己的）")
async def recalc_trust_score(
    user_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(status_code=403, detail="无权重算他人评分")
    snap = await TrustScoreService.compute_for_user(
        db, user_id, trigger_source="api", reason="用户手动触发重算"
    )
    return {
        "user_id": user_id,
        "total_score": snap.score_total,
        "tier": snap.trust_level,
        "snapshot_date": snap.snapshot_date.isoformat(),
    }


# ── 资质端点 ──────────────────────────────────────────────────────────────

@router.get("/qualifications", summary="我的资质列表")
async def list_my_qualifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quals = await TrustScoreService.list_qualifications(db, current_user.id)
    return {"qualifications": [q.to_dict() for q in quals]}


@router.post("/qualifications", summary="新增资质", status_code=201)
async def create_qualification(
    payload: QualificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = await TrustScoreService.create_qualification(
        db,
        current_user.id,
        qualification_type=payload.qualification_type,
        qualification_name=payload.qualification_name,
        cert_number=payload.cert_number,
        issuing_authority=payload.issuing_authority,
        issue_date=payload.issue_date,
        expiry_date=payload.expiry_date,
        file_url=payload.file_url,
        file_hash=payload.file_hash,
    )
    # 新增资质后自动重算评分
    try:
        await TrustScoreService.compute_for_user(
            db, current_user.id, trigger_source="api", reason="新增资质触发重算"
        )
    except Exception as exc:
        logger.warning("资质新增后重算失败: %s", exc)
    return q.to_dict()


# ── 评价端点 ──────────────────────────────────────────────────────────────

@router.get("/reviews/{user_id}", summary="用户收到的评价（公开）")
async def get_user_reviews(
    user_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
):
    reviews = await TrustScoreService.list_reviews(db, user_id)
    return {
        "user_id": user_id,
        "reviews": [
            {
                **r.to_dict(),
                "from_anonymous": r.is_anonymous,
                # 匿名时隐藏评价方
                "from_user_id": None if r.is_anonymous else r.from_user_id,
            }
            for r in reviews
        ],
    }


@router.post("/reviews", summary="发表评价", status_code=201)
async def create_review(
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        r = await TrustScoreService.create_review(
            db,
            from_user_id=current_user.id,
            to_user_id=payload.to_user_id,
            rating=payload.rating,
            content=payload.content,
            order_id=payload.order_id,
            is_anonymous=payload.is_anonymous,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    # 被评价方评分重算
    try:
        await TrustScoreService.compute_for_user(
            db, payload.to_user_id, trigger_source="api", reason="新评价触发重算"
        )
    except Exception as exc:
        logger.warning("评价后重算失败: %s", exc)
    return r.to_dict()


# ── 辅助 ──────────────────────────────────────────────────────────────────

def _tier_label(level: str) -> str:
    labels = {
        "pending": "待完善",
        "basic": "基础级",
        "good": "良好级",
        "excellent": "优秀级",
        "top": "顶级",
    }
    return labels.get(level, level)


# ── Mac mini 模型状态上报（供 MLX 推理节点推送） ───────────────────────────
import json as _json
import os as _os
import time as _time

_MAC_REPORT_TOKEN = _os.environ.get("MAC_REPORT_TOKEN", "mac-mini-report-2026")
_MAC_OUT = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
    "data/mac_mini/models_status.json",
)


@router.post("/mac-status", summary="Mac mini 模型状态上报（MLX 节点推送）")
async def receive_mac_status(request: Request):
    """接收 Mac mini 上报的模型状态，写入 data/mac_mini/models_status.json。

    鉴权: header `X-Mac-Token` 必须等于 MAC_REPORT_TOKEN（或默认开发值）。
    """
    token = request.headers.get("X-Mac-Token", "")
    if token != _MAC_REPORT_TOKEN:
        raise HTTPException(status_code=401, detail="无效的 Mac 上报令牌")
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="请求体必须是 JSON")
    if payload.get("device") != "Mac mini":
        raise HTTPException(status_code=400, detail="device 字段必须为 Mac mini")
    payload["received_at"] = _time.strftime("%Y-%m-%d %H:%M:%S")
    _os.makedirs(_os.path.dirname(_MAC_OUT), exist_ok=True)
    with open(_MAC_OUT, "w", encoding="utf-8") as f:
        _json.dump(payload, f, ensure_ascii=False, indent=2)
    return {"ok": True, "received": payload.get("model_count", 0)}
