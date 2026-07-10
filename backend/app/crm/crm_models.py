"""CRM 数据模型。

复用策略:
  - CrmContact.user_id 可选关联 User (名片交换对方)
  - CrmContact.source 记录来源: match(名片交换) | manual(手动) | visitor(访客) | import(导入)
  - CrmActivity 自动关联 Message/MatchRecord/VisitorLog
  - CrmDeal.status 映射 pipeline 阶段名
  - CrmPipelineStage 为可配置的管道阶段

表名前缀: crm_*
"""

from datetime import datetime
from decimal import Decimal
import json

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CrmPipelineStage(Base):
    """销售管道阶段定义（每个用户可自定义）。"""

    __tablename__ = "crm_pipeline_stages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="阶段名称")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    color: Mapped[str] = mapped_column(String(16), default="#1890ff", comment="显示颜色")
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否是新联系人默认阶段"
    )
    is_closed: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否终止阶段(成交/丢失)"
    )
    win_probability: Mapped[float] = mapped_column(
        Float, default=0.0, comment="该阶段的默认赢单率(0-100)"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "sort_order": self.sort_order,
            "color": self.color,
            "is_default": self.is_default,
            "is_closed": self.is_closed,
            "win_probability": self.win_probability,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CrmContact(Base):
    """CRM 联系人。

    可通过 user_id 关联平台现有用户(名片交换对方)，也可独立存在(手动/导入)。
    """

    __tablename__ = "crm_contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="CRM所属用户"
    )

    # ── 关联平台用户（可选） ──────────────────────────────────────────
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="关联的平台用户(名片交换对方)",
    )

    # ── 联系人基本信息 ────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="姓名")
    phone: Mapped[str] = mapped_column(String(32), default="", comment="手机号")
    email: Mapped[str] = mapped_column(String(128), default="", comment="邮箱")
    company: Mapped[str] = mapped_column(String(256), default="", comment="公司")
    title: Mapped[str] = mapped_column(String(128), default="", comment="职位")
    department: Mapped[str] = mapped_column(String(128), default="", comment="部门")
    avatar: Mapped[str] = mapped_column(String(512), default="", comment="头像URL")
    intro: Mapped[str] = mapped_column(Text, default="", comment="个人简介/备注")

    # ── 来源 ──────────────────────────────────────────────────────────
    source: Mapped[str] = mapped_column(
        String(16),
        default="manual",
        comment="来源: match(名片交换) | manual(手动) | visitor(访客) | import(导入)",
    )
    source_record_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="来源记录ID(如MatchRecord.id)"
    )

    # ── 四级可见性 ────────────────────────────────────────────────────────
    visibility: Mapped[str] = mapped_column(
        String(20), default="public", comment="可见性: public/platform/network/private"
    )

    # ── 标签（JSON 数组，也可通过 UserTag 关联） ───────────────────────
    tags: Mapped[str] = mapped_column(
        Text, default="[]", comment="联系人标签(JSON数组)"
    )

    # ── 销售管道状态 ──────────────────────────────────────────────────
    pipeline_stage_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("crm_pipeline_stages.id"),
        nullable=True,
        default=None,
        comment="当前管道阶段",
    )
    deal_value: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True, default=None, comment="预估成交金额"
    )
    deal_currency: Mapped[str] = mapped_column(String(8), default="CNY", comment="币种")

    # ── 时间戳 ────────────────────────────────────────────────────────
    last_contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, comment="最后联系时间"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # ── 关系 ──────────────────────────────────────────────────────────
    stage = relationship("CrmPipelineStage", backref="contacts", lazy="joined")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "user_id": self.user_id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "company": self.company,
            "title": self.title,
            "department": self.department,
            "avatar": self.avatar,
            "intro": self.intro,
            "source": self.source,
            "source_record_id": self.source_record_id,
            "visibility": self.visibility,
            "tags": self.tags,
            "pipeline_stage_id": self.pipeline_stage_id,
            "deal_value": float(self.deal_value) if self.deal_value else None,
            "deal_currency": self.deal_currency,
            "last_contacted_at": self.last_contacted_at.isoformat()
            if self.last_contacted_at
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "stage_name": self.stage.name if self.stage else None,
        }


