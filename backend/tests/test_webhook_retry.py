"""Tests: WebhookRetryService — 重试/死信队列 (11 cases)"""
from unittest.mock import AsyncMock, patch
import httpx
import pytest
import pytest_asyncio
from app.services.webhook_retry import WebhookRetryService


@pytest_asyncio.fixture
async def retry_service():
    svc = WebhookRetryService()
    yield svc
    await svc.close()


def _mock_client(status_code=200, text="ok", exc=None):
    client = AsyncMock(spec=httpx.AsyncClient)
    async def post(*a, **kw):
        if exc: raise exc
        r = AsyncMock(spec=httpx.Response, status_code=status_code, text=text)
        return r
    client.post = post
    return client


# ── 1-3: 成功发送不需重试 ────────────────────────────────────

@pytest.mark.asyncio
async def test_send_success_200(retry_service):
    retry_service._client = _mock_client(200, "ok")
    r = await retry_service.send_with_retry("https://hook.example.com/evt", {"evt": "a"})
    assert r["success"] and r["status_code"] == 200
    assert retry_service.get_dead_letter_count() == 0

@pytest.mark.asyncio
async def test_send_success_201(retry_service):
    retry_service._client = _mock_client(201, "created")
    r = await retry_service.send_with_retry("https://hook.example.com/evt2", {"evt": "b"})
    assert r["success"] and r["status_code"] == 201

@pytest.mark.asyncio
async def test_4xx_is_success(retry_service):
    retry_service._client = _mock_client(400, "bad request")
    r = await retry_service.send_with_retry("https://hook.example.com/4xx", {"evt": "c"})
    assert r["success"] is True and r["status_code"] == 400

# ── 4-5: 触发全部重试后进入死信 ──────────────────────────────

@pytest.mark.asyncio
async def test_5xx_goes_to_dead_letter(retry_service):
    cnt = 0
    async def post(*a, **kw):
        nonlocal cnt; cnt += 1
        r = AsyncMock(spec=httpx.Response, status_code=500, text="err")
        return r
    retry_service._client = AsyncMock(spec=httpx.AsyncClient); retry_service._client.post = post
    with patch("asyncio.sleep"):
        r = await retry_service.send_with_retry("https://hook.example.com/5xx", {"evt": "t"})
    assert r["success"] is False and r["status_code"] == 500
    assert r["dead_letter_id"] is not None and retry_service.get_dead_letter_count() == 1
    assert cnt == 5

@pytest.mark.asyncio
async def test_connection_error_goes_to_dead_letter(retry_service):
    cnt = 0
    async def post(*a, **kw):
        nonlocal cnt; cnt += 1
        raise httpx.ConnectError("Connection refused")
    retry_service._client = AsyncMock(spec=httpx.AsyncClient); retry_service._client.post = post
    with patch("asyncio.sleep"):
        r = await retry_service.send_with_retry("https://hook.example.com/refused", {"evt": "t"})
    assert r["success"] is False and "Connection refused" in r["error"]
    assert r["dead_letter_id"] is not None and retry_service.get_dead_letter_count() == 1
    assert cnt == 5

# ── 6-8: 死信队列管理 ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_all_dead_letters(retry_service):
    retry_service._client = _mock_client(500, "err")
    with patch("asyncio.sleep"):
        r1 = await retry_service.send_with_retry("https://hook.a", {"evt": "a"})
        r2 = await retry_service.send_with_retry("https://hook.b", {"evt": "b"})
        r3 = await retry_service.send_with_retry("https://hook.c", {"evt": "c"})
    all_dl = retry_service.get_dead_letter()
    assert len(all_dl) == 3
    assert all_dl[0]["id"] == r1["dead_letter_id"]
    for dl in all_dl:
        assert all(k in dl for k in ("url", "payload", "attempts", "last_error"))

@pytest.mark.asyncio
async def test_get_dead_letter_by_id(retry_service):
    retry_service._client = _mock_client(500, "err")
    with patch("asyncio.sleep"):
        r = await retry_service.send_with_retry("https://hook.example.com/x", {"evt": "x"})
    items = retry_service.get_dead_letter(r["dead_letter_id"])
    assert len(items) == 1 and items[0]["id"] == r["dead_letter_id"]

def test_get_dead_letter_not_found():
    svc = WebhookRetryService()
    assert svc.get_dead_letter(99999) == []

# ── 9-11: 手动重试死信 ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_retry_dead_letter_success_removes(retry_service):
    cnt = 0
    async def post(*a, **kw):
        nonlocal cnt; cnt += 1
        r = AsyncMock(spec=httpx.Response)
        r.status_code = 200 if cnt > 5 else 500; r.text = "ok"
        return r
    retry_service._client = AsyncMock(spec=httpx.AsyncClient); retry_service._client.post = post
    with patch("asyncio.sleep"):
        r1 = await retry_service.send_with_retry("https://hook.example.com/rm", {"evt": "t"})
    dl_id = r1["dead_letter_id"]
    assert retry_service.get_dead_letter_count() == 1
    with patch("asyncio.sleep"):
        r2 = await retry_service.retry_dead_letter(dl_id)
    assert r2["success"] is True
    assert retry_service.get_dead_letter_count() == 0

@pytest.mark.asyncio
async def test_retry_dead_letter_fail_updates(retry_service):
    retry_service._client = _mock_client(503, "service unavailable")
    with patch("asyncio.sleep"):
        r1 = await retry_service.send_with_retry("https://hook.example.com/broken", {"evt": "f"})
    with patch("asyncio.sleep"):
        r2 = await retry_service.retry_dead_letter(r1["dead_letter_id"])
    assert r2["success"] is False
    assert retry_service.get_dead_letter_count() == 1
    assert "service unavailable" in retry_service.get_dead_letter()[0]["last_error"]

@pytest.mark.asyncio
async def test_retry_dead_letter_not_found(retry_service):
    r = await retry_service.retry_dead_letter(99999)
    assert r["success"] is False and "not found" in r["error"]
