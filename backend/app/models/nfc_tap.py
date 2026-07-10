"""
NFC 碰触记录 ORM 模型
─────────────────────
NfcTapRecord — 记录一次 NFC 碰触分享事件

谁（from_user_id）通过 NFC 碰触拿到了谁（to_user_id）的名片
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NfcTapRecord(Base):
    """NFC 碰触事件记录"""

    __tablename__ = "nfc_tap_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="发起碰触的用户 ID（碰的人）"
    )
    to_user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="被碰触的用户 ID（名片主人）"
    )
    nfc_uid: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="NFC 标签 UID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<NfcTapRecord(id={self.id}, from={self.from_user_id}, "
            f"to={self.to_user_id}, nfc={self.nfc_uid})>"
        )
