"""API 治理层：标准错误响应、分页、异常处理器。"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


# ── 模型定义（仅用于文档 / type hints）─────────────────────────────

class StandardErrorResponse:
    """
    统一错误响应模型。

    Schema:
        { "error": { "code": "VALIDATION_ERROR",
                     "message": "输入参数校验失败",
                     "details": { ... },
                     "request_id": "abc-123" } }
    """


class StandardPageResponse:
    """
    统一分页响应模型。

    Schema:
        { "data": [...],
      "pagination": { "page": 1, "page_size": 20,
                      "total": 100, "total_pages": 5 } }
    """


# ── 构建函数 ────────────────────────────────────────────────────────


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
    request_id: str | None = None,
) -> JSONResponse:
    """构建标准错误 JSON 响应。

    Args:
        status_code: HTTP 状态码（400, 403, 404, 500 ...）。
        code:       机器可读的错误代码，如 ``"VALIDATION_ERROR"``。
        message:    人类可读的错误描述。
        details:    可选的详细错误信息（dict/list/str）。
        request_id: 请求追踪 ID；为 ``None`` 时自动生成。

    Returns:
        ``fastapi.responses.JSONResponse`` 实例。
    """
    rid = request_id or uuid.uuid4().hex[:12]
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": rid,
        }
    }
    return JSONResponse(status_code=status_code, content=body)


def paginated_response(
    data: list[Any],
    page: int,
    page_size: int,
    total: int,
) -> dict[str, Any]:
    """构建统一分页响应字典。

    Args:
        data:      当前页数据列表。
        page:      当前页码（从 1 开始）。
        page_size: 每页条目数。
        total:     总条目数。

    Returns:
        符合 ``StandardPageResponse`` schema 的字典。
    """
    # 护边界：page / page_size 至少为 1
    safe_page = max(page, 1)
    safe_page_size = max(page_size, 1)
    total_pages = (total + safe_page_size - 1) // safe_page_size if total > 0 else 0

    return {
        "data": data,
        "pagination": {
            "page": safe_page,
            "page_size": safe_page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }


# ── FastAPI 异常处理器 ──────────────────────────────────────────────


def _make_exception_handler(status_code: int, code: str):
    """生成一个从 request + exception 提取信息的异常处理器。"""

    def handler(request: Request, exc: Exception) -> JSONResponse:
        return error_response(
            status_code=status_code,
            code=code,
            message=str(exc) or code.replace("_", " ").title(),
            request_id=getattr(request.state, "request_id", None),
        )

    return handler


def register_error_handlers(app: "FastAPI") -> None:  # noqa: F821
    """为常见异常注册统一格式的处理器。

    注册的异常类型：
        - ValidationError  → 422
        - ValueError       → 400
        - PermissionError  → 403
        - FileNotFoundError → 404
        - HTTPException    → 按自带状态码
        - Exception        → 500 (兜底)
    """
    from fastapi import HTTPException
    from fastapi.exceptions import RequestValidationError

    app.add_exception_handler(
        RequestValidationError,
        _make_exception_handler(422, "VALIDATION_ERROR"),
    )
    app.add_exception_handler(ValueError, _make_exception_handler(400, "BAD_REQUEST"))
    app.add_exception_handler(
        PermissionError, _make_exception_handler(403, "FORBIDDEN")
    )
    app.add_exception_handler(
        FileNotFoundError, _make_exception_handler(404, "NOT_FOUND")
    )

    # HTTPException — 提取自带状态码与 detail
    async def http_exc_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return error_response(
            status_code=exc.status_code,
            code="HTTP_ERROR",
            message=str(exc.detail),
            request_id=getattr(request.state, "request_id", None),
        )

    app.add_exception_handler(HTTPException, http_exc_handler)

    # 兜底 500
    async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
        return error_response(
            status_code=500,
            code="INTERNAL_ERROR",
            message="服务器内部错误，请稍后重试。",
            request_id=getattr(request.state, "request_id", None),
        )

    app.add_exception_handler(Exception, generic_handler)
