"""通讯录服务 — 联系人导入、查询、删除、统计、匹配。

依赖 crypto_service 做手机号加密切片，依赖 matching_engine_v2 做匹配。
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import ImportedContact
from app.models.user import User
from app.services.crypto_service import encrypt_phone, hash_phone

logger = logging.getLogger(__name__)


# ── 导入结果 ────────────────────────────────────────────────────────────


@dataclass
class ImportResult:
    """批量导入结果"""
    total: int = 0
    success: int = 0
    duplicates: int = 0
    failed: int = 0
    failures: list[dict] = field(default_factory=list)


# ── 通讯录服务 ──────────────────────────────────────────────────────────


class ContactService:
    """通讯录导入与管理服务"""

    # ── 导入 ────────────────────────────────────────────────────────

    @staticmethod
    async def import_contacts(
        user_id: int,
        contacts: list[dict],
        source: str,
        db: AsyncSession,
    ) -> ImportResult:
        """批量导入联系人。

        Args:
            user_id: 当前用户 ID。
            contacts: 联系人列表，每项含 name, phone, 可选 company, position。
            source: 来源 wechat|csv|manual。
            db: 数据库会话。

        Returns:
            ImportResult 导入结果统计。
        """
        result = ImportResult(total=len(contacts))

        for item in contacts:
            result = await ContactService._import_one(
                user_id, item, source, db, result,
            )

        await db.commit()
        logger.info(
            "通讯录导入完成: user=%d, total=%d, success=%d, dup=%d, fail=%d",
            user_id, result.total, result.success, result.duplicates, result.failed,
        )
        return result

    @staticmethod
    async def _import_one(
        user_id: int,
        item: dict,
        source: str,
        db: AsyncSession,
        result: ImportResult,
    ) -> ImportResult:
        """导入单条联系人。"""
        name = (item.get("name") or "").strip()
        phone = (item.get("phone") or "").strip()

        # 校验必填字段
        if not name or not phone:
            result.failed += 1
            result.failures.append({
                "row": result.total,
                "reason": f"姓名为空" if not name else "手机号为空",
            })
            return result

        # 清理手机号
        digits = "".join(c for c in phone if c.isdigit())
        if len(digits) < 7:
            result.failed += 1
            result.failures.append({
                "row": result.total,
                "reason": f"手机号格式无效: {phone}",
            })
            return result

        # 去重检查（同一用户不能重复导入同一手机号）
        phone_sha256 = hash_phone(digits)
        from sqlalchemy import select
        existing = await db.execute(
            select(ImportedContact).where(
                ImportedContact.user_id == user_id,
                ImportedContact.phone_hash == phone_sha256,
                ImportedContact.deleted_at.is_(None),
            )
        )
        if existing.scalars().first():
            result.duplicates += 1
            return result

        # 加密
        encrypted, _, last4 = encrypt_phone(digits)

        # 写入
        contact = ImportedContact(
            user_id=user_id,
            name=name,
            phone_hash=phone_sha256,
            phone_enc=encrypted,
            phone_last4=last4,
            company=(item.get("company") or "").strip(),
            position=(item.get("position") or "").strip(),
            source=source,
        )
        db.add(contact)
        result.success += 1
        return result

    # ── 查询 ────────────────────────────────────────────────────────

    @staticmethod
    async def get_contacts(
        user_id: int,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        source: str | None = None,
        keyword: str | None = None,
    ) -> dict:
        """获取联系人列表（分页）。

        Returns:
            包含 items, total, page, page_size 的字典。
        """
        query = select(ImportedContact).where(
            ImportedContact.user_id == user_id,
            ImportedContact.deleted_at.is_(None),
        )

        if source:
            query = query.where(ImportedContact.source == source)
        if keyword:
            query = query.where(ImportedContact.name.ilike(f"%{keyword}%"))

        # 总数
        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.order_by(ImportedContact.created_at.desc()).offset(offset).limit(page_size)
        rows = (await db.execute(query)).scalars().all()

        return {
            "items": [c.to_dict() for c in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    async def get_contact_by_id(
        contact_id: int,
        user_id: int,
        db: AsyncSession,
    ) -> ImportedContact | None:
        """按 ID 获取单条联系人（校验归属）。"""
        result = await db.execute(
            select(ImportedContact).where(
                ImportedContact.id == contact_id,
                ImportedContact.user_id == user_id,
                ImportedContact.deleted_at.is_(None),
            )
        )
        return result.scalars().first()

    # ── 删除 ────────────────────────────────────────────────────────

    @staticmethod
    async def delete_contact(contact_id: int, user_id: int, db: AsyncSession) -> bool:
        """软删除单条联系人。"""
        contact = await ContactService.get_contact_by_id(contact_id, user_id, db)
        if contact is None:
            return False
        contact.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        return True

    @staticmethod
    async def clear_contacts(user_id: int, db: AsyncSession) -> int:
        """清空当前用户所有联系人（软删除）。

        Returns:
            被删除的联系人数量。
        """
        result = await db.execute(
            select(ImportedContact).where(
                ImportedContact.user_id == user_id,
                ImportedContact.deleted_at.is_(None),
            )
        )
        contacts = result.scalars().all()
        now = datetime.now(timezone.utc)
        for c in contacts:
            c.deleted_at = now
        await db.commit()
        return len(contacts)

    # ── 统计 ────────────────────────────────────────────────────────

    @staticmethod
    async def get_contact_stats(user_id: int, db: AsyncSession) -> dict:
        """获取联系人统计信息。"""
        base = and_(ImportedContact.user_id == user_id, ImportedContact.deleted_at.is_(None))

        total = (
            await db.execute(select(func.count()).select_from(ImportedContact).where(base))
        ).scalar() or 0

        # 按来源统计
        source_count_q = (
            select(ImportedContact.source, func.count().label("cnt"))
            .where(base)
            .group_by(ImportedContact.source)
        )
        source_rows = (await db.execute(source_count_q)).all()
        by_source = {row.source: row.cnt for row in source_rows}

        # 已匹配数
        matched = (
            await db.execute(
                select(func.count()).select_from(ImportedContact).where(
                    base, ImportedContact.is_matched == 1,
                )
            )
        ).scalar() or 0

        return {
            "total": total,
            "matched": matched,
            "by_source": by_source,
        }

    # ── 匹配 ────────────────────────────────────────────────────────

    @staticmethod
    async def match_contacts(
        user_id: int,
        db: AsyncSession,
    ) -> list[dict]:
        """对未匹配的联系人执行匹配引擎。

        通过手机号 SHA-256 哈希比对系统用户，找到已在平台注册的联系人。

        Returns:
            匹配结果列表。
        """
        # 1. 获取当前用户所有未匹配的联系人
        result = await db.execute(
            select(ImportedContact).where(
                ImportedContact.user_id == user_id,
                ImportedContact.is_matched == 0,
                ImportedContact.deleted_at.is_(None),
            )
        )
        contacts = result.scalars().all()

        if not contacts:
            return []

        # 2. 获取所有系统用户（排除当前用户自己）
        user_result = await db.execute(
            select(User).where(User.id != user_id)
        )
        all_users = user_result.scalars().all()

        # 3. 构建 phone → user_id 映射（通过哈希）
        phone_hash_to_user: dict[str, int] = {}
        for u in all_users:
            if u.phone:
                h = hash_phone(u.phone)
                phone_hash_to_user[h] = u.id

        # 4. 匹配
        matched_results: list[dict] = []
        for c in contacts:
            matched_uid = phone_hash_to_user.get(c.phone_hash)
            if matched_uid is not None:
                c.is_matched = True
                c.matched_user_id = matched_uid
                matched_results.append({
                    "contact_id": c.id,
                    "name": c.name,
                    "phone_last4": c.phone_last4,
                    "matched_user_id": matched_uid,
                })
            else:
                # 标记已处理（无匹配也标记，避免反复扫描）
                c.is_matched = True

        await db.commit()

        logger.info(
            "联系人匹配完成: user=%d, total=%d, matched=%d",
            user_id, len(contacts), len(matched_results),
        )
        return matched_results
