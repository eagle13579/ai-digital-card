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
