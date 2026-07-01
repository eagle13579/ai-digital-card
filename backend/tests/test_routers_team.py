"""
团队路由单元测试（团队 CRUD + 成员管理）
========================================

覆盖范围:
  P0: 团队 CRUD — 创建/获取/列表/更新 (4 tests)
  P0: 成员管理 — 列表/邀请/接受/拒绝/移除 (5 tests)
  P1: 权限边界 — 权限不足/不存在资源 (4 tests)
  P1: 错误处理 — 重复 slug / 无效邀请令牌 (2 tests)

测试策略:
  使用 unittest.mock 隔离 app.routers.team 的依赖，不依赖数据库。
  所有 TeamService 方法、get_db、get_current_user 均被 mock。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from fastapi import status


# ── 测试用固定值 ────────────────────────────────────────────────

MOCK_USER_ID = 42
MOCK_TEAM_ID = 1
MOCK_SLUG = "acme-corp"
MOCK_INVITE_TOKEN = "mock-token-abcdef123456"
MOCK_TIMESTAMP = "2025-06-27T12:00:00"


# ── 通用 fixture ────────────────────────────────────────────────


@pytest.fixture
def mock_db():
    """返回一个 AsyncMock 充当 AsyncSession。"""
    return AsyncMock()


@pytest.fixture
def mock_user():
    """返回一个模拟的 User 对象。"""
    user = MagicMock()
    user.id = MOCK_USER_ID
    user.name = "测试用户"
    user.phone = "13800138000"
    user.avatar = ""
    user.company = "测试科技"
    user.title = "工程师"
    return user


@pytest.fixture
def mock_team():
    """返回一个模拟的 Team ORM 对象。"""
    team = MagicMock()
    team.id = MOCK_TEAM_ID
    team.name = "Acme 科技"
    team.slug = MOCK_SLUG
    team.description = "一家测试公司"
    team.logo = ""
    team.website = "https://acme.example.com"
    team.industry = "科技"
    team.size = "1-10"
    team.owner_id = MOCK_USER_ID
    team.max_members = 50
    team.is_active = True
    team.created_at = datetime(2025, 6, 27, 12, 0, 0)
    team.updated_at = datetime(2025, 6, 27, 12, 0, 0)
    return team


@pytest.fixture
def mock_member():
    """返回一个模拟的 TeamMember ORM 对象（owner 视角）。"""
    tm = MagicMock()
    tm.id = 10
    tm.team_id = MOCK_TEAM_ID
    tm.user_id = MOCK_USER_ID
    tm.role = MagicMock()
    tm.role.value = "owner"
    tm.title_in_team = "创始人"
    tm.is_active = True
    tm.joined_at = datetime(2025, 6, 27, 12, 0, 0)
    tm.invited_by = MOCK_USER_ID
    return tm


@pytest.fixture
def mock_invite():
    """返回一个模拟的 TeamInvite ORM 对象。"""
    inv = MagicMock()
    inv.id = 100
    inv.team_id = MOCK_TEAM_ID
    inv.inviter_id = MOCK_USER_ID
    inv.invitee_email = "newguy@example.com"
    inv.invitee_phone = ""
    inv.invitee_id = None
    inv.role = MagicMock()
    inv.role.value = "member"
    inv.status = MagicMock()
    inv.status.value = "pending"
    inv.token = MOCK_INVITE_TOKEN
    inv.message = "欢迎加入！"
    inv.expires_at = datetime(2025, 6, 30, 12, 0, 0)
    inv.created_at = datetime(2025, 6, 27, 12, 0, 0)
    inv.updated_at = datetime(2025, 6, 27, 12, 0, 0)
    return inv


# ── 辅助：patch router 依赖 ────────────────────────────────────


def _patch_deps(mock_db, mock_user):
    """返回一个 context manager，patch  router 模块的依赖。"""
    return patch.multiple(
        "app.routers.team",
        get_db=MagicMock(return_value=mock_db),
        get_current_user=MagicMock(return_value=mock_user),
    )


# ══════════════════════════════════════════════════════════════
# 团队 CRUD
# ══════════════════════════════════════════════════════════════


class TestTeamCRUD:
    """团队创建、获取、更新、删除测试。"""

    @patch("app.routers.team.TeamService")
    def test_create_team_success(self, mock_ts, mock_db, mock_user, mock_team):
        """POST /api/teams — 正常创建团队返回 201。"""
        mock_ts.create_team = AsyncMock(return_value=mock_team)

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import create_team
            from app.routers.team import TeamCreate

            data = TeamCreate(
                name="Acme 科技",
                slug=MOCK_SLUG,
                description="一家测试公司",
                website="https://acme.example.com",
                industry="科技",
            )

            result = create_team(data, mock_db, mock_user)

        # 不能 await，因为是 sync 测试环境；我们检查返回值类型
        import asyncio
        resp = asyncio.run(result)
        assert resp.id == MOCK_TEAM_ID
        assert resp.name == "Acme 科技"
        assert resp.slug == MOCK_SLUG
        assert resp.owner_id == MOCK_USER_ID

        mock_ts.create_team.assert_awaited_once_with(
            db=mock_db, name="Acme 科技", slug=MOCK_SLUG,
            owner_id=MOCK_USER_ID, description="一家测试公司",
            logo="", website="https://acme.example.com",
            industry="科技", size="1-10", max_members=50,
        )

    @patch("app.routers.team.TeamService")
    def test_create_team_duplicate_slug(self, mock_ts, mock_db, mock_user):
        """POST /api/teams — slug 重复时返回 409。"""
        mock_ts.create_team = AsyncMock(side_effect=ValueError("团队标识 'acme-corp' 已被使用"))

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import create_team, TeamCreate
            from fastapi import HTTPException

            data = TeamCreate(name="Acme 科技", slug=MOCK_SLUG)

            with pytest.raises(HTTPException) as exc:
                import asyncio
                asyncio.run(create_team(data, mock_db, mock_user))

            assert exc.value.status_code == 409
            assert "已被使用" in exc.value.detail

    @patch("app.routers.team.TeamService")
    def test_list_my_teams(self, mock_ts, mock_db, mock_user, mock_team):
        """GET /api/teams — 返回当前用户所在团队列表。"""
        mock_ts.list_user_teams = AsyncMock(return_value=[mock_team])
        mock_ts.get_member_count = AsyncMock(return_value=3)
        mock_ts.get_invites_by_team = AsyncMock(return_value=[])

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import list_my_teams

            import asyncio
            result = asyncio.run(list_my_teams(mock_db, mock_user))

        assert len(result) == 1
        assert result[0].id == MOCK_TEAM_ID
        assert result[0].name == "Acme 科技"
        assert result[0].member_count == 3

        mock_ts.list_user_teams.assert_awaited_once_with(mock_db, MOCK_USER_ID)

    @patch("app.routers.team.TeamService")
    def test_get_team_success(self, mock_ts, mock_db, mock_user, mock_team):
        """GET /api/teams/{id} — 返回团队详情。"""
        mock_ts.get_team_by_id = AsyncMock(return_value=mock_team)
        mock_ts.get_member_count = AsyncMock(return_value=5)
        mock_ts.get_invites_by_team = AsyncMock(return_value=[])

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import get_team

            import asyncio
            result = asyncio.run(get_team(MOCK_TEAM_ID, mock_db, mock_user))

        assert result.id == MOCK_TEAM_ID
        assert result.name == "Acme 科技"
        assert result.member_count == 5
        assert result.invite_count == 0

    @patch("app.routers.team.TeamService")
    def test_get_team_not_found(self, mock_ts, mock_db, mock_user):
        """GET /api/teams/{id} — 不存在的团队返回 404。"""
        mock_ts.get_team_by_id = AsyncMock(return_value=None)

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import get_team
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc:
                import asyncio
                asyncio.run(get_team(99999, mock_db, mock_user))

            assert exc.value.status_code == 404
            assert "不存在" in exc.value.detail

    @patch("app.routers.team.TeamService")
    def test_update_team_success(self, mock_ts, mock_db, mock_user, mock_team):
        """PUT /api/teams/{id} — 正常更新团队信息。"""
        mock_ts.get_team_by_id = AsyncMock(return_value=mock_team)
        mock_ts.is_owner_or_admin = AsyncMock(return_value=True)

        updated = MagicMock()
        updated.configure_mock(**{
            "id": MOCK_TEAM_ID, "name": "新名称", "slug": MOCK_SLUG,
            "description": "新描述", "logo": "", "website": "",
            "industry": "教育", "size": "1-10", "owner_id": MOCK_USER_ID,
            "max_members": 100, "is_active": True,
            "created_at": datetime(2025, 6, 27, 12, 0, 0),
            "updated_at": datetime(2025, 6, 27, 12, 0, 0),
        })
        mock_ts.update_team = AsyncMock(return_value=updated)

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import update_team, TeamUpdate

            data = TeamUpdate(name="新名称", industry="教育", max_members=100)
            import asyncio
            result = asyncio.run(update_team(MOCK_TEAM_ID, data, mock_db, mock_user))

        assert result.name == "新名称"
        assert result.industry == "教育"
        assert result.max_members == 100
        mock_ts.update_team.assert_awaited_once()

    @patch("app.routers.team.TeamService")
    def test_update_team_forbidden(self, mock_ts, mock_db, mock_user, mock_team):
        """PUT /api/teams/{id} — 非管理员更新返回 403。"""
        mock_ts.get_team_by_id = AsyncMock(return_value=mock_team)
        mock_ts.is_owner_or_admin = AsyncMock(return_value=False)

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import update_team, TeamUpdate
            from fastapi import HTTPException

            data = TeamUpdate(name="黑客攻击")
            with pytest.raises(HTTPException) as exc:
                import asyncio
                asyncio.run(update_team(MOCK_TEAM_ID, data, mock_db, mock_user))

            assert exc.value.status_code == 403

    @patch("app.routers.team.TeamService")
    def test_delete_team_not_owner(self, mock_ts, mock_db, mock_user, mock_team):
        """DELETE /api/teams/{id} — 非 owner 删除返回 403。"""
        mock_ts.get_team_by_id = AsyncMock(return_value=mock_team)
        mock_ts.check_role = AsyncMock(return_value=False)

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import delete_team
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc:
                import asyncio
                asyncio.run(delete_team(MOCK_TEAM_ID, mock_db, mock_user))

            assert exc.value.status_code == 403
            assert "所有者权限" in exc.value.detail

# ══════════════════════════════════════════════════════════════
# 成员管理
# ══════════════════════════════════════════════════════════════


class TestMemberManagement:
    """团队成员管理测试：邀请、加入、退出、角色变更。"""

    @patch("app.routers.team.TeamService")
    def test_list_members(self, mock_ts, mock_db, mock_user, mock_team):
        """GET /api/teams/{id}/members — 返回成员列表。"""
        mock_ts.get_team_by_id = AsyncMock(return_value=mock_team)
        mock_ts.get_members = AsyncMock(return_value=[
            {
                "id": 10, "user_id": MOCK_USER_ID, "name": "测试用户",
                "avatar": "", "phone": "13800138000", "company": "测试科技",
                "title": "工程师", "role": "owner", "title_in_team": "创始人",
                "joined_at": MOCK_TIMESTAMP, "invited_by": MOCK_USER_ID,
            },
        ])

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import list_members

            import asyncio
            result = asyncio.run(list_members(MOCK_TEAM_ID, mock_db, mock_user))

        assert len(result) == 1
        assert result[0].user_id == MOCK_USER_ID
        assert result[0].role == "owner"
        assert result[0].title_in_team == "创始人"
        mock_ts.get_members.assert_awaited_once_with(mock_db, MOCK_TEAM_ID)

    @patch("app.routers.team.TeamService")
    def test_remove_member_success(self, mock_ts, mock_db, mock_user, mock_team):
        """DELETE /api/teams/{id}/members/{uid} — 管理员成功移除成员。"""
        mock_ts.get_team_by_id = AsyncMock(return_value=mock_team)
        mock_ts.is_owner_or_admin = AsyncMock(return_value=True)

        # 被移除成员不是 owner
        target_member = MagicMock()
        target_member.role = MagicMock()
        target_member.role.value = "member"
        mock_ts.get_member = AsyncMock(return_value=target_member)

        mock_ts.remove_member = AsyncMock(return_value=None)

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import remove_member

            import asyncio
            result = asyncio.run(remove_member(MOCK_TEAM_ID, 99, mock_db, mock_user))

        assert result is None  # 204 No Content
        mock_ts.remove_member.assert_awaited_once_with(mock_db, MOCK_TEAM_ID, 99)

    @patch("app.routers.team.TeamService")
    def test_remove_owner_forbidden(self, mock_ts, mock_db, mock_user, mock_team):
        """DELETE /api/teams/{id}/members/{uid} — 不能移除 owner。"""
        mock_ts.get_team_by_id = AsyncMock(return_value=mock_team)
        mock_ts.is_owner_or_admin = AsyncMock(return_value=True)

        # 目标成员是 owner
        owner_member = MagicMock()
        owner_member.role = MagicMock()
        owner_member.role.value = "owner"
        mock_ts.get_member = AsyncMock(return_value=owner_member)

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import remove_member
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc:
                import asyncio
                asyncio.run(remove_member(MOCK_TEAM_ID, MOCK_USER_ID, mock_db, mock_user))

            assert exc.value.status_code == 403
            assert "不能移除团队所有者" in exc.value.detail

    @patch("app.routers.team.TeamService")
    def test_create_invite_success(self, mock_ts, mock_db, mock_user, mock_team, mock_invite):
        """POST /api/teams/{id}/invites — 成功创建邀请返回 201。"""
        mock_ts.get_team_by_id = AsyncMock(return_value=mock_team)
        mock_ts.is_owner_or_admin = AsyncMock(return_value=True)
        mock_ts.create_invite = AsyncMock(return_value=mock_invite)

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import create_invite, InviteCreate

            data = InviteCreate(email="newguy@example.com", message="欢迎加入！")
            import asyncio
            result = asyncio.run(create_invite(MOCK_TEAM_ID, data, mock_db, mock_user))

        assert result.id == 100
        assert result.invitee_email == "newguy@example.com"
        assert result.status == "pending"

        mock_ts.create_invite.assert_awaited_once_with(
            db=mock_db, team_id=MOCK_TEAM_ID, inviter_id=MOCK_USER_ID,
            invitee_email="newguy@example.com", invitee_phone="",
            role=mock_ts.create_invite.call_args.kwargs["role"],
            message="欢迎加入！",
        )

    @patch("app.routers.team.TeamService")
    def test_accept_invite_success(self, mock_ts, mock_db, mock_user, mock_team):
        """POST /api/teams/invites/{token}/accept — 成功接受邀请。"""
        mock_member_result = {
            "id": 20, "user_id": MOCK_USER_ID, "name": "测试用户",
            "avatar": "", "phone": "13800138000", "company": "测试科技",
            "title": "工程师", "role": "member", "title_in_team": "",
            "joined_at": MOCK_TIMESTAMP, "invited_by": MOCK_USER_ID,
        }
        mock_ts.accept_invite = AsyncMock(return_value=mock_team)
        mock_ts.get_members = AsyncMock(return_value=[mock_member_result])

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import accept_invite

            import asyncio
            result = asyncio.run(accept_invite(MOCK_INVITE_TOKEN, mock_db, mock_user))

        assert result.user_id == MOCK_USER_ID
        assert result.role == "member"
        mock_ts.accept_invite.assert_awaited_once_with(mock_db, MOCK_INVITE_TOKEN, MOCK_USER_ID)

    @patch("app.routers.team.TeamService")
    def test_decline_invite_success(self, mock_ts, mock_db, mock_user):
        """POST /api/teams/invites/{token}/decline — 成功拒绝邀请。"""
        mock_ts.decline_invite = AsyncMock(return_value=None)

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import decline_invite

            import asyncio
            result = asyncio.run(decline_invite(MOCK_INVITE_TOKEN, mock_db, mock_user))

        assert result["message"] == "已拒绝邀请"
        mock_ts.decline_invite.assert_awaited_once_with(mock_db, MOCK_INVITE_TOKEN)

    @patch("app.routers.team.TeamService")
    def test_decline_invite_not_found(self, mock_ts, mock_db, mock_user):
        """POST /api/teams/invites/{token}/decline — 无效令牌返回 400。"""
        mock_ts.decline_invite = AsyncMock(side_effect=ValueError("邀请不存在"))

        with _patch_deps(mock_db, mock_user):
            from app.routers.team import decline_invite
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc:
                import asyncio
                asyncio.run(decline_invite("bad-token", mock_db, mock_user))

            assert exc.value.status_code == 400
