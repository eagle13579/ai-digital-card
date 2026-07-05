"""发票 API — 创建(从订单)、列表、详情、下载(HTML/PDF)"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.database import get_db
from app.models.invoice import Invoice
from app.models.payment import PaymentOrder
from app.services.invoice_service import InvoiceService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/invoices", tags=["发票"])


# ── Schemas ─────────────────────────────────────────────────────────

class InvoiceItemSchema(BaseModel):
    """发票项目"""
    description: str = Field(..., description="项目描述")
    quantity: int = Field(1, description="数量")
    unit_price: float = Field(0.0, description="单价")
    amount: float = Field(0.0, description="金额")


class InvoiceSchema(BaseModel):
    """发票响应"""
    id: int
    invoice_no: str
    user_id: int
    amount: float
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    status: str
    order_no: str = ""
    buyer_name: str = ""
    buyer_tax_id: str = ""
    seller_name: str = ""
    seller_tax_id: str = ""
    items: list[dict]
    notes: str = ""
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """发票列表响应"""
    items: list[InvoiceSchema]
    total: int
    offset: int
    limit: int


class CreateInvoiceFromOrderRequest(BaseModel):
    """从支付订单创建发票请求"""
    order_no: str = Field(..., description="支付订单号")
    tax_rate: float = Field(0.0, description="税率（%），如 3、6、13")
    buyer_name: str = Field("", description="购买方名称")
    buyer_tax_id: str = Field("", description="购买方税号")
    seller_name: str = Field("AI数智名片", description="销售方名称")
    seller_tax_id: str = Field("", description="销售方税号")
    notes: str = Field("", description="备注")


class CreateInvoiceDirectRequest(BaseModel):
    """直接创建发票请求"""
    amount: float = Field(..., gt=0, description="不含税金额")
    items: list[InvoiceItemSchema] = Field(..., min_length=1, description="发票项目")
    tax_rate: float = Field(0.0, description="税率（%）")
    order_no: str = Field("", description="关联订单号")
    buyer_name: str = Field("", description="购买方名称")
    buyer_tax_id: str = Field("", description="购买方税号")
    seller_name: str = Field("AI数智名片", description="销售方名称")
    seller_tax_id: str = Field("", description="销售方税号")
    notes: str = Field("", description="备注")


# ── Helpers ─────────────────────────────────────────────────────────

def _invoice_to_schema(invoice: Invoice) -> InvoiceSchema:
    return InvoiceSchema(
        id=invoice.id,
        invoice_no=invoice.invoice_no,
        user_id=invoice.user_id,
        amount=invoice.amount,
        tax_rate=invoice.tax_rate,
        tax_amount=invoice.tax_amount,
        total_amount=invoice.total_amount,
        status=invoice.status,
        order_no=invoice.order_no or "",
        buyer_name=invoice.buyer_name or "",
        buyer_tax_id=invoice.buyer_tax_id or "",
        seller_name=invoice.seller_name or "",
        seller_tax_id=invoice.seller_tax_id or "",
        items=invoice.items or [],
        notes=invoice.notes or "",
        created_at=invoice.created_at.isoformat() if hasattr(invoice.created_at, 'isoformat') else str(invoice.created_at),
        updated_at=invoice.updated_at.isoformat() if hasattr(invoice.updated_at, 'isoformat') else str(invoice.updated_at),
    )


# ── Endpoints ───────────────────────────────────────────────────────

@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    offset: int = Query(0, ge=0, description="偏移"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取当前用户的发票列表"""
    user_id = current_user.id
    invoices = await InvoiceService.list_invoices(db, user_id, offset=offset, limit=limit)
    total = await InvoiceService.count_invoices(db, user_id)
    return InvoiceListResponse(
        items=[_invoice_to_schema(inv) for inv in invoices],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{invoice_id}", response_model=InvoiceSchema)
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取发票详情"""
    invoice = await InvoiceService.get_invoice(db, invoice_id, current_user.id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="发票不存在")
    return _invoice_to_schema(invoice)


@router.post("/create", response_model=InvoiceSchema, status_code=status.HTTP_201_CREATED)
async def create_invoice_from_order(
    req: CreateInvoiceFromOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """从支付订单生成发票"""
    user_id = current_user.id

    # 查找支付订单
    result = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.order_no == req.order_no,
            PaymentOrder.user_id == user_id,
        )
    )
    payment_order = result.scalar_one_or_none()
    if not payment_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="支付订单不存在")

    # 检查是否已开过发票
    existing = await InvoiceService.get_invoice_by_order(db, req.order_no, user_id)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该订单已开具发票",)

    invoice = await InvoiceService.from_payment_order(
        db,
        payment_order,
        tax_rate=req.tax_rate,
        buyer_name=req.buyer_name,
        buyer_tax_id=req.buyer_tax_id,
        seller_name=req.seller_name,
        seller_tax_id=req.seller_tax_id,
        notes=req.notes,
    )
    return _invoice_to_schema(invoice)


@router.post("/create-direct", response_model=InvoiceSchema, status_code=status.HTTP_201_CREATED)
async def create_invoice_direct(
    req: CreateInvoiceDirectRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """直接创建发票（不依赖支付订单）"""
    invoice = await InvoiceService.create_invoice(
        db,
        user_id=current_user.id,
        amount=req.amount,
        items=[item.model_dump() for item in req.items],
        tax_rate=req.tax_rate,
        order_no=req.order_no,
        buyer_name=req.buyer_name,
        buyer_tax_id=req.buyer_tax_id,
        seller_name=req.seller_name,
        seller_tax_id=req.seller_tax_id,
        notes=req.notes,
    )
    return _invoice_to_schema(invoice)


@router.post("/{invoice_id}/download")
async def download_invoice_html(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """下载发票 (HTML 格式，可在浏览器中打印/另存为 PDF)"""
    invoice = await InvoiceService.get_invoice(db, invoice_id, current_user.id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="发票不存在")

    html = InvoiceService.render_invoice_html(invoice)
    return HTMLResponse(content=html, status_code=200)


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """下载发票 PDF（使用 reportlab 生成）"""
    invoice = await InvoiceService.get_invoice(db, invoice_id, current_user.id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="发票不存在")

    try:
        pdf_bytes = InvoiceService.generate_pdf(invoice)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF 生成失败: {str(exc)}",
        )

    filename = f"{invoice.invoice_no}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
