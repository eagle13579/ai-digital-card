"""AI数智名片 — 中间件集成测试（FastAPI TestClient）"""
import pytest
from unittest.mock import patch, AsyncMock

# ── 中间件测试 ──────────────────────────────

class TestRateLimitMiddleware:
    """速率限制中间件测试 — app/middleware/rate_limit_middleware.py"""

    @pytest.mark.asyncio
    async def test_rate_limit_normal_request(self):
        """正常请求应通过速率限制"""
        from app.middleware.rate_limit_middleware import RateLimitMiddleware
        middleware = RateLimitMiddleware(max_requests=100, window_seconds=60)
        result = await middleware.check_rate_limit("127.0.0.1")
        assert result is True

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """超限请求应被拒绝"""
        from app.middleware.rate_limit_middleware import RateLimitMiddleware
        middleware = RateLimitMiddleware(max_requests=3, window_seconds=60)
        # 连续请求超出限制
        for _ in range(3):
            await middleware.check_rate_limit("test_client")
        result = await middleware.check_rate_limit("test_client")
        assert result is False

    @pytest.mark.asyncio
    async def test_rate_limit_window_reset(self):
        """时间窗口重置后应允许新请求"""
        from app.middleware.rate_limit_middleware import RateLimitMiddleware
        middleware = RateLimitMiddleware(max_requests=2, window_seconds=1)
        await middleware.check_rate_limit("test_client")
        await middleware.check_rate_limit("test_client")
        # 冷窗口（重置后）应允许
        import asyncio
        await asyncio.sleep(1.1)
        result = await middleware.check_rate_limit("test_client")
        assert result is True


class TestRBACMiddleware:
    """RBAC中间件测试 — app/middleware/rbac_middleware.py"""

    @pytest.mark.asyncio
    async def test_admin_access_granted(self):
        """管理员应有全部权限"""
        from app.middleware.rbac_middleware import RBACMiddleware
        middleware = RBACMiddleware()
        result = await middleware.check_permission(
            user_id="admin",
            required_role="admin",
            resource="brochure:delete"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_user_access_limited(self):
        """普通用户只能访问自己的资源"""
        from app.middleware.rbac_middleware import RBACMiddleware
        middleware = RBACMiddleware()
        result = await middleware.check_permission(
            user_id="user_001",
            required_role="user",
            resource="brochure:own:read"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_unauthorized_access_denied(self):
        """越权访问应被拒绝"""
        from app.middleware.rbac_middleware import RBACMiddleware
        middleware = RBACMiddleware()
        result = await middleware.check_permission(
            user_id="user_001",
            required_role="admin",
            resource="system:config"
        )
        assert result is False


class TestCSRFMiddleware:
    """CSRF防护中间件测试 — app/middleware/csrf_middleware.py"""

    def test_token_generation(self):
        """CSRF token应能正常生成"""
        from app.middleware.csrf_middleware import CSRFTokenProvider
        provider = CSRFTokenProvider()
        token = provider.generate_token("user_session_001")
        assert token is not None
        assert len(token) > 8

    def test_token_validation_valid(self):
        """有效的CSRF token应通过验证"""
        from app.middleware.csrf_middleware import CSRFTokenProvider
        provider = CSRFTokenProvider()
        token = provider.generate_token("user_session_002")
        result = provider.validate_token("user_session_002", token)
        assert result is True

    def test_token_validation_invalid(self):
        """无效的CSRF token应被拒绝"""
        from app.middleware.csrf_middleware import CSRFTokenProvider
        provider = CSRFTokenProvider()
        result = provider.validate_token("user_session_003", "fake_token_123")
        assert result is False
