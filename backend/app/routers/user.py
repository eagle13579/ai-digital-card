from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户个人信息"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前用户个人信息"""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户列表（需登录）"""
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    """获取指定用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserResponse.model_validate(user)
