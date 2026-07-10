"""AI数字名片 启动脚本 — 设置环境变量后启动"""
import os, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-local-dev-only")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./data/digital_brochure.db")
os.environ.setdefault("ENV", "development")

from app import create_app
import uvicorn

app = create_app()
print(f"AI数字名片 启动于 http://0.0.0.0:8002")
uvicorn.run(app, host="0.0.0.0", port=8002)
