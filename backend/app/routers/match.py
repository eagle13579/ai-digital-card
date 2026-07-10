import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.vector_search import VectorSearchEngine
from app.agents.agent_runtime import AgentRuntime
from app.database import get_db
from app.dependencies import get_agent_runtime
from app.models.tag import MatchRecord, UserTag
from app.models.user import User, UnlockRecord
from app.routers.auth import get_current_user
from app.routers.brochure import SmartSearchQuery, SmartSearchResponse, execute_smart_search
from app.routers.brochure import PURPOSE_TEMPLATES, PurposeTemplateResponse
from app.schemas import MatchResponse, MatchAction, UnlockRequest, UnlockResponse
from app.services.social_connect_service import SocialConnectService
from app.services.social_match_service import SocialMatchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/match", tags=["匹配"])


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
    name_masked = user.name[:1] + "**" if len(user.name) >= 1 else user.name

    phone = user.phone or ""
    if len(phone) >= 7:
        phone_masked = phone[:3] + "****" + phone[-4:]
    elif len(phone) >= 4:
        phone_masked = phone[:3] + "****"
    else:
        phone_masked = "****"

    company = user.company or ""
    if len(company) >= 2:
        company_masked = company[:2] + "**"
    elif company:
        company_masked = company[0] + "**"
    else:
        company_masked = ""

    avatar = user.avatar or ""
    if avatar and not avatar.endswith("_blur"):
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
        "title": user.title,
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


# ── Agent 通知函数（异步非阻塞） ──────────────────────────────────────


async def _notify_growth_agent(
    agent_runtime: AgentRuntime,
    user_id: int,
    match_count: int,
    top_scores: list[float],
) -> None:
    """异步通知 GrowthAgent 记录匹配事件，用于 A/B 分析和优化建议。

    非阻塞 — Agent 报错不会影响主 API 响应。
    """
    try:
        growth = agent_runtime.get_agent("growth")
        if growth is None:
            logger.warning("GrowthAgent not found, skipping match event notification")
            return
        # 通过 handle_event 发送匹配事件，让 GrowthAgent 进行分析
        await growth.handle_event({
            "type": "match.engine.completed",
            "user_id": user_id,
            "match_count": match_count,
            "top_scores": top_scores,
        })
        logger.info("GrowthAgent notified: user_id=%s, matches=%d", user_id, match_count)
    except Exception:
        logger.exception("GrowthAgent notification failed (non-blocking, safe to ignore)")


