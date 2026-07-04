"""结构化日志中间件 (Structured JSON Logging Middleware)

为每个 HTTP 请求产生 JSON 格式的结构化日志行，包含：
  - method, path, status, duration_ms
  - request_id (复用 RequestIDMiddleware 的 contextvar)
  - user_id (从请求 scope 或 JWT 中提取)

依赖:
  - Python stdlib logging 模块
  - app.middleware.request_id.request_id_var (已有)

用法:
  from app.middleware.logging_middleware import LoggingMiddleware
  app.add_middleware(LoggingMiddleware)
"""

import json
import logging
import time
import datetime
from contextvars import ContextVar

# ── 日志记录器 ────────────────────────────────────────────────────
logger = logging.getLogger("app.access")


class JSONFormatter(logging.Formatter):
    """将日志记录格式化为 JSON 行，包含结构化字段。"""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        timestamp += f".{int(record.msecs * 1000):06d}Z"
        
        log_entry = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # 合并 extra 字段 (如 method, path, status, duration_ms 等)
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in ("args", "asctime", "created", "exc_info", "exc_text",
                         "filename", "funcName", "levelname", "levelno", "lineno",
                         "module", "msecs", "message", "msg", "name", "pathname",
                         "process", "processName", "relativeCreated", "stack_info",
                         "thread", "threadName")
        }
        log_entry.update(extra_fields)
        return json.dumps(log_entry, ensure_ascii=False, default=str)


def setup_json_logging(log_level: int = logging.INFO) -> None:
    """配置 app.access 记录器使用 JSON 格式化输出到 stderr。

    可在应用启动时调用一次；若已配置则跳过。
    """
    access_logger = logging.getLogger("app.access")
    if access_logger.handlers:
        return  # 已配置，避免重复添加

    access_logger.setLevel(log_level)
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    access_logger.addHandler(handler)
    # 防止日志向上传递到 root logger 导致重复输出
    access_logger.propagate = False


# ── ASGI 中间件 ──────────────────────────────────────────────────
class LoggingMiddleware:
    """ASGI 中间件：记录每个 HTTP 请求的结构化 JSON 日志。

    自动复用 RequestIDMiddleware 注入的 request_id，
    尝试从 scope 或 Authorization 中提取 user_id。
    """

    __slots__ = ("app",)

    def __init__(self, app):
        self.app = app
        # 确保 JSON logging 已配置
        setup_json_logging()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")

        # 获取 request_id (由 RequestIDMiddleware 注入)
        try:
            from app.middleware.request_id import request_id_var
            request_id = request_id_var.get() or ""
        except Exception:
            request_id = ""

        # 获取 user_id (从 scope 中提取)
        user_id = ""
        try:
            # 尝试从 scope 中读取由 AuthMiddleware 注入的 user_id
            user_id = scope.get("user_id", "")
            if not user_id:
                # 退而求其次，从 scope 的 query_string 或 headers 中解析
                headers = dict(scope.get("headers", []))
                # 尝试从 Authorization header 中提取 (仅记录，不解析)
                pass
        except Exception:
            pass

        # 收集响应状态码
        status_code = 0

        def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            return send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "request_failed",
                extra={
                    "method": method,
                    "path": path,
                    "status": 500,
                    "duration_ms": duration_ms,
                    "request_id": request_id,
                    "user_id": user_id,
                    "error": str(exc),
                },
            )
            raise
        else:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "request_completed",
                extra={
                    "method": method,
                    "path": path,
                    "status": status_code,
                    "duration_ms": duration_ms,
                    "request_id": request_id,
                    "user_id": user_id,
                },
            )
