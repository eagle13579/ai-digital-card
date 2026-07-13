from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_standards import PaginatedResponse, paginate, raise_http_error
from app.database import get_db
from app.models.user import User
from app.models.tag import UserTag
from app.routers.auth import get_current_user
from app.schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/api/users", tags=["用户"])


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
    for field, value in update_data.items():
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
    """获取用户列表（需登录），标准分页响应"""
    query = select(User).order_by(User.id)
    return await paginate(db, query, page, page_size, UserResponse)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取指定用户信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise_http_error(404, "NOT_FOUND", "用户不存在")
    return UserResponse.model_validate(user)


@router.get("/search/list", response_model=PaginatedResponse[UserResponse])
async def search_users(
    q: str = Query("", description="关键词搜索 name/company/title/intro"),
    industry: str = Query("", description="行业标签筛选"),
    region: str = Query("", description="地区标签筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    搜索用户（关键词+行业+地区筛选，LIKE模糊匹配）
    - q: 在 name/company/title/intro 模糊搜索
    - industry: 通过 UserTag(tag_type='provide', tag) 过滤行业
    - region: 通过 UserTag(tag_type='need', tag) 过滤地区
    """
    # 基础查询：排除当前用户
    query = select(User).where(User.id != current_user.id)

    # 关键词模糊匹配
    if q.strip():
        keyword = f"%{q.strip()}%"
        query = query.where(
            or_(
                User.name.ilike(keyword),
                User.company.ilike(keyword),
                User.title.ilike(keyword),
                User.intro.ilike(keyword),
            )
        )

    # 行业标签筛选（UserTag.tag_type = 'provide' 表示行业标签）
    if industry.strip():
        industry_sub = (
            select(UserTag.user_id)
            .where(
                UserTag.tag_type == "provide",
                UserTag.tag == industry.strip(),
            )
            .subquery()
        )
        query = query.where(User.id.in_(select(industry_sub.c.user_id)))

    # 地区标签筛选（UserTag.tag_type = 'need' 表示地区标签）
    if region.strip():
        region_sub = (
            select(UserTag.user_id)
            .where(
                UserTag.tag_type == "need",
                UserTag.tag == region.strip(),
            )
            .subquery()
        )
        query = query.where(User.id.in_(select(region_sub.c.user_id)))

    query = query.order_by(User.id)
    return await paginate(db, query, page, page_size, UserResponse)
