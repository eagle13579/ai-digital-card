"""DBQueryMonitor — 数据库查询性能监控中间件/装饰器。

通过装饰器或上下文管理器包装查询，记录执行时间并报告慢查询。
"""

import time
import logging
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, AsyncGenerator, Callable

logger = logging.getLogger("db_query_monitor")

SLOW_QUERY_THRESHOLD_MS: float = 500.0


@asynccontextmanager
async def track_query(
    label: str = "db_query",
    threshold_ms: float = SLOW_QUERY_THRESHOLD_MS,
) -> AsyncGenerator[None, None]:
    """异步上下文管理器，跟踪数据库查询耗时。

    Args:
        label: 查询标签（如表名或操作名）。
        threshold_ms: 慢查询阈值（毫秒）。

    Usage::

        async with track_query("users.insert"):
            await db.execute(...)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > threshold_ms:
            logger.warning(
                "SLOW_QUERY [%s]: %.1f ms (threshold=%d ms)",
                label,
                elapsed_ms,
                threshold_ms,
            )
        else:
            logger.debug("QUERY [%s]: %.1f ms", label, elapsed_ms)


def monitor_query(
    label: str | None = None,
    threshold_ms: float = SLOW_QUERY_THRESHOLD_MS,
) -> Callable[..., Any]:
    """装饰器：自动跟踪异步函数的执行时间。

    Args:
        label: 查询标签，默认使用函数名。
        threshold_ms: 慢查询阈值（毫秒）。

    Usage::

        @monitor_query(label="get_user")
        async def get_user(db, user_id):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            _label = label or func.__name__
            async with track_query(label=_label, threshold_ms=threshold_ms):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
