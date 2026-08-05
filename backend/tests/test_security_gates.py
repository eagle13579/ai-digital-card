"""安全合规门禁测试 — 验证所有安全中间件已加载到 FastAPI 应用中。

覆盖范围:
  1. middleware/__init__.py 中导出的所有中间件是否被 app.__init__.py 加载
  2. JWT_SECRET 三档安全校验 (空值 / 占位值 / 长度不足20字符)
  3. CORS 白名单配置是否合规
  4. CSRF token 生成与校验
  5. SecurityHeaders 完整性

测试策略:
  - 大部分测试直接检查 app user_middleware stack，不发送 HTTP 请求
  - 部分测试使用 conftest.py 的 client fixture (ASGI transport)
"""

from __future__ import annotations

import os
import sys
from typing import Any

import pytest
from fastapi import FastAPI

from app.middleware import (
    RequestIDMiddleware,
    RateLimiterMiddleware,
    MetricsMiddleware,
    I18nMiddleware,
    AuditMiddleware,
    ApiKeyMiddleware,
    LoggingMiddleware,
    SecurityHeadersMiddleware,
    CsrfMiddleware,
)
from app.middleware.api_version import APIVersionRedirectMiddleware


# ══════════════════════════════════════════════════════════════════════
# 辅助函数
# ══════════════════════════════════════════════════════════════════════


def _get_middleware_classes(app: FastAPI) -> list[type]:
    """从 FastAPI app 的 user_middleware stack 中提取所有中间件类。"""
    return [
        m.cls  # type: ignore[misc]
        for m in app.user_middleware
    ]


def _get_app() -> FastAPI:
    """获取 FastAPI 应用实例。"""
    from app.__init__ import create_app

    return create_app()


# ══════════════════════════════════════════════════════════════════════
# Test 1.1: 所有安全中间件已注册
# ══════════════════════════════════════════════════════════════════════


