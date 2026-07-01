"""数据导出 API — 支持 CSV / JSON 格式导出用户名片及相关数据。"""
import csv
import io
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.user import User
from app.models.brochure import Brochure
from app.models.tag import UserTag
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/export", tags=["数据导出"])


def _build_card_data(user: User, db_brochures: list[Brochure]) -> dict[str, Any]:
    """将用户及其名片数据组装为统一字典格式。"""
    return {
        "user_id": user.id,
        "name": user.name,
        "phone": user.phone,
        "company": user.company,
        "title": user.title,
        "intro": user.intro,
        "avatar": user.avatar,
        "role": user.role,
        "membership_tier": user.membership_tier,
        "membership_expires_at": (
            user.membership_expires_at.isoformat()
            if user.membership_expires_at else None
        ),
        "brochures": [
            {
                "id": b.id,
                "title": b.title,
                "purpose": b.purpose,
                "status": b.status,
                "share_token": b.share_token,
                "view_count": b.view_count,
                "pages_count": b.pages_count,
                "created_at": b.created_at.isoformat(),
                "updated_at": b.updated_at.isoformat(),
            }
            for b in db_brochures
        ],
        "tags": [],  # 下面由调用方补充
        "exported_at": datetime.utcnow().isoformat() + "Z",
    }


async def _load_tags(
    db: AsyncSession, user_id: int,
) -> list[dict[str, Any]]:
    """加载用户标签。"""
    from app.models.tag import UserTag

    result = await db.execute(
        select(UserTag).where(UserTag.user_id == user_id)
    )
    tags = result.scalars().all()
    return [
        {
            "id": t.id,
            "tag_type": t.tag_type,
            "tag": t.tag,
            "weight": t.weight,
            "source": t.source,
        }
        for t in tags
    ]


def _flatten_for_csv(record: dict[str, Any]) -> list[dict[str, str]]:
    """将嵌套的卡片数据展平为 CSV 行列表（一个 brochure 一行）。"""
    rows: list[dict[str, str]] = []
    base = {
        "user_id": str(record.get("user_id", "")),
        "name": record.get("name", ""),
        "phone": record.get("phone", ""),
        "company": record.get("company", ""),
        "title": record.get("title", ""),
        "intro": record.get("intro", ""),
        "role": record.get("role", ""),
        "membership_tier": record.get("membership_tier", ""),
        "membership_expires_at": record.get("membership_expires_at") or "",
        "exported_at": record.get("exported_at", ""),
    }
    tags_str = "; ".join(
        f"{t['tag']}({t['tag_type']})" for t in record.get("tags", [])
    )
    base["tags"] = tags_str

    brochures = record.get("brochures", [])
    if brochures:
        for b in brochures:
            row = {
                **base,
                "brochure_id": str(b.get("id", "")),
                "brochure_title": b.get("title", ""),
                "purpose": b.get("purpose", ""),
                "status": b.get("status", ""),
                "share_token": b.get("share_token", ""),
                "view_count": str(b.get("view_count", 0)),
                "pages_count": str(b.get("pages_count", 0)),
                "brochure_created_at": b.get("created_at", ""),
                "brochure_updated_at": b.get("updated_at", ""),
            }
            rows.append(row)
    else:
        rows.append({**base, **{k: "" for k in [
            "brochure_id", "brochure_title", "purpose", "status",
            "share_token", "view_count", "pages_count",
            "brochure_created_at", "brochure_updated_at",
        ]}})
    return rows


CSV_HEADERS = [
    "user_id", "name", "phone", "company", "title", "intro",
    "role", "membership_tier", "membership_expires_at",
    "tags", "brochure_id", "brochure_title", "purpose", "status",
    "share_token", "view_count", "pages_count",
    "brochure_created_at", "brochure_updated_at", "exported_at",
]


# ── 导出端点 ─────────────────────────────────────────────────────────────


@router.get("/json")
async def export_json(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """以 JSON 格式导出当前用户的所有名片数据（含标签）。"""
    # 加载用户的 brochure
    result = await db.execute(
        select(Brochure)
        .where(Brochure.user_id == current_user.id)
        .order_by(Brochure.created_at.desc())
    )
    brochures = list(result.scalars().all())

    data = _build_card_data(current_user, brochures)
    data["tags"] = await _load_tags(db, current_user.id)

    filename = f"card_export_{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    content = json.dumps(data, ensure_ascii=False, indent=2)

    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content.encode("utf-8"))),
        },
    )


@router.get("/csv")
async def export_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """以 CSV 格式导出当前用户的所有名片数据（含标签）。"""
    # 加载用户的 brochure
    result = await db.execute(
        select(Brochure)
        .where(Brochure.user_id == current_user.id)
        .order_by(Brochure.created_at.desc())
    )
    brochures = list(result.scalars().all())

    data = _build_card_data(current_user, brochures)
    data["tags"] = await _load_tags(db, current_user.id)

    rows = _flatten_for_csv(data)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_HEADERS)
    writer.writeheader()
    writer.writerows(rows)

    content = output.getvalue()
    filename = f"card_export_{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content.encode("utf-8"))),
        },
    )
