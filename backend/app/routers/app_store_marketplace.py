"""AI数智名片 — App Store Marketplace API
============================================
公开市场端点（前缀 /api/v1/marketplace）：
  1. GET    /plugins                – 插件列表（分类/搜索/分页）
  2. GET    /plugins/{id}           – 插件详情 + 版本列表
  3. POST   /plugins                – 开发者提交插件
  4. PUT    /plugins/{id}           – 更新插件
  5. POST   /plugins/{id}/install   – 用户安装插件
  6. DELETE /plugins/{id}/install   – 卸载插件
  7. GET    /my-installs            – 当前用户已安装列表
  8. POST   /plugins/{id}/review    – 用户评价
  9. GET    /categories             – 分类列表
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func as sa_func, desc, asc, or_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.app_store import (
    Plugin,
    PluginVersion,
    PluginInstall,
    PluginCreate,
    PluginUpdate,
)
from app.models.user import User
from app.core.response import api_success, api_created, api_deleted, api_paginated

logger = logging.getLogger("chainke.app_store_marketplace")

# ── Router ──────────────────────────────────────────────────────────────────
router = APIRouter(prefix="/api/v1/marketplace", tags=["App Store Marketplace"])

# ── 分类常量 ────────────────────────────────────────────────────────────────
PLUGIN_CATEGORIES = [
    "tools",
    "analytics",
    "automation",
    "communication",
    "ai",
    "custom",
]

# ── Pydantic Schemas ──────────────────────────────────────────────────────


class UserReviewCreate(BaseModel):
    """用户评分/评价请求"""
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    comment: Optional[str] = Field(None, max_length=500, description="评价内容")


# ── 依赖 ───────────────────────────────────────────────────────────────────


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user_optional(
    token: Optional[str] = None,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """可选的当前用户获取（未登录则返回 None）"""
    try:
        from app.routers.auth import get_current_user as _auth_user
        return await _auth_user(token, db)
    except Exception:
        return None


# ── 1. GET /plugins — 插件列表（支持分类/搜索/分页）─────────────────────


@router.get("/plugins")
def list_plugins(
    search: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    sort_by: str = Query("created_at", description="排序字段: created_at/install_count/rating/price"),
    sort_order: str = Query("desc", description="排序方向: asc/desc"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取插件列表，支持分类、搜索、分页和排序"""
    query = db.query(Plugin).filter(Plugin.status == "published")

    # 搜索（名称/描述/标签）
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Plugin.name.ilike(term),
                Plugin.description.ilike(term),
                Plugin.tags.ilike(term),
            )
        )

    # 分类筛选
    if category:
        query = query.filter(Plugin.category == category)

    # 排序
    sort_column = getattr(Plugin, sort_by, Plugin.created_at)
    order_func = desc if sort_order == "desc" else asc
    query = query.order_by(order_func(sort_column))

    # 分页
    total = query.count()
    offset = (page - 1) * page_size
    plugins = query.offset(offset).limit(page_size).all()

    items = [p.to_dict() for p in plugins]
    return api_paginated(items, page, page_size, total)


# ── 2. GET /plugins/{id} — 插件详情 + 版本列表 ────────────────────────────


@router.get("/plugins/{plugin_id}")
def get_plugin_detail(
    plugin_id: int,
    db: Session = Depends(get_db),
):
    """获取插件详情，包含版本列表"""
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    return api_success(plugin.to_dict(include_versions=True))


# ── 3. POST /plugins — 开发者提交插件 ──────────────────────────────────────


@router.post("/plugins", status_code=201)
def create_plugin(
    data: PluginCreate,
    developer_id: int = Query(..., description="开发者用户 ID"),
    db: Session = Depends(get_db),
):
    """开发者提交新插件"""
    # 检查用户存在
    user = db.query(User).filter(User.id == developer_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    # 检查同名插件
    existing = db.query(Plugin).filter(Plugin.name == data.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"插件「{data.name}」已存在")

    plugin = Plugin(
        developer_id=developer_id,
        name=data.name,
        description=data.description or "",
        icon_url=data.icon_url or "",
        category=data.category,
        price=max(0.0, data.price),
        status="draft",
        version="1.0.0",
        homepage_url=data.homepage_url or "",
        documentation_url=data.documentation_url or "",
        repository_url=data.repository_url or "",
        tags=data.tags or "",
    )
    db.add(plugin)
    db.commit()
    db.refresh(plugin)
    logger.info("[Marketplace] 开发者 %d 创建插件「%s」(id=%d)", developer_id, data.name, plugin.id)
    return api_created(plugin.to_dict(), message="插件创建成功")


# ── 4. PUT /plugins/{id} — 更新插件 ──────────────────────────────────────


@router.put("/plugins/{plugin_id}")
def update_plugin(
    plugin_id: int,
    data: PluginUpdate,
    user_id: int = Query(..., description="用户 ID"),
    db: Session = Depends(get_db),
):
    """更新插件信息（仅开发者本人或管理员可操作）"""
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if plugin.developer_id != user_id and getattr(user, "role", "") != "admin":
        raise HTTPException(status_code=403, detail="只能编辑自己的插件")

    if plugin.status not in ("draft", "rejected"):
        raise HTTPException(status_code=400, detail="只能修改草稿或被驳回的插件")

    update_data = data.model_dump(exclude_none=True)
    from datetime import datetime
    for field, value in update_data.items():
        setattr(plugin, field, value)
    plugin.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plugin)
    logger.info("[Marketplace] 插件 %d 已更新", plugin_id)
    return api_success(plugin.to_dict(), message="插件更新成功")


