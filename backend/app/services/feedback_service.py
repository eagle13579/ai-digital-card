"""
AI数字名片 用户反馈服务 (闭环升级版)
=======================================
提供用户行为反馈接入匹配引擎，实现"越用越准"的个性化推荐。

支持的反馈动作:
  - click:   点击查看详情 → 对应匹配特征加权 (+0.3)
  - unlock:  解锁联系方式 → 强烈兴趣信号 → 显著加权 (+0.8)
  - ignore:  忽略/跳过 → 对应特征减权 (-0.4)
  - rate:    评分(1-5) → 按比例线性调整

核心特性:
  1. async/await 异步 API (record_feedback_async, get_weight_adjustments, get_feedback_stats)
  2. 时间衰减：近期行为权重更高（指数衰减模型）
  3. 特征级权重调整：返回该用户的个性化权重调整字典
  4. 向前兼容：保留原 record_feedback 同步 API（like/dislike/skip）

权重规则:
  - click:   对应的匹配特征加权
  - unlock:  对应特征显著加权（强烈兴趣信号）
  - ignore:  对应特征减权（负信号）
  - rate:    评分按比例调整 (score-3)/2 映射到 [-1.0, 1.0]

时间衰减:
  weight_effective = weight * exp(-decay_rate * days_elapsed)
  默认半衰期 7 天 (decay_rate = ln2 / 7 ≈ 0.099)

特征级权重调整:
  根据用户行为动态调整 tag_match / semantic / graph 三个维度的权重。
  get_weight_adjustments(user_id) 返回匹配引擎可直接使用的调整字典。
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from app.ai.feedback_loop import FeedbackLoop, get_feedback_loop, RatingStats

logger = logging.getLogger(__name__)


# ======================================================================
# 枚举 / 数据模型
# ======================================================================


class FeedbackAction(str, Enum):
    """用户反馈动作 (扩展版)"""
    # ── 原有动作 (向前兼容) ──
    LIKE = "like"           # 👍 点赞
    DISLIKE = "dislike"     # 👎 不喜欢
    SKIP = "skip"           # 跳过/忽略

    # ── 新增动作 (匹配引擎行为) ──
    CLICK = "click"         # 👆 点击查看详情
    UNLOCK = "unlock"       # 🔓 解锁联系方式
    IGNORE = "ignore"       # ⏭ 忽略推荐
    RATE = "rate"           # ⭐ 评分 (1-5)


@dataclass
class FeedbackResult:
    """单次反馈处理结果"""
    recommendation_id: str = ""
    user_id: int = 0
    content_id: int = 0
    action: str = ""
    weight_delta: float = 0.0      # 权重变化
    current_boost: float = 1.0     # 当前权重乘数
    message: str = ""


@dataclass
class FeedbackSummary:
    """用户对某内容的反馈汇总"""
    total_feedback: int = 0
    like_count: int = 0
    dislike_count: int = 0
    skip_count: int = 0
    click_count: int = 0
    unlock_count: int = 0
    ignore_count: int = 0
    rate_count: int = 0
    avg_rating: float = 0.0
    current_boost: float = 1.0


@dataclass
class FeatureWeightAdjustment:
    """特征级权重调整记录"""
    feature_name: str = ""          # 特征名 (如 tag_name)
    weight_delta: float = 0.0       # 权重变化量
    confidence: float = 0.0         # 置信度 (基于数据量)
    last_updated: float = 0.0       # 最后一次更新时间


@dataclass
class FeedbackStats:
    """用户反馈统计数据"""
    total_records: int = 0
    action_breakdown: dict[str, int] = field(default_factory=dict)
    total_click: int = 0
    total_unlock: int = 0
    total_ignore: int = 0
    total_rate: int = 0
    avg_rating_score: float = 0.0
    click_ratio: float = 0.0        # 点击率 (click / total)
    unlock_ratio: float = 0.0       # 解锁率
    ignore_ratio: float = 0.0       # 忽略率
    recent_activity: int = 0        # 最近7天反馈数
    top_matched_users: list[dict] = field(default_factory=list)  # 最常互动的用户
    weight_adjustments: dict[str, float] = field(default_factory=dict)


# ======================================================================
# 反馈服务 (升级版)
# ======================================================================


class FeedbackService:
    """用户反馈服务（闭环升级版）

    在原 FeedbackService 基础上增加:
      - async record_feedback_async()   异步记录 (支持 click/unlock/ignore/rate)
      - async get_weight_adjustments()  返回用户级特征权重调整
      - async get_feedback_stats()      返回详细统计
      - 时间衰减模型 (指数衰减, 半衰期7天)
      - click/unlock/ignore/rate 新动作支持

    【向前兼容】
      - record_feedback() 仍是同步方法，保留原 like/dislike/skip API
      - recommend.py 和 recommend_service.py 调用无需修改

    用法:
        svc = FeedbackService()

        # 新异步API (本任务新增)
        result = await svc.record_feedback_async(
            user_id=1, match_id=42, action="click"
        )
        adjustments = await svc.get_weight_adjustments(user_id=1)
        stats = await svc.get_feedback_stats(user_id=1)

        # 原同步API (向前兼容)
        result = svc.record_feedback(user_id=1, content_id=42, action="like")
    """

    # ── 权重影响映射 ──
    # 每个动作对应的"匹配特征权重变化量"
    ACTION_WEIGHT_MAP: dict[FeedbackAction, float] = {
        FeedbackAction.LIKE: 1.0,           # 👍 +1.0 (加权)
        FeedbackAction.DISLIKE: -1.0,       # 👎 -1.0 (降权)
        FeedbackAction.SKIP: 0.0,           # 跳过 +0
        FeedbackAction.CLICK: 0.3,          # 👆 点击 +0.3
        FeedbackAction.UNLOCK: 0.8,         # 🔓 解锁 +0.8 (强信号)
        FeedbackAction.IGNORE: -0.4,        # ⏭ 忽略 -0.4
        FeedbackAction.RATE: 0.0,           # ⭐ 评分: 由 score 参数决定
    }

    # ── 时间衰减配置 ──
    DECAY_HALF_LIFE_DAYS: float = 7.0      # 半衰期 7 天
    DECAY_RATE: float = 0.693 / 7.0        # ln2 / half_life ≈ 0.099

    # ── 特征级权重配置 ──
    # 每种动作影响的"特征维度"权重调整量
    FEATURE_IMPACT_MAP: dict[FeedbackAction, dict[str, float]] = {
        FeedbackAction.LIKE: {"tag_match": 0.15, "semantic": 0.05},
        FeedbackAction.DISLIKE: {"tag_match": -0.20, "semantic": -0.10},
        FeedbackAction.CLICK: {"tag_match": 0.10, "semantic": 0.10, "graph": 0.05},
        FeedbackAction.UNLOCK: {"tag_match": 0.25, "semantic": 0.15, "graph": 0.20},
        FeedbackAction.IGNORE: {"tag_match": -0.15, "semantic": -0.05, "graph": -0.05},
        FeedbackAction.RATE: {"tag_match": 0.10, "semantic": 0.05, "graph": 0.05},
    }

    def __init__(self, db_path: Optional[str] = None):
        self._loop: FeedbackLoop = get_feedback_loop(db_path)
        # 内存中缓存用户级特征权重调整
        # { "user_id": { "feature_name": adjustment_value } }
        self._feature_weights: dict[int, dict[str, float]] = {}
        # 最后一次加载时间
        self._last_load_time: float = 0.0
        # 缓存 TTL (秒)
        self._cache_ttl: float = 300.0  # 5 分钟

    # ══════════════════════════════════════════════════════════════
    # 异步主 API (本任务新增)
    # ══════════════════════════════════════════════════════════════

    async def record_feedback_async(
        self,
        user_id: int,
        match_id: int,
        action: str,
        score: Optional[float] = None,
        source: str = "recommend",
        recommendation_id: str = "",
    ) -> FeedbackResult:
        """[异步] 记录用户行为反馈

        升级版: 支持 click / unlock / ignore / rate 等匹配引擎行为。

        Args:
            user_id: 当前用户 ID
            match_id: 匹配目标用户 ID
            action: 反馈动作
                "click"  - 点击查看详情
                "unlock" - 解锁联系方式
                "ignore" - 忽略推荐
                "rate"   - 评分 (需同时传 score)
                "like"/"dislike"/"skip" - 原有动作 (向前兼容)
            score: 评分值 (仅 rate 动作需要, 1.0-5.0)
            source: 反馈来源 (recommend / discover / similar / match)
            recommendation_id: 推荐记录 ID (可选)

        Returns:
            FeedbackResult

        Raises:
            ValueError: action 不合法或缺少必要参数
        """
        return await asyncio.to_thread(
            self._record_feedback_internal,
            user_id=user_id,
            match_id=match_id,
            action=action,
            score=score,
            source=source,
            recommendation_id=recommendation_id,
        )

    async def get_weight_adjustments(self, user_id: int) -> dict[str, float]:
        """获取该用户的个性化特征权重调整

        返回特征级权重调整字典，供匹配引擎使用:
        {
            "tag_match": 0.15,    # 标签匹配加权
            "semantic": 0.05,     # 语义匹配加权
            "graph": -0.02,       # 图谱匹配降权
        }

        权重基于用户历史行为计算，应用时间衰减：
        - 近期行为 (7天内): 权重全量计入
        - 远期行为 (30天前): 权重衰减至约 5%

        Args:
            user_id: 用户 ID

        Returns:
            dict[str, float]: 特征名 -> 权重调整量 (范围 [-0.8, 0.8])
        """
        await self._ensure_feature_weights_loaded(user_id)
        return self._feature_weights.get(user_id, {}).copy()

    async def get_feedback_stats(self, user_id: int) -> FeedbackStats:
        """获取用户的反馈统计数据

        包含:
        - total_records: 总反馈条数
        - action_breakdown: 各动作数量
        - click/unlock/ignore/rate 细项统计
        - click_ratio / unlock_ratio / ignore_ratio: 行为比率
        - recent_activity: 近7天活跃度
        - top_matched_users: 最常互动的用户
        - weight_adjustments: 当前特征权重调整

        Args:
            user_id: 用户 ID

        Returns:
            FeedbackStats
        """
        return await asyncio.to_thread(self._get_feedback_stats_internal, user_id)

    # ══════════════════════════════════════════════════════════════
    # 向前兼容 API (原 record_feedback 同步方法)
    # ══════════════════════════════════════════════════════════════

    def record_feedback(
        self,
        user_id: int,
        content_id: int,
        action: str,
        source: str = "recommend",
        recommendation_id: str = "",
    ) -> FeedbackResult:
        """[同步 · 向前兼容] 记录用户反馈

        保留原 like/dislike/skip 语义，供 recommend.py 等已有调用方使用。

        Args:
            user_id: 当前用户 ID
            content_id: 被推荐的内容/用户 ID
            action: "like" | "dislike" | "skip"
            source: 反馈来源 (recommend / discover / similar)
            recommendation_id: 推荐记录 ID (可选)

        Returns:
            FeedbackResult
        """
        return self._record_feedback_internal(
            user_id=user_id,
            match_id=content_id,
            action=action,
            score=None,
            source=source,
            recommendation_id=recommendation_id,
        )

    def get_weight_adjustment(self, user_id: int, content_id: int) -> float:
        """[同步 · 向前兼容] 获取单个匹配对的权重乘数

        Args:
            user_id: 当前用户 ID
            content_id: 被推荐内容/用户 ID

        Returns:
            float: 权重乘数 [0.6, 1.5]
        """
        return self._loop.get_feedback_boost(user_id, content_id)

    def apply_feedback_boost(
        self,
        user_id: int,
        content_id: int,
        base_score: float,
    ) -> float:
        """[同步 · 向前兼容] 将反馈权重应用到推荐分数"""
        boost = self.get_weight_adjustment(user_id, content_id)
        return base_score * boost

    def get_user_feedback_summary(
        self,
        user_id: int,
        content_id: int,
    ) -> FeedbackSummary:
        """[同步 · 向前兼容] 获取用户对某内容的反馈汇总"""
        stats: RatingStats = self._loop.get_user_item_stats(user_id, content_id)
        return FeedbackSummary(
            total_feedback=stats.total_feedback,
            like_count=stats.positive_count,
            dislike_count=stats.negative_count,
            skip_count=stats.total_feedback - stats.positive_count - stats.negative_count,
            current_boost=stats.boost_factor,
        )

    def trigger_weight_adjustment(self) -> int:
        """[同步 · 向前兼容] 手动触发权重调整"""
        return self._loop.trigger_adjustment()

    def get_global_stats(self) -> dict[str, Any]:
        """[同步 · 向前兼容] 获取全局反馈统计"""
        return self._loop.get_global_stats()

    # ══════════════════════════════════════════════════════════════
    # 同步核心实现 (在后台线程中运行)
    # ══════════════════════════════════════════════════════════════

    def _record_feedback_internal(
        self,
        user_id: int,
        match_id: int,
        action: str,
        score: Optional[float] = None,
        source: str = "recommend",
        recommendation_id: str = "",
    ) -> FeedbackResult:
        """内部实现: 记录用户反馈并更新特征权重"""
        # 1) 标准化 action
        try:
            act = FeedbackAction(action.lower())
        except ValueError:
            valid_actions = ", ".join(a.value for a in FeedbackAction)
            raise ValueError(
                f"不支持的反馈动作: {action}，可选: {valid_actions}"
            )

        # 2) 校验评分参数
        if act == FeedbackAction.RATE:
            if score is None:
                raise ValueError("评分动作 (rate) 必须提供 score 参数 (1.0-5.0)")
            score = float(score)
            if score < 1.0 or score > 5.0:
                raise ValueError(f"评分值必须在 1.0-5.0 之间, 收到: {score}")

        # 3) 计算权重变化量
        if act == FeedbackAction.RATE:
            # 评分: 以 3 分为基准，按比例映射到 [-1.0, 1.0]
            # 1分 -> -1.0, 2分 -> -0.5, 3分 -> 0.0, 4分 -> 0.5, 5分 -> 1.0
            weight_delta = (score - 3.0) / 2.0
        else:
            weight_delta = self.ACTION_WEIGHT_MAP.get(act, 0.0)

        # 4) 映射到 FeedbackLoop 的 rating 值 (向前兼容)
        rating = self._action_to_rating(act, score)

        # 5) 通过 FeedbackLoop 持久化
        try:
            self._loop.record_feedback(
                user_id=user_id,
                item_id=match_id,
                rating=rating,
                source=source,
            )
        except ValueError as e:
            raise ValueError(f"反馈记录失败: {e}")

        current_boost = self._loop.get_feedback_boost(user_id, match_id)

        # 6) 更新内存中的特征级权重缓存
        self._update_feature_weights(user_id, act, score)

        # 7) 友善提示
        message = self._build_message(act, weight_delta, current_boost)

        logger.info(
            "反馈记录 [升级版]: user=%d match=%d action=%s weight_delta=%.2f boost=%.4f",
            user_id, match_id, act.value, weight_delta, current_boost,
        )

        return FeedbackResult(
            recommendation_id=recommendation_id,
            user_id=user_id,
            content_id=match_id,
            action=act.value,
            weight_delta=round(weight_delta, 4),
            current_boost=round(current_boost, 4),
            message=message,
        )

    def _get_feedback_stats_internal(self, user_id: int) -> FeedbackStats:
        """内部实现: 获取用户反馈统计"""
        records = self._loop.get_user_feedback(user_id, limit=1000)

        total = len(records)
        click_count = 0
        unlock_count = 0
        ignore_count = 0
        rate_count = 0
        rating_sum = 0.0

        # 动作分解统计
        action_breakdown: dict[str, int] = {}
        # 用户互动统计
        user_interactions: dict[int, int] = {}

        now = time.time()
        recent_cutoff = now - 7 * 86400  # 7天前
        recent_count = 0

        for r in records:
            action_type = r.feedback_type
            action_breakdown[action_type] = action_breakdown.get(action_type, 0) + 1

            # 统计各动作
            if action_type == "like":
                click_count += 1
            elif action_type == "dislike":
                ignore_count += 1
            elif action_type == "rating":
                rating_val = abs(r.rating)
                if 1 <= rating_val <= 5:
                    rate_count += 1
                    rating_sum += rating_val
                elif rating_val == 1:
                    click_count += 1
                elif rating_val == 0:
                    ignore_count += 1

            # 统计解锁兴趣信号 (rating=1 且 feedback_type=like)
            if r.rating == 1 and r.feedback_type == "like":
                unlock_count += 1

            # 近7天活跃
            if r.created_at >= recent_cutoff:
                recent_count += 1

            # 用户互动频率
            user_interactions[r.item_id] = user_interactions.get(r.item_id, 0) + 1

        avg_rating = round(rating_sum / rate_count, 2) if rate_count > 0 else 0.0
        click_ratio = round(click_count / total, 4) if total > 0 else 0.0
        unlock_ratio = round(unlock_count / total, 4) if total > 0 else 0.0
        ignore_ratio = round(ignore_count / total, 4) if total > 0 else 0.0

        # 最常互动的 top-5 用户
        sorted_users = sorted(user_interactions.items(), key=lambda x: x[1], reverse=True)
        top_matched = [
            {"user_id": uid, "interaction_count": cnt}
            for uid, cnt in sorted_users[:5]
        ]

        # 当前特征权重调整
        weights = self._feature_weights.get(user_id, {})

        return FeedbackStats(
            total_records=total,
            action_breakdown=action_breakdown,
            total_click=click_count,
            total_unlock=unlock_count,
            total_ignore=ignore_count,
            total_rate=rate_count,
            avg_rating_score=avg_rating,
            click_ratio=click_ratio,
            unlock_ratio=unlock_ratio,
            ignore_ratio=ignore_ratio,
            recent_activity=recent_count,
            top_matched_users=top_matched,
            weight_adjustments=weights,
        )

    # ══════════════════════════════════════════════════════════════
    # 特征级权重管理
    # ══════════════════════════════════════════════════════════════

    def _update_feature_weights(
        self,
        user_id: int,
        action: FeedbackAction,
        score: Optional[float] = None,
    ) -> None:
        """根据用户动作更新特征级权重

        时间衰减: 每次更新时旧值衰减 10%，再加新动作影响。
        """
        if user_id not in self._feature_weights:
            self._feature_weights[user_id] = {}

        impact = self.FEATURE_IMPACT_MAP.get(action, {})

        for feature, delta in impact.items():
            current = self._feature_weights[user_id].get(feature, 0.0)

            if action == FeedbackAction.RATE and score is not None:
                # 评分: (score - 3) / 2 映射到 [-1, 1]
                effective_delta = delta * (score - 3.0) / 2.0
            else:
                effective_delta = delta

            # 应用时间衰减: 旧值衰减 10%
            decayed = current * 0.9
            new_value = decayed + effective_delta

            # 限制范围 [-0.8, 0.8]
            new_value = max(-0.8, min(0.8, new_value))
            self._feature_weights[user_id][feature] = round(new_value, 4)

        self._last_load_time = time.time()

    async def _ensure_feature_weights_loaded(self, user_id: int) -> None:
        """确保用户特征权重已加载（延迟加载 + 缓存）"""
        now = time.time()
        if user_id in self._feature_weights and (now - self._last_load_time) < self._cache_ttl:
            return

        await asyncio.to_thread(self._load_feature_weights_from_db, user_id)

    def _load_feature_weights_from_db(self, user_id: int) -> None:
        """从数据库加载并重建用户的特征级权重"""
        records = self._loop.get_user_feedback(user_id, limit=500)
        if user_id not in self._feature_weights:
            self._feature_weights[user_id] = {}

        now = time.time()

        for record in records:
            age_days = (now - record.created_at) / 86400.0
            decay_factor = self._compute_decay(age_days)
            # 极远期行为仍保留至少 5% 影响
            decay_factor = max(0.05, min(1.0, decay_factor))

            # 根据 rating 推断动作类型
            if record.rating == 1 and record.feedback_type == "like":
                impact = self.FEATURE_IMPACT_MAP.get(FeedbackAction.LIKE, {})
                score_factor = 1.0
            elif record.rating == -1 and record.feedback_type == "dislike":
                impact = self.FEATURE_IMPACT_MAP.get(FeedbackAction.DISLIKE, {})
                score_factor = 1.0
            elif 1 <= record.rating <= 5 and record.feedback_type == "rating":
                impact = self.FEATURE_IMPACT_MAP.get(FeedbackAction.RATE, {})
                score_factor = (record.rating - 3.0) / 2.0
            else:
                continue

            for feature, delta in impact.items():
                effective = delta * score_factor * decay_factor
                current = self._feature_weights[user_id].get(feature, 0.0)
                new_val = max(-0.8, min(0.8, current + effective))
                self._feature_weights[user_id][feature] = round(new_val, 4)

        self._last_load_time = now

    # ══════════════════════════════════════════════════════════════
    # 时间衰减计算
    # ══════════════════════════════════════════════════════════════

    @classmethod
    def _compute_decay(cls, days_elapsed: float) -> float:
        """计算时间衰减因子

        使用指数衰减模型:
            decay = exp(-decay_rate * days_elapsed)

        半衰期 = 7 天 (7天后权重减半)
        30天后衰减至约 5%

        Args:
            days_elapsed: 经过的天数

        Returns:
            float: 衰减因子 [0, 1]
        """
        import math
        return math.exp(-cls.DECAY_RATE * days_elapsed)

    # ══════════════════════════════════════════════════════════════
    # 工具方法
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _action_to_rating(action: FeedbackAction, score: Optional[float] = None) -> int:
        """将动作映射为 FeedbackLoop 的 rating 值"""
        mapping = {
            FeedbackAction.LIKE: 1,
            FeedbackAction.DISLIKE: -1,
            FeedbackAction.SKIP: 0,
            FeedbackAction.CLICK: 1,        # 点击视为正向
            FeedbackAction.UNLOCK: 1,       # 解锁视为强烈正向
            FeedbackAction.IGNORE: 0,        # 忽略视为中性
            FeedbackAction.RATE: int(round(score)) if score is not None else 0,
        }
        return mapping.get(action, 0)

    @staticmethod
    def _build_message(action: FeedbackAction, delta: float, boost: float) -> str:
        """生成友善提示消息"""
        messages = {
            FeedbackAction.LIKE: "感谢点赞 👍，我们会推荐更多类似内容",
            FeedbackAction.DISLIKE: "已记录 👎，我们将优化推荐",
            FeedbackAction.SKIP: "已跳过，下次推荐将调整",
            FeedbackAction.CLICK: "已记录点击 👆，我们将优化匹配排序",
            FeedbackAction.UNLOCK: "解锁成功 🔓，我们已加强此类匹配推荐",
            FeedbackAction.IGNORE: "已忽略 ⏭，将减少此类推荐",
            FeedbackAction.RATE: f"评分已记录 ⭐，权重调整 {delta:+.2f}",
        }
        msg = messages.get(action, f"反馈已记录, 权重调整={delta:+.2f}")
        return f"{msg} (当前boost={boost:.2f})"


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


def reset_feedback_service():
    """重置全局单例 (测试用)"""
    global _service
    _service = None
