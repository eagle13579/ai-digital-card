"""资源平台商业化模型 — 询赋 A02+A04 组合

3角色平台模型（秘书长/秘书处/会员）+ 年费订阅。
"""
import time

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def unixepoch() -> int:
    """返回当前 Unix 时间戳（秒）"""
    return int(time.time())


class ResourcePlatform(Base):
    """资源平台 - 用户可创建付费资源平台"""
    __tablename__ = "resource_platforms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform_no: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    annual_fee: Mapped[int] = mapped_column(Integer, default=0, comment="年费(分)")
    description: Mapped[str] = mapped_column(Text, default="")
    member_limit: Mapped[int] = mapped_column(Integer, default=1000)
    visibility: Mapped[str] = mapped_column(String(20), default="public", comment="可见性: public/platform/network/private")
    created_at: Mapped[int] = mapped_column(Integer, default=unixepoch)
    updated_at: Mapped[int] = mapped_column(Integer, default=unixepoch, onupdate=unixepoch)


class PlatformMember(Base):
    """平台成员"""
    __tablename__ = "platform_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    platform_id: Mapped[int] = mapped_column(Integer, ForeignKey("resource_platforms.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member", comment="secretary_general / secretariat / member")
    joined_at: Mapped[int] = mapped_column(Integer, default=unixepoch)

    __table_args__ = (UniqueConstraint("platform_id", "user_id", name="uq_platform_user"),)


class PlatformOpportunity(Base):
    """平台商机"""
    __tablename__ = "platform_opportunities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    platform_id: Mapped[int] = mapped_column(Integer, ForeignKey("resource_platforms.id"), nullable=False)
    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    industry: Mapped[str] = mapped_column(String(50), default="")
    city: Mapped[str] = mapped_column(String(50), default="")
    budget: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[int] = mapped_column(Integer, default=unixepoch)
