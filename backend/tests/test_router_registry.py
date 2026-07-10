"""路由注册单元测试 — 验证核心API路由已注册。"""

from __future__ import annotations

import pytest


class TestRouterRegistration:
    """路由注册验证"""

    def test_core_routes_exist(self):
        """验证核心路由已注册到应用"""
        from app.__init__ import create_app
        app = create_app()
        paths = [r.path for r in app.routes]
        # 验证核心路由端点
        core_paths = ["/health", "/api/health"]
        for cp in core_paths:
            assert cp in paths, f"核心路由 {cp} 未注册"

    def test_auth_routes_exist(self):
        """验证认证路由已注册"""
        from app.__init__ import create_app
        app = create_app()
        paths = [r.path for r in app.routes]
        auth_patterns = ["/api/v1/auth/login", "/api/v1/auth/register"]
        for ap in auth_patterns:
            assert ap in paths, f"认证路由 {ap} 未注册"

    def test_brochure_routes_exist(self):
        """验证画册路由已注册"""
        from app.__init__ import create_app
        app = create_app()
        paths = [r.path for r in app.routes]
        assert any("/brochures" in p for p in paths), "画册路由未注册"
