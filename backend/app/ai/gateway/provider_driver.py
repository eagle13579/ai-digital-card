"""Provider Driver — Craft Agents Provider Driver pattern for multi-AI backend switching.

This module implements a lightweight DriverRegistry pattern that wraps existing
AIGatewayProtocol adapters (DeepSeek, OpenAI, Anthropic, etc.) into a unified
switching/routing layer. It does NOT modify any existing adapter code.

Usage:
    from app.ai.gateway.provider_driver import DriverRegistry, OpenAIDriver, AnthropicDriver

    registry = DriverRegistry()
    registry.register("openai", OpenAIDriver(api_key=...))
    registry.register("anthropic", AnthropicDriver(api_key=...))

    response = await registry.get_driver("openai").chat(request)
"""

from __future__ import annotations

import abc
import logging
from typing import Any

from app.ai.gateway.interfaces import AIRequest, AIResponse, AIGatewayProtocol

logger = logging.getLogger(__name__)


# ======================================================================
# Base Provider Driver
# ======================================================================


class ProviderDriver(abc.ABC):
    """Abstract base for an AI provider driver.

    Each ProviderDriver wraps an existing AIGatewayProtocol adapter and
    exposes a unified interface for chat and embedding operations.
    Drivers can be registered, switched, and tested at runtime.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable provider name (e.g. 'openai', 'anthropic')."""
        ...

    @property
    @abc.abstractmethod
    def display_name(self) -> str:
        """Display name for UI (e.g. 'OpenAI', 'Anthropic Claude')."""
        ...

    @abc.abstractmethod
    async def chat(self, request: AIRequest) -> AIResponse:
        """Send a chat completion request via this provider."""
        ...

    @abc.abstractmethod
    async def test_connection(self) -> dict[str, Any]:
        """Test connectivity to this provider's API.

        Returns:
            Dict with keys:
                - success: bool
                - latency_ms: float (if success)
                - error: str (if not success)
        """
        ...

    @abc.abstractmethod
    def get_config(self) -> dict[str, Any]:
        """Return current configuration metadata for this driver."""
        ...


# ======================================================================
# Concrete Drivers
# ======================================================================


