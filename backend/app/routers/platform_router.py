"""
平台/组织管理路由 — 询赋吸收模块

API路径: /api/business-card/platforms/*
响应格式: {code: number, message: string, data: any}

功能清单:
  - GET    /api/business-card/platforms          — 平台推荐列表
  - POST   /api/business-card/platforms          — 创建平台（创建者自动成为秘书长）
  - GET    /api/business-card/platforms/{id}     — 平台详情
  - PUT    /api/business-card/platforms/{id}     — 更新平台信息
  - GET    /api/business-card/platforms/{id}/members  — 成员列表（按角色排序）
  - POST   /api/business-card/platforms/{id}/join     — 加入平台（角色=member）
  - GET    /api/business-card/platforms/{id}/report    — 商业报告
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.platform import Platform, PlatformMember
from app.models.user import User
from app.routers.auth import get_current_user
from app.api_standards import raise_http_error, ErrorCode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/business-card/platforms", tags=["询赋-平台管理"])


# ── Pydantic 模型 ──────────────────────────────────────────────────────────────


class PlatformCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="平台名称")
    platform_no: Optional[str] = Field(None, max_length=32, description="平台编号")
    annual_fee: float = Field(0.0, ge=0, description="年费")
    description: str = Field("", max_length=2048, description="平台描述")


class PlatformUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    platform_no: Optional[str] = Field(None, max_length=32)
    annual_fee: Optional[float] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=2048)


class PlatformResponse(BaseModel):
    id: int
    name: str
    platform_no: Optional[str] = None
    creator_id: int
    annual_fee: float
    description: str
    member_count: int = 0
    resource_count: int = 0
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    id: int
    user_id: int
    name: str = ""
    company: str = ""
    title: str = ""
    avatar: str = ""
    role: str
    joined_at: str

    model_config = {"from_attributes": True}


# ── 辅助函数 ──────────────────────────────────────────────────────────────────


def success(data: any = None, message: str = "操作成功") -> dict:
    """统一成功响应"""
    return {"code": 0, "message": message, "data": data}


def _role_sort(role: str) -> int:
    """角色排序权重：秘书长=1, 秘书处=2, 会员=3"""
    return {"secretary_general": 1, "secretariat": 2, "member": 3}.get(role, 99)


# ── API 端点 ────────────────────────────────────────────────────────────────────


@router.get("")
async def list_platforms(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """平台推荐列表（按成员数排序）"""
    query = (
        select(
            Platform,
            func.count(PlatformMember.id).over(partition_by=Platform.id).label("member_count"),
        )
        .outerjoin(PlatformMember, PlatformMember.platform_id == Platform.id)
        .distinct()
    )

    if keyword:
        query = query.where(Platform.name.like(f"%{keyword}%"))

    query = query.order_by(text("member_count DESC")).offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    platforms = []
    for row in rows:
        p = row[0]
        platforms.append({
            "id": p.id,
            "name": p.name,
            "platform_no": p.platform_no,
            "creator_id": p.creator_id,
            "annual_fee": p.annual_fee,
            "description": p.description,
            "member_count": row[1] or 0,
            "created_at": p.created_at.isoformat() if p.created_at else "",
            "updated_at": p.updated_at.isoformat() if p.updated_at else "",
        })

    return success(platforms)


@router.post("")
async def create_platform(
    data: PlatformCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建平台 — 创建者自动成为秘书长(secretary_general)"""
    platform = Platform(
        name=data.name,
        platform_no=data.platform_no,
        creator_id=current_user.id,
        annual_fee=data.annual_fee,
        description=data.description,
    )
    db.add(platform)
    await db.flush()

    # 创建者自动成为秘书长
    member = PlatformMember(
        platform_id=platform.id,
        user_id=current_user.id,
        role="secretary_general",
    )
    db.add(member)

    await db.commit()
    await db.refresh(platform)

    logger.info("平台创建: id=%d, name=%s, creator=%d", platform.id, platform.name, current_user.id)

    return success(
        {
            "id": platform.id,
            "name": platform.name,
            "platform_no": platform.platform_no,
            "creator_id": platform.creator_id,
            "annual_fee": platform.annual_fee,
            "description": platform.description,
            "member_count": 1,
            "created_at": platform.created_at.isoformat() if platform.created_at else "",
            "updated_at": platform.updated_at.isoformat() if platform.updated_at else "",
        },
        message="平台创建成功",
    )


@router.get("/{platform_id}")
async def get_platform(
    platform_id: int,
    db: AsyncSession = Depends(get_db),
):
    """平台详情（含成员/资源统计）"""
    result = await db.execute(select(Platform).where(Platform.id == platform_id))
    platform = result.scalar_one_or_none()
    if platform is None:
        raise_http_error(404, ErrorCode.NOT_FOUND, "平台不存在")

    # 成员数统计
    result = await db.execute(
        select(func.count()).select_from(PlatformMember).where(PlatformMember.platform_id == platform_id)
    )
    member_count = result.scalar() or 0

    return success({
        "id": platform.id,
        "name": platform.name,
        "platform_no": platform.platform_no,
        "creator_id": platform.creator_id,
        "annual_fee": platform.annual_fee,
        "description": platform.description,
        "member_count": member_count,
        "created_at": platform.created_at.isoformat() if platform.created_at else "",
        "updated_at": platform.updated_at.isoformat() if platform.updated_at else "",
    })


