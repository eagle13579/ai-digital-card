"""DirectAIGateway — AIGatewayProtocol adapter that calls DeepSeek API directly.

Wraps the DeepSeek chat completion and embedding APIs via async HTTP (httpx).
Includes:
    - chat() for standard completions
    - stream_chat() for streaming token-by-token responses
    - embed() for vector embeddings
    - Basic retry logic (3 attempts with exponential backoff)
    - Graceful fallback: returns error message on failure
    - Metrics tracking (latency, tokens, cost estimate)
"""

from __future__ import annotations

import asyncio
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
from app.ai.token_pricing import calculate_cost, classify_model, USD_TO_CNY
from app.config import settings

logger = logging.getLogger(__name__)

# ── DeepSeek API endpoints ───────────────────────────────────────────────
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_EMBED_URL = "https://api.deepseek.com/v1/embeddings"

MAX_RETRIES = 3
BASE_BACKOFF_SEC = 1.0

# ── User-facing fallback messages (Chinese) ────────────────────────────
FALLBACK_MESSAGE = (
    "抱歉，AI 服务暂时不可用，请稍后再试。"
    "（DeepSeek API 连接失败，所有重试均已耗尽）"
)

FALLBACK_STREAM_MESSAGE = (
    "抱歉，AI 服务暂时不可用，请稍后再试。"
    "（DeepSeek API 流式连接失败）"
)

FALLBACK_EMBED_MESSAGE = (
    "Embedding 服务暂时不可用，请稍后再试。"
    "（DeepSeek Embedding API 连接失败）"
)

CACHED_FALLBACK_PREFIX = "（以下为缓存的上次成功结果 — API 当前不可用）\n\n"


