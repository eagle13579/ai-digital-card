"""HubSpot CRM 连接器 — 存根实现。

生产替换步骤:
1. pip install hubspot-api-client
2. 在 .env 中配置:
   HUBSPOT_ACCESS_TOKEN=xxx
   HUBSPOT_CLIENT_ID=xxx
   HUBSPOT_CLIENT_SECRET=xxx
3. 将 Stub 中的模拟逻辑替换为 hubspot-api-client 调用
4. 移除本文件或重命名为 hubspot.py
"""

from __future__ import annotations

import logging
from typing import Optional

from .crm_base import CrmBase, ContactData, SyncResult

logger = logging.getLogger(__name__)


class HubSpotStub(CrmBase):
    """HubSpot CRM 存根连接器。

    当前返回模拟数据，不依赖任何外部 SDK。
    """

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self._mock_store: dict[str, dict] = {}

    # ── 认证 ──────────────────────────────────────────

    def authenticate(self) -> bool:
        # TODO: 替换为 hubspot-api-client 认证
        # from hubspot import HubSpot
        # self._hs = HubSpot(access_token=self.config["access_token"])
        required = ["access_token"]
        if not all(k in self.config for k in required):
            logger.warning(
                "HubSpotStub: 缺少必要凭据 %s (使用模拟模式)",
                [k for k in required if k not in self.config],
            )
        self._authenticated = True
        logger.info("HubSpotStub: 模拟认证通过")
        return True

    # ── 联系人 CRUD ───────────────────────────────────

    def get_contact(self, external_id: str) -> Optional[ContactData]:
        raw = self._mock_store.get(external_id)
        if raw is None:
            return None
        return ContactData.from_dict(raw)

    def search_contacts(self, query: str, limit: int = 20) -> list[ContactData]:
        results: list[ContactData] = []
        for raw in self._mock_store.values():
            if len(results) >= limit:
                break
            if query.lower() in raw.get("name", "").lower() or \
               query.lower() in raw.get("email", "").lower():
                results.append(ContactData.from_dict(raw))
        logger.info("HubSpotStub: search(%s) → %d 条", query, len(results))
        return results

    def create_contact(self, contact: ContactData) -> SyncResult:
        ext_id = f"HS-{contact.email.replace('@', '-')}"
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
                    ext_id = f"HS-{c.email.replace('@', '-')}"
                    c.external_id = ext_id
                    self._mock_store[ext_id] = c.to_dict()
                    result.created += 1
            elif strategy == "append":
                ext_id = f"HS-{c.email.replace('@', '-')}"
                c.external_id = ext_id
                self._mock_store[ext_id] = c.to_dict()
                result.created += 1
            else:
                result.errors.append(f"Unsupported strategy: {strategy}")
        self._log_sync(f"sync_contacts({strategy})", result)
        return result

    # ── 健康检查 ──────────────────────────────────────

    def health_check(self) -> dict:
        # TODO: 替换为真实 hubspot API 探测
        return {"status": "ok", "provider": "hubspot", "latency_ms": 35, "mode": "stub"}
