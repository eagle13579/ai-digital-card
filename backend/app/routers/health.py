"""Health check endpoint for AI数字名片 API.

Architecture:
  - GET /health       → Primary health check (simple plain-text "OK")
                        Used for k8s liveness/readiness probes
  - GET /api/health   → JSON health check (version + status)
                        Used for monitoring / debugging
  - GET /api/v1/health → Rewritten to /api/health by APIVersionRedirectMiddleware
"""
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_class=PlainTextResponse)
async def health_check():
    """Return simple health status. Primary endpoint for k8s probes."""
    return "OK"
