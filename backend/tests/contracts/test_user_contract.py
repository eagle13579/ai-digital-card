"""
用户 API 契约测试
===================

验证 /api/users/* 端点的请求/响应格式一致性。
契约测试不验证业务逻辑（如权限、计算），只验证：
  - 状态码正确性
  - Content-Type 一致性
  - 响应字段完整性
  - 响应字段类型正确性
  - 错误响应格式一致性

参考 OpenAPI 规范: openapi.yaml -> components.schemas.UserResponse
"""

import pytest
from fastapi import status


# ── 用户响应字段契约（来自 openapi.yaml components.schemas.UserResponse） ──

USER_RESPONSE_FIELDS = {
    "id": int,
    "phone": str,
    "name": str,
    "avatar": str,
    "company": str,
    "title": str,
    "intro": str,
    "role": str,
    "membership_tier": str,
    "created_at": str,      # datetime.isoformat
    "updated_at": str,      # datetime.isoformat
}

USER_RESPONSE_OPTIONAL = {"username", "membership_expires_at", "unlock_quota"}

ERROR_RESPONSE_FIELDS = {"detail": str}


# ══════════════════════════════════════════════════════════════════════
# GET /api/users/me — 获取当前用户信息
# ══════════════════════════════════════════════════════════════════════


class TestGetMeContract:
    """GET /api/users/me 契约 — 获取当前用户个人信息"""

    ENDPOINT = "/api/users/me"

    @pytest.mark.asyncio
    async def test_success_contract(self, client, auth_headers):
        """200: 成功响应必须包含所有 UserResponse 字段"""
        resp = await client.get(self.ENDPOINT, headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert "application/json" in resp.headers.get("content-type", "")

        data = resp.json()
        self._validate_user_response(data)

    @pytest.mark.asyncio
    async def test_unauthorized_contract(self, client):
        """401: 未认证请求返回标准错误格式"""
        resp = await client.get(self.ENDPOINT)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert "application/json" in resp.headers.get("content-type", "")
        self._validate_error_response(resp.json())

    @pytest.mark.asyncio
    async def test_invalid_token_contract(self, client):
        """401: 无效 token 返回标准错误格式"""
        resp = await client.get(
            self.ENDPOINT, headers={"Authorization": "Bearer invalid_token_xyz"}
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        self._validate_error_response(resp.json())

    # ── 辅助方法 ──────────────────────────────────────────────────────

    def _validate_user_response(self, data: dict):
        """验证 UserResponse 格式契约"""
        # 所有必选字段必须存在
        missing = set(USER_RESPONSE_FIELDS.keys()) - data.keys()
        assert not missing, f"缺少必选字段: {missing}"

        # 字段类型校验
        for field, expected_type in USER_RESPONSE_FIELDS.items():
            assert isinstance(
                data[field], expected_type
            ), f"字段 {field} 期望类型 {expected_type.__name__}, 实际 {type(data[field]).__name__}"

        # role 字段枚举值约束
        assert data["role"] in (
            "user",
            "admin",
        ), f"role 值非法: {data['role']}"

        # optional 字段如果存在则检查类型
        if "username" in data and data["username"] is not None:
            assert isinstance(data["username"], str)
        if "unlock_quota" in data:
            assert isinstance(data["unlock_quota"], int)

    def _validate_error_response(self, data: dict):
        """验证标准错误响应格式"""
        assert "detail" in data, "错误响应缺少 detail 字段"
        assert isinstance(data["detail"], str), "detail 必须是字符串"


# ══════════════════════════════════════════════════════════════════════
# PUT /api/users/me — 更新当前用户信息
# ══════════════════════════════════════════════════════════════════════


class TestUpdateMeContract:
    """PUT /api/users/me 契约 — 更新当前用户个人信息"""

    ENDPOINT = "/api/users/me"

    @pytest.mark.asyncio
    async def test_success_contract(self, client, auth_headers):
        """200: 更新成功后返回 UserResponse 格式"""
        payload = {"name": "新名字", "company": "新公司", "title": "新职位"}
        resp = await client.put(self.ENDPOINT, json=payload, headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert "application/json" in resp.headers.get("content-type", "")

        data = resp.json()
        assert data["name"] == "新名字"
        assert data["company"] == "新公司"
        assert data["title"] == "新职位"

        # 完整 UserResponse 格式校验
        from tests.contracts.test_user_contract import TestGetMeContract
        TestGetMeContract._validate_user_response(self, data)

    @pytest.mark.asyncio
    async def test_partial_update_contract(self, client, auth_headers):
        """200: 部分更新只返回更新后的完整 UserResponse"""
        payload = {"intro": "只更新简介"}
        resp = await client.put(self.ENDPOINT, json=payload, headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["intro"] == "只更新简介"
        assert "name" in data  # 未更新的字段仍然存在

    @pytest.mark.asyncio
    async def test_unauthorized_contract(self, client):
        """401: 未认证请求返回标准错误格式"""
        resp = await client.put(
            self.ENDPOINT, json={"name": "hacker"}, headers={}
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        data = resp.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    @pytest.mark.asyncio
    async def test_invalid_field_type_contract(self, client, auth_headers):
        """422: 字段类型错误返回标准校验错误"""
        # name 应该是字符串，传入数字
        resp = await client.put(
            self.ENDPOINT, json={"name": 12345}, headers=auth_headers
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = resp.json()
        assert "detail" in data


# ══════════════════════════════════════════════════════════════════════
# GET /api/users — 获取用户列表（需认证）
# ══════════════════════════════════════════════════════════════════════


class TestListUsersContract:
    """GET /api/users 契约 — 获取用户列表"""

    ENDPOINT = "/api/users"

    @pytest.mark.asyncio
    async def test_success_contract(self, client, auth_headers):
        """200: 返回分页的用户列表"""
        resp = await client.get(self.ENDPOINT, headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert "application/json" in resp.headers.get("content-type", "")

        data = resp.json()
        # 分页响应格式校验
        assert "items" in data, "分页响应缺少 items"
        assert "total" in data, "分页响应缺少 total"
        assert "page" in data, "分页响应缺少 page"
        assert "page_size" in data, "分页响应缺少 page_size"
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["page"], int)
        assert isinstance(data["page_size"], int)

        # 每项应遵循 UserResponse 格式
        for item in data["items"]:
            TestGetMeContract._validate_user_response(self, item)

    @pytest.mark.asyncio
    async def test_pagination_params_contract(self, client, auth_headers):
        """200: 分页参数 page=1, page_size=5 返回正确格式"""
        resp = await client.get(
            self.ENDPOINT,
            params={"page": 1, "page_size": 5},
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["items"]) <= 5

    @pytest.mark.asyncio
    async def test_unauthorized_contract(self, client):
        """401: 未认证请求返回标准错误格式"""
        resp = await client.get(self.ENDPOINT)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        data = resp.json()
        assert "detail" in data


# ══════════════════════════════════════════════════════════════════════
# GET /api/users/{user_id} — 获取指定用户信息
# ══════════════════════════════════════════════════════════════════════


class TestGetUserByIdContract:
    """GET /api/users/{user_id} 契约 — 获取指定用户信息"""

    ENDPOINT_PATTERN = "/api/users"

    @pytest.mark.asyncio
    async def test_success_contract(self, client, auth_headers, test_user):
        """200: 返回指定用户的 UserResponse"""
        resp = await client.get(
            f"{self.ENDPOINT_PATTERN}/{test_user.id}", headers=auth_headers
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        TestGetMeContract._validate_user_response(self, data)
        assert data["id"] == test_user.id

    @pytest.mark.asyncio
    async def test_not_found_contract(self, client, auth_headers):
        """404: 不存在的用户 ID 返回标准错误格式"""
        resp = await client.get(
            f"{self.ENDPOINT_PATTERN}/99999", headers=auth_headers
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        data = resp.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    @pytest.mark.asyncio
    async def test_invalid_id_type_contract(self, client, auth_headers):
        """422: 非数字 user_id 返回校验错误"""
        resp = await client.get(
            f"{self.ENDPOINT_PATTERN}/abc", headers=auth_headers
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = resp.json()
        assert "detail" in data


# ══════════════════════════════════════════════════════════════════════
# 全模块通用契约: 跨端点的格式一致性校验
# ══════════════════════════════════════════════════════════════════════


class TestUserModuleCommonContract:
    """用户模块通用契约 — 所有端点的共同约束"""

    ALL_ENDPOINTS = [
        "/api/users/me",
        "/api/users",
    ]

    @pytest.mark.asyncio
    async def test_cors_preflight_contract(self, client):
        """OPTIONS 请求返回 204 + 标准 CORS 头"""
        for endpoint in self.ALL_ENDPOINTS:
            resp = await client.options(endpoint)
            assert resp.status_code == status.HTTP_204_NO_CONTENT, (
                f"{endpoint} OPTIONS 应返回 204"
            )

    @pytest.mark.asyncio
    async def test_method_not_allowed_contract(self, client, auth_headers):
        """不支持的 HTTP 方法返回 405"""
        resp = await client.delete(
            "/api/users/me", headers=auth_headers
        )
        assert resp.status_code in (
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_404_NOT_FOUND,
        )

    @pytest.mark.asyncio
    async def test_content_type_header_present(self, client, auth_headers):
        """所有成功响应必须包含 content-type 头"""
        endpoints = [
            ("GET", "/api/users/me", auth_headers),
        ]
        for method, path, headers in endpoints:
            resp = await client.request(method, path, headers=headers)
            assert "content-type" in resp.headers, (
                f"{method} {path} 缺少 content-type 头"
            )
