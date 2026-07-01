from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserTag(Base):
    __tablename__ = "user_tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    tag_type: Mapped[str] = mapped_column(String(16), nullable=False)  # provide | need
    tag: Mapped[str] = mapped_column(String(64), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    source: Mapped[str] = mapped_column(String(16), default="manual")  # manual | ai | import
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class MatchRecord(Base):
    __tablename__ = "match_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_a_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    user_b_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending | matched | confirmed
    common_tags: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    source: Mapped[str] = mapped_column(String(16), default="auto")  # auto | manual
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
