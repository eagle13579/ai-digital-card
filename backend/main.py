"""AI数字名片 API — 模块化架构入口。"""
import os
import sys

import uvicorn

# 确保 app 模块可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# 主应用
app = create_app()

if __name__ == "__main__":
    print("[HTTP] 使用HTTP模式（微信开发者工具兼容性更好）")
    uvicorn.run("main:app", host="0.0.0.0", port=8201, reload=False, log_level="info")
