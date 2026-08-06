"""
链客宝 — A/B 测试管理器（内存存储）
========================================
在 app/ai/ab_testing.py 统计函数之上的高层管理器。

提供 AutoABTestEngine 所需的所有接口:
    - 实验创建 / 禁用 / 删除
    - 用户变体分配（确定性哈希）
    - 转化 / 非转化跟踪
    - 统计分析（卡方检验 p-value + Wilson 置信区间）
    - 胜者自动判定

设计为内存存储（实验不持久化），
与 auto_ab_testing.py 自身的内存存储机制配合使用。
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.ai.ab_testing import chi_square_pvalue


@dataclass
class ABTestStat:
    """单一变体在实验中的统计结果"""

    variant: str = ""
    impressions: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    significant: bool = False
    p_value: float = 1.0
    confidence_interval: Tuple[float, float] = (0.0, 0.0)


class ABTestManager:
    """A/B 测试管理器（内存存储）

    负责变体分配、转化跟踪、统计分析。
    实验数据存于内存，进程重启后丢失。

    用法示例::

        mgr = ABTestManager()
        mgr.create_experiment("exp1", {"A": 50, "B": 50})
        variant = mgr.assign("exp1", "user_123")
        mgr.track_conversion("exp1", "user_123", variant)
        stats = mgr.get_stats("exp1")
        winner = mgr.get_winner("exp1")
    """

    def __init__(self):
        # _experiments: Dict[str, dict]
        # {
        #     "name": {
        #         "variants": {"A": 0.5, "B": 0.5},     # variant_name -> weight
        #         "enabled": True,
        #         "assignments": {"user_id": "variant"},
        #         "conversions": {"user_id": True},       # set of converted users
        #         "impression_counts": {"A": int, "B": int},
        #         "conversion_counts": {"A": int, "B": int},
        #         "metadata": {...},
        #         "created_at": float,
        #     }
        # }
        self._experiments: Dict[str, Dict[str, Any]] = {}

    # ── 实验生命周期 ──────────────────────────────────────────

    def create_experiment(
        self,
        name: str,
        variants: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """创建新实验

        Args:
            name: 实验名称（唯一）
            variants: variant_name -> 流量权重（无需归一化）
            metadata: 附加元数据

        Returns:
            实验名称

        Raises:
            ValueError: 实验已存在 或 变体为空
        """
        if name in self._experiments:
            raise ValueError(f"Experiment '{name}' already exists")
        if not variants:
            raise ValueError("At least one variant is required")

        self._experiments[name] = {
            "variants": dict(variants),
            "enabled": True,
            "assignments": {},
            "conversions": {},
            "impression_counts": {v: 0 for v in variants},
            "conversion_counts": {v: 0 for v in variants},
            "metadata": metadata or {},
            "created_at": time.time(),
        }
        return name

    def disable_experiment(self, name: str) -> None:
        """禁用实验 — 停止分配流量

        Args:
            name: 实验名称

        Raises:
            ValueError: 实验不存在
        """
        exp = self._get_or_raise(name)
        exp["enabled"] = False

    def delete_experiment(self, name: str) -> None:
        """删除实验（从内存中移除）

        Args:
            name: 实验名称

        Raises:
            ValueError: 实验不存在
        """
        if name not in self._experiments:
            raise ValueError(f"Experiment '{name}' not found")
        del self._experiments[name]

    # ── 用户分配 ──────────────────────────────────────────

    def assign(self, experiment_name: str, user_id: str) -> Optional[str]:
        """为用户分配变体

        使用 user_id 的确定性哈希（SHA-256），
        确保同一用户始终分配到同一变体。

        Args:
            experiment_name: 实验名称
            user_id: 用户标识符

        Returns:
            分配的 variant 名称；实验未启用时返回 None
        """
        exp = self._experiments.get(experiment_name)
        if not exp or not exp["enabled"]:
            return None

        # 已分配则直接返回（幂等）
        if user_id in exp["assignments"]:
            return exp["assignments"][user_id]

        # 确定性分配：SHA-256 哈希 → 带权重选择
        variants = list(exp["variants"].keys())
        weights = list(exp["variants"].values())
        total_weight = sum(weights)
        if total_weight <= 0:
            return None

        hash_bytes = hashlib.sha256(
            f"{experiment_name}:{user_id}".encode()
        ).digest()
        hash_int = int.from_bytes(hash_bytes[:8], "big")
        normalized = hash_int / (2**64)  # 0.0 ~ 1.0

        cumulative = 0.0
        chosen = variants[0]
        for v, w in zip(variants, weights):
            cumulative += w / total_weight
            if normalized <= cumulative:
                chosen = v
                break

        exp["assignments"][user_id] = chosen
        exp["impression_counts"][chosen] = (
            exp["impression_counts"].get(chosen, 0) + 1
        )
        return chosen

    def get_assignment(
        self, experiment_name: str, user_id: str
    ) -> Optional[str]:
        """查询用户已有的变体分配

        Args:
            experiment_name: 实验名称
            user_id: 用户标识符

        Returns:
            variant 名称，或 None（未分配或实验不存在）
        """
        exp = self._experiments.get(experiment_name)
        if not exp:
            return None
        return exp["assignments"].get(user_id)

    # ── 转化跟踪 ──────────────────────────────────────────

    def track_conversion(
        self,
        experiment_name: str,
        user_id: str,
        variant: Optional[str] = None,
    ) -> None:
        """记录一次转化事件

        同一用户只计一次转化（幂等）。

        Args:
            experiment_name: 实验名称
            user_id: 用户标识符
            variant: 变体名称；为 None 时从已有分配中查找

        Raises:
            ValueError: 实验不存在，或无法确定变体
        """
        exp = self._get_or_raise(experiment_name)

        if variant is None:
            variant = exp["assignments"].get(user_id)

        if variant is None:
            raise ValueError(
                f"No assignment found for user '{user_id}' "
                f"in experiment '{experiment_name}'"
            )

        # 幂等：同一用户只计一次
        if user_id not in exp["conversions"]:
            exp["conversions"][user_id] = True
            exp["conversion_counts"][variant] = (
                exp["conversion_counts"].get(variant, 0) + 1
            )

    def track_non_conversion(
        self,
        experiment_name: str,
        user_id: str,
        variant: Optional[str] = None,
    ) -> None:
        """记录一次非转化事件（预留接口）

        当前实现为空操作——非转化在 impression 计数中已体现。

        Args:
            experiment_name: 实验名称
            user_id: 用户标识符
            variant: 变体名称（未使用）
        """
        # 非转化在 assign() 中已通过 impression_counts 记录，
        # 此处无需额外操作。
        pass

    # ── 统计分析 ──────────────────────────────────────────

    def get_stats(self, experiment_name: str) -> List[ABTestStat]:
        """获取实验的统计结果

        对每个变体计算：
            - impressions / conversions / conversion_rate
            - p_value（卡方检验，以第一个变体为对照组）
            - significant（p_value < 0.05）
            - confidence_interval（Wilson score 95% 置信区间）

        Returns:
            按变体原始顺序排列的 ABTestStat 列表
        """
        exp = self._get_or_raise(experiment_name)
        variants = list(exp["variants"].keys())
        if not variants:
            return []

        control = variants[0]
        control_imp = exp["impression_counts"].get(control, 0)
        control_conv = exp["conversion_counts"].get(control, 0)

        results: List[ABTestStat] = []
        for variant in variants:
            imp = exp["impression_counts"].get(variant, 0)
            conv = exp["conversion_counts"].get(variant, 0)
            rate = conv / imp if imp > 0 else 0.0

            if variant == control:
                # 对照组 vs 自身 → p=1.0, 不显著
                p_value = 1.0
                significant = False
            else:
                observed = [
                    [control_conv, control_imp - control_conv],
                    [conv, imp - conv],
                ]
                p_value = chi_square_pvalue(observed)
                significant = p_value < 0.05

            ci = self._wilson_confidence_interval(conv, imp)

            results.append(
                ABTestStat(
                    variant=variant,
                    impressions=imp,
                    conversions=conv,
                    conversion_rate=rate,
                    significant=significant,
                    p_value=p_value,
                    confidence_interval=ci,
                )
            )

        return results

    def get_winner(self, experiment_name: str) -> Optional[str]:
        """获取当前统计显著的胜者

        判断规则:
            1. 对照组（第一个变体）不作为候选
            2. 候选变体必须统计显著优于对照组（p < 0.05）
            3. 从满足条件的变体中选取转化率最高的

        Returns:
            胜者 variant 名称，或 None（无显著胜者）
        """
        stats = self.get_stats(experiment_name)
        if not stats:
            return None

        control = stats[0]

        candidates = [
            s
            for s in stats[1:]
            if s.significant and s.conversion_rate > control.conversion_rate
        ]

        if not candidates:
            return None

        best = max(candidates, key=lambda s: s.conversion_rate)
        return best.variant

    # ── 内部工具 ──────────────────────────────────────────

    def _get_or_raise(self, name: str) -> Dict[str, Any]:
        """获取实验数据，不存在则抛出 ValueError"""
        if name not in self._experiments:
            raise ValueError(f"Experiment '{name}' not found")
        return self._experiments[name]

    @staticmethod
    def _wilson_confidence_interval(
        successes: int,
        trials: int,
        confidence: float = 0.95,
    ) -> Tuple[float, float]:
        """Wilson score 置信区间（比 Wald 区间更稳健）

        Args:
            successes: 成功（转化）次数
            trials: 总试验（展示）次数
            confidence: 置信水平，默认 0.95

        Returns:
            (lower_bound, upper_bound)
        """
        if trials == 0:
            return (0.0, 0.0)

        # z 值对应置信水平
        # 0.90 → 1.645,  0.95 → 1.96,  0.99 → 2.576
        if confidence >= 0.99:
            z = 2.576
        elif confidence >= 0.95:
            z = 1.96
        elif confidence >= 0.90:
            z = 1.645
        else:
            z = 1.96  # default to 95%

        p = successes / trials
        denominator = 1.0 + z**2 / trials
        centre = (p + z**2 / (2.0 * trials)) / denominator
        margin = (
            z
            * math.sqrt(
                p * (1.0 - p) / trials + z**2 / (4.0 * trials**2)
            )
            / denominator
        )

        lower = max(0.0, centre - margin)
        upper = min(1.0, centre + margin)
        return (round(lower, 6), round(upper, 6))
