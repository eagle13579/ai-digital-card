"""trust_engine_merge_add_trust_tables

信任体系迁移: 新增 5 张 trust 表
(trust_qualifications / trust_score_snapshots / trust_audit_reports / trust_reviews / trust_score_logs)

Revision ID: a1b2c3d4e5f6
Revises: 83aadcb07de8
Create Date: 2026-08-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '83aadcb07de8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── trust_qualifications 企业资质档案 ─────────────────────────────
    op.create_table('trust_qualifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('qualification_type', sa.String(length=64), nullable=False),
        sa.Column('qualification_name', sa.String(length=256), nullable=False),
        sa.Column('cert_number', sa.String(length=128), nullable=True),
        sa.Column('issuing_authority', sa.String(length=256), nullable=True),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('file_url', sa.String(length=1024), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('verification_level', sa.String(length=16), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'active', 'expired', 'rejected')", name='ck_qualification_status'),
        sa.CheckConstraint("verification_level IN ('ai', 'manual', 'both')", name='ck_qualification_verification'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_trust_qualifications_user_id', 'trust_qualifications', ['user_id'], unique=False)

    # ── trust_score_snapshots 信任评分每日快照 ───────────────────────
    op.create_table('trust_score_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('score_total', sa.Float(), nullable=False),
        sa.Column('score_qualification', sa.Float(), nullable=True),
        sa.Column('score_transaction', sa.Float(), nullable=True),
        sa.Column('score_compliance', sa.Float(), nullable=True),
        sa.Column('trust_level', sa.String(length=16), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('calc_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('score_total >= 0 AND score_total <= 100', name='ck_score_total_range'),
        sa.CheckConstraint("trust_level IN ('pending', 'basic', 'good', 'excellent', 'top')", name='ck_trust_level'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'snapshot_date', name='uq_user_snapshot_date'),
    )
    op.create_index('ix_trust_score_snapshots_user_id', 'trust_score_snapshots', ['user_id'], unique=False)

    # ── trust_audit_reports 企业审计报告 ─────────────────────────────
    op.create_table('trust_audit_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(length=32), nullable=False),
        sa.Column('audit_firm', sa.String(length=256), nullable=False),
        sa.Column('audit_conclusion', sa.String(length=512), nullable=False),
        sa.Column('report_url', sa.String(length=1024), nullable=False),
        sa.Column('report_hash', sa.String(length=64), nullable=False),
        sa.Column('audit_period_start', sa.Date(), nullable=False),
        sa.Column('audit_period_end', sa.Date(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('view_permission', sa.String(length=16), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("report_type IN ('financial', 'security', 'compliance')", name='ck_audit_report_type'),
        sa.CheckConstraint("view_permission IN ('public', 'gold', 'diamond', 'board')", name='ck_audit_view_permission'),
        sa.CheckConstraint("status IN ('pending', 'active', 'expired', 'rejected')", name='ck_audit_status'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_trust_audit_reports_user_id', 'trust_audit_reports', ['user_id'], unique=False)

    # ── trust_reviews 企业评价 ───────────────────────────────────────
    op.create_table('trust_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('from_user_id', sa.Integer(), nullable=False),
        sa.Column('to_user_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(length=36), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_review_rating'),
        sa.CheckConstraint("status IN ('active', 'hidden', 'deleted')", name='ck_review_status'),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id', name='uq_review_order'),
    )
    op.create_index('ix_trust_reviews_from_user_id', 'trust_reviews', ['from_user_id'], unique=False)
    op.create_index('ix_trust_reviews_to_user_id', 'trust_reviews', ['to_user_id'], unique=False)

    # ── trust_score_logs 信任评分变更日志 ────────────────────────────
    op.create_table('trust_score_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('old_score', sa.Float(), nullable=True),
        sa.Column('new_score', sa.Float(), nullable=False),
        sa.Column('change_reason', sa.String(length=256), nullable=True),
        sa.Column('trigger_source', sa.String(length=64), nullable=False),
        sa.Column('calc_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_trust_score_logs_user_id', 'trust_score_logs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_trust_score_logs_user_id', table_name='trust_score_logs')
    op.drop_table('trust_score_logs')
    op.drop_index('ix_trust_reviews_to_user_id', table_name='trust_reviews')
    op.drop_index('ix_trust_reviews_from_user_id', table_name='trust_reviews')
    op.drop_table('trust_reviews')
    op.drop_index('ix_trust_audit_reports_user_id', table_name='trust_audit_reports')
    op.drop_table('trust_audit_reports')
    op.drop_index('ix_trust_score_snapshots_user_id', table_name='trust_score_snapshots')
    op.drop_table('trust_score_snapshots')
    op.drop_index('ix_trust_qualifications_user_id', table_name='trust_qualifications')
    op.drop_table('trust_qualifications')
