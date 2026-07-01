"""
APM / Prometheus 监控中间件 — 纯 Python 实现，不依赖 prometheus_client。

指标：
  - ncard_http_requests_total             计数器（按 status="2xx|4xx|5xx" 分片）
  - ncard_http_request_duration_seconds   直方图（10 个 bucket）
  - ncard_http_active_requests            仪表盘（当前并发请求数）
  - ncard_db_query_duration_seconds       直方图（DB 查询延迟，秒）
  - ncard_ai_inference_duration_seconds   直方图（AI 推理延迟，秒）
  - ncard_cache_operations_total          计数器（按 type="hit|miss" 分片）
"""

import time
import logging
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)

# ── 模块级单例引用 ─────────────────────────
# 由 MetricsMiddleware.__init__ 自动注册，供 /metrics 路由读取
_metrics_instance: "MetricsMiddleware | None" = None


def get_metrics_instance() -> "MetricsMiddleware | None":
    """获取当前 MetricsMiddleware 实例（可能为 None）。"""
    return _metrics_instance


class MetricsMiddleware:
    """ASGI 中间件，采集 HTTP 请求指标并暴露 Prometheus 文本格式。"""

    def __init__(self, app):
        self.app = app
        global _metrics_instance
        _metrics_instance = self

        # ── 计数器 ────────────────────────────
        self.total_requests = 0
        self.successful_requests = 0  # 2xx
        self.client_errors = 0        # 4xx
        self.server_errors = 0        # 5xx

        # ── 活跃请求（仪表盘） ────────────────
        self.active_requests = 0

        # ── 延迟列表 & 直方图 ────────────────
        self.request_times: list[float] = []  # 秒（保留最近 10k 条）
        self.total_sum = 0.0
        self.total_count = 0
        # 标准 Prometheus bucket 边界（秒）
        self.buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
        self.bucket_counts = {le: 0 for le in self.buckets}

        # 防止 request_times 无限增长
        self._max_times = 10000

        # ── DB 查询延迟直方图 ─────────────────
        self.db_query_count = 0
        self.db_query_sum = 0.0
        self.db_query_bucket_counts = {le: 0 for le in self.buckets}

        # ── AI 推理延迟直方图 ─────────────────
        self.ai_inference_count = 0
        self.ai_inference_sum = 0.0
        self.ai_inference_bucket_counts = {le: 0 for le in self.buckets}
        # AI 推理用更宽的 bucket（模型调用通常较慢）
        self.ai_buckets = [0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0]
        self.ai_inference_bucket_counts = {le: 0 for le in self.ai_buckets}

        # ── 缓存命中/未命中计数器 ─────────────
        self.cache_hits = 0
        self.cache_misses = 0

    # ------------------------------------------------------------------
    # 内部辅助：记录延迟到直方图
    # ------------------------------------------------------------------
    def _record_duration(self, bucket_counts: dict, count: int, total_sum: float, dur: float, buckets: list[float]):
        """将 dur（秒）记录到直方图 buckets 中，返回更新后的 (count, total_sum, bucket_counts)。"""
        count += 1
        total_sum += dur
        for bucket in buckets:
            if dur <= bucket:
                bucket_counts[bucket] += 1
        return count, total_sum, bucket_counts

    # ------------------------------------------------------------------
    # ASGI 入口
    # ------------------------------------------------------------------
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # /metrics 端点不计入指标，避免递归
        if scope["path"] == "/metrics":
            await self.app(scope, receive, send)
            return

        self.active_requests += 1
        self.total_requests += 1
        start = time.monotonic()

        # 包装 send 以嗅探响应状态码
        async def _send_wrapper(message):
            if message["type"] == "http.response.start":
                code = message["status"]
                if code < 400:
                    self.successful_requests += 1
                elif code < 500:
                    self.client_errors += 1
                else:
                    self.server_errors += 1
            await send(message)

        try:
            await self.app(scope, receive, _send_wrapper)
        finally:
            self.active_requests -= 1
            dur = time.monotonic() - start

            # 直方图
            self.total_count += 1
            self.total_sum += dur
            for bucket in self.buckets:
                if dur <= bucket:
                    self.bucket_counts[bucket] += 1

            # 保留最近 N 条用于调试
            self.request_times.append(dur)
            if len(self.request_times) > self._max_times:
                self.request_times = self.request_times[-self._max_times:]

    # ------------------------------------------------------------------
    # 公共 API：记录 DB 查询延迟
    # ------------------------------------------------------------------
    def observe_db_query(self, duration_seconds: float):
        """记录一次 DB 查询延迟（秒）。"""
        self.db_query_count += 1
        self.db_query_sum += duration_seconds
        for bucket in self.buckets:
            if duration_seconds <= bucket:
                self.db_query_bucket_counts[bucket] += 1

    # ------------------------------------------------------------------
    # 公共 API：记录 AI 推理延迟
    # ------------------------------------------------------------------
    def observe_ai_inference(self, duration_seconds: float):
        """记录一次 AI 推理延迟（秒）。"""
        self.ai_inference_count += 1
        self.ai_inference_sum += duration_seconds
        for bucket in self.ai_buckets:
            if duration_seconds <= bucket:
                self.ai_inference_bucket_counts[bucket] += 1

    # ------------------------------------------------------------------
    # 公共 API：缓存命中/未命中
    # ------------------------------------------------------------------
    def record_cache_hit(self):
        """记录一次缓存命中。"""
        self.cache_hits += 1

    def record_cache_miss(self):
        """记录一次缓存未命中。"""
        self.cache_misses += 1

    # ------------------------------------------------------------------
    # Prometheus 文本格式输出
    # ------------------------------------------------------------------
    def generate_metrics(self) -> str:
        lines: list[str] = []

        # ── 请求总数（Counter） ────────────────
        lines.append("# HELP ncard_http_requests_total Total HTTP requests by status class")
        lines.append("# TYPE ncard_http_requests_total counter")
        lines.append(f'ncard_http_requests_total{{status="2xx"}} {self.successful_requests}')
        lines.append(f'ncard_http_requests_total{{status="4xx"}} {self.client_errors}')
        lines.append(f'ncard_http_requests_total{{status="5xx"}} {self.server_errors}')
        lines.append("")

        # ── 请求延迟分布（Histogram） ──────────
        prefix = "ncard_http_request_duration_seconds"
        lines.append(f"# HELP {prefix} HTTP request duration distribution in seconds")
        lines.append(f"# TYPE {prefix} histogram")
        for le in self.buckets:
            lines.append(f'{prefix}_bucket{{le="{le}"}} {self.bucket_counts[le]}')
        lines.append(f'{prefix}_bucket{{le="+Inf"}} {self.total_count}')
        lines.append(f'{prefix}_count {self.total_count}')
        lines.append(f'{prefix}_sum {self.total_sum:.9f}')
        lines.append("")

        # ── 活跃请求数（Gauge） ────────────────
        lines.append("# HELP ncard_http_active_requests Currently active HTTP requests")
        lines.append("# TYPE ncard_http_active_requests gauge")
        lines.append(f"ncard_http_active_requests {self.active_requests}")
        lines.append("")

        # ── DB 查询延迟（Histogram） ───────────
        db_prefix = "ncard_db_query_duration_seconds"
        lines.append(f"# HELP {db_prefix} Database query duration distribution in seconds")
        lines.append(f"# TYPE {db_prefix} histogram")
        if self.db_query_count > 0:
            for le in self.buckets:
                lines.append(f'{db_prefix}_bucket{{le="{le}"}} {self.db_query_bucket_counts[le]}')
            lines.append(f'{db_prefix}_bucket{{le="+Inf"}} {self.db_query_count}')
            lines.append(f'{db_prefix}_count {self.db_query_count}')
            lines.append(f'{db_prefix}_sum {self.db_query_sum:.9f}')
        else:
            for le in self.buckets:
                lines.append(f'{db_prefix}_bucket{{le="{le}"}} 0')
            lines.append(f'{db_prefix}_bucket{{le="+Inf"}} 0')
            lines.append(f'{db_prefix}_count 0')
            lines.append(f'{db_prefix}_sum 0.0')
        lines.append("")

        # ── AI 推理延迟（Histogram） ───────────
        ai_prefix = "ncard_ai_inference_duration_seconds"
        lines.append(f"# HELP {ai_prefix} AI inference duration distribution in seconds")
        lines.append(f"# TYPE {ai_prefix} histogram")
        if self.ai_inference_count > 0:
            for le in self.ai_buckets:
                lines.append(f'{ai_prefix}_bucket{{le="{le}"}} {self.ai_inference_bucket_counts[le]}')
            lines.append(f'{ai_prefix}_bucket{{le="+Inf"}} {self.ai_inference_count}')
            lines.append(f'{ai_prefix}_count {self.ai_inference_count}')
            lines.append(f'{ai_prefix}_sum {self.ai_inference_sum:.9f}')
        else:
            for le in self.ai_buckets:
                lines.append(f'{ai_prefix}_bucket{{le="{le}"}} 0')
            lines.append(f'{ai_prefix}_bucket{{le="+Inf"}} 0')
            lines.append(f'{ai_prefix}_count 0')
            lines.append(f'{ai_prefix}_sum 0.0')
        lines.append("")

        # ── 缓存操作计数器（Counter） ──────────
        lines.append("# HELP ncard_cache_operations_total Cache hit/miss operations total")
        lines.append("# TYPE ncard_cache_operations_total counter")
        lines.append(f'ncard_cache_operations_total{{type="hit"}} {self.cache_hits}')
        lines.append(f'ncard_cache_operations_total{{type="miss"}} {self.cache_misses}')
        lines.append("")

        return "\n".join(lines) + "\n"


