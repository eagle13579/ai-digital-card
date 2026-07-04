"""链客宝 — App Store 数据模型
====================================
Plugin: 插件主表
PluginVersion: 插件版本
PluginReview: 插件审核记录
PluginInstall: 用户安装记录
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Plugin(Base):
    """插件主表"""
    __tablename__ = "app_store_plugins"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    developer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="开发者用户 ID")
    name = Column(String(128), nullable=False, comment="插件名称")
    description = Column(Text, nullable=True, comment="插件描述")
    icon_url = Column(String(512), nullable=True, comment="图标 URL")
    category = Column(String(64), nullable=False, index=True, comment="分类: tools/analytics/automation/communication/ai/custom")
    version = Column(String(32), nullable=False, default="1.0.0", comment="当前版本号")
    price = Column(Float, nullable=False, default=0.0, comment="价格 (0=免费)")
    status = Column(
        String(20), nullable=False, default="draft", index=True,
        comment="状态: draft/pending/review/published/rejected"
    )
    install_count = Column(Integer, nullable=False, default=0, comment="安装次数")
    rating = Column(Float, nullable=False, default=0.0, comment="评分 (0-5)")
    rating_count = Column(Integer, nullable=False, default=0, comment="评分人数")
    homepage_url = Column(String(512), nullable=True, comment="项目主页")
    documentation_url = Column(String(512), nullable=True, comment="文档地址")
    repository_url = Column(String(512), nullable=True, comment="源码仓库")
    tags = Column(String(512), nullable=True, comment="标签 (逗号分隔)")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # Relationships
    versions = relationship("PluginVersion", back_populates="plugin", cascade="all, delete-orphan",
                            order_by="PluginVersion.created_at.desc()")
    reviews = relationship("PluginReview", back_populates="plugin", cascade="all, delete-orphan",
                           order_by="PluginReview.created_at.desc()")
    installations = relationship("PluginInstall", back_populates="plugin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Plugin(id={self.id}, name={self.name}, status={self.status})>"

    def to_dict(self, include_versions: bool = False, include_reviews: bool = False) -> dict:
        data = {
            "id": self.id,
            "developer_id": self.developer_id,
            "name": self.name,
            "description": self.description or "",
            "icon_url": self.icon_url or "",
            "category": self.category,
            "version": self.version,
            "price": self.price,
            "status": self.status,
            "install_count": self.install_count,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "homepage_url": self.homepage_url or "",
            "documentation_url": self.documentation_url or "",
            "repository_url": self.repository_url or "",
            "tags": self.tags or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_versions:
            data["versions"] = [v.to_dict() for v in (self.versions or [])]
        if include_reviews:
            data["reviews"] = [r.to_dict() for r in (self.reviews or [])]
        return data


class PluginVersion(Base):
    """插件版本表"""
    __tablename__ = "app_store_plugin_versions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plugin_id = Column(Integer, ForeignKey("app_store_plugins.id"), nullable=False, index=True)
    version = Column(String(32), nullable=False, comment="版本号 (semver)")
    changelog = Column(Text, nullable=True, comment="更新日志")
    download_url = Column(String(512), nullable=True, comment="下载地址")
    required_api_version = Column(String(32), nullable=False, default="1.0.0", comment="最低 API 版本")
    file_size = Column(Integer, nullable=True, comment="文件大小 (字节)")
    checksum = Column(String(128), nullable=True, comment="文件校验和 (SHA256)")
    is_published = Column(Integer, nullable=False, default=0, comment="是否发布 (0/1)")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    plugin = relationship("Plugin", back_populates="versions")

    def __repr__(self):
        return f"<PluginVersion(id={self.id}, plugin_id={self.plugin_id}, version={self.version})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plugin_id": self.plugin_id,
            "version": self.version,
            "changelog": self.changelog or "",
            "download_url": self.download_url or "",
            "required_api_version": self.required_api_version,
            "file_size": self.file_size,
            "checksum": self.checksum or "",
            "is_published": bool(self.is_published),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PluginReview(Base):
    """插件审核记录"""
    __tablename__ = "app_store_plugin_reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plugin_id = Column(Integer, ForeignKey("app_store_plugins.id"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="审核员 ID")
    status = Column(String(20), nullable=False, comment="审核结果: approved/rejected")
    comments = Column(Text, nullable=True, comment="审核意见")
    created_at = Column(DateTime, default=func.now(), comment="审核时间")

    plugin = relationship("Plugin", back_populates="reviews")

    def __repr__(self):
        return f"<PluginReview(id={self.id}, plugin_id={self.plugin_id}, status={self.status})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plugin_id": self.plugin_id,
            "reviewer_id": self.reviewer_id,
            "status": self.status,
            "comments": self.comments or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PluginInstall(Base):
    """用户插件安装记录"""
    __tablename__ = "app_store_plugin_installs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plugin_id = Column(Integer, ForeignKey("app_store_plugins.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="安装者")
    version_id = Column(Integer, ForeignKey("app_store_plugin_versions.id"), nullable=True, comment="安装版本")
    is_active = Column(Integer, nullable=False, default=1, comment="是否已安装")
    installed_at = Column(DateTime, default=func.now(), comment="安装时间")
    uninstalled_at = Column(DateTime, nullable=True, comment="卸载时间")

    plugin = relationship("Plugin", back_populates="installations")

    def __repr__(self):
        return f"<PluginInstall(id={self.id}, plugin_id={self.plugin_id}, user_id={self.user_id})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plugin_id": self.plugin_id,
            "user_id": self.user_id,
            "version_id": self.version_id,
            "is_active": bool(self.is_active),
            "installed_at": self.installed_at.isoformat() if self.installed_at else None,
            "uninstalled_at": self.uninstalled_at.isoformat() if self.uninstalled_at else None,
        }


# ── Pydantic schemas ──────────────────────────────────────────────────────────

from pydantic import BaseModel, Field


class PluginCreate(BaseModel):
    """创建插件请求"""
    name: str = Field(..., min_length=1, max_length=128, description="插件名称")
    description: Optional[str] = Field(None, description="插件描述")
    icon_url: Optional[str] = Field(None, max_length=512, description="图标 URL")
    category: str = Field(..., description="分类: tools/analytics/automation/communication/ai/custom")
    price: float = Field(0.0, ge=0, description="价格 (0=免费)")
    homepage_url: Optional[str] = Field(None, max_length=512)
    documentation_url: Optional[str] = Field(None, max_length=512)
    repository_url: Optional[str] = Field(None, max_length=512)
    tags: Optional[str] = Field(None, max_length=512)


class PluginUpdate(BaseModel):
    """更新插件请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    icon_url: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    homepage_url: Optional[str] = None
    documentation_url: Optional[str] = None
    repository_url: Optional[str] = None
    tags: Optional[str] = None


