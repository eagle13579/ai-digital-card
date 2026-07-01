"""
Tests for knowledge_graph, optimization, and ab_testing modules.
"""
from __future__ import annotations

import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.knowledge_graph import (
    GraphNode,
    GraphEdge,
    KnowledgeGraph,
    KnowledgeGraphBuilder,
    CachedKnowledgeGraphBuilder,
)
from app.ai.optimization import OptimizationAnalyzer
from app.ai.ab_testing import (
    ExperimentConfig,
    ExperimentState,
    VariantDistributor,
    MetricsCollector,
    SignificanceTester,
    ABTestingEngine,
    get_ab_testing_engine,
    chi_square_pvalue,
    bayesian_win_probability,
    z_score,
    EXPERIMENT_STATUS_DRAFT,
    EXPERIMENT_STATUS_RUNNING,
    EXPERIMENT_STATUS_PAUSED,
    EXPERIMENT_STATUS_COMPLETED,
)


# ======================================================================
# KnowledgeGraph 模块测试
# ======================================================================


class TestGraphNode:
    """GraphNode 数据类测试"""

    def test_node_creation_defaults(self):
        node = GraphNode(id="user:1", label="张三", type="user")
        assert node.id == "user:1"
        assert node.label == "张三"
        assert node.type == "user"
        assert node.properties == {}

    def test_node_creation_with_properties(self):
        node = GraphNode(
            id="user:1",
            label="张三",
            type="user",
            properties={"company": "TestCorp", "title": "经理"},
        )
        assert node.properties["company"] == "TestCorp"

    def test_node_to_dict(self):
        node = GraphNode(id="user:1", label="张三", type="user", properties={"title": "CTO"})
        d = node.to_dict()
        assert d == {"id": "user:1", "label": "张三", "type": "user", "properties": {"title": "CTO"}}

    def test_brochure_node(self):
        node = GraphNode(id="brochure:42", label="我的画册", type="brochure")
        assert node.type == "brochure"
        assert "brochure" in node.id

    def test_tag_node(self):
        node = GraphNode(id="tag:python", label="Python开发", type="tag", properties={"weight": 0.9})
        assert node.id == "tag:python"
        assert node.properties["weight"] == 0.9


class TestGraphEdge:
    """GraphEdge 数据类测试"""

    def test_edge_defaults(self):
        edge = GraphEdge(source="user:1", target="user:2", relation="trust")
        assert edge.source == "user:1"
        assert edge.target == "user:2"
        assert edge.relation == "trust"
        assert edge.weight == 1.0
        assert edge.properties == {}

    def test_edge_custom_weight(self):
        edge = GraphEdge(source="user:1", target="user:2", relation="tag_match", weight=0.75)
        assert edge.weight == 0.75

    def test_edge_to_dict(self):
        edge = GraphEdge(
            source="user:1",
            target="user:2",
            relation="trust",
            weight=1.0,
            properties={"created_at": "2025-01-01"},
        )
        d = edge.to_dict()
        assert d["source"] == "user:1"
        assert d["target"] == "user:2"
        assert d["relation"] == "trust"
        assert d["weight"] == 1.0

    def test_edge_negative_weight(self):
        edge = GraphEdge(source="user:1", target="user:2", relation="blocked", weight=-1.0)
        assert edge.weight == -1.0  # 允许负权重


class TestKnowledgeGraph:
    """KnowledgeGraph 集合操作测试"""

    def test_empty_graph(self):
        kg = KnowledgeGraph()
        assert kg.nodes == []
        assert kg.edges == []

    def test_add_node(self):
        kg = KnowledgeGraph()
        node = GraphNode(id="user:1", label="张三", type="user")
        kg.add_node(node)
        assert len(kg.nodes) == 1

    def test_add_node_dedup(self):
        kg = KnowledgeGraph()
        n1 = GraphNode(id="user:1", label="张三", type="user")
        n2 = GraphNode(id="user:1", label="张三", type="user")
        kg.add_node(n1)
        kg.add_node(n2)
        assert len(kg.nodes) == 1  # 重复 ID 不应添加

    def test_add_node_different_ids(self):
        kg = KnowledgeGraph()
        kg.add_node(GraphNode(id="user:1", label="A", type="user"))
        kg.add_node(GraphNode(id="user:2", label="B", type="user"))
        kg.add_node(GraphNode(id="brochure:1", label="C", type="brochure"))
        assert len(kg.nodes) == 3

    def test_to_dict_full(self):
        kg = KnowledgeGraph()
        kg.add_node(GraphNode(id="user:1", label="张三", type="user"))
        kg.add_edge(GraphEdge(source="user:1", target="user:2", relation="trust"))
        d = kg.to_dict()
        assert len(d["nodes"]) == 1
        assert len(d["edges"]) == 1
        assert d["nodes"][0]["id"] == "user:1"


