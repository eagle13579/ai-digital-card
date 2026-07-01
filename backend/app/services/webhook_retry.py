"""
Webhook 重试队列服务
功能: send_with_retry(指数退避:10s/30s/60s/120s/300s), 死信队列, 手动重试
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger("webhook_retry")
RETRY_DELAYS = [10, 30, 60, 120, 300]
MAX_RETRIES = len(RETRY_DELAYS)


@dataclass
class DeadLetterEntry:
    id: int
    url: str
    payload: dict[str, Any]
    attempts: int
    last_error: str
    created_at: float
    last_attempt_at: float


class WebhookRetryService:
    def __init__(self) -> None:
        self._dead_letter_queue: dict[int, DeadLetterEntry] = {}
        self._next_id: int = 1
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def send_with_retry(
        self, url: str, payload: dict[str, Any],
        headers: dict[str, str] | None = None,
        secret: str | None = None,
    ) -> dict[str, Any]:
        """发送 webhook + 指数退避重试 (10/30/60/120/300s)

        参数:
            url:     目标 URL
            payload: 要发送的 JSON 数据
            headers: 额外 HTTP 头
            secret:  可选签名密钥，提供后将自动添加 X-Webhook-Signature 头 (HMAC-SHA256)
        """
        client = await self.get_client()
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req_headers = {"Content-Type": "application/json", **(headers or {})}

        # 自动签名
        if secret:
            from app.services.webhook_signer import sign as _sign
            req_headers["X-Webhook-Signature"] = _sign(body, secret)
        last_error, last_code, success = "", None, False

        for attempt in range(1, MAX_RETRIES + 1):
            if attempt > 1:
                await asyncio.sleep(RETRY_DELAYS[attempt - 2])
            try:
                resp = await client.post(url, content=body, headers=req_headers)
                last_code = resp.status_code
                if resp.status_code < 500:
                    success = True
                    break
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as e:
                last_error = str(e)
                logger.warning("Webhook %s attempt #%d: %s", url, attempt, e)

        if not success:
            return await self._move_to_dead_letter(url, payload, last_error, last_code)
        return {"success": True, "status_code": last_code, "error": "",
                "attempts": MAX_RETRIES, "dead_letter_id": None}

    async def _move_to_dead_letter(
        self, url: str, payload: dict[str, Any],
        error: str, status_code: int | None,
    ) -> dict[str, Any]:
        entry = DeadLetterEntry(
            id=self._next_id, url=url, payload=payload,
            attempts=MAX_RETRIES, last_error=error,
            created_at=time.time(), last_attempt_at=time.time(),
        )
        self._dead_letter_queue[self._next_id] = entry
        self._next_id += 1
        return {"success": False, "status_code": status_code, "error": error,
                "attempts": MAX_RETRIES, "dead_letter_id": entry.id}

    def get_dead_letter(self, dead_letter_id: int | None = None) -> list[dict[str, Any]]:
        if dead_letter_id is not None:
            entry = self._dead_letter_queue.get(dead_letter_id)
            return [self._entry_to_dict(entry)] if entry else []
        return [self._entry_to_dict(e) for e in sorted(
            self._dead_letter_queue.values(), key=lambda x: x.created_at)]

    def _entry_to_dict(self, entry: DeadLetterEntry) -> dict[str, Any]:
        return {"id": entry.id, "url": entry.url, "payload": entry.payload,
                "attempts": entry.attempts, "last_error": entry.last_error,
                "created_at": entry.created_at, "last_attempt_at": entry.last_attempt_at}

    async def retry_dead_letter(self, dead_letter_id: int) -> dict[str, Any]:
        entry = self._dead_letter_queue.get(dead_letter_id)
        if entry is None:
            return {"success": False, "status_code": None,
                    "error": f"Dead letter #{dead_letter_id} not found",
                    "attempts": 0, "dead_letter_id": None}
        del self._dead_letter_queue[dead_letter_id]
        result = await self.send_with_retry(entry.url, entry.payload)
        if result.get("success"):
            result["dead_letter_id"] = dead_letter_id
        return result

    def get_dead_letter_count(self) -> int:
        return len(self._dead_letter_queue)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
