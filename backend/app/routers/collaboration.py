"""Collaboration API routes — 实时协作：名片+CRM多人编辑/评论系统

所有端点均以 /api/collaboration/ 为前缀。
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.collaboration_service import get_collaboration_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/collaboration", tags=["collaboration"])


# ======================================================================
# 请求 / 响应模型
# ======================================================================


class CreateSessionRequest(BaseModel):
    """创建协作会话请求体。"""
    document_type: str = Field(..., description="文档类型: brochure / crm")
    document_id: str = Field(..., description="文档 ID")


class CreateSessionResponse(BaseModel):
    """创建协作会话响应体。"""
    session_id: str
    document_type: str
    document_id: str
    participants: list = []
    created_at: str


class JoinLeaveRequest(BaseModel):
    """加入/离开会话请求体。"""
    user_id: str = Field(..., description="用户 ID")
    user_name: str = Field("", description="用户显示名")


class AddCommentRequest(BaseModel):
    """添加评论请求体。"""
    user_id: str = Field(..., description="用户 ID")
    user_name: str = Field("", description="用户显示名")
    content: str = Field(..., description="评论内容")


class CommentResponse(BaseModel):
    """评论响应体。"""
    id: int
    session_id: str
    user_id: str
    user_name: str
    content: str
    created_at: str
    resolved: bool


# ======================================================================
# 会话管理路由
# ======================================================================


@router.post("/session", response_model=CreateSessionResponse)
async def create_session(body: CreateSessionRequest):
    """创建协作会话。自动生成 session_id (UUID v4)。"""
    svc = get_collaboration_service()
    session_id = str(uuid.uuid4())
    session = svc.create_session(session_id, body.document_type, body.document_id)
    return CreateSessionResponse(
        session_id=session.session_id,
        document_type=session.document_type,
        document_id=session.document_id,
        participants=session.participants,
        created_at=session.created_at,
    )


@router.post("/session/{session_id}/join")
async def join_session(session_id: str, body: JoinLeaveRequest):
    """加入协作会话。"""
    svc = get_collaboration_service()
    session = svc.join_session(session_id, body.user_id, body.user_name)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"status": "ok", "session_id": session.session_id, "participants": session.participants}


@router.post("/session/{session_id}/leave")
async def leave_session(session_id: str, body: JoinLeaveRequest):
    """离开协作会话。"""
    svc = get_collaboration_service()
    session = svc.leave_session(session_id, body.user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"status": "ok", "session_id": session.session_id, "participants": session.participants}


# ======================================================================
# 评论管理路由
# ======================================================================


@router.get("/session/{session_id}/comments", response_model=list[CommentResponse])
async def get_comments(session_id: str):
    """获取会话的所有评论（按时间升序）。"""
    svc = get_collaboration_service()
    comments = svc.get_comments(session_id)
    return [
        CommentResponse(
            id=c.id,
            session_id=c.session_id,
            user_id=c.user_id,
            user_name=c.user_name,
            content=c.content,
            created_at=c.created_at,
            resolved=c.resolved,
        )
        for c in comments
    ]


@router.post("/session/{session_id}/comments", response_model=CommentResponse)
async def add_comment(session_id: str, body: AddCommentRequest):
    """在会话中添加评论。"""
    svc = get_collaboration_service()
    comment = svc.add_comment(session_id, body.user_id, body.user_name, body.content)
    return CommentResponse(
        id=comment.id,
        session_id=comment.session_id,
        user_id=comment.user_id,
        user_name=comment.user_name,
        content=comment.content,
        created_at=comment.created_at,
        resolved=comment.resolved,
    )


@router.put("/comments/{comment_id}/resolve")
async def resolve_comment(comment_id: int):
    """将评论标记为已解决。"""
    svc = get_collaboration_service()
    comment = svc.resolve_comment(comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="评论不存在")
    return {"status": "ok", "comment_id": comment.id, "resolved": True}


# ======================================================================
# 全局查询路由
# ======================================================================


@router.get("/sessions/active")
async def get_active_sessions():
    """获取所有活跃协作会话。"""
    svc = get_collaboration_service()
    sessions = svc.get_active_sessions()
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "document_type": s.document_type,
                "document_id": s.document_id,
                "participants": s.participants,
                "created_at": s.created_at,
            }
            for s in sessions
        ]
    }
