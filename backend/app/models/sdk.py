"""
SDK 应用 / 第三方集成模型 (SDK Application Model)

管理第三方 SDK / 应用的注册、API 授权范围和状态。用于 SDK 市场、
开放平台集成和企业级连接器管理。
"""

from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Boolean, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SdkApp(Base):
    """SDK 应用 / 第三方集成实体。

    描述一个注册到平台的 SDK、插件或第三方服务集成。
    """

    __tablename__ = "sdk_apps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(128), nullable=False,
        comment="应用名称",
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=True, default="",
        comment="应用描述",
    )
    app_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True,
        comment="唯一应用标识 (SDK App ID)",
    )
    app_secret: Mapped[str] = mapped_column(
        String(128), nullable=True,
        comment="应用密钥 (哈希存储，仅创建时明文返回)",
    )
    developer_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True,
        comment="开发者用户 ID",
    )
    sdk_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="web",
        comment="SDK 类型: web / mobile_ios / mobile_android / server / mini_program / plugin / connector",
    )
    platform: Mapped[str] = mapped_column(
        String(32), nullable=True, default="",
        comment="目标平台: web / ios / android / wechat / dingtalk / feishu / enterprise",
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active",
        comment="状态: active / inactive / suspended / revoked / deprecated",
    )
    version: Mapped[str] = mapped_column(
        String(16), nullable=True, default="1.0.0",
        comment="当前 SDK 版本号",
    )
    permissions: Mapped[str] = mapped_column(
        Text, nullable=True, default="",
        comment="请求的权限列表（JSON 数组，如 ['user:read', 'brochure:write']）",
    )
    redirect_uris: Mapped[str] = mapped_column(
        Text, nullable=True, default="",
        comment="OAuth 回调地址列表（JSON 数组）",
    )
    icon_url: Mapped[str] = mapped_column(
        String(512), nullable=True, default="",
        comment="应用图标 URL",
    )
    homepage_url: Mapped[str] = mapped_column(
        String(512), nullable=True, default="",
        comment="应用主页 URL",
    )
    privacy_policy_url: Mapped[str] = mapped_column(
        String(512), nullable=True, default="",
        comment="SDK 隐私政策 URL",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="是否经过平台验证",
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="是否在 SDK 市场公开",
    )
    total_installs: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="总安装次数",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    __table_args__ = (
        Index("idx_sdk_developer", "developer_id"),
        Index("idx_sdk_status", "status"),
        Index("idx_sdk_type_status", "sdk_type", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<SdkApp id={self.id} name={self.name!r} "
            f"app_id={self.app_id} status={self.status}>"
        )
