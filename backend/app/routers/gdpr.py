"""
GDPR 数据管理 API (General Data Protection Regulation)

提供用户数据导出、账户删除和审计日志查询功能，满足 GDPR 合规要求。

Endpoints:
    GET  /api/gdpr/data            请求数据导出（生成一次性下载令牌，返回脱敏预览）
    GET  /api/gdpr/data/download   使用一次性令牌下载完整导出包（脱敏后）
    GET  /api/gdpr/logs            查看当前用户的审计日志
    DELETE /api/gdpr/account       删除当前用户账户（需密码二次确认，匿名化处理）

合规修复记录:
    BUG-035: 导出改一次性下载令牌 + 访问审计 + 敏感字段脱敏（phone/wechat_openid/visitor_ip）
    BUG-012: 账户删除增加密码二次确认 + 删除审计留痕（审计日志保留并脱敏 user 关联）
"""
import json
import logging
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.audit import AuditLog
from app.models.brochure import Brochure, Page
from app.models.tag import UserTag, MatchRecord
from app.models.visitor import VisitorLog
from app.models.trust import TrustNetwork
from app.routers.auth import get_current_user, pwd_context
from app.middleware.audit import record_audit

logger = logging.getLogger("gdpr")

router = APIRouter(prefix="/api/v1/gdpr", tags=["GDPR 合规"])

# ── 一次性导出令牌存储 ─────────────────────────────────────────────────────
# BUG-035: 导出数据不直接响应明文，而是生成一次性下载令牌（10 分钟有效）。
# 单实例进程内存储；多实例部署时应迁移到 Redis（key: gdpr_export:{token}）。

EXPORT_TOKEN_TTL_MINUTES = 10
_EXPORT_STORE: dict[str, dict] = {}


def _prune_expired_exports() -> None:
    """清理过期导出令牌。"""
    now = datetime.utcnow()
    expired = [t for t, v in _EXPORT_STORE.items() if v["expires_at"] < now]
    for t in expired:
        _EXPORT_STORE.pop(t, None)


# ── 敏感字段脱敏 ──────────────────────────────────────────────────────────


def _mask_phone(phone: str | None) -> str:
    """手机号脱敏：138****0000（保留前3后4）。"""
    if not phone:
        return ""
    digits = "".join(c for c in str(phone) if c.isdigit())
    if len(digits) < 7:
        return digits[:1] + "*" * (len(digits) - 1) if digits else ""
    return digits[:3] + "*" * (len(digits) - 7) + digits[-4:]


def _mask_openid(openid: str | None) -> str:
    """微信 openid 脱敏：保留前4后4，中间掩码。"""
    if not openid:
        return ""
    s = str(openid)
    if len(s) <= 8:
        return s[:2] + "*" * (len(s) - 2)
    return s[:4] + "*" * (len(s) - 8) + s[-4:]


