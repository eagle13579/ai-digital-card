"""
数据库引擎配置 — 自动检测 DATABASE_URL 并选择合适的异步引擎。

支持两种数据库后端：
  - SQLite (开发环境):  sqlite+aiosqlite:///./data/digital_brochure.db
  - PostgreSQL (生产):  postgresql+asyncpg://user:pass@host:5432/dbname

检测逻辑:
  - DATABASE_URL 以 "postgresql" 开头 → 使用 asyncpg 异步引擎 + 连接池
  - 否则 → 使用 SQLite + aiosqlite（仅限开发环境）

SQLite 说明:
  ⚠️ SQLite 仅用于开发/本地测试，生产环境必须使用 PostgreSQL。
  SQLite 不支持并发写入，连接池参数 (pool_size/max_overflow) 对其无效。
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# ── 异步引擎 ────────────────────────────────────────────────────────────
# PostgreSQL 生产环境:
#   - 使用 asyncpg 驱动（高性能异步 PostgreSQL 驱动）
#   - 启用连接池 (pool_size=20, max_overflow=10)
#   - 启用 pool_pre_ping 自动检测失效连接
#
# SQLite 开发环境:
#   - 使用 aiosqlite 驱动
#   - SQLAlchemy 会自动忽略 pool_size/max_overflow
#   - 不支持并发写入
_engine_kwargs = {"echo": False}

if settings.DATABASE_URL.startswith("postgresql"):
    # ── PostgreSQL 生产配置 ──────────────────────────────────────────
    # psycopg 异步引擎:  postgresql+psycopg://user:pass@host/db
    # asyncpg 异步引擎:  postgresql+asyncpg://user:pass@host/db
    #
    # 生产环境推荐 asyncpg (最快异步 PG 驱动):
    #   pip install asyncpg
    #
    # 如果使用 psycopg (SQLAlchemy 2.0 原生):
    #   pip install psycopg[binary] psycopg_pool
    #   DATABASE_URL=postgresql+psycopg://user:pass@host/db
    _engine_kwargs["pool_size"] = 20
    _engine_kwargs["max_overflow"] = 10
    _engine_kwargs["pool_pre_ping"] = True
    _engine_kwargs["pool_recycle"] = 3600  # 1小时后回收连接
else:
    # ── SQLite 开发配置 ──────────────────────────────────────────────
    # ⚠️ 仅用于开发环境！SQLite 不支持并发写入，连接池参数无效。
    pass

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI 依赖：获取异步数据库会话"""
    from app.middleware.metrics import track_db_query

    async with AsyncSessionLocal() as db:
        try:
            # wrap db operations with metrics tracking
            original_execute = db.execute
            original_stream = db.stream

            async def _tracked_execute(*args, **kwargs):
                with track_db_query():
                    return await original_execute(*args, **kwargs)

            async def _tracked_stream(*args, **kwargs):
                with track_db_query():
                    return await original_stream(*args, **kwargs)

            db.execute = _tracked_execute
            db.stream = _tracked_stream

            yield db
        finally:
            pass  # async_sessionmaker context manager handles close/rollback


# ── 同步引擎兼容（用于暂未迁移到 async 的旧模块） ──────────────────────
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_sync_url = (
    settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "")
)
sync_engine = create_engine(_sync_url, echo=False)
SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)
