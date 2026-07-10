"""
NFC 数字名片 API 路由
──────────────────────
提供 NFC 标签的完整 CRUD、vCard 下载、碰触分享及统计。

路由前缀: /api/v1/nfc
（通过 APIVersionRedirectMiddleware 自动重写为 /api/nfc）

API 清单:
  POST   /api/v1/nfc/cards                   — 注册 NFC 标签（写入卡片数据）
  GET    /api/v1/nfc/cards                   — 获取用户的 NFC 卡片列表
  GET    /api/v1/nfc/cards/{nfc_uid}         — 按 NFC UID 获取名片信息
  PUT    /api/v1/nfc/cards/{nfc_uid}         — 更新 NFC 卡片内容
  DELETE /api/v1/nfc/cards/{nfc_uid}         — 注销 NFC 标签
  GET    /api/v1/nfc/cards/{nfc_uid}/vcard   — 获取 vCard 格式下载
  POST   /api/v1/nfc/share                   — 碰触分享记录（谁碰了谁）
  GET    /api/v1/nfc/stats                   — NFC 碰触统计
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.nfc_card import NFCCard
from app.models.nfc_tap import NfcTapRecord
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.nfc_service import (
    build_ndef_records,
    check_nfc_uid_available,
    generate_vcard_40,
    get_tap_stats,
    record_tap_event,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nfc", tags=["NFC"])


# ────────────────────────────────────────────────────────────
# Pydantic 请求/响应模型
# ────────────────────────────────────────────────────────────


from pydantic import BaseModel, Field


class NfcCardRegister(BaseModel):
    """注册 NFC 标签请求"""

    nfc_uid: str = Field(
        ..., min_length=4, max_length=64,
        description="NFC 标签硬件 UID（如 04:AB:CD:EF:12:34:56:78）",
    )
    card_data: dict[str, Any] = Field(
        ..., description="名片数据 JSON，包含 name/company/title/phone/email 等字段",
    )
    share_url: str = Field(
        "", description="名片在线查看链接（将写入 NDEF Record 2）",
    )


class NfcCardUpdate(BaseModel):
    """更新 NFC 标签请求"""

    card_data: dict[str, Any] | None = Field(
        None, description="更新的名片数据 JSON",
    )
    share_url: str | None = Field(
        None, description="更新的分享链接",
    )


class TapShareRecord(BaseModel):
    """碰触分享记录请求"""

    from_user_id: int = Field(
        ..., description="发起碰触的用户 ID（碰的人）",
    )
    to_user_id: int = Field(
        ..., description="被碰触的用户 ID（名片主人）",
    )
    nfc_uid: str = Field(
        ..., min_length=4, max_length=64,
        description="被碰触的 NFC 标签 UID",
    )


# ────────────────────────────────────────────────────────────
# API 端点
# ────────────────────────────────────────────────────────────


@router.post("/cards")
async def register_nfc_card(
    data: NfcCardRegister,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    注册 NFC 标签 — 将名片数据绑定到 NFC 标签。

    自动生成:
      - vCard 4.0 格式文本（缓存至 vcard_raw 字段）
      - NDEF 标准记录（可通过 GET /cards/{nfc_uid}/ndef 获取）
    """
    # UID 冲突检测
    available = await check_nfc_uid_available(db, data.nfc_uid)
    if not available:
        raise HTTPException(
            status_code=409,
            detail=f"NFC UID {data.nfc_uid} 已被绑定到其他名片",
        )

    # 序列化 card_data
    card_data_json = json.dumps(data.card_data, ensure_ascii=False)
    # 生成 vCard
    vcard_raw = generate_vcard_40(data.card_data)
    # 构建 NDEF
    ndef_records = build_ndef_records(data.card_data, data.share_url)

    card = NFCCard(
        user_id=current_user.id,
        nfc_uid=data.nfc_uid,
        card_data_json=card_data_json,
        vcard_raw=vcard_raw,
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)

    logger.info(
        "NFC card registered: user=%d, nfc_uid=%s",
        current_user.id, data.nfc_uid,
    )

    return {
        "code": 200,
        "message": "NFC 标签注册成功",
        "data": {
            "id": card.id,
            "user_id": card.user_id,
            "nfc_uid": card.nfc_uid,
            "created_at": card.created_at.isoformat() if card.created_at else None,
            "vcard_preview": vcard_raw[:200] + "..." if len(vcard_raw) > 200 else vcard_raw,
            "ndef_records": ndef_records,
        },
    }


@router.get("/cards")
async def list_nfc_cards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):
    """获取当前用户的 NFC 卡片列表（分页）。"""
    from sqlalchemy import func as sa_func

    # 总数
    count_stmt = (
        select(sa_func.count(NFCCard.id))
        .where(NFCCard.user_id == current_user.id)
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # 分页查询
    offset_val = (page - 1) * page_size
    stmt = (
        select(NFCCard)
        .where(NFCCard.user_id == current_user.id)
        .order_by(NFCCard.created_at.desc())
        .offset(offset_val)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    cards = result.scalars().all()

    return {
        "code": 200,
        "message": "ok",
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": c.id,
                    "user_id": c.user_id,
                    "nfc_uid": c.nfc_uid,
                    "card_data": json.loads(c.card_data_json) if c.card_data_json else {},
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                }
                for c in cards
            ],
        },
    }


