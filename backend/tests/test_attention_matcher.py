"""Tests for AttentionMatcher (attention_matcher.py) — 四头注意力匹配引擎

测试覆盖:
  1. UserFeatures dataclass 默认值
  2. AttentionMatcher 初始化
  3. score() — 四头综合匹配度计算
  4. batch_score() — 批量评分
  5. explain() — 匹配详情解释
  6. 各头独立性 — 单头变化影响
  7. 可用性 — 负载影响
  8. 边界条件 — 空特征/零负载
"""

import math

import pytest

from app.ai.attention_matcher import (
    AttentionMatcher,
    UserFeatures,
    HEAD_WEIGHTS,
    softmax,
)


# ══════════════════════════════════════════════════════════════════════
# softmax
# ══════════════════════════════════════════════════════════════════════


class TestSoftmax:
    """softmax 基础函数测试"""

    def test_empty_input(self):
        assert softmax([]) == []

    def test_single_element(self):
        result = softmax([5.0])
        assert len(result) == 1
        assert abs(result[0] - 1.0) < 1e-10

    def test_two_elements(self):
        result = softmax([1.0, 0.0])
        assert len(result) == 2
        assert abs(sum(result) - 1.0) < 1e-10
        assert result[0] > result[1]

    def test_temperature_high(self):
        """高温度使分布更平滑"""
        low_temp = softmax([3.0, 1.0], temperature=0.5)
        high_temp = softmax([3.0, 1.0], temperature=2.0)
        # 高温度下较大值的概率应该更低
        assert low_temp[0] > high_temp[0]

    def test_zero_temperature_clamped(self):
        """零温度自动钳位到1.0"""
        result = softmax([1.0, 0.0], temperature=0.0)
        assert abs(sum(result) - 1.0) < 1e-10


# ══════════════════════════════════════════════════════════════════════
# UserFeatures
# ══════════════════════════════════════════════════════════════════════


class TestUserFeatures:
    """UserFeatures dataclass 默认值测试"""

    def test_defaults(self):
        f = UserFeatures()
        assert f.industries == []
        assert f.capabilities == []
        assert f.regions == []
        assert f.hotness == 0.0
        assert f.load == 0
        assert f.max_load == 10

    def test_custom_values(self):
        f = UserFeatures(
            industries=["科技", "金融"],
            capabilities=["ai", "数据分析"],
            regions=["北京"],
            hotness=0.8,
            load=3,
            max_load=8,
        )
        assert f.industries == ["科技", "金融"]
        assert f.capabilities == ["ai", "数据分析"]
        assert f.regions == ["北京"]
        assert f.hotness == 0.8
        assert f.load == 3
        assert f.max_load == 8


# ══════════════════════════════════════════════════════════════════════
# AttentionMatcher
# ══════════════════════════════════════════════════════════════════════


class TestAttentionMatcherInit:
    """初始化测试"""

    def test_default_init(self):
        matcher = AttentionMatcher()
        assert matcher.temperature == 0.8
        assert matcher._vocab == {
            "industry": {},
            "capability": {},
            "region": {},
        }

    def test_custom_temperature(self):
        matcher = AttentionMatcher(temperature=1.5)
        assert matcher.temperature == 1.5


class TestAttentionMatcherRegister:
    """词表注册测试"""

    def test_register_features(self):
        matcher = AttentionMatcher()
        matcher.register_features("industry", ["科技", "金融"])
        assert matcher._dims["industry"] == 2
        assert matcher._vocab["industry"]["科技"] == 0
        assert matcher._vocab["industry"]["金融"] == 1

    def test_register_duplicates(self):
        matcher = AttentionMatcher()
        matcher.register_features("industry", ["科技", "金融", "科技"])
        assert matcher._dims["industry"] == 2  # 去重

    def test_invalid_head_noop(self):
        matcher = AttentionMatcher()
        matcher.register_features("nonexistent", ["科技"])  # 不会报错
        assert True


