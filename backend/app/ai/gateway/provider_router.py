"""Provider Driver Router — API endpoints for multi-AI provider management.

Endpoints:
    GET    /api/v1/providers          — List all registered providers
    POST   /api/v1/providers/switch   — Switch the default provider
    POST   /api/v1/providers/test     — Test connection to a specific provider
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.gateway.provider_driver import DriverRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/providers", tags=["providers"])


# ======================================================================
# Request / Response Models
# ======================================================================


class SwitchProviderRequest(BaseModel):
    provider: str = Field(..., description="Provider name to set as default (e.g. 'openai', 'anthropic')")


class TestProviderRequest(BaseModel):
    provider: str = Field(..., description="Provider name to test (e.g. 'openai', 'anthropic')")


class ProviderInfo(BaseModel):
    name: str
    display_name: str
    is_default: bool
    config: dict[str, Any]


class ProviderListResponse(BaseModel):
    providers: list[ProviderInfo]
    default: str | None


class SwitchProviderResponse(BaseModel):
    success: bool
    previous_default: str | None
    current_default: str
    message: str


class TestProviderResponse(BaseModel):
    success: bool
    provider: str
    latency_ms: float | None = None
    error: str | None = None


class ErrorResponse(BaseModel):
    detail: str


# ======================================================================
# Routes
# ======================================================================


@router.get(
    "",
    summary="List all registered AI providers",
    description="Returns a list of all registered provider drivers with their metadata and current default.",
    response_model=ProviderListResponse,
    responses={500: {"model": ErrorResponse}},
)
async def list_providers():
    """GET /api/v1/providers — List all registered provider drivers."""
    try:
        registry = DriverRegistry.get_instance()
        drivers = registry.list_drivers()
        return ProviderListResponse(
            providers=[
                ProviderInfo(
                    name=d["name"],
                    display_name=d["display_name"],
                    is_default=d["is_default"],
                    config=d["config"],
                )
                for d in drivers
            ],
            default=registry.default_driver,
        )
    except Exception as exc:
        logger.exception("Failed to list providers")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/switch",
    summary="Switch the default AI provider",
    description="Change the default provider driver for all subsequent AI calls.",
    response_model=SwitchProviderResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def switch_provider(req: SwitchProviderRequest):
    """POST /api/v1/providers/switch — Switch default provider."""
    try:
        registry = DriverRegistry.get_instance()
        previous = registry.default_driver
        registry.set_default(req.provider)
        return SwitchProviderResponse(
            success=True,
            previous_default=previous,
            current_default=req.provider,
            message=f"Default provider switched from '{previous}' to '{req.provider}'",
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{req.provider}' is not registered. "
                   f"Available: {list(DriverRegistry.get_instance().list_drivers())}",
        )
    except Exception as exc:
        logger.exception("Failed to switch provider")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/test",
    summary="Test a provider connection",
    description="Test connectivity to a specific provider's API endpoint.",
    response_model=TestProviderResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def test_provider(req: TestProviderRequest):
    """POST /api/v1/providers/test — Test connection to a provider."""
    try:
        registry = DriverRegistry.get_instance()
        driver = registry.get_driver(req.provider)
        result = await driver.test_connection()
        return TestProviderResponse(
            success=result.get("success", False),
            provider=req.provider,
            latency_ms=result.get("latency_ms"),
            error=result.get("error"),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{req.provider}' is not registered. "
                   f"Available: {list(DriverRegistry.get_instance().list_drivers())}",
        )
    except Exception as exc:
        logger.exception("Failed to test provider")
        raise HTTPException(status_code=500, detail=str(exc))