@router.get("/cards/{nfc_uid}")
async def get_nfc_card(
    nfc_uid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """按 NFC UID 获取名片信息。"""
    stmt = select(NFCCard).where(
        NFCCard.nfc_uid == nfc_uid,
        NFCCard.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=404,
            detail=f"NFC 标签 {nfc_uid} 未找到或不属于当前用户",
        )

    ndef_records = build_ndef_records(
        json.loads(card.card_data_json) if card.card_data_json else {},
        "",  # share_url not stored separately currently
    )

    return {
        "code": 200,
        "message": "ok",
        "data": {
            "id": card.id,
            "user_id": card.user_id,
            "nfc_uid": card.nfc_uid,
            "card_data": json.loads(card.card_data_json) if card.card_data_json else {},
            "vcard_raw": card.vcard_raw,
            "ndef_records": ndef_records,
            "created_at": card.created_at.isoformat() if card.created_at else None,
            "updated_at": card.updated_at.isoformat() if card.updated_at else None,
        },
    }


@router.put("/cards/{nfc_uid}")
async def update_nfc_card(
    nfc_uid: str,
    data: NfcCardUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新 NFC 卡片内容（名片数据 / 分享链接）。"""
    stmt = select(NFCCard).where(
        NFCCard.nfc_uid == nfc_uid,
        NFCCard.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=404,
            detail=f"NFC 标签 {nfc_uid} 未找到或不属于当前用户",
        )

    # 更新字段
    if data.card_data is not None:
        card.card_data_json = json.dumps(data.card_data, ensure_ascii=False)
        card.vcard_raw = generate_vcard_40(data.card_data)

    await db.commit()
    await db.refresh(card)

    return {
        "code": 200,
        "message": "NFC 卡片更新成功",
        "data": {
            "id": card.id,
            "nfc_uid": card.nfc_uid,
            "updated_at": card.updated_at.isoformat() if card.updated_at else None,
        },
    }


@router.delete("/cards/{nfc_uid}")
async def delete_nfc_card(
    nfc_uid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """注销 NFC 标签（解除绑定）。"""
    stmt = select(NFCCard).where(
        NFCCard.nfc_uid == nfc_uid,
        NFCCard.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=404,
            detail=f"NFC 标签 {nfc_uid} 未找到或不属于当前用户",
        )

    await db.delete(card)
    await db.commit()

    return {
        "code": 200,
        "message": f"NFC 标签 {nfc_uid} 已成功注销",
    }


@router.get("/cards/{nfc_uid}/vcard")
async def download_vcard(
    nfc_uid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取 vCard 4.0 格式下载。

    返回 text/vcard 内容，浏览器自动触发下载。
    """
    stmt = select(NFCCard).where(
        NFCCard.nfc_uid == nfc_uid,
    )
    result = await db.execute(stmt)
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=404,
            detail=f"NFC 标签 {nfc_uid} 未找到",
        )

    # 如果有缓存的 vcard_raw 则使用，否则重新生成
    if card.vcard_raw:
        vcard_text = card.vcard_raw
    else:
        card_data = json.loads(card.card_data_json) if card.card_data_json else {}
        vcard_text = generate_vcard_40(card_data)

    # 从 card_data 提取文件名
    card_data = json.loads(card.card_data_json) if card.card_data_json else {}
    name = card_data.get("name", "contact").replace(" ", "_")

    return PlainTextResponse(
        content=vcard_text,
        media_type="text/vcard",
        headers={
            "Content-Disposition": f'attachment; filename="{name}.vcf"',
        },
    )


@router.post("/share")
async def record_tap(
    data: TapShareRecord,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    记录一次 NFC 碰触分享事件。

    谁（from_user_id）通过碰触获取了谁（to_user_id）的名片。
    调用方：移动端 NFC 读取成功后的回调。
    """
    # 验证 NFC 标签存在
    stmt = select(NFCCard).where(NFCCard.nfc_uid == data.nfc_uid)
    result = await db.execute(stmt)
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=404,
            detail=f"NFC 标签 {data.nfc_uid} 未在系统中注册",
        )

    # 记录碰触事件
    tap_record = await record_tap_event(
        db=db,
        from_user_id=data.from_user_id,
        to_user_id=data.to_user_id,
        nfc_uid=data.nfc_uid,
    )

    return {
        "code": 200,
        "message": "碰触分享记录成功",
        "data": {
            "tap_id": tap_record.id,
            "from_user_id": tap_record.from_user_id,
            "to_user_id": tap_record.to_user_id,
            "nfc_uid": tap_record.nfc_uid,
            "created_at": tap_record.created_at.isoformat() if tap_record.created_at else None,
        },
    }


@router.get("/stats")
async def nfc_tap_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
):
    """获取当前用户的 NFC 碰触统计。"""
    stats = await get_tap_stats(db=db, user_id=current_user.id, days=days)

    return {
        "code": 200,
        "message": "ok",
        "data": stats,
    }
