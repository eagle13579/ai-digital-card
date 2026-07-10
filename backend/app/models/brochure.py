from datetime import datetime
import uuid

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.tenant import TenantBase


def generate_share_token() -> str:
    return uuid.uuid4().hex[:16]


class Brochure(TenantBase):
    __tablename__ = "brochures"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    cover: Mapped[str] = mapped_column(String(256), default="")
    purpose: Mapped[str] = mapped_column(String(32), default="")  # partner/client/investor/supplier
    pages_count: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="draft")  # draft | published
    visibility: Mapped[str] = mapped_column(String(16), default="public")  # public | platform | network | private
    share_token: Mapped[str] = mapped_column(String(32), unique=True, default=generate_share_token)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    album_meta: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: 翻页图册元数据
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    owner = relationship("User", backref="brochures")
    pages = relationship("Page", backref="brochure", cascade="all, delete-orphan",
                         order_by="Page.sort_order")


class Page(TenantBase):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    brochure_id: Mapped[int] = mapped_column(Integer, ForeignKey("brochures.id"), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    content_type: Mapped[str] = mapped_column(String(16), default="text")  # text | image | cover | video
    content: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(String(256), default="")
    media_url: Mapped[str] = mapped_column(String(512), default="")
    """视频/多媒体文件 URL（支持 mp4/webm）"""
    ai_summary: Mapped[str] = mapped_column(Text, default="")