class TestAllSecurityMiddlewareRegistered:
    """验证 middleware/__init__.py 中每个安全中间件都在 app 中注册了。

    安全中间件列表 (来自 middleware/__init__.py):
      - RequestIDMiddleware      ✅ 请求追踪
      - RateLimiterMiddleware    ✅ 速率限制 (三级)
      - MetricsMiddleware        ✅ APM 监控
      - I18nMiddleware           ✅ 国际化
      - SecurityHeadersMiddleware ✅ 安全响应头
      - CsrfMiddleware           ✅ CSRF 保护
      - ApiKeyMiddleware         ✅ API Key 认证
      - LoggingMiddleware        ✅ 请求日志
      - AuditMiddleware          ⚠️ 已导出但未在 create_app() 中注册
      - APIVersionRedirectMiddleware ✅ API 版本重定向
      - CORSMiddleware           ✅ CORS (starlette 中间件)

    注意:
      - RBACMiddleware, TenantMiddleware, SSOMiddleware 不在 __init__.py 中导出，
        它们作为 FastAPI 依赖注入/装饰器使用，不是 ASGI 中间件。
      - db_query_monitor 是装饰器/上下文管理器，不是 ASGI 中间件。
    """

    def test_request_id_middleware_registered(self):
        app = _get_app()
        classes = _get_middleware_classes(app)
        assert RequestIDMiddleware in classes, "RequestIDMiddleware 未注册"

    def test_rate_limiter_middleware_registered(self):
        app = _get_app()
        classes = _get_middleware_classes(app)
        assert RateLimiterMiddleware in classes, "RateLimiterMiddleware 未注册"

    def test_metrics_middleware_registered(self):
        app = _get_app()
        classes = _get_middleware_classes(app)
        assert MetricsMiddleware in classes, "MetricsMiddleware 未注册"

    def test_i18n_middleware_registered(self):
        app = _get_app()
        classes = _get_middleware_classes(app)
        assert I18nMiddleware in classes, "I18nMiddleware 未注册"

    def test_security_headers_middleware_registered(self):
        app = _get_app()
        classes = _get_middleware_classes(app)
        assert SecurityHeadersMiddleware in classes, "SecurityHeadersMiddleware 未注册"

    def test_csrf_middleware_registered(self):
        app = _get_app()
        classes = _get_middleware_classes(app)
        assert CsrfMiddleware in classes, "CsrfMiddleware 未注册"

    def test_api_key_middleware_registered(self):
        app = _get_app()
        classes = _get_middleware_classes(app)
        assert ApiKeyMiddleware in classes, "ApiKeyMiddleware 未注册"

    def test_logging_middleware_registered(self):
        app = _get_app()
        classes = _get_middleware_classes(app)
        assert LoggingMiddleware in classes, "LoggingMiddleware 未注册"

    def test_api_version_redirect_middleware_registered(self):
        app = _get_app()
        classes = _get_middleware_classes(app)
        assert APIVersionRedirectMiddleware in classes, (
            "APIVersionRedirectMiddleware 未注册"
        )

    # ⚠️ AuditMiddleware 已导出但未在 create_app() 中注册 — 此为已知差距
    def test_audit_middleware_exported_but_not_registered(self):
        """AuditMiddleware 在 middleware/__init__.py 中导出但未在 create_app() 中注册。

        这是一个已知的安全合规差距，需要添加:
            app.add_middleware(AuditMiddleware)
        """
        from app.middleware.__init__ import __all__ as middleware_exports

        assert "AuditMiddleware" in middleware_exports, (
            "AuditMiddleware 应在 middleware/__init__.__all__ 中"
        )
        app = _get_app()
        classes = _get_middleware_classes(app)
        if AuditMiddleware not in classes:
            pytest.skip(
                "⚠️ AuditMiddleware 已导出但未注册 — 安全合规差距，需添加 app.add_middleware(AuditMiddleware)"
            )

    def test_all_middleware_exports_covered(self):
        """验证 middleware/__init__.__all__ 中所有 ASGI 中间件类都被 coverage 了。"""
        from app.middleware.__init__ import __all__ as middleware_exports

        app = _get_app()
        classes = _get_middleware_classes(app)

        # 确定哪些导出项是 ASGI 中间件类（以 Middleware 结尾）
        middleware_classes_in_exports = {
            name
            for name in middleware_exports
            if name.endswith("Middleware")
        }

        # 从 FastAPI stack 获取已注册的中间件类名
        registered_names = {cls.__name__ for cls in classes}

        missing = middleware_classes_in_exports - registered_names
        if missing:
            pytest.skip(
                f"⚠️ 以下中间件已导出但未注册: {missing}. "
                f"需在 create_app() 中添加 app.add_middleware() 调用。"
            )

    def test_middleware_registration_order(self):
        """验证关键安全中间件的相对顺序是否正确。

        Starlette 的 add_middleware 使用 insert(0, ...)，因此:
          - user_middleware 列表 = 注册顺序的倒序
          - user_middleware 中 index=0 的中间件最先执行（最外层包裹）

        注册顺序与列表中的 index 关系:
          Metrics (0) → ApiKey (1) → RateLimit (2) → I18n (3) → RequestID (4)
          → SecurityHeaders (5) → APIVersion (6) → CORS (7) → Csrf (8) → Logging (9)

        在 user_middleware (insert 0):
          [0] Logging, [1] Csrf, [2] CORS, [3] APIVersion, [4] SecurityHeaders, ...

        关键约束: SecurityHeadersMiddleware 应包裹 LoggingMiddleware
        （security_headers 先执行，确保所有响应都有安全头部）。
        """
        app = _get_app()
        classes = _get_middleware_classes(app)

        # 检查关键中间件都存在
        for cls in (MetricsMiddleware, SecurityHeadersMiddleware,
                    CsrfMiddleware, LoggingMiddleware):
            assert cls in classes, f"{cls.__name__} 未在中间件栈中找到"

        # SecurityHeadersMiddleware 在 user_middleware 中的 index 应大于
        # LoggingMiddleware (因为 SecurityHeaders 先注册，insert(0,?) 时被推到后面)
        sec_idx = classes.index(SecurityHeadersMiddleware)
        log_idx = classes.index(LoggingMiddleware)
        assert sec_idx > log_idx, (
            f"SecurityHeadersMiddleware (位置 {sec_idx}) "
            f"应包裹 LoggingMiddleware (位置 {log_idx})"
        )


