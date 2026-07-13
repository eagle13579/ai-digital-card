"""
AI数字名片 反馈服务测试
======================
测试 FeedbackService 升级版的新增功能。

测试范围:
  1. 向前兼容: record_feedback 同步API
  2. 异步API: record_feedback_async
  3. 动作支持: click / unlock / ignore / rate
  4. get_weight_adjustments: 特征级权重调整
  5. get_feedback_stats: 反馈统计数据
  6. 时间衰减计算
  7. 错误处理: 无效动作 / 缺少参数
"""

import os
import tempfile
import time
from typing import Generator

import pytest

from app.ai.feedback_loop import FeedbackLoop, get_feedback_loop
from app.services.feedback_service import (
    FeedbackAction,
    FeedbackResult,
    FeedbackService,
    FeedbackStats,
    get_feedback_service,
    reset_feedback_service,
)


# ======================================================================
# 辅助函数: 重置 FeedbackLoop 单例
# ======================================================================


def _reset_feedback_loop():
    """重置 FeedbackLoop 单例，确保每个测试使用独立的数据库"""
    FeedbackLoop._instance = None
    FeedbackLoop._weight_cache = {}
    FeedbackLoop._feedback_count = 0
    # 重置 get_feedback_loop 的模块级缓存
    import app.ai.feedback_loop as _fb_mod
    _fb_mod._engine = None


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def tmp_db_path() -> Generator[str, None, None]:
    """创建临时 SQLite 数据库路径"""
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test_feedback.db")
    yield db_path
    # 清理
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        os.rmdir(tmpdir)
    except (PermissionError, OSError):
        pass  # Windows 上可能有锁


@pytest.fixture
def service(tmp_db_path: str) -> Generator[FeedbackService, None, None]:
    """每次测试创建一个全新的 FeedbackService 实例"""
    # 完全重置所有单例
    reset_feedback_service()
    _reset_feedback_loop()
    svc = FeedbackService(db_path=tmp_db_path)
    yield svc
    reset_feedback_service()
    _reset_feedback_loop()


# ======================================================================
# 测试: 向前兼容
# ======================================================================


class TestBackwardCompatibility:
    """验证原 record_feedback 同步 API 仍可正常工作"""

    def test_record_feedback_like(self, service: FeedbackService):
        """record_feedback(action='like') 返回正确结果"""
        result = service.record_feedback(
            user_id=1, content_id=42, action="like", source="recommend"
        )
        assert isinstance(result, FeedbackResult)
        assert result.user_id == 1
        assert result.content_id == 42
        assert result.action == "like"
        assert result.weight_delta == 1.0
        assert 0.6 <= result.current_boost <= 1.5
        assert "点赞" in result.message

    def test_record_feedback_dislike(self, service: FeedbackService):
        """record_feedback(action='dislike') 返回降权结果"""
        result = service.record_feedback(
            user_id=1, content_id=99, action="dislike", source="discover"
        )
        assert result.action == "dislike"
        assert result.weight_delta == -1.0
        assert "记录" in result.message

    def test_record_feedback_skip(self, service: FeedbackService):
        """record_feedback(action='skip') 权重不变"""
        result = service.record_feedback(
            user_id=1, content_id=55, action="skip"
        )
        assert result.action == "skip"
        assert result.weight_delta == 0.0

    def test_get_weight_adjustment_backward(self, service: FeedbackService):
        """get_weight_adjustment 向后兼容"""
        # 记录一个 like
        service.record_feedback(user_id=1, content_id=42, action="like")
        boost = service.get_weight_adjustment(user_id=1, content_id=42)
        assert isinstance(boost, float)
        assert 0.6 <= boost <= 1.5

    def test_apply_feedback_boost(self, service: FeedbackService):
        """apply_feedback_boost 向后兼容"""
        service.record_feedback(user_id=1, content_id=42, action="like")
        adjusted = service.apply_feedback_boost(
            user_id=1, content_id=42, base_score=10.0
        )
        assert isinstance(adjusted, float)
        assert adjusted >= 6.0  # 0.6 * 10 = 6


# ======================================================================
# 测试: 异步 API
# ======================================================================


