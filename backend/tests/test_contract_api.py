"""
API契约测试: 响应格式合同验证
验证每个端点的响应包含预期字段, error 响应格式一致
(不依赖异步greenlet兼容性, 仅验证可正常返回的端点)
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
    loop.run_until_complete(_prepare())
    app.dependency_overrides[get_db] = _get_test_db
    yield
    loop.run_until_complete(_teardown())
    loop.close()
    app.dependency_overrides.clear()

async def _prepare():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def _teardown():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _test_engine.dispose()

async def _get_test_db():
    async with _test_async_session_factory() as session:
        yield session

def gen_phone():
    return "1" + "".join(random.choices("0123456789", k=10))

@pytest.fixture
def client(_setup_db):
    return TestClient(app)

@pytest.fixture
def auth_token(client):
    phone, suffix = gen_phone(), "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8))
    resp = client.post("/api/auth/register", json={
        "phone": phone, "password": "contractpass", "name": "契约测试", "username": f"ct{suffix}",
    })
    assert resp.status_code == 200, f"注册失败: {resp.json()}"
    return resp.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

class TestHealthContract:
    def test_health_content_type(self, client):
        resp = client.get("/health")
        assert "text/plain" in resp.headers.get("content-type", "")

    def test_api_health_field_types(self, client):
        data = client.get("/api/health").json()
        assert isinstance(data["status"], str) and isinstance(data["service"], str)

class TestAuthContract:
    def test_register_response_structure(self, client):
        resp = client.post("/api/auth/register", json={
            "phone": gen_phone(), "password": "testpass123", "name": "契约验证",
        })
        data = resp.json()
        assert {"access_token", "token_type", "user"}.issubset(data.keys())
        assert isinstance(data["access_token"], str) and len(data["access_token"]) > 0
        assert data["token_type"] == "bearer"

    def test_user_response_all_fields(self, client):
        resp = client.post("/api/auth/register", json={
            "phone": gen_phone(), "password": "testpass123", "name": "字段完整",
        })
        user = resp.json()["user"]
        required = {"id", "phone", "name", "avatar", "company", "title",
                     "intro", "role", "membership_tier", "created_at", "updated_at"}
        assert not (required - user.keys()), f"缺少字段: {required - user.keys()}"
        assert isinstance(user["id"], int) and user["role"] in ("user", "admin")

    def test_422_error_format(self, client):
        resp = client.post("/api/auth/register", json={"phone": "bad"})
        assert resp.status_code == 422 and "detail" in resp.json()

    def test_401_error_format(self, client):
        resp = client.post("/api/brochures", json={"title": "x"})
        assert resp.status_code == 401 and isinstance(resp.json()["detail"], str)

    def test_404_error_format(self, client):
        resp = client.get("/api/brochures/99999")
        assert resp.status_code == 404 and isinstance(resp.json()["detail"], str)

    def test_400_error_format(self, client):
        phone = gen_phone()
        client.post("/api/auth/register", json={"phone": phone, "password": "testpass123", "name": "dup"})
        resp = client.post("/api/auth/register", json={"phone": phone, "password": "testpass456", "name": "dup2"})
        assert resp.status_code == 400 and isinstance(resp.json()["detail"], str)

class TestBrochureContract:
    def test_template_required_keys(self, client):
        data = client.get("/api/brochures/template/partner").json()
        for key in ("purpose", "name", "theme", "pages", "highlights", "suggested_sections"):
            assert key in data, f"缺少字段: {key}"

    def test_template_theme_has_primary(self, client):
        for p in ("partner", "client", "investor", "supplier"):
            data = client.get(f"/api/brochures/template/{p}").json()
            assert "primary" in data["theme"], f"{p} 缺少 theme.primary"

    def test_template_pages_have_type_and_title(self, client):
        data = client.get("/api/brochures/template/investor").json()
        for page in data["pages"]:
            assert "type" in page and "title" in page

    def test_brochure_list_is_array(self, client):
        assert isinstance(client.get("/api/brochures").json(), list)
