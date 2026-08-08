"""邀请码 API — 生成/验证/使用"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.invitation_code import InvitationCode
from app.models.user import User
from app.middleware.rbac import require_permission
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/invite", tags=["内测邀请"])

@router.post("/generate")
async def generate_codes(
    count: int = Query(10, ge=1, le=100, description="生成数量"),
    batch_id: Optional[str] = Query(None),
    max_uses: int = Query(1, ge=1),
    expire_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """生成一批邀请码（管理员用）"""
    from app.routers.auth import get_current_user
    from app.models.user import User
    current_user = Depends(get_current_user)
    # 暂时允许所有登录用户生成（内测期间）
    
    codes = []
    for _ in range(count):
        while True:
            code_str = InvitationCode.generate_code()
            exists = await db.execute(
                select(InvitationCode).where(InvitationCode.code == code_str)
            )
            if not exists.scalars().first():
                break
        invite = InvitationCode(
            code=code_str,
            batch_id=batch_id or f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            max_uses=max_uses,
            expires_at=datetime.utcnow() + timedelta(days=expire_days),
        )
        db.add(invite)
        codes.append(code_str)
    
    await db.commit()
    return {"count": count, "batch_id": batch_id, "codes": codes, "expires_in_days": expire_days}

@router.post("/verify")
async def verify_code(code: str, db: AsyncSession = Depends(get_db)):
    """验证邀请码是否有效"""
    result = await db.execute(
        select(InvitationCode).where(InvitationCode.code == code.upper())
    )
    invite = result.scalars().first()
    if not invite:
        raise HTTPException(404, "邀请码不存在")
    if not invite.is_valid():
        raise HTTPException(400, "邀请码已过期或已用完")
    return {"valid": True, "code": code.upper()}

@router.post("/redeem")
async def redeem_code(
    code: str,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """消耗邀请码（注册时调用）"""
    # 修复 BUG-006：强制使用当前登录用户，禁止伪造他人 user_id 消耗邀请码
    user_id = current_user.id
    result = await db.execute(
        select(InvitationCode).where(InvitationCode.code == code.upper())
    )
    invite = result.scalars().first()
    if not invite:
        raise HTTPException(404, "邀请码不存在")
    if not invite.use():
        raise HTTPException(400, "邀请码无效")
    await db.commit()
    return {"success": True, "code": code.upper()}

@router.get("/stats")
async def invite_stats(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_permission("system:metrics")),
):
    """邀请码统计（BUG-030：仅 system:metrics 权限可读，禁止匿名访问）"""
    total = (await db.execute(select(func.count(InvitationCode.id)))).scalar()
    used = (await db.execute(
        select(func.count(InvitationCode.id)).where(InvitationCode.used_count > 0)
    )).scalar()
    active = (await db.execute(
        select(func.count(InvitationCode.id)).where(InvitationCode.is_active == True)
    )).scalar()
    return {"total": total, "used": used, "active": active, "remaining": total - used}
