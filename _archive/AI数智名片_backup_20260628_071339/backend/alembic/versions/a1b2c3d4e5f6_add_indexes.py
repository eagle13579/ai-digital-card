"""添加常用查询索引

Revision ID: a1b2c3d4e5f6
Revises: db2fd0f53768
Create Date: 2026-06-28 01:34:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'db2fd0f53768'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_index('ix_users_phone', 'users', ['phone'])

    # brochures
    op.create_index('ix_brochures_user_status', 'brochures', ['user_id', 'status'])

    # visitor_logs
    op.create_index('ix_visitor_logs_brochure_created', 'visitor_logs', ['brochure_id', 'created_at'])

    # teams
    op.create_index('ix_teams_owner', 'teams', ['owner_id'])

    # audit_logs
    op.create_index('ix_audit_logs_resource_action', 'audit_logs', ['resource', 'action'])

    # payment_orders
    op.create_index('ix_payment_orders_user', 'payment_orders', ['user_id'])

    # ab_tests
    op.create_index('ix_ab_test_experiment', 'ab_tests', ['created_by', 'status'])


def downgrade() -> None:
    op.drop_index('ix_ab_test_experiment', table_name='ab_tests')
    op.drop_index('ix_payment_orders_user', table_name='payment_orders')
    op.drop_index('ix_audit_logs_resource_action', table_name='audit_logs')
    op.drop_index('ix_teams_owner', table_name='teams')
    op.drop_index('ix_visitor_logs_brochure_created', table_name='visitor_logs')
    op.drop_index('ix_brochures_user_status', table_name='brochures')
    op.drop_index('ix_users_phone', table_name='users')
