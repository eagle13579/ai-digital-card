"""Tests for matching_engine.py — MatchEngine class (三层综合评分)."""

import json
import math
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.tag import UserTag, MatchRecord
from app.models.brochure import Brochure, Page
from app.services.matching_engine import MatchEngine


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
    """Create two test users with tags for matching tests."""
    u1 = User(id=1, phone="13800138001", name="用户A", company="公司A",
              title="工程师", intro="Python开发, 数据分析",
              password_hash="hashed_pw")
    u2 = User(id=2, phone="13800138002", name="用户B", company="公司B",
              title="设计师", intro="UI设计, 品牌设计",
              password_hash="hashed_pw")
    db_session.add_all([u1, u2])
    db_session.commit()

    # Tags for user A: provide = Python,数据分析 ; need = 设计,品牌
    for tag, w in [("Python", 0.9), ("数据分析", 0.8)]:
        db_session.add(UserTag(user_id=1, tag=tag, tag_type="provide", weight=w))
    for tag, w in [("设计", 0.7), ("品牌", 0.6)]:
        db_session.add(UserTag(user_id=1, tag=tag, tag_type="need", weight=w))

    # Tags for user B: provide = 设计,品牌 ; need = Python,数据分析
    for tag, w in [("设计", 0.8), ("品牌", 0.7)]:
        db_session.add(UserTag(user_id=2, tag=tag, tag_type="provide", weight=w))
    for tag, w in [("Python", 0.9), ("数据分析", 0.7)]:
        db_session.add(UserTag(user_id=2, tag=tag, tag_type="need", weight=w))

    db_session.commit()
    db_session.refresh(u1)
    db_session.refresh(u2)
    return u1, u2


# ═══════════════════════════════════════════════════════════════════════════
# _build_tag_vector
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildTagVector:
    def test_build_provide_vector(self, db_session, sample_users):
        u1, u2 = sample_users
        vec = MatchEngine._build_tag_vector(db_session, u1.id, "provide")
        assert vec == {"Python": 0.9, "数据分析": 0.8}

    def test_build_need_vector(self, db_session, sample_users):
        u1, u2 = sample_users
        vec = MatchEngine._build_tag_vector(db_session, u1.id, "need")
        assert vec == {"设计": 0.7, "品牌": 0.6}

    def test_empty_tags(self, db_session):
        u = User(id=99, phone="13900999001", name="空用户")
        db_session.add(u)
        db_session.commit()
        vec = MatchEngine._build_tag_vector(db_session, u.id, "provide")
        assert vec == {}


# ═══════════════════════════════════════════════════════════════════════════
# _cosine_similarity
# ═══════════════════════════════════════════════════════════════════════════

class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = {"a": 1.0, "b": 0.5}
        sim = MatchEngine._cosine_similarity(v, v)
        # cosine of identical vectors = 1.0, normalized = (1+1)/2 = 1.0
        assert sim == 1.0

    def test_orthogonal_vectors(self):
        a = {"a": 1.0}
        b = {"b": 1.0}
        sim = MatchEngine._cosine_similarity(a, b)
        assert sim == 0.5  # (0 + 1)/2

    def test_zero_vector_a(self):
        sim = MatchEngine._cosine_similarity({}, {"a": 1.0})
        assert sim == 0.0

    def test_zero_vector_b(self):
        sim = MatchEngine._cosine_similarity({"a": 1.0}, {})
        assert sim == 0.0

    def test_both_zero(self):
        sim = MatchEngine._cosine_similarity({}, {})
        assert sim == 0.0

    def test_partial_overlap(self):
        a = {"a": 1.0, "b": 1.0}
        b = {"a": 1.0, "c": 1.0}
        sim = MatchEngine._cosine_similarity(a, b)
        # dot=1, norm_a=sqrt(2), norm_b=sqrt(2) → cos=0.5 → norm=(0.5+1)/2=0.75
        assert sim == pytest.approx(0.75, rel=1e-4)


# ═══════════════════════════════════════════════════════════════════════════
# _tag_overlap_score
# ═══════════════════════════════════════════════════════════════════════════

