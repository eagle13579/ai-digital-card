"""认证API路由测试 — 注册/登录/登出/获取当前用户。"""

from __future__ import annotations

import pytest


class TestHealthCheck:
    """健康检查端点测试"""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """GET /health 应返回 200 和 status=ok"""
        resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "service" in body
        assert "version" in body

    @pytest.mark.asyncio
    async def test_health_endpoint_via_api_v1(self, client):
        """GET /api/v1/health 应被重写为 /health 并返回 200"""
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"


class TestRegister:
    """注册端点测试"""

    @pytest.mark.asyncio
    async def test_register_success(self, client, test_db):
        """注册新用户应返回 access_token"""
        payload = {
            "phone": "13800138001",
            "password": "TestPass123!",
            "name": "注册测试用户",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 200, f"注册失败: {resp.text}"
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["phone"] == "13800138001"

    @pytest.mark.asyncio
    async def test_register_duplicate_phone(self, client, test_db, test_user):
        """重复手机号注册应返回 400"""
        payload = {
            "phone": "13800000001",  # test_user 的手机号
            "password": "TestPass123!",
            "name": "重复注册",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400
        assert "已注册" in resp.text

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client, test_db):
        """弱密码注册应返回 400"""
        payload = {
            "phone": "13800138002",
            "password": "weak",  # 太短，无大写字母和特殊字符
            "name": "弱密码测试",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400


class TestLogin:
    """登录端点测试"""

    @pytest.mark.asyncio
    async def test_login_success(self, client, test_db, test_user):
        """正确手机号和密码应返回 access_token"""
        payload = {"phone": "13800000001", "password": "testpass123"}
        resp = await client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 200, f"登录失败: {resp.text}"
        body = resp.json()
        assert "access_token" in body
        assert body["user"]["phone"] == "13800000001"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_db, test_user):
        """错误密码应返回 401"""
        payload = {"phone": "13800000001", "password": "wrongpassword"}
        resp = await client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client, test_db):
        """不存在的手机号应返回 401"""
        payload = {"phone": "13900000000", "password": "testpass123"}
        resp = await client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 401


class TestMe:
    """获取当前用户端点测试"""

    @pytest.mark.asyncio
    async def test_get_current_user(self, client, test_db, test_user, auth_headers):
        """携带有效 token 获取当前用户应返回用户信息"""
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200, f"获取用户信息失败: {resp.text}"
        body = resp.json()
        assert body["phone"] == "13800000001"
        assert body["name"] == "测试用户"

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client):
        """未携带 token 应返回 401"""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client):
        """无效 token 应返回 401"""
        headers = {"Authorization": "Bearer invalidtoken123"}
        resp = await client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 401


class TestLogout:
    """登出端点测试"""

    @pytest.mark.asyncio
    async def test_logout(self, client, test_db, test_user, auth_headers):
        """已登录用户登出应返回成功"""
        resp = await client.post("/api/v1/auth/logout", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

    @pytest.mark.asyncio
    async def test_logout_no_auth(self, client):
        """未登录用户登出应返回 401"""
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 401
