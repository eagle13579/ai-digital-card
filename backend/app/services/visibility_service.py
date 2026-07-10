"""
四级资源可见性权限服务 - 来自询赋A02原子吸收

可见性等级:
- public:   所有人可见
- platform: 同一平台/企业内成员可见（基于 tenant_id）
- network:  已建联的好友可见（基于 social_connections 表 approved 状态）
- private:  仅自己可见
"""

from typing import Optional

from sqlalchemy import or_, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social_connection import SocialConnection

VISIBILITY_LEVELS = ["public", "platform", "network", "private"]
"""可见性级别（按公开程度降序）"""


class VisibilityService:
    """四级资源可见性权限服务"""

    @staticmethod
    async def check_visibility_generic(
        model_name: str,
        owner_id: int,
        viewer_id: int,
        visibility_value: str,
        resource_tenant_id: Optional[int] = None,
        viewer_tenant_id: Optional[int] = None,
        db: Optional[AsyncSession] = None,
    ) -> bool:
        """
        泛化可见性检查 — 所有模型共用同一逻辑。

        与 check_visibility 不同的是，此方法接收 model_name 用于日志/审计，
        实际可见性判定逻辑与 check_visibility 完全一致。

        Args:
            model_name: 模型名称（'user', 'brochure', 'resource', 'team', 'crm_contact'），仅用于日志
            owner_id: 资源所有者用户ID
            viewer_id: 查看者用户ID
            visibility_value: 可见性级别值
            resource_tenant_id: 资源所属租户ID（platform级别需要）
            viewer_tenant_id: 查看者所属租户ID（platform级别需要）
            db: 异步数据库会话（network级别需要查询 social_connections）

        Returns:
            True 表示可见，False 表示不可见
        """
        return await VisibilityService.check_visibility(
            resource_owner_id=owner_id,
            viewer_id=viewer_id,
            resource_visibility=visibility_value,
            resource_tenant_id=resource_tenant_id,
            viewer_tenant_id=viewer_tenant_id,
            db=db,
        )

    @staticmethod
    async def check_visibility(
        resource_owner_id: int,
        viewer_id: int,
        resource_visibility: str,
        resource_tenant_id: Optional[int] = None,
        viewer_tenant_id: Optional[int] = None,
        db: Optional[AsyncSession] = None,
    ) -> bool:
        """
        检查 viewer 是否能看某个资源。

        逻辑:
        1. private       → 仅 owner 可看
        2. network       → owner 的已建联好友可看
        3. platform      → 同 platform (tenant) 成员可看
        4. public        → 所有人可看

        Args:
            resource_owner_id: 资源所有者用户ID
            viewer_id: 查看者用户ID
            resource_visibility: 资源可见性级别
            resource_tenant_id: 资源所属租户ID（platform级别需要）
            viewer_tenant_id: 查看者所属租户ID（platform级别需要）
            db: 异步数据库会话（network级别需要查询 social_connections）

        Returns:
            True 表示可见，False 表示不可见
        """
        # 资源所有者自己总是可见
        if viewer_id == resource_owner_id:
            return True

        if resource_visibility == "private":
            return False

        if resource_visibility == "public":
            return True

        if resource_visibility == "platform":
            # 同 tenant 即视为同平台成员
            if resource_tenant_id is not None and viewer_tenant_id is not None:
                return resource_tenant_id == viewer_tenant_id
            return False

        if resource_visibility == "network":
            # 需要检查 social_connections 表
            if db is None:
                return False
            return await VisibilityService._is_connected(db, resource_owner_id, viewer_id)

        # 未知级别，按最严格处理
        return False

    @staticmethod
    async def _is_connected(db: AsyncSession, user_a: int, user_b: int) -> bool:
        """检查两个用户之间是否有已批准的建联关系（双向任一方向）"""
        result = await db.execute(
            select(SocialConnection.id).where(
                or_(
                    and_(
                        SocialConnection.user_id == user_a,
                        SocialConnection.contact_id == user_b,
                        SocialConnection.status == "approved",
                    ),
                    and_(
                        SocialConnection.user_id == user_b,
                        SocialConnection.contact_id == user_a,
                        SocialConnection.status == "approved",
                    ),
                )
            )
        )
        return result.scalars().first() is not None

    @staticmethod
    def build_visibility_filter(
        viewer_id: int,
        table_alias: str = "r",
    ) -> tuple:
        """
        构建可见性过滤 SQLAlchemy WHERE 条件。

        返回: (where_clause, params_dict)
        用于查询时自动过滤不可见的资源。

        生成的 SQL 逻辑:
            (r.visibility = 'public')
            OR (r.owner_id = :viewer_id)
            OR (r.visibility = 'network' AND r.owner_id IN (
                SELECT contact_id FROM social_connections
                WHERE user_id = :viewer_id AND status = 'approved'
            ))
            OR (r.visibility = 'network' AND r.owner_id IN (
                SELECT user_id FROM social_connections
                WHERE contact_id = :viewer_id AND status = 'approved'
            ))
            OR (r.visibility = 'platform' AND r.tenant_id = :viewer_tenant_id)

        注意: viewer_tenant_id 需要在外部绑定。
        """
        # 构建子查询：查看者已建联的所有好友ID
        network_subq = (
            select(SocialConnection.contact_id)
            .where(
                SocialConnection.user_id == viewer_id,
                SocialConnection.status == "approved",
            )
        ).union(
            select(SocialConnection.user_id).where(
                SocialConnection.contact_id == viewer_id,
                SocialConnection.status == "approved",
            )
        )

        # 使用字符串来构建条件，因为 SQLAlchemy 的 Text 需要特殊处理
        # 这里我们返回纯 SQL 文本和参数
        table = table_alias

        where_clause = (
            f"({table}.visibility = 'public')"
            f" OR ({table}.user_id = :_viewer_id)"
            f" OR ({table}.visibility = 'network'"
            f"     AND {table}.user_id IN ("
            f"         SELECT contact_id FROM social_connections"
            f"         WHERE user_id = :_viewer_id2 AND status = 'approved'"
            f"     ))"
            f" OR ({table}.visibility = 'network'"
            f"     AND {table}.user_id IN ("
            f"         SELECT user_id FROM social_connections"
            f"         WHERE contact_id = :_viewer_id3 AND status = 'approved'"
            f"     ))"
            f" OR ({table}.visibility = 'platform')"
        )

        params = {
            "_viewer_id": viewer_id,
            "_viewer_id2": viewer_id,
            "_viewer_id3": viewer_id,
        }

        return where_clause, params

    @staticmethod
    async def get_visible_resources_for_user(
        viewer_id: int,
        model_class,
        db: AsyncSession,
        resource_type: Optional[str] = None,
        extra_filters: Optional[list] = None,
    ) -> list:
        """
        获取用户可见的所有资源。

        返回：
        - 自己的所有资源
        - 公开资源
        - 关系网内资源
        - 同平台资源

        Args:
            viewer_id: 查看者用户ID
            model_class: 资源模型类（如 Brochure）
            db: 异步数据库会话
            resource_type: 可选，资源类型筛选
            extra_filters: 可选，额外 SQLAlchemy filter 条件

        Returns:
            资源对象列表
        """
        from sqlalchemy import select

        visibility_clause, params = VisibilityService.build_visibility_filter(
            viewer_id=viewer_id, table_alias=model_class.__tablename__
        )

        query = select(model_class)

        # 应用可见性过滤（使用 text() 构建 raw SQL）
        from sqlalchemy import text

        query = query.where(text(visibility_clause).bindparams(**params))

        if extra_filters:
            for f in extra_filters:
                query = query.where(f)

        if resource_type and hasattr(model_class, "resource_type"):
            query = query.where(model_class.resource_type == resource_type)

        result = await db.execute(query)
        return list(result.scalars().all())
