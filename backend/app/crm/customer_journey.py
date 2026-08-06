"""客户旅程阶段模型。

记录每位联系人在客户旅程中所处的阶段、停留时长、已执行动作及评分，
帮助营销团队识别转化瓶颈并制定下一最佳行动。
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CustomerJourneyStage(Base):
    """客户旅程阶段 — 记录联系人在 Awareness→Consideration→Decision→Retention 中的位置。"""

    __tablename__ = "customer_journey_stages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── 关联 ────────────────────────────────────────────────────
    contact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_contacts.id"), nullable=False, index=True
    )
    pipeline_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("crm_pipeline_stages.id"),
        nullable=True,
        default=None,
        comment="关联的管道阶段(可选)",
    )

    # ── 旅程阶段 ────────────────────────────────────────────────
    stage: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="awareness | consideration | decision | retention",
    )

    entered_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="进入该阶段的时间"
    )
    duration_days: Mapped[int] = mapped_column(
        Integer, default=0, comment="在该阶段停留的天数"
    )

    # ── 动作与评分 ──────────────────────────────────────────────
    actions_taken: Mapped[str] = mapped_column(
        Text,
        default="[]",
        comment="已执行动作(JSON数组): [{'action':'email_sent','date':'...'}, ...]",
    )
    score: Mapped[float] = mapped_column(
        Float, default=0.0, comment="客户评分(0-100)"
    )
    next_action: Mapped[str] = mapped_column(
        String(256), default="", comment="推荐的下一个最佳行动"
    )

    def to_dict(self) -> dict:
        import json

        return {
            "id": self.id,
            "contact_id": self.contact_id,
            "pipeline_id": self.pipeline_id,
            "stage": self.stage,
            "entered_at": self.entered_at.isoformat() if self.entered_at else None,
            "duration_days": self.duration_days,
            "actions_taken": json.loads(self.actions_taken)
            if self.actions_taken
            else [],
            "score": self.score,
            "next_action": self.next_action,
        }
