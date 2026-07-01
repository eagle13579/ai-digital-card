import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, or_, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


class MessageService:
    """消息服务层 - 封装消息的发送、查询、标记已读等业务逻辑"""

    @staticmethod
    async def send_message(
        db: AsyncSession,
        sender_id: int,
        receiver_id: int,
        content: str,
    ) -> Message:
        """发送消息（自动生成或沿用已有会话 ID）"""
        conversation_id = await MessageService._get_or_create_conversation(
            db, sender_id, receiver_id
        )
        msg = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            conversation_id=conversation_id,
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def get_conversations(
        db: AsyncSession,
        user_id: int,
    ) -> list[dict]:
        """获取当前用户的会话列表（按 conversation_id 分组，取最新一条消息 + 未读数）"""
        # 子查询：每个会话的最新消息时间
        subq = (
            select(
                Message.conversation_id,
                func.max(Message.created_at).label("max_created_at"),
            )
            .where(
                or_(Message.sender_id == user_id, Message.receiver_id == user_id)
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

        # 关联取最新消息全文
        stmt = (
            select(Message)
            .join(
                subq,
                and_(
                    Message.conversation_id == subq.c.conversation_id,
                    Message.created_at == subq.c.max_created_at,
                ),
            )
            .order_by(Message.created_at.desc())
        )
        result = await db.execute(stmt)
        latest_msgs: list[Message] = list(result.scalars().all())

        conversations = []
        for msg in latest_msgs:
            # 该会话中当前用户未读消息数
            unread_count = await MessageService._count_unread_in_conversation(
                db, msg.conversation_id, user_id
            )
            other_user_id = (
                msg.receiver_id if msg.sender_id == user_id else msg.sender_id
            )
            conversations.append(
                {
                    "conversation_id": msg.conversation_id,
                    "other_user_id": other_user_id,
                    "last_message": msg.content,
                    "last_message_at": msg.created_at.isoformat()
                    if msg.created_at
                    else "",
                    "last_sender_id": msg.sender_id,
                    "unread_count": unread_count,
                }
            )
        return conversations

    @staticmethod
    async def get_conversation_messages(
        db: AsyncSession,
        conversation_id: str,
        user_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """获取某个会话的详细消息（分页，按时间正序）"""
        # 验证当前用户是否参与此会话
        check = await db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                or_(Message.sender_id == user_id, Message.receiver_id == user_id),
            )
            .limit(1)
        )
        if not check.scalars().first():
            raise PermissionError("无权访问此会话")

        # 总数
        count_stmt = select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 分页数据
        offset = (page - 1) * page_size
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        messages = result.scalars().all()

        return {
            "messages": [
                {
                    "id": m.id,
                    "sender_id": m.sender_id,
                    "receiver_id": m.receiver_id,
                    "content": m.content,
                    "is_read": m.is_read,
                    "created_at": m.created_at.isoformat() if m.created_at else "",
                }
                for m in messages
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    async def mark_as_read(
        db: AsyncSession,
        conversation_id: str,
        user_id: int,
    ) -> int:
        """标记会话中所有发给当前用户的未读消息为已读，返回影响行数"""
        stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.receiver_id == user_id,
                Message.is_read == False,
            )
        )
        result = await db.execute(stmt)
        unread_msgs = result.scalars().all()
        for msg in unread_msgs:
            msg.is_read = True
        await db.commit()
        return len(unread_msgs)

    @staticmethod
    async def count_unread(
        db: AsyncSession,
        user_id: int,
    ) -> dict:
        """统计当前用户的未读消息总数和按会话分组的未读数"""
        # 总未读数
        total_stmt = select(func.count(Message.id)).where(
            Message.receiver_id == user_id,
            Message.is_read == False,
        )
        total_result = await db.execute(total_stmt)
        total_unread = total_result.scalar() or 0

        # 按会话分组未读数
        group_stmt = (
            select(
                Message.conversation_id,
                func.count(Message.id).label("unread_count"),
            )
            .where(
                Message.receiver_id == user_id,
                Message.is_read == False,
            )
            .group_by(Message.conversation_id)
        )
        group_result = await db.execute(group_stmt)
        by_conversation = {
            row.conversation_id: row.unread_count for row in group_result
        }

        return {
            "total_unread": total_unread,
            "by_conversation": by_conversation,
        }

    # ── 内部辅助方法 ──────────────────────────────────────────

    @staticmethod
    async def _get_or_create_conversation(
        db: AsyncSession,
        user_a: int,
        user_b: int,
    ) -> str:
        """查找两个用户之间现有的会话 ID，若不存在则创建新的"""
        stmt = (
            select(Message.conversation_id)
            .where(
                or_(
                    and_(Message.sender_id == user_a, Message.receiver_id == user_b),
                    and_(Message.sender_id == user_b, Message.receiver_id == user_a),
                )
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        existing = result.scalar()
        if existing:
            return existing
        return uuid.uuid4().hex

    @staticmethod
    async def _count_unread_in_conversation(
        db: AsyncSession,
        conversation_id: str,
        user_id: int,
    ) -> int:
        stmt = select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id,
            Message.receiver_id == user_id,
            Message.is_read == False,
        )
        result = await db.execute(stmt)
        return result.scalar() or 0
