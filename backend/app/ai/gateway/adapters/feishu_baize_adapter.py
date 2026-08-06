"""FeishuBaizeAdapter — AIGatewayProtocol adapter that calls Feishu Baize API.

Uses tenant_access_token for authentication via app_id + app_secret.
Implements the same AIGatewayProtocol interface as DirectAIGateway,
allowing seamless swapping between DeepSeek and Feishu Baize.

Authentication flow:
    1. POST /auth/v3/tenant_access_token/internal
       → Get tenant_access_token using app_id + app_secret
    2. Use token to call AI API: /ai/v1/chat/completions
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, AsyncIterator

import httpx

from app.ai.gateway.interfaces import (
    AIRequest,
    AIResponse,
    AIGatewayProtocol,
    EmbeddingRequest,
    EmbeddingResponse,
)
from app.config import settings

logger = logging.getLogger(__name__)

FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

MAX_RETRIES = 3
BASE_BACKOFF_SEC = 1.0

FALLBACK_MESSAGE = (
    "抱歉，AI 服务暂时不可用，请稍后再试。"
    "（飞书白泽 API 连接失败，所有重试均已耗尽）"
)

FALLBACK_STREAM_MESSAGE = (
    "抱歉，AI 服务暂时不可用，请稍后再试。"
    "（飞书白泽 API 流式连接失败）"
)

FALLBACK_EMBED_MESSAGE = (
    "Embedding 服务暂时不可用，请稍后再试。"
    "（飞书白泽 Embedding API 连接失败）"
)

CACHED_FALLBACK_PREFIX = "（以下为缓存的上次成功结果 — API 当前不可用）\n\n"


class FeishuBaizeAdapter(AIGatewayProtocol):
    """Feishu Baize AI Gateway adapter.

    Implements AIGatewayProtocol for calling Feishu Baize API.
    Uses tenant_access_token for authentication.
    """

    _tenant_token: str = ""
    _token_expires_at: float = 0.0

    def __init__(
        self,
        app_id: str | None = None,
        app_secret: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self._app_id = app_id or settings.FEISHU_APP_ID
        self._app_secret = app_secret or settings.FEISHU_APP_SECRET
        self._base_url = (base_url or settings.FEISHU_BAIZE_API_URL).rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries

        self.metrics: dict[str, Any] = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "total_latency_ms": 0.0,
            "errors": 0,
            "fallbacks_served": 0,
        }

        self._last_successful: dict[str, Any] = {
            "chat": None,
            "stream_chat": "",
            "embed": None,
        }

        self._client: httpx.AsyncClient | None = None

    async def _ensure_token(self) -> str:
        now = time.time()
        if self._tenant_token and now < self._token_expires_at - 60:
            return self._tenant_token

        payload = {
            "app_id": self._app_id,
            "app_secret": self._app_secret,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(FEISHU_TOKEN_URL, json=payload)
                response.raise_for_status()
                result = response.json()
            except httpx.HTTPStatusError as e:
                logger.error("飞书 token 获取失败: %s", e.response.text)
                raise
            except Exception as e:
                logger.error("飞书 token 请求异常: %s", e)
                raise

        self._tenant_token = result.get("tenant_access_token", "")
        expire = result.get("expire", 7200)
        self._token_expires_at = now + expire
        logger.debug("飞书 tenant_access_token 已刷新，有效 %s 秒", expire)
        return self._tenant_token

    async def _get_client(self) -> httpx.AsyncClient:
        token = await self._ensure_token()
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
            )
        else:
            self._client.headers["Authorization"] = f"Bearer {token}"
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def chat(self, request: AIRequest) -> AIResponse:
        start = time.monotonic()
        self.metrics["total_requests"] += 1

        payload = self._build_chat_payload(request)
        url = self._base_url

        last_error: str | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                client = await self._get_client()
                response = await client.post(url, json=payload)

                if response.is_success:
                    data = response.json()
                    elapsed_ms = (time.monotonic() - start) * 1000.0

                    choice = data["choices"][0]
                    message = choice.get("message", {})
                    content = message.get("content", "")
                    finish_reason = choice.get("finish_reason", "stop")
                    tool_calls = message.get("tool_calls")

                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
                    usage_dict = {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                    }

                    model_used = data.get("model", request.model)

                    self.metrics["total_tokens"] += total_tokens
                    self.metrics["total_latency_ms"] += elapsed_ms

                    response_obj = AIResponse(
                        content=content,
                        model=model_used,
                        usage=usage_dict,
                        latency_ms=elapsed_ms,
                        finish_reason=finish_reason,
                        tool_calls=tool_calls,
                        request_id=request.request_id,
                    )
                    self._last_successful["chat"] = response_obj

                    return response_obj

                if response.status_code in (429, 502, 503, 504):
                    wait = BASE_BACKOFF_SEC * (2 ** (attempt - 1))
                    logger.warning(
                        "飞书白泽 API returned %d (attempt %d/%d). "
                        "Retrying in %.1fs...",
                        response.status_code,
                        attempt,
                        self._max_retries,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    continue

                last_error = f"HTTP {response.status_code}: {response.text}"
                self.metrics["errors"] += 1
                return self._fallback_chat_response(request, last_error, start)

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                wait = BASE_BACKOFF_SEC * (2 ** (attempt - 1))
                logger.warning(
                    "飞书白泽 API connection error (attempt %d/%d): %s. "
                    "Retrying in %.1fs...",
                    attempt,
                    self._max_retries,
                    exc,
                    wait,
                )
                await asyncio.sleep(wait)
                last_error = str(exc)
                continue
            except Exception as exc:
                logger.exception("Unexpected error calling Feishu Baize chat API")
                self.metrics["errors"] += 1
                return self._fallback_chat_response(request, str(exc), start)

        self.metrics["errors"] += 1
        return self._fallback_chat_response(request, last_error or "unknown error", start)

    async def stream_chat(
        self,
        request: AIRequest,
    ) -> AsyncIterator[str]:
        request = self._ensure_streaming(request)
        payload = self._build_chat_payload(request)
        url = self._base_url

        full_content = ""
        attempt = 0

        while attempt < self._max_retries:
            attempt += 1
            try:
                client = await self._get_client()
                async with client.stream("POST", url, json=payload) as response:
                    if not response.is_success:
                        error_text = await response.aread()
                        logger.warning(
                            "Stream chat error (attempt %d/%d): %s",
                            attempt,
                            self._max_retries,
                            error_text,
                        )
                        if attempt < self._max_retries:
                            wait = BASE_BACKOFF_SEC * (2 ** (attempt - 1))
                            await asyncio.sleep(wait)
                            continue
                        if self._last_successful["stream_chat"]:
                            note = "（以下为缓存的上次成功结果 — API 当前不可用）\n\n"
                            yield note
                            yield self._last_successful["stream_chat"]
                        else:
                            yield FALLBACK_STREAM_MESSAGE
                        return

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            token = delta.get("content", "")
                            if token:
                                full_content += token
                                yield token
                        except json.JSONDecodeError:
                            continue

                    if full_content:
                        self._last_successful["stream_chat"] = full_content
                    return

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                logger.warning(
                    "Stream chat connection error (attempt %d/%d): %s",
                    attempt,
                    self._max_retries,
                    exc,
                )
                if attempt < self._max_retries:
                    wait = BASE_BACKOFF_SEC * (2 ** (attempt - 1))
                    await asyncio.sleep(wait)
                else:
                    if self._last_successful["stream_chat"]:
                        note = "（以下为缓存的上次成功结果 — API 当前不可用）\n\n"
                        yield note
                        yield self._last_successful["stream_chat"]
                    else:
                        yield FALLBACK_STREAM_MESSAGE
                    return
            except Exception as exc:
                logger.exception("Unexpected error in stream_chat")
                if self._last_successful["stream_chat"]:
                    note = "（以下为缓存的上次成功结果 — API 当前不可用）\n\n"
                    yield note
                    yield self._last_successful["stream_chat"]
                else:
                    yield FALLBACK_STREAM_MESSAGE
                return

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        start = time.monotonic()
        self.metrics["total_requests"] += 1

        logger.warning("飞书白泽 Embedding API 尚未实现，返回空响应")
        elapsed_ms = (time.monotonic() - start) * 1000.0

        cached = self._last_successful.get("embed")
        if cached is not None:
            return EmbeddingResponse(
                embeddings=cached.embeddings,
                model=cached.model,
                dimension=cached.dimension,
                usage=cached.usage,
                latency_ms=elapsed_ms,
            )

        return EmbeddingResponse(
            embeddings=[],
            model=request.model,
            dimension=0,
            usage={},
            latency_ms=elapsed_ms,
        )

    def _build_chat_payload(self, request: AIRequest) -> dict[str, Any]:
        messages: list[dict[str, str]] = []
        if request.prompt:
            messages.append({"role": "system", "content": request.prompt})
        messages.extend(request.messages)

        payload: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream,
        }

        if request.tools:
            payload["tools"] = request.tools
        if request.response_format:
            payload["response_format"] = request.response_format

        return payload

    @staticmethod
    def _ensure_streaming(request: AIRequest) -> AIRequest:
        import dataclasses
        return dataclasses.replace(request, stream=True)

    def _fallback_chat_response(
        self,
        request: AIRequest,
        error: str,
        start: float,
    ) -> AIResponse:
        self.metrics["fallbacks_served"] += 1
        elapsed_ms = (time.monotonic() - start) * 1000.0

        cached = self._last_successful.get("chat")
        if cached is not None:
            logger.warning(
                "飞书白泽 API unavailable — serving cached chat response. "
                "Error: %s",
                error,
            )
            return AIResponse(
                content=f"{CACHED_FALLBACK_PREFIX}{cached.content}",
                model=cached.model,
                usage=cached.usage,
                latency_ms=elapsed_ms,
                finish_reason="degraded_fallback",
                tool_calls=cached.tool_calls,
                request_id=request.request_id,
            )

        logger.error(
            "飞书白泽 API unavailable and no cached response — "
            "returning fallback message. Error: %s",
            error,
        )
        return AIResponse(
            content=FALLBACK_MESSAGE,
            model=request.model,
            usage={},
            latency_ms=elapsed_ms,
            finish_reason="error",
            request_id=request.request_id,
        )