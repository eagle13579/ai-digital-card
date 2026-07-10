"""AI 助手 API — 文案生成与优化建议"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.writing_assistant import WritingAssistant
from app.ai.optimization import OptimizationAnalyzer
from app.agents.agent_runtime import AgentRuntime
from app.database import get_db
from app.dependencies import get_agent_runtime
from app.models.brochure import Brochure
from app.models.user import User
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai/assist", tags=["AI 助手"])


# ── 请求/响应模型 ──────────────────────────────────────────────────────


class WriteRequest(BaseModel):
    purpose: str = Field(
        ...,
        pattern=r"^(bio|company|company_intro|recommendation|slogan|personal)$",
        description="文案用途: bio=个人简介, company=公司介绍, company_intro=公司介绍(与company同义), recommendation=推荐语, slogan=名片标语, personal=个人用途",
    )
    name: str = ""
    position: str = ""
    company: str = ""
    industry: str = ""
    skills: str = ""
    description: str = ""
    highlights: str = ""
    relationship: str = ""
    core_value: str = ""


class WriteResponse(BaseModel):
    purpose: str
    content: str
    error: str = ""

    model_config = {"json_schema_extra": {
        "example": {
            "purpose": "bio",
            "content": "资深全栈工程师，8年互联网行业经验，擅长React/Node.js/Python技术栈，致力于用技术驱动业务增长。",
        }
    }}


class WriteAllRequest(BaseModel):
    name: str = ""
    position: str = ""
    company: str = ""
    industry: str = ""
    skills: str = ""
    description: str = ""
    highlights: str = ""
    relationship: str = ""
    core_value: str = ""


class WriteAllResponse(BaseModel):
    bio: str = ""
    company: str = ""
    recommendation: str = ""
    slogan: str = ""


class OptimizeResponse(BaseModel):
    brochure_id: int
    overall_score: float
    completeness: dict
    keyword_coverage: dict
    professionalism: dict
    top_priorities: list[str]


# ── Agent 通知函数（异步非阻塞） ──────────────────────────────────────


async def _assess_copy_quality(
    agent_runtime: AgentRuntime,
    user_id: int,
    purpose: str,
    content: str,
) -> None:
    """异步通知 KnowledgeAgent 做文案质量评估并反馈到 Gaia 学习循环。

    非阻塞 — Agent 报错不会影响主 API 响应。
    """
    try:
        knowledge = agent_runtime.get_agent("knowledge")
        if knowledge is None:
            logger.warning("KnowledgeAgent not found, skipping copy quality assessment")
            return
        await knowledge.handle_event({
            "type": "ai.assist.copy.generated",
            "user_id": user_id,
            "purpose": purpose,
            "content_length": len(content),
        })
        logger.info("KnowledgeAgent quality assessment triggered: user_id=%s, purpose=%s", user_id, purpose)
    except Exception:
        logger.exception("KnowledgeAgent quality assessment failed (non-blocking, safe to ignore)")


# ── API 端点 ──────────────────────────────────────────────────────────


@router.post("/write", response_model=WriteResponse)
async def generate_copy(
    data: WriteRequest,
    current_user: User = Depends(get_current_user),
    agent_runtime: AgentRuntime = Depends(get_agent_runtime),
):
    """生成名片文案

    根据用途和参数生成对应的名片文案。
    支持以下用途：
    - bio: 个人简介
    - company: 公司介绍 (含 company_intro 别名)
    - recommendation: 推荐语
    - slogan: 名片标语
    - personal: 个人用途
    """
    # 兼容 company_intro → company
    actual_purpose = "company" if data.purpose == "company_intro" else data.purpose
    content = await WritingAssistant.generate(
        purpose=actual_purpose,
        name=data.name,
        position=data.position,
        company=data.company,
        industry=data.industry,
        skills=data.skills,
        description=data.description,
        highlights=data.highlights,
        relationship=data.relationship,
        core_value=data.core_value,
    )

    if content.startswith("【"):
        return WriteResponse(purpose=data.purpose, content="", error=content)

    # ── Agent: 异步通知 KnowledgeAgent 做回答质量评估（反馈到Gaia学习循环）──
    asyncio.create_task(_assess_copy_quality(
        agent_runtime=agent_runtime,
        user_id=current_user.id,
        purpose=data.purpose,
        content=content,
    ))

    return WriteResponse(purpose=data.purpose, content=content)


@router.post("/write/all", response_model=WriteAllResponse)
async def generate_all_copy(
    data: WriteAllRequest,
    current_user: User = Depends(get_current_user),
):
    """一次性生成全部文案（个人简介+公司介绍+推荐语+标语）"""
    fields = data.model_dump()
    results = await WritingAssistant.generate_all(fields)
    return WriteAllResponse(**results)


@router.get("/optimize/{brochure_id}", response_model=OptimizeResponse)
async def get_optimization(
    brochure_id: int,
    industry: str = Query("", description="行业名称，用于关键词覆盖分析"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取名片优化建议

    分析名片信息的：
    - 完整度（字段填写完整程度）
    - 关键词覆盖（行业术语覆盖率）
    - 专业度评分（文案质量和专业程度）
    """
    # 获取画册信息
    result = await db.execute(select(Brochure).where(Brochure.id == brochure_id))
    brochure = result.scalars().first()

    if brochure is None:
        raise HTTPException(status_code=404, detail="画册不存在")

    if brochure.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此画册")

    # 从画册数据中提取字段信息
    fields = {}
    if brochure.album_meta:
        import json as json_mod
        try:
            meta = json_mod.loads(brochure.album_meta)
            # 尝试从 album_meta 中提取字段
            if isinstance(meta, dict):
                pages = meta.get("pages", [])
                for page in pages:
                    page_fields = page.get("fields", [])
                    for pf in page_fields:
                        if isinstance(pf, dict):
                            fields[pf.get("label", "")] = pf.get("value", "")
                    content = page.get("content", {})
                    if isinstance(content, dict):
                        fields.update(content)
        except (json_mod.JSONDecodeError, AttributeError):
            pass

    # 补充数据库中的字段
    fields.setdefault("name", brochure.title or "")

    # 获取优化建议
    suggestion = await OptimizationAnalyzer.get_optimization_suggestions(
        brochure_id=brochure_id,
        fields=fields,
        industry=industry,
    )

    return OptimizeResponse(**suggestion)