class TestTagOverlapScore:
    def test_bidirectional_match(self):
        provide_a = {"Python": 0.9, "数据分析": 0.8}
        need_b = {"Python": 0.9, "数据分析": 0.7}
        provide_b = {"设计": 0.8, "品牌": 0.7}
        need_a = {"设计": 0.7, "品牌": 0.6}

        score, common = MatchEngine._tag_overlap_score(provide_a, need_b, provide_b, need_a)

        # Python: 0.9*0.9=0.81, 数据分析: 0.8*0.7=0.56 → 1.37
        # 设计: 0.8*0.7=0.56, 品牌: 0.7*0.6=0.42 → 0.98
        # total: 2.35
        assert score == pytest.approx(2.35, rel=1e-3)
        assert len(common) == 4

    def test_one_way_match(self):
        provide_a = {"Python": 0.9}
        need_b = {"Python": 0.9}
        provide_b = {}
        need_a = {}
        score, common = MatchEngine._tag_overlap_score(provide_a, need_b, provide_b, need_a)
        assert score == pytest.approx(0.81, rel=1e-3)
        assert len(common) == 1

    def test_no_match(self):
        score, common = MatchEngine._tag_overlap_score({}, {}, {}, {})
        assert score == 0.0
        assert common == []

    def test_direction_labels(self):
        provide_a = {"A": 1.0}
        need_b = {"A": 1.0}
        provide_b = {"B": 1.0}
        need_a = {"B": 1.0}
        _, common = MatchEngine._tag_overlap_score(provide_a, need_b, provide_b, need_a)
        directions = {c["direction"] for c in common}
        assert directions == {"我提供→对方需要", "我需要→对方提供"}


# ═══════════════════════════════════════════════════════════════════════════
# _build_user_document
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildUserDocument:
    def test_with_intro_and_tags(self, db_session, sample_users):
        u1, u2 = sample_users
        parts = MatchEngine._build_user_document(db_session, u1.id)
        assert "Python开发, 数据分析" in parts
        assert "提供Python" in parts
        assert "提供数据分析" in parts
        assert "需要设计" in parts
        assert "需要品牌" in parts

    def test_with_brochure(self, db_session):
        u = User(id=10, phone="13900139010", name="带画册用户", intro="简介文本")
        db_session.add(u)
        db_session.commit()
        b = Brochure(user_id=10, title="我的作品集", status="published")
        db_session.add(b)
        db_session.commit()
        p = Page(brochure_id=b.id, ai_summary="这是一个优秀的设计作品集")
        db_session.add(p)
        db_session.commit()
        parts = MatchEngine._build_user_document(db_session, 10)
        assert "我的作品集" in parts
        assert "这是一个优秀的设计作品集" in parts

    def test_no_data(self, db_session):
        u = User(id=99, phone="13900999099", name="空用户")
        db_session.add(u)
        db_session.commit()
        parts = MatchEngine._build_user_document(db_session, 99)
        assert parts == []

    def test_nonexistent_user(self, db_session):
        parts = MatchEngine._build_user_document(db_session, 9999)
        assert parts == []


# ═══════════════════════════════════════════════════════════════════════════
# _compute_vector_semantic
# ═══════════════════════════════════════════════════════════════════════════

class TestComputeVectorSemantic:
    def test_semantic_similarity(self, db_session, sample_users):
        u1, u2 = sample_users
        # Use mock to avoid actual embedding computation
        with patch("app.services.matching_engine.VectorSearchEngine.compute_semantic_similarity",
                   return_value=0.75):
            sim = MatchEngine._compute_vector_semantic(db_session, u1.id, u2.id)
            assert sim == 0.75

    def test_semantic_empty_document(self, db_session):
        u = User(id=99, phone="13900999099", name="空用户")
        db_session.add(u)
        db_session.commit()
        sim = MatchEngine._compute_vector_semantic(db_session, 99, 99)
        assert sim == 0.0

    def test_semantic_exception_fallback(self, db_session, sample_users):
        u1, u2 = sample_users
        with patch("app.services.matching_engine.VectorSearchEngine.compute_semantic_similarity",
                   side_effect=Exception("API error")):
            sim = MatchEngine._compute_vector_semantic(db_session, u1.id, u2.id)
            assert sim == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# _compute_tag_weight_score
