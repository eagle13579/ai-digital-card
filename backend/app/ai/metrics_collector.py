"""
AI 用量监控 — 按模型聚合的 Token 消耗/延迟/调用次数/错误率
=============================================================

架构:
  AIMetricsCollector (单例)
    ├─ record(model, tokens, latency_ms, is_error)  记录一次调用
    ├─ summary()          → 今日汇总数据
    ├─ models_summary()   → 按模型分组的统计
    ├─ persist()          → 写入 SQLite (重启恢复)
    └─ restore()          → 从 SQLite 恢复

数据流:
  1. AI 调用代码在返回后调用 collector.record()
  2. collector 更新内存计数器
  3. 每 60 秒或在 shutdown 时 persist() 写入 SQLite
  4. 服务重启时从 SQLite restore() 恢复

注意:
  - 同时向 MetricsMiddleware (Prometheus) 写入 AI 推理延迟
  - 内存计数器在纯重启时重置，但 SQLite 持久化可跨重启恢复当日数据
"""

import json
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ======================================================================
# SQLite 持久化路径
# ======================================================================

def _db_path() -> str:
    """返回 SQLite 数据库文件路径。"""
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "ai_metrics.db")


# ======================================================================
# 数据模型
# ======================================================================

class ModelStats:
    """单个模型的运行时统计。"""

    __slots__ = (
        "model_name", "call_count", "error_count",
        "total_tokens", "prompt_tokens", "completion_tokens",
        "total_latency_ms",
    )

    def __init__(self, model_name: str = ""):
        self.model_name: str = model_name
        self.call_count: int = 0
        self.error_count: int = 0
        self.total_tokens: int = 0
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.total_latency_ms: float = 0.0

    def record(self, tokens: int, latency_ms: float, is_error: bool,
               prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        """记录一次 AI 调用。"""
        self.call_count += 1
        self.total_tokens += tokens
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_latency_ms += latency_ms
        if is_error:
            self.error_count += 1

    @property
    def avg_latency_ms(self) -> float:
        if self.call_count == 0:
            return 0.0
        return round(self.total_latency_ms / self.call_count, 2)

    @property
    def error_rate(self) -> float:
        if self.call_count == 0:
            return 0.0
        return round(self.error_count / self.call_count, 4)

    def snapshot(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "error_rate": self.error_rate,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_latency_ms": round(self.total_latency_ms, 2),
            "avg_latency_ms": self.avg_latency_ms,
        }


# ======================================================================
# 采集器单例
# ======================================================================

class AIMetricsCollector:
    """AI 用量采集器 — 按模型聚合 Token 消耗、延迟和错误率。

    使用方式:
        collector = AIMetricsCollector.get_instance()
        collector.record("deepseek-chat", tokens=150, latency_ms=1200)
        summary = collector.summary()
    """

    _instance: "AIMetricsCollector | None" = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._models: dict[str, ModelStats] = {}
        self._start_time: float = time.time()
        self._day_date: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._restore_from_db()

    # ── 单例 ──────────────────────────────────────────────────────────

    @classmethod
    def get_instance(cls) -> "AIMetricsCollector":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── 记录 ──────────────────────────────────────────────────────────

    def record(self, model_name: str, tokens: int = 0, latency_ms: float = 0.0,
               is_error: bool = False, prompt_tokens: int = 0,
               completion_tokens: int = 0) -> None:
        """记录一次 AI 调用。

        Args:
            model_name: 模型名称 (e.g. "deepseek-chat", "deepseek-rag")
            tokens: 消耗的总 token 数
            latency_ms: 延迟毫秒数
            is_error: 是否错误
            prompt_tokens: prompt token 数
            completion_tokens: completion token 数
        """
        if model_name not in self._models:
            self._models[model_name] = ModelStats(model_name=model_name)

        self._models[model_name].record(
            tokens=tokens,
            latency_ms=latency_ms,
            is_error=is_error,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        # 检查是否需要切换日期
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._day_date:
            # 新的一天，重置计数器（但保留持久化数据用于跨天查询）
            self._reset_day(today)

    def record_error(self, model_name: str, latency_ms: float = 0.0) -> None:
        """记录一次 AI 调用错误（便捷方法）。"""
        self.record(model_name=model_name, tokens=0, latency_ms=latency_ms, is_error=True)

    # ── 聚合查询 ──────────────────────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        """今日 AI 用量汇总。"""
        total_calls = 0
        total_errors = 0
        total_tokens = 0
        total_latency = 0.0

        for stats in self._models.values():
            total_calls += stats.call_count
            total_errors += stats.error_count
            total_tokens += stats.total_tokens
            total_latency += stats.total_latency_ms

        return {
            "date": self._day_date,
            "total_calls": total_calls,
            "total_errors": total_errors,
            "error_rate": round(total_errors / max(total_calls, 1), 4),
            "total_tokens": total_tokens,
            "total_latency_ms": round(total_latency, 2),
            "avg_latency_ms": round(total_latency / max(total_calls, 1), 2) if total_calls > 0 else 0.0,
            "model_count": len(self._models),
            "uptime_seconds": round(time.time() - self._start_time),
        }

    def models_summary(self) -> list[dict[str, Any]]:
        """按模型分组的用量统计。"""
        return [
            stats.snapshot()
            for stats in sorted(self._models.values(), key=lambda s: s.call_count, reverse=True)
        ]

    # ── 日期重置 ──────────────────────────────────────────────────────

    def _reset_day(self, new_date: str) -> None:
        """切换到新的一天，重置内存计数器。"""
        # 持久化当前数据
        self._persist()
        # 重置内存
        self._models.clear()
        self._day_date = new_date
        self._start_time = time.time()
        logger.info("AI 指标已重置为新的一天: %s", new_date)

    # ── SQLite 持久化 ─────────────────────────────────────────────────

    def _ensure_db(self, conn: sqlite3.Connection) -> None:
        """确保 SQLite 表存在。"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                model_name TEXT NOT NULL,
                call_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_latency_ms REAL DEFAULT 0.0,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_metrics_date_model
            ON ai_metrics(date, model_name)
        """)
        conn.commit()

    def _persist(self) -> None:
        """将当前内存数据写入 SQLite。"""
        if not self._models:
            return
        try:
            conn = sqlite3.connect(_db_path(), timeout=5)
            self._ensure_db(conn)
            for stats in self._models.values():
                conn.execute("""
                    INSERT INTO ai_metrics (date, model_name, call_count, error_count,
                                            total_tokens, prompt_tokens, completion_tokens,
                                            total_latency_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(date, model_name) DO UPDATE SET
                        call_count = excluded.call_count,
                        error_count = excluded.error_count,
                        total_tokens = excluded.total_tokens,
                        prompt_tokens = excluded.prompt_tokens,
                        completion_tokens = excluded.completion_tokens,
                        total_latency_ms = excluded.total_latency_ms,
                        updated_at = datetime('now')
                """, (
                    self._day_date,
                    stats.model_name,
                    stats.call_count,
                    stats.error_count,
                    stats.total_tokens,
                    stats.prompt_tokens,
                    stats.completion_tokens,
                    stats.total_latency_ms,
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning("AI 指标 SQLite 持久化失败: %s", e)

    def _restore_from_db(self) -> None:
        """从 SQLite 恢复今日数据。"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        try:
            conn = sqlite3.connect(_db_path(), timeout=5)
            self._ensure_db(conn)
            cursor = conn.execute(
                "SELECT model_name, call_count, error_count, total_tokens, "
                "prompt_tokens, completion_tokens, total_latency_ms "
                "FROM ai_metrics WHERE date = ?",
                (today,)
            )
            rows = cursor.fetchall()
            for row in rows:
                model_name, call_count, error_count, total_tokens, prompt_tokens, completion_tokens, total_latency_ms = row
                stats = ModelStats(model_name=model_name)
                stats.call_count = call_count
                stats.error_count = error_count
                stats.total_tokens = total_tokens
                stats.prompt_tokens = prompt_tokens
                stats.completion_tokens = completion_tokens
                stats.total_latency_ms = total_latency_ms
                self._models[model_name] = stats
            conn.close()
            if rows:
                logger.info("从 SQLite 恢复了 %d 个模型的今日指标数据", len(rows))
        except Exception as e:
            logger.debug("SQLite 恢复失败（首次运行或无持久化数据）: %s", e)

    def persist_now(self) -> None:
        """立即持久化（可在 shutdown 时调用）。"""
        self._persist()

    def get_model(self, model_name: str) -> ModelStats | None:
        """获取指定模型的统计。"""
        return self._models.get(model_name)


# ======================================================================
# 模块级快捷函数
# ======================================================================

def get_collector() -> AIMetricsCollector:
    """获取全局 AI 指标采集器实例。"""
    return AIMetricsCollector.get_instance()


def record_ai_call(model_name: str, tokens: int = 0, latency_ms: float = 0.0,
                   is_error: bool = False, prompt_tokens: int = 0,
                   completion_tokens: int = 0) -> None:
    """记录一次 AI 调用到全局采集器（便捷函数）。

    在 AI 调用返回后调用:
        record_ai_call("deepseek-chat", tokens=150, latency_ms=1200.5)
    """
    collector = get_collector()
    collector.record(
        model_name=model_name,
        tokens=tokens,
        latency_ms=latency_ms,
        is_error=is_error,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )


def get_ai_metrics_summary() -> dict[str, Any]:
    """获取今日 AI 用量汇总。"""
    return get_collector().summary()


def get_ai_models_metrics() -> list[dict[str, Any]]:
    """获取按模型分组的 AI 用量统计。"""
    return get_collector().models_summary()
