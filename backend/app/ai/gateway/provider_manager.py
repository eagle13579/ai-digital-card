"""Provider Driver Manager — factory for auto-registering provider drivers on application startup.

This module provides a factory function that initializes the DriverRegistry singleton
with available provider drivers (Anthropic, OpenAI) using environment configuration.
It is called from the application startup event and does NOT modify existing adapters.

Usage (in app/__init__.py startup event):

    from app.ai.gateway.provider_manager import init_provider_drivers
    await init_provider_drivers()
"""

from __future__ import annotations

import logging
import os
from typing import Any

from app.ai.gateway.provider_driver import (
    AnthropicDriver,
    DriverRegistry,
    OpenAIDriver,
)

logger = logging.getLogger(__name__)


def init_provider_drivers(
    registry: DriverRegistry | None = None,
    overrides: dict[str, dict[str, Any]] | None = None,
) -> DriverRegistry:
    """Initialize and register all available provider drivers.

    Reads environment variables for API keys and configuration.
    Skips providers whose API key is not configured (graceful degradation).

    Args:
        registry: Optional existing registry instance. If None, uses the singleton.
        overrides: Optional dict of per-provider config overrides.
            E.g. {"openai": {"api_key": "...", "base_url": "..."}}

    Returns:
        The DriverRegistry instance with registered drivers.
    """
    if registry is None:
        registry = DriverRegistry.get_instance()

    # ── OpenAI Driver ──────────────────────────────────────────────
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    if overrides and "openai" in overrides:
        openai_cfg = overrides["openai"]
        openai_api_key = openai_cfg.get("api_key", openai_api_key)
        openai_base_url = openai_cfg.get("base_url", "https://api.openai.com/v1")
        openai_model = openai_cfg.get("default_model", "gpt-4o")
    else:
        openai_base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        openai_model = os.environ.get("OPENAI_DEFAULT_MODEL", "gpt-4o")

    if openai_api_key:
        try:
            driver = OpenAIDriver(
                api_key=openai_api_key,
                base_url=openai_base_url,
                default_model=openai_model,
            )
            registry.register("openai", driver)
            logger.info("OpenAI Provider Driver registered (base_url=%s)", openai_base_url)
        except ValueError as exc:
            logger.warning("OpenAI Driver registration skipped: %s", exc)
    else:
        logger.info(
            "OpenAI Provider Driver skipped: OPENAI_API_KEY not configured. "
            "Set env var OPENAI_API_KEY to enable."
        )

    # ── Anthropic Driver ───────────────────────────────────────────
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if overrides and "anthropic" in overrides:
        anthropic_cfg = overrides["anthropic"]
        anthropic_api_key = anthropic_cfg.get("api_key", anthropic_api_key)
        anthropic_base_url = anthropic_cfg.get("base_url", "https://api.anthropic.com/v1")
        anthropic_model = anthropic_cfg.get("default_model", "claude-sonnet-4-20250514")
    else:
        anthropic_base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1")
        anthropic_model = os.environ.get(
            "ANTHROPIC_DEFAULT_MODEL", "claude-sonnet-4-20250514"
        )

    if anthropic_api_key:
        try:
            driver = AnthropicDriver(
                api_key=anthropic_api_key,
                base_url=anthropic_base_url,
                default_model=anthropic_model,
            )
            registry.register("anthropic", driver)
            logger.info("Anthropic Provider Driver registered (base_url=%s)", anthropic_base_url)
        except ValueError as exc:
            logger.warning("Anthropic Driver registration skipped: %s", exc)
    else:
        logger.info(
            "Anthropic Provider Driver skipped: ANTHROPIC_API_KEY not configured. "
            "Set env var ANTHROPIC_API_KEY to enable."
        )

    # ── free-claude-code Proxy Driver ─────────────────────────────
    free_claude_proxy_url = os.environ.get(
        "FREE_CLAUDE_PROXY_URL", "http://localhost:5080"
    )
    free_claude_api_key = os.environ.get("PROXY_API_KEY", "free-claude-key")
    upstream_key = os.environ.get("UPSTREAM_KEY", "")
    upstream_url = os.environ.get(
        "UPSTREAM_URL", "https://api.deepseek.com/v1/chat/completions"
    )
    upstream_model = os.environ.get("UPSTREAM_MODEL", "deepseek-chat")

    try:
        from app.ai.gateway.provider_driver import FreeClaudeProxyDriver

        driver = FreeClaudeProxyDriver(
            proxy_url=free_claude_proxy_url,
            proxy_api_key=free_claude_api_key,
            upstream_key=upstream_key,
            upstream_url=upstream_url,
            upstream_model=upstream_model,
        )
        registry.register("free-claude-proxy", driver)
        logger.info(
            "FreeClaude Proxy Driver registered (proxy_url=%s, upstream=%s)",
            free_claude_proxy_url,
            upstream_model,
        )
    except ImportError as exc:
        logger.warning(
            "FreeClaude Proxy Driver registration skipped: %s. "
            "Install httpx and fastapi to enable.",
            exc,
        )
    except Exception as exc:
        logger.warning(
            "FreeClaude Proxy Driver registration failed: %s", exc
        )

    # Log summary
    total = len(registry)
    if total == 0:
        logger.warning(
            "No provider drivers registered. Configure at least one API key "
            "(OPENAI_API_KEY or ANTHROPIC_API_KEY) in environment."
        )
    else:
        logger.info(
            "Provider Driver initialization complete: %d driver(s) registered, "
            "default=%s",
            total,
            registry.default_driver,
        )

    return registry
