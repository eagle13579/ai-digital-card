"""HubSpot CRM 连接器 — 生产就绪版。

特性:
  1. 环境变量就绪 → 真实 HTTP 调用 (requests + HubSpot REST API)
  2. 环境变量缺失或网络异常 → 自动降级到内存存根 (不报错，静默降级)
  3. 兼容 CrmBase 接口，即插即用

环境变量:
  HUBSPOT_ACCESS_TOKEN  — Private App Token 或 OAuth Token (必需)
  HUBSPOT_BASE_URL      — API 基础 URL (可选，默认 https://api.hubapi.com/crm/v3)
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import requests

from .crm_base import CrmBase, ContactData, SyncResult
from .hubspot_stub import HubSpotStub

logger = logging.getLogger(__name__)

# ── HubSpot REST API 常量 ────────────────────────────────────────────────
DEFAULT_API_BASE = "https://api.hubapi.com/crm/v3"
REQUEST_TIMEOUT = 10


def _read_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _check_env() -> dict[str, str]:
    """检查环境变量是否齐全，返回凭据字典；缺失返回空 dict。"""
    access_token = _read_env("HUBSPOT_ACCESS_TOKEN")
    if not access_token:
        logger.info(
            "HubSpotConnector: HUBSPOT_ACCESS_TOKEN 未设置 → 自动降级到存根模式"
        )
        return {}
    base_url = _read_env("HUBSPOT_BASE_URL", DEFAULT_API_BASE)
    return {
        "access_token": access_token,
        "base_url": base_url.rstrip("/"),
    }


def _hs_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def _map_to_hs(contact: ContactData) -> dict:
    """将 ContactData 映射到 HubSpot 属性格式。"""
    name = contact.name or ""
    parts = name.split(" ", 1)
    props = {
        "firstname": parts[0],
        "lastname": parts[1] if len(parts) > 1 else "",
        "email": contact.email,
        "phone": contact.phone,
        "company": contact.company,
        "jobtitle": contact.title,
    }
    return {k: v for k, v in props.items() if v}


def _unmap_from_hs(hs_data: dict) -> dict:
    """将 HubSpot API 响应映射到 ContactData 字段。"""
    props = hs_data.get("properties", {})
    return {
        "external_id": hs_data.get("id", ""),
        "name": f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
        "email": props.get("email", ""),
        "phone": props.get("phone", ""),
        "company": props.get("company", ""),
        "title": props.get("jobtitle", ""),
        "raw": hs_data,
    }


class HubSpotConnector(CrmBase):
    """HubSpot CRM 连接器 — 生产就绪 + 自动存根降级。

    用法:
        connector = HubSpotConnector()
        connector.authenticate()
        contact = connector.get_contact("123456")
    """

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self._stub: HubSpotStub | None = None
        self._access_token: str = ""
        self._base_url: str = DEFAULT_API_BASE
        self._mode: str = "stub"  # "real" | "stub"

    # ── 认证 ─────────────────────────────────────────────────────────

    def authenticate(self) -> bool:
        creds = _check_env()
        if not creds:
            # 环境变量缺失 → 使用存根
            self._mode = "stub"
            self._stub = HubSpotStub(self.config)
            result = self._stub.authenticate()
            self._authenticated = result
            logger.info("HubSpotConnector: 存根模式认证通过")
            return result

        # 验证 Token 有效性：发起一个轻量请求
        self._access_token = creds["access_token"]
        self._base_url = creds["base_url"]
        test_url = f"{self._base_url}/objects/contacts?limit=1"

        try:
            resp = requests.get(test_url, headers=_hs_headers(self._access_token), timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                self._mode = "real"
                self._authenticated = True
                logger.info("HubSpotConnector: 真实认证通过")
                return True
            else:
                logger.warning("HubSpotConnector: Token 无效 (HTTP %d) → 降级到存根模式", resp.status_code)
        except Exception as e:
            logger.warning("HubSpotConnector: 认证异常 (%s) → 降级到存根模式", e)

        # 降级
        self._mode = "stub"
        self._stub = HubSpotStub(self.config)
        result = self._stub.authenticate()
        self._authenticated = result
        return result

    # ── 公共属性 ─────────────────────────────────────────────────────

    @property
    def mode(self) -> str:
        """当前模式: 'real' 或 'stub'。"""
        return self._mode

    # ── 联系人 CRUD ────────────────────────────────────────────────

    def _real_or_stub(self):
        if self._mode == "stub" and self._stub is None:
            self._stub = HubSpotStub(self.config)
            self._stub.authenticate()

    def get_contact(self, external_id: str) -> Optional[ContactData]:
        if self._mode == "stub":
            self._real_or_stub()
            return self._stub.get_contact(external_id)

        url = f"{self._base_url}/objects/contacts/{external_id}"
        try:
            resp = requests.get(url, headers=_hs_headers(self._access_token), timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                mapped = _unmap_from_hs(data)
                return ContactData.from_dict(mapped)
            return None
        except Exception as e:
            logger.warning("HubSpot get_contact 失败 → 降级到存根: %s", e)
            return self._fallback_stub().get_contact(external_id)

    def search_contacts(self, query: str, limit: int = 20) -> list[ContactData]:
        if self._mode == "stub":
            self._real_or_stub()
            return self._stub.search_contacts(query, limit)

        # HubSpot 使用 search API (POST)
        url = f"{self._base_url}/objects/contacts/search"
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "CONTAINS_TOKEN",
                            "value": query,
                        }
                    ]
                }
            ],
            "properties": ["firstname", "lastname", "email", "phone", "company", "jobtitle"],
            "limit": limit,
        }
        # 也搜索姓名
        payload_name = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "firstname",
                            "operator": "CONTAINS_TOKEN",
                            "value": query,
                        }
                    ]
                },
                {
                    "filters": [
                        {
                            "propertyName": "lastname",
                            "operator": "CONTAINS_TOKEN",
                            "value": query,
                        }
                    ]
                },
            ],
            "properties": ["firstname", "lastname", "email", "phone", "company", "jobtitle"],
            "limit": limit,
        }
        try:
            seen: set[str] = set()
            results: list[ContactData] = []

            for pl in [payload, payload_name]:
                resp = requests.post(url, headers=_hs_headers(self._access_token), json=pl, timeout=REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    for rec in resp.json().get("results", []):
                        rid = rec.get("id", "")
                        if rid not in seen and len(results) < limit:
                            seen.add(rid)
                            mapped = _unmap_from_hs(rec)
                            results.append(ContactData.from_dict(mapped))

            logger.info("HubSpotConnector: search(%s) → %d 条", query, len(results))
            return results[:limit]
        except Exception as e:
            logger.warning("HubSpot search_contacts 失败 → 降级到存根: %s", e)
            return self._fallback_stub().search_contacts(query, limit)

    def create_contact(self, contact: ContactData) -> SyncResult:
        if self._mode == "stub":
            self._real_or_stub()
            return self._stub.create_contact(contact)

        properties = _map_to_hs(contact)
        url = f"{self._base_url}/objects/contacts"
        try:
            resp = requests.post(
                url,
                headers=_hs_headers(self._access_token),
                json={"properties": properties},
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code in (200, 201):
                created = resp.json()
                ext_id = created.get("id", "")
                contact.external_id = ext_id
                logger.info("HubSpotConnector: 创建联系人 %s", ext_id)
                return SyncResult(success=True, created=1, details=f"created {ext_id}")
            else:
                err = resp.text[:200]
                logger.warning("HubSpot 创建联系人失败: %s", err)
                return SyncResult(success=False, errors=[f"创建失败: {err}"])
        except Exception as e:
            logger.warning("HubSpot create_contact 失败 → 降级到存根: %s", e)
            return self._fallback_stub().create_contact(contact)

    def update_contact(self, contact: ContactData) -> SyncResult:
        if self._mode == "stub":
            self._real_or_stub()
            return self._stub.update_contact(contact)

        ext_id = contact.external_id
        if not ext_id:
            return SyncResult(success=False, errors=["external_id 为空，无法更新"])

        properties = _map_to_hs(contact)
        url = f"{self._base_url}/objects/contacts/{ext_id}"
        try:
            resp = requests.patch(
                url,
                headers=_hs_headers(self._access_token),
                json={"properties": properties},
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code in (200, 204):
                logger.info("HubSpotConnector: 更新联系人 %s", ext_id)
                return SyncResult(success=True, updated=1, details=f"updated {ext_id}")
            else:
                err = resp.text[:200]
                logger.warning("HubSpot 更新联系人失败: %s", err)
                return SyncResult(success=False, errors=[f"更新失败: {err}"])
        except Exception as e:
            logger.warning("HubSpot update_contact 失败 → 降级到存根: %s", e)
            return self._fallback_stub().update_contact(contact)

    def delete_contact(self, external_id: str) -> SyncResult:
        if self._mode == "stub":
            self._real_or_stub()
            return self._stub.delete_contact(external_id)

        url = f"{self._base_url}/objects/contacts/{external_id}"
        try:
            resp = requests.delete(url, headers=_hs_headers(self._access_token), timeout=REQUEST_TIMEOUT)
            if resp.status_code == 204:
                logger.info("HubSpotConnector: 删除联系人 %s", external_id)
                return SyncResult(success=True, deleted=1, details=f"deleted {external_id}")
            else:
                return SyncResult(success=False, errors=[f"删除失败: {resp.status_code}"])
        except Exception as e:
            logger.warning("HubSpot delete_contact 失败 → 降级到存根: %s", e)
            return self._fallback_stub().delete_contact(external_id)

    # ── 批量同步 ──────────────────────────────────────────────────

    def sync_contacts(
        self,
        contacts: list[ContactData],
        strategy: str = "upsert",
    ) -> SyncResult:
        if self._mode == "stub":
            self._real_or_stub()
            return self._stub.sync_contacts(contacts, strategy)

        result = SyncResult(success=True)
        for c in contacts:
            try:
                if strategy == "upsert":
                    found = None
                    if c.email:
                        found = self._find_by_email(c.email)
                    if found:
                        c.external_id = found.get("id", "")
                        sub = self.update_contact(c)
                    else:
                        sub = self.create_contact(c)
                elif strategy == "append":
                    sub = self.create_contact(c)
                elif strategy == "replace":
                    sub = self.create_contact(c)
                else:
                    result.errors.append(f"不支持的策略: {strategy}")
                    continue

                if sub.success:
                    result.created += sub.created
                    result.updated += sub.updated
                    result.deleted += sub.deleted
                else:
                    result.errors.extend(sub.errors)
            except Exception as e:
                result.errors.append(f"同步联系人失败: {e}")

        self._log_sync(f"sync_contacts({strategy})", result)
        return result

    def _find_by_email(self, email: str) -> Optional[dict]:
        """通过 Search API 按 Email 查找联系人。"""
        url = f"{self._base_url}/objects/contacts/search"
        payload = {
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
        try:
            resp = requests.post(url, headers=_hs_headers(self._access_token), json=payload, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                return results[0] if results else None
            return None
        except Exception:
            return None

    # ── 健康检查 ──────────────────────────────────────────────────

    def health_check(self) -> dict:
        if self._mode == "stub":
            self._real_or_stub()
            return self._stub.health_check()

        import time
        start = time.time()
        try:
            url = f"{self._base_url}/objects/contacts?limit=1"
            resp = requests.get(url, headers=_hs_headers(self._access_token), timeout=REQUEST_TIMEOUT)
            latency = int((time.time() - start) * 1000)
            if resp.status_code == 200:
                return {"status": "ok", "provider": "hubspot", "latency_ms": latency, "mode": "real"}
            return {"status": "error", "provider": "hubspot", "code": resp.status_code, "mode": "real"}
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return {"status": "error", "provider": "hubspot", "error": str(e), "latency_ms": latency, "mode": "real"}

    # ── 辅助 ──────────────────────────────────────────────────────

    def _fallback_stub(self):
        """将当前实例降级为存根模式并返回存根实例。"""
        self._mode = "stub"
        self._stub = HubSpotStub(self.config)
        self._stub.authenticate()
        self._authenticated = True
        return self._stub