@router.put("/{platform_id}")
async def update_platform(
    platform_id: int,
    data: PlatformUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新平台信息（仅秘书长可操作）"""
    result = await db.execute(select(Platform).where(Platform.id == platform_id))
    platform = result.scalar_one_or_none()
    if platform is None:
        raise_http_error(404, ErrorCode.NOT_FOUND, "平台不存在")

    # 权限校验：只有秘书长可以更新
    result = await db.execute(
        select(PlatformMember).where(
            PlatformMember.platform_id == platform_id,
            PlatformMember.user_id == current_user.id,
            PlatformMember.role == "secretary_general",
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise_http_error(403, ErrorCode.FORBIDDEN, "仅秘书长可更新平台信息")

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        setattr(platform, field, value)

    await db.commit()
    await db.refresh(platform)

    return success(
        {
            "id": platform.id,
            "name": platform.name,
            "platform_no": platform.platform_no,
            "description": platform.description,
            "annual_fee": platform.annual_fee,
            "updated_at": platform.updated_at.isoformat() if platform.updated_at else "",
        },
        message="平台信息已更新",
    )


@router.get("/{platform_id}/members")
async def list_members(
    platform_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取平台成员列表（按角色排序: 秘书长 > 秘书处 > 会员 > 加入时间倒序）"""
    # 验证平台存在
    result = await db.execute(select(Platform).where(Platform.id == platform_id))
    if result.scalar_one_or_none() is None:
        raise_http_error(404, ErrorCode.NOT_FOUND, "平台不存在")

    # 查询成员 + 用户信息
    sql = text("""
        SELECT pm.id, pm.user_id, u.name, u.company, u.title, u.avatar, pm.role, pm.joined_at
        FROM platform_members pm
        JOIN users u ON u.id = pm.user_id
        WHERE pm.platform_id = :pid
        ORDER BY
          CASE pm.role
            WHEN 'secretary_general' THEN 1
            WHEN 'secretariat' THEN 2
            ELSE 3
          END,
          pm.joined_at DESC
    """)
    result = await db.execute(sql, {"pid": platform_id})
    rows = result.all()

    members = [
        {
            "id": row[0],
            "user_id": row[1],
            "name": row[2] or "",
            "company": row[3] or "",
            "title": row[4] or "",
            "avatar": row[5] or "",
            "role": row[6],
            "joined_at": row[7].isoformat() if row[7] else "",
        }
        for row in rows
    ]

    return success(members)


@router.post("/{platform_id}/join")
async def join_platform(
    platform_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """加入平台（角色=member）"""
    # 验证平台存在
    result = await db.execute(select(Platform).where(Platform.id == platform_id))
    if result.scalar_one_or_none() is None:
        raise_http_error(404, ErrorCode.NOT_FOUND, "平台不存在")

    # 检查是否已经是成员
    result = await db.execute(
        select(PlatformMember).where(
            PlatformMember.platform_id == platform_id,
            PlatformMember.user_id == current_user.id,
        )
    )
    if result.scalar_one_or_none() is not None:
        raise_http_error(400, ErrorCode.RESOURCE_CONFLICT, "已是平台成员")

    member = PlatformMember(
        platform_id=platform_id,
        user_id=current_user.id,
        role="member",
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    logger.info("加入平台: platform=%d, user=%d", platform_id, current_user.id)

    return success(
        {
            "id": member.id,
            "platform_id": member.platform_id,
            "user_id": member.user_id,
            "role": member.role,
            "joined_at": member.joined_at.isoformat() if member.joined_at else "",
        },
        message="加入平台成功",
    )


@router.get("/{platform_id}/report")
async def get_platform_report(
    platform_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """商业报告 — 角色分布、资源排名、城市/行业覆盖度（仅秘书长可见）"""
    # 验证平台存在
    result = await db.execute(select(Platform).where(Platform.id == platform_id))
    platform = result.scalar_one_or_none()
    if platform is None:
        raise_http_error(404, ErrorCode.NOT_FOUND, "平台不存在")

    # 权限校验：仅秘书长可查看报告
    result = await db.execute(
        select(PlatformMember).where(
            PlatformMember.platform_id == platform_id,
            PlatformMember.user_id == current_user.id,
            PlatformMember.role == "secretary_general",
        )
    )
    if result.scalar_one_or_none() is None:
        raise_http_error(403, ErrorCode.FORBIDDEN, "仅秘书长可查看商业报告")

    # 1. 角色分布统计
    result = await db.execute(
        select(PlatformMember.role, func.count().label("count"))
        .where(PlatformMember.platform_id == platform_id)
        .group_by(PlatformMember.role)
    )
    role_distribution = {row[0]: row[1] for row in result.all()}

    # 2. 成员总览
    result = await db.execute(
        select(func.count()).select_from(PlatformMember).where(PlatformMember.platform_id == platform_id)
    )
    total_members = result.scalar() or 0

    # 3. 城市覆盖度（基于用户的 company/用户信息中的城市维度）
    # 使用 users 表中的数据作为城市维度的近似
    # 注意：当前 User 模型没有 city 字段，先返回占位
    city_coverage = 0
    industry_coverage = 0

    # 尝试从用户的 company 和 title 字段统计
    sql = text("""
        SELECT COUNT(DISTINCT u.company) as company_count
        FROM platform_members pm
        JOIN users u ON u.id = pm.user_id
        WHERE pm.platform_id = :pid AND u.company != ''
    """)
    result = await db.execute(sql, {"pid": platform_id})
    row = result.one_or_none()
    if row:
        city_coverage = row[0] or 0

    return success({
        "platform_id": platform_id,
        "platform_name": platform.name,
        "total_members": total_members,
        "role_distribution": {
            "secretary_general": role_distribution.get("secretary_general", 0),
            "secretariat": role_distribution.get("secretariat", 0),
            "member": role_distribution.get("member", 0),
        },
        "coverage": {
            "company_count": city_coverage,
            "industry_count": industry_coverage,
        },
    })
