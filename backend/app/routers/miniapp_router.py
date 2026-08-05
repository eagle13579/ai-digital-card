"""
微信小程序 API 适配路由

将小程序前端调用的 /api/business-card/cards/* 和 /api/matching/* 路径
映射到后端已有的 brochure（画册/名片）和 match（匹配）业务逻辑。

无需修改小程序代码，只需在 app/__init__.py 中注册此适配路由即可。
"""
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.brochure import Brochure, Page
from app.models.connection import Connection
from app.models.platform import PlatformMember
from app.models.tag import MatchRecord
from app.models.user import User
from app.routers.auth import get_current_user, get_optional_user
from app.schemas import (
    BrochureCreate,
    BrochureResponse,
    BrochureUpdate,
    PageSchema,
)
from app.services.share_service import generate_qr_code, build_share_url

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 路由定义
# ═══════════════════════════════════════════════════════════════

# 小程序调用: GET/POST/PUT /api/business-card/cards/...
# 后端映射:   GET/POST/PUT /api/brochures/...
router = APIRouter(prefix="/api/business-card/cards", tags=["miniapp"])

# 小程序也可能调用 POST /api/business-card/exchange（无 /cards 前缀）
exchange_alt_router = APIRouter(prefix="/api/business-card", tags=["miniapp"])

# 小程序调用: GET /api/matching/recommendations
# 后端映射:   POST /api/match/engine
recommend_router = APIRouter(prefix="/api/matching", tags=["miniapp"])


# ── 请求/响应模型 ───────────────────────────────────────────────


class CardExchangeRequest(BaseModel):
    """换名片/交换请求"""
    target_card_id: int = Field(..., description="目标名片 ID")
    message: str = Field("", max_length=256, description="附言")


class CardExchangeResponse(BaseModel):
    """换名片响应"""
    match_id: int
    status: str
    message: str = ""


class RecommendationResponse(BaseModel):
    """推荐结果"""
    user_id: int
    user_name: str
    user_company: str = ""
    user_title: str = ""
    user_avatar: str = ""
    score: float
    common_tags: list[str] = []
    brochure_id: Optional[int] = None
    brochure_title: str = ""


# ── 名片 CRUD 适配 ──────────────────────────────────────────────


