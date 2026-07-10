"""核心架构测试 - 验证应用工厂/中间件/路由"""
import pytest


class TestCreateApp:
    """验证应用工厂"""

    def test_app_title(self):
        from app import create_app
        app = create_app()
        assert app.title == "AI数字名片 API"

    def test_app_version(self):
        from app import create_app
        app = create_app()
        assert app.version == "2.0.0"


class TestMiddlewareChain:
    """验证中间件链完整性"""

    def test_middleware_at_least_10(self):
        from app import create_app
        app = create_app()
        assert len(app.user_middleware) >= 10

    def test_security_headers_registered(self):
        from app import create_app
        app = create_app()
        names = [m.cls.__name__ for m in app.user_middleware]
        assert "SecurityHeadersMiddleware" in names

    def test_audit_middleware_registered(self):
        from app import create_app
        app = create_app()
        names = [m.cls.__name__ for m in app.user_middleware]
        assert "AuditMiddleware" in names

    def test_tenant_middleware_registered(self):
        from app import create_app
        app = create_app()
        names = [m.cls.__name__ for m in app.user_middleware]
        assert "TenantMiddleware" in names


class TestRouterRegistration:
    """验证核心路由注册"""

    def test_health_route(self):
        from app import create_app
        app = create_app()
        paths = [r.path for r in app.routes]
        assert "/health" in paths

    def test_api_health_route(self):
        from app import create_app
        app = create_app()
        paths = [r.path for r in app.routes]
        assert "/api/health" in paths
