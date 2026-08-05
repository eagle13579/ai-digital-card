from datetime import datetime

from sqlalchemy import Integer, String, Float, Text, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Platform(Base):
    """平台/组织 — 用户可创建或加入的平台/圈子"""
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="平台名称")
    platform_no: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, comment="平台编号")
    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者(秘书长)")
    annual_fee: Mapped[float] = mapped_column(Float, default=0.0, comment="年费")
    description: Mapped[str] = mapped_column(Text, default="", comment="平台描述")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class PlatformMember(Base):
    """平台成员 — 用户与平台的多对多关联，带角色"""
    __tablename__ = "platform_members"
    __table_args__ = (UniqueConstraint("platform_id", "user_id", name="uq_platform_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    platform_id: Mapped[int] = mapped_column(Integer, ForeignKey("platforms.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(
        String(32), default="member",
        comment="角色: secretary_general(秘书长) / secretariat(秘书处) / member(会员)"
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
