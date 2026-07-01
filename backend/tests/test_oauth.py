"""OAuthService 单元测试 — 覆盖 16 用例"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.oauth_service import OAuthService, get_oauth_service


# ══════════════════════════════════════════════════════════════════════
# Helpers & Fixtures
# ══════════════════════════════════════════════════════════════════════


def _make_mock_resp(status_code: int, json_data: dict):
    """Sync-style mock HTTP response (httpx.Response.json is sync)."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = MagicMock(return_value=json_data)
    resp.text = str(json_data)
    if status_code >= 400:
        resp.raise_for_status.side_effect = __import__("httpx").HTTPStatusError(
            f"{status_code}", request=MagicMock(), response=resp
        )
    else:
        resp.raise_for_status = MagicMock()
    return resp


def _patch_async_client(post_resp=None, get_resp=None):
    """Patch httpx.AsyncClient so async-with returns a client with sync-style methods."""
    client = MagicMock()
    if post_resp is not None:
        client.post = AsyncMock(return_value=post_resp)
    if get_resp is not None:
        client.get = AsyncMock(return_value=get_resp)

    cls_mock = MagicMock()
    cls_mock.return_value.__aenter__ = AsyncMock(return_value=client)
    return patch("httpx.AsyncClient", cls_mock)


@pytest.fixture
def svc() -> OAuthService:
    """Fresh OAuthService with 3 providers registered"""
    s = OAuthService()
    s.register_provider(
        name="google",
        client_id="gid123",
        client_secret="gsecret123",
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
        scopes=["openid", "email", "profile"],
    )
    s.register_provider(
        name="github",
        client_id="ghid456",
        client_secret="ghsecret456",
        auth_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        userinfo_url="https://api.github.com/user",
        scopes=["read:user", "user:email"],
    )
    s.register_provider(
        name="wechat",
        client_id="wxid789",
        client_secret="wxsecret789",
        auth_url="https://open.weixin.qq.com/connect/qrconnect",
        token_url="https://api.weixin.qq.com/sns/oauth2/access_token",
        userinfo_url="https://api.weixin.qq.com/sns/userinfo",
        scopes=["snsapi_login"],
    )
    return s


# ══════════════════════════════════════════════════════════════════════
# Test 1-3: get_provider
# ══════════════════════════════════════════════════════════════════════


def test_get_provider_returns_config(svc):
    cfg = svc.get_provider("google")
    assert cfg is not None
    assert cfg.name == "google"
    assert cfg.client_id == "gid123"


def test_get_provider_returns_none_for_unknown(svc):
    assert svc.get_provider("unknown") is None


def test_get_provider_wechat(svc):
    cfg = svc.get_provider("wechat")
    assert cfg is not None
    assert cfg.name == "wechat"
    assert cfg.auth_url == "https://open.weixin.qq.com/connect/qrconnect"


# ══════════════════════════════════════════════════════════════════════
# Test 4-7: get_authorization_url
# ══════════════════════════════════════════════════════════════════════


def test_get_authorization_url_builds_correct_url(svc):
    url = svc.get_authorization_url("google", "https://example.com/callback")
    assert url is not None
    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=gid123" in url
    assert "response_type=code" in url
    assert "redirect_uri=https%3A%2F%2Fexample.com%2Fcallback" in url
    assert "scope=openid+email+profile" in url
    assert "state=" in url


def test_get_authorization_url_github(svc):
    url = svc.get_authorization_url("github", "https://example.com/cb")
    assert url is not None
    assert url.startswith("https://github.com/login/oauth/authorize?")
    assert "client_id=ghid456" in url
    assert "scope=read%3Auser+user%3Aemail" in url


def test_get_authorization_url_wechat(svc):
    url = svc.get_authorization_url("wechat", "https://example.com/cb")
    assert url is not None
    assert url.startswith("https://open.weixin.qq.com/connect/qrconnect?")
    assert "client_id=wxid789" in url
    assert "scope=snsapi_login" in url


