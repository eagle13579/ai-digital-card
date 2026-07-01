"""AI数字名片 API — 模块化架构入口。"""
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.middleware import (
    RequestIDMiddleware,
    MetricsMiddleware,
    get_metrics_instance,
    RateLimiterMiddleware,
    I18nMiddleware,
    ApiKeyMiddleware,
)


def init_sentry(dsn: str = "") -> None:
    """Initialize Sentry SDK with production-grade configuration.

    配置说明:
      - traces_sample_rate: 生产预热阶段用 1.0，稳定后改为 0.2（20% 采样）
      - request_id 自动注入 Sentry scope 用于问题追踪
      - 集成 FastAPI / SQLAlchemy / Logging 三大集成
    """
    if dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration

            # 日志集成: 捕获 >= WARNING 级别的日志作为 Sentry event
            sentry_logging = LoggingIntegration(
                level=logging.INFO,       # 捕获 INFO 及以上日志
                event_level=logging.ERROR  # 将 ERROR 及以上提升为 Sentry Event
            )

            sentry_sdk.init(
                dsn=dsn,
                integrations=[
                    FastApiIntegration(),
                    SqlalchemyIntegration(),
                    sentry_logging,
                ],
                # 生产预热阶段使用 1.0，稳定后改为 0.2
                traces_sample_rate=1.0,  # TODO: 生产稳定后改为 0.2
                environment=os.getenv("ENV", "development"),
                # 自动注入 request_id 到 Sentry scope
                before_send=lambda event, hint: _inject_request_id(event, hint),
            )
            logger.info("Sentry SDK 初始化完成 (DSN=%s...)", dsn[:20] if len(dsn) > 20 else dsn)
        except ImportError as exc:
            logger.warning("sentry_sdk 未安装，跳过 Sentry 初始化: %s", exc)
        except Exception as exc:
            logger.warning("Sentry 初始化失败: %s", exc)


def _inject_request_id(event: dict, hint: dict) -> dict:
    """将当前请求的 request_id 注入到 Sentry event 的 tags 中。"""
    try:
        from app.middleware.request_id import request_id_var
        rid = request_id_var.get()
        if rid:
            event.setdefault("tags", {})["request_id"] = rid
    except Exception:
        pass
    return event


class APIVersionRedirectMiddleware:
    """Redirect /api/v1/xxx -> /xxx and /api/xxx -> /xxx (backward compat)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope["path"]
            if path.startswith("/api/v1/"):
                scope["path"] = path[8:]
                scope["raw_path"] = scope["path"].encode()
            elif path.startswith("/api/") and not path.startswith("/api/v1/"):
                scope["path"] = "/" + path[5:]
                scope["raw_path"] = scope["path"].encode()
        await self.app(scope, receive, send)


def create_app():
    """Create and configure FastAPI app instance."""
    from app.config import settings as cfg

    init_sentry(cfg.SENTRY_DSN)

    app = FastAPI(title="AI数字名片 API", description="AI数字名片后端服务 - 模块化架构", version="2.0.0")

    # Middleware
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(ApiKeyMiddleware)
    app.add_middleware(RateLimiterMiddleware, max_requests=1000, window_seconds=60)
    app.add_middleware(I18nMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.CORS_ORIGINS.split(",") if cfg.CORS_ORIGINS else ["*"],
        allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
    )

    # Routers
    from app.routers import (auth_router, user_router, brochure_router, tag_router,
                             match_router, brochure_alias_router, visitor_router,
                             trust_router, i18n_router, public_router, payment_router,
                             integration_router, export_router, webhook_router,
                             recommend_router, ab_test_router, api_keys_router)
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(brochure_router)
    app.include_router(tag_router)
    app.include_router(match_router)
    app.include_router(brochure_alias_router)
    app.include_router(visitor_router)
    app.include_router(trust_router)
    app.include_router(i18n_router)
    app.include_router(public_router)
    app.include_router(payment_router)
    app.include_router(integration_router)
    app.include_router(export_router)
    app.include_router(webhook_router)
    app.include_router(recommend_router)
    app.include_router(ab_test_router)
    app.include_router(api_keys_router)

    # Static
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(BASE_DIR, "templates")
    static_dir = os.path.join(BASE_DIR, "static")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Frontend routes
    @app.get("/", response_class=HTMLResponse)
    def index():
        with open(os.path.join(templates_dir, "index.html"), encoding="utf-8") as f:
            return HTMLResponse(f.read())

    @app.get("/card-editor", response_class=HTMLResponse)
    def card_editor():
        with open(os.path.join(templates_dir, "card_editor.html"), encoding="utf-8") as f:
            return HTMLResponse(f.read())

    @app.get("/offline", response_class=HTMLResponse)
    def offline():
        with open(os.path.join(templates_dir, "offline.html"), encoding="utf-8") as f:
            return HTMLResponse(f.read())

    @app.get("/view/{share_token}", response_class=HTMLResponse)
    def brochure_viewer(share_token: str):
        with open(os.path.join(templates_dir, "brochure_viewer.html"), encoding="utf-8") as f:
            return HTMLResponse(f.read())

    # API endpoints
    @app.get("/health", response_class=PlainTextResponse)
    def health():
        return "OK"

    @app.get("/api/health")
    def api_health():
        from fastapi.responses import JSONResponse
        return JSONResponse({"status": "ok", "service": "digital_brochure"})

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics():
        mi = get_metrics_instance()
        return PlainTextResponse(mi.generate_metrics() if mi else "# metrics unavailable")

    # Startup
    @app.on_event("startup")
    async def startup():
        data_dir = os.path.join(os.path.dirname(BASE_DIR), "data")
        os.makedirs(data_dir, exist_ok=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建/验证完成 (async)")

        # 初始化 Redis 缓存层
        try:
            from app.cache import init_cache
            init_cache(
                redis_host=cfg.REDIS_HOST,
                redis_port=cfg.REDIS_PORT,
                redis_db=cfg.REDIS_DB,
                redis_password=cfg.REDIS_PASSWORD,
                redis_max_connections=cfg.REDIS_MAX_CONNECTIONS,
            )
        except Exception as e:
            logger.warning("Redis 初始化失败（降级运行）: %s", e)

    # Shutdown
    @app.on_event("shutdown")
    async def shutdown():
        from app.services.webhook_dispatcher import webhook_dispatcher
        try:
            await webhook_dispatcher.close()
            logger.info("Webhook HTTP 客户端已关闭")
        except Exception as e:
            logger.exception("Webhook 关闭异常: %s", e)

    return app
