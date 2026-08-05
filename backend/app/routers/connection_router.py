"""
社交关系管理路由 — 询赋吸收模块

API路径: /api/business-card/connections/*
响应格式: {code: number, message: string, data: any}

功能清单:
  - POST   /api/business-card/connections/request         — 发起建联请求
  - PUT    /api/business-card/connections/{id}/review     — 审核建联请求
  - GET    /api/business-card/connections                 — 我的好友列表
  - GET    /api/business-card/connections/pending         — 待审核请求列表
  - GET    /api/business-card/connections/path/{target_user_id}  — BFS触达路径

关系模式: 双向双行记录（A→B 和 B→A 各一行，详见 F05）
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.connection import Connection
from app.models.user import User
from app.routers.auth import get_current_user
from app.api_standards import raise_http_error, ErrorCode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/business-card/connections", tags=["询赋-社交关系"])


# ── Pydantic 模型 ──────────────────────────────────────────────────────────────


class ConnectionRequest(BaseModel):
    target_user_id: int = Field(..., description="目标用户ID")
    message: str = Field("", max_length=256, description="附言")
    source: str = Field("platform", description="关系来源: platform/scan/manual")


class ReviewRequest(BaseModel):
    approved: bool = Field(..., description="true=批准, false=拒绝")


class ConnectionResponse(BaseModel):
    id: int
    user_id: int
    contact_id: int
    source: str
    status: str
    strength: float
    label: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class UserBrief(BaseModel):
    """用户简要信息（用于好友列表）"""
    id: int
    name: str
    company: str = ""
    title: str = ""
    avatar: str = ""
    connection_id: int
    status: str
    strength: float = 0.0
    label: str = ""
    created_at: str


# ── 辅助函数 ──────────────────────────────────────────────────────────────────


def success(data: any = None, message: str = "操作成功") -> dict:
    return {"code": 0, "message": message, "data": data}


# ── API 端点 ────────────────────────────────────────────────────────────────────


@router.post("/request")
async def request_connection(
    data: ConnectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发起建联请求（自动创建双向双行记录）"""
    if data.target_user_id == current_user.id:
        raise_http_error(400, ErrorCode.VALIDATION_ERROR, "不能与自己建联")

    # 验证目标用户存在
    result = await db.execute(select(User).where(User.id == data.target_user_id))
    target_user = result.scalar_one_or_none()
    if target_user is None:
        raise_http_error(404, ErrorCode.NOT_FOUND, "目标用户不存在")

    # 检查是否已存在关系（双向）
    result = await db.execute(
        select(Connection).where(
            or_(
                (Connection.user_id == current_user.id) & (Connection.contact_id == data.target_user_id),
                (Connection.user_id == data.target_user_id) & (Connection.contact_id == current_user.id),
            )
        ).limit(1)
    )
    existing = result.scalar_one_or_none()
    if existing:
        if existing.status == "approved":
            raise_http_error(400, ErrorCode.RESOURCE_CONFLICT, "已建立好友关系")
        elif existing.status == "pending":
            raise_http_error(400, ErrorCode.RESOURCE_CONFLICT, "已发送建联请求，请等待对方审核")
        else:
            raise_http_error(400, ErrorCode.RESOURCE_CONFLICT, f"建联请求已被拒绝，状态: {existing.status}")

    # 正向记录: 当前用户 → 目标用户
    forward = Connection(
        user_id=current_user.id,
        contact_id=data.target_user_id,
        source=data.source,
        status="pending",
    )
    db.add(forward)

    # 反向记录: 目标用户 → 当前用户
    reverse = Connection(
        user_id=data.target_user_id,
        contact_id=current_user.id,
        source=data.source,
        status="pending",
    )
    db.add(reverse)

    await db.commit()
    await db.refresh(forward)

    logger.info(
        "建联请求: user=%d → target=%d, conn_id=%d",
        current_user.id, data.target_user_id, forward.id,
    )

    return success(
        {
            "id": forward.id,
            "user_id": forward.user_id,
            "contact_id": forward.contact_id,
            "status": forward.status,
        },
        message="建联请求已发送",
    )