@router.get("", response_model=list[BrochureResponse])
async def list_cards(
    user_id: int | None = Query(None, description="按用户ID筛选"),
    status: str | None = Query(None, description="按状态筛选(draft|published)"),
    visibility: str | None = Query(None, description="按可见性筛选(public|platform|network|private)"),
    platform_id: int | None = Query(None, description="按平台ID筛选"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """获取名片列表（适配小程序 GET /api/business-card/cards → GET /api/brochures）

    支持 4 级可见性矩阵过滤：
      - public: 所有人可见
      - platform: 同平台成员可见
      - network: 好友可见
      - private: 仅自己可见
    未登录用户只能看到 public 的资源。
    """
    query = select(Brochure)

    # ── 4级可见性矩阵过滤 ────────────────────────────────────────────
    from sqlalchemy import or_

    visibility_conditions = [Brochure.visibility == "public"]

    if current_user is not None:
        # 自己的资源全部可见
        visibility_conditions.append(Brochure.user_id == current_user.id)

        # platform: 同平台成员可见
        # 查当前用户加入了哪些平台
        platform_subq = (
            select(PlatformMember.platform_id)
            .where(PlatformMember.user_id == current_user.id)
            .subquery()
        )
        visibility_conditions.append(
            (Brochure.visibility == "platform")
            & (Brochure.platform_id.in_(select(platform_subq.c.platform_id)))
        )

        # network: 好友可见
        friend_subq_1 = (
            select(Connection.contact_id)
            .where(Connection.user_id == current_user.id, Connection.status == "approved")
            .subquery()
        )
        friend_subq_2 = (
            select(Connection.user_id)
            .where(Connection.contact_id == current_user.id, Connection.status == "approved")
            .subquery()
        )
        all_friends = select(friend_subq_1.c.contact_id).union(
            select(friend_subq_2.c.user_id)
        ).subquery()
        visibility_conditions.append(
            (Brochure.visibility == "network")
            & (Brochure.user_id.in_(select(all_friends.c.contact_id)))
        )

    query = query.where(or_(*visibility_conditions))
    # ────────────────────────────────────────────────────────────────

    if user_id:
        query = query.where(Brochure.user_id == user_id)
    if status:
        query = query.where(Brochure.status == status)
    if visibility:
        query = query.where(Brochure.visibility == visibility)
    if platform_id:
        query = query.where(Brochure.platform_id == platform_id)

    query = query.order_by(Brochure.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    brochures = result.scalars().all()

    results = []
    for b in brochures:
        resp = BrochureResponse.model_validate(b)
        resp.pages = [PageSchema.model_validate(p) for p in b.pages]
        results.append(resp)
    return results


@router.post("", response_model=BrochureResponse, status_code=201)
async def create_card(
    data: BrochureCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建名片（适配小程序 POST /api/business-card/cards → POST /api/brochures）"""
    brochure = Brochure(
        user_id=current_user.id,
        title=data.title,
        cover=data.cover,
        purpose=data.purpose,
        album_meta=data.album_meta,
        pages_count=len(data.pages),
    )
    db.add(brochure)
    await db.flush()

    for idx, page_data in enumerate(data.pages):
        page = Page(
            brochure_id=brochure.id,
            sort_order=page_data.sort_order or idx,
            content_type=page_data.content_type,
            content=page_data.content,
            image_url=page_data.image_url,
            media_url=page_data.media_url or "",
            ai_summary=page_data.ai_summary,
        )
        db.add(page)

    await db.commit()
    await db.refresh(brochure)
    resp = BrochureResponse.model_validate(brochure)
    resp.pages = [PageSchema.model_validate(p) for p in brochure.pages]
    return resp


@router.get("/{card_id}", response_model=BrochureResponse)
async def get_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取名片详情（适配小程序 GET /api/business-card/cards/{id} → GET /api/brochures/{id}）"""
    result = await db.execute(select(Brochure).where(Brochure.id == card_id))
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="名片不存在")

    resp = BrochureResponse.model_validate(brochure)
    resp.pages = [PageSchema.model_validate(p) for p in brochure.pages]
    return resp


@router.put("/{card_id}", response_model=BrochureResponse)
async def update_card(
    card_id: int,
    data: BrochureUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新名片（适配小程序 PUT /api/business-card/cards/{id} → PUT /api/brochures/{id}）"""
    result = await db.execute(select(Brochure).where(Brochure.id == card_id))
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="名片不存在")
    if brochure.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改此名片")

    update_data = data.model_dump(exclude_unset=True)
    pages_data = update_data.pop("pages", None)

    for field, value in update_data.items():
        setattr(brochure, field, value)

    if pages_data is not None:
        # 删除旧页面，重新添加
        result = await db.execute(select(Page).where(Page.brochure_id == card_id))
        existing_pages = result.scalars().all()
        for p in existing_pages:
            await db.delete(p)

        for idx, page_data in enumerate(pages_data):
            page = Page(
                brochure_id=brochure.id,
                sort_order=page_data.sort_order or idx,
                content_type=page_data.content_type,
                content=page_data.content,
                image_url=page_data.image_url,
                media_url=page_data.media_url or "",
                ai_summary=page_data.ai_summary,
            )
            db.add(page)

        brochure.pages_count = len(pages_data)

    await db.commit()
    await db.refresh(brochure)
    resp = BrochureResponse.model_validate(brochure)
    resp.pages = [PageSchema.model_validate(p) for p in brochure.pages]
    return resp


# ── 换名片（交换）适配 ────────────────────────────────────────


async def _do_exchange_card(
    data: CardExchangeRequest,
    current_user: User,
    db: AsyncSession,
) -> CardExchangeResponse:
    """核心换名片逻辑（被两个路径共享）"""
    # 查目标名片
    result = await db.execute(select(Brochure).where(Brochure.id == data.target_card_id))
    target_brochure = result.scalars().first()
    if target_brochure is None:
        raise HTTPException(status_code=404, detail="目标名片不存在")

    target_user_id = target_brochure.user_id
    if target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能与自己交换名片")

    # 查是否已有匹配记录（双向去重）
    result = await db.execute(
        select(MatchRecord).where(
            or_(
                (MatchRecord.user_a_id == current_user.id) & (MatchRecord.user_b_id == target_user_id),
                (MatchRecord.user_a_id == target_user_id) & (MatchRecord.user_b_id == current_user.id),
            )
        )
    )
    existing = result.scalars().first()
    if existing:
        return CardExchangeResponse(
            match_id=existing.id,
            status=existing.status,
            message="已交换过名片",
        )

    # 创建匹配记录
    record = MatchRecord(
        user_a_id=current_user.id,
        user_b_id=target_user_id,
        match_score=1.0,
        status="matched",
        common_tags=json.dumps([], ensure_ascii=False),
        source="manual",  # 手动交换
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(
        "换名片: user=%d (%s) ↔ target=%d (%s), match_id=%d",
        current_user.id, current_user.name,
        target_user_id, target_brochure.title,
        record.id,
    )

    # ── 触发 CRM 自动匹配钩子 ───────────────────────────────────────
    try:
        from app.crm.match_hook import sync_match_to_crm
        await sync_match_to_crm(db=db, match_record_id=record.id)
    except Exception:
        logger.exception("CRM 自动匹配钩子执行失败（非致命）")
    # ─────────────────────────────────────────────────────────────────

    return CardExchangeResponse(
        match_id=record.id,
        status=record.status,
        message="名片交换成功",
    )


@router.post("/exchange", response_model=CardExchangeResponse)
async def exchange_card(
    data: CardExchangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """换名片（适配小程序 POST /api/business-card/cards/exchange）"""
    return await _do_exchange_card(data, current_user, db)


@exchange_alt_router.post("/exchange", response_model=CardExchangeResponse)
async def exchange_card_alt(
    data: CardExchangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """换名片（备用路径 POST /api/business-card/exchange）"""
    return await _do_exchange_card(data, current_user, db)


# ── 推荐/匹配适配 ────────────────────────────────────────────────


@recommend_router.get("/recommendations", response_model=list[RecommendationResponse])
async def get_recommendations(
    min_score: float = Query(0.3, description="最低匹配分数"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取推荐名片（适配小程序 GET /api/matching/recommendations → POST /api/match/engine）

    基于标签供需关系计算匹配度，返回推荐列表。
    """
    # 延迟导入避免循环依赖
    from app.models.tag import UserTag

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
    for other in other_users:
        result = await db.execute(select(UserTag).where(UserTag.user_id == other.id))
        other_tags = result.scalars().all()
        other_provide_map = {t.tag: t.weight for t in other_tags if t.tag_type == "provide"}
        other_need_map = {t.tag: t.weight for t in other_tags if t.tag_type == "need"}

        score = 0.0
        matched_tags = []

        for tag, weight in my_provide_map.items():
            if tag in other_need_map:
                match_weight = weight * other_need_map[tag]
                score += match_weight
                matched_tags.append(tag)

        for tag, weight in my_need_map.items():
            if tag in other_provide_map:
                match_weight = weight * other_provide_map[tag]
                score += match_weight
                matched_tags.append(tag)

        if score >= min_score:
            # 查找该用户的名片（brochure）
            b_result = await db.execute(
                select(Brochure)
                .where(Brochure.user_id == other.id, Brochure.status == "published")
                .order_by(Brochure.updated_at.desc())
                .limit(1)
            )
            brochure = b_result.scalars().first()

            matches.append(RecommendationResponse(
                user_id=other.id,
                user_name=other.name or "",
                user_company=other.company or "",
                user_title=other.title or "",
                user_avatar=other.avatar or "",
                score=round(score, 2),
                common_tags=matched_tags,
                brochure_id=brochure.id if brochure else None,
                brochure_title=brochure.title if brochure else "",
            ))

    matches.sort(key=lambda x: x.score, reverse=True)
    matches = matches[:limit]

    # 保存匹配记录（top matches）
    for m in matches:
        result = await db.execute(
            select(MatchRecord).where(
                or_(
                    (MatchRecord.user_a_id == current_user.id) & (MatchRecord.user_b_id == m.user_id),
                    (MatchRecord.user_a_id == m.user_id) & (MatchRecord.user_b_id == current_user.id),
                )
            )
        )
        existing = result.scalars().first()
        if not existing:
            record = MatchRecord(
                user_a_id=current_user.id,
                user_b_id=m.user_id,
                match_score=m.score,
                status="matched",
                common_tags=json.dumps(m.common_tags, ensure_ascii=False),
                source="auto",
            )
            db.add(record)

    await db.commit()

    return matches


# ═══════════════════════════════════════════════════════════════
# 小程序码/二维码生成
# ═══════════════════════════════════════════════════════════════

# 小程序调用: GET /api/v1/miniapp/qrcode → 被中间件重写为 GET /api/miniapp/qrcode
miniapp_code_router = APIRouter(prefix="/api/miniapp", tags=["miniapp"])


@miniapp_code_router.get("/qrcode")
async def get_miniapp_qrcode(
    share_token: str = Query(..., description="名片分享 token"),
    width: int = Query(280, ge=100, le=1000, description="二维码图片宽度（像素）"),
    current_user: User = Depends(get_optional_user),
):
    """生成名片二维码图片（使用 qrcode 库生成真实二维码）

    替代前端基于字符串哈希的伪二维码生成。
    返回 Base64 编码的 PNG 图片。（前端 request.js 期望 JSON 响应）

    对接微信小程序码（wxacode.getUnlimited）：
      当设置了 WECHAT_APPID/WECHAT_SECRET 时，自动调用微信API生成小程序码；
      否则使用标准 QR 码（分享到浏览器查看）。
    """
    import base64

    from app.config import settings

    wechat_appid = getattr(settings, "WECHAT_APPID", "") or ""
    wechat_secret = getattr(settings, "WECHAT_SECRET", "") or ""

    img_bytes = None

    # 尝试调用微信小程序码 API
    if wechat_appid and wechat_secret:
        try:
            import httpx

            # 1. 获取 access_token
            async with httpx.AsyncClient() as client:
                token_resp = await client.get(
                    "https://api.weixin.qq.com/cgi-bin/token",
                    params={
                        "grant_type": "client_credential",
                        "appid": wechat_appid,
                        "secret": wechat_secret,
                    },
                )
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    raise ValueError(f"微信 access_token 获取失败: {token_data}")

                # 2. 调用 wxacode.getUnlimited
                code_resp = await client.post(
                    f"https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={access_token}",
                    json={
                        "scene": share_token,
                        "width": width,
                        "auto_color": False,
                        "page": "pages/brochure/preview/index",
                    },
                )
                # 如果返回的是图片二进制（content-type 含 image），直接使用
                content_type = code_resp.headers.get("content-type", "")
                if "image" in content_type:
                    img_bytes = code_resp.content
                else:
                    err_data = code_resp.json()
                    logger.warning("微信小程序码生成返回错误: %s", err_data)
        except Exception as e:
            logger.warning("微信小程序码生成失败，降级到标准 QR 码: %s", e)

    # 降级：使用标准 QR 码（分享到浏览器查看名片）
    if img_bytes is None:
        try:
            img_bytes = generate_qr_code(share_token, box_size=10, border=2)
        except Exception as e:
            logger.error("QR 码生成失败: %s", e)
            raise HTTPException(status_code=500, detail="二维码生成失败")

    # 返回 Base64 编码（前端 request.js 期望 JSON）
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    data_url = f"data:image/png;base64,{b64}"
    return {"code": 0, "message": "success", "data": data_url}
