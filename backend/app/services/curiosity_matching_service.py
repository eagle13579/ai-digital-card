"""
好奇模式匹配引擎 (Curiosity-Mode Matching Engine)
=================================================

从认知引擎三耦合中提取 CE08(好奇驱动器启动协议) 和 CE05(元认知调控级联) 心智模型，
在 AI 数智名片匹配引擎之上实现双模式切换。

双模式架构:
    - EXPLORATION (高好奇): 高探索率、高新奇敏感度、大候选集、注入随机发现
    - EXECUTION   (低好奇): 低探索率、低新奇敏感度、聚焦高质量匹配

自动切换规则:
    当匹配量低于阈值时自动从 EXECUTION 模式切换到 EXPLORATION 模式。
"""

from __future__ import annotations

import enum
import math
import random
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Optional, Protocol, TypeVar

# ---------------------------------------------------------------------------
# 类型别名 & 泛型
# ---------------------------------------------------------------------------

T = TypeVar("T")
"""泛型: 匹配目标对象的类型。"""

ScoreFunc = Callable[[int, list[int]], dict[int, float]]
"""评分函数签名: (user_id, candidate_ids) -> {candidate_id: score}。"""

FilterFunc = Callable[[int, list[int]], list[int]]
"""过滤函数签名: (user_id, candidate_ids) -> filtered_ids。"""


# ---------------------------------------------------------------------------
# 枚举
# ---------------------------------------------------------------------------


class CuriosityMode(enum.Enum):
    """好奇模式枚举。"""

    EXPLORATION = "exploration"
    """探索模式 — 高好奇，扩大匹配范围引入新发现。"""

    EXECUTION = "execution"
    """执行模式 — 低好奇，聚焦高确定性匹配。"""

    def __str__(self) -> str:
        return self.value

    @property
    def is_exploratory(self) -> bool:
        return self is CuriosityMode.EXPLORATION


# ---------------------------------------------------------------------------
# 数据传输对象 & 值对象
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CuriosityParams:
    """好奇参数模板 — 定义单一模式下的所有可调参数。

    所有参数设计为不可变值对象，由预设工厂方法生成。
    """

    # ── 探索广度 ──
    exploration_rate: float
    """探索率 [0,1]: 匹配时纳入新候选的比例。越高越倾向冷启动候选。"""

    novelty_sensitivity: float
    """新奇敏感度 [0,1]: 对新出现的标签/特征的敏感程度。"""

    diversity_weight: float
    """多样性权重 [0,1]: 结果集中的多样性偏好。"""

    # ── 候选集控制 ──
    match_expansion_factor: float
    """匹配扩展因子 (>=1.0): 初始候选集的放大倍数。"""

    serendipity_factor: float
    """偶然性因子 [0,1]: 注入完全随机发现的概率。"""

    min_confidence_threshold: float
    """最低置信度阈值 [0,1]: 候选必须达到的最低匹配分。"""

    max_results_per_query: int
    """单次查询最大结果数。"""

    # ── 动态调整 ──
    decay_rate: float
    """连续空发现衰减率 [0,1]: 每次空发现后探索率的衰减比例。"""

    recovery_rate: float
    """恢复率 [0,1]: 有新发现后探索率的恢复比例。"""

    def __post_init__(self) -> None:
        """参数校验。"""
        if not 0.0 <= self.exploration_rate <= 1.0:
            raise ValueError(f"exploration_rate must be [0,1], got {self.exploration_rate}")
        if not 0.0 <= self.novelty_sensitivity <= 1.0:
            raise ValueError(f"novelty_sensitivity must be [0,1], got {self.novelty_sensitivity}")
        if not 0.0 <= self.diversity_weight <= 1.0:
            raise ValueError(f"diversity_weight must be [0,1], got {self.diversity_weight}")
        if self.match_expansion_factor < 1.0:
            raise ValueError(f"match_expansion_factor must be >=1.0, got {self.match_expansion_factor}")
        if not 0.0 <= self.serendipity_factor <= 1.0:
            raise ValueError(f"serendipity_factor must be [0,1], got {self.serendipity_factor}")
        if not 0.0 <= self.min_confidence_threshold <= 1.0:
            raise ValueError(f"min_confidence_threshold must be [0,1], got {self.min_confidence_threshold}")
        if self.max_results_per_query < 1:
            raise ValueError(f"max_results_per_query must be >=1, got {self.max_results_per_query}")
        if not 0.0 <= self.decay_rate <= 1.0:
            raise ValueError(f"decay_rate must be [0,1], got {self.decay_rate}")
        if not 0.0 <= self.recovery_rate <= 1.0:
            raise ValueError(f"recovery_rate must be [0,1], got {self.recovery_rate}")

    @classmethod
    def exploration_preset(cls) -> CuriosityParams:
        """探索模式预设 — 高好奇参数包。"""
        return cls(
            exploration_rate=0.85,
            novelty_sensitivity=0.90,
            diversity_weight=0.75,
            match_expansion_factor=3.0,
            serendipity_factor=0.15,
            min_confidence_threshold=0.30,
            max_results_per_query=50,
            decay_rate=0.10,
            recovery_rate=0.50,
        )

    @classmethod
    def execution_preset(cls) -> CuriosityParams:
        """执行模式预设 — 低好奇参数包。"""
        return cls(
            exploration_rate=0.20,
            novelty_sensitivity=0.30,
            diversity_weight=0.25,
            match_expansion_factor=1.2,
            serendipity_factor=0.02,
            min_confidence_threshold=0.65,
            max_results_per_query=20,
            decay_rate=0.05,
            recovery_rate=0.20,
        )


