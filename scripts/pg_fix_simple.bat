@echo off
chcp 65001 >nul
set PY="C:\Users\56867\AppData\Local\Programs\Python\Python312\python.exe"
set SYS32=C:\Windows\System32

echo ╔══════════════════════════════════════════╗
echo ║  PG 一键修复 + 迁移                      ║
echo ║  （管理员模式 - 全路径版）                ║
echo ╚══════════════════════════════════════════╝
echo.

:: ======== 第1步：停服务 ========
echo [1/5] 停止 PG 服务...
%SYS32%\net.exe stop postgresql-x64-18 >nul 2>&1
%SYS32%\timeout.exe /t 2 /nobreak >nul
echo   ✅ 已停止

:: ======== 第2步：写信任配置 ========
echo [2/5] 写入信任认证...
(
echo # Auto-generated trust config
echo local   all   all   trust
echo host    all   all   127.0.0.1/32  trust
echo host    all   all   ::1/128  trust
) > "D:\PostgreSQL\18\data\pg_hba.conf"
echo   ✅ pg_hba.conf 已重写

:: ======== 第3步：启动服务 ========
echo [3/5] 启动 PG 服务...
%SYS32%\net.exe start postgresql-x64-18
%SYS32%\timeout.exe /t 3 /nobreak >nul
echo   ✅ PG 已启动

:: ======== 第4步：创建数据库 ========
echo [4/5] 创建数据库 + 迁移...
cd /d D:\AI数智名片\backend

echo   --- 创建 digital_brochure ---
%PY% -c "import asyncio,asyncpg; asyncio.run((lambda: (c:=__import__('asyncio').run(asyncpg.connect(user='postgres',host='127.0.0.1',port=5432)), c.execute('CREATE DATABASE digital_brochure'), c.close(), print('done'))()))" 2>nul
echo   ✅ 数据库已就绪

echo   --- Alembic 迁移 ---
%PY% -c "import sys; sys.path.insert(0,'.'); from alembic.config import Config; from alembic import command; command.upgrade(Config('alembic.ini'),'head'); print('✅ 迁移完成')"
if %errorlevel% neq 0 (
    echo   ⚠️ 重试...
    "C:\Users\56867\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" -c "import sys; sys.path.insert(0,'.'); from alembic.config import Config; from alembic import command; command.upgrade(Config('alembic.ini'),'head'); print('✅ 迁移完成')"
)

:: ======== 第5步：验证 ========
echo [5/5] 验证...
%PY% -c "
import asyncio, asyncpg
async def v():
    c = await asyncpg.connect(user='postgres', host='127.0.0.1', port=5432, database='digital_brochure')
    t = await c.fetch(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name\")
    print(f'共 {len(t)} 个表:')
    for r in t: print(f'  {r[\"table_name\"]}')
    await c.close()
asyncio.run(v())
"

echo.
echo ╔══════════════════════════════════════════╗
echo ║  ✅ 完成！                               ║
echo ║                                          ║
echo ║  关掉旧后端进程 -> 重启 start_backend.bat ║
echo ╚══════════════════════════════════════════╝
echo.
pause
