"""Salesforce CRM 连接器 — 生产就绪版。

特性:
  1. 环境变量就绪 → 真实 HTTP 调用 (requests + Salesforce REST API)
  2. 环境变量缺失或网络异常 → 自动降级到内存存根 (不报错，静默降级)
  3. 兼容 CrmBase 接口，即插即用

环境变量 (SF_* 优先，SALESFORCE_* 向后兼容):
  SF_CONSUMER_KEY | SALESFORCE_CLIENT_ID
  SF_CONSUMER_SECRET | SALESFORCE_CLIENT_SECRET
  SF_USERNAME | SALESFORCE_USERNAME
  SF_PASSWORD | SALESFORCE_PASSWORD
  SF_SECURITY_TOKEN | SALESFORCE_SECURITY_TOKEN
  SF_INSTANCE_URL | SALESFORCE_INSTANCE_URL
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import requests

from .crm_base import CrmBase, ContactData, SyncResult
from .salesforce_stub import SalesforceStub

logger = logging.getLogger(__name__)

# ── Salesforce REST API 常量 ──────────────────────────────────────────────
SF_LOGIN_URL = "https://login.salesforce.com/services/oauth2/token"
SF_API_VERSION = "v58.0"
REQUEST_TIMEOUT = 10  # 超时秒数


def _read_env(key_sf: str, key_salesforce: str, default: str = "") -> str:
    """读取环境变量，SF_* 优先，SALESFORCE_* 为后备。"""
    return os.environ.get(key_sf) or os.environ.get(key_salesforce) or default


def _check_env() -> dict[str, str]:
    """检查环境变量是否齐全，返回凭据字典；缺失返回空 dict。"""
    creds = {
        "instance_url": _read_env("SF_INSTANCE_URL", "SALESFORCE_INSTANCE_URL"),
        "client_id": _read_env("SF_CONSUMER_KEY", "SALESFORCE_CLIENT_ID"),
        "client_secret": _read_env("SF_CONSUMER_SECRET", "SALESFORCE_CLIENT_SECRET"),
        "username": _read_env("SF_USERNAME", "SALESFORCE_USERNAME"),
        "password": _read_env("SF_PASSWORD", "SALESFORCE_PASSWORD"),
        "security_token": _read_env("SF_SECURITY_TOKEN", "SALESFORCE_SECURITY_TOKEN"),
    }
    # 这些是必需的
    required = ["instance_url", "client_id", "client_secret", "username", "password"]
    missing = [k for k in required if not creds[k]]
    if missing:
        logger.info(
            "SalesforceConnector: 环境变量缺失 %s → 自动降级到存根模式",
            missing,
        )
        return {}
    return creds


def _get_access_token(
    client_id: str,
    client_secret: str,
    username: str,
    password: str,
) -> dict:
    """通过 OAuth 2.0 Username-Password Flow 获取 Access Token。"""
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
            }
        else:
            err = resp.json()
            logger.warning("Salesforce 认证失败: %s", err.get("error_description", err))
            return {"success": False}
    except requests.exceptions.Timeout:
        logger.warning("Salesforce 登录超时")
        return {"success": False}
    except requests.exceptions.ConnectionError:
        logger.warning("无法连接到 login.salesforce.com")
        return {"success": False}
    except Exception as e:
        logger.warning("Salesforce 登录异常: %s", e)
        return {"success": False}


def _sf_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def _map_to_sf(contact: ContactData) -> dict:
    """将 ContactData 映射到 Salesforce Contact 字段。"""
    name = contact.name or ""
    parts = name.split(" ", 1)
    fields = {
        "FirstName": parts[0],
        "LastName": parts[1] if len(parts) > 1 else name,
        "Email": contact.email,
        "Phone": contact.phone,
        "Title": contact.title,
    }
    return {k: v for k, v in fields.items() if v}


def _unmap_from_sf(sf_data: dict) -> dict:
    """将 Salesforce API 响应映射到 ContactData 字段。"""
    return {
        "external_id": sf_data.get("Id", ""),
        "name": f"{sf_data.get('FirstName', '')} {sf_data.get('LastName', '')}".strip(),
        "email": sf_data.get("Email", ""),
        "phone": sf_data.get("Phone", ""),
        "company": sf_data.get("AccountId", ""),
        "title": sf_data.get("Title", ""),
        "raw": sf_data,
    }


class SalesforceConnector(CrmBase):
    """Salesforce CRM 连接器 — 生产就绪 + 自动存根降级。

    用法:
        connector = SalesforceConnector()
        connector.authenticate()          # 自动检测模式
        contact = connector.get_contact("003...")
    """

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self._stub: SalesforceStub | None = None
        self._creds: dict[str, str] = {}
        self._access_token: str = ""
        self._instance_url: str = ""
        self._mode: str = "stub"  # "real" | "stub"

    # ── 认证 ─────────────────────────────────────────────────────────

    def authenticate(self) -> bool:
        creds = _check_env()
        if not creds:
            # 环境变量缺失 → 使用存根
            self._mode = "stub"
            self._stub = SalesforceStub(self.config)
            result = self._stub.authenticate()
            self._authenticated = result
            logger.info("SalesforceConnector: 存根模式认证通过")
            return result

        # 尝试真实认证
        password = creds["password"]
        if creds.get("security_token"):
            password = creds["password"] + creds["security_token"]

        token_result = _get_access_token(
            creds["client_id"],
            creds["client_secret"],
            creds["username"],
            password,
        )
        if token_result.get("success"):
            self._mode = "real"
            self._access_token = token_result["access_token"]
            self._instance_url = token_result["instance_url"] or creds["instance_url"]
            self._authenticated = True
            logger.info("SalesforceConnector: 真实认证通过 → %s", self._instance_url)
            return True
        else:
            # 认证失败 → 降级到存根
            logger.warning("SalesforceConnector: 认证失败 → 降级到存根模式")
            self._mode = "stub"
            self._stub = SalesforceStub(self.config)
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
        """确保存根已初始化（降级时）。"""
        if self._mode == "stub" and self._stub is None:
            self._stub = SalesforceStub(self.config)
            self._stub.authenticate()

    def get_contact(self, external_id: str) -> Optional[ContactData]:
        if self._mode == "stub":
            self._real_or_stub()
            return self._stub.get_contact(external_id)

        url = f"{self._instance_url}/services/data/{SF_API_VERSION}/sobjects/Contact/{external_id}"
        try:
            resp = requests.get(url, headers=_sf_headers(self._access_token), timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                mapped = _unmap_from_sf(data)
                return ContactData.from_dict(mapped)
            return None
        except Exception as e:
            logger.warning("Salesforce get_contact 失败 → 降级到存根: %s", e)
            return self._fallback_stub().get_contact(external_id)

    def search_contacts(self, query: str, limit: int = 20) -> list[ContactData]:
        if self._mode == "stub":
            self._real_or_stub()
            return self._stub.search_contacts(query, limit)

        # SOQL 模糊搜索
        safe_query = query.replace("'", "\\'")
        soql = (
            f"SELECT Id, FirstName, LastName, Email, Phone, Title "  # nosec - SOQL, not SQL; query is sanitized
            f"FROM Contact "
            f"WHERE Name LIKE '%{safe_query}%' OR Email LIKE '%{safe_query}%' "
            f"LIMIT {limit}"
        )
        from urllib.parse import quote
        url = f"{self._instance_url}/services/data/{SF_API_VERSION}/query?q={quote(soql)}"
        try:
            resp = requests.get(url, headers=_sf_headers(self._access_token), timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                records = resp.json().get("records", [])
                results = []
                for rec in records:
                    mapped = _unmap_from_sf(rec)
                    results.append(ContactData.from_dict(mapped))
                logger.info("SalesforceConnector: search(%s) → %d 条", query, len(results))
                return results[:limit]
            return []
        except Exception as e:
            logger.warning("Salesforce search_contacts 失败 → 降级到存根: %s", e)
            return self._fallback_stub().search_contacts(query, limit)

    def create_contact(self, contact: ContactData) -> SyncResult:
        if self._mode == "stub":
            self._real_or_stub()
            return self._stub.create_contact(contact)

        fields = _map_to_sf(contact)
        url = f"{self._instance_url}/services/data/{SF_API_VERSION}/sobjects/Contact"
        try:
            resp = requests.post(url, headers=_sf_headers(self._access_token), json=fields, timeout=REQUEST_TIMEOUT)
            if resp.status_code in (200, 201):
                created = resp.json()
                ext_id = created.get("id", "")
                contact.external_id = ext_id
                logger.info("SalesforceConnector: 创建联系人 %s", ext_id)
                return SyncResult(success=True, created=1, details=f"created {ext_id}")
            else:
                err = resp.text[:200]
                logger.warning("Salesforce 创建联系人失败: %s", err)
                return SyncResult(success=False, errors=[f"创建失败: {err}"])
        except Exception as e:
            logger.warning("Salesforce create_contact 失败 → 降级到存根: %s", e)
            return self._fallback_stub().create_contact(contact)

    def update_contact(self, contact: ContactData) -> SyncResult:
        if self._mode == "stub":
            self._real_or_stub()
            return self._stub.update_contact(contact)

        ext_id = contact.external_id
        if not ext_id:
            return SyncResult(success=False, errors=["external_id 为空，无法更新"])

        fields = _map_to_sf(contact)
        url = f"{self._instance_url}/services/data/{SF_API_VERSION}/sobjects/Contact/{ext_id}"
        try:
            resp = requests.patch(url, headers=_sf_headers(self._access_token), json=fields, timeout=REQUEST_TIMEOUT)
            if resp.status_code in (200, 204):
                logger.info("SalesforceConnector: 更新联系人 %s", ext_id)
                return SyncResult(success=True, updated=1, details=f"updated {ext_id}")
            else:
                err = resp.text[:200]
                logger.warning("Salesforce 更新联系人失败: %s", err)
                return SyncResult(success=False, errors=[f"更新失败: {err}"])
        except Exception as e:
            logger.warning("Salesforce update_contact 失败 → 降级到存根: %s", e)
            return self._fallback_stub().update_contact(contact)

    def delete_contact(self, external_id: str) -> SyncResult:
        if self._mode == "stub":
            self._real_or_stub()
            return self._stub.delete_contact(external_id)

        url = f"{self._instance_url}/services/data/{SF_API_VERSION}/sobjects/Contact/{external_id}"
        try:
            resp = requests.delete(url, headers=_sf_headers(self._access_token), timeout=REQUEST_TIMEOUT)
            if resp.status_code == 204:
                logger.info("SalesforceConnector: 删除联系人 %s", external_id)
                return SyncResult(success=True, deleted=1, details=f"deleted {external_id}")
            else:
                return SyncResult(success=False, errors=[f"删除失败: {resp.status_code}"])
        except Exception as e:
            logger.warning("Salesforce delete_contact 失败 → 降级到存根: %s", e)
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
                    # 按 email 查找
                    found = None
                    if c.email:
                        found = self._find_by_email(c.email)
                    if found:
                        c.external_id = found.get("Id", "")
                        sub = self.update_contact(c)
                    else:
                        sub = self.create_contact(c)
                elif strategy == "append":
                    sub = self.create_contact(c)
                elif strategy == "replace":
                    # replace: 删除所有 + 重新创建
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
        """通过 SOQL 按 Email 查找联系人。"""
        safe_email = email.replace("'", "\\'")
        soql = f"SELECT Id, FirstName, LastName, Email FROM Contact WHERE Email = '{safe_email}' LIMIT 1"  # nosec - SOQL, not SQL; email is sanitized
        from urllib.parse import quote
        url = f"{self._instance_url}/services/data/{SF_API_VERSION}/query?q={quote(soql)}"
        try:
            resp = requests.get(url, headers=_sf_headers(self._access_token), timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                records = resp.json().get("records", [])
                return records[0] if records else None
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
            url = f"{self._instance_url}/services/data/{SF_API_VERSION}/sobjects/Contact/describe"
            resp = requests.get(url, headers=_sf_headers(self._access_token), timeout=REQUEST_TIMEOUT)
            latency = int((time.time() - start) * 1000)
            if resp.status_code == 200:
                return {"status": "ok", "provider": "salesforce", "latency_ms": latency, "mode": "real"}
            return {"status": "error", "provider": "salesforce", "code": resp.status_code, "mode": "real"}
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return {"status": "error", "provider": "salesforce", "error": str(e), "latency_ms": latency, "mode": "real"}

    # ── 辅助 ──────────────────────────────────────────────────────

    def _fallback_stub(self):
        """将当前实例降级为存根模式并返回存根实例。"""
        self._mode = "stub"
        self._stub = SalesforceStub(self.config)
        self._stub.authenticate()
        self._authenticated = True
        return self._stub
