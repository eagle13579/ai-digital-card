"""团队管理 API：CRUD + 成员管理 + 邀请管理 + 角色管理"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from datetime import datetime

from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.team import (
    Team, TeamRole, InviteStatus,
    ApprovalRequest, ApprovalAction, ApprovalStatus,
    TeamMember,
)
from app.routers.auth import get_current_user
from app.services.team_service import TeamService

router = APIRouter(prefix="/api/teams", tags=["团队管理"])

# ─── Schemas ────────────────────────────────────────────────────


class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9\-]+$")
    description: str = ""
    logo: str = ""
    website: str = ""
    industry: str = ""
    size: str = "1-10"
    max_members: int = 50


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    max_members: Optional[int] = None


class TeamResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    logo: str
    website: str
    industry: str
    size: str
    owner_id: int
    max_members: int
    is_active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    id: int
    user_id: int
    name: str
    avatar: str
    phone: str
    company: str
    title: str
    role: str
    title_in_team: str
    joined_at: Optional[str] = None
    invited_by: Optional[int] = None


class RoleUpdate(BaseModel):
    role: str = Field(..., pattern=r"^(owner|admin|member|viewer)$")


class TitleUpdate(BaseModel):
    title_in_team: str = Field(..., max_length=128)


class InviteCreate(BaseModel):
    email: str = ""
    phone: str = ""
    role: str = "member"
    message: str = ""


class InviteResponse(BaseModel):
    id: int
    team_id: int
    inviter_id: int
    invitee_email: str
    invitee_phone: str
    invitee_id: Optional[int] = None
    role: str
    status: str
    token: str
    message: str
    expires_at: str
    created_at: str

    model_config = {"from_attributes": True}


class TeamDetailResponse(BaseModel):
    """团队详情，含成员数和邀请数"""
    id: int
    name: str
    slug: str
    description: str
    logo: str
    website: str
    industry: str
    size: str
    owner_id: int
    max_members: int
    member_count: int
    invite_count: int
    is_active: bool
    created_at: str
    updated_at: str


# ─── Helper ─────────────────────────────────────────────────────


async def _get_team_or_404(db: AsyncSession, team_id: int) -> Team:
    team = await TeamService.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    return team


async def _require_admin(
    db: AsyncSession, team_id: int, user_id: int,
) -> None:
    """要求用户是团队 owner 或 admin"""
    if not await TeamService.is_owner_or_admin(db, team_id, user_id):
        raise HTTPException(status_code=403, detail="权限不足，需要管理员或所有者权限")


async def _require_owner(
    db: AsyncSession, team_id: int, user_id: int,
) -> None:
    """要求用户是团队 owner"""
    if not await TeamService.check_role(db, team_id, user_id, {TeamRole.OWNER}):
        raise HTTPException(status_code=403, detail="权限不足，需要所有者权限")


# ─── Team CRUD ──────────────────────────────────────────────────


@router.post("", response_model=TeamResponse, status_code=201)
async def create_team(
    data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建团队"""
    try:
        team = await TeamService.create_team(
            db=db,
            name=data.name,
            slug=data.slug,
            owner_id=current_user.id,
            description=data.description,
            logo=data.logo,
            website=data.website,
            industry=data.industry,
            size=data.size,
            max_members=data.max_members,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return TeamResponse(
        id=team.id,
        name=team.name,
        slug=team.slug,
        description=team.description,
        logo=team.logo,
        website=team.website,
        industry=team.industry,
        size=team.size,
        owner_id=team.owner_id,
        max_members=team.max_members,
        is_active=team.is_active,
        created_at=team.created_at.isoformat() if team.created_at else "",
        updated_at=team.updated_at.isoformat() if team.updated_at else "",
    )


@router.get("", response_model=list[TeamDetailResponse])
async def list_my_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户加入的所有团队"""
    teams = await TeamService.list_user_teams(db, current_user.id)
    results = []
    for team in teams:
        member_count = await TeamService.get_member_count(db, team.id)
        invites = await TeamService.get_invites_by_team(db, team.id)
        pending_count = sum(1 for i in invites if i.status == InviteStatus.PENDING)
        results.append(TeamDetailResponse(
            id=team.id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            logo=team.logo,
            website=team.website,
            industry=team.industry,
            size=team.size,
            owner_id=team.owner_id,
            max_members=team.max_members,
            member_count=member_count,
            invite_count=pending_count,
            is_active=team.is_active,
            created_at=team.created_at.isoformat() if team.created_at else "",
            updated_at=team.updated_at.isoformat() if team.updated_at else "",
        ))
    return results


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取团队详情"""
    team = await _get_team_or_404(db, team_id)
    member_count = await TeamService.get_member_count(db, team.id)
    invites = await TeamService.get_invites_by_team(db, team.id)
    pending_count = sum(1 for i in invites if i.status == InviteStatus.PENDING)

    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        slug=team.slug,
        description=team.description,
        logo=team.logo,
        website=team.website,
        industry=team.industry,
        size=team.size,
        owner_id=team.owner_id,
        max_members=team.max_members,
        member_count=member_count,
        invite_count=pending_count,
        is_active=team.is_active,
        created_at=team.created_at.isoformat() if team.created_at else "",
        updated_at=team.updated_at.isoformat() if team.updated_at else "",
    )


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新团队信息（需 owner 或 admin）"""
    team = await _get_team_or_404(db, team_id)
    await _require_admin(db, team_id, current_user.id)

    update_data = data.model_dump(exclude_unset=True)
    team = await TeamService.update_team(db, team, **update_data)

    return TeamResponse(
        id=team.id,
        name=team.name,
        slug=team.slug,
        description=team.description,
        logo=team.logo,
        website=team.website,
        industry=team.industry,
        size=team.size,
        owner_id=team.owner_id,
        max_members=team.max_members,
        is_active=team.is_active,
        created_at=team.created_at.isoformat() if team.created_at else "",
        updated_at=team.updated_at.isoformat() if team.updated_at else "",
    )


@router.delete("/{team_id}", status_code=204)
async def delete_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除团队（需 owner）"""
    team = await _get_team_or_404(db, team_id)
    await _require_owner(db, team_id, current_user.id)
    await TeamService.delete_team(db, team)


