from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UsageCounter(Base):
    """使用计数器：按功能纬度记录每个用户的使用量。

    支持双重计费：
    - 按功能计次（used_count）— 兼容现有体系
    - 按 token 计费（token_* 字段）— token 级别精细计费
    """

    __tablename__ = "usage_counters"

    __table_args__ = (
        UniqueConstraint("user_id", "feature", "period", name="uq_usage_user_feature_period"),
    )

    # ── 基础字段（兼容现有体系） ─────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="用户ID")
    feature: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="功能标识: ocr/visitor/batch_import/api/card"
    )
    period: Mapped[str] = mapped_column(
        String(16), nullable=False, default="monthly", comment="统计周期: monthly"
    )
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="已使用次数")
    limit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="周期上限（-1=无限制）")
    reset_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="限额重置时间")

    # ── Token 追踪字段（双重计费） ───────────────────────────────
    model_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="internal", comment="模型类型: internal/external"
    )
    model_name: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", comment="模型名称: deepseek-chat/m3e 等"
    )
    token_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="chat",
        comment="Token 类型: chat/embedding/search/rule/query",
    )
    prompt_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="输入 token 数（外部模型）"
    )
    completion_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="输出 token 数（外部模型）"
    )
    total_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="总 token 数"
    )
    token_cost: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="用户费用（¥）"
    )
    external_cost: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="外部模型成本（¥，仅 external 有效）",
    )
    markup_rate: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="加价率（external 默认 0.5）"
    )

    # ── 时间戳 ───────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
