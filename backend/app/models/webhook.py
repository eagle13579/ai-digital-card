"""Webhook 事件订阅模型：记录用户注册的 webhook 端点与事件类型映射。"""
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WebhookSubscription(Base):
    """Webhook 事件订阅表"""

    __tablename__ = "webhook_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="所属用户ID"
    )
    name: Mapped[str] = mapped_column(
        String(128), default="", comment="订阅名称（用户自定义）"
    )
    url: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="Webhook 回调 URL"
    )
    secret: Mapped[str] = mapped_column(
        String(128), default="", comment="签名密钥（用于 HMAC-SHA256 签名）"
    )
    events: Mapped[str] = mapped_column(
        Text, default="[]", comment="监听的事件类型列表，JSON 数组"
    )
    """示例: ["card.created", "card.updated", "card.deleted", "contact.exported"]"""
    active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否启用"
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, default=3, comment="失败重试次数"
    )
    timeout_seconds: Mapped[int] = mapped_column(
        Integer, default=10, comment="HTTP 请求超时秒数"
    )
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="上次触发时间"
    )
    last_response_code: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="上次响应状态码"
    )
    last_error: Mapped[str] = mapped_column(
        Text, default="", comment="上次错误信息"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def get_events_list(self) -> list[str]:
        """解析 events JSON 为列表"""
        import json
        try:
            return json.loads(self.events) if self.events else []
        except (json.JSONDecodeError, TypeError):
            return []

    def set_events_list(self, events: list[str]) -> None:
        """将事件列表序列化为 JSON"""
        import json
        self.events = json.dumps(events, ensure_ascii=False)

    def __repr__(self) -> str:
        return (
            f"<WebhookSubscription id={self.id} user_id={self.user_id} "
            f"active={self.active} events={self.events}>"
        )
