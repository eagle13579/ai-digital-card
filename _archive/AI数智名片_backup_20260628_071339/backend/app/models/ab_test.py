"""
A/B 测试 ORM 模型
───────────────────
ABTest — 实验
ABTestVariant — 实验变体（版本）
ABTestEvent — 实验事件埋点
"""

from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ABTest(Base):
    """A/B 测试实验"""
    __tablename__ = "ab_tests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True)
    """draft | running | paused | completed"""

    # 实验配置
    traffic_fraction: Mapped[float] = mapped_column(Float, default=1.0)
    """0.0 ~ 1.0，进入实验的流量比例"""
    min_sample_size: Mapped[int] = mapped_column(Integer, default=100)
    significance_level: Mapped[float] = mapped_column(Float, default=0.05)
    metric: Mapped[str] = mapped_column(String(32), default="click_rate")
    """click_rate | view_count | conversion"""
    target_brochure_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("brochures.id"), nullable=True, index=True
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 缓存结果（JSON）
    cached_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 关系
    variants = relationship(
        "ABTestVariant", back_populates="experiment",
        cascade="all, delete-orphan", order_by="ABTestVariant.sort_order",
    )
    events = relationship(
        "ABTestEvent", back_populates="experiment",
        cascade="all, delete-orphan",
    )


class ABTestVariant(Base):
    """A/B 测试实验变体"""
    __tablename__ = "ab_test_variants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ab_tests.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(256), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_control: Mapped[bool] = mapped_column(default=False)
    """是否为对照组"""

    # 版本配置（JSON，包含具体的名片样式、布局等差异配置）
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 权重（流量分配比例，默认均分）
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    # 是否为胜出发布变体（auto-decision 发布后标记）
    is_default: Mapped[bool] = mapped_column(default=False)

    # 统计缓存
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系
    experiment = relationship("ABTest", back_populates="variants")


class ABTestEvent(Base):
    """A/B 测试事件埋点"""
    __tablename__ = "ab_test_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ab_tests.id"), nullable=False, index=True
    )
    variant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ab_test_variants.id"), nullable=False, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    visitor_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    """impression | click | conversion | view"""

    # 元数据（JSON，可存来源、页面、时长等）
    event_meta: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    # 关系
    experiment = relationship("ABTest", back_populates="events")


class ABTestDecisionLog(Base):
    """A/B 测试自动决策日志"""
    __tablename__ = "ab_test_decision_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ab_tests.id"), nullable=False, index=True
    )

    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    """rollout | continue | stop"""

    variant_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    """胜出变体名称（仅 rollout 时有效）"""

    p_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    """决策时的 p_value"""

    reason: Mapped[str] = mapped_column(Text, default="")
    """决策理由"""

    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    """决策详情（含各变体指标对比）"""

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
