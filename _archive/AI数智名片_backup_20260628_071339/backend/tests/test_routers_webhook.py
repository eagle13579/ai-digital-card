"""
Webhook 订阅管理 API 测试 — CRUD + 事件触发 + HMAC + 重试机制。

覆盖 10 个测试用例:
  1. 创建 Webhook 成功
  2. 创建 Webhook 非法事件
  3. 列表 / 详情
  4. 找不到返回 404
  5. 更新配置
  6. 删除订阅
  7. 测试事件发送
  8. 手动触发事件
  9. HMAC-SHA256 签名
  10. 重试机制 (5xx 重试)
"""

import json
import hmac
import hashlib
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def _make_sub(sub_id=1, user_id=1, url="https://example.com/hook", secret="sk",
              events=None, active=True, retry_count=3, timeout=10):
    if events is None:
        events = ["card.created", "card.updated"]
    sub = MagicMock()
    sub.id = sub_id
    sub.user_id = user_id
    sub.name = f"订阅{sub_id}"
    sub.url = url
    sub.secret = secret
    sub.active = active
    sub.retry_count = retry_count
    sub.timeout_seconds = timeout
    sub.last_triggered_at = None
    sub.last_response_code = 200
    sub.last_error = ""
    sub.created_at = datetime(2026, 6, 27, 12, 0, 0)
    sub.updated_at = datetime(2026, 6, 27, 12, 0, 0)
    sub.get_events_list = lambda: events
    sub.set_events_list = lambda evts: events.clear() or events.extend(evts)
    return sub


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def client(mock_db):
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user
    from app.models.user import User

    async def _db_override():
        yield mock_db

    fake_user = MagicMock(spec=User)
    fake_user.id = 1
    fake_user.name = "测试用户"

    async def _user_override():
        return fake_user

    app.dependency_overrides = {}
    app.dependency_overrides[get_db] = _db_override
    app.dependency_overrides[get_current_user] = _user_override
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


class TestWebhookCRUD:
    """Webhook CRUD (6 用例)。"""

    BASE = "/api/webhooks"

    def test_create_success(self, client, mock_db):
        sub = _make_sub(sub_id=42)
        async def refresh_side(obj):
            for a in ["id", "user_id", "created_at", "updated_at"]:
                setattr(obj, a, getattr(sub, a))
            obj.get_events_list = sub.get_events_list
        mock_db.refresh = AsyncMock(side_effect=refresh_side)
        resp = client.post(self.BASE, json={"url": "https://ex.com/h", "events": ["card.created"]})
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["events"] == ["card.created"]

    def test_create_invalid_event(self, client):
        resp = client.post(self.BASE, json={"url": "https://ex.com/h", "events": ["bad.event"]})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_webhooks(self, client, mock_db):
        mock_db.execute.return_value.scalars.return_value.all.return_value = [
            _make_sub(sub_id=1), _make_sub(sub_id=2)]
        resp = client.get(self.BASE)
        assert len(resp.json()) == 2

    def test_get_not_found(self, client, mock_db):
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        resp = client.get(f"{self.BASE}/999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_update_webhook(self, client, mock_db):
        sub = _make_sub(sub_id=1)
        mock_db.execute.return_value.scalar_one_or_none.return_value = sub
        resp = client.put(f"{self.BASE}/1", json={"url": "https://new.ex.com"})
        assert resp.status_code == status.HTTP_200_OK
        assert sub.url == "https://new.ex.com"

    def test_delete_webhook(self, client, mock_db):
        mock_db.execute.return_value.scalar_one_or_none.return_value = _make_sub(sub_id=1)
        resp = client.delete(f"{self.BASE}/1")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert mock_db.delete.called


class TestWebhookTrigger:
    """事件触发 (2 用例)。"""

    BASE = "/api/webhooks"

    def test_test_event(self, client, mock_db):
        mock_db.execute.return_value.scalar_one_or_none.return_value = _make_sub(sub_id=1, active=True)
        with patch("app.routers.webhooks.webhook_dispatcher.dispatch", new_callable=AsyncMock) as md:
            md.return_value = [{"subscription_id": 1, "success": True, "status_code": 200}]
            resp = client.post(f"{self.BASE}/1/test", json={})
            assert resp.json()["success"] is True

    def test_trigger_event(self, client, mock_db):
        with patch("app.routers.webhooks.webhook_dispatcher.dispatch", new_callable=AsyncMock) as md:
            md.return_value = [{"subscription_id": 1, "success": True}]
            resp = client.post(f"{self.BASE}/trigger?event_type=card.created", json={"id": 1})
            assert resp.json()["matched_subscriptions"] == 1


class TestHMACAndRetry:
    """HMAC 签名 + 重试 (2 用例)。"""

    @pytest.mark.asyncio
    async def test_hmac_signature(self):
        from app.services.webhook_dispatcher import WebhookDispatcher
        d = WebhookDispatcher()
        d._client = AsyncMock()
        d._client.post = AsyncMock(return_value=MagicMock(status_code=200))
        sub = _make_sub(secret="testkey")
        async def sf():
            db = AsyncMock()
            db.__aenter__ = AsyncMock(return_value=db)
            db.__aexit__ = AsyncMock()
            db.execute = AsyncMock(return_value=AsyncMock(scalar_one_or_none=lambda: sub))
            return db
        with patch("app.services.webhook_dispatcher.select"):
            await d.dispatch(db_session_factory=sf, event_type="card.created", payload={"x": 1}, user_id=1)
        headers = d._client.post.call_args[1]["headers"]
        assert "X-Webhook-Signature" in headers
        assert len(headers["X-Webhook-Signature"]) == 64

    @pytest.mark.asyncio
    async def test_retry_on_5xx(self):
        from app.services.webhook_dispatcher import WebhookDispatcher
        d = WebhookDispatcher()
        d._client = AsyncMock()
        d._client.post = AsyncMock(side_effect=[
            MagicMock(status_code=500, text="ERR"),
            MagicMock(status_code=502, text="BAD"),
            MagicMock(status_code=200, text="OK"),
        ])
        sub = _make_sub(retry_count=3)
        async def sf():
            db = AsyncMock()
            db.__aenter__ = AsyncMock(return_value=db)
            db.__aexit__ = AsyncMock()
            db.execute = AsyncMock(return_value=AsyncMock(scalar_one_or_none=lambda: sub))
            return db
        with patch("app.services.webhook_dispatcher.select"):
            r = await d.dispatch(db_session_factory=sf, event_type="card.created", payload={}, user_id=1)
        assert r[0]["success"] is True
        assert r[0]["status_code"] == 200
        assert d._client.post.call_count == 3