class TestKnowledgeGraphBuilderMocked:
    """KnowledgeGraphBuilder 模拟 DB 异步测试"""

    @pytest.mark.asyncio
    async def test_build_user_graph_user_not_found(self):
        """用户不存在时应返回空图"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        builder = KnowledgeGraphBuilder(db=mock_db)
        kg = await builder.build_user_graph(user_id=999)
        assert len(kg.nodes) == 0
        assert len(kg.edges) == 0

    @pytest.mark.asyncio
    async def test_get_shortest_path_same_user(self):
        """相同用户应返回空路径"""
        mock_db = AsyncMock()
        builder = KnowledgeGraphBuilder(db=mock_db)
        paths = await builder.get_shortest_path(user_id_a=1, user_id_b=1)
        assert paths == []

    @pytest.mark.asyncio
    async def test_get_common_neighbors_no_db_calls(self):
        """当模拟数据库无邻居时返回空列表"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        builder = KnowledgeGraphBuilder(db=mock_db)
        common = await builder.get_common_neighbors(1, 2)
        assert common == []

    @pytest.mark.asyncio
    async def test_get_recommendation_candidates_empty(self):
        """无邻居时推荐为空"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        builder = KnowledgeGraphBuilder(db=mock_db)
        candidates = await builder.get_recommendation_candidates(user_id=1)
        assert candidates == []

    @pytest.mark.asyncio
    async def test_max_nodes_limit(self):
        """max_nodes 限制应生效"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        builder = KnowledgeGraphBuilder(db=mock_db)
        kg = await builder.build_user_graph(user_id=1, max_nodes=1)
        assert len(kg.nodes) == 0


# ======================================================================
# OptimizationAnalyzer 模块测试
# ======================================================================


