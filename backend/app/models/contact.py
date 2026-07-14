"""通讯录导入 — Contact 数据模型。

使用 Fernet 加密手机号存储 + SHA-256 哈希去重 + 尾号4位展示。
软删除通过 deleted_at 字段实现。
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ImportedContact(Base):
    """已导入的联系人"""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="归属用户ID"
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="联系人姓名")
    phone_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="手机号 SHA-256 哈希（去重用）"
    )
    phone_enc: Mapped[str] = mapped_column(
        Text, nullable=False, comment="手机号 Fernet 加密密文"
    )
    phone_last4: Mapped[str] = mapped_column(
        String(4), nullable=False, default="", comment="手机号后4位（展示用）"
    )
    company: Mapped[str] = mapped_column(String(128), default="", comment="公司")
    position: Mapped[str] = mapped_column(String(128), default="", comment="职位")
    source: Mapped[str] = mapped_column(
        String(16), nullable=False, default="manual", comment="来源: wechat|csv|manual"
    )
    is_matched: Mapped[bool] = mapped_column(
        SmallInteger, default=0, comment="是否已在匹配引擎中处理"
    )
    matched_user_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None, comment="匹配到的平台用户ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, comment="软删除时间"
    )

    def to_dict(self) -> dict:
        """转为字典（不含加密字段）"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "phone_last4": self.phone_last4,
            "company": self.company or "",
            "position": self.position or "",
            "source": self.source,
            "is_matched": bool(self.is_matched),
            "matched_user_id": self.matched_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
