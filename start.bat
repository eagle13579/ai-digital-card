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

echo [2/3] 启动后端服务 (port 8001)...
cd /d "%~dp0backend"
start "AI名片-后端" cmd /c "uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
cd /d "%~dp0"

echo [3/3] 等待服务就绪...
ping 127.0.0.1 -n 4 >nul

echo.
echo ============================================
echo  AI数智名片 已启动！
echo  后端地址: http://localhost:8001
echo  API文档:  http://localhost:8001/docs
echo  小程序:  用微信开发者工具打开 miniapp/
echo ============================================
echo.
echo 新页面入口：
echo   - 画册创建: 首页点击"创建画册"
echo   - 画册预览: 创建成功后自动跳转
echo   - 平台创建: 个人中心点击"创建平台"
echo.
pause
