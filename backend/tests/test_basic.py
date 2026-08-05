"""AI数字名片 — 基础测试入口
运行: pytest backend/tests/ -v
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_import_app():
    """验证应用模块可导入"""
    os.environ['JWT_SECRET'] = 'test-secret'
    from app import create_app
    app = create_app()
    assert app is not None
    assert app.title == "AI数字名片 API"


def test_health_endpoint():
    """验证健康检查端点"""
    os.environ['JWT_SECRET'] = 'test-secret'
    from app import create_app
    from fastapi.testclient import TestClient

    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
