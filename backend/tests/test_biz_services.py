"""业务服务层单元测试 — 验证核心服务组件行为（应用创建、服务导入）。"""

from __future__ import annotations

import pytest


class TestCreateApp:
    """应用创建与服务组件验证"""

    def test_app_created_successfully(self):
        """验证 create_app 能正常创建 FastAPI 实例"""
        from app.__init__ import create_app
        app = create_app()
        assert app is not None
        assert app.title == "AI数字名片 API"
        assert app.version == "2.0.0"

    def test_app_has_routes(self):
        """验证应用已注册路由"""
        from app.__init__ import create_app
        app = create_app()
        assert len(app.routes) > 0
        # 验证核心路由端点存在
        paths = [r.path for r in app.routes]
        assert any("/health" in p for p in paths)

    def test_app_has_middleware(self):
        """验证应用已注册中间件"""
        from app.__init__ import create_app
        app = create_app()
        # FastAPI 自定义中间件 >= 10 个
        assert len(app.user_middleware) >= 10


class TestPricingEventsService:
    """定价事件服务测试"""

    def test_pricing_service_imports(self):
        """验证定价服务模块可导入且包含核心函数"""
        from services.pricing_service import record_pricing_click, get_pricing_stats
        assert callable(record_pricing_click)
        assert callable(get_pricing_stats)

    def test_pricing_stats_structure(self):
        """验证 get_pricing_stats 返回结构"""
        from services.pricing_service import get_pricing_stats
        stats = get_pricing_stats()
        assert isinstance(stats, dict)
        assert "total_views" in stats
        assert "total_trials" in stats
        assert "trial_conversion_rate" in stats


class TestMonitorService:
    """监控告警服务测试"""

    def test_monitor_send_alert_import(self):
        """验证监控服务 send_alert 函数可导入"""
        from services.monitor import send_alert
        assert callable(send_alert)

    def test_monitor_json_formatter(self):
        """验证 JSON 日志格式化器可用"""
        from services.monitor import JsonLogFormatter
        import logging
        formatter = JsonLogFormatter()
        assert formatter is not None
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname=__file__, lineno=1, msg="test message",
            args=(), exc_info=None
        )
        output = formatter.format(record)
        assert "test message" in output
        assert "level" in output
