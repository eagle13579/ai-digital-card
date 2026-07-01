"""HubSpot CRM API 集成 — 基于 HubSpot REST API (crm.contacts)。

提供两种使用方式:
  1. HubSpotProvider (async class) — 与 CRMBridge 框架集成
  2. test_connection / export_contact (sync functions) — 独立快速调用
"""
import json
import logging
from typing import Any

import httpx
import requests

from app.services.crm_bridge import CRMProvider

logger = logging.getLogger("crm_hubspot")

# ── HubSpot REST API 常量 ────────────────────────────────────────────────
HUBSPOT_API_BASE = "https://api.hubapi.com/crm/v3"
REQUEST_TIMEOUT = 10  # 超时秒数


class HubSpotProvider(CRMProvider):
    """HubSpot CRM 集成实现。"""

    API_BASE = "https://api.hubapi.com/crm/v3"

    def __init__(self, access_token: str = "") -> None:
        self._access_token = access_token

    # ── 配置 ──────────────────────────────────────────────────────────────

    def configure(self, config: dict[str, Any]) -> None:
        """从字典加载配置（通常来自 Integration.config 字段）。"""
        self._access_token = config.get("access_token", config.get("api_key", ""))

    def get_provider_name(self) -> str:
        return "hubspot"

    # ── HTTP 客户端 ───────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    # ── CRM 接口实现 ──────────────────────────────────────────────────────

    async def export_contact(self, contact_data: dict[str, Any]) -> dict[str, Any]:
        """创建或更新 HubSpot 联系人（通过 email 去重）。"""
        properties = self._map_contact_data(contact_data)
        # 先查询是否存在
        email = properties.get("email", "")
        existing = await self._find_by_email(email) if email else None
        if existing:
            contact_id = existing["id"]
            return await self._update(contact_id, properties)
        return await self._create(properties)

    async def update_contact(
        self, contact_id: str, contact_data: dict[str, Any]
    ) -> dict[str, Any]:
        properties = self._map_contact_data(contact_data)
        return await self._update(contact_id, properties)

    async def delete_contact(self, contact_id: str) -> bool:
        url = f"{self.API_BASE}/objects/contacts/{contact_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, headers=self._headers())
            return resp.status_code == 204

    async def get_contact(self, contact_id: str) -> dict[str, Any] | None:
        url = f"{self.API_BASE}/objects/contacts/{contact_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._headers())
            if resp.status_code == 200:
                data = resp.json()
                return self._unmap_contact(data)
            return None

    async def test_connection(self) -> bool:
        """通过获取联系人列表来测试 Token 有效性。"""
        url = f"{self.API_BASE}/objects/contacts?limit=1"
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=self._headers())
                return resp.status_code == 200
            except Exception:
                return False

    # ── 内部方法 ──────────────────────────────────────────────────────────

    def _map_contact_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """将通用名片数据映射到 HubSpot 属性格式。"""
        props = {
            "firstname": data.get("name", "").split(" ", 1)[0] if data.get("name") else "",
            "lastname": (
                data.get("name", "").split(" ", 1)[1] if data.get("name") and " " in data["name"] else ""
            ),
            "email": data.get("email", ""),
            "phone": data.get("phone", ""),
            "company": data.get("company", ""),
            "jobtitle": data.get("title", ""),
            "hs_lead_status": data.get("status", "NEW"),
        }
        # 自定义字段
        extra = data.get("custom_fields", {})
        if isinstance(extra, dict):
            for k, v in extra.items():
                if k not in props:
                    props[k] = str(v) if not isinstance(v, str) else v
        return {k: v for k, v in props.items() if v}

    def _unmap_contact(self, hubspot_data: dict[str, Any]) -> dict[str, Any]:
        """将 HubSpot API 响应映射回通用格式。"""
        props = hubspot_data.get("properties", {})
        return {
            "id": hubspot_data.get("id"),
            "name": f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
            "email": props.get("email", ""),
            "phone": props.get("phone", ""),
            "company": props.get("company", ""),
            "title": props.get("jobtitle", ""),
            "status": props.get("hs_lead_status", ""),
            "source": "hubspot",
        }

    async def _create(self, properties: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.API_BASE}/objects/contacts"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers=self._headers(),
                json={"properties": properties},
            )
            resp.raise_for_status()
            data = resp.json()
            return {"id": data.get("id"), "provider": "hubspot"}

    async def _update(self, contact_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.API_BASE}/objects/contacts/{contact_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                url,
                headers=self._headers(),
                json={"properties": properties},
            )
            resp.raise_for_status()
            return {"id": contact_id, "provider": "hubspot", "updated": True}

    async def _find_by_email(self, email: str) -> dict[str, Any] | None:
        url = f"{self.API_BASE}/objects/contacts/search"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers=self._headers(),
                json={
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "propertyName": "email",
                                    "operator": "EQ",
                                    "value": email,
                                }
                            ]
                        }
                    ],
                    "limit": 1,
                },
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                return results[0] if results else None
            return None


