import html

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_standards import PaginatedResponse, paginate, raise_http_error
from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["用户"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户个人信息"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户个人信息"""
    update_data = data.model_dump(exclude_unset=True)
    ESCAPED_FIELDS = {"name", "company", "title", "intro", "avatar"}
    for field, value in update_data.items():
        if field in ESCAPED_FIELDS and isinstance(value, str):
            value = html.escape(value)
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户列表（仅限管理员），标准分页响应"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    query = select(User).order_by(User.id)
    return await paginate(db, query, page, page_size, UserResponse)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定用户信息"""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="无权访问")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise_http_error(404, "NOT_FOUND", "用户不存在")
    return UserResponse.model_validate(user)
