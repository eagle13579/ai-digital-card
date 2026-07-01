"""
SLO Tracker — AI数字名片服务水平目标追踪器

使用内存中滑动窗口(最近1小时)追踪:
  - availability: 成功率 >= 99.9% (允许 0.1% 错误)
  - latency: P99 < 1s

用法:
    from app.slo_tracker import slo_tracker
    slo_tracker.record_request(200, 50)
    print(slo_tracker.get_sli())
    print(slo_tracker.get_slo_status())
"""

import time
from collections import deque
from typing import Dict, Tuple


class SLOTracker:
    """基于滑动窗口的SLO追踪器。窗口默认为1小时。"""

    def __init__(self, window_seconds: int = 3600):
        self.window_seconds = window_seconds
        # 每一项: (timestamp, status_code, duration_ms)
        self.requests: deque = deque()

    def record_request(self, status_code: int, duration_ms: float) -> None:
        """记录一次请求。"""
        now = time.time()
        self.requests.append((now, status_code, duration_ms))
        self._evict_old(now)

    def _evict_old(self, now: float | None = None) -> None:
        """移除窗口外的过期数据。"""
        if now is None:
            now = time.time()
        cutoff = now - self.window_seconds
        while self.requests and self.requests[0][0] < cutoff:
            self.requests.popleft()

    def get_sli(self) -> Dict[str, float]:
        """返回当前SLI指标。

        Returns:
            {
                "availability": 0.9995,   # 成功率 (0~1)
                "latency_p50": 0.12,       # P50延迟(秒)
                "latency_p95": 0.45,       # P95延迟(秒)
                "latency_p99": 0.89,       # P99延迟(秒)
                "total_requests": 1234,    # 窗口内总请求数
                "error_count": 2           # 窗口内错误数
            }
        """
        now = time.time()
        self._evict_old(now)

        total = len(self.requests)
        if total == 0:
            return {
                "availability": 1.0,
                "latency_p50": 0.0,
                "latency_p95": 0.0,
                "latency_p99": 0.0,
                "total_requests": 0,
                "error_count": 0,
            }

        errors = sum(1 for _, sc, _ in self.requests if sc >= 500)
        availability = (total - errors) / total

        durations = sorted(d for _, _, d in self.requests)
        p50 = durations[int(total * 0.50)] / 1000.0
        p95 = durations[int(total * 0.95)] / 1000.0
        p99 = durations[int(total * 0.99)] / 1000.0

        return {
            "availability": availability,
            "latency_p50": round(p50, 4),
            "latency_p95": round(p95, 4),
            "latency_p99": round(p99, 4),
            "total_requests": total,
            "error_count": errors,
        }

    def get_slo_status(self) -> Dict[str, Tuple[bool, float, float]]:
        """返回SLO达标状态。

        SLO阈值:
          - availability >= 99.9%  (0.999)
          - latency P99 < 1s

        Returns:
            {
                "availability": (True, 0.9995, 0.999),   # (达标?, 当前值, 阈值)
                "latency_p99":   (True, 0.89, 1.0),
            }
        """
        sli = self.get_sli()

        avail_ok = sli["availability"] >= 0.999
        latency_ok = sli["latency_p99"] < 1.0

        return {
            "availability": (avail_ok, round(sli["availability"], 4), 0.999),
            "latency_p99": (latency_ok, round(sli["latency_p99"], 4), 1.0),
        }


# 全局单例
slo_tracker = SLOTracker()