# ═══════════════════════════════════════════════════════════════════════════

class TestComputeTagWeightScore:
    def test_equal_tags(self):
        score = MatchEngine._compute_tag_weight_score(
            {"a": 1.0, "b": 1.0}, {"c": 1.0},
            {"d": 1.0, "e": 1.0}, {"f": 1.0},
        )
        # tag_count_score=3/3=1.0, avg_weight_a=1.0, avg_weight_b=1.0
        # avg_weight=(1+1)/4=0.5, weight_norm=0.5
        # final=1.0*0.5 + 0.5*0.5 = 0.75
        assert score == pytest.approx(0.75, rel=1e-3)

    def test_one_user_no_tags(self):
        score = MatchEngine._compute_tag_weight_score({}, {}, {"a": 1.0}, {"b": 1.0})
        assert score == 0.0

    def test_both_no_tags(self):
        score = MatchEngine._compute_tag_weight_score({}, {}, {}, {})
        assert score == 0.0

    def test_unbalanced_tags(self):
        score = MatchEngine._compute_tag_weight_score(
            {"a": 1.0}, {},
            {"b": 1.0, "c": 1.0, "d": 1.0}, {"e": 1.0, "f": 1.0},
        )
        # tag_count_score=1/5=0.2, weights roughly average
        assert 0.0 < score < 1.0


# ═══════════════════════════════════════════════════════════════════════════
# compute_similarity (核心三层评分)
# ═══════════════════════════════════════════════════════════════════════════

class TestComputeSimilarity:
    def test_full_match_with_tags(self, db_session, sample_users):
        u1, u2 = sample_users
        with patch("app.services.matching_engine.VectorSearchEngine.compute_semantic_similarity",
                   return_value=0.8):
            result = MatchEngine.compute_similarity(db_session, u1.id, u2.id)

        assert "score" in result
        assert "tag_overlap" in result
        assert "tag_overlap_raw" in result
        assert "vector_semantic" in result
        assert "tag_weight" in result
        assert "common_tags" in result
        assert 0 <= result["score"] <= 1
        assert len(result["common_tags"]) == 4

    def test_no_tags_both_users(self, db_session):
        u1 = User(id=1, phone="13800138001", name="A")
        u2 = User(id=2, phone="13800138002", name="B")
        db_session.add_all([u1, u2])
        db_session.commit()
        with patch("app.services.matching_engine.VectorSearchEngine.compute_semantic_similarity",
                   return_value=0.0):
            result = MatchEngine.compute_similarity(db_session, 1, 2)
        assert result["score"] == 0.0
        assert result["tag_overlap_raw"] == 0.0
        assert result["vector_semantic"] == 0.0
        assert result["tag_weight"] == 0.0

    def test_full_tag_overlap_same_user_tags(self, db_session):
        """Same provide/need tags = perfect overlap."""
        u1 = User(id=1, phone="13800138001", name="A")
        u2 = User(id=2, phone="13800138002", name="B")
        db_session.add_all([u1, u2])
        db_session.commit()
        for uid in [1, 2]:
            db_session.add(UserTag(user_id=uid, tag="Python", tag_type="provide", weight=1.0))
            db_session.add(UserTag(user_id=uid, tag="Python", tag_type="need", weight=1.0))
        db_session.commit()
        with patch("app.services.matching_engine.VectorSearchEngine.compute_semantic_similarity",
                   return_value=0.8):
            result = MatchEngine.compute_similarity(db_session, 1, 2)
        assert result["tag_overlap"] > 0
        assert result["score"] > 0


# ═══════════════════════════════════════════════════════════════════════════
# hybrid_search
# ═══════════════════════════════════════════════════════════════════════════

