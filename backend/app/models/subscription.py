"""订阅数据库模型 — 定价套餐(Plan) + 用户订阅关系(Subscription)。

设计说明:
  - Plan:        定价表。免费版 / Pro版 / 企业版 三档，月价 + 年价(含年付折扣)，
                 权益以 JSON 列表存储，is_decoy 标记"诱饵套餐"(锚定效应用)。
  - Subscription: 用户订阅关系表。记录用户当前购买的套餐、起止时间与状态。
                 status: active(生效中) / expired(已到期) / cancelled(已取消)
"""

from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    Boolean,
    Float,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Plan(Base):
    """定价套餐 — 免费/Pro/Enterprise 三档"""

    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="套餐名称: 免费版/Pro版/企业版")
    tier: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, comment="套餐标识: free/pro/enterprise")
    price_monthly: Mapped[float] = mapped_column(Float, default=0, comment="月付价格(元)")
    price_annual: Mapped[float] = mapped_column(Float, default=0, comment="年付价格(元, 已含年付折扣)")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否上架")
    is_decoy: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否诱饵套餐(锚定效应)")
    features: Mapped[dict] = mapped_column(JSON, default=dict, comment="权益列表(JSON): [{name, description, enabled}]")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 反向关系: 一个套餐可被多条订阅引用 (默认 lazy, 访问时才加载)
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="plan"
    )


class Subscription(Base):
    """用户订阅关系 — 用户 ↔ 套餐 的购买记录"""

    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
        comment="用户ID",
    )
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plans.id"), nullable=False, index=True,
        comment="套餐ID",
    )
    status: Mapped[str] = mapped_column(
        String(16), default="active", index=True,
        comment="状态: active/expired/cancelled",
    )
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="订阅开始时间")
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="订阅到期时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # 关系: 订阅 → 套餐
    plan: Mapped["Plan"] = relationship(back_populates="subscriptions")
