"""
链客宝 — SLA 监控服务
=====================
追踪可用性(99.9%/99.99%)、响应时间(P50/P95/P99)、错误率，
计算 7 日 / 30 日 SLA 达成率，低于阈值触发告警。

架构:
  - SlaMonitor: 核心引擎，内存 + SQLite 持久化
  - 外部通过 API 查询状态和报告
  - 与 Prometheus 指标 /metrics 联动

用法:
    from app.services.sla_monitor import sla_monitor
    await sla_monitor.record_request(status_code, latency_ms)
    report = await sla_monitor.get_report(days=7)
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("chainke.sla")


# ════════════════════════════════════════════════════════════════════════
# 配置常量
# ════════════════════════════════════════════════════════════════════════

# SLA 目标层级
SLA_TIERS = {
    "tier1": {"availability": 99.99, "p99_ms": 200, "error_rate": 0.001},  # 关键 API
    "tier2": {"availability": 99.9, "p99_ms": 500, "error_rate": 0.01},   # 标准 API
    "tier3": {"availability": 99.0, "p99_ms": 2000, "error_rate": 0.05},  # 后台/批处理
}

# 告警阈值 (超过即告警)
ALERT_THRESHOLDS = {
    "availability_7d": 99.5,       # 7 日可用性低于 99.5% 告警
    "availability_30d": 99.8,      # 30 日可用性低于 99.8% 告警
    "p99_latency": 1000,           # P99 延迟超过 1000ms 告警
    "error_rate_5m": 0.05,         # 5 分钟错误率超过 5% 告警
}

DB_PATH = Path(__file__).resolve().parent.parent / "sla_data.db"


# ════════════════════════════════════════════════════════════════════════
# 数据模型
# ════════════════════════════════════════════════════════════════════════


@dataclass
class SlaRecord:
    """单次请求记录 (聚合级别)"""
    timestamp: float  # Unix timestamp (秒)
    tier: str         # tier1 / tier2 / tier3
    total: int = 0
    success: int = 0
    error: int = 0
    latency_sum: float = 0.0
    latency_buckets: list[float] = field(default_factory=lambda: [0.0] * 101)  # 百分位桶


@dataclass
class SlaReport:
    """SLA 报告"""
    period_days: int
    total_requests: int
    availability: float           # 百分比 (99.9)
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    sla_met: bool                 # 是否达标
    by_tier: dict[str, dict[str, Any]] = field(default_factory=dict)
    alerts: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SlaAlert:
    """SLA 告警记录"""
    timestamp: float
    rule: str                     # 告警规则名
    current_value: float
    threshold: float
    severity: str                 # warning / critical
    message: str
    acknowledged: bool = False


# ════════════════════════════════════════════════════════════════════════
# 持久化层 (SQLite)
# ════════════════════════════════════════════════════════════════════════


class SlaStorage:
    """SLA 数据持久化"""

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path))
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sla_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                tier TEXT NOT NULL DEFAULT 'tier2',
                total INTEGER NOT NULL DEFAULT 0,
                success INTEGER NOT NULL DEFAULT 0,
                error INTEGER NOT NULL DEFAULT 0,
                latency_sum REAL NOT NULL DEFAULT 0.0,
                latency_buckets TEXT NOT NULL DEFAULT '[]'
            );
            CREATE TABLE IF NOT EXISTS sla_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                rule TEXT NOT NULL,
                current_value REAL NOT NULL,
                threshold REAL NOT NULL,
                severity TEXT NOT NULL DEFAULT 'warning',
                message TEXT NOT NULL,
                acknowledged INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_sla_records_ts ON sla_records(timestamp);
            CREATE INDEX IF NOT EXISTS idx_sla_alerts_ts ON sla_alerts(timestamp);
        """)
        conn.commit()

    def save_record(self, record: SlaRecord) -> None:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO sla_records (timestamp, tier, total, success, error, latency_sum, latency_buckets)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                record.timestamp,
                record.tier,
                record.total,
                record.success,
                record.error,
                record.latency_sum,
                json.dumps(record.latency_buckets),
            ),
        )
        conn.commit()

    def save_alert(self, alert: SlaAlert) -> None:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO sla_alerts (timestamp, rule, current_value, threshold, severity, message)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                alert.timestamp,
                alert.rule,
                alert.current_value,
                alert.threshold,
                alert.severity,
                alert.message,
            ),
        )
        conn.commit()

    def query_records(self, since: float, until: float | None = None) -> list[SlaRecord]:
        conn = self._get_conn()
        if until is None:
            until = time.time()
        rows = conn.execute(
            "SELECT * FROM sla_records WHERE timestamp >= ? AND timestamp <= ? ORDER BY timestamp",
            (since, until),
        ).fetchall()
        records = []
        for row in rows:
            records.append(SlaRecord(
                timestamp=row["timestamp"],
                tier=row["tier"],
                total=row["total"],
                success=row["success"],
                error=row["error"],
                latency_sum=row["latency_sum"],
                latency_buckets=json.loads(row["latency_buckets"]),
            ))
        return records

    def query_alerts(self, since: float, until: float | None = None, limit: int = 100) -> list[SlaAlert]:
        conn = self._get_conn()
        if until is None:
            until = time.time()
        rows = conn.execute(
            "SELECT * FROM sla_alerts WHERE timestamp >= ? AND timestamp <= ? ORDER BY timestamp DESC LIMIT ?",
            (since, until, limit),
        ).fetchall()
        return [
            SlaAlert(
                timestamp=row["timestamp"],
                rule=row["rule"],
                current_value=row["current_value"],
                threshold=row["threshold"],
                severity=row["severity"],
                message=row["message"],
                acknowledged=bool(row["acknowledged"]),
            )
            for row in rows
        ]


