"""AI画册生成路由 — 从联系人/一句话简介生成画册内容，或增强已有画册。

所有 AI 调用均通过 ModelRegistry（DeepSeek → Cache → Ollama 降级链）。
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/brochure-gen", tags=["AI画册生成"])


# ── Pydantic 模型 ──────────────────────────────────────────────────────────


class ContactInput(BaseModel):
    """联系人信息输入"""

    name: str = Field("", description="姓名")
    title: str = Field("", description="职位/头衔")
    company: str = Field("", description="公司/组织")
    phone: str = Field("", description="手机号")
    email: str = Field("", description="邮箱")
    wechat: str = Field("", description="微信号")
    skills: str = Field("", description="技能标签（逗号分隔）")
    intro: str = Field("", description="个人简介")


class PageOutput(BaseModel):
    """画册页面输出"""

    type: str = Field("text", description="页面类型: cover/text/contact/image")
    content: str = Field("", description="页面内容")
    style: str = Field("card", description="页面样式: centered/card/compact")


class ContactGenerationOutput(BaseModel):
    """从联系人生成的结果"""

    title: str = Field("", description="画册标题")
    pages: list[PageOutput] = Field(default_factory=list, description="页面列表")
    tags: list[str] = Field(default_factory=list, description="推荐标签")
    suggested_template: str = Field("professional", description="推荐模板风格")


class BriefPageOutput(BaseModel):
    """从简介生成的单页输出"""

    title: str = Field("", description="页面标题")
    content: str = Field("", description="页面内容")
    layout: str = Field("text", description="布局: cover/text/split/image")
    icon: str = Field("📄", description="页面图标")


class EnhanceOutput(BaseModel):
    """增强结果输出"""

    suggestions: list[dict] = Field(default_factory=list, description="优化建议列表")
    tags: list[str] = Field(default_factory=list, description="推荐标签")
    summary: str = Field("", description="画册内容总结")
    missing_sections: list[str] = Field(
        default_factory=list, description="建议补充的章节"
    )


# ── API 端点 ──────────────────────────────────────────────────────────────


@router.post(
    "/from-contact",
    response_model=ContactGenerationOutput,
    summary="从联系人信息生成名片/画册",
    description="根据用户填写的联系人信息（姓名、职位、公司等），AI 自动生成一份精美的电子名片或画册内容。",
)
async def generate_from_contact(contact: ContactInput):
    """从联系人信息生成名片/画册内容。"""
    try:
        from app.services.brochure_generation_service import (
            BrochureGenerationService,
        )

        service = BrochureGenerationService()
        result = await service.generate_from_contact(contact.model_dump())
        return ContactGenerationOutput(
            title=result.get("title", ""),
            pages=[PageOutput(**p) for p in result.get("pages", [])],
            tags=result.get("tags", []),
            suggested_template=result.get("suggested_template", "professional"),
        )
    except Exception as exc:
        logger.exception("从联系人生成画册失败: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="AI 生成服务暂时不可用，请稍后重试",
        )


@router.post(
    "/from-brief",
    response_model=list[BriefPageOutput],
    summary="从一句话简介生成多页画册",
    description="根据用户的一句话自我介绍，AI 自动生成多页精美画册内容，支持选择模板风格。",
)
async def generate_from_brief(
    brief: str = Query(..., description="一句话简介，如：'我是AI创业者，专注企业智能解决方案'"),
    template: str = Query("professional", description="模板风格: professional(专业商务)/creative(创意设计)/minimal(极简主义)/tech(科技感)"),
):
    """从一句话简介生成多页画册内容。"""
    if not brief or not brief.strip():
        raise HTTPException(
            status_code=422,
            detail="简介不能为空",
        )
    if template not in ("professional", "creative", "minimal", "tech"):
        template = "professional"

    try:
        from app.services.brochure_generation_service import (
            BrochureGenerationService,
        )

        service = BrochureGenerationService()
        pages = await service.generate_pages_from_brief(brief, template)
        return [BriefPageOutput(**p) for p in pages]
    except Exception as exc:
        logger.exception("从简介生成画册失败: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="AI 生成服务暂时不可用，请稍后重试",
        )


@router.post(
    "/enhance/{brochure_id}",
    response_model=list[EnhanceOutput],
    summary="增强已有画册内容",
    description="对已有画册进行 AI 智能增强：补充描述文案、推荐标签、内容改进建议等。",
)
async def enhance_brochure(brochure_id: int):
    """增强已有画册内容（AI补充描述/标签/建议）。"""
    if brochure_id < 1:
        raise HTTPException(
            status_code=422,
            detail="无效的画册 ID",
        )

    try:
        from app.services.brochure_generation_service import (
            BrochureGenerationService,
        )

        service = BrochureGenerationService()
        result = await service.enhance_existing_brochure(brochure_id)
        return [EnhanceOutput(**item) for item in result]
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("增强画册内容失败: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="AI 生成服务暂时不可用，请稍后重试",
        )
