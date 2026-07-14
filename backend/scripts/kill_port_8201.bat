@echo off
REM kill_port_8201.bat — 启动前确保 8201 端口无人占用
REM 放在 PM2 ecosystem.config.js 的 pre-exec 中调用
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8201 ^| findstr LISTENING') do (
    echo [kill_port] Killing PID %%a on port 8201
    taskkill /F /PID %%a >nul 2>&1
)
REM 等待端口释放
timeout /t 3 /nobreak >nul