class CrmDeal(Base):
    """销售机会。

    一个联系人可以有多个销售机会(不同产品或不同时间)。
    简化设计: 一个联系人在同一时间只在一个阶段(Pipeline中体现)。
    """

    __tablename__ = "crm_deals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    contact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_contacts.id"), nullable=False, index=True
    )
    pipeline_stage_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_pipeline_stages.id"), nullable=False
    )

    # ── 机会信息 ──────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(256), nullable=False, comment="机会标题")
    value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0, comment="预估金额"
    )
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    probability: Mapped[float] = mapped_column(Float, default=0.0, comment="赢单概率 0-100")
    expected_close_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, comment="预计成交日期"
    )

    # ── 状态 ──────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(16),
        default="open",
        comment="open(进行中) | won(已成交) | lost(已丢失) | paused(暂缓)",
    )
    lost_reason: Mapped[str] = mapped_column(Text, default="", comment="丢单原因")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # ── 关系 ──────────────────────────────────────────────────────────
    contact = relationship("CrmContact", backref="deals", lazy="joined")
    stage = relationship("CrmPipelineStage", backref="deals", lazy="joined")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "contact_id": self.contact_id,
            "pipeline_stage_id": self.pipeline_stage_id,
            "title": self.title,
            "value": float(self.value),
            "currency": self.currency,
            "probability": self.probability,
            "expected_close_date": self.expected_close_date.isoformat()
            if self.expected_close_date
            else None,
            "status": self.status,
            "lost_reason": self.lost_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "contact_name": self.contact.name if self.contact else None,
            "stage_name": self.stage.name if self.stage else None,
        }


class CrmActivity(Base):
    """活动记录 — 联系人时间线。

    自动生成: 名片交换/名片查看/消息往来/匹配
    手动创建: 电话/会面/邮件
    """

    __tablename__ = "crm_activities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    contact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_contacts.id"), nullable=False, index=True
    )
    deal_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("crm_deals.id"), nullable=True, comment="关联的机会"
    )

    # ── 活动类型 ──────────────────────────────────────────────────────
    activity_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="类型: call | meeting | email | note | message | match | visit | system",
    )

    # ── 活动内容 ──────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(256), default="", comment="活动标题")
    description: Mapped[str] = mapped_column(Text, default="", comment="活动描述/纪要")
    source_model: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="来源表名(如messages/visitor_logs)"
    )
    source_record_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="来源记录ID"
    )

    # ── 时间 ──────────────────────────────────────────────────────────
    activity_date: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), comment="活动发生时间"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "contact_id": self.contact_id,
            "deal_id": self.deal_id,
            "activity_type": self.activity_type,
            "title": self.title,
            "description": self.description,
            "source_model": self.source_model,
            "source_record_id": self.source_record_id,
            "activity_date": self.activity_date.isoformat()
            if self.activity_date
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CrmNote(Base):
    """联系人/机会笔记（轻量级，自由文本）。"""

    __tablename__ = "crm_notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    contact_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("crm_contacts.id"), nullable=True, comment="关联联系人"
    )
    deal_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("crm_deals.id"), nullable=True, comment="关联机会"
    )

    content: Mapped[str] = mapped_column(Text, nullable=False, comment="笔记内容")
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否置顶")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "contact_id": self.contact_id,
            "deal_id": self.deal_id,
            "content": self.content,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CrmWorkflowRule(Base):
    """工作流自动化规则。

    纯 JSON 配置，说明字段见 crm_workflow_engine.py 的 PRESET_RULES。
    """

    __tablename__ = "crm_workflow_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # ── 基本信息 ──────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="规则名称"
    )
    description: Mapped[str] = mapped_column(
        Text, default="", comment="规则描述"
    )

    # ── 触发条件 ──────────────────────────────────────────────────────────
    trigger_event: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="触发事件: contact_added | deal_created | stage_changed",
    )
    conditions: Mapped[str] = mapped_column(
        Text,
        default="[]",
        comment="条件列表(JSON): [{\"field\":\"source\",\"operator\":\"eq\",\"value\":\"manual\"}]",
    )

    # ── 动作 ──────────────────────────────────────────────────────────────
    actions: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="动作列表(JSON): [{\"type\":\"send_email\",\"config\":{...}}]",
    )

    # ── 启用状态 ──────────────────────────────────────────────────────────
    enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否启用"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "description": self.description,
            "trigger_event": self.trigger_event,
            "conditions": json.loads(self.conditions) if self.conditions else [],
            "actions": json.loads(self.actions) if self.actions else [],
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CrmWorkflowLog(Base):
    """工作流执行日志。"""

    __tablename__ = "crm_workflow_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    rule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_workflow_rules.id"), nullable=False
    )
    rule_name: Mapped[str] = mapped_column(
        String(128), default="", comment="规则名称(冗余方便查询)"
    )
    trigger_event: Mapped[str] = mapped_column(
        String(32), default="", comment="触发事件"
    )
    context_snapshot: Mapped[str] = mapped_column(
        Text, default="", comment="触发时的上下文快照(JSON)"
    )
    action_results: Mapped[str] = mapped_column(
        Text, default="", comment="动作执行结果(JSON)"
    )
    success: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否全部成功"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "trigger_event": self.trigger_event,
            "context_snapshot": json.loads(self.context_snapshot) if self.context_snapshot else {},
            "action_results": json.loads(self.action_results) if self.action_results else [],
            "success": self.success,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 邮件营销 Campaign
