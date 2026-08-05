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
        get_metrics_instance,
        init_otel,
        SentryExceptionMiddleware,
        DetailToMessageMiddleware,
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
    # Sentry 异常捕获中间件 — 兜底捕获所有未处理异常并上报 Sentry
    app.add_middleware(SentryExceptionMiddleware)
    app.add_middleware(DetailToMessageMiddleware)
    app.add_middleware(LoggingMiddleware)

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
                                 match_router, brochure_alias_router, card_alias_router, visitor_router,
                            trust_router, i18n_router, public_router, payment_router,
                            integration_router, export_router, webhook_router,
                            recommend_router, ab_test_router, api_keys_router,
                            docs_router, web_vitals_router, graphql_router,
                            oauth_router, admin_router, ai_assist_router)
    from app.routers.miniapp_router import (
        router as miniapp_router,
        exchange_alt_router as miniapp_exchange_router,
        recommend_router as miniapp_recommend_router,
        miniapp_code_router,
    )
    from app.routers.graphql_route import strawberry_app
    from app.routers.tenant_api import router as tenant_router
    from app.routers.developer import router as developer_router
    from app.routers.messages import router as message_router
    from app.routers.invoice import router as invoice_router
    from app.routers.knowledge_graph import router as knowledge_graph_router
    from app.routers.subscription_router import router as subscription_router
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
    from app.routers.platform_router import router as platform_router
    from app.routers.connection_router import router as connection_router
    # ── 链客宝合并路由 ──
    from app.routers.organization_router import router as organization_router
    from app.routers.six_degrees_router import router as six_degrees_router
    from app.routers.escrow_router import router as escrow_router
    from app.routers.ocr_router import router as ocr_router
    from app.routers.pdf_router import router as pdf_router
    from app.routers.security_scan import router as security_scan_router
    from app.routers.skill_registry import router as skill_registry_router
    # ── CloakBrowser 智能爬虫 ──
    from app.routers.cloak_scraper import router as cloak_scraper_router
    from app.routers.progressive_search_router import router as progressive_search_router
    from app.routers.task_slicer_router import router as task_slicer_router
    # ── Crawlee 名片爬虫服务 ──
    from app.routers.crawlee_router import router as crawlee_router
    # ── F10 智能Agent指挥官调度层 ──
    from app.routers.commander_router import router as commander_router
    from app.routers.circuit_breaker_router import router as circuit_breaker_router
    # ── F11 分制-压缩流水线 ──
    from app.routers.compression_router import router as compression_router
    # ── F13 Token 预算指令系统 ──
    from app.routers.token_budget_router import router as token_budget_router
    # ── F12 Prompt分治模板库 ──
    from app.routers.prompt_router import router as prompt_router
    # ── F14 工具规则装饰器 ──
    from app.routers.tool_rules_router import router as tool_rules_router
    # ── F21 Agent化任务决策矩阵 ──
    from app.routers.decision_matrix_router import router as decision_matrix_router
    # ── IM 桥接适配器 (企微 / 钉钉) ──
    from app.routers.im_bridge import router as im_bridge_router
    # ── F19 Token 消耗分析仪表盘 ──
    from app.routers.token_analytics_router import router as token_analytics_router
    # ── F17 灰度发布平台 (彩虹部署) ──
    from app.routers.canary_router import router as canary_router
    # ── F18 Agent质量评估看板 ──
    from app.routers.quality_router import router as quality_router
    # ── F16 异步任务 Checkpoint 恢复 ──
    from app.routers.checkpoint_router import router as checkpoint_router
    # ── F20 名片Agent准确率门禁 ──
    from app.routers.accuracy_gate_router import router as accuracy_gate_router
    # ── Dify 工具插件 + 应用编排服务 ──
    from app.routers.dify_tool_routes import router as dify_tool_router

    # ── ds2api 服务模块 — SSE引擎 + 工具调用服务 ──
    from services.sse_engine import SseEngineService, SSEStreamEngine, SSEParser
    from services.tool_call_service import ToolCallService, ToolCallPipeline

    # ── ds4 服务模块 — Engine-Session + 单工作者队列 ──
    from services.ds4_engine_service import ModelEngine, InferenceSession
    from services.ds4_worker_service import WorkerQueue

    # ── DSX 白泽推理引擎 — 7大能力集成 ──
    from services.dsx_service import register_dsx_routes, get_dsx_available
    register_dsx_routes(app)

    # ── 惰性注册：knowledge_models_router
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
    from app.routers.design_qa_router import router as design_qa_router
    _register_knowledge_models(app)  # 惰性注册，避免 routers/__init__.py 循环依赖
    app.include_router(design_qa_router)
    app.include_router(gaia_router)
    app.include_router(platform_router)
    app.include_router(connection_router)
    # ── 链客宝合并路由 ──
    app.include_router(organization_router)
    app.include_router(six_degrees_router)
    app.include_router(escrow_router)
    app.include_router(ocr_router)
    app.include_router(pdf_router)
    app.include_router(security_scan_router)
    app.include_router(crm_router)
    app.include_router(campaign_router)
    app.include_router(prediction_router)
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(brochure_router)
    app.include_router(tag_router)
    app.include_router(ai_assist_router)
    app.include_router(match_router)
    from app.routers.matching import router as matching_router
    app.include_router(matching_router)
    from app.routers.k3_router import router as k3_router
    app.include_router(k3_router)
    from app.routers.transphee import router as transphee_router
    app.include_router(transphee_router)
    from app.routers.inference_gateway import router as inference_gateway_router
    app.include_router(inference_gateway_router)
    app.include_router(brochure_alias_router)
    app.include_router(card_alias_router)
    app.include_router(miniapp_router)
    app.include_router(miniapp_exchange_router)
    app.include_router(miniapp_recommend_router)
    app.include_router(miniapp_code_router)
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
    try:
        from app.routers.xinsen_match import router as xinsen_router
        app.include_router(xinsen_router)
    except ModuleNotFoundError:
        logger.warning("xinsen_match 路由未找到，跳过")
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
    app.include_router(skill_registry_router)
    # ── CloakBrowser 智能爬虫 ──
    app.include_router(cloak_scraper_router)
    app.include_router(progressive_search_router)
    app.include_router(task_slicer_router)
    # ── Crawlee 名片爬虫服务 ──
    app.include_router(crawlee_router)
    app.include_router(circuit_breaker_router)
    # ── F11 分制-压缩流水线 ──
    app.include_router(compression_router)
    # ── F13 Token 预算指令系统 ──
    app.include_router(token_budget_router)
    # ── F12 Prompt分治模板库 ──
    app.include_router(prompt_router)
    # ── F14 工具规则装饰器 ──
    app.include_router(tool_rules_router)
    # ── F21 Agent化任务决策矩阵 ──
    app.include_router(decision_matrix_router)
    # ── F10 智能Agent指挥官调度层 ──
    app.include_router(commander_router)
    # ── IM 桥接适配器 (企微 / 钉钉) ──
    app.include_router(im_bridge_router)
    # ── F17 灰度发布平台 (彩虹部署) ──
    app.include_router(canary_router)
    # ── F18 Agent质量评估看板 ──
    app.include_router(quality_router)
    # ── F19 Token 消耗分析仪表盘 ──
    app.include_router(token_analytics_router)
    # ── F16 异步任务 Checkpoint 恢复 ──
    app.include_router(checkpoint_router)
    # ── F20 名片Agent准确率门禁 ──
    app.include_router(accuracy_gate_router)
    # ── Dify 工具插件 + 应用编排服务 ──
    app.include_router(dify_tool_router)
    # ── F0 多AI Provider Driver 路由 ──
    from app.ai.gateway.provider_router import router as provider_router
    app.include_router(provider_router)

    # ── notification 行业动态推送路由 ──
    from app.routers.notification_router import router as notification_router
    app.include_router(notification_router)

    # ── ds2api 服务健康检查 ──
    from fastapi import APIRouter
    _ds2api_router = APIRouter(prefix="/api/v1/ds2api")

    @_ds2api_router.get("/sse-engine/health")
    async def ds2api_sse_health():
        """SSE引擎服务健康检查"""
        return {
            "status": "ok",
            "service": "sse_engine",
            "version": "1.0.0",
            "loaded": True,
        }

    @_ds2api_router.get("/tool-call/health")
    async def ds2api_toolcall_health():
        """工具调用服务健康检查"""
        return {
            "status": "ok",
            "service": "tool_call_service",
            "version": "1.0.0",
            "loaded": True,
        }

    app.include_router(_ds2api_router)

    # ── MiniMax AI 多模态 ──
    from app.routers.minimax_router import router as minimax_router
    app.include_router(minimax_router)

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
        # ── JWT_SECRET 安全校验 ──────────────────────────────────────
        jwt_secret = cfg.JWT_SECRET
        if not jwt_secret:
            logger.critical("JWT_SECRET 未配置！应用将退出")
            sys.exit(1)
        if jwt_secret in ("change-me", "default", "changeme"):
            logger.critical("JWT_SECRET 使用了占位值 '%s'！请配置强随机密钥。应用将退出", jwt_secret)
            sys.exit(1)
        if len(jwt_secret) < 20:
            logger.warning("JWT_SECRET 长度不足20字符（当前 %d 位），建议使用64位随机密钥", len(jwt_secret))
        else:
            logger.info("JWT_SECRET 安全校验通过 (%d 位)", len(jwt_secret))

        data_dir = os.path.join(os.path.dirname(BASE_DIR), "data")
        os.makedirs(data_dir, exist_ok=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建/验证完成 (async)")

        # Sentry 状态确认
        sentry_dsn = cfg.SENTRY_DSN
        if sentry_dsn:
            logger.info("Sentry 生产监控已启用 (DSN 已配置)")
        else:
            logger.info("Sentry 生产监控未启用 (未配置 SENTRY_DSN，如需启用请在 .env 中设置)")

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

        # 初始化多AI Provider Driver 注册表
        try:
            from app.ai.gateway.provider_manager import init_provider_drivers
            init_provider_drivers()
            logger.info("多AI Provider Driver 注册表初始化完成")
        except Exception as e:
            logger.warning("Provider Driver 初始化失败（降级运行）: %s", e)

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
