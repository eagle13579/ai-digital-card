import json
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.brochure import Brochure, Page
from app.models.user import User
from app.models.visitor import VisitorLog


class BrochureService:
    """画册服务层 - 封装画册 CRUD、发布、公开访问等业务逻辑"""

    @staticmethod
    def create_brochure(
        db: Session,
        user_id: int,
        title: str,
        cover: str = "",
        purpose: str = "",
        pages_data: list[dict] | None = None,
        album_meta: str | None = None,
    ) -> Brochure:
        """创建画册（含多页初始化）

        Args:
            db: 数据库会话
            user_id: 用户ID
            title: 画册标题
            cover: 封面URL
            purpose: 名片用途 (partner/client/investor/supplier)
            pages_data: 页面数据列表，每项含 sort_order/content_type/content/image_url/ai_summary
            album_meta: 翻页图册元数据(JSON)

        Returns:
            创建的 Brochure 实例
        """
        pages_data = pages_data or []
        brochure = Brochure(
            user_id=user_id,
            title=title,
            cover=cover,
            purpose=purpose,
            album_meta=album_meta,
            pages_count=len(pages_data),
        )
        db.add(brochure)
        db.flush()

        for idx, page_dict in enumerate(pages_data):
            page = Page(
                brochure_id=brochure.id,
                sort_order=page_dict.get("sort_order", idx),
                content_type=page_dict.get("content_type", "text"),
                content=page_dict.get("content", ""),
                image_url=page_dict.get("image_url", ""),
                ai_summary=page_dict.get("ai_summary", ""),
            )
            db.add(page)

        # 如果没传页面数据，初始化4页默认画册
        if not pages_data:
            default_pages = [
                {"sort_order": 0, "content_type": "cover", "content": "个人封面"},
                {"sort_order": 1, "content_type": "text", "content": "联系方式"},
                {"sort_order": 2, "content_type": "text", "content": "企业信息"},
                {"sort_order": 3, "content_type": "image", "content": "二维码"},
            ]
            for idx, page_dict in enumerate(default_pages):
                page = Page(
                    brochure_id=brochure.id,
                    sort_order=idx,
                    content_type=page_dict["content_type"],
                    content=page_dict["content"],
                    image_url="",
                    ai_summary="",
                )
                db.add(page)
            brochure.pages_count = 4

        db.commit()
        db.refresh(brochure)
        return brochure

    @staticmethod
    def update_brochure(
        db: Session,
        brochure_id: int,
        user_id: int,
        update_data: dict,
    ) -> Brochure:
        """更新画册（含页面替换逻辑）

        Args:
            db: 数据库会话
            brochure_id: 画册ID
            user_id: 当前用户ID（鉴权用）
            update_data: 更新数据，可选含 pages 字段

        Returns:
            更新后的 Brochure 实例
        """
        brochure = db.query(Brochure).filter(Brochure.id == brochure_id).first()
        if brochure is None:
            raise ValueError("画册不存在")
        if brochure.user_id != user_id:
            raise PermissionError("无权修改此画册")

        pages_data = update_data.pop("pages", None)

        for field, value in update_data.items():
            if hasattr(brochure, field):
                setattr(brochure, field, value)

        if pages_data is not None:
            # 删除旧页面，重新添加
            existing_pages = db.query(Page).filter(Page.brochure_id == brochure_id).all()
            for p in existing_pages:
                db.delete(p)

            for idx, page_dict in enumerate(pages_data):
                page = Page(
                    brochure_id=brochure.id,
                    sort_order=page_dict.get("sort_order", idx),
                    content_type=page_dict.get("content_type", "text"),
                    content=page_dict.get("content", ""),
                    image_url=page_dict.get("image_url", ""),
                    ai_summary=page_dict.get("ai_summary", ""),
                )
                db.add(page)

            brochure.pages_count = len(pages_data)

        db.commit()
        db.refresh(brochure)
        return brochure

    @staticmethod
    def publish_brochure(
        db: Session,
        brochure_id: int,
        user_id: int,
    ) -> Brochure:
        """发布画册（生成分享 token）

        Args:
            db: 数据库会话
            brochure_id: 画册ID
            user_id: 当前用户ID

        Returns:
            发布后的 Brochure 实例
        """
        brochure = db.query(Brochure).filter(Brochure.id == brochure_id).first()
        if brochure is None:
            raise ValueError("画册不存在")
        if brochure.user_id != user_id:
            raise PermissionError("无权发布此画册")

        brochure.status = "published"
        brochure.share_token = uuid.uuid4().hex[:16]
        db.commit()
        db.refresh(brochure)
        return brochure

    @staticmethod
    def delete_brochure(
        db: Session,
        brochure_id: int,
        user_id: int,
        soft_delete: bool = True,
    ) -> dict:
        """删除画册（默认软删除：status -> deleted）

        Args:
            db: 数据库会话
            brochure_id: 画册ID
            user_id: 当前用户ID
            soft_delete: 是否软删除（True=改状态, False=物理删除）

        Returns:
            操作结果
        """
        brochure = db.query(Brochure).filter(Brochure.id == brochure_id).first()
        if brochure is None:
            raise ValueError("画册不存在")
        if brochure.user_id != user_id:
            raise PermissionError("无权删除此画册")

        if soft_delete:
            brochure.status = "deleted"
            db.commit()
            return {"detail": "画册已软删除"}
        else:
            db.delete(brochure)
            db.commit()
            return {"detail": "画册已物理删除"}

    @staticmethod
    def get_public_brochure(
        db: Session,
        share_token: str,
        visitor_ip: str = "",
        visitor_name: str = "",
    ) -> Brochure:
        """通过分享 token 公开访问画册（自动记录访问日志）

        Args:
            db: 数据库会话
            share_token: 分享令牌
            visitor_ip: 访问者IP
            visitor_name: 访问者名称

        Returns:
            Brochure 实例
        """
        brochure = db.query(Brochure).filter(
            Brochure.share_token == share_token,
            Brochure.status == "published",
        ).first()
        if brochure is None:
            raise ValueError("画册不存在或链接已失效")

        # 增加访问计数
        brochure.view_count += 1
        db.commit()

        # 记录访问日志
        log = VisitorLog(
            brochure_id=brochure.id,
            visitor_ip=visitor_ip,
            visitor_name=visitor_name,
            source="share",
        )
        db.add(log)
        db.commit()

        db.refresh(brochure)
        return brochure
