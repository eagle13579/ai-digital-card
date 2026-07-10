"""Pytest fixtures for AI数字名片 integration tests.

Provides 6+ fixtures:
  - test_db / test_db_session : in-memory SQLite async session
  - test_redis               : mock Redis client patching app.cache
  - client                    : httpx.AsyncClient via ASGITransport(create_app())
  - test_user / second_user   : User instances in test database
  - auth_headers / test_auth_headers : JWT Authorization header dict
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── Override settings before any app-level imports ──────────────────────
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key-for-development-only")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from app.database import Base

# ── Pre-import all models so Base.metadata.create_all works ─────────────
import app.models.user  # noqa: F401, E402
import app.models.brochure  # noqa: F401, E402
import app.models.tag  # noqa: F401, E402


# ── App instance (shared across tests, lazy-created) ────────────────────
_app = None


def _get_app():
    global _app
    if _app is None:
        # Late import avoids triggering broken import chains at module load
        from app.__init__ import create_app

        _app = create_app()
    return _app


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════


@pytest_asyncio.fixture
async def test_db():
    """In-memory SQLite async session with fresh schema per test.

    Creates all tables on setup, drops them on teardown.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_db):
    """Alias for *test_db* — used by :mod:`test_models` and other model-level tests."""
    return test_db


@pytest_asyncio.fixture
def test_redis():
    """Mock Redis client injected into ``app.cache``.

    Patches both ``app.cache.redis._redis_client`` and ``app.cache._get_client``.
    All core methods (get, set, delete, exists, ping) return sensible defaults.
    """
    redis_client = MagicMock()
    redis_client.get = AsyncMock(return_value=None)
    redis_client.set = AsyncMock()
    redis_client.delete = AsyncMock(return_value=1)
    redis_client.exists = AsyncMock(return_value=False)
    redis_client.ping = MagicMock(return_value=True)
    redis_client.pipeline = MagicMock()

    with (
        patch("app.cache.redis._redis_client", redis_client),
        patch("app.cache._get_client", return_value=redis_client),
    ):
        yield redis_client


@pytest_asyncio.fixture
async def client():
    """Async HTTP client wired to the FastAPI app via ASGITransport.

    Usage::

        resp = await client.get("/health")
        assert resp.status_code == 200
    """
    app = _get_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(test_db):
    """Pre-created :class:`User` persisted in the test database."""
    # Lazy import to work around broken import chain in app.routers.__init__
    from app.models.user import User
    from app.routers.auth import pwd_context

    user = User(
        phone="13800000001",
        name="测试用户",
        username="testuser",
        password_hash=pwd_context.hash("testpass123"),
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_user(test_db):
    """A second :class:`User` instance (different phone)."""
    from app.models.user import User
    from app.routers.auth import pwd_context

    user = User(
        phone="13800000002",
        name="第二个用户",
        username="seconduser",
        password_hash=pwd_context.hash("testpass456"),
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
def auth_headers(test_user):
    """``Authorization: Bearer *** header dict for *test_user*."""
    from app.routers.auth import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def test_auth_headers(auth_headers):
    """Explicit alias for *auth_headers*; identical dict."""
    return auth_headers