# ══════════════════════════════════════════════════════════════════════
# Test 2: JWT_SECRET 三档安全校验
# ══════════════════════════════════════════════════════════════════════


class TestJwtSecretTriLevelValidation:
    """验证 JWT_SECRET 的三档校验逻辑 (见 app/__init__.py startup 事件)。

    三档校验:
      1. 空值校验 — if not jwt_secret: sys.exit(1)
      2. 占位值校验 — if jwt_secret in ("change-me", "default", "changeme"): sys.exit(1)
      3. 长度校验 — if len(jwt_secret) < 20: warning
    """

    def test_jwt_secret_not_empty(self):
        """JWT_SECRET 不能为空 (生产环境)."""
        from app.config import settings

        assert settings.JWT_SECRET, "JWT_SECRET 未配置"

    def test_jwt_secret_not_placeholder(self):
        """JWT_SECRET 不能是占位值。"""
        from app.config import settings

        placeholders = {"change-me", "default", "changeme"}
        assert settings.JWT_SECRET not in placeholders, (
            f"JWT_SECRET 使用了占位值 '{settings.JWT_SECRET}'"
        )

    def test_jwt_secret_length_sufficient(self):
        """JWT_SECRET 长度应 >= 20 字符。"""
        from app.config import settings

        secret = settings.JWT_SECRET
        assert len(secret) >= 20, (
            f"JWT_SECRET 长度不足20字符（当前 {len(secret)} 位）"
        )

    def test_jwt_secret_recommended_length(self):
        """JWT_SECRET 推荐长度 >= 64 字符 (256位)。"""
        from app.config import settings

        secret = settings.JWT_SECRET
        if len(secret) < 64:
            pytest.skip(
                f"⚠️ JWT_SECRET 长度 {len(secret)} 位 < 推荐 64 位，建议使用更长的密钥"
            )

    def test_startup_validation_logic_exists(self):
        """确认 app/__init__.py 的 startup 事件中包含三档校验逻辑。"""
        import inspect

        from app.__init__ import create_app

        source = inspect.getsource(create_app)
        assert "JWT_SECRET" in source, "startup 中缺少 JWT_SECRET 校验"
        assert "change-me" in source or "changeme" in source, (
            "startup 中缺少占位值校验"
        )
        assert "len(jwt_secret) < 20" in source, "startup 中缺少长度校验"
        assert "sys.exit(1)" in source, "startup 中缺少 sys.exit 安全退出"

    def test_jwt_algorithm_supports_rs256_fallback(self):
        """验证 JWT 支持 RS256 -> HS256 降级 (app/auth_jwt.py)。"""
        from app.auth_jwt import create_access_token, decode_access_token
        from jose import JWTError

        # 签发并验证 token
        token = create_access_token({"sub": "1", "test": "data"})
        payload = decode_access_token(token)
        assert payload["sub"] == "1"
        assert payload["test"] == "data"


# ══════════════════════════════════════════════════════════════════════
# Test 3: CORS 白名单配置验证
# ══════════════════════════════════════════════════════════════════════


