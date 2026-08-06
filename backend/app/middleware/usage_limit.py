"""
UsageLimitMiddleware — 使用限制中间件

拦截 /api/v1/brochure/ 等路由，基于用户层级检查使用限制。
超限时返回 402 Payment Required + 升级提示。
"""

from __future__ import annotations

import logging
import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.database import AsyncSessionLocal
from app.services.usage_service import increment_usage, check_limit

logger = logging.getLogger(__name__)

# ===================================================================
# 受限制的路由模式表
# ===================================================================
# (path_pattern, feature_name, method_whitelist)
# None method_whitelist = all methods
LIMITED_ROUTES: list[tuple[re.Pattern, str, list[str] | None]] = [
    (re.compile(r"^/api/v1/brochure/$"), "card", ["POST"]),
    (re.compile(r"^/api/v1/brochure/\d+$"), "card", ["PUT", "PATCH"]),
    (re.compile(r"^/api/v1/brochure/[^/]+/ocr$"), "ocr", None),
    (re.compile(r"^/api/v1/visitor/export"), "batch_import", None),
    (re.compile(r"^/api/v1/visitor/batch"), "batch_import", ["POST"]),
    (re.compile(r"^/api/v1/api-keys/"), "api", None),
]

# 豁免路径（不检查使用限制）
WHITELIST_PATHS: list[re.Pattern] = [
    re.compile(r"^/health"),
    re.compile(r"^/api/v1/auth/"),
    re.compile(r"^/api/v1/membership/"),
    re.compile(r"^/api/v1/payment/"),
]


def _get_user_id_from_request(request: Request) -> int | None:
    """尝试从请求中提取用户ID。"""
    # 优先取 state（由 AuthMiddleware 等注入）
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        return user_id

    # 尝试从 scope 或 query 参数获取
    user_id = request.headers.get("X-User-Id")
    if user_id is not None:
        try:
            return int(user_id)
        except (ValueError, TypeError):
            pass

    return None


class UsageLimitMiddleware(BaseHTTPMiddleware):
    """
    使用限制中间件。

    根据用户层级（free/pro/enterprise）对功能使用进行限制。
    超限返回 402 Payment Required。

    用法:
        app.add_middleware(UsageLimitMiddleware)
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        logger.info("[UsageLimit] 使用限制中间件已初始化")

    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        path = request.url.path
        method = request.method

        # 豁免路径直接放行
        for pattern in WHITELIST_PATHS:
            if pattern.match(path):
                return await call_next(request)

        # 检查是否命中受限制路由
        matched_feature: str | None = None
        for path_pattern, feature, methods in LIMITED_ROUTES:
            if path_pattern.match(path):
                if methods is None or method.upper() in [m.upper() for m in methods]:
                    matched_feature = feature
                    break

        if matched_feature is None:
            # 不在限制列表中 → 直接放行
            return await call_next(request)

        # 获取用户 ID
        user_id = _get_user_id_from_request(request)
        if user_id is None:
            # 匿名用户 → 走正常流程（路由层会返回 401）
            return await call_next(request)

        # 检查限制
        allowed, remaining, limit_val = await check_limit(user_id, matched_feature)

        if not allowed:
            logger.info(
                "[UsageLimit] user_id=%s 超限: feature=%s, limit=%s",
                user_id,
                matched_feature,
                limit_val,
            )
            return JSONResponse(
                status_code=402,
                content={
                    "detail": f"您的 {matched_feature} 使用次数已达上限",
                    "code": "USAGE_LIMIT_EXCEEDED",
                    "feature": matched_feature,
                    "limit": limit_val,
                    "remaining": 0,
                    "message": "请升级会员以解锁更多使用次数",
                    "upgrade_url": "/api/v1/membership/upgrade",
                },
                headers={
                    "X-Usage-Limit": str(limit_val),
                    "X-Usage-Remaining": "0",
                    "X-Usage-Feature": matched_feature,
                },
            )

        # 正常请求 — 在响应中记录使用量并附加 Header
        response = await call_next(request)

        # 对于成功的请求（2xx），增加使用计数
        if 200 <= response.status_code < 300:
            try:
                await increment_usage(user_id, matched_feature)
                # 更新 remaining（减 1）
                new_remaining = remaining - 1 if remaining > 0 else remaining
            except Exception:
                # 计数失败不阻塞请求
                new_remaining = remaining
                logger.exception(
                    "[UsageLimit] 增加计数失败: user_id=%s, feature=%s",
                    user_id,
                    matched_feature,
                )

            response.headers["X-Usage-Limit"] = str(limit_val)
            response.headers["X-Usage-Remaining"] = str(new_remaining)
            response.headers["X-Usage-Feature"] = matched_feature

        return response
