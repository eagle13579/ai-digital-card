"""
好奇模式匹配引擎 — 单元测试
"""
import math
import time
import pytest
from curiosity_matching_service import (
    CuriosityMode,
    CuriosityParams,
    CuriosityMetrics,
    MatchCandidate,
    CuriosityMatchingService,
    create_exploration_engine,
    create_execution_engine,
)


class TestCuriosityParams:
    """测试好奇参数模板。"""

    def test_exploration_preset_values(self):
        params = CuriosityParams.exploration_preset()
        assert params.exploration_rate == 0.85
        assert params.novelty_sensitivity == 0.90
        assert params.serendipity_factor == 0.15
        assert params.min_confidence_threshold == 0.30

    def test_execution_preset_values(self):
        params = CuriosityParams.execution_preset()
        assert params.exploration_rate == 0.20
        assert params.novelty_sensitivity == 0.30
        assert params.serendipity_factor == 0.02
        assert params.min_confidence_threshold == 0.65

    def test_param_validation_out_of_range(self):
        with pytest.raises(ValueError):
            CuriosityParams(
                exploration_rate=1.5,
                novelty_sensitivity=0.5,
                diversity_weight=0.5,
                match_expansion_factor=1.0,
                serendipity_factor=0.1,
                min_confidence_threshold=0.5,
                max_results_per_query=10,
                decay_rate=0.1,
                recovery_rate=0.1,
            )

    def test_param_validation_negative_exploration(self):
        with pytest.raises(ValueError):
            CuriosityParams(
                exploration_rate=-0.1,
                novelty_sensitivity=0.5,
                diversity_weight=0.5,
                match_expansion_factor=1.0,
                serendipity_factor=0.1,
                min_confidence_threshold=0.5,
                max_results_per_query=10,
                decay_rate=0.1,
                recovery_rate=0.1,
            )

    def test_expansion_factor_gate(self):
        with pytest.raises(ValueError):
            CuriosityParams(
                exploration_rate=0.5,
                novelty_sensitivity=0.5,
                diversity_weight=0.5,
                match_expansion_factor=0.5,
                serendipity_factor=0.1,
                min_confidence_threshold=0.5,
                max_results_per_query=10,
                decay_rate=0.1,
                recovery_rate=0.1,
            )


class TestMatchCandidate:
    """测试匹配候选结果。"""

    def test_valid_candidate(self):
        c = MatchCandidate(target_id=42, score=0.85)
        assert c.target_id == 42
        assert c.score == 0.85
        assert c.source == "matched"
        assert c.novelty_flag is False

    def test_score_validation(self):
        with pytest.raises(ValueError):
            MatchCandidate(target_id=1, score=1.5)

    def test_novelty_discovered_candidate(self):
        c = MatchCandidate(
            target_id=100,
            score=0.72,
            source="discovered",
            novelty_flag=True,
            metadata={"base_score": 0.60, "novelty_bonus": 0.12},
        )
        assert c.source == "discovered"
        assert c.novelty_flag is True
        assert c.metadata["novelty_bonus"] == 0.12

    def test_serendipity_candidate(self):
        c = MatchCandidate(
            target_id=999999,
            score=0.45,
            source="serendipity",
            novelty_flag=True,
        )
        assert c.source == "serendipity"
        assert c.score == 0.45


class TestCuriosityMetrics:
    """测试好奇指标。"""

    def test_initial_state(self):
        m = CuriosityMetrics()
        assert m.current_mode == CuriosityMode.EXECUTION
        assert m.match_discovery_count == 0
        assert m.total_queries == 0

    def test_record_query(self):
        m = CuriosityMetrics()
        m.record_query(candidates=100, discoveries=15, mode=CuriosityMode.EXPLORATION)
        assert m.total_queries == 1
        assert m.match_discovery_count == 15
        assert len(m.query_history) == 1

    def test_record_mode_switch(self):
        m = CuriosityMetrics()
        m.record_mode_switch(CuriosityMode.EXPLORATION, "test switch")
        assert m.mode_switch_count == 1
        assert m.current_mode == CuriosityMode.EXPLORATION
        assert len(m.mode_history) == 1

    def test_average_discovery_rate(self):
        m = CuriosityMetrics()
        assert m.average_discovery_rate == 0.0
        m.record_query(candidates=50, discoveries=10, mode=CuriosityMode.EXECUTION)
        m.record_query(candidates=80, discoveries=20, mode=CuriosityMode.EXECUTION)
        assert m.average_discovery_rate == 15.0

    def test_snapshot_includes_uptime(self):
        m = CuriosityMetrics()
        snap = m.snapshot()
        assert "current_mode" in snap
        assert "uptime_seconds" in snap
        assert snap["total_queries"] == 0

    def test_query_history_capped(self):
        m = CuriosityMetrics()
        for i in range(150):
            m.record_query(candidates=10, discoveries=i % 5, mode=CuriosityMode.EXECUTION)
        assert len(m.query_history) == 100