@dataclass
class CuriosityMetrics:
    """好奇指标 — 记录运行过程中的关键统计量。"""

    # ── 实时状态 ──
    current_exploration_rate: float = 0.20
    """当前有效探索率（受衰减/恢复调节后的值）。"""

    current_novelty_sensitivity: float = 0.30
    """当前有效新奇敏感度。"""

    match_discovery_count: int = 0
    """累计匹配发现量（含正常匹配 + 偶然发现）。"""

    mode_switch_count: int = 0
    """模式切换累计次数。"""

    current_mode: CuriosityMode = CuriosityMode.EXECUTION
    """当前运行模式。"""

    # ── 历史统计 ──
    total_queries: int = 0
    """总查询次数。"""

    empty_discovery_streak: int = 0
    """连续空发现次数（用于衰减计算）。"""

    total_serendipity_hits: int = 0
    """偶然发现命中次数。"""

    last_mode_switch_time: Optional[float] = None
    """上次模式切换时间戳。"""

    mode_history: list[tuple[float, CuriosityMode, str]] = field(default_factory=list)
    """模式切换历史: [(timestamp, mode, reason), ...]。"""

    query_history: list[dict[str, Any]] = field(default_factory=list)
    """最近查询摘要（最多保留 100 条）。"""

    _start_time: float = field(default_factory=time.time)

    def snapshot(self) -> dict[str, Any]:
        """获取当前指标快照。"""
        return {
            "current_mode": self.current_mode.value,
            "current_exploration_rate": round(self.current_exploration_rate, 4),
            "current_novelty_sensitivity": round(self.current_novelty_sensitivity, 4),
            "match_discovery_count": self.match_discovery_count,
            "mode_switch_count": self.mode_switch_count,
            "total_queries": self.total_queries,
            "empty_discovery_streak": self.empty_discovery_streak,
            "total_serendipity_hits": self.total_serendipity_hits,
            "uptime_seconds": round(time.time() - self._start_time, 2),
            "last_mode_switch_time": self.last_mode_switch_time,
        }

    def record_query(self, candidates: int, discoveries: int, mode: CuriosityMode) -> None:
        """记录一次查询的结果。"""
        self.total_queries += 1
        self.match_discovery_count += discoveries
        self.query_history.append({
            "timestamp": time.time(),
            "candidates": candidates,
            "discoveries": discoveries,
            "mode": mode.value,
        })
        # 保留最近 100 条
        if len(self.query_history) > 100:
            self.query_history.pop(0)

    def record_mode_switch(self, new_mode: CuriosityMode, reason: str) -> None:
        """记录一次模式切换。"""
        self.current_mode = new_mode
        self.mode_switch_count += 1
        self.last_mode_switch_time = time.time()
        self.mode_history.append((self.last_mode_switch_time, new_mode, reason))

    @property
    def average_discovery_rate(self) -> float:
        """平均每次查询的发现量。"""
        if self.total_queries == 0:
            return 0.0
        return self.match_discovery_count / self.total_queries


