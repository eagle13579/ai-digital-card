"""信任体系数据模型（自链客宝 trust_models.py 迁移，适配 AI数智名片）

迁移适配点:
- user_id 从 String(36) UUID → Integer (对齐 AI数智名片 users.id)
- 使用异步 SQLAlchemy 2.0 Mapped 风格 (与 app.models 其他模块一致)
- Base 从 app.database 导入
- 保留原表名与字段语义，兼容链客宝 PRD 设计

表清单:
  trust_qualifications   企业资质档案
  trust_score_snapshots  信任评分每日快照
  trust_audit_reports    企业审计报告
  trust_reviews          企业评价
  trust_score_logs       信任评分变更日志
"""
from datetime import date, datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid4())


# ── 枚举常量 ──────────────────────────────────────────────────────────────

class QualificationStatus:
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REJECTED = "rejected"


class VerificationLevel:
    AI = "ai"
    MANUAL = "manual"
    BOTH = "both"


class AuditReportType:
    FINANCIAL = "financial"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class ViewPermission:
    PUBLIC = "public"
    GOLD = "gold"
    DIAMOND = "diamond"
    BOARD = "board"


class TrustLevelEnum:
    PENDING = "pending"
    BASIC = "basic"
    GOOD = "good"
    EXCELLENT = "excellent"
    TOP = "top"


# =============================================================================
# 表1: trust_qualifications — 企业资质档案
# =============================================================================

class TrustQualification(Base):
    """企业资质档案 — 营业执照/ISO/ICP/专利等"""
    __tablename__ = "trust_qualifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    qualification_type: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="资质类型: business_license / iso_cert / icp / patent / trademark / saas_record / industry_license / copyright"
    )
    qualification_name: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="资质名称"
    )
    cert_number: Mapped[Optional[str]] = mapped_column(String(128), comment="证书编号")
    issuing_authority: Mapped[Optional[str]] = mapped_column(String(256), comment="发证机构")
    issue_date: Mapped[date] = mapped_column(Date, nullable=False, comment="发证日期")
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, comment="有效期（无期则为NULL）")
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False, comment="原件存储URL")
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, comment="SHA-256文件哈希")
    status: Mapped[str] = mapped_column(
        String(16), default="pending",
        comment="pending / active / expired / rejected"
    )
    verification_level: Mapped[str] = mapped_column(
        String(16), default="ai", comment="ai / manual / both"
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, comment="驳回原因")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'active', 'expired', 'rejected')",
            name="ck_qualification_status"
        ),
        CheckConstraint(
            "verification_level IN ('ai', 'manual', 'both')",
            name="ck_qualification_verification"
        ),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "qualification_type": self.qualification_type,
            "qualification_name": self.qualification_name,
            "cert_number": self.cert_number,
            "issuing_authority": self.issuing_authority,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "file_url": self.file_url,
            "file_hash": self.file_hash,
            "status": self.status,
            "verification_level": self.verification_level,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# 表2: trust_score_snapshots — 信任评分每日快照
# =============================================================================

class TrustScoreSnapshot(Base):
    """信任评分快照 — 每日全量重算，UNIQUE(user_id, snapshot_date)"""
    __tablename__ = "trust_score_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    score_total: Mapped[float] = mapped_column(Float, nullable=False, comment="综合评分 0.00-100.00")
    score_qualification: Mapped[Optional[float]] = mapped_column(Float, comment="资质可信度得分")
    score_transaction: Mapped[Optional[float]] = mapped_column(Float, comment="交易可信度得分")
    score_compliance: Mapped[Optional[float]] = mapped_column(Float, comment="合规健康度得分")
    trust_level: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="pending / basic / good / excellent / top"
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    calc_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, comment="计算明细元数据（各子指标分值+衰减因子+事件来源）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date", name="uq_user_snapshot_date"),
        CheckConstraint(
            "score_total >= 0 AND score_total <= 100", name="ck_score_total_range"
        ),
        CheckConstraint(
            "trust_level IN ('pending', 'basic', 'good', 'excellent', 'top')",
            name="ck_trust_level"
        ),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "score_total": self.score_total,
            "score_qualification": self.score_qualification,
            "score_transaction": self.score_transaction,
            "score_compliance": self.score_compliance,
            "trust_level": self.trust_level,
            "snapshot_date": self.snapshot_date.isoformat() if self.snapshot_date else None,
            "calc_metadata": self.calc_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# 表3: trust_audit_reports — 企业审计报告
