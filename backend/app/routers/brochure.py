import asyncio
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_standards import PaginatedResponse, paginate_cursor
from app.database import get_db
from app.models.brochure import Brochure, Page
from app.models.user import User
from app.models.tag import UserTag
from app.routers.auth import get_current_user
from app.schemas import BrochureCreate, BrochureUpdate, BrochureResponse, PageSchema
from app.services.matching_engine import MatchEngine
from app.services.brochure import BrochureService
from sqlalchemy.orm import selectinload
from app.ai.vector_search import VectorSearchEngine
from app.services.media_service import MediaService

router = APIRouter(prefix="/api/v1/brochures", tags=["画册"])


# ── 用途推荐模板配置 ──────────────────────────────────


# 各用途对应的主题色、推荐布局和突出模块
PURPOSE_TEMPLATES = {
    "partner": {
        "name": "找合作伙伴",
        "theme": {
            "primary": "#f5576c",
            "secondary": "#f093fb",
            "gradient": "linear-gradient(135deg, #f093fb, #f5576c)",
            "bg_start": "#1a0a1e",
            "bg_mid": "#2d1b3a",
            "bg_end": "#1a0f1e",
            "accent": "rgba(245,87,108,0.15)",
        },
        "pages": [
            {"type": "cover", "title": "🤝 合作封面", "hint": "填写您的团队背景与合作意向"},
            {"type": "text", "title": "👥 团队背景", "hint": "介绍核心团队成员的资历与专长"},
            {"type": "text", "title": "🏆 合作案例", "hint": "展示过往成功合作案例"},
            {"type": "text", "title": "🔗 合作模式", "hint": "说明开放的合作方式（技术/渠道/资源）"},
            {"type": "image", "title": "📱 联系方式", "hint": "二维码及联系方式"},
        ],
        "highlights": ["团队背景", "合作案例", "合作模式"],
        "suggested_sections": [
            {"icon": "👥", "label": "团队背景", "description": "核心团队介绍与行业经验"},
            {"icon": "🏆", "label": "合作案例", "description": "过往合作成果与客户评价"},
            {"icon": "🔗", "label": "合作模式", "description": "技术联合/渠道共享/资源互换"},
        ],
    },
    "client": {
        "name": "找客户",
        "theme": {
            "primary": "#4ade80",
            "secondary": "#22c55e",
            "gradient": "linear-gradient(135deg, #4ade80, #22c55e)",
            "bg_start": "#0a1a0e",
            "bg_mid": "#1a2d1b",
            "bg_end": "#0e1a0f",
            "accent": "rgba(74,222,128,0.15)",
        },
        "pages": [
            {"type": "cover", "title": "💼 服务封面", "hint": "填写您的产品/服务名称与定位"},
            {"type": "text", "title": "🛎️ 产品/服务", "hint": "详细介绍您的核心产品与服务内容"},
            {"type": "text", "title": "⭐ 客户案例", "hint": "展示成功客户案例与口碑"},
            {"type": "text", "title": "🎁 优惠方案", "hint": "列出当前优惠套餐或报价方案"},
            {"type": "image", "title": "📱 联系方式", "hint": "二维码及咨询方式"},
        ],
        "highlights": ["产品/服务", "客户案例", "优惠方案"],
        "suggested_sections": [
            {"icon": "🛎️", "label": "产品/服务", "description": "核心产品与服务内容介绍"},
            {"icon": "⭐", "label": "客户案例", "description": "成功案例与客户评价"},
            {"icon": "🎁", "label": "优惠方案", "description": "当前优惠套餐与报价"},
        ],
    },
    "investor": {
        "name": "找投资人",
        "theme": {
            "primary": "#facc15",
            "secondary": "#eab308",
            "gradient": "linear-gradient(135deg, #facc15, #eab308)",
            "bg_start": "#1a1a0a",
            "bg_mid": "#2d2d1b",
            "bg_end": "#1a1a0e",
            "accent": "rgba(250,204,21,0.15)",
        },
        "pages": [
            {"type": "cover", "title": "📈 融资封面", "hint": "填写项目名称与融资轮次"},
            {"type": "text", "title": "👥 团队背景", "hint": "核心团队资历与行业背景"},
            {"type": "text", "title": "💰 融资历程", "hint": "历史融资情况与当前计划"},
            {"type": "text", "title": "📊 数据增长", "hint": "展示关键业务数据与增长曲线"},
            {"type": "text", "title": "🌐 市场规模", "hint": "目标市场规模与增长潜力分析"},
            {"type": "image", "title": "📱 联系投资人", "hint": "BP获取方式及联系方式"},
        ],
        "highlights": ["团队背景", "融资历程", "数据增长", "市场规模"],
        "suggested_sections": [
            {"icon": "👥", "label": "团队背景", "description": "核心团队介绍与行业经验"},
            {"icon": "💰", "label": "融资历程", "description": "融资历史与当前轮次计划"},
            {"icon": "📊", "label": "数据增长", "description": "关键指标与增长趋势"},
            {"icon": "🌐", "label": "市场规模", "description": "目标市场与增长潜力"},
        ],
    },
    "supplier": {
        "name": "找供应商",
        "theme": {
            "primary": "#60a5fa",
            "secondary": "#3b82f6",
            "gradient": "linear-gradient(135deg, #60a5fa, #3b82f6)",
            "bg_start": "#0a0e1a",
            "bg_mid": "#1b1f2d",
            "bg_end": "#0e0f1a",
            "accent": "rgba(96,165,250,0.15)",
        },
        "pages": [
            {"type": "cover", "title": "🔧 供应商封面", "hint": "填写公司名称与采购品类"},
            {"type": "text", "title": "📦 采购需求", "hint": "详细描述需要采购的产品/服务类别"},
            {"type": "text", "title": "✅ 资质认证", "hint": "列出需要的供应商资质与认证要求"},
            {"type": "text", "title": "📋 合作流程", "hint": "说明采购流程与供应商合作方式"},
            {"type": "image", "title": "📱 联系方式", "hint": "采购联系人二维码及联系方式"},
        ],
        "highlights": ["采购需求", "资质认证", "合作流程"],
        "suggested_sections": [
            {"icon": "📦", "label": "采购需求", "description": "具体采购品类与规格要求"},
            {"icon": "✅", "label": "资质认证", "description": "供应商资质与认证要求"},
            {"icon": "📋", "label": "合作流程", "description": "采购流程与合作方式说明"},
        ],
    },
}


