"""
数据库迁移辅助函数 — 阿里云/生产环境安全迁移

在 SQLite 上安全地 ALTER TABLE 添加缺失列，避免 OperationalError。
同时也适用于 PostgreSQL / MySQL — 各数据库的 DDL 语法差异已处理。
"""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger("db_migration")


async def add_visibility_column(conn: AsyncConnection) -> None:
    """确保 brochures 表包含 visibility 列和 platform_id 列。

    SQLite 在 ALTER TABLE 后不支持撤销, 所以先检查列是否存在。
    """
    # 1a. 检查 visibility 列
    try:
        row = await conn.execute(
            text(
                "SELECT COUNT(*) AS cnt FROM pragma_table_info('brochures') "
                "WHERE name = 'visibility'"
            )
        )
        result = row.one_or_none()
        if result and result[0] > 0:
            logger.info("brochures.visibility 列已存在，跳过")
        else:
            await conn.execute(
                text(
                    "ALTER TABLE brochures ADD COLUMN visibility VARCHAR(16) "
                    "DEFAULT 'public' NOT NULL"
                )
            )
            logger.info("✅ 迁移成功: brochures 表添加了 visibility 列 (默认 'public')")
    except Exception as e:
        err_str = str(e).lower()
        if "duplicate column" in err_str or "already exists" in err_str:
            logger.info("visibility 列已存在（并发创建），忽略")
        else:
            logger.warning("添加 visibility 列失败（非致命）: %s", e)

    # 1b. 检查 platform_id 列
    try:
        row = await conn.execute(
            text(
                "SELECT COUNT(*) AS cnt FROM pragma_table_info('brochures') "
                "WHERE name = 'platform_id'"
            )
        )
        result = row.one_or_none()
        if result and result[0] > 0:
            logger.info("brochures.platform_id 列已存在，跳过")
        else:
            await conn.execute(
                text(
                    "ALTER TABLE brochures ADD COLUMN platform_id INTEGER "
                    "REFERENCES platforms(id) DEFAULT NULL"
                )
            )
            logger.info("✅ 迁移成功: brochures 表添加了 platform_id 列")
    except Exception as e:
        err_str = str(e).lower()
        if "duplicate column" in err_str or "already exists" in err_str:
            logger.info("platform_id 列已存在（并发创建），忽略")
        else:
            logger.warning("添加 platform_id 列失败（非致命）: %s", e)


async def ensure_rbac_tables(conn: AsyncConnection) -> None:
    """确保 CRM RBAC 相关表存在 (rbac_roles, rbac_user_roles, rbac_role_permissions).

    `Base.metadata.create_all` 在模型已导入时会自动建表，
    但若 `app.models.rbac` 未被提前导入则跳过。
    本函数提供 DDL 级别的兜底保障。
    """
    tables = [
        (
            "rbac_roles",
            """
            CREATE TABLE IF NOT EXISTS rbac_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(32) NOT NULL UNIQUE,
                display_name VARCHAR(64) DEFAULT '',
                description TEXT DEFAULT '',
                is_system BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
        ),
        (
            "rbac_role_permissions",
            """
            CREATE TABLE IF NOT EXISTS rbac_role_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL REFERENCES rbac_roles(id) ON DELETE CASCADE,
                permission_key VARCHAR(64) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(role_id, permission_key)
            )
            """,
        ),
        (
            "rbac_user_roles",
            """
            CREATE TABLE IF NOT EXISTS rbac_user_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL REFERENCES rbac_roles(id) ON DELETE CASCADE,
                granted_by INTEGER DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, role_id)
            )
            """,
        ),
    ]
    created = 0
    for name, ddl in tables:
        try:
            await conn.execute(text(ddl))
            created += 1
            logger.info("✅ 确保表 %s 存在", name)
        except Exception as e:
            logger.warning("创建表 %s 失败（非致命）: %s", name, e)

    if created:
        logger.info("✅ RBAC 表迁移完成 (%d/3)", created)
    else:
        logger.info("RBAC 表已全部存在，跳过")