# ══════════════════════════════════════════════════════════════════════════
# 独立同步函数 — 无需类实例化，直接使用 requests 库
# 适用于简单的一键调用场景
# ══════════════════════════════════════════════════════════════════════════


def _hs_headers(api_key: str) -> dict[str, str]:
    """构造 HubSpot API 请求头。"""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def test_connection(api_key: str) -> dict[str, Any]:
    """测试 HubSpot API 连接有效性。

    Args:
        api_key: HubSpot Private App Access Token

    Returns:
        {"connected": True/False, "message": "..."}
    """
    url = f"{HUBSPOT_API_BASE}/objects/contacts?limit=1"
    try:
        resp = requests.get(url, headers=_hs_headers(api_key), timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            return {"connected": True, "message": "HubSpot 连接成功"}
        elif resp.status_code == 401:
            return {"connected": False, "message": "HubSpot API Key 无效或已过期"}
        else:
            return {
                "connected": False,
                "message": f"HubSpot 返回异常状态码: {resp.status_code}",
            }
    except requests.exceptions.Timeout:
        return {"connected": False, "message": "HubSpot 连接超时（10秒）"}
    except requests.exceptions.ConnectionError:
        return {"connected": False, "message": "无法连接到 HubSpot API 服务器"}
    except Exception as e:
        return {"connected": False, "message": f"HubSpot 连接异常: {e}"}


def export_contact(api_key: str, contact_data: dict[str, Any]) -> dict[str, Any]:
    """导出联系人到 HubSpot（通过 email 去重，存在则更新）。

    Args:
        api_key: HubSpot Private App Access Token
        contact_data: 联系人信息，支持字段:
            name, email, phone, company, title, status, custom_fields

    Returns:
        {"success": True, "contact_id": "..."} 或 {"success": False, "error": "..."}
    """
    # 1. 数据映射
    name = contact_data.get("name", "") or ""
    parts = name.split(" ", 1) if name else ["", ""]
    properties = {
        "firstname": parts[0],
        "lastname": parts[1] if len(parts) > 1 else "",
        "email": contact_data.get("email", ""),
        "phone": contact_data.get("phone", ""),
        "company": contact_data.get("company", ""),
        "jobtitle": contact_data.get("title", ""),
        "hs_lead_status": contact_data.get("status", "NEW"),
    }
    properties = {k: v for k, v in properties.items() if v}

    # 自定义字段
    extra = contact_data.get("custom_fields", {})
    if isinstance(extra, dict):
        for k, v in extra.items():
            if k not in properties:
                properties[k] = str(v) if not isinstance(v, str) else v

    headers = _hs_headers(api_key)

    try:
        # 2. 先按 email 查重
        email = properties.get("email", "")
        if email:
            search_url = f"{HUBSPOT_API_BASE}/objects/contacts/search"
            search_payload = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": email,
                            }
                        ]
                    }
                ],
                "limit": 1,
            }
            search_resp = requests.post(
                search_url, headers=headers, json=search_payload, timeout=REQUEST_TIMEOUT
            )
            if search_resp.status_code == 200:
                results = search_resp.json().get("results", [])
                if results:
                    # 已存在 → 更新
                    contact_id = results[0]["id"]
                    update_url = f"{HUBSPOT_API_BASE}/objects/contacts/{contact_id}"
                    up_resp = requests.patch(
                        update_url, headers=headers, json={"properties": properties},
                        timeout=REQUEST_TIMEOUT
                    )
                    if up_resp.status_code in (200, 204):
                        return {"success": True, "contact_id": contact_id}
                    else:
                        return {
                            "success": False,
                            "error": f"更新联系人失败: {up_resp.status_code} {up_resp.text[:200]}",
                        }

        # 3. 不存在 → 新建
        create_url = f"{HUBSPOT_API_BASE}/objects/contacts"
        create_resp = requests.post(
            create_url, headers=headers, json={"properties": properties},
            timeout=REQUEST_TIMEOUT
        )
        if create_resp.status_code in (200, 201):
            created = create_resp.json()
            return {"success": True, "contact_id": created.get("id")}
        else:
            return {
                "success": False,
                "error": f"创建联系人失败: {create_resp.status_code} {create_resp.text[:200]}",
            }

    except requests.exceptions.Timeout:
        return {"success": False, "error": "HubSpot 请求超时（10秒）"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "无法连接到 HubSpot API 服务器"}
    except Exception as e:
        return {"success": False, "error": f"HubSpot 导出异常: {e}"}