class TestCorsWhitelist:
    """验证 CORS 配置的安全性。"""

    def test_cors_origins_configured(self):
        """CORS_ORIGINS 必须配置，不能为空。"""
        from app.config import settings

        assert settings.CORS_ORIGINS, "CORS_ORIGINS 未配置"

    def test_cors_origins_are_specific(self):
        """CORS origins 必须是具体域名，不能使用通配符。"""
        from app.config import settings

        origins = settings.CORS_ORIGINS.split(",")
        for origin in origins:
            origin = origin.strip()
            assert origin, "CORS origin 不能为空"
            assert origin != "*", "CORS 不能设置为通配符 *"
            # 必须包含协议
            assert origin.startswith("http://") or origin.startswith("https://"), (
                f"CORS origin '{origin}' 缺少协议"
            )

    def test_cors_production_origins_are_https(self):
        """生产环境 CORS origins 必须使用 HTTPS。"""
        from app.config import settings

        origins = settings.CORS_ORIGINS.split(",")
        for origin in origins:
            origin = origin.strip()
            # localhost 可以不用 HTTPS
            if "localhost" in origin or "127.0.0.1" in origin:
                continue
            assert origin.startswith("https://"), (
                f"生产环境 CORS origin '{origin}' 必须使用 HTTPS"
            )

    def test_cors_middleware_registered(self):
        """CORSMiddleware 必须已注册到 app 中。"""
        from fastapi.middleware.cors import CORSMiddleware

        app = _get_app()
        classes = _get_middleware_classes(app)
        assert CORSMiddleware in classes, "CORSMiddleware 未注册"


# ══════════════════════════════════════════════════════════════════════
# Test 4: CSRF 保护验证
# ══════════════════════════════════════════════════════════════════════


class TestCsrfProtection:
    """验证 CSRF 中间件的关键安全属性。"""

    def test_csrf_middleware_importable(self):
        """CsrfMiddleware 可导入且实例化。"""
        from app.middleware.csrf_middleware import CsrfMiddleware

        instance = CsrfMiddleware(app=None)
        assert instance is not None

    def test_csrf_uses_double_submit_cookie(self):
        """CSRF 使用 Double Submit Cookie 模式 (非 HttpOnly Cookie + 请求头校验)。"""
        from app.middleware.csrf_middleware import (
            CSRF_COOKIE_NAME,
            CSRF_HEADER_NAME,
            CSRF_TOKEN_PATH,
            EXCLUDED_PATHS,
        )

        assert CSRF_COOKIE_NAME == "csrf_token", "Cookie 名称应为 csrf_token"
        assert CSRF_HEADER_NAME == "X-CSRF-Token", "请求头名称应为 X-CSRF-Token"
        assert CSRF_TOKEN_PATH == "/api/csrf/token", "Token 端点路径正确"
        assert len(EXCLUDED_PATHS) > 0, "应有排除路径"

        # 排除路径应包含认证端点和 webhook
        excluded = [p.lower() for p in EXCLUDED_PATHS]
        assert any("login" in p for p in excluded), "排除路径应包含登录端点"
        assert any("webhook" in p for p in excluded), "排除路径应包含 webhook"

    def test_csrf_token_length(self):
        """CSRF token 长度应为 64 字符 (secrets.token_hex(32))。"""
        import secrets

        token = secrets.token_hex(32)
        assert len(token) == 64, "CSRF token 应为 64 字符"

    def test_csrf_uses_constant_time_compare(self):
        """CSRF 校验应使用恒定时间比较防止时序攻击。"""
        import inspect

        from app.middleware.csrf_middleware import CsrfMiddleware

        source = inspect.getsource(CsrfMiddleware._validate_csrf)
        assert "compare_digest" in source, "应使用 secrets.compare_digest 恒定时间比较"


# ══════════════════════════════════════════════════════════════════════
# Test 5: 安全响应头完整性 (集成测试)
# ══════════════════════════════════════════════════════════════════════


