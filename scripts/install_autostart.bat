@echo off
chcp 65001 >nul
echo ============================================
echo  安装 AI数智名片 开机自启
echo ============================================
echo.
:: 删除旧任务（如果有）
schtasks /delete /tn "AI数智名片-后端" /f >nul 2>&1

:: 创建开机自启任务
schtasks /create /tn "AI数智名片-后端" /tr "D:\AI数智名片\start_backend.bat" /sc onstart /delay 0000:30 /ru %USERNAME% /f

if %errorlevel% equ 0 (
    echo ✅ 开机自启已注册
    echo   任务名: AI数智名片-后端
    echo   延迟:   30秒（等待系统就绪）
) else (
    echo ❌ 注册失败，尝试备用方案...
    :: 备用：加到启动文件夹
    echo start /min \"\" \"D:\AI数智名片\start_backend.bat\" > "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AI数智名片.bat"
    echo ✅ 已加到启动文件夹
)

echo.
echo ✅ 完成！重启电脑后自动启动 :8002
pause
