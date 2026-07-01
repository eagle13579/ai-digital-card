"""CRM 连接器测试 — 同时覆盖真实 API 和存根降级模式。

测试策略:
  1. 有真实环境变量 → 通过 @skipUnless 跑真实 API 测试
  2. 无环境变量 → 自动降级到存根，验证降级路径

运行:
  # 存根模式测试 (默认)
  pytest backend/tests/connectors/ -v

  # 真实 API 测试 (需先配置 .env)
  SF_INSTANCE_URL=... SF_CONSUMER_KEY=... pytest backend/tests/connectors/ -v
"""

from __future__ import annotations

import os
import sys
from typing import Optional

import pytest

# ── 确保 backend 在路径中 ────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.connectors import (
    SalesforceConnector,
    HubSpotConnector,
    ContactData,
    SyncResult,
)

# ══════════════════════════════════════════════════════════════════════
# 检测环境
# ══════════════════════════════════════════════════════════════════════

HAS_SF_ENV = all(
    os.environ.get(k)
    for k in [
        "SF_INSTANCE_URL",
        "SF_CONSUMER_KEY",
        "SF_CONSUMER_SECRET",
        "SF_USERNAME",
        "SF_PASSWORD",
    ]
)

HAS_HS_ENV = bool(os.environ.get("HUBSPOT_ACCESS_TOKEN"))

# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_contact() -> ContactData:
    return ContactData(
        external_id="",
        name="测试用户",
        email="test-crm@example.com",
        phone="13800138000",
        company="测试公司",
        title="测试工程师",
    )


@pytest.fixture
def sample_contact_update() -> ContactData:
    return ContactData(
        external_id="",
        name="测试用户更新",
        email="test-crm@example.com",
        phone="13900139000",
        company="测试公司更新",
        title="高级工程师",
    )


# ══════════════════════════════════════════════════════════════════════
# SalesforceConnector 测试
# ══════════════════════════════════════════════════════════════════════


class TestSalesforceConnectorStub:
    """Salesforce 存根降级模式测试 (无环境变量时自动触发)。"""

    @pytest.fixture(autouse=True)
    def _clean_env(self, monkeypatch):
        """清除 Salesforce 环境变量以确保触发存根模式。"""
        for key in [
            "SF_INSTANCE_URL",
            "SF_CONSUMER_KEY",
            "SF_CONSUMER_SECRET",
            "SF_USERNAME",
            "SF_PASSWORD",
            "SF_SECURITY_TOKEN",
            "SALESFORCE_INSTANCE_URL",
            "SALESFORCE_CLIENT_ID",
            "SALESFORCE_CLIENT_SECRET",
            "SALESFORCE_USERNAME",
            "SALESFORCE_PASSWORD",
            "SALESFORCE_SECURITY_TOKEN",
        ]:
            monkeypatch.delenv(key, raising=False)

    @pytest.fixture
    def connector(self):
        c = SalesforceConnector()
        c.authenticate()
        assert c.mode == "stub", "应自动降级为存根模式"
        return c

    def test_authenticate_stub_mode(self, connector):
        """存根模式下认证应成功。"""
        assert connector.is_authenticated
        assert connector.mode == "stub"

    def test_health_check(self, connector):
        """健康检查返回存根信息。"""
        hc = connector.health_check()
        assert hc["status"] == "ok"
        assert hc["mode"] == "stub"
        assert hc["provider"] == "salesforce"

    def test_create_and_get_contact(self, connector, sample_contact):
        """创建联系人后应能通过 get_contact 获取。"""
        result = connector.create_contact(sample_contact)
        assert result.success
        assert result.created == 1
        assert sample_contact.external_id != ""

        fetched = connector.get_contact(sample_contact.external_id)
        assert fetched is not None
        assert fetched.email == sample_contact.email
        assert fetched.name == sample_contact.name

    def test_get_contact_not_found(self, connector):
        """不存在的联系人应返回 None。"""
        fetched = connector.get_contact("NONEXISTENT-ID")
        assert fetched is None

    def test_update_contact(self, connector, sample_contact, sample_contact_update):
        """更新联系人后字段应变更。"""
        # 先创建
        connector.create_contact(sample_contact)
        ext_id = sample_contact.external_id

        # 更新
        sample_contact_update.external_id = ext_id
        result = connector.update_contact(sample_contact_update)
        assert result.success
        assert result.updated == 1

        # 验证
        fetched = connector.get_contact(ext_id)
        assert fetched is not None
        assert fetched.name == sample_contact_update.name
        assert fetched.phone == sample_contact_update.phone

    def test_search_contacts(self, connector):
        """搜索联系人应返回匹配结果。"""
        # 先塞数据
        contacts = [
            ContactData(external_id="", name="张三", email="zhangsan@test.com"),
            ContactData(external_id="", name="李四", email="lisi@test.com"),
            ContactData(external_id="", name="王五", email="wangwu@test.com"),
        ]
        for c in contacts:
            connector.create_contact(c)

        results = connector.search_contacts("张三")
        assert len(results) >= 1
        assert any("张三" in r.name for r in results)

    def test_delete_contact(self, connector, sample_contact):
        """删除联系人后应无法再获取。"""
        connector.create_contact(sample_contact)
        ext_id = sample_contact.external_id

        result = connector.delete_contact(ext_id)
        assert result.success
        assert result.deleted == 1

        fetched = connector.get_contact(ext_id)
        assert fetched is None

    def test_sync_contacts_upsert(self, connector):
        """sync_contacts upsert 模式工作正常。"""
        contacts = [
            ContactData(external_id="", name="用户A", email="usera@test.com"),
            ContactData(external_id="", name="用户B", email="userb@test.com"),
        ]
        result = connector.sync_contacts(contacts, strategy="upsert")
        assert result.success
        assert result.created == 2

        # 再次同步，应该更新已存在的
        contacts[0].name = "用户A-更新"
        result2 = connector.sync_contacts(contacts, strategy="upsert")
        assert result2.success
        assert result2.updated == 2

    def test_sync_contacts_append(self, connector):
        """sync_contacts append 模式应全部新建。"""
        contacts = [
            ContactData(external_id="", name="用户C", email="userc@test.com"),
        ]
        result = connector.sync_contacts(contacts, strategy="append")
        assert result.success
        assert result.created == 1

        # append 模式下再次同步会再创建
        result2 = connector.sync_contacts(contacts, strategy="append")
        assert result2.success
        assert result2.created == 1

    def test_sync_contacts_replace(self, connector):
        """sync_contacts replace 模式工作正常。"""
        contacts = [
            ContactData(external_id="", name="用户D", email="userd@test.com"),
        ]
        result = connector.sync_contacts(contacts, strategy="replace")
        assert result.success

    def test_sync_contacts_invalid_strategy(self, connector, sample_contact):
        """不支持的 strategy 应记录错误。"""
        result = connector.sync_contacts([sample_contact], strategy="invalid")
        assert len(result.errors) > 0


