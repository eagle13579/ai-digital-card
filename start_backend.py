"""启动AI数字名片后端服务"""
import subprocess, sys, os

backend = r"D:\AI数智名片\backend"
os.chdir(backend)
proc = subprocess.Popen(
    [sys.executable, "-B", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"],
    cwd=backend,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
)
print(f"PID={proc.pid}")
