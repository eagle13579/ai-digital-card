"""
Rate Limit 状态查询 Router
============================
提供 Rate Limit 内部状态查询端点，供 SDK 和管理员使用。

这些路由不会被 RateLimitMiddleware 限流（已加入白名单），
确保限流管理本身不会因被限流而无法访问。

Endpoints:
    GET /api/v1/rate-limit/status       → 当前所有活跃桶的状态（管理员用）
    GET /api/v1/rate-limit/remaining    → 当前请求的剩余次数
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict

from fastapi import APIRouter, Request

from app.middleware.rate_limit_middleware import (
    _get_client_ip,
    _get_bucket_for_ip,
)

logger = logging.getLogger("chainke.sdk.ratelimit.router")

router = APIRouter(prefix="/api/v1/rate-limit", tags=["Rate Limit SDK"])


# =====================================================================
# 当前限流状态概览（管理员）
# =====================================================================


@router.get("/status", summary="当前限流状态概览")
async def get_rate_limit_status() -> Dict[str, Any]:
    """返回当前所有活跃限流桶的状态摘要。

    **注意:** 生产环境中建议加管理员鉴权。

    Returns:
        {
            "active_buckets": int,         # 活跃桶数量
            "total_ips": int,              # 受限制的独立 IP/Key 数量
            "buckets": [                   # 每个桶的详细信息
                {
                    "key": str,
                    "rate": int,
                    "remaining": int,
                    "window": int,
                },
                ...
            ]
        }
    """
    from sdk.rate_limit_client import get_all_buckets as _get_all

    buckets = _get_all()
    return {
        "active_buckets": len(buckets),
        "total_ips": len(buckets),
        "buckets": buckets,
    }


# =====================================================================
# 当前请求剩余次数
# =====================================================================


@router.get("/remaining", summary="当前请求剩余次数")
async def get_my_remaining(request: Request) -> Dict[str, Any]:
    """返回当前请求的客户端 IP 的限流剩余次数。

    用于客户端在发送请求前判断是否需要降级。

    Returns:
        {
            "client_ip": str,
            "remaining": int,
            "limit": int,
            "reset_time": float,
        }
    """
    # 获取客户端 IP
    client_ip = _get_client_ip(request)

    # 从 os.environ 读默认值（与中间件保持同步）
    default_rate = int(os.getenv("RATE_LIMIT_DEFAULT", "60"))
    auth_rate = int(os.getenv("RATE_LIMIT_AUTH", "10"))
    admin_rate = int(os.getenv("RATE_LIMIT_ADMIN", "120"))

    # 获取对应桶，**不消耗令牌**
    bucket = _get_bucket_for_ip(
        client_ip,
        request.url.path,
        default_rate,
        auth_rate,
        admin_rate,
    )
    bucket._refill()

    return {
        "client_ip": client_ip,
        "remaining": int(bucket.tokens),
        "limit": bucket.rate,
        "reset_time": time.time() + bucket.per_second,
    }
