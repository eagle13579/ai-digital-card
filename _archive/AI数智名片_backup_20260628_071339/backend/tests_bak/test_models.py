"""
Model creation and query tests for AI Digital Business Card.

Tests cover:
- User model: create, query, unique constraints
- Brochure & Page models: create, relationship, cascade delete
- Tag model: create, filter by type
- TrustNetwork model: create, bidirectional relationships
- VisitorLog model: create, query

Each test uses a fresh in-memory SQLite database.
"""

import pytest
from sqlalchemy import select, func


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, test_db_session):
        """Creating a user should persist and return correct attributes."""
        from app.models.user import User
        from app.routers.auth import pwd_context

        user = User(
            phone="13600000001",
            name="模型测试用户",
            username="modeltest",
            company="测试集团",
            title="数据工程师",
            intro="模型测试专用",
            password_hash=pwd_context.hash("pass123"),
        )
        test_db_session.add(user)
        test_db_session.commit()

        assert user.id is not None
        assert user.id > 0
        assert user.name == "模型测试用户"
        assert user.phone == "13600000001"
        assert user.role == "user"  # default
        assert user.created_at is not None

    def test_query_user_by_phone(self, test_db_session):
        """Querying a user by phone should work."""
        from app.models.user import User
        from app.routers.auth import pwd_context

        user = User(phone="13600000002", name="查询测试", password_hash="hash")
        test_db_session.add(user)
        test_db_session.commit()

        found = test_db_session.query(User).filter(User.phone == "13600000002").first()
        assert found is not None
        assert found.name == "查询测试"

    def test_unique_phone_constraint(self, test_db_session):
        """Duplicate phone numbers should raise an integrity error."""
        from app.models.user import User
        from app.routers.auth import pwd_context
        from sqlalchemy.exc import IntegrityError

        user1 = User(phone="13600000003", name="用户A", password_hash="hash1")
        user2 = User(phone="13600000003", name="用户B", password_hash="hash2")
        test_db_session.add(user1)
        test_db_session.commit()

        test_db_session.add(user2)
        with pytest.raises(IntegrityError):
            test_db_session.commit()

        test_db_session.rollback()

    def test_user_defaults(self, test_db_session):
        """New user should have sensible defaults."""
        from app.models.user import User

        user = User(phone="13600000004", name="默认值测试", password_hash="hash")
        test_db_session.add(user)
        test_db_session.commit()

        assert user.company == ""
        assert user.title == ""
        assert user.intro == ""
        assert user.avatar == ""
        assert user.role == "user"
        assert user.username is None


class TestBrochureModel:
    """Tests for the Brochure and Page models."""

    def test_create_brochure(self, test_db_session):
        """Creating a brochure should return correct attributes."""
        from app.models.user import User
        from app.models.brochure import Brochure

        user = User(phone="13700000001", name="画册主人", password_hash="hash")
        test_db_session.add(user)
        test_db_session.flush()

        brochure = Brochure(
            user_id=user.id,
            title="我的作品集",
            cover="https://example.com/cover.jpg",
        )
        test_db_session.add(brochure)
        test_db_session.commit()

        assert brochure.id is not None
        assert brochure.title == "我的作品集"
        assert brochure.status == "draft"  # default
        assert brochure.view_count == 0
        assert brochure.pages_count == 1  # default
        assert len(brochure.share_token) == 16

    def test_brochure_with_pages(self, test_db_session):
        """A brochure should be able to have multiple pages."""
        from app.models.user import User
        from app.models.brochure import Brochure, Page

        user = User(phone="13700000002", name="画册主人2", password_hash="hash")
        test_db_session.add(user)
        test_db_session.flush()

        brochure = Brochure(user_id=user.id, title="多页画册", pages_count=3)
        test_db_session.add(brochure)
        test_db_session.flush()

        pages = [
            Page(brochure_id=brochure.id, sort_order=0, content="第一页"),
            Page(brochure_id=brochure.id, sort_order=1, content="第二页"),
            Page(brochure_id=brochure.id, sort_order=2, content="第三页"),
        ]
        for p in pages:
            test_db_session.add(p)
        test_db_session.commit()

        # Verify relationship via backref
        assert len(brochure.pages) == 3
        assert brochure.pages[0].content == "第一页"

    def test_cascade_delete_brochure(self, test_db_session):
        """Deleting a brochure should cascade-delete its pages."""
        from app.models.user import User
        from app.models.brochure import Brochure, Page

        user = User(phone="13700000003", name="级联删除测试", password_hash="hash")
        test_db_session.add(user)
        test_db_session.flush()

        brochure = Brochure(user_id=user.id, title="将被删除")
        test_db_session.add(brochure)
        test_db_session.flush()

        test_db_session.add(Page(brochure_id=brochure.id, content="附件页"))
        test_db_session.commit()

        page_id = brochure.pages[0].id
        test_db_session.delete(brochure)
        test_db_session.commit()

        # Pages should be gone
        remaining = test_db_session.query(Page).filter(Page.id == page_id).count()
        assert remaining == 0

    def test_share_token_unique(self, test_db_session):
        """Share tokens should be unique across brochures."""
        from app.models.user import User
        from app.models.brochure import Brochure

        user = User(phone="13700000004", name="唯一性测试", password_hash="hash")
        test_db_session.add(user)
        test_db_session.flush()

        b1 = Brochure(user_id=user.id, title="画册A")
        b2 = Brochure(user_id=user.id, title="画册B")
        test_db_session.add(b1)
        test_db_session.add(b2)
        test_db_session.commit()

        assert b1.share_token != b2.share_token


