"""Tests for trust_service.py — TrustService class.

Coverage targets:
- add_trust: happy path / self-trust / duplicate / nonexistent user
- remove_trust: happy path / nonexistent relationship
- get_trust_network: empty / with trusting / with trusted_by / both
- get_trust_degree: 0 / 1 (direct) / 2 (indirect) / self
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.trust import TrustNetwork
from app.services.trust_service import TrustService


# ── In-memory database fixture ──────────────────────────────────────────────

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def sample_users(db_session):
    """Create three test users for trust network tests."""
    users = [
        User(id=1, phone="13800138001", name="用户A", company="公司A", title="工程师"),
        User(id=2, phone="13800138002", name="用户B", company="公司B", title="设计师"),
        User(id=3, phone="13800138003", name="用户C", company="公司C", title="经理"),
    ]
    db_session.add_all(users)
    db_session.commit()
    for u in users:
        db_session.refresh(u)
    return {u.id: u for u in users}


# ═══════════════════════════════════════════════════════════════════════════
# add_trust
# ═══════════════════════════════════════════════════════════════════════════

class TestAddTrust:
    def test_add_trust_success(self, db_session, sample_users):
        """Happy path: user 1 trusts user 2."""
        trust = TrustService.add_trust(db_session, 1, 2)
        assert trust.user_id == 1
        assert trust.trusted_user_id == 2
        assert trust.id is not None

        # Verify persisted
        saved = db_session.query(TrustNetwork).filter(
            TrustNetwork.user_id == 1,
            TrustNetwork.trusted_user_id == 2,
        ).first()
        assert saved is not None

    def test_self_trust_raises(self, db_session, sample_users):
        """Cannot trust oneself."""
        with pytest.raises(ValueError, match="不能信任自己"):
            TrustService.add_trust(db_session, 1, 1)

    def test_nonexistent_trusted_user_raises(self, db_session, sample_users):
        """Target user must exist in the database."""
        with pytest.raises(ValueError, match="被信任的用户不存在"):
            TrustService.add_trust(db_session, 1, 9999)

    def test_duplicate_trust_raises(self, db_session, sample_users):
        """Cannot add the same trust relationship twice."""
        TrustService.add_trust(db_session, 1, 2)
        with pytest.raises(ValueError, match="已建立信任关系，请勿重复添加"):
            TrustService.add_trust(db_session, 1, 2)

    def test_bidirectional_trust_allowed(self, db_session, sample_users):
        """A→B and B→A should both be allowed."""
        TrustService.add_trust(db_session, 1, 2)
        TrustService.add_trust(db_session, 2, 1)  # Should not raise

        count = db_session.query(TrustNetwork).count()
        assert count == 2


# ═══════════════════════════════════════════════════════════════════════════
# remove_trust
# ═══════════════════════════════════════════════════════════════════════════

class TestRemoveTrust:
    def test_remove_trust_success(self, db_session, sample_users):
        """Happy path: remove an existing trust relationship."""
        TrustService.add_trust(db_session, 1, 2)
        result = TrustService.remove_trust(db_session, 1, 2)
        assert result == {"detail": "信任关系已移除"}

        # Verify deleted
        saved = db_session.query(TrustNetwork).filter(
            TrustNetwork.user_id == 1,
            TrustNetwork.trusted_user_id == 2,
        ).first()
        assert saved is None

    def test_remove_nonexistent_raises(self, db_session, sample_users):
        """Cannot remove a relationship that doesn't exist."""
        with pytest.raises(ValueError, match="信任关系不存在"):
            TrustService.remove_trust(db_session, 1, 2)

    def test_remove_wrong_direction(self, db_session, sample_users):
        """Removing trust in the opposite direction should fail."""
        TrustService.add_trust(db_session, 1, 2)
        # 2 never trusted 1, so removing 2→1 should raise
        with pytest.raises(ValueError, match="信任关系不存在"):
            TrustService.remove_trust(db_session, 2, 1)


