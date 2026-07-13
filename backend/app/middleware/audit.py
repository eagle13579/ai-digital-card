"""
审计日志中间件 (Audit Log Middleware)

自动记录所有 API 请求到 audit_logs 表，支持异步数据库写入。
提供便捷函数供业务代码手动记录审计事件。

用法:
    # 注册中间件 (FastAPI)
    app.add_middleware(AuditMiddleware)

    # 在业务代码中手动记录审计事件
    from app.middleware.audit import record_audit
    await record_audit(db, user_id=1, action="EXPORT", resource="/api/gdpr/data", ...)
"""
import json
import logging
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.audit import AuditLog

logger = logging.getLogger("audit")

# ── ContextVar: 协程安全的审计上下文 ──────────────────────────
audit_user_id_var: ContextVar[int | None] = ContextVar("audit_user_id", default=None)
"""当前请求的 user_id（由中间件解析 JWT 后注入）"""


async def _get_user_id_from_token(scope: dict) -> int | None:
    """尝试从请求头 Authorization 中解析 JWT 获取 user_id。

    与 app.routers.auth 中 JWT 格式保持一致：payload.sub = str(user_id)
    """
    headers = dict(scope.get("headers", []))
    auth_header = headers.get(b"authorization", b"")
    if not auth_header:
        return None
    try:
        token_str = auth_header.decode("utf-8")
        if token_str.startswith("Bearer "):
            token_str = token_str[7:]
        # 轻量解析 JWT (不依赖 jose 库，只解析 payload 部分)
        import base64
        import json
        parts = token_str.split(".")
        if len(parts) != 3:
            return None
        # 补齐 base64 padding
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        decoded = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(decoded)
        sub = payload.get("sub")
        if sub:
            return int(sub)
    except Exception:
        pass
    return None


async def _get_client_ip(scope: dict) -> str:
    """从 ASGI scope 中提取客户端 IP。"""
    headers = dict(scope.get("headers", []))
    # 优先取 X-Forwarded-For (反向代理场景)
    xff = headers.get(b"x-forwarded-for", b"")
    if xff:
        ip = xff.decode("utf-8").split(",")[0].strip()
        if ip:
            return ip
    # 回退到 ASGI scope 中的 client 地址
    client = scope.get("client")
    if client:
        return client[0]
    return ""


async def _get_user_agent(scope: dict) -> str:
    """从请求头中提取 User-Agent。"""
    headers = dict(scope.get("headers", []))
    ua = headers.get(b"user-agent", b"")
    return ua.decode("utf-8", errors="replace")[:512] if ua else ""


def _classify_action(method: str) -> str:
    """根据 HTTP 方法归类操作类型。"""
    method_map = {
        "GET": "READ",
        "POST": "CREATE",
        "PUT": "UPDATE",
        "PATCH": "UPDATE",
        "DELETE": "DELETE",
    }
    return method_map.get(method.upper(), "OTHER")


def _should_skip(path: str) -> bool:
    """判断是否应跳过审计记录（健康检查、静态文件等）。"""
    skip_patterns = (
        "/health",
        "/api/health",
        "/metrics",
        "/static/",
        "/favicon",
    )
    for pattern in skip_patterns:
        if path.startswith(pattern):
            return True
    return False


# ── 手动记录审计事件 ────────────────────────────────────────────


async def record_audit(
    db: AsyncSession,
    user_id: int | None,
    action: str,
    resource: str,
    detail: str | dict | None = None,
    ip: str = "",
    user_agent: str = "",
) -> AuditLog:
    """手动记录一条审计日志。

    Args:
        db: 数据库会话
        user_id: 操作用户 ID（可为 None）
        action: 操作类型（如 CREATE, DELETE, EXPORT, DELETE_ACCOUNT）
        resource: 操作资源路径
        detail: 操作详情（dict 会转为 JSON 字符串）
        ip: 客户端 IP
        user_agent: 客户端 User-Agent

    Returns:
        创建的 AuditLog 实例
    """
    if isinstance(detail, dict):
        detail = json.dumps(detail, ensure_ascii=False, default=str)
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        detail=detail or "",
        ip=ip,
        user_agent=user_agent,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    logger.debug("Audit recorded: %s %s (user=%s)", action, resource, user_id)
    return log


# ── ASGI 中间件 ──────────────────────────────────────────────────


class AuditMiddleware:
    """ASGI 中间件：自动记录所有 API 请求到 audit_logs 表。

    使用方式 (FastAPI):
        from app.middleware.audit import AuditMiddleware
        app.add_middleware(AuditMiddleware)
    """

    __slots__ = ("app",)

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # 仅处理 HTTP 请求
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "GET")

        # 跳过健康检查等无关路径
        if _should_skip(path):
            await self.app(scope, receive, send)
            return

        # ── 1. 收集请求上下文 ────────────────────────────────
        #    在中间件执行前（request 进入阶段）获取信息
        #    注意：IP 和 user_agent 在请求阶段即可获取
        ip = await _get_client_ip(scope)
        user_agent = await _get_user_agent(scope)

        # ── 2. 注入 user_id 到 contextvar ────────────────────
        user_id = await _get_user_id_from_token(scope)
        token = audit_user_id_var.set(user_id)

        try:
            # ── 3. 放行请求，等待响应 ────────────────────────
            #    通过包装 send 捕获响应状态
            response_status = [None]

            async def send_with_capture(message):
                if message["type"] == "http.response.start":
                    response_status[0] = message.get("status", 0)
                await send(message)

            await self.app(scope, receive, send_with_capture)

            # ── 4. 响应后异步记录审计日志 ────────────────────
            #    仅记录业务端点和非 4xx/5xx 的跳过（由调用者决定）
            #    这里记录所有非静态请求
            status_code = response_status[0] or 0
            action = _classify_action(method)

            # 对于 GET 请求，只记录关键资源的读取，不记录每个静态资源
            # 但对于所有非 GET 操作和关键 GET 端点（如 /api/*），都记录
            is_api_path = path.startswith("/api/") or path.startswith("/api")

            if action != "READ" or is_api_path:
                detail_data = {
                    "method": method,
                    "status": status_code,
                    "path": path,
                }
                detail_json = json.dumps(detail_data, ensure_ascii=False)

                try:
                    async with AsyncSessionLocal() as audit_db:
                        log = AuditLog(
                            user_id=user_id,
                            action=action,
                            resource=path,
                            detail=detail_json,
                            ip=ip,
                            user_agent=user_agent,
                        )
                        audit_db.add(log)
                        await audit_db.commit()
                except Exception as e:
                    logger.warning("Failed to write audit log: %s", e)

        finally:
            audit_user_id_var.reset(token)
