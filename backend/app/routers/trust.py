from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.trust import TrustNetwork
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import TrustCreate, TrustResponse

router = APIRouter(prefix="/api/v1/trust", tags=["信任网络"])


@router.get("/network")
async def get_trust_network(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的信任网络（信任的人 + 信任我的人）"""
    # 我信任的人
    result = await db.execute(
        select(TrustNetwork).where(TrustNetwork.user_id == current_user.id)
    )
    trusting = result.scalars().all()
    trusting_ids = [t.trusted_user_id for t in trusting]

    # 信任我的人
    result = await db.execute(
        select(TrustNetwork).where(TrustNetwork.trusted_user_id == current_user.id)
    )
    trusted_by = result.scalars().all()
    trusted_by_ids = [t.user_id for t in trusted_by]

    trusting_users = []
    if trusting_ids:
        result = await db.execute(select(User).where(User.id.in_(trusting_ids)))
        trusting_users = result.scalars().all()

    trusted_by_users = []
    if trusted_by_ids:
        result = await db.execute(select(User).where(User.id.in_(trusted_by_ids)))
        trusted_by_users = result.scalars().all()

    return {
        "trusting": [
            {
                "id": u.id,
                "name": u.name,
                "company": u.company,
                "title": u.title,
                "avatar": u.avatar,
            }
            for u in trusting_users
        ],
        "trusted_by": [
            {
                "id": u.id,
                "name": u.name,
                "company": u.company,
                "title": u.title,
                "avatar": u.avatar,
            }
            for u in trusted_by_users
        ],
    }


@router.post("/network", response_model=TrustResponse)
async def add_trust(
    data: TrustCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """添加信任关系"""
    if data.trusted_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能信任自己")

    # 验证被信任用户存在
    result = await db.execute(select(User).where(User.id == data.trusted_user_id))
    trusted_user = result.scalars().first()
    if trusted_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否已存在信任关系
    result = await db.execute(
        select(TrustNetwork).where(
            TrustNetwork.user_id == current_user.id,
            TrustNetwork.trusted_user_id == data.trusted_user_id,
        )
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="已建立信任关系")

    trust = TrustNetwork(
        user_id=current_user.id,
        trusted_user_id=data.trusted_user_id,
    )
    db.add(trust)
    await db.commit()
    await db.refresh(trust)
    return TrustResponse.model_validate(trust)


@router.delete("/network/{trusted_user_id}")
async def remove_trust(
    trusted_user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """移除信任关系"""
    result = await db.execute(
        select(TrustNetwork).where(
            TrustNetwork.user_id == current_user.id,
            TrustNetwork.trusted_user_id == trusted_user_id,
        )
    )
    trust = result.scalars().first()
    if trust is None:
        raise HTTPException(status_code=404, detail="信任关系不存在")

    await db.delete(trust)
    await db.commit()
    return {"detail": "信任关系已移除"}


@router.get("/network/{user_id}", response_model=list[dict])
async def get_user_trust_network(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取指定用户的信任网络"""
    result = await db.execute(
        select(TrustNetwork).where(TrustNetwork.user_id == user_id)
    )
    trusting = result.scalars().all()
    trusting_ids = [t.trusted_user_id for t in trusting]

    users = []
    if trusting_ids:
        result = await db.execute(select(User).where(User.id.in_(trusting_ids)))
        users = result.scalars().all()

    return [
        {
            "id": u.id,
            "name": u.name,
            "company": u.company,
            "title": u.title,
            "avatar": u.avatar,
        }
        for u in users
    ]