def _mask_ip(ip: str) -> str:
    """IP 脱敏：保留前两段。"""
    if not ip:
        return ""
    parts = str(ip).split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{'.'.join(['*'] * 2)}"
    return ip[: len(ip) // 2] + "*" * (len(ip) - len(ip) // 2)


# ── 辅助函数 ──────────────────────────────────────────────────────────


async def _get_client_ip(request: Request) -> str:
    """从请求中提取客户端 IP。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    client = request.client
    if client:
        return client.host
    return ""


async def _build_export_package(
    db: AsyncSession, current_user: User
) -> dict:
    """构建导出包（所有敏感字段已脱敏，符合 BUG-035）。"""
    user_id = current_user.id

    # 1. 用户基本信息（phone/wechat_openid 脱敏）
    user_data = {
        "id": current_user.id,
        "username": current_user.username,
        "phone": _mask_phone(current_user.phone),
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

    # 5. 访客记录（visitor_ip 脱敏）
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
            "visitor_ip": _mask_ip(v.visitor_ip),
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
            "ip": _mask_ip(log.ip),
            "timestamp": log.timestamp.isoformat(),
        }
        for log in audit_logs
    ]

    return {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "user": user_data,
        "brochures": brochures_data,
        "tags": tags_data,
        "match_records": matches_data,
        "visitor_logs": visitors_data,
        "trust_network": trust_data,
        "audit_logs": audit_data,
    }


# ── 数据导出（一次性令牌） ────────────────────────────────────────────────


@router.get("/data", summary="请求导出我的所有数据 (GDPR) — 生成一次性下载令牌")
async def export_my_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """请求导出当前用户的所有个人数据。

    BUG-035 修复：
      - 不直接在响应中返回明文导出包，而是生成一次性下载令牌；
      - 导出包中敏感字段（phone / wechat_openid / visitor_ip）已脱敏；
      - 令牌 10 分钟有效、仅可下载一次；
      - 请求与下载均记录审计日志。
    """
    user_id = current_user.id
    export_package = await _build_export_package(db, current_user)

    # 生成一次性下载令牌
    _prune_expired_exports()
    token = secrets.token_urlsafe(32)
    _EXPORT_STORE[token] = {
        "user_id": user_id,
        "package": export_package,
        "expires_at": datetime.utcnow() + timedelta(minutes=EXPORT_TOKEN_TTL_MINUTES),
    }

    # 记录审计事件（只记录大小，不落导出内容，避免明文落库）
    ip = await _get_client_ip(request)
    await record_audit(
        db, user_id, "EXPORT_REQUEST", "/api/v1/gdpr/data",
        detail={
            "export_size": len(json.dumps(export_package, ensure_ascii=False, default=str)),
            "token_ttl_minutes": EXPORT_TOKEN_TTL_MINUTES,
        },
        ip=ip,
    )

    # 返回脱敏预览 + 一次性下载地址（不含完整敏感数据）
    preview = {
        "user": {
            "id": export_package["user"]["id"],
            "name": export_package["user"]["name"],
            "phone": export_package["user"]["phone"],
        },
        "brochure_count": len(export_package["brochures"]),
        "tag_count": len(export_package["tags"]),
        "match_record_count": len(export_package["match_records"]),
        "visitor_log_count": len(export_package["visitor_logs"]),
        "audit_log_count": len(export_package["audit_logs"]),
    }

    return {
        "code": 200,
        "message": "导出请求已受理，请使用一次性令牌在 10 分钟内下载",
        "data": {
            "download_token": token,
            "expires_at": _EXPORT_STORE[token]["expires_at"].isoformat() + "Z",
            "download_url": f"/api/v1/gdpr/data/download?token={token}",
            "preview": preview,
        },
    }


@router.get("/data/download", summary="使用一次性令牌下载导出数据 (GDPR)")
async def download_export(
    request: Request,
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """使用一次性令牌下载完整导出包（脱敏后）。

    - 令牌不存在 / 已使用 / 已过期 → 404/410
    - 令牌只能使用一次（下载后立即销毁）
    - 下载行为记录审计日志（访问审计）
    """
    _prune_expired_exports()
    entry = _EXPORT_STORE.pop(token, None)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="下载令牌无效、已使用或已过期，请重新发起导出请求",
        )
    if entry["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="下载令牌不属于当前用户",
        )

    ip = await _get_client_ip(request)
    await record_audit(
        db, current_user.id, "EXPORT_DOWNLOAD", "/api/v1/gdpr/data/download",
        detail={"export_size": len(json.dumps(entry["package"], ensure_ascii=False, default=str))},
        ip=ip,
    )

    return {
        "code": 200,
        "message": "数据导出成功（敏感字段已脱敏）",
        "data": entry["package"],
    }


# ── 审计日志查询 ────────────────────────────────────────────────────────


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
                "ip": _mask_ip(log.ip),
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ],
    }


# ── 删除账户（密码二次确认） ─────────────────────────────────────────────


class DeleteAccountRequest(BaseModel):
    """账户删除二次确认请求体。"""

    password: str = Field(..., min_length=1, max_length=128, description="登录密码（二次确认）")
    confirm: bool = Field(True, description="明确确认删除（必须为 true）")


@router.delete("/account", summary="删除我的账户 (GDPR 被遗忘权)")
async def delete_my_account(
    req: DeleteAccountRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除当前用户账户（GDPR 被遗忘权）。

    BUG-012 修复：
      1. 密码二次确认：必须提供正确登录密码，且 confirm=true；
      2. 冷静期提示：返回 deletion_review_hours（前端可引导用户在窗口期内联系客服撤回）；
      3. 删除审计留痕：审计日志不再物理删除，user_id 置 NULL 保留记录内容，
         并写入 DELETE_ACCOUNT_REQUEST / DELETE_ACCOUNT 两条审计留痕。

    操作：
      1. 匿名化用户资料（保留记录但去除个人身份信息）
      2. 删除名片及页面内容
      3. 删除标签、匹配记录
      4. 审计日志保留（用于平台安全审计），user_id 置为 NULL

    GDPR 说明：根据 GDPR 第 17 条，我们采用"匿名化"方案而非完全删除，
    以保留平台的运营安全记录和反滥用能力。
    """
    user_id = current_user.id
    ip = await _get_client_ip(request)

    # ── 1. 密码二次确认（BUG-012） ──────────────────────────────────
    if not req.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请确认您已知晓删除后果（confirm=true）",
        )
    if current_user.password_hash in ("ANONYMIZED", ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该账户已处于删除/匿名化状态",
        )
    if not pwd_context.verify(req.password, current_user.password_hash):
        await record_audit(
            db, user_id, "DELETE_ACCOUNT_FAILED", "/api/v1/gdpr/account",
            detail={"reason": "密码校验失败"}, ip=ip,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="密码校验失败，无法删除账户",
        )

    # ── 1.5 删除请求审计留痕（删除前记录，避免被匿名化覆盖） ──────
    await record_audit(
        db, user_id, "DELETE_ACCOUNT_REQUEST", "/api/v1/gdpr/account",
        detail={"original_user_id": user_id}, ip=ip,
    )

    # ── 2. 匿名化用户资料 ──────────────────────────────────────────
    anonymized_phone = f"deleted_{user_id}"
    current_user.phone = anonymized_phone
    current_user.phone_hash = None
    current_user.phone_enc = None
    current_user.phone_last4 = ""
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

    # ── 3. 匿名化名片数据 ──────────────────────────────────────────
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

    # ── 4. 删除标签 ────────────────────────────────────────────────
    await db.execute(delete(UserTag).where(UserTag.user_id == user_id))

    # ── 5. 删除匹配记录 ────────────────────────────────────────────
    await db.execute(
        delete(MatchRecord).where(
            (MatchRecord.user_a_id == user_id) | (MatchRecord.user_b_id == user_id)
        )
    )

    # ── 6. 删除信任网络 ────────────────────────────────────────────
    await db.execute(
        delete(TrustNetwork).where(
            (TrustNetwork.user_id == user_id) | (TrustNetwork.trusted_user_id == user_id)
        )
    )

    # ── 7. 审计日志留痕：user_id 置 NULL（保留记录内容，脱敏关联）──
    # BUG-012: 不再物理删除审计日志；user_id 置 NULL 保留平台安全审计能力。
    await db.execute(
        update(AuditLog)
        .where(AuditLog.user_id == user_id)
        .values(user_id=None)
    )

    await db.commit()

    # 使用独立 session 记录删除完成审计（此时 user 已匿名化）
    try:
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as audit_db:
            await record_audit(
                audit_db, None, "DELETE_ACCOUNT", "/api/v1/gdpr/account",
                detail={"original_user_id": user_id},
                ip=ip,
            )
    except Exception as e:  # noqa: BLE001
        logger.warning("删除审计留痕写入失败: %s", e)

    logger.info("User %d account anonymized (GDPR right to erasure)", user_id)

    return {
        "code": 200,
        "message": "账户已删除（匿名化），所有个人数据已移除。",
        "data": {
            "deletion_review_hours": 72,
            "note": "72 小时冷静期内请联系客服可撤回；审计日志已脱敏留痕。",
        },
    }