class TestTagModel:
    """Tests for the UserTag model."""

    def test_create_tag(self, test_db_session):
        """Creating a tag should persist correctly."""
        from app.models.user import User
        from app.models.tag import UserTag

        user = User(phone="13900000001", name="标签用户", password_hash="hash")
        test_db_session.add(user)
        test_db_session.flush()

        tag = UserTag(user_id=user.id, tag_type="provide", tag="Python开发", weight=0.9)
        test_db_session.add(tag)
        test_db_session.commit()

        assert tag.id is not None
        assert tag.tag == "Python开发"
        assert tag.tag_type == "provide"
        assert tag.source == "manual"  # default

    def test_filter_tags_by_type(self, test_db_session):
        """Tags should be filterable by type (provide/need)."""
        from app.models.user import User
        from app.models.tag import UserTag

        user = User(phone="13900000002", name="多标签用户", password_hash="hash")
        test_db_session.add(user)
        test_db_session.flush()

        tags = [
            UserTag(user_id=user.id, tag_type="provide", tag="Python"),
            UserTag(user_id=user.id, tag_type="provide", tag="Django"),
            UserTag(user_id=user.id, tag_type="need", tag="设计师"),
        ]
        for t in tags:
            test_db_session.add(t)
        test_db_session.commit()

        provide_tags = (
            test_db_session.query(UserTag)
            .filter(UserTag.user_id == user.id, UserTag.tag_type == "provide")
            .all()
        )
        assert len(provide_tags) == 2

        need_tags = (
            test_db_session.query(UserTag)
            .filter(UserTag.user_id == user.id, UserTag.tag_type == "need")
            .all()
        )
        assert len(need_tags) == 1


class TestTrustNetworkModel:
    """Tests for the TrustNetwork model."""

    def test_create_trust_relationship(self, test_db_session):
        """Creating a trust relationship should persist."""
        from app.models.user import User
        from app.models.trust import TrustNetwork

        user_a = User(phone="13100000001", name="用户甲", password_hash="hash")
        user_b = User(phone="13100000002", name="用户乙", password_hash="hash")
        test_db_session.add_all([user_a, user_b])
        test_db_session.flush()

        trust = TrustNetwork(user_id=user_a.id, trusted_user_id=user_b.id)
        test_db_session.add(trust)
        test_db_session.commit()

        assert trust.id is not None
        assert trust.user_id == user_a.id
        assert trust.trusted_user_id == user_b.id

    def test_bidirectional_trust_query(self, test_db_session):
        """Query trust relationships in both directions."""
        from app.models.user import User
        from app.models.trust import TrustNetwork

        user_a = User(phone="13100000003", name="用户丙", password_hash="hash")
        user_b = User(phone="13100000004", name="用户丁", password_hash="hash")
        test_db_session.add_all([user_a, user_b])
        test_db_session.flush()

        # A trusts B
        test_db_session.add(TrustNetwork(user_id=user_a.id, trusted_user_id=user_b.id))
        test_db_session.commit()

        # Who does A trust?
        trusting = (
            test_db_session.query(TrustNetwork)
            .filter(TrustNetwork.user_id == user_a.id)
            .all()
        )
        assert len(trusting) == 1
        assert trusting[0].trusted_user_id == user_b.id

        # Who trusts B?
        trusted_by = (
            test_db_session.query(TrustNetwork)
            .filter(TrustNetwork.trusted_user_id == user_b.id)
            .all()
        )
        assert len(trusted_by) == 1
        assert trusted_by[0].user_id == user_a.id


class TestVisitorLogModel:
    """Tests for the VisitorLog model."""

    def test_create_visitor_log(self, test_db_session):
        """Creating a visitor log entry should persist."""
        from app.models.user import User
        from app.models.brochure import Brochure
        from app.models.visitor import VisitorLog

        user = User(phone="13200000001", name="访客测试", password_hash="hash")
        test_db_session.add(user)
        test_db_session.flush()

        brochure = Brochure(user_id=user.id, title="访客画册")
        test_db_session.add(brochure)
        test_db_session.flush()

        log = VisitorLog(
            brochure_id=brochure.id,
            visitor_name="路人甲",
            visitor_ip="127.0.0.1",
            source="direct",
            page_viewed="首页",
            duration=30,
        )
        test_db_session.add(log)
        test_db_session.commit()

        assert log.id is not None
        assert log.interested is False  # default
        assert log.visit_time is not None

    def test_query_visitor_logs(self, test_db_session):
        """Visitor logs should be queryable by brochure."""
        from app.models.user import User
        from app.models.brochure import Brochure
        from app.models.visitor import VisitorLog

        user = User(phone="13200000002", name="访客测试2", password_hash="hash")
        test_db_session.add(user)
        test_db_session.flush()

        brochure = Brochure(user_id=user.id, title="访客画册2")
        test_db_session.add(brochure)
        test_db_session.flush()

        logs = [
            VisitorLog(brochure_id=brochure.id, visitor_name="访客1"),
            VisitorLog(brochure_id=brochure.id, visitor_name="访客2"),
        ]
        for log in logs:
            test_db_session.add(log)
        test_db_session.commit()

        results = (
            test_db_session.query(VisitorLog)
            .filter(VisitorLog.brochure_id == brochure.id)
            .all()
        )
        assert len(results) == 2
