"""Health check endpoint for AI数字名片 API."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Return service health status.

    The APIVersionRedirectMiddleware rewrites /api/v1/xxx → /api/xxx
    at ASGI scope level, so this endpoint is accessible at:
      - GET /api/health  (direct)
      - GET /api/v1/health  (rewritten by middleware)
    """
    return {
        "status": "ok",
        "service": "ai-digital-brochure",
        "version": "3.4.0",
    }
