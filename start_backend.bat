@echo off
title AI数智名片 — 后端启动器
cd /d "%~dp0backend"

echo === 清理端口 8002 ===
powershell -Command "Get-NetTCPConnection -LocalPort 8002 -ErrorAction SilentlyContinue | ForEach-Object { try { Stop-Process -Id $_.OwningProcess -Force } catch {} }"
timeout /t 2 /nobreak >nul

echo === 启动后端 :8002 ===
python run.py

pause
