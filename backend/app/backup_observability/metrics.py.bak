"""
APM / Prometheus 监控中间件 — 纯 Python 实现，不依赖 prometheus_client。

指标：
  - ncard_http_requests_total         计数器（按 status="2xx|4xx|5xx" 分片）
  - ncard_http_request_duration_seconds 直方图（10 个 bucket）
  - ncard_http_active_requests        仪表盘（当前并发请求数）
"""

import time

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

        return "\n".join(lines) + "\n"