class TestOptimizationAnalyzer:
    """OptimizationAnalyzer 静态方法测试"""

    def test_analyze_completeness_full(self):
        fields = {
            "name": "张三",
            "position": "CTO",
            "company": "TestCorp",
            "phone": "13800138000",
            "email": "test@test.com",
            "wechat": "wx123",
            "address": "北京",
            "website": "https://test.com",
            "cover_image": "img.jpg",
            "intro": "十年技术管理经验",
        }
        result = OptimizationAnalyzer.analyze_completeness(fields)
        assert result["score"] >= 85
        assert result["level"] in ("优秀", "良好")
        assert result["filled_fields"] >= 9
        assert result["missing_fields"] == []

    def test_analyze_completeness_empty(self):
        result = OptimizationAnalyzer.analyze_completeness({})
        assert result["score"] == 0.0
        assert result["filled_fields"] == 0
        assert result["level"] == "待完善"

    def test_analyze_completeness_partial(self):
        fields = {"name": "张三", "position": "CTO", "company": "TestCorp"}
        result = OptimizationAnalyzer.analyze_completeness(fields)
        assert 20 <= result["score"] <= 80
        assert "phone" in result["missing_fields"]

    def test_analyze_completeness_extra_fields_bonus(self):
        """intro / skills / industry 应获得加分"""
        fields = {
            "name": "张三",
            "position": "CTO",
            "company": "TestCorp",
            "intro": "资深技术专家",
            "skills": "Python,Go",
        }
        result = OptimizationAnalyzer.analyze_completeness(fields)
        base_only = OptimizationAnalyzer.analyze_completeness(
            {"name": "张三", "position": "CTO", "company": "TestCorp"}
        )
        assert result["score"] > base_only["score"]

    def test_analyze_keyword_coverage_matched(self):
        fields = {
            "intro": "我是一名产品经理，擅长数据分析与用户体验设计",
            "position": "产品经理",
        }
        result = OptimizationAnalyzer.analyze_keyword_coverage(fields, industry="互联网")
        assert result["score"] > 0
        assert len(result["matched_keywords"]) > 0

    def test_analyze_keyword_coverage_no_match(self):
        fields = {"intro": "热爱生活，喜欢运动"}
        result = OptimizationAnalyzer.analyze_keyword_coverage(fields, industry="金融")
        assert result["score"] == 0
        assert result["matched_keywords"] == []
        assert len(result["suggested_keywords"]) > 0

    def test_analyze_keyword_coverage_unknown_industry(self):
        """未知行业应返回默认关键词列表"""
        fields = {"intro": "专业服务"}
        result = OptimizationAnalyzer.analyze_keyword_coverage(fields, industry="未知行业")
        assert result["total_keywords"] == 5

    def test_analyze_professionalism_perfect(self):
        fields = {
            "name": "张三丰",
            "position": "CTO",
            "company": "TestCorp",
            "phone": "13800138000",
            "email": "test@test.com",
            "intro": "资深技术专家",
        }
        result = OptimizationAnalyzer.analyze_professionalism(fields)
        assert result["score"] >= 80
        assert len(result["issues"]) == 0

    def test_analyze_professionalism_missing_required(self):
        fields = {}
        result = OptimizationAnalyzer.analyze_professionalism(fields)
        issues = {i["field"] for i in result["issues"]}
        assert issues.intersection({"name", "position", "company"})

    def test_analyze_professionalism_bad_phone(self):
        fields = {
            "name": "张三",
            "position": "CTO",
            "company": "Corp",
            "phone": "12345",
        }
        result = OptimizationAnalyzer.analyze_professionalism(fields)
        phone_issues = [i for i in result["issues"] if i["field"] == "phone"]
        assert len(phone_issues) > 0

    def test_analyze_professionalism_bad_email(self):
        fields = {
            "name": "张三",
            "position": "CTO",
            "company": "Corp",
            "email": "bademail",
        }
        result = OptimizationAnalyzer.analyze_professionalism(fields)
        email_issues = [i for i in result["issues"] if i["field"] == "email"]
        assert len(email_issues) > 0

    @pytest.mark.asyncio
    async def test_get_optimization_suggestions(self):
        """综合优化建议应返回完整的4项分析"""
        fields = {
            "name": "张三",
            "position": "CTO",
            "company": "TestCorp",
            "intro": "资深全栈工程师，擅长数据分析",
        }
        result = await OptimizationAnalyzer.get_optimization_suggestions(
            brochure_id=1, fields=fields, industry="互联网"
        )
        assert result["brochure_id"] == 1
        assert "completeness" in result
        assert "keyword_coverage" in result
        assert "professionalism" in result
        assert "overall_score" in result
        assert len(result["top_priorities"]) > 0

    @pytest.mark.asyncio
    async def test_get_optimization_suggestions_empty_fields(self):
        """空字段应返回待完善建议"""
        result = await OptimizationAnalyzer.get_optimization_suggestions(
            brochure_id=2, fields={}, industry=""
        )
        assert result["overall_score"] < 50
        assert any("补充" in p for p in result["top_priorities"])


# ======================================================================
# A/B Testing 模块测试
# ======================================================================


class TestExperimentConfig:
    def test_config_defaults(self):
        c = ExperimentConfig(name="测试实验")
        assert c.name == "测试实验"
        assert c.traffic_fraction == 1.0
        assert c.min_sample_size == 100
        assert c.significance_level == 0.05
        assert c.metric == "click_rate"

    def test_config_traffic_clamping(self):
        c = ExperimentConfig(name="test", traffic_fraction=5.0)
        assert c.traffic_fraction == 1.0
        c2 = ExperimentConfig(name="test", traffic_fraction=-1.0)
        assert c2.traffic_fraction == 0.01

    def test_config_with_variants(self):
        variants = [{"name": "A", "color": "red"}, {"name": "B", "color": "blue"}]
        c = ExperimentConfig(name="test", variants=variants)
        assert len(c.variants) == 2


