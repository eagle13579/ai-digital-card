import html
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_standards import PaginatedResponse, paginate, raise_http_error
from app.database import get_db
from app.middleware.tenant import tenant_id_var
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import UserResponse, UserUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/users", tags=["用户"])


# ── 租户ID提取工具 ──────────────────────────────────────────
def _get_tenant_id(request: Request) -> int | None:
    """从请求中提取 tenant_id，优先 request.state，回退 ContextVar。"""
    try:
        # 优先从 request.state 读取（由中间件注入）
        tid = getattr(request.state, "tenant_id", None)
        if tid is not None:
            return int(tid)
    except Exception:
        pass
    # 回退到 ContextVar
    try:
        return tenant_id_var.get()
    except Exception:
        return None


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
    request: Request = None,
):
    """获取用户列表（仅限管理员），标准分页响应"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    query = select(User).order_by(User.id)
    # 多租户过滤：如果存在 tenant_id，只返回当前租户的用户
    try:
        tid = _get_tenant_id(request) if request else None
        if tid is not None:
            query = query.where(User.tenant_id == tid)
    except Exception as exc:
        logger.warning("租户过滤失败（向后兼容）: %s", exc)
    return await paginate(db, query, page, page_size, UserResponse)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None,
):
    """获取指定用户信息"""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="无权访问")
    query = select(User).where(User.id == user_id)
    # 多租户过滤
    try:
        tid = _get_tenant_id(request) if request else None
        if tid is not None:
            query = query.where(User.tenant_id == tid)
    except Exception as exc:
        logger.warning("租户过滤失败（向后兼容）: %s", exc)
    result = await db.execute(query)
    user = result.scalars().first()
    if user is None:
        raise_http_error(404, "NOT_FOUND", "用户不存在")
    return UserResponse.model_validate(user)
