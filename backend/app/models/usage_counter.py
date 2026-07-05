from datetime import datetime

from sqlalchemy import Integer, String, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UsageCounter(Base):
    """使用计数器：按功能纬度记录每个用户的使用量。"""

    __tablename__ = "usage_counters"

    __table_args__ = (
        UniqueConstraint("user_id", "feature", "period", name="uq_usage_user_feature_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="用户ID")
    feature: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="功能标识: ocr/visitor/batch_import/api/card"
    )
    period: Mapped[str] = mapped_column(
        String(16), nullable=False, default="monthly", comment="统计周期: monthly"
    )
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="已使用次数")
    limit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="周期上限（-1=无限制）")
    reset_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="限额重置时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
