"""
Web Vitals 性能监控端点
──────────────────────
接收前端上报的 Core Web Vitals 指标 (LCP/FID/CLS/TTFB/FCP)。
通过 POST /api/v1/metrics/web-vitals 接收 JSON 数据。
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/metrics", tags=["性能监控"])


class WebVitalMetricSchema(BaseModel):
    """单条 Web Vital 指标数据模型。"""
    name: Literal["LCP", "FID", "CLS", "TTFB", "FCP", "INP"]
    value: float = Field(..., description="指标值（毫秒或无量纲）")
    rating: Literal["good", "needs-improvement", "poor"]
    delta: float = Field(0.0, description="自上次上报的变化值")
    id: str = Field("", description="指标唯一标识")
    navigationType: str = Field("navigate", description="导航类型")


class WebVitalsBatchSchema(BaseModel):
    """批量上报性能指标。"""
    metrics: list[WebVitalMetricSchema] = Field(default_factory=list)
    user_agent: str = Field("", description="客户端 User-Agent")
    url: str = Field("", description="页面 URL")
    timestamp: str = Field("", description="上报时间")


@router.post("/web-vitals")
async def receive_web_vitals(data: WebVitalsBatchSchema):
    """接收前端 Web Vitals 性能数据并记录。"""
    page_url = data.url or "unknown"
    logger.info(
        "[Web Vitals] 收到 %d 条指标 from %s: %s",
        len(data.metrics), page_url, data.user_agent[:100] if data.user_agent else "N/A",
    )

    for metric in data.metrics:
        _log_metric(metric, page_url)

    return {"status": "ok", "received": len(data.metrics)}


@router.post("/web-vitals/single")
async def receive_single_vital(data: WebVitalMetricSchema):
    """接收单条 Web Vital 指标（支持 sendBeacon 单条发送）。"""
    logger.info(
        "[Web Vitals][%s] %.2f (%s) [%s]",
        data.name, data.value, data.rating, data.navigationType,
    )
    return {"status": "ok"}


def _log_metric(metric: WebVitalMetricSchema, page_url: str) -> None:
    """将单条指标写入日志（结构化 Key-Value 格式，便于日志系统解析）。"""
    extra = {
        "metric": metric.name,
        "value": metric.value,
        "rating": metric.rating,
        "delta": metric.delta,
        "id": metric.id,
        "navigation_type": metric.navigationType,
        "page_url": page_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    logger.info(
        "[Web Vitals][%(metric)s] value=%(value).2f rating=%(rating)s nav=%(navigation_type)s page=%(page_url)s",
        extra,
    )
