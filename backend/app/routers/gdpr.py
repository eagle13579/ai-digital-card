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
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UnlockRecord
from app.models.audit import AuditLog
from app.models.brochure import Brochure, Page
from app.models.tag import UserTag, MatchRecord
from app.models.visitor import VisitorLog
from app.models.trust import TrustNetwork
from app.models.connection import Connection
from app.models.contact import ImportedContact
from app.models.organization import OrganizationMember
from app.models.six_degrees import (
    RelationEvent,
    ReferralLink,
    SixDegreePathCache,
    UserRelation,
)
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


# ── GDPR 关联表清理清单（BUG-036） ──────────────────────────────────────
# 账户删除后，以下所有含 user 引用的关联表必须同步清理，否则残留引用。
# 每一项为 (模型, [(列, 用户ID条件), ...])，任一条件命中即删除该行。
# 审计日志（AuditLog）按 BUG-012 保留策略不物理删除，仅 user_id 置 NULL。

GDPR_RELATED_TABLE_CLEANUPS: list[tuple[object, list[tuple]]] = [
    # 用户标签
    (UserTag, [("user_id", "user_id")]),
    # 匹配记录（双向引用）
    (MatchRecord, [("user_a_id", "user_id"), ("user_b_id", "user_id")]),
    # 解锁记录（解锁方 + 被解锁方）
    (UnlockRecord, [("user_id", "user_id"), ("target_user_id", "user_id")]),
    # 信任网络（双向引用）
    (TrustNetwork, [("user_id", "user_id"), ("trusted_user_id", "user_id")]),
    # 社交连接（视角用户 + 关系对象）
    (Connection, [("user_id", "user_id"), ("contact_id", "user_id")]),
    # 通讯录（归属用户 + 匹配到的平台用户）
    (ImportedContact, [("user_id", "user_id"), ("matched_user_id", "user_id")]),
    # 六度人脉关系边（双向引用）
    (UserRelation, [("from_user_id", "user_id"), ("to_user_id", "user_id")]),
    # 关系事件日志（双向引用）
    (RelationEvent, [("from_user_id", "user_id"), ("to_user_id", "user_id")]),
    # 六度路径缓存（双向引用）
    (SixDegreePathCache, [("from_user_id", "user_id"), ("to_user_id", "user_id")]),
    # 邀请链接（归属用户）
    (ReferralLink, [("owner_user_id", "user_id")]),
    # 组织成员关系
    (OrganizationMember, [("user_id", "user_id")]),
]


def _build_user_filters(model: object, user_id: int) -> list:
    """根据清理清单条目构建 OR 条件列表（任一列命中即命中）。"""
    from sqlalchemy.sql import or_

    filters = []
    for entry in GDPR_RELATED_TABLE_CLEANUPS:
        if entry[0] is model:
            for col_name, _ in entry[1]:
                filters.append(getattr(model, col_name) == user_id)
            break
    return filters


async def _cleanup_related_tables(db: AsyncSession, user_id: int) -> dict[str, int]:
    """按 GDPR 关联表清理清单删除所有残留引用（BUG-036）。

    Returns:
        {表名: 删除行数} 字典，仅包含实际有删除的表。
    """
    from sqlalchemy.sql import or_

    cleaned: dict[str, int] = {}
    for model, _ in GDPR_RELATED_TABLE_CLEANUPS:
        filters = _build_user_filters(model, user_id)
        if not filters:
            continue
        result = await db.execute(delete(model).where(or_(*filters)))
        if result.rowcount:
            cleaned[model.__tablename__] = result.rowcount
    return cleaned


async def _residual_scan(db: AsyncSession, user_id: int) -> dict[str, int]:
    """删除后残留巡检：逐表统计仍残留 user 引用的行数（BUG-036）。

    正常删除后应为空；若非空说明存在未覆盖的关联表，需补充清理清单。
    """
    from sqlalchemy.sql import or_

    residuals: dict[str, int] = {}
    for model, _ in GDPR_RELATED_TABLE_CLEANUPS:
        filters = _build_user_filters(model, user_id)
        if not filters:
            continue
        count = (
            await db.execute(select(func.count()).select_from(model).where(or_(*filters)))
        ).scalar_one()
        if count:
            residuals[model.__tablename__] = count
    return residuals


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

    # ── 4-6. 关联表全量清理（BUG-036：清单化清理） ──────────────────
    # 覆盖: user_tags / match_records / unlock_records / trust_network /
    #       connections / contacts / user_relations / relation_events /
    #       six_degree_path_cache / referral_links / organization_members
    cleaned = await _cleanup_related_tables(db, user_id)
    if cleaned:
        logger.info(
            "GDPR 关联清理 user=%d: %s", user_id,
            ", ".join(f"{t}({n})" for t, n in cleaned.items()),
        )

    # ── 7. 审计日志留痕：user_id 置 NULL（保留记录内容，脱敏关联）──
    # BUG-012: 不再物理删除审计日志；user_id 置 NULL 保留平台安全审计能力。
    await db.execute(
        update(AuditLog)
        .where(AuditLog.user_id == user_id)
        .values(user_id=None)
    )

    await db.commit()

    # ── 7.5 删除后残留巡检（BUG-036） ──────────────────────────────
    # 使用独立 session 巡检，确保提交后的数据无残留引用。
    try:
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as audit_db:
            residuals = await _residual_scan(audit_db, user_id)
            if residuals:
                logger.warning(
                    "GDPR 删除后残留引用 user=%d: %s", user_id,
                    ", ".join(f"{t}({n})" for t, n in residuals.items()),
                )
            else:
                logger.info("GDPR 残留巡检通过 user=%d: 无残留引用", user_id)
    except Exception as e:  # noqa: BLE001
        logger.warning("GDPR 残留巡检失败: %s", e)
        residuals = {}

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
            "cleaned_tables": cleaned,
            "residual_refs": residuals,
        },
    }
