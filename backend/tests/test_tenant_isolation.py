"""
Test: Multi-tenant 数据隔离

验证 15 个场景:
  1. 不同 tenant_id 看不到对方数据
  2. TenantSession 自动 tenant_id 过滤
  3. 不加过滤看到全部
  4. TenantSession.add() 自动填充 tenant_id
  5. 已存在的 WHERE tenant_id 条件不重复加
  6. JWT 中提取 tenant_id
  7. 无 tenant_id 时 require_tenant 拒绝
  8. ContextVar 隔离
  9. Admin 创建租户
 10. 重复 slug 返回 409
 11. Admin 列表租户
 12. 无 tenant_id /profile 返回 400
 13. 有 tenant_id /profile 成功
 14. 非 admin 不能创建租户
 15. 非 TenantBase 模型不受 TenantSession 影响
"""
from __future__ import annotations

import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── 设置测试环境变量 (必须在 app 导入前) ──────────────────────────────
os.environ.setdefault("JWT_SECRET", "test-tenant-secret-key-1234567890")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from app.database import Base
from app.middleware.tenant import (
    TenantMiddleware,
    TenantSession,
    tenant_id_var,
    get_current_tenant_id,
    require_tenant,
)
from app.models.tenant import Tenant, TenantBase
from app.routers.auth import create_access_token

# ── Test Model (继承 TenantBase 用于验证隔离) ─────────────────────────
class TenantItem(TenantBase):
    __tablename__ = "tenant_items"
    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    name: str = Column(String(64), nullable=False)  # type: ignore


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def _app():
    """创建带 TenantMiddleware 的 FastAPI 应用 (module scope)。"""
    from app.__init__ import create_app
    app = create_app()
    app.add_middleware(TenantMiddleware)
    return app


