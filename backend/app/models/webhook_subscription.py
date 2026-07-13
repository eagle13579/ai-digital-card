"""
链客宝 — Webhook 订阅数据模型
=================================
Webhook 订阅的 SQLAlchemy ORM 模型，包含数据库持久化与 Pydantic 校验 Schema。

字段:
    id              — 主键
    user_id         — 所属用户 ID
    url             — 回调 URL
    events          — 订阅事件类型列表 (JSON 数组存储)
    secret          — HMAC 签名密钥
    active          — 是否活跃
    created_at      — 创建时间
    last_triggered_at — 最后触发时间
"""

from __future__ import annotations

import json
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func

from app.database import Base

# ===================================================================
# 事件类型常量 — Webhook 支持的事件
# ===================================================================

WEBHOOK_EVENTS = frozenset({
    "contact.created",
    "contact.updated",
    "match.found",
    "payment.completed",
    "nfc.shared",
    "order.created",
})


# ===================================================================
# SQLAlchemy ORM 模型
# ===================================================================

class WebhookSubscription(Base):
    """Webhook 订阅 — 数据库持久化模型"""

    __tablename__ = "webhook_subscriptions_v2"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="所属用户 ID")
    url = Column(String(1024), nullable=False, comment="回调 URL")
    events = Column(Text, nullable=False, comment="订阅事件类型 JSON 数组")
    secret = Column(String(128), nullable=False, comment="HMAC 签名密钥")
    active = Column(Boolean, nullable=False, default=True, comment="是否活跃")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    last_triggered_at = Column(DateTime, nullable=True, comment="最后触发时间")

    @property
    def event_list(self) -> list[str]:
        """获取事件类型列表"""
        try:
            return json.loads(self.events)
        except (json.JSONDecodeError, TypeError):
            return []

    @event_list.setter
    def event_list(self, value: list[str]) -> None:
        """设置事件类型列表"""
        self.events = json.dumps(value, ensure_ascii=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "url": self.url,
            "events": self.event_list,
            "secret": self.secret,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<WebhookSubscription(id={self.id}, user_id={self.user_id}, "
            f"url={self.url}, events={self.event_list})>"
        )


# ===================================================================
# Pydantic Schema (请求/响应)
# ===================================================================

class CreateWebhookRequest(BaseModel):
    """创建 Webhook 订阅请求"""
    url: str = Field(..., description="回调 URL", max_length=1024, examples=["https://example.com/webhook"])
    events: list[str] = Field(..., description="订阅事件类型列表", min_length=1, max_length=20)
    secret: Optional[str] = Field(None, description="自定义签名密钥（可选，自动生成）", min_length=16, max_length=128)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL 必须以 http:// 或 https:// 开头")
        if len(v) > 1024:
            raise ValueError("URL 长度不能超过 1024 个字符")
        return v

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[str]) -> list[str]:
        normalized = {e.strip().lower() for e in v if e.strip()}
        invalid = normalized - WEBHOOK_EVENTS
        if invalid:
            raise ValueError(
                f"不支持的事件类型: {', '.join(sorted(invalid))}. "
                f"支持的事件: {', '.join(sorted(WEBHOOK_EVENTS))}"
            )
        return sorted(normalized)


class UpdateWebhookRequest(BaseModel):
    """更新 Webhook 订阅请求"""
    url: Optional[str] = Field(None, description="回调 URL", max_length=1024)
    events: Optional[list[str]] = Field(None, description="订阅事件类型列表", min_length=1, max_length=20)
    secret: Optional[str] = Field(None, description="签名密钥", min_length=16, max_length=128)
    active: Optional[bool] = Field(None, description="是否活跃")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL 必须以 http:// 或 https:// 开头")
        return v

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        normalized = {e.strip().lower() for e in v if e.strip()}
        invalid = normalized - WEBHOOK_EVENTS
        if invalid:
            raise ValueError(
                f"不支持的事件类型: {', '.join(sorted(invalid))}. "
                f"支持的事件: {', '.join(sorted(WEBHOOK_EVENTS))}"
            )
        return sorted(normalized)


class WebhookResponse(BaseModel):
    """Webhook 订阅响应"""
    id: int
    user_id: int
    url: str
    events: list[str]
    secret: str
    active: bool
    created_at: Optional[str] = None
    last_triggered_at: Optional[str] = None

    class Config:
        from_attributes = True


class WebhookListItem(BaseModel):
    """Webhook 订阅列表项（不暴露 secret）"""
    id: int
    user_id: int
    url: str
    events: list[str]
    active: bool
    created_at: Optional[str] = None
    last_triggered_at: Optional[str] = None

    class Config:
        from_attributes = True


class DeliveryLogResponse(BaseModel):
    """投递日志响应"""
    id: int
    subscription_id: int
    event_type: str
    event_id: str
    status: str
    attempt: int
    response_code: Optional[int] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


__all__ = [
    "WebhookSubscription",
    "CreateWebhookRequest",
    "UpdateWebhookRequest",
    "WebhookResponse",
    "WebhookListItem",
    "DeliveryLogResponse",
    "WEBHOOK_EVENTS",
]
