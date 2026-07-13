"""团队业务逻辑服务"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import (
    Team, TeamMember, TeamInvite,
    TeamRole, InviteStatus,
)
from app.models.user import User


class TeamService:
    """团队管理服务"""

    # ── 团队 CRUD ────────────────────────────────────────────────

    @staticmethod
    async def create_team(
        db: AsyncSession,
        name: str,
        slug: str,
        owner_id: int,
        description: str = "",
        logo: str = "",
        website: str = "",
        industry: str = "",
        size: str = "1-10",
        max_members: int = 50,
    ) -> Team:
        """创建团队，同时将创建者添加为 owner"""
        # 检查 slug 唯一性
        existing = await db.execute(select(Team).where(Team.slug == slug))
        if existing.scalars().first():
            raise ValueError(f"团队标识 '{slug}' 已被使用")

        team = Team(
            name=name,
            slug=slug,
            description=description,
            logo=logo,
            website=website,
            industry=industry,
            size=size,
            owner_id=owner_id,
            max_members=max_members,
        )
        db.add(team)
        await db.flush()  # 获取 team.id

        # 将创建者添加为 owner
        member = TeamMember(
            team_id=team.id,
            user_id=owner_id,
            role=TeamRole.OWNER,
            title_in_team="创始人",
            invited_by=owner_id,
        )
        db.add(member)
        await db.commit()
        await db.refresh(team)
        return team

    @staticmethod
    async def get_team_by_id(db: AsyncSession, team_id: int) -> Optional[Team]:
        result = await db.execute(select(Team).where(Team.id == team_id, Team.is_active))
        return result.scalars().first()

    @staticmethod
    async def get_team_by_slug(db: AsyncSession, slug: str) -> Optional[Team]:
        result = await db.execute(select(Team).where(Team.slug == slug, Team.is_active))
        return result.scalars().first()

    @staticmethod
    async def update_team(db: AsyncSession, team: Team, **kwargs) -> Team:
        """更新团队信息"""
        for field, value in kwargs.items():
            if value is not None and hasattr(team, field):
                setattr(team, field, value)
        await db.commit()
        await db.refresh(team)
        return team

    @staticmethod
    async def delete_team(db: AsyncSession, team: Team) -> None:
        """软删除团队"""
        team.is_active = False
        await db.commit()

    @staticmethod
    async def list_user_teams(db: AsyncSession, user_id: int) -> list[Team]:
        """获取用户加入的所有活跃团队"""
        result = await db.execute(
            select(Team).join(TeamMember, TeamMember.team_id == Team.id)
            .where(TeamMember.user_id == user_id, TeamMember.is_active, Team.is_active)
            .order_by(Team.created_at.desc())
        )
        return list(result.scalars().all())

    # ── 成员管理 ────────────────────────────────────────────────

    @staticmethod
    async def get_members(db: AsyncSession, team_id: int) -> list[dict]:
        """获取团队所有成员（含用户信息）"""
        result = await db.execute(
            select(TeamMember, User)
            .join(User, User.id == TeamMember.user_id)
            .where(TeamMember.team_id == team_id, TeamMember.is_active)
            .order_by(TeamMember.role, TeamMember.joined_at)
        )
        rows = result.all()
        members = []
        for member, user in rows:
            members.append({
                "id": member.id,
                "user_id": user.id,
                "name": user.name,
                "avatar": user.avatar,
                "phone": user.phone,
                "company": user.company,
                "title": user.title,
                "role": member.role.value,
                "title_in_team": member.title_in_team,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                "invited_by": member.invited_by,
            })
        return members

    @staticmethod
    async def get_member(db: AsyncSession, team_id: int, user_id: int) -> Optional[TeamMember]:
        result = await db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
                TeamMember.is_active,
            )
        )
        return result.scalars().first()

    @staticmethod
    async def update_member_role(
        db: AsyncSession, team_id: int, user_id: int, new_role: TeamRole
    ) -> TeamMember:
        """更新成员角色"""
        member = await TeamService.get_member(db, team_id, user_id)
        if not member:
            raise ValueError("成员不存在")
        member.role = new_role
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def update_member_title(
        db: AsyncSession, team_id: int, user_id: int, title: str
    ) -> TeamMember:
        """更新成员职位"""
        member = await TeamService.get_member(db, team_id, user_id)
        if not member:
            raise ValueError("成员不存在")
        member.title_in_team = title
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def remove_member(db: AsyncSession, team_id: int, user_id: int) -> None:
        """移除成员（软删除）"""
        member = await TeamService.get_member(db, team_id, user_id)
        if not member:
            raise ValueError("成员不存在")
        member.is_active = False
        await db.commit()

    @staticmethod
    async def get_member_count(db: AsyncSession, team_id: int) -> int:
        result = await db.execute(
            select(func.count(TeamMember.id))
            .where(TeamMember.team_id == team_id, TeamMember.is_active)
        )
        return result.scalar() or 0

    # ── 邀请管理 ────────────────────────────────────────────────

    @staticmethod
    async def create_invite(
        db: AsyncSession,
        team_id: int,
        inviter_id: int,
        invitee_email: str = "",
        invitee_phone: str = "",
        invitee_id: Optional[int] = None,
        role: TeamRole = TeamRole.MEMBER,
        message: str = "",
        expires_in_hours: int = 72,
    ) -> TeamInvite:
        """创建邀请"""
        # 检查是否已存在待处理的邀请
        conditions = [
            TeamInvite.team_id == team_id,
            TeamInvite.status == InviteStatus.PENDING,
        ]
        if invitee_id:
            conditions.append(TeamInvite.invitee_id == invitee_id)
        if invitee_email:
            conditions.append(TeamInvite.invitee_email == invitee_email)
        if invitee_phone:
            conditions.append(TeamInvite.invitee_phone == invitee_phone)

        existing = await db.execute(
            select(TeamInvite).where(and_(*conditions))
        )
        if existing.scalars().first():
            raise ValueError("已存在待处理的邀请")

        token = uuid.uuid4().hex + uuid.uuid4().hex[:16]
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

        invite = TeamInvite(
            team_id=team_id,
            inviter_id=inviter_id,
            invitee_email=invitee_email,
            invitee_phone=invitee_phone,
            invitee_id=invitee_id,
            role=role,
            status=InviteStatus.PENDING,
            token=token,
            message=message,
            expires_at=expires_at,
        )
        db.add(invite)
        await db.commit()
        await db.refresh(invite)
        return invite

    @staticmethod
    async def get_invites_by_team(db: AsyncSession, team_id: int) -> list[TeamInvite]:
        """获取团队的所有邀请"""
        result = await db.execute(
            select(TeamInvite)
            .where(TeamInvite.team_id == team_id)
            .order_by(TeamInvite.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_invite_by_token(db: AsyncSession, token: str) -> Optional[TeamInvite]:
        result = await db.execute(
            select(TeamInvite).where(TeamInvite.token == token)
        )
        return result.scalars().first()

    @staticmethod
    async def accept_invite(db: AsyncSession, token: str, user_id: int) -> TeamMember:
        """接受邀请"""
        invite = await TeamService.get_invite_by_token(db, token)
        if not invite:
            raise ValueError("邀请不存在或已失效")
        if invite.status != InviteStatus.PENDING:
            raise ValueError("邀请已处理")
        if invite.expires_at < datetime.utcnow():
            invite.status = InviteStatus.EXPIRED
            await db.commit()
            raise ValueError("邀请已过期")

        # 检查团队是否已满
        team = await TeamService.get_team_by_id(db, invite.team_id)
        if not team:
            raise ValueError("团队不存在")
        member_count = await TeamService.get_member_count(db, team.id)
        if member_count >= team.max_members:
            raise ValueError("团队人数已达上限")

        # 检查用户是否已是成员
        existing = await TeamService.get_member(db, invite.team_id, user_id)
        if existing:
            invite.status = InviteStatus.ACCEPTED
            await db.commit()
            return existing

        # 创建成员关系
        member = TeamMember(
            team_id=invite.team_id,
            user_id=user_id,
            role=invite.role,
            invited_by=invite.inviter_id,
        )
        db.add(member)
        invite.status = InviteStatus.ACCEPTED
        invite.invitee_id = user_id
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def decline_invite(db: AsyncSession, token: str) -> None:
        """拒绝邀请"""
        invite = await TeamService.get_invite_by_token(db, token)
        if not invite:
            raise ValueError("邀请不存在")
        invite.status = InviteStatus.DECLINED
        await db.commit()

    @staticmethod
    async def cancel_invite(db: AsyncSession, invite_id: int) -> None:
        """取消邀请"""
        result = await db.execute(
            select(TeamInvite).where(TeamInvite.id == invite_id)
        )
        invite = result.scalars().first()
        if not invite:
            raise ValueError("邀请不存在")
        invite.status = InviteStatus.EXPIRED
        await db.commit()

    # ── 权限检查 ────────────────────────────────────────────────

    @staticmethod
    async def check_role(
        db: AsyncSession, team_id: int, user_id: int,
        required_roles: set[TeamRole] | None = None,
    ) -> bool:
        """检查用户在团队中是否具有指定角色"""
        member = await TeamService.get_member(db, team_id, user_id)
        if not member:
            return False
        if required_roles is None:
            return True  # 只要是成员即可
        return member.role in required_roles

    @staticmethod
    async def is_owner_or_admin(db: AsyncSession, team_id: int, user_id: int) -> bool:
        return await TeamService.check_role(
            db, team_id, user_id, {TeamRole.OWNER, TeamRole.ADMIN}
        )
