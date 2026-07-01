"""文档生成数据库模型 — 报价单(Quotation)/合同(Contract)/提案(Proposal)"""

from datetime import datetime

from sqlalchemy import Integer, String, DateTime, Text, Float, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Document(Base):
    """生成的文档记录 — 报价单/合同/提案"""

    __tablename__ = "crm_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="所属用户 ID")
    contact_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="关联 CRM 联系人 ID")
    deal_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="关联销售机会 ID")

    # ── 文档类型 ────────────────────────────────────────────
    doc_type: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="文档类型: quotation | contract | proposal"
    )
    template_name: Mapped[str] = mapped_column(
        String(64), default="", comment="模板名称(预设模板的 key)"
    )
    title: Mapped[str] = mapped_column(String(256), default="", comment="文档标题")
    doc_number: Mapped[str] = mapped_column(
        String(32), default="", comment="文档编号 Q-YYYYMMDD-XXXX / C-... / P-..."
    )

    # ── 内容 ────────────────────────────────────────────────
    content_html: Mapped[str] = mapped_column(
        Text, default="", comment="渲染后的 HTML 内容"
    )
    content_data: Mapped[dict] = mapped_column(
        JSON, default=dict, comment="填写的变量数据 {key: value}"
    )

    # ── 金额 ────────────────────────────────────────────────
    total_amount: Mapped[float] = mapped_column(Float, default=0.0, comment="总金额")
    currency: Mapped[str] = mapped_column(String(8), default="CNY", comment="币种")

    # ── 状态 ────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(16),
        default="draft",
        comment="draft(草稿) | final(定稿) | sent(已发送) | signed(已签署)",
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
