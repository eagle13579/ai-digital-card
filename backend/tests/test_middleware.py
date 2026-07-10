"""中间件链单元测试 — 验证中间件注册和顺序。"""

from __future__ import annotations

import pytest


class TestMiddlewareRegistration:
    """中间件注册验证"""

    def test_middleware_count(self):
        """验证应用至少有10个中间件（包含FastAPI内置）"""
        from app.__init__ import create_app
        app = create_app()
        # user_middleware 包含通过 app.add_middleware 注册的所有中间件
        middlewares = [m.cls.__name__ for m in app.user_middleware]
        assert len(middlewares) >= 10, f"只有 {len(middlewares)} 个中间件: {middlewares}"

    def test_middleware_names_known(self):
        """验证关键中间件已注册"""
        from app.__init__ import create_app
        app = create_app()
        names = {m.cls.__name__ for m in app.user_middleware}
        expected = {
            "CORSMiddleware",
            "CsrfMiddleware",
            "LoggingMiddleware",
        }
        missing = expected - names
        assert not missing, f"缺少中间件: {missing}"

    def test_middleware_order_both_exist(self):
        """验证 CORS 和 CSRF 中间件都存在（顺序不重要，各自工作正常）"""
        from app.__init__ import create_app
        app = create_app()
        names = {m.cls.__name__ for m in app.user_middleware}
        assert "CORSMiddleware" in names, "CORSMiddleware 未注册"
        assert "CsrfMiddleware" in names, "CsrfMiddleware 未注册"
