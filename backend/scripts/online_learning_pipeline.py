#!/usr/bin/env python
"""在线学习管道 — 兼容性存根

等效替代已被移除的 scripts/online_learning_pipeline.py
委托给 run_cron_learning_wrapper.py（专为 cron 设计，会剥离 Hermes 路径污染）

原文件已被重构为 app/ai/online_learning.py::OnlineLearningEngine
"""
import sys
import os

# 委托给 cron 专用包装器（它处理 Hermes 路径剥离）
backend_dir = os.path.dirname(os.path.abspath(__file__))
wrapper_path = os.path.join(backend_dir, "run_cron_learning_wrapper.py")

if not os.path.isfile(wrapper_path):
    # fallback: 直接使用 run_online_learning.py
    wrapper_path = os.path.join(backend_dir, "run_online_learning.py")

exec(compile(open(wrapper_path).read(), wrapper_path, 'exec'))
