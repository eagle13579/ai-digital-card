"""数智名片技能注册表 — 动态技能发现与管理。

端点:
  GET    /api/mingpian/skills          — 列出所有注册的名片技能
  POST   /api/mingpian/skills          — 注册新技能
  GET    /api/mingpian/skills/search?q=xxx — 按名称/描述搜索技能

技能注册表（Skill Registry）允许 AI Agent 动态发现名片可以执行的能力，
并允许外部模块或用户注册新的技能到名片上。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/mingpian", tags=["数智名片技能"])


# ── Schemas ─────────────────────────────────────────────────────────────


class SkillRegisterRequest(BaseModel):
    """注册新技能的请求体"""

    name: str = Field(..., min_length=1, max_length=128, description="技能名称")
    description: str = Field("", max_length=1024, description="技能描述")
    endpoint: str = Field("", max_length=256, description="技能调用端点（可选）")
    icon: str = Field("🤖", max_length=64, description="技能图标 emoji")
    category: str = Field("general", max_length=64, description="技能分类")
    metadata: dict = Field(default_factory=dict, description="扩展元数据")


class SkillSchema(BaseModel):
    """技能完整响应"""

    id: str = Field(..., description="技能唯一标识符")
    name: str
    description: str
    endpoint: str
    icon: str
    category: str
    active: bool = True
    registered_at: str
    metadata: dict = Field(default_factory=dict)


class SkillSearchResult(BaseModel):
    """搜索结果"""
    query: str
    total: int
    results: list[SkillSchema]


# ── In-Memory 技能注册表 ──────────────────────────────────────────────
# 生产环境应替换为数据库持久化存储

_registry: dict[str, dict] = {}

# 预注册一些默认名片技能
_DEFAULT_SKILLS = [
    {
        "name": "名片交换",
        "description": "通过 AI 智能匹配交换电子名片，支持跨平台一键交换",
        "endpoint": "/api/miniapp/exchange",
        "icon": "🤝",
        "category": "interaction",
    },
    {
        "name": "六度人脉推荐",
        "description": "基于六度关系理论，智能推荐潜在合作伙伴和行业联系人",
        "endpoint": "/api/six-degrees/recommend",
        "icon": "🔗",
        "category": "networking",
    },
    {
        "name": "AI 名片设计",
        "description": "AI 智能生成个性化名片设计，支持多种模板和风格",
        "endpoint": "/api/ai/design",
        "icon": "🎨",
        "category": "creation",
    },
    {
        "name": "名片 OCR 识别",
        "description": "拍照识别纸质名片，自动提取联系方式和企业信息",
        "endpoint": "/api/ocr/scan",
        "icon": "📷",
        "category": "recognition",
    },
    {
        "name": "CRM 客户管理",
        "description": "自动将交换的名片同步到 CRM 系统，管理客户关系",
        "endpoint": "/api/crm/contacts",
        "icon": "📊",
        "category": "management",
    },
    {
        "name": "AI 销售助手",
        "description": "智能分析客户画像，提供销售建议和跟进策略",
        "endpoint": "/api/ai/assist",
        "icon": "🧠",
        "category": "intelligence",
    },
    {
        "name": "多语言翻译",
        "description": "名片内容实时翻译，支持 50+ 语言，跨国交流无障碍",
        "endpoint": "/api/i18n/translate",
        "icon": "🌐",
        "category": "i18n",
    },
    {
        "name": "信任评分",
        "description": "基于区块链和社交证明的信任评分系统，评估联系人可信度",
        "endpoint": "/api/trust/score",
        "icon": "🛡️",
        "category": "trust",
    },
]


def _init_default_skills() -> None:
    """初始化默认技能到注册表（如为空）"""
    if _registry:
        return
    now = datetime.now(timezone.utc).isoformat()
    for skill in _DEFAULT_SKILLS:
        sid = str(uuid.uuid4())[:8]
        _registry[sid] = {
            "id": sid,
            **skill,
            "active": True,
            "registered_at": now,
            "metadata": {},
        }


# 模块加载时初始化默认技能
_init_default_skills()


# ── API 端点 ────────────────────────────────────────────────────────────


@router.get("/skills", response_model=list[SkillSchema])
async def list_skills(
    category: Optional[str] = Query(None, description="按分类筛选"),
    active_only: bool = Query(True, description="仅返回激活状态的技能"),
) -> list[SkillSchema]:
    """列出所有注册的名片技能。

    支持按分类筛选和激活状态过滤。
    """
    skills = list(_registry.values())

    if active_only:
        skills = [s for s in skills if s.get("active", True)]

    if category:
        skills = [s for s in skills if s.get("category", "") == category]

    return [SkillSchema(**s) for s in skills]


@router.post("/skills", response_model=SkillSchema, status_code=status.HTTP_201_CREATED)
async def register_skill(body: SkillRegisterRequest) -> SkillSchema:
    """注册一个新的名片技能。

    注册成功后返回包含唯一 ID 的技能完整信息。
    """
    sid = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()

    skill = {
        "id": sid,
        "name": body.name,
        "description": body.description,
        "endpoint": body.endpoint,
        "icon": body.icon,
        "category": body.category,
        "active": True,
        "registered_at": now,
        "metadata": body.metadata,
    }

    # 检查名称是否已存在
    for existing in _registry.values():
        if existing["name"] == body.name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"技能名称 '{body.name}' 已存在",
            )

    _registry[sid] = skill
    return SkillSchema(**skill)


@router.get("/skills/search", response_model=SkillSearchResult)
async def search_skills(
    q: str = Query(..., min_length=1, max_length=200, description="搜索关键词"),
    active_only: bool = Query(True, description="仅搜索激活状态的技能"),
) -> SkillSearchResult:
    """按名称或描述搜索名片技能。

    返回匹配的技能列表及搜索元信息。
    """
    query = q.lower().strip()
    skills = list(_registry.values())

    if active_only:
        skills = [s for s in skills if s.get("active", True)]

    results = [
        s
        for s in skills
        if query in s.get("name", "").lower()
        or query in s.get("description", "").lower()
        or query in s.get("category", "").lower()
    ]

    return SkillSearchResult(
        query=q,
        total=len(results),
        results=[SkillSchema(**s) for s in results],
    )
