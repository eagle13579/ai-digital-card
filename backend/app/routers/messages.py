from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.message_service import MessageService

router = APIRouter(prefix="/api/v1/messages", tags=["消息"])


# ── Pydantic 请求/响应模型 ──────────────────────────────────────


class SendMessageRequest(BaseModel):
    receiver_id: int = Field(..., description="接收方用户ID")
    content: str = Field(..., min_length=1, max_length=5000, description="消息内容")


class SendMessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    conversation_id: str
    created_at: str

    model_config = {"from_attributes": True}


class ConversationItem(BaseModel):
    conversation_id: str
    other_user_id: int
    last_message: str
    last_message_at: str
    last_sender_id: int
    unread_count: int


class MessageItem(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool
    created_at: str


class ConversationMessagesResponse(BaseModel):
    messages: list[MessageItem]
    total: int
    page: int
    page_size: int


class UnreadCountResponse(BaseModel):
    total_unread: int
    by_conversation: dict[str, int]


# ── 统一响应包装 ──────────────────────────────────────────────


def ok(data=None):
    return {"code": 0, "message": "ok", "data": data}


# ── 路由 ─────────────────────────────────────────────────────


@router.get("")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """当前用户的消息列表（按 conversation_id 分组，取最新一条）"""
    conversations = await MessageService.get_conversations(db, current_user.id)
    return ok(conversations)


@router.get("/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """会话列表（同上，按 conversation 分组）"""
    conversations = await MessageService.get_conversations(db, current_user.id)
    return ok(conversations)


@router.get("/{conversation_id}")
async def get_conversation_messages(
    conversation_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """某个会话的详细消息"""
    try:
        result = await MessageService.get_conversation_messages(
            db, conversation_id, current_user.id, page=page, page_size=page_size
        )
        return ok(result)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("")
async def send_message(
    data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发送消息"""
    if data.receiver_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能给自己发送消息")

    msg = await MessageService.send_message(
        db, current_user.id, data.receiver_id, data.content
    )
    return ok(
        {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "content": msg.content,
            "conversation_id": msg.conversation_id,
            "created_at": msg.created_at.isoformat() if msg.created_at else "",
        }
    )


@router.post("/{conversation_id}/read")
async def mark_as_read(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记会话中所有未读消息为已读"""
    count = await MessageService.mark_as_read(db, conversation_id, current_user.id)
    return ok({"marked_count": count})


@router.get("/unread/count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """当前用户的未读消息数"""
    result = await MessageService.count_unread(db, current_user.id)
    return ok(result)
