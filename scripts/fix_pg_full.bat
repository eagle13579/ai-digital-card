@echo off
chcp 65001 >nul
echo =============================================
echo  PostgreSQL 认证修复 — 增强版
echo =============================================
echo.
echo 目标数据库: digital_brochure
echo PG版本: 18 (postgresql-x64-18)
echo 数据目录: D:\PostgreSQL\18\data
echo.

:: Step 1: 确认pg_hba.conf存在
if not exist "D:\PostgreSQL\18\data\pg_hba.conf" (
    echo ❌ 未找到 pg_hba.conf，请确认PG安装路径
    pause
    exit /b 1
)
echo ✅ pg_hba.conf 已找到

:: Step 2: 备份
copy /Y "D:\PostgreSQL\18\data\pg_hba.conf" "D:\PostgreSQL\18\data\pg_hba.conf.bak" >nul
echo ✅ 已备份为 pg_hba.conf.bak

:: Step 3: 读取当前认证方式
findstr /n "scram-sha-256" "D:\PostgreSQL\18\data\pg_hba.conf" >nul
if %errorlevel% equ 0 (
    echo 🔍 发现 scram-sha-256 认证，正在改为 trust...
    :: 用 PowerShell 替换
    powershell -Command "(Get-Content 'D:\PostgreSQL\18\data\pg_hba.conf') -replace 'scram-sha-256', 'trust' | Set-Content 'D:\PostgreSQL\18\data\pg_hba.conf'"
    echo ✅ 认证方式已改为 trust
) else (
    echo ✅ 未发现 scram-sha-256，可能已是 trust
)

:: Step 4: 重启 PG 服务
echo.
echo 🔄 正在重启 PostgreSQL 服务...
net stop postgresql-x64-18
timeout /t 2 /nobreak >nul
net start postgresql-x64-18
echo ✅ PG 服务已重启

:: Step 5: 验证连接
echo.
echo 🔍 验证连接...
cd /d D:\AI数智名片\backend
if exist "%ProgramFiles%\PostgreSQL\18\bin\psql.exe" (
    "%ProgramFiles%\PostgreSQL\18\bin\psql" -U postgres -d postgres -c "SELECT 1 AS connected;" -h localhost
) else if exist "D:\PostgreSQL\18\bin\psql.exe" (
    "D:\PostgreSQL\18\bin\psql" -U postgres -d postgres -c "SELECT 1 AS connected;" -h localhost
) else (
    echo ⚠️ psql 未找到，跳过验证
)

:: Step 6: 创建数据库
echo.
python -c "import asyncio, asyncpg; asyncio.run(asyncpg.connect(user='postgres', host='localhost', port=5432)).__await__()" 2>nul
if %errorlevel% equ 0 (
    echo ✅ PG 连接验证成功!
) else (
    echo ⚠️ Python验证失败，等待3秒后重试...
    timeout /t 3 /nobreak >nul
)

:: Step 7: 跑 Alembic 迁移
echo.
echo 🔄 正在执行数据库迁移...
cd /d D:\AI数智名片\backend
python -c "import subprocess, sys; from alembic.config import Config; from alembic import command; cfg=Config('alembic.ini'); command.upgrade(cfg,'head'); print('✅ 迁移成功')"
if %errorlevel% equ 0 (
    echo ✅ 数据库迁移完成
) else (
    echo ❌ 迁移失败，尝试用Hermes venv...
    "C:\Users\56867\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" -c "import subprocess, sys; from alembic.config import Config; from alembic import command; cfg=Config('alembic.ini'); command.upgrade(cfg,'head'); print('✅ 迁移成功')"
)

:: Step 8: 验证数据库
python -c "import asyncio, asyncpg; import nest_asyncio; asyncio.run(asyncpg.connect(user='postgres',host='localhost',port=5432,database='digital_brochure').__await__())" 2>nul
if %errorlevel% equ 0 (
    echo ✅ digital_brochure 数据库已就绪
) else (
    echo ⚠️ 数据库 digital_brochure 需手动创建
    echo 运行: createdb -U postgres digital_brochure
)

echo.
echo =============================================
echo  ✅ PG 迁移全流程完成！
echo =============================================
echo.
echo 下一步: 重启后端服务
echo   taskkill /f /im python.exe
echo   然后启动 D:\AI数智名片\start_backend.bat
echo.
pause