@pytest_asyncio.fixture
async def test_db():
    """内存 SQLite — 只建 TenantItem 表 (tenants 由 Base.metadata 自动建)。"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        await session.close()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def seed_tenants(test_db):
    """创建两个租户。"""
    t1 = Tenant(name="Acme Corp", slug="acme", plan="PRO")
    t2 = Tenant(name="Globex Inc", slug="globex", plan="FREE")
    test_db.add_all([t1, t2])
    await test_db.commit()
    await test_db.refresh(t1)
    await test_db.refresh(t2)
    return t1, t2


@pytest_asyncio.fixture
async def seed_items(test_db, seed_tenants):
    """每个租户下各创建 2 条 TenantItem。"""
    t1, t2 = seed_tenants
    items = [
        TenantItem(tenant_id=t1.id, name=f"acme-item-{i}") for i in range(2)
    ] + [
        TenantItem(tenant_id=t2.id, name=f"globex-item-{i}") for i in range(2)
    ]
    test_db.add_all(items)
    await test_db.commit()
    return t1, t2


# ══════════════════════════════════════════════════════════════════════
# Test: TenantSession — 自动租户过滤
# ══════════════════════════════════════════════════════════════════════

class TestTenantSession:
    """TenantSession 自动租户过滤"""

    @pytest.mark.asyncio
    async def test_auto_filter_by_tenant(self, test_db, seed_items):
        """租户 1 只能看到自己的 2 条数据。"""
        t1, _ = seed_items
        tdb = TenantSession(test_db, tenant_id=t1.id)
        result = await tdb.execute(select(TenantItem).order_by(TenantItem.id))
        rows = result.scalars().all()
        assert len(rows) == 2, f"期望 2 条, 得到 {len(rows)}"
        for r in rows:
            assert r.tenant_id == t1.id

    @pytest.mark.asyncio
    async def test_tenant_b_sees_only_own_data(self, test_db, seed_items):
        """租户 2 只能看到自己的 2 条。"""
        _, t2 = seed_items
        tdb = TenantSession(test_db, tenant_id=t2.id)
        result = await tdb.execute(select(TenantItem))
        rows = result.scalars().all()
        assert len(rows) == 2
        for r in rows:
            assert r.tenant_id == t2.id

    @pytest.mark.asyncio
    async def test_no_tenant_session_sees_all(self, test_db, seed_items):
        """不加 TenantSession 可以看到全部 4 条。"""
        result = await test_db.execute(select(TenantItem).order_by(TenantItem.id))
        rows = result.scalars().all()
        assert len(rows) == 4

    @pytest.mark.asyncio
    async def test_auto_fill_tenant_id_on_add(self, test_db, seed_tenants):
        """TenantSession.add() 自动填充 tenant_id。"""
        t1, _ = seed_tenants
        tdb = TenantSession(test_db, tenant_id=t1.id)
        item = TenantItem(name="auto-fill-test")
        tdb.add(item)
        assert item.tenant_id == t1.id

    @pytest.mark.asyncio
    async def test_existing_tenant_condition_not_duplicated(self, test_db, seed_items):
        """查询已有 tenant_id WHERE 条件时不重复加。"""
        t1, _ = seed_items
        tdb = TenantSession(test_db, tenant_id=t1.id)
        stmt = select(TenantItem).where(TenantItem.tenant_id == t1.id, TenantItem.name.like("acme%"))
        result = await tdb.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_non_tenant_model_unaffected(self, test_db, seed_items):
        """非 TenantBase 模型的查询不受 TenantSession 影响。"""
        from app.models.user import User
        from app.routers.auth import pwd_context
        u = User(phone="13800000102", name="独立用户", password_hash=pwd_context.hash("p"))
        test_db.add(u)
        await test_db.commit()

        t1, _ = seed_items
        tdb = TenantSession(test_db, tenant_id=t1.id)
        result = await tdb.execute(select(User).where(User.phone == "13800000102"))
        rows = result.scalars().all()
        assert len(rows) == 1


# ══════════════════════════════════════════════════════════════════════
# Test: TenantMiddleware — JWT / ContextVar
# ══════════════════════════════════════════════════════════════════════

class TestTenantMiddleware:
    """TenantMiddleware 的 JWT / Header 提取"""

    @pytest.mark.asyncio
    async def test_extract_tenant_from_jwt(self):
        """从 JWT payload 提取 tenant_id。"""
        token = create_access_token({"sub": "1", "tenant_id": 42, "tenant_plan": "PRO"})
        from app.middleware.tenant import _decode_jwt_payload
        payload = _decode_jwt_payload(token)
        assert payload.get("tenant_id") == 42
        assert payload.get("tenant_plan") == "PRO"

    @pytest.mark.asyncio
    async def test_no_tenant_id_rejected(self):
        """无 tenant_id 时 require_tenant 抛 HTTPException 400。"""
        tenant_id_var.set(None)
        tid = await get_current_tenant_id()
        assert tid is None
        with pytest.raises(Exception):
            await require_tenant()

    @pytest.mark.asyncio
    async def test_contextvar_isolation(self):
        """不同协程的 tenant_id 互不干扰。"""
        import asyncio

        async def worker(tid):
            token = tenant_id_var.set(tid)
            await asyncio.sleep(0.01)
            result = tenant_id_var.get()
            tenant_id_var.reset(token)
            return result

        results = await asyncio.gather(worker(1), worker(2), worker(3))
        assert results == [1, 2, 3]


# ══════════════════════════════════════════════════════════════════════
# Test: Tenant API — 集成测试
# ══════════════════════════════════════════════════════════════════════

class TestTenantAPI:
    """Tenant 管理 API 集成测试"""

    @pytest_asyncio.fixture
    async def client(self, _app, test_db):
        from app.database import get_db

        async def _override():
            yield test_db

        _app.dependency_overrides[get_db] = _override
        transport = ASGITransport(app=_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
        _app.dependency_overrides.clear()

    @pytest_asyncio.fixture
    async def admin_user(self, test_db):
        from app.models.user import User
        from app.routers.auth import pwd_context
        user = User(
            phone="13800000999", name="Admin", username="admin",
            password_hash=pwd_context.hash("admin123"), role="admin",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        return user

    @pytest_asyncio.fixture
    async def admin_headers(self, admin_user):
        token = create_access_token({"sub": str(admin_user.id), "tenant_id": 1})
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_admin_create_tenant(self, client, test_db, admin_headers):
        """POST /api/v1/admin/tenants 成功创建租户。"""
        payload = {"name": "新租户", "slug": "newco", "plan": "FREE"}
        resp = await client.post("/api/v1/admin/tenants", json=payload, headers=admin_headers)
        assert resp.status_code == 200, f"body={resp.text}"
        data = resp.json()
        assert data["name"] == "新租户"
        assert data["slug"] == "newco"

    @pytest.mark.asyncio
    async def test_admin_create_tenant_duplicate_slug(self, client, test_db, admin_headers, seed_tenants):
        """POST 重复 slug 返回 409。"""
        payload = {"name": "重复", "slug": "acme", "plan": "FREE"}
        resp = await client.post("/api/v1/admin/tenants", json=payload, headers=admin_headers)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_admin_list_tenants(self, client, test_db, admin_headers, seed_tenants):
        """GET /api/v1/admin/tenants 返回租户列表。"""
        resp = await client.get("/api/v1/admin/tenants", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        slugs = {i["slug"] for i in data["items"]}
        assert "acme" in slugs
        assert "globex" in slugs

    @pytest.mark.asyncio
    async def test_tenant_profile_no_tenant(self, client, test_db):
        """无 tenant_id 时 /api/v1/tenant/profile 返回 400。"""
        from app.models.user import User
        from app.routers.auth import pwd_context
        user = User(phone="13800000103", name="无租户用户", password_hash=pwd_context.hash("pass"))
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        token = create_access_token({"sub": str(user.id)})  # 无 tenant_id
        resp = await client.get("/api/v1/tenant/profile", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_tenant_profile_success(self, client, test_db, seed_tenants):
        """有 tenant_id 时 /api/v1/tenant/profile 返回租户信息。"""
        from app.models.user import User
        from app.routers.auth import pwd_context
        user = User(phone="13800000100", name="租户用户", password_hash=pwd_context.hash("pass"), role="user")
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        t1, _ = seed_tenants
        token = create_access_token({"sub": str(user.id), "tenant_id": t1.id})
        resp = await client.get("/api/v1/tenant/profile", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Acme Corp"

    @pytest.mark.asyncio
    async def test_non_admin_cannot_create_tenant(self, client, test_db):
        """非 admin 用户创建租户返回 403。"""
        from app.models.user import User
        from app.routers.auth import pwd_context
        user = User(phone="13800000101", name="普通用户", password_hash=pwd_context.hash("pass"), role="user")
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        token = create_access_token({"sub": str(user.id)})
        resp = await client.post("/api/v1/admin/tenants", json={"name": "x", "slug": "x", "plan": "FREE"},
                                 headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
