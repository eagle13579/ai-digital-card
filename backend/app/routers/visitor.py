import html
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.brochure import Brochure
from app.models.visitor import VisitorLog
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import VisitorLogCreate, VisitorLogResponse, InterestCreate

router = APIRouter(prefix="/api/v1/visitors", tags=["访客日志"])


@router.get("/{brochure_id}", response_model=list[VisitorLogResponse])
async def get_visitor_logs(
    brochure_id: int,
    limit: int = Query(30, description="返回条数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取画册的访客记录（需为画册主人）"""
    result = await db.execute(select(Brochure).where(Brochure.id == brochure_id))
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")
    if brochure.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此画册的访客记录")

    result = await db.execute(
        select(VisitorLog)
        .where(VisitorLog.brochure_id == brochure_id)
        .order_by(VisitorLog.visit_time.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [VisitorLogResponse.model_validate(log) for log in logs]


@router.post("/{brochure_id}/log")
async def log_visit(
    brochure_id: int,
    data: VisitorLogCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """记录访客访问（公开接口，无需登录）"""
    result = await db.execute(select(Brochure).where(Brochure.id == brochure_id))
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")

    log = VisitorLog(
        brochure_id=brochure_id,
        visitor_id=data.visitor_id,
        visitor_name=html.escape(data.visitor_name),
        visitor_ip=data.visitor_ip or request.client.host if request.client else "",
        source=data.source,
        page_viewed=html.escape(data.page_viewed),
        duration=data.duration,
    )
    db.add(log)
    await db.commit()
    return {"detail": "访问已记录"}


@router.post("/{brochure_id}/interest")
async def express_interest(
    brochure_id: int,
    data: InterestCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """访客表达兴趣/留言（公开接口，无需登录）"""
    result = await db.execute(select(Brochure).where(Brochure.id == brochure_id))
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")

    log = VisitorLog(
        brochure_id=brochure_id,
        visitor_name=html.escape(data.visitor_name),
        visitor_ip=request.client.host if request.client else "",
        source="interest",
        interested=True,
        contact_msg=html.escape(data.contact_msg),
    )
    db.add(log)
    await db.commit()
    return {"detail": "兴趣已表达"}


@router.get("/{brochure_id}/stats")
async def get_visitor_stats(
    brochure_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取画册访客统计（含趋势和来源分布）"""
    result = await db.execute(select(Brochure).where(Brochure.id == brochure_id))
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")
    if brochure.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此画册的统计")

    # 总访问次数
    result = await db.execute(
        select(func.count(VisitorLog.id)).where(VisitorLog.brochure_id == brochure_id)
    )
    total = result.scalar()

    # 感兴趣次数
    result = await db.execute(
        select(func.count(VisitorLog.id)).where(
            VisitorLog.brochure_id == brochure_id,
            VisitorLog.interested == True,
        )
    )
    interested = result.scalar()

    # ── 最近7天趋势 ──
    today = datetime.now(timezone.utc).date()
    seven_days_ago = today - timedelta(days=6)

    # 用 date(visit_time) 按天分组
    trend_rows = await db.execute(
        select(
            cast(VisitorLog.visit_time, Date).label("day"),
            func.count(VisitorLog.id).label("cnt"),
        )
        .where(
            VisitorLog.brochure_id == brochure_id,
            cast(VisitorLog.visit_time, Date) >= seven_days_ago,
        )
        .group_by(cast(VisitorLog.visit_time, Date))
        .order_by(cast(VisitorLog.visit_time, Date))
    )
    trend_map = {row.day: row.cnt for row in trend_rows}
    trend = []
    for i in range(7):
        d = seven_days_ago + timedelta(days=i)
        trend.append({"date": d.isoformat(), "count": trend_map.get(d, 0)})

    # ── 来源分布 ──
    source_rows = await db.execute(
        select(
            VisitorLog.source,
            func.count(VisitorLog.id).label("cnt"),
        )
        .where(VisitorLog.brochure_id == brochure_id)
        .group_by(VisitorLog.source)
        .order_by(func.count(VisitorLog.id).desc())
    )
    source_distribution = [
        {"source": row.source, "count": row.cnt} for row in source_rows
    ]

    # ── 最近访客（时间线） ──
    recent_rows = await db.execute(
        select(VisitorLog)
        .where(VisitorLog.brochure_id == brochure_id)
        .order_by(VisitorLog.visit_time.desc())
        .limit(10)
    )
    recent_visitors = [
        {
            "id": log.id,
            "visitor_name": log.visitor_name or "匿名访客",
            "visitor_ip": log.visitor_ip,
            "source": log.source,
            "page_viewed": log.page_viewed,
            "duration": log.duration,
            "interested": log.interested,
            "visit_time": log.visit_time.isoformat() if log.visit_time else None,
        }
        for log in recent_rows.scalars().all()
    ]

    return {
        "total_visits": total,
        "interested_count": interested,
        "view_count": brochure.view_count,
        "trend": trend,
        "source_distribution": source_distribution,
        "recent_visitors": recent_visitors,
    }
