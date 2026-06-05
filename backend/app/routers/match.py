import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.ai.vector_search import VectorSearchEngine
from app.database import get_db
from app.models.tag import MatchRecord, UserTag
from app.models.user import User, UnlockRecord
from app.routers.auth import get_current_user
from app.routers.brochure import SmartSearchQuery, SmartSearchResponse, execute_smart_search
from app.routers.brochure import PURPOSE_TEMPLATES, PurposeTemplateResponse
from app.schemas import MatchResponse, MatchAction, UnlockRequest, UnlockResponse

router = APIRouter(prefix="/api/match", tags=["匹配"])


# ── 脱敏工具函数 ────────────────────────────────────────────────────────────

def _desensitize_user(user: User, viewer_is_free: bool = True) -> dict:
    """对用户信息脱敏处理

    当 viewer_is_free=True 时，对展示信息做脱敏：
    - 姓名：张**（首字+2星）
    - 电话：138****5678（前3+4星+后4）
    - 微信：完全隐藏
    - 头像：返回模糊版（附加 _blur 后缀）
    - 公司名：保留前2字+**
    """
    if not viewer_is_free:
        # 付费用户看到完整信息
        return {
            "name": user.name,
            "phone": user.phone,
            "company": user.company,
            "title": user.title,
            "avatar": user.avatar,
        }

    # ── free 会员脱敏 ──
    # 姓名：只保留首字
    name_masked = user.name[:1] + "**" if len(user.name) >= 1 else user.name

    # 电话：前3+4星+后4
    phone = user.phone or ""
    if len(phone) >= 7:
        phone_masked = phone[:3] + "****" + phone[-4:]
    elif len(phone) >= 4:
        phone_masked = phone[:3] + "****"
    else:
        phone_masked = "****"

    # 公司：保留前2字+**
    company = user.company or ""
    if len(company) >= 2:
        company_masked = company[:2] + "**"
    elif company:
        company_masked = company[0] + "**"
    else:
        company_masked = ""

    # 头像：加模糊后缀（前端根据后缀做模糊处理）
    avatar = user.avatar or ""
    if avatar and not avatar.endswith("_blur"):
        # 在文件名后追加 _blur 标记，前端据此做高斯模糊
        dot_idx = avatar.rfind(".")
        if dot_idx > 0:
            avatar_blur = avatar[:dot_idx] + "_blur" + avatar[dot_idx:]
        else:
            avatar_blur = avatar + "_blur"
    else:
        avatar_blur = avatar

    return {
        "name": name_masked,
        "phone": phone_masked,
        "company": company_masked,
        "title": user.title,  # 职位不脱敏
        "avatar": avatar_blur,
    }


def _is_paid_member(user: User) -> bool:
    """检查用户是否为付费会员（gold/diamond/board）且未过期"""
    from datetime import datetime
    if user.membership_tier in ("gold", "diamond", "board"):
        if user.membership_expires_at is None:
            return True  # 永不过期视为有效
        return user.membership_expires_at > datetime.utcnow()
    return False


