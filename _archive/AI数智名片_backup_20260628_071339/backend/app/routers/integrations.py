"""集成管理 API — CRM (HubSpot/Salesforce) + Webhook 集成的 CRUD 与操作端点。"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.integration import Integration
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.crm_bridge import crm_bridge
from app.services.crm_hubspot import HubSpotProvider
from app.services.crm_salesforce import SalesforceProvider

router = APIRouter(prefix="/api/integrations", tags=["集成管理"])

# ── Schemas ──────────────────────────────────────────────────────────────────────


class IntegrationCreate(BaseModel):
    provider: str = Field(..., pattern=r"^(hubspot|salesforce|webhook)$")
    name: str = Field(default="", max_length=128)
    config: dict[str, Any] = Field(default_factory=dict)
    webhook_url: str = Field(default="", max_length=512)
    webhook_secret: str = Field(default="", max_length=128)
    webhook_enabled: bool = False
    enabled: bool = False


class IntegrationUpdate(BaseModel):
    name: str | None = None
    config: dict[str, Any] | None = None
    webhook_url: str | None = None
    webhook_secret: str | None = None
    webhook_enabled: bool | None = None
    enabled: bool | None = None


class IntegrationResponse(BaseModel):
    id: int
    user_id: int
    provider: str
    name: str
    enabled: bool
    config: dict[str, Any]
    webhook_url: str
    webhook_secret: str
    webhook_enabled: bool
    last_sync_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExportContactRequest(BaseModel):
    contact_data: dict[str, Any] = Field(
        default_factory=lambda: {
            "name": "",
            "email": "",
            "phone": "",
            "company": "",
            "title": "",
            "status": "NEW",
        }
    )


# ── 辅助函数 ────────────────────────────────────────────────────────────────────


def _build_provider(integration: Integration, db_provider: str) -> Any | None:
    """根据数据库中的集成记录动态构建 CRM Provider 实例。"""
    config = integration.get_config_dict()
    if db_provider == "hubspot":
        p = HubSpotProvider()
        p.configure(config)
        return p
    elif db_provider == "salesforce":
        p = SalesforceProvider()
        p.configure(config)
        return p
    return None


# ── CRUD 端点 ───────────────────────────────────────────────────────────────────


@router.get("", response_model=list[IntegrationResponse])
async def list_integrations(
    provider: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的所有集成配置。"""
    stmt = select(Integration).where(Integration.user_id == current_user.id)
    if provider:
        stmt = stmt.where(Integration.provider == provider)
    stmt = stmt.order_by(Integration.created_at.desc())
    result = await db.execute(stmt)
    integrations = result.scalars().all()
    return [
        IntegrationResponse(
            **{k: v for k, v in i.__dict__.items() if k != "_sa_instance_state"},
            config=i.get_config_dict(),
        )
        for i in integrations
    ]


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个集成配置详情。"""
    integration = await _get_owned_integration(db, integration_id, current_user.id)
    return IntegrationResponse(
        **{k: v for k, v in integration.__dict__.items() if k != "_sa_instance_state"},
        config=integration.get_config_dict(),
    )


@router.post("", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    data: IntegrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新的集成配置。"""
    # 检查同类型集成是否已存在
    existing_stmt = select(Integration).where(
        Integration.user_id == current_user.id,
        Integration.provider == data.provider,
    )
    existing = (await db.execute(existing_stmt)).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{data.provider} 集成已存在，请勿重复创建",
        )

    integration = Integration(
        user_id=current_user.id,
        provider=data.provider,
        name=data.name or data.provider,
        enabled=data.enabled,
        webhook_url=data.webhook_url,
        webhook_secret=data.webhook_secret,
        webhook_enabled=data.webhook_enabled,
    )
    integration.set_config_dict(data.config)
    db.add(integration)
    await db.commit()
    await db.refresh(integration)

    # 如果是 CRM 类型且启用了，注册到全局桥接
    if data.enabled and data.provider in ("hubspot", "salesforce"):
        _register_to_bridge(integration)

    return IntegrationResponse(
        **{k: v for k, v in integration.__dict__.items() if k != "_sa_instance_state"},
        config=integration.get_config_dict(),
    )


