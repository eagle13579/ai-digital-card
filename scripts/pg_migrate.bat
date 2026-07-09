@echo off
chcp 65001 >nul
echo =============================================
echo  PostgreSQL 一键修复 + 迁移
echo =============================================
echo.
echo PG版本: 18 | 端口: 5432
echo 目标库: digital_brochure
echo.

:: ======== 第1步：定位 pg_hba.conf ========
set PGHBA=D:\PostgreSQL\18\data\pg_hba.conf
if not exist "%PGHBA%" (
    echo ❌ 找不到 %PGHBA%
    pause
    exit /b
)
echo ✅ 找到 pg_hba.conf

:: ======== 第2步：备份 ========
copy /Y "%PGHBA%" "%PGHBA%.bak" >nul
echo ✅ 已备份

:: ======== 第3步：改认证 ========
echo 🔧 将 scram-sha-256 改为 trust...
powershell -Command ^
    "(Get-Content '%PGHBA%') -replace 'scram-sha-256', 'trust' | Set-Content '%PGHBA%'"
echo ✅ 认证已改为 trust

:: ======== 第4步：重启服务 ========
echo 🔄 重启 PostgreSQL 服务...
net stop postgresql-x64-18
timeout /t 2 /nobreak >nul
net start postgresql-x64-18
echo ✅ PG服务已重启
timeout /t 3 /nobreak >nul

:: ======== 第5步：创建数据库 ========
cd /d D:\AI数智名片\backend

:: 用 Python 创建数据库
python -c "
import asyncio, asyncpg

async def init():
    conn = await asyncpg.connect(user='postgres', host='127.0.0.1', port=5432)
    try:
        await conn.execute('CREATE DATABASE digital_brochure')
        print('✅ 数据库 digital_brochure 创建成功')
    except asyncpg.exceptions.DuplicateDatabaseError:
        print('✅ 数据库 digital_brochure 已存在')
    await conn.close()

asyncio.run(init())
"

:: ======== 第6步：Alembic 迁移 ========
echo 🔄 执行数据库迁移...
python -c "
import sys
sys.path.insert(0, '.')
from alembic.config import Config
from alembic import command

cfg = Config('alembic.ini')
command.upgrade(cfg, 'head')
print('✅ 数据库迁移完成')
"

:: ======== 第7步：验证 ========
echo.
echo 🔍 验证迁移结果...
python -c "
import asyncio, asyncpg

async def verify():
    conn = await asyncpg.connect(user='postgres', host='127.0.0.1', port=5432, database='digital_brochure')
    tables = await conn.fetch(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public'\")
    print(f'📊 共 {len(tables)} 个表:')
    for t in tables:
        print(f'   📄 {t[\"table_name\"]}')
    await conn.close()

asyncio.run(verify())
"

echo.
echo =============================================
echo  ✅ PG迁移全部完成！
echo =============================================
echo.
echo 接下来重启后端:
echo   1. 任务管理器关掉 python.exe (:8002)
echo   2. 双击 D:\AI数智名片\start_backend.bat
echo.
pause
