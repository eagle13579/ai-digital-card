"""
AI数字名片 — A/B 定价实验服务 (A/B Pricing Experiment)
=====================================================

在标准版定价基础上运行 A/B 实验：
  - 对照组 (control): 当前定价 ¥99/月 (9900 cents)
  - 实验组 (variant): 新定价策略

实验规则:
  - 新用户随机分配 50:50 到 control/variant
  - 实验独立运行，每个实验有唯一 name
  - metrics 记录转化、曝光等数据
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# ── 实验状态 枚举 ─────────────────────────────────────────────────────────


class ExperimentStatus:
    """实验状态常量"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


# ── 数据结构 ──────────────────────────────────────────────────────────────


@dataclass
class PricingVariant:
    """定价实验变体"""
    name: str                          # control / variant
    label: str                         # 可读名称
    price_cents: int                   # 定价 (分)
    price_yuan: str                    # 定价 (元)
    description: str = ""


@dataclass
class ExperimentMetrics:
    """实验指标"""
    exposure_count: int = 0            # 曝光数（用户分配到实验组）
    conversion_count: int = 0          # 转化数（用户完成购买）
    conversion_rate: float = 0.0       # 转化率
    revenue_cents: int = 0             # 收入 (分)
    avg_revenue_per_user: float = 0.0  # 每用户平均收入


@dataclass
class ABPricingExperiment:
    """A/B 定价实验定义

    示例:
        ABPricingExperiment(
            name="standard_v2_2026Q3",
            description="标准版定价实验 — ¥99 vs ¥79",
            control=PricingVariant(
                name="control",
                label="当前定价 ¥99",
                price_cents=9900,
                price_yuan="99",
                description="当前标准版定价 ¥99/月",
            ),
            variant=PricingVariant(
                name="variant",
                label="实验定价 ¥79",
                price_cents=7900,
                price_yuan="79",
                description="新定价策略 ¥79/月",
            ),
            traffic_split=50,
            status=ExperimentStatus.RUNNING,
        )
    """
    name: str
    description: str = ""
    control: PricingVariant = field(default_factory=lambda: PricingVariant(
        name="control", label="当前定价 ¥99", price_cents=9900, price_yuan="99",
    ))
    variant: PricingVariant = field(default_factory=lambda: PricingVariant(
        name="variant", label="实验定价 ¥79", price_cents=7900, price_yuan="79",
    ))
    traffic_split: int = 50            # 实验组流量百分比 (50 = 50:50)
    status: str = ExperimentStatus.DRAFT
    created_at: str = ""
    updated_at: str = ""
    metrics: ExperimentMetrics = field(default_factory=ExperimentMetrics)
    variant_metrics: ExperimentMetrics = field(default_factory=ExperimentMetrics)


# ── 实验存储 (内存，生产应使用 DB/Redis) ────────────────────────────────


_experiments: dict[str, ABPricingExperiment] = {}

_DEFAULT_EXPERIMENT = ABPricingExperiment(
    name="standard_v2_2026Q3",
    description="标准版定价 A/B 实验 — 对照组 ¥99/月 vs 实验组 ¥79/月",
    control=PricingVariant(
        name="control",
        label="当前定价 ¥99",
        price_cents=9900,
        price_yuan="99",
        description="当前标准版定价 ¥99/月",
    ),
    variant=PricingVariant(
        name="variant",
        label="实验定价 ¥79",
        price_cents=7900,
        price_yuan="79",
        description="新定价策略 ¥79/月 — 降低入门门槛，提升转化率",
    ),
    traffic_split=50,
    status=ExperimentStatus.DRAFT,
    created_at=datetime.utcnow().isoformat(),
    updated_at=datetime.utcnow().isoformat(),
)


def _init_default() -> None:
    """初始化默认实验"""
    if "standard_v2_2026Q3" not in _experiments:
        _experiments["standard_v2_2026Q3"] = _DEFAULT_EXPERIMENT


# ── 核心服务函数 ─────────────────────────────────────────────────────────


def get_experiment(name: str) -> Optional[ABPricingExperiment]:
    """获取指定实验"""
    _init_default()
    return _experiments.get(name)


def list_experiments() -> list[ABPricingExperiment]:
    """列出所有实验"""
    _init_default()
    return list(_experiments.values())


def start_experiment(name: str) -> ABPricingExperiment:
    """启动实验 (draft -> running)"""
    _init_default()
    exp = _experiments.get(name)
    if not exp:
        raise ValueError(f"实验不存在: {name}")
    if exp.status != ExperimentStatus.DRAFT:
        raise ValueError(f"只有草稿状态的实验可以启动，当前状态: {exp.status}")
    exp.status = ExperimentStatus.RUNNING
    exp.updated_at = datetime.utcnow().isoformat()
    return exp


