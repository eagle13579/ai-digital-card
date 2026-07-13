"""
AI数智名片 — 在线学习单元测试
============================

测试 OnlineLearningService 和 online_learning_pipeline 的核心功能。

运行:
    cd backend && python -m pytest tests/test_online_learning.py -v

覆盖:
  - OnlineLearningService.process_feedback()  — 单条反馈处理
  - OnlineLearningService.update_model_weights() — 批量权重更新
  - OnlineLearningService.get_online_stats()  — 学习统计
  - 奖励值映射 (action → reward)
  - 相似度估计 (reward → similarity)
  - 权重重置
  - Pipeline 初始化与配置
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── 将 backend 加入路径 ──
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_feedback_service():
    """模拟的 FeedbackService。"""
    svc = MagicMock()
    # record_feedback_async 返回标准的 FeedbackResult
    from app.services.feedback_service import FeedbackResult

    async def mock_record(user_id, match_id, action, score=None, source="recommend", recommendation_id=""):
        return FeedbackResult(
            user_id=user_id,
            content_id=match_id,
            action=action,
            weight_delta=0.3,
            current_boost=1.0,
            message="测试反馈",
        )

    svc.record_feedback_async = mock_record
    svc.get_global_stats = MagicMock(return_value={
        "total_feedback": 100,
        "recent_feedback": 25,
        "total_users": 10,
    })
    return svc


@pytest.fixture
def online_service(mock_feedback_service):
    """带有 mock feedback_service 的 OnlineLearningService。"""
    from app.services.online_learning_service import OnlineLearningService, reset_online_learning_service

    reset_online_learning_service()
    svc = OnlineLearningService(
        feedback_service=mock_feedback_service,
        model_dir=BACKEND_DIR / "tests" / "test_models",
        lr=0.1,
        baseline_decay=0.8,
    )
    yield svc
    reset_online_learning_service()


# ═══════════════════════════════════════════════════════════════════
# 测试: 单条反馈处理
# ═══════════════════════════════════════════════════════════════════


class TestProcessFeedback:
    """测试 OnlineLearningService.process_feedback()。"""

    @pytest.mark.asyncio
    async def test_click_feedback(self, online_service):
        """TC1: 点击反馈 → 权重正向更新"""
        result = await online_service.process_feedback(
            user_id=1, match_id=42, action="click",
        )

        assert result["feedback_result"] is not None
        assert result["feedback_result"].action == "click"
        assert result["reward"] > 0
        assert "old_weights" in result
        assert "new_weights" in result
        # 权重应该发生了变化
        assert result["new_weights"] != result["old_weights"]
        # 奖励值应为 1.0 (click)
        assert abs(result["reward"] - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_unlock_feedback(self, online_service):
        """TC2: 解锁反馈 → 强正信号奖励"""
        result = await online_service.process_feedback(
            user_id=2, match_id=99, action="unlock",
        )

        assert result["reward"] == 2.0
        assert result["weight_delta"] >= 0

    @pytest.mark.asyncio
    async def test_ignore_feedback(self, online_service):
        """TC3: 忽略反馈 → 负奖励"""
        result = await online_service.process_feedback(
            user_id=3, match_id=7, action="ignore",
        )

        assert result["reward"] < 0  # 负向奖励
        assert result["weight_delta"] >= 0

    @pytest.mark.asyncio
    async def test_rate_feedback(self, online_service):
        """TC4: 评分反馈 → 按比例奖励"""
        # 5分 → 正奖励
        result_high = await online_service.process_feedback(
            user_id=4, match_id=10, action="rate", score=5.0,
        )
        assert result_high["reward"] > 0

        # 1分 → 负奖励
        result_low = await online_service.process_feedback(
            user_id=4, match_id=11, action="rate", score=1.0,
        )
        assert result_low["reward"] < 0

        # 3分 → 中性
        result_mid = await online_service.process_feedback(
            user_id=4, match_id=12, action="rate", score=3.0,
        )
        assert abs(result_mid["reward"]) < 0.01

    @pytest.mark.asyncio
    async def test_invalid_action(self, online_service):
        """TC5: 非法动作 → 抛出 ValueError"""
        with pytest.raises(ValueError, match="不支持的反馈动作"):
            await online_service.process_feedback(
                user_id=5, match_id=1, action="invalid_action",
            )

    @pytest.mark.asyncio
    async def test_rate_without_score(self, online_service):
        """TC6: rate 动作缺少 score → 抛出 ValueError"""
        with pytest.raises(ValueError, match="必须提供 score"):
            await online_service.process_feedback(
                user_id=5, match_id=1, action="rate",
            )


# ═══════════════════════════════════════════════════════════════════
# 测试: 批量权重更新
# ═══════════════════════════════════════════════════════════════════


class TestUpdateModelWeights:
    """测试 OnlineLearningService.update_model_weights()。"""

    @pytest.mark.asyncio
    async def test_batch_update(self, online_service):
        """TC7: 批量更新 → 返回权重变化"""
        # 先处理几条反馈
        for i in range(5):
            await online_service.process_feedback(
                user_id=i, match_id=i * 10, action="click",
            )

        result = await online_service.update_model_weights()

        assert "weights_before" in result
        assert "weights_after" in result
        assert result["users_processed"] >= 0

    @pytest.mark.asyncio
    async def test_empty_update(self, online_service):
        """TC8: 无反馈时更新 → 安全运行"""
        result = await online_service.update_model_weights()

        assert result is not None
        assert isinstance(result["users_processed"], int)


# ═══════════════════════════════════════════════════════════════════
# 测试: 在线学习统计
# ═══════════════════════════════════════════════════════════════════


class TestOnlineStats:
    """测试 OnlineLearningService.get_online_stats()。"""

    @pytest.mark.asyncio
    async def test_initial_stats(self, online_service):
        """TC9: 初始统计 → 零值状态"""
        stats = await online_service.get_online_stats()

        assert stats.total_feedback_processed == 0
        assert stats.total_weight_updates == 0
        assert stats.total_reward == 0.0
        assert stats.avg_reward == 0.0
        assert "alpha" in stats.current_weights
        assert "beta" in stats.current_weights
        assert "gamma" in stats.current_weights

    @pytest.mark.asyncio
    async def test_stats_after_feedback(self, online_service):
        """TC10: 处理后统计 → 正确累加"""
        await online_service.process_feedback(user_id=1, match_id=10, action="click")
        await online_service.process_feedback(user_id=2, match_id=20, action="unlock")
        await online_service.process_feedback(user_id=3, match_id=30, action="ignore")

        stats = await online_service.get_online_stats()

        assert stats.total_feedback_processed == 3
        # click(1.0) + unlock(2.0) + ignore(-0.5) = 2.5
        assert abs(stats.total_reward - 2.5) < 0.01
        assert stats.total_weight_updates == 3
        assert stats.action_distribution.get("click") == 1
        assert stats.action_distribution.get("unlock") == 1
        assert stats.action_distribution.get("ignore") == 1


# ═══════════════════════════════════════════════════════════════════
# 测试: 奖励值映射
# ═══════════════════════════════════════════════════════════════════


class TestActionToReward:
    """测试 OnlineLearningService._action_to_reward() 奖励映射。"""

    def _reward(self, action, score=None):
        from app.services.online_learning_service import OnlineLearningService
        return OnlineLearningService._action_to_reward(action, score)

    def test_like_reward(self):
        assert self._reward("like") == 1.0

    def test_dislike_reward(self):
        assert self._reward("dislike") == -0.5

    def test_skip_reward(self):
        assert self._reward("skip") == 0.0

    def test_click_reward(self):
        assert self._reward("click") == 1.0

    def test_unlock_reward(self):
        assert self._reward("unlock") == 2.0

    def test_ignore_reward(self):
        assert self._reward("ignore") == -0.5

    def test_rate_score_5(self):
        # (5-3)/4 = 0.5
        assert abs(self._reward("rate", 5.0) - 0.5) < 0.01

    def test_rate_score_1(self):
        # (1-3)/4 = -0.5
        assert abs(self._reward("rate", 1.0) - (-0.5)) < 0.01

    def test_rate_score_3(self):
        # (3-3)/4 = 0.0
        assert abs(self._reward("rate", 3.0)) < 0.01

    def test_rate_no_score(self):
        """rate 不传 score → 0.0"""
        assert abs(self._reward("rate")) < 0.01

    def test_unknown_action(self):
        """未知动作 → 0.0"""
        assert abs(self._reward("unknown_action")) < 0.01


# ═══════════════════════════════════════════════════════════════════
# 测试: 相似度估计
# ═══════════════════════════════════════════════════════════════════


class TestSimilarityEstimation:
    """测试 OnlineLearningService._estimate_similarity_from_reward()。"""

    def _sim(self, reward, key="alpha"):
        from app.services.online_learning_service import OnlineLearningService
        return OnlineLearningService._estimate_similarity_from_reward(reward, key)

    def test_positive_reward_high_similarity(self):
        """正奖励 → 高相似度"""
        sim = self._sim(2.0)  # unlock
        assert 0.8 <= sim <= 0.9

    def test_negative_reward_low_similarity(self):
        """负奖励 → 低相似度"""
        sim = self._sim(-0.5)  # ignore/dislike
        assert 0.1 <= sim <= 0.3

    def test_neutral_reward(self):
        """中性奖励 → 0.5 附近"""
        sim = self._sim(0.0)  # skip
        assert abs(sim - 0.5) < 0.05

    def test_mild_positive(self):
        """弱正奖励"""
        sim = self._sim(0.25)
        assert 0.5 < sim < 0.6

    def test_extreme_reward_clamped(self):
        """极端值被 clamp"""
        sim_high = self._sim(10.0)  # 远超上限
        assert sim_high <= 0.9

        sim_low = self._sim(-10.0)  # 远低下限
        assert sim_low >= 0.1


# ═══════════════════════════════════════════════════════════════════
# 测试: 权重重置
# ═══════════════════════════════════════════════════════════════════


class TestWeightReset:
    """测试 OnlineLearningService.reset_weights()。"""

    @pytest.mark.asyncio
    async def test_reset_to_default(self, online_service):
        """TC11: 重置为默认值"""
        # 先修改权重
        await online_service.process_feedback(user_id=1, match_id=1, action="unlock")
        weights_before = online_service.get_weight_optimizer().get_weights()

        # 重置
        online_service.reset_weights()

        weights_after = online_service.get_weight_optimizer().get_weights()

        # 默认: alpha=0.5, beta=0.3, gamma=0.2
        assert abs(weights_after["alpha"] - 0.5) < 0.01
        assert abs(weights_after["beta"] - 0.3) < 0.01
        assert abs(weights_after["gamma"] - 0.2) < 0.01
        # 应该与更新前不同
        assert weights_after != weights_before

    @pytest.mark.asyncio
    async def test_reset_custom(self, online_service):
        """TC12: 重置为自定义权重"""
        custom = {"alpha": 0.6, "beta": 0.3, "gamma": 0.1}
        online_service.reset_weights(custom)

        weights = online_service.get_weight_optimizer().get_weights()
        assert abs(weights["alpha"] - 0.6) < 0.01
        assert abs(weights["beta"] - 0.3) < 0.01
        assert abs(weights["gamma"] - 0.1) < 0.01


# ═══════════════════════════════════════════════════════════════════
# 测试: Pipeline
# ═══════════════════════════════════════════════════════════════════


class TestPipeline:
    """测试 OnlineLearningPipeline。"""

    def test_pipeline_initialization(self):
        """TC13: 管道初始化"""
        from scripts.online_learning_pipeline import OnlineLearningPipeline, DEFAULT_MODEL_DIR

        pipeline = OnlineLearningPipeline()
        assert pipeline.min_feedback == 20
        assert pipeline.retrain_threshold == 200
        assert pipeline.weights_only is False

    def test_pipeline_custom_config(self):
        """TC14: 自定义配置"""
        from scripts.online_learning_pipeline import OnlineLearningPipeline

        pipeline = OnlineLearningPipeline(
            min_feedback=10,
            retrain_threshold=100,
            weights_only=True,
            lookback_hours=24,
        )
        assert pipeline.min_feedback == 10
        assert pipeline.retrain_threshold == 100
        assert pipeline.weights_only is True
        assert pipeline.lookback_hours == 24

    @pytest.mark.asyncio
    async def test_global_singleton(self, online_service):
        """TC15: 全局单例"""
        from app.services.online_learning_service import (
            get_online_learning_service, reset_online_learning_service,
        )

        svc1 = get_online_learning_service()
        svc2 = get_online_learning_service()

        assert svc1 is svc2  # 同一个实例

        reset_online_learning_service()
        svc3 = get_online_learning_service()
        assert svc3 is not svc2  # 重置后是新实例


# ═══════════════════════════════════════════════════════════════════
# 测试: 管道报告
# ═══════════════════════════════════════════════════════════════════


class TestPipelineReport:
    """测试 PipelineReport 数据模型。"""

    def test_default_report(self):
        """TC16: 默认报告"""
        from scripts.online_learning_pipeline import PipelineReport

        report = PipelineReport()
        assert report.status == "success"
        assert report.pipeline_version == "1.0.0"
        assert report.feedback_records_processed == 0
        assert report.retrain_triggered is False

    def test_report_serialization(self):
        """TC17: 报告 JSON 序列化"""
        from scripts.online_learning_pipeline import PipelineReport
        from dataclasses import asdict

        report = PipelineReport(
            status="success",
            feedback_records_processed=50,
            weights_before={"alpha": 0.5, "beta": 0.3, "gamma": 0.2},
            weights_after={"alpha": 0.52, "beta": 0.28, "gamma": 0.2},
            weight_changes={"alpha": 0.02, "beta": -0.02, "gamma": 0.0},
        )

        data = asdict(report)
        assert data["status"] == "success"
        assert data["feedback_records_processed"] == 50
        assert data["weights_after"]["alpha"] == 0.52

        # 确认可 JSON 序列化
        json_str = json.dumps(data, ensure_ascii=False)
        assert '"status": "success"' in json_str


# ═══════════════════════════════════════════════════════════════════
# 执行入口
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