# ─── 成员管理 ──────────────────────────────────────────────────


@router.get("/{team_id}/members", response_model=list[MemberResponse])
async def list_members(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取团队成员列表"""
    await _get_team_or_404(db, team_id)
    members = await TeamService.get_members(db, team_id)
    return [MemberResponse(**m) for m in members]


@router.put("/{team_id}/members/{user_id}/role")
async def update_member_role(
    team_id: int,
    user_id: int,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新成员角色（需 owner 或 admin）"""
    await _get_team_or_404(db, team_id)
    await _require_admin(db, team_id, current_user.id)

    # 只有 owner 才能设置为 admin
    new_role = TeamRole(data.role)
    if new_role == TeamRole.OWNER:
        await _require_owner(db, team_id, current_user.id)

    try:
        member = await TeamService.update_member_role(
            db, team_id, user_id, new_role
        )
        return {"message": "角色更新成功", "role": member.role.value}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{team_id}/members/{user_id}/title")
async def update_member_title(
    team_id: int,
    user_id: int,
    data: TitleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新成员职位（需 admin）"""
    await _get_team_or_404(db, team_id)
    await _require_admin(db, team_id, current_user.id)

    try:
        member = await TeamService.update_member_title(
            db, team_id, user_id, data.title_in_team
        )
        return {"message": "职位更新成功", "title_in_team": member.title_in_team}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{team_id}/members/{user_id}", status_code=204)
async def remove_member(
    team_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """移除成员（需 admin，不能移除 owner）"""
    await _get_team_or_404(db, team_id)
    await _require_admin(db, team_id, current_user.id)

    # 不能移除 owner
    member = await TeamService.get_member(db, team_id, user_id)
    if member and member.role == TeamRole.OWNER:
        raise HTTPException(status_code=403, detail="不能移除团队所有者")

    try:
        await TeamService.remove_member(db, team_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─── 邀请管理 ──────────────────────────────────────────────────


@router.post("/{team_id}/invites", response_model=InviteResponse, status_code=201)
async def create_invite(
    team_id: int,
    data: InviteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """邀请成员加入团队（需 admin）"""
    await _get_team_or_404(db, team_id)
    await _require_admin(db, team_id, current_user.id)

    if not data.email and not data.phone:
        raise HTTPException(status_code=400, detail="邮箱或手机号至少需要一项")

    try:
        invite = await TeamService.create_invite(
            db=db,
            team_id=team_id,
            inviter_id=current_user.id,
            invitee_email=data.email,
            invitee_phone=data.phone,
            role=TeamRole(data.role),
            message=data.message,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return InviteResponse(
        id=invite.id,
        team_id=invite.team_id,
        inviter_id=invite.inviter_id,
        invitee_email=invite.invitee_email,
        invitee_phone=invite.invitee_phone,
        invitee_id=invite.invitee_id,
        role=invite.role.value if hasattr(invite.role, 'value') else invite.role,
        status=invite.status.value if hasattr(invite.status, 'value') else invite.status,
        token=invite.token,
        message=invite.message,
        expires_at=invite.expires_at.isoformat() if invite.expires_at else "",
        created_at=invite.created_at.isoformat() if invite.created_at else "",
    )


@router.get("/{team_id}/invites", response_model=list[InviteResponse])
async def list_invites(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取团队邀请列表（需 admin）"""
    await _get_team_or_404(db, team_id)
    await _require_admin(db, team_id, current_user.id)

    invites = await TeamService.get_invites_by_team(db, team_id)
    result = []
    for invite in invites:
        result.append(InviteResponse(
            id=invite.id,
            team_id=invite.team_id,
            inviter_id=invite.inviter_id,
            invitee_email=invite.invitee_email,
            invitee_phone=invite.invitee_phone,
            invitee_id=invite.invitee_id,
            role=invite.role.value if hasattr(invite.role, 'value') else invite.role,
            status=invite.status.value if hasattr(invite.status, 'value') else invite.status,
            token=invite.token,
            message=invite.message,
            expires_at=invite.expires_at.isoformat() if invite.expires_at else "",
            created_at=invite.created_at.isoformat() if invite.created_at else "",
        ))
    return result


@router.delete("/{team_id}/invites/{invite_id}", status_code=204)
async def cancel_invite(
    team_id: int,
    invite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消邀请（需 admin）"""
    await _get_team_or_404(db, team_id)
    await _require_admin(db, team_id, current_user.id)
    await TeamService.cancel_invite(db, invite_id)


# ─── 公开邀请处理 ──────────────────────────────────────────────


@router.post("/invites/{token}/accept", response_model=MemberResponse)
async def accept_invite(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """接受团队邀请"""
    try:
        member = await TeamService.accept_invite(db, token, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 获取用户信息
    members = await TeamService.get_members(db, member.team_id)
    for m in members:
        if m["user_id"] == current_user.id:
            return MemberResponse(**m)
    raise HTTPException(status_code=500, detail="加入成功但获取成员信息失败")


@router.post("/invites/{token}/decline")
async def decline_invite(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """拒绝团队邀请"""
    try:
        await TeamService.decline_invite(db, token)
        return {"message": "已拒绝邀请"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── 审批流 ──────────────────────────────────────────────────


class ApprovalRequestCreate(BaseModel):
    """提交审批请求"""
    action: str = Field(..., pattern=r"^(join|invite|upgrade|remove)$", description="动作: join/invite/upgrade/remove")
    target_user_id: Optional[int] = Field(None, description="目标用户ID (join时可不填,默认为自己)")
    reason: Optional[str] = Field(None, max_length=500, description="申请原因")


class ApprovalRequestResponse(BaseModel):
    """审批请求响应"""
    id: int
    team_id: int
    requester_id: int
    action: str
    target_user_id: Optional[int] = None
    reason: Optional[str] = None
    status: str
    reviewer_id: Optional[int] = None
    reject_reason: Optional[str] = None
    created_at: str
    reviewed_at: Optional[str] = None

    model_config = {"from_attributes": True}


class ApprovalActionRequest(BaseModel):
    """审批操作"""
    action: str = Field(..., pattern=r"^(approve|reject)$", description="approve 或 reject")
    reject_reason: Optional[str] = Field(None, max_length=500, description="拒绝原因")


async def _execute_approval_action(
    db: AsyncSession, req: ApprovalRequest,
) -> None:
    """审批通过后自动执行对应动作"""
    action = req.action
    team_id = req.team_id
    requester_id = req.requester_id
    target_id = req.target_user_id if req.target_user_id else requester_id

    if action == ApprovalAction.JOIN:
        # 申请加入团队 → 添加为普通成员
        existing = await TeamService.get_member(db, team_id, requester_id)
        if existing:
            return  # 已是成员，跳过
        team = await TeamService.get_team_by_id(db, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="团队不存在")
        member_count = await TeamService.get_member_count(db, team_id)
        if member_count >= team.max_members:
            raise HTTPException(status_code=400, detail="团队人数已达上限")
        member = TeamMember(
            team_id=team_id,
            user_id=requester_id,
            role=TeamRole.MEMBER,
            invited_by=None,
        )
        db.add(member)

    elif action == ApprovalAction.INVITE:
        # 邀请他人 → 直接添加目标用户为成员
        if not target_id:
            raise HTTPException(status_code=400, detail="邀请操作需要指定目标用户ID")
        existing = await TeamService.get_member(db, team_id, target_id)
        if existing:
            return
        team = await TeamService.get_team_by_id(db, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="团队不存在")
        member_count = await TeamService.get_member_count(db, team_id)
        if member_count >= team.max_members:
            raise HTTPException(status_code=400, detail="团队人数已达上限")
        member = TeamMember(
            team_id=team_id,
            user_id=target_id,
            role=TeamRole.MEMBER,
            invited_by=requester_id,
        )
        db.add(member)

    elif action == ApprovalAction.UPGRADE:
        # 提升角色 → 升级为目标（默认 MEMBER→ADMIN）
        if not target_id:
            raise HTTPException(status_code=400, detail="升级操作需要指定目标用户ID")
        member = await TeamService.get_member(db, team_id, target_id)
        if not member:
            raise HTTPException(status_code=404, detail="目标成员不存在")
        if member.role == TeamRole.OWNER:
            raise HTTPException(status_code=400, detail="不能升级团队所有者")
        member.role = TeamRole.ADMIN

    elif action == ApprovalAction.REMOVE:
        # 移除成员
        if not target_id:
            raise HTTPException(status_code=400, detail="移除操作需要指定目标用户ID")
        member = await TeamService.get_member(db, team_id, target_id)
        if not member:
            raise HTTPException(status_code=404, detail="目标成员不存在")
        if member.role == TeamRole.OWNER:
            raise HTTPException(status_code=400, detail="不能移除团队所有者")
        member.is_active = False


@router.post("/{team_id}/approval-requests", response_model=ApprovalRequestResponse, status_code=201)
async def create_approval_request(
    team_id: int,
    data: ApprovalRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交审批请求（需要是团队成员）"""
    await _get_team_or_404(db, team_id)

    # 必须已是团队成员才能提交审批
    member = await TeamService.get_member(db, team_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="只有团队成员才能提交审批请求")

    action = ApprovalAction(data.action)
    target_user_id = data.target_user_id

    # 参数校验
    if action == ApprovalAction.JOIN:
        if target_user_id is not None and target_user_id != current_user.id:
            raise HTTPException(status_code=400, detail="join 操作的 target_user_id 必须为自己或不填")
        target_user_id = current_user.id  # join 默认为自己

    if action in (ApprovalAction.INVITE, ApprovalAction.UPGRADE, ApprovalAction.REMOVE):
        if not target_user_id:
            raise HTTPException(status_code=400, detail=f"{data.action} 操作需要指定 target_user_id")

    if action == ApprovalAction.UPGRADE:
        # 不能升级自己
        if target_user_id == current_user.id:
            raise HTTPException(status_code=400, detail="不能申请升级自己")
        target_member = await TeamService.get_member(db, team_id, target_user_id)
        if not target_member:
            raise HTTPException(status_code=404, detail="目标用户不是团队成员")
        if target_member.role == TeamRole.OWNER:
            raise HTTPException(status_code=400, detail="不能升级团队所有者")

    if action == ApprovalAction.REMOVE:
        if target_user_id == current_user.id:
            raise HTTPException(status_code=400, detail="不能申请移除自己")
        target_member = await TeamService.get_member(db, team_id, target_user_id)
        if not target_member:
            raise HTTPException(status_code=404, detail="目标用户不是团队成员")
        if target_member.role == TeamRole.OWNER:
            raise HTTPException(status_code=400, detail="不能移除团队所有者")

    if action == ApprovalAction.INVITE:
        existing = await TeamService.get_member(db, team_id, target_user_id)
        if existing:
            raise HTTPException(status_code=400, detail="目标用户已是团队成员")

    # 检查是否已有该用户该团队的待处理审批
    existing_req = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.team_id == team_id,
            ApprovalRequest.requester_id == current_user.id,
            ApprovalRequest.action == action,
            ApprovalRequest.status == ApprovalStatus.PENDING,
        )
    )
    if existing_req.scalars().first():
        raise HTTPException(status_code=409, detail="已有相同待处理的审批请求")

    approval_req = ApprovalRequest(
        team_id=team_id,
        requester_id=current_user.id,
        action=action,
        target_user_id=target_user_id,
        reason=data.reason,
        status=ApprovalStatus.PENDING,
    )
    db.add(approval_req)
    await db.commit()
    await db.refresh(approval_req)

    return ApprovalRequestResponse(
        id=approval_req.id,
        team_id=approval_req.team_id,
        requester_id=approval_req.requester_id,
        action=approval_req.action.value,
        target_user_id=approval_req.target_user_id,
        reason=approval_req.reason,
        status=approval_req.status.value,
        reviewer_id=approval_req.reviewer_id,
        reject_reason=approval_req.reject_reason,
        created_at=approval_req.created_at.isoformat() if approval_req.created_at else "",
        reviewed_at=approval_req.reviewed_at.isoformat() if approval_req.reviewed_at else None,
    )


@router.get("/{team_id}/approval-requests", response_model=list[ApprovalRequestResponse])
async def list_approval_requests(
    team_id: int,
    status: Optional[str] = Query(None, pattern=r"^(pending|approved|rejected)$", description="筛选状态"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查看团队的审批请求列表（需 admin/owner）"""
    await _get_team_or_404(db, team_id)
    await _require_admin(db, team_id, current_user.id)

    conditions = [ApprovalRequest.team_id == team_id]
    if status:
        conditions.append(ApprovalRequest.status == ApprovalStatus(status))
    else:
        # 默认只显示待审批
        conditions.append(ApprovalRequest.status == ApprovalStatus.PENDING)

    result = await db.execute(
        select(ApprovalRequest)
        .where(*conditions)
        .order_by(ApprovalRequest.created_at.desc())
    )
    requests = result.scalars().all()

    return [
        ApprovalRequestResponse(
            id=req.id,
            team_id=req.team_id,
            requester_id=req.requester_id,
            action=req.action.value,
            target_user_id=req.target_user_id,
            reason=req.reason,
            status=req.status.value,
            reviewer_id=req.reviewer_id,
            reject_reason=req.reject_reason,
            created_at=req.created_at.isoformat() if req.created_at else "",
            reviewed_at=req.reviewed_at.isoformat() if req.reviewed_at else None,
        )
        for req in requests
    ]


@router.put("/{team_id}/approval-requests/{req_id}")
async def review_approval_request(
    team_id: int,
    req_id: int,
    data: ApprovalActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审批请求（approve/reject，需 admin/owner）"""
    await _get_team_or_404(db, team_id)
    await _require_admin(db, team_id, current_user.id)

    # 获取审批请求
    result = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.id == req_id,
            ApprovalRequest.team_id == team_id,
        )
    )
    req = result.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="审批请求不存在")

    if req.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="该审批请求已被处理")

    decision = data.action
    now = datetime.utcnow()

    if decision == "approve":
        # 审批通过 → 执行对应动作
        try:
            await _execute_approval_action(db, req)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"执行审批动作失败: {str(e)}")

        req.status = ApprovalStatus.APPROVED
        req.reviewer_id = current_user.id
        req.reviewed_at = now

        await db.commit()
        return {
            "message": "审批已通过",
            "action": req.action.value,
            "status": ApprovalStatus.APPROVED.value,
        }

    elif decision == "reject":
        req.status = ApprovalStatus.REJECTED
        req.reviewer_id = current_user.id
        req.reviewed_at = now
        req.reject_reason = data.reject_reason

        await db.commit()
        return {
            "message": "审批已拒绝",
            "action": req.action.value,
            "status": ApprovalStatus.REJECTED.value,
        }

    raise HTTPException(status_code=400, detail="无效的审批操作")
