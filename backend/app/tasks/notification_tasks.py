"""通知推送异步任务 - 新匹配/新连接/新消息"""
import logging
from app.database import AsyncSessionLocal
from app.models.connection import Connection
from app.models.message import Message
from sqlalchemy import select

logger = logging.getLogger(__name__)

async def send_match_notification(user_id: int, matched_user_id: int):
    """发送新匹配通知"""
    logger.info(f"Match notification: user={user_id}, matched={matched_user_id}")
    return {"status": "ok", "notification": "match", "user_id": user_id}

def celery_match_notification(user_id: int, matched_user_id: int):
    """Celery任务包装器"""
    import asyncio
    return asyncio.run(send_match_notification(user_id, matched_user_id))
