"""集成配置模型：存储 HubSpot/Salesforce/Webhook 集成配置。"""
import json
from datetime import datetime
from typing import Any

from sqlalchemy import Integer, String, Text, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Integration(Base):
    """CRM / Webhook 集成配置表"""

    __tablename__ = "integrations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="所属用户ID")
    provider: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="集成类型: hubspot / salesforce / webhook"
    )
    name: Mapped[str] = mapped_column(String(128), default="", comment="集成名称（用户自定义）")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否启用")
    config: Mapped[str] = mapped_column(
        Text, default="{}", comment="JSON 配置（API Key、Token、端点等）"
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最后成功同步时间"
    )
    webhook_url: Mapped[str] = mapped_column(
        String(512), default="", comment="Webhook 回调 URL"
    )
    webhook_secret: Mapped[str] = mapped_column(
        String(128), default="", comment="Webhook 签名密钥"
    )
    webhook_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否启用 Webhook"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # ── 便捷方法 ──────────────────────────────────────────────────────────

    def get_config_dict(self) -> dict[str, Any]:
        """解析 config JSON 为字典"""
        try:
            return json.loads(self.config) if self.config else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_config_dict(self, config_dict: dict[str, Any]) -> None:
        """将字典序列化为 JSON 写入 config 字段"""
        self.config = json.dumps(config_dict, ensure_ascii=False)

    def __repr__(self) -> str:
        return f"<Integration id={self.id} provider={self.provider} enabled={self.enabled}>"
