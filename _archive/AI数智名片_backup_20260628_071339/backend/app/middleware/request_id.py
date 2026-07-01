"""
请求ID追踪中间件 (Request ID Tracking Middleware)

功能:
  1. 每个请求自动分配 UUID 作为 X-Request-ID
  2. 如果客户端传了 X-Request-ID 则复用该值
  3. 将 request_id 注入到 logging 上下文 (通过 contextvars + logging.Filter)
  4. 响应头返回 X-Request-ID
  5. 纯 Python 标准库实现 (无第三方依赖)

用法:
  # 1. 注册中间件 (FastAPI)
  app.add_middleware(RequestIDMiddleware)

  # 2. 在日志格式中使用 %(request_id)s
  import logging
  logging.basicConfig(
      format="%(asctime)s [%(request_id)s] %(levelname)s %(name)s: %(message)s"
  )
  # 并添加 Filter
  for handler in logging.getLogger().handlers:
      handler.addFilter(RequestIDLogFilter())

  # 3. 在业务代码中获取当前请求 ID
  from app.middleware import request_id_var
  rid = request_id_var.get()
"""

import uuid
import logging
from contextvars import ContextVar

# ── ContextVar: 线程/协程安全的请求 ID 存储 ──────────────────────
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


# ── Logging Filter: 将 request_id 注入到每条日志记录的 extra ────
class RequestIDLogFilter(logging.Filter):
    """将当前请求的 request_id 注入到 LogRecord 的 request_id 属性中。

    在日志格式中通过 %(request_id)s 使用；若当前无请求上下文则显示 "-"。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True


# ── ASGI 中间件 ──────────────────────────────────────────────────
class RequestIDMiddleware:
    """ASGI 中间件：为每个 HTTP 请求分配/复用 X-Request-ID。

    使用方式 (FastAPI):
        from app.middleware import RequestIDMiddleware
        app.add_middleware(RequestIDMiddleware)

    使用方式 (Starlette / 原生 ASGI):
        from app.middleware import RequestIDMiddleware
        app = RequestIDMiddleware(app)
    """

    __slots__ = ("app",)

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # 仅处理 HTTP 请求
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # ── 1. 获取/生成 request_id ──────────────────────────────
        #    从请求头中读取客户端传入的 X-Request-ID，若无则生成新 UUID
        headers = dict(scope.get("headers", []))
        raw_request_id = headers.get(b"x-request-id", b"")

        if raw_request_id:
            request_id = raw_request_id.decode("utf-8", errors="replace")
        else:
            request_id = uuid.uuid4().hex

        # ── 2. 注入到 context ────────────────────────────────────
        token = request_id_var.set(request_id)

        # ── 3. 包装 send 以注入响应头 ────────────────────────────
        original_send = send

        async def send_with_request_id(message):
            """在发送响应头时注入 X-Request-ID"""
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                # 检查是否已存在 X-Request-ID (避免重复)
                has_request_id = any(
                    k.lower() == b"x-request-id" for k, _ in headers
                )
                if not has_request_id:
                    headers = list(headers)
                    headers.append((b"x-request-id", request_id.encode()))
                    message["headers"] = headers
            await original_send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            # ── 4. 清理 context ──────────────────────────────────
            request_id_var.reset(token)
