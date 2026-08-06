"""用量查询API — 对接 UsageCounter 模型"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.usage_service import get_user_usage

router = APIRouter(prefix="/api/v1/usage", tags=["用量"])


@router.get("")
async def get_my_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的使用量"""
    result = await get_user_usage(current_user.id, db)
    return result
