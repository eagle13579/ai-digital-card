"""
API 标准化工具 — PaginatedResponse、ErrorResponse、分页辅助函数等。

用法:
    from app.api_standards import (
        PaginatedResponse, ErrorResponse, ErrorCode,
        paginate, paginate_cursor, raise_http_error, deprecated,
    )

    # Offset/limit 分页
    @router.get("/api/v1/users", response_model=PaginatedResponse[UserResponse])
    async def list_users(page: int = 1, page_size: int = 20, db=Depends(get_db)):
        query = select(User).order_by(User.id)
        return await paginate(db, query, page, page_size, UserResponse)

    # Error with request_id
    raise_http_error(404, ErrorCode.NOT_FOUND, "用户不存在")

    # Deprecation
    @router.get("/api/v1/old-endpoint")
    @deprecated(sunset="2027-01-01", successor="/api/v2/brochures")
    async def old_endpoint():
        ...
"""

import base64
import json
import logging
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from fastapi import HTTPException, Response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ─── 泛型类型变量 ──────────────────────────────────────────────────────────────

T = TypeVar("T")


# ─── 错误码枚举 ────────────────────────────────────────────────────────────────

class ErrorCode(str, Enum):
    """统一错误码。格式: {CATEGORY}_{SPECIFIC}"""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DEPRECATED = "DEPRECATED"
    PAYMENT_REQUIRED = "PAYMENT_REQUIRED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"


# ─── 错误响应模型 ──────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    """错误详情（可选，用于字段级错误）"""

    field: Optional[str] = None
    reason: str


class ErrorResponse(BaseModel):
    """统一错误响应模型。

    所有 API 错误（4xx/5xx）均返回此格式：

    ```json
    {
      "code": "VALIDATION_ERROR",
      "message": "请求参数校验失败",
      "details": {"fields": [{"field": "email", "reason": "格式错误"}]},
      "request_id": "req_abc123"
    }
    ```
    """

    code: str = Field(..., description="错误码（全大写+下划线）")
    message: str = Field(..., description="人类可读的错误描述（英文）")
    details: Optional[dict[str, Any]] = Field(None, description="额外错误详情")
    request_id: Optional[str] = Field(None, description="请求唯一标识，用于追踪问题")


