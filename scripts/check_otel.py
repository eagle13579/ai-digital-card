#!/usr/bin/env python3
"""
OTel 连通性诊断工具 — OpenTelemetry Connection Diagnostic Tool

检测 AI 数智名片后端与 OpenTelemetry Collector 之间的连通性。

测试项:
  1. HTTP OTLP 端点 (localhost:4318) — 用于 traces + metrics
  2. gRPC OTLP 端点 (localhost:4317) — 可选，用于 traces
  3. Prometheus /metrics 端点 (localhost:8000) — 确认业务指标可达

用法:
    python scripts/check_otel.py
    python scripts/check_otel.py --timeout 5

返回码:
    0 = 全部可达
    1 = 部分可达
    2 = 全部不可达
"""

from __future__ import annotations

import argparse
import http.client
import logging
import socket
import sys
import urllib.error
import urllib.request

# ── 色彩输出 ──────────────────────────────────────────────────────────
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _ok(msg: str) -> str:
    return f"{_GREEN}{_BOLD}✓{_RESET} {msg}"


def _warn(msg: str) -> str:
    return f"{_YELLOW}{_BOLD}⚠{_RESET} {msg}"


def _fail(msg: str) -> str:
    return f"{_RED}{_BOLD}✗{_RESET} {msg}"


# ══════════════════════════════════════════════════════════════════════
# 网络检查工具
# ══════════════════════════════════════════════════════════════════════


