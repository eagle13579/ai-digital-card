"""
AI数字名片 — API 响应时间基准测试脚本
====================================
测试10个核心端点的响应时间，输出 P50 / P90 / P99 延迟统计。

用法:
    python benchmarks/api_benchmark.py                          # 默认 http://localhost:8201
    python benchmarks/api_benchmark.py --base-url http://localhost:8200  # 通过 nginx
    python benchmarks/api_benchmark.py --iterations 20          # 更多迭代
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from statistics import median
from typing import Any

import requests

# ── 配置 ──────────────────────────────────────────────────────────────────────
DEFAULT_BASE_URL = "http://localhost:8201"
DEFAULT_ITERATIONS = 10
DEFAULT_TIMEOUT = 5  # 快速超时，避免无服务时卡死
REPORT_DIR = Path(__file__).resolve().parent.parent / "docs" / "benchmarks"


class EndpointResult:
    """单个端点的基准测试结果。"""

    def __init__(self, name: str, latencies_ms: list[float], statuses: list[int]):
        self.name = name
        self.latencies_ms = sorted(latencies_ms)
        self.statuses = statuses
        self.count = len(latencies_ms)

    @property
    def p50_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return median(self.latencies_ms)

    @property
    def p90_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        idx = int(len(self.latencies_ms) * 0.90)
        return self.latencies_ms[min(idx, len(self.latencies_ms) - 1)]

    @property
    def p99_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        idx = int(len(self.latencies_ms) * 0.99)
        return self.latencies_ms[min(idx, len(self.latencies_ms) - 1)]

    @property
    def avg_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return sum(self.latencies_ms) / len(self.latencies_ms)

    @property
    def max_ms(self) -> float:
        return max(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def min_ms(self) -> float:
        return min(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def error_rate(self) -> float:
        if not self.statuses:
            return 0.0
        errors = sum(1 for s in self.statuses if s >= 400)
        return errors / len(self.statuses)

    def report_row(self) -> str:
        return (
            f"| {self.name:<30} | {self.p50_ms:>7.2f} | {self.p90_ms:>7.2f} | "
            f"{self.p99_ms:>7.2f} | {self.avg_ms:>7.2f} | {self.min_ms:>7.2f} | "
            f"{self.max_ms:>7.2f} | {self.error_rate:>6.0%} |"
        )

    def to_dict(self) -> dict:
        return {
            "endpoint": self.name,
            "p50_ms": round(self.p50_ms, 2),
            "p90_ms": round(self.p90_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
            "avg_ms": round(self.avg_ms, 2),
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "error_rate": round(self.error_rate, 4),
            "iterations": self.count,
        }


class APIBenchmark:
    """API 端点基准测试运行器。"""

    def __init__(
        self,
        base_url: str,
        iterations: int = DEFAULT_ITERATIONS,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.iterations = iterations
        self.timeout = timeout
        self.session = requests.Session()
        # 连接超时短（2s），请求超时 5s
        self._timeout_tuple = (2, timeout)
        self.results: list[EndpointResult] = []
        # 登录后获取的 token
        self._token: str | None = None

    def _headers(self, auth: bool = False) -> dict[str, str]:
        headers = {
            "User-Agent": "AI-BizCard-Benchmark/1.0",
            "Accept": "application/json",
        }
        if auth and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if not auth:
            # For GraphQL
            headers["Content-Type"] = "application/json"
        return headers

    def _measure(self, name: str, method: str, path: str, **kwargs) -> EndpointResult:
        """对单个端点执行多次请求并记录延迟。"""
        latencies: list[float] = []
        statuses: list[int] = []

        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", self._headers())

        for _ in range(self.iterations):
            try:
                t0 = time.perf_counter()
                resp = self.session.request(
                    method, url, headers=headers, timeout=self._timeout_tuple, **kwargs
                )
                elapsed = (time.perf_counter() - t0) * 1000  # ms
                latencies.append(elapsed)
                statuses.append(resp.status_code)
            except requests.RequestException as e:
                latencies.append(-1)
                statuses.append(599)

        return EndpointResult(name, latencies, statuses)

    def try_login(self) -> bool:
        """尝试登录获取 token（失败时静默继续）。"""
        try:
            resp = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"phone": "13800138000", "password": "test1234"},
                headers={"Content-Type": "application/json"},
                timeout=self._timeout_tuple,
            )
            if resp.status_code == 200:
                data = resp.json()
                self._token = data.get("access_token") or data.get("token") or ""
                return bool(self._token)
        except Exception:
            pass
        return False

    def run_all(self) -> list[EndpointResult]:
        """运行所有预定义的基准测试。"""
        results: list[EndpointResult] = []

        # 尝试登录
        authed = self.try_login()
        if authed:
            print(f"  ✓ 登录成功，已获取访问令牌")
        else:
            print("  ⚠ 登录失败（或端点不存在），将以无认证模式运行")

        # ── 无需认证的端点 ──
        print("\n  ── 运行健康检查（无需认证） ──")
        results.append(self._measure(
            "/health", "GET", "/health",
            headers=self._headers(),
        ))

        print("  ── 运行公开模板端点（无需认证） ──")
        results.append(self._measure(
            "/api/v1/templates", "GET", "/api/v1/templates",
            headers=self._headers(),
        ))

        # GraphQL 公开查询
        print("  ── 运行 GraphQL 查询（无需认证） ──")
        results.append(self._measure(
            "GraphQL: templates", "POST", "/graphql",
            json={"query": "{ templates { id title } }"},
            headers={**self._headers(), "Content-Type": "application/json"},
        ))

        # ── 需要认证的端点 ──
        if authed:
            auth_h = self._headers(auth=True)
            auth_h_post = {**auth_h, "Content-Type": "application/json"}

            print("  ── 运行认证端点 ──")

            results.append(self._measure(
                "GET /api/v1/users/me", "GET", "/api/v1/users/me",
                headers=auth_h,
            ))

            results.append(self._measure(
                "GET /api/v1/brochures", "GET", "/api/v1/brochures?limit=10",
                headers=auth_h,
            ))

            results.append(self._measure(
                "GraphQL: brochures", "POST", "/graphql",
                json={"query": "{ brochures(limit: 5) { id title status } }"},
                headers=auth_h_post,
            ))

            results.append(self._measure(
                "GET /api/v1/matches", "GET", "/api/v1/matches?limit=5",
                headers=auth_h,
            ))

            results.append(self._measure(
                "GET /api/v1/connections", "GET", "/api/v1/connections?limit=5",
                headers=auth_h,
            ))

            results.append(self._measure(
                "GET /api/v1/visitors", "GET", "/api/v1/visitors?limit=5",
                headers=auth_h,
            ))

            results.append(self._measure(
                "GET /api/v1/tags", "GET", "/api/v1/tags",
                headers=auth_h,
            ))
        else:
            # 无认证时的降级测试
            print("  ── 降级：测试额外公开端点 ──")
            results.append(self._measure(
                "GET /api/v1/public/brochures", "GET", "/api/v1/public/brochures?limit=5",
                headers=self._headers(),
            ))
            results.append(self._measure(
                "GET /api/v1/ping", "GET", "/api/v1/ping",
                headers=self._headers(),
            ))

        self.results = results
        return results

    def print_report(self) -> None:
        """打印 Markdown 格式的报告到 stdout。"""
        print(f"\n{'='*90}")
        print(f"  AI数字名片 — API 响应时间基准测试报告")
        print(f"  基准 URL: {self.base_url}")
        print(f"  每端点迭代: {self.iterations}")
        print(f"  时间戳: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*90}\n")

        header = (
            f"| {'Endpoint':<30} | {'P50(ms)':>7} | {'P90(ms)':>7} | "
            f"{'P99(ms)':>7} | {'Avg(ms)':>7} | {'Min(ms)':>7} | "
            f"{'Max(ms)':>7} | {'Err%':>6} |"
        )
        sep = "|" + "-"*32 + "|" + "-"*9 + "|" + "-"*9 + "|" + "-"*9 + "|" + \
              "-"*9 + "|" + "-"*9 + "|" + "-"*9 + "|" + "-"*8 + "|"

        print(header)
        print(sep)
        for r in self.results:
            print(r.report_row())
        print()

        # 摘要
        if self.results:
            p99s = [r.p99_ms for r in self.results if r.p99_ms > 0]
            if p99s:
                print(f"  📊 所有端点 P99 中位数: {median(p99s):.2f}ms")
                print(f"  📊 所有端点 P99 最大值: {max(p99s):.2f}ms")

    def save_json(self, path: str | Path | None = None) -> Path:
        """以 JSON 格式保存基准测试结果。"""
        if path is None:
            REPORT_DIR.mkdir(parents=True, exist_ok=True)
            path = REPORT_DIR / f"baseline_{time.strftime('%Y%m%d_%H%M%S')}.json"

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "meta": {
                "base_url": self.base_url,
                "iterations": self.iterations,
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "tool": "api_benchmark.py",
            },
            "results": [r.to_dict() for r in self.results],
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  💾 结果已保存: {path}")
        return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI数字名片 — API 响应时间基准测试",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"基准 URL (默认: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--iterations", "-n",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"每端点的请求次数 (默认: {DEFAULT_ITERATIONS})",
    )
    parser.add_argument(
        "--save",
        nargs="?",
        const=True,
        default=True,
        help="保存 JSON 结果到 docs/benchmarks/",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    print(f"\n  🚀 AI数字名片 — API 性能基准测试")
    print(f"  ├─ 目标: {args.base_url}")
    print(f"  ├─ 迭代: {args.iterations}")
    print(f"  └─ 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    bench = APIBenchmark(
        base_url=args.base_url,
        iterations=args.iterations,
    )
    bench.run_all()
    bench.print_report()

    if args.save:
        json_path = REPORT_DIR / f"baseline_{time.strftime('%Y%m%d_%H%M%S')}.json"
        bench.save_json(json_path)

    return 0 if all(r.error_rate == 0 for r in bench.results) else 1


if __name__ == "__main__":
    sys.exit(main())
