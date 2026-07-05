"""V1 Deprecated API 路由 — 返回 Sunset / Deprecation 响应头。

这些路由在中间件重写 /api/v1/ → /api/ 之前被匹配，
注册在 __init__.py 的 app.include_router 中，且入口路径不含 /api/v1 前缀，
中间件通过检查 scope["path"] 后直接修改路由，故需特殊处理：
  - v1 路由注册在 /api/v1/... 路径
  - 中间件中排除这些路径，不进行重写
"""

from fastapi import APIRouter

from app.api_standards import deprecated

router = APIRouter(prefix="/api/v1", tags=["弃用"])


@router.get("/users")
@deprecated(
    sunset="Sat, 01 Jan 2027 00:00:00 GMT",
    successor="/api/v1/users",
)
async def v1_list_users():
    """[弃用] 获取用户列表 — 请使用 /api/v1/users 替代。"""
    from fastapi.responses import JSONResponse

    return JSONResponse(
        content={
            "code": "DEPRECATED",
            "message": "此接口已弃用，请使用 /api/v1/users",
        },
        status_code=410,
    )


@router.get("/brochures")
@deprecated(
    sunset="Sat, 01 Jan 2027 00:00:00 GMT",
    successor="/api/v1/brochures",
)
async def v1_list_brochures():
    """[弃用] 获取画册列表 — 请使用 /api/v1/brochures 替代。"""
    from fastapi.responses import JSONResponse

    return JSONResponse(
        content={
            "code": "DEPRECATED",
            "message": "此接口已弃用，请使用 /api/v1/brochures",
        },
        status_code=410,
    )