class OpenAIDriver(ProviderDriver):
    """Provider Driver for OpenAI-compatible APIs (incl. DeepSeek)."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        default_model: str = "gpt-4o",
        adapter: AIGatewayProtocol | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._adapter = adapter  # Optional: use existing AIGatewayProtocol adapter
        self._connected: bool = False

    @property
    def name(self) -> str:
        return "openai"

    @property
    def display_name(self) -> str:
        return "OpenAI"

    async def chat(self, request: AIRequest) -> AIResponse:
        """Delegate chat to the underlying adapter or direct API."""
        if self._adapter is not None:
            return await self._adapter.chat(request)

        # Fallback: direct HTTP call via httpx
        import httpx

        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": request.model or self._default_model,
                "messages": request.messages or [
                    {"role": "system", "content": request.prompt},
                    {"role": "user", "content": request.prompt},
                ],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": False,
            }
            if request.tools:
                payload["tools"] = request.tools
            if request.response_format:
                payload["response_format"] = request.response_format

            import time
            start = time.monotonic()
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            elapsed_ms = (time.monotonic() - start) * 1000.0

            if resp.status_code != 200:
                raise ConnectionError(
                    f"OpenAI API error {resp.status_code}: {resp.text}"
                )

            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return AIResponse(
                content=choice["message"]["content"] or "",
                model=data["model"],
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                latency_ms=elapsed_ms,
                finish_reason=choice.get("finish_reason", "stop"),
                request_id=request.request_id,
            )

    async def test_connection(self) -> dict[str, Any]:
        """Test connection by listing models or sending a minimal request."""
        import time

        try:
            import httpx

            start = time.monotonic()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self._base_url}/models",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
            elapsed_ms = (time.monotonic() - start) * 1000.0

            if resp.status_code == 200:
                self._connected = True
                return {"success": True, "latency_ms": round(elapsed_ms, 1)}
            else:
                return {
                    "success": False,
                    "latency_ms": round(elapsed_ms, 1),
                    "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                }
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000.0 if "start" in dir() else 0.0
            return {
                "success": False,
                "latency_ms": round(elapsed_ms, 1),
                "error": str(exc),
            }

    def get_config(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "base_url": self._base_url,
            "default_model": self._default_model,
            "connected": self._connected,
            "has_adapter": self._adapter is not None,
        }


class AnthropicDriver(ProviderDriver):
    """Provider Driver for Anthropic Claude API."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.anthropic.com/v1",
        default_model: str = "claude-sonnet-4-20250514",
        adapter: AIGatewayProtocol | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._adapter = adapter
        self._connected: bool = False

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def display_name(self) -> str:
        return "Anthropic Claude"

    async def chat(self, request: AIRequest) -> AIResponse:
        """Delegate chat to the underlying adapter or direct Anthropic API."""
        if self._adapter is not None:
            return await self._adapter.chat(request)

        import httpx
        import time

        # Convert messages to Anthropic format
        system_prompt = ""
        anthropic_messages = []

        for msg in request.messages or []:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_prompt = content
            else:
                anthropic_role = "assistant" if role == "assistant" else "user"
                anthropic_messages.append({"role": anthropic_role, "content": content})

        if not anthropic_messages:
            anthropic_messages = [{"role": "user", "content": request.prompt or "Hello"}]

        payload: dict[str, Any] = {
            "model": request.model or self._default_model,
            "max_tokens": request.max_tokens or 2048,
            "messages": anthropic_messages,
        }
        if system_prompt:
            payload["system"] = system_prompt
        payload["temperature"] = request.temperature

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        start = time.monotonic()
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self._base_url}/messages",
                headers=headers,
                json=payload,
            )
        elapsed_ms = (time.monotonic() - start) * 1000.0

        if resp.status_code != 200:
            raise ConnectionError(
                f"Anthropic API error {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        content_blocks = data.get("content", [])
        text_content = "".join(
            block.get("text", "") for block in content_blocks if block.get("type") == "text"
        )
        usage = data.get("usage", {})
        return AIResponse(
            content=text_content,
            model=data.get("model", self._default_model),
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            },
            latency_ms=elapsed_ms,
            finish_reason=data.get("stop_reason", "stop"),
            request_id=request.request_id,
        )

    async def test_connection(self) -> dict[str, Any]:
        """Test connection to Anthropic API."""
        import time

        try:
            import httpx

            start = time.monotonic()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self._base_url}/models",
                    headers={
                        "x-api-key": self._api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
            elapsed_ms = (time.monotonic() - start) * 1000.0

            if resp.status_code == 200:
                self._connected = True
                return {"success": True, "latency_ms": round(elapsed_ms, 1)}
            else:
                return {
                    "success": False,
                    "latency_ms": round(elapsed_ms, 1),
                    "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                }
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000.0 if "start" in dir() else 0.0
            return {
                "success": False,
                "latency_ms": round(elapsed_ms, 1),
                "error": str(exc),
            }

    def get_config(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "base_url": self._base_url,
            "default_model": self._default_model,
            "connected": self._connected,
            "has_adapter": self._adapter is not None,
        }


# ======================================================================
# free-claude-code Proxy Driver
# ======================================================================


class FreeClaudeProxyDriver(ProviderDriver):
    """Provider Driver for free-claude-code-proxy SSE 微服务。

    将 Anthropic Messages API 格式请求转发到本地的 free-claude-code-proxy
    (http://localhost:5080)，由 proxy 完成 DeepSeek 上游 ↔ Anthropic 格式转换。

    典型用途:
        - AI名片前端通过此 Driver 直接调用 "Claude Code" 能力
        - 无需 Anthropic API Key，通过本地 SSE proxy 中转
        - 支持流式 (SSE) 和非流式响应
    """

    def __init__(
        self,
        proxy_url: str = "http://localhost:5080",
        proxy_api_key: str = "free-claude-key",
        upstream_key: str = "",
        upstream_url: str = "https://api.deepseek.com/v1/chat/completions",
        upstream_model: str = "deepseek-chat",
        adapter: AIGatewayProtocol | None = None,
    ) -> None:
        self._proxy_url = proxy_url.rstrip("/")
        self._proxy_api_key = proxy_api_key
        self._upstream_key = upstream_key
        self._upstream_url = upstream_url
        self._upstream_model = upstream_model
        self._adapter = adapter
        self._connected: bool = False

    @property
    def name(self) -> str:
        return "free-claude-proxy"

    @property
    def display_name(self) -> str:
        return "Free Claude Code Proxy"

    async def chat(self, request: AIRequest) -> AIResponse:
        """通过 free-claude-code-proxy 发送聊天请求。

        将 AIRequest 转为 Anthropic Messages API 格式，
        通过 SSE proxy 转发到上游 (DeepSeek)，返回 AIResponse。
        """
        import httpx
        import time

        if self._adapter is not None:
            return await self._adapter.chat(request)

        # 构建 Anthropic Messages API 兼容请求体
        messages = []
        for msg in request.messages or []:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            messages.append({"role": role, "content": content})

        if not messages:
            messages = [{"role": "user", "content": request.prompt or "Hello"}]

        payload: dict[str, Any] = {
            "model": request.model or "claude-sonnet-4-20250514",
            "max_tokens": request.max_tokens or 4096,
            "messages": messages,
            "stream": False,
            "temperature": request.temperature or 0.7,
        }
        if request.system_prompt:
            payload["system"] = [{"type": "text", "text": request.system_prompt}]
        if request.tools:
            payload["tools"] = request.tools

        # 发送到本地 proxy
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._proxy_url}/v1/messages",
                json=payload,
                headers={
                    "x-api-key": self._proxy_api_key,
                    "Content-Type": "application/json",
                },
            )
        elapsed_ms = (time.monotonic() - start) * 1000.0

        if resp.status_code != 200:
            raise ConnectionError(
                f"FreeClaudeProxy error {resp.status_code}: {resp.text[:500]}"
            )

        data = resp.json()

        # 从 SSE 响应中提取文本
        content = ""
        if isinstance(data, dict):
            content = data.get("content", [{}])[0].get("text", "") if data.get("content") else ""
            if not content and "error" in data:
                content = f"[Proxy Error] {data['error']}"

        return AIResponse(
            content=content,
            model=payload["model"],
            usage={
                "prompt_tokens": len(str(payload)) // 4,
                "completion_tokens": len(content) // 4,
                "total_tokens": (len(str(payload)) + len(content)) // 4,
            },
            latency_ms=round(elapsed_ms, 1),
            finish_reason="stop",
            request_id=request.request_id,
        )

    async def test_connection(self) -> dict[str, Any]:
        """通过 proxy 的 /health 端点测试连接。"""
        import httpx
        import time

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self._proxy_url}/health")
            elapsed_ms = (time.monotonic() - start) * 1000.0

            if resp.status_code == 200:
                self._connected = True
                data = resp.json()
                return {
                    "success": True,
                    "latency_ms": round(elapsed_ms, 1),
                    "proxy_version": data.get("version", "unknown"),
                }
            else:
                return {
                    "success": False,
                    "latency_ms": round(elapsed_ms, 1),
                    "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                }
        except httpx.ConnectError:
            elapsed_ms = (time.monotonic() - start) * 1000.0
            return {
                "success": False,
                "latency_ms": round(elapsed_ms, 1),
                "error": f"无法连接到 free-claude-code-proxy ({self._proxy_url})",
            }
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000.0
            return {
                "success": False,
                "latency_ms": round(elapsed_ms, 1),
                "error": str(exc),
            }

    def get_config(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "proxy_url": self._proxy_url,
            "upstream_url": self._upstream_url,
            "upstream_model": self._upstream_model,
            "connected": self._connected,
            "has_adapter": self._adapter is not None,
        }


# ======================================================================
# Thread‑Local Driver Registry
# ======================================================================


class DriverRegistry:
    """Global registry for AI provider drivers.

    Thread‑local safe. Singletons are lazily initialised via provider_manager
    on application startup.

    Typical workflow:
        1. registry = DriverRegistry.get_instance()
        2. registry.register("openai", OpenAIDriver(api_key=...))
        3. driver = registry.get_driver("openai")
        4. response = await driver.chat(request)
        5. registry.set_default("openai")
    """

    _instance: DriverRegistry | None = None

    def __init__(self) -> None:
        self._drivers: dict[str, ProviderDriver] = {}
        self._default_driver: str | None = None

    @classmethod
    def get_instance(cls) -> DriverRegistry:
        """Get the global DriverRegistry singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, name: str, driver: ProviderDriver) -> None:
        """Register a provider driver by name.

        Args:
            name: Unique provider key (e.g. 'openai', 'anthropic').
            driver: The ProviderDriver instance.

        Raises:
            ValueError: If a driver with this name is already registered.
        """
        if name in self._drivers:
            raise ValueError(f"Driver '{name}' is already registered")
        self._drivers[name] = driver
        logger.info("Provider driver registered: %s (%s)", name, driver.display_name)
        if self._default_driver is None:
            self._default_driver = name

    def unregister(self, name: str) -> None:
        """Unregister a provider driver."""
        self._drivers.pop(name, None)
        if self._default_driver == name:
            self._default_driver = next(iter(self._drivers)) if self._drivers else None

    def get_driver(self, name: str | None = None) -> ProviderDriver:
        """Get a registered driver by name, or the default driver.

        Args:
            name: Provider name. If None, returns the default driver.

        Returns:
            The ProviderDriver instance.

        Raises:
            KeyError: If the driver is not found or no default is set.
        """
        if name is None:
            if self._default_driver is None:
                raise KeyError("No default provider driver configured")
            name = self._default_driver
        if name not in self._drivers:
            raise KeyError(f"Provider driver '{name}' is not registered. "
                           f"Available: {list(self._drivers.keys())}")
        return self._drivers[name]

    def set_default(self, name: str) -> None:
        """Set the default provider driver.

        Args:
            name: Provider name to set as default.

        Raises:
            KeyError: If the driver is not registered.
        """
        if name not in self._drivers:
            raise KeyError(f"Cannot set default: driver '{name}' is not registered. "
                           f"Available: {list(self._drivers.keys())}")
        self._default_driver = name
        logger.info("Default provider driver switched to: %s", name)

    def list_drivers(self) -> list[dict[str, Any]]:
        """List all registered drivers with their metadata."""
        return [
            {
                "name": name,
                "display_name": driver.display_name,
                "is_default": name == self._default_driver,
                "config": driver.get_config(),
            }
            for name, driver in self._drivers.items()
        ]

    @property
    def default_driver(self) -> str | None:
        """Name of the current default driver, or None."""
        return self._default_driver

    def __len__(self) -> int:
        return len(self._drivers)

    def __contains__(self, name: str) -> bool:
        return name in self._drivers
