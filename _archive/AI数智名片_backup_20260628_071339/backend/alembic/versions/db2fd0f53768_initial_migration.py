"""initial_migration — 创建所有核心表

Revision ID: db2fd0f53768
Revises:
Create Date: 2026-06-26 11:49:12.034133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'db2fd0f53768'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(64), nullable=True),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('password_hash', sa.String(128), nullable=False),
        sa.Column('wechat_openid', sa.String(64), nullable=True),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('company', sa.String(128), server_default='', nullable=False),
        sa.Column('title', sa.String(128), server_default='', nullable=False),
        sa.Column('intro', sa.Text(), server_default='', nullable=False),
        sa.Column('avatar', sa.String(256), server_default='', nullable=False),
        sa.Column('role', sa.String(16), server_default='user', nullable=False),
        sa.Column('membership_tier', sa.String(16), server_default='free', nullable=False),
        sa.Column('membership_expires_at', sa.DateTime(), nullable=True),
        sa.Column('membership_synced_at', sa.DateTime(), nullable=True),
        sa.Column('unlock_quota', sa.Integer(), server_default='0', nullable=False),
        sa.Column('quota_reset_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('phone'),
        sa.UniqueConstraint('wechat_openid'),
    )

    # --- unlock_records ---
    op.create_table(
        'unlock_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=False),
        sa.Column('match_record_id', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- brochures ---
    op.create_table(
        'brochures',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(128), nullable=False),
        sa.Column('cover', sa.String(256), server_default='', nullable=False),
        sa.Column('purpose', sa.String(32), server_default='', nullable=False),
        sa.Column('pages_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.String(16), server_default='draft', nullable=False),
        sa.Column('share_token', sa.String(32), nullable=False),
        sa.Column('view_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('album_meta', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('share_token'),
    )

    # --- pages ---
    op.create_table(
        'pages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('brochure_id', sa.Integer(), sa.ForeignKey('brochures.id'), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('content_type', sa.String(16), server_default='text', nullable=False),
        sa.Column('content', sa.Text(), server_default='', nullable=False),
        sa.Column('image_url', sa.String(256), server_default='', nullable=False),
        sa.Column('ai_summary', sa.Text(), server_default='', nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- user_tags ---
    op.create_table(
        'user_tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tag_type', sa.String(16), nullable=False),
        sa.Column('tag', sa.String(64), nullable=False),
        sa.Column('weight', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('source', sa.String(16), server_default='manual', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- match_records ---
    op.create_table(
        'match_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_a_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('user_b_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('match_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('status', sa.String(16), server_default='pending', nullable=False),
        sa.Column('common_tags', sa.Text(), server_default='[]', nullable=False),
        sa.Column('source', sa.String(16), server_default='auto', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- visitor_logs ---
    op.create_table(
        'visitor_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('brochure_id', sa.Integer(), sa.ForeignKey('brochures.id'), nullable=False),
        sa.Column('visitor_id', sa.String(64), nullable=True),
        sa.Column('visitor_ip', sa.String(48), server_default='', nullable=False),
        sa.Column('visitor_name', sa.String(64), server_default='', nullable=False),
        sa.Column('source', sa.String(32), server_default='direct', nullable=False),
        sa.Column('page_viewed', sa.String(64), server_default='', nullable=False),
        sa.Column('duration', sa.Integer(), server_default='0', nullable=False),
        sa.Column('interested', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('contact_msg', sa.Text(), server_default='', nullable=False),
        sa.Column('visit_time', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- trust_network ---
    op.create_table(
        'trust_network',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('trusted_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('trust_network')
    op.drop_table('visitor_logs')
    op.drop_table('match_records')
    op.drop_table('user_tags')
    op.drop_table('pages')
    op.drop_table('brochures')
    op.drop_table('unlock_records')
    op.drop_table('users')
