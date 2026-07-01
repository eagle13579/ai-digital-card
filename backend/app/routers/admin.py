"""Admin Panel API — 用户管理/名片列表/系统统计/审计日志搜索 (RBAC保护)"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.audit import AuditLog
from app.models.brochure import Brochure
from app.models.user import User
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["Admin Panel"])

async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足：需要管理员角色")
    return True

AdminDep = Depends(require_admin)

def _user_to_dict(u: User) -> dict:
    return {"id": u.id, "phone": u.phone, "name": u.name, "avatar": u.avatar,
            "company": u.company, "title": u.title, "role": u.role,
            "membership_tier": u.membership_tier,
            "created_at": u.created_at.isoformat(), "updated_at": u.updated_at.isoformat()}

@router.get("/users")
async def admin_list_users(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
                           q: Optional[str] = Query(None), db: AsyncSession = Depends(get_db),
                           _: bool = AdminDep):
    query = select(User).order_by(User.created_at.desc())
    count_query = select(func.count(User.id))
    if q:
        like = f"%{q}%"
        query = query.where(or_(User.name.like(like), User.phone.like(like)))
        count_query = count_query.where(or_(User.name.like(like), User.phone.like(like)))
    total = (await db.execute(count_query)).scalar() or 0
    users = (await db.execute(query.offset((page - 1) * per_page).limit(per_page))).scalars().all()
    return {"total": total, "page": page, "per_page": per_page, "items": [_user_to_dict(u) for u in users]}

@router.get("/users/{user_id}")
async def admin_get_user(user_id: int, db: AsyncSession = Depends(get_db), _: bool = AdminDep):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"id": user.id, "phone": user.phone, "username": user.username, "name": user.name,
            "avatar": user.avatar, "company": user.company, "title": user.title, "intro": user.intro,
            "role": user.role, "wechat_openid": user.wechat_openid,
            "membership_tier": user.membership_tier,
            "membership_expires_at": user.membership_expires_at.isoformat() if user.membership_expires_at else None,
            "unlock_quota": user.unlock_quota,
            "created_at": user.created_at.isoformat(), "updated_at": user.updated_at.isoformat()}

@router.patch("/users/{user_id}")
async def admin_update_user_status(user_id: int, status: str = Query(..., pattern=r"^(active|disabled)$"),
                                   db: AsyncSession = Depends(get_db), _: bool = AdminDep):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.role = "user" if status == "active" else "disabled"
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "role": user.role, "status": status}

@router.get("/brochures")
async def admin_list_brochures(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
                               db: AsyncSession = Depends(get_db), _: bool = AdminDep):
    query = select(Brochure).order_by(Brochure.created_at.desc())
    total = (await db.execute(select(func.count(Brochure.id)))).scalar() or 0
    items = (await db.execute(query.offset((page - 1) * per_page).limit(per_page))).scalars().all()
    return {"total": total, "page": page, "per_page": per_page,
            "items": [{"id": b.id, "user_id": b.user_id, "title": b.title, "cover": b.cover,
                       "purpose": b.purpose, "status": b.status, "share_token": b.share_token,
                       "view_count": b.view_count, "pages_count": b.pages_count,
                       "created_at": b.created_at.isoformat(), "updated_at": b.updated_at.isoformat()}
                      for b in items]}

@router.get("/stats")
async def admin_stats(db: AsyncSession = Depends(get_db), _: bool = AdminDep):
    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    brochure_count = (await db.execute(select(func.count(Brochure.id)))).scalar() or 0
    since = datetime.utcnow() - timedelta(hours=24)
    dau = (await db.execute(select(func.count(func.distinct(AuditLog.user_id)))
                            .where(AuditLog.timestamp >= since, AuditLog.user_id.isnot(None)))).scalar() or 0
    admin_count = (await db.execute(select(func.count(User.id)).where(User.role == "admin"))).scalar() or 0
    new_users_7d = (await db.execute(select(func.count(User.id))
                                     .where(User.created_at >= datetime.utcnow() - timedelta(days=7)))).scalar() or 0
    return {"user_count": user_count, "brochure_count": brochure_count, "dau": dau,
            "admin_count": admin_count, "new_users_7d": new_users_7d,
            "timestamp": datetime.utcnow().isoformat()}

@router.get("/audit-log")
async def admin_audit_log(user_id: Optional[int] = Query(None), action: Optional[str] = Query(None),
                          start_time: Optional[str] = Query(None), end_time: Optional[str] = Query(None),
                          page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
                          db: AsyncSession = Depends(get_db), _: bool = AdminDep):
    query = select(AuditLog).order_by(AuditLog.timestamp.desc())
    count_query = select(func.count(AuditLog.id))
    if user_id is not None:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action.upper())
        count_query = count_query.where(AuditLog.action == action.upper())
    if start_time:
        try: dt_start = datetime.fromisoformat(start_time)
        except ValueError: raise HTTPException(400, "start_time 格式无效")
        query = query.where(AuditLog.timestamp >= dt_start)
        count_query = count_query.where(AuditLog.timestamp >= dt_start)
    if end_time:
        try: dt_end = datetime.fromisoformat(end_time)
        except ValueError: raise HTTPException(400, "end_time 格式无效")
        query = query.where(AuditLog.timestamp <= dt_end)
        count_query = count_query.where(AuditLog.timestamp <= dt_end)
    total = (await db.execute(count_query)).scalar() or 0
    items = (await db.execute(query.offset((page - 1) * per_page).limit(per_page))).scalars().all()
    return {"total": total, "page": page, "per_page": per_page,
            "items": [{"id": log.id, "user_id": log.user_id, "action": log.action,
                       "resource": log.resource, "detail": log.detail, "ip": log.ip,
                       "user_agent": log.user_agent, "timestamp": log.timestamp.isoformat()}
                      for log in items]}
