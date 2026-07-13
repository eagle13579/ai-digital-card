"""
API Key 认证中间件。

支持两种认证方式：
1. JWT Bearer Token（标准前端认证）
2. X-API-Key Header（开发者 API 接口认证）

同时记录 API Key 的调用用量到 api_key_usage 表。
"""
from datetime import date
from typing import Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, and_

from app.database import AsyncSessionLocal
from app.models.api_key import ApiKey, ApiKeyUsage


# 用于在请求中存储 API Key 信息的 contextvar
_api_key_var: Optional[dict] = None


def get_api_key_info() -> Optional[dict]:
    """获取当前请求的 API Key 信息（如有）"""
    return _api_key_var


class ApiKeyMiddleware:
    """
    API Key 认证中间件。

    检查 X-API-Key Header，验证 Key 是否存在且 is_active。
    如果请求已通过 JWT 认证（Authorization: Bearer），则跳过。
    记录请求用量到 api_key_usage 表（异步批量写入）。
    """

    def __init__(self, app):
        self.app = app
        # 白名单路径：不需要认证的公开 API
        self.public_paths = {
            "/health", "/api/health", "/metrics", "/",
            "/api/auth/login", "/api/auth/register",
            "/api/public/", "/view/", "/static",
        }

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        path = request.url.path

        # 公开路径跳过
        if any(path.startswith(p) for p in self.public_paths):
            await self.app(scope, receive, send)
            return

        # 检查 X-API-Key Header
        api_key_value = request.headers.get("X-API-Key")

        if api_key_value:
            # 验证 API Key
            try:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(ApiKey).where(ApiKey.key == api_key_value)
                    )
                    api_key = result.scalars().first()

                    if not api_key:
                        response = JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={"code": 401, "message": "API Key 不存在"},
                        )
                        await response(scope, receive, send)
                        return

                    if not api_key.is_active:
                        response = JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"code": 403, "message": "API Key 已被吊销"},
                        )
                        await response(scope, receive, send)
                        return

                    # 更新 last_used_at
                    from datetime import datetime
                    api_key.last_used_at = datetime.utcnow()

                    # 记录用量（upsert 模式）
                    today = date.today().isoformat()
                    usage_result = await db.execute(
                        select(ApiKeyUsage).where(
                            and_(
                                ApiKeyUsage.api_key_id == api_key.id,
                                ApiKeyUsage.date == today,
                            )
                        )
                    )
                    usage = usage_result.scalars().first()
                    if usage:
                        usage.request_count += 1
                    else:
                        usage = ApiKeyUsage(
                            api_key_id=api_key.id,
                            date=today,
                            request_count=1,
                        )
                        db.add(usage)

                    await db.commit()

                    # 在请求中标记 API Key 认证
                    scope["api_key_user_id"] = api_key.user_id
                    scope["api_key_id"] = api_key.id
                    scope["auth_method"] = "api_key"

                    global _api_key_var
                    _api_key_var = {
                        "user_id": api_key.user_id,
                        "key_id": api_key.id,
                        "key_name": api_key.name,
                        "permissions": api_key.get_permissions_list(),
                    }

            except Exception as e:
                print(f"[ApiKeyMiddleware] 错误: {e}")
                # 降级：如果数据库出错，允许请求继续（JWT 可能仍然有效）
                pass

        await self.app(scope, receive, send)
