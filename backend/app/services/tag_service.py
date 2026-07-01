from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import UserTag


class TagService:
    """标签服务层 - 支持 provide/need 双维度标签管理"""

    @staticmethod
    async def add_tag(
        db: AsyncSession,
        user_id: int,
        tag: str,
        tag_type: str,
        weight: float = 1.0,
        source: str = "manual",
    ) -> UserTag:
        """添加单个标签"""
        if tag_type not in ("provide", "need"):
            raise ValueError("tag_type 必须是 provide 或 need")

        tag_obj = UserTag(
            user_id=user_id,
            tag_type=tag_type,
            tag=tag,
            weight=weight,
            source=source,
        )
        db.add(tag_obj)
        await db.commit()
        await db.refresh(tag_obj)
        return tag_obj

    @staticmethod
    async def batch_add_tags(
        db: AsyncSession,
        user_id: int,
        tags: list[str],
        tag_type: str,
        weight: float = 1.0,
        source: str = "manual",
    ) -> list[UserTag]:
        """批量添加标签"""
        if tag_type not in ("provide", "need"):
            raise ValueError("tag_type 必须是 provide 或 need")

        created = []
        for tag_text in tags:
            result = await db.execute(
                select(UserTag).where(
                    UserTag.user_id == user_id,
                    UserTag.tag == tag_text,
                    UserTag.tag_type == tag_type,
                )
            )
            existing = result.scalars().first()
            if existing:
                created.append(existing)
                continue

            tag_obj = UserTag(
                user_id=user_id,
                tag_type=tag_type,
                tag=tag_text,
                weight=weight,
                source=source,
            )
            db.add(tag_obj)
            await db.flush()
            created.append(tag_obj)

        await db.commit()
        for obj in created:
            await db.refresh(obj)
        return created

    @staticmethod
    async def remove_tag(
        db: AsyncSession,
        tag_id: int,
        user_id: int,
    ) -> dict:
        """删除标签"""
        result = await db.execute(select(UserTag).where(UserTag.id == tag_id))
        tag = result.scalars().first()
        if tag is None:
            raise ValueError("标签不存在")
        if tag.user_id != user_id:
            raise PermissionError("无权删除此标签")

        await db.delete(tag)
        await db.commit()
        return {"detail": "标签已删除"}

    @staticmethod
    async def get_user_tags(
        db: AsyncSession,
        user_id: int,
        tag_type: Optional[str] = None,
    ) -> dict:
        """获取用户的标签（分 provide/need 两个维度返回）"""
        query = select(UserTag).where(UserTag.user_id == user_id)
        if tag_type:
            query = query.where(UserTag.tag_type == tag_type)
        query = query.order_by(UserTag.weight.desc())
        result = await db.execute(query)
        tags = result.scalars().all()

        result_data: dict = {"provide": [], "need": []}
        for t in tags:
            result_data[t.tag_type].append({
                "id": t.id,
                "user_id": t.user_id,
                "tag_type": t.tag_type,
                "tag": t.tag,
                "weight": t.weight,
                "source": t.source,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            })
        return result_data