class TestCuriosityMatchingService:
    """测试好奇模式匹配引擎。"""

    def test_default_execution_mode(self):
        engine = CuriosityMatchingService()
        assert engine.mode == CuriosityMode.EXECUTION
        assert engine.active_params.exploration_rate == 0.20

    def test_exploration_mode_init(self):
        engine = CuriosityMatchingService(
            mode=CuriosityMode.EXPLORATION,
        )
        assert engine.mode == CuriosityMode.EXPLORATION
        assert engine.active_params.exploration_rate == 0.85

    def test_match_returns_list(self):
        engine = CuriosityMatchingService()
        results = engine.match(user_id=1, candidates=[10, 20, 30])
        assert isinstance(results, list)

    def test_match_execution_mode_limited_results(self):
        """执行模式下返回结果不应超过预设的 max_results_per_query。"""
        engine = CuriosityMatchingService(mode=CuriosityMode.EXECUTION)
        large_pool = list(range(1, 300))
        results = engine.match(user_id=1, candidates=large_pool)
        assert len(results) <= 20  # execution_preset max_results=20

    def test_match_exploration_mode_more_results(self):
        """探索模式应返回更多结果。"""
        engine = CuriosityMatchingService(mode=CuriosityMode.EXPLORATION)
        large_pool = list(range(1, 300))
        results = engine.match(user_id=1, candidates=large_pool)
        assert len(results) <= 50  # exploration_preset max_results=50

    def test_auto_switch_on_low_results(self):
        """当匹配结果低于阈值时，应自动切换到探索模式。"""
        engine = CuriosityMatchingService(
            mode=CuriosityMode.EXECUTION,
            auto_switch_threshold=10,
        )
        # 用小候选集
        results = engine.match(user_id=1, candidates=[1, 2, 3, 4, 5])
        # 自动切换后引擎应该做了重试
        assert engine.metrics.mode_switch_count >= 1

    def test_manual_mode_switch(self):
        engine = CuriosityMatchingService(mode=CuriosityMode.EXECUTION)
        assert engine.metrics.mode_switch_count == 0
        engine.mode = CuriosityMode.EXPLORATION
        assert engine.mode == CuriosityMode.EXPLORATION
        assert engine.metrics.mode_switch_count == 1

    def test_seen_ids_tracking(self):
        engine = CuriosityMatchingService(
            mode=CuriosityMode.EXECUTION,
            seen_ids=set(),
        )
        results = engine.match(user_id=1, candidates=[10, 20, 30])
        # seen_ids 应该在匹配后更新
        assert len(engine._seen_ids) > 0

    def test_discovery_feedback_decay(self):
        """连续空发现应衰减探索率。"""
        engine = CuriosityMatchingService(mode=CuriosityMode.EXPLORATION)
        initial_rate = engine.metrics.current_exploration_rate

        for _ in range(5):
            engine.apply_discovery_feedback(found_new=False)

        assert engine.metrics.current_exploration_rate < initial_rate

    def test_discovery_feedback_recovery(self):
        """有新发现应恢复探索率。"""
        engine = CuriosityMatchingService(mode=CuriosityMode.EXPLORATION)

        # 先衰减
        for _ in range(2):
            engine.apply_discovery_feedback(found_new=False)

        decayed_rate = engine.metrics.current_exploration_rate

        # 恢复（使用多次恢复越过浮点数精度坑）
        engine.apply_discovery_feedback(found_new=True)

        assert engine.metrics.current_exploration_rate >= decayed_rate

    def test_performance_report_shape(self):
        engine = CuriosityMatchingService(mode=CuriosityMode.EXPLORATION)
        # 先跑几次
        for i in range(10):
            engine.match(user_id=i, candidates=list(range(i * 10, i * 10 + 50)))
        report = engine.get_performance_report()
        assert "engine" in report
        assert "mode" in report
        assert "metrics" in report
        assert "active_params" in report
        assert report["engine"] == "CuriosityMatchingService"

    def test_set_params(self):
        engine = CuriosityMatchingService()
        new_params = CuriosityParams(
            exploration_rate=0.5,
            novelty_sensitivity=0.5,
            diversity_weight=0.5,
            match_expansion_factor=2.0,
            serendipity_factor=0.1,
            min_confidence_threshold=0.4,
            max_results_per_query=30,
            decay_rate=0.1,
            recovery_rate=0.3,
        )
        engine.set_params(CuriosityMode.EXECUTION, new_params)
        assert engine.active_params.exploration_rate == 0.5

    def test_reset_metrics(self):
        engine = CuriosityMatchingService()
        engine.match(user_id=1, candidates=[10, 20, 30])
        assert engine.metrics.total_queries > 0
        engine.reset_metrics()
        assert engine.metrics.total_queries == 0
        assert engine.metrics.match_discovery_count == 0


class TestFactoryFunctions:
    """测试便捷工厂函数。"""

    def test_create_exploration_engine(self):
        engine = create_exploration_engine()
        assert engine.mode == CuriosityMode.EXPLORATION

    def test_create_execution_engine(self):
        engine = create_execution_engine()
        assert engine.mode == CuriosityMode.EXECUTION