@router.put("/{connection_id}/review")
async def review_connection(
    connection_id: int,
    data: ReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """审核建联请求（同步更新双向记录）"""
    # 查找正向记录: 对方→我（即 contact_id = 当前用户）
    result = await db.execute(
        select(Connection).where(
            Connection.id == connection_id,
            Connection.contact_id == current_user.id,
            Connection.status == "pending",
        )
    )
    conn = result.scalar_one_or_none()
    if conn is None:
        raise_http_error(404, ErrorCode.NOT_FOUND, "建联请求不存在或已处理")

    new_status = "approved" if data.approved else "rejected"

    # 更新正向记录
    conn.status = new_status
    db.add(conn)

    # 同步更新反向记录: 我→对方
    result = await db.execute(
        select(Connection).where(
            Connection.user_id == current_user.id,
            Connection.contact_id == conn.user_id,
        )
    )
    reverse_conn = result.scalar_one_or_none()
    if reverse_conn:
        reverse_conn.status = new_status
        db.add(reverse_conn)

    await db.commit()
    await db.refresh(conn)

    action = "已批准" if data.approved else "已拒绝"
    logger.info(
        "建联审核: connection=%d, %s (user=%d ↔ contact=%d)",
        connection_id, action, conn.user_id, conn.contact_id,
    )

    return success(
        {
            "id": conn.id,
            "status": conn.status,
            "contact_id": conn.contact_id,
            "user_id": conn.user_id,
        },
        message=f"建联请求{action}",
    )


@router.get("")
async def list_connections(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取我的好友/关系列表"""
    query = select(Connection).where(Connection.user_id == current_user.id)
    if status:
        query = query.where(Connection.status == status)
    else:
        query = query.where(Connection.status == "approved")

    query = query.order_by(Connection.updated_at.desc())
    result = await db.execute(query)
    connections = result.scalars().all()

    if not connections:
        return success([])

    contact_ids = [c.contact_id for c in connections]
    result = await db.execute(select(User).where(User.id.in_(contact_ids)))
    users_map = {u.id: u for u in result.scalars().all()}

    items = []
    for c in connections:
        u = users_map.get(c.contact_id)
        items.append({
            "id": u.id if u else c.contact_id,
            "name": u.name if u else "",
            "company": u.company if u else "",
            "title": u.title if u else "",
            "avatar": u.avatar if u else "",
            "connection_id": c.id,
            "status": c.status,
            "strength": c.strength,
            "label": c.label,
            "created_at": c.created_at.isoformat() if c.created_at else "",
        })

    return success(items)


@router.get("/pending")
async def list_pending_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取待审核的建联请求列表（别人向我发起的请求）"""
    result = await db.execute(
        select(Connection).where(
            Connection.contact_id == current_user.id,
            Connection.status == "pending",
        ).order_by(Connection.created_at.desc())
    )
    requests = result.scalars().all()

    if not requests:
        return success([])

    requester_ids = [r.user_id for r in requests]
    result = await db.execute(select(User).where(User.id.in_(requester_ids)))
    users_map = {u.id: u for u in result.scalars().all()}

    items = []
    for r in requests:
        u = users_map.get(r.user_id)
        items.append({
            "connection_id": r.id,
            "user_id": r.user_id,
            "name": u.name if u else "",
            "company": u.company if u else "",
            "title": u.title if u else "",
            "avatar": u.avatar if u else "",
            "source": r.source,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else "",
        })

    return success(items)


@router.get("/path/{target_user_id}")
async def find_path(
    target_user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """BFS社交图谱路径查找 — 在已批准的好友关系图中查找最短触达路径（最大3度人脉）

    使用广度优先搜索（BFS），每次从数据库中加载当前节点的已批准好友列表。
    最大搜索深度限制为 3 度人脉（path.length <= 4）。
    """
    if target_user_id == current_user.id:
        return success({
            "distance": 0,
            "path": [{"id": current_user.id, "name": current_user.name}],
        })

    # BFS 初始化
    visited = {current_user.id}
    queue: list[dict] = [{"id": current_user.id, "path_ids": [current_user.id]}]

    found_path_ids = None

    while queue:
        current = queue.pop(0)  # FIFO

        # 最大3度人脉：path.length > 4 时跳过（包括当前节点）
        if len(current["path_ids"]) > 4:
            continue

        # 查询当前节点的已批准好友
        result = await db.execute(
            text("SELECT contact_id FROM connections WHERE user_id = :uid AND status = 'approved'"),
            {"uid": current["id"]},
        )
        neighbors = [row[0] for row in result.all()]

        for neighbor_id in neighbors:
            if neighbor_id == target_user_id:
                # 找到目标！构建完整路径
                found_path_ids = current["path_ids"] + [target_user_id]
                break

            if neighbor_id not in visited:
                visited.add(neighbor_id)
                queue.append({
                    "id": neighbor_id,
                    "path_ids": current["path_ids"] + [neighbor_id],
                })

        if found_path_ids:
            break

    if not found_path_ids:
        return success({
            "distance": -1,
            "path": [],
            "message": "未找到可触达路径（超过3度人脉或无连接）",
        })

    # 获取路径上所有用户的信息
    result = await db.execute(select(User).where(User.id.in_(found_path_ids)))
    users_map = {u.id: u for u in result.scalars().all()}

    path = [
        {
            "id": uid,
            "name": users_map[uid].name if uid in users_map else f"用户{uid}",
            "company": users_map[uid].company if uid in users_map else "",
            "avatar": users_map[uid].avatar if uid in users_map else "",
        }
        for uid in found_path_ids
    ]

    distance = len(found_path_ids) - 1  # 边数 = 节点数 - 1

    logger.info(
        "BFS路径查找: user=%d → target=%d, distance=%d, path=%s",
        current_user.id, target_user_id, distance, found_path_ids,
    )

    return success({
        "distance": distance,
        "path": path,
        "message": f"{distance}度人脉",
    })
