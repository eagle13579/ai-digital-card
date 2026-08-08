"""
Web Vitals 性能监控端点
──────────────────────
接收前端上报的 Core Web Vitals 指标 (LCP/FID/CLS/TTFB/FCP)。
通过 POST /api/v1/metrics/web-vitals 接收 JSON 数据。

BUG-027 修复（2026-08）:
  - 匿名埋点端点无法要求登录鉴权，改为基于 IP 的进程内滑动窗口限流
    （每 IP 每分钟最多 60 次上报请求），防止匿名无限流刷库；
  - 单次批量上报截断至 20 条，防超大批量写入；
  - 日志匿名化：user_agent / page_url 截断，避免敏感信息落日志。
"""
from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/metrics", tags=["性能监控"])

# ── 轻量进程内限流（BUG-027）─────────────────────────────────────────────
# 单实例进程内存储；多实例部署时应迁移到 Redis（key: webvitals:{ip}）。
_WINDOW_SECONDS = 60
_MAX_REQUESTS_PER_WINDOW = 60    # 每 IP 每分钟最多 60 次上报请求
_MAX_METRICS_PER_BATCH = 20      # 单次批量上报最多 20 条指标
_MAX_LOG_FIELD_LEN = 200         # 日志字段截断长度（匿名化）
_RATE_STORE: dict[str, list[float]] = defaultdict(list)
_RATE_LOCK = threading.Lock()


def _client_ip(request: Request) -> str:
    """从请求中提取客户端 IP（优先 X-Forwarded-For）。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _rate_limited(ip: str) -> bool:
    """滑动窗口限流检查：返回 True 放行，False 表示超限。

    与全局 RateLimiterMiddleware 同思路的轻量实现：
    记录每个 IP 的请求时间戳，窗口内超过阈值即拒绝。
    """
    now = time.time()
    cutoff = now - _WINDOW_SECONDS
    with _RATE_LOCK:
        timestamps = _RATE_STORE[ip]
        # 移除窗口外过期时间戳
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)
        if len(timestamps) >= _MAX_REQUESTS_PER_WINDOW:
            return False
        timestamps.append(now)
        # 定期清理无活跃 IP，避免内存无限增长
        if len(_RATE_STORE) > 10000:
            for key in [k for k, v in _RATE_STORE.items() if not v or v[-1] < cutoff]:
                _RATE_STORE.pop(key, None)
        return True


def _truncate(value: str, limit: int = _MAX_LOG_FIELD_LEN) -> str:
    """日志字段截断（匿名化：避免完整 URL/UA 落日志）。"""
    if not value:
        return ""
    return value if len(value) <= limit else value[:limit] + "..."


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
async def receive_web_vitals(data: WebVitalsBatchSchema, request: Request):
    """接收前端 Web Vitals 性能数据并记录（BUG-027：限流 + 匿名化）。"""
    ip = _client_ip(request)
    if not _rate_limited(ip):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    # BUG-027: 截断超大批量，防刷库
    metrics = data.metrics[:_MAX_METRICS_PER_BATCH]
    page_url = _truncate(data.url or "unknown")
    user_agent = _truncate(data.user_agent)
    logger.info(
        "[Web Vitals] 收到 %d 条指标 from %s: %s (ip=%s)",
        len(metrics), page_url, user_agent or "N/A", ip,
    )

    for metric in metrics:
        _log_metric(metric, page_url)

    return {"status": "ok", "received": len(metrics)}


@router.post("/web-vitals/single")
async def receive_single_vital(data: WebVitalMetricSchema, request: Request):
    """接收单条 Web Vital 指标（支持 sendBeacon 单条发送，BUG-027：限流）。"""
    ip = _client_ip(request)
    if not _rate_limited(ip):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    logger.info(
        "[Web Vitals][%s] %.2f (%s) [%s] (ip=%s)",
        data.name, data.value, data.rating, _truncate(data.navigationType, 64), ip,
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
