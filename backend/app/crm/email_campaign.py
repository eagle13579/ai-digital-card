"""邮件营销活动模型。

独立于 CrmCampaign（后者侧重批量发送 + 追踪像素），
EmailCampaign 侧重活动本身的内容模板、目标人群段、排期和综合统计。
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EmailCampaign(Base):
    """邮件营销活动 — 内容、目标人群、排期与统计。"""

    __tablename__ = "email_campaigns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── 基本信息 ────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="活动名称"
    )
    subject: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="邮件主题"
    )
    content_template: Mapped[str] = mapped_column(
        Text, default="", comment="邮件内容模板（HTML/纯文本）"
    )

    # ── 目标人群 ────────────────────────────────────────────────
    target_segment: Mapped[str] = mapped_column(
        Text,
        default="{}",
        comment="目标人群段(JSON): {tags:[], pipeline_stage_ids:[], sources:[], created_after:, created_before:}",
    )

    # ── 排期 ────────────────────────────────────────────────────
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, comment="计划发送时间"
    )

    # ── 统计 ────────────────────────────────────────────────────
    sent_count: Mapped[int] = mapped_column(Integer, default=0, comment="已发送数")
    open_count: Mapped[int] = mapped_column(Integer, default=0, comment="已打开数")
    click_count: Mapped[int] = mapped_column(Integer, default=0, comment="点击数")

    # ── 状态 ────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(16),
        default="draft",
        comment="draft | scheduled | sending | sent | paused | cancelled",
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self) -> dict:
        import json

        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "content_template": self.content_template,
            "target_segment": json.loads(self.target_segment)
            if self.target_segment
            else {},
            "scheduled_at": self.scheduled_at.isoformat()
            if self.scheduled_at
            else None,
            "sent_count": self.sent_count,
            "open_count": self.open_count,
            "click_count": self.click_count,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
