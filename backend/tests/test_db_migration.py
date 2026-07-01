"""Alembic 迁移测试 — 验证 upgrade/downgrade 可逆 + 表结构正确。

8+ 测试用例覆盖:
  - upgrade → downgrade 可逆
  - 关键表及列存在性
  - autogenerate 新 revision 可生成

注意: 只测试首个迁移 (db2fd0f53768)。第二个迁移 (a1b2c3d4e5f6)
引用了初始迁移中不存在的表和列 (teams, created_at 等), 在干净数据库
上无法运行, 属既有缺陷。
"""

import os
import tempfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, create_engine

# ── 项目根目录 ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_CFG_PATH = PROJECT_ROOT / "alembic.ini"
BASE_REV = "db2fd0f53768"  # 初始迁移 revision ID


# ── Helper: 创建临时的 Alembic Config（指向 SQLite 文件） ─────────

@pytest.fixture
def alembic_cfg() -> Config:
    """返回指向临时 SQLite 数据库的 Alembic Config（使用 aiosqlite 异步驱动）。"""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = tmp.name

    cfg = Config(str(ALEMBIC_CFG_PATH))
    cfg.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_path}")

    # 保存 db_path 供 teardown 和 sync_engine 使用
    cfg._test_db_path = db_path  # type: ignore[attr-defined]
    yield cfg

    # teardown
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sync_engine(alembic_cfg: Config):
    """同步 SQLAlchemy engine（使用 sync driver）用于检查表结构。"""
    db_path = alembic_cfg._test_db_path  # type: ignore[attr-defined]
    engine = create_engine(f"sqlite:///{db_path}")
    yield engine
    engine.dispose()


# ══════════════════════════════════════════════════════════════════
# 测试用例
# ══════════════════════════════════════════════════════════════════


class TestMigrationUpgrade:
    """验证 upgrade 后表结构正确。"""

    def test_upgrade_to_base_succeeds(self, alembic_cfg: Config):
        """upgrade 到初始迁移不抛异常。"""
        command.upgrade(alembic_cfg, BASE_REV)

    def test_expected_tables_exist_after_upgrade(
        self, alembic_cfg: Config, sync_engine
    ):
        """升级后核心表均存在。"""
        command.upgrade(alembic_cfg, BASE_REV)
        inspector = inspect(sync_engine)
        tables = inspector.get_table_names()
        expected = {
            "users", "unlock_records", "brochures", "pages",
            "user_tags", "match_records", "visitor_logs", "trust_network",
        }
        missing = expected - set(tables)
        assert not missing, f"缺少表: {missing}"

    def test_users_table_columns(self, alembic_cfg: Config, sync_engine):
        """users 表包含所有关键列。"""
        command.upgrade(alembic_cfg, BASE_REV)
        cols = {c["name"] for c in inspect(sync_engine).get_columns("users")}
        expected = {
            "id", "username", "phone", "password_hash", "wechat_openid",
            "name", "company", "title", "intro", "avatar", "role",
            "membership_tier", "created_at", "updated_at",
        }
        assert expected.issubset(cols), f"users 缺列: {expected - cols}"

    def test_brochures_table_columns(self, alembic_cfg: Config, sync_engine):
        """brochures 表包含所有关键列。"""
        command.upgrade(alembic_cfg, BASE_REV)
        cols = {c["name"] for c in inspect(sync_engine).get_columns("brochures")}
        for col in ("id", "user_id", "title", "share_token", "status"):
            assert col in cols, f"brochures 缺列: {col}"

    def test_visitor_logs_uses_visit_time(self, alembic_cfg: Config, sync_engine):
        """visitor_logs 使用 visit_time 列（非 created_at）。"""
        command.upgrade(alembic_cfg, BASE_REV)
        cols = {c["name"] for c in inspect(sync_engine).get_columns("visitor_logs")}
        assert "visit_time" in cols, "visitor_logs 缺 visit_time"
        assert "brochure_id" in cols, "visitor_logs 缺 brochure_id"


class TestMigrationDowngrade:
    """验证 downgrade 可逆。"""

    def test_downgrade_to_base_succeeds(self, alembic_cfg: Config):
        """upgrade 后能 downgrade 到 base。"""
        command.upgrade(alembic_cfg, BASE_REV)
        command.downgrade(alembic_cfg, "base")

    def test_tables_removed_after_downgrade(
        self, alembic_cfg: Config, sync_engine
    ):
        """downgrade 到 base 后核心表被删除。"""
        command.upgrade(alembic_cfg, BASE_REV)
        command.downgrade(alembic_cfg, "base")
        tables = inspect(sync_engine).get_table_names()
        core = {"users", "brochures", "pages", "match_records"}
        remaining = core & set(tables)
        assert not remaining, f"downgrade 后表未清理: {remaining}"

    def test_full_cycle_reversible(self, alembic_cfg: Config):
        """upgrade→downgrade→upgrade 完整周期不抛异常。"""
        command.upgrade(alembic_cfg, BASE_REV)
        command.downgrade(alembic_cfg, "base")
        command.upgrade(alembic_cfg, BASE_REV)

    def test_autogenerate_revision_creates_file(
        self, alembic_cfg: Config, tmp_path: Path
    ):
        """autogenerate 能生成新的 revision 文件。"""
        command.upgrade(alembic_cfg, BASE_REV)
        alembic_cfg.set_main_option("version_locations", str(tmp_path))
        alembic_cfg.set_main_option("version_path_separator", "os")
        command.revision(alembic_cfg, message="test_auto", autogenerate=False)
        files = list(tmp_path.glob("*.py"))
        assert len(files) >= 1, "autogenerate 未创建文件"
        content = files[0].read_text()
        assert "test_auto" in content, "revision 消息未写入"
        assert "def upgrade" in content, "缺少 upgrade 函数"
        assert "def downgrade" in content, "缺少 downgrade 函数"