# ══════════════════════════════════════════════════════════════════════
# 便捷工具函数 / 装饰器
# ══════════════════════════════════════════════════════════════════════


@contextmanager
def track_db_query():
    """Context manager: 自动记录 DB 查询延迟到 metrics。

    用法:
        with track_db_query():
            await db.execute(...)
    """
    mi = _metrics_instance
    if mi is None:
        yield
        return
    start = time.monotonic()
    try:
        yield
    finally:
        dur = time.monotonic() - start
        mi.observe_db_query(dur)


@contextmanager
def track_ai_inference(model_name: str = "unknown"):
    """Context manager: 自动记录 AI 推理延迟到 metrics。

    用法:
        with track_ai_inference(model_name="deepseek"):
            result = await llm.call(...)
    """
    mi = _metrics_instance
    if mi is None:
        yield
        return
    start = time.monotonic()
    try:
        yield
    finally:
        dur = time.monotonic() - start
        mi.observe_ai_inference(dur)
        logger.debug("AI 推理完成 (model=%s, duration=%.3fs)", model_name, dur)


def record_cache_hit():
    """记录一次缓存命中。"""
    mi = _metrics_instance
    if mi is not None:
        mi.record_cache_hit()


def record_cache_miss():
    """记录一次缓存未命中。"""
    mi = _metrics_instance
    if mi is not None:
        mi.record_cache_miss()
