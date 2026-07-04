"""链客宝 — App Store API（插件市场 + 提交 + 审核）
====================================================
端点:
  GET    /api/app-store/plugins                — 插件列表（搜索+分类+排序）
  GET    /api/app-store/plugins/{id}           — 插件详情
  POST   /api/app-store/plugins                — 提交插件（开发者）
  PUT    /api/app-store/plugins/{id}           — 更新插件
  DELETE /api/app-store/plugins/{id}           — 删除插件（开发者本人/管理员）
  POST   /api/app-store/plugins/{id}/versions  — 发布新版本
  POST   /api/app-store/plugins/{id}/install   — 安装（用户）
  POST   /api/app-store/plugins/{id}/uninstall — 卸载
  POST   /api/app-store/plugins/{id}/reviews   — 审核（管理员）
  GET    /api/app-store/categories             — 分类列表
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func as sa_func, desc, or_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.app_store import (
    Plugin,
    PluginVersion,
    PluginReview,
    PluginInstall,
    PluginCreate,
    PluginUpdate,
    VersionCreate,
    ReviewCreate,
    RewardRedemptionCreate,
)
from app.models.user import User
from app.core.response import api_success, api_created, api_deleted, api_paginated, api_error

logger = logging.getLogger("chainke.app_store")

# ===================================================================
# Router
# ===================================================================
router = APIRouter(prefix="/api/app-store", tags=["App Store"])

PLUGIN_CATEGORIES = [
    "tools",
    "analytics",
    "automation",
    "communication",
    "ai",
    "custom",
]

PLUGIN_STATUSES = ["draft", "pending", "review", "published", "rejected"]


# ===================================================================
# 依赖
# ===================================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_current_user(db: Session, user_id: int = Query(None)) -> User | None:
    """简易获取用户（生产环境应替换为真正的 Auth 中间件）"""
    if user_id is None:
        return None
    return db.query(User).filter(User.id == user_id).first()


def _require_user(db: Session, user_id: int) -> User:
    user = _get_current_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="未登录或用户不存在")
    return user


def _require_admin(db: Session, user_id: int) -> User:
    user = _require_user(db, user_id)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# ===================================================================
# API: 插件列表（搜索+分类+排序）
# ===================================================================
@router.get("/plugins")
def list_plugins(
    search: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    status: Optional[str] = Query("published", description="状态筛选"),
    sort_by: str = Query("created_at", description="排序: created_at/install_count/rating/price"),
    sort_order: str = Query("desc", description="排序方向: asc/desc"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    query = db.query(Plugin)

    # 搜索
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Plugin.name.ilike(search_term),
                Plugin.description.ilike(search_term),
                Plugin.tags.ilike(search_term),
            )
        )

    # 分类筛选
    if category:
        query = query.filter(Plugin.category == category)

    # 状态筛选
    if status:
        query = query.filter(Plugin.status == status)

    # 排序
    sort_column = getattr(Plugin, sort_by, Plugin.created_at)
    order_func = desc if sort_order == "desc" else sa_func.asc
    query = query.order_by(order_func(sort_column))

    # 分页
    total = query.count()
    offset = (page - 1) * page_size
    plugins = query.offset(offset).limit(page_size).all()

    items = [p.to_dict() for p in plugins]
    return api_paginated(items, page, page_size, total)


# ===================================================================
# API: 插件详情
# ===================================================================
@router.get("/plugins/{plugin_id}")
def get_plugin(
    plugin_id: int,
    include_versions: bool = Query(False, description="是否包含版本列表"),
    include_reviews: bool = Query(False, description="是否包含审核记录"),
    db: Session = Depends(get_db),
):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    return api_success(plugin.to_dict(include_versions=include_versions, include_reviews=include_reviews))


# ===================================================================
# API: 提交插件（开发者）
# ===================================================================
@router.post("/plugins", status_code=201)
def create_plugin(
    data: PluginCreate,
    developer_id: int = Query(..., description="开发者用户 ID"),
    db: Session = Depends(get_db),
):
    user = _require_user(db, developer_id)

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
    logger.info("[AppStore] 开发者 %d 创建插件「%s」(id=%d)", developer_id, data.name, plugin.id)
    return api_created(plugin.to_dict(), message="插件创建成功")


# ===================================================================
# API: 更新插件
# ===================================================================
@router.put("/plugins/{plugin_id}")
def update_plugin(
    plugin_id: int,
    data: PluginUpdate,
    user_id: int = Query(..., description="用户 ID"),
    db: Session = Depends(get_db),
):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")

    user = _require_user(db, user_id)
    if plugin.developer_id != user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="只能编辑自己的插件")

    # 只允许修改草稿状态
    if plugin.status not in ("draft", "rejected"):
        raise HTTPException(status_code=400, detail="只能修改草稿或被驳回的插件")

    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(plugin, field, value)
    plugin.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plugin)
    logger.info("[AppStore] 插件 %d 已更新", plugin_id)
    return api_success(plugin.to_dict(), message="插件更新成功")


# ===================================================================
# API: 删除插件
# ===================================================================
@router.delete("/plugins/{plugin_id}")
def delete_plugin(
    plugin_id: int,
    user_id: int = Query(..., description="用户 ID"),
    db: Session = Depends(get_db),
):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")

    user = _require_user(db, user_id)
    if plugin.developer_id != user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="只能删除自己的插件")

    db.delete(plugin)
    db.commit()
    logger.info("[AppStore] 插件 %d 已删除", plugin_id)
    return api_deleted(message="插件已删除")


# ===================================================================
# API: 发布新版本
# ===================================================================
@router.post("/plugins/{plugin_id}/versions", status_code=201)
def create_version(
    plugin_id: int,
    data: VersionCreate,
    user_id: int = Query(..., description="用户 ID"),
    db: Session = Depends(get_db),
):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")

    user = _require_user(db, user_id)
    if plugin.developer_id != user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="只能为自有插件发布版本")

    # 检查版本号是否已存在
    existing = db.query(PluginVersion).filter(
        PluginVersion.plugin_id == plugin_id,
        PluginVersion.version == data.version,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"版本 {data.version} 已存在")

    version = PluginVersion(
        plugin_id=plugin_id,
        version=data.version,
        changelog=data.changelog or "",
        download_url=data.download_url or "",
        required_api_version=data.required_api_version or "1.0.0",
        file_size=data.file_size,
        checksum=data.checksum or "",
        is_published=0,
    )
    db.add(version)

    # 更新插件主版本号
    plugin.version = data.version
    plugin.status = "pending"  # 提交新版本后进入待审核
    plugin.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(version)
    logger.info("[AppStore] 插件 %d 发布版本 %s", plugin_id, data.version)
    return api_created(version.to_dict(), message="版本创建成功，进入待审核")


# ===================================================================
# API: 安装插件
# ===================================================================
@router.post("/plugins/{plugin_id}/install")
def install_plugin(
    plugin_id: int,
    user_id: int = Query(..., description="用户 ID"),
    db: Session = Depends(get_db),
):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    if plugin.status != "published":
        raise HTTPException(status_code=400, detail="只能安装已发布的插件")

    user = _require_user(db, user_id)

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
    plugin.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(install)
    logger.info("[AppStore] 用户 %d 安装插件 %d", user_id, plugin_id)
    return api_success(install.to_dict(), message="安装成功")


# ===================================================================
# API: 卸载插件
# ===================================================================
@router.post("/plugins/{plugin_id}/uninstall")
def uninstall_plugin(
    plugin_id: int,
    user_id: int = Query(..., description="用户 ID"),
    db: Session = Depends(get_db),
):
    install = db.query(PluginInstall).filter(
        PluginInstall.plugin_id == plugin_id,
        PluginInstall.user_id == user_id,
        PluginInstall.is_active == 1,
    ).first()
    if not install:
        raise HTTPException(status_code=404, detail="未安装该插件")

    install.is_active = 0
    install.uninstalled_at = datetime.utcnow()

    # 减少安装计数（不低于0）
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if plugin and plugin.install_count > 0:
        plugin.install_count -= 1
        plugin.updated_at = datetime.utcnow()

    db.commit()
    logger.info("[AppStore] 用户 %d 卸载插件 %d", user_id, plugin_id)
    return api_success(message="卸载成功")


# ===================================================================
# API: 审核（管理员）
# ===================================================================
@router.post("/plugins/{plugin_id}/reviews")
def review_plugin(
    plugin_id: int,
    data: ReviewCreate,
    reviewer_id: int = Query(..., description="审核员 ID"),
    db: Session = Depends(get_db),
):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    if plugin.status not in ("pending", "review"):
        raise HTTPException(status_code=400, detail="插件不在待审核状态")

    reviewer = _require_admin(db, reviewer_id)

    review = PluginReview(
        plugin_id=plugin_id,
        reviewer_id=reviewer_id,
        status=data.status,
        comments=data.comments or "",
    )
    db.add(review)

    # 更新插件状态
    if data.status == "approved":
        plugin.status = "published"
        # 发布最新版本
        latest_version = db.query(PluginVersion).filter(
            PluginVersion.plugin_id == plugin_id,
            PluginVersion.version == plugin.version,
        ).first()
        if latest_version:
            latest_version.is_published = 1
    else:
        plugin.status = "rejected"

    plugin.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(review)
    logger.info("[AppStore] 审核员 %d 审核插件 %d: %s", reviewer_id, plugin_id, data.status)
    return api_success(review.to_dict(), message=f"审核完成: {data.status}")


# ===================================================================
# API: 分类列表
# ===================================================================
@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """返回预定义分类列表及每个分类的插件数量"""
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


# ═══════════════════════════════════════════════════════════════════
# 开发者奖励 API
# ═══════════════════════════════════════════════════════════════════


@router.get("/leaderboard")
def get_leaderboard(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db),
):
    """获取开发者积分排行榜"""
    from app.services.developer_rewards import get_leaderboard as _get_leaderboard
    entries = _get_leaderboard(db, limit=limit, offset=offset)
    return api_success([e.model_dump() for e in entries])


@router.get("/developers/{developer_id}/rewards")
def get_developer_rewards(
    developer_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取开发者奖励记录"""
    from app.services.developer_rewards import get_developer_rewards as _get_rewards
    from app.services.developer_rewards import get_developer_balance as _get_balance
    rewards = _get_rewards(db, developer_id, limit=limit, offset=offset)
    balance = _get_balance(db, developer_id)
    total = db.query(Plugin).filter(Plugin.developer_id == developer_id).count()
    return api_success({
        "balance": balance.to_dict() if balance else {"balance": 0, "total_points": 0, "used_points": 0},
        "rewards": [r.to_dict() for r in rewards],
        "plugin_count": total,
    })


