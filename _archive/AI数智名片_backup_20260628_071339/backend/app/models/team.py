"""团队/企业模型：Team, TeamMember, TeamInvite"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Enum, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

import enum


class TeamRole(str, enum.Enum):
    """团队内角色"""
    OWNER = "owner"          # 所有者（创始人）
    ADMIN = "admin"          # 管理员
    MEMBER = "member"        # 普通成员
    VIEWER = "viewer"        # 只读查看者


class InviteStatus(str, enum.Enum):
    """邀请状态"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class Team(Base):
    """团队/企业"""
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="团队名称")
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="唯一标识 slug")
    description: Mapped[str] = mapped_column(Text, default="", comment="团队简介")
    logo: Mapped[str] = mapped_column(String(256), default="", comment="团队 Logo URL")
    website: Mapped[str] = mapped_column(String(256), default="", comment="团队网站")
    industry: Mapped[str] = mapped_column(String(64), default="", comment="所属行业")
    size: Mapped[str] = mapped_column(String(16), default="1-10", comment="团队规模")
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者/所有者")
    max_members: Mapped[int] = mapped_column(Integer, default=50, comment="最大成员数")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class TeamMember(Base):
    """团队成员关系"""
    __tablename__ = "team_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False, comment="团队ID")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    role: Mapped[TeamRole] = mapped_column(Enum(TeamRole), default=TeamRole.MEMBER, comment="角色")
    title_in_team: Mapped[str] = mapped_column(String(128), default="", comment="在团队中的职位")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否在职")
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="加入时间")
    invited_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, comment="邀请人")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TeamInvite(Base):
    """团队邀请"""
    __tablename__ = "team_invites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False, comment="团队ID")
    inviter_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="邀请人ID")
    invitee_email: Mapped[str] = mapped_column(String(256), default="", comment="被邀请人邮箱")
    invitee_phone: Mapped[str] = mapped_column(String(20), default="", comment="被邀请人手机号")
    invitee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, comment="已注册用户的ID")
    role: Mapped[TeamRole] = mapped_column(Enum(TeamRole), default=TeamRole.MEMBER, comment="邀请角色")
    status: Mapped[InviteStatus] = mapped_column(Enum(InviteStatus), default=InviteStatus.PENDING, comment="状态")
    token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, comment="邀请令牌")
    message: Mapped[str] = mapped_column(Text, default="", comment="邀请附言")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ApprovalAction(str, enum.Enum):
    """审批动作类型"""
    JOIN = "join"            # 申请加入团队
    INVITE = "invite"        # 邀请他人加入
    UPGRADE = "upgrade"      # 提升角色
    REMOVE = "remove"        # 移除成员


class ApprovalStatus(str, enum.Enum):
    """审批状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalRequest(Base):
    """团队审批请求"""
    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False, comment="团队ID")
    requester_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="请求人ID")
    action: Mapped[ApprovalAction] = mapped_column(Enum(ApprovalAction), nullable=False, comment="动作类型")
    target_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, comment="目标用户ID")
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="申请原因")
    status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, comment="状态")
    reviewer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, comment="审批人ID")
    reject_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="拒绝原因")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="审批时间")