class VersionCreate(BaseModel):
    """创建版本请求"""
    version: str = Field(..., min_length=1, max_length=32, description="版本号 (semver)")
    changelog: Optional[str] = None
    download_url: Optional[str] = Field(None, max_length=512)
    required_api_version: str = Field("1.0.0", max_length=32)
    file_size: Optional[int] = None
    checksum: Optional[str] = Field(None, max_length=128)


class ReviewCreate(BaseModel):
    """审核请求"""
    status: str = Field(..., pattern=r"^(approved|rejected)$", description="审核结果")
    comments: Optional[str] = None


# ── 开发者奖励模型 ──────────────────────────────────────────────────────


class DeveloperRewardType:
    """奖励类型常量"""
    INSTALL = "install"           # 安装奖励
    QUALITY = "quality"           # 质量奖励
    ACTIVITY = "activity"         # 活动奖励
    BONUS = "bonus"               # 额外奖励


class DeveloperRewardStatus:
    """奖励状态常量"""
    PENDING = "pending"           # 待发放
    ISSUED = "issued"             # 已发放
    CANCELLED = "cancelled"       # 已取消


class DeveloperReward(Base):
    """开发者奖励记录"""
    __tablename__ = "developer_rewards"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    developer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="开发者 ID")
    reward_type = Column(String(32), nullable=False, comment="奖励类型: install/quality/activity/bonus")
    points = Column(Integer, nullable=False, default=0, comment="奖励积分")
    reason = Column(String(256), nullable=True, comment="奖励原因")
    source_id = Column(Integer, nullable=True, comment="来源 ID (如插件ID)")
    source_desc = Column(String(128), nullable=True, comment="来源描述")
    status = Column(String(20), nullable=False, default="pending", comment="状态: pending/issued/cancelled")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    issued_at = Column(DateTime, nullable=True, comment="发放时间")

    def __repr__(self):
        return f"<DeveloperReward(dev={self.developer_id}, type={self.reward_type}, points={self.points}, status={self.status})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "developer_id": self.developer_id,
            "reward_type": self.reward_type,
            "points": self.points,
            "reason": self.reason or "",
            "source_id": self.source_id,
            "source_desc": self.source_desc or "",
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
        }


class DeveloperRewardBalance(Base):
    """开发者积分余额"""
    __tablename__ = "developer_reward_balances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    developer_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True, comment="开发者 ID")
    total_points = Column(Integer, nullable=False, default=0, comment="总获得积分")
    used_points = Column(Integer, nullable=False, default=0, comment="已使用积分")
    balance = Column(Integer, nullable=False, default=0, comment="可用余额")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def to_dict(self) -> dict:
        return {
            "developer_id": self.developer_id,
            "total_points": self.total_points,
            "used_points": self.used_points,
            "balance": self.balance,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RewardRedemption(Base):
    """积分兑换记录"""
    __tablename__ = "reward_redemptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    developer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="开发者 ID")
    points_spent = Column(Integer, nullable=False, comment="花费积分")
    redemption_type = Column(String(32), nullable=False, comment="兑换类型: api_quota/promotion")
    quota_amount = Column(Integer, nullable=True, comment="兑换数量 (如 API 调用次数)")
    description = Column(String(256), nullable=True, comment="兑换描述")
    status = Column(String(20), nullable=False, default="completed", comment="状态: completed/cancelled")
    created_at = Column(DateTime, default=func.now(), comment="兑换时间")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "developer_id": self.developer_id,
            "points_spent": self.points_spent,
            "redemption_type": self.redemption_type,
            "quota_amount": self.quota_amount,
            "description": self.description or "",
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RewardRedemptionCreate(BaseModel):
    """积分兑换请求"""
    points_spent: int = Field(..., ge=1, description="花费积分")
    redemption_type: str = Field(..., pattern=r"^(api_quota|promotion)$", description="兑换类型")
    quota_amount: Optional[int] = Field(None, ge=1, description="兑换数量")
    description: Optional[str] = Field(None, max_length=256, description="描述")


class RewardLeaderboardEntry(BaseModel):
    """排行榜条目"""
    rank: int = Field(..., ge=1)
    developer_id: int
    developer_name: str = ""
    total_points: int
    balance: int
    plugin_count: int = 0
