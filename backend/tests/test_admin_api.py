"""Admin Panel API 测试 — 16 用例覆盖 RBAC + 所有端点"""
from __future__ import annotations
import pytest, pytest_asyncio
from datetime import datetime
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.database import Base

def _get_app():
    from app.__init__ import create_app
    return create_app()

def _admin_token():
    from app.routers.auth import create_access_token
    return create_access_token({"sub": "999"})

def _user_token():
    from app.routers.auth import create_access_token
    return create_access_token({"sub": "1"})

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()

@pytest_asyncio.fixture
async def seed_data(db_session):
    from app.models.user import User
    from app.models.brochure import Brochure
    from app.models.audit import AuditLog
    admin = User(id=999, phone="13800000999", name="管理员", role="admin", password_hash="x")
    normal = User(id=1, phone="13800000001", name="普通用户", role="user", password_hash="x")
    db_session.add_all([admin, normal])
    await db_session.commit()
    b = Brochure(id=10, user_id=1, title="测试名片", status="published")
    db_session.add(b)
    await db_session.commit()
    log = AuditLog(user_id=1, action="LOGIN", resource="/api/auth/login",
                   detail='{"ip":"127.0.0.1"}', ip="127.0.0.1", timestamp=datetime.utcnow())
    db_session.add(log)
    await db_session.commit()
    return {"admin": admin, "normal": normal, "brochure": b, "log": log}

@pytest_asyncio.fixture
async def client(db_session):
    app = _get_app()
    from app.database import get_db
    async def _override_db(): yield db_session
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = _override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_non_admin_cannot_list_users(client, seed_data):
    resp = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {_user_token()}"})
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_admin_list_users(client, seed_data):
    resp = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {_admin_token()}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2 and data["page"] == 1

@pytest.mark.asyncio
async def test_admin_search_users(client, seed_data):
    resp = await client.get("/api/v1/admin/users?q=管理", headers={"Authorization": f"Bearer {_admin_token()}"})
    assert resp.status_code == 200
    names = [i["name"] for i in resp.json()["items"]]
    assert "管理员" in names

@pytest.mark.asyncio
async def test_non_admin_cannot_get_user_detail(client, seed_data):
    resp = await client.get("/api/v1/admin/users/1", headers={"Authorization": f"Bearer {_user_token()}"})
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_admin_get_user_detail(client, seed_data):
    resp = await client.get("/api/v1/admin/users/1", headers={"Authorization": f"Bearer {_admin_token()}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "普通用户"

@pytest.mark.asyncio
async def test_admin_disable_user(client, seed_data):
    resp = await client.patch("/api/v1/admin/users/1?status=disabled",
                              headers={"Authorization": f"Bearer {_admin_token()}"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "disabled"

@pytest.mark.asyncio
async def test_admin_enable_user(client, seed_data):
    resp = await client.patch("/api/v1/admin/users/1?status=active",
                              headers={"Authorization": f"Bearer {_admin_token()}"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "user"

@pytest.mark.asyncio
async def test_non_admin_cannot_list_brochures(client, seed_data):
    resp = await client.get("/api/v1/admin/brochures", headers={"Authorization": f"Bearer {_user_token()}"})
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_admin_list_brochures(client, seed_data):
    resp = await client.get("/api/v1/admin/brochures", headers={"Authorization": f"Bearer {_admin_token()}"})
    assert resp.status_code == 200
    assert resp.json()["items"][0]["title"] == "测试名片"

@pytest.mark.asyncio
async def test_non_admin_cannot_get_stats(client, seed_data):
    resp = await client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {_user_token()}"})
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_admin_get_stats(client, seed_data):
    resp = await client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {_admin_token()}"})
    assert resp.status_code == 200
    d = resp.json()
    assert d["user_count"] >= 2 and d["brochure_count"] >= 1 and d["admin_count"] >= 1

@pytest.mark.asyncio
async def test_admin_audit_log_search(client, seed_data):
    resp = await client.get("/api/v1/admin/audit-log", headers={"Authorization": f"Bearer {_admin_token()}"})
    assert resp.status_code == 200
    assert resp.json()["items"][0]["action"] == "LOGIN"

@pytest.mark.asyncio
async def test_admin_audit_log_filter_by_user(client, seed_data):
    resp = await client.get("/api/v1/admin/audit-log?user_id=1",
                            headers={"Authorization": f"Bearer {_admin_token()}"})
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["user_id"] == 1

@pytest.mark.asyncio
async def test_admin_audit_log_filter_by_action(client, seed_data):
    resp = await client.get("/api/v1/admin/audit-log?action=LOGIN",
                            headers={"Authorization": f"Bearer {_admin_token()}"})
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["action"] == "LOGIN"

@pytest.mark.asyncio
async def test_admin_get_nonexistent_user(client, seed_data):
    resp = await client.get("/api/v1/admin/users/99999",
                            headers={"Authorization": f"Bearer {_admin_token()}"})
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_admin_audit_log_invalid_time(client, seed_data):
    resp = await client.get("/api/v1/admin/audit-log?start_time=bad-date",
                            headers={"Authorization": f"Bearer {_admin_token()}"})
    assert resp.status_code == 400
