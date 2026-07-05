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
    """Rewrite /api/v1/xxx -> /api/xxx at ASGI scope level.
    Routes are registered under /api/xxx, so we just strip the /v1 part."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope["path"]
            if path.startswith("/api/v1/"):
                # /api/v1/brochures -> /api/brochures
                scope["path"] = "/api/" + path[8:]
                scope["raw_path"] = scope["path"].encode()
        await self.app(scope, receive, send)


def create_app():
    """Create and configure FastAPI app instance."""
    from app.config import settings as cfg

    # Lazy imports to avoid circular import chain:
    # app.__init__ → middleware → models → crm → routers → middleware
    from app.middleware import (
        RequestIDMiddleware,
        MetricsMiddleware,
        RateLimiterMiddleware,
        I18nMiddleware,
        ApiKeyMiddleware,
        LoggingMiddleware,
        SecurityHeadersMiddleware,
        CsrfMiddleware,
        UsageLimitMiddleware,
        get_metrics_instance,
        init_otel,
    )
    from app.middleware.api_version import APIVersionRedirectMiddleware

    init_sentry(cfg.SENTRY_DSN)
    init_otel()

    app = FastAPI(title="AI数字名片 API", description="AI数字名片后端服务 - 模块化架构", version="2.0.0")

    # Middleware
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(ApiKeyMiddleware)
    app.add_middleware(
        RateLimiterMiddleware,
        limits={"anonymous": 100, "standard": 1000, "enterprise": 10000},
        window_seconds=60,
    )
    app.add_middleware(I18nMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    # APIVersionRedirect: rewrites /api/v1/xxx -> /xxx at ASGI scope level
    app.add_middleware(APIVersionRedirectMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.CORS_ORIGINS.split(",") if cfg.CORS_ORIGINS else [
            "https://liankebao.top", "https://api.liankebao.top",
            "http://localhost:5173", "http://localhost:8200",
        ],
        allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
    )
    app.add_middleware(CsrfMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(UsageLimitMiddleware)

    # FastAPI 集成 (OpenTelemetry) — instrument_app 会在内部跳过若未初始化
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("OpenTelemetry FastAPI 集成注册失败: %s", exc)

    # Routers
    from app.routers import (auth_router, user_router, brochure_router, tag_router,
                             match_router, brochure_alias_router, visitor_router,
                             trust_router, i18n_router, public_router, payment_router,
                             integration_router, export_router, webhook_router,
                             recommend_router, ab_test_router, api_keys_router,
                             docs_router, web_vitals_router, graphql_router,
                             oauth_router, admin_router)
    from app.routers.miniapp_router import (
        router as miniapp_router,
        exchange_alt_router as miniapp_exchange_router,
        recommend_router as miniapp_recommend_router,
    )
    from app.routers.graphql_route import strawberry_app
    from app.routers.tenant_api import router as tenant_router
    from app.routers.developer import router as developer_router
    from app.routers.messages import router as message_router
    from app.routers.invoice import router as invoice_router
    from app.routers.knowledge_graph import router as knowledge_graph_router
    from app.routers.subscription_router import router as subscription_router
    from app.routers.membership import router as membership_router
    from app.routers.gaia_router import router as gaia_router
    from app.crm.crm_router import router as crm_router
    from app.crm.campaign_router import router as campaign_router
    from app.crm.prediction_router import router as prediction_router
    from app.routers.bot_router import router as bot_router
    from app.routers.learning_router import router as learning_router
    from app.routers.v1_deprecated import router as v1_deprecated_router
    from app.crm.form_capture_router import router as form_capture_router
    from app.routers.document import router as document_router
    from app.routers.analytics import router as analytics_router
    from app.routers.health import router as health_router

    # ── AI助手路由 ──────────────────────────────────────────
    # ai_assist_router 已在 routers/__init__.py 中导入，直接注册
    try:
        from app.routers.ai_assist import router as ai_assist_router
        app.include_router(ai_assist_router)
        logger.info("AI助手路由已注册: /api/v1/ai/assist/*")
    except Exception as e:
        logger.warning("AI助手路由注册失败（可降级运行）: %s", e)

    # ── AI对话路由 ──────────────────────────────────────────
    try:
        from app.routers.ai_chat import router as ai_chat_router
        app.include_router(ai_chat_router)
        logger.info("AI对话路由已注册: /api/v1/ai/chat")
    except Exception as e:
        logger.warning("AI对话路由注册失败（可降级运行）: %s", e)

    # ── DeepSeek 代理路由 ──────────────────────────────────────────
    try:
        from app.routers.ai_deepseek import router as ai_deepseek_router
        app.include_router(ai_deepseek_router)
        logger.info("DeepSeek代理路由已注册: /api/v1/ai/deepseek/*")
    except Exception as e:
        logger.warning("DeepSeek代理路由注册失败（可降级运行）: %s", e)

    # ── 惰性注册：knowledge_models_router ──────────────────────────
    # 故意不加入 routers/__init__.py 以避免 via ai_assist → auth 的循环依赖
    def _register_knowledge_models(app):
        from app.routers.knowledge_models_router import router as km_router
        app.include_router(km_router)

    app.include_router(bot_router)
    app.include_router(learning_router)
    app.include_router(v1_deprecated_router)
    app.include_router(form_capture_router)
    app.include_router(document_router)
    app.include_router(analytics_router)
    app.include_router(health_router)
    from app.routers.design_qa_router import router as design_qa_router
    _register_knowledge_models(app)  # 惰性注册，避免 routers/__init__.py 循环依赖
    app.include_router(design_qa_router)
    app.include_router(gaia_router)
    app.include_router(crm_router)
    app.include_router(campaign_router)
    app.include_router(prediction_router)
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(brochure_router)
    app.include_router(tag_router)
    app.include_router(match_router)
    app.include_router(brochure_alias_router)
    app.include_router(miniapp_router)
    app.include_router(miniapp_exchange_router)
    app.include_router(miniapp_recommend_router)
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
    app.include_router(docs_router)
    app.include_router(web_vitals_router)
    app.include_router(graphql_router)
    from app.routers.graphql_route import HAS_STRAWBERRY, strawberry_app
    if HAS_STRAWBERRY and strawberry_app is not None:
        app.include_router(strawberry_app, prefix="/graphql")
    app.include_router(oauth_router)
    app.include_router(admin_router)
    app.include_router(tenant_router)
    app.include_router(developer_router)
    app.include_router(message_router)
    app.include_router(invoice_router)
    app.include_router(knowledge_graph_router)
    app.include_router(subscription_router)
    app.include_router(membership_router)

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
    async def brochure_viewer(share_token: str):
        """公开画册翻页查看页 — StPageFlip 渲染 + 小程序引导"""
        from app.database import AsyncSessionLocal
        from app.services.brochure_viewer import render_public_brochure_html

        async with AsyncSessionLocal() as db:
            try:
                html = await render_public_brochure_html(db, share_token)
                return HTMLResponse(content=html)
            except ValueError:
                from fastapi.responses import HTMLResponse as _HTMLResponse
                return _HTMLResponse(
                    content="""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>画册不存在 - AI数字名片</title>
