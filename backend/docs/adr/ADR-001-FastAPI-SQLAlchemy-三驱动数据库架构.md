# ADR-001: FastAPI + SQLAlchemy + 三驱动数据库架构

**状态**: Accepted
**日期**: 2026-06-26
**决策者**: 架构组

## 上下文

链客宝作为 B2B 匹配 SaaS 平台，需要支撑以下数据访问场景：

1. **核心业务存储** — 用户、企业、匹配关系等结构化数据（PostgreSQL）
2. **全文搜索** — 企业简介、产品描述等中文全文检索与高亮（Elasticsearch）
3. **缓存与会话** — 高频读取的热数据与分布式会话（Redis）
4. **统一的事务管理** — 跨驱动的事务协调需求

初始方案讨论中出现两个方向：
- **方向 A**：只用 PostgreSQL，搜索用 `pg_search` / `pgvector` 扩展
- **方向 B**：PostgreSQL + 专门的搜索引擎 + 缓存层，每个驱动独立管理

## 决策

采用 **FastAPI + SQLAlchemy Async** 作为 ORM 底座，**同时注册三个数据库驱动**：

| 驱动 | 数据库 | 用途 |
|------|--------|------|
| `asyncpg` (via asyncpg driver) | PostgreSQL | 核心业务持久化，强事务 |
| `opensearch-py-async` / `elasticsearch-py` | Elasticsearch / OpenSearch | 全文搜索、企业匹配索引 |
| `redis-py` (async) | Redis | 缓存、分布式 Session、消息队列 |

统一通过 `app/core/db.py` 中的 `async def get_db()` 和 `get_redis()` 等依赖注入暴露。

## 理由

1. **最佳工具做最佳工作** — PostgreSQL 的 pg_search 在中文分词、高亮、评分算法上与专用搜索引擎有差距。B2B 匹配依赖复杂的搜索召回和排序逻辑，专用搜索引擎更合适。
2. **SQLAlchemy Async 天然支持多引擎** — `create_async_engine` 可以创建多个引擎实例，通过 `AsyncSession` 绑定不同的 `bind` 实现多库路由，代码结构清晰。
3. **性能与可靠性分离** — Redis 缓存层隔离高频读请求，减少 PostgreSQL 连接压力；搜索流量走 ES 集群，不影响核心写入链路。
4. **团队熟悉度** — 团队已有 SQLAlchemy + asyncpg 使用经验，无需引入 Tortoise ORM 或 Beanie 等新框架。

## 后果

**正面**:
- 各数据库独立扩展，互不影响
- 搜索能力强，支持中文分词、同义词、评分调优
- 缓存层可独立降级（Redis 挂掉不影响核心写操作）

**负面**:
- 维护三个数据库驱动增加了运维复杂度
- 跨驱动无法做分布式事务（需通过 Saga 或最终一致性补偿）
- 本地开发需要启动 PostgreSQL + Redis + ES 三个服务，环境配置成本更高

## 替代方案

| 方案 | 否决理由 |
|------|---------|
| 纯 PostgreSQL + pg_search | 中文搜索能力不足，企业级 B2B 匹配需要复杂 scoring |
| Tortoise ORM | 社区生态不如 SQLAlchemy 成熟，异步支持 SQLAlchemy 已足够 |
| MongoDB + Atlas Search | 团队无 MongoDB 运维经验，且关系型数据（企业-用户-匹配）用文档型数据库建模反直觉 |
| 单体数据库 + 应用层做搜索 | 实现类似 Elasticsearch 的倒排索引+评分算法成本极高，不现实 |
