"""Model Registry — multi-model routing with fallback chain.

Provides a registry and routing layer that:
    1. Registers AI providers (DeepSeek, Ollama, Cache) with priority ordering
    2. Routes requests through the fallback chain: DeepSeek → Ollama → Cache
    3. Implements ModelRegistryProtocol from interfaces.py
    4. Reports which provider served each request (for monitoring/headers)
    5. Supports dynamic enable/disable of providers at runtime

Architecture:
    ModelRegistry
        ├── route(request)      — Try each provider in priority order
        ├── get_default(task)   — Return the default model for a task
        └── resolve(model)      — Resolve model name with fallback

    Providers (in priority order):
        0: DirectAIGateway   (DeepSeek API — primary)
        1: OllamaGateway     (local Ollama — first fallback)
        2: CachedAIGateway   (cached responses — last resort)
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from app.ai.gateway.interfaces import (
    AIRequest,
    AIResponse,
    AIGatewayProtocol,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelRegistryProtocol,
)
from app.ai.gateway.adapters.direct_api_adapter import DirectAIGateway
from app.ai.gateway.adapters.cached_gateway_adapter import CachedAIGateway
from app.cache.adapters.memory_adapter import InMemoryCache

logger = logging.getLogger(__name__)


class AllProvidersFailedError(Exception):
    """Raised when every provider in the fallback chain has failed.

    Attributes:
        errors: List of (provider_index, provider_name, exception) tuples.
        last_error: The exception from the last attempted provider.
    """

    def __init__(
        self,
        errors: list[tuple[int, str, Exception]],
        message: str = "All AI providers in the fallback chain failed",
    ) -> None:
        self.errors = errors
        self.last_error = errors[-1][2] if errors else None
        self.details = "; ".join(
            f"[{idx}]{name}: {exc}" for idx, name, exc in errors
        )
        super().__init__(f"{message}. Details: {self.details}")


class ProviderNotRegisteredError(Exception):
    """Raised when a requested provider is not in the registry."""

    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name
        super().__init__(f"Provider '{provider_name}' is not registered")


# ======================================================================
# Provider wrapper with metadata
# ======================================================================


@dataclasses.dataclass
class ProviderEntry:
    """A registered provider with metadata and health status.

    Attributes:
        name: Human-readable provider name (e.g. "deepseek", "ollama").
        gateway: The AIGatewayProtocol instance.
        enabled: Whether this provider is currently active.
        priority: Lower number = higher priority (0 = primary).
    """
    name: str
    gateway: AIGatewayProtocol
    enabled: bool = True
    priority: int = 0


# ======================================================================
# Model Registry
# ======================================================================


class ModelRegistry:
    """Model registry — routes AI requests through a priority-ordered fallback chain.

    The registry maintains an ordered list of AI providers. Each provider
    implements ``AIGatewayProtocol``. When a request arrives:
        1. Try providers in priority order (lowest priority number first).
        2. If a provider fails (raises an exception), log the error and try
           the next provider.
        3. If all providers fail, raise ``AllProvidersFailedError``.
        4. Return the response with metadata about which provider served it.

    Default provider chain:
        0. DirectAIGateway (DeepSeek API — primary cloud provider)
        1. CachedAIGateway (cached responses — degraded fallback)

    Ollama can be added as a local fallback via ``register_provider()``:

        registry.register_provider("ollama", OllamaGateway(...), priority=1)

    Usage:
        registry = ModelRegistry()
        response = await registry.route(request)
        # response.metadata["provider"] == "deepseek"  (or "cache", "ollama")
    """

    def __init__(
        self,
        deepseek_api_key: str | None = None,
        deepseek_base_url: str | None = None,
        cache_ttl: int = 3600,
    ) -> None:
        """Initialise the model registry with default providers.

        Args:
            deepseek_api_key: Optional DeepSeek API key override.
            deepseek_base_url: Optional DeepSeek API URL override.
            cache_ttl: TTL in seconds for cached responses (default: 3600).
        """
        # ── Default provider: DirectAIGateway (DeepSeek) ─────────────
        self._direct = DirectAIGateway(
            api_key=deepseek_api_key,
            base_url=deepseek_base_url,
        )

        # ── Cache fallback: CachedAIGateway wrapping DirectAIGateway ─
        self._memory_cache = InMemoryCache(default_ttl=cache_ttl)
        self._cached = CachedAIGateway(
            inner=self._direct,
            cache=self._memory_cache,
            cache_ttl=cache_ttl,
        )

        # ── Registered providers in priority order ───────────────────
        # Providers are stored as a list of ProviderEntry, sorted by
        # priority (ascending). Lower priority number = tried first.
        self._providers: list[ProviderEntry] = [
            ProviderEntry(
                name="deepseek",
                gateway=self._direct,
                enabled=True,
                priority=0,
            ),
            ProviderEntry(
                name="cache",
                gateway=self._cached,
                enabled=True,
                priority=2,
            ),
        ]

        # ── Metrics ──────────────────────────────────────────────────
        self._total_requests: int = 0
        self._provider_hits: dict[str, int] = {
            "deepseek": 0,
            "cache": 0,
        }
        self._provider_errors: dict[str, int] = {
            "deepseek": 0,
            "cache": 0,
        }

    # ── Provider management ──────────────────────────────────────────

    def register_provider(
        self,
        name: str,
        gateway: AIGatewayProtocol,
        priority: int = 1,
        enabled: bool = True,
    ) -> None:
        """Register a new AI provider in the fallback chain.

        Args:
            name: Provider name (e.g. "ollama", "openai", "anthropic").
            gateway: AIGatewayProtocol instance.
            priority: Priority in the fallback chain. Lower = tried first.
                Default: 1 (between DeepSeek=0 and Cache=2).
            enabled: Whether this provider starts enabled.
        """
        # Remove existing provider with same name (replace)
        self._providers = [p for p in self._providers if p.name != name]

        self._providers.append(ProviderEntry(
            name=name,
            gateway=gateway,
            enabled=enabled,
            priority=priority,
        ))
        self._providers.sort(key=lambda p: p.priority)

        self._provider_hits[name] = 0
        self._provider_errors[name] = 0

        logger.info(
            "Registered provider '%s' at priority %d. "
            "Chain order: %s",
            name,
            priority,
            [p.name for p in self._providers if p.enabled],
        )

    def enable_provider(self, name: str) -> None:
        """Enable a previously registered provider.

        Args:
            name: Provider name to enable.

        Raises:
            ProviderNotRegisteredError: If the provider is not registered.
        """
        for p in self._providers:
            if p.name == name:
                p.enabled = True
                logger.info("Enabled provider '%s'", name)
                return
        raise ProviderNotRegisteredError(name)

    def disable_provider(self, name: str) -> None:
        """Disable a provider (remove it from the active chain).

        Args:
            name: Provider name to disable.

        Raises:
            ProviderNotRegisteredError: If the provider is not registered.
        """
        for p in self._providers:
            if p.name == name:
                p.enabled = False
                logger.warning("Disabled provider '%s'", name)
                return
        raise ProviderNotRegisteredError(name)

    def get_provider(self, name: str) -> AIGatewayProtocol | None:
        """Get a registered provider by name.

        Args:
            name: Provider name.

        Returns:
            The AIGatewayProtocol instance, or None if not found.
        """
        for p in self._providers:
            if p.name == name:
                return p.gateway
        return None

    @property
    def active_providers(self) -> list[str]:
        """List of currently active (enabled) provider names in priority order."""
        return [p.name for p in self._providers if p.enabled]

    # ── Metrics ──────────────────────────────────────────────────────

    @property
    def metrics(self) -> dict[str, Any]:
        """Return current metrics snapshot."""
        return {
            "total_requests": self._total_requests,
            "provider_hits": dict(self._provider_hits),
            "provider_errors": dict(self._provider_errors),
            "active_providers": self.active_providers,
        }

    # ── Routing ──────────────────────────────────────────────────────

    async def route(
        self,
        request: AIRequest,
    ) -> tuple[AIResponse, str]:
        """Route an AI request through the fallback chain.

        Tries each enabled provider in priority order. On success, returns
        a tuple of (response, provider_name). On failure of all providers,
        raises AllProvidersFailedError.

        Args:
            request: The chat completion request.

        Returns:
            Tuple of (AIResponse, provider_name) where provider_name is
            the name of the provider that successfully handled the request.

        Raises:
            AllProvidersFailedError: If all providers fail.
        """
        self._total_requests += 1
        errors: list[tuple[int, str, Exception]] = []

        enabled_providers = [p for p in self._providers if p.enabled]
        if not enabled_providers:
            raise AllProvidersFailedError(
                errors,
                message="No enabled AI providers in the registry",
            )

        for idx, entry in enumerate(enabled_providers):
            try:
                response = await entry.gateway.chat(request)

                # Success — record and return
                self._provider_hits[entry.name] = (
                    self._provider_hits.get(entry.name, 0) + 1
                )
                logger.info(
                    "ModelRegistry: request=%s served by '%s' (provider %d/%d)",
                    request.request_id[:8],
                    entry.name,
                    idx + 1,
                    len(enabled_providers),
                )
                return (response, entry.name)

            except Exception as exc:
                self._provider_errors[entry.name] = (
                    self._provider_errors.get(entry.name, 0) + 1
                )
                errors.append((idx, entry.name, exc))
                logger.warning(
                    "ModelRegistry: provider '%s' failed for request=%s "
                    "(attempt %d/%d). Error: %s",
                    entry.name,
                    request.request_id[:8],
                    idx + 1,
                    len(enabled_providers),
                    exc,
                )
                # Continue to next provider

        # All providers exhausted
        raise AllProvidersFailedError(errors)

    async def route_embed(
        self,
        request: EmbeddingRequest,
    ) -> tuple[EmbeddingResponse, str]:
        """Route an embedding request through the fallback chain.

        Same semantics as ``route()`` but for embedding requests.

        Args:
            request: The embedding request.

        Returns:
            Tuple of (EmbeddingResponse, provider_name).

        Raises:
            AllProvidersFailedError: If all providers fail.
        """
        self._total_requests += 1
        errors: list[tuple[int, str, Exception]] = []

        enabled_providers = [p for p in self._providers if p.enabled]
        if not enabled_providers:
            raise AllProvidersFailedError(
                errors,
                message="No enabled AI providers in the registry",
            )

        for idx, entry in enumerate(enabled_providers):
            try:
                response = await entry.gateway.embed(request)
                self._provider_hits[entry.name] = (
                    self._provider_hits.get(entry.name, 0) + 1
                )
                logger.info(
                    "ModelRegistry.embed: served by '%s' (provider %d/%d)",
                    entry.name,
                    idx + 1,
                    len(enabled_providers),
                )
                return (response, entry.name)

            except Exception as exc:
                self._provider_errors[entry.name] = (
                    self._provider_errors.get(entry.name, 0) + 1
                )
                errors.append((idx, entry.name, exc))
                logger.warning(
                    "ModelRegistry.embed: provider '%s' failed. Error: %s",
                    entry.name,
                    exc,
                )

        raise AllProvidersFailedError(errors)

    async def close(self) -> None:
        """Close all registered providers that support close()."""
        for entry in self._providers:
            if hasattr(entry.gateway, "close") and callable(entry.gateway.close):
                try:
                    await entry.gateway.close()
                except Exception as exc:
                    logger.warning(
                        "ModelRegistry.close: error closing '%s': %s",
                        entry.name,
                        exc,
                    )
