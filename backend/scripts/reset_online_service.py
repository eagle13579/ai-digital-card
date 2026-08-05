#!/usr/bin/env python
"""重置在线学习服务单例并运行管道一次"""

import sys
import os

# 确保 backend 在路径中
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.online_learning_service import reset_online_learning_service

reset_online_learning_service()
print("✅ 在线学习服务单例已重置")