# =============================================================================

class TrustAuditReport(Base):
    """企业审计报告 — 财务/安全/合规，带权限控制"""
    __tablename__ = "trust_audit_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    report_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="financial / security / compliance"
    )
    audit_firm: Mapped[str] = mapped_column(String(256), nullable=False, comment="审计机构名称")
    audit_conclusion: Mapped[str] = mapped_column(String(512), nullable=False, comment="审计结论")
    report_url: Mapped[str] = mapped_column(String(1024), nullable=False, comment="报告文件URL")
    report_hash: Mapped[str] = mapped_column(String(64), nullable=False, comment="SHA-256")
    audit_period_start: Mapped[date] = mapped_column(Date, nullable=False, comment="审计期间开始")
    audit_period_end: Mapped[date] = mapped_column(Date, nullable=False, comment="审计期间结束")
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否公开展示")
    view_permission: Mapped[str] = mapped_column(
        String(16), default="diamond", comment="public / gold / diamond / board"
    )
    status: Mapped[str] = mapped_column(
        String(16), default="pending",
        comment="pending / active / expired / rejected"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "report_type IN ('financial', 'security', 'compliance')",
            name="ck_audit_report_type"
        ),
        CheckConstraint(
            "view_permission IN ('public', 'gold', 'diamond', 'board')",
            name="ck_audit_view_permission"
        ),
        CheckConstraint(
            "status IN ('pending', 'active', 'expired', 'rejected')",
            name="ck_audit_status"
        ),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "report_type": self.report_type,
            "audit_firm": self.audit_firm,
            "audit_conclusion": self.audit_conclusion,
            "report_url": self.report_url,
            "report_hash": self.report_hash,
            "audit_period_start": self.audit_period_start.isoformat() if self.audit_period_start else None,
            "audit_period_end": self.audit_period_end.isoformat() if self.audit_period_end else None,
            "is_public": self.is_public,
            "view_permission": self.view_permission,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# 表4: trust_reviews — 企业评价
# =============================================================================

class TrustReview(Base):
    """企业评价 — 订单完成后互评，一笔订单一条"""
    __tablename__ = "trust_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    from_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="评价方用户ID"
    )
    to_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="被评价方用户ID"
    )
    order_id: Mapped[Optional[str]] = mapped_column(
        String(36), comment="关联订单ID（防刷：一笔订单一条评价）"
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False, comment="评分 1-5")
    content: Mapped[Optional[str]] = mapped_column(Text, comment="评价内容")
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否匿名")
    status: Mapped[str] = mapped_column(
        String(16), default="active", comment="active / hidden / deleted"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating"),
        CheckConstraint(
            "status IN ('active', 'hidden', 'deleted')", name="ck_review_status"
        ),
        UniqueConstraint("order_id", name="uq_review_order"),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "from_user_id": self.from_user_id,
            "to_user_id": self.to_user_id,
            "order_id": self.order_id,
            "rating": self.rating,
            "content": self.content,
            "is_anonymous": self.is_anonymous,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# 表5: trust_score_logs — 信任评分变更日志
# =============================================================================

class TrustScoreLog(Base):
    """信任评分变更日志 — 记录每次评分重算的明细（审计用）"""
    __tablename__ = "trust_score_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    old_score: Mapped[Optional[float]] = mapped_column(Float, comment="旧评分")
    new_score: Mapped[float] = mapped_column(Float, nullable=False, comment="新评分")
    change_reason: Mapped[str] = mapped_column(String(256), comment="变更原因")
    trigger_source: Mapped[str] = mapped_column(
        String(64), default="system", comment="触发来源: system / api / cron / manual"
    )
    calc_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, comment="计算元数据")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "old_score": self.old_score,
            "new_score": self.new_score,
            "change_reason": self.change_reason,
            "trigger_source": self.trigger_source,
            "calc_metadata": self.calc_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
