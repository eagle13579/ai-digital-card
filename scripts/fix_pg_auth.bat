@echo off
chcp 65001 >nul
echo ==========================================
echo  PostgreSQL 认证修复脚本
echo ==========================================
echo.
echo 当前PG版本: 18 (postgresql-x64-18)
echo 数据目录: D:\PostgreSQL\18\data
echo.
echo 步骤1: 定位 pg_hba.conf
set PGDATA=D:\PostgreSQL\18\data
if exist "%PGDATA%\pg_hba.conf" (
    echo ✅ pg_hba.conf 已找到
) else (
    echo ❌ 未找到 pg_hba.conf，请手动确认路径
    pause
    exit /b
)

echo.
echo 步骤2: 备份原始文件
copy "%PGDATA%\pg_hba.conf" "%PGDATA%\pg_hba.conf.bak" >nul
echo ✅ 已备份为 pg_hba.conf.bak

echo.
echo 步骤3: 将认证方式从 scram-sha-256 改为 trust
powershell -Command "(Get-Content '%PGDATA%\pg_hba.conf') -replace 'scram-sha-256', 'trust' | Set-Content '%PGDATA%\pg_hba.conf'"
echo ✅ 认证方式已改为 trust

echo.
echo 步骤4: 重启 PostgreSQL 服务
net stop postgresql-x64-18
net start postgresql-x64-18

echo.
echo ==========================================
echo  完成！PG 认证已修复
echo  现在可以跑: cd D:\AI数智名片\backend
echo  python -m alembic upgrade head
echo ==========================================
pause
