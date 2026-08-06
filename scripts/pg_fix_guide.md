# PostgreSQL 连接修复

## 问题
端口 5432 开放但连接认证失败。

## 修复方法

### 方法1: 修改 pg_hba.conf（推荐）
1. 找到 PostgreSQL 安装目录下的 `data/pg_hba.conf`
2. 将 `METHOD` 从 `scram-sha-256` 改为 `trust`
3. 重启 PostgreSQL 服务: `net stop postgresql-x64-16 && net start postgresql-x64-16`

### 方法2: 重置密码
`psql -U postgres -c "ALTER USER postgres PASSWORD 'postgres';"`

### 方法3: 用 Docker 启动新 PG（如果 Docker 可用）
`docker run -d --name pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16`