@router.post("/engine")
def run_match_engine(
    min_score: float = Query(0.3, description="最低匹配分数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """匹配引擎：基于标签供需关系计算用户匹配度

    算法：对于每个其他用户，计算 provide→need 交集作为匹配度。
    A 的 provide 标签 ∩ B 的 need 标签 的加权和。
    """
    # 获取当前用户的 provide 和 need 标签
    my_provide = db.query(UserTag).filter(
        UserTag.user_id == current_user.id,
        UserTag.tag_type == "provide",
    ).all()
    my_need = db.query(UserTag).filter(
        UserTag.user_id == current_user.id,
        UserTag.tag_type == "need",
    ).all()

    my_provide_map = {t.tag: t.weight for t in my_provide}
    my_need_map = {t.tag: t.weight for t in my_need}

    # 获取所有其他用户
    other_users = db.query(User).filter(User.id != current_user.id).all()
    matches = []
    viewer_is_free = not _is_paid_member(current_user)

    for other in other_users:
        other_tags = db.query(UserTag).filter(UserTag.user_id == other.id).all()
        other_provide_map = {t.tag: t.weight for t in other_tags if t.tag_type == "provide"}
        other_need_map = {t.tag: t.weight for t in other_tags if t.tag_type == "need"}

        # 分数 = 我能提供 ∩ 对方需要 + 对方提供 ∩ 我需要
        score = 0.0
        common_tags = []

        for tag, weight in my_provide_map.items():
            if tag in other_need_map:
                match_weight = weight * other_need_map[tag]
                score += match_weight
                common_tags.append({"tag": tag, "direction": "我提供→对方需要", "weight": match_weight})

        for tag, weight in my_need_map.items():
            if tag in other_provide_map:
                match_weight = weight * other_provide_map[tag]
                score += match_weight
                common_tags.append({"tag": tag, "direction": "我需要→对方提供", "weight": match_weight})

        if score >= min_score:
            desensitized = _desensitize_user(other, viewer_is_free)
            matches.append({
                "user_id": other.id,
                "user_name": desensitized["name"],
                "user_company": desensitized["company"],
                "user_title": desensitized["title"],
                "user_avatar": desensitized["avatar"],
                "user_phone_masked": desensitized["phone"],  # 始终为脱敏版
                "score": round(score, 2),
                "common_tags": common_tags,
            })

    # 按分数降序排列
    matches.sort(key=lambda x: x["score"], reverse=True)

    # 保存匹配记录（top matches）
    for m in matches[:20]:
        existing = db.query(MatchRecord).filter(
            or_(
                (MatchRecord.user_a_id == current_user.id) & (MatchRecord.user_b_id == m["user_id"]),
                (MatchRecord.user_a_id == m["user_id"]) & (MatchRecord.user_b_id == current_user.id),
            )
        ).first()
        if not existing:
            record = MatchRecord(
                user_a_id=current_user.id,
                user_b_id=m["user_id"],
                match_score=m["score"],
                status="matched",
                common_tags=json.dumps([ct["tag"] for ct in m["common_tags"]], ensure_ascii=False),
                source="auto",
            )
            db.add(record)

    db.commit()

    return {
        "matches": matches,
        "total": len(matches),
    }


@router.get("/records", response_model=list[MatchResponse])
def get_match_records(
    status: str | None = Query(None, description="过滤状态"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的匹配记录"""
    query = db.query(MatchRecord).filter(
        (MatchRecord.user_a_id == current_user.id) | (MatchRecord.user_b_id == current_user.id)
    )
    if status:
        query = query.filter(MatchRecord.status == status)
    records = query.order_by(MatchRecord.match_score.desc(), MatchRecord.created_at.desc()).all()
    return [MatchResponse.model_validate(r) for r in records]


@router.put("/records/{record_id}/status")
def update_match_status(
    record_id: int,
    data: MatchAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新匹配记录状态（确认/感兴趣等）"""
    record = db.query(MatchRecord).filter(MatchRecord.id == record_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="匹配记录不存在")
    if record.user_a_id != current_user.id and record.user_b_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此记录")

    record.status = data.status
    db.commit()
    return {"detail": f"状态已更新为 {data.status}"}


# ── 请求模型 ─────────────────────────────────────────────────────────────

class SemanticSearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="搜索文本，如'Python全栈开发'")
    top_k: int = Field(10, ge=1, le=50, description="返回结果数量上限")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="最低相似度阈值")


class RerankQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="重排序查询文本")
    candidates: list[dict] = Field(..., min_length=1, description="待重排序的候选列表（每项必须含 user_id）")
    top_k: Optional[int] = Field(None, ge=1, le=50, description="返回结果数量上限（默认全部）")


# ── 新 API 端点 ─────────────────────────────────────────────────────────

# ── 脱敏语义搜索 ──────────────────────────────────────────────────────────

@router.post("/semantic-search")
def semantic_search(
    data: SemanticSearchQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """语义搜索匹配的用户

    基于 TF-IDF + Cosine Similarity，对输入文本做语义搜索，
    返回匹配度最高的用户列表。

    适用于：自由文本搜索（如"找Python全栈开发者"）
    """
    vse = VectorSearchEngine(db)
    vse.build_index()

    results = vse.search(
        query=data.query,
        top_k=data.top_k,
        min_score=data.min_score,
    )

    # 对结果脱敏
    viewer_is_free = not _is_paid_member(current_user)
    if viewer_is_free:
        for r in results:
            user_obj = db.query(User).filter(User.id == r.get("user_id")).first()
            if user_obj:
                masked = _desensitize_user(user_obj, viewer_is_free=True)
                r["user_name"] = masked["name"]
                r["company"] = masked["company"]
                r["avatar"] = masked["avatar"]

    return {
        "query": data.query,
        "results": results,
        "total": len(results),
    }


@router.post("/rerank")
def rerank_candidates(
    data: RerankQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对已有匹配结果做语义重排序

    使用 TF-IDF 余弦相似度对候选列表重新计算语义相关性并排序。

    适用于：对 /api/match/engine 的结果做二次语义排序
    """
    vse = VectorSearchEngine(db)
    reranked = vse.rerank(
        candidates=data.candidates,
        query=data.query,
        top_k=data.top_k,
    )

    # 对结果脱敏
    viewer_is_free = not _is_paid_member(current_user)
    if viewer_is_free:
        for r in reranked:
            user_obj = db.query(User).filter(User.id == r.get("user_id")).first()
            if user_obj:
                masked = _desensitize_user(user_obj, viewer_is_free=True)
                r["user_name"] = masked["name"]
                r["company"] = masked["company"]
                r["avatar"] = masked["avatar"]

    return {
        "query": data.query,
        "results": reranked,
        "total": len(reranked),
    }


# ── 付费解锁 API ─────────────────────────────────────────────────────────

def _ensure_quota_reset(user: User, db: Session) -> None:
    """检查并重置每月解锁配额

    如果 quota_reset_at 早于本月1日，则根据会员等级重置配额。
    """
    from datetime import datetime
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if user.quota_reset_at is None or user.quota_reset_at < month_start:
        # 重置配额
        from app.config import settings
        QUOTA_MAP = {
            "free": settings.MEMBERSHIP_FREE_QUOTA,
            "gold": settings.MEMBERSHIP_GOLD_QUOTA,
            "diamond": settings.MEMBERSHIP_DIAMOND_QUOTA,
            "board": settings.MEMBERSHIP_BOARD_QUOTA,
        }
        user.unlock_quota = QUOTA_MAP.get(user.membership_tier, 0)
        user.quota_reset_at = now
        db.commit()


@router.post("/{record_id}/unlock", response_model=UnlockResponse)
def unlock_contact(
    record_id: int,
    data: UnlockRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """付费解锁匹配对象的联系方式

    检查用户会员等级+配额→扣减配额→记录解锁记录→返回联系方式。
    配额不足时返回错误码+引导升级。
    """
    # 1. 查找匹配记录
    record = db.query(MatchRecord).filter(MatchRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="匹配记录不存在")

    # 2. 确认用户是匹配参与方
    if record.user_a_id != current_user.id and record.user_b_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此匹配记录")

    # 3. 确定目标用户
    target_user_id = record.user_b_id if record.user_a_id == current_user.id else record.user_a_id
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    # 4. 检查会员状态
    if not _is_paid_member(current_user):
        raise HTTPException(
            status_code=402,
            detail="需要付费会员才能解锁联系方式，请升级会员",
        )

    # 5. 检查并重置配额
    _ensure_quota_reset(current_user, db)

    # 6. 配额检查
    if current_user.unlock_quota <= 0:
        raise HTTPException(
            status_code=402,
            detail="本月解锁配额已用尽，请升级会员获取更多配额",
        )

    # 7. 检查是否已经解锁过（幂等）
    existing = db.query(UnlockRecord).filter(
        UnlockRecord.user_id == current_user.id,
        UnlockRecord.target_user_id == target_user_id,
        UnlockRecord.match_record_id == record_id,
    ).first()

    if existing:
        # 已解锁过，直接返回联系方式（不扣配额）
        return UnlockResponse(
            unlocked=True,
            name=target_user.name,
            phone=target_user.phone,
            wechat=target_user.wechat_openid or "",
            company=target_user.company,
            unlock_quota_remaining=current_user.unlock_quota,
            message="已解锁，可直接查看联系方式",
        )

    # 8. 扣减配额
    current_user.unlock_quota -= 1

    # 9. 记录解锁记录
    unlock = UnlockRecord(
        user_id=current_user.id,
        target_user_id=target_user_id,
        match_record_id=record_id,
    )
    db.add(unlock)
    db.commit()
    db.refresh(current_user)

    return UnlockResponse(
        unlocked=True,
        name=target_user.name,
        phone=target_user.phone,
        wechat=target_user.wechat_openid or "",
        company=target_user.company,
        unlock_quota_remaining=current_user.unlock_quota,
        message="解锁成功",
    )


# ── 别名路由：POST /api/brochure/smart-search ────────────────────────────
# 智能搜索名义上是 brochure 的能力，但语义上属于匹配/推荐范畴
# brochure router 注册在 /api/brochures 下（复数）
# 这里使用独立 router 提供 /api/brochure（单数）作为别名

brochure_alias_router = APIRouter(prefix="/api/brochure", tags=["画册别名"])


@brochure_alias_router.post("/smart-search")
def brochure_smart_search(
    data: SmartSearchQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """智能搜索名片（别名路由）

    与 POST /api/brochures/smart-search 功能完全一致。
    提供 /api/brochure/smart-search 路径访问（单数brochure）。
    """
    results = execute_smart_search(
        db=db,
        query_text=data.query,
        current_user_id=current_user.id,
        top_k=data.top_k,
        mode=data.mode,
        min_score=data.min_score,
    )

    return SmartSearchResponse(
        query=data.query,
        mode=data.mode,
        results=results,
        total=len(results),
    )


@brochure_alias_router.get("/template/{purpose}", response_model=PurposeTemplateResponse)
def brochure_template_alias(purpose: str):
    """获取用途推荐模板配置（别名路由）

    与 GET /api/brochures/template/{purpose} 功能完全一致。
    提供 GET /api/brochure/template/{purpose} 路径访问（单数brochure）。
    """
    if purpose not in PURPOSE_TEMPLATES:
        raise HTTPException(
            status_code=404,
            detail=f"不支持的用途: {purpose}，可选值: partner, client, investor, supplier",
        )
    template = PURPOSE_TEMPLATES[purpose]
    return PurposeTemplateResponse(
        purpose=purpose,
        name=template["name"],
        theme=template["theme"],
        pages=template["pages"],
        highlights=template["highlights"],
        suggested_sections=template["suggested_sections"],
    )
