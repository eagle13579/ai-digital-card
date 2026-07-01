"""
契约测试基础配置与 Fixtures
============================

提供契约测试专用的 fixtures:
  - client           : httpx.AsyncClient (ASGI Transport)
  - auth_headers     : JWT Authorization header
  - contract_registry: 可扩展的契约注册表 (dict)

设计原则
--------
1. 契约测试使用独立的 in-memory SQLite，不污染其他测试的数据库。
2. 所有 fixture 定义在此处，契约测试文件只写断言逻辑。
3. 不安装新包 — 复用 conftest.py 已有的 pytest-asyncio + httpx 依赖。
4. 使用懒导入避免启动时触发有问题的 import 链。
"""

import os
import random
import string

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── 环境变量 (必须在 app 导入前设置) ──────────────────────────────────────
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key-for-contracts")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


# ── 应用工厂 (懒创建) ─────────────────────────────────────────────────────
_app = None


def _get_app():
    global _app
    if _app is None:
        from app.__init__ import create_app
        _app = create_app()
    return _app


# ── 数据库引擎 (隔离于 conftest.py 的引擎) ────────────────────────────────
_contract_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:", echo=False
)
_contract_session_factory = async_sessionmaker(
    _contract_engine, class_=AsyncSession, expire_on_commit=False
)


def _gen_phone():
    """生成唯一测试手机号"""
    return f"13{''.join(random.choices(string.digits, k=9))}"


def _gen_username():
    """生成唯一测试用户名"""
    return f"ct_{''.join(random.choices(string.ascii_lowercase, k=6))}"


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════


@pytest_asyncio.fixture(scope="module")
async def contract_db():
    """模块级隔离的 in-memory 数据库（所有契约测试共用）。"""
    from app.database import Base

    async with _contract_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _contract_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _contract_engine.dispose()


@pytest_asyncio.fixture
async def db_session(contract_db):
    """每个测试函数获取独立的 session。"""
    session = _contract_session_factory()
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def client(contract_db):
    """Async HTTP client via ASGI Transport — 契约测试专用。

    依赖 contract_db 确保数据库 schema 已创建。
    """
    app = _get_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session):
    """预创建用户（契约测试专用）。"""
    from app.models.user import User
    from app.routers.auth import pwd_context

    phone = _gen_phone()
    user = User(
        phone=phone,
        name="契约测试用户",
        username=_gen_username(),
        password_hash=pwd_context.hash("contractpass123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user):
    """JWT Authorization header (Bearer token)。"""
    from app.routers.auth import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


# ── 契约注册表 (可选扩展) ────────────────────────────────────────────────


class ContractRegistry(dict):
    """端点契约注册表，用于运行时收集与验证。

    使用示例::

        registry = ContractRegistry()
        registry.register("GET /api/users/me", {
            "status": 200,
            "required_fields": {"id", "phone", "name"},
        })
    """

    def register(self, endpoint: str, contract: dict):
        self[endpoint] = contract

    def get_contract(self, endpoint: str) -> dict:
        return self.get(endpoint, {})


@pytest_asyncio.fixture
def contract_registry():
    """全局契约注册表（可选）。"""
    return ContractRegistry()
