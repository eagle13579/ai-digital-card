from datetime import datetime

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VisitorLog(Base):
    __tablename__ = "visitor_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    brochure_id: Mapped[int] = mapped_column(Integer, ForeignKey("brochures.id"), nullable=False)
    visitor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    visitor_ip: Mapped[str] = mapped_column(String(48), default="")
    visitor_name: Mapped[str] = mapped_column(String(64), default="")
    source: Mapped[str] = mapped_column(String(32), default="direct")  # direct | qrcode | share | scan
    page_viewed: Mapped[str] = mapped_column(String(64), default="")
    duration: Mapped[int] = mapped_column(Integer, default=0)
    interested: Mapped[bool] = mapped_column(Boolean, default=False)
    contact_msg: Mapped[str] = mapped_column(Text, default="")
    visit_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
