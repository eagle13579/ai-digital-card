"""
pytest fixtures for AI Digital Business Card tests.

Provides:
- test_db: SQLite in-memory database session
- override_get_db: FastAPI dependency override
- client: TestClient with overridden DB dependency
- test_user: Pre-created test user
- auth_headers: Authorization headers for test_user
"""

import sys
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, get_db
from main import app
from app.config import settings
from app.routers.auth import pwd_context, create_access_token
from app.models.user import User

# ── In-memory SQLite database for tests ──────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh in-memory database for each test function.

    Creates all tables before the test and drops them after.
    """
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def override_get_db(test_db):
    """Override FastAPI's get_db dependency with the test database."""

    def _override():
        yield test_db

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function")
def client(override_get_db):
    """FastAPI TestClient with overridden database dependency."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def test_db_session(test_db):
    """Alias for test_db — a direct SQLAlchemy session for model tests."""
    yield test_db


@pytest.fixture(scope="function")
def test_user(test_db):
    """Create a test user directly in the database."""
    user = User(
        phone="13800138000",
        name="测试用户",
        username="testuser",
        company="测试公司",
        title="测试工程师",
        intro="这是一个测试用户",
        avatar="",
        password_hash=pwd_context.hash("testpass123"),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """JWT authorization headers for the test user."""
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def second_user(test_db):
    """Create a second test user (for trust network tests, etc.)."""
    user = User(
        phone="13900139000",
        name="第二个用户",
        username="user2",
        company="另一家公司",
        title="设计师",
        intro="我是第二个用户",
        avatar="",
        password_hash=pwd_context.hash("pass456"),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user
