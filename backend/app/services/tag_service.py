from typing import Optional

from sqlalchemy.orm import Session

from app.models.tag import UserTag


class TagService:
    """标签服务层 - 支持 provide/need 双维度标签管理"""

    @staticmethod
    def add_tag(
        db: Session,
        user_id: int,
        tag: str,
        tag_type: str,
        weight: float = 1.0,
        source: str = "manual",
    ) -> UserTag:
        """添加单个标签

        Args:
            db: 数据库会话
            user_id: 用户ID
            tag: 标签内容
            tag_type: 标签类型 (provide | need)
            weight: 权重
            source: 来源 (manual | ai | import)

        Returns:
            创建的 UserTag 实例
        """
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
        db.commit()
        db.refresh(tag_obj)
        return tag_obj

    @staticmethod
    def batch_add_tags(
        db: Session,
        user_id: int,
        tags: list[str],
        tag_type: str,
        weight: float = 1.0,
        source: str = "manual",
    ) -> list[UserTag]:
        """批量添加标签

        Args:
            db: 数据库会话
            user_id: 用户ID
            tags: 标签列表
            tag_type: 标签类型 (provide | need)
            weight: 默认权重
            source: 来源

        Returns:
            创建的 UserTag 实例列表
        """
        if tag_type not in ("provide", "need"):
            raise ValueError("tag_type 必须是 provide 或 need")

        created = []
        for tag_text in tags:
            # 避免重复添加
            existing = db.query(UserTag).filter(
                UserTag.user_id == user_id,
                UserTag.tag == tag_text,
                UserTag.tag_type == tag_type,
            ).first()
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
            db.flush()
            created.append(tag_obj)

        db.commit()
        for obj in created:
            db.refresh(obj)
        return created

    @staticmethod
    def remove_tag(
        db: Session,
        tag_id: int,
        user_id: int,
    ) -> dict:
        """删除标签

        Args:
            db: 数据库会话
            tag_id: 标签ID
            user_id: 当前用户ID（鉴权用）

        Returns:
            操作结果
        """
        tag = db.query(UserTag).filter(UserTag.id == tag_id).first()
        if tag is None:
            raise ValueError("标签不存在")
        if tag.user_id != user_id:
            raise PermissionError("无权删除此标签")

        db.delete(tag)
        db.commit()
        return {"detail": "标签已删除"}

    @staticmethod
    def get_user_tags(
        db: Session,
        user_id: int,
        tag_type: Optional[str] = None,
    ) -> dict:
        """获取用户的标签（分 provide/need 两个维度返回）

        Args:
            db: 数据库会话
            user_id: 用户ID
            tag_type: 可选，筛选类型

        Returns:
            {"provide": [...], "need": [...]}
        """
        query = db.query(UserTag).filter(UserTag.user_id == user_id)
        if tag_type:
            query = query.filter(UserTag.tag_type == tag_type)
        tags = query.order_by(UserTag.weight.desc()).all()

        result: dict = {"provide": [], "need": []}
        for t in tags:
            result[t.tag_type].append({
                "id": t.id,
                "user_id": t.user_id,
                "tag_type": t.tag_type,
                "tag": t.tag,
                "weight": t.weight,
                "source": t.source,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            })
        return result
