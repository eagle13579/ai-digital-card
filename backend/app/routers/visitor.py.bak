from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.brochure import Brochure
from app.models.visitor import VisitorLog
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import VisitorLogCreate, VisitorLogResponse, InterestCreate

router = APIRouter(prefix="/api/visitors", tags=["访客日志"])


@router.get("/{brochure_id}", response_model=list[VisitorLogResponse])
def get_visitor_logs(
    brochure_id: int,
    limit: int = Query(30, description="返回条数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取画册的访客记录（需为画册主人）"""
    brochure = db.query(Brochure).filter(Brochure.id == brochure_id).first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")
    if brochure.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此画册的访客记录")

    logs = db.query(VisitorLog).filter(
        VisitorLog.brochure_id == brochure_id
    ).order_by(VisitorLog.visit_time.desc()).limit(limit).all()

    return [VisitorLogResponse.model_validate(log) for log in logs]


@router.post("/{brochure_id}/log")
def log_visit(
    brochure_id: int,
    data: VisitorLogCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """记录访客访问（公开接口，无需登录）"""
    brochure = db.query(Brochure).filter(Brochure.id == brochure_id).first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")

    log = VisitorLog(
        brochure_id=brochure_id,
        visitor_id=data.visitor_id,
        visitor_name=data.visitor_name,
        visitor_ip=data.visitor_ip or request.client.host if request.client else "",
        source=data.source,
        page_viewed=data.page_viewed,
        duration=data.duration,
    )
    db.add(log)
    db.commit()
    return {"detail": "访问已记录"}


@router.post("/{brochure_id}/interest")
def express_interest(
    brochure_id: int,
    data: InterestCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """访客表达兴趣/留言（公开接口，无需登录）"""
    brochure = db.query(Brochure).filter(Brochure.id == brochure_id).first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")

    log = VisitorLog(
        brochure_id=brochure_id,
        visitor_name=data.visitor_name,
        visitor_ip=request.client.host if request.client else "",
        source="interest",
        interested=True,
        contact_msg=data.contact_msg,
    )
    db.add(log)
    db.commit()
    return {"detail": "兴趣已表达"}


@router.get("/{brochure_id}/stats")
def get_visitor_stats(
    brochure_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取画册访客统计"""
    brochure = db.query(Brochure).filter(Brochure.id == brochure_id).first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")
    if brochure.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此画册的统计")

    total = db.query(VisitorLog).filter(VisitorLog.brochure_id == brochure_id).count()
    interested = db.query(VisitorLog).filter(
        VisitorLog.brochure_id == brochure_id,
        VisitorLog.interested == True,
    ).count()

    return {
        "total_visits": total,
        "interested_count": interested,
        "view_count": brochure.view_count,
    }
