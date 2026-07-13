"""
Tenant ORM Model & TenantBase — Multi-tenant 数据隔离基类。

所有需要租户隔离的业务模型应继承 TenantBase 而非 Base：
    class Brochure(TenantBase):
        __tablename__ = "brochures"
        ...
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.database import Base


class Plan(str, Enum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class Tenant(Base):
    """租户主表"""
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="租户名称")
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="唯一标识")
    plan: Mapped[str] = mapped_column(String(16), default=Plan.FREE, comment="套餐: FREE/PRO/ENTERPRISE")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Tenant id={self.id} slug={self.slug!r} plan={self.plan}>"


class TenantBase(Base):
    """
    多租户基类 — 所有业务模型继承此类自动获得 tenant_id 外键。

    继承示例:
        class MyModel(TenantBase):
            __tablename__ = "my_models"
            ...
    """
    __abstract__ = True

    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenants.id"), nullable=False, index=True,
        comment="所属租户 ID",
    )

    @declared_attr
    def __table_args__(cls):  # noqa
        return ({"extend_existing": True},)
