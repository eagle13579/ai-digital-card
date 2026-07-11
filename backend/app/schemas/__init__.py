from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    phone: str = Field(..., pattern=r"^1\d{10}$")
    password: str = Field(..., min_length=8, description="密码，至少8位，需包含大小写字母、数字和特殊字符")
    name: str = Field(..., min_length=1, max_length=64)
    username: Optional[str] = None
    company: Optional[str] = ""
    title: Optional[str] = ""
    intro: Optional[str] = ""
    avatar: Optional[str] = ""


class UserLogin(BaseModel):
    phone: str
    password: str


class WeChatLogin(BaseModel):
    code: str


class UserResponse(BaseModel):
    id: int
    username: Optional[str] = None
    phone: str
    name: str
    avatar: str
    company: str
    title: str
    intro: str
    role: str
    membership_tier: str = "free"
    membership_expires_at: Optional[datetime] = None
    unlock_quota: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    intro: Optional[str] = None


# ── Brochure ──────────────────────────────────────────────────────────────────

class PageSchema(BaseModel):
    id: Optional[int] = None
    sort_order: int = 0
    content_type: str = "text"
    content: str = ""
    image_url: str = ""
    media_url: str = ""
    """视频/多媒体文件 URL"""
    ai_summary: str = ""

    model_config = {"from_attributes": True}


class BrochureCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=128)
    cover: str = ""
    purpose: str = ""
    album_meta: Optional[str] = None
    pages: list[PageSchema] = []


class BrochureUpdate(BaseModel):
    title: Optional[str] = None
    cover: Optional[str] = None
    purpose: Optional[str] = None
    album_meta: Optional[str] = None
    pages: Optional[list[PageSchema]] = None


class BrochureResponse(BaseModel):
    id: int
    user_id: int
    title: str
    cover: str
    purpose: str
    pages_count: int
    status: str
    share_token: str
    view_count: int
    album_meta: Optional[str] = None
    visibility: str = "public"
    platform_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    pages: list[PageSchema] = []

    model_config = {"from_attributes": True}


# ── Tag ───────────────────────────────────────────────────────────────────────

class TagInput(BaseModel):
    tag: str = Field(..., min_length=1, max_length=64)
    weight: float = 1.0


class TagBatchInput(BaseModel):
    tags: list[TagInput] = Field(..., min_length=1, max_length=50)
    tag_type: str = Field(..., pattern=r"^(provide|need)$")
    source: str = "manual"


class TagResponse(BaseModel):
    id: int
    user_id: int
    tag_type: str
    tag: str
    weight: float
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Match ─────────────────────────────────────────────────────────────────────

class MatchResponse(BaseModel):
    id: int
    user_a_id: int
    user_b_id: int
    match_score: float
    status: str
    common_tags: str = "[]"
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchAction(BaseModel):
    status: str = Field(..., pattern=r"^(pending|matched|confirmed)$")


# ── Unlock ────────────────────────────────────────────────────────────────────

class UnlockRequest(BaseModel):
    match_record_id: int


class UnlockResponse(BaseModel):
    unlocked: bool
    name: str = ""
    phone: str = ""
    wechat: str = ""
    company: str = ""
    unlock_quota_remaining: int = 0
    message: str = ""


# ── Visitor ───────────────────────────────────────────────────────────────────

class VisitorLogCreate(BaseModel):
    visitor_id: Optional[str] = None
    visitor_name: str = ""
    visitor_ip: str = ""
    source: str = "direct"
    page_viewed: str = ""
    duration: int = 0


class InterestCreate(BaseModel):
    contact_msg: str = ""
    visitor_name: str = ""


class VisitorLogResponse(BaseModel):
    id: int
    brochure_id: int
    visitor_id: Optional[str]
    visitor_ip: str
    visitor_name: str
    source: str
    page_viewed: str
    duration: int
    interested: bool
    contact_msg: str
    visit_time: datetime

    model_config = {"from_attributes": True}


# ── Trust Network ─────────────────────────────────────────────────────────────

class TrustCreate(BaseModel):
    trusted_user_id: int


class TrustResponse(BaseModel):
    id: int
    user_id: int
    trusted_user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Auth ──────────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class WeChatMiniLogin(BaseModel):
    code: str = Field(..., min_length=1, description="微信小程序 wx.login() 返回的临时 code")
    user_info: Optional[dict] = None