class TestRecordFeedbackAsync:
    """测试新的异步 record_feedback_async API"""

    @pytest.mark.asyncio
    async def test_record_click(self, service: FeedbackService):
        """async record_feedback_async(action='click') 返回正确结果"""
        result = await service.record_feedback_async(
            user_id=1, match_id=42, action="click", source="match"
        )
        assert isinstance(result, FeedbackResult)
        assert result.user_id == 1
        assert result.content_id == 42
        assert result.action == "click"
        assert result.weight_delta == 0.3
        assert "点击" in result.message

    @pytest.mark.asyncio
    async def test_record_unlock(self, service: FeedbackService):
        """async record_feedback_async(action='unlock') 显著加权"""
        result = await service.record_feedback_async(
            user_id=1, match_id=42, action="unlock", source="match"
        )
        assert result.action == "unlock"
        assert result.weight_delta == 0.8
        assert "解锁" in result.message

    @pytest.mark.asyncio
    async def test_record_ignore(self, service: FeedbackService):
        """async record_feedback_async(action='ignore') 降权"""
        result = await service.record_feedback_async(
            user_id=1, match_id=42, action="ignore"
        )
        assert result.action == "ignore"
        assert result.weight_delta == -0.4
        assert "忽略" in result.message

    @pytest.mark.asyncio
    async def test_record_rate(self, service: FeedbackService):
        """async record_feedback_async(action='rate', score=4.5) 按比例调整"""
        result = await service.record_feedback_async(
            user_id=1, match_id=42, action="rate", score=4.5
        )
        assert result.action == "rate"
        # (4.5 - 3.0) / 2.0 = 0.75
        assert result.weight_delta == pytest.approx(0.75, abs=0.01)
        assert "评分" in result.message

    @pytest.mark.asyncio
    async def test_record_rate_low_score(self, service: FeedbackService):
        """评分 1 分 → 负权重调整"""
        result = await service.record_feedback_async(
            user_id=1, match_id=42, action="rate", score=1.0
        )
        assert result.weight_delta == pytest.approx(-1.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_record_rate_neutral(self, service: FeedbackService):
        """评分 3 分 → 中性"""
        result = await service.record_feedback_async(
            user_id=1, match_id=42, action="rate", score=3.0
        )
        assert result.weight_delta == pytest.approx(0.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_record_feedback_idempotent(self, service: FeedbackService):
        """同一用户-匹配对多次记录不会抛异常"""
        for _ in range(3):
            result = await service.record_feedback_async(
                user_id=1, match_id=42, action="click"
            )
            assert isinstance(result, FeedbackResult)


# ======================================================================
# 测试: 特征级权重调整
# ======================================================================


class TestWeightAdjustments:
    """测试 get_weight_adjustments 返回特征级权重调整"""

    @pytest.mark.asyncio
    async def test_weight_adjustments_returns_dict(self, service: FeedbackService):
        """get_weight_adjustments 返回 dict"""
        adjustments = await service.get_weight_adjustments(user_id=1)
        assert isinstance(adjustments, dict)

    @pytest.mark.asyncio
    async def test_click_adds_tag_match_weight(self, service: FeedbackService):
        """点击动作 → tag_match 加权"""
        await service.record_feedback_async(user_id=1, match_id=42, action="click")
        adjustments = await service.get_weight_adjustments(user_id=1)
        assert "tag_match" in adjustments
        assert adjustments["tag_match"] > 0

    @pytest.mark.asyncio
    async def test_unlock_strongly_boosts(self, service: FeedbackService):
        """解锁动作 → tag_match 显著加权"""
        await service.record_feedback_async(user_id=1, match_id=42, action="unlock")
        adjustments = await service.get_weight_adjustments(user_id=1)
        assert "tag_match" in adjustments
        # unlock 的 tag_match 影响是 0.25
        assert adjustments["tag_match"] >= 0.20

    @pytest.mark.asyncio
    async def test_ignore_reduces_weight(self, service: FeedbackService):
        """忽略动作 → tag_match 降权"""
        await service.record_feedback_async(user_id=1, match_id=42, action="ignore")
        adjustments = await service.get_weight_adjustments(user_id=1)
        assert "tag_match" in adjustments
        assert adjustments["tag_match"] < 0

    @pytest.mark.asyncio
    async def test_multiple_actions_accumulate(self, service: FeedbackService):
        """多个动作累积影响特征权重"""
        await service.record_feedback_async(user_id=1, match_id=10, action="click")
        await service.record_feedback_async(user_id=1, match_id=20, action="unlock")
        await service.record_feedback_async(user_id=1, match_id=30, action="click")

        adjustments = await service.get_weight_adjustments(user_id=1)
        assert "tag_match" in adjustments
        assert "semantic" in adjustments
        assert "graph" in adjustments
        # tag_match: click(+0.10) + unlock(+0.25) + click(+0.10) = 累积
        # 每次衰减 10%: 0.10 + 0.25*0.9 + 0.10*0.9*0.9
        # = 0.10 + 0.225 + 0.081 = 0.406
        # 用近似值
        assert 0.30 <= adjustments["tag_match"] <= 0.50

    @pytest.mark.asyncio
    async def test_weight_adjustments_clamped(self, service: FeedbackService):
        """权重调整被限制在 [-0.8, 0.8] 范围内"""
        # 多次 unlock (每次 +0.25 tag_match)
        for _ in range(20):
            await service.record_feedback_async(
                user_id=1, match_id=42, action="unlock"
            )
        adjustments = await service.get_weight_adjustments(user_id=1)
        for feature, value in adjustments.items():
            assert -0.8 <= value <= 0.8, f"{feature}={value} 超出范围"


# ======================================================================
# 测试: 反馈统计
# ======================================================================


class TestFeedbackStats:
    """测试 get_feedback_stats 返回详细统计"""

    @pytest.mark.asyncio
    async def test_stats_basic_structure(self, service: FeedbackService):
        """get_feedback_stats 返回正确结构"""
        stats = await service.get_feedback_stats(user_id=1)
        assert isinstance(stats, FeedbackStats)
        assert stats.total_records == 0
        assert stats.action_breakdown == {}
        assert stats.recent_activity == 0

    @pytest.mark.asyncio
    async def test_stats_counts_actions(self, service: FeedbackService):
        """统计正确反映各动作数量"""
        await service.record_feedback_async(user_id=1, match_id=10, action="click")
        await service.record_feedback_async(user_id=1, match_id=20, action="unlock")
        await service.record_feedback_async(user_id=1, match_id=30, action="ignore")
        await service.record_feedback_async(user_id=1, match_id=40, action="rate", score=4.0)

        stats = await service.get_feedback_stats(user_id=1)
        assert stats.total_records == 4
        assert stats.total_click >= 1
        assert stats.total_rate >= 1
        assert stats.top_matched_users != []

    @pytest.mark.asyncio
    async def test_stats_top_matched_users(self, service: FeedbackService):
        """top_matched_users 返回所有互动的用户"""
        # 针对不同的 match_id 各记录一次（FeedbackLoop UPSERT 防止重复计数）
        for match_id in [10, 20, 30, 40]:
            await service.record_feedback_async(
                user_id=1, match_id=match_id, action="click"
            )
        stats = await service.get_feedback_stats(user_id=1)
        assert len(stats.top_matched_users) >= 1
        # 所有 match_id 都在 top 列表中
        matched_ids = [u["user_id"] for u in stats.top_matched_users]
        for mid in [10, 20, 30, 40]:
            assert mid in matched_ids

    @pytest.mark.asyncio
    async def test_stats_recent_activity(self, service: FeedbackService):
        """recent_activity 统计近7天反馈"""
        # 记录一条反馈 (当前时间)
        await service.record_feedback_async(user_id=1, match_id=42, action="click")
        stats = await service.get_feedback_stats(user_id=1)
        assert stats.recent_activity >= 1

    @pytest.mark.asyncio
    async def test_stats_weight_adjustments_included(self, service: FeedbackService):
        """统计中包含当前特征权重调整"""
        await service.record_feedback_async(user_id=1, match_id=42, action="click")
        await service.record_feedback_async(user_id=1, match_id=42, action="unlock")

        stats = await service.get_feedback_stats(user_id=1)
        assert isinstance(stats.weight_adjustments, dict)
        assert len(stats.weight_adjustments) > 0


# ======================================================================
# 测试: 时间衰减
# ======================================================================


class TestTimeDecay:
    """测试时间衰减计算"""

    def test_compute_decay_zero_days(self, service: FeedbackService):
        """0 天 → decay=1.0 (无衰减)"""
        decay = FeedbackService._compute_decay(0.0)
        assert decay == pytest.approx(1.0, abs=0.01)

    def test_compute_decay_half_life(self, service: FeedbackService):
        """半衰期 7 天 → decay≈0.5"""
        decay = FeedbackService._compute_decay(7.0)
        assert decay == pytest.approx(0.5, abs=0.05)

    def test_compute_decay_one_day(self, service: FeedbackService):
        """1 天 → decay≈0.9"""
        decay = FeedbackService._compute_decay(1.0)
        assert decay == pytest.approx(0.905, abs=0.02)

    def test_compute_decay_30_days(self, service: FeedbackService):
        """30 天 → decay≈0.05 (远期行为影响很小)"""
        decay = FeedbackService._compute_decay(30.0)
        assert decay <= 0.1  # 30天后不到 10%

    def test_compute_decay_monotonic(self, service: FeedbackService):
        """衰减函数单调递减"""
        decays = [FeedbackService._compute_decay(d) for d in [0, 1, 3, 7, 14, 30]]
        for i in range(len(decays) - 1):
            assert decays[i] >= decays[i + 1]


# ======================================================================
# 测试: 错误处理
# ======================================================================


class TestErrorHandling:
    """测试错误处理"""

    def test_invalid_action_sync(self, service: FeedbackService):
        """无效动作 → ValueError"""
        with pytest.raises(ValueError, match="不支持的反馈动作"):
            service.record_feedback(
                user_id=1, content_id=42, action="invalid_action"
            )

    @pytest.mark.asyncio
    async def test_invalid_action_async(self, service: FeedbackService):
        """无效动作 → ValueError (异步版本)"""
        with pytest.raises(ValueError, match="不支持的反馈动作"):
            await service.record_feedback_async(
                user_id=1, match_id=42, action="bad_action"
            )

    @pytest.mark.asyncio
    async def test_rate_without_score(self, service: FeedbackService):
        """rate 动作缺少 score → ValueError"""
        with pytest.raises(ValueError, match="必须提供 score"):
            await service.record_feedback_async(
                user_id=1, match_id=42, action="rate"
            )

    @pytest.mark.asyncio
    async def test_rate_score_out_of_range(self, service: FeedbackService):
        """rate 动作 score 超出范围 → ValueError"""
        with pytest.raises(ValueError, match="评分值必须在"):
            await service.record_feedback_async(
                user_id=1, match_id=42, action="rate", score=6.0
            )

    @pytest.mark.asyncio
    async def test_rate_score_negative(self, service: FeedbackService):
        """rate 动作 score 为负数 → ValueError"""
        with pytest.raises(ValueError, match="评分值必须在"):
            await service.record_feedback_async(
                user_id=1, match_id=42, action="rate", score=-1.0
            )

    @pytest.mark.asyncio
    async def test_action_case_insensitive(self, service: FeedbackService):
        """动作大小写不敏感"""
        result = await service.record_feedback_async(
            user_id=1, match_id=42, action="CLICK"
        )
        assert result.action == "click"

        result = await service.record_feedback_async(
            user_id=1, match_id=42, action="Like"
        )
        assert result.action == "like"


# ======================================================================
# 测试: 单例模式
# ======================================================================


class TestSingleton:
    """测试 get_feedback_service 单例"""

    def test_get_feedback_service_singleton(self, tmp_db_path: str):
        """get_feedback_service 返回同一个实例"""
        reset_feedback_service()
        svc1 = get_feedback_service(tmp_db_path)
        svc2 = get_feedback_service(tmp_db_path)
        assert svc1 is svc2
        reset_feedback_service()

    def test_reset_feedback_service(self, tmp_db_path: str):
        """reset_feedback_service 后获取新实例"""
        reset_feedback_service()
        svc1 = get_feedback_service(tmp_db_path)
        reset_feedback_service()
        svc2 = get_feedback_service(tmp_db_path)
        assert svc1 is not svc2
        reset_feedback_service()


# ======================================================================
# 测试: 集成场景
# ======================================================================


class TestIntegration:
    """真实使用场景集成测试"""

    @pytest.mark.asyncio
    async def test_match_engine_feedback_loop(self, service: FeedbackService):
        """模拟匹配引擎的反馈闭环流程"""
        # Step 1: 用户看到推荐结果 (用不同 match_id 避免 UPSERT 合并)
        result = await service.record_feedback_async(
            user_id=1, match_id=100, action="click"
        )
        assert result.weight_delta == 0.3

        # Step 2: 用户查看另一个推荐详情后非常喜欢，解锁联系方式
        result = await service.record_feedback_async(
            user_id=1, match_id=101, action="unlock"
        )
        assert result.weight_delta == 0.8

        # Step 3: 又一个推荐被忽略
        result = await service.record_feedback_async(
            user_id=1, match_id=200, action="ignore"
        )
        assert result.weight_delta == -0.4

        # Step 4: 给另一个推荐打分
        result = await service.record_feedback_async(
            user_id=1, match_id=300, action="rate", score=5.0
        )
        assert result.weight_delta == pytest.approx(1.0, abs=0.01)

        # Step 5: 获取权重调整
        adjustments = await service.get_weight_adjustments(user_id=1)
        assert "tag_match" in adjustments
        assert adjustments["tag_match"] > 0.20

        # Step 6: 获取统计
        stats = await service.get_feedback_stats(user_id=1)
        assert stats.total_records >= 4
        # 最常互动的用户 (超过1次互动的)
        assert len(stats.top_matched_users) >= 4
