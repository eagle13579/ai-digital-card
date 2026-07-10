"""资源平台商业化服务 — 平台创建/加入/商机/商业报告"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, case, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.resource_platform import (
    PlatformMember,
    PlatformOpportunity,
    ResourcePlatform,
)
from app.models.payment import PaymentOrder, EnterpriseSubscription
from app.models.user import User

logger = logging.getLogger(__name__)


class ResourcePlatformService:
    """资源平台核心服务"""

    # ── 平台 CRUD ──────────────────────────────────────────────────────

    @staticmethod
    async def create_platform(
        db: AsyncSession,
        name: str,
        annual_fee: int,
        creator_id: int,
        description: str = "",
        member_limit: int = 1000,
    ) -> dict:
        """创建平台 + 自动成为秘书长

        Args:
            db: 数据库会话
            name: 平台名称
            annual_fee: 年费(分)
            creator_id: 创建者用户ID
            description: 平台描述
            member_limit: 成员上限

        Returns:
            dict: 平台信息 {id, name, platform_no, ...}

        Raises:
            ValueError: 参数校验失败
        """
        if not name or not name.strip():
            raise ValueError("平台名称不能为空")

        # 生成平台编号: RP + 时间戳后8位
        import time
        platform_no = f"RP{int(time.time()) % 100000000:08d}"

        platform = ResourcePlatform(
            name=name.strip(),
            platform_no=platform_no,
            annual_fee=annual_fee,
            creator_id=creator_id,
            description=description.strip(),
            member_limit=member_limit,
        )
        db.add(platform)
        await db.flush()  # 获取 platform.id

        # 创建者自动成为秘书长
        member = PlatformMember(
            platform_id=platform.id,
            user_id=creator_id,
            role="secretary_general",
        )
        db.add(member)
        await db.commit()
        await db.refresh(platform)

        return {
            "id": platform.id,
            "name": platform.name,
            "platform_no": platform.platform_no,
            "annual_fee": platform.annual_fee,
            "description": platform.description,
            "member_limit": platform.member_limit,
            "creator_id": platform.creator_id,
            "created_at": platform.created_at,
        }

    @staticmethod
    async def get_platforms(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """平台推荐列表（按资源数/成员数排序）

        Returns:
            dict: {items: [...], total: int, page: int, page_size: int}
        """
        # 子查询: 各平台成员数
        member_count_subq = (
            select(
                PlatformMember.platform_id,
                func.count(PlatformMember.id).label("member_count"),
            )
            .group_by(PlatformMember.platform_id)
            .subquery()
        )

        # 子查询: 各平台商机数
        opp_count_subq = (
            select(
                PlatformOpportunity.platform_id,
                func.count(PlatformOpportunity.id).label("opportunity_count"),
            )
            .group_by(PlatformOpportunity.platform_id)
            .subquery()
        )

        # 查询总量
        total_q = select(func.count(ResourcePlatform.id))
        total_result = await db.execute(total_q)
        total = total_result.scalar() or 0

        # 分页查询，按成员数降序
        query = (
            select(
                ResourcePlatform,
                func.coalesce(member_count_subq.c.member_count, 0).label("member_count"),
                func.coalesce(opp_count_subq.c.opportunity_count, 0).label("opportunity_count"),
            )
            .outerjoin(member_count_subq, ResourcePlatform.id == member_count_subq.c.platform_id)
            .outerjoin(opp_count_subq, ResourcePlatform.id == opp_count_subq.c.platform_id)
            .order_by(func.coalesce(member_count_subq.c.member_count, 0).desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(query)
        rows = result.all()

        items = []
        for row in rows:
            platform = row[0]
            items.append({
                "id": platform.id,
                "name": platform.name,
                "platform_no": platform.platform_no,
                "description": platform.description,
                "annual_fee": platform.annual_fee,
                "member_limit": platform.member_limit,
                "member_count": row.member_count,
                "opportunity_count": row.opportunity_count,
                "creator_id": platform.creator_id,
                "created_at": platform.created_at,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    async def get_platform(
        db: AsyncSession,
        platform_id: int,
    ) -> Optional[dict]:
        """平台详情 + 统计数据（成员数/资源数/商机数）

        Args:
            db: 数据库会话
            platform_id: 平台ID

        Returns:
            dict or None: 平台详情（含统计）
        """
        result = await db.execute(
            select(ResourcePlatform).where(ResourcePlatform.id == platform_id)
        )
        platform = result.scalars().first()
        if platform is None:
            return None

        # 成员数
        result = await db.execute(
            select(func.count(PlatformMember.id)).where(
                PlatformMember.platform_id == platform_id
            )
        )
        member_count = result.scalar() or 0

        # 商机数
        result = await db.execute(
            select(func.count(PlatformOpportunity.id)).where(
                PlatformOpportunity.platform_id == platform_id
            )
        )
        opportunity_count = result.scalar() or 0

        return {
            "id": platform.id,
            "name": platform.name,
            "platform_no": platform.platform_no,
            "description": platform.description,
            "annual_fee": platform.annual_fee,
            "member_limit": platform.member_limit,
            "creator_id": platform.creator_id,
            "member_count": member_count,
            "opportunity_count": opportunity_count,
            "created_at": platform.created_at,
            "updated_at": platform.updated_at,
        }

    @staticmethod
    async def update_platform(
        db: AsyncSession,
        platform_id: int,
        user_id: int,
        **kwargs,
    ) -> Optional[dict]:
        """更新平台信息（仅秘书长可操作）

        Args:
            db: 数据库会话
            platform_id: 平台ID
            user_id: 操作用户ID
            **kwargs: 可更新字段 (name, description, annual_fee, member_limit)

        Returns:
            dict or None: 更新后的平台信息

        Raises:
            PermissionError: 非秘书长操作
            ValueError: 参数错误
        """
        # 验证权限
        result = await db.execute(
            select(PlatformMember).where(
                PlatformMember.platform_id == platform_id,
                PlatformMember.user_id == user_id,
                PlatformMember.role == "secretary_general",
            )
        )
        if result.scalars().first() is None:
            raise PermissionError("仅秘书长可更新平台信息")

        result = await db.execute(
            select(ResourcePlatform).where(ResourcePlatform.id == platform_id)
        )
        platform = result.scalars().first()
        if platform is None:
            return None

        allowed_fields = {"name", "description", "annual_fee", "member_limit"}
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(platform, key, value)

        # 更新 updated_at
        import time
        platform.updated_at = int(time.time())

        await db.commit()
        await db.refresh(platform)

        return {
            "id": platform.id,
            "name": platform.name,
            "platform_no": platform.platform_no,
            "description": platform.description,
            "annual_fee": platform.annual_fee,
            "member_limit": platform.member_limit,
            "updated_at": platform.updated_at,
        }

    # ── 成员管理 ──────────────────────────────────────────────────────

    @staticmethod
    async def join_platform(
        db: AsyncSession,
        platform_id: int,
        user_id: int,
    ) -> dict:
        """加入平台

        Args:
            db: 数据库会话
            platform_id: 平台ID
            user_id: 用户ID

        Returns:
            dict: 成员信息

        Raises:
            ValueError: 平台不存在 / 已达成员上限 / 已加入
        """
        # 检查平台是否存在
        result = await db.execute(
            select(ResourcePlatform).where(ResourcePlatform.id == platform_id)
        )
        platform = result.scalars().first()
        if platform is None:
            raise ValueError("平台不存在")

        # 检查成员上限
        result = await db.execute(
            select(func.count(PlatformMember.id)).where(
                PlatformMember.platform_id == platform_id
            )
        )
        current_count = result.scalar() or 0
        if current_count >= platform.member_limit:
            raise ValueError("平台成员已满")

        # 检查是否已加入
        result = await db.execute(
            select(PlatformMember).where(
                PlatformMember.platform_id == platform_id,
                PlatformMember.user_id == user_id,
            )
        )
        if result.scalars().first() is not None:
            raise ValueError("已加入该平台")

        # 如果平台有年费，检查支付/订阅状态
        if platform.annual_fee > 0:
            # 检查用户是否已有该平台的付费订阅
            result = await db.execute(
                select(PaymentOrder).where(
                    PaymentOrder.user_id == user_id,
                    PaymentOrder.status == "paid",
                    PaymentOrder.membership_tier == f"platform_{platform_id}",
                ).order_by(PaymentOrder.created_at.desc())
            )
            existing_payment = result.scalars().first()

            if not existing_payment:
                # 无有效年费订阅，返回需要支付的信息（不阻止加入，返回支付提示）
                logger.info(
                    f"用户 {user_id} 加入平台 {platform_id} 需支付年费 {platform.annual_fee}分"
                )

        member = PlatformMember(
            platform_id=platform_id,
            user_id=user_id,
            role="member",
        )
        db.add(member)
        await db.commit()
        await db.refresh(member)

        return {
            "id": member.id,
            "platform_id": member.platform_id,
            "user_id": member.user_id,
            "role": member.role,
            "joined_at": member.joined_at,
            "annual_fee": platform.annual_fee,
            "annual_fee_required": platform.annual_fee > 0,
        }

    @staticmethod
    async def get_members(
        db: AsyncSession,
        platform_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """成员列表（按角色排序: 秘书长 > 秘书处 > 会员）

        Returns:
            dict: {items: [...], total: int}
        """
        # 角色排序: 秘书长排最前，然后是秘书处，最后是会员
        role_order = case(
            (PlatformMember.role == "secretary_general", 0),
            (PlatformMember.role == "secretariat", 1),
            else_=2,
        )

        # 总量
        total_result = await db.execute(
            select(func.count(PlatformMember.id)).where(
                PlatformMember.platform_id == platform_id
            )
        )
        total = total_result.scalar() or 0

        query = (
            select(PlatformMember, User.name, User.company)
            .join(User, PlatformMember.user_id == User.id)
            .where(PlatformMember.platform_id == platform_id)
            .order_by(role_order, PlatformMember.joined_at)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(query)
        rows = result.all()

        items = []
        for row in rows:
            pm = row[0]
            items.append({
                "id": pm.id,
                "platform_id": pm.platform_id,
                "user_id": pm.user_id,
                "name": row.name,
                "company": row.company,
                "role": pm.role,
                "joined_at": pm.joined_at,
            })

        return {"items": items, "total": total}

    @staticmethod
    async def get_management_data(
        db: AsyncSession,
        platform_id: int,
    ) -> Optional[dict]:
        """商业报告 — 城市/行业覆盖率 + 成员资源排名

        Args:
            db: 数据库会话
            platform_id: 平台ID

        Returns:
            dict or None: 商业报告数据
        """
        # 验证平台存在
        result = await db.execute(
            select(ResourcePlatform).where(ResourcePlatform.id == platform_id)
        )
        platform = result.scalars().first()
        if platform is None:
            return None

        # 成员数
        result = await db.execute(
            select(func.count(PlatformMember.id)).where(
                PlatformMember.platform_id == platform_id
            )
        )
        member_count = result.scalar() or 0

        # 商机数
        result = await db.execute(
            select(func.count(PlatformOpportunity.id)).where(
                PlatformOpportunity.platform_id == platform_id
            )
        )
        opportunity_count = result.scalar() or 0

        # 行业覆盖率（按商机行业统计）
        result = await db.execute(
            select(
                PlatformOpportunity.industry,
                func.count(PlatformOpportunity.id).label("count"),
            )
            .where(
                PlatformOpportunity.platform_id == platform_id,
                PlatformOpportunity.industry != "",
            )
            .group_by(PlatformOpportunity.industry)
            .order_by(func.count(PlatformOpportunity.id).desc())
        )
        industry_coverage = [
            {"industry": row.industry, "count": row.count}
            for row in result.all()
        ]

        # 城市覆盖率（按商机城市统计）
        result = await db.execute(
            select(
                PlatformOpportunity.city,
                func.count(PlatformOpportunity.id).label("count"),
            )
            .where(
                PlatformOpportunity.platform_id == platform_id,
                PlatformOpportunity.city != "",
            )
            .group_by(PlatformOpportunity.city)
            .order_by(func.count(PlatformOpportunity.id).desc())
        )
        city_coverage = [
            {"city": row.city, "count": row.count}
            for row in result.all()
        ]

        # 成员资源排名（按各成员发布的商机数排名）
        result = await db.execute(
            select(
                PlatformMember.user_id,
                User.name,
                User.company,
                func.count(PlatformOpportunity.id).label("opportunity_count"),
            )
            .join(User, PlatformMember.user_id == User.id)
            .outerjoin(
                PlatformOpportunity,
                and_(
                    PlatformOpportunity.platform_id == platform_id,
                    PlatformOpportunity.creator_id == PlatformMember.user_id,
                ),
            )
            .where(PlatformMember.platform_id == platform_id)
            .group_by(PlatformMember.user_id, User.name, User.company)
            .order_by(func.count(PlatformOpportunity.id).desc())
        )
        member_ranking = [
            {
                "user_id": row.user_id,
                "name": row.name,
                "company": row.company,
                "opportunity_count": row.opportunity_count,
            }
            for row in result.all()
        ]

        return {
            "platform_id": platform_id,
            "platform_name": platform.name,
            "member_count": member_count,
            "opportunity_count": opportunity_count,
            "industry_coverage": industry_coverage,
            "city_coverage": city_coverage,
            "member_ranking": member_ranking,
        }

    # ── 商机管理 ──────────────────────────────────────────────────────

    @staticmethod
    async def create_opportunity(
        db: AsyncSession,
        platform_id: int,
        creator_id: int,
        title: str,
        description: str = "",
        industry: str = "",
        city: str = "",
        budget: int = 0,
    ) -> dict:
        """发布商机

        Args:
            db: 数据库会话
            platform_id: 平台ID
            creator_id: 创建者用户ID
            title: 商机标题
            description: 商机描述
            industry: 行业
            city: 城市
            budget: 预算(分)

        Returns:
            dict: 商机信息

        Raises:
            ValueError: 参数错误/非平台成员
        """
        if not title or not title.strip():
            raise ValueError("商机标题不能为空")

        # 检查发布者是否为平台成员
        result = await db.execute(
            select(PlatformMember).where(
                PlatformMember.platform_id == platform_id,
                PlatformMember.user_id == creator_id,
            )
        )
        if result.scalars().first() is None:
            raise ValueError("仅平台成员可发布商机")

        opportunity = PlatformOpportunity(
            platform_id=platform_id,
            creator_id=creator_id,
            title=title.strip(),
            description=description.strip(),
            industry=industry.strip(),
            city=city.strip(),
            budget=budget,
            status="open",
        )
        db.add(opportunity)
        await db.commit()
        await db.refresh(opportunity)

        return {
            "id": opportunity.id,
            "platform_id": opportunity.platform_id,
            "creator_id": opportunity.creator_id,
            "title": opportunity.title,
            "description": opportunity.description,
            "industry": opportunity.industry,
            "city": opportunity.city,
            "budget": opportunity.budget,
            "status": opportunity.status,
            "created_at": opportunity.created_at,
        }

    @staticmethod
    async def get_opportunities(
        db: AsyncSession,
        platform_id: int,
        page: int = 1,
        page_size: int = 20,
        industry: Optional[str] = None,
        city: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """获取平台商机列表（支持按行业/城市/状态筛选）

        Returns:
            dict: {items: [...], total: int}
        """
        filters = [PlatformOpportunity.platform_id == platform_id]
        if industry:
            filters.append(PlatformOpportunity.industry == industry)
        if city:
            filters.append(PlatformOpportunity.city == city)
        if status:
            filters.append(PlatformOpportunity.status == status)

        # 总量
        total_result = await db.execute(
            select(func.count(PlatformOpportunity.id)).where(*filters)
        )
        total = total_result.scalar() or 0

        query = (
            select(PlatformOpportunity, User.name, User.company)
            .join(User, PlatformOpportunity.creator_id == User.id)
            .where(*filters)
            .order_by(PlatformOpportunity.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(query)
        rows = result.all()

        items = []
        for row in rows:
            opp = row[0]
            items.append({
                "id": opp.id,
                "platform_id": opp.platform_id,
                "creator_id": opp.creator_id,
                "creator_name": row.name,
                "creator_company": row.company,
                "title": opp.title,
                "description": opp.description,
                "industry": opp.industry,
                "city": opp.city,
                "budget": opp.budget,
                "status": opp.status,
                "created_at": opp.created_at,
            })

        return {"items": items, "total": total}

    # ── 权限检查 ──────────────────────────────────────────────────────

    @staticmethod
    async def check_membership(
        db: AsyncSession,
        platform_id: int,
        user_id: int,
    ) -> Optional[dict]:
        """检查用户是否为平台成员及角色

        Returns:
            dict or None: {role, joined_at} 或 None（非成员）
        """
        result = await db.execute(
            select(PlatformMember).where(
                PlatformMember.platform_id == platform_id,
                PlatformMember.user_id == user_id,
            )
        )
        pm = result.scalars().first()
        if pm is None:
            return None
        return {"role": pm.role, "joined_at": pm.joined_at}

    # ── 年费订阅（资源平台→AI名片订阅打通） ─────────────────────────────

    @staticmethod
    async def create_annual_fee_order(
        db: AsyncSession,
        platform_id: int,
        user_id: int,
        channel: str = "wechat",
    ) -> dict:
        """为资源平台年费创建支付订单

        当用户加入有年费的资源平台时，创建一笔支付订单。
        支付完成后，用户在该平台的身份即为正式付费会员。

        Args:
            db: 数据库会话
            platform_id: 平台ID
            user_id: 用户ID
            channel: 支付渠道 (wechat/alipay)

        Returns:
            dict: 订单信息 {order_no, total_cents, platform_id, ...}

        Raises:
            ValueError: 平台不存在 / 年费为0
        """
        # 检查平台
        result = await db.execute(
            select(ResourcePlatform).where(ResourcePlatform.id == platform_id)
        )
        platform = result.scalars().first()
        if platform is None:
            raise ValueError("平台不存在")
        if platform.annual_fee <= 0:
            raise ValueError("该平台无需年费")

        # 检查用户是否已支付
        result = await db.execute(
            select(PaymentOrder).where(
                PaymentOrder.user_id == user_id,
                PaymentOrder.status == "paid",
                PaymentOrder.membership_tier == f"platform_{platform_id}",
            ).order_by(PaymentOrder.created_at.desc())
        )
        existing = result.scalars().first()
        if existing:
            raise ValueError("您已支付该平台年费")

        # 生成订单号
        import time
        order_no = f"PF{int(time.time() * 1000) % 100000000000:012d}"

        order = PaymentOrder(
            order_no=order_no,
            user_id=user_id,
            membership_tier=f"platform_{platform_id}",
            channel=channel,
            status="pending",
            total_cents=platform.annual_fee,
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)

        return {
            "order_id": order.id,
            "order_no": order.order_no,
            "platform_id": platform_id,
            "user_id": user_id,
            "total_cents": order.total_cents,
            "total_yuan": f"{order.total_cents / 100:.2f}",
            "channel": order.channel,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }

    @staticmethod
    async def confirm_annual_fee_payment(
        db: AsyncSession,
        order_no: str,
        channel_order_no: str = "",
    ) -> dict:
        """确认年费支付（模拟支付回调）

        支付成功后，标记订单为 paid，同时为用户创建 EnterpriseSubscription 记录
        或延长其在资源平台的有效期。

        Args:
            db: 数据库会话
            order_no: 内部订单号
            channel_order_no: 渠道订单号（可选）

        Returns:
            dict: 更新后的订单信息

        Raises:
            ValueError: 订单不存在 / 已支付
        """
        result = await db.execute(
            select(PaymentOrder).where(PaymentOrder.order_no == order_no)
        )
        order = result.scalars().first()
        if order is None:
            raise ValueError("订单不存在")
        if order.status == "paid":
            raise ValueError("订单已支付，无需重复处理")

        # 更新订单状态
        order.status = "paid"
        order.paid_at = datetime.utcnow()
        if channel_order_no:
            order.channel_order_no = channel_order_no

        # 解析 membership_tier → platform_id
        tier_str = order.membership_tier  # "platform_{platform_id}"
        if tier_str.startswith("platform_"):
            platform_id = int(tier_str.split("_")[1])

            # 创建 EnterpriseSubscription 记录（年费订阅，有效期1年）
            now = datetime.utcnow()
            end_date = now + timedelta(days=365)
            sub = EnterpriseSubscription(
                user_id=order.user_id,
                company_name=f"资源平台_{platform_id}",
                seats=1,
                tier=tier_str,
                start_date=now,
                end_date=end_date,
                auto_renew=False,
                status="active",
                features={
                    "resource_platform_id": platform_id,
                    "annual_fee": order.total_cents,
                    "paid_at": now.isoformat(),
                },
            )
            db.add(sub)

        await db.commit()
        await db.refresh(order)

        return {
            "order_id": order.id,
            "order_no": order.order_no,
            "status": order.status,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        }