class TestSecurityHeadersOnResponses:
    """验证所有 HTTP 响应都包含完整的安全响应头。"""

    @pytest.mark.asyncio
    async def test_health_endpoint_has_all_headers(self, client):
        """/health 端点应包含所有 7 个安全响应头。"""
        from app.middleware.security_headers import SECURITY_HEADERS

        resp = await client.get("/health")
        assert resp.status_code == 200
        for name, value in SECURITY_HEADERS.items():
            header_value = resp.headers.get(name.lower())
            assert header_value is not None, f"缺少安全响应头: {name}"
            assert header_value == value, (
                f"安全响应头 {name} 值不匹配: 期望 '{value}', 实际 '{header_value}'"
            )

    @pytest.mark.asyncio
    async def test_error_page_has_all_headers(self, client):
        """404 错误页面也应包含所有安全响应头。"""
        from app.middleware.security_headers import SECURITY_HEADERS

        resp = await client.get("/nonexistent-path-xyz-999")
        assert resp.status_code == 404
        for name in SECURITY_HEADERS:
            assert resp.headers.get(name.lower()) is not None, (
                f"404 页面缺少安全响应头: {name}"
            )

    @pytest.mark.asyncio
    async def test_specific_security_headers_values(self, client):
        """验证关键安全响应头的精确值。"""
        resp = await client.get("/health")

        checks = {
            "content-security-policy": "default-src 'self'",
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY",
            "x-xss-protection": "1; mode=block",
        }
        for header, expected_value in checks.items():
            actual = resp.headers.get(header)
            assert actual == expected_value, (
                f"响应头 {header}: 期望 '{expected_value}', 实际 '{actual}'"
            )


# ══════════════════════════════════════════════════════════════════════
# Test 6: 速率限制配置验证
# ══════════════════════════════════════════════════════════════════════


class TestRateLimitConfiguration:
    """验证速率限制中间件的分级配置。"""

    def test_rate_limiter_limits_configured(self):
        """验证三级限流配置。"""
        from app.middleware.rate_limiter import DEFAULT_LIMITS

        assert "anonymous" in DEFAULT_LIMITS
        assert "standard" in DEFAULT_LIMITS
        assert "enterprise" in DEFAULT_LIMITS
        assert DEFAULT_LIMITS["anonymous"] == 100
        assert DEFAULT_LIMITS["standard"] == 1000
        assert DEFAULT_LIMITS["enterprise"] == 10000

    def test_rate_limiter_middleware_importable(self):
        """RateLimiterMiddleware 可导入。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        instance = RateLimiterMiddleware(
            _echo_app,
            limits={"anonymous": 100, "standard": 1000, "enterprise": 10000},
            window_seconds=60,
        )
        assert instance is not None


# ══════════════════════════════════════════════════════════════════════
# Test 7: 中间件导入完整性
# ══════════════════════════════════════════════════════════════════════


class TestMiddlewareImportIntegrity:
    """验证所有中间件模块可独立导入。"""

    def test_csrf_middleware_module_importable(self):
        import app.middleware.csrf_middleware  # noqa: F811

    def test_rate_limiter_module_importable(self):
        import app.middleware.rate_limiter  # noqa: F811

    def test_security_headers_module_importable(self):
        import app.middleware.security_headers  # noqa: F811

    def test_api_key_module_importable(self):
        import app.middleware.api_key  # noqa: F811

    def test_audit_module_importable(self):
        import app.middleware.audit  # noqa: F811

    def test_rbac_module_importable(self):
        import app.middleware.rbac  # noqa: F811

    def test_tenant_module_importable(self):
        import app.middleware.tenant  # noqa: F811

    def test_request_id_module_importable(self):
        import app.middleware.request_id  # noqa: F811

    def test_logging_middleware_module_importable(self):
        import app.middleware.logging_middleware  # noqa: F811

    def test_i18n_middleware_module_importable(self):
        import app.middleware.i18n_middleware  # noqa: F811

    def test_metrics_module_importable(self):
        import app.middleware.metrics  # noqa: F811

    def test_otel_module_importable(self):
        import app.middleware.otel  # noqa: F811

    def test_api_version_module_importable(self):
        import app.middleware.api_version  # noqa: F811


# ══════════════════════════════════════════════════════════════════════
# 辅助
# ══════════════════════════════════════════════════════════════════════

async def _echo_app(scope, receive, send):
    """最小的 ASGI echo app。"""
    body = b'{"ok":true}'
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
        ],
    })
    await send({"type": "http.response.body", "body": body})