<style>body{font-family:-apple-system,sans-serif;background:#0f0c29;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:20px}
h1{font-size:24px;margin-bottom:12px;background:linear-gradient(90deg,#f093fb,#f5576c);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
p{color:rgba(255,255,255,0.6);margin-bottom:20px}
.btn{background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);color:#fff;padding:10px 28px;border-radius:24px;text-decoration:none;font-size:14px}</style>
</head>
<body>
<h1>😕 画册不存在</h1>
<p>该画册链接已失效或已被删除</p>
<a href="/" class="btn">返回首页</a>
</body>
</html>""",
                    status_code=404,
                )

    # API endpoints
    @app.get("/health", response_class=PlainTextResponse)
    def health():
        return "OK"

    @app.get("/api/health")
    def api_health():
        from fastapi.responses import JSONResponse
        return JSONResponse({"status": "ok", "service": "ai-digital-brochure", "version": "3.4.0"})

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics():
        """Prometheus 指标端点 — 同时暴露 APM 中间件指标和业务指标。"""
        parts: list[str] = []

        # 1. 中间件 APM 指标（请求数、延迟、活跃请求等）
        from app.middleware.metrics import get_metrics_instance as get_apm
        mi = get_apm()
        if mi:
            parts.append(mi.generate_metrics())
        else:
            parts.append("# APM metrics unavailable")

        # 2. 业务指标（prometheus_client）
        from app.business_metrics import generate_business_metrics
        parts.append(generate_business_metrics())

        return PlainTextResponse("\n".join(parts))

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

        # 初始化异步任务队列
        try:
            from task_queue import init_task_queue
            await init_task_queue(
                max_workers=cfg.TASK_QUEUE_MAX_WORKERS,
                max_queue_size=cfg.TASK_QUEUE_MAX_SIZE,
            )
        except Exception as e:
            logger.warning("任务队列初始化失败（降级运行）: %s", e)

    # Shutdown
    @app.on_event("shutdown")
    async def shutdown():
        from app.services.webhook_dispatcher import webhook_dispatcher
        try:
            await webhook_dispatcher.close()
            logger.info("Webhook HTTP 客户端已关闭")
        except Exception as e:
            logger.exception("Webhook 关闭异常: %s", e)

        # 关闭异步任务队列
        try:
            from task_queue import shutdown_task_queue
            await shutdown_task_queue()
        except Exception as e:
            logger.exception("任务队列关闭异常: %s", e)

    return app
