"""发票服务层 — 发票 CRUD、编号生成、PDF 生成（reportlab）"""

from __future__ import annotations

import io
import os
import random
from datetime import datetime
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice
from app.models.payment import PaymentOrder


class InvoiceService:
    """发票服务"""

    INVOICE_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "invoices"
    )

    # ── 编号生成 ─────────────────────────────────────────────────

    @staticmethod
    def generate_invoice_no() -> str:
        """生成发票编号: INV-YYYYMMDD-XXXX"""
        today = datetime.now().strftime("%Y%m%d")
        seq = random.randint(1000, 9999)
        return f"INV-{today}-{seq}"

    # ── 从支付订单转换 ───────────────────────────────────────────

    @staticmethod
    async def from_payment_order(
        db: AsyncSession,
        payment_order: PaymentOrder,
        *,
        tax_rate: float = 0.0,
        buyer_name: str = "",
        buyer_tax_id: str = "",
        seller_name: str = "AI数智名片",
        seller_tax_id: str = "",
        notes: str = "",
    ) -> Invoice:
        """从 PaymentOrder 生成 Invoice（自动计算税额与含税金额）"""
        # PaymentOrder.total_cents 以「分」为单位 → 转换为元
        amount = payment_order.total_cents / 100.0
        tax_amount = round(amount * tax_rate / 100.0, 2)
        total_amount = round(amount + tax_amount, 2)

        # 根据支付状态映射发票状态
        status_map = {
            "paid": "paid",
            "success": "paid",
            "completed": "paid",
            "pending": "unpaid",
            "unpaid": "unpaid",
            "cancelled": "cancelled",
            "refunded": "cancelled",
        }
        invoice_status = status_map.get(payment_order.status, "unpaid")

        # 构建发票项目
        items = [
            {
                "description": f"AI数字名片 — {payment_order.membership_tier} 会员",
                "quantity": 1,
                "unit_price": amount,
                "amount": amount,
            }
        ]

        invoice = Invoice(
            invoice_no=InvoiceService.generate_invoice_no(),
            user_id=payment_order.user_id,
            amount=amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            status=invoice_status,
            order_no=payment_order.order_no,
            buyer_name=buyer_name,
            buyer_tax_id=buyer_tax_id,
            seller_name=seller_name,
            seller_tax_id=seller_tax_id,
            items=items,
            notes=notes,
        )
        db.add(invoice)
        await db.flush()
        await db.refresh(invoice)
        return invoice

    # ── CRUD ─────────────────────────────────────────────────────

    @staticmethod
    async def create_invoice(
        db: AsyncSession,
        user_id: int,
        amount: float,
        items: list[dict[str, Any]],
        *,
        tax_rate: float = 0.0,
        status: str = "unpaid",
        order_no: str = "",
        buyer_name: str = "",
        buyer_tax_id: str = "",
        seller_name: str = "AI数智名片",
        seller_tax_id: str = "",
        notes: str = "",
    ) -> Invoice:
        """创建发票"""
        tax_amount = round(amount * tax_rate / 100.0, 2)
        total_amount = round(amount + tax_amount, 2)
        invoice = Invoice(
            invoice_no=InvoiceService.generate_invoice_no(),
            user_id=user_id,
            amount=amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            status=status,
            order_no=order_no,
            buyer_name=buyer_name,
            buyer_tax_id=buyer_tax_id,
            seller_name=seller_name,
            seller_tax_id=seller_tax_id,
            items=items,
            notes=notes,
        )
        db.add(invoice)
        await db.flush()
        await db.refresh(invoice)
        return invoice

    @staticmethod
    async def get_invoice(db: AsyncSession, invoice_id: int, user_id: int) -> Invoice | None:
        """按 ID 获取发票（仅当前用户）"""
        result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_invoice_by_order(db: AsyncSession, order_no: str, user_id: int) -> Invoice | None:
        """按订单号获取发票"""
        result = await db.execute(
            select(Invoice).where(Invoice.order_no == order_no, Invoice.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_invoices(
        db: AsyncSession, user_id: int, offset: int = 0, limit: int = 20
    ) -> list[Invoice]:
        """获取用户发票列表"""
        result = await db.execute(
            select(Invoice)
            .where(Invoice.user_id == user_id)
            .order_by(Invoice.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def count_invoices(db: AsyncSession, user_id: int) -> int:
        """统计用户发票总数"""
        result = await db.execute(
            select(func.count(Invoice.id)).where(Invoice.user_id == user_id)
        )
        return result.scalar() or 0

    @staticmethod
    async def update_status(db: AsyncSession, invoice_id: int, status: str) -> Invoice | None:
        """更新发票状态"""
        result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
        invoice = result.scalar_one_or_none()
        if invoice:
            invoice.status = status
            await db.flush()
            await db.refresh(invoice)
        return invoice

    # ── HTML 发票生成 ────────────────────────────────────────────

    @staticmethod
    def render_invoice_html(invoice: Invoice) -> str:
        """生成格式化的 HTML 发票内容（可打印 / 可另存为 PDF）"""
        status_label = {"paid": "已支付", "unpaid": "未支付", "cancelled": "已取消"}.get(
            invoice.status, invoice.status
        )
        status_color = {"paid": "#22c55e", "unpaid": "#f59e0b", "cancelled": "#ef4444"}.get(
            invoice.status, "#6b7280"
        )

        items_rows = ""
        for idx, item in enumerate(invoice.items or [], 1):
            desc = item.get("description", "")
            qty = item.get("quantity", 1)
            unit_price = item.get("unit_price", 0)
            amt = item.get("amount", qty * unit_price)
            items_rows += f"""
            <tr>
                <td>{idx}</td>
                <td>{desc}</td>
                <td style="text-align:center">{qty}</td>
                <td style="text-align:right">¥{unit_price:.2f}</td>
                <td style="text-align:right">¥{amt:.2f}</td>
            </tr>"""

        # 含税信息行
        tax_rows = ""
        if invoice.tax_rate > 0:
            tax_rows = f"""
            <tr>
                <td colspan="3" style="text-align:right;padding:6px 12px;font-size:13px;color:#6b7280">税率: {invoice.tax_rate:.1f}%</td>
                <td style="text-align:right;padding:6px 12px;font-size:13px;color:#6b7280">税额: ¥{invoice.tax_amount:.2f}</td>
                <td style="text-align:right;padding:6px 12px;font-weight:600;font-size:16px">¥{invoice.total_amount:.2f}</td>
            </tr>"""

        created_at_str = (
            invoice.created_at.strftime("%Y-%m-%d %H:%M")
            if isinstance(invoice.created_at, datetime)
            else str(invoice.created_at)
        )

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>发票 - {invoice.invoice_no}</title>
<style>
    @page {{ margin: 20mm; }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
        color: #1f2937; background: #f3f4f6; padding: 40px 20px;
    }}
    .invoice-wrap {{
        max-width: 800px; margin: 0 auto;
        background: #fff; border-radius: 12px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08); overflow: hidden;
    }}
    .header {{
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: #fff; padding: 32px 40px;
    }}
    .header h1 {{ font-size: 26px; font-weight: 600; margin-bottom: 4px; }}
    .header p {{ font-size: 14px; opacity: 0.85; }}
    .body {{ padding: 32px 40px; }}
    .meta {{ display: flex; justify-content: space-between; margin-bottom: 28px; }}
    .meta-left p, .meta-right p {{ font-size: 14px; line-height: 1.8; color: #4b5563; }}
    .meta-right {{ text-align: right; }}
    .status-badge {{
        display: inline-block; padding: 4px 14px; border-radius: 20px;
        font-size: 13px; font-weight: 600; color: #fff;
        background: {status_color};
    }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 16px; }}
    th {{
        background: #f8fafc; padding: 10px 12px; font-size: 13px;
        font-weight: 600; color: #475569; text-align: left;
        border-bottom: 2px solid #e2e8f0;
    }}
    td {{
        padding: 10px 12px; font-size: 14px; border-bottom: 1px solid #e2e8f0;
    }}
    .total-row td {{ font-weight: 600; font-size: 16px; border-top: 2px solid #1e40af; }}
    .info-section {{ margin-bottom: 20px; }}
    .info-section h3 {{ font-size: 14px; color: #374151; margin-bottom: 8px; border-left: 3px solid #3b82f6; padding-left: 10px; }}
    .info-section p {{ font-size: 13px; line-height: 1.6; color: #4b5563; padding-left: 13px; }}
    .footer {{
        padding: 20px 40px; border-top: 1px solid #e2e8f0;
        font-size: 12px; color: #9ca3af; text-align: center;
    }}
    .print-btn {{
        display: inline-block; margin: 0 40px 32px;
        padding: 10px 28px; background: #1e40af; color: #fff;
        border: none; border-radius: 8px; font-size: 14px; cursor: pointer;
    }}
    .print-btn:hover {{ background: #1e3a8a; }}
    @media print {{
        body {{ background: #fff; padding: 0; }}
        .invoice-wrap {{ box-shadow: none; border-radius: 0; }}
        .print-btn {{ display: none; }}
        .no-print {{ display: none; }}
    }}
</style>
</head>
<body>
<div class="invoice-wrap">
    <div class="header">
        <h1>电子发票</h1>
        <p>发票号: {invoice.invoice_no}</p>
        {f'<p>关联订单: {invoice.order_no}</p>' if invoice.order_no else ''}
    </div>
    <div class="body">
        <div class="meta">
            <div class="meta-left">
                <p><strong>开票日期:</strong> {created_at_str}</p>
                <p><strong>客户 ID:</strong> #{invoice.user_id}</p>
            </div>
            <div class="meta-right">
                <p><span class="status-badge">{status_label}</span></p>
                <p style="margin-top:8px"><strong>含税金额:</strong> ¥{invoice.total_amount:.2f}</p>
            </div>
        </div>

        {"<div class='info-section'><h3>购买方信息</h3><p>" + (invoice.buyer_name or '-') + (" ｜ 税号: " + invoice.buyer_tax_id if invoice.buyer_tax_id else "") + "</p></div>" if invoice.buyer_name else ""}
        {"<div class='info-section'><h3>销售方信息</h3><p>" + (invoice.seller_name or '-') + (" ｜ 税号: " + invoice.seller_tax_id if invoice.seller_tax_id else "") + "</p></div>" if invoice.seller_name else ""}

        <table>
            <thead>
                <tr>
                    <th style="width:40px">#</th>
                    <th>项目名称</th>
                    <th style="width:60px">数量</th>
                    <th style="width:100px">单价</th>
                    <th style="width:100px">金额</th>
                </tr>
            </thead>
            <tbody>
                {items_rows}
                {f'<tr class="total-row"><td colspan="4" style="text-align:right">小计（不含税）</td><td style="text-align:right">¥{invoice.amount:.2f}</td></tr>' if invoice.tax_rate > 0 else ''}
                {tax_rows}
                {'' if invoice.tax_rate > 0 else f'<tr class="total-row"><td colspan="4" style="text-align:right">合计</td><td style="text-align:right">¥{invoice.total_amount:.2f}</td></tr>'}
            </tbody>
        </table>
        {f'<p style="font-size:13px;color:#6b7280;margin-bottom:16px"><strong>备注:</strong> {invoice.notes}</p>' if invoice.notes else ''}
        <button class="print-btn no-print" onclick="window.print()">🖨️ 打印 / 另存为 PDF</button>
    </div>
    <div class="footer">
        AI 数字名片 · 电子发票系统 &mdash; 本发票具有法律效力
    </div>
</div>
</body>
</html>"""
        return html

    # ── PDF 生成（reportlab） ─────────────────────────────────────

    @staticmethod
    def generate_pdf(invoice: Invoice) -> bytes:
        """使用 reportlab 生成专业发票 PDF，返回 bytes"""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib.enums import TA_RIGHT, TA_CENTER
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable
        )
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # ── 尝试注册中文字体 ──
        _font_registered = False
        _chinese_font_candidates = [
            # Windows 常见中文字体路径
            "C:/Windows/Fonts/msyh.ttc",          # Microsoft YaHei
            "C:/Windows/Fonts/simhei.ttf",         # SimHei
            "C:/Windows/Fonts/simsun.ttc",         # SimSun
            "C:/Windows/Fonts/SimSun.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # Linux
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
        font_name = "Helvetica"  # fallback

        for fp in _chinese_font_candidates:
            if os.path.exists(fp):
                try:
                    pdfmetrics.registerFont(TTFont("ChineseFont", fp))
                    font_name = "ChineseFont"
                    _font_registered = True
                    break
                except Exception:
                    continue

        # ── 构建 PDF ──
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            topMargin=20*mm, bottomMargin=15*mm,
            leftMargin=20*mm, rightMargin=20*mm,
        )

        getSampleStyleSheet()

        # 自定义样式
        style_title = ParagraphStyle(
            "InvoiceTitle", fontName=font_name, fontSize=22,
            leading=30, alignment=TA_CENTER, spaceAfter=4*mm,
            textColor=colors.HexColor("#1e40af"),
        )
        style_subtitle = ParagraphStyle(
            "InvoiceSubtitle", fontName=font_name, fontSize=10,
            leading=14, alignment=TA_CENTER, spaceAfter=6*mm,
            textColor=colors.HexColor("#6b7280"),
        )
        style_label = ParagraphStyle(
            "Label", fontName=font_name, fontSize=9,
            leading=13, textColor=colors.HexColor("#4b5563"),
        )
        style_value = ParagraphStyle(
            "Value", fontName=font_name, fontSize=10,
            leading=14, textColor=colors.HexColor("#111827"),
        )
        style_right = ParagraphStyle(
            "RightAlign", fontName=font_name, fontSize=10,
            leading=14, alignment=TA_RIGHT, textColor=colors.HexColor("#111827"),
        )
        style_center = ParagraphStyle(
            "CenterAlign", fontName=font_name, fontSize=10,
            leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#111827"),
        )
        style_th = ParagraphStyle(
            "TableHeader", fontName=font_name, fontSize=9,
            leading=12, textColor=colors.white,
        )
        style_small = ParagraphStyle(
            "Small", fontName=font_name, fontSize=8,
            leading=11, textColor=colors.HexColor("#9ca3af"),
            alignment=TA_CENTER,
        )
        ParagraphStyle(
            "Section", fontName=font_name, fontSize=10,
            leading=14, textColor=colors.HexColor("#374151"),
            spaceBefore=4*mm, spaceAfter=2*mm,
        )

        def P(text, style=style_value):
            """Shortcut: Paragraph with safe encoding"""
            return Paragraph(str(text), style)

        elements = []

        # ── 标题 ──
        elements.append(Paragraph("电 子 发 票", style_title))
        elements.append(Paragraph(f"发票号: {invoice.invoice_no}", style_subtitle))
        if invoice.order_no:
            elements.append(Paragraph(f"订单号: {invoice.order_no}", style_subtitle))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")))
        elements.append(Spacer(1, 3*mm))

        # ── 头部信息 ──
        status_label = {"paid": "已支付", "unpaid": "未支付", "cancelled": "已取消"}.get(
            invoice.status, invoice.status
        )
        created_at_str = (
            invoice.created_at.strftime("%Y-%m-%d")
            if isinstance(invoice.created_at, datetime)
            else str(invoice.created_at)[:10]
        )

        header_data = [
            [P("开票日期:", style_label), P(created_at_str, style_value),
             P("状态:", style_label), P(status_label, style_value)],
            [P("客户 ID:", style_label), P(f"#{invoice.user_id}", style_value),
             P("含税金额:", style_label), P(f"¥{invoice.total_amount:.2f}", style_value)],
        ]
        header_table = Table(header_data, colWidths=[22*mm, 50*mm, 22*mm, 50*mm])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 3*mm))

        # ── 购销方信息 ──
        if invoice.buyer_name or invoice.seller_name:
            info_data = []
            if invoice.buyer_name:
                buyer_line = f"<b>购买方:</b> {invoice.buyer_name}"
                if invoice.buyer_tax_id:
                    buyer_line += f"&nbsp;&nbsp;|&nbsp;&nbsp;税号: {invoice.buyer_tax_id}"
                info_data.append([P(buyer_line, style_label)])
            if invoice.seller_name:
                seller_line = f"<b>销售方:</b> {invoice.seller_name}"
                if invoice.seller_tax_id:
                    seller_line += f"&nbsp;&nbsp;|&nbsp;&nbsp;税号: {invoice.seller_tax_id}"
                info_data.append([P(seller_line, style_label)])

            if info_data:
                info_table = Table(info_data, colWidths=[144*mm])
                info_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ]))
                elements.append(info_table)
                elements.append(Spacer(1, 3*mm))

        # ── 明细表 ──
        table_data = [
            [P("#", style_th), P("项目名称", style_th),
             P("数量", style_th), P("单价", style_th), P("金额", style_th)],
        ]

        for idx, item in enumerate(invoice.items or [], 1):
            desc = item.get("description", "")
            qty = item.get("quantity", 1)
            unit_price = item.get("unit_price", 0)
            amt = item.get("amount", qty * unit_price)
            table_data.append([
                P(str(idx), style_center),
                P(str(desc), style_value),
                P(str(qty), style_center),
                P(f"¥{unit_price:.2f}", style_right),
                P(f"¥{amt:.2f}", style_right),
            ])

        # 合计行
        if invoice.tax_rate > 0:
            table_data.append([
                P("", style_value),
                P("", style_value),
                P("", style_value),
                P(f"税率 {invoice.tax_rate:.1f}%", ParagraphStyle("tax", fontName=font_name, fontSize=9, leading=12, alignment=TA_RIGHT, textColor=colors.HexColor("#6b7280"))),
                P(f"¥{invoice.total_amount:.2f}", ParagraphStyle("total", fontName=font_name, fontSize=11, leading=14, alignment=TA_RIGHT, textColor=colors.HexColor("#1e40af"))),
            ])
        else:
            table_data.append([
                P("", style_value),
                P("", style_value),
                P("", style_value),
                P("合计", ParagraphStyle("total_label", fontName=font_name, fontSize=10, leading=14, alignment=TA_RIGHT, textColor=colors.HexColor("#111827"))),
                P(f"¥{invoice.total_amount:.2f}", ParagraphStyle("total", fontName=font_name, fontSize=11, leading=14, alignment=TA_RIGHT, textColor=colors.HexColor("#1e40af"))),
            ])

        col_widths = [12*mm, 56*mm, 16*mm, 30*mm, 30*mm]
        items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        items_table.setStyle(TableStyle([
            # 表头样式
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            # 表格线
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#1e40af")),
            ("LINEABOVE", (0, -1), (-1, -1), 1.5, colors.HexColor("#1e40af")),
            # 对齐
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            # 间距
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            # 合计行高亮
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f4ff")),
        ]))
        elements.append(items_table)

        # ── 备注 ──
        if invoice.notes:
            elements.append(Spacer(1, 3*mm))
            elements.append(Paragraph(f"<b>备注:</b> {invoice.notes}", style_label))

        # ── 金额大写 ──
        elements.append(Spacer(1, 5*mm))
        total_cn = InvoiceService._num2cn(invoice.total_amount)
        elements.append(Paragraph(f"<b>合计金额（大写）:</b> {total_cn}", style_label))

        # ── 页脚 ──
        elements.append(Spacer(1, 8*mm))
        elements.append(HRFlowable(width="100%", thickness=0.3, color=colors.HexColor("#d1d5db")))
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph("AI 数字名片 · 电子发票系统 — 本发票具有法律效力", style_small))

        # ── 构建 ──
        doc.build(elements)
        pdf_bytes = buf.getvalue()
        buf.close()
        return pdf_bytes

    @staticmethod
    def _num2cn(num: float) -> str:
        """金额数字转中文大写（支持到亿）"""
        if num == 0:
            return "零元整"

        units = ["", "拾", "佰", "仟", "万", "拾", "佰", "仟", "亿"]
        digits = ["零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"]

        integer_part = int(num)
        decimal_part = round(num - integer_part, 2)
        jiao = int(decimal_part * 10)
        fen = int(round(decimal_part * 100 - jiao * 10))

        def _convert(n: int) -> str:
            if n == 0:
                return "零"
            result = ""
            s = str(n)
            zero_flag = False
            for i, ch in enumerate(s):
                digit = int(ch)
                pos = len(s) - i - 1
                if digit == 0:
                    zero_flag = True
                else:
                    if zero_flag:
                        result += "零"
                        zero_flag = False
                    result += digits[digit] + units[pos]
            return result

        result = ""
        yi = integer_part // 100000000
        wan = (integer_part % 100000000) // 10000
        ge = integer_part % 10000

        if yi > 0:
            result += _convert(yi) + "亿"
        if wan > 0:
            if yi > 0 and wan < 1000:
                result += "零"
            result += _convert(wan) + "万"
        if ge > 0:
            if (yi > 0 or wan > 0) and ge < 1000:
                result += "零"
            result += _convert(ge)
        else:
            if yi > 0 or wan > 0:
                result += "元"
                if jiao == 0 and fen == 0:
                    result += "整"
                return result

        result += "元"

        if jiao == 0 and fen == 0:
            result += "整"
        else:
            if jiao > 0:
                result += digits[jiao] + "角"
            if fen > 0:
                result += digits[fen] + "分"

        return result
