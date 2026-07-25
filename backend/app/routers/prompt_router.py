"""F12 Prompt分治模板库 — API 路由。

端点:
  GET    /api/f12/prompts              — 列出所有模板（支持类别/标签过滤）
  GET    /api/f12/prompts/{id}         — 获取单个模板详情
  GET    /api/f12/prompts/{id}/render  — 渲染模板（参数插值）
  POST   /api/f12/prompts              — 创建新模板 / 注册
  POST   /api/f12/prompts/{id}/promote — 版本提升
  DELETE /api/f12/prompts/{id}         — 删除模板
  GET    /api/f12/prompts/stats        — 模板统计信息
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.prompt import PromptCategory, PromptTemplate
from app.services.prompt_templates import (
    TemplateRegistry,
    TemplateRenderer,
    VersionManager,
    get_template_registry,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/f12/prompts", tags=["F12 Prompt分治模板库"])


# ── Schemas ─────────────────────────────────────────────────────────────


class PromptTemplateCreate(BaseModel):
    """创建模板请求体"""

    id: Optional[str] = Field(
        None, description="模板 ID（自动生成，格式: {category}/v{version}）"
    )
    name: str = Field(..., min_length=1, max_length=128, description="模板名称")
    category: str = Field(
        ...,
        description="模板类别",
        pattern="^(input_parser|info_extractor|analysis_reasoning|formatter|quality_control)$",
    )
    version: str = Field("v1", max_length=32, description="语义版本号")
    description: str = Field("", max_length=512, description="模板用途描述")
    system_prompt: str = Field(..., min_length=1, description="System prompt 内容")
    user_prompt_template: str = Field("", description="User prompt 内容（可选）")
    parameters_schema: Optional[dict] = Field(
        None, description="期望入参的 JSON Schema"
    )
    output_schema: Optional[dict] = Field(
        None, description="期望输出的 JSON Schema"
    )
    tags: list[str] = Field(default_factory=list, description="标签数组")


class PromptTemplateResponse(BaseModel):
    """模板响应体"""

    id: str
    name: str
    category: str
    version: str
    description: str
    system_prompt: str
    user_prompt_template: str
    parameters_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    tags: list[str] = []
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PromptRenderRequest(BaseModel):
    """渲染模板请求体"""

    params: dict[str, Any] = Field(..., description="模板插值参数")
    validate: bool = Field(True, description="是否校验入参")


class PromptRenderResponse(BaseModel):
    """渲染结果响应体"""

    template_id: str
    system: str
    user: str
    validation_errors: list[str] = []


class PromptStatsResponse(BaseModel):
    """模板统计响应体"""

    total: int
    by_category: dict[str, int]
    categories: list[str]


class PromptListResponse(BaseModel):
    """模板列表响应体"""

    templates: list[PromptTemplateResponse]
    total: int


# ── API 端点 ───────────────────────────────────────────────────────────


def _template_to_response(tmpl: dict) -> PromptTemplateResponse:
    """将模板字典转为 API 响应模型。"""
    return PromptTemplateResponse(
        id=tmpl["id"],
        name=tmpl["name"],
        category=tmpl["category"],
        version=tmpl.get("version", "v1"),
        description=tmpl.get("description", ""),
        system_prompt=tmpl.get("system_prompt", ""),
        user_prompt_template=tmpl.get("user_prompt_template", ""),
        parameters_schema=tmpl.get("parameters_schema"),
        output_schema=tmpl.get("output_schema"),
        tags=tmpl.get("tags", []),
        is_active=tmpl.get("is_active", True),
    )


@router.get("/stats", response_model=PromptStatsResponse)
async def get_stats(registry: TemplateRegistry = Depends(get_template_registry)):
    """获取模板库统计信息。"""
    categories = registry.get_categories()
    by_category = registry.count_by_category()
    total = sum(by_category.values())
    return PromptStatsResponse(
        total=total, by_category=by_category, categories=categories
    )


@router.get("", response_model=PromptListResponse)
async def list_prompts(
    category: Optional[str] = Query(None, description="按类别过滤"),
    tag: Optional[str] = Query(None, description="按标签过滤"),
    registry: TemplateRegistry = Depends(get_template_registry),
):
    """列出所有 F12 分治模板，支持类别和标签过滤。"""
    templates = registry.list(category=category, tag=tag)
    return PromptListResponse(
        templates=[_template_to_response(t) for t in templates],
        total=len(templates),
    )


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt(
    template_id: str,
    registry: TemplateRegistry = Depends(get_template_registry),
):
    """获取单个模板详情。"""
    tmpl = registry.get(template_id)
    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板不存在: {template_id}",
        )
    return _template_to_response(tmpl)


@router.post("/{template_id}/render", response_model=PromptRenderResponse)
async def render_prompt(
    template_id: str,
    req: PromptRenderRequest,
    registry: TemplateRegistry = Depends(get_template_registry),
):
    """渲染指定模板（变量插值）。"""
    tmpl = registry.get(template_id)
    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板不存在: {template_id}",
        )

    # 参数校验
    validation_errors: list[str] = []
    if req.validate:
        validation_errors = TemplateRenderer.validate_parameters(tmpl, req.params)

    # 渲染
    try:
        rendered = TemplateRenderer.render_full(tmpl, req.params)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"模板渲染失败: {exc}",
        )

    return PromptRenderResponse(
        template_id=template_id,
        system=rendered["system"],
        user=rendered["user"],
        validation_errors=validation_errors,
    )


@router.post(
    "",
    response_model=PromptTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_prompt(
    req: PromptTemplateCreate,
    db: AsyncSession = Depends(get_db),
    registry: TemplateRegistry = Depends(get_template_registry),
):
    """创建新的 F12 分治模板。

    如果未指定 id，自动生成为 {category}/v{version}。
    如果指定 id 且已存在，返回 409 冲突。
    """
    # 自动生成 ID
    template_id = req.id or f"{req.category}/v{req.version}"

    # 检查冲突
    if registry.exists(template_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"模板 ID 已存在: {template_id}",
        )

    # 校验类别
    if req.category not in [c.value for c in PromptCategory]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的模板类别: {req.category}。可选: {[c.value for c in PromptCategory]}",
        )

    # 写入数据库
    now = datetime.now(timezone.utc)
    db_record = PromptTemplate(
        id=template_id,
        name=req.name,
        category=PromptCategory(req.category),
        version=req.version,
        description=req.description,
        system_prompt=req.system_prompt,
        user_prompt_template=req.user_prompt_template,
        parameters_schema=req.parameters_schema,
        output_schema=req.output_schema,
        tags=req.tags,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(db_record)
    await db.commit()
    await db.refresh(db_record)

    # 同步到内存注册表
    registry.register(db_record.to_dict())

    logger.info("F12 模板已创建: %s (类别=%s)", template_id, req.category)
    return PromptTemplateResponse(**db_record.to_dict())


@router.post("/{template_id}/promote", response_model=PromptTemplateResponse)
async def promote_prompt_version(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    registry: TemplateRegistry = Depends(get_template_registry),
):
    """将指定模板提升为下一个版本（v1 → v2 或 v1.0 → v1.1）。"""
    tmpl = registry.get(template_id)
    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板不存在: {template_id}",
        )

    new_id = registry.promote_version(template_id)
    if not new_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="版本提升失败",
        )

    # 写入数据库
    new_tmpl = registry.get(new_id)
    now = datetime.now(timezone.utc)
    db_record = PromptTemplate(
        id=new_id,
        name=new_tmpl["name"],
        category=PromptCategory(new_tmpl["category"]),
        version=new_tmpl["version"],
        description=new_tmpl.get("description", ""),
        system_prompt=new_tmpl["system_prompt"],
        user_prompt_template=new_tmpl.get("user_prompt_template", ""),
        parameters_schema=new_tmpl.get("parameters_schema"),
        output_schema=new_tmpl.get("output_schema"),
        tags=new_tmpl.get("tags", []),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(db_record)
    await db.commit()
    await db.refresh(db_record)

    logger.info(
        "模板版本已提升: %s → %s", template_id, new_id
    )
    return PromptTemplateResponse(**db_record.to_dict())


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    registry: TemplateRegistry = Depends(get_template_registry),
):
    """删除 F12 分治模板（软删除：设置 is_active=False）。"""
    # 查找数据库记录
    result = await db.execute(
        select(PromptTemplate).where(PromptTemplate.id == template_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板不存在: {template_id}",
        )

    # 软删除
    record.is_active = False
    record.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # 同步内存注册表
    registry.delete(template_id)

    logger.info("F12 模板已删除: %s", template_id)
    return None
