from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tag import UserTag
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import TagInput, TagBatchInput, TagResponse

router = APIRouter(prefix="/api/tags", tags=["标签"])


@router.get("/me", response_model=dict)
def get_my_tags(
    tag_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的标签（分 provide/need 两个维度）"""
    query = db.query(UserTag).filter(UserTag.user_id == current_user.id)
    if tag_type:
        query = query.filter(UserTag.tag_type == tag_type)
    tags = query.order_by(UserTag.weight.desc()).all()

    # 分维组织
    result = {"provide": [], "need": []}
    for t in tags:
        result[t.tag_type].append(TagResponse.model_validate(t))
    return result


@router.post("/me", response_model=list[TagResponse])
def add_tags(
    data: TagBatchInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量添加标签"""
    created = []
    for tag_input in data.tags:
        tag = UserTag(
            user_id=current_user.id,
            tag_type=data.tag_type,
            tag=tag_input.tag,
            weight=tag_input.weight,
            source=data.source,
        )
        db.add(tag)
        db.flush()
        created.append(TagResponse.model_validate(tag))

    db.commit()
    return created


@router.delete("/me/{tag_id}")
def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除标签"""
    tag = db.query(UserTag).filter(UserTag.id == tag_id).first()
    if tag is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    if tag.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此标签")

    db.delete(tag)
    db.commit()
    return {"detail": "标签已删除"}


@router.get("/users/{user_id}", response_model=dict)
def get_user_tags(
    user_id: int,
    db: Session = Depends(get_db),
):
    """获取指定用户的标签"""
    query = db.query(UserTag).filter(UserTag.user_id == user_id)
    tags = query.order_by(UserTag.weight.desc()).all()

    result = {"provide": [], "need": []}
    for t in tags:
        result[t.tag_type].append(TagResponse.model_validate(t))
    return result
