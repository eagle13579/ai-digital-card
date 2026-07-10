"""健康检查端点测试 — 轻量版健康检查 & API健康检查"""

from __future__ import annotations

import os
from unittest import mock

import pytest


class TestHealthEndpoint:
    """健康检查端点基础测试"""

    @pytest.mark.asyncio
    async def test_health_returns_200_ok(self, client):
        """GET /health 应返回 200 + 纯文本 OK"""
        resp = await client.get("/health")
        assert resp.status_code == 200
        text = resp.text
        assert "OK" in text
        # 应为纯文本响应
        content_type = resp.headers.get("content-type", "")
        assert "text/plain" in content_type or "text" in content_type

    @pytest.mark.asyncio
    async def test_api_v1_health_returns_200(self, client):
        """GET /api/v1/health 应被重写为 /api/health 并返回 200"""
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "service" in body
        assert "version" in body

    @pytest.mark.asyncio
    async def test_api_health_returns_json_with_all_fields(self, client):
        """GET /api/health 返回完整的系统信息 JSON"""
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()

        # 必须包含的字段
        assert body["status"] == "ok"
        assert "service" in body
        assert "version" in body

        # version 应为字符串（版本号格式）
        assert isinstance(body["version"], str)
        assert len(body["version"]) > 0

    @pytest.mark.asyncio
    async def test_root_returns_200(self, client):
        """GET / 应返回 200"""
        resp = await client.get("/")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_production_docs_disabled(self):
        """ENV=production 时 docs_enabled 应为 False"""
        from app.config import Settings

        with mock.patch.dict(
            os.environ,
            {
                "ENV": "production",
                "JWT_SECRET": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            },
        ):
            settings = Settings()
            assert settings.docs_enabled is False
