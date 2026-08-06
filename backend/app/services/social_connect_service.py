"""A08 扫码建联服务 — 社交连接管理

基于询赋项目吸取的社交连接模式，提供建联发起、审核、查询和BFS人脉路径搜索。
"""
import logging
import uuid
from collections import deque
from typing import Optional

from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social_connection import SocialConnection
from app.models.tag import UserTag
from app.models.user import User

logger = logging.getLogger(__name__)


class SocialConnectService:
    """社交连接服务 - 扫码建联与关系管理"""

    @staticmethod
    async def request_connection(
        db: AsyncSession,
        user_id: int,
        target_user_id: int,
        message: str = "",
        source: str = "qrcode",
    ) -> dict:
        """发起建联请求 — 使用双向记录模式 (A03)

        1. 检查是否已存在关系
        2. 双向INSERT (user→target + target→user)
        3. 返回建联ID和状态

        Args:
            db: 异步数据库会话
            user_id: 发起方用户ID
            target_user_id: 目标方用户ID
            message: 附言消息
            source: 来源（qrcode/manual/share）

        Returns:
            dict: {id, user_id, contact_id, source, message, status, created_at}

        Raises:
            ValueError: 参数校验失败
        """
        if user_id == target_user_id:
            raise ValueError("不能与自己建联")

        # 验证目标用户存在
        result = await db.execute(select(User).where(User.id == target_user_id))
        target_user = result.scalars().first()
        if target_user is None:
            raise ValueError("目标用户不存在")

        # 检查是否已存在建联关系（双向任一方向）
        result = await db.execute(
            select(SocialConnection).where(
                or_(
                    and_(
                        SocialConnection.user_id == user_id,
                        SocialConnection.contact_id == target_user_id,
                    ),
                    and_(
                        SocialConnection.user_id == target_user_id,
                        SocialConnection.contact_id == user_id,
                    ),
                )
            )
        )
        existing = result.scalars().first()
        if existing:
            if existing.status == "approved":
                raise ValueError("你们已经是好友了")
            elif existing.status == "pending":
                raise ValueError("已发送建联请求，请等待对方审核")
            elif existing.status == "rejected":
                # 被拒绝后允许重新发起（创建新记录）
                pass

        # 生成UUID
        conn_id = str(uuid.uuid4())

        # 双向INSERT: user→target (发起方向)
        conn_out = SocialConnection(
            id=conn_id,
            user_id=user_id,
            contact_id=target_user_id,
            source=source,
            message=message,
            status="pending",
        )
        db.add(conn_out)

        # target→user (接收方向) - 使用相同ID保持关联
        conn_in = SocialConnection(
            id=conn_id + "_rev",
            user_id=target_user_id,
            contact_id=user_id,
            source=source,
            message=message,
            status="pending",
        )
        db.add(conn_in)

        await db.commit()
        await db.refresh(conn_out)

        return {
            "id": conn_out.id,
            "user_id": conn_out.user_id,
            "contact_id": conn_out.contact_id,
            "source": conn_out.source,
            "message": conn_out.message,
            "status": conn_out.status,
            "created_at": conn_out.created_at.isoformat() if conn_out.created_at else None,
        }

    @staticmethod
    async def review_connection(
        db: AsyncSession,
        connection_id: str,
        user_id: int,
        approved: bool,
    ) -> dict:
        """审核建联 — 同步更新双向记录

        Args:
            db: 异步数据库会话
            connection_id: 建联记录ID（发起方方向）
            user_id: 当前用户ID（审核方）
            approved: True=通过, False=拒绝

        Returns:
            dict: {id, status, message}

        Raises:
            ValueError: 记录不存在或无权操作
        """
        # 查找发起方向的记录（ID是发起方的UUID）
        result = await db.execute(
            select(SocialConnection).where(
                SocialConnection.id == connection_id,
                SocialConnection.status == "pending",
            )
        )
        conn_out = result.scalars().first()
        if conn_out is None:
            raise ValueError("建联记录不存在或已处理")

        # 检查当前用户是否是目标方（contact_id == 当前用户）
        if conn_out.contact_id != user_id:
            raise ValueError("无权审核此建联请求")

        new_status = "approved" if approved else "rejected"

        # 更新发起方向记录
        conn_out.status = new_status
        db.add(conn_out)

        # 同步更新接收方向记录（反向记录）
        rev_id = connection_id + "_rev"
        result = await db.execute(
            select(SocialConnection).where(SocialConnection.id == rev_id)
        )
        conn_in = result.scalars().first()
        if conn_in:
            conn_in.status = new_status
            db.add(conn_in)

        await db.commit()

        return {
            "id": connection_id,
            "status": new_status,
            "message": "建联已通过" if approved else "建联已拒绝",
        }

    @staticmethod
    async def get_my_connections(
        db: AsyncSession,
        user_id: int,
        status: str = "approved",
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取我的连接列表

        Args:
            db: 异步数据库会话
            user_id: 用户ID
            status: 筛选状态（approved/pending/rejected）
            page: 页码
            page_size: 每页条数

        Returns:
            dict: {items: [...], total, page, page_size}
        """
        # 查询当前用户发起的符合条件的连接
        query = select(SocialConnection).where(
            SocialConnection.user_id == user_id,
            SocialConnection.status == status,
        ).order_by(SocialConnection.created_at.desc())

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        paginated_query = query.offset(offset).limit(page_size)
        result = await db.execute(paginated_query)
        rows = result.scalars().all()

        # 获取联系人详细信息
        items = []
        for row in rows:
            contact_id = row.contact_id
            contact_result = await db.execute(
                select(User).where(User.id == contact_id)
            )
            contact = contact_result.scalars().first()
            contact_info = None
            if contact:
                contact_info = {
                    "id": contact.id,
                    "name": contact.name,
                    "company": contact.company,
                    "title": contact.title,
                    "avatar": contact.avatar,
                }

            items.append({
                "id": row.id,
                "user_id": row.user_id,
                "contact_id": row.contact_id,
                "contact": contact_info,
                "source": row.source,
                "message": row.message,
                "status": row.status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    async def get_pending_requests(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取待审核请求（别人发给我的）

        Args:
            db: 异步数据库会话
            user_id: 当前用户ID
            page: 页码
            page_size: 每页条数

        Returns:
            dict: {items: [...], total, page, page_size}
        """
        # 查找目标用户是当前用户的pending记录 = 别人发给我的建联请求
        query = select(SocialConnection).where(
            SocialConnection.contact_id == user_id,
            SocialConnection.status == "pending",
        ).order_by(SocialConnection.created_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        paginated_query = query.offset(offset).limit(page_size)
        result = await db.execute(paginated_query)
        rows = result.scalars().all()

        items = []
        for row in rows:
            # 发起方是 user_id，需要获取发起方信息
            requester_id = row.user_id
            requester_result = await db.execute(
                select(User).where(User.id == requester_id)
            )
            requester = requester_result.scalars().first()
            requester_info = None
            if requester:
                requester_info = {
                    "id": requester.id,
                    "name": requester.name,
                    "company": requester.company,
                    "title": requester.title,
                    "avatar": requester.avatar,
                }

            items.append({
                "id": row.id,
                "user_id": row.user_id,
                "contact_id": row.contact_id,
                "requester": requester_info,
                "source": row.source,
                "message": row.message,
                "status": row.status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    async def get_connection_recommendations(
        db: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> list:
        """
        推荐可能认识的人（二度人脉推荐）
        算法: 取当前用户好友的好友，排除已连接的和自己
        """
        # 语言级描述：
        # SELECT DISTINCT c2.contact_id
        # FROM social_connections c1
        # JOIN social_connections c2 ON c2.user_id = c1.contact_id
        # WHERE c1.user_id = :user_id
        #   AND c1.status = 'approved'
        #   AND c2.status = 'approved'
        #   AND c2.contact_id != :user_id
        #   AND c2.contact_id NOT IN (
        #       SELECT contact_id FROM social_connections WHERE user_id = :user_id
        #   )
        # LIMIT :limit
        subquery = (
            select(SocialConnection.contact_id)
            .where(SocialConnection.user_id == user_id)
        )
        query = (
            select(SocialConnection.contact_id)
            .select_from(
                SocialConnection.__table__.alias("c1")
            )
            .join(
                SocialConnection.__table__.alias("c2"),
                SocialConnection.__table__.alias("c2").c.user_id == SocialConnection.__table__.alias("c1").c.contact_id,
            )
            .where(
                SocialConnection.__table__.alias("c1").c.user_id == user_id,
                SocialConnection.__table__.alias("c1").c.status == "approved",
                SocialConnection.__table__.alias("c2").c.status == "approved",
                SocialConnection.__table__.alias("c2").c.contact_id != user_id,
                SocialConnection.__table__.alias("c2").c.contact_id.not_in(subquery),
            )
            .distinct()
            .limit(limit)
        )
        result = await db.execute(query)
        contact_ids = result.scalars().all()

        # 获取推荐用户的详细信息
        recommendations = []
        for cid in contact_ids:
            user_result = await db.execute(select(User).where(User.id == cid))
            user = user_result.scalars().first()
            if user:
                recommendations.append({
                    "id": user.id,
                    "name": user.name,
                    "company": user.company,
                    "title": user.title,
                    "avatar": user.avatar,
                })
        return recommendations

    @staticmethod
    async def get_social_graph_stats(
        db: AsyncSession,
        user_id: int,
    ) -> dict:
        """
        社交图谱统计
        返回: 直接好友数、二度人脉数、三度人脉数、覆盖城市、覆盖行业
        """
        # 1. 直接好友数
        result = await db.execute(
            select(func.count()).select_from(
                select(SocialConnection.id)
                .where(
                    SocialConnection.user_id == user_id,
                    SocialConnection.status == "approved",
                )
                .subquery()
            )
        )
        direct_count = result.scalar() or 0

        # 2. 二度人脉数（好友的好友，排除自己和已连接）
        # 先查所有直接好友
        result = await db.execute(
            select(SocialConnection.contact_id)
            .where(
                SocialConnection.user_id == user_id,
                SocialConnection.status == "approved",
            )
        )
        direct_friend_ids = set(result.scalars().all())

        # 查所有二度人脉
        second_degree_ids = set()
        for fid in direct_friend_ids:
            result = await db.execute(
                select(SocialConnection.contact_id)
                .where(
                    SocialConnection.user_id == fid,
                    SocialConnection.status == "approved",
                )
            )
            for cid in result.scalars().all():
                if cid != user_id and cid not in direct_friend_ids:
                    second_degree_ids.add(cid)
        second_count = len(second_degree_ids)

        # 3. 三度人脉数（好友的好友的好友，排除自己和已连接）
        third_degree_ids = set()
        for fid in second_degree_ids:
            result = await db.execute(
                select(SocialConnection.contact_id)
                .where(
                    SocialConnection.user_id == fid,
                    SocialConnection.status == "approved",
                )
            )
            for cid in result.scalars().all():
                if (
                    cid != user_id
                    and cid not in direct_friend_ids
                    and cid not in second_degree_ids
                ):
                    third_degree_ids.add(cid)
        third_count = len(third_degree_ids)

        # 4. 覆盖企业（基于直接好友的company字段去重）
        companies = set()
        for fid in direct_friend_ids:
            result = await db.execute(select(User.company).where(User.id == fid))
            company = result.scalar()
            if company:
                companies.add(company)
        company_count = len(companies)

        # 5. 覆盖行业 — 从 user_tags 表中取 tag_type='need' 或 'provide' 的不同 tag
        #    作为行业覆盖的近似统计
        industry_count = 0
        all_related_ids = direct_friend_ids | second_degree_ids | third_degree_ids
        if all_related_ids:
            result = await db.execute(
                select(func.count(func.distinct(UserTag.tag)))
                .where(
                    UserTag.user_id.in_(all_related_ids),
                )
            )
            industry_count = result.scalar() or 0

        return {
            "direct_count": direct_count,
            "second_degree_count": second_count,
            "third_degree_count": third_count,
            "company_count": company_count,
            "industry_tag_count": industry_count,
        }

    @staticmethod
    async def update_connection_strength(
        db: AsyncSession,
        connection_id: str,
        interaction_score: float = 1.0,
    ) -> dict:
        """
        更新关系强度（基于交互频率）
        strength = strength * 0.7 + interaction_score * 0.3
        """
        # 查找连接记录
        result = await db.execute(
            select(SocialConnection).where(SocialConnection.id == connection_id)
        )
        conn = result.scalars().first()
        if conn is None:
            raise ValueError("建联记录不存在")

        # 计算新强度，限制在 0.0 ~ 1.0 之间
        new_strength = conn.strength * 0.7 + interaction_score * 0.3
        new_strength = max(0.0, min(1.0, new_strength))

        conn.strength = new_strength
        db.add(conn)

        # 同步更新反向记录的关系强度
        rev_id = connection_id + "_rev"
        result = await db.execute(
            select(SocialConnection).where(SocialConnection.id == rev_id)
        )
        conn_rev = result.scalars().first()
        if conn_rev:
            conn_rev.strength = new_strength
            db.add(conn_rev)

        await db.commit()
        await db.refresh(conn)

        return {
            "id": conn.id,
            "strength": conn.strength,
        }

    @staticmethod
    async def find_path(
        db: AsyncSession,
        user_id: int,
        target_user_id: int,
    ) -> dict:
        """BFS最短路径查找（最多3度人脉）- 来自询赋A01

        使用广度优先搜索算法查找两个用户之间的最短路径，
        最多搜索到3度人脉（4层深度）。

        Args:
            db: 异步数据库会话
            user_id: 起始用户ID
            target_user_id: 目标用户ID

        Returns:
            dict: {distance: int, path: list[int], message: str}
        """
        if user_id == target_user_id:
            return {"distance": 0, "path": [user_id], "message": "自己"}

        visited = {user_id}
        queue = deque([{"id": user_id, "path": [user_id]}])

        while queue:
            current = queue.popleft()
            # 最多搜索3度人脉（path长度<=4）
            if len(current["path"]) > 4:
                continue

            # 获取当前用户的所有已建联联系人
            result = await db.execute(
                select(SocialConnection.contact_id).where(
                    SocialConnection.user_id == current["id"],
                    SocialConnection.status == "approved",
                )
            )
            conns = result.scalars().all()

            for contact_id in conns:
                if contact_id == target_user_id:
                    full_path = current["path"] + [target_user_id]
                    return {
                        "distance": len(current["path"]),
                        "path": full_path,
                        "message": f"找到可触达路径（{len(current['path'])}度人脉）",
                    }
                if contact_id not in visited:
                    visited.add(contact_id)
                    queue.append({"id": contact_id, "path": current["path"] + [contact_id]})

        return {
            "distance": -1,
            "path": [],
            "message": "未找到可触达路径（超过3度人脉或无连接）",
        }