def test_get_authorization_url_unknown_provider(svc):
    url = svc.get_authorization_url("unknown", "https://x.com/cb")
    assert url is None


# ══════════════════════════════════════════════════════════════════════
# Test 8-10: exchange_code
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_exchange_code_success(svc):
    mock_resp = _make_mock_resp(200, {"access_token": "at_xyz", "token_type": "bearer"})
    with _patch_async_client(post_resp=mock_resp):
        result = await svc.exchange_code("google", "auth_code_abc", "https://x.com/cb")

    assert result["access_token"] == "at_xyz"
    assert result["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_exchange_code_http_error(svc):
    mock_resp = _make_mock_resp(400, {"error": "bad_request"})
    with _patch_async_client(post_resp=mock_resp):
        with pytest.raises(ValueError, match="令牌交换 HTTP 错误"):
            await svc.exchange_code("google", "bad_code", "https://x.com/cb")


@pytest.mark.asyncio
async def test_exchange_code_unknown_provider(svc):
    with pytest.raises(ValueError, match="not registered"):
        await svc.exchange_code("unknown", "code", "https://x.com/cb")


# ══════════════════════════════════════════════════════════════════════
# Test 11-12: get_user_info
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_user_info_google(svc):
    mock_resp = _make_mock_resp(200, {
        "sub": "google_123",
        "email": "alice@gmail.com",
        "name": "Alice",
        "picture": "https://example.com/avatar.png",
    })
    with _patch_async_client(get_resp=mock_resp):
        info = await svc.get_user_info("google", "at_xyz")

    assert info["sub"] == "google_123"
    assert info["email"] == "alice@gmail.com"
    assert info["name"] == "Alice"
    assert info["picture"] == "https://example.com/avatar.png"


@pytest.mark.asyncio
async def test_get_user_info_github(svc):
    mock_resp = _make_mock_resp(200, {
        "id": 42,
        "login": "octocat",
        "name": "Octo Cat",
        "avatar_url": "https://avatars.githubusercontent.com/u/42",
    })
    with _patch_async_client(get_resp=mock_resp):
        info = await svc.get_user_info("github", "at_xyz")

    assert info["sub"] == "42"
    assert info["name"] == "Octo Cat"
    assert info["picture"].startswith("https://avatars")


# ══════════════════════════════════════════════════════════════════════
# Test 13-14: list_providers / register_provider
# ══════════════════════════════════════════════════════════════════════


def test_list_providers(svc):
    names = svc.list_providers()
    assert "google" in names
    assert "github" in names
    assert "wechat" in names
    assert len(names) == 3


def test_register_provider_dynamic(svc):
    svc.register_provider(
        name="custom",
        client_id="cid",
        client_secret="csec",
        auth_url="https://custom.example.com/auth",
        token_url="https://custom.example.com/token",
        userinfo_url="https://custom.example.com/userinfo",
        scopes=["openid"],
    )
    cfg = svc.get_provider("custom")
    assert cfg is not None
    assert cfg.auth_url == "https://custom.example.com/auth"


# ══════════════════════════════════════════════════════════════════════
# Test 15: exchange_code provider error in response
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_exchange_code_provider_error(svc):
    mock_resp = _make_mock_resp(200, {"error": "invalid_grant", "error_description": "code expired"})
    with _patch_async_client(post_resp=mock_resp):
        with pytest.raises(ValueError, match="提供商返回错误"):
            await svc.exchange_code("google", "stale_code", "https://x.com/cb")


# ══════════════════════════════════════════════════════════════════════
# Test 16: singleton factory
# ══════════════════════════════════════════════════════════════════════


def test_get_oauth_service_singleton():
    s1 = get_oauth_service()
    s2 = get_oauth_service()
    assert s1 is s2
    assert "google" in s1.list_providers()
    assert "github" in s1.list_providers()
    assert "wechat" in s1.list_providers()
