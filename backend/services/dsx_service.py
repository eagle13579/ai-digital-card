"""
DSX 白泽推理引擎 — AI数智名片适配层

将DSX的7大能力注册为名片的路由:
- /api/v1/dsx/health — 健康检查
- /api/v1/dsx/stats — 省钱统计
- /api/v1/dsx/audit — 审计记录
"""

import logging
import sys, os

logger = logging.getLogger(__name__)

_dsx_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dsx-engine"))
if _dsx_path not in sys.path:
    sys.path.insert(0, _dsx_path)

try:
    from dsx.features.cost_tracker import CostTracker
    from dsx.features.audit_chain import AuditChain
    _dsx_available = True
    logger.info("DSX engine loaded for AI名片 ✅")
except ImportError as e:
    _dsx_available = False
    logger.warning(f"DSX not available for AI名片: {e}")


def get_dsx_available() -> bool:
    return _dsx_available


def register_dsx_routes(app):
    """在FastAPI app上注册DSX路由"""
    if not _dsx_available:
        return
    from fastapi import APIRouter
    router = APIRouter(prefix="/api/v1/dsx")

    @router.get("/health")
    async def dsx_health():
        return {"status": "ok", "engine": "dsx", "version": "0.1.0"}

    @router.get("/stats")
    async def dsx_stats():
        ct = CostTracker()
        return {"status": "ok", "stats": ct.get_stats()}

    app.include_router(router)
    logger.info("DSX routes registered for AI名片 ✅")
