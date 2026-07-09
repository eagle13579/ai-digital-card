"""AI数字名片 后端入口 — 直接启动（生产模式）"""
import sys, os

# 设置生产环境标志
os.environ.setdefault("ENV", "production")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