# ════════════════════════════════════════════════════════════════════════
# SLA 监控引擎
# ════════════════════════════════════════════════════════════════════════


class SlaMonitor:
    """SLA 监控核心引擎"""

    def __init__(self, storage: SlaStorage | None = None):
        self.storage = storage or SlaStorage()
        self._buffer: list[SlaRecord] = []
        self._buffer_lock = threading.Lock()
        self._alerts: list[SlaAlert] = []
        self._flush_interval = 60  # 每 60 秒刷盘一次
        self._running = False
        self._task: asyncio.Task | None = None

    # ── 公共 API ──────────────────────────────────────────────────────

    async def start(self) -> None:
        """启动后台刷盘协程"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._flush_loop())
        logger.info("[SLA Monitor] 已启动 (flush interval=%ds)", self._flush_interval)

    async def stop(self) -> None:
        """停止后台刷盘"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._flush()
        logger.info("[SLA Monitor] 已停止")

    async def record_request(
        self,
        status_code: int,
        latency_ms: float,
        tier: str = "tier2",
    ) -> None:
        """记录一次请求结果

        Args:
            status_code: HTTP 状态码
            latency_ms: 延迟 (毫秒)
            tier: SLA 层级 (tier1/tier2/tier3)
        """
        now = time.time()
        minute_ts = int(now / 60) * 60  # 按分钟聚合

        success = 1 if status_code < 500 else 0
        error = 1 if status_code >= 400 else 0

        record = SlaRecord(
            timestamp=minute_ts,
            tier=tier,
            total=1,
            success=success,
            error=error,
            latency_sum=latency_ms,
            latency_buckets=[0.0] * 101,
        )
        # 更新百分位桶 (简化: 记录到最近的 1ms 桶)
        bucket_idx = min(int(latency_ms), 100)
        record.latency_buckets[bucket_idx] += 1.0

        with self._buffer_lock:
            self._buffer.append(record)

    async def get_status(self) -> dict[str, Any]:
        """获取当前 SLA 状态快照"""
        now = time.time()
        seven_days_ago = now - 7 * 86400
        thirty_days_ago = now - 30 * 86400

        report_7d = self._compute_report(seven_days_ago, now)
        report_30d = self._compute_report(thirty_days_ago, now)

        recent_alerts = self.storage.query_alerts(since=now - 86400, limit=50)
        return {
            "current": {
                "uptime_7d": round(report_7d.availability, 4),
                "uptime_30d": round(report_30d.availability, 4),
                "p50_latency_ms": round(report_7d.p50_latency_ms, 2),
                "p95_latency_ms": round(report_7d.p95_latency_ms, 2),
                "p99_latency_ms": round(report_7d.p99_latency_ms, 2),
                "error_rate_5m": round(self._error_rate_last_5m(), 6),
                "error_rate_7d": round(report_7d.error_rate, 6),
                "total_requests_7d": report_7d.total_requests,
            },
            "sla_met": {
                "tier1_7d": report_7d.availability >= SLA_TIERS["tier1"]["availability"],
                "tier2_7d": report_7d.availability >= SLA_TIERS["tier2"]["availability"],
                "tier3_7d": report_7d.availability >= SLA_TIERS["tier3"]["availability"],
                "tier1_30d": report_30d.availability >= SLA_TIERS["tier1"]["availability"],
                "tier2_30d": report_30d.availability >= SLA_TIERS["tier2"]["availability"],
                "tier3_30d": report_30d.availability >= SLA_TIERS["tier3"]["availability"],
            },
            "recent_alerts": [asdict(a) for a in recent_alerts],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_report(self, days: int = 7) -> dict[str, Any]:
        """获取 SLA 报告

        Args:
            days: 报告覆盖天数 (7 或 30)

        Returns:
            包含完整 SLA 统计的报告字典
        """
        now = time.time()
        since = now - days * 86400
        report = self._compute_report(since, now)
        self._check_alerts(report)

        result = asdict(report)
        result["period_end"] = datetime.now(timezone.utc).isoformat()
        result["period_start"] = datetime.fromtimestamp(since, tz=timezone.utc).isoformat()
        return result

    async def get_alerts(
        self,
        since_hours: int = 24,
        severity: str | None = None,
    ) -> list[dict[str, Any]]:
        """获取告警历史

        Args:
            since_hours: 过去多少小时
            severity: 过滤严重级别 (warning/critical)
        """
        now = time.time()
        since = now - since_hours * 3600
        alerts = self.storage.query_alerts(since=since, limit=200)
        result = [asdict(a) for a in alerts]
        if severity:
            result = [a for a in result if a["severity"] == severity]
        return result

    # ── 内部方法 ──────────────────────────────────────────────────────

    def _compute_report(self, since: float, until: float) -> SlaReport:
        records = self.storage.query_records(since, until)
        if not records:
            return SlaReport(
                period_days=int((until - since) / 86400),
                total_requests=0,
                availability=100.0,
                p50_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
                error_rate=0.0,
                sla_met=True,
            )

        total = sum(r.total for r in records)
        success = sum(r.success for r in records)
        errors_ = sum(r.error for r in records)
        latency_total = sum(r.latency_sum for r in records)

        # 可用性 = (成功请求 / 总请求) * 100
        availability = (success / total * 100) if total > 0 else 100.0
        error_rate = (errors_ / total) if total > 0 else 0.0
        (latency_total / total) if total > 0 else 0.0

        # 百分位计算 (聚合所有记录的 latency_buckets)
        all_latencies = []
        for r in records:
            for bucket_idx, count in enumerate(r.latency_buckets):
                if count > 0:
                    all_latencies.extend([bucket_idx] * int(count))

        p50 = self._percentile(all_latencies, 50) if all_latencies else 0.0
        p95 = self._percentile(all_latencies, 95) if all_latencies else 0.0
        p99 = self._percentile(all_latencies, 99) if all_latencies else 0.0

        # 按层级统计
        tiers: dict[str, list[SlaRecord]] = defaultdict(list)
        for r in records:
            tiers[r.tier].append(r)

        by_tier = {}
        for tier_name, tier_records in tiers.items():
            t_total = sum(r.total for r in tier_records)
            t_success = sum(r.success for r in tier_records)
            t_errors = sum(r.error for r in tier_records)
            t_avail = (t_success / t_total * 100) if t_total > 0 else 100.0
            t_err_rate = (t_errors / t_total) if t_total > 0 else 0.0
            t_latencies = []
            for r in tier_records:
                for bidx, cnt in enumerate(r.latency_buckets):
                    if cnt > 0:
                        t_latencies.extend([bidx] * int(cnt))
            by_tier[tier_name] = {
                "total_requests": t_total,
                "availability": round(t_avail, 4),
                "error_rate": round(t_err_rate, 6),
                "p50_ms": round(self._percentile(t_latencies, 50), 2) if t_latencies else 0,
                "p95_ms": round(self._percentile(t_latencies, 95), 2) if t_latencies else 0,
                "p99_ms": round(self._percentile(t_latencies, 99), 2) if t_latencies else 0,
            }

        sla_met = availability >= ALERT_THRESHOLDS["availability_7d"]

        return SlaReport(
            period_days=int((until - since) / 86400),
            total_requests=total,
            availability=round(availability, 4),
            p50_latency_ms=round(p50, 2),
            p95_latency_ms=round(p95, 2),
            p99_latency_ms=round(p99, 2),
            error_rate=round(error_rate, 6),
            sla_met=sla_met,
            by_tier=by_tier,
        )

    def _error_rate_last_5m(self) -> float:
        """计算最近 5 分钟的错误率"""
        now = time.time()
        since = now - 300  # 5 分钟
        records = self.storage.query_records(since, now)
        total = sum(r.total for r in records)
        errors_ = sum(r.error for r in records)
        return (errors_ / total) if total > 0 else 0.0

    def _check_alerts(self, report: SlaReport) -> None:
        """检查是否需要触发告警"""
        now = time.time()

        # 可用性告警
        if report.availability < ALERT_THRESHOLDS["availability_7d"]:
            alert = SlaAlert(
                timestamp=now,
                rule="availability_7d_below_threshold",
                current_value=report.availability,
                threshold=ALERT_THRESHOLDS["availability_7d"],
                severity="critical",
                message=f"7日SLA可用性 {report.availability}% 低于阈值 {ALERT_THRESHOLDS['availability_7d']}%",
            )
            self.storage.save_alert(alert)
            logger.warning("[SLA Alert] %s", alert.message)

        # P99 延迟告警
        if report.p99_latency_ms > ALERT_THRESHOLDS["p99_latency"]:
            alert = SlaAlert(
                timestamp=now,
                rule="p99_latency_above_threshold",
                current_value=report.p99_latency_ms,
                threshold=ALERT_THRESHOLDS["p99_latency"],
                severity="warning",
                message=f"P99延迟 {report.p99_latency_ms}ms 超过阈值 {ALERT_THRESHOLDS['p99_latency']}ms",
            )
            self.storage.save_alert(alert)
            logger.warning("[SLA Alert] %s", alert.message)

        # 错误率告警
        error_5m = self._error_rate_last_5m()
        if error_5m > ALERT_THRESHOLDS["error_rate_5m"]:
            alert = SlaAlert(
                timestamp=now,
                rule="error_rate_5m_above_threshold",
                current_value=error_5m,
                threshold=ALERT_THRESHOLDS["error_rate_5m"],
                severity="warning",
                message=f"5分钟错误率 {error_5m:.4f} 超过阈值 {ALERT_THRESHOLDS['error_rate_5m']}",
            )
            self.storage.save_alert(alert)
            logger.warning("[SLA Alert] %s", alert.message)

    @staticmethod
    def _percentile(data: list[float], percent: int) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * percent / 100
        f = int(k)
        c = k - f
        if f + 1 < len(sorted_data):
            return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c
        return sorted_data[-1]

    async def _flush_loop(self) -> None:
        """后台刷盘循环"""
        while self._running:
            await asyncio.sleep(self._flush_interval)
            try:
                self._flush()
            except Exception as e:
                logger.error("[SLA Monitor] 刷盘失败: %s", e)

    def _flush(self) -> None:
        """将缓冲区数据刷入数据库"""
        with self._buffer_lock:
            if not self._buffer:
                return
            batch = self._buffer
            self._buffer = []

        # 按分钟 + tier 聚合
        aggregated: dict[tuple[int, str], SlaRecord] = {}
        for rec in batch:
            key = (int(rec.timestamp), rec.tier)
            if key in aggregated:
                existing = aggregated[key]
                existing.total += rec.total
                existing.success += rec.success
                existing.error += rec.error
                existing.latency_sum += rec.latency_sum
                for i in range(101):
                    existing.latency_buckets[i] += rec.latency_buckets[i]
            else:
                aggregated[key] = rec

        for record in aggregated.values():
            self.storage.save_record(record)

        logger.debug("[SLA Monitor] 刷盘完成: %d 条记录聚合为 %d 条", len(batch), len(aggregated))


# ════════════════════════════════════════════════════════════════════════
# 全局单例
# ════════════════════════════════════════════════════════════════════════

sla_monitor = SlaMonitor()
