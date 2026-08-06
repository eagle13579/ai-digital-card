"""AI数字名片 API — 工业级模块化架构入口 (v2.1 生产版)
支持：
- PM2 进程管理（崩溃自启+日志轮转）
- Uvicorn 异步并发（单进程即可处理数千并发连接）
- 环境感知配置（开发/生产模式）
- 启动前自动清理占用端口（防端口冲突重启循环）
- 健康探针（liveness + readiness）
"""
import os
import sys
import subprocess
import socket

import uvicorn

# 确保 app 模块可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 2026-08-02 修复: 显式注入 baize_libs 路径 (pth 在 uv venv 下不可靠)
# 只注入 D:\baize_libs (完整版). 注意: 绝不注入归档版 D:\__archive\...\baize_libs
# 因为归档版含 secrets.py 会遮蔽 Python 标准库 secrets 模块, 导致 starlette 崩溃
for _p in (r"D:\baize_libs",):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

# 2026-08-02 修复: Python 3.14 包导入行为变化, 手动预注册 baize_libs 父包
# (否则 from .xxx import 在子模块导入时报 "No module named 'baize_libs'")
try:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        "baize_libs", os.path.join(r"D:\baize_libs", "__init__.py"),
        submodule_search_locations=[r"D:\baize_libs"],
    )
    if _spec and "baize_libs" not in sys.modules:
        _mod = _ilu.module_from_spec(_spec)
        sys.modules["baize_libs"] = _mod
        _spec.loader.exec_module(_mod)
except Exception:
    pass  # 预注册失败则回退到 pth/常规导入

# Debug: test baize_libs import before app
try:
    import baize_libs.generic_agent.agent_safety
    print("[boot] baize_libs import OK from:", baize_libs.__file__)
except Exception as e:
    print(f"[boot] baize_libs FAILED: {e}")
    import sys as _sys
    print(f"[boot] _baize_paths={[p for p in _sys.path if 'baize' in p.lower() or '记忆' in p]}")

from app import create_app

# 主应用
app = create_app()

# ─── 生产配置 ───────────────────────────────────────────────
PROD = os.getenv("PROD", "").lower() in ("1", "true", "yes")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8201"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info" if not PROD else "warning")


def kill_stale_process(port):
    """启动前清理占用端口的旧进程（防止 PM2 重启循环）"""
    if sys.platform != "win32":
        return
    try:
        r = subprocess.run(
            ["cmd", "/c", f"netstat -ano | findstr :{port} | findstr LISTENING"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            for line in r.stdout.strip().split("\n"):
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        subprocess.run(["taskkill", "/F", "/PID", pid],
                                       capture_output=True, timeout=5)
                        print(f"[端口清理] 已终止旧进程 PID={pid} (端口:{port})")
                    except Exception:
                        pass
    except Exception:
        pass


def main():
    # 启动前清理端口
    kill_stale_process(PORT)

    mode = "生产" if PROD else "开发"
    print(f"[{mode}] AI数字名片 API v2.1 — {HOST}:{PORT} (async 单进程, log={LOG_LEVEL})")
    print(f"[{mode}] 工业级进程管理: PM2 监控中 (崩溃自动重启)")

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level=LOG_LEVEL,
    )


if __name__ == "__main__":
    main()
