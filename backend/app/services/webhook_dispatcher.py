"""Webhook 事件分发服务：
- 根据事件类型查找所有匹配的活跃订阅
- 异步发送 HTTP POST 请求（带 HMAC-SHA256 签名）
- 支持重试机制
- 记录触发状态
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger("webhook_dispatcher")


class WebhookDispatcher:
    """Webhook 事件分发器"""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self.stats: dict[str, dict] = {}

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def dispatch(
        self,
        db_session_factory,
        event_type: str,
        payload: dict[str, Any],
        user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """分发事件到所有匹配的活跃 webhook 订阅。

        参数:
            db_session_factory: 异步数据库会话工厂（async_sessionmaker）
            event_type: 事件类型，如 "card.created"
            payload: 事件载荷数据
            user_id: 可选，限定仅发送给指定用户的订阅

        返回:
            每个发送结果的列表
        """
        from app.models.webhook import WebhookSubscription
        from sqlalchemy import select

        results: list[dict[str, Any]] = []

        # 查找匹配的订阅
        async with db_session_factory() as db:
            stmt = select(WebhookSubscription).where(
                WebhookSubscription.active.is_(True),
            )
            if user_id is not None:
                stmt = stmt.where(WebhookSubscription.user_id == user_id)
            result = await db.execute(stmt)
            subscriptions = result.scalars().all()

        # 过滤出监听该事件类型的订阅
        matched = [
            sub for sub in subscriptions
            if event_type in sub.get_events_list()
        ]

        if not matched:
            logger.debug("事件 %s 无匹配 webhook 订阅", event_type)
            return results

        client = await self.get_client()
        event_payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": payload,
        }

        for sub in matched:
            result = await self._send_single(
                client, sub, event_payload, db_session_factory
            )
            results.append(result)

        return results

    async def _send_single(
        self,
        client: httpx.AsyncClient,
        subscription: "WebhookSubscription",  # noqa: F821
        payload: dict[str, Any],
        db_session_factory,
    ) -> dict[str, Any]:
        """发送单个 webhook 并记录结果。"""
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": payload.get("event", ""),
        }

        # HMAC-SHA256 签名（使用 webhook_signer 服务）
        if subscription.secret:
            from app.services.webhook_signer import sign as _sign
            signature = _sign(body, subscription.secret)
            headers["X-Webhook-Signature"] = signature

        last_error = ""
        last_code: int | None = None
        success = False

        # 指数退避重试逻辑 (最多重试5次: 1s/2s/4s/8s/16s)
        max_retries = 5
        delays = [2 ** i for i in range(max_retries)]  # [1, 2, 4, 8, 16]

        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    await asyncio.sleep(delays[attempt - 2])
                resp = await client.post(
                    subscription.url,
                    content=body,
                    headers=headers,
                    timeout=subscription.timeout_seconds,
                )
                last_code = resp.status_code
                if resp.status_code < 500:
                    success = True
                else:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "Webhook %s 发送失败 (尝试 %d/%d): %s",
                    subscription.url, attempt, max_retries, e,
                )

            # 记录每次尝试到 stats (成功/失败均记录)
            url = subscription.url
            if url not in self.stats:
                self.stats[url] = {"retries": [], "last_error": ""}
            self.stats[url]["retries"].append({
                "attempt": attempt,
                "delay_s": delays[attempt - 2] if attempt > 1 else 0,
                "error": last_error,
                "status_code": last_code,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })

            if success:
                break

        # 最终失败写入 last_error
        if not success:
            url = subscription.url
            if url not in self.stats:
                self.stats[url] = {"retries": [], "last_error": ""}
            self.stats[url]["last_error"] = last_error

        # 更新订阅记录
        async with db_session_factory() as db:
            from sqlalchemy import select
            from app.models.webhook import WebhookSubscription

            stmt = select(WebhookSubscription).where(
                WebhookSubscription.id == subscription.id
            )
            result = await db.execute(stmt)
            sub = result.scalar_one_or_none()
            if sub:
                sub.last_triggered_at = datetime.utcnow()
                sub.last_response_code = last_code
                sub.last_error = last_error
                await db.commit()

        return {
            "subscription_id": subscription.id,
            "url": subscription.url,
            "event": payload.get("event", ""),
            "success": success,
            "status_code": last_code,
            "error": last_error,
        }

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


# 全局单例
webhook_dispatcher = WebhookDispatcher()
