"""Salesforce CRM 集成测试 — 8+ 测试用例覆盖认证/创建/更新/同步/错误处理。

测试策略:
  1. SalesforceProvider (async class) — httpx.AsyncClient 被 mock，验证 CRMProvider 接口
  2. 独立同步函数 — requests 被 mock，验证 get_access_token / test_connection / export_contact
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from typing import Any

from app.services.crm_salesforce import (
    SalesforceProvider,
    get_access_token,
    test_connection as sync_test_connection,
    export_contact as sync_export_contact,
    SF_LOGIN_URL,
    SF_API_VERSION,
)


# ══════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def provider() -> SalesforceProvider:
    """预配置的 SalesforceProvider 实例（含有效 Token）。"""
    p = SalesforceProvider()
    p.configure({
        "instance_url": "https://na1.salesforce.com",
        "access_token": "test_access_token_123",
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "username": "test@example.com",
        "password": "testpass123",
    })
    return p


@pytest.fixture
def sample_contact() -> dict[str, Any]:
    """标准联系人数据样本。"""
    return {
        "name": "张三",
        "email": "zhangsan@example.com",
        "phone": "13800138000",
        "company": "示例公司",
        "title": "技术总监",
        "source": "API",
    }


# ══════════════════════════════════════════════════════════════════════════
# SalesforceProvider (async class) — 单元测试
# ══════════════════════════════════════════════════════════════════════════


class TestSalesforceProvider:
    """SalesforceProvider async class 测试。"""

    # ── test_connection ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_connection_success(self, provider: SalesforceProvider):
        """test_connection 在 API 返回 200 时应返回 True。"""
        mock_resp = AsyncMock()
        mock_resp.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            result = await provider.test_connection()
            assert result is True

            # 验证请求 URL 正确
            expected_url = "https://na1.salesforce.com/services/data/v58.0/sobjects/Contact/describe"
            mock_client.get.assert_called_once_with(expected_url, headers=ANY)

    @pytest.mark.asyncio
    async def test_connection_failure(self, provider: SalesforceProvider):
        """test_connection 在 API 返回非 200 时应返回 False。"""
        mock_resp = AsyncMock()
        mock_resp.status_code = 401

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            result = await provider.test_connection()
            assert result is False

    @pytest.mark.asyncio
    async def test_connection_exception_returns_false(self, provider: SalesforceProvider):
        """test_connection 在请求异常时应返回 False 而非抛出异常。"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = ConnectionError("无法连接")
            mock_client_cls.return_value = mock_client

            result = await provider.test_connection()
            assert result is False

    # ── export_contact — 新建联系人 ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_export_contact_create_new(
        self, provider: SalesforceProvider, sample_contact: dict[str, Any]
    ):
        """export_contact 当 Email 不存在时应创建新联系人。"""
        # mock _find_by_email 返回 None（未找到）
        # mock _create 返回成功结果
        with (
            patch.object(provider, "_find_by_email", new_callable=AsyncMock) as mock_find,
            patch.object(provider, "_create", new_callable=AsyncMock) as mock_create,
        ):
            mock_find.return_value = None
            mock_create.return_value = {"id": "003XX0000000001", "provider": "salesforce"}

            result = await provider.export_contact(sample_contact)

            assert result == {"id": "003XX0000000001", "provider": "salesforce"}
            mock_find.assert_called_once_with("zhangsan@example.com")
            mock_create.assert_called_once()

            # 验证传给 _create 的字段映射正确
            created_fields = mock_create.call_args[0][0]
            assert created_fields["FirstName"] == "张三"
            assert created_fields["LastName"] == "张三"  # 无空格，全名作为 LastName
            assert created_fields["Email"] == "zhangsan@example.com"
            assert created_fields["Phone"] == "13800138000"

    # ── export_contact — 更新已有联系人 ──────────────────────────────

    @pytest.mark.asyncio
    async def test_export_contact_update_existing(
        self, provider: SalesforceProvider, sample_contact: dict[str, Any]
    ):
        """export_contact 当 Email 已存在时应更新联系人。"""
        existing = {"Id": "003XX0000000001", "FirstName": "张", "LastName": "三", "Email": "zhangsan@example.com"}

        with (
            patch.object(provider, "_find_by_email", new_callable=AsyncMock) as mock_find,
            patch.object(provider, "_update", new_callable=AsyncMock) as mock_update,
        ):
            mock_find.return_value = existing
            mock_update.return_value = {"id": "003XX0000000001", "provider": "salesforce", "updated": True}

            result = await provider.export_contact(sample_contact)

            assert result["updated"] is True
            assert result["id"] == "003XX0000000001"
            mock_find.assert_called_once_with("zhangsan@example.com")
            mock_update.assert_called_once_with("003XX0000000001", ANY)

    # ── update_contact ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_update_contact_direct(
        self, provider: SalesforceProvider, sample_contact: dict[str, Any]
    ):
        """update_contact 应直接更新指定 ID 的联系人。"""
        contact_id = "003XX0000000001"

        with patch.object(provider, "_update", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = {"id": contact_id, "provider": "salesforce", "updated": True}

            result = await provider.update_contact(contact_id, sample_contact)

            assert result["updated"] is True
            mock_update.assert_called_once_with(contact_id, ANY)

    # ── delete_contact ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_delete_contact_success(self, provider: SalesforceProvider):
        """delete_contact 在 API 返回 204 时应返回 True。"""
        mock_resp = AsyncMock()
        mock_resp.status_code = 204

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.delete.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            result = await provider.delete_contact("003XX0000000001")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_contact_failure(self, provider: SalesforceProvider):
        """delete_contact 在 API 返回非 204 时应返回 False。"""
        mock_resp = AsyncMock()
        mock_resp.status_code = 404

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.delete.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            result = await provider.delete_contact("003XX0000009999")
            assert result is False

    # ── get_contact ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_contact_found(self, provider: SalesforceProvider):
        """get_contact 在联系人存在时应返回映射后的数据。"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "Id": "003XX0000000001",
            "FirstName": "张",
            "LastName": "三",
            "Email": "zhangsan@example.com",
            "Phone": "13800138000",
            "Title": "技术总监",
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            result = await provider.get_contact("003XX0000000001")
            assert result is not None
            assert result["name"] == "张 三"
            assert result["email"] == "zhangsan@example.com"
            assert result["phone"] == "13800138000"
            assert result["source"] == "salesforce"

    @pytest.mark.asyncio
    async def test_get_contact_not_found(self, provider: SalesforceProvider):
        """get_contact 在联系人不存在时应返回 None。"""
        mock_resp = AsyncMock()
        mock_resp.status_code = 404

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            result = await provider.get_contact("003XX0000009999")
            assert result is None

    # ── _find_by_email ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_find_by_email_found(self, provider: SalesforceProvider):
        """_find_by_email 在找到匹配联系人时应返回记录。"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "totalSize": 1,
            "records": [{"Id": "003XX0000000001", "FirstName": "张", "LastName": "三", "Email": "zhangsan@example.com"}],
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            result = await provider._find_by_email("zhangsan@example.com")
            assert result is not None
            assert result["Id"] == "003XX0000000001"

    @pytest.mark.asyncio
    async def test_find_by_email_not_found(self, provider: SalesforceProvider):
        """_find_by_email 在无匹配联系人时应返回 None。"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"totalSize": 0, "records": []}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            result = await provider._find_by_email("nonexistent@example.com")
            assert result is None

    # ── _map_contact_data ────────────────────────────────────────────

    def test_map_contact_data_with_name_parts(self, provider: SalesforceProvider):
        """_map_contact_data 应将姓名按空格拆分为 FirstName/LastName。"""
        result = provider._map_contact_data({
            "name": "张 三",
            "email": "zs@example.com",
            "phone": "13800000000",
            "title": "CTO",
            "company_id": "001XX0000000001",
            "source": "API",
        })
        assert result["FirstName"] == "张"
        assert result["LastName"] == "三"
        assert result["LeadSource"] == "API"

    def test_map_contact_data_single_name(self, provider: SalesforceProvider):
        """_map_contact_data 在姓名为单字时应将全名作为 LastName。"""
        result = provider._map_contact_data({
            "name": "单名",
            "email": "danming@example.com",
        })
        # 无空格，整个 name 作为 LastName
        assert result.get("FirstName") == "单名"
        assert result.get("LastName") == "单名"

    # ── provider name ────────────────────────────────────────────────

    def test_get_provider_name(self, provider: SalesforceProvider):
        """get_provider_name 应返回 'salesforce'。"""
        assert provider.get_provider_name() == "salesforce"

    # ── 错误处理 — HTTP 错误 ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_export_contact_http_error(
        self, provider: SalesforceProvider, sample_contact: dict[str, Any]
    ):
        """export_contact 在 Salesforce API 返回错误时应传播异常。"""
        with (
            patch.object(provider, "_find_by_email", new_callable=AsyncMock) as mock_find,
            patch.object(provider, "_create", new_callable=AsyncMock) as mock_create,
        ):
            mock_find.return_value = None
            mock_create.side_effect = Exception("Salesforce API 400: Bad Request")

            with pytest.raises(Exception, match="Bad Request"):
                await provider.export_contact(sample_contact)

    @pytest.mark.asyncio
    async def test_export_contact_no_email_still_works(
        self, provider: SalesforceProvider
    ):
        """export_contact 在无 Email 时应跳过查重直接创建。"""
        contact_no_email = {"name": "李四", "phone": "13900000000"}

        with (
            patch.object(provider, "_find_by_email", new_callable=AsyncMock) as mock_find,
            patch.object(provider, "_create", new_callable=AsyncMock) as mock_create,
        ):
            mock_create.return_value = {"id": "003XX0000000002", "provider": "salesforce"}

            result = await provider.export_contact(contact_no_email)
            assert result["id"] == "003XX0000000002"
            # 无 Email 时不应调用 _find_by_email
            mock_find.assert_not_called()


# ══════════════════════════════════════════════════════════════════════════
# 独立同步函数 — 单元测试
# ══════════════════════════════════════════════════════════════════════════


class TestSyncGetAccessToken:
    """get_access_token 同步函数测试。"""

    def test_get_access_token_success(self):
        """有效的用户名密码应成功获取 Token。"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "00DXX0000000001!ARfAQ...",
            "instance_url": "https://na1.salesforce.com",
            "token_type": "Bearer",
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = get_access_token(
                client_id="test_client",
                client_secret="test_secret",
                username="user@example.com",
                password="pass123",
            )

            assert result["success"] is True
            assert result["access_token"] == "00DXX0000000001!ARfAQ..."
            assert result["instance_url"] == "https://na1.salesforce.com"

            # 验证请求参数
            mock_post.assert_called_once_with(
                SF_LOGIN_URL,
                data={
                    "grant_type": "password",
                    "client_id": "test_client",
                    "client_secret": "test_secret",
                    "username": "user@example.com",
                    "password": "pass123",
                },
                timeout=10,
            )

    def test_get_access_token_invalid_credentials(self):
        """无效的用户名密码应返回错误信息。"""
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {
            "error": "invalid_grant",
            "error_description": "authentication failure",
        }

        with patch("requests.post", return_value=mock_resp):
            result = get_access_token(
                client_id="bad_client",
                client_secret="bad_secret",
                username="bad@user.com",
                password="wrong",
            )

            assert result["success"] is False
            assert "认证失败" in result["error"]

    def test_get_access_token_timeout(self):
        """请求超时应返回友好的错误信息。"""
        import requests

        with patch("requests.post", side_effect=requests.exceptions.Timeout("Connection timed out")):
            result = get_access_token(
                client_id="x", client_secret="x", username="x", password="x"
            )
            assert result["success"] is False
            assert "超时" in result["error"]

    def test_get_access_token_connection_error(self):
        """网络连接错误应返回友好的错误信息。"""
        import requests

        with patch("requests.post", side_effect=requests.exceptions.ConnectionError("DNS lookup failed")):
            result = get_access_token(
                client_id="x", client_secret="x", username="x", password="x"
            )
            assert result["success"] is False
            assert "无法连接" in result["error"]


class TestSyncTestConnection:
    """test_connection 同步函数测试。"""

    def test_sync_test_connection_success(self):
        """有效的 Token 和实例 URL 应返回连接成功。"""
        config = {
            "access_token": "00DXX0000000001!ARfAQ...",
            "instance_url": "https://na1.salesforce.com",
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("requests.get", return_value=mock_resp) as mock_get:
            result = sync_test_connection(config)

            assert result["connected"] is True
            assert result["message"] == "Salesforce 连接成功"

            expected_url = "https://na1.salesforce.com/services/data/v58.0/sobjects/Contact/describe"
            mock_get.assert_called_once_with(expected_url, headers=ANY, timeout=10)

    def test_sync_test_connection_auto_token(self):
        """未提供 Token 时应自动通过 Username-Password Flow 获取。"""
        config = {
            "client_id": "test_client",
            "client_secret": "test_secret",
            "username": "user@example.com",
            "password": "pass123",
        }

        token_resp = MagicMock()
        token_resp.status_code = 200
        token_resp.json.return_value = {
            "access_token": "00DXX0000000001!ARfAQ...",
            "instance_url": "https://na1.salesforce.com",
        }

        describe_resp = MagicMock()
        describe_resp.status_code = 200

        with (
            patch("requests.post", return_value=token_resp) as mock_post,
            patch("requests.get", return_value=describe_resp) as mock_get,
        ):
            result = sync_test_connection(config)

            assert result["connected"] is True
            mock_post.assert_called_once()
            mock_get.assert_called_once()

    def test_sync_test_connection_token_failure(self):
        """自动获取 Token 失败时应返回错误。"""
        config = {
            "client_id": "bad_client",
            "client_secret": "bad_secret",
            "username": "bad@user.com",
            "password": "wrong",
        }

        token_resp = MagicMock()
        token_resp.status_code = 400
        token_resp.json.return_value = {"error": "invalid_grant", "error_description": "authentication failure"}

        with patch("requests.post", return_value=token_resp):
            result = sync_test_connection(config)

            assert result["connected"] is False
            assert "认证失败" in result["message"]

    def test_sync_test_connection_missing_instance_url(self):
        """缺少 instance_url 时应返回错误。"""
        config = {"access_token": "some_token"}  # 没有 instance_url

        result = sync_test_connection(config)
        assert result["connected"] is False
        assert "缺少 instance_url" in result["message"]

    def test_sync_test_connection_unauthorized(self):
        """Token 无效应返回 401 错误。"""
        config = {
            "access_token": "expired_token",
            "instance_url": "https://na1.salesforce.com",
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 401

        with patch("requests.get", return_value=mock_resp):
            result = sync_test_connection(config)
            assert result["connected"] is False
            assert "无效或已过期" in result["message"]


class TestSyncExportContact:
    """export_contact 同步函数测试。"""

    def test_sync_export_create_new_contact(self):
        """export_contact 应创建新联系人（Email 不存在时）。"""
        config = {
            "access_token": "test_token",
            "instance_url": "https://na1.salesforce.com",
        }
        contact_data = {
            "name": "张三",
            "email": "zhangsan@example.com",
            "phone": "13800138000",
        }

        # mock SOQL 查询返回空（不存在）
        query_resp = MagicMock()
        query_resp.status_code = 200
        query_resp.json.return_value = {"totalSize": 0, "records": []}

        # mock POST 创建成功
        create_resp = MagicMock()
        create_resp.status_code = 201
        create_resp.json.return_value = {"id": "003XX0000000001", "success": True}

        with patch("requests.get", return_value=query_resp) as mock_get:
            with patch("requests.post", return_value=create_resp) as mock_post:
                result = sync_export_contact(config, contact_data)

                assert result["success"] is True
                assert result["contact_id"] == "003XX0000000001"
                mock_get.assert_called_once()  # SOQL 查询
                mock_post.assert_called_once()  # 创建 Contact

    def test_sync_export_update_existing_contact(self):
        """export_contact 应更新已有联系人（Email 已存在时）。"""
        config = {
            "access_token": "test_token",
            "instance_url": "https://na1.salesforce.com",
        }
        contact_data = {
            "name": "张三",
            "email": "zhangsan@example.com",
            "phone": "13900000000",  # 更新电话号码
        }

        # mock SOQL 查询返回已有记录
        query_resp = MagicMock()
        query_resp.status_code = 200
        query_resp.json.return_value = {
            "totalSize": 1,
            "records": [{"Id": "003XX0000000001"}],
        }

        # mock PATCH 更新成功
        update_resp = MagicMock()
        update_resp.status_code = 204

        with (
            patch("requests.get", return_value=query_resp),
            patch("requests.patch", return_value=update_resp) as mock_patch,
        ):
            result = sync_export_contact(config, contact_data)

            assert result["success"] is True
            assert result["contact_id"] == "003XX0000000001"
            mock_patch.assert_called_once()

    def test_sync_export_timeout_error(self):
        """export_contact 在请求超时应返回错误信息。"""
        from urllib.parse import quote
        import requests

        config = {
            "access_token": "test_token",
            "instance_url": "https://na1.salesforce.com",
        }
        contact_data = {"name": "李四", "email": "lisi@example.com"}

        with patch("requests.get", side_effect=requests.exceptions.Timeout("timeout")):
            result = sync_export_contact(config, contact_data)
            assert result["success"] is False
            assert "超时" in result["error"]

    def test_sync_export_connection_error(self):
        """export_contact 在网络错误时应返回错误信息。"""
        from urllib.parse import quote
        import requests

        config = {
            "access_token": "test_token",
            "instance_url": "https://na1.salesforce.com",
        }
        contact_data = {"name": "王五", "email": "wangwu@example.com"}

        with patch("requests.get", side_effect=requests.exceptions.ConnectionError("connection refused")):
            result = sync_export_contact(config, contact_data)
            assert result["success"] is False
            assert "无法连接" in result["error"]

    def test_sync_export_create_failure_reported(self):
        """export_contact 在 Salesforce 返回创建失败时应报告错误。"""
        config = {
            "access_token": "test_token",
            "instance_url": "https://na1.salesforce.com",
        }
        contact_data = {"name": "测试", "email": "test@example.com"}

        query_resp = MagicMock()
        query_resp.status_code = 200
        query_resp.json.return_value = {"totalSize": 0, "records": []}

        # POST 返回错误
        create_resp = MagicMock()
        create_resp.status_code = 400
        create_resp.text = '[{"message":"Required field missing: LastName","errorCode":"REQUIRED_FIELD_MISSING"}]'

        with (
            patch("requests.get", return_value=query_resp),
            patch("requests.post", return_value=create_resp),
        ):
            result = sync_export_contact(config, contact_data)
            assert result["success"] is False
            assert "创建联系人失败" in result["error"]

    def test_sync_export_auto_token_flow(self):
        """export_contact 未提供 Token 时应自动获取。"""
        config = {
            "client_id": "test_client",
            "client_secret": "test_secret",
            "username": "user@example.com",
            "password": "pass123",
        }
        contact_data = {"name": "自动 Token", "email": "auto@example.com"}

        # Token 响应
        token_resp = MagicMock()
        token_resp.status_code = 200
        token_resp.json.return_value = {
            "access_token": "auto_generated_token",
            "instance_url": "https://na1.salesforce.com",
        }

        # SOQL 查询（空结果）
        query_resp = MagicMock()
        query_resp.status_code = 200
        query_resp.json.return_value = {"totalSize": 0, "records": []}

        # 创建成功
        create_resp = MagicMock()
        create_resp.status_code = 201
        create_resp.json.return_value = {"id": "003XX0000000003", "success": True}

        # 使用 side_effect 区分调用:
        # 第1次 post → token_resp (SF_LOGIN_URL)
        # 第2次 get  → query_resp (SOQL)
        # 第3次 post → create_resp (sobjects/Contact)
        def post_side_effect(url, **kwargs):
            if "login.salesforce.com" in str(url):
                return token_resp
            return create_resp

        with (
            patch("requests.post", side_effect=post_side_effect) as mock_post,
            patch("requests.get", return_value=query_resp) as mock_get,
        ):
            result = sync_export_contact(config, contact_data)
            assert result["success"] is True
            assert result["contact_id"] == "003XX0000000003"