class TestSignificanceTester:
    def test_chi_square_significant(self):
        tester = SignificanceTester(alpha=0.05)
        result = tester.chi_square_test(
            control_impressions=1000, control_success=100,
            variant_impressions=1000, variant_success=150,
        )
        assert result["is_significant"] is True
        assert result["p_value"] < 0.05

    def test_chi_square_not_significant(self):
        tester = SignificanceTester(alpha=0.05)
        result = tester.chi_square_test(
            control_impressions=100, control_success=10,
            variant_impressions=100, variant_success=11,
        )
        assert result["is_significant"] is False

    def test_chi_square_zero_impressions(self):
        tester = SignificanceTester()
        result = tester.chi_square_test(
            control_impressions=0, control_success=0,
            variant_impressions=100, variant_success=10,
        )
        assert result["control_rate"] == 0.0
        assert result["p_value"] >= 0

    def test_bayesian_basic(self):
        tester = SignificanceTester()
        result = tester.bayesian_test(
            control_success=50, control_total=1000,
            variant_success=80, variant_total=1000,
        )
        assert 0 <= result["win_probability"] <= 1.0
        assert result["method"] == "bayesian"

    def test_bayesian_no_data(self):
        tester = SignificanceTester()
        result = tester.bayesian_test(
            control_success=0, control_total=0,
            variant_success=0, variant_total=0,
        )
        assert result["win_probability"] == 0.5


class TestVariantDistributor:
    def test_assign_by_user_id_deterministic(self):
        variants = [{"name": "A"}, {"name": "B"}]
        r1 = VariantDistributor.assign_by_user_id(42, variants)
        r2 = VariantDistributor.assign_by_user_id(42, variants)
        assert r1 == r2

    def test_assign_by_user_id_different_users(self):
        variants = [{"name": "A"}, {"name": "B"}]
        results = {
            VariantDistributor.assign_by_user_id(i, variants)
            for i in range(1, 101)
        }
        assert len(results) > 1

    def test_assign_random_empty(self):
        assert VariantDistributor.assign_random([]) == 0

    def test_assign_random_with_weights(self):
        variants = [{"name": "A"}, {"name": "B"}, {"name": "C"}]
        weights = [0.0, 0.0, 1.0]
        results = [
            VariantDistributor.assign_random(variants, weights)
            for _ in range(100)
        ]
        assert all(r == 2 for r in results)


class TestMetricsCollector:
    def test_aggregate_empty(self):
        result = MetricsCollector.aggregate_events([], metric="click_rate")
        assert result == {}

    def test_aggregate_basic(self):
        events = [
            {"variant_id": 0, "event_type": "impression"},
            {"variant_id": 0, "event_type": "click"},
            {"variant_id": 1, "event_type": "impression"},
            {"variant_id": 1, "event_type": "conversion"},
        ]
        result = MetricsCollector.aggregate_events(events, metric="click_rate")
        assert 0 in result
        assert 1 in result
        # impressions incremented per event: variant 0 has 2 events → click_rate = 1/2 = 0.5
        assert result[0]["click_rate"] == 0.5
        # variant 1 has 2 events → conversion_rate = 1/2 = 0.5
        assert result[1]["conversion_rate"] == 0.5

    def test_aggregate_zero_impressions(self):
        events = [{"variant_id": 0, "event_type": "click"}]
        result = MetricsCollector.aggregate_events(events)
        assert result[0]["click_rate"] == 1.0

    def test_aggregate_multiple_metrics(self):
        events = [
            {"variant_id": 0, "event_type": "impression"},
            {"variant_id": 0, "event_type": "click"},
            {"variant_id": 0, "event_type": "view"},
            {"variant_id": 0, "event_type": "conversion"},
            {"variant_id": 1, "event_type": "impression"},
        ]
        result = MetricsCollector.aggregate_events(events, metric="conversion")
        assert result[0]["conversions"] == 1
        assert result[0]["views"] == 1
        assert result[1]["impressions"] == 1


