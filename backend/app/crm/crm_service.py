"""CRM 核心服务 — 联系人 CRUD、搜索、分组、导入导出、自动创建。

功能:
  1. CRUD: CrmContact / CrmDeal / CrmActivity / CrmNote / CrmPipelineStage
  2. 搜索: 按姓名/公司/标签/职位模糊搜索
  3. 分组: 按标签/来源/管道阶段/公司分组统计
  4. 自动创建: 从 MatchRecord(名片交换) 自动创建 CrmContact + CrmActivity
  5. CSV 导入导出
  6. 默认管道阶段初始化
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.crm.crm_models import (
    CrmActivity,
    CrmContact,
    CrmDeal,
    CrmNote,
    CrmPipelineStage,
)
from app.models.tag import MatchRecord
from app.models.user import User

logger = logging.getLogger(__name__)

# ── 默认管道阶段 ──────────────────────────────────────────────────────────────────

DEFAULT_PIPELINE_STAGES = [
    {"name": "潜在客户", "sort_order": 0, "color": "#d9d9d9", "is_default": True, "is_closed": False, "win_probability": 10.0},
    {"name": "初步接触", "sort_order": 1, "color": "#1890ff", "is_default": False, "is_closed": False, "win_probability": 25.0},
    {"name": "需求确认", "sort_order": 2, "color": "#52c41a", "is_default": False, "is_closed": False, "win_probability": 50.0},
    {"name": "方案/报价", "sort_order": 3, "color": "#faad14", "is_default": False, "is_closed": False, "win_probability": 70.0},
    {"name": "谈判中", "sort_order": 4, "color": "#fa8c16", "is_default": False, "is_closed": False, "win_probability": 85.0},
    {"name": "已成交", "sort_order": 5, "color": "#52c41a", "is_default": False, "is_closed": True, "win_probability": 100.0},
    {"name": "已丢失", "sort_order": 6, "color": "#ff4d4f", "is_default": False, "is_closed": True, "win_probability": 0.0},
]


class CrmService:
    """CRM 核心业务逻辑。"""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id

    # ── 管道阶段管理 ──────────────────────────────────────────────────────────────

    async def ensure_default_stages(self) -> list[CrmPipelineStage]:
        """确保用户有默认管道阶段，没有则创建。"""
        result = await self.db.execute(
            select(CrmPipelineStage).where(
                CrmPipelineStage.user_id == self.user_id
            ).order_by(CrmPipelineStage.sort_order).limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            # 已存在，直接返回全部
            result = await self.db.execute(
                select(CrmPipelineStage).where(
                    CrmPipelineStage.user_id == self.user_id
                ).order_by(CrmPipelineStage.sort_order)
            )
            return list(result.scalars().all())

        # 创建默认阶段
        stages = []
        for s in DEFAULT_PIPELINE_STAGES:
            stage = CrmPipelineStage(
                user_id=self.user_id,
                name=s["name"],
                sort_order=s["sort_order"],
                color=s["color"],
                is_default=s["is_default"],
                is_closed=s["is_closed"],
                win_probability=s["win_probability"],
            )
            self.db.add(stage)
            stages.append(stage)
        await self.db.commit()
        for s in stages:
            await self.db.refresh(s)
        logger.info("为用户 %s 创建了默认管道阶段 %d 个", self.user_id, len(stages))
        return stages

    async def get_pipeline_stages(self) -> list[CrmPipelineStage]:
        """获取用户的管道阶段列表。"""
        result = await self.db.execute(
            select(CrmPipelineStage).where(
                CrmPipelineStage.user_id == self.user_id
            ).order_by(CrmPipelineStage.sort_order)
        )
        return list(result.scalars().all())

    # ── 联系人 CRUD ──────────────────────────────────────────────────────────────

    async def create_contact(self, data: dict) -> CrmContact:
        """创建 CRM 联系人。"""
        # 确保管道阶段存在
        stages = await self.get_pipeline_stages()
        default_stage = next((s for s in stages if s.is_default), stages[0] if stages else None)

        contact = CrmContact(
            owner_id=self.user_id,
            user_id=data.get("user_id"),
            name=data["name"],
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            company=data.get("company", ""),
            title=data.get("title", ""),
            department=data.get("department", ""),
            avatar=data.get("avatar", ""),
            intro=data.get("intro", ""),
            source=data.get("source", "manual"),
            source_record_id=data.get("source_record_id"),
            tags=json.dumps(data.get("tags", []), ensure_ascii=False),
            pipeline_stage_id=data.get("pipeline_stage_id", default_stage.id if default_stage else None),
            deal_value=data.get("deal_value"),
            deal_currency=data.get("deal_currency", "CNY"),
            last_contacted_at=data.get("last_contacted_at"),
        )
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)

        # 记录创建活动
        await self._add_activity(
            contact_id=contact.id,
            activity_type="system",
            title=f"添加联系人: {contact.name}",
            description=f"来源: {contact.source}",
        )
        return contact

    async def get_contact(self, contact_id: int) -> CrmContact | None:
        """获取单个联系人（带管道阶段）。"""
        result = await self.db.execute(
            select(CrmContact).options(
                joinedload(CrmContact.stage)
            ).where(
                CrmContact.id == contact_id,
                CrmContact.owner_id == self.user_id,
            )
        )
        return result.unique().scalar_one_or_none()

    async def update_contact(self, contact_id: int, data: dict) -> CrmContact | None:
        """更新联系人。"""
        contact = await self.get_contact(contact_id)
        if not contact:
            return None

        updatable_fields = {
            "name", "phone", "email", "company", "title", "department",
            "avatar", "intro", "pipeline_stage_id", "deal_value",
            "deal_currency", "last_contacted_at",
        }
        for key, value in data.items():
            if key in updatable_fields:
                setattr(contact, key, value)
            elif key == "tags" and isinstance(value, list):
                contact.tags = json.dumps(value, ensure_ascii=False)

        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int) -> bool:
        """删除联系人（含关联的备注和活动）。"""
        contact = await self.get_contact(contact_id)
        if not contact:
            return False

        # 删除关联的笔记和活动
        await self.db.execute(
            CrmNote.__table__.delete().where(CrmNote.contact_id == contact_id)
        )
        await self.db.execute(
            CrmActivity.__table__.delete().where(CrmActivity.contact_id == contact_id)
        )
        await self.db.execute(
            CrmDeal.__table__.delete().where(CrmDeal.contact_id == contact_id)
        )
        await self.db.delete(contact)
        await self.db.commit()
        return True

    async def build_contacts_query(
        self,
        search: str | None = None,
        stage_id: int | None = None,
        source: str | None = None,
        tag: str | None = None,
        company: str | None = None,
    ) -> Select:
        """构建联系人筛选查询（不含分页），供 paginate_cursor 使用。"""

        query = select(CrmContact).options(
            joinedload(CrmContact.stage)
        ).where(CrmContact.owner_id == self.user_id)

        if search:
            kw = f"%{search}%"
            query = query.where(
                or_(
                    CrmContact.name.ilike(kw),
                    CrmContact.company.ilike(kw),
                    CrmContact.title.ilike(kw),
                    CrmContact.email.ilike(kw),
                    CrmContact.phone.ilike(kw),
                    CrmContact.intro.ilike(kw),
                )
            )
        if stage_id:
            query = query.where(CrmContact.pipeline_stage_id == stage_id)
        if source:
            query = query.where(CrmContact.source == source)
        if tag:
            query = query.where(CrmContact.tags.ilike(f"%{tag}%"))
        if company:
            query = query.where(CrmContact.company.ilike(f"%{company}%"))

        return query

    async def list_contacts(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        stage_id: int | None = None,
        source: str | None = None,
        tag: str | None = None,
        company: str | None = None,
    ) -> tuple[list[CrmContact], int]:
        """搜索/筛选联系人，返回 (列表, 总数)。"""
        query = select(CrmContact).options(
            joinedload(CrmContact.stage)
        ).where(CrmContact.owner_id == self.user_id)

        # 筛选条件
        if search:
            kw = f"%{search}%"
            query = query.where(
                or_(
                    CrmContact.name.ilike(kw),
                    CrmContact.company.ilike(kw),
                    CrmContact.title.ilike(kw),
                    CrmContact.email.ilike(kw),
                    CrmContact.phone.ilike(kw),
                    CrmContact.intro.ilike(kw),
                )
            )
        if stage_id:
            query = query.where(CrmContact.pipeline_stage_id == stage_id)
        if source:
            query = query.where(CrmContact.source == source)
        if tag:
            query = query.where(CrmContact.tags.ilike(f"%{tag}%"))
        if company:
            query = query.where(CrmContact.company.ilike(f"%{company}%"))

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        query = query.order_by(CrmContact.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        contacts = list(result.unique().scalars().all())

        return contacts, total

    # ── 活动 / 时间线 ─────────────────────────────────────────────────────────────

    async def _add_activity(
        self,
        contact_id: int,
        activity_type: str,
        title: str = "",
        description: str = "",
        deal_id: int | None = None,
        source_model: str | None = None,
        source_record_id: int | None = None,
        activity_date: datetime | None = None,
    ) -> CrmActivity:
        """内部添加活动记录。"""
        activity = CrmActivity(
            owner_id=self.user_id,
            contact_id=contact_id,
            deal_id=deal_id,
            activity_type=activity_type,
            title=title,
            description=description,
            source_model=source_model,
            source_record_id=source_record_id,
            activity_date=activity_date or func.now(),
        )
        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)
        return activity

    async def add_activity(self, data: dict) -> CrmActivity:
        """外部添加活动记录（通过API）。"""
        return await self._add_activity(
            contact_id=data["contact_id"],
            activity_type=data["activity_type"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            deal_id=data.get("deal_id"),
            source_model=data.get("source_model"),
            source_record_id=data.get("source_record_id"),
            activity_date=data.get("activity_date"),
        )

    async def get_contact_timeline(
        self, contact_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[CrmActivity], int]:
        """获取联系人时间线。"""
        query = select(CrmActivity).where(
            CrmActivity.contact_id == contact_id,
            CrmActivity.owner_id == self.user_id,
        )

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(CrmActivity.activity_date.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        activities = list(result.scalars().all())

        return activities, total

    # ── 笔记 ──────────────────────────────────────────────────────────────────────

    async def create_note(self, data: dict) -> CrmNote:
        """创建笔记。"""
        note = CrmNote(
            owner_id=self.user_id,
            contact_id=data.get("contact_id"),
            deal_id=data.get("deal_id"),
            content=data["content"],
            is_pinned=data.get("is_pinned", False),
        )
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)

        # 同步写一条活动
        if note.contact_id:
            await self._add_activity(
                contact_id=note.contact_id,
                activity_type="note",
                title="添加笔记",
                description=note.content[:200],
                deal_id=note.deal_id,
            )
        return note

    async def get_contact_notes(
        self, contact_id: int, page: int = 1, page_size: int = 50
    ) -> tuple[list[CrmNote], int]:
        """获取联系人笔记。"""
        query = select(CrmNote).where(
            CrmNote.contact_id == contact_id,
            CrmNote.owner_id == self.user_id,
        )
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(CrmNote.is_pinned.desc(), CrmNote.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        notes = list(result.scalars().all())
        return notes, total

    async def update_note(self, note_id: int, data: dict) -> CrmNote | None:
        """更新笔记。"""
        result = await self.db.execute(
            select(CrmNote).where(
                CrmNote.id == note_id,
                CrmNote.owner_id == self.user_id,
            )
        )
        note = result.scalar_one_or_none()
        if not note:
            return None
        if "content" in data:
            note.content = data["content"]
        if "is_pinned" in data:
            note.is_pinned = data["is_pinned"]
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def delete_note(self, note_id: int) -> bool:
        """删除笔记。"""
        result = await self.db.execute(
            select(CrmNote).where(
                CrmNote.id == note_id,
                CrmNote.owner_id == self.user_id,
            )
        )
        note = result.scalar_one_or_none()
        if not note:
            return False
        await self.db.delete(note)
        await self.db.commit()
        return True

    # ── 机会(Deal) CRUD ──────────────────────────────────────────────────────────

    async def create_deal(self, data: dict) -> CrmDeal:
        """创建销售机会。"""
        deal = CrmDeal(
            owner_id=self.user_id,
            contact_id=data["contact_id"],
            pipeline_stage_id=data["pipeline_stage_id"],
            title=data["title"],
            value=data.get("value", 0),
            currency=data.get("currency", "CNY"),
            probability=data.get("probability", 0.0),
            expected_close_date=data.get("expected_close_date"),
        )
        self.db.add(deal)
        await self.db.commit()
        await self.db.refresh(deal)

        # 更新联系人的管道阶段
        contact = await self.get_contact(data["contact_id"])
        if contact:
            contact.pipeline_stage_id = data["pipeline_stage_id"]
            await self.db.commit()

        return deal

    async def update_deal_stage(
        self, deal_id: int, stage_id: int
    ) -> CrmDeal | None:
        """更新机会的管道阶段（拖拽）。"""
        result = await self.db.execute(
            select(CrmDeal).where(
                CrmDeal.id == deal_id,
                CrmDeal.owner_id == self.user_id,
            )
        )
        deal = result.scalar_one_or_none()
        if not deal:
            return None
        deal.pipeline_stage_id = stage_id
        await self.db.commit()
        await self.db.refresh(deal)
        return deal

    async def get_pipeline_deals(self) -> dict[int, list[CrmDeal]]:
        """获取按管道阶段分组的销售机会。"""
        stages = await self.get_pipeline_stages()
        result = await self.db.execute(
            select(CrmDeal).options(
                joinedload(CrmDeal.contact),
                joinedload(CrmDeal.stage),
            ).where(
                CrmDeal.owner_id == self.user_id,
                CrmDeal.status == "open",
            ).order_by(CrmDeal.updated_at.desc())
        )
        deals = list(result.unique().scalars().all())

        grouped: dict[int, list[CrmDeal]] = {}
        for stage in stages:
            grouped[stage.id] = []
        for deal in deals:
            if deal.pipeline_stage_id in grouped:
                grouped[deal.pipeline_stage_id].append(deal)
        return grouped

    # ── 从名片交换自动创建联系人 ──────────────────────────────────────────────────

    async def create_contact_from_match(self, match_record: MatchRecord) -> CrmContact | None:
        """从名片交换记录自动创建 CRM 联系人。

        当用户 A 和用户 B 交换名片后，A 的 CRM 中出现 B 的联系人，反之亦然。
        """
        # 确定当前用户是 A 还是 B，对方是另一个
        if match_record.user_a_id == self.user_id:
            target_user_id = match_record.user_b_id
        elif match_record.user_b_id == self.user_id:
            target_user_id = match_record.user_a_id
        else:
            return None

        # 检查是否已存在
        result = await self.db.execute(
            select(CrmContact).where(
                CrmContact.owner_id == self.user_id,
                CrmContact.user_id == target_user_id,
            ).limit(1)
        )
        if result.scalar_one_or_none():
            return None  # 已存在，不重复创建

        # 获取对方用户信息
        result = await self.db.execute(
            select(User).where(User.id == target_user_id)
        )
        target_user = result.scalar_one_or_none()
        if not target_user:
            return None

        # 创建联系人
        contact = CrmContact(
            owner_id=self.user_id,
            user_id=target_user_id,
            name=target_user.name,
            phone=target_user.phone or "",
            email=target_user.email or "",
            company=target_user.company or "",
            title=target_user.title or "",
            avatar=target_user.avatar or "",
            intro=target_user.intro or "",
            source="match",
            source_record_id=match_record.id,
        )
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)

        # 记录活动
        await self._add_activity(
            contact_id=contact.id,
            activity_type="match",
            title=f"名片交换: {target_user.name}",
            description=f"匹配分数: {match_record.match_score}",
            source_model="match_records",
            source_record_id=match_record.id,
            activity_date=match_record.created_at,
        )
        logger.info(
            "自动从名片交换创建 CRM 联系人: user=%s -> contact=%s",
            self.user_id, contact.id,
        )
        return contact

    # ── 统计/分组 ──────────────────────────────────────────────────────────────────

    async def get_group_stats(self) -> dict[str, Any]:
        """获取联系人分组统计。"""
        contacts_result = await self.db.execute(
            select(CrmContact).where(CrmContact.owner_id == self.user_id)
        )
        contacts = list(contacts_result.scalars().all())

        # 按来源
        by_source: dict[str, int] = {}
        # 按公司
        by_company: dict[str, int] = {}
        # 按管道阶段
        by_stage: dict[str, int] = {}
        # 标签云
        tag_count: dict[str, int] = {}

        for c in contacts:
            by_source[c.source] = by_source.get(c.source, 0) + 1
            if c.company:
                by_company[c.company] = by_company.get(c.company, 0) + 1
            if c.stage:
                by_stage[c.stage.name] = by_stage.get(c.stage.name, 0) + 1
            try:
                tags = json.loads(c.tags) if isinstance(c.tags, str) else (c.tags or [])
                for t in tags:
                    tag_count[t] = tag_count.get(t, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "total_contacts": len(contacts),
            "by_source": by_source,
            "by_company": dict(sorted(by_company.items(), key=lambda x: -x[1])[:20]),
            "by_stage": by_stage,
            "top_tags": dict(sorted(tag_count.items(), key=lambda x: -x[1])[:20]),
        }

    # ── CSV 导入导出 ──────────────────────────────────────────────────────────────

    async def export_csv(self) -> str:
        """导出联系人 CSV。"""
        contacts, _ = await self.list_contacts(page=1, page_size=10000)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "姓名", "手机", "邮箱", "公司", "职位", "部门",
            "来源", "标签", "管道阶段", "预估金额", "最后联系时间",
        ])
        for c in contacts:
            try:
                tags_list = json.loads(c.tags) if isinstance(c.tags, str) else []
            except (json.JSONDecodeError, TypeError):
                tags_list = []
            writer.writerow([
                c.name, c.phone, c.email, c.company, c.title, c.department,
                c.source, "; ".join(tags_list),
                c.stage.name if c.stage else "",
                float(c.deal_value) if c.deal_value else "",
                c.last_contacted_at.isoformat() if c.last_contacted_at else "",
            ])
        return output.getvalue()

    async def import_csv(self, csv_content: str) -> dict[str, Any]:
        """从 CSV 导入联系人。"""
        reader = csv.DictReader(io.StringIO(csv_content))
        created = 0
        errors: list[str] = []
        stages = await self.get_pipeline_stages()
        default_stage = next((s for s in stages if s.is_default), stages[0] if stages else None)

        for i, row in enumerate(reader, start=1):
            try:
                name = row.get("姓名", "").strip()
                if not name:
                    errors.append(f"第{i}行: 姓名为空")
                    continue
                tags_str = row.get("标签", "").strip()
                tags = [t.strip() for t in tags_str.split(";") if t.strip()] if tags_str else []

                contact = CrmContact(
                    owner_id=self.user_id,
                    name=name,
                    phone=row.get("手机", "").strip(),
                    email=row.get("邮箱", "").strip(),
                    company=row.get("公司", "").strip(),
                    title=row.get("职位", "").strip(),
                    department=row.get("部门", "").strip(),
                    source="import",
                    tags=json.dumps(tags, ensure_ascii=False),
                    pipeline_stage_id=default_stage.id if default_stage else None,
                )
                self.db.add(contact)
                created += 1
            except Exception as e:
                errors.append(f"第{i}行: {e}")

        await self.db.commit()
        return {"created": created, "errors": errors, "total_rows": i}
