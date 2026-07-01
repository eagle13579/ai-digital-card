"""Connectors — 外部CRM集成适配器接口。

包含:
- CrmBase:           抽象基类
- ContactData:       统一联系人数据模型
- SyncResult:        同步结果模型
- SalesforceConnector:  生产就绪 Salesforce 连接器 (含自动存根降级)
- HubSpotConnector:     生产就绪 HubSpot 连接器 (含自动存根降级)
- SalesforceStub:        Salesforce 存根 (直接使用)
- HubSpotStub:           HubSpot 存根 (直接使用)

环境变量就绪 → 真实 HTTP 调用。
环境变量缺失 → 自动降级到内存存根 (静默，无报错)。
"""

from .crm_base import CrmBase, ContactData, SyncResult
from .salesforce_connector import SalesforceConnector
from .hubspot_connector import HubSpotConnector
from .salesforce_stub import SalesforceStub
from .hubspot_stub import HubSpotStub

__all__ = [
    "CrmBase",
    "ContactData",
    "SyncResult",
    "SalesforceConnector",
    "HubSpotConnector",
    "SalesforceStub",
    "HubSpotStub",
]
