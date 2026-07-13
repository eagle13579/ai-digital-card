"""Tests for Developer API (API Key management).

Note: Uses _create_tables fixture to ensure app's SQLite tables exist
(since httpx ASGITransport doesn't trigger FastAPI startup events).
"""
import asyncio
import pytest
from httpx import AsyncClient

from app.database import Base, engine


BASE = "/api/v1/developer"


@pytest.fixture(scope="session")
def _create_tables():
    """Ensure tables exist on the app's in-memory engine (once per session)."""
    async def _init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(_init())
    loop.close()


def make_token_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
class TestDeveloperApi:
    """Developer API: API Key CRUD + usage + auth guard."""

    async def _register_and_login(self, client: AsyncClient, phone: str) -> dict:
        await client.post("/api/auth/register", json={
            "phone": phone, "password": "Test@1234", "name": "Dev User",
        })
        login_resp = await client.post("/api/auth/login", json={
            "phone": phone, "password": "Test@1234",
        })
        return make_token_headers(login_resp.json()["access_token"])

    async def test_create_api_key(self, client: AsyncClient, _create_tables):
        """POST → 201 + full token."""
        headers = await self._register_and_login(client, "13800001001")
        resp = await client.post(f"{BASE}/api-keys", json={
            "name": "My Key", "permissions": ["read", "write"],
        }, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] > 0
        assert data["key"].startswith("ask_")
        assert data["name"] == "My Key"
        assert data["permissions"] == ["read", "write"]
        assert data["is_active"] is True

    async def test_list_api_keys(self, client: AsyncClient, _create_tables):
        """GET → list with masked key."""
        headers = await self._register_and_login(client, "13800001002")
        await client.post(f"{BASE}/api-keys", json={"name": "Key A"}, headers=headers)
        resp = await client.get(f"{BASE}/api-keys", headers=headers)
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 1
        item = items[0]
        assert item["name"] == "Key A"
        assert "****" in item["masked_key"]
        assert item["is_active"] is True

    async def test_revoke_api_key(self, client: AsyncClient, _create_tables):
        """DELETE → 204, key becomes inactive."""
        headers = await self._register_and_login(client, "13800001003")
        create_resp = await client.post(f"{BASE}/api-keys", json={"name": "To Revoke"},
                                         headers=headers)
        key_id = create_resp.json()["id"]
        del_resp = await client.delete(f"{BASE}/api-keys/{key_id}", headers=headers)
        assert del_resp.status_code == 204
        list_resp = await client.get(f"{BASE}/api-keys", headers=headers)
        revoked = [k for k in list_resp.json() if k["id"] == key_id][0]
        assert revoked["is_active"] is False

    async def test_revoke_nonexistent_key_returns_404(self, client: AsyncClient, _create_tables):
        """DELETE with invalid id → 404."""
        headers = await self._register_and_login(client, "13800001004")
        resp = await client.delete(f"{BASE}/api-keys/99999", headers=headers)
        assert resp.status_code == 404

    async def test_usage_stats(self, client: AsyncClient, _create_tables):
        """GET /usage → 200 with counters."""
        headers = await self._register_and_login(client, "13800001005")
        create_resp = await client.post(f"{BASE}/api-keys", json={"name": "Usage Key"},
                                         headers=headers)
        assert create_resp.status_code == 201
        resp = await client.get(f"{BASE}/usage", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "this_month" in data
        assert "today" in data

    async def test_unauthorized_create(self, client: AsyncClient):
        """POST without auth → 401."""
        resp = await client.post(f"{BASE}/api-keys", json={"name": "No Auth"})
        assert resp.status_code == 401

    async def test_unauthorized_list(self, client: AsyncClient):
        """GET without auth → 401."""
        resp = await client.get(f"{BASE}/api-keys")
        assert resp.status_code == 401

    async def test_unauthorized_revoke(self, client: AsyncClient):
        """DELETE without auth → 401."""
        resp = await client.delete(f"{BASE}/api-keys/1")
        assert resp.status_code == 401

    async def test_unauthorized_usage(self, client: AsyncClient):
        """GET /usage without auth → 401."""
        resp = await client.get(f"{BASE}/usage")
        assert resp.status_code == 401

    async def test_create_multiple_keys(self, client: AsyncClient, _create_tables):
        """Create 2 keys, list returns both."""
        headers = await self._register_and_login(client, "13800001006")
        await client.post(f"{BASE}/api-keys", json={"name": "Key 1"}, headers=headers)
        await client.post(f"{BASE}/api-keys", json={"name": "Key 2"}, headers=headers)
        resp = await client.get(f"{BASE}/api-keys", headers=headers)
        items = resp.json()
        names = [i["name"] for i in items]
        assert "Key 1" in names
        assert "Key 2" in names