# ─── 分页响应模型 ──────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应模型（支持 offset/limit 和 cursor 两种模式）。

    使用方式:
        @router.get("/api/v1/users",
                    response_model=PaginatedResponse[UserResponse])
        async def list_users(page: int = 1, page_size: int = 20, ...):
            ...
            return PaginatedResponse[UserResponse](
                items=[UserResponse.model_validate(u) for u in users],
                total=total,
                page=page,
                page_size=page_size,
            )
    """

    items: list[T] = Field(default_factory=list, description="当前页的数据条目")
    total: int = Field(0, description="总记录数")
    page: int = Field(1, description="当前页码（从 1 开始，offset 模式）")
    page_size: int = Field(20, description="每页条数")
    has_more: bool = Field(False, description="是否还有更多数据")
    next_cursor: Optional[str] = Field(None, description="下一页游标（cursor 模式）")


# ─── 分页辅助函数 ──────────────────────────────────────────────────────────────

async def paginate(
    db: Any,
    query: Any,
    page: int = 1,
    page_size: int = 20,
    response_model: Optional[type[BaseModel]] = None,
    *,
    max_page_size: int = 100,
) -> PaginatedResponse:
    """Offset/Limit 分页辅助函数。

    自动执行 count + select 双查询，返回 PaginatedResponse。

    参数:
        db: AsyncSession 或 sync Session
        query: SQLAlchemy select 语句（已含 filter/where 条件，不含 offset/limit）
        page: 页码（从 1 开始），默认 1
        page_size: 每页条数，默认 20
        response_model: 可选，若传入则自动对 items 做 model_validate
        max_page_size: page_size 上限，默认 100

    返回:
        PaginatedResponse[response_model] 或 PaginatedResponse[dict]
    """
    page = max(1, page)
    page_size = max(1, min(page_size, max_page_size))

    from sqlalchemy import select as sa_select, func

    # 构建 count 查询
    count_query = sa_select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 构建分页查询
    offset = (page - 1) * page_size
    paginated_query = query.offset(offset).limit(page_size)
    result = await db.execute(paginated_query)
    rows = result.scalars().all()

    # 序列化
    if response_model is not None:
        items = [response_model.model_validate(row) for row in rows]
    else:
        items = list(rows)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total,
    )


def encode_cursor(value: Any) -> str:
    """将游标值编码为不透明 Base64 字符串。"""
    raw = json.dumps({"v": value}, ensure_ascii=False, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode()).rstrip(b"=").decode()


def decode_cursor(cursor: str) -> Any:
    """解码 Base64 游标值。"""
    try:
        # 补齐 padding
        padding = 4 - len(cursor) % 4
        if padding != 4:
            cursor += "=" * padding
        raw = base64.urlsafe_b64decode(cursor).decode()
        return json.loads(raw)["v"]
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        logger.warning("游标解码失败: %s", exc)
        raise ValueError("无效的游标参数") from exc


async def paginate_cursor(
    db: Any,
    query: Any,
    cursor: Optional[str] = None,
    page_size: int = 20,
    cursor_column: Any = None,
    response_model: Optional[type[BaseModel]] = None,
    *,
    max_page_size: int = 100,
) -> PaginatedResponse:
    """Cursor-based 分页辅助函数。

    参数:
        db: AsyncSession
        query: SQLAlchemy select 语句（已含 filter/where 条件）
        cursor: 不透明 Base64 游标（首次请求传 None）
        page_size: 每页条数，默认 20
        cursor_column: 用于排序/定位的 SQLAlchemy 列（如 User.id）
        response_model: 可选，自动对 items 做 model_validate
        max_page_size: page_size 上限，默认 100

    返回:
        PaginatedResponse
    """
    from sqlalchemy import select as sa_select, func

    page_size = max(1, min(page_size, max_page_size))

    # 解码游标
    cursor_value = None
    if cursor:
        cursor_value = decode_cursor(cursor)

    # 构建 count 查询
    count_query = sa_select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 应用游标筛选
    if cursor_value is not None and cursor_column is not None:
        query = query.where(cursor_column > cursor_value)

    # 执行分页查询（取 page_size + 1 以判断 has_more）
    paginated_query = query.order_by(cursor_column).limit(page_size + 1)
    result = await db.execute(paginated_query)
    rows = result.scalars().all()

    has_more = len(rows) > page_size
    if has_more:
        rows = rows[:page_size]

    # 生成下一页游标
    next_cursor = None
    if has_more and rows:
        last_value = getattr(rows[-1], cursor_column.name if hasattr(cursor_column, "name") else "id", None)
        if last_value is not None:
            next_cursor = encode_cursor(last_value)

    # 序列化
    if response_model is not None:
        items = [response_model.model_validate(row) for row in rows]
    else:
        items = list(rows)

    return PaginatedResponse(
        items=items,
        total=total,
        page=0,  # cursor 模式不适用页码
        page_size=page_size,
        has_more=has_more,
        next_cursor=next_cursor,
    )


# ─── 错误抛出辅助 ──────────────────────────────────────────────────────────────

def raise_http_error(
    status_code: int,
    code: str | ErrorCode,
    message: str,
    *,
    details: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, str]] = None,
) -> None:
    """抛出统一的 HTTP 错误异常。

    参数:
        status_code: HTTP 状态码
        code: 错误码（ErrorCode 枚举或字符串）
        message: 人类可读的错误描述
        details: 额外错误详情（可选）
        headers: 额外响应头（可选）
    """
    if isinstance(code, ErrorCode):
        code = code.value

    # 尝试自动获取 request_id
    request_id = None
    try:
        from app.middleware.request_id import request_id_var

        request_id = request_id_var.get()
    except (ImportError, AttributeError):
        pass

    error_body = ErrorResponse(
        code=code,
        message=message,
        details=details,
        request_id=request_id,
    )

    raise HTTPException(
        status_code=status_code,
        detail=error_body.model_dump(exclude_none=True),
        headers=headers,
    )


# ─── Deprecation 装饰器 ────────────────────────────────────────────────────────

from functools import wraps
from typing import Callable


def deprecated(
    sunset: str = "",
    successor: str = "",
    deprecation_date: Optional[str] = None,
) -> Callable:
    """接口废弃/弃用装饰器。

    自动注入 Sunset / Deprecation / Link 响应头。

    参数:
        sunset: RFC 1123 格式的废弃截止日期，如 "Sat, 01 Jan 2027 00:00:00 GMT"
        successor: 替代接口路径，如 "/api/v2/users"
        deprecation_date: 废弃宣告日期（可选），默认当前日期

    用法:
        @router.get("/api/v1/old-endpoint")
        @deprecated(sunset="Sat, 01 Jan 2027 00:00:00 GMT",
                     successor="/api/v2/brochures")
        async def old_endpoint():
            return {"message": "this is deprecated"}
    """
    if not sunset:
        sunset = "Sat, 01 Jan 2027 00:00:00 GMT"

    if not deprecation_date:
        deprecation_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)

            # 如果返回的是 Response 对象，直接加头
            if isinstance(response, Response):
                response.headers["Sunset"] = sunset
                response.headers["Deprecation"] = "true"
                if successor:
                    response.headers["Link"] = f'<{successor}>; rel="successor-version"'
                return response

            # 如果是 dict 或其他，返回带头的 Response
            from fastapi.responses import JSONResponse

            if isinstance(response, dict):
                content = response
            elif isinstance(response, BaseModel):
                content = response.model_dump()
            else:
                content = response

            resp = JSONResponse(content=content)
            resp.headers["Sunset"] = sunset
            resp.headers["Deprecation"] = "true"
            if successor:
                resp.headers["Link"] = f'<{successor}>; rel="successor-version"'
            return resp

        return wrapper

    return decorator


# ─── 请求 ID 注入中间件辅助 ─────────────────────────────────────────────────────

def make_error_response(
    status_code: int,
    code: str | ErrorCode,
    message: str,
    *,
    details: Optional[dict[str, Any]] = None,
) -> dict:
    """构建标准错误响应字典（用于中间件中直接返回）。"""
    if isinstance(code, ErrorCode):
        code = code.value
    request_id = None
    try:
        from app.middleware.request_id import request_id_var

        request_id = request_id_var.get()
    except (ImportError, AttributeError):
        pass
    body = ErrorResponse(code=code, message=message, details=details, request_id=request_id)
    return body.model_dump(exclude_none=True)
