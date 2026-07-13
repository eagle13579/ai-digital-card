"""
AI数字名片 用户反馈服务 (❤️/👎 闭环)
=====================================
提供 👍(like) / 👎(dislike) / 跳过(skip) 的反馈收集与权重影响。

权重规则:
  - like:   +1 (提升推荐权重)
  - dislike: -1 (降低推荐权重)
  - skip:    +0 (不影响权重，但记录行为)

架构:
  1. FeedbackService 是 FeedbackLoop (app/ai/feedback_loop.py) 的轻量封装
  2. 使用 FeedbackLoop 的 SQLite 持久化存储
  3. 反馈数据影响 FeedbackLoop.get_feedback_boost() 输出的权重乘数
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from app.ai.feedback_loop import FeedbackLoop, get_feedback_loop, RatingStats

logger = logging.getLogger(__name__)


# ======================================================================
# 枚举 / 数据模型
# ======================================================================


class FeedbackAction(str, Enum):
    """用户反馈动作"""
    LIKE = "like"       # 👍 点赞
    DISLIKE = "dislike"  # 👎 不喜欢
    SKIP = "skip"       # 跳过/忽略


@dataclass
class FeedbackResult:
    """单次反馈处理结果"""
    recommendation_id: str = ""
    user_id: int = 0
    content_id: int = 0
    action: str = ""
    weight_delta: int = 0       # 权重变化: +1 / -1 / 0
    current_boost: float = 1.0  # 当前权重乘数
    message: str = ""


@dataclass
class FeedbackSummary:
    """用户对某内容的反馈汇总"""
    total_feedback: int = 0
    like_count: int = 0
    dislike_count: int = 0
    skip_count: int = 0
    current_boost: float = 1.0


# ======================================================================
# 反馈服务
# ======================================================================


class FeedbackService:
    """用户反馈服务

    轻量封装 FeedbackLoop，提供 👍/👎/skip 语义化 API。

    用法:
        svc = FeedbackService()
        svc.record_feedback(user_id=1, content_id=42, action="like")
        boost = svc.get_weight_adjustment(user_id=1, content_id=42)
    """

    # 权重影响映射
    ACTION_WEIGHT_MAP = {
        FeedbackAction.LIKE: 1,      # 👍 +1
        FeedbackAction.DISLIKE: -1,  # 👎 -1
        FeedbackAction.SKIP: 0,      # 跳过 +0
    }

    def __init__(self, db_path: Optional[str] = None):
        self._loop: FeedbackLoop = get_feedback_loop(db_path)

    def record_feedback(
        self,
        user_id: int,
        content_id: int,
        action: str,
        source: str = "recommend",
        recommendation_id: str = "",
    ) -> FeedbackResult:
        """记录用户反馈

        Args:
            user_id: 当前用户 ID
            content_id: 被推荐的内容/用户 ID
            action: "like" | "dislike" | "skip"
            source: 反馈来源 (recommend / discover / similar)
            recommendation_id: 推荐记录 ID (可选, 用于追踪)

        Returns:
            FeedbackResult
        """
        # 标准化 action
        try:
            act = FeedbackAction(action.lower())
        except ValueError:
            raise ValueError(f"不支持的反馈动作: {action}，可选: like, dislike, skip")

        weight_delta = self.ACTION_WEIGHT_MAP[act]

        # 映射到 FeedbackLoop 的 rating 值
        # like -> rating=1, dislike -> rating=-1, skip -> rating=0
        rating_map = {
            FeedbackAction.LIKE: 1,
            FeedbackAction.DISLIKE: -1,
            FeedbackAction.SKIP: 0,
        }
        rating = rating_map[act]

        # 通过 FeedbackLoop 记录
        self._loop.record_feedback(
            user_id=user_id,
            item_id=content_id,
            rating=rating,
            source=source,
        )

        current_boost = self._loop.get_feedback_boost(user_id, content_id)

        # 友善提示
        messages = {
            FeedbackAction.LIKE: "感谢点赞 👍，我们会推荐更多类似内容",
            FeedbackAction.DISLIKE: "已记录 👎，我们将优化推荐",
            FeedbackAction.SKIP: "已跳过，下次推荐将调整",
        }

        logger.info(
            "反馈记录: user=%d content=%d action=%s weight_delta=%+d boost=%.4f",
            user_id, content_id, act.value, weight_delta, current_boost,
        )

        return FeedbackResult(
            recommendation_id=recommendation_id,
            user_id=user_id,
            content_id=content_id,
            action=act.value,
            weight_delta=weight_delta,
            current_boost=round(current_boost, 4),
            message=messages[act],
        )

    def get_weight_adjustment(self, user_id: int, content_id: int) -> float:
        """获取反馈权重乘数

        返回 [0.6, 1.5] 范围的值，用于调整推荐分数。
        1.0 = 中性，>1.0 = 加权，<1.0 = 降权。

        Args:
            user_id: 当前用户 ID
            content_id: 被推荐内容/用户 ID

        Returns:
            float: 权重乘数
        """
        return self._loop.get_feedback_boost(user_id, content_id)

    def apply_feedback_boost(
        self,
        user_id: int,
        content_id: int,
        base_score: float,
    ) -> float:
        """将反馈权重应用到推荐分数

        Args:
            user_id: 当前用户 ID
            content_id: 被推荐内容/用户 ID
            base_score: 原始推荐分数

        Returns:
            float: 调整后的分数
        """
        boost = self.get_weight_adjustment(user_id, content_id)
        return base_score * boost

    def get_user_feedback_summary(
        self,
        user_id: int,
        content_id: int,
    ) -> FeedbackSummary:
        """获取用户对某内容的反馈汇总

        Args:
            user_id: 用户 ID
            content_id: 被推荐内容/用户 ID

        Returns:
            FeedbackSummary
        """
        stats: RatingStats = self._loop.get_user_item_stats(user_id, content_id)
        return FeedbackSummary(
            total_feedback=stats.total_feedback,
            like_count=stats.positive_count,
            dislike_count=stats.negative_count,
            skip_count=stats.total_feedback - stats.positive_count - stats.negative_count,
            current_boost=stats.boost_factor,
        )

    def trigger_weight_adjustment(self) -> int:
        """手动触发权重调整

        Returns:
            int: 更新的权重记录数
        """
        return self._loop.trigger_adjustment()

    def get_global_stats(self) -> dict[str, Any]:
        """获取全局反馈统计"""
        return self._loop.get_global_stats()


# ======================================================================
# 全局单例
# ======================================================================

_service: Optional[FeedbackService] = None


def get_feedback_service(db_path: Optional[str] = None) -> FeedbackService:
    """获取全局 FeedbackService 单例"""
    global _service
    if _service is None:
        _service = FeedbackService(db_path)
    return _service