# ═══════════════════════════════════════════════════════════════════════════════


class CrmCampaign(Base):
    """邮件营销活动。

    管理批量邮件发送，支持按标签/管道阶段/来源筛选目标人群，
    内建打开率追踪（追踪像素）和退订机制。
    """

    __tablename__ = "crm_campaigns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # ── 活动基本信息 ────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="活动名称"
    )
    subject: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="邮件主题"
    )
    template_name: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="模板名称(对应 email_templates 中的函数名)"
    )
    template_params: Mapped[str] = mapped_column(
        Text, default="{}", comment="模板参数(JSON)"
    )

    # ── 目标人群筛选条件 ─────────────────────────────────────────
    target_filter: Mapped[str] = mapped_column(
        Text,
        default="{}",
        comment="目标筛选条件(JSON): {tags:[], pipeline_stage_ids:[], sources:[], created_after:, created_before:}",
    )

    # ── 发送状态 ────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(16),
        default="draft",
        comment="draft | sending | sent | paused",
    )

    # ── 统计（冗余，方便快速读取） ──────────────────────────────
    total_recipients: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    opened_count: Mapped[int] = mapped_column(Integer, default=0)
    unsubscribed_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "subject": self.subject,
            "template_name": self.template_name,
            "template_params": json.loads(self.template_params) if self.template_params else {},
            "target_filter": json.loads(self.target_filter) if self.target_filter else {},
            "status": self.status,
            "total_recipients": self.total_recipients,
            "sent_count": self.sent_count,
            "opened_count": self.opened_count,
            "unsubscribed_count": self.unsubscribed_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CrmCampaignRecipient(Base):
    """邮件营销活动 — 收件人记录。

    记录每个收件人的发送状态、打开时间、退订状态。
    使用 tracking_token 做追踪像素和退订链接的唯一标识。
    """

    __tablename__ = "crm_campaign_recipients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_campaigns.id"), nullable=False, index=True
    )
    contact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_contacts.id"), nullable=False
    )

    # ── 收件人信息（冗余，避免关联查询） ──────────────────────
    email: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="收件人邮箱"
    )
    name: Mapped[str] = mapped_column(
        String(128), default="", comment="收件人姓名"
    )

    # ── 追踪令牌（用于追踪像素和退订链接） ─────────────────────
    tracking_token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="唯一追踪令牌",
    )

    # ── 状态 ────────────────────────────────────────────────────
    sent: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已发送")
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, comment="发送时间"
    )
    send_error: Mapped[str] = mapped_column(
        Text, default="", comment="发送错误信息"
    )

    opened: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已打开")
    opened_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, comment="打开时间"
    )

    unsubscribed: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否退订"
    )
    unsubscribed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, comment="退订时间"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
