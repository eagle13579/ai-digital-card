#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI数智名片 Watchdog — 每5分钟检查 :8002，离线自动重启
"""
import subprocess, time, os, sys
from datetime import datetime

PORT = 8002
LOG = r"D:\AI数智名片\logs\watchdog.log"
BE = r"D:\AI数智名片\backend"
PYTHON = r"C:\Users\56867\AppData\Local\Programs\Python\Python312\python.exe"

os.makedirs(r"D:\AI数智名片\logs", exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def check_port():
    """检查端口是否在线"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    result = s.connect_ex(('127.0.0.1', PORT))
    s.close()
    return result == 0

def restart_backend():
    """杀死旧进程，启动新后端"""
    log("🔄 后端离线，正在重启...")
    # 杀旧进程
    subprocess.run(f'taskkill /f /im python.exe /fi "WINDOWTITLE eq AI数智名片*" 2>nul', shell=True, timeout=10)
    time.sleep(2)
    # 启动新后端
    subprocess.Popen(
        f'start "AI数智名片" cmd /c "cd /d {BE} && {PYTHON} run.py"',
        shell=True
    )
    log("✅ 重启命令已发送")
    # 等待启动
    time.sleep(5)
    if check_port():
        log("✅ 后端已恢复在线")
    else:
        log("⚠️ 后端启动中，下次巡检再验证")

def main():
    alive = check_port()
    if alive:
        log("🟢 :8002 在线")
    else:
        log("🔴 :8002 离线")
        restart_backend()

if __name__ == "__main__":
    main()