class DirectAIGateway(AIGatewayProtocol):
    """Direct HTTP AI Gateway — calls DeepSeek API (or compatible) directly.

    Uses ``httpx.AsyncClient`` for all HTTP communication.  API key is
    read from ``settings.DEEPSEEK_API_KEY``.

    Retry behaviour:
        - On 429 (rate limit), 502, 503, 504 → retry up to 3 times
        - Exponential backoff: 1s, 2s, 4s
        - Other errors are returned immediately as failure responses

    Fallback behaviour (single-point-of-failure protection):
        - Stores the last successful response in-memory
        - On failure after all retries, returns the cached last response
          (prefixed with a note) if available, or a polite fallback message.
        - Prevents 500 crashes when DeepSeek API is unreachable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        """Initialise the DeepSeek gateway.

        Args:
            api_key: DeepSeek API key.  Falls back to
                ``settings.DEEPSEEK_API_KEY`` or ``settings.EMBEDDING_API_KEY``.
            base_url: Base URL for DeepSeek API.  Falls back to
                ``settings.DEEPSEEK_API_URL``.
            timeout: Default HTTP request timeout in seconds.
            max_retries: Number of retry attempts for retriable failures.
        """
        self._api_key = api_key or settings.DEEPSEEK_API_KEY or settings.EMBEDDING_API_KEY
        self._base_url = (base_url or settings.DEEPSEEK_API_URL or DEEPSEEK_CHAT_URL).rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries

        # ── Metrics accumulator (in-memory, reset on restart) ────────
        self.metrics: dict[str, Any] = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "total_latency_ms": 0.0,
            "errors": 0,
            "fallbacks_served": 0,
        }

        # ── Last-successful-response cache (in-memory fallback) ──────
        # Stores the most recent successful response per method.
        # Used as a degraded-fallback when the API is unreachable.
        self._last_successful: dict[str, Any] = {
            "chat": None,       # AIResponse | None
            "stream_chat": "",  # str (full content)
            "embed": None,      # EmbeddingResponse | None
        }

        self._client: httpx.AsyncClient | None = None

    # ── HTTP client lifecycle ─────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init an httpx AsyncClient (reused across calls)."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ── AIGatewayProtocol ─────────────────────────────────────────────

    async def chat(self, request: AIRequest) -> AIResponse:
        """Send a chat completion request to DeepSeek.

        Returns an AIResponse with generated content and metadata.
        On failure returns an AIResponse with an error message in content.
        """
        start = time.monotonic()
        self.metrics["total_requests"] += 1

        payload = self._build_chat_payload(request)
        url = self._chat_url()

        last_error: str | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                client = await self._get_client()
                response = await client.post(url, json=payload)

                if response.is_success:
                    data = response.json()
                    elapsed_ms = (time.monotonic() - start) * 1000.0

                    # Parse response
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
                    cost = calculate_cost(
                        "external", model_used, prompt_tokens, completion_tokens
                    )["token_cost"]

                    # Update metrics
                    self.metrics["total_tokens"] += total_tokens
                    self.metrics["total_cost"] += cost
                    self.metrics["total_latency_ms"] += elapsed_ms

                    # ── Cache last successful response for fallback ──
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

                # Handle retriable status codes
                if response.status_code in (429, 502, 503, 504):
                    wait = BASE_BACKOFF_SEC * (2 ** (attempt - 1))
                    logger.warning(
                        "DeepSeek API returned %d (attempt %d/%d). "
                        "Retrying in %.1fs...",
                        response.status_code,
                        attempt,
                        self._max_retries,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    continue

                # Non-retriable error → return fallback
                last_error = f"HTTP {response.status_code}: {response.text}"
                self.metrics["errors"] += 1
                return self._fallback_chat_response(request, last_error, start)

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                wait = BASE_BACKOFF_SEC * (2 ** (attempt - 1))
                logger.warning(
                    "DeepSeek API connection error (attempt %d/%d): %s. "
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
                logger.exception("Unexpected error calling DeepSeek chat API")
                self.metrics["errors"] += 1
                return self._fallback_chat_response(request, str(exc), start)

        # All retries exhausted → return fallback
        self.metrics["errors"] += 1
        return self._fallback_chat_response(request, last_error or "unknown error", start)

    async def stream_chat(
        self,
        request: AIRequest,
    ) -> AsyncIterator[str]:
        """Streaming chat completion — yields content tokens as they arrive.

        The caller iterates over this async generator to receive tokens.
        The final yielded value is always the full concatenated response.

        On error, yields an error message and stops.
        """
        request = self._ensure_streaming(request)
        payload = self._build_chat_payload(request)
        url = self._chat_url()

        client = await self._get_client()
        full_content = ""
        attempt = 0

        while attempt < self._max_retries:
            attempt += 1
            try:
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
                        # All retries exhausted — serve cached or fallback
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
                        import json
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            token = delta.get("content", "")
                            if token:
                                full_content += token
                                yield token
                        except json.JSONDecodeError:
                            continue

                    # Stream completed successfully — cache full content
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
                    # All retries exhausted — serve cached or fallback
                    if self._last_successful["stream_chat"]:
                        note = "（以下为缓存的上次成功结果 — API 当前不可用）\n\n"
                        yield note
                        yield self._last_successful["stream_chat"]
                    else:
                        yield FALLBACK_STREAM_MESSAGE
                    return
            except Exception as exc:
                logger.exception("Unexpected error in stream_chat")
                # Serve cached or fallback
                if self._last_successful["stream_chat"]:
                    note = "（以下为缓存的上次成功结果 — API 当前不可用）\n\n"
                    yield note
                    yield self._last_successful["stream_chat"]
                else:
                    yield FALLBACK_STREAM_MESSAGE
                return

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate vector embeddings via DeepSeek embedding API.

        Falls back to returning an empty embedding list on failure.
        """
        start = time.monotonic()
        self.metrics["total_requests"] += 1

        payload = {
            "model": request.model,
            "input": request.texts,
        }
        url = self._embed_url()

        last_error: str | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                client = await self._get_client()
                response = await client.post(url, json=payload)

                if response.is_success:
                    data = response.json()
                    elapsed_ms = (time.monotonic() - start) * 1000.0

                    embeddings = [item["embedding"] for item in data["data"]]
                    dimension = len(embeddings[0]) if embeddings else 0
                    model_used = data.get("model", request.model)
                    usage = data.get("usage", {})
                    total_tokens = usage.get("total_tokens", 0)

                    self.metrics["total_tokens"] += total_tokens
                    self.metrics["total_latency_ms"] += elapsed_ms

                    # ── Cache last successful embedding for fallback ──
                    embed_response = EmbeddingResponse(
                        embeddings=embeddings,
                        model=model_used,
                        dimension=dimension,
                        usage={
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "total_tokens": total_tokens,
                        },
                        latency_ms=elapsed_ms,
                    )
                    self._last_successful["embed"] = embed_response

                    return embed_response

                if response.status_code in (429, 502, 503, 504):
                    wait = BASE_BACKOFF_SEC * (2 ** (attempt - 1))
                    logger.warning(
                        "DeepSeek embed API %d (attempt %d/%d). Retrying in %.1fs...",
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
                return self._fallback_embed_response(request, last_error, start)

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                wait = BASE_BACKOFF_SEC * (2 ** (attempt - 1))
                logger.warning(
                    "DeepSeek embed connection error (attempt %d/%d): %s. "
                    "Retrying...",
                    attempt,
                    self._max_retries,
                    exc,
                )
                await asyncio.sleep(wait)
                last_error = str(exc)
                continue
            except Exception as exc:
                logger.exception("Unexpected error calling DeepSeek embed API")
                self.metrics["errors"] += 1
                return self._fallback_embed_response(request, str(exc), start)

        self.metrics["errors"] += 1
        return self._fallback_embed_response(request, last_error or "unknown error", start)

    # ── Internals ─────────────────────────────────────────────────────

    def _build_chat_payload(self, request: AIRequest) -> dict[str, Any]:
        """Build the JSON payload for a DeepSeek chat completion request."""
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

    def _chat_url(self) -> str:
        """Return the chat completion endpoint URL."""
        if "/chat/completions" in self._base_url:
            return self._base_url
        return f"{self._base_url}/chat/completions"

    def _embed_url(self) -> str:
        """Return the embeddings endpoint URL."""
        if "/embeddings" in self._base_url:
            return self._base_url.replace("/chat/completions", "/embeddings")
        return f"{self._base_url}/embeddings"

    @staticmethod
    def _ensure_streaming(request: AIRequest) -> AIRequest:
        """Force streaming to be enabled for stream_chat."""
        import dataclasses
        return dataclasses.replace(request, stream=True)

    @staticmethod
    def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost in ¥ (CNY) via centralized token pricing engine."""
        result = calculate_cost(
            "external", model, prompt_tokens, completion_tokens
        )
        return round(result["token_cost"], 6)

    # ── Fallback helpers ──────────────────────────────────────────────

    def _fallback_chat_response(
        self,
        request: AIRequest,
        error: str,
        start: float,
    ) -> AIResponse:
        """Return a degraded fallback AIResponse when DeepSeek API fails.

        Strategy:
            1. If a previous successful response exists → return it prefixed
               with a notice that cached content is being shown.
            2. Otherwise → return a polite Chinese fallback message.
        """
        self.metrics["fallbacks_served"] += 1
        elapsed_ms = (time.monotonic() - start) * 1000.0

        cached = self._last_successful.get("chat")
        if cached is not None:
            logger.warning(
                "DeepSeek API unavailable — serving cached chat response. "
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
            "DeepSeek API unavailable and no cached response — "
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

    def _fallback_embed_response(
        self,
        request: EmbeddingRequest,
        error: str,
        start: float,
    ) -> EmbeddingResponse:
        """Return a degraded fallback EmbeddingResponse when DeepSeek API fails.

        Strategy:
            1. If a previous successful embedding exists → return it.
            2. Otherwise → return an empty embedding list.
        """
        self.metrics["fallbacks_served"] += 1
        elapsed_ms = (time.monotonic() - start) * 1000.0

        cached = self._last_successful.get("embed")
        if cached is not None:
            logger.warning(
                "DeepSeek embed API unavailable — serving cached embedding. "
                "Error: %s",
                error,
            )
            return EmbeddingResponse(
                embeddings=cached.embeddings,
                model=cached.model,
                dimension=cached.dimension,
                usage=cached.usage,
                latency_ms=elapsed_ms,
            )

        logger.error(
            "DeepSeek embed API unavailable and no cached embedding — "
            "returning empty response. Error: %s",
            error,
        )
        return EmbeddingResponse(
            embeddings=[],
            model=request.model,
            dimension=0,
            usage={},
            latency_ms=elapsed_ms,
        )
