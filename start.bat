@echo off
chcp 65001 >nul
echo ============================================
echo AI数智名片 v3.4.0 - 一键启动
echo ============================================
echo.

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo [2/3] 启动后端服务 (port 8002)...
cd /d "%~dp0backend"
start "AI名片-后端" cmd /c "python run.py"
cd /d "%~dp0"

echo [3/3] 等待服务启动...
ping 127.0.0.1 -n 4 >nul

echo.
echo ============================================
echo  AI数智名片 启动完成
echo  后端地址: http://localhost:8002
echo  API文档:  http://localhost:8002/docs
echo  小程序:   用微信开发者工具打开 miniapp/
echo ============================================
echo.
echo 快速操作指南：
echo   - 名片创建: 首页点击"创建名片"
echo   - 画册预览: 创建成功后自动跳转
echo   - 平台管理: 点击"管理平台"
echo.
pause