# ═══════════════════════════════════════════════════════════════════════════
# get_trust_network
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTrustNetwork:
    def test_empty_network(self, db_session, sample_users):
        """User with no trust relationships."""
        network = TrustService.get_trust_network(db_session, 1)
        assert network == {"trusting": [], "trusted_by": []}

    def test_only_trusting(self, db_session, sample_users):
        """User trusts others but nobody trusts them back."""
        TrustService.add_trust(db_session, 1, 2)
        TrustService.add_trust(db_session, 1, 3)

        network = TrustService.get_trust_network(db_session, 1)
        assert len(network["trusting"]) == 2
        assert len(network["trusted_by"]) == 0
        trusted_ids = {u["id"] for u in network["trusting"]}
        assert trusted_ids == {2, 3}

    def test_only_trusted_by(self, db_session, sample_users):
        """Others trust the user, but user trusts nobody."""
        TrustService.add_trust(db_session, 2, 1)
        TrustService.add_trust(db_session, 3, 1)

        network = TrustService.get_trust_network(db_session, 1)
        assert len(network["trusting"]) == 0
        assert len(network["trusted_by"]) == 2
        trusted_by_ids = {u["id"] for u in network["trusted_by"]}
        assert trusted_by_ids == {2, 3}

    def test_both_directions(self, db_session, sample_users):
        """Full trust network: user both trusts and is trusted."""
        TrustService.add_trust(db_session, 1, 2)   # 1 trusts 2
        TrustService.add_trust(db_session, 3, 1)   # 3 trusts 1

        network = TrustService.get_trust_network(db_session, 1)
        assert len(network["trusting"]) == 1
        assert network["trusting"][0]["id"] == 2
        assert len(network["trusted_by"]) == 1
        assert network["trusted_by"][0]["id"] == 3

    def test_trusted_by_deleted_user(self, db_session, sample_users):
        """If a trusted user is deleted from DB, they should be filtered out."""
        # Make user 2 trust user 1
        TrustService.add_trust(db_session, 2, 1)
        # Delete user 2
        db_session.query(User).filter(User.id == 2).delete()
        db_session.commit()

        network = TrustService.get_trust_network(db_session, 1)
        # user 2 no longer exists, should be filtered out
        assert len(network["trusted_by"]) == 0


# ═══════════════════════════════════════════════════════════════════════════
# get_trust_degree
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTrustDegree:
    def test_self_returns_zero(self, db_session, sample_users):
        """Trust degree to self should be 0."""
        degree = TrustService.get_trust_degree(db_session, 1, 1)
        assert degree == 0

    def test_no_relationship_returns_zero(self, db_session, sample_users):
        """No trust relationship between users."""
        degree = TrustService.get_trust_degree(db_session, 1, 2)
        assert degree == 0

    def test_direct_trust_returns_one(self, db_session, sample_users):
        """Direct trust (A trusts B) = degree 1."""
        TrustService.add_trust(db_session, 1, 2)
        degree = TrustService.get_trust_degree(db_session, 1, 2)
        assert degree == 1

    def test_indirect_trust_returns_two(self, db_session, sample_users):
        """Indirect trust (A trusts B, B trusts C) = degree 2."""
        # Create a trust chain: 1 → 2 → 3
        TrustService.add_trust(db_session, 1, 2)
        TrustService.add_trust(db_session, 2, 3)

        degree = TrustService.get_trust_degree(db_session, 1, 3)
        assert degree == 2

    def test_indirect_not_through_direct(self, db_session, sample_users):
        """If both direct and indirect exist, should return 1 (closer)."""
        TrustService.add_trust(db_session, 1, 2)   # direct
        TrustService.add_trust(db_session, 2, 3)
        TrustService.add_trust(db_session, 1, 3)   # also direct!

        degree = TrustService.get_trust_degree(db_session, 1, 3)
        assert degree == 1  # direct takes priority

    def test_no_indirect_path(self, db_session, sample_users):
        """A trusts B, but B does not trust C → no path to C."""
        TrustService.add_trust(db_session, 1, 2)
        # No trust from 2 to 3
        degree = TrustService.get_trust_degree(db_session, 1, 3)
        assert degree == 0

    def test_reverse_direction_not_counted(self, db_session, sample_users):
        """B trusts A should not count as A trusting B."""
        TrustService.add_trust(db_session, 2, 1)  # 2 trusts 1
        degree = TrustService.get_trust_degree(db_session, 1, 2)
        assert degree == 0  # 1 does not trust 2
