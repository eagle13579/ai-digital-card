"""API Key 模型：开发者自助门户核心模型。"""
import secrets
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Boolean, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def generate_api_key() -> str:
    """生成安全的 API Key（43字符URL安全字符串）"""
    return "ask_" + secrets.token_urlsafe(32)


class ApiKeyUsage(Base):
    """API Key 用量记录表（按天统计）"""
    __tablename__ = "api_key_usage"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    api_key_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("api_keys.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    date: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="统计日期 YYYY-MM-DD"
    )
    request_count: Mapped[int] = mapped_column(Integer, default=0, comment="当日请求数")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<ApiKeyUsage id={self.id} key_id={self.api_key_id} date={self.date} count={self.request_count}>"


class ApiKey(Base):
    """API Key 表：开发者门户核心模型"""
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, default=generate_api_key,
        comment="API Key 值（完整）"
    )
    name: Mapped[str] = mapped_column(
        String(128), nullable=False, default="默认 Key",
        comment="Key 名称（用户自定义标识）"
    )
    permissions: Mapped[str] = mapped_column(
        Text, default='["read"]',
        comment="权限列表 JSON 数组，例如 [\"read\", \"write\", \"admin\"]"
    )
    rate_limit: Mapped[int] = mapped_column(
        Integer, default=1000,
        comment="每小时速率限制（请求数/小时）"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, comment="最后使用时间"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def mask_key(self) -> str:
        """返回掩码后的 Key，仅显示前8位和后4位"""
        if len(self.key) > 16:
            return self.key[:8] + "****" + self.key[-4:]
        return self.key[:4] + "****"

    def get_permissions_list(self) -> list[str]:
        """解析权限 JSON"""
        import json
        try:
            return json.loads(self.permissions) if self.permissions else ["read"]
        except (json.JSONDecodeError, TypeError):
            return ["read"]

    def __repr__(self) -> str:
        return f"<ApiKey id={self.id} name={self.name} active={self.is_active}>"
