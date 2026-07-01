"""名片交换 → CRM 自动匹配钩子。

当用户交换名片（POST /api/business-card/cards/exchange 或
POST /api/business-card/exchange）时，自动:

  1. 检查双方 CRM 中是否已有相同手机/邮箱的联系人
  2. 有则更新姓名/公司/职位等信息
  3. 无则为双方各创建一条 CrmContact（来源=match）
  4. 记录 "名片交换" 活动到双方的时间线

使用方式:
  from app.crm.match_hook import sync_match_to_crm
  await sync_match_to_crm(db=db, match_record_id=record.id)

最小改动: 在 app/routers/miniapp_router.py 的 _do_exchange_card 末尾
调用此函数即可，无需修改现有路由注册。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import MatchRecord
from app.models.user import User

logger = logging.getLogger(__name__)

# 允许在非 CRM 环境下静默降级
try:
    from app.crm.crm_models import CrmActivity, CrmContact
    from app.crm.crm_service import CrmService

    _CRM_AVAILABLE = True
except ImportError:
    CrmContact = None  # type: ignore
    CrmActivity = None  # type: ignore
    CrmService = None  # type: ignore
    _CRM_AVAILABLE = False
    logger.warning("CRM 模块未加载，名片交换匹配钩子降级为空操作")


async def _ensure_default_stage(db: AsyncSession, user_id: int) -> int | None:
    """确保用户有默认管道阶段，返回默认 stage_id。"""
    from app.crm.crm_models import CrmPipelineStage

    result = await db.execute(
        select(CrmPipelineStage)
        .where(CrmPipelineStage.user_id == user_id)
        .order_by(CrmPipelineStage.sort_order)
        .limit(1)
    )
    stage = result.scalar_one_or_none()
    if stage:
        return stage.id

    # 创建一组默认阶段
    from app.crm.crm_service import DEFAULT_PIPELINE_STAGES

    stages = []
    for s in DEFAULT_PIPELINE_STAGES:
        st = CrmPipelineStage(
            user_id=user_id,
            name=s["name"],
            sort_order=s["sort_order"],
            color=s["color"],
            is_default=s["is_default"],
            is_closed=s["is_closed"],
            win_probability=s["win_probability"],
        )
        db.add(st)
        stages.append(st)
    await db.commit()
    for st in stages:
        await db.refresh(st)
    default = next((s for s in stages if s.is_default), stages[0] if stages else None)
    return default.id if default else None


async def _find_or_create_contact(
    db: AsyncSession,
    owner_id: int,
    target_user: User,
    match_record: MatchRecord,
) -> CrmContact | None:
    """为 owner_id 查找或创建对应 target_user 的 CRM 联系人。"""
    # ── 1. 优先通过 user_id 查找（已关联平台用户） ────────────────────
    result = await db.execute(
        select(CrmContact).where(
            CrmContact.owner_id == owner_id,
            CrmContact.user_id == target_user.id,
        ).limit(1)
    )
    existing = result.scalar_one_or_none()
    if existing:
        # 更新信息
        changed = False
        if target_user.name and existing.name != target_user.name:
            existing.name = target_user.name
            changed = True
        if target_user.phone and existing.phone != target_user.phone:
            existing.phone = target_user.phone
            changed = True
        if target_user.email and existing.email != target_user.email:
            existing.email = target_user.email
            changed = True
        if target_user.company and existing.company != target_user.company:
            existing.company = target_user.company
            changed = True
        if target_user.title and existing.title != target_user.title:
            existing.title = target_user.title
            changed = True
        if target_user.avatar and existing.avatar != target_user.avatar:
            existing.avatar = target_user.avatar
            changed = True
        if changed:
            await db.commit()
            await db.refresh(existing)
            logger.info(
                "更新 CRM 联系人 %s (owner=%s, target=%s)",
                existing.id, owner_id, target_user.id,
            )
        return existing

    # ── 2. 通过手机/邮箱查找 ─────────────────────────────────────────
    phone = (target_user.phone or "").strip()
    email = (target_user.email or "").strip()
    if phone or email:
        filters = [CrmContact.owner_id == owner_id]
        or_conditions = []
        if phone:
            or_conditions.append(CrmContact.phone == phone)
        if email:
            or_conditions.append(CrmContact.email == email)
        from sqlalchemy import or_
        filters.append(or_(*or_conditions))

        result = await db.execute(
            select(CrmContact).where(*filters).limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            # 更新信息
            existing.user_id = target_user.id
            if target_user.name:
                existing.name = target_user.name
            if target_user.company:
                existing.company = target_user.company
            if target_user.title:
                existing.title = target_user.title
            if target_user.avatar:
                existing.avatar = target_user.avatar
            if phone:
                existing.phone = phone
            if email:
                existing.email = email
            existing.source = "match"
            existing.source_record_id = match_record.id
            await db.commit()
            await db.refresh(existing)
            logger.info(
                "通过手机/邮箱匹配更新 CRM 联系人 %s (owner=%s, target=%s)",
                existing.id, owner_id, target_user.id,
            )
            return existing

    # ── 3. 创建新联系人 ──────────────────────────────────────────────
    default_stage_id = await _ensure_default_stage(db, owner_id)

    contact = CrmContact(
        owner_id=owner_id,
        user_id=target_user.id,
        name=target_user.name or "",
        phone=target_user.phone or "",
        email=target_user.email or "",
        company=target_user.company or "",
        title=target_user.title or "",
        avatar=target_user.avatar or "",
        intro="",
        source="match",
        source_record_id=match_record.id,
        tags="[]",
        pipeline_stage_id=default_stage_id,
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    logger.info(
        "从名片交换自动创建 CRM 联系人 %s (owner=%s, target=%s)",
        contact.id, owner_id, target_user.id,
    )
    return contact


async def _add_exchange_activity(
    db: AsyncSession,
    contact: CrmContact,
    match_record: MatchRecord,
    is_initiator: bool,
) -> None:
    """为联系人添加名片交换活动记录。"""
    if is_initiator:
        title = f"名片交换: 与对方交换名片"
    else:
        title = f"名片交换: 与对方交换名片"

    activity = CrmActivity(
        owner_id=contact.owner_id,
        contact_id=contact.id,
        activity_type="match",
        title=title,
        description=f"匹配分数: {match_record.match_score}",
        source_model="match_records",
        source_record_id=match_record.id,
        activity_date=match_record.created_at or datetime.utcnow(),
    )
    db.add(activity)
    await db.commit()
    logger.info(
        "名片交换活动已记录: owner=%s, contact=%s",
        contact.owner_id, contact.id,
    )


async def sync_match_to_crm(
    db: AsyncSession,
    match_record_id: int,
) -> dict:
    """名片交换 → CRM 自动同步。

    为交换双方各创建/更新 CRM 联系人，并记录时间线活动。

    参数:
        db: 数据库会话
        match_record_id: MatchRecord.id

    返回:
        {"user_a_contact_id": int|None, "user_b_contact_id": int|None}
    """
    if not _CRM_AVAILABLE:
        logger.warning("CRM 模块不可用，跳过自动同步 match_id=%s", match_record_id)
        return {"user_a_contact_id": None, "user_b_contact_id": None}

    # 获取匹配记录
    result = await db.execute(
        select(MatchRecord).where(MatchRecord.id == match_record_id)
    )
    match_record = result.scalar_one_or_none()
    if not match_record:
        logger.warning("MatchRecord %s 不存在，跳过 CRM 同步", match_record_id)
        return {"user_a_contact_id": None, "user_b_contact_id": None}

    # 获取双方用户信息
    result = await db.execute(select(User).where(User.id == match_record.user_a_id))
    user_a = result.scalar_one_or_none()
    result = await db.execute(select(User).where(User.id == match_record.user_b_id))
    user_b = result.scalar_one_or_none()
    if not user_a or not user_b:
        logger.warning("MatchRecord %s 关联用户不存在，跳过 CRM 同步", match_record_id)
        return {"user_a_contact_id": None, "user_b_contact_id": None}

    # 为 A 创建 B 的联系人
    contact_a = await _find_or_create_contact(db, user_a.id, user_b, match_record)
    if contact_a:
        await _add_exchange_activity(db, contact_a, match_record, is_initiator=True)

    # 为 B 创建 A 的联系人
    contact_b = await _find_or_create_contact(db, user_b.id, user_a, match_record)
    if contact_b:
        await _add_exchange_activity(db, contact_b, match_record, is_initiator=False)

    return {
        "user_a_contact_id": contact_a.id if contact_a else None,
        "user_b_contact_id": contact_b.id if contact_b else None,
    }
