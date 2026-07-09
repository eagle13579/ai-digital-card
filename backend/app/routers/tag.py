import html

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tag import UserTag
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import TagInput, TagBatchInput, TagResponse

router = APIRouter(prefix="/api/v1/tags", tags=["标签"])


@router.get("/me", response_model=dict)
async def get_my_tags(
    tag_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的标签（分 provide/need 两个维度）"""
    query = select(UserTag).where(UserTag.user_id == current_user.id)
    if tag_type:
        query = query.where(UserTag.tag_type == tag_type)
    query = query.order_by(UserTag.weight.desc())
    result = await db.execute(query)
    tags = result.scalars().all()

    # 分维组织
    result_data = {"provide": [], "need": []}
    for t in tags:
        result_data[t.tag_type].append(TagResponse.model_validate(t))
    return result_data


@router.post("/me", response_model=list[TagResponse])
async def add_tags(
    data: TagBatchInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量添加标签"""
    created = []
    for tag_input in data.tags:
        # XSS防护：对标签内容做HTML转义
        safe_tag = html.escape(tag_input.tag)
        tag = UserTag(
            user_id=current_user.id,
            tag_type=data.tag_type,
            tag=safe_tag,
            weight=tag_input.weight,
            source=data.source,
        )
        db.add(tag)
        await db.flush()
        created.append(TagResponse.model_validate(tag))

    await db.commit()
    return created


@router.delete("/me/{tag_id}")
async def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除标签"""
    result = await db.execute(select(UserTag).where(UserTag.id == tag_id))
    tag = result.scalars().first()
    if tag is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    if tag.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此标签")

    await db.delete(tag)
    await db.commit()
    return {"detail": "标签已删除"}


@router.get("/users/{user_id}", response_model=dict)
async def get_user_tags(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取指定用户的标签"""
    result = await db.execute(
        select(UserTag)
        .where(UserTag.user_id == user_id)
        .order_by(UserTag.weight.desc())
    )
    tags = result.scalars().all()

    result_data = {"provide": [], "need": []}
    for t in tags:
        result_data[t.tag_type].append(TagResponse.model_validate(t))
    return result_data
