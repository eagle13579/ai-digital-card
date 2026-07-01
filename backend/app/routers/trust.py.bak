from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.trust import TrustNetwork
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import TrustCreate, TrustResponse

router = APIRouter(prefix="/api/trust", tags=["信任网络"])


@router.get("/network")
def get_trust_network(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的信任网络（信任的人 + 信任我的人）"""
    # 我信任的人
    trusting = db.query(TrustNetwork).filter(TrustNetwork.user_id == current_user.id).all()
    trusting_ids = [t.trusted_user_id for t in trusting]

    # 信任我的人
    trusted_by = db.query(TrustNetwork).filter(TrustNetwork.trusted_user_id == current_user.id).all()
    trusted_by_ids = [t.user_id for t in trusted_by]

    trusting_users = db.query(User).filter(User.id.in_(trusting_ids)).all() if trusting_ids else []
    trusted_by_users = db.query(User).filter(User.id.in_(trusted_by_ids)).all() if trusted_by_ids else []

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
def add_trust(
    data: TrustCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """添加信任关系"""
    if data.trusted_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能信任自己")

    # 验证被信任用户存在
    trusted_user = db.query(User).filter(User.id == data.trusted_user_id).first()
    if trusted_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否已存在信任关系
    existing = db.query(TrustNetwork).filter(
        TrustNetwork.user_id == current_user.id,
        TrustNetwork.trusted_user_id == data.trusted_user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="已建立信任关系")

    trust = TrustNetwork(
        user_id=current_user.id,
        trusted_user_id=data.trusted_user_id,
    )
    db.add(trust)
    db.commit()
    db.refresh(trust)
    return TrustResponse.model_validate(trust)


@router.delete("/network/{trusted_user_id}")
def remove_trust(
    trusted_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """移除信任关系"""
    trust = db.query(TrustNetwork).filter(
        TrustNetwork.user_id == current_user.id,
        TrustNetwork.trusted_user_id == trusted_user_id,
    ).first()
    if trust is None:
        raise HTTPException(status_code=404, detail="信任关系不存在")

    db.delete(trust)
    db.commit()
    return {"detail": "信任关系已移除"}


@router.get("/network/{user_id}", response_model=list[dict])
def get_user_trust_network(
    user_id: int,
    db: Session = Depends(get_db),
):
    """获取指定用户的信任网络"""
    trusting = db.query(TrustNetwork).filter(TrustNetwork.user_id == user_id).all()
    trusting_ids = [t.trusted_user_id for t in trusting]

    trusting_users = db.query(User).filter(User.id.in_(trusting_ids)).all() if trusting_ids else []

    return [
        {
            "id": u.id,
            "name": u.name,
            "company": u.company,
            "title": u.title,
            "avatar": u.avatar,
        }
        for u in trusting_users
    ]
