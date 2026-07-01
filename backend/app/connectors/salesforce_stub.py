"""Salesforce CRM 连接器 — 存根实现。

生产替换步骤:
1. pip install simple-salesforce
2. 在 .env 中配置:
   SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
   SALESFORCE_CLIENT_ID=xxx
   SALESFORCE_CLIENT_SECRET=xxx
   SALESFORCE_USERNAME=xxx
   SALESFORCE_PASSWORD=xxx
   SALESFORCE_SECURITY_TOKEN=xxx
3. 将 Stub 中的模拟逻辑替换为 simple-salesforce API 调用
4. 移除本文件或重命名为 salesforce.py
"""

from __future__ import annotations

import logging
from typing import Optional

from .crm_base import CrmBase, ContactData, SyncResult

logger = logging.getLogger(__name__)


class SalesforceStub(CrmBase):
    """Salesforce CRM 存根连接器。

    当前返回模拟数据，不依赖任何外部 SDK。
    """

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self._mock_store: dict[str, dict] = {}  # external_id -> raw dict

    # ── 认证 ──────────────────────────────────────────

    def authenticate(self) -> bool:
        # TODO: 替换为 simple-salesforce 认证
        # from simple_salesforce import Salesforce
        # self._sf = Salesforce(
        #     username=self.config["username"],
        #     password=self.config["password"],
        #     security_token=self.config["security_token"],
        #     client_id=self.config["client_id"],
        # )
        required = ["instance_url", "client_id", "client_secret", "username", "password"]
        if not all(k in self.config for k in required):
            logger.warning(
                "SalesforceStub: 缺少必要凭据 %s (使用模拟模式)",
                [k for k in required if k not in self.config],
            )
        self._authenticated = True
        logger.info("SalesforceStub: 模拟认证通过")
        return True

    # ── 联系人 CRUD ───────────────────────────────────

    def get_contact(self, external_id: str) -> Optional[ContactData]:
        raw = self._mock_store.get(external_id)
        if raw is None:
            return None
        return ContactData.from_dict(raw)

    def search_contacts(self, query: str, limit: int = 20) -> list[ContactData]:
        # 模拟: 按 name/email 前缀匹配
        results: list[ContactData] = []
        for raw in self._mock_store.values():
            if len(results) >= limit:
                break
            if query.lower() in raw.get("name", "").lower() or \
               query.lower() in raw.get("email", "").lower():
                results.append(ContactData.from_dict(raw))
        logger.info("SalesforceStub: search(%s) → %d 条", query, len(results))
        return results

    def create_contact(self, contact: ContactData) -> SyncResult:
        ext_id = f"SF-{contact.email.replace('@', '-')}"
        contact.external_id = ext_id
        self._mock_store[ext_id] = contact.to_dict()
        return SyncResult(success=True, created=1, details=f"created {ext_id}")

    def update_contact(self, contact: ContactData) -> SyncResult:
        if contact.external_id not in self._mock_store:
            return SyncResult(
                success=False,
                errors=[f"Contact {contact.external_id} not found"],
            )
        self._mock_store[contact.external_id] = contact.to_dict()
        return SyncResult(success=True, updated=1)

    def delete_contact(self, external_id: str) -> SyncResult:
        if external_id in self._mock_store:
            del self._mock_store[external_id]
            return SyncResult(success=True, deleted=1)
        return SyncResult(
            success=False,
            errors=[f"Contact {external_id} not found"],
        )

    # ── 批量同步 ──────────────────────────────────────

    def sync_contacts(
        self,
        contacts: list[ContactData],
        strategy: str = "upsert",
    ) -> SyncResult:
        result = SyncResult(success=True)
        for c in contacts:
            if strategy == "upsert":
                if c.external_id and c.external_id in self._mock_store:
                    self._mock_store[c.external_id] = c.to_dict()
                    result.updated += 1
                else:
                    ext_id = f"SF-{c.email.replace('@', '-')}"
                    c.external_id = ext_id
                    self._mock_store[ext_id] = c.to_dict()
                    result.created += 1
            elif strategy == "append":
                ext_id = f"SF-{c.email.replace('@', '-')}"
                c.external_id = ext_id
                self._mock_store[ext_id] = c.to_dict()
                result.created += 1
            else:
                result.errors.append(f"Unsupported strategy: {strategy}")
        self._log_sync(f"sync_contacts({strategy})", result)
        return result

    # ── 健康检查 ──────────────────────────────────────

    def health_check(self) -> dict:
        # TODO: 替换为真实 simple-salesforce 端点探测
        return {"status": "ok", "provider": "salesforce", "latency_ms": 42, "mode": "stub"}
