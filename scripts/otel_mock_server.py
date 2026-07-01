#!/usr/bin/env python3
"""
OTel Mock Collector Server
==========================
模拟 OpenTelemetry Collector 的 OTLP HTTP 端点。

当 Docker 不可用时代替真实 OTel Collector，接收后端通过 SDK
发送的 spans/metrics 并打印到日志。

启动:
    python scripts/otel_mock_server.py

验证:
    curl -v -X POST http://localhost:4318/v1/traces \\
        -H "Content-Type: application/x-protobuf" \\
        --data-binary @/dev/null
"""

from __future__ import annotations

import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

# ── 日志配置 ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("otel-mock")


class OTelMockHandler(BaseHTTPRequestHandler):
    """模拟 OTel Collector 的 HTTP 请求处理器"""

    # ── 路由表 ────────────────────────────────────────────────────────
    _ROUTES: dict[str, dict[str, str]] = {
        "/v1/traces": {"POST": "handle_traces"},
        "/v1/metrics": {"POST": "handle_metrics"},
        "/v1/logs": {"POST": "handle_logs"},
        "/health": {"GET": "handle_health"},
    }

    # ── 通用 ──────────────────────────────────────────────────────────

    def log_message(self, format: str, *args: Any) -> None:
        """覆写父类 stderr 输出，改用 logger"""
        logger.info("📨 %s - %s", self.client_address[0], format % args)

    def _send_json(
        self,
        status: int,
        data: dict[str, Any] | None = None,
        message: str = "",
    ) -> None:
        """发送 JSON 响应"""
        body = json.dumps({"status": status, "message": message, "data": data})
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body.encode())))
        self.end_headers()
        self.wfile.write(body.encode())

    def _read_body(self) -> bytes:
        """读取请求体"""
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length > 0 else b""

    def _route(self, method: str) -> None:
        """根据 method + path 路由请求"""
        path = self.path.rstrip("/")
        routes = self._ROUTES.get(path)
        if routes and method in routes:
            handler_name = routes[method]
            handler = getattr(self, handler_name, None)
            if handler:
                handler()
                return

        # 404
        self._send_json(404, message=f"Not Found: {method} {self.path}")

    # ── HTTP 方法入口 ─────────────────────────────────────────────────

    def do_GET(self) -> None:
        self._route("GET")

    def do_POST(self) -> None:
        self._route("POST")

    # ── 路由处理器 ─────────────────────────────────────────────────────

    def handle_health(self) -> None:
        """健康检查端点"""
        self._send_json(
            200,
            data={
                "service": "otel-mock-collector",
                "version": "0.1.0",
                "status": "running",
            },
            message="OK",
        )
        logger.info("✅ Health check OK")

    def handle_traces(self) -> None:
        """接收 OTLP Traces"""
        body = self._read_body()
        content_type = self.headers.get("Content-Type", "")

        logger.info("🔬 === OTLP Traces 接收到 ===")
        logger.info("   Content-Type: %s", content_type)
        logger.info("   数据大小: %d bytes", len(body))

        # 尝试解析（根据 Content-Type）
        if "json" in content_type:
            self._log_json_body(body, "traces")
        elif "protobuf" in content_type:
            logger.info("   Protobuf 数据 (hex): %s", body.hex()[:200])
        else:
            logger.info("   原始数据 (前200字节): %s", body[:200].hex())

        # 模拟成功响应
        self._send_json(
            200,
            data={"partialSuccess": {"rejectedSpans": 0}},
            message="traces received",
        )
        logger.info("🔬 === Traces 处理完成 ===")

    def handle_metrics(self) -> None:
        """接收 OTLP Metrics"""
        body = self._read_body()
        content_type = self.headers.get("Content-Type", "")

        logger.info("📊 === OTLP Metrics 接收到 ===")
        logger.info("   Content-Type: %s", content_type)
        logger.info("   数据大小: %d bytes", len(body))

        if "json" in content_type:
            self._log_json_body(body, "metrics")
        elif "protobuf" in content_type:
            logger.info("   Protobuf 数据 (hex): %s", body.hex()[:200])
        else:
            logger.info("   原始数据 (前200字节): %s", body[:200].hex())

        self._send_json(
            200,
            data={"partialSuccess": {"rejectedDataPoints": 0}},
            message="metrics received",
        )
        logger.info("📊 === Metrics 处理完成 ===")

    def handle_logs(self) -> None:
        """接收 OTLP Logs"""
        body = self._read_body()
        content_type = self.headers.get("Content-Type", "")

        logger.info("📝 === OTLP Logs 接收到 ===")
        logger.info("   Content-Type: %s", content_type)
        logger.info("   数据大小: %d bytes", len(body))

        if "json" in content_type:
            self._log_json_body(body, "logs")
        elif "protobuf" in content_type:
            logger.info("   Protobuf 数据 (hex): %s", body.hex()[:200])
        else:
            logger.info("   原始数据 (前200字节): %s", body[:200].hex())

        self._send_json(
            200,
            data={"partialSuccess": {"rejectedLogRecords": 0}},
            message="logs received",
        )
        logger.info("📝 === Logs 处理完成 ===")

    # ── 辅助方法 ──────────────────────────────────────────────────────

    def _log_json_body(self, body: bytes, label: str) -> None:
        """尝试解析并打印 JSON 格式的请求体"""
        try:
            data = json.loads(body.decode("utf-8"))
            logger.info("   JSON 内容 (前1000字符):")
            for line in json.dumps(data, indent=2, ensure_ascii=False).split(
                "\n"
            )[:30]:
                logger.info("     %s", line)
            if len(json.dumps(data)) > 1000:
                logger.info("     ... (内容已截断)")
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.info("   JSON 解析失败: %s", e)
            logger.info("   原始文本: %s", body[:300].decode("utf-8", errors="replace"))


def main() -> None:
    """启动 OTLP Mock Collector 服务器"""
    host = "0.0.0.0"
    port = 4318

    server = HTTPServer((host, port), OTelMockHandler)

    print(f"\n{'='*60}")
    print(f"  🚀 OTel Mock Collector Server")
    print(f"  📍 Listening on http://{host}:{port}")
    print(f"  📌 Endpoints:")
    print(f"     POST /v1/traces   - OTLP Traces")
    print(f"     POST /v1/metrics  - OTLP Metrics")
    print(f"     POST /v1/logs     - OTLP Logs")
    print(f"     GET  /health      - Health Check")
    print(f"{'='*60}\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Server shutting down...")
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()
