"""
AI数字名片 推荐服务
===================
提供推荐相关的业务逻辑、数据模型和服务编排。

反馈数据模型:
  - FeedbackRecommendation: 推荐反馈记录 (recommendation_id, user_id, content_id, action, timestamp)
  - 权重影响: like+1, dislike-1, skip+0
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.recommendation import RecommendEngine, RecommendResult
from app.services.feedback_service import (
    FeedbackResult,
    FeedbackSummary,
    get_feedback_service,
)

logger = logging.getLogger(__name__)


# ======================================================================
# 反馈数据模型
# ======================================================================


@dataclass
class FeedbackRecommendation:
    """推荐反馈记录

    记录用户对某条推荐结果的反馈。

    Fields:
        recommendation_id: 推荐记录唯一标识 (可 UUID 或自增 ID)
        user_id:           反馈用户 ID
        content_id:        被推荐的内容/用户 ID
        action:            反馈动作: like / dislike / skip
        source:            来源: recommend / discover / similar
        timestamp:         反馈时间
    """
    recommendation_id: str = ""
    user_id: int = 0
    content_id: int = 0
    action: str = ""
    source: str = "recommend"
    timestamp: float = 0.0


# ======================================================================
# 推荐服务
# ======================================================================


class RecommendService:
    """推荐服务 - 集成推荐引擎 + 反馈闭环

    统一入口，协调:
      - RecommendEngine (多维评分)
      - FeedbackService (👍/👎 权重调整)
      - FeedbackLoop (持久化 + 权重微调)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._engine = RecommendEngine(db)
        self._feedback_service = get_feedback_service()

    async def personalize(
        self,
        user_id: int,
        top_k: int = 20,
        exclude_ids: Optional[list[int]] = None,
        strategy: str = "hybrid",
    ) -> RecommendResult:
        """个性化推荐 (自动集成反馈权重)

        Args:
            user_id: 目标用户 ID
            top_k: 返回数量
            exclude_ids: 排除的用户 ID 列表
            strategy: 推荐策略

        Returns:
            RecommendResult
        """
        return await self._engine.personalize_recommend(
            user_id=user_id,
            top_k=top_k,
            exclude_ids=exclude_ids,
            strategy=strategy,
        )

    async def discover(
        self,
        user_id: int,
        top_k: int = 30,
        purpose: Optional[str] = None,
    ) -> RecommendResult:
        """发现推荐 (自动集成反馈权重)"""
        return await self._engine.discover(
            user_id=user_id,
            top_k=top_k,
            purpose=purpose,
        )

    async def similar(
        self,
        target_user_id: int,
        current_user_id: int,
        top_k: int = 10,
    ) -> RecommendResult:
        """相似名片推荐 (自动集成反馈权重)"""
        return await self._engine.similar_users(
            target_user_id=target_user_id,
            current_user_id=current_user_id,
            top_k=top_k,
        )

    # ── 反馈方法 ────────────────────────────────────────────────

    def record_feedback(
        self,
        user_id: int,
        content_id: int,
        action: str,
        source: str = "recommend",
        recommendation_id: str = "",
    ) -> FeedbackResult:
        """记录反馈并影响推荐权重

        Args:
            user_id: 当前用户 ID
            content_id: 被推荐内容/用户 ID
            action: "like" | "dislike" | "skip"
            source: 反馈来源
            recommendation_id: 推荐记录 ID (可选)

        Returns:
            FeedbackResult
        """
        return self._feedback_service.record_feedback(
            user_id=user_id,
            content_id=content_id,
            action=action,
            source=source,
            recommendation_id=recommendation_id,
        )

    def get_weight_adjustment(self, user_id: int, content_id: int) -> float:
        """获取反馈权重乘数"""
        return self._feedback_service.get_weight_adjustment(user_id, content_id)

    def apply_feedback_boost(
        self,
        user_id: int,
        content_id: int,
        base_score: float,
    ) -> float:
        """应用反馈权重到推荐分数"""
        return self._feedback_service.apply_feedback_boost(user_id, content_id, base_score)

    def get_feedback_summary(self, user_id: int, content_id: int) -> FeedbackSummary:
        """获取用户对某内容的反馈汇总"""
        return self._feedback_service.get_user_feedback_summary(user_id, content_id)

    def get_global_feedback_stats(self) -> dict[str, Any]:
        """获取全局反馈统计"""
        return self._feedback_service.get_global_stats()

    def trigger_weight_adjustment(self) -> int:
        """手动触发权重调整"""
        return self._feedback_service.trigger_weight_adjustment()
