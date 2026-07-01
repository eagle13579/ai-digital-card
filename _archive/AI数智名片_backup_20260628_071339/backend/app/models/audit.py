"""
审计日志模型 (Audit Log Model)

记录所有 API 请求的操作轨迹，用于安全审计和 GDPR 合规。
"""
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditLog(Base):
    """审计日志：记录用户操作行为。"""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None,
        comment="操作用户 ID（未登录时为 None）",
    )
    action: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="操作类型: CREATE / READ / UPDATE / DELETE / LOGIN / EXPORT / DELETE_ACCOUNT",
    )
    resource: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="操作资源路径，如 /api/users/me",
    )
    detail: Mapped[str] = mapped_column(
        Text, nullable=True, default="", comment="操作详情（JSON 格式的摘要信息）",
    )
    ip: Mapped[str] = mapped_column(
        String(45), nullable=False, default="", comment="客户端 IP 地址",
    )
    user_agent: Mapped[str] = mapped_column(
        String(512), nullable=True, default="", comment="客户端 User-Agent",
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, comment="操作时间",
    )

    __table_args__ = (
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_user_action", "user_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} user_id={self.user_id} "
            f"action={self.action} resource={self.resource!r}>"
        )
