@echo off
REM ============================================================
REM git_auto_sync_local_setup.bat — 本地代码自动同步一键部署
REM 用法: 双击运行一次，自动注册计划任务（每15分钟静默同步）
REM 位置: D:\AI数智名片\scripts\git_auto_sync_local_setup.bat
REM ============================================================
cd /d D:\AI数智名片
echo [1/3] 同步代码到最新...
git pull origin master --ff-only
echo.
echo [2/3] 注册计划任务 Hermes-GitAutoSync（每15分钟自动双向同步）...
python scripts\git_auto_sync_local.py --setup
echo.
echo [3/3] 立即执行一次同步验证...
python scripts\git_auto_sync_local.py
echo.
echo ============================================================
echo 部署完成！本地 ↔ GitHub ↔ 服务器 已开启自动双向同步
echo 每15分钟自动执行，无需任何手动操作
echo 查看日志: %%TEMP%%\git_auto_sync_local.log
echo ============================================================
pause
