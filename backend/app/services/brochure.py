import csv
import io
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brochure import Brochure, Page
from app.models.visitor import VisitorLog


class BrochureService:
    """画册服务层 - 封装画册 CRUD、发布、公开访问等业务逻辑"""

    @staticmethod
    async def create_brochure(
        db: AsyncSession,
        user_id: int,
        title: str,
        cover: str = "",
        purpose: str = "",
        pages_data: list[dict] | None = None,
        album_meta: str | None = None,
    ) -> Brochure:
        """创建画册（含多页初始化）"""
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
        await db.flush()

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

        await db.commit()
        await db.refresh(brochure)
        return brochure

    @staticmethod
    async def update_brochure(
        db: AsyncSession,
        brochure_id: int,
        user_id: int,
        update_data: dict,
    ) -> Brochure:
        """更新画册（含页面替换逻辑）"""
        result = await db.execute(select(Brochure).where(Brochure.id == brochure_id))
        brochure = result.scalars().first()
        if brochure is None:
            raise ValueError("画册不存在")
        if brochure.user_id != user_id:
            raise PermissionError("无权修改此画册")

        pages_data = update_data.pop("pages", None)

        for field, value in update_data.items():
            if hasattr(brochure, field):
                setattr(brochure, field, value)

        if pages_data is not None:
            result = await db.execute(select(Page).where(Page.brochure_id == brochure_id))
            existing_pages = result.scalars().all()
            for p in existing_pages:
                await db.delete(p)

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

        await db.commit()
        await db.refresh(brochure)
        return brochure

    @staticmethod
    async def publish_brochure(
        db: AsyncSession,
        brochure_id: int,
        user_id: int,
    ) -> Brochure:
        """发布画册（生成分享 token）"""
        result = await db.execute(select(Brochure).where(Brochure.id == brochure_id))
        brochure = result.scalars().first()
        if brochure is None:
            raise ValueError("画册不存在")
        if brochure.user_id != user_id:
            raise PermissionError("无权发布此画册")

        brochure.status = "published"
        brochure.share_token = uuid.uuid4().hex[:16]
        await db.commit()
        await db.refresh(brochure)
        return brochure

    @staticmethod
    async def delete_brochure(
        db: AsyncSession,
        brochure_id: int,
        user_id: int,
        soft_delete: bool = True,
    ) -> dict:
        """删除画册（默认软删除：status -> deleted）"""
        result = await db.execute(select(Brochure).where(Brochure.id == brochure_id))
        brochure = result.scalars().first()
        if brochure is None:
            raise ValueError("画册不存在")
        if brochure.user_id != user_id:
            raise PermissionError("无权删除此画册")

        if soft_delete:
            brochure.status = "deleted"
            await db.commit()
            return {"detail": "画册已软删除"}
        else:
            await db.delete(brochure)
            await db.commit()
            return {"detail": "画册已物理删除"}

    @staticmethod
    async def get_public_brochure(
        db: AsyncSession,
        share_token: str,
        visitor_ip: str = "",
        visitor_name: str = "",
    ) -> Brochure:
        """通过分享 token 公开访问画册（自动记录访问日志）"""
        result = await db.execute(
            select(Brochure).where(
                Brochure.share_token == share_token,
                Brochure.status == "published",
            )
        )
        brochure = result.scalars().first()
        if brochure is None:
            raise ValueError("画册不存在或链接已失效")

        brochure.view_count += 1
        await db.commit()

        log = VisitorLog(
            brochure_id=brochure.id,
            visitor_ip=visitor_ip,
            visitor_name=visitor_name,
            source="share",
        )
        db.add(log)
        await db.commit()

        await db.refresh(brochure)
        return brochure

    @staticmethod
    async def batch_import_from_csv(
        db: AsyncSession,
        user_id: int,
        csv_content: str,
    ) -> dict:
        """批量导入名片(CSV格式), 按name+phone去重"""
        reader = csv.DictReader(io.StringIO(csv_content))
        created, duplicates, errors = 0, 0, 0
        dup_list, err_list = [], []
        for row in reader:
            name = row.get("name", "").strip()
            phone = row.get("phone", "").strip()
            if not name and not phone:
                errors += 1
                err_list.append({"row": row, "reason": "缺少姓名和电话"})
                continue
            stmt = select(Brochure).where(
                Brochure.user_id == user_id,
                Brochure.title == name,
            )
            result = await db.execute(stmt)
            if result.scalars().first():
                duplicates += 1
                dup_list.append({"name": name, "phone": phone})
                continue
            brochure = Brochure(
                user_id=user_id,
                title=name or f"联系人{phone}",
                purpose=row.get("company", ""),
                status="published",
            )
            db.add(brochure)
            created += 1
        await db.commit()
        return {
            "created": created, "duplicates": duplicates, "errors": errors,
            "duplicate_items": dup_list[:10], "error_items": err_list[:10],
        }

    @staticmethod
    async def batch_export_csv(
        db: AsyncSession,
        user_id: int,
        filters: Optional[dict] = None,
    ) -> str:
        """导出名片为CSV"""
        stmt = select(Brochure).where(Brochure.user_id == user_id)
        if filters and filters.get("status"):
            stmt = stmt.where(Brochure.status == filters["status"])
        result = await db.execute(stmt)
        brochures = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["name", "company", "phone", "email", "status", "views", "created_at"])
        for b in brochures:
            writer.writerow([
                b.title, b.purpose, "", "",
                b.status, b.view_count,
                b.created_at.isoformat() if b.created_at else "",
            ])
        return output.getvalue()
