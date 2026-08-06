"""optmem_service.py — OptMem 永久记忆服务（AI数智名片）

将 OptMem 原子化能力封装为应用服务：
  - 记忆库目录：$AGENT_MEMORY_DIR 或 backend/data/agent_memory（默认）
  - 进程内单例，保证同一库同一身份
  - 提供 wake/note/recall/zoom/nap/forget/stats 的完整封装
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from services.optmem_core import OptMemStore, OptMemError

logger = logging.getLogger(__name__)

_singleton: OptMemStore | None = None


def get_memory_dir() -> str:
    """解析记忆库目录（env 优先，默认项目 data 目录）。"""
    env = os.environ.get("AGENT_MEMORY_DIR")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    default = Path(__file__).resolve().parent.parent / "data" / "agent_memory"
    return str(default)


def get_memory() -> OptMemStore:
    """获取进程内 OptMem 单例（首次自动初始化）。"""
    global _singleton
    if _singleton is None:
        d = get_memory_dir()
        os.makedirs(d, exist_ok=True)
        store = OptMemStore(d)
        if not os.path.exists(store.log_path()):
            store.init()
            logger.info("OptMem 记忆库已创建: %s", d)
        _singleton = store
        logger.info("OptMem 记忆库就绪: %s (%d 条)", d, store.log_len())
    return _singleton


def reset_singleton() -> None:
    """重置单例（测试用）。"""
    global _singleton
    _singleton = None


# ───────────────────────── 面向 API 的包装 ─────────────────────────

def stats() -> dict:
    m = get_memory()
    cfg = m.config_get()
    return {
        "dir": m.dir,
        "memories": m.log_len(),
        "pending": m.pending_count(),
        "config": {k: cfg[k] for k in ("WAKE_LINES", "ENTRY_CHARS")},
    }


def wake(limit: int | None = None) -> dict:
    m = get_memory()
    return m.wake(limit=limit)


def note(text: str) -> dict:
    m = get_memory()
    return m.note(text)


def recall(regex: str, newest: int = 20000) -> dict:
    m = get_memory()
    return m.recall(regex, newest=newest)


def zoom(block: str) -> dict:
    m = get_memory()
    return m.zoom(block)


def nap(block: str, summary: str) -> dict:
    m = get_memory()
    return m.nap(block, summary)


def forget(block: str) -> dict:
    m = get_memory()
    return m.forget(block)
