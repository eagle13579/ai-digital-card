"""DatabaseMonitor — 慢查询检测 + 连接池监控 + 健康检查。

用法::

    from app.database_monitor import DatabaseMonitor
    monitor = DatabaseMonitor()
    await monitor.check_connection()
    stats = monitor.pool_stats()
"""

import time
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

logger = logging.getLogger("db_monitor")

SLOW_QUERY_THRESHOLD_MS: float = 500.0


class DatabaseMonitor:
    """数据库运行时监控器。

    Attributes:
        engine: SQLAlchemy 异步引擎实例。
        session_factory: 异步会话工厂。
    """

    def __init__(
        self,
        engine: AsyncEngine | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        from app.database import engine as _engine, AsyncSessionLocal

        self.engine: AsyncEngine = engine or _engine
        self.session_factory: async_sessionmaker[AsyncSession] = (
            session_factory or AsyncSessionLocal
        )

    # ── 慢查询日志包装器 ────────────────────────────────────────────

    async def _tracked_execute(
        self, session: AsyncSession, sql: Any, *args: Any, **kwargs: Any
    ) -> Any:
        """执行查询并记录超过阈值的慢查询。"""
        start = time.perf_counter()
        try:
            result = await session.execute(sql, *args, **kwargs)
            return result
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            if elapsed_ms > SLOW_QUERY_THRESHOLD_MS:
                stmt_str = str(sql).strip()[:200]
                logger.warning(
                    "SLOW_QUERY (%.1f ms) | %s",
                    elapsed_ms,
                    stmt_str,
                )

    # ── 连接池状态 ──────────────────────────────────────────────────

    def pool_stats(self) -> dict[str, int]:
        """返回连接池统计信息。

        Returns:
            包含 *size*, *active*, *waiting* 的字典。
            SQLite (StaticPool) 等不支持池化的引擎返回各字段为 0。
        """
        try:
            sync_engine = self.engine.sync_engine
            pool = sync_engine.pool
            pool_size = pool.size() if hasattr(pool, "size") else 0
            checkedout = pool.checkedout() if hasattr(pool, "checkedout") else 0
            waiting = 0
            if hasattr(pool, "_pool") and hasattr(pool._pool, "_waiters"):
                waiting = len(pool._pool._waiters)
            return {
                "size": pool_size,
                "active": checkedout,
                "waiting": waiting,
            }
        except Exception as exc:
            logger.warning("pool_stats 获取失败: %s", exc)
            return {"size": 0, "active": 0, "waiting": 0}

    # ── 健康检查 ────────────────────────────────────────────────────

    async def check_connection(self) -> dict[str, Any]:
        """执行一次简单查询验证数据库连接是否正常。

        Returns:
            包含 *status*, *latency_ms*, *error* 的字典。
        """
        start = time.perf_counter()
        try:
            async with self.session_factory() as session:
                await session.execute(text("SELECT 1"))
            latency_ms = (time.perf_counter() - start) * 1000
            return {
                "status": "ok",
                "latency_ms": round(latency_ms, 2),
                "error": None,
            }
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            return {
                "status": "error",
                "latency_ms": round(latency_ms, 2),
                "error": str(exc),
            }
