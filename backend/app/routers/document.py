"""CRM 文档生成 API — 模板列表/生成/下载/历史。

端点:
  GET    /api/crm/documents/templates     — 模板列表
  POST   /api/crm/documents/generate       — 生成文档
  GET    /api/crm/documents/{id}/download   — 下载 PDF
  GET    /api/crm/documents                — 文档历史
  GET    /api/crm/documents/{id}           — 文档详情
  PUT    /api/crm/documents/{id}/status    — 更新状态
  DELETE /api/crm/documents/{id}           — 删除文档
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.database import get_db
from app.models.document import Document
from app.crm.crm_models import CrmContact, CrmDeal
from app.routers.auth import get_current_user
from app.services.document_gen import DocumentGenService

router = APIRouter(prefix="/api/v1/crm/documents", tags=["CRM 文档"])


# ── Schemas ─────────────────────────────────────────────────────────────


class TemplateSchema(BaseModel):
    """模板响应"""
    key: str
    name: str
    description: str
    doc_type: str
    default_title: str
    variables: list[dict[str, str]]


class DocumentSchema(BaseModel):
    """文档响应"""
    id: int
    owner_id: int
    contact_id: int | None = None
    deal_id: int | None = None
    doc_type: str
    template_name: str = ""
    title: str = ""
    doc_number: str = ""
    total_amount: float = 0.0
    currency: str = "CNY"
    status: str = "draft"
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    items: list[DocumentSchema]
    total: int
    offset: int
    limit: int


class GenerateRequest(BaseModel):
    """生成文档请求"""
    template_key: str = Field(..., description="模板 key")
    contact_id: int | None = Field(None, description="CRM 联系人 ID")
    deal_id: int | None = Field(None, description="CRM 机会 ID")
    title: str = Field("", description="自定义标题（留空使用模板默认）")
    items: list[dict] = Field(default_factory=list, description="报价明细 [{description, quantity, unit_price, amount}]")
    extra: dict = Field(default_factory=dict, description="额外变量覆盖")


class GenerateResponse(BaseModel):
    """生成文档响应"""
    document: DocumentSchema
    html_preview: str = ""


class StatusUpdateRequest(BaseModel):
    """状态更新请求"""
    status: str = Field(..., description="draft | final | sent | signed")


# ── Helpers ─────────────────────────────────────────────────────────────


def _doc_to_schema(doc: Document) -> DocumentSchema:
    return DocumentSchema(
        id=doc.id,
        owner_id=doc.owner_id,
        contact_id=doc.contact_id,
        deal_id=doc.deal_id,
        doc_type=doc.doc_type,
        template_name=doc.template_name or "",
        title=doc.title or "",
        doc_number=doc.doc_number or "",
        total_amount=doc.total_amount or 0.0,
        currency=doc.currency or "CNY",
        status=doc.status or "draft",
        created_at=doc.created_at.isoformat() if hasattr(doc.created_at, "isoformat") else str(doc.created_at),
        updated_at=doc.updated_at.isoformat() if hasattr(doc.updated_at, "isoformat") else str(doc.updated_at),
    )


# ── Endpoints ───────────────────────────────────────────────────────────


@router.get("/templates", response_model=list[TemplateSchema])
async def list_templates(
    doc_type: str = Query(None, description="按类型过滤: quotation | contract | proposal"),
):
    """获取预设模板列表"""
    return DocumentGenService.list_templates(doc_type)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    doc_type: str = Query(None, description="按类型过滤"),
    offset: int = Query(0, ge=0, description="偏移"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取当前用户的文档历史"""
    user_id = current_user.id
    docs = await DocumentGenService.list_documents(
        db, user_id, doc_type=doc_type, offset=offset, limit=limit
    )
    total = await DocumentGenService.count_documents(db, user_id, doc_type=doc_type)
    return DocumentListResponse(
        items=[_doc_to_schema(d) for d in docs],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{doc_id}", response_model=DocumentSchema)
async def get_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取文档详情"""
    doc = await DocumentGenService.get_document(db, doc_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    return _doc_to_schema(doc)


@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_document(
    req: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """生成文档（报价单/合同/提案）"""
    # 检查模板是否存在
    tmpl = DocumentGenService.get_template(req.template_key)
    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板不存在: {req.template_key}",
        )

    # 查询联系人/机会数据（如果提供）
    contact_data = None
    deal_data = None

    if req.contact_id:
        result = await db.execute(
            select(CrmContact).where(
                CrmContact.id == req.contact_id,
                CrmContact.owner_id == current_user.id,
            )
        )
        contact = result.scalar_one_or_none()
        if contact:
            contact_data = {
                "name": contact.name,
                "company": contact.company,
                "phone": contact.phone,
                "email": contact.email,
                "title": contact.title,
            }

    if req.deal_id:
        result = await db.execute(
            select(CrmDeal).where(
                CrmDeal.id == req.deal_id,
                CrmDeal.owner_id == current_user.id,
            )
        )
        deal = result.scalar_one_or_none()
        if deal:
            deal_data = {
                "title": deal.title,
                "value": float(deal.value),
                "currency": deal.currency,
                "probability": deal.probability,
            }

    # 用户数据
    user_data = {"name": getattr(current_user, "name", "") or getattr(current_user, "username", "")}

    # 构建 HTML
    title = req.title or tmpl.default_title
    html_content = DocumentGenService.build_html(
        req.template_key,
        contact=contact_data,
        deal=deal_data,
        user=user_data,
        extra=req.extra,
        doc_title=title,
        items=req.items or None,
    )

    # 计算金额
    total_amount = 0.0
    if req.items:
        total_amount = sum(
            item.get("amount", item.get("quantity", 1) * item.get("unit_price", 0))
            for item in req.items
        )
    elif deal_data:
        total_amount = float(deal_data.get("value", 0))

    # 构建变量数据快照
    content_data = {
        "contact": contact_data,
        "deal": deal_data,
        "extra": req.extra,
        "item_count": len(req.items) if req.items else 0,
    }

    # 创建数据库记录
    doc = await DocumentGenService.create_document(
        db,
        owner_id=current_user.id,
        doc_type=tmpl.doc_type,
        template_name=req.template_key,
        contact_id=req.contact_id,
        deal_id=req.deal_id,
        title=title,
        content_html=html_content,
        content_data=content_data,
        total_amount=total_amount,
        currency=deal_data.get("currency", "CNY") if deal_data else "CNY",
    )

    return GenerateResponse(
        document=_doc_to_schema(doc),
        html_preview=html_content[:2000] + ("..." if len(html_content) > 2000 else ""),
    )


@router.get("/{doc_id}/download")
async def download_document_pdf(
    doc_id: int,
    fmt: str = Query("pdf", description="输出格式: pdf | html"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """下载文档（PDF 或 HTML）"""
    doc = await DocumentGenService.get_document(db, doc_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")

    if fmt == "html":
        return HTMLResponse(
            content=doc.content_html,
            status_code=200,
        )

    # PDF
    try:
        pdf_bytes = DocumentGenService.generate_pdf(doc.content_html, title=doc.title)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF 生成失败: {str(exc)}",
        )

    filename = f"{doc.doc_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.put("/{doc_id}/status", response_model=DocumentSchema)
async def update_document_status(
    doc_id: int,
    req: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新文档状态"""
    valid_statuses = {"draft", "final", "sent", "signed"}
    if req.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效状态: {req.status}，可选: {', '.join(valid_statuses)}",
        )
    doc = await DocumentGenService.update_status(db, doc_id, req.status, current_user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    return _doc_to_schema(doc)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除文档"""
    deleted = await DocumentGenService.delete_document(db, doc_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