class TestAttentionMatcherScore:
    """score() 核心匹配度测试"""

    @pytest.fixture
    def matcher(self):
        return AttentionMatcher()

    @pytest.mark.asyncio
    async def test_identical_features_perfect_availability(self, matcher):
        """完全相同的特征 → 较高匹配度"""
        user = UserFeatures(
            industries=["科技"],
            capabilities=["ai"],
            regions=["北京"],
            hotness=0.5,
            load=0,
            max_load=10,
        )
        score = await matcher.score(user, user)
        # 相同特征 + 零负载 → 高匹配度
        assert score > 0.7
        assert score <= 1.0

    @pytest.mark.asyncio
    async def test_completely_different_features(self, matcher):
        """完全不同特征 → 低匹配度"""
        user_a = UserFeatures(
            industries=["科技"],
            capabilities=["ai"],
            regions=["北京"],
            hotness=0.5,
        )
        user_b = UserFeatures(
            industries=["农业"],
            capabilities=["养殖"],
            regions=["新疆"],
            hotness=0.5,
        )
        score = await matcher.score(user_a, user_b)
        # 完全不同的行业/能力/地区，但热度相同 → 仅热度头贡献
        # 各头基础分 ~0.5 (sigmoid(0)), 热度头 1.0
        # weighted = 0.30*0.5 + 0.35*0.5 + 0.20*0.5 + 0.15*1.0 = 0.575
        assert score < 0.7

    @pytest.mark.asyncio
    async def test_high_load_reduces_score(self, matcher):
        """高负载拉低匹配度"""
        user = UserFeatures(industries=["科技"], load=0)
        cand_free = UserFeatures(industries=["科技"], load=0)
        cand_busy = UserFeatures(industries=["科技"], load=9, max_load=10)

        score_free = await matcher.score(user, cand_free)
        score_busy = await matcher.score(user, cand_busy)
        assert score_free > score_busy

    @pytest.mark.asyncio
    async def test_overloaded_reduces_score(self, matcher):
        """超载 → 可用性降低 → 分数显著下降"""
        user = UserFeatures(industries=["科技"])
        cand = UserFeatures(industries=["科技"], load=10, max_load=10)
        score = await matcher.score(user, cand)
        # combined_avail = (1.0 + 0.0) / 2 = 0.5
        # 分数约为正常值(0.644)的一半
        assert score < 0.4

    @pytest.mark.asyncio
    async def test_industry_head_dominance(self, matcher):
        """行业头权重0.30 — 行业匹配对分数影响显著"""
        user = UserFeatures(industries=["科技", "金融", "ai"])
        cand_same_industry = UserFeatures(
            industries=["科技", "金融", "ai"],
            capabilities=[], regions=[],
            hotness=0.5,
        )
        cand_diff_industry = UserFeatures(
            industries=["农业", "教育"],
            capabilities=[], regions=[],
            hotness=0.5,
        )
        score_same = await matcher.score(user, cand_same_industry)
        score_diff = await matcher.score(user, cand_diff_industry)
        assert score_same > score_diff

    @pytest.mark.asyncio
    async def test_capability_head_weights_highest(self, matcher):
        """能力头权重最高(0.35)"""
        user = UserFeatures(capabilities=["ai", "nlp", "ml"])
        cand_high_cap = UserFeatures(capabilities=["ai", "nlp", "ml"])
        cand_low_cap = UserFeatures(capabilities=[])
        score_high = await matcher.score(user, cand_high_cap)
        score_low = await matcher.score(user, cand_low_cap)
        # 能力头权重0.35, 差异应显著
        assert score_high > score_low
        assert abs(score_high - score_low) > 0.1


class TestAttentionMatcherBatchScore:
    """batch_score() 批量评分测试"""

    @pytest.mark.asyncio
    async def test_batch_empty(self):
        matcher = AttentionMatcher()
        user = UserFeatures()
        scores = await matcher.batch_score(user, [])
        assert scores == []

    @pytest.mark.asyncio
    async def test_batch_multiple(self):
        matcher = AttentionMatcher()
        user = UserFeatures(industries=["科技"], hotness=0.5)
        candidates = [
            UserFeatures(industries=["科技"], hotness=0.5),
            UserFeatures(industries=["农业"], hotness=0.5),
            UserFeatures(industries=["金融"], hotness=0.5),
        ]
        scores = await matcher.batch_score(user, candidates)
        assert len(scores) == 3
        # 第一个候选与用户相同 → 应该最高
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]

    @pytest.mark.asyncio
    async def test_batch_returns_in_order(self):
        """batch_score 返回顺序与输入列表一致"""
        matcher = AttentionMatcher()
        user = UserFeatures(industries=["科技"])
        candidates = [
            UserFeatures(industries=["金融"]),
            UserFeatures(industries=["科技"]),
            UserFeatures(industries=["农业"]),
        ]
        scores = await matcher.batch_score(user, candidates)
        assert len(scores) == 3
        # 第二个候选(科技)应该最高
        assert scores[1] > scores[0]
        assert scores[1] > scores[2]


