# 数据库迁移运行手册

## PostgreSQL切换步骤
1. 安装PostgreSQL + asyncpg: `pip install asyncpg psycopg2-binary`
2. 创建数据库: `createdb ai_digital_card`
3. 更新.env: `DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ai_digital_card`
4. 启动应用: 自动检测PG并使用连接池(pool_size=20)
5. 运行迁移: `alembic upgrade head`

## 回滚
- alembic downgrade -1
