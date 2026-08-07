"""信任评分服务层 — 链客宝 trust_engine 迁移适配（异步版）

职责:
  1. 从数据库读取资质/交易/合规原始数据
  2. 调用 trust_engine.scoring.TrustScorer 计算三维评分
  3. 落库快照 + 变更日志
  4. 提供查询接口（当前分/历史/明细）

适配说明:
  - 原链客宝 trust_api.py 是同步 SQLAlchemy + 模拟数据；本服务对接
    AI数智名片异步 get_db 与真实数据表（trust_qualifications 等）
  - user_id 为 Integer (AI数智名片 users.id)
"""
import logging
from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.trust_engine.scoring import (
    TrustScorer,
    QualificationData,
    TransactionData,
    ComplianceData,
)
from app.trust_engine.tier import TrustTier, TrustLevel
from app.models.trust_score import (
    TrustQualification,
    TrustScoreSnapshot,
    TrustAuditReport,
    TrustReview,
    TrustScoreLog,
)

logger = logging.getLogger(__name__)


class TrustScoreService:
    """信任评分服务（单例静态方法）"""

    # ── 评分计算 ──────────────────────────────────────────────────────

    @staticmethod
    async def compute_for_user(
        db: AsyncSession,
        user_id: int,
        *,
        trigger_source: str = "api",
        reason: str = "评分重算",
    ) -> TrustScoreSnapshot:
        """计算用户当前信任评分并落库快照

        从 trust_qualifications / trust_audit_reports / trust_reviews
        聚合真实数据，调用评分引擎计算，写入快照表 + 变更日志。
        """
        # 1. 聚合原始数据
        quals = (
            await db.execute(
                select(TrustQualification).where(
                    TrustQualification.user_id == user_id
                )
            )
        ).scalars().all()

        active_quals = [q for q in quals if q.status == "active"]
        expired_count = len([q for q in quals if q.status == "expired"])
        about_to_expire = len(
            [
                q
                for q in active_quals
                if q.expiry_date
                and 0 <= (q.expiry_date - date.today()).days <= 90
            ]
        )
        cert_types = {q.qualification_type for q in active_quals}

        # 审计报告
        audits = (
            await db.execute(
                select(TrustAuditReport).where(
                    TrustAuditReport.user_id == user_id,
                    TrustAuditReport.status == "active",
                )
            )
        ).scalars().all()
        has_valid_audit = len(audits) > 0

        # 评价数据（作为交易可信度代理）
        reviews = (
            await db.execute(
                select(TrustReview).where(
                    TrustReview.to_user_id == user_id,
                    TrustReview.status == "active",
                )
            )
        ).scalars().all()
        total_rated = len(reviews)
        positive_rate = (
            sum(1 for r in reviews if r.rating >= 4) / total_rated
            if total_rated
            else 1.0
        )

        # 2. 调用评分引擎
        scorer = TrustScorer()
        breakdown = scorer.calculate_from_raw_data(
            QualificationData(
                qualification_type=active_quals[0].qualification_type if active_quals else "",
                is_active=bool(active_quals),
            ),
            TransactionData(
                total_trades=total_rated,
                total_amount=0.0,
                positive_rate=positive_rate,
                dispute_count=0,
                total_rated=total_rated,
                repurchase_count=0,
            ),
            ComplianceData(
                active_qual_count=len(active_quals),
                expired_count=expired_count,
                about_to_expire_count=about_to_expire,
                compliance_cert_types=cert_types,
                has_valid_audit=has_valid_audit,
                has_expired_audit=False,
                last_update_months=None,
            ),
            cert_level="enterprise" if active_quals else "none",
            id_level="id_card" if active_quals else "none",
            months_on_platform=0.0,
        )

        tier = TrustTier(breakdown.total)

        # 3. 取上一快照（用于日志 diff）
        prev = (
            await db.execute(
                select(TrustScoreSnapshot)
                .where(TrustScoreSnapshot.user_id == user_id)
                .order_by(TrustScoreSnapshot.snapshot_date.desc())
                .limit(1)
            )
        ).scalars().first()

        # 4. 写入今日快照（upsert 语义：同一天覆盖）
        today = date.today()
        existing = (
            await db.execute(
                select(TrustScoreSnapshot).where(
                    TrustScoreSnapshot.user_id == user_id,
                    TrustScoreSnapshot.snapshot_date == today,
                )
            )
        ).scalars().first()

        if existing:
            existing.score_total = breakdown.total
            existing.score_qualification = breakdown.qualification.weighted
            existing.score_transaction = breakdown.transaction.weighted
            existing.score_compliance = breakdown.compliance.weighted
            existing.trust_level = tier.level.value
            existing.calc_metadata = breakdown.to_dict()
            snap = existing
        else:
            snap = TrustScoreSnapshot(
                user_id=user_id,
                score_total=breakdown.total,
                score_qualification=breakdown.qualification.weighted,
                score_transaction=breakdown.transaction.weighted,
                score_compliance=breakdown.compliance.weighted,
                trust_level=tier.level.value,
                snapshot_date=today,
                calc_metadata=breakdown.to_dict(),
            )
            db.add(snap)

        # 5. 变更日志
        db.add(
            TrustScoreLog(
                user_id=user_id,
                old_score=prev.score_total if prev else None,
                new_score=breakdown.total,
                change_reason=reason,
                trigger_source=trigger_source,
                calc_metadata=breakdown.to_dict(),
            )
        )

        await db.commit()
        await db.refresh(snap)
        logger.info("信任评分计算完成 user=%s score=%s tier=%s", user_id, snap.score_total, snap.trust_level)
        return snap

    # ── 查询 ──────────────────────────────────────────────────────────

    @staticmethod
    async def get_current(
        db: AsyncSession, user_id: int
    ) -> Optional[TrustScoreSnapshot]:
        """获取最新评分快照"""
        return (
            await db.execute(
                select(TrustScoreSnapshot)
                .where(TrustScoreSnapshot.user_id == user_id)
                .order_by(TrustScoreSnapshot.snapshot_date.desc())
                .limit(1)
            )
        ).scalars().first()

    @staticmethod
    async def get_history(
        db: AsyncSession, user_id: int, months: int = 12
    ) -> list[TrustScoreSnapshot]:
        """获取评分历史（近 N 月）"""
        cutoff = date.today().replace(day=1)
        # 简单回退 months 个月
        for _ in range(months):
            if cutoff.month == 1:
                cutoff = cutoff.replace(year=cutoff.year - 1, month=12)
            else:
                cutoff = cutoff.replace(month=cutoff.month - 1)
        return (
            await db.execute(
                select(TrustScoreSnapshot)
                .where(
                    TrustScoreSnapshot.user_id == user_id,
                    TrustScoreSnapshot.snapshot_date >= cutoff,
                )
                .order_by(TrustScoreSnapshot.snapshot_date.asc())
            )
        ).scalars().all()

    @staticmethod
    async def list_qualifications(
        db: AsyncSession, user_id: int
    ) -> list[TrustQualification]:
        return (
            await db.execute(
                select(TrustQualification)
                .where(TrustQualification.user_id == user_id)
                .order_by(TrustQualification.created_at.desc())
            )
        ).scalars().all()

    @staticmethod
    async def create_qualification(
        db: AsyncSession,
        user_id: int,
        *,
        qualification_type: str,
        qualification_name: str,
        issue_date: date,
        cert_number: Optional[str] = None,
        issuing_authority: Optional[str] = None,
        expiry_date: Optional[date] = None,
        file_url: str = "",
        file_hash: str = "",
    ) -> TrustQualification:
        q = TrustQualification(
            user_id=user_id,
            qualification_type=qualification_type,
            qualification_name=qualification_name,
            cert_number=cert_number,
            issuing_authority=issuing_authority,
            issue_date=issue_date,
            expiry_date=expiry_date,
            file_url=file_url,
            file_hash=file_hash,
            status="active",
            verification_level="ai",
        )
        db.add(q)
        await db.commit()
        await db.refresh(q)
        return q

    @staticmethod
    async def list_reviews(
        db: AsyncSession, user_id: int
    ) -> list[TrustReview]:
        return (
            await db.execute(
                select(TrustReview)
                .where(
                    TrustReview.to_user_id == user_id,
                    TrustReview.status == "active",
                )
                .order_by(TrustReview.created_at.desc())
            )
        ).scalars().all()

    @staticmethod
    async def create_review(
        db: AsyncSession,
        from_user_id: int,
        to_user_id: int,
        *,
        rating: int,
        content: Optional[str] = None,
        order_id: Optional[str] = None,
        is_anonymous: bool = False,
    ) -> TrustReview:
        if not 1 <= rating <= 5:
            raise ValueError("评分必须在 1-5 之间")
        if from_user_id == to_user_id:
            raise ValueError("不能评价自己")
        r = TrustReview(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            order_id=order_id,
            rating=rating,
            content=content,
            is_anonymous=is_anonymous,
            status="active",
        )
        db.add(r)
        await db.commit()
        await db.refresh(r)
        return r
