"""Web 表单捕获 API 路由。

端点前缀: /api/crm/forms

认证端点（需要 JWT）:
  POST   /api/crm/forms              → 创建表单
  GET    /api/crm/forms              → 表单列表
  GET    /api/crm/forms/{id}/embed   → 获取嵌入代码
  DELETE /api/crm/forms/{id}         → 删除表单
  GET    /api/crm/forms/{id}/logs    → 提交日志

公开端点（无需认证）:
  POST   /api/crm/forms/{id}/submit  → 表单提交
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User

# 延迟导入避免循环依赖
from app.routers.auth import get_current_user

from app.services.form_capture import (
    CrmForm,
    FormCaptureService,
    form_rate_limiter,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crm/forms", tags=["CRM 表单捕获"])


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Schemas
# ═══════════════════════════════════════════════════════════════════════════════


class FormFieldSchema(BaseModel):
    """表单字段定义。"""
    name: str = Field(..., description="字段显示名称（如: 姓名、手机）")
    field: str = Field(..., description="字段标识名（如: name, phone, email, company, title）")
    type: str = Field("text", description="字段类型: text | tel | email | textarea | select")
    required: bool = False
    placeholder: str = ""
    label: str = ""
    options: list[str] = Field(default_factory=list, description="select 类型的选项列表")


class FormCreate(BaseModel):
    """创建表单请求体。"""
    name: str = Field(..., description="表单名称（内部标识）")
    title: str = Field("", description="表单标题（显示给访客）")
    description: str = Field("", description="表单描述")
    fields: list[FormFieldSchema] = Field(
        default_factory=lambda: [
            FormFieldSchema(name="姓名", field="name", type="text", required=True, placeholder="请输入姓名"),
            FormFieldSchema(name="手机", field="phone", type="tel", required=True, placeholder="请输入手机号"),
            FormFieldSchema(name="邮箱", field="email", type="email", required=False, placeholder="请输入邮箱"),
            FormFieldSchema(name="公司", field="company", type="text", required=False, placeholder="请输入公司名称"),
            FormFieldSchema(name="职位", field="title", type="text", required=False, placeholder="请输入职位"),
        ],
        description="字段定义列表",
    )
    submit_action: str = "create_contact"
    redirect_url: str = ""
    success_message: str = "感谢您的提交，我们会尽快与您联系！"
    enable_honeypot: bool = True
    enable_rate_limit: bool = True
    auto_tags: list[str] = Field(default_factory=list, description="自动添加到联系人的标签")
    embed_theme: str = "light"
    embed_primary_color: str = "#1890ff"


class FormUpdate(BaseModel):
    """更新表单请求体（全量更新）。"""
    name: str | None = None
    title: str | None = None
    description: str | None = None
    fields: list[FormFieldSchema] | None = None
    submit_action: str | None = None
    redirect_url: str | None = None
    success_message: str | None = None
    enable_honeypot: bool | None = None
    enable_rate_limit: bool | None = None
    auto_tags: list[str] | None = None
    is_active: bool | None = None
    embed_theme: str | None = None
    embed_primary_color: str | None = None


class FormResponse(BaseModel):
    """表单响应。"""
    id: int
    owner_id: int
    name: str
    title: str
    description: str
    fields: list[dict]
    submit_action: str
    redirect_url: str
    success_message: str
    enable_honeypot: bool
    enable_rate_limit: bool
    auto_tags: list[str]
    is_active: bool
    submission_count: int
    embed_theme: str
    embed_primary_color: str
    created_at: str | None
    updated_at: str | None

    class Config:
        from_attributes = True


class FormSubmitPayload(BaseModel):
    """表单提交数据（由嵌入的 JavaScript 发送）。"""
    pass  # 接受任意字段，由服务层验证

    class Config:
        extra = "allow"  # 允许额外字段（如 honeypot）


class FormSubmitResponse(BaseModel):
    """表单提交响应。"""
    success: bool
    contact_id: int | None = None
    contact_name: str | None = None
    redirect_url: str = ""
    success_message: str = ""
    detail: str | None = None


class EmbedCodeResponse(BaseModel):
    """嵌入代码响应。"""
    form_id: int
    embed_code: str
    html_snippet: str
    script_tag: str


class SubmissionLogItem(BaseModel):
    """提交日志条目。"""
    id: int
    form_id: int
    submitter_ip: str
    submitter_ua: str
    payload: dict
    contact_id: int | None
    honeypot_triggered: bool
    success: bool
    error_message: str
    created_at: str | None


class SubmissionLogResponse(BaseModel):
    """提交日志列表响应。"""
    items: list[SubmissionLogItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ═══════════════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════════════


def _get_form_svc(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FormCaptureService:
    return FormCaptureService(db, current_user.id)


# ═══════════════════════════════════════════════════════════════════════════════
# 表单管理端点（需要认证）
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("", response_model=FormResponse, status_code=201)
async def create_form(
    data: FormCreate,
    svc: FormCaptureService = Depends(_get_form_svc),
):
    """创建表单捕获。"""
    form = await svc.create_form(data.model_dump())
    return form


@router.get("", response_model=list[FormResponse])
async def list_forms(
    svc: FormCaptureService = Depends(_get_form_svc),
):
    """获取当前用户的表单列表。"""
    forms = await svc.list_forms()
    return forms


@router.get("/{form_id}", response_model=FormResponse)
async def get_form(
    form_id: int,
    svc: FormCaptureService = Depends(_get_form_svc),
):
    """获取表单详情。"""
    form = await svc.get_owned_form(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    return form


@router.get("/{form_id}/embed", response_model=EmbedCodeResponse)
async def get_embed_code(
    form_id: int,
    svc: FormCaptureService = Depends(_get_form_svc),
    request: Request = None,
):
    """获取表单嵌入代码。

    返回 HTML/JS 嵌入片段，可直接放入网站 HTML。
    """
    form = await svc.get_owned_form(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")

    # 确定 base_url
    base_url = str(request.base_url).rstrip("/") if request else ""

    embed_code = svc.generate_embed_code(form, base_url=base_url)

    return EmbedCodeResponse(
        form_id=form.id,
        embed_code=embed_code,
        html_snippet=embed_code,
        script_tag=embed_code,
    )


@router.put("/{form_id}", response_model=FormResponse)
async def update_form(
    form_id: int,
    data: FormUpdate,
    svc: FormCaptureService = Depends(_get_form_svc),
):
    """更新表单配置。"""
    form = await svc.get_owned_form(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")

    update_data = data.model_dump(exclude_none=True)
    if "fields" in update_data and update_data["fields"] is not None:
        update_data["fields"] = [f.model_dump() for f in update_data["fields"]]
    if "auto_tags" in update_data and update_data["auto_tags"] is not None:
        update_data["auto_tags"] = list(update_data["auto_tags"])

    # 直接更新模型
    updatable = {
        "name", "title", "description", "submit_action", "redirect_url",
        "success_message", "enable_honeypot", "enable_rate_limit",
        "is_active", "embed_theme", "embed_primary_color",
    }
    for key, value in update_data.items():
        if key in updatable and value is not None:
            setattr(form, key, value)
        elif key == "fields" and value is not None:
            form.fields = json.dumps(value, ensure_ascii=False)
        elif key == "auto_tags" and value is not None:
            form.auto_tags = json.dumps(value, ensure_ascii=False)

    await svc.db.commit()
    await svc.db.refresh(form)
    return form


@router.delete("/{form_id}", status_code=204)
async def delete_form(
    form_id: int,
    svc: FormCaptureService = Depends(_get_form_svc),
):
    """删除表单。"""
    ok = await svc.delete_form(form_id)
    if not ok:
        raise HTTPException(status_code=404, detail="表单不存在")


@router.get("/{form_id}/logs", response_model=SubmissionLogResponse)
async def get_submission_logs(
    form_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: FormCaptureService = Depends(_get_form_svc),
):
    """获取表单提交日志。"""
    logs, total = await svc.get_submission_logs(form_id, page=page, page_size=page_size)
    items = [log.to_dict() for log in logs]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 提交端点（公开，无需认证）
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/{form_id}/submit", response_model=FormSubmitResponse)
async def submit_form(
    form_id: int,
    payload: dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """【公开端点】表单提交。

    不需要 JWT 认证，供嵌入网站的 JavaScript 调用。
    反垃圾: Honeypot 检测 + IP 速率限制。
    """
    # 获取表单（不需要认证）
    svc = FormCaptureService(db)
    form = await svc.get_form(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    if not form.is_active:
        raise HTTPException(status_code=410, detail="表单已禁用")

    # ── 速率限制 ─────────────────────────────────────────────────────
    client_ip = request.client.host if request.client else "unknown"
    if form.enable_rate_limit:
        if not form_rate_limiter.is_allowed(client_ip):
            remaining = form_rate_limiter.get_remaining(client_ip)
            logger.warning("速率限制触发 form=%s ip=%s", form_id, client_ip)
            raise HTTPException(
                status_code=429,
                detail=f"提交过于频繁，请稍后重试（剩余配额: {remaining}次/小时）",
            )

    # ── 处理提交 ─────────────────────────────────────────────────────
    user_agent = request.headers.get("user-agent", "")
    result = await svc.submit_form(
        form_id=form_id,
        payload=payload,
        submitter_ip=client_ip,
        submitter_ua=user_agent,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "提交失败"))

    return FormSubmitResponse(
        success=True,
        contact_id=result.get("contact_id"),
        contact_name=result.get("contact_name"),
        redirect_url=result.get("redirect_url", ""),
        success_message=result.get("success_message", "提交成功"),
    )