def pause_experiment(name: str) -> ABPricingExperiment:
    """暂停实验 (running -> paused)"""
    exp = _experiments.get(name)
    if not exp:
        raise ValueError(f"实验不存在: {name}")
    if exp.status != ExperimentStatus.RUNNING:
        raise ValueError(f"只有运行中的实验可以暂停，当前状态: {exp.status}")
    exp.status = ExperimentStatus.PAUSED
    exp.updated_at = datetime.utcnow().isoformat()
    return exp


def complete_experiment(name: str) -> ABPricingExperiment:
    """完成实验 (running/paused -> completed)"""
    exp = _experiments.get(name)
    if not exp:
        raise ValueError(f"实验不存在: {name}")
    if exp.status not in (ExperimentStatus.RUNNING, ExperimentStatus.PAUSED):
        raise ValueError(f"只有运行中或已暂停的实验可以完成，当前状态: {exp.status}")
    exp.status = ExperimentStatus.COMPLETED
    exp.updated_at = datetime.utcnow().isoformat()
    return exp


def assign_user_to_variant(
    experiment_name: str,
    user_id: int | str,
) -> str:
    """将用户分配到实验组 (control / variant)

    基于 user_id 的哈希实现确定性分配，保证同一用户始终进入同一组。
    新用户 50:50 随机分配。
    """
    exp = get_experiment(experiment_name)
    if not exp or exp.status != ExperimentStatus.RUNNING:
        return "control"  # 默认分配 control

    # 确定性分配：基于 user_id 哈希
    seed = hash(f"{experiment_name}:{user_id}") & 0x7FFFFFFF
    r = seed % 100

    if r < exp.traffic_split:
        # 记录曝光
        exp.metrics.exposure_count += 1
        return "variant"
    else:
        exp.variant_metrics.exposure_count += 1
        return "control"


def record_conversion(
    experiment_name: str,
    user_id: int | str,
    variant: str,
    amount_cents: int = 0,
) -> None:
    """记录转化事件（用户完成购买）"""
    exp = get_experiment(experiment_name)
    if not exp:
        return

    if variant == "control":
        exp.metrics.conversion_count += 1
        exp.metrics.revenue_cents += amount_cents
        if exp.metrics.exposure_count > 0:
            exp.metrics.conversion_rate = round(
                exp.metrics.conversion_count / exp.metrics.exposure_count * 100, 2
            )
        if exp.metrics.exposure_count > 0:
            exp.metrics.avg_revenue_per_user = round(
                exp.metrics.revenue_cents / exp.metrics.exposure_count, 2
            )
    else:
        exp.variant_metrics.conversion_count += 1
        exp.variant_metrics.revenue_cents += amount_cents
        if exp.variant_metrics.exposure_count > 0:
            exp.variant_metrics.conversion_rate = round(
                exp.variant_metrics.conversion_count / exp.variant_metrics.exposure_count * 100, 2
            )
        if exp.variant_metrics.exposure_count > 0:
            exp.variant_metrics.avg_revenue_per_user = round(
                exp.variant_metrics.revenue_cents / exp.variant_metrics.exposure_count, 2
            )

    exp.updated_at = datetime.utcnow().isoformat()


def get_experiment_status(name: str) -> dict:
    """获取实验详细状态（含指标）"""
    exp = get_experiment(name)
    if not exp:
        raise ValueError(f"实验不存在: {name}")

    return {
        "name": exp.name,
        "description": exp.description,
        "status": exp.status,
        "traffic_split": exp.traffic_split,
        "created_at": exp.created_at,
        "updated_at": exp.updated_at,
        "control": {
            "name": exp.control.name,
            "label": exp.control.label,
            "price_cents": exp.control.price_cents,
            "price_yuan": exp.control.price_yuan,
            "description": exp.control.description,
            "metrics": {
                "exposure_count": exp.metrics.exposure_count,
                "conversion_count": exp.metrics.conversion_count,
                "conversion_rate": exp.metrics.conversion_rate,
                "revenue_cents": exp.metrics.revenue_cents,
                "avg_revenue_per_user": exp.metrics.avg_revenue_per_user,
            },
        },
        "variant": {
            "name": exp.variant.name,
            "label": exp.variant.label,
            "price_cents": exp.variant.price_cents,
            "price_yuan": exp.variant.price_yuan,
            "description": exp.variant.description,
            "metrics": {
                "exposure_count": exp.variant_metrics.exposure_count,
                "conversion_count": exp.variant_metrics.conversion_count,
                "conversion_rate": exp.variant_metrics.conversion_rate,
                "revenue_cents": exp.variant_metrics.revenue_cents,
                "avg_revenue_per_user": exp.variant_metrics.avg_revenue_per_user,
            },
        },
    }
