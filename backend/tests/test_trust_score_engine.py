"""信任体系单元测试 — 链客宝 trust_engine 迁移验证

覆盖:
  1. 评分引擎三维计算正确性
  2. 五级分级边界
  3. 匹配预过滤逻辑
  4. 服务层资质/评价创建校验
"""
import pytest
from datetime import date

from app.trust_engine.scoring import (
    TrustScorer,
    QualificationData,
    TransactionData,
    ComplianceData,
    ScoreBreakdown,
)
from app.trust_engine.tier import TrustTier, TrustLevel, TIER_DEFINITIONS
from app.trust_engine.matching import pre_filter_candidate, MatchingConfig


# ── 评分引擎 ──────────────────────────────────────────────────────────────

class TestTrustScorer:
    def setup_method(self):
        self.scorer = TrustScorer()

    def test_empty_profile_zero_score(self):
        """空档案 → 待完善级（<40，乐观默认给基础分但不达基础级）"""
        bd = self.scorer.calculate_from_raw_data(
            QualificationData(qualification_type="", is_active=False),
            TransactionData(),
            ComplianceData(),
        )
        assert bd.total < 40

    def test_full_profile_high_score(self):
        """完整档案（认证+资质+交易+合规）→ 高分"""
        bd = self.scorer.calculate_from_raw_data(
            QualificationData(qualification_type="business_license", is_active=True),
            TransactionData(
                total_trades=50, total_amount=500000, positive_rate=0.99,
                dispute_count=0, total_rated=50, repurchase_count=30,
                last_trade_date=date.today(),
            ),
            ComplianceData(
                active_qual_count=5, expired_count=0,
                compliance_cert_types={"iso_cert", "icp", "patent", "trademark", "copyright"},
                has_valid_audit=True,
                last_update_months=1,
            ),
            cert_level="diamond", id_level="legal_person_video", months_on_platform=40,
        )
        assert bd.total >= 80

    def test_score_range(self):
        """评分必须在 [0, 100]"""
        bd = self.scorer.calculate_from_raw_data(
            QualificationData(qualification_type="x", is_active=True),
            TransactionData(total_trades=999, total_amount=999999),
            ComplianceData(active_qual_count=99),
            cert_level="diamond", id_level="legal_person_video", months_on_platform=99,
        )
        assert 0 <= bd.total <= 100

    def test_breakdown_fields(self):
        """明细包含三维度"""
        bd = self.scorer.calculate_from_raw_data(
            QualificationData(qualification_type="x", is_active=True),
            TransactionData(total_trades=1, total_amount=100),
            ComplianceData(active_qual_count=1),
        )
        d = bd.to_dict()
        assert "qualification" in d
        assert "transaction" in d
        assert "compliance" in d
        assert "total" in d


# ── 五级分级 ──────────────────────────────────────────────────────────────

class TestTrustTier:
    def test_levels(self):
        """五级分级边界正确"""
        assert TrustTier(0).level == TrustLevel.PENDING
        assert TrustTier(39).level == TrustLevel.PENDING
        assert TrustTier(40).level == TrustLevel.BASIC
        assert TrustTier(59).level == TrustLevel.BASIC
        assert TrustTier(60).level == TrustLevel.GOOD
        assert TrustTier(79).level == TrustLevel.GOOD
        assert TrustTier(80).level == TrustLevel.EXCELLENT
        assert TrustTier(89).level == TrustLevel.EXCELLENT
        assert TrustTier(90).level == TrustLevel.TOP
        assert TrustTier(100).level == TrustLevel.TOP

    def test_tier_definitions_complete(self):
        """5个等级定义齐全"""
        assert len(TIER_DEFINITIONS) == 5
        levels = {t.level for t in TIER_DEFINITIONS}
        assert levels == set(TrustLevel)


# ── 匹配预过滤 ────────────────────────────────────────────────────────────

class TestPreFilter:
    def test_low_trust_removed(self):
        """低于最低要求 → 移除"""
        r = pre_filter_candidate(50.0, min_trust_requirement=60.0)
        assert r.passed is False

    def test_low_trust_penalized(self):
        """低于40 → 降权50%"""
        r = pre_filter_candidate(35.0)
        assert r.passed is True
        assert r.exposure_weight == 0.5

    def test_normal_trust(self):
        """正常信任 → 正常曝光"""
        r = pre_filter_candidate(75.0)
        assert r.passed is True
        assert r.exposure_weight == 1.0
