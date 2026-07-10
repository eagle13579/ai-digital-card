"""
AI 用量监控路由 — 提供 Token 消耗/延迟/调用次数实时聚合视图
=============================================================

端点:
  GET /api/v1/ai/metrics/summary  → 今日 AI 用量汇总
  GET /api/v1/ai/metrics/models   → 按模型分组的用量统计

数据来源:
  - AIMetricsCollector (内存 + SQLite 持久化)
  - 同时融合 MetricsMiddleware (Prometheus) 的 AI 推理延迟直方图
"""

import logging
from typing import Any

from fastapi import APIRouter

from app.ai.metrics_collector import get_ai_metrics_summary, get_ai_models_metrics
from app.middleware.metrics import get_metrics_instance

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai/metrics", tags=["AI 用量监控"])


# ======================================================================
# 辅助函数
# ======================================================================

def _get_prometheus_ai_stats() -> dict[str, Any]:
    """从 Prometheus MetricsMiddleware 获取 AI 推理延迟统计。

    Returns:
        包含 ai_inference_count, ai_inference_sum, ai_inference_avg_ms 的字典。
        若中间件不可用，返回空字典。
    """
    mi = get_metrics_instance()
    if mi is None:
        return {}

    count = mi.ai_inference_count
    total_sum = mi.ai_inference_sum  # 秒

    return {
        "prometheus_ai_inference_count": count,
        "prometheus_ai_inference_sum_seconds": round(total_sum, 6),
        "prometheus_ai_inference_avg_ms": round(
            (total_sum * 1000) / max(count, 1), 2
        ) if count > 0 else 0.0,
    }


# ======================================================================
# 端点
# ======================================================================


@router.get("/summary")
async def ai_metrics_summary():
    """AI 用量汇总 — 今日调用次数 / Token 消耗 / 平均延迟 / 错误率。

    数据来源:
      1. AIMetricsCollector — 按模型聚合的精确调用统计 (内存 + SQLite 持久化)
      2. MetricsMiddleware — Prometheus 级别的 AI 推理延迟直方图

    Returns:
        JSON 包含:
          - date: 统计日期
          - total_calls: 今日总调用次数
          - total_errors: 今日错误次数
          - error_rate: 错误率
          - total_tokens: 总 Token 消耗
          - avg_latency_ms: 平均延迟 (毫秒)
          - model_count: 活跃模型数
          - uptime_seconds: 采集器运行时长
          - prometheus: (如有) Prometheus 级别统计
    """
    try:
        summary = get_ai_metrics_summary()
    except Exception as e:
        logger.error("获取 AI 用量汇总失败: %s", e)
        return {
            "error": "无法获取 AI 用量汇总",
            "detail": str(e),
            "total_calls": 0,
            "total_tokens": 0,
        }

    # 融合 Prometheus 数据
    prom_stats = _get_prometheus_ai_stats()

    return {
        **summary,
        "prometheus": prom_stats if prom_stats else None,
    }


@router.get("/models")
async def ai_models_metrics():
    """按模型分组的 AI 用量统计。

    每个模型包含:
      - model_name: 模型名称
      - call_count: 调用次数
      - error_count: 错误次数
      - error_rate: 错误率
      - total_tokens: 总 Token 消耗
      - prompt_tokens: Prompt Token 数
      - completion_tokens: Completion Token 数
      - total_latency_ms: 总延迟 (毫秒)
      - avg_latency_ms: 平均延迟 (毫秒)

    Returns:
        JSON 包含:
          - models: 按调用次数降序排列的模型统计列表
          - total: 汇总数据
    """
    try:
        models_data = get_ai_models_metrics()
    except Exception as e:
        logger.error("获取按模型 AI 用量统计失败: %s", e)
        return {
            "error": "无法获取按模型 AI 用量统计",
            "detail": str(e),
            "models": [],
            "total": {"total_calls": 0, "total_tokens": 0},
        }

    # 计算总汇总
    total_calls = sum(m["call_count"] for m in models_data)
    total_tokens = sum(m["total_tokens"] for m in models_data)
    total_errors = sum(m["error_count"] for m in models_data)

    return {
        "models": models_data,
        "total": {
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "total_errors": total_errors,
            "error_rate": round(total_errors / max(total_calls, 1), 4),
        },
    }