class TestHybridSearch:
    def test_empty_query(self, db_session):
        results = MatchEngine.hybrid_search(db_session, "", 1)
        assert results == []

    def test_keyword_match(self, db_session):
        u1 = User(id=1, phone="13800138001", name="Alice", company="公司A",
                  title="工程师", intro="Python开发")
        u2 = User(id=2, phone="13800138002", name="Bob", company="公司B",
                  title="设计师", intro="UI设计")
        db_session.add_all([u1, u2])
        db_session.commit()
        with patch("app.services.matching_engine.VectorSearchEngine") as MockVSE:
            mock_instance = MockVSE.return_value
            mock_instance.build_index.return_value = None
            mock_instance.search.return_value = []
            results = MatchEngine.hybrid_search(db_session, "Python", 1)
        assert len(results) == 1
        assert results[0]["user_id"] == 1

    def test_self_excluded(self, db_session):
        u1 = User(id=1, phone="13800138001", name="Alice", company="公司A")
        u2 = User(id=2, phone="13800138002", name="Bob", company="公司B")
        db_session.add_all([u1, u2])
        db_session.commit()
        with patch("app.services.matching_engine.VectorSearchEngine") as MockVSE:
            mock_instance = MockVSE.return_value
            mock_instance.build_index.return_value = None
            mock_instance.search.return_value = []
            results = MatchEngine.hybrid_search(db_session, "Alice", 1)
        # "Alice" should not match user 1 (self) and should not match user 2
        assert len(results) == 0

    def test_vector_only_results(self, db_session):
        u1 = User(id=1, phone="13800138001", name="Alice")
        u2 = User(id=2, phone="13800138002", name="Bob", intro="Some intro")
        db_session.add_all([u1, u2])
        db_session.commit()
        with patch("app.services.matching_engine.VectorSearchEngine") as MockVSE:
            mock_instance = MockVSE.return_value
            mock_instance.build_index.return_value = None
            mock_instance.search.return_value = [
                {"user_id": 2, "user_name": "Bob", "user_company": "",
                 "user_title": "", "user_avatar": "", "score": 0.6}
            ]
            results = MatchEngine.hybrid_search(db_session, "unrelated", 1, vector_weight=1.0)
        assert len(results) == 1
        assert results[0]["source"] == "vector_only"

    def test_top_k_limit(self, db_session):
        for i in range(1, 6):
            db_session.add(User(id=i, phone=f"1380013800{i}", name=f"User{i}"))
        db_session.commit()
        # Mock vector search to return many results
        with patch("app.services.matching_engine.VectorSearchEngine") as MockVSE:
            mock_instance = MockVSE.return_value
            mock_instance.build_index.return_value = None
            mock_instance.search.return_value = []
            results = MatchEngine.hybrid_search(db_session, "Nonexistent", 1, top_k=3)
        assert len(results) <= 3


# ═══════════════════════════════════════════════════════════════════════════
# get_daily_recommendations
# ═══════════════════════════════════════════════════════════════════════════

class TestGetDailyRecommendations:
    def test_recommendations_ordered(self, db_session):
        u1 = User(id=1, phone="13800138001", name="当前用户")
        u2 = User(id=2, phone="13800138002", name="用户B")
        u3 = User(id=3, phone="13800138003", name="用户C")
        db_session.add_all([u1, u2, u3])
        db_session.commit()
        # Add tags to ensure non-zero scores
        for uid in [1, 2, 3]:
            db_session.add(UserTag(user_id=uid, tag="tag1", tag_type="provide", weight=1.0))
        db_session.commit()

        with patch.object(MatchEngine, 'compute_similarity') as mock_sim:
            def side_effect(db, aid, bid):
                sim_map = {2: 0.8, 3: 0.5}
                s = sim_map.get(bid, 0.0)
                return {"score": s, "tag_overlap": s, "tag_overlap_raw": s,
                        "vector_semantic": s, "tag_weight": s, "common_tags": []}
            mock_sim.side_effect = side_effect

            results = MatchEngine.get_daily_recommendations(db_session, 1, limit=10, min_score=0.1)

        assert len(results) == 2
        assert results[0]["score"] >= results[1]["score"]

    def test_nonexistent_user_raises(self, db_session):
        with pytest.raises(ValueError, match="用户不存在"):
            MatchEngine.get_daily_recommendations(db_session, 9999)

    def test_min_score_filter(self, db_session):
        u1 = User(id=1, phone="13800138001", name="A")
        u2 = User(id=2, phone="13800138002", name="B")
        db_session.add_all([u1, u2])
        db_session.commit()
        with patch.object(MatchEngine, 'compute_similarity', return_value={
            "score": 0.05, "tag_overlap": 0, "tag_overlap_raw": 0,
            "vector_semantic": 0, "tag_weight": 0, "common_tags": []
        }):
            results = MatchEngine.get_daily_recommendations(db_session, 1, min_score=0.1)
        assert len(results) == 0

    def test_saves_match_records(self, db_session):
        u1 = User(id=1, phone="13800138001", name="A")
        u2 = User(id=2, phone="13800138002", name="B")
        db_session.add_all([u1, u2])
        db_session.commit()
        with patch.object(MatchEngine, 'compute_similarity', return_value={
            "score": 0.8, "tag_overlap": 0.8, "tag_overlap_raw": 0.8,
            "vector_semantic": 0.8, "tag_weight": 0.8,
            "common_tags": [{"tag": "Python", "direction": "提供", "weight": 0.5}]
        }):
            MatchEngine.get_daily_recommendations(db_session, 1, limit=10, min_score=0.1)

        records = db_session.query(MatchRecord).all()
        assert len(records) == 1
        assert records[0].user_a_id == 1
        assert records[0].user_b_id == 2
        assert records[0].match_score == 0.8
        assert records[0].status == "matched"
        assert records[0].source == "auto"
        assert "Python" in records[0].common_tags


