from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SocialConnection(Base):
    """社交连接 - 用户之间的建联关系（待审核/已建联/已拒绝）"""
    __tablename__ = "social_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment="UUID")
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="发起方用户ID")
    contact_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="目标方用户ID")
    source: Mapped[str] = mapped_column(String(32), default="qrcode", comment="来源: qrcode / manual / share")
    message: Mapped[str] = mapped_column(Text, default="", comment="建联附言")
    status: Mapped[str] = mapped_column(String(16), default="pending", comment="状态: pending / approved / rejected")
    strength: Mapped[float] = mapped_column(Float, default=0.0, comment="关系强度 (0.0 ~ 1.0)")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