class TestAttentionMatcherExplain:
    """explain() 匹配解释测试"""

    @pytest.mark.asyncio
    async def test_explain_returns_all_keys(self):
        matcher = AttentionMatcher()
        user_a = UserFeatures(
            industries=["科技"],
            capabilities=["ai"],
            regions=["北京"],
            hotness=0.7,
        )
        user_b = UserFeatures(
            industries=["科技"],
            capabilities=["nlp"],
            regions=["上海"],
            hotness=0.3,
        )
        result = await matcher.explain(user_a, user_b)

        # 顶层键
        assert "score" in result
        assert "details" in result
        assert "availability" in result
        assert "features" in result

        # 四头详情
        for head in ["industry", "capability", "region", "hotness"]:
            assert head in result["details"]
            assert "attention" in result["details"][head]
            assert "weight" in result["details"][head]
            assert "contribution" in result["details"][head]

        # 权重匹配 HEAD_WEIGHTS
        for head, info in result["details"].items():
            assert info["weight"] == pytest.approx(HEAD_WEIGHTS[head])

    @pytest.mark.asyncio
    async def test_explain_features_reflects_input(self):
        matcher = AttentionMatcher()
        user_a = UserFeatures(
            industries=["科技", "金融"],
            capabilities=["ai"],
            regions=["北京"],
            hotness=0.8,
        )
        user_b = UserFeatures(
            industries=["教育"],
            capabilities=["nlp"],
            regions=["上海"],
            hotness=0.2,
        )
        result = await matcher.explain(user_a, user_b)

        assert result["features"]["user_a"]["industries"] == ["科技", "金融"]
        assert result["features"]["user_b"]["industries"] == ["教育"]
        assert result["features"]["user_a"]["hotness"] == 0.8

    @pytest.mark.asyncio
    async def test_explain_score_equals_score_method(self):
        """explain() 的 score 应与 score() 一致"""
        matcher = AttentionMatcher()
        user_a = UserFeatures(industries=["科技"], capabilities=["ai"], hotness=0.5)
        user_b = UserFeatures(industries=["金融"], capabilities=["nlp"], hotness=0.6)

        score_direct = await matcher.score(user_a, user_b)
        explain_result = await matcher.explain(user_a, user_b)
        assert score_direct == explain_result["score"]


class TestAttentionMatcherEdgeCases:
    """边界条件测试"""

    @pytest.mark.asyncio
    async def test_empty_features(self):
        """空特征 → 返回有效值而非崩溃"""
        matcher = AttentionMatcher()
        user = UserFeatures()
        cand = UserFeatures()
        score = await matcher.score(user, cand)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_empty_batch_no_candidates(self):
        """空候选列表"""
        matcher = AttentionMatcher()
        user = UserFeatures()
        scores = await matcher.batch_score(user, [])
        assert scores == []

    @pytest.mark.asyncio
    async def test_hotness_range_clamping(self):
        """热度值在边界的行为"""
        matcher = AttentionMatcher()
        user = UserFeatures(hotness=0.0)
        cand = UserFeatures(hotness=1.0)
        score = await matcher.score(user, cand)
        assert 0.0 <= score <= 1.0

        # 相同热度 → 热度头满分
        same_hot = matcher._score_hotness_head(0.5, 0.5)
        assert same_hot == 1.0

        # 完全相反 → 热度头0分
        opposite_hot = matcher._score_hotness_head(0.0, 1.0)
        assert opposite_hot == 0.0

    @pytest.mark.asyncio
    async def test_zero_max_load(self):
        """max_load=0时可用性为1.0 (无负载概念)"""
        matcher = AttentionMatcher()
        avail = matcher._availability(5, 0)
        assert avail == 1.0


class TestAttentionMatcherHeadWeights:
    """验证 HEAD_WEIGHTS 总和为1.0"""

    def test_head_weights_sum_to_one(self):
        total = sum(HEAD_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-10, f"权重总和为 {total}, 应为 1.0"

    def test_all_heads_present(self):
        expected = {"industry", "capability", "region", "hotness"}
        assert set(HEAD_WEIGHTS.keys()) == expected
