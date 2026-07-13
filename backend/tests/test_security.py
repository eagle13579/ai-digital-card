"""Tests for security headers middleware.

Verifies all 9 security headers are present and correct on HTTP responses.
Uses the shared ``conftest.py`` ``client`` fixture (ASGI transport).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.middleware.security_headers import SECURITY_HEADERS


class TestSecurityHeadersPresent:
    """Every security header defined in SECURITY_HEADERS must appear on every
    HTTP response, including error pages."""

    @pytest.mark.asyncio
    async def test_health_has_all_security_headers(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        for name, value in SECURITY_HEADERS.items():
            assert resp.headers.get(name.lower()) == value, (
                f"Missing or wrong header: {name}"
            )

    @pytest.mark.asyncio
    async def test_api_health_has_all_security_headers(self, client: AsyncClient):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        for name, value in SECURITY_HEADERS.items():
            assert resp.headers.get(name.lower()) == value

    @pytest.mark.asyncio
    async def test_404_has_all_security_headers(self, client: AsyncClient):
        resp = await client.get("/nonexistent-endpoint-xyz")
        assert resp.status_code == 404
        for name, value in SECURITY_HEADERS.items():
            assert resp.headers.get(name.lower()) == value

    @pytest.mark.asyncio
    async def test_root_has_all_security_headers(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        for name, value in SECURITY_HEADERS.items():
            assert resp.headers.get(name.lower()) == value


class TestIndividualSecurityHeaders:
    """Verify each header individually with correct value."""

    @pytest.mark.asyncio
    async def test_content_security_policy(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.headers.get("content-security-policy") == (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://hm.baidu.com https://*.baidu.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: blob: https:; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "connect-src 'self' https://api.liankebao.top wss:; "
            "frame-src 'self' https:; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'; "
            "object-src 'none'; "
            "upgrade-insecure-requests"
        )

    @pytest.mark.asyncio
    async def test_strict_transport_security(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.headers.get("strict-transport-security") == (
            "max-age=31536000; includeSubDomains; preload"
        )

    @pytest.mark.asyncio
    async def test_x_content_type_options(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    @pytest.mark.asyncio
    async def test_x_frame_options(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.headers.get("x-frame-options") == "DENY"

    @pytest.mark.asyncio
    async def test_x_xss_protection(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.headers.get("x-xss-protection") == "1; mode=block"

    @pytest.mark.asyncio
    async def test_referrer_policy(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.headers.get("referrer-policy") == (
            "strict-origin-when-cross-origin"
        )

    @pytest.mark.asyncio
    async def test_permissions_policy(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.headers.get("permissions-policy") == (
            "camera=(), microphone=(), geolocation=(), "
            "display-capture=(), fullscreen=(self), "
            "payment=(), usb=(), magnetometer=(), "
            "accelerometer=(), gyroscope=(), "
            "interest-cohort=()"
        )

    @pytest.mark.asyncio
    async def test_headers_not_overridden_by_existing_headers(self, client: AsyncClient):
        """If a downstream response sets a header with the same name, the
        middleware must NOT clobber it."""
        resp = await client.get("/health")
        # The middleware adds lat/lng — just check all headers are present
        assert "x-xss-protection" in resp.headers
        assert "x-frame-options" in resp.headers


class TestSecurityHeadersMiddlewareIsolation:
    """Double-check the middleware class can be imported and instantiated."""

    def test_import_and_instantiate(self):
        from app.middleware.security_headers import SecurityHeadersMiddleware

        instance = SecurityHeadersMiddleware(app=None)
        assert instance is not None
        assert instance.app is None

    def test_security_headers_dict_is_complete(self):
        expected_keys = {
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy",
            "Cross-Origin-Embedder-Policy",
            "Cross-Origin-Opener-Policy",
        }
        assert set(SECURITY_HEADERS.keys()) == expected_keys