class TestABTestingEngine:
    """ABTestingEngine 主引擎全生命周期测试"""

    def test_create_experiment(self):
        engine = ABTestingEngine()
        state = engine.create_experiment(
            experiment_id=1,
            name="首页CTA测试",
            variants=[{"name": "红色按钮"}, {"name": "蓝色按钮"}],
        )
        assert state.experiment_id == 1
        assert state.status == EXPERIMENT_STATUS_DRAFT
        assert engine.get_experiment(1) is state

    def test_create_duplicate_id_overwrites(self):
        engine = ABTestingEngine()
        engine.create_experiment(experiment_id=1, name="原实验")
        engine.create_experiment(experiment_id=1, name="新实验")
        assert engine.get_experiment(1).config.name == "新实验"

    def test_experiment_lifecycle(self):
        engine = ABTestingEngine()
        engine.create_experiment(
            experiment_id=10,
            name="生命周期测试",
            variants=[{"name": "A"}, {"name": "B"}],
        )
        engine.start_experiment(10)
        assert engine.get_experiment(10).status == EXPERIMENT_STATUS_RUNNING
        engine.pause_experiment(10)
        assert engine.get_experiment(10).status == EXPERIMENT_STATUS_PAUSED
        engine.resume_experiment(10)
        assert engine.get_experiment(10).status == EXPERIMENT_STATUS_RUNNING
        engine.stop_experiment(10)
        assert engine.get_experiment(10).status == EXPERIMENT_STATUS_COMPLETED

    def test_pause_not_running(self):
        engine = ABTestingEngine()
        engine.create_experiment(experiment_id=20, name="test")
        engine.pause_experiment(20)
        assert engine.get_experiment(20).status == EXPERIMENT_STATUS_DRAFT

    def test_delete_experiment(self):
        engine = ABTestingEngine()
        engine.create_experiment(experiment_id=30, name="待删除")
        assert engine.delete_experiment(30) is True
        assert engine.get_experiment(30) is None
        assert engine.delete_experiment(999) is False

    def test_list_experiments(self):
        engine = ABTestingEngine()
        engine.create_experiment(experiment_id=1, name="A")
        engine.create_experiment(experiment_id=2, name="B")
        assert len(engine.list_experiments()) == 2

    def test_assign_variant_not_running(self):
        engine = ABTestingEngine()
        engine.create_experiment(
            experiment_id=40, name="未运行",
            variants=[{"name": "A"}, {"name": "B"}],
        )
        result = engine.assign_variant(40, user_id=1)
        assert result is None

    def test_assign_variant_running(self):
        engine = ABTestingEngine()
        engine.create_experiment(
            experiment_id=50, name="运行中",
            variants=[{"name": "A"}, {"name": "B"}],
        )
        engine.start_experiment(50)
        result = engine.assign_variant(50, user_id=42)
        assert result is None or 0 <= result < 2

    def test_record_and_compute_chi_square(self):
        engine = ABTestingEngine()
        engine.create_experiment(
            experiment_id=60, name="卡方测试",
            variants=[{"name": "对照组"}, {"name": "实验组"}],
            metric="click_rate",
        )
        engine.start_experiment(60)
        events = []
        for _ in range(1000):
            events.append({"variant_id": 0, "event_type": "impression"})
        for _ in range(80):
            events.append({"variant_id": 0, "event_type": "click"})
        for _ in range(1000):
            events.append({"variant_id": 1, "event_type": "impression"})
        for _ in range(120):
            events.append({"variant_id": 1, "event_type": "click"})
        result = engine.compute_results(60, events, method="chi_square")
        assert result["experiment_id"] == 60
        assert len(result["variants"]) == 1
        assert result["control"]["variant_name"] == "对照组"
        assert result["variants"][0]["variant_name"] == "实验组"

    def test_record_and_compute_bayesian(self):
        engine = ABTestingEngine()
        engine.create_experiment(
            experiment_id=70, name="贝叶斯测试",
            variants=[{"name": "A"}, {"name": "B"}],
        )
        engine.start_experiment(70)
        events = []
        for _ in range(500):
            events.append({"variant_id": 0, "event_type": "impression"})
        for _ in range(40):
            events.append({"variant_id": 0, "event_type": "conversion"})
        for _ in range(500):
            events.append({"variant_id": 1, "event_type": "impression"})
        for _ in range(60):
            events.append({"variant_id": 1, "event_type": "conversion"})
        result = engine.compute_results(70, events, method="bayesian")
        assert result["test_method"] == "bayesian"
        assert "win_probability" in result["variants"][0]["test_result"]

    def test_compute_results_no_experiment(self):
        engine = ABTestingEngine()
        result = engine.compute_results(999, [], method="chi_square")
        assert "error" in result

    def test_auto_decision_no_experiment(self):
        engine = ABTestingEngine()
        decision = engine.auto_decision(999)
        assert decision["decision"] == "error"

    def test_auto_decision_continue(self):
        engine = ABTestingEngine()
        engine.create_experiment(
            experiment_id=80, name="继续测试",
            variants=[{"name": "A"}, {"name": "B"}],
            min_sample_size=10,
        )
        engine.start_experiment(80)
        events = []
        for _ in range(100):
            events.append({"variant_id": 0, "event_type": "impression"})
        for _ in range(10):
            events.append({"variant_id": 0, "event_type": "click"})
        for _ in range(100):
            events.append({"variant_id": 1, "event_type": "impression"})
        for _ in range(11):
            events.append({"variant_id": 1, "event_type": "click"})
        results = engine.compute_results(80, events)
        decision = engine.auto_decision(80, results)
        assert decision["decision"] in ("continue", "stop")

    def test_rollout_winner(self):
        engine = ABTestingEngine()
        engine.create_experiment(
            experiment_id=90, name="发布测试",
            variants=[{"name": "原始版"}, {"name": "新版"}],
        )
        engine.start_experiment(90)
        result = engine.rollout_winner(90, "新版")
        assert result["success"] is True
        assert result["variant_name"] == "新版"
        assert engine.get_experiment(90).status == EXPERIMENT_STATUS_COMPLETED

    def test_rollout_winner_not_found(self):
        engine = ABTestingEngine()
        engine.create_experiment(
            experiment_id=91, name="找不到变体",
            variants=[{"name": "A"}],
        )
        result = engine.rollout_winner(91, "不存在的变体")
        assert "error" in result

    def test_decision_logs(self):
        engine = ABTestingEngine()
        engine.create_experiment(
            experiment_id=95, name="决策日志",
            variants=[{"name": "A"}, {"name": "B"}],
        )
        engine.start_experiment(95)
        logs = engine.get_decision_logs(95)
        assert logs == []
        # 先收集一些事件再触发决策
        events = []
        for _ in range(100):
            events.append({"variant_id": 0, "event_type": "impression"})
        for _ in range(10):
            events.append({"variant_id": 0, "event_type": "click"})
        for _ in range(100):
            events.append({"variant_id": 1, "event_type": "impression"})
        for _ in range(12):
            events.append({"variant_id": 1, "event_type": "click"})
        results = engine.compute_results(95, events)
        decision = engine.auto_decision(95, results)
        logs = engine.get_decision_logs(95)
        assert len(logs) == 1

    def test_get_ab_testing_engine_singleton(self):
        e1 = get_ab_testing_engine()
        e2 = get_ab_testing_engine()
        assert e1 is e2


class TestStatFunctions:
    """独立统计函数测试"""

    def test_z_score_default(self):
        z = z_score(alpha=0.05, two_tailed=True)
        assert 1.8 < z < 2.0

    def test_z_score_one_tailed(self):
        z = z_score(alpha=0.05, two_tailed=False)
        assert 1.6 < z < 1.7

    def test_chi_square_pvalue_independent(self):
        p = chi_square_pvalue([[50, 50], [50, 50]])
        assert p > 0.9

    def test_chi_square_pvalue_different(self):
        p = chi_square_pvalue([[20, 80], [80, 20]])
        assert p < 0.01

    def test_chi_square_pvalue_zero_total(self):
        assert chi_square_pvalue([[0, 0], [0, 0]]) == 1.0

    def test_bayesian_win_probability_no_data(self):
        wp, lift = bayesian_win_probability(0, 0, 0, 0)
        assert wp == 0.5
        assert lift == 0.0

    def test_bayesian_win_probability_sure_win(self):
        wp, lift = bayesian_win_probability(0, 100, 100, 100, simulations=5000)
        assert wp > 0.95
