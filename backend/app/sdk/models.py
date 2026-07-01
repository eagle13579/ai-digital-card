"""
AI数字名片 SDK 数据模型

基于 Pydantic 的类型安全数据模型，映射后端 API 的请求/响应结构。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

# ══════════════════════════════════════════════════════════════════════════════
# 通用模型
# ══════════════════════════════════════════════════════════════════════════════

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """API 统一响应包裹。"""

    code: int = 0
    message: str = "ok"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应。"""

    items: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


# ══════════════════════════════════════════════════════════════════════════════
# 用户模型
# ══════════════════════════════════════════════════════════════════════════════


class User(BaseModel):
    """用户信息。"""

    id: int
    username: Optional[str] = None
    phone: str
    name: str
    avatar: str = ""
    company: str = ""
    title: str = ""
    intro: str = ""
    role: str = "user"
    membership_tier: str = "free"
    membership_expires_at: Optional[datetime] = None
    unlock_quota: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """注册请求。"""

    phone: str = Field(..., pattern=r"^1\d{10}$")
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=64)
    username: Optional[str] = None
    company: Optional[str] = ""
    title: Optional[str] = ""
    intro: Optional[str] = ""
    avatar: Optional[str] = ""


class UserLogin(BaseModel):
    """登录请求。"""

    phone: str
    password: str


class UserUpdate(BaseModel):
    """用户信息更新。"""

    name: Optional[str] = None
    avatar: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    intro: Optional[str] = None


class TokenResponse(BaseModel):
    """认证令牌响应。"""

    access_token: str
    token_type: str = "bearer"
    user: User


# ══════════════════════════════════════════════════════════════════════════════
# 名片模型
# ══════════════════════════════════════════════════════════════════════════════


class Page(BaseModel):
    """名片页面。"""

    id: Optional[int] = None
    sort_order: int = 0
    content_type: str = "text"
    content: str = ""
    image_url: str = ""
    media_url: str = ""
    ai_summary: str = ""

    model_config = {"from_attributes": True}


class Brochure(BaseModel):
    """电子名片。"""

    id: int
    user_id: int
    title: str
    cover: str = ""
    purpose: str = ""
    pages_count: int = 1
    status: str = "draft"
    share_token: str = ""
    view_count: int = 0
    album_meta: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    pages: list[Page] = []

    model_config = {"from_attributes": True}


class BrochureCreate(BaseModel):
    """创建名片请求。"""

    title: str = Field(..., min_length=1, max_length=128)
    cover: str = ""
    purpose: str = ""
    album_meta: Optional[str] = None
    pages: list[Page] = []


class BrochureUpdate(BaseModel):
    """更新名片请求。"""

    title: Optional[str] = None
    cover: Optional[str] = None
    purpose: Optional[str] = None
    album_meta: Optional[str] = None
    pages: Optional[list[Page]] = None


# ══════════════════════════════════════════════════════════════════════════════
# CRM 模型
# ══════════════════════════════════════════════════════════════════════════════


class CrmPipelineStage(BaseModel):
    """销售管道阶段。"""

    id: int
    user_id: int
    name: str
    sort_order: int = 0
    color: str = "#1890ff"
    is_default: bool = False
    is_closed: bool = False
    win_probability: float = 0.0
    created_at: datetime

    model_config = {"from_attributes": True}


class CrmContact(BaseModel):
    """CRM 联系人。"""

    id: int
    owner_id: int
    user_id: Optional[int] = None
    name: str
    phone: str = ""
    email: str = ""
    company: str = ""
    title: str = ""
    department: str = ""
    avatar: str = ""
    intro: str = ""
    source: str = "manual"
    source_record_id: Optional[int] = None
    tags: str = "[]"
    pipeline_stage_id: Optional[int] = None
    deal_value: Optional[float] = None
    deal_currency: str = "CNY"
    last_contacted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    stage_name: Optional[str] = None

    model_config = {"from_attributes": True}


class CrmContactCreate(BaseModel):
    """创建 CRM 联系人请求。"""

    name: str = Field(..., min_length=1, max_length=128)
    phone: str = ""
    email: str = ""
    company: str = ""
    title: str = ""
    department: str = ""
    avatar: str = ""
    intro: str = ""
    source: str = "manual"
    tags: str = "[]"
    pipeline_stage_id: Optional[int] = None
    deal_value: Optional[float] = None


class CrmContactUpdate(BaseModel):
    """更新 CRM 联系人请求。"""

    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    avatar: Optional[str] = None
    intro: Optional[str] = None
    tags: Optional[str] = None
    pipeline_stage_id: Optional[int] = None
    deal_value: Optional[float] = None


class CrmDeal(BaseModel):
    """销售机会。"""

    id: int
    owner_id: int
    contact_id: int
    pipeline_stage_id: int
    title: str
    value: float = 0.0
    currency: str = "CNY"
    probability: float = 0.0
    expected_close_date: Optional[datetime] = None
    status: str = "open"
    lost_reason: str = ""
    created_at: datetime
    updated_at: datetime
    contact_name: Optional[str] = None
    stage_name: Optional[str] = None

    model_config = {"from_attributes": True}


class CrmDealCreate(BaseModel):
    """创建销售机会请求。"""

    contact_id: int
    pipeline_stage_id: int
    title: str = Field(..., min_length=1, max_length=256)
    value: float = 0.0
    currency: str = "CNY"
    probability: float = 0.0
    expected_close_date: Optional[datetime] = None


class CrmActivity(BaseModel):
    """CRM 活动记录。"""

    id: int
    owner_id: int
    contact_id: int
    deal_id: Optional[int] = None
    activity_type: str
    title: str = ""
    description: str = ""
    source_model: Optional[str] = None
    source_record_id: Optional[int] = None
    activity_date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class CrmNote(BaseModel):
    """CRM 笔记。"""

    id: int
    owner_id: int
    contact_id: Optional[int] = None
    deal_id: Optional[int] = None
    content: str
    is_pinned: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CrmNoteCreate(BaseModel):
    """创建笔记请求。"""

    contact_id: Optional[int] = None
    deal_id: Optional[int] = None
    content: str = Field(..., min_length=1)


class CrmNoteUpdate(BaseModel):
    """更新笔记请求。"""

    content: Optional[str] = None
    is_pinned: Optional[bool] = None