# ═══════════════════════════════════════════════════════════════════════════
# record_interest
# ═══════════════════════════════════════════════════════════════════════════

class TestRecordInterest:
    def test_record_new_interest(self, db_session):
        u1 = User(id=1, phone="13800138001", name="A")
        u2 = User(id=2, phone="13800138002", name="B")
        db_session.add_all([u1, u2])
        db_session.commit()
        result = MatchEngine.record_interest(db_session, 1, 2)
        assert result.user_a_id == 1
        assert result.user_b_id == 2
        assert result.status == "matched"
        assert result.source == "manual"

    def test_self_interest_raises(self, db_session):
        u1 = User(id=1, phone="13800138001", name="A")
        db_session.add(u1)
        db_session.commit()
        with pytest.raises(ValueError, match="不能对自己感兴趣"):
            MatchEngine.record_interest(db_session, 1, 1)

    def test_update_existing_record(self, db_session):
        u1 = User(id=1, phone="13800138001", name="A")
        u2 = User(id=2, phone="13800138002", name="B")
        db_session.add_all([u1, u2])
        db_session.commit()
        existing = MatchRecord(user_a_id=1, user_b_id=2, match_score=0.5,
                               status="pending", common_tags="[]", source="auto")
        db_session.add(existing)
        db_session.commit()

        result = MatchEngine.record_interest(db_session, 1, 2)
        assert result.id == existing.id
        assert result.status == "matched"


# ═══════════════════════════════════════════════════════════════════════════
# confirm_match
# ═══════════════════════════════════════════════════════════════════════════

class TestConfirmMatch:
    def test_confirm_match_success(self, db_session):
        u1 = User(id=1, phone="13800138001", name="A")
        u2 = User(id=2, phone="13800138002", name="B")
        db_session.add_all([u1, u2])
        db_session.commit()
        record = MatchRecord(user_a_id=1, user_b_id=2, match_score=0.8,
                             status="matched", common_tags="[]", source="auto")
        db_session.add(record)
        db_session.commit()

        result = MatchEngine.confirm_match(db_session, record.id, user_id=1)
        assert result.status == "confirmed"

    def test_confirm_nonexistent_record(self, db_session):
        with pytest.raises(ValueError, match="匹配记录不存在"):
            MatchEngine.confirm_match(db_session, 999, user_id=1)

    def test_confirm_unauthorized(self, db_session):
        u1 = User(id=1, phone="13800138001", name="A")
        u2 = User(id=2, phone="13800138002", name="B")
        u3 = User(id=3, phone="13800138003", name="C")
        db_session.add_all([u1, u2, u3])
        db_session.commit()
        record = MatchRecord(user_a_id=1, user_b_id=2, match_score=0.8,
                             status="matched", common_tags="[]", source="auto")
        db_session.add(record)
        db_session.commit()

        with pytest.raises(PermissionError, match="无权操作此匹配记录"):
            MatchEngine.confirm_match(db_session, record.id, user_id=3)
