"""发票数据库模型 — 含税点、购销方信息、关联订单"""

from datetime import datetime

from sqlalchemy import Integer, String, DateTime, Float, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Invoice(Base):
    """发票"""
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, comment="发票号 INV-YYYYMMDD-XXXX")
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="用户ID")

    # 金额
    amount: Mapped[float] = mapped_column(Float, default=0.0, comment="不含税金额")
    tax_rate: Mapped[float] = mapped_column(Float, default=0.0, comment="税率（%），如 3、6、13")
    tax_amount: Mapped[float] = mapped_column(Float, default=0.0, comment="税额")
    total_amount: Mapped[float] = mapped_column(Float, default=0.0, comment="含税总金额")

    # 状态 & 关联
    status: Mapped[str] = mapped_column(String(16), default="unpaid", comment="状态: paid/unpaid/cancelled")
    order_no: Mapped[str] = mapped_column(String(32), default="", comment="关联支付订单号")

    # 购买方信息
    buyer_name: Mapped[str] = mapped_column(String(128), default="", comment="购买方名称")
    buyer_tax_id: Mapped[str] = mapped_column(String(32), default="", comment="购买方税号")

    # 销售方信息
    seller_name: Mapped[str] = mapped_column(String(128), default="", comment="销售方名称")
    seller_tax_id: Mapped[str] = mapped_column(String(32), default="", comment="销售方税号")

    # 明细
    items: Mapped[dict] = mapped_column(JSON, default=list, comment="发票项 [{description, quantity, unit_price, amount}]")
    notes: Mapped[str] = mapped_column(Text, default="", comment="备注")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
