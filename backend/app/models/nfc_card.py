"""
NFC 数字名片 ORM 模型
─────────────────────
NFCCard — NFC 标签与数字名片的绑定关系

NFC 写入格式（NDEF 标准）:
  - Record 1: vCard 4.0 (完整联系人信息)
  - Record 2: URL (名片在线查看链接)
  - Record 3: 自定义 JSON (扩展数据 / 应用专属元数据)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NFCCard(Base):
    """NFC 标签 — 数字名片绑定记录"""

    __tablename__ = "nfc_cards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    """所属用户 ID"""

    nfc_uid: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    """NFC 标签唯一标识符（硬件 UID，如 04:AB:CD:EF:12:34:56:78）"""

    card_data_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}"
    )
    """
    名片数据的 JSON 序列化。
    包含生成 vCard 所需的所有字段:
      {
        "name": "张三",
        "company": "某公司",
        "title": "技术总监",
        "phone": "13800138000",
        "email": "zhangsan@example.com",
        "website": "https://liankebao.top/card/abc123",
        "avatar_url": "https://...",
        "address": "北京市朝阳区...",
        "social": { "wechat": "...", "linkedin": "..." }
      }
    """

    # vCard相关内容
    vcard_raw: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """预生成的 vCard 4.0 格式文本（缓存），首次写入时生成"""

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<NFCCard(id={self.id}, user_id={self.user_id}, nfc_uid={self.nfc_uid})>"