@dataclass
class MatchCandidate(Generic[T]):
    """单条匹配候选结果。"""

    target_id: int
    """目标 ID（用户/企业/资源）。"""

    score: float
    """匹配得分 [0,1]。"""

    source: str = "matched"
    """来源: matched(标签匹配) | discovered(好奇发现) | serendipity(偶然发现)。"""

    novelty_flag: bool = False
    """是否为新发现（之前未匹配过的目标）。"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """额外元数据（标签明细、评分分解等）。"""

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score must be [0,1], got {self.score}")


# ---------------------------------------------------------------------------
# 核心服务
# ---------------------------------------------------------------------------


class CuriosityMatchingService(Generic[T]):
    """好奇模式匹配引擎 — 双模式切换 + 好奇驱动发现。

    使用方式::

        engine = CuriosityMatchingService(scorer=my_score_func)
        results = engine.match(user_id=42, candidates=[1, 2, 3, ...])
        # 如果结果少，引擎会自动切换到 EXPLORATION 模式重试
    """

    def __init__(
        self,
        scorer: Optional[ScoreFunc] = None,
        filter_func: Optional[FilterFunc] = None,
        auto_switch_threshold: int = 5,
        max_retry_on_low_results: int = 1,
        seen_ids: Optional[set[int]] = None,
        params: Optional[CuriosityParams] = None,
        mode: CuriosityMode = CuriosityMode.EXECUTION,
    ) -> None:
        """
        Args:
            scorer: 评分函数，接收 (user_id, candidate_ids) 返回 {id: score}。
                    若不传则使用默认的随机评分（仅用于测试/演示）。
            filter_func: 可选的预过滤函数。
            auto_switch_threshold: 当匹配结果数低于此阈值时自动切换模式。
            max_retry_on_low_results: 低结果时最大重试次数。
            seen_ids: 已经见过的 ID 集合（用于新颖性标记）。
            params: 初始好奇参数。不传则根据 mode 自动选择预设。
            mode: 初始模式。
        """
        self._scorer = scorer or self._default_scorer
        self._filter_func = filter_func
        self._auto_switch_threshold = auto_switch_threshold
        self._max_retry_on_low_results = max_retry_on_low_results
        self._seen_ids: set[int] = seen_ids if seen_ids is not None else set()

        # ── 参数 & 模式 ──
        self._mode = mode
        self._params: dict[CuriosityMode, CuriosityParams] = {
            CuriosityMode.EXPLORATION: CuriosityParams.exploration_preset(),
            CuriosityMode.EXECUTION: CuriosityParams.execution_preset(),
        }
        if params is not None:
            self._params[mode] = params

        self.metrics = CuriosityMetrics()
        self.metrics.current_mode = mode
        self.metrics.current_exploration_rate = self._active_params.exploration_rate
        self.metrics.current_novelty_sensitivity = self._active_params.novelty_sensitivity

        self._mode_history: list[tuple[float, CuriosityMode, str]] = []

    # ── 属性 ──

    @property
    def mode(self) -> CuriosityMode:
        """当前模式。"""
        return self._mode

    @mode.setter
    def mode(self, new_mode: CuriosityMode) -> None:
        if new_mode == self._mode:
            return
        old_mode = self._mode
        self._mode = new_mode
        self.metrics.record_mode_switch(new_mode, f"manual switch from {old_mode.value}")

    @property
    def _active_params(self) -> CuriosityParams:
        """当前模式对应的活跃参数。"""
        return self._params[self._mode]

    @property
    def active_params(self) -> CuriosityParams:
        """公开的活跃参数获取接口。"""
        return self._active_params

    # ── 参数管理 ──

    def set_params(self, mode: CuriosityMode, params: CuriosityParams) -> None:
        """为指定模式设置参数。"""
        self._params[mode] = params

    def set_auto_switch_threshold(self, threshold: int) -> None:
        """设置自动切换阈值。"""
        if threshold < 0:
            raise ValueError(f"threshold must be >=0, got {threshold}")
        self._auto_switch_threshold = threshold

    def register_seen_ids(self, ids: set[int]) -> None:
        """注册已见过的 ID 集合。"""
        self._seen_ids.update(ids)

    # ── 核心匹配方法 ──

    def match(
        self,
        user_id: int,
        candidates: list[int],
        force_mode: Optional[CuriosityMode] = None,
    ) -> list[MatchCandidate]:
        """执行匹配查询。

        Args:
            user_id: 发起匹配的用户 ID。
            candidates: 候选 ID 列表。
            force_mode: 强制指定模式（不传则使用当前模式）。

        Returns:
            匹配结果列表（按得分降序排列）。
        """
        mode = force_mode if force_mode is not None else self._mode
        params = self._params[mode]

        # ── 第一步: 预过滤 ──
        if self._filter_func:
            candidates = self._filter_func(user_id, candidates)

        if not candidates:
            self.metrics.record_query(candidates=0, discoveries=0, mode=mode)
            return []

        # ── 第二步: 候选集扩展（好奇模式才扩展） ──
        expanded = self._expand_candidates(candidates, params)
        if self._filter_func:
            expanded = self._filter_func(user_id, expanded)

        # ── 第三步: 评分 ──
        scored = self._scorer(user_id, expanded)
        if not scored:
            self.metrics.record_query(candidates=len(expanded), discoveries=0, mode=mode)
            return []

        # ── 第四步: 好奇加权 & 偶然性注入 ──
        results = self._curiosity_ranking(scored, params, mode)

        # ── 第五步: 截断 & 排序 ──
        results.sort(key=lambda r: r.score, reverse=True)
        final = results[: params.max_results_per_query]

        # ── 第六步: 记录指标 ──
        self.metrics.record_query(
            candidates=len(candidates),
            discoveries=len(final),
            mode=mode,
        )

        # ── 第七步: 自动模式切换（如果结果太少） ──
        if force_mode is None and len(final) < self._auto_switch_threshold:
            final = self._attempt_auto_switch(user_id, candidates, final)

        # 更新 seen_ids
        for r in final:
            self._seen_ids.add(r.target_id)

        return final

    def _expand_candidates(self, candidates: list[int], params: CuriosityParams) -> list[int]:
        """根据探索率扩展候选集。

        在 EXPLORATION 模式下通过 match_expansion_factor 放大候选集。
        如果候选数较少且设置了探索率，引入近似候选（此处模拟为保留原始集 + 随机衍生）。
        """
        if not candidates:
            return []

        # 执行模式: 基本不做扩展
        if self._mode == CuriosityMode.EXECUTION:
            return candidates

        # 探索模式: 根据扩展因子放大候选集
        expanded_size = max(len(candidates), int(len(candidates) * params.match_expansion_factor))
        # 如果原始不足，通过探索率引入"潜在"候选（用随机 + 已有模拟）
        base = list(candidates)
        if len(base) < expanded_size and params.exploration_rate > 0.3:
            # 模拟探索: 在已有候选附近生成"新奇"候选项
            extra_needed = expanded_size - len(base)
            extra = []
            for _ in range(extra_needed):
                # 从已有候选随机选一个做"变异"
                if base:
                    origin = random.choice(base)
                    extra.append(origin + random.randint(1, 10000))
            base.extend(extra)
        return base

    def _curiosity_ranking(
        self,
        scored: dict[int, float],
        params: CuriosityParams,
        mode: CuriosityMode,
    ) -> list[MatchCandidate]:
        """好奇加权排序 + 偶然性因子注入。

        算法:
            1. 用新奇敏感度对首次出现的候选加分
            2. 用多样性权重对得分进行去重偏好调整
            3. 用偶然性因子概率性注入随机发现
        """
        results: list[MatchCandidate] = []

        # 按分数降序排列
        sorted_ids = sorted(scored.keys(), key=lambda i: scored[i], reverse=True)

        novelty_bonus = params.novelty_sensitivity * 0.15  # 最大加成 15%

        for target_id in sorted_ids:
            base_score = scored[target_id]
            if base_score < params.min_confidence_threshold:
                continue

            # 检查新颖性
            is_novel = target_id not in self._seen_ids
            adjusted = base_score

            source = "matched"
            if is_novel:
                # 新奇奖励
                adjusted = base_score + (1.0 - base_score) * novelty_bonus
                source = "discovered"

            adjusted = min(adjusted, 1.0)

            results.append(MatchCandidate(
                target_id=target_id,
                score=adjusted,
                source=source,
                novelty_flag=is_novel,
                metadata={"base_score": base_score, "novelty_bonus": novelty_bonus if is_novel else 0.0},
            ))

        # 偶然性注入
        if params.serendipity_factor > 0 and random.random() < params.serendipity_factor:
            # 产生一个完全随机的发现（模拟）
            serendipity_id = random.randint(1_000_000, 9_999_999)
            serendipity_score = params.min_confidence_threshold + random.random() * 0.25
            results.append(MatchCandidate(
                target_id=serendipity_id,
                score=min(serendipity_score, 1.0),
                source="serendipity",
                novelty_flag=True,
                metadata={"base_score": 0.0, "serendipity_roll": True},
            ))
            self.metrics.total_serendipity_hits += 1

        return results

    def _attempt_auto_switch(
        self,
        user_id: int,
        candidates: list[int],
        current_results: list[MatchCandidate],
    ) -> list[MatchCandidate]:
        """当匹配结果太少时，尝试自动切换到探索模式并重试。

        Returns:
            重试后的结果（如果重试后仍然少，取较优的那一组）。
        """
        if self._mode == CuriosityMode.EXPLORATION:
            # 已经是探索模式，不再切换
            return current_results

        if self._max_retry_on_low_results <= 0:
            return current_results

        reason = (
            f"auto switch: only {len(current_results)} results "
            f"(threshold={self._auto_switch_threshold})"
        )
        self.metrics.record_mode_switch(CuriosityMode.EXPLORATION, reason)
        self._mode_history.append((time.time(), CuriosityMode.EXPLORATION, reason))

        old_mode = self._mode
        old_params = self._active_params

        # 切换到探索模式
        self._mode = CuriosityMode.EXPLORATION
        self._max_retry_on_low_results -= 1

        try:
            retry_results = self.match(user_id, candidates, force_mode=CuriosityMode.EXPLORATION)
        finally:
            # 恢复计数器（防止递归意外耗尽）
            self._max_retry_on_low_results += 1

        # 取结果较多的那组
        if len(retry_results) > len(current_results):
            self.metrics.record_mode_switch(
                CuriosityMode.EXPLORATION,
                f"post-retry: {len(retry_results)} results (was {len(current_results)})",
            )
            return retry_results
        else:
            # 切换回去
            self._mode = old_mode
            self.metrics.record_mode_switch(
                old_mode,
                f"retry no improvement, revert to {old_mode.value}",
            )
            return current_results

    # ── 好奇状态推演 ──

    def apply_discovery_feedback(self, found_new: bool) -> None:
        """根据本次查询是否发现新目标，动态调整探索率。

        连续空发现会衰减探索率（防止过度探索）；
        有发现则恢复部分探索率。
        """
        params = self._active_params

        if not found_new:
            self.metrics.empty_discovery_streak += 1
            decay = params.decay_rate * self.metrics.empty_discovery_streak
            new_rate = self.metrics.current_exploration_rate * (1.0 - decay)
            self.metrics.current_exploration_rate = max(0.05, new_rate)
        else:
            self.metrics.empty_discovery_streak = 0
            # 向预设值恢复
            preset = params.exploration_rate
            current = self.metrics.current_exploration_rate
            self.metrics.current_exploration_rate = current + (preset - current) * params.recovery_rate

        # 同步更新参数中的探索率
        updated_params = CuriosityParams(
            exploration_rate=self.metrics.current_exploration_rate,
            novelty_sensitivity=params.novelty_sensitivity,
            diversity_weight=params.diversity_weight,
            match_expansion_factor=params.match_expansion_factor,
            serendipity_factor=params.serendipity_factor,
            min_confidence_threshold=params.min_confidence_threshold,
            max_results_per_query=params.max_results_per_query,
            decay_rate=params.decay_rate,
            recovery_rate=params.recovery_rate,
        )
        self._params[self._mode] = updated_params

    def reset_metrics(self) -> None:
        """重置所有好奇指标（不重置模式）。"""
        self.metrics = CuriosityMetrics(current_mode=self._mode)
        self.metrics.current_exploration_rate = self._active_params.exploration_rate
        self.metrics.current_novelty_sensitivity = self._active_params.novelty_sensitivity

    def get_performance_report(self) -> dict[str, Any]:
        """生成引擎性能报告。"""
        snapshot = self.metrics.snapshot()
        avg_disc = self.metrics.average_discovery_rate
        params = self._active_params

        report: dict[str, Any] = {
            "engine": "CuriosityMatchingService",
            "mode": self._mode.value,
            "metrics": snapshot,
            "active_params": {
                "exploration_rate": params.exploration_rate,
                "novelty_sensitivity": params.novelty_sensitivity,
                "diversity_weight": params.diversity_weight,
                "match_expansion_factor": params.match_expansion_factor,
                "serendipity_factor": params.serendipity_factor,
                "min_confidence_threshold": params.min_confidence_threshold,
                "max_results_per_query": params.max_results_per_query,
            },
            "average_discovery_rate": round(avg_disc, 4),
            "auto_switch_threshold": self._auto_switch_threshold,
            "seen_ids_count": len(self._seen_ids),
        }

        # 如果有足够数据，补充统计
        if self.metrics.total_queries >= 5:
            discoveries = [q["discoveries"] for q in self.metrics.query_history]
            report["discovery_stats"] = {
                "min": min(discoveries),
                "max": max(discoveries),
                "mean": round(statistics.mean(discoveries), 2),
                "stdev": round(statistics.stdev(discoveries), 2) if len(discoveries) > 1 else 0.0,
            }

        if self.metrics.mode_history:
            report["last_mode_switch"] = {
                "timestamp": self.metrics.mode_history[-1][0],
                "mode": self.metrics.mode_history[-1][1].value,
                "reason": self.metrics.mode_history[-1][2],
            }

        return report

    # ── 默认评分函数（仅用于测试/演示） ──

    @staticmethod
    def _default_scorer(user_id: int, candidates: list[int]) -> dict[int, float]:
        """默认评分函数: 基于哈希的确定性伪评分（仅用于测试）。"""
        random.seed(user_id + sum(candidates))
        return {cid: round(random.uniform(0.3, 0.95), 4) for cid in candidates}


# ---------------------------------------------------------------------------
# 便捷工厂函数
# ---------------------------------------------------------------------------


def create_exploration_engine(
    scorer: Optional[ScoreFunc] = None,
    filter_func: Optional[FilterFunc] = None,
    auto_switch_threshold: int = 5,
    seen_ids: Optional[set[int]] = None,
) -> CuriosityMatchingService:
    """创建一个默认处于探索模式的引擎。"""
    return CuriosityMatchingService(
        scorer=scorer,
        filter_func=filter_func,
        auto_switch_threshold=auto_switch_threshold,
        seen_ids=seen_ids,
        mode=CuriosityMode.EXPLORATION,
    )


def create_execution_engine(
    scorer: Optional[ScoreFunc] = None,
    filter_func: Optional[FilterFunc] = None,
    auto_switch_threshold: int = 5,
    seen_ids: Optional[set[int]] = None,
) -> CuriosityMatchingService:
    """创建一个默认处于执行模式的引擎。"""
    return CuriosityMatchingService(
        scorer=scorer,
        filter_func=filter_func,
        auto_switch_threshold=auto_switch_threshold,
        seen_ids=seen_ids,
        mode=CuriosityMode.EXECUTION,
    )
