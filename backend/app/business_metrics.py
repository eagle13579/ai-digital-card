"""
业务指标采集器 — Business Metrics Collector

基于 prometheus_client，定义 AI 数字名片的核心业务指标，
自动注册到 Prometheus 默认 REGISTRY，通过 /metrics 端点暴露。

指标一览:
  - ncard_users_created_total          Counter  注册用户总数
  - ncard_users_active_24h             Gauge    24 小时活跃用户数
  - ncard_brochures_created_total      Counter  名片创建总数
  - ncard_matches_total                Counter  匹配总数
  - ncard_billing_revenue_cents_total  Counter  交易收入（累计，单位: 分）
  - ncard_trial_conversion_ratio       Gauge    试用转付费转化率（0.0 ~ 1.0）
"""

from __future__ import annotations

import logging
from functools import lru_cache

from prometheus_client import Counter, Gauge, generate_latest, REGISTRY

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════
# Prometheus 指标定义
# ══════════════════════════════════════════════════════════════════════

# ── 注册用户数 ───────────────────────────────────────────────────────
users_created: Counter = Counter(
    "ncard_users_created_total",
    "累计注册用户总数",
    labelnames=["source"],  # source: "wechat" | "phone" | "oauth" | "admin"
)
"""注册用户计数器。每次新用户完成注册时 +1。"""

# ── 24 小时活跃用户数 ────────────────────────────────────────────────
users_active_24h: Gauge = Gauge(
    "ncard_users_active_24h",
    "过去 24 小时活跃用户数（至少发起一次 API 请求的 user_id 去重计数）",
)
"""活跃用户仪表盘。由定时任务或查询结果定期更新。"""

# ── 名片创建数 ───────────────────────────────────────────────────────
brochures_created: Counter = Counter(
    "ncard_brochures_created_total",
    "累计名片创建总数",
    labelnames=["purpose"],  # purpose: "partner" | "client" | "investor" | "supplier" | ""
)
"""名片创建计数器。每次用户成功创建/发布名片时 +1。"""

# ── 匹配数 ───────────────────────────────────────────────────────────
matches_total: Counter = Counter(
    "ncard_matches_total",
    "累计匹配总数",
    labelnames=["source"],  # source: "auto" | "manual"
)
"""匹配计数器。每次系统生成或用户手动确认匹配时 +1。"""

# ── 交易收入（累计，单位: 分） ───────────────────────────────────────
billing_revenue_cents: Counter = Counter(
    "ncard_billing_revenue_cents_total",
    "累计交易收入（单位: 人民币分）",
    labelnames=["channel", "tier"],
    # channel: "wechat" | "alipay"
    # tier:    "gold" | "diamond" | "board" | "enterprise"
)
"""收入计数器。每次支付成功回调时增加对应的金额（分）。"""

# ── 试用转付费转化率 ─────────────────────────────────────────────────
trial_conversion_ratio: Gauge = Gauge(
    "ncard_trial_conversion_ratio",
    "试用转付费转化率（0.0 ~ 1.0），由定时任务计算更新",
)
"""转化率仪表盘。由定时任务统计试用->付费用户的比例后更新。"""


# ══════════════════════════════════════════════════════════════════════
# 便捷 API — 让业务代码无需 import prometheus_client
# ══════════════════════════════════════════════════════════════════════


def inc_users_created(source: str = "phone") -> None:
    """记录一次用户注册事件。

    Args:
        source: 注册来源 — "wechat" | "phone" | "oauth" | "admin"
    """
    users_created.labels(source=source).inc()
    logger.debug("business_metric: users_created (source=%s)", source)


def set_users_active_24h(count: int) -> None:
    """设置过去 24 小时活跃用户数。

    Args:
        count: 活跃用户数
    """
    users_active_24h.set(count)
    logger.debug("business_metric: users_active_24h=%d", count)


def inc_brochures_created(purpose: str = "") -> None:
    """记录一次名片创建事件。

    Args:
        purpose: 名片用途 — "partner" | "client" | "investor" | "supplier" | ""
    """
    brochures_created.labels(purpose=purpose).inc()
    logger.debug("business_metric: brochures_created (purpose=%s)", purpose)


def inc_matches(source: str = "auto") -> None:
    """记录一次匹配事件。

    Args:
        source: 匹配来源 — "auto" | "manual"
    """
    matches_total.labels(source=source).inc()
    logger.debug("business_metric: matches_total (source=%s)", source)


def inc_billing_revenue(cents: int, channel: str = "wechat", tier: str = "") -> None:
    """记录一次交易收入。

    Args:
        cents:   交易金额（人民币分）
        channel: 支付渠道 — "wechat" | "alipay"
        tier:    会员等级 — "gold" | "diamond" | "board" | "enterprise"
    """
    billing_revenue_cents.labels(channel=channel, tier=tier).inc(cents)
    logger.debug(
        "business_metric: billing_revenue_cents (channel=%s, tier=%s, cents=%d)",
        channel, tier, cents,
    )


def set_trial_conversion_ratio(ratio: float) -> None:
    """设置试用转付费转化率。

    Args:
        ratio: 转化率（0.0 ~ 1.0）
    """
    if not 0.0 <= ratio <= 1.0:
        logger.warning("trial_conversion_ratio out of range: %f", ratio)
        ratio = max(0.0, min(1.0, ratio))
    trial_conversion_ratio.set(ratio)
    logger.debug("business_metric: trial_conversion_ratio=%.4f", ratio)


# ══════════════════════════════════════════════════════════════════════
# 批量导出
# ══════════════════════════════════════════════════════════════════════


@lru_cache(maxsize=1)
def get_prometheus_registry():
    """返回默认的 Prometheus REGISTRY（缓存避免重复引用）。"""
    return REGISTRY


def generate_business_metrics() -> str:
    """生成 Prometheus 文本格式的业务指标输出。

    返回的字符串可直接写入 HTTP Response body。

    用法:
        from app.business_metrics import generate_business_metrics
        metrics_text = generate_business_metrics()
    """
    return generate_latest(REGISTRY).decode("utf-8")


# ══════════════════════════════════════════════════════════════════════
# Health / debug
# ══════════════════════════════════════════════════════════════════════


def list_all_metrics() -> list[str]:
    """返回当前注册的所有 metric 名称（用于调试）。"""
    return [m.name for m in REGISTRY.collect()]


if __name__ == "__main__":
    # 快速验证 — 手动运行 python -m app.business_metrics
    print("=== 业务指标采集器自检 ===")
    print(generate_business_metrics())
    print(f"\n已注册指标: {list_all_metrics()}")
