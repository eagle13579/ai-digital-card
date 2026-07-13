"""
用户同意记录模型 (User Consent Model)

记录用户对数据收集、处理、分享等操作的同意/授权状态，满足 GDPR / 个人信息保护法
合规要求。每次用户的同意偏好变更都会新增一条记录（不可变审计追踪）。
"""

from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Boolean, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserConsent(Base):
    """用户同意记录：跟踪用户对数据处理的授权状态。

    设计原则：
    - 追加写入（append-only）：每次变更都新增记录，不原地更新。
    - 查询最新同意状态时按 user_id + consent_type 分组取 max(created_at)。
    """

    __tablename__ = "user_consents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True,
        comment="用户 ID",
    )
    consent_type: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="同意类型: data_collection / data_processing / data_sharing / marketing / cookies_analytics / cookies_functional / cookies_advertising / biometric / location / third_party",
    )
    granted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="是否同意 (True=同意, False=撤回)",
    )
    consent_version: Mapped[str] = mapped_column(
        String(16), nullable=True, default="1.0",
        comment="同意时的策略版本号",
    )
    source: Mapped[str] = mapped_column(
        String(64), nullable=True, default="",
        comment="同意来源: registration / settings_page / api / gdpr_portal / popup_banner",
    )
    ip: Mapped[str] = mapped_column(
        String(45), nullable=True, default="",
        comment="操作时的客户端 IP",
    )
    user_agent: Mapped[str] = mapped_column(
        String(512), nullable=True, default="",
        comment="操作时的 User-Agent",
    )
    detail: Mapped[str] = mapped_column(
        Text, nullable=True, default="",
        comment="额外说明（JSON 格式，记录具体授权范围等）",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
        comment="记录创建时间",
    )

    __table_args__ = (
        Index("idx_consent_user_type", "user_id", "consent_type"),
        Index("idx_consent_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<UserConsent id={self.id} user_id={self.user_id} "
            f"type={self.consent_type} granted={self.granted}>"
        )
