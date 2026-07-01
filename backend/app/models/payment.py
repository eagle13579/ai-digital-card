"""支付订单数据库模型"""

from datetime import datetime

from sqlalchemy import Integer, String, DateTime, Boolean, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PaymentOrder(Base):
    """支付订单"""
    __tablename__ = "payment_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, comment="内部订单号")
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="用户ID")
    membership_tier: Mapped[str] = mapped_column(String(16), nullable=False, comment="会员等级")
    channel: Mapped[str] = mapped_column(String(16), nullable=False, comment="支付渠道: wechat/alipay")
    channel_order_no: Mapped[str] = mapped_column(String(64), default="", comment="渠道订单号")
    status: Mapped[str] = mapped_column(String(16), default="pending", comment="支付状态")
    total_cents: Mapped[int] = mapped_column(Integer, default=0, comment="金额（分）")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="支付时间")
    raw_callback: Mapped[str] = mapped_column(String(2048), default="", comment="原始回调数据")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class EnterpriseSubscription(Base):
    """企业版订阅"""
    __tablename__ = "enterprise_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="管理员用户ID")
    company_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="企业名称")
    seats: Mapped[int] = mapped_column(Integer, nullable=False, comment="席位数量")
    tier: Mapped[str] = mapped_column(String(32), nullable=False, comment="套餐等级: free/standard/enterprise")
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="订阅开始时间")
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="订阅到期时间")
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否自动续费")
    status: Mapped[str] = mapped_column(String(16), default="active", comment="状态: active/trial/expired/cancelled")
    features: Mapped[dict] = mapped_column(JSON, default=dict, comment="功能特性配置(JSON)")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class TrialRecord(Base):
    """试用记录 — 追踪每个用户的免费试用使用情况"""
    __tablename__ = "trial_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="用户ID")
    subscription_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="关联的订阅ID")
    trial_tier: Mapped[str] = mapped_column(String(32), default="standard", comment="试用套餐等级")
    status: Mapped[str] = mapped_column(String(16), default="active", comment="状态: active/used/expired")
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="试用开始时间")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="试用到期时间")
    converted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="转为正式订阅的时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
