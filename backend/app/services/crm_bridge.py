"""CRM 抽象层 — 定义统一的 CRM 集成接口、桥接注册中心与同步调度函数。

提供两种使用模式:
  1. CRMBridge (async class-based) — 配合 Provider 类实例注册使用
  2. dispatch (sync function) — 根据 integration 类型直接路由到对应的 sync 函数
"""
from abc import ABC, abstractmethod
from typing import Any

import requests


# ══════════════════════════════════════════════════════════════════════════
# 抽象基类（供 async class 模式使用）
# ══════════════════════════════════════════════════════════════════════════


class CRMProvider(ABC):
    """CRM 提供商抽象基类。所有具体集成（HubSpot / Salesforce）需实现此接口。"""

    @abstractmethod
    async def export_contact(self, contact_data: dict[str, Any]) -> dict[str, Any]:
        """导出联系人到 CRM。返回 CRM 侧联系人 ID / URL 等信息。"""
        ...

    @abstractmethod
    async def update_contact(
        self, contact_id: str, contact_data: dict[str, Any]
    ) -> dict[str, Any]:
        """更新 CRM 中已有联系人。"""
        ...

    @abstractmethod
    async def delete_contact(self, contact_id: str) -> bool:
        """从 CRM 删除联系人。"""
        ...

    @abstractmethod
    async def get_contact(self, contact_id: str) -> dict[str, Any] | None:
        """查询 CRM 联系人详情。"""
        ...

    @abstractmethod
    async def test_connection(self) -> bool:
        """测试与 CRM 的连接是否有效（校验 Token / API Key）。"""
        ...

    @abstractmethod
    async def get_provider_name(self) -> str:
        """返回提供商名称标识（如 'hubspot' / 'salesforce'）。"""
        ...


class CRMBridge:
    """CRM 桥接注册中心 — 管理所有已注册的 CRM Provider。"""

    def __init__(self) -> None:
        self._providers: dict[str, CRMProvider] = {}

    def register(self, provider: CRMProvider) -> None:
        """注册一个 CRM Provider 实例。"""
        name = provider.get_provider_name()
        self._providers[name] = provider

    def get(self, name: str) -> CRMProvider | None:
        """按名称获取已注册的 CRM Provider。"""
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        """列出所有已注册的提供商名称。"""
        return list(self._providers.keys())

    async def export_to_all(
        self, contact_data: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """将联系人批量导出到所有已注册且可用的 CRM。返回 {provider_name: result}。"""
        results: dict[str, dict[str, Any]] = {}
        for name, provider in self._providers.items():
            try:
                result = await provider.export_contact(contact_data)
                results[name] = {"success": True, "data": result}
            except Exception as e:
                results[name] = {"success": False, "error": str(e)}
        return results

    async def health_check_all(self) -> dict[str, bool]:
        """检测所有注册 CRM 的连接状态。"""
        status: dict[str, bool] = {}
        for name, provider in self._providers.items():
            try:
                status[name] = await provider.test_connection()
            except Exception:
                status[name] = False
        return status


# ── 全局单例（供 async class 模式使用） ──────────────────────────────────
crm_bridge = CRMBridge()


# ══════════════════════════════════════════════════════════════════════════
# 同步调度函数 — 根据 integration 类型路由到具体 provider 的 sync 函数
# 适用于 FastAPI endpoint 中的简单同步调用
# ══════════════════════════════════════════════════════════════════════════


SUPPORTED_PROVIDERS = frozenset({"hubspot", "salesforce"})


def dispatch(
    integration_type: str,
    config: dict[str, Any],
    contact_data: dict[str, Any] | None = None,
    action: str = "test",
) -> dict[str, Any]:
    """根据集成类型调度到对应的 CRM sync 函数。

    Args:
        integration_type: 集成类型 — "hubspot" 或 "salesforce"
        config: CRM 配置字典
            - HubSpot: {"api_key": "..."} 或 {"access_token": "..."}
            - Salesforce: {"client_id": ..., "client_secret": ..., "username": ..., "password": ...}
                          或 {"access_token": ..., "instance_url": ...}
        contact_data: 联系人数据（仅 action="export" 时需要）
        action: 操作类型 — "test" 连接测试 | "export" 导出联系人

    Returns:
        test 返回: {"connected": True/False, "message": "..."}
        export 返回: {"success": True/False, "contact_id": "...", ...}

    Raises:
        ValueError: 不支持的集成类型或操作
    """
    if integration_type not in SUPPORTED_PROVIDERS:
        return {
            "success": False,
            "error": f"不支持的 CRM 集成类型: '{integration_type}'，支持的: {', '.join(sorted(SUPPORTED_PROVIDERS))}",
        }

    # 延迟导入，避免模块加载时产生循环依赖
    if integration_type == "hubspot":
        from app.services.crm_hubspot import test_connection as hs_test
        from app.services.crm_hubspot import export_contact as hs_export

        api_key = config.get("api_key") or config.get("access_token", "")
        if not api_key:
            return {"success": False, "error": "缺少 HubSpot API Key (api_key/access_token)"}

        if action == "test":
            return hs_test(api_key)
        elif action == "export":
            if contact_data is None:
                return {"success": False, "error": "export 操作需要 contact_data 参数"}
            return hs_export(api_key, contact_data)
        else:
            return {"success": False, "error": f"不支持的操作: '{action}'，仅支持 test/export"}

    elif integration_type == "salesforce":
        from app.services.crm_salesforce import test_connection as sf_test
        from app.services.crm_salesforce import export_contact as sf_export

        if action == "test":
            return sf_test(config)
        elif action == "export":
            if contact_data is None:
                return {"success": False, "error": "export 操作需要 contact_data 参数"}
            return sf_export(config, contact_data)
        else:
            return {"success": False, "error": f"不支持的操作: '{action}'，仅支持 test/export"}

    # 不会执行到这里（SUPPORTED_PROVIDERS 已检查）
    return {"success": False, "error": f"未知集成类型: {integration_type}"}
