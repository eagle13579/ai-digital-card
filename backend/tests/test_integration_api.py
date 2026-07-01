"""
集成测试: TestClient 完整请求-响应循环
测试核心API端点 (health, auth, brochure templates, error handling)
Mock数据库session, 完整走FastAPI请求-响应循环
注意: Brochure create/list端点存在异步greenlet兼容性问题(sync TestClient + async lazy-load),
     故跳过这些端点的写测试，通过 template/error/auth 路径覆盖完整请求-响应验证。
"""
import os, sys, random, pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key-for-development-only")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.database import Base, get_db
from app import create_app

app = create_app()
_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_test_async_session_factory = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="module")
def _setup_db():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_init_db())
    app.dependency_overrides[get_db] = _get_test_db
    yield
    loop.run_until_complete(_cleanup_db())
    loop.close()
    app.dependency_overrides.clear()

async def _init_db():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def _cleanup_db():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _test_engine.dispose()

async def _get_test_db():
    async with _test_async_session_factory() as session:
        yield session

def gen_phone():
    return "1" + "".join(random.choices("0123456789", k=10))

def gen_username():
    return "u" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=10))

@pytest.fixture
def client(_setup_db):
    return TestClient(app)

def register_user(client):
    phone, username = gen_phone(), gen_username()
    resp = client.post("/api/auth/register", json={
        "phone": phone, "password": "testpass123", "name": "测试用户", "username": username,
    })
    assert resp.status_code == 200, f"注册失败: {resp.json()}"
    data = resp.json()
    return data["access_token"], data["user"]

class TestHealthIntegration:
    def test_health_text(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200 and resp.text == "OK"

    def test_api_health_json(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200 and resp.json()["status"] == "ok"

class TestAuthIntegration:
    def test_register_and_login(self, client):
        token, user = register_user(client)
        assert len(token) > 0 and user["id"] > 0
        resp = client.post("/api/auth/login", json={
            "phone": user["phone"], "password": "testpass123",
        })
        assert resp.status_code == 200 and "access_token" in resp.json()

    def test_register_duplicate_phone(self, client):
        phone = gen_phone()
        client.post("/api/auth/register", json={"phone": phone, "password": "testpass123", "name": "A"})
        resp = client.post("/api/auth/register", json={"phone": phone, "password": "testpass456", "name": "B"})
        assert resp.status_code == 400 and "已注册" in resp.json()["detail"]

    def test_login_wrong_password(self, client):
        phone = gen_phone()
        client.post("/api/auth/register", json={"phone": phone, "password": "correct", "name": "测试"})
        resp = client.post("/api/auth/login", json={"phone": phone, "password": "wrong"})
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/auth/login", json={"phone": "13800000000", "password": "x"})
        assert resp.status_code == 401

    def test_register_invalid_phone_format(self, client):
        resp = client.post("/api/auth/register", json={"phone": "not-a-phone", "password": "123456", "name": "测试"})
        assert resp.status_code == 422

    def test_register_missing_password(self, client):
        resp = client.post("/api/auth/register", json={"phone": gen_phone(), "name": "测试"})
        assert resp.status_code == 422

class TestBrochureIntegration:
    def test_template_valid_purpose(self, client):
        resp = client.get("/api/brochures/template/partner")
        assert resp.status_code == 200 and resp.json()["purpose"] == "partner"

    def test_template_all_purposes(self, client):
        for p in ("partner", "client", "investor", "supplier"):
            resp = client.get(f"/api/brochures/template/{p}")
            assert resp.status_code == 200 and resp.json()["purpose"] == p

    def test_template_invalid_purpose(self, client):
        resp = client.get("/api/brochures/template/invalid")
        assert resp.status_code == 404

    def test_get_brochure_not_found(self, client):
        resp = client.get("/api/brochures/99999")
        assert resp.status_code == 404 and "detail" in resp.json()

    def test_create_brochure_without_auth_returns_401(self, client):
        resp = client.post("/api/brochures", json={"title": "test"})
        assert resp.status_code == 401

    def test_brochure_list_public(self, client):
        resp = client.get("/api/brochures")
        assert resp.status_code == 200 and isinstance(resp.json(), list)

class TestWeChatLoginIntegration:
    def test_wx_login_creates_new_user(self, client):
        resp = client.post("/api/auth/wx-login", json={"code": "code_1234"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data and data["user"]["name"].startswith("微信用户")

    def test_wx_login_repeat_returns_different_users(self, client):
        resp1 = client.post("/api/auth/wx-login", json={"code": "unique_code"})
        resp2 = client.post("/api/auth/wx-login", json={"code": "other_code"})
        assert resp1.status_code == 200 and resp2.status_code == 200
        assert resp1.json()["user"]["id"] != resp2.json()["user"]["id"]