# ── 5. POST /plugins/{id}/install — 用户安装插件 ──────────────────────────


@router.post("/plugins/{plugin_id}/install", status_code=201)
def install_plugin(
    plugin_id: int,
    user_id: int = Query(..., description="用户 ID"),
    db: Session = Depends(get_db),
):
    """用户安装插件"""
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    if plugin.status != "published":
        raise HTTPException(status_code=400, detail="只能安装已发布的插件")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    # 检查是否已安装
    existing = db.query(PluginInstall).filter(
        PluginInstall.plugin_id == plugin_id,
        PluginInstall.user_id == user_id,
        PluginInstall.is_active == 1,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="已安装该插件")

    install = PluginInstall(
        plugin_id=plugin_id,
        user_id=user_id,
        is_active=1,
    )
    db.add(install)

    # 增加安装计数
    plugin.install_count = (plugin.install_count or 0) + 1
    from datetime import datetime
    plugin.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(install)
    logger.info("[Marketplace] 用户 %d 安装插件 %d", user_id, plugin_id)
    return api_success(install.to_dict(), message="安装成功")


# ── 6. DELETE /plugins/{id}/install — 卸载插件 ────────────────────────────


@router.delete("/plugins/{plugin_id}/install")
def uninstall_plugin(
    plugin_id: int,
    user_id: int = Query(..., description="用户 ID"),
    db: Session = Depends(get_db),
):
    """用户卸载插件"""
    install = db.query(PluginInstall).filter(
        PluginInstall.plugin_id == plugin_id,
        PluginInstall.user_id == user_id,
        PluginInstall.is_active == 1,
    ).first()
    if not install:
        raise HTTPException(status_code=404, detail="未安装该插件")

    from datetime import datetime
    install.is_active = 0
    install.uninstalled_at = datetime.utcnow()

    # 减少安装计数（不低于0）
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if plugin and plugin.install_count > 0:
        plugin.install_count -= 1
        plugin.updated_at = datetime.utcnow()

    db.commit()
    logger.info("[Marketplace] 用户 %d 卸载插件 %d", user_id, plugin_id)
    return api_success(message="卸载成功")


# ── 7. GET /my-installs — 当前用户已安装列表 ─────────────────────────────


@router.get("/my-installs")
def list_my_installs(
    user_id: int = Query(..., description="用户 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取当前用户已安装的插件列表"""
    query = (
        db.query(PluginInstall)
        .filter(
            PluginInstall.user_id == user_id,
            PluginInstall.is_active == 1,
        )
        .order_by(desc(PluginInstall.installed_at))
    )

    total = query.count()
    offset = (page - 1) * page_size
    installs = query.offset(offset).limit(page_size).all()

    # 附加插件信息
    items = []
    for inst in installs:
        item = inst.to_dict()
        plugin = db.query(Plugin).filter(Plugin.id == inst.plugin_id).first()
        if plugin:
            item["plugin"] = {
                "id": plugin.id,
                "name": plugin.name,
                "icon_url": plugin.icon_url or "",
                "category": plugin.category,
                "version": plugin.version,
                "description": plugin.description or "",
            }
        items.append(item)

    return api_paginated(items, page, page_size, total)


# ── 8. POST /plugins/{id}/review — 用户评价 ──────────────────────────────


@router.post("/plugins/{plugin_id}/review")
def review_plugin(
    plugin_id: int,
    data: UserReviewCreate,
    user_id: int = Query(..., description="用户 ID"),
    db: Session = Depends(get_db),
):
    """用户对插件进行评分和评价"""
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    if plugin.status != "published":
        raise HTTPException(status_code=400, detail="只能评价已发布的插件")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    # 检查用户是否已安装（未安装也能评价）
    # 使用滑动平均更新评分
    current_total = plugin.rating * plugin.rating_count
    plugin.rating_count += 1
    plugin.rating = round((current_total + data.rating) / plugin.rating_count, 1)

    from datetime import datetime
    plugin.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plugin)

    logger.info(
        "[Marketplace] 用户 %d 评价插件 %d: rating=%d/5",
        user_id, plugin_id, data.rating,
    )
    return api_success({
        "plugin_id": plugin_id,
        "user_id": user_id,
        "rating": data.rating,
        "comment": data.comment or "",
        "new_average_rating": plugin.rating,
        "rating_count": plugin.rating_count,
    }, message="评价成功")


# ── 9. GET /categories — 分类列表 ─────────────────────────────────────────


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """返回预定义分类列表及每个分类已发布插件的数量"""
    categories = []
    for cat in PLUGIN_CATEGORIES:
        count = db.query(Plugin).filter(
            Plugin.category == cat,
            Plugin.status == "published",
        ).count()
        categories.append({
            "slug": cat,
            "name": cat.capitalize(),
            "count": count,
        })
    return api_success(categories)
