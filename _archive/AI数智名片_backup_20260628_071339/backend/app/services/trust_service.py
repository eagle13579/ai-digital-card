from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trust import TrustNetwork
from app.models.user import User


class TrustService:
    """信任网络服务层 - 用户之间的信任关系管理（A 独有的能力）"""

    @staticmethod
    async def add_trust(
        db: AsyncSession,
        user_id: int,
        trusted_user_id: int,
    ) -> TrustNetwork:
        """添加信任关系"""
        if user_id == trusted_user_id:
            raise ValueError("不能信任自己")

        result = await db.execute(select(User).where(User.id == trusted_user_id))
        trusted_user = result.scalars().first()
        if trusted_user is None:
            raise ValueError("被信任的用户不存在")

        result = await db.execute(
            select(TrustNetwork).where(
                TrustNetwork.user_id == user_id,
                TrustNetwork.trusted_user_id == trusted_user_id,
            )
        )
        existing = result.scalars().first()
        if existing:
            raise ValueError("已建立信任关系，请勿重复添加")

        trust = TrustNetwork(
            user_id=user_id,
            trusted_user_id=trusted_user_id,
        )
        db.add(trust)
        await db.commit()
        await db.refresh(trust)
        return trust

    @staticmethod
    async def remove_trust(
        db: AsyncSession,
        user_id: int,
        trusted_user_id: int,
    ) -> dict:
        """移除信任关系"""
        result = await db.execute(
            select(TrustNetwork).where(
                TrustNetwork.user_id == user_id,
                TrustNetwork.trusted_user_id == trusted_user_id,
            )
        )
        trust = result.scalars().first()
        if trust is None:
            raise ValueError("信任关系不存在")

        await db.delete(trust)
        await db.commit()
        return {"detail": "信任关系已移除"}

    @staticmethod
    async def get_trust_network(
        db: AsyncSession,
        user_id: int,
    ) -> dict:
        """获取用户的完整信任网络（信任的人 + 信任我的人）"""
        result = await db.execute(
            select(TrustNetwork).where(TrustNetwork.user_id == user_id)
        )
        trusting = result.scalars().all()
        trusting_ids = [t.trusted_user_id for t in trusting]

        result = await db.execute(
            select(TrustNetwork).where(TrustNetwork.trusted_user_id == user_id)
        )
        trusted_by = result.scalars().all()
        trusted_by_ids = [t.user_id for t in trusted_by]

        async def _user_to_dict(uid: int) -> Optional[dict]:
            result = await db.execute(select(User).where(User.id == uid))
            u = result.scalars().first()
            if u is None:
                return None
            return {
                "id": u.id,
                "name": u.name,
                "company": u.company,
                "title": u.title,
                "avatar": u.avatar,
            }

        trusting_list = []
        for uid in trusting_ids:
            u = await _user_to_dict(uid)
            if u:
                trusting_list.append(u)

        trusted_by_list = []
        for uid in trusted_by_ids:
            u = await _user_to_dict(uid)
            if u:
                trusted_by_list.append(u)

        return {
            "trusting": trusting_list,
            "trusted_by": trusted_by_list,
        }

    @staticmethod
    async def get_trust_degree(
        db: AsyncSession,
        user_id: int,
        target_user_id: int,
    ) -> int:
        """获取信任度数（1=直接信任, 2=间接信任, 0=无信任关系）"""
        if user_id == target_user_id:
            return 0

        result = await db.execute(
            select(TrustNetwork).where(
                TrustNetwork.user_id == user_id,
                TrustNetwork.trusted_user_id == target_user_id,
            )
        )
        direct = result.scalars().first()
        if direct:
            return 1

        result = await db.execute(
            select(TrustNetwork).where(TrustNetwork.user_id == user_id)
        )
        my_trusting = result.scalars().all()
        my_trusting_ids = [t.trusted_user_id for t in my_trusting]

        if my_trusting_ids:
            result = await db.execute(
                select(TrustNetwork).where(
                    TrustNetwork.user_id.in_(my_trusting_ids),
                    TrustNetwork.trusted_user_id == target_user_id,
                )
            )
            indirect = result.scalars().first()
            if indirect:
                return 2

        return 0
