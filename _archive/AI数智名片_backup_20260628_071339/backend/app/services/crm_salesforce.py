"""Salesforce CRM API 集成 — 基于 Salesforce REST API (sobjects/Contact)。

提供两种使用方式:
  1. SalesforceProvider (async class) — 与 CRMBridge 框架集成
  2. get_access_token / test_connection / export_contact (sync functions) — 独立快速调用
"""
import logging
from typing import Any

import httpx
import requests

from app.services.crm_bridge import CRMProvider

logger = logging.getLogger("crm_salesforce")

# ── Salesforce REST API 常量 ─────────────────────────────────────────────
SF_LOGIN_URL = "https://login.salesforce.com/services/oauth2/token"
SF_API_VERSION = "v58.0"
REQUEST_TIMEOUT = 10  # 超时秒数


class SalesforceProvider(CRMProvider):
    """Salesforce CRM 集成实现（OAuth 2.0 Username-Password / JWT Bearer Token）。"""

    def __init__(
        self,
        instance_url: str = "",
        access_token: str = "",
    ) -> None:
        self._instance_url = instance_url.rstrip("/")
        self._access_token = access_token

    # ── 配置 ──────────────────────────────────────────────────────────────

    def configure(self, config: dict[str, Any]) -> None:
        """从字典加载配置。"""
        self._instance_url = config.get("instance_url", "").rstrip("/")
        self._access_token = config.get("access_token", "")
        # 如果是 Password flow，缓存 client 用于自动刷新
        self._client_id = config.get("client_id", "")
        self._client_secret = config.get("client_secret", "")
        self._username = config.get("username", "")
        self._password = config.get("password", "")

    def get_provider_name(self) -> str:
        return "salesforce"

    # ── HTTP 客户端 ───────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    # ── CRM 接口实现 ──────────────────────────────────────────────────────

    async def export_contact(self, contact_data: dict[str, Any]) -> dict[str, Any]:
        """创建或更新 Salesforce 联系人（通过 Email 去重）。"""
        sf_fields = self._map_contact_data(contact_data)
        email = sf_fields.get("Email", "")
        existing = await self._find_by_email(email) if email else None

        if existing:
            contact_id = existing["Id"]
            return await self._update(contact_id, sf_fields)
        else:
            return await self._create(sf_fields)

    async def update_contact(
        self, contact_id: str, contact_data: dict[str, Any]
    ) -> dict[str, Any]:
        sf_fields = self._map_contact_data(contact_data)
        return await self._update(contact_id, sf_fields)

    async def delete_contact(self, contact_id: str) -> bool:
        url = f"{self._instance_url}/services/data/v58.0/sobjects/Contact/{contact_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, headers=self._headers())
            return resp.status_code == 204

    async def get_contact(self, contact_id: str) -> dict[str, Any] | None:
        url = f"{self._instance_url}/services/data/v58.0/sobjects/Contact/{contact_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._headers())
            if resp.status_code == 200:
                return self._unmap_contact(resp.json())
            return None

    async def test_connection(self) -> bool:
        """通过查询 API 版本信息验证 Token 有效性。"""
        url = f"{self._instance_url}/services/data/v58.0/sobjects/Contact/describe"
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=self._headers())
                return resp.status_code == 200
            except Exception:
                return False

    # ── 内部方法 ──────────────────────────────────────────────────────────

    def _map_contact_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """将通用名片数据映射到 Salesforce Contact 字段。"""
        fields = {
            "FirstName": data.get("name", "").split(" ", 1)[0] if data.get("name") else "",
            "LastName": (
                data.get("name", "").split(" ", 1)[1]
                if data.get("name") and " " in data["name"]
                else data.get("name", "")
            ),
            "Email": data.get("email", ""),
            "Phone": data.get("phone", ""),
            "Title": data.get("title", ""),
            "AccountId": data.get("company_id", ""),
            "LeadSource": data.get("source", "API"),
        }
        # 公司名映射到 Account Name（简化：如果没有 AccountId 就不填）
        if not fields["AccountId"]:
            fields.pop("AccountId", None)
        return {k: v for k, v in fields.items() if v}

    def _unmap_contact(self, sf_data: dict[str, Any]) -> dict[str, Any]:
        """将 Salesforce API 响应映射回通用格式。"""
        return {
            "id": sf_data.get("Id"),
            "name": f"{sf_data.get('FirstName', '')} {sf_data.get('LastName', '')}".strip(),
            "email": sf_data.get("Email", ""),
            "phone": sf_data.get("Phone", ""),
            "title": sf_data.get("Title", ""),
            "company_id": sf_data.get("AccountId", ""),
            "source": "salesforce",
        }

    async def _create(self, fields: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._instance_url}/services/data/v58.0/sobjects/Contact"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=self._headers(), json=fields)
            resp.raise_for_status()
            data = resp.json()
            return {"id": data.get("id"), "provider": "salesforce"}

    async def _update(self, contact_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._instance_url}/services/data/v58.0/sobjects/Contact/{contact_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.patch(url, headers=self._headers(), json=fields)
            # Salesforce PATCH 返回 204 No Content
            if resp.status_code == 204:
                return {"id": contact_id, "provider": "salesforce", "updated": True}
            resp.raise_for_status()
            return {"id": contact_id, "provider": "salesforce", "updated": True}

    async def _find_by_email(self, email: str) -> dict[str, Any] | None:
        """通过 SOQL 查询按 Email 查找联系人。"""
        escaped_email = email.replace("'", "\\'")
        query = f"SELECT Id, FirstName, LastName, Email FROM Contact WHERE Email = '{escaped_email}' LIMIT 1"
        url = f"{self._instance_url}/services/data/v58.0/query?q={httpx.utils.quote(query)}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._headers())
            if resp.status_code == 200:
                records = resp.json().get("records", [])
                return records[0] if records else None
            return None


# ══════════════════════════════════════════════════════════════════════════
# 独立同步函数 — 无需类实例化，直接使用 requests 库
# 适用于简单的一键调用场景
# ══════════════════════════════════════════════════════════════════════════


def get_access_token(
    client_id: str,
    client_secret: str,
    username: str,
    password: str,
) -> dict[str, Any]:
    """通过 OAuth 2.0 Username-Password Flow 获取 Salesforce Access Token。

    Args:
        client_id: Salesforce Connected App Consumer Key
        client_secret: Salesforce Connected App Consumer Secret
        username: Salesforce 用户名
        password: Salesforce 密码（可附加 Security Token）

    Returns:
        {"access_token": "...", "instance_url": "...", "success": True}
        或 {"success": False, "error": "..."}
    """
    try:
        resp = requests.post(
            SF_LOGIN_URL,
            data={
                "grant_type": "password",
                "client_id": client_id,
                "client_secret": client_secret,
                "username": username,
                "password": password,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "success": True,
                "access_token": data.get("access_token"),
                "instance_url": data.get("instance_url"),
                "token_type": data.get("token_type", "Bearer"),
            }
        else:
            err_data = resp.json()
            return {
                "success": False,
                "error": f"Salesforce 认证失败: {err_data.get('error_description', err_data.get('error', resp.text[:200]))}",
            }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Salesforce 登录超时（10秒）"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "无法连接到 login.salesforce.com"}
    except Exception as e:
        return {"success": False, "error": f"Salesforce 登录异常: {e}"}


def _sf_headers(access_token: str) -> dict[str, str]:
    """构造 Salesforce API 请求头。"""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def test_connection(config: dict[str, Any]) -> dict[str, Any]:
    """测试 Salesforce 连接有效性（自动获取 Token 后校验）。

    Args:
        config: 包含以下键:
            - client_id, client_secret, username, password
            或直接提供:
            - access_token, instance_url

    Returns:
        {"connected": True/False, "message": "...", "instance_url": "..."}
    """
    # 如果未提供 token，先自动获取
    access_token = config.get("access_token", "")
    instance_url = config.get("instance_url", "")

    if not access_token:
        token_result = get_access_token(
            config.get("client_id", ""),
            config.get("client_secret", ""),
            config.get("username", ""),
            config.get("password", ""),
        )
        if not token_result.get("success"):
            return {"connected": False, "message": token_result.get("error", "Token 获取失败")}
        access_token = token_result["access_token"]
        instance_url = token_result.get("instance_url", "")

    if not instance_url:
        return {"connected": False, "message": "缺少 instance_url"}

    try:
        url = f"{instance_url.rstrip('/')}/services/data/{SF_API_VERSION}/sobjects/Contact/describe"
        resp = requests.get(url, headers=_sf_headers(access_token), timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            return {"connected": True, "message": "Salesforce 连接成功", "instance_url": instance_url}
        elif resp.status_code == 401:
            return {"connected": False, "message": "Salesforce Access Token 无效或已过期"}
        else:
            return {
                "connected": False,
                "message": f"Salesforce 返回异常状态码: {resp.status_code}",
            }
    except requests.exceptions.Timeout:
        return {"connected": False, "message": "Salesforce 连接超时（10秒）"}
    except requests.exceptions.ConnectionError:
        return {"connected": False, "message": "无法连接到 Salesforce 实例"}
    except Exception as e:
        return {"connected": False, "message": f"Salesforce 连接异常: {e}"}


def export_contact(config: dict[str, Any], contact_data: dict[str, Any]) -> dict[str, Any]:
    """导出联系人到 Salesforce（自动获取 Token，按 Email 去重）。

    Args:
        config: Salesforce 配置字典，支持:
            - client_id, client_secret, username, password (用于自动获取 Token)
            - access_token, instance_url (直接提供凭证)
        contact_data: 联系人信息，支持字段:
            name, email, phone, company, title, source

    Returns:
        {"success": True, "contact_id": "..."} 或 {"success": False, "error": "..."}
    """
    # 1. 获取/刷新 Token
    access_token = config.get("access_token", "")
    instance_url = config.get("instance_url", "")

    if not access_token:
        token_result = get_access_token(
            config.get("client_id", ""),
            config.get("client_secret", ""),
            config.get("username", ""),
            config.get("password", ""),
        )
        if not token_result.get("success"):
            return {"success": False, "error": token_result.get("error", "Token 获取失败")}
        access_token = token_result["access_token"]
        instance_url = token_result.get("instance_url", "")

    if not instance_url:
        return {"success": False, "error": "缺少 instance_url"}

    headers = _sf_headers(access_token)
    base_url = f"{instance_url.rstrip('/')}/services/data/{SF_API_VERSION}"

    # 2. 数据映射到 Salesforce Contact 字段
    name = contact_data.get("name", "") or ""
    parts = name.split(" ", 1) if name else ["", ""]
    fields = {
        "FirstName": parts[0],
        "LastName": parts[1] if len(parts) > 1 else name,
        "Email": contact_data.get("email", ""),
        "Phone": contact_data.get("phone", ""),
        "Title": contact_data.get("title", ""),
        "LeadSource": contact_data.get("source", "API"),
    }
    fields = {k: v for k, v in fields.items() if v}

    try:
        # 3. 按 Email 查重
        email = fields.get("Email", "")
        if email:
            escaped = email.replace("'", "\\'")
            query = f"SELECT Id FROM Contact WHERE Email = '{escaped}' LIMIT 1"
            from urllib.parse import quote
            q_url = f"{base_url}/query?q={quote(query)}"
            search_resp = requests.get(q_url, headers=headers, timeout=REQUEST_TIMEOUT)
            if search_resp.status_code == 200:
                records = search_resp.json().get("records", [])
                if records:
                    # 已存在 → 更新
                    contact_id = records[0]["Id"]
                    up_url = f"{base_url}/sobjects/Contact/{contact_id}"
                    up_resp = requests.patch(up_url, headers=headers, json=fields, timeout=REQUEST_TIMEOUT)
                    if up_resp.status_code in (200, 204):
                        return {"success": True, "contact_id": contact_id}
                    else:
                        return {
                            "success": False,
                            "error": f"更新联系人失败: {up_resp.status_code} {up_resp.text[:200]}",
                        }

        # 4. 不存在 → 新建
        create_url = f"{base_url}/sobjects/Contact/"
        create_resp = requests.post(create_url, headers=headers, json=fields, timeout=REQUEST_TIMEOUT)
        if create_resp.status_code in (200, 201):
            created = create_resp.json()
            return {"success": True, "contact_id": created.get("id")}
        else:
            return {
                "success": False,
                "error": f"创建联系人失败: {create_resp.status_code} {create_resp.text[:200]}",
            }

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Salesforce 请求超时（10秒）"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "无法连接到 Salesforce 实例"}
    except Exception as e:
        return {"success": False, "error": f"Salesforce 导出异常: {e}"}
