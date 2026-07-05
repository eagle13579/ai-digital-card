@echo off
REM ============================================
REM AI数智名片 — 一键启动脚本
REM v3.3.0 - 2026-07-05
REM ============================================

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装 Python 3.10+
    exit /b 1
)

echo [2/3] 启动后端服务 (port 8001)...
cd /d "%~dp0backend"
start "AI数字名片-后端" cmd /c "uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
if errorlevel 1 (
    echo ❌ 后端启动失败
    exit /b 1
)

echo [3/3] 等待服务就绪...
timeout /t 3 /nobreak >nul

REM 验证
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Health 检查未通过，但服务可能仍在启动中
) else (
    echo ✅ 后端服务运行中: http://localhost:8001
    echo ✅ API文档: http://localhost:8001/docs
)

echo.
echo ============================================
echo  AI数智名片 v3.3.0 已启动
echo  后端: http://localhost:8001
echo  API:  http://localhost:8001/docs
echo  小程序: 用微信开发者工具打开 miniapp/
echo ============================================
pause