@router.post("/engine")
async def run_match_engine(
    min_score: float = Query(0.3, description="最低匹配分数"),
    social: bool = Query(True, description="启用社交路径加权排序（默认开启，false=纯属性匹配）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_runtime: AgentRuntime = Depends(get_agent_runtime),
):
    """匹配引擎：属性匹配 + BFS社交路径加权排序（全面替换）

    匹配流程：
      1. 属性匹配：基于标签供需关系（provide→need）计算初始分数
      2. BFS社交路径增强（social=true，默认）：
         - 对每个候选计算社交距离（BFS，最多3度）
         - social_score = 1.0 / distance（距离越近分越高）
         - final_score = attribute_score × 0.6 + social_score × 0.4
      3. 综合排序：按 final_score 降序排列
      4. social=false 时回退纯属性匹配（兼容旧前端）
    """
    # 获取当前用户的 provide 和 need 标签
    result = await db.execute(
        select(UserTag).where(
            UserTag.user_id == current_user.id,
            UserTag.tag_type == "provide",
        )
    )
    my_provide = result.scalars().all()
    result = await db.execute(
        select(UserTag).where(
            UserTag.user_id == current_user.id,
            UserTag.tag_type == "need",
        )
    )
    my_need = result.scalars().all()

    my_provide_map = {t.tag: t.weight for t in my_provide}
    my_need_map = {t.tag: t.weight for t in my_need}

    # 获取所有其他用户
    result = await db.execute(select(User).where(User.id != current_user.id))
    other_users = result.scalars().all()
    matches = []
    viewer_is_free = not _is_paid_member(current_user)

    for other in other_users:
        result = await db.execute(select(UserTag).where(UserTag.user_id == other.id))
        other_tags = result.scalars().all()
        other_provide_map = {t.tag: t.weight for t in other_tags if t.tag_type == "provide"}
        other_need_map = {t.tag: t.weight for t in other_tags if t.tag_type == "need"}

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
            match_item = {
                "user_id": other.id,
                "user_name": desensitized["name"],
                "user_company": desensitized["company"],
                "user_title": desensitized["title"],
                "user_avatar": desensitized["avatar"],
                "user_phone_masked": desensitized["phone"],
                "score": round(score, 2),
                "common_tags": common_tags,
            }

            # ── BFS社交路径加权（social=True 时计算社交分数） ──
            if social:
                path_result = await SocialConnectService.find_path(
                    db=db, user_id=current_user.id, target_user_id=other.id
                )
                distance = path_result.get("distance", -1)
                match_item["social_distance"] = distance
                match_item["social_path"] = path_result.get("path", [])
                match_item["path_summary"] = path_result.get("message", "无社交连接路径")
                # 社交分数：距离越近分越高（1度=1.0, 2度=0.5, 3度=0.333）
                match_item["social_score"] = round(1.0 / distance, 4) if distance > 0 else 0.0
            else:
                match_item["social_distance"] = -1
                match_item["social_path"] = []
                match_item["path_summary"] = None
                match_item["social_score"] = 0.0

            matches.append(match_item)

    # ── BFS社交路径综合排序 ──────────────────────────────────────────
    if social:
        # 综合评分: 属性分×0.6 + 社交分×0.4
        for m in matches:
            m["final_score"] = round(m["score"] * 0.6 + m.get("social_score", 0.0) * 0.4, 4)
        matches.sort(key=lambda x: x["final_score"], reverse=True)
    else:
        # 纯属性分排序（兼容旧前端）
        for m in matches:
            m["final_score"] = m["score"]
        matches.sort(key=lambda x: x["score"], reverse=True)

    # 保存匹配记录（top matches）
    for m in matches[:20]:
        result = await db.execute(
            select(MatchRecord).where(
                or_(
                    (MatchRecord.user_a_id == current_user.id) & (MatchRecord.user_b_id == m["user_id"]),
                    (MatchRecord.user_a_id == m["user_id"]) & (MatchRecord.user_b_id == current_user.id),
                )
            )
        )
        existing = result.scalars().first()
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

    await db.commit()

    # ── Agent: 异步通知 GrowthAgent 记录匹配事件 ──
    asyncio.create_task(_notify_growth_agent(
        agent_runtime=agent_runtime,
        user_id=current_user.id,
        match_count=len(matches),
        top_scores=[m["score"] for m in matches[:5]],
    ))

    return {
        "matches": matches,
        "total": len(matches),
        "social_enabled": social,
    }


@router.get("/records", response_model=list[MatchResponse])
async def get_match_records(
    status: str | None = Query(None, description="过滤状态"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的匹配记录"""
    query = select(MatchRecord).where(
        (MatchRecord.user_a_id == current_user.id) | (MatchRecord.user_b_id == current_user.id)
    )
    if status:
        query = query.where(MatchRecord.status == status)
    query = query.order_by(MatchRecord.match_score.desc(), MatchRecord.created_at.desc())
    result = await db.execute(query)
    records = result.scalars().all()
    return [MatchResponse.model_validate(r) for r in records]


@router.put("/records/{record_id}/status")
async def update_match_status(
    record_id: int,
    data: MatchAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新匹配记录状态（确认/感兴趣等）"""
    result = await db.execute(select(MatchRecord).where(MatchRecord.id == record_id))
    record = result.scalars().first()
    if record is None:
        raise HTTPException(status_code=404, detail="匹配记录不存在")
    if record.user_a_id != current_user.id and record.user_b_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此记录")

    record.status = data.status
    await db.commit()
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
async def semantic_search(
    data: SemanticSearchQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """语义搜索匹配的用户"""
    vse = VectorSearchEngine(db)
    await vse.build_index()

    results = await vse.search(
        query=data.query,
        top_k=data.top_k,
        min_score=data.min_score,
    )

    viewer_is_free = not _is_paid_member(current_user)
    if viewer_is_free:
        for r in results:
            result = await db.execute(select(User).where(User.id == r.get("user_id")))
            user_obj = result.scalars().first()
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
async def rerank_candidates(
    data: RerankQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """对已有匹配结果做语义重排序"""
    vse = VectorSearchEngine(db)
    reranked = await vse.rerank(
        candidates=data.candidates,
        query=data.query,
        top_k=data.top_k,
    )

    viewer_is_free = not _is_paid_member(current_user)
    if viewer_is_free:
        for r in reranked:
            result = await db.execute(select(User).where(User.id == r.get("user_id")))
            user_obj = result.scalars().first()
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

async def _ensure_quota_reset(user: User, db: AsyncSession) -> None:
    """检查并重置每月解锁配额"""
    from datetime import datetime
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if user.quota_reset_at is None or user.quota_reset_at < month_start:
        from app.config import settings
        QUOTA_MAP = {
            "free": settings.MEMBERSHIP_FREE_QUOTA,
            "gold": settings.MEMBERSHIP_GOLD_QUOTA,
            "diamond": settings.MEMBERSHIP_DIAMOND_QUOTA,
            "board": settings.MEMBERSHIP_BOARD_QUOTA,
        }
        user.unlock_quota = QUOTA_MAP.get(user.membership_tier, 0)
        user.quota_reset_at = now
        await db.commit()


@router.post("/{record_id}/unlock", response_model=UnlockResponse)
async def unlock_contact(
    record_id: int,
    data: UnlockRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """付费解锁匹配对象的联系方式"""
    # 1. 查找匹配记录
    result = await db.execute(select(MatchRecord).where(MatchRecord.id == record_id))
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="匹配记录不存在")

    # 2. 确认用户是匹配参与方
    if record.user_a_id != current_user.id and record.user_b_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此匹配记录")

    # 3. 确定目标用户
    target_user_id = record.user_b_id if record.user_a_id == current_user.id else record.user_a_id
    result = await db.execute(select(User).where(User.id == target_user_id))
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    # 4. 检查会员状态
    if not _is_paid_member(current_user):
        raise HTTPException(
            status_code=402,
            detail="需要付费会员才能解锁联系方式，请升级会员",
        )

    # 5. 检查并重置配额
    await _ensure_quota_reset(current_user, db)

    # 6. 配额检查
    if current_user.unlock_quota <= 0:
        raise HTTPException(
            status_code=402,
            detail="本月解锁配额已用尽，请升级会员获取更多配额",
        )

    # 7. 检查是否已经解锁过（幂等）
    result = await db.execute(
        select(UnlockRecord).where(
            UnlockRecord.user_id == current_user.id,
            UnlockRecord.target_user_id == target_user_id,
            UnlockRecord.match_record_id == record_id,
        )
    )
    existing = result.scalars().first()

    if existing:
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
    await db.commit()
    await db.refresh(current_user)

    return UnlockResponse(
        unlocked=True,
        name=target_user.name,
        phone=target_user.phone,
        wechat=target_user.wechat_openid or "",
        company=target_user.company,
        unlock_quota_remaining=current_user.unlock_quota,
        message="解锁成功",
    )


# ── 社交路径增强匹配 API ────────────────────────────────────────────


@router.get("/social")
async def social_match_search(
    q: str = Query("", description="搜索关键词（模糊匹配 name / company / title）"),
    industry: str = Query("", description="行业标签过滤"),
    city: str = Query("", description="城市过滤"),
    limit: int = Query(20, ge=1, le=100, description="返回数量上限"),
    include_path: bool = Query(True, description="是否包含BFS社交触达路径"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """语义搜索 + 社交路径增强

    在关键词/行业/城市匹配的基础上，增加BFS社交路径维度：
    - 有社交路径的结果排在无社交路径前面
    - 返回结果附带社交距离和路径摘要

    Returns:
        {code: 0, data: {items: [...], total: int}, message: "success"}
    """
    items = await SocialMatchService.match_with_social_path(
        db=db,
        viewer_id=current_user.id,
        keyword=q,
        industry=industry,
        city=city,
        limit=limit,
        include_path=include_path,
    )
    return {
        "code": 0,
        "data": {
            "items": items,
            "total": len(items),
        },
        "message": "success",
    }


@router.get("/social/recommend")
async def social_based_recommendations(
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
    min_strength: float = Query(0.0, ge=0.0, le=1.0, description="最小关系强度阈值"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """基于社交图谱的人脉推荐（二度/三度人脉）

    从当前用户的社交网络出发，推荐可能认识的人：
    1. 直接好友（一度人脉）
    2. 好友的好友（二度人脉）
    3. 二度人脉的好友（三度人脉）

    排序: 人脉近优先 > 关系强度高优先 > 新用户优先

    Returns:
        {code: 0, data: {items: [...], total: int}, message: "success"}
    """
    items = await SocialMatchService.get_social_based_recommendations(
        db=db,
        viewer_id=current_user.id,
        limit=limit,
        min_strength=min_strength,
    )
    return {
        "code": 0,
        "data": {
            "items": items,
            "total": len(items),
        },
        "message": "success",
    }


# ── 别名路由：POST /api/v1/brochure/smart-search ────────────────────────

brochure_alias_router = APIRouter(prefix="/api/v1/brochure", tags=["画册别名"])


@brochure_alias_router.post("/smart-search")
async def brochure_smart_search(
    data: SmartSearchQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """智能搜索名片（别名路由）"""
    results = await execute_smart_search(
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
async def brochure_template_alias(purpose: str):
    """获取用途推荐模板配置（别名路由）"""
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