@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: int,
    data: IntegrationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新集成配置。"""
    integration = await _get_owned_integration(db, integration_id, current_user.id)

    update_fields = data.model_dump(exclude_unset=True)
    if "config" in update_fields:
        integration.set_config_dict(update_fields.pop("config"))
    for field, value in update_fields.items():
        setattr(integration, field, value)

    await db.commit()
    await db.refresh(integration)

    # 如果启用了 CRM 类型，注册到桥接
    if integration.enabled and integration.provider in ("hubspot", "salesforce"):
        _register_to_bridge(integration)

    return IntegrationResponse(
        **{k: v for k, v in integration.__dict__.items() if k != "_sa_instance_state"},
        config=integration.get_config_dict(),
    )


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除集成配置。"""
    integration = await _get_owned_integration(db, integration_id, current_user.id)
    await db.delete(integration)
    await db.commit()
    return None


# ── 操作端点 ────────────────────────────────────────────────────────────────────


@router.post("/{integration_id}/test", response_model=dict[str, Any])
async def test_integration(
    integration_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """测试集成连接是否有效。"""
    integration = await _get_owned_integration(db, integration_id, current_user.id)
    if integration.provider == "webhook":
        return {"success": True, "message": "Webhook 无需连接测试，请发送测试事件验证"}

    provider = _build_provider(integration, integration.provider)
    if not provider:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {integration.provider}")

    ok = await provider.test_connection()
    return {"success": ok, "provider": integration.provider}


@router.post("/{integration_id}/export", response_model=dict[str, Any])
async def export_contact(
    integration_id: int,
    data: ExportContactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """将联系人导出到指定的 CRM 集成。"""
    integration = await _get_owned_integration(db, integration_id, current_user.id)
    if not integration.enabled:
        raise HTTPException(status_code=400, detail="集成未启用")

    if integration.provider == "webhook":
        return await _trigger_webhook(integration, data.contact_data)

    provider = _build_provider(integration, integration.provider)
    if not provider:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {integration.provider}")

    try:
        result = await provider.export_contact(data.contact_data)
        # 更新同步时间
        integration.last_sync_at = datetime.utcnow()
        await db.commit()
        return {"success": True, "provider": integration.provider, "data": result}
    except Exception as e:
        return {"success": False, "provider": integration.provider, "error": str(e)}


@router.post("/export-all", response_model=dict[str, Any])
async def export_to_all_enabled(
    data: ExportContactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """将联系人导出到当前用户所有已启用的 CRM 集成。"""
    stmt = select(Integration).where(
        Integration.user_id == current_user.id,
        Integration.enabled.is_(True),
    )
    result = await db.execute(stmt)
    integrations = result.scalars().all()

    if not integrations:
        raise HTTPException(status_code=404, detail="没有已启用的集成")

    results: dict[str, Any] = {}
    for integration in integrations:
        if integration.provider == "webhook":
            results["webhook"] = await _trigger_webhook(integration, data.contact_data)
        else:
            provider = _build_provider(integration, integration.provider)
            if provider:
                try:
                    r = await provider.export_contact(data.contact_data)
                    results[integration.provider] = {"success": True, "data": r}
                    integration.last_sync_at = datetime.utcnow()
                except Exception as e:
                    results[integration.provider] = {"success": False, "error": str(e)}
    await db.commit()
    return results


# ── Webhook 处理 ────────────────────────────────────────────────────────────────


async def _trigger_webhook(
    integration: Integration, contact_data: dict[str, Any]
) -> dict[str, Any]:
    """向配置的 Webhook URL 发送联系人数据。"""
    if not integration.webhook_url:
        return {"success": False, "error": "Webhook URL 未配置"}
    if not integration.webhook_enabled:
        return {"success": False, "error": "Webhook 未启用"}

    import hashlib
    import hmac
    import json

    import httpx

    payload = json.dumps(contact_data, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    # 签名
    if integration.webhook_secret:
        signature = hmac.new(
            integration.webhook_secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()
        headers["X-Webhook-Signature"] = signature

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                integration.webhook_url, content=payload, headers=headers
            )
            return {
                "success": resp.status_code < 500,
                "status_code": resp.status_code,
                "provider": "webhook",
            }
    except Exception as e:
        return {"success": False, "error": str(e), "provider": "webhook"}


# ── 内部辅助 ────────────────────────────────────────────────────────────────────


async def _get_owned_integration(
    db: AsyncSession, integration_id: int, user_id: int
) -> Integration:
    """获取属于当前用户的集成配置，不存在则 404。"""
    stmt = select(Integration).where(
        Integration.id == integration_id,
        Integration.user_id == user_id,
    )
    result = await db.execute(stmt)
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="集成配置不存在")
    return integration


def _register_to_bridge(integration: Integration) -> None:
    """将集成注册到全局 CRM Bridge。"""
    provider = _build_provider(integration, integration.provider)
    if provider:
        crm_bridge.register(provider)
