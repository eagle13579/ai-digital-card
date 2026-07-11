from datetime import datetime

from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Connection(Base):
    """社交关系 — 双向双行记录模式（A→B 和 B→A 各一行）

    查询 A 的好友: SELECT * FROM connections WHERE user_id = A AND status = 'approved'
    不需要 OR contact_id = ? 的复杂条件。
    """
    __tablename__ = "connections"
    __table_args__ = (UniqueConstraint("user_id", "contact_id", name="uq_user_contact"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="视角用户")
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="关系对象")
    source: Mapped[str] = mapped_column(String(32), default="platform", comment="关系来源: platform/scan/manual")
    status: Mapped[str] = mapped_column(
        String(16), default="pending",
        comment="状态: pending(待审核) / approved(已批准) / rejected(已拒绝)"
    )
    strength: Mapped[float] = mapped_column(Float, default=0.0, comment="关系强度评分")
    label: Mapped[str] = mapped_column(String(64), default="", comment="备注名/分组标签")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
