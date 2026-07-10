"""AI数字名片 API — 模块化架构入口。"""
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from key_manager import SecretManager
from app.database import engine, Base
_secrets = SecretManager()


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
                environment=_secrets.get("ENV", "development"),
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

    # ── 芯森态Feature: 添加services/到搜索路径 ──
    _svc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services")
    if _svc_path not in sys.path:
        sys.path.insert(0, _svc_path)
        logger.info("芯森态Feature services 已挂载: %s", _svc_path)

    # Lazy imports to avoid circular import chain:
    # app.__init__ → middleware → models → crm → routers → middleware
    from app.middleware import (
        RequestIDMiddleware,
        MetricsMiddleware,
        RateLimiterMiddleware,
        IPRateLimitMiddleware,
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
    from app.middleware import AuditMiddleware
    from app.middleware.tenant import TenantMiddleware
    from app.middleware.rbac import RBACMiddleware
    from app.middleware.sso import SSOMiddleware

    init_sentry(cfg.SENTRY_DSN)
    init_otel()


    # ── 生产环境禁用 API 文档暴露 ──────────────────────────
    _docs_enabled = cfg.docs_enabled


    app = FastAPI(
        title="AI数字名片 API",
        description="AI数字名片后端服务 - 模块化架构",
        version="2.0.0",
        docs_url="/docs" if _docs_enabled else None,
        redoc_url="/redoc" if _docs_enabled else None,
        openapi_url="/openapi.json" if _docs_enabled else None,
    )
    if not _docs_enabled:
        logger.info("生产环境：API文档端点已禁用 (/docs, /redoc, /openapi.json)")

    # Middleware
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(TenantMiddleware)
    app.add_middleware(ApiKeyMiddleware)
    app.add_middleware(RBACMiddleware)
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
    # IP Rate Limiter: 60 req/min per IP, after CORS, before auth
    app.add_middleware(IPRateLimitMiddleware)
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
    app.add_middleware(AuditMiddleware)
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
    from app.crm.marketing_router import router as marketing_router
    from app.crm.report_router import router as report_router
    from app.routers.document import router as document_router
    from app.routers.analytics import router as analytics_router
    from app.routers.metrics_dashboard import router as metrics_dashboard_router
    from app.routers.health import router as health_router
    from app.routers.ai_config import router as ai_config_router
    from app.routers.usage_router import router as usage_router
    from app.routers.token_pricing_router import router as token_pricing_router

    # ── 桥接路由（前后端API路径不一致修复）───────────────
    try:
        from app.routers.bridge_routes import router as bridge_router
        app.include_router(bridge_router)
        logger.info("桥接路由已注册: 10处前后端API路径不一致已修复")
        print("[DEBUG] Bridge router registered with routes:", [r.path for r in bridge_router.routes], flush=True)
    except Exception as e:
        logger.warning("桥接路由注册失败（可降级运行）: %s", e)
        import traceback
        traceback.print_exc()

    # ── 反馈闭环路由 ─────────────────────────────────────
    try:
        from app.routers.feedback_routes import router as feedback_router
        app.include_router(feedback_router)
        logger.info("反馈闭环路由已注册: POST /api/feedback")
    except Exception as e:
        logger.warning("反馈闭环路由注册失败（可降级运行）: %s", e)

    # ── Mock 降级异常处理器
    # 当桥接路由未能捕获的已知前端路径返回 404 时，自动降级返回 Mock 数据
    _MOCK_FALLBACK_PATHS = {
        "/api/v1/brochures/purpose-templates": {
            "templates": [
                {"id": "partner", "name": "找合作伙伴", "icon": "🤝"},
                {"id": "client", "name": "找客户", "icon": "💼"},
                {"id": "investor", "name": "找投资", "icon": "🚀"},
                {"id": "recruiter", "name": "招人才", "icon": "🎯"},
            ]
        },
        "/api/v1/membership/plans": {"plans": []},
        "/api/v1/membership/usage-stats": {"usage": {}, "limits": {}},
    }

    @app.exception_handler(404)
    async def mock_fallback_404_handler(request, exc):
        path = request.url.path
        if path in _MOCK_FALLBACK_PATHS:
            logger.warning("[Mock降级] 404 路径 %s → 返回 Mock 数据", path)
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=200, content=_MOCK_FALLBACK_PATHS[path])
        # 对 /api/v1/ 开头的路径也做通用降级
        if path.startswith("/api/v1/") and not path.startswith("/api/v1/auth/"):
            logger.warning("[Mock降级] 通用 404 路径 %s → 返回空 Mock", path)
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=200, content={"mock": True, "data": []})
        # 非 API 路径的正常 404
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    # ── 500 降级处理器 ──────────────────────────────────
    @app.exception_handler(500)
    async def mock_fallback_500_handler(request, exc):
        path = request.url.path
        logger.error("[Mock降级] 500 错误 path=%s: %s", path, exc)
        if path.startswith("/api/v1/"):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=200, content={"mock": True, "error": "服务暂时不可用，返回Mock数据", "data": []})
        raise exc

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

    # ── SAG / Hybrid / 三管道路由 ──────────────────────────
    try:
        from app.routers.pipeline_router import router as pipeline_router
        app.include_router(pipeline_router)
        logger.info("三管道路由已注册: /api/v1/ai/sag/* /hybrid/* /pipeline/*")
    except Exception as e:
        logger.warning("三管道路由注册失败（可降级运行）: %s", e)

    # ── DeepSeek 代理路由 ──────────────────────────────────────────
    try:
        from app.routers.ai_deepseek import router as ai_deepseek_router
        app.include_router(ai_deepseek_router)
        logger.info("DeepSeek代理路由已注册: /api/v1/ai/deepseek/*")
    except Exception as e:
        logger.warning("DeepSeek代理路由注册失败（可降级运行）: %s", e)

    # ── AI画册生成路由 ──────────────────────────────────────────
    try:
        from app.routers.brochure_generation import router as brochure_gen_router
        app.include_router(brochure_gen_router)
        logger.info("AI画册生成路由已注册: /api/v1/brochure-gen/*")
    except Exception as e:
        logger.warning("AI画册生成路由注册失败（可降级运行）: %s", e)

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
    app.include_router(metrics_dashboard_router)
    app.include_router(health_router)
    app.include_router(ai_config_router)
    from app.routers.design_qa_router import router as design_qa_router
    _register_knowledge_models(app)  # 惰性注册，避免 routers/__init__.py 循环依赖
    app.include_router(design_qa_router)
    app.include_router(gaia_router)
    app.include_router(crm_router)
    app.include_router(campaign_router)
    app.include_router(prediction_router)
    app.include_router(marketing_router)
    app.include_router(report_router)
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
    if _docs_enabled:
        app.include_router(docs_router)
    app.include_router(web_vitals_router)
    app.include_router(graphql_router)
    from app.routers.graphql_route import HAS_STRAWBERRY, strawberry_app
    if HAS_STRAWBERRY and strawberry_app is not None:
        app.include_router(strawberry_app, prefix="/graphql")
    app.include_router(oauth_router)
    app.include_router(admin_router)

    # ── NFC 名片路由 ─────────────────────────────────────────
    try:
        from app.routers.nfc import router as nfc_router
        app.include_router(nfc_router, prefix="/api/v1/nfc")
        logger.info("NFC 路由已注册: /api/v1/nfc/*")
    except Exception as e:
        logger.warning("NFC 路由注册失败（可降级运行）: %s", e)

    # ── 翻译管理路由 ─────────────────────────────────────────
    try:
        from app.routers.translation_admin import router as translation_admin_router
        app.include_router(translation_admin_router)
        logger.info("翻译管理路由已注册: /api/admin/translations/*")
    except Exception as e:
        logger.warning("翻译管理路由注册失败（可降级运行）: %s", e)

    app.include_router(tenant_router)
    app.include_router(developer_router)
    app.include_router(message_router)
    app.include_router(invoice_router)
    app.include_router(knowledge_graph_router)
    app.include_router(subscription_router)
    app.include_router(membership_router)
    # ── A08 扫码建联路由 ─────────────────────────
    try:
        from app.routers.social_connect_router import router as social_connect_router
        app.include_router(social_connect_router)
        logger.info("扫码建联路由已注册: /api/v1/scan/*")
    except Exception as e:
        logger.warning("扫码建联路由注册失败（可降级运行）: %s", e)

    # ── 资源平台商业化路由 ─────────────────────────
    try:
        from app.routers.resource_platform_router import router as resource_platform_router
        app.include_router(resource_platform_router)
        logger.info("资源平台路由已注册: /api/v1/platforms/*")
    except Exception as e:
        logger.warning("资源平台路由注册失败（可降级运行）: %s", e)

    app.include_router(usage_router)
    app.include_router(token_pricing_router)
    logger.info("Token定价路由已注册: /api/v1/token/*")

    # ── AI 用量监控路由 ────────────────────────────────────────
    try:
        from app.routers.ai_metrics_router import router as ai_metrics_router
        app.include_router(ai_metrics_router)
        logger.info("AI用量监控路由已注册: /api/v1/ai/metrics/*")
    except Exception as e:
        logger.warning("AI指标路由注册失败（可降级运行）: %s", e)

    # ── 模型部署（Canary）路由 ──────────────────────────
    try:
        from app.routers.model_deploy_router import router as deploy_router
        app.include_router(deploy_router)
        logger.info("模型部署路由已注册: /api/v1/deploy/*")
    except Exception as e:
        logger.warning("模型部署路由注册失败（可降级运行）: %s", e)
    # ── 芯森态Feature: 管理中心API ──────────────────────────
    try:
        from services.feature_manager import get_registry
        _freg = get_registry()
        _fc = len(_freg.list())
        logger.info("芯森态Feature管理中心: %d 个Feature已注册", _fc)
    except Exception as e:
        logger.warning("Feature管理中心初始化失败: %s", e)



    # ── 芯森态Feature: RBAC权限路由 ──────────────────────────
    try:
        from backend.app.routers.rbac_router import router as rbac_router
        app.include_router(rbac_router, prefix="/api/admin", tags=["RBAC"])
        logger.info("芯森态RBAC路由已注册: /api/admin/roles/*")
    except Exception as e:
        logger.warning("RBAC路由注册失败（可降级运行）: %s", e)

    # ── 芯森态Feature: BGE嵌入预热 ──────────────────────────
    try:
        from services.embedding_service import get_embedding_service
        _bge = get_embedding_service(dim=512)
        _bge.embed("预热")
        logger.info("芯森态BGE嵌入引擎已预热 (512维)")
    except Exception as e:
        logger.info("BGE嵌入引擎未就绪（使用hash降级）: %s", e)

    # ── 芯森态Feature: 告警监控 ──────────────────────────
    try:
        from services.monitor import send_alert
        logger.info("芯森态飞书告警通道已就绪")
    except Exception as e:
        logger.info("飞书告警通道未就绪: %s", e)

    # ── 实时协作路由 ──────────────────────────────────────────
    try:
        from app.routers.collaboration import router as collaboration_router
        app.include_router(collaboration_router)
        logger.info("协作路由已注册: /api/collaboration/*")
    except Exception as e:
        logger.warning("协作路由注册失败（可降级运行）: %s", e)

    # ── 统一 User Profile 路由 ──────────────────────────────
    try:
        from app.routers.profile_unified import router as profile_unified_router
        app.include_router(profile_unified_router)
        logger.info("统一User Profile路由已注册: /api/unified/profile/*")
    except Exception as e:
        logger.warning("统一User Profile路由注册失败（可降级运行）: %s", e)

    # ── App Store 路由 ─────────────────────────────────────
    try:
        from app.routers.app_store import router as app_store_router
        app.include_router(app_store_router)
        logger.info("App Store 路由已注册: /api/v1/app-store/*")
    except Exception as e:
        logger.warning("App Store 路由注册失败: %s", e)

    # ── Agent 活跃看板路由 ──────────────────────────
    try:
        from app.routers.agent_dashboard_router import router as agent_dashboard_router
        app.include_router(agent_dashboard_router)
        logger.info("Agent活跃看板路由已注册: /api/v1/admin/agents/*")
    except Exception as e:
        logger.warning("Agent活跃看板路由注册失败（可降级运行）: %s", e)

    # ── App Store Marketplace 路由 ──────────────────────────
    try:
        from app.routers.app_store_marketplace import router as app_store_marketplace_router
        app.include_router(app_store_marketplace_router)
        logger.info("应用市场路由已注册: /api/v1/marketplace/*")
    except Exception as e:
        logger.warning("应用市场路由注册失败: %s", e)

    # ── 批量 IO 路由（CSV 导入/导出） ──────────────────────
    try:
        from app.routers.bulk_io import router as bulk_io_router
        app.include_router(bulk_io_router)
        logger.info("批量 IO 路由已注册: /api/admin/bulk/*")
    except Exception as e:
        logger.warning("批量 IO 路由注册失败（可降级运行）: %s", e)

    # Static
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(BASE_DIR, "templates")
    static_dir = os.path.join(BASE_DIR, "static")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # 前端静态文件
    frontend_dist = os.path.join(os.path.dirname(BASE_DIR), "..", "frontend", "dist")
    frontend_dist = os.path.normpath(frontend_dist)
    if os.path.isdir(os.path.join(frontend_dist, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="frontend_assets")
    if os.path.isdir(os.path.join(frontend_dist, "icons")):
        app.mount("/icons", StaticFiles(directory=os.path.join(frontend_dist, "icons")), name="frontend_icons")

    # Frontend routes - 首页改为SPA
    @app.get("/", response_class=HTMLResponse)
    async def root():
        frontend_index = os.path.join(frontend_dist, "index.html")
        if os.path.isfile(frontend_index):
            with open(frontend_index, encoding="utf-8") as f:
                return HTMLResponse(f.read())
        return JSONResponse({"service": "AI数智名片", "version": "3.4.0", "status": "ok"})

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
            except ValueError as e:
                from fastapi.responses import HTMLResponse as _HTMLResponse
                error_msg = str(e)
                status_code = 404 if "不存在" in error_msg or "失效" in error_msg else 503
                return _HTMLResponse(
                    content=f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>画册暂时无法加载 - AI数字名片</title>
<style>body{{font-family:-apple-system,sans-serif;background:#0f0c29;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:20px}}
h1{{font-size:24px;margin-bottom:12px;background:linear-gradient(90deg,#f093fb,#f5576c);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
p{{color:rgba(255,255,255,0.6);margin-bottom:20px;line-height:1.6}}
.btn{{display:inline-block;background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);color:#fff;padding:10px 28px;border-radius:24px;text-decoration:none;font-size:14px;transition:all 0.3s}}
.btn:hover{{background:rgba(255,255,255,0.2);transform:translateY(-1px)}}</style>
</head>
<body>
<h1>{"😕 画册不存在" if status_code == 404 else "⏳ 画册暂时无法加载"}</h1>
<p>{"该画册链接已失效或已被删除" if status_code == 404 else error_msg + "<br>请稍后刷新重试"}</p>
<a href="/" class="btn">返回首页</a>
</body>
</html>""",
                    status_code=status_code,
                )
            except Exception:
                logger.exception("画册查看页未知异常: share_token=%s", share_token)
                from fastapi.responses import HTMLResponse as _HTMLResponse
                return _HTMLResponse(
                    content="""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>画册暂时无法加载 - AI数字名片</title>
<style>body{font-family:-apple-system,sans-serif;background:#0f0c29;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:20px}
h1{font-size:24px;margin-bottom:12px;background:linear-gradient(90deg,#f093fb,#f5576c);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
p{color:rgba(255,255,255,0.6);margin-bottom:20px;line-height:1.6}
.btn{display:inline-block;background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);color:#fff;padding:10px 28px;border-radius:24px;text-decoration:none;font-size:14px;transition:all 0.3s}
.btn:hover{background:rgba(255,255,255,0.2);transform:translateY(-1px)}
.icon-spin{display:inline-block;animation:spin 2s linear infinite;font-size:48px}
@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}</style>
</head>
<body>
<div class="icon-spin">⏳</div>
<h1>画册暂时无法加载</h1>
<p>系统繁忙，请稍后刷新重试</p>
<a href="javascript:location.reload()" class="btn">重新加载</a>
<br><br>
<a href="/" class="btn" style="background:transparent;border-color:rgba(255,255,255,0.1)">返回首页</a>
</body>
</html>""",
                    status_code=503,
                )

    # API endpoints
    # GET /health is provided by routers/health.py (simple "OK" plaintext)
    # GET /api/health returns JSON with version + status for monitoring
    @app.get("/api/health")
    def api_health():
        from fastapi.responses import JSONResponse
        return JSONResponse({"status": "ok", "service": "ai-digital-brochure", "version": "3.4.0"})

    if _docs_enabled:
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
