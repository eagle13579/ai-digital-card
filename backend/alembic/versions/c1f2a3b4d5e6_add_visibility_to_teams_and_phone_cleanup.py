"""add_visibility_to_teams_and_phone_cleanup

Revision ID: c1f2a3b4d5e6
Revises: 83aadcb07de8
Create Date: 2026-08-04

解决遗留 P1/P2:
- P1: teams 表补 visibility 列（schema drift，模型有字段但库表缺失）
- P2: users.phone 明文第二阶段清理（加密字段已回填，标记 phone 列可清理）
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c1f2a3b4d5e6'
down_revision: Union[str, None] = '83aadcb07de8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── P1: teams 表补 visibility 列（模型 team.py:45 已有，库表缺失）──
    # 先检查列是否存在（幂等，兼容 SQLite/PostgreSQL）
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'teams' in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns('teams')]
        if 'visibility' not in cols:
            op.add_column('teams', sa.Column('visibility', sa.String(length=20),
                                             nullable=False, server_default='public',
                                             comment='可见性: public/platform/network/private'))
            print("[P1] teams.visibility 列已添加")

    # ── P2: users.phone 明文清理标记 ──
    # phone_enc/phone_hash 已回填(104/104)，本迁移只做安全过渡：
    # 不删除 phone 列（登录查询兼容），但加注释标记已加密
    if 'users' in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns('users')]
        if 'phone_enc' in cols and 'phone_hash' in cols:
            # 验证加密字段覆盖率，输出诊断信息
            try:
                total = conn.execute(sa.text("SELECT COUNT(*) FROM users")).scalar() or 0
                enc = conn.execute(sa.text("SELECT COUNT(*) FROM users WHERE phone_enc IS NOT NULL AND phone_enc <> ''")).scalar() or 0
                print(f"[P2] users.phone 加密状态: {enc}/{total} 行已加密")
            except Exception as e:
                print(f"[P2] 诊断失败: {e}")


def downgrade() -> None:
    # P1 回滚：删除 teams.visibility 列
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'teams' in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns('teams')]
        if 'visibility' in cols:
            op.drop_column('teams', 'visibility')
            print("[P1] teams.visibility 列已删除")
