from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.tenant import TenantBase


class UnlockRecord(Base):
    """解锁记录：记录付费用户解锁匹配对象联系信息的操作"""
    __tablename__ = "unlock_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="解锁方用户ID")
    target_user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="被解锁的用户ID")
    match_record_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="关联的匹配记录ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class User(TenantBase):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)
    # ── BUG-034 修复：手机号加密存储 ─────────────────────────────────────────
    # phone 列过渡期保留（登录仍走 phone 唯一索引查询），第二阶段清理后删除；
    # phone_hash 为 SHA-256 哈希 + 唯一索引，用于后续登录查询与去重；
    # phone_enc 为 Fernet 加密密文；phone_last4 用于脱敏展示。
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="手机号（过渡期明文，迁移完成后清理）")
    phone_hash: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True, default=None, comment="手机号 SHA-256 哈希（登录查询唯一索引）"
    )
    phone_enc: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None, comment="手机号 Fernet 加密密文"
    )
    phone_last4: Mapped[str] = mapped_column(
        String(4), nullable=False, default="", comment="手机号后4位（脱敏展示用）"
    )
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    wechat_openid: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    company: Mapped[str] = mapped_column(String(128), default="")
    title: Mapped[str] = mapped_column(String(128), default="")
    intro: Mapped[str] = mapped_column(Text, default="")
    avatar: Mapped[str] = mapped_column(String(256), default="")
    role: Mapped[str] = mapped_column(String(16), default="user")  # user | admin

    # ── 四级可见性 ────────────────────────────────────────────────────────
    visibility: Mapped[str] = mapped_column(String(20), default="public", comment="可见性: public/platform/network/private")

    # ── 会员相关字段（Phase 1） ──────────────────────────────────────────
    membership_tier: Mapped[str] = mapped_column(String(16), default="free", comment="会员等级: free/gold/diamond/board")
    membership_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="会员过期时间")
    membership_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="最后同步链客宝时间")
    unlock_quota: Mapped[int] = mapped_column(Integer, default=0, comment="本月剩余解锁配额")
    quota_reset_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="配额重置时间")

    # ── 关系 ──────────────────────────────────────────────────────────
    memberships = relationship("OrganizationMember", back_populates="user")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
