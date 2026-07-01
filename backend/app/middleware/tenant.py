"""
TenantMiddleware — Multi-tenant 数据隔离中间件。

核心机制:
  1. 从 JWT payload 提取 tenant_id (也可从 X-Tenant-ID header 回退)
  2. 注入 tenant_id ContextVar
  3. TenantSession 自动为所有查询添加 WHERE tenant_id = ?
"""
from __future__ import annotations

import base64
import json
import logging
from contextvars import ContextVar
from typing import Any, Optional

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import TenantBase

logger = logging.getLogger("tenant")

# ── ContextVar (协程安全) ──────────────────────────────────────────────────
tenant_id_var: ContextVar[Optional[int]] = ContextVar("tenant_id", default=None)
"""当前请求的 tenant_id，由 TenantMiddleware 注入。"""
tenant_plan_var: ContextVar[Optional[str]] = ContextVar("tenant_plan", default=None)
"""当前请求的租户套餐等级。"""


# ── JWT 解析工具 ──────────────────────────────────────────────────────────

def _decode_jwt_payload(token: str) -> dict:
    """轻量解析 JWT payload (不依赖 jose 库)。"""
    parts = token.split(".")
    if len(parts) != 3:
        return {}
    payload_b64 = parts[1]
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    try:
        decoded = base64.urlsafe_b64decode(payload_b64)
        return json.loads(decoded)
    except Exception:
        return {}


# ── Tenant Session Wrapper ─────────────────────────────────────────────────

class TenantSession:
    """
    包装 AsyncSession，自动为所有查询添加 tenant_id 过滤。

    用法:
        tenant_db = TenantSession(db, tenant_id=42)
        result = await tenant_db.execute(select(Model).where(...))
        # 自动变成: select ... WHERE tenant_id = 42 AND ...
    """

    def __init__(self, session: AsyncSession, tenant_id: int):
        self._session = session
        self._tenant_id = tenant_id

    def _inject_tenant_filter(self, statement: Any) -> Any:
        """检查 statement 中的模型是否继承 TenantBase，自动加 tenant_id 过滤。"""
        if not isinstance(statement, Select):
            return statement

        # 从 column_descriptions 提取实体类
        entities = []
        for desc in statement.column_descriptions:
            ent = desc.get("entity")
            if ent is not None and isinstance(ent, type) and issubclass(ent, TenantBase):
                entities.append(ent)

        if not entities:
            return statement

        # 只对还没有 tenant_id 条件的查询加过滤
        from sqlalchemy.sql import visitors
        has_tenant_condition = False
        wc = statement.whereclause
        if wc is not None:
            for visitor in visitors.iterate(wc):
                col_name = getattr(visitor, "name", None)
                if col_name == "tenant_id":
                    has_tenant_condition = True
                    break

        if not has_tenant_condition:
            for entity in entities:
                statement = statement.where(entity.tenant_id == self._tenant_id)
        return statement

    async def execute(self, statement: Any, *args, **kwargs):
        statement = self._inject_tenant_filter(statement)
        return await self._session.execute(statement, *args, **kwargs)

    def add(self, instance: Any):
        """添加新记录时自动填充 tenant_id。"""
        if isinstance(instance, TenantBase):
            instance.tenant_id = self._tenant_id
        self._session.add(instance)

    async def commit(self):
        return await self._session.commit()

    async def flush(self):
        return await self._session.flush()

    async def refresh(self, instance: Any, *args, **kwargs):
        return await self._session.refresh(instance, *args, **kwargs)

    async def rollback(self):
        return await self._session.rollback()

    async def close(self):
        return await self._session.close()

    def __getattr__(self, name: str):
        return getattr(self._session, name)


# ── ASGI 中间件 ───────────────────────────────────────────────────────────

class TenantMiddleware:
    """
    ASGI 中间件：从 JWT Authorization header 提取 tenant_id，
    注入 contextvar，后续所有数据库操作自动隔离。

    使用方式:
        app.add_middleware(TenantMiddleware)  # 注册到 FastAPI
    """

    __slots__ = ("app",)

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        tenant_id = None
        tenant_plan = None

        # 1. 从 JWT 提取
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode("utf-8")
        if auth_header.startswith("Bearer "):
            payload = _decode_jwt_payload(auth_header[7:])
            tenant_id = payload.get("tenant_id")
            tenant_plan = payload.get("tenant_plan")

        # 2. 回退：从 X-Tenant-ID header 读取（测试/手动场景）
        if tenant_id is None:
            x_tid = headers.get(b"x-tenant-id", b"").decode("utf-8")
            if x_tid:
                try:
                    tenant_id = int(x_tid)
                except (ValueError, TypeError):
                    pass

        # 注入 contextvar
        tid_token = tenant_id_var.set(tenant_id)
        plan_token = tenant_plan_var.set(tenant_plan)

        try:
            await self.app(scope, receive, send)
        finally:
            tenant_id_var.reset(tid_token)
            tenant_plan_var.reset(plan_token)


# ── FastAPI 依赖项 ─────────────────────────────────────────────────────────

async def get_current_tenant_id() -> Optional[int]:
    """FastAPI 依赖：获取当前请求的 tenant_id。"""
    return tenant_id_var.get()


async def require_tenant() -> int:
    """FastAPI 依赖：确保当前请求有 tenant_id，否则拒绝。"""
    tid = tenant_id_var.get()
    if tid is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少租户标识：请求未关联任何租户",
        )
    return tid
