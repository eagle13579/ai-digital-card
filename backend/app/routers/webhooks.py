"""Webhook 订阅管理 API — CRUD + 事件触发。

与 backend/app/routers/integrations.py 中的 webhook 功能互补：
- integrations.py: 集成配置中的 webhook（CRM 导出时触发）
- webhooks.py: 独立的 webhook 事件订阅系统（可自定义事件类型）

签名验证说明 (供接收方参考):
  系统在发送 webhook 时会自动计算 HMAC-SHA256 签名并写入
  X-Webhook-Signature 请求头。接收方验证方式:

  ```python
  import hmac, hashlib

  body = await request.body()          # 原始请求体 bytes
  sig  = request.headers.get("X-Webhook-Signature", "")
  expected = hmac.new(
      secret.encode("utf-8"),          # secret = 创建订阅时设置的密钥
      body,
      hashlib.sha256,
  ).hexdigest()
  verified = hmac.compare_digest(expected, sig)
  ```

  密钥通过创建/更新 webhook 订阅时的 "secret" 字段设置。
  如未设置 secret，则不会生成签名头。
"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.webhook import WebhookSubscription
from app.routers.auth import get_current_user
from app.services.webhook_dispatcher import webhook_dispatcher

router = APIRouter(prefix="/api/webhooks", tags=["Webhook 订阅"])

# ── Schemas ──────────────────────────────────────────────────────────────

EVENT_TYPES = [
    "card.created",
    "card.updated",
    "card.deleted",
    "card.viewed",
    "contact.exported",
    "match.found",
    "user.updated",
    "webhook.test",
]


class WebhookCreate(BaseModel):
    name: str = Field(default="", max_length=128)
    url: str = Field(..., max_length=512, description="Webhook 回调 URL")
    secret: str = Field(default="", max_length=128, description="签名密钥")
    events: list[str] = Field(
        default=["card.created", "card.updated"],
        description="监听的事件类型列表",
    )
    active: bool = True
    retry_count: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=10, ge=1, le=60)


class WebhookUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    secret: str | None = None
    events: list[str] | None = None
    active: bool | None = None
    retry_count: int | None = None
    timeout_seconds: int | None = None


class WebhookResponse(BaseModel):
    id: int
    user_id: int
    name: str
    url: str
    secret: str
    events: list[str]
    active: bool
    retry_count: int
    timeout_seconds: int
    last_triggered_at: datetime | None = None
    last_response_code: int | None = None
    last_error: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_events(cls, sub: WebhookSubscription) -> "WebhookResponse":
        """从 ORM 对象构造响应，自动解析 events 字段。"""
        return cls(
            id=sub.id,
            user_id=sub.user_id,
            name=sub.name,
            url=sub.url,
            secret=sub.secret,
            events=sub.get_events_list(),
            active=sub.active,
            retry_count=sub.retry_count,
            timeout_seconds=sub.timeout_seconds,
            last_triggered_at=sub.last_triggered_at,
            last_response_code=sub.last_response_code,
            last_error=sub.last_error,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
        )


class WebhookTestEvent(BaseModel):
    event_type: str = Field(default="webhook.test", description="测试事件类型")
    data: dict[str, Any] = Field(
        default_factory=lambda: {"message": "This is a test event from AI数字名片"}
    )


# ── 辅助函数 ────────────────────────────────────────────────────────────


async def _get_owned_webhook(
    db: AsyncSession, webhook_id: int, user_id: int,
) -> WebhookSubscription:
    """获取属于当前用户的 webhook 订阅，不存在则 404。"""
    stmt = select(WebhookSubscription).where(
        WebhookSubscription.id == webhook_id,
        WebhookSubscription.user_id == user_id,
    )
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook 订阅不存在",
        )
    return sub


# ── CRUD 端点 ───────────────────────────────────────────────────────────


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(
    active: bool | None = Query(None, description="筛选启用状态"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的所有 Webhook 订阅。"""
    stmt = select(WebhookSubscription).where(
        WebhookSubscription.user_id == current_user.id,
    )
    if active is not None:
        stmt = stmt.where(WebhookSubscription.active == active)
    stmt = stmt.order_by(WebhookSubscription.created_at.desc())

    result = await db.execute(stmt)
    subs = result.scalars().all()
    return [WebhookResponse.from_orm_with_events(s) for s in subs]


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个 Webhook 订阅详情。"""
    sub = await _get_owned_webhook(db, webhook_id, current_user.id)
    return WebhookResponse.from_orm_with_events(sub)


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新的 Webhook 订阅。"""
    # 验证事件类型
    for event in data.events:
        if event not in EVENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的事件类型: {event}，可选: {', '.join(EVENT_TYPES)}",
            )

    sub = WebhookSubscription(
        user_id=current_user.id,
        name=data.name,
        url=data.url,
        secret=data.secret,
        active=data.active,
        retry_count=data.retry_count,
        timeout_seconds=data.timeout_seconds,
    )
    sub.set_events_list(data.events)

    db.add(sub)
    await db.commit()
    await db.refresh(sub)

    return WebhookResponse.from_orm_with_events(sub)


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    data: WebhookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新 Webhook 订阅配置。"""
    sub = await _get_owned_webhook(db, webhook_id, current_user.id)

    update_fields = data.model_dump(exclude_unset=True)
    if "events" in update_fields:
        events = update_fields.pop("events")
        # 验证事件类型
        for event in events:
            if event not in EVENT_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"不支持的事件类型: {event}，可选: {', '.join(EVENT_TYPES)}",
                )
        sub.set_events_list(events)

    for field, value in update_fields.items():
        setattr(sub, field, value)

    await db.commit()
    await db.refresh(sub)

    return WebhookResponse.from_orm_with_events(sub)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除 Webhook 订阅。"""
    sub = await _get_owned_webhook(db, webhook_id, current_user.id)
    await db.delete(sub)
    await db.commit()
    return None