class PurposeTemplateResponse(BaseModel):
    purpose: str
    name: str
    theme: dict
    pages: list[dict]
    highlights: list[str]
    suggested_sections: list[dict]

    model_config = {"json_schema_extra": {
        "example": {
            "purpose": "partner",
            "name": "找合作伙伴",
            "theme": {
                "primary": "#f5576c",
                "secondary": "#f093fb",
                "gradient": "linear-gradient(135deg, #f093fb, #f5576c)",
                "bg_start": "#1a0a1e",
                "bg_mid": "#2d1b3a",
                "bg_end": "#1a0f1e",
                "accent": "rgba(245,87,108,0.15)",
            },
            "pages": [
                {"type": "cover", "title": "🤝 合作封面", "hint": "填写您的团队背景与合作意向"},
            ],
            "highlights": ["团队背景", "合作案例", "合作模式"],
            "suggested_sections": [
                {"icon": "👥", "label": "团队背景", "description": "核心团队介绍与行业经验"},
            ],
        }
    }}


@router.get("/template/{purpose}", response_model=PurposeTemplateResponse)
async def get_purpose_template(purpose: str):
    """获取指定用途的推荐模板配置（主题色、页面结构、推荐模块）"""
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


@router.post("", response_model=BrochureResponse)
async def create_brochure(
    data: BrochureCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建画册"""
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

    # 重新查询（含pages关系）
    result = await db.execute(
        select(Brochure).options(selectinload(Brochure.pages)).where(Brochure.id == brochure.id)
    )
    brochure = result.scalars().first()
    resp = BrochureResponse.model_validate(brochure)
    resp.pages = [PageSchema.model_validate(p) for p in (brochure.pages or [])]

    # 创建画册后自动触发匹配池（异步执行，不阻塞响应）
    asyncio.create_task(_trigger_matching_pool(db, current_user.id))

    return resp


@router.get("", response_model=PaginatedResponse[BrochureResponse])
async def list_brochures(
    cursor: str | None = Query(None, description="分页游标（首次请求不传）"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    user_id: int | None = Query(None, description="按用户ID筛选"),
    status: str | None = Query(None, description="按状态筛选(draft|published)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取画册列表（cursor 分页）"""
    query = select(Brochure).options(selectinload(Brochure.pages))
    if user_id:
        query = query.where(Brochure.user_id == user_id)
    if status:
        query = query.where(Brochure.status == status)
    return await paginate_cursor(
        db, query, cursor=cursor, page_size=page_size,
        cursor_column=Brochure.id, response_model=BrochureResponse,
    )


@router.get("/{brochure_id}", response_model=BrochureResponse)
async def get_brochure(
    brochure_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取画册详情（含页面数据）"""
    result = await db.execute(
        select(Brochure).options(selectinload(Brochure.pages)).where(Brochure.id == brochure_id)
    )
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")

    resp = BrochureResponse.model_validate(brochure)
    resp.pages = [PageSchema.model_validate(p) for p in brochure.pages]
    return resp


@router.get("/share/{share_token}", response_model=BrochureResponse)
async def get_brochure_by_share_token(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    """通过分享token获取画册（公开访问）"""
    result = await db.execute(
        select(Brochure).options(selectinload(Brochure.pages)).where(Brochure.share_token == share_token)
    )
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在或链接已失效")

    # 增加访问计数
    brochure.view_count += 1
    await db.commit()

    resp = BrochureResponse.model_validate(brochure)
    resp.pages = [PageSchema.model_validate(p) for p in brochure.pages]
    return resp


@router.put("/{brochure_id}", response_model=BrochureResponse)
async def update_brochure(
    brochure_id: int,
    data: BrochureUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新画册"""
    result = await db.execute(select(Brochure).where(Brochure.id == brochure_id))
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")
    if brochure.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改此画册")

    update_data = data.model_dump(exclude_unset=True)
    pages_data = update_data.pop("pages", None)

    for field, value in update_data.items():
        setattr(brochure, field, value)

    if pages_data is not None:
        # 删除旧页面，重新添加
        result = await db.execute(select(Page).where(Page.brochure_id == brochure_id))
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


@router.delete("/{brochure_id}")
async def delete_brochure(
    brochure_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除画册"""
    result = await db.execute(select(Brochure).where(Brochure.id == brochure_id))
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")
    if brochure.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此画册")

    await db.delete(brochure)
    await db.commit()
    return {"detail": "画册已删除"}


@router.post("/{brochure_id}/publish", response_model=BrochureResponse)
async def publish_brochure(
    brochure_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发布画册"""
    result = await db.execute(select(Brochure).where(Brochure.id == brochure_id))
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")
    if brochure.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权发布此画册")

    brochure.status = "published"
    # 刷新分享token
    brochure.share_token = uuid.uuid4().hex[:16]
    await db.commit()
    await db.refresh(brochure)
    resp = BrochureResponse.model_validate(brochure)
    resp.pages = [PageSchema.model_validate(p) for p in brochure.pages]

    # 发布画册后自动触发匹配池
    asyncio.create_task(_trigger_matching_pool(db, current_user.id))

    return resp


@router.post("/{brochure_id}/refresh-token")
async def refresh_share_token(
    brochure_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """刷新分享token"""
    result = await db.execute(select(Brochure).where(Brochure.id == brochure_id))
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")
    if brochure.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此画册")

    brochure.share_token = uuid.uuid4().hex[:16]
    await db.commit()
    return {"share_token": brochure.share_token}


# ── 匹配池自动触发 ──────────────────────────────────


async def _trigger_matching_pool(db: AsyncSession, user_id: int) -> None:
    """创建/发布画册后自动触发匹配池：计算该用户与其他用户的匹配度。

    异步执行，不阻塞 API 响应。
    使用独立会话以避免跨任务共享会话。
    """
    try:
        from app.database import AsyncSessionLocal
        from app.services.matching_engine import MatchEngine

        async with AsyncSessionLocal() as session:
            await MatchEngine.get_daily_recommendations(
                db=session,
                user_id=user_id,
                limit=20,
                min_score=0.1,
            )
            logger.info("匹配池已触发: user_id=%s", user_id)
    except Exception as exc:
        logger.warning("匹配池触发失败（降级）: user_id=%s, error=%s", user_id, exc)


# ── 智能搜索（自然语言搜索名片）─────────────────────────────────────────


class SmartSearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="自然语言搜索文本，如'找Python全栈开发者'")
    top_k: int = Field(10, ge=1, le=50, description="返回结果数量上限")
    mode: str = Field("hybrid", pattern=r"^(hybrid|vector|keyword)$", description="搜索模式：hybrid混合/vector语义/keyword关键词")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="最低分数阈值")


class SmartSearchResponse(BaseModel):
    query: str
    mode: str
    results: list[dict]
    total: int


async def execute_smart_search(
    db: AsyncSession,
    query_text: str,
    current_user_id: int,
    top_k: int = 10,
    mode: str = "hybrid",
    min_score: float = 0.0,
) -> list[dict]:
    """执行智能搜索的核心逻辑（可被路由和别名路由复用）"""
    if not query_text.strip():
        return []

    if mode == "hybrid":
        results = await MatchEngine.hybrid_search(
            db=db,
            query_text=query_text,
            current_user_id=current_user_id,
            top_k=top_k,
        )
        results = [r for r in results if r["score"] >= min_score]

    elif mode == "vector":
        vse = VectorSearchEngine(db)
        await vse.build_index()
        raw = await vse.search(
            query=query_text,
            top_k=top_k,
            min_score=min_score,
            exclude_user_id=current_user_id,
        )
        results = [
            {
                "user_id": r["user_id"],
                "user_name": r["user_name"],
                "user_company": r.get("user_company", ""),
                "user_title": r.get("user_title", ""),
                "user_avatar": r.get("user_avatar", ""),
                "score": r["score"],
                "keyword_score": 0.0,
                "vector_score": r["score"],
                "source": "vector",
            }
            for r in raw
        ]

    else:  # keyword
        result = await db.execute(select(User).where(User.id != current_user_id))
        other_users = result.scalars().all()
        query_lower = query_text.lower()
        results = []
        for other in other_users:
            searchable = f"{other.name or ''} {other.intro or ''} {other.company or ''} {other.title or ''}".lower()
            result = await db.execute(select(UserTag).where(UserTag.user_id == other.id))
            tags = result.scalars().all()
            searchable += " " + " ".join([t.tag for t in tags]).lower()

            if query_lower in searchable:
                score = 0.5
                for term in query_lower.split():
                    score += 0.05 * searchable.count(term)
                score = min(1.0, score)
                results.append({
                    "user_id": other.id,
                    "user_name": other.name,
                    "user_company": other.company or "",
                    "user_title": other.title or "",
                    "user_avatar": other.avatar or "",
                    "score": round(score, 4),
                    "keyword_score": round(score, 4),
                    "vector_score": 0.0,
                    "source": "keyword",
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:top_k]

    return results


@router.post("/smart-search")
async def smart_search(
    data: SmartSearchQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """智能搜索名片（自然语言搜索）"""
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


# ── 视频上传 ──────────────────────────────────────────────────


class VideoUploadResponse(BaseModel):
    url: str
    original_name: str
    size: int
    transcoded: bool


@router.post("/upload-video", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """上传视频文件（mp4/webm），返回可访问的媒体 URL"""
    result = await MediaService.handle_video_upload(
        file=file,
        user_id=current_user.id,
        transcode=True,
    )
    return VideoUploadResponse(**result)


# ── 图片上传 ──────────────────────────────────────────────────


class ImageUploadResponse(BaseModel):
    url: str
    original_name: str
    size: int


@router.post("/upload-image", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """上传图片文件（jpg/png/webp，≤5MB），返回可访问的图片 URL"""
    result = await MediaService.handle_image_upload(
        file=file,
        user_id=current_user.id,
    )
    return ImageUploadResponse(**result)


@router.post("/batch-import")
async def batch_import(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量导入名片(CSV)"""
    content = await file.read()
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content.decode("gbk", errors="replace")
    result = await BrochureService.batch_import_from_csv(db, current_user.id, csv_text)
    return {"code": 200, "data": result}

@router.post("/batch-export")
async def batch_export(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量导出名片为CSV"""
    csv_output = await BrochureService.batch_export_csv(db, current_user.id, {"status": status} if status else None)
    from fastapi.responses import StreamingResponse
    import io
    return StreamingResponse(
        io.BytesIO(csv_output.encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=business_cards.csv"},
    )
