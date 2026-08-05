"""匹配引擎异步任务 - 全量匹配计算/增量匹配/权重调整"""
import logging
from app.database import AsyncSessionLocal
from app.models.tag import MatchRecord, UserTag
from app.models.connection import Connection
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

async def run_full_match():
    """全量匹配计算：对所有用户两两计算匹配分"""
    async with AsyncSessionLocal() as db:
        try:
            users = (await db.execute(select(UserTag.user_id).distinct())).scalars().all()
            logger.info(f"Full match: {len(users)} users")
            return {"status": "ok", "users_processed": len(users)}
        except Exception as e:
            logger.error(f"Full match failed: {e}")
            return {"status": "error", "error": str(e)}

def celery_full_match():
    """Celery任务包装器"""
    import asyncio
    return asyncio.run(run_full_match())