def _tcp_check(host: str, port: int, timeout: int = 3) -> bool:
    """检查 TCP 端口是否可连接。"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.error):
        return False


def _http_get(url: str, timeout: int = 3) -> tuple[bool, int | None, str | None]:
    """发送 HTTP GET 请求，返回 (成功, 状态码, 错误消息)。"""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return True, resp.status, body[:500]
    except urllib.error.HTTPError as exc:
        # HTTPError 仍然说明连接成功（服务端返回了非 2xx）
        return True, exc.code, None
    except urllib.error.URLError as exc:
        return False, None, str(exc.reason)
    except (socket.timeout, OSError) as exc:
        return False, None, str(exc)


# ══════════════════════════════════════════════════════════════════════
# 单项检测
# ══════════════════════════════════════════════════════════════════════


def check_otlp_http(timeout: int = 3) -> dict:
    """检测 OTLP HTTP 端点 (localhost:4318)。

    Collector 的 OTLP HTTP 接收器默认监听 /v1/traces 和 /v1/metrics。
    我们检查 TCP 连通性，再尝试 GET /v1/traces（期望 405 或 200）。
    """
    host, port = "localhost", 4318
    result: dict = {
        "name": "OTLP HTTP (端口 4318)",
        "tcp_reachable": False,
        "http_reachable": False,
        "http_status": None,
        "detail": "",
    }

    # TCP 检查
    result["tcp_reachable"] = _tcp_check(host, port, timeout)
    if not result["tcp_reachable"]:
        result["detail"] = "TCP 连接失败 — Collector 可能未运行或端口未开放"
        return result

    # HTTP 检查 — Collector 对 /v1/traces 返回 405 Method Not Allowed 说明工作正常
    ok, status, err = _http_get(f"http://{host}:{port}/v1/traces", timeout)
    result["http_reachable"] = ok
    result["http_status"] = status

    if ok and status == 405:
        result["detail"] = "Collector 可达 (返回 405, 符合预期)"
    elif ok and status is not None and 200 <= status < 500:
        result["detail"] = f"Collector 可达 (HTTP {status})"
    elif ok:
        result["detail"] = f"Collector 可达 (HTTP {status})"
    else:
        result["detail"] = f"HTTP 请求失败: {err}"

    return result


def check_otlp_grpc(timeout: int = 3) -> dict:
    """检测 OTLP gRPC 端点 (localhost:4317)。

    gRPC 基于 HTTP/2，TCP 连通即基本可用。完整握手需要 gRPC 客户端库。
    """
    host, port = "localhost", 4317
    result: dict = {
        "name": "OTLP gRPC (端口 4317)",
        "tcp_reachable": False,
        "detail": "",
    }

    result["tcp_reachable"] = _tcp_check(host, port, timeout)
    if result["tcp_reachable"]:
        result["detail"] = "TCP 端口可达 (gRPC 握手需 grpcio 库进一步验证)"
    else:
        result["detail"] = "TCP 连接失败 — Collector 可能未启用 gRPC 接收器"

    return result


def check_prometheus_metrics(timeout: int = 3) -> dict:
    """检测 Prometheus /metrics 端点 (localhost:8000)。

    注意：FastAPI 默认在 8000 端口暴露 /metrics。
    """
    host, port = "localhost", 8000
    result: dict = {
        "name": "Prometheus /metrics (localhost:8000)",
        "reachable": False,
        "http_status": None,
        "has_metrics": False,
        "detail": "",
    }

    ok, status, body = _http_get(f"http://{host}:{port}/metrics", timeout)
    result["reachable"] = ok
    result["http_status"] = status

    if ok and body:
        result["has_metrics"] = body.strip() != ""
        if result["has_metrics"]:
            lines = [l for l in body.split("\n") if l and not l.startswith("#")]
            result["detail"] = f"可达, 返回 {len(lines)} 个指标行"
        else:
            result["detail"] = "可达, 但 /metrics 返回空内容"
    elif ok and status is not None:
        result["detail"] = f"可达 (HTTP {status})"
    else:
        result["detail"] = "不可达 — 后端应用可能未运行"

    return result


# ══════════════════════════════════════════════════════════════════════
# 诊断报告
# ══════════════════════════════════════════════════════════════════════


def print_result(item: dict) -> None:
    """打印单项检测结果。"""
    name = item["name"]

    if item.get("tcp_reachable") is False:
        print(f"  {_fail(name)}")
        print(f"       {item['detail']}")
        return

    if item.get("reachable") is False:
        print(f"  {_fail(name)}")
        print(f"       {item['detail']}")
        return

    if item.get("http_reachable") is False:
        print(f"  {_fail(name)}")
        print(f"       {item['detail']}")
        return

    # 全部通过
    print(f"  {_ok(name)}")
    print(f"       {item['detail']}")


def print_report(
    otlp_http: dict,
    otlp_grpc: dict,
    prom: dict,
) -> int:
    """格式化输出诊断报告，返回退出码。"""
    header = f"""{_BOLD}══════════════════════════════════════════════════════{_RESET}
{_BOLD}  AI 数智名片 — OTel 可观测性连通性诊断{_RESET}
{_BOLD}══════════════════════════════════════════════════════{_RESET}
"""
    print(header)

    print(f"{_BOLD}[1] OTLP 端点 - HTTP{_RESET} (localhost:4318/v1/traces)")
    print_result(otlp_http)
    print()

    print(f"{_BOLD}[2] OTLP 端点 - gRPC{_RESET} (localhost:4317)")
    print_result(otlp_grpc)
    print()

    print(f"{_BOLD}[3] Prometheus 指标端点{_RESET} (localhost:8000/metrics)")
    print_result(prom)
    print()

    # ── 综合评级 ─────────────────────────────────────────────────────
    http_ok = otlp_http["http_reachable"]
    grpc_ok = otlp_grpc["tcp_reachable"]
    prom_ok = prom["reachable"]

    print(f"{_BOLD}──── 综合诊断 ────{_RESET}")

    if http_ok and prom_ok:
        print(f"  {_ok('状态: 全部可达 — OTel 可观测性链路完整')}")
        print(f"      建议: Collector 已就绪，可启用 OTLP 导出")
        return 0

    if http_ok or grpc_ok or prom_ok:
        print(f"  {_warn('状态: 部分可达 — 可观测性链路不完整')}")
        if not http_ok:
            print(f"       → OTLP HTTP 不可达: traces/metrics 无法导出到 Collector")
        if not grpc_ok:
            print(f"       → OTLP gRPC 不可达: 备用传输不可用")
        if not prom_ok:
            print(f"       → Prometheus 端点不可达: 后端可能未运行")
        print(f"      建议: 检查 Collector 是否已启动 (docker compose)")
        return 1

    print(f"  {_fail('状态: 全部不可达 — 可观测性链路完全断开')}")
    print(f"      建议: 按照 deploy/otel/README.md 启动 Collector")
    return 2


# ══════════════════════════════════════════════════════════════════════
# CLI 入口
# ══════════════════════════════════════════════════════════════════════


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OTel 连通性诊断工具 — 检测与 OpenTelemetry Collector 的连接",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python scripts/check_otel.py\n"
            "  python scripts/check_otel.py --timeout 5\n"
            "  python scripts/check_otel.py --quiet\n"
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3,
        help="每个检测的超时时间 (秒)，默认 3",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="仅输出 JSON 格式结果，适合脚本解析",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    timeout = args.timeout

    # 执行检测
    otlp_http = check_otlp_http(timeout)
    otlp_grpc = check_otlp_grpc(timeout)
    prom = check_prometheus_metrics(timeout)

    if args.quiet:
        import json

        report = {
            "otlp_http": otlp_http,
            "otlp_grpc": otlp_grpc,
            "prometheus_metrics": prom,
        }
        all_ok = (
            otlp_http["http_reachable"]
            and prom["reachable"]
        )
        report["status"] = "all_reachable" if all_ok else "partial" if any(
            [otlp_http["http_reachable"], otlp_grpc["tcp_reachable"], prom["reachable"]]
        ) else "none_reachable"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if all_ok else 1 if any(
            [otlp_http["http_reachable"], otlp_grpc["tcp_reachable"], prom["reachable"]]
        ) else 2

    exit_code = print_report(otlp_http, otlp_grpc, prom)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