# ── 事件触发端点 ────────────────────────────────────────────────────────


@router.post("/{webhook_id}/test", response_model=dict[str, Any])
async def test_webhook(
    webhook_id: int,
    data: WebhookTestEvent = WebhookTestEvent(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """向指定 Webhook 发送测试事件。"""
    sub = await _get_owned_webhook(db, webhook_id, current_user.id)
    if not sub.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook 已停用，请先启用后再测试",
        )

    from app.database import AsyncSessionLocal

    result = await webhook_dispatcher.dispatch(
        db_session_factory=AsyncSessionLocal,
        event_type=data.event_type,
        payload=data.data,
        user_id=current_user.id,
    )

    return {
        "success": any(r.get("success") for r in result),
        "results": result,
    }


@router.post("/trigger", response_model=dict[str, Any])
async def trigger_event(
    event_type: str = Query(..., description="事件类型"),
    payload: dict[str, Any] = Body(default_factory=dict, description="事件载荷"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发一个事件，分发给当前用户所有匹配的 Webhook 订阅。"""
    if event_type not in EVENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的事件类型: {event_type}，可选: {', '.join(EVENT_TYPES)}",
        )

    from app.database import AsyncSessionLocal

    results = await webhook_dispatcher.dispatch(
        db_session_factory=AsyncSessionLocal,
        event_type=event_type,
        payload=payload,
        user_id=current_user.id,
    )

    return {
        "event": event_type,
        "matched_subscriptions": len(results),
        "results": results,
    }


@router.get("/events/list", response_model=list[str])
async def list_event_types():
    """获取所有支持的事件类型。"""
    return EVENT_TYPES


# ── 投递日志端点 ─────────────────────────────────────────────────────────


@router.get("/{webhook_id}/logs", response_model=dict)
async def get_webhook_logs(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定 Webhook 的投递日志（指数退避重试记录）。

    返回该 webhook URL 关联的所有重试历史及最终错误信息。
    """
    sub = await _get_owned_webhook(db, webhook_id, current_user.id)
    return webhook_dispatcher.stats.get(sub.url, {"retries": [], "last_error": ""})
