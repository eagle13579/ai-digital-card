"""JWT 令牌 & 认证路由测试 — 令牌生成/验证/过期/白名单"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from unittest import mock

import pytest
from jose import jwt, JWTError


# ═══════════════════════════════════════════════════════════════════
# JWT 令牌生成 & 验证（直接单元测试 auth_jwt 模块）
# ═══════════════════════════════════════════════════════════════════


class TestJWTTokens:
    """JWT token 生成和验证核心逻辑"""

    def test_create_access_token_returns_string(self):
        """签发 JWT token 应返回字符串"""
        from app.auth_jwt import create_access_token

        token = create_access_token({"sub": "42"})
        assert isinstance(token, str)
        assert len(token) > 20
        # JWT 格式: header.payload.signature
        assert token.count(".") == 2

    def test_decode_valid_token_returns_payload(self):
        """解码自己签发的 token 应返回原始 payload"""
        from app.auth_jwt import create_access_token, decode_access_token

        token = create_access_token({"sub": "42", "role": "user"})
        payload = decode_access_token(token)
        assert payload["sub"] == "42"
        assert payload["role"] == "user"
        assert "exp" in payload

    def test_decode_expired_token_raises(self):
        """过期的 token 应抛出 JWTError"""
        from app.config import settings
        from app.auth_jwt import decode_access_token

        # 直接签发一个已过期的 token（设置 exp 为过去）
        expired_payload = {
            "sub": "42",
            "exp": datetime.utcnow() - timedelta(hours=1),
        }
        token = jwt.encode(expired_payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)

        with pytest.raises(JWTError):
            decode_access_token(token)

    def test_decode_invalid_signature_raises(self):
        """使用错误密钥签发的 token 应抛出 JWTError"""
        from app.auth_jwt import decode_access_token
        from app.config import settings

        # 用不同的密钥签发
        wrong_token = jwt.encode(
            {"sub": "42", "exp": datetime.utcnow() + timedelta(hours=1)},
            "wrong-secret-key-that-does-not-match",
            algorithm="HS256",
        )

        with pytest.raises(JWTError):
            decode_access_token(wrong_token)

    def test_decode_malformed_token_raises(self):
        """格式错误的 token 应抛出 JWTError"""
        from app.auth_jwt import decode_access_token

        with pytest.raises(JWTError):
            decode_access_token("not-a-jwt-token")

    def test_token_contains_exp_claim(self):
        """JWT token 应包含 exp 过期时间"""
        from app.auth_jwt import create_access_token, decode_access_token

        token = create_access_token({"sub": "1"})
        payload = decode_access_token(token)
        assert "exp" in payload
        assert isinstance(payload["exp"], int)


# ═══════════════════════════════════════════════════════════════════
# 认证路由集成测试（使用 TestClient / httpx.AsyncClient）
# ═══════════════════════════════════════════════════════════════════


class TestAuthAPI:
    """认证 API 端点集成测试"""

    @pytest.mark.asyncio
    async def test_register_success(self, client, test_db):
        """注册新用户返回 200 + access_token"""
        payload = {
            "phone": "13900139001",
            "password": "StrongPass1!",
            "name": "集成测试用户",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 200, f"注册失败: {resp.text}"
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["phone"] == "13900139001"

    @pytest.mark.asyncio
    async def test_register_duplicate(self, client, test_db, test_user):
        """重复手机号注册返回 400"""
        payload = {
            "phone": "13800000001",
            "password": "StrongPass1!",
            "name": "重复用户",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400
        assert "已注册" in resp.text

    @pytest.mark.asyncio
    async def test_login_success(self, client, test_db, test_user):
        """正确手机号+密码登录返回 200 + access_token"""
        payload = {"phone": "13800000001", "password": "testpass123"}
        resp = await client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 200, f"登录失败: {resp.text}"
        body = resp.json()
        assert "access_token" in body
        assert body["user"]["phone"] == "13800000001"

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client, test_db, test_user):
        """错误密码登录返回 401"""
        payload = {"phone": "13800000001", "password": "wrongpass123"}
        resp = await client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_returns_401(self, client, test_db):
        """不存在的手机号登录返回 401"""
        payload = {"phone": "19900000000", "password": "testpass123"}
        resp = await client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_access_protected_route_without_token_returns_401(self, client):
        """未携带 token 访问受保护路由返回 401"""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_access_protected_route_with_invalid_token_returns_401(self, client):
        """无效 token 访问受保护路由返回 401"""
        headers = {"Authorization": "Bearer invalidtoken123"}
        resp = await client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_access_protected_route_with_valid_token(self, client, test_db, test_user, auth_headers):
        """有效 token 访问 /me 返回用户信息"""
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200, f"获取用户信息失败: {resp.text}"
        body = resp.json()
        assert body["phone"] == "13800000001"
        assert body["name"] == "测试用户"

    @pytest.mark.asyncio
    async def test_logout_success(self, client, test_db, test_user, auth_headers):
        """已登录用户登出返回成功"""
        resp = await client.post("/api/v1/auth/logout", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

    @pytest.mark.asyncio
    async def test_logout_without_auth_returns_401(self, client):
        """未登录用户登出返回 401"""
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_flow(self, client, test_db, test_user):
        """登录后获取 token → 再次使用正常（模拟 token 刷新场景）"""
        # 先登录
        payload = {"phone": "13800000001", "password": "testpass123"}
        login_resp = await client.post("/api/v1/auth/login", json=payload)
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 用 token 访问 me
        me_resp = await client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["phone"] == "13800000001"

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(self, client, test_db, test_user):
        """使用过期 token 访问受保护路由应返回 401"""
        from app.auth_jwt import create_access_token, decode_access_token
        from jose import JWTError

        # 签发一个立即过期的 token（通过 mock 时间）
        # 方式：创建 token 后等待 exp 过期
        # 更可靠：手动构造一个 exp 为过去的 token
        from app.config import settings
        import time

        expired_payload = {
            "sub": str(test_user.id),
            "exp": int(time.time()) - 3600,  # 1小时前过期
        }
        expired_token = jwt.encode(
            expired_payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        resp = await client.get("/api/v1/auth/me", headers=headers)

        # FastAPI 内部通过 decode_access_token 验证，应返回 401
        assert resp.status_code == 401