@router.get("/developers/{developer_id}/redemptions")
def get_developer_redemptions(
    developer_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取开发者兑换记录"""
    from app.services.developer_rewards import get_developer_redemptions as _get_redemptions
    redemptions = _get_redemptions(db, developer_id, limit=limit, offset=offset)
    return api_success([r.to_dict() for r in redemptions])


@router.post("/developers/{developer_id}/redeem")
def redeem_points(
    developer_id: int,
    data: RewardRedemptionCreate,
    db: Session = Depends(get_db),
):
    """积分兑换"""
    from app.services.developer_rewards import redeem_rewards as _redeem
    user = _require_user(db, developer_id)
    redemption = _redeem(db, developer_id, data)
    if not redemption:
        raise HTTPException(status_code=400, detail="积分不足或兑换失败")
    db.commit()
    db.refresh(redemption)
    logger.info("[AppStore] 开发者 %d 积分兑换: %s, 消耗 %d", developer_id, data.redemption_type, data.points_spent)
    return api_success(redemption.to_dict(), message="兑换成功")


@router.post("/developers/{developer_id}/rewards/issue")
def issue_developer_rewards(
    developer_id: int,
    db: Session = Depends(get_db),
):
    """发放开发者所有待发放奖励"""
    from app.services.developer_rewards import issue_rewards as _issue
    user = _require_user(db, developer_id)
    total = _issue(db, developer_id)
    db.commit()
    return api_success({"points_issued": total}, message=f"已发放 {total} 积分")


# ═══════════════════════════════════════════════════════════════════
# 开发者插件管理
# ═══════════════════════════════════════════════════════════════════


@router.get("/developers/{developer_id}/plugins")
def get_developer_plugins(
    developer_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取开发者所有插件"""
    query = db.query(Plugin).filter(Plugin.developer_id == developer_id)
    if status:
        query = query.filter(Plugin.status == status)
    query = query.order_by(desc(Plugin.created_at))
    total = query.count()
    offset = (page - 1) * page_size
    plugins = query.offset(offset).limit(page_size).all()
    return api_paginated([p.to_dict() for p in plugins], page, page_size, total)


# ═══════════════════════════════════════════════════════════════════
# Community Stats API
# ═══════════════════════════════════════════════════════════════════


@router.get("/stats/community")
def get_community_stats(db: Session = Depends(get_db)):
    """获取社区统计概览数据"""
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 总插件数
    total_plugins = db.query(Plugin).filter(Plugin.status == "published").count()

    # 本月新增
    new_plugins = db.query(Plugin).filter(
        Plugin.status == "published",
        Plugin.created_at >= month_start,
    ).count()

    # 总安装量
    total_installs = db.query(sa_func.coalesce(sa_func.sum(Plugin.install_count), 0)).filter(
        Plugin.status == "published"
    ).scalar() or 0

    # 上月安装量（用于增长率）
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    # 活跃开发者
    active_devs = db.query(Plugin.developer_id).filter(
        Plugin.status == "published"
    ).distinct().count()

    # 本月新开发者
    new_devs = db.query(Plugin.developer_id).filter(
        Plugin.status == "published",
        Plugin.created_at >= month_start,
    ).distinct().count()

    return api_success({
        "total_plugins": total_plugins,
        "new_plugins_this_month": new_plugins,
        "total_installs": total_installs,
        "active_developers": active_devs,
        "new_developers_this_month": new_devs,
        "updated_at": now.isoformat(),
    })
