"""轻量性能基准测试(替代k6)——AI数字名片健康端点压测"""
import requests
import time
import statistics

BASE = "http://localhost:8002"

endpoints = [
    ("健康检查", "/health"),
    ("API健康", "/api/health"),
]

for name, path in endpoints:
    times = []
    successes = 0
    for _ in range(20):
        start = time.time()
        try:
            r = requests.get(f"{BASE}{path}", timeout=10)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            if r.status_code == 200:
                successes += 1
        except requests.RequestException as e:
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            print(f"  ⚠ 请求失败: {e}")

    p50 = statistics.median(times)
    sorted_times = sorted(times)
    p95 = sorted_times[18]  # 0-based index for 95th percentile of 20 samples
    print(f"{name}: P50={p50:.1f}ms P95={p95:.1f}ms 成功率={successes}/20")
