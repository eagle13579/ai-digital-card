"""
开发者门户 — DeveloperApp ORM 模型
=====================================
OAuth2 风格的应用注册模型，用于管理第三方应用接入。

与 ApiKey 模型 (developer_portal_models.py) 并存但职责分离:
  - DeveloperApp  → OAuth2 应用注册 (client_id/client_secret, redirect_uris)
  - ApiKey        → 服务端 API 密钥 (hash 存储, 按 tier 限流)
"""

import hashlib
import secrets
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy import func

from app.database import Base


def generate_client_id() -> str:
    """生成唯一的 client_id (app_xxx 格式)"""
    return f"app_{secrets.token_hex(16)}"


def generate_client_secret() -> str:
    """生成 client_secret 并返回明文 (仅创建时返回一次)"""
    return f"sec_{secrets.token_hex(32)}"


def hash_client_secret(secret: str) -> str:
    """对 client_secret 进行 SHA256 哈希存储"""
    return hashlib.sha256(secret.encode()).hexdigest()


class DeveloperApp(Base):
    """第三方应用注册模型"""

    __tablename__ = "developer_apps"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="所属用户 ID")
    name = Column(String(100), nullable=False, comment="应用名称")
    description = Column(Text, nullable=True, default="", comment="应用描述")
    website = Column(String(512), nullable=True, default="", comment="应用网站 URL")
    redirect_uris = Column(Text, nullable=True, default="", comment="OAuth2 回调 URI (逗号分隔)")
    client_id = Column(String(64), unique=True, nullable=False, index=True, comment="客户端 ID (app_xxx)")
    client_secret_hash = Column(String(128), nullable=False, comment="client_secret 的 SHA256 哈希")
    client_secret_prefix = Column(String(8), nullable=False, comment="secret 前 8 位用于显示")
    scopes = Column(String(500), nullable=False, default="read", comment="权限范围 JSON 数组字符串")
    active = Column(Boolean, nullable=False, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<DeveloperApp(id={self.id}, client_id={self.client_id}, name={self.name})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description or "",
            "website": self.website or "",
            "redirect_uris": [u.strip() for u in (self.redirect_uris or "").split(",") if u.strip()],
            "client_id": self.client_id,
            "client_secret_prefix": self.client_secret_prefix,
            "scopes": self.scopes.split(",") if self.scopes else ["read"],
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_safe_dict(self) -> dict:
        """安全输出 (不含哈希)"""
        d = self.to_dict()
        d.pop("client_secret_hash", None)
        d.pop("client_secret_prefix", None)
        return d
