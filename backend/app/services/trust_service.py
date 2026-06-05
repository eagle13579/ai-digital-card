from typing import Optional

from sqlalchemy.orm import Session

from app.models.trust import TrustNetwork
from app.models.user import User


class TrustService:
    """信任网络服务层 - 用户之间的信任关系管理（A 独有的能力）"""

    @staticmethod
    def add_trust(
        db: Session,
        user_id: int,
        trusted_user_id: int,
    ) -> TrustNetwork:
        """添加信任关系

        Args:
            db: 数据库会话
            user_id: 当前用户ID（主动信任方）
            trusted_user_id: 被信任的用户ID

        Returns:
            创建的 TrustNetwork 实例
        """
        if user_id == trusted_user_id:
            raise ValueError("不能信任自己")

        # 验证被信任用户存在
        trusted_user = db.query(User).filter(User.id == trusted_user_id).first()
        if trusted_user is None:
            raise ValueError("被信任的用户不存在")

        # 检查是否已存在信任关系
        existing = db.query(TrustNetwork).filter(
            TrustNetwork.user_id == user_id,
            TrustNetwork.trusted_user_id == trusted_user_id,
        ).first()
        if existing:
            raise ValueError("已建立信任关系，请勿重复添加")

        trust = TrustNetwork(
            user_id=user_id,
            trusted_user_id=trusted_user_id,
        )
        db.add(trust)
        db.commit()
        db.refresh(trust)
        return trust

    @staticmethod
    def remove_trust(
        db: Session,
        user_id: int,
        trusted_user_id: int,
    ) -> dict:
        """移除信任关系

        Args:
            db: 数据库会话
            user_id: 当前用户ID
            trusted_user_id: 被信任的用户ID

        Returns:
            操作结果
        """
        trust = db.query(TrustNetwork).filter(
            TrustNetwork.user_id == user_id,
            TrustNetwork.trusted_user_id == trusted_user_id,
        ).first()
        if trust is None:
            raise ValueError("信任关系不存在")

        db.delete(trust)
        db.commit()
        return {"detail": "信任关系已移除"}

    @staticmethod
    def get_trust_network(
        db: Session,
        user_id: int,
    ) -> dict:
        """获取用户的完整信任网络（信任的人 + 信任我的人）

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            {
                "trusting": [...],   # 我信任的人
                "trusted_by": [...]  # 信任我的人
            }
        """
        # 我信任的人
        trusting = db.query(TrustNetwork).filter(TrustNetwork.user_id == user_id).all()
        trusting_ids = [t.trusted_user_id for t in trusting]

        # 信任我的人
        trusted_by = db.query(TrustNetwork).filter(TrustNetwork.trusted_user_id == user_id).all()
        trusted_by_ids = [t.user_id for t in trusted_by]

        def _user_to_dict(uid: int) -> Optional[dict]:
            u = db.query(User).filter(User.id == uid).first()
            if u is None:
                return None
            return {
                "id": u.id,
                "name": u.name,
                "company": u.company,
                "title": u.title,
                "avatar": u.avatar,
            }

        return {
            "trusting": [_user_to_dict(uid) for uid in trusting_ids if _user_to_dict(uid)],
            "trusted_by": [_user_to_dict(uid) for uid in trusted_by_ids if _user_to_dict(uid)],
        }

    @staticmethod
    def get_trust_degree(
        db: Session,
        user_id: int,
        target_user_id: int,
    ) -> int:
        """获取信任度数（1=直接信任, 2=间接信任, 0=无信任关系）

        Args:
            db: 数据库会话
            user_id: 用户ID
            target_user_id: 目标用户ID

        Returns:
            信任度数：0(无), 1(直接), 2(间接)
        """
        if user_id == target_user_id:
            return 0

        # 直接信任
        direct = db.query(TrustNetwork).filter(
            TrustNetwork.user_id == user_id,
            TrustNetwork.trusted_user_id == target_user_id,
        ).first()
        if direct:
            return 1

        # 间接信任（我信任的人信任目标）
        my_trusting = db.query(TrustNetwork).filter(
            TrustNetwork.user_id == user_id,
        ).all()
        my_trusting_ids = [t.trusted_user_id for t in my_trusting]

        if my_trusting_ids:
            indirect = db.query(TrustNetwork).filter(
                TrustNetwork.user_id.in_(my_trusting_ids),
                TrustNetwork.trusted_user_id == target_user_id,
            ).first()
            if indirect:
                return 2

        return 0
