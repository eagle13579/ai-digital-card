"""Sentry exception capture middleware for FastAPI.
捕获未处理的请求异常并上报到 Sentry。
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger(__name__)


class SentryExceptionMiddleware(BaseHTTPMiddleware):
    """捕获 FastAPI 请求处理中的未处理异常并上报 Sentry。

    配合 app/__init__.py 中的 init_sentry() 使用。
    当 Sentry SDK 已初始化时，异常会自动上报；
    未初始化（SENTRY_DSN 未配置）时静默降级，不影响业务。
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            # 将异常注入 Sentry scope 并捕获
            # 即使 sentry_sdk 未初始化，此操作也是安全的
            try:
                import sentry_sdk

                with sentry_sdk.push_scope() as scope:
                    scope.set_tag("middleware", "sentry_exception")
                    scope.set_context(
                        "request",
                        {
                            "url": str(request.url),
                            "method": request.method,
                            "headers": dict(request.headers),
                            "client_host": request.client.host if request.client else None,
                        },
                    )
                    sentry_sdk.capture_exception(exc)
                logger.exception("Sentry middleware caught unhandled exception")
            except ImportError:
                logger.debug("sentry_sdk not installed, skipping exception capture")
            except Exception as send_err:
                logger.warning("Sentry exception上报失败: %s", send_err)

            # 返回通用 500 错误，不暴露内部细节
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )


# 快捷引用，方便其他模块使用
__all__ = ["SentryExceptionMiddleware"]
