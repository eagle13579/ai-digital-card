from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# ── 异步引擎 ────────────────────────────────────────────────
# PostgreSQL 支持连接池, SQLite 不支持 pool_size/max_overflow
_engine_kwargs = {"echo": False}
if "postgresql" in settings.DATABASE_URL:
    _engine_kwargs["pool_size"] = 20
    _engine_kwargs["max_overflow"] = 10
    _engine_kwargs["pool_pre_ping"] = True
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


# ── 同步引擎兼容（用于暂未迁移到 async 的旧模块） ──────────
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_sync_url = (
    settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "")
)
sync_engine = create_engine(_sync_url, echo=False)
SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)
