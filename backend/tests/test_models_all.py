"""
全模型测试 — 覆盖 13+ 个 ORM 模型（≤200行）
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select


class TestUserModel:
    @pytest.mark.asyncio
    async def test_create_user(self, test_db_session):
        from app.models.user import User
        u = User(phone="15000000001", name="全模型测试", password_hash="hash")
        test_db_session.add(u); await test_db_session.commit()
        assert u.id and u.name == "全模型测试" and u.role == "user"

    @pytest.mark.asyncio
    async def test_unique_phone(self, test_db_session):
        from app.models.user import User
        from sqlalchemy.exc import IntegrityError
        test_db_session.add(User(phone="15000000002", name="A", password_hash="h"))
        await test_db_session.commit()
        test_db_session.add(User(phone="15000000002", name="B", password_hash="h"))
        with pytest.raises(IntegrityError):
            await test_db_session.commit()
        await test_db_session.rollback()


class TestBrochureModel:
    @pytest.mark.asyncio
    async def test_create_brochure_with_pages_and_cascade(self, test_db_session):
        from app.models.user import User
        from app.models.brochure import Brochure, Page
        u = User(phone="15100000001", name="画册主", password_hash="h")
        test_db_session.add(u); await test_db_session.flush()
        b = Brochure(user_id=u.id, title="测试画册")
        test_db_session.add(b); await test_db_session.flush()
        test_db_session.add(Page(brochure_id=b.id, sort_order=0, content="第一页"))
        test_db_session.add(Page(brochure_id=b.id, sort_order=1, content="第二页"))
        await test_db_session.commit()
        pages = (await test_db_session.execute(
            select(Page.id).where(Page.brochure_id == b.id)
        )).scalars().all()
        assert len(pages) == 2 and b.status == "draft"
        # cascade delete
        pid = pages[0]
        await test_db_session.delete(b); await test_db_session.commit()
        assert await test_db_session.get(Page, pid) is None


class TestTeamModel:
    @pytest.mark.asyncio
    async def test_create_team_with_member(self, test_db_session):
        from app.models.user import User
        from app.models.team import Team, TeamMember
        u = User(phone="15200000001", name="队长", password_hash="h")
        test_db_session.add(u); await test_db_session.flush()
        t = Team(name="测试团队", slug="test-team", owner_id=u.id)
        test_db_session.add(t); await test_db_session.flush()
        tm = TeamMember(team_id=t.id, user_id=u.id, role="owner")
        test_db_session.add(tm); await test_db_session.commit()
        assert t.slug == "test-team" and tm.joined_at is not None

    @pytest.mark.asyncio
    async def test_team_invite(self, test_db_session):
        from app.models.user import User
        from app.models.team import Team, TeamInvite
        u = User(phone="15200000002", name="邀请者", password_hash="h")
        test_db_session.add(u); await test_db_session.flush()
        t = Team(name="招人", slug="recruit", owner_id=u.id)
        test_db_session.add(t); await test_db_session.flush()
        inv = TeamInvite(team_id=t.id, inviter_id=u.id, token="tok123",
                         invitee_email="test@example.com",
                         expires_at=datetime.utcnow() + timedelta(days=7))
        test_db_session.add(inv); await test_db_session.commit()
        assert inv.status.value == "pending"


class TestPaymentModel:
    @pytest.mark.asyncio
    async def test_payment_order(self, test_db_session):
        from app.models.payment import PaymentOrder
        po = PaymentOrder(order_no="ORD001", user_id=1, membership_tier="gold",
                          channel="wechat", total_cents=9900)
        test_db_session.add(po); await test_db_session.commit()
        assert po.status == "pending" and po.id is not None

    @pytest.mark.asyncio
    async def test_enterprise_subscription(self, test_db_session):
        from app.models.payment import EnterpriseSubscription
        es = EnterpriseSubscription(user_id=1, company_name="测试企业", seats=10,
                                    tier="business",
                                    start_date=datetime.utcnow(),
                                    end_date=datetime.utcnow() + timedelta(days=365))
        test_db_session.add(es); await test_db_session.commit()
        assert es.status == "active" and es.auto_renew is True


class TestABTestModel:
    @pytest.mark.asyncio
    async def test_ab_test_with_variants(self, test_db_session):
        from app.models.user import User
        from app.models.ab_test import ABTest, ABTestVariant
        u = User(phone="15300000001", name="AB实验", password_hash="h")
        test_db_session.add(u); await test_db_session.flush()
        ab = ABTest(user_id=u.id, name="标题测试")
        test_db_session.add(ab); await test_db_session.flush()
        v1 = ABTestVariant(experiment_id=ab.id, name="A", is_control=True, sort_order=0)
        v2 = ABTestVariant(experiment_id=ab.id, name="B", sort_order=1)
        test_db_session.add_all([v1, v2]); await test_db_session.commit()
        variants = (await test_db_session.execute(
            select(ABTestVariant).where(ABTestVariant.experiment_id == ab.id)
        )).scalars().all()
        assert len(variants) == 2 and v1.is_control
        assert ab.status == "draft"


class TestApiKeyModel:
    @pytest.mark.asyncio
    async def test_api_key_create_and_mask(self, test_db_session):
        from app.models.api_key import ApiKey
        ak = ApiKey(user_id=1, name="测试Key", permissions='["read","write"]')
        test_db_session.add(ak); await test_db_session.commit()
        assert ak.key.startswith("ask_") and "****" in ak.mask_key()
        assert ak.get_permissions_list() == ["read", "write"]


class TestAuditLogModel:
    @pytest.mark.asyncio
    async def test_audit_log_create(self, test_db_session):
        from app.models.audit import AuditLog
        al = AuditLog(user_id=1, action="LOGIN", resource="/api/auth/login",
                      ip="192.168.1.1", user_agent="pytest")
        test_db_session.add(al); await test_db_session.commit()
        assert al.action == "LOGIN" and al.timestamp is not None


class TestWebhookModel:
    @pytest.mark.asyncio
    async def test_webhook_subscription_events(self, test_db_session):
        from app.models.webhook import WebhookSubscription
        wh = WebhookSubscription(user_id=1, url="https://hook.example.com/cb",
                                 events='["card.created","card.updated"]')
        test_db_session.add(wh); await test_db_session.commit()
        assert wh.get_events_list() == ["card.created", "card.updated"]
        assert wh.active is True and wh.retry_count == 3


class TestIntegrationModel:
    @pytest.mark.asyncio
    async def test_integration_config(self, test_db_session):
        from app.models.integration import Integration
        ig = Integration(user_id=1, provider="hubspot", enabled=True)
        ig.set_config_dict({"api_key": "abc123"})
        test_db_session.add(ig); await test_db_session.commit()
        assert ig.provider == "hubspot"
        assert ig.get_config_dict() == {"api_key": "abc123"}


class TestTagAndMatchModel:
    @pytest.mark.asyncio
    async def test_user_tag_and_match(self, test_db_session):
        from app.models.user import User
        from app.models.tag import UserTag, MatchRecord
        u1 = User(phone="15400000001", name="标签A", password_hash="h")
        u2 = User(phone="15400000002", name="标签B", password_hash="h")
        test_db_session.add_all([u1, u2]); await test_db_session.flush()
        test_db_session.add(UserTag(user_id=u1.id, tag_type="provide", tag="Python"))
        test_db_session.add(UserTag(user_id=u2.id, tag_type="need", tag="Python"))
        mr = MatchRecord(user_a_id=u1.id, user_b_id=u2.id, match_score=0.85)
        test_db_session.add(mr); await test_db_session.commit()
        assert mr.status == "pending" and mr.match_score == 0.85


class TestVisitorLogModel:
    @pytest.mark.asyncio
    async def test_visitor_log(self, test_db_session):
        from app.models.user import User
        from app.models.brochure import Brochure
        from app.models.visitor import VisitorLog
        u = User(phone="15500000001", name="访客测试", password_hash="h")
        test_db_session.add(u); await test_db_session.flush()
        b = Brochure(user_id=u.id, title="访客画册")
        test_db_session.add(b); await test_db_session.flush()
        vl = VisitorLog(brochure_id=b.id, visitor_name="路人", source="qrcode")
        test_db_session.add(vl); await test_db_session.commit()
        assert vl.interested is False and vl.visit_time is not None


class TestTrustNetworkModel:
    @pytest.mark.asyncio
    async def test_trust_relationship(self, test_db_session):
        from app.models.user import User
        from app.models.trust import TrustNetwork
        u1 = User(phone="15600000001", name="甲", password_hash="h")
        u2 = User(phone="15600000002", name="乙", password_hash="h")
        test_db_session.add_all([u1, u2]); await test_db_session.flush()
        tn = TrustNetwork(user_id=u1.id, trusted_user_id=u2.id)
        test_db_session.add(tn); await test_db_session.commit()
        assert tn.id is not None