@pytest.mark.skipif(not HAS_SF_ENV, reason="需要设置 Salesforce 环境变量")
class TestSalesforceConnectorReal:
    """Salesforce 真实 API 测试 (需要有效凭据)。"""

    @pytest.fixture
    def connector(self):
        c = SalesforceConnector()
        c.authenticate()
        assert c.mode == "real", "应使用真实模式"
        return c

    def test_authenticate_real_mode(self, connector):
        """真实认证应成功。"""
        assert connector.is_authenticated
        assert connector.mode == "real"

    def test_health_check(self, connector):
        """真实健康检查应返回有效状态。"""
        hc = connector.health_check()
        assert hc["status"] in ("ok", "error")
        assert hc["provider"] == "salesforce"
        assert hc["mode"] == "real"


# ══════════════════════════════════════════════════════════════════════
# HubSpotConnector 测试
# ══════════════════════════════════════════════════════════════════════


class TestHubSpotConnectorStub:
    """HubSpot 存根降级模式测试。"""

    @pytest.fixture(autouse=True)
    def _clean_env(self, monkeypatch):
        monkeypatch.delenv("HUBSPOT_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("HUBSPOT_BASE_URL", raising=False)

    @pytest.fixture
    def connector(self):
        c = HubSpotConnector()
        c.authenticate()
        assert c.mode == "stub", "应自动降级为存根模式"
        return c

    def test_authenticate_stub_mode(self, connector):
        assert connector.is_authenticated
        assert connector.mode == "stub"

    def test_health_check(self, connector):
        hc = connector.health_check()
        assert hc["status"] == "ok"
        assert hc["mode"] == "stub"
        assert hc["provider"] == "hubspot"

    def test_create_and_get_contact(self, connector, sample_contact):
        result = connector.create_contact(sample_contact)
        assert result.success
        assert result.created == 1
        assert sample_contact.external_id != ""

        fetched = connector.get_contact(sample_contact.external_id)
        assert fetched is not None
        assert fetched.email == sample_contact.email

    def test_get_contact_not_found(self, connector):
        fetched = connector.get_contact("NONEXISTENT-ID")
        assert fetched is None

    def test_update_contact(self, connector, sample_contact, sample_contact_update):
        connector.create_contact(sample_contact)
        ext_id = sample_contact.external_id

        sample_contact_update.external_id = ext_id
        result = connector.update_contact(sample_contact_update)
        assert result.success
        assert result.updated == 1

        fetched = connector.get_contact(ext_id)
        assert fetched is not None
        assert fetched.name == sample_contact_update.name

    def test_search_contacts(self, connector):
        contacts = [
            ContactData(external_id="", name="张三", email="zhangsan@hs-test.com"),
            ContactData(external_id="", name="李四", email="lisi@hs-test.com"),
        ]
        for c in contacts:
            connector.create_contact(c)

        results = connector.search_contacts("张三")
        assert len(results) >= 1

    def test_delete_contact(self, connector, sample_contact):
        connector.create_contact(sample_contact)
        ext_id = sample_contact.external_id

        result = connector.delete_contact(ext_id)
        assert result.success
        assert result.deleted == 1

        fetched = connector.get_contact(ext_id)
        assert fetched is None

    def test_sync_contacts_upsert(self, connector):
        contacts = [
            ContactData(external_id="", name="用户A", email="usera@hs-test.com"),
            ContactData(external_id="", name="用户B", email="userb@hs-test.com"),
        ]
        result = connector.sync_contacts(contacts, strategy="upsert")
        assert result.success
        assert result.created == 2

        contacts[0].name = "用户A-更新"
        result2 = connector.sync_contacts(contacts, strategy="upsert")
        assert result2.success
        assert result2.updated == 2


@pytest.mark.skipif(not HAS_HS_ENV, reason="需要设置 HUBSPOT_ACCESS_TOKEN")
class TestHubSpotConnectorReal:
    """HubSpot 真实 API 测试 (需要有效凭据)。"""

    @pytest.fixture
    def connector(self):
        c = HubSpotConnector()
        c.authenticate()
        assert c.mode == "real", "应使用真实模式"
        return c

    def test_authenticate_real_mode(self, connector):
        assert connector.is_authenticated
        assert connector.mode == "real"

    def test_health_check(self, connector):
        hc = connector.health_check()
        assert hc["status"] in ("ok", "error")
        assert hc["provider"] == "hubspot"
        assert hc["mode"] == "real"
