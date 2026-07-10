"""
NFC 服务层
───────────
提供:
  - vCard 4.0 生成器（从名片数据自动构建标准 vCard）
  - NDEF 记录编码/解码
  - 碰触事件记录与管理
  - NFC UID 冲突检测
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.nfc_card import NFCCard
from app.models.nfc_tap import NfcTapRecord

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────
# vCard 4.0 生成器
# ────────────────────────────────────────────────────────────


def generate_vcard_40(card_data: dict[str, Any]) -> str:
    """
    从名片数据自动生成标准 vCard 4.0 格式。

    支持的字段:
      name, company, title, phone, email, website, avatar_url,
      address, social (dict), birthday, note

    符合 RFC 6350 (vCard 4.0) 标准。
    """
    lines: list[str] = [
        "BEGIN:VCARD",
        "VERSION:4.0",
    ]

    # ── 名称 ────────────────────────────────────────────────
    name = card_data.get("name", "")
    if name:
        family = card_data.get("family_name", "")
        given = card_data.get("given_name", name)
        lines.append(f"N:{family};{given};;;")
        lines.append(f"FN:{name}")

    # ── 组织 & 职位 ─────────────────────────────────────────
    company = card_data.get("company", "")
    title = card_data.get("title", "")
    if company:
        lines.append(f"ORG:{company}")
    if title:
        lines.append(f"TITLE:{title}")

    # ── 电话号码 ────────────────────────────────────────────
    phone = card_data.get("phone", "")
    if phone:
        lines.append(f"TEL;TYPE=cell,voice:{_sanitize_phone(phone)}")

    phone2 = card_data.get("phone2", "")
    if phone2:
        lines.append(f"TEL;TYPE=work,voice:{_sanitize_phone(phone2)}")

    # ── 邮箱 ────────────────────────────────────────────────
    email = card_data.get("email", "")
    if email:
        lines.append(f"EMAIL:{email}")

    # ── 网址 ────────────────────────────────────────────────
    website = card_data.get("website", "")
    if website:
        lines.append(f"URL:{website}")

    # ── 头像 ────────────────────────────────────────────────
    avatar_url = card_data.get("avatar_url", "")
    if avatar_url:
        lines.append(f"PHOTO;MEDIATYPE=image/jpeg:{avatar_url}")

    # ── 地址 ────────────────────────────────────────────────
    address = card_data.get("address", "")
    if address:
        lines.append(f"ADR:;;{address};;;")

    # ── 社交媒体 ────────────────────────────────────────────
    social = card_data.get("social", {}) or {}
    if isinstance(social, dict):
        wechat = social.get("wechat", "")
        if wechat:
            lines.append(f"X-SOCIAL-WECHAT:{wechat}")
        linkedin = social.get("linkedin", "")
        if linkedin:
            lines.append(f"X-SOCIAL-LINKEDIN:{linkedin}")
        weibo = social.get("weibo", "")
        if weibo:
            lines.append(f"X-SOCIAL-WEIBO:{weibo}")

    # ── 生日 ────────────────────────────────────────────────
    birthday = card_data.get("birthday", "")
    if birthday:
        lines.append(f"BDAY:{birthday}")

    # ── 备注 ────────────────────────────────────────────────
    note = card_data.get("note", "")
    if note:
        for line in note.split("\n"):
            lines.append(f"NOTE:{line.strip()}")

    # ── 时间戳 & UID ────────────────────────────────────────
    now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines.append(f"REV:{now_str}")
    lines.append(f"UID:{_generate_uid(card_data)}")

    lines.append("END:VCARD")
    return "\r\n".join(lines) + "\r\n"


def _sanitize_phone(phone: str) -> str:
    """清理电话号码：去除空格、横线、括号，保留 + 号。"""
    allowed = set("+0123456789")
    return "".join(ch for ch in phone if ch in allowed)


def _generate_uid(card_data: dict[str, Any]) -> str:
    """基于 name + email 或 phone 生成稳定 UID。"""
    import uuid
    name = card_data.get("name", "unknown")
    email = card_data.get("email", "")
    phone = card_data.get("phone", "")
    if email:
        return f"{name}-{email}" if name else email
    if phone:
        return f"{name}-{phone}" if name else phone
    return str(uuid.uuid4())


# ────────────────────────────────────────────────────────────
# NDEF 编码/解码
# ────────────────────────────────────────────────────────────


def build_ndef_records(
    card_data: dict[str, Any],
    share_url: str = "",
) -> list[dict[str, Any]]:
    """
    构建 NDEF 标准记录列表（三个记录）。

    返回适合手机端 NFC 写入库消费的 JSON 结构:
      [
        {"type": "vcard",   "payload": "BEGIN:VCARD...END:VCARD"},
        {"type": "url",     "payload": "https://..."},
        {"type": "json",    "payload": '{"app":"ai_bizcard","version":"1.0"}'},
      ]
    """
    vcard_text = generate_vcard_40(card_data)

    ndef_records: list[dict[str, Any]] = [
        {"type": "vcard", "payload": vcard_text},
    ]

    if share_url:
        ndef_records.append({"type": "url", "payload": share_url})

    custom_payload = {
        "app": "ai_bizcard",
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    ndef_records.append(
        {"type": "json", "payload": json.dumps(custom_payload, ensure_ascii=False)}
    )

    return ndef_records


def parse_ndef_records(ndef_records: list[dict[str, Any]]) -> dict[str, Any]:
    """
    解析 NDEF 记录列表，提取名片数据。

    返回:
      {
        "vcard": "BEGIN:VCARD...",
        "url": "https://...",
        "app_data": {"app": "ai_bizcard", ...},
      }
    """
    result: dict[str, Any] = {"vcard": "", "url": "", "app_data": {}}
    for record in ndef_records:
        rtype = record.get("type", "")
        payload = record.get("payload", "")
        if rtype == "vcard":
            result["vcard"] = payload
        elif rtype == "url":
            result["url"] = payload
        elif rtype == "json":
            try:
                result["app_data"] = (
                    json.loads(payload) if isinstance(payload, str) else payload
                )
            except (json.JSONDecodeError, TypeError):
                result["app_data"] = {"raw": payload}
    return result


# ────────────────────────────────────────────────────────────
# NFC UID 冲突检测
# ────────────────────────────────────────────────────────────


async def check_nfc_uid_available(
    db: AsyncSession,
    nfc_uid: str,
    exclude_card_id: int | None = None,
) -> bool:
    """
    检测 NFC UID 是否可用（未被绑定）。

    Args:
        db: 数据库 session
        nfc_uid: 待检测的 NFC 标签 UID
        exclude_card_id: 排除的卡片 ID（更新场景）

    Returns:
        True 表示可用的 UID，False 表示已被绑定
    """
    stmt = select(NFCCard).where(NFCCard.nfc_uid == nfc_uid)
    if exclude_card_id is not None:
        stmt = stmt.where(NFCCard.id != exclude_card_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is None


# ────────────────────────────────────────────────────────────
# 碰触事件记录
# ────────────────────────────────────────────────────────────


async def record_tap_event(
    db: AsyncSession,
    from_user_id: int,
    to_user_id: int,
    nfc_uid: str,
) -> NfcTapRecord:
    """
    记录一次 NFC 碰触事件。

    Args:
        db: 数据库 session
        from_user_id: 发起碰触的用户 ID（碰的人）
        to_user_id: 被碰触的用户 ID（名片主人）
        nfc_uid: NFC 标签 UID

    Returns:
        NfcTapRecord ORM 对象
    """
    record = NfcTapRecord(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        nfc_uid=nfc_uid,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(
        "NFC Tap: from_user=%d tapped to_user=%d via nfc_uid=%s",
        from_user_id, to_user_id, nfc_uid,
    )
    return record


async def get_tap_stats(
    db: AsyncSession,
    user_id: int,
    days: int = 30,
) -> dict[str, Any]:
    """
    获取用户的 NFC 碰触统计。

    Args:
        db: 数据库 session
        user_id: 用户 ID
        days: 统计天数（默认 30 天）

    Returns:
        {
            "total_taps_received": N,  # 被碰触次数
            "total_taps_given": N,     # 碰触别人次数
            "unique_tappers": N,       # 不同碰触者数
            "recent_taps": [...],      # 最近碰触记录
            "daily_taps": [...],       # 每日碰触趋势
        }
    """
    from sqlalchemy import func as sa_func

    # 被碰触次数（别人碰我的名片）
    count_received = await db.execute(
        select(sa_func.count(NfcTapRecord.id)).where(
            NfcTapRecord.to_user_id == user_id
        )
    )
    total_received = count_received.scalar() or 0

    # 碰触别人次数
    count_given = await db.execute(
        select(sa_func.count(NfcTapRecord.id)).where(
            NfcTapRecord.from_user_id == user_id
        )
    )
    total_given = count_given.scalar() or 0

    # 不同碰触者数
    unique_stmt = (
        select(sa_func.count(sa_func.distinct(NfcTapRecord.from_user_id)))
        .where(NfcTapRecord.to_user_id == user_id)
    )
    unique_result = await db.execute(unique_stmt)
    unique_tappers = unique_result.scalar() or 0

    # 最近碰触记录
    recent_stmt = (
        select(NfcTapRecord)
        .where(
            (NfcTapRecord.to_user_id == user_id)
            | (NfcTapRecord.from_user_id == user_id)
        )
        .order_by(NfcTapRecord.created_at.desc())
        .limit(20)
    )
    recent_result = await db.execute(recent_stmt)
    recent_taps = [
        {
            "id": r.id,
            "from_user_id": r.from_user_id,
            "to_user_id": r.to_user_id,
            "nfc_uid": r.nfc_uid,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recent_result.scalars().all()
    ]

    # 每日碰触趋势（过去 days 天）
    since = datetime.now(timezone.utc) - timedelta(days=days)
    daily_stmt = (
        select(
            sa_func.date(NfcTapRecord.created_at).label("day"),
            sa_func.count(NfcTapRecord.id).label("cnt"),
        )
        .where(
            (NfcTapRecord.to_user_id == user_id)
            | (NfcTapRecord.from_user_id == user_id)
        )
        .where(NfcTapRecord.created_at >= since)
        .group_by(sa_func.date(NfcTapRecord.created_at))
        .order_by(sa_func.date(NfcTapRecord.created_at).asc())
    )
    daily_result = await db.execute(daily_stmt)
    daily_taps = [
        {"date": str(row.day), "count": row.cnt}
        for row in daily_result.fetchall()
    ]

    return {
        "total_taps_received": total_received,
        "total_taps_given": total_given,
        "unique_tappers": unique_tappers,
        "recent_taps": recent_taps,
        "daily_taps": daily_taps,
    }
