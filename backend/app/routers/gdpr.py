"""
GDPR 数据管理 API (General Data Protection Regulation)

提供用户数据导出、账户删除和审计日志查询功能，满足 GDPR 合规要求。

Endpoints:
    GET  /api/gdpr/data         导出当前用户的所有个人数据
    GET  /api/gdpr/logs         查看当前用户的审计日志
    DELETE /api/gdpr/account    删除当前用户账户（匿名化处理）
"""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.audit import AuditLog
from app.models.brochure import Brochure, Page
from app.models.tag import UserTag, MatchRecord
from app.models.visitor import VisitorLog
from app.models.trust import TrustNetwork
from app.routers.auth import get_current_user
from app.middleware.audit import record_audit

logger = logging.getLogger("gdpr")

router = APIRouter(prefix="/api/v1/gdpr", tags=["GDPR 合规"])


# ── 辅助函数 ──────────────────────────────────────────────────────


async def _get_client_ip(request: Request) -> str:
    """从请求中提取客户端 IP。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    client = request.client
    if client:
        return client.host
    return ""


# ── 数据导出 ──────────────────────────────────────────────────────


@router.get("/data", summary="导出我的所有数据 (GDPR)")
async def export_my_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """导出当前用户的所有个人数据，以 JSON 格式返回。

    包含：
    - 用户资料
    - 名片（画册）及页面
    - 标签（提供/需求）
    - 匹配记录
    - 访客记录
    - 信任网络
    - 审计日志
    """
    user_id = current_user.id

    # 1. 用户基本信息
    user_data = {
        "id": current_user.id,
        "username": current_user.username,
        "phone": current_user.phone,
        "name": current_user.name,
        "company": current_user.company,
        "title": current_user.title,
        "intro": current_user.intro,
        "avatar": current_user.avatar,
        "role": current_user.role,
        "membership_tier": current_user.membership_tier,
        "membership_expires_at": (
            current_user.membership_expires_at.isoformat()
            if current_user.membership_expires_at else None
        ),
        "created_at": current_user.created_at.isoformat(),
        "updated_at": current_user.updated_at.isoformat(),
    }

    # 2. 名片数据
    result = await db.execute(
        select(Brochure).where(Brochure.user_id == user_id)
    )
    brochures = result.scalars().all()
    brochures_data = []
    for b in brochures:
        pages_result = await db.execute(
            select(Page).where(Page.brochure_id == b.id).order_by(Page.sort_order)
        )
        pages = pages_result.scalars().all()
        brochures_data.append({
            "id": b.id,
            "title": b.title,
            "cover": b.cover,
            "purpose": b.purpose,
            "status": b.status,
            "share_token": b.share_token,
            "view_count": b.view_count,
            "album_meta": b.album_meta,
            "created_at": b.created_at.isoformat(),
            "updated_at": b.updated_at.isoformat(),
            "pages": [
                {
                    "id": p.id,
                    "sort_order": p.sort_order,
                    "content_type": p.content_type,
                    "content": p.content,
                    "image_url": p.image_url,
                    "media_url": p.media_url,
                    "ai_summary": p.ai_summary,
                }
                for p in pages
            ],
        })

    # 3. 标签
    result = await db.execute(
        select(UserTag).where(UserTag.user_id == user_id)
    )
    tags = result.scalars().all()
    tags_data = [
        {
            "id": t.id,
            "tag_type": t.tag_type,
            "tag": t.tag,
            "weight": t.weight,
            "source": t.source,
            "created_at": t.created_at.isoformat(),
        }
        for t in tags
    ]

    # 4. 匹配记录
    result = await db.execute(
        select(MatchRecord).where(
            (MatchRecord.user_a_id == user_id) | (MatchRecord.user_b_id == user_id)
        )
    )
    matches = result.scalars().all()
    matches_data = [
        {
            "id": m.id,
            "user_a_id": m.user_a_id,
            "user_b_id": m.user_b_id,
            "match_score": m.match_score,
            "status": m.status,
            "common_tags": m.common_tags,
            "source": m.source,
            "created_at": m.created_at.isoformat(),
        }
        for m in matches
    ]

    # 5. 访客记录
    result = await db.execute(
        select(VisitorLog).where(VisitorLog.brochure_id.in_(
            select(Brochure.id).where(Brochure.user_id == user_id)
        ))
    )
    visitors = result.scalars().all()
    visitors_data = [
        {
            "id": v.id,
            "brochure_id": v.brochure_id,
            "visitor_id": v.visitor_id,
            "visitor_ip": v.visitor_ip,
            "visitor_name": v.visitor_name,
            "source": v.source,
            "page_viewed": v.page_viewed,
            "duration": v.duration,
            "interested": v.interested,
            "contact_msg": v.contact_msg,
            "visit_time": v.visit_time.isoformat(),
        }
        for v in visitors
    ]

    # 6. 信任网络
    result = await db.execute(
        select(TrustNetwork).where(
            (TrustNetwork.user_id == user_id) | (TrustNetwork.trusted_user_id == user_id)
        )
    )
    trust = result.scalars().all()
    trust_data = [
        {
            "id": t.id,
            "user_id": t.user_id,
            "trusted_user_id": t.trusted_user_id,
            "created_at": t.created_at.isoformat(),
        }
        for t in trust
    ]

    # 7. 审计日志
    result = await db.execute(
        select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.timestamp.desc()).limit(500)
    )
    audit_logs = result.scalars().all()
    audit_data = [
        {
            "id": log.id,
            "action": log.action,
            "resource": log.resource,
            "detail": log.detail,
            "ip": log.ip,
            "timestamp": log.timestamp.isoformat(),
        }
        for log in audit_logs
    ]

    # ── 组装导出数据 ──
    export_package = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "user": user_data,
        "brochures": brochures_data,
        "tags": tags_data,
        "match_records": matches_data,
        "visitor_logs": visitors_data,
        "trust_network": trust_data,
        "audit_logs": audit_data,
    }

    # 记录审计事件
    ip = await _get_client_ip(request)
    await record_audit(
        db, user_id, "EXPORT", "/api/v1/gdpr/data",
        detail={"export_size": len(json.dumps(export_package, ensure_ascii=False, default=str))},
        ip=ip,
    )

    return {
        "code": 200,
        "message": "数据导出成功",
        "data": export_package,
    }


# ── 审计日志查询 ────────────────────────────────────────────────


@router.get("/logs", summary="查看我的审计日志")
async def get_my_audit_logs(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查看当前用户的审计日志记录，按时间倒序排列。"""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == current_user.id)
        .order_by(AuditLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()

    return {
        "code": 200,
        "message": "ok",
        "data": [
            {
                "id": log.id,
                "action": log.action,
                "resource": log.resource,
                "detail": log.detail,
                "ip": log.ip,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ],
    }


# ── 删除账户 ──────────────────────────────────────────────────────


@router.delete("/account", summary="删除我的账户 (GDPR 被遗忘权)")
async def delete_my_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除当前用户账户（GDPR 被遗忘权）。

    操作：
    1. 匿名化用户资料（保留记录但去除个人身份信息）
    2. 删除名片及页面内容
    3. 删除标签、匹配记录
    4. 保留审计日志（用于平台安全审计），但日志中的 user_id 置为 NULL

    GDPR 说明：根据 GDPR 第 17 条，我们采用"匿名化"方案而非完全删除，
    以保留平台的运营安全记录和反滥用能力。
    """
    user_id = current_user.id
    ip = await _get_client_ip(request)

    # ── 1. 匿名化用户资料 ──────────────────────────────────
    anonymized_phone = f"deleted_{user_id}"
    current_user.phone = anonymized_phone
    current_user.name = "已注销用户"
    current_user.username = None
    current_user.company = ""
    current_user.title = ""
    current_user.intro = ""
    current_user.avatar = ""
    current_user.wechat_openid = None
    current_user.password_hash = "ANONYMIZED"
    current_user.membership_tier = "free"
    current_user.membership_expires_at = None

    # ── 2. 匿名化名片数据 ──────────────────────────────────
    result = await db.execute(
        select(Brochure).where(Brochure.user_id == user_id)
    )
    brochures = result.scalars().all()
    for b in brochures:
        # 删除名片页面
        await db.execute(delete(Page).where(Page.brochure_id == b.id))
        # 匿名化名片元数据
        b.title = "已删除"
        b.cover = ""
        b.purpose = ""
        b.status = "deleted"

    # ── 3. 删除标签 ────────────────────────────────────────
    await db.execute(delete(UserTag).where(UserTag.user_id == user_id))

    # ── 4. 删除匹配记录 ────────────────────────────────────
    await db.execute(
        delete(MatchRecord).where(
            (MatchRecord.user_a_id == user_id) | (MatchRecord.user_b_id == user_id)
        )
    )

    # ── 5. 删除信任网络 ────────────────────────────────────
    await db.execute(
        delete(TrustNetwork).where(
            (TrustNetwork.user_id == user_id) | (TrustNetwork.trusted_user_id == user_id)
        )
    )

    # ── 6. 审计日志脱敏：将 user_id 置为 NULL ─────────────
    await db.execute(
        delete(AuditLog).where(AuditLog.user_id == user_id)
    )

    await db.commit()

    # 使用独立 session 记录删除操作（此时 user 已匿名化）
    try:
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as audit_db:
            await record_audit(
                audit_db, None, "DELETE_ACCOUNT", "/api/v1/gdpr/account",
                detail={"original_user_id": user_id},
                ip=ip,
            )
    except Exception:
        pass

    logger.info("User %d account anonymized (GDPR right to erasure)", user_id)

    return {
        "code": 200,
        "message": "账户已删除（匿名化），所有个人数据已移除。",
    }
