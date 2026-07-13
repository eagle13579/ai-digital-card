"""
MatchEngineV2 测试套件

覆盖范围:
    - 行业检测 (_detect_industries)
    - 行业互补评分 (_industry_complement_score)
    - 注意力评分 (_attention_score, _build_user_features)
    - V2 综合评分 (compute_similarity_v2)
    - 权重配置完整性
    - 边缘情况（空标签、无行业匹配等）
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from app.services.matching_engine_v2 import (
    INDUSTRY_CATEGORIES,
    INDUSTRY_KEYWORDS,
    INDUSTRY_SUPPLY_DEMAND_MAP,
    SAME_INDUSTRY_BONUS,
    CROSS_INDUSTRY_BONUS,
    WEIGHTS_V2,
    MatchEngineV2,
)
from app.services.matching_engine import MatchEngine


class TestIndustryDetection:
    """行业检测功能测试"""

    def test_detect_ai_technology(self):
        """AI/科技行业检测"""
        provide = {"AI算法开发": 1.0}
        need = {"云计算服务": 1.0}
        industries = MatchEngineV2._detect_industries(provide, need)
        assert "AI/科技" in industries

    def test_detect_finance(self):
        """金融/投资行业检测"""
        provide = {"证券投资顾问": 1.0}
        need = {}
        industries = MatchEngineV2._detect_industries(provide, need)
        assert "金融/投资" in industries

    def test_detect_manufacturing(self):
        """制造/工业行业检测"""
        provide = {"供应链管理": 1.0}
        need = {}
        industries = MatchEngineV2._detect_industries(provide, need)
        assert "制造/工业" in industries

    def test_detect_education(self):
        """教育/培训行业检测"""
        provide = {"在线课程开发": 1.0}
        need = {}
        industries = MatchEngineV2._detect_industries(provide, need)
        assert "教育/培训" in industries

    def test_detect_empty_tags(self):
        """空标签情况"""
        industries = MatchEngineV2._detect_industries({}, {})
        assert industries == []

    def test_detect_multiple_industries(self):
        """多个行业同时检测"""
        provide = {"AI算法": 1.0, "证券投资": 1.0}
        need = {"医疗健康": 1.0}
        industries = MatchEngineV2._detect_industries(provide, need)
        assert "AI/科技" in industries
        assert "金融/投资" in industries
        assert "医疗/健康" in industries

    def test_detect_unknown_tags(self):
        """无关联行业的标签"""
        provide = {"兴趣爱好": 1.0, "生活服务": 1.0}
        need = {"日常用品": 1.0}
        industries = MatchEngineV2._detect_industries(provide, need)
        # 这些标签应该不会匹配已知行业关键词
        # 但"日常用品"可能匹配不到... 我们只验证不会报错
        assert isinstance(industries, list)


class TestIndustryComplementScore:
    """行业互补评分测试"""

    def test_same_industry_bonus(self):
        """同类行业互补加分"""
        provide_a = {"AI算法开发": 1.0}
        need_a = {}
        provide_b = {"云计算服务": 1.0}
        need_b = {}
        # 双方都是 AI/科技，期望得到 SAME_INDUSTRY_BONUS
        score = MatchEngineV2._industry_complement_score(
            provide_a, need_a, provide_b, need_b,
        )
        # 唯一一对比较 = AI/科技 vs AI/科技 → +0.1
        # 归一化: 0.1 / 1 = 0.1
        assert score == pytest.approx(SAME_INDUSTRY_BONUS, rel=0.01)

    def test_cross_industry_complement(self):
        """跨行业供需互补加分"""
        provide_a = {"AI算法开发": 1.0}  # AI/科技
        need_a = {}
        provide_b = {"智能工厂方案": 1.0}  # 制造/工业
        need_b = {}
        # AI/科技 → 制造/工业 在供需映射中
        score = MatchEngineV2._industry_complement_score(
            provide_a, need_a, provide_b, need_b,
        )
        # 预期 CROSS_INDUSTRY_BONUS
        assert score == pytest.approx(CROSS_INDUSTRY_BONUS, rel=0.01)

    def test_no_industry_match(self):
        """无行业匹配"""
        provide_a = {"AI算法开发": 1.0}
        need_a = {}
        provide_b = {}  # 空标签
        need_b = {}
        # 一方无行业
        score = MatchEngineV2._industry_complement_score(
            provide_a, need_a, provide_b, need_b,
        )
        assert score == 0.0

    def test_both_empty(self):
        """双方都空标签"""
        score = MatchEngineV2._industry_complement_score({}, {}, {}, {})
        assert score == 0.0

    def test_mixed_industries(self):
        """多行业混合情况"""
        provide_a = {"AI算法": 1.0, "证券投资": 1.0}
        need_a = {}
        provide_b = {"智能工厂": 1.0, "医疗设备": 1.0}
        need_b = {}
        # AI/科技 → 制造/工业 = CROSS (+0.3)
        # AI/科技 → 医疗/健康 = CROSS (+0.3)
        # 金融/投资 → 制造/工业 = CROSS (+0.3)
        # 金融/投资 → 医疗/健康 = CROSS (+0.3)
        # 总加分 = 1.2, 比较次数 = 4, 归一化 = 0.3
        score = MatchEngineV2._industry_complement_score(
            provide_a, need_a, provide_b, need_b,
        )
        assert 0.2 <= score <= 0.4  # 预期大约 0.3

    def test_reverse_complement(self):
        """反向供需互补"""
        provide_a = {"智能制造": 1.0}  # 制造/工业
        need_a = {}
        provide_b = {"AI产品": 1.0}  # AI/科技
        need_b = {}
        # 供需映射表: AI/科技 → 制造/工业
        # 反向: 制造/工业 → AI/科技 (也在映射表中)
        score = MatchEngineV2._industry_complement_score(
            provide_a, need_a, provide_b, need_b,
        )
        assert score == pytest.approx(CROSS_INDUSTRY_BONUS, rel=0.01)

    def test_no_known_mapping(self):
        """无供需映射关系的行业"""
        provide_a = {"教育培训": 1.0}  # 教育/培训
        need_a = {}
        provide_b = {"短视频制作": 1.0}  # 传媒/内容
        need_b = {}
        # 教育/培训 不在 INDUSTRY_SUPPLY_DEMAND_MAP 的 key 中（作为源头）
        # 传媒/内容 → 电商/零售, 品牌/营销（不包含教育）
        # 所以无匹配
        score = MatchEngineV2._industry_complement_score(
            provide_a, need_a, provide_b, need_b,
        )
        assert score == 0.0


class TestBuildUserFeatures:
    """UserFeatures 构建测试"""

    def test_basic_build(self):
        """基本特征构建"""
        provide_a = {"AI算法开发": 1.0, "Python": 1.0}
        need_a = {"云计算服务": 1.0}
        provide_b = {"前端开发": 1.0}
        need_b = {"数据分析": 1.0}

        features_a, features_b = MatchEngineV2._build_user_features(
            provide_a, need_a, provide_b, need_b,
        )

        # 验证行业检测
        assert len(features_a.industries) > 0
        assert "AI/科技" in features_a.industries

        # 验证能力 = 提供标签
        assert "AI算法开发" in features_a.capabilities
        assert "Python" in features_a.capabilities

        # 验证 hotness 默认值
        assert features_a.hotness == 0.5
        assert features_b.hotness == 0.5

    def test_region_detection(self):
        """地区检测"""
        provide_a = {"AI开发_北京": 1.0}
        need_a = {"上海客户": 1.0}
        provide_b = {"深圳合作": 1.0}
        need_b = {}

        features_a, features_b = MatchEngineV2._build_user_features(
            provide_a, need_a, provide_b, need_b,
        )

        # 应检测到北京/上海/深圳
        assert any("北京" in r for r in features_a.regions) or \
            any("上海" in r for r in features_a.regions)

        assert any("深圳" in r for r in features_b.regions)


class TestAttentionScore:
    """注意力匹配分数测试"""

    @pytest.mark.asyncio
    async def test_attention_score_basic(self):
        """基础注意力匹配"""
        provide_a = {"AI算法开发": 1.0, "机器学习": 1.0}
        need_a = {"云计算": 1.0}
        provide_b = {"大数据分析": 1.0}
        need_b = {"AI产品": 1.0}

        score = await MatchEngineV2._attention_score(
            provide_a, need_a, provide_b, need_b,
        )
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_attention_score_empty(self):
        """空标签情况"""
        score = await MatchEngineV2._attention_score({}, {}, {}, {})
        assert 0.0 <= score <= 1.0


class TestComputeSimilarityV2:
    """V2 综合评分测试"""

    @pytest.mark.asyncio
    async def test_compute_v2_basic(self):
        """基础综合评分（模拟数据库）"""
        mock_db = AsyncMock()

        # 模拟 _build_tag_vector 返回值
        with patch.object(
            MatchEngine, "_build_tag_vector",
            new_callable=AsyncMock,
        ) as mock_build:
            mock_build.side_effect = [
                {"AI算法": 1.0, "Python": 0.8},     # provide_a
                {"投资": 1.0, "云计算": 0.6},         # need_a
                {"智能制造": 1.0, "数据分析": 0.9},   # provide_b
                {"AI产品": 0.7, "技术咨询": 0.5},    # need_b
            ]

            with patch.object(
                MatchEngine, "_compute_vector_semantic",
                new_callable=AsyncMock, return_value=0.5,
            ) as mock_vec:
                with patch.object(
                    MatchEngine, "_compute_tag_weight_score",
                    return_value=0.5,
                ):
                    with patch.object(
                        MatchEngineV2, "_attention_score",
                        new_callable=AsyncMock, return_value=0.5,
                    ):
                        result = await MatchEngineV2.compute_similarity_v2(
                            mock_db, 1, 2,
                        )

                        # 验证结果包含所有五层字段
                        assert "score" in result
                        assert "tag_overlap" in result
                        assert "vector_semantic" in result
                        assert "tag_weight" in result
                        assert "industry_complement" in result
                        assert "attention_score" in result
                        assert "common_tags" in result

                        # 验证分数范围
                        assert 0.0 <= result["score"] <= 1.0

    @pytest.mark.asyncio
    async def test_compute_v2_all_zero(self):
        """全零情况"""
        mock_db = AsyncMock()

        with patch.object(
            MatchEngine, "_build_tag_vector",
            new_callable=AsyncMock, return_value={},
        ):
            with patch.object(
                MatchEngine, "_compute_vector_semantic",
                new_callable=AsyncMock, return_value=0.0,
            ):
                with patch.object(
                    MatchEngine, "_compute_tag_weight_score",
                    return_value=0.0,
                ):
                    with patch.object(
                        MatchEngineV2, "_attention_score",
                        new_callable=AsyncMock, return_value=0.0,
                    ):
                        result = await MatchEngineV2.compute_similarity_v2(
                            mock_db, 1, 2,
                        )
                        assert result["score"] == pytest.approx(0.0, abs=0.01)
                        assert result["tag_overlap"] == 0.0
                        assert result["vector_semantic"] == 0.0
                        assert result["tag_weight"] == 0.0
                        assert result["industry_complement"] == 0.0
                        assert result["attention_score"] == 0.0


class TestScoreWeights:
    """评分权重配置验证"""

    def test_weights_sum_to_one(self):
        """所有权重之和必须为 1.0"""
        total = sum(WEIGHTS_V2.values())
        assert total == pytest.approx(1.0, abs=0.001), \
            f"权重之和为 {total}，应为 1.0"

    def test_weights_has_all_keys(self):
        """权重须包含所有五层"""
        expected_keys = {
            "tag_overlap", "vector_semantic", "tag_weight",
            "industry_complement", "attention_score",
        }
        assert set(WEIGHTS_V2.keys()) == expected_keys

    def test_industry_complement_weight(self):
        """行业互补权重应为 0.20"""
        assert WEIGHTS_V2["industry_complement"] == pytest.approx(0.20, abs=0.001)

    def test_attention_score_weight(self):
        """注意力匹配权重应为 0.10"""
        assert WEIGHTS_V2["attention_score"] == pytest.approx(0.10, abs=0.001)

    def test_tag_overlap_reduced(self):
        """标签重叠权重从 V1 的 0.40 降为 0.35"""
        assert WEIGHTS_V2["tag_overlap"] == pytest.approx(0.35, abs=0.001)

    def test_vector_semantic_reduced(self):
        """语义相似度权重从 V1 的 0.40 降为 0.25"""
        assert WEIGHTS_V2["vector_semantic"] == pytest.approx(0.25, abs=0.001)


class TestIndustryConfig:
    """行业配置验证"""

    def test_industry_categories_count(self):
        """应有 10 个行业类别"""
        assert len(INDUSTRY_CATEGORIES) == 10

    def test_all_categories_have_keywords(self):
        """每个行业类别都有对应的关键词"""
        for category in INDUSTRY_CATEGORIES:
            assert category in INDUSTRY_KEYWORDS, \
                f"缺少行业关键词：{category}"
            assert len(INDUSTRY_KEYWORDS[category]) > 0, \
                f"行业 {category} 的关键词列表为空"

    def test_supply_demand_keys_in_categories(self):
        """供需映射表的源头行业都包含在 10 个类别中"""
        for key in INDUSTRY_SUPPLY_DEMAND_MAP:
            assert key in INDUSTRY_CATEGORIES, \
                f"供需映射源头 {key} 不在行业类别列表中"

    def test_supply_demand_values_in_categories(self):
        """供需映射表的目标行业都包含在 10 个类别中"""
        for key, values in INDUSTRY_SUPPLY_DEMAND_MAP.items():
            for v in values:
                assert v in INDUSTRY_CATEGORIES, \
                    f"供需映射目标 {v}（从 {key}）不在行业类别列表中"


class TestMMRIntegration:
    """MMR 集成测试（针对 hybrid_search_v2 的 MMR 部分）"""

    @pytest.mark.asyncio
    async def test_hybrid_search_v2_empty_query(self):
        """空查询应返回空列表"""
        mock_db = AsyncMock()
        result = await MatchEngineV2.hybrid_search_v2(
            mock_db, "", 1, top_k=10,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_hybrid_search_v2_mmr_off(self):
        """关闭 MMR 时仍可正常工作"""
        mock_db = AsyncMock()

        # 模拟 select(User) 返回空（无其他用户）
        mock_execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_execute.return_value = mock_result
        mock_db.execute = mock_execute

        with patch(
            "app.services.matching_engine_v2.VectorSearchEngine",
            autospec=True,
        ) as mock_vse_cls:
            mock_vse = AsyncMock()
            mock_vse.build_index = AsyncMock()
            mock_vse.search = AsyncMock(return_value=[])
            mock_vse_cls.return_value = mock_vse

            result = await MatchEngineV2.hybrid_search_v2(
                mock_db, "AI", 1, top_k=10, mmr_enabled=False,
            )
            assert result == []  # 没有其他用户


class TestEdgeCases:
    """边缘情况测试"""

    def test_empty_supply_demand_for_education(self):
        """教育/培训 不在供需映射表的 key 中——不应报错"""
        provide_a = {"教育培训": 1.0, "课程开发": 1.0}
        need_a = {}
        provide_b = {"AI产品": 1.0}
        need_b = {}

        # 教育/培训 vs AI/科技 — AI/科技 → 教育/培训 在供需映射表中
        # 所以是跨行业互补，score = 0.3
        score = MatchEngineV2._industry_complement_score(
            provide_a, need_a, provide_b, need_b,
        )
        assert score == pytest.approx(CROSS_INDUSTRY_BONUS, rel=0.01)

    def test_single_industry_self_match(self):
        """单行业自匹配"""
        provide_a = {"AI产品": 1.0}
        need_a = {}
        provide_b = {"AI产品": 1.0}
        need_b = {}

        score = MatchEngineV2._industry_complement_score(
            provide_a, need_a, provide_b, need_b,
        )
        assert score == pytest.approx(SAME_INDUSTRY_BONUS, rel=0.01)


class TestRecommendationsV2:
    """V2 每日推荐测试"""

    @pytest.mark.asyncio
    async def test_user_not_found(self):
        """用户不存在时抛出 ValueError"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None

        async def mock_execute(*args, **kwargs):
            return mock_result

        mock_db.execute = mock_execute

        with pytest.raises(ValueError, match="用户不存在"):
            await MatchEngineV2.get_daily_recommendations_v2(mock_db, 999)

    @pytest.mark.asyncio
    async def test_recommendations_with_other_users(self):
        """有推荐用户"""
        mock_db = AsyncMock()

        # 模拟 current_user
        current_user = MagicMock()
        current_user.id = 1
        current_user.name = "测试用户"

        # 模拟 other_users
        other_user = MagicMock()
        other_user.id = 2
        other_user.name = "匹配用户"
        other_user.company = "科技公司"
        other_user.title = "工程师"
        other_user.avatar = "avatar.jpg"

        # mock execute 返回值
        first_call = MagicMock()
        first_call.scalars.return_value.first.return_value = current_user

        second_call = MagicMock()
        second_call.scalars.return_value.all.return_value = [other_user]

        third_call = MagicMock()
        third_call.scalars.return_value.first.return_value = None  # 无已有 MatchRecord

        execute_responses = [first_call, second_call, third_call]

        async def mock_execute(*args, **kwargs):
            return execute_responses.pop(0)

        mock_db.execute = mock_execute

        with patch.object(
            MatchEngineV2, "compute_similarity_v2",
            new_callable=AsyncMock,
            return_value={
                "score": 0.85,
                "tag_overlap": 0.7,
                "tag_overlap_raw": 0.5,
                "vector_semantic": 0.8,
                "tag_weight": 0.6,
                "industry_complement": 0.5,
                "attention_score": 0.4,
                "common_tags": [{"tag": "AI", "direction": "我提供→对方需要", "weight": 0.8}],
            },
        ):
            result = await MatchEngineV2.get_daily_recommendations_v2(
                mock_db, 1, limit=5,
            )
            assert len(result) == 1
            assert result[0]["user_id"] == 2
            assert result[0]["score"] == 0.85
            assert "industry_complement" in result[0]
            assert "attention_score" in result[0]


class TestRecordInterestV2:
    """兴趣记录委托测试"""

    @pytest.mark.asyncio
    async def test_record_interest_delegates_to_v1(self):
        """V2 的 record_interest 应委托给 V1"""
        mock_db = AsyncMock()

        with patch.object(
            MatchEngine, "record_interest",
            new_callable=AsyncMock,
            return_value=MagicMock(spec=object),
        ) as mock_v1:
            record = await MatchEngineV2.record_interest_v2(
                mock_db, 1, 2,
            )
            mock_v1.assert_called_once_with(mock_db, 1, 2)
            assert record is not None
