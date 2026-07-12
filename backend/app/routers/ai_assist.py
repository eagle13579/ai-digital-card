"""AI 助手 API — 文案生成与优化建议"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.writing_assistant import WritingAssistant
from app.ai.optimization import OptimizationAnalyzer
from app.database import get_db
from app.models.brochure import Brochure
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/ai", tags=["AI 助手"])


# ── 请求/响应模型 ──────────────────────────────────────────────────────


class WriteRequest(BaseModel):
    purpose: str = Field(
        ...,
        pattern=r"^(bio|company|recommendation|slogan)$",
        description="文案用途: bio=个人简介, company=公司介绍, recommendation=推荐语, slogan=名片标语",
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


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户输入的聊天消息")
    history: list[dict] = Field(default_factory=list, description="历史消息列表，每项 {role, content}")


class ChatResponse(BaseModel):
    reply: str
    type: str = "text"

    model_config = {"json_schema_extra": {
        "example": {
            "reply": "你好！我是AI数智名片助手，有什么可以帮助你的？",
            "type": "text",
        }
    }}


class OptimizeResponse(BaseModel):
    brochure_id: int
    overall_score: float
    completeness: dict
    keyword_coverage: dict
    professionalism: dict
    top_priorities: list[str]


# ── AI 对话（独立于文案生成）────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """AI 智能对话

    用户可以在名片场景中向 AI 助手提问，AI 根据上下文给出回复。
    支持名片制作建议、文案优化、访客分析等对话场景。

    当 DEEPSEEK_API_KEY 未配置时，使用规则匹配生成结构化回复。
    """
    from app.config import settings

    message = data.message.strip()
    history = data.history or []

    # 如果有 DeepSeek API Key，调用真实 LLM
    if settings.DEEPSEEK_API_KEY:
        try:
            import httpx

            # 构建对话历史
            messages = [{"role": "system", "content": "你是一个AI数智名片助手。你帮助用户生成名片文案、分析匹配度、提供访客数据洞察、推荐标签等。请用中文回答，简洁专业。"}]
            for msg in history:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
            messages.append({"role": "user", "content": message})

            from app.middleware.metrics import track_ai_inference

            async with httpx.AsyncClient(timeout=30) as client:
                with track_ai_inference(model_name="deepseek-chat"):
                    resp = await client.post(
                        settings.DEEPSEEK_API_URL,
                        headers={
                            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "deepseek-chat",
                            "messages": messages,
                            "max_tokens": 500,
                            "temperature": 0.7,
                        },
                    )
                    result = resp.json()
                    reply = result["choices"][0]["message"]["content"].strip()
                    return ChatResponse(reply=reply, type="text")
        except Exception as e:
            return ChatResponse(reply=f"【AI回复生成失败: {str(e)}，请稍后重试】", type="text")

    # ── 无 DeepSeek API Key — 规则匹配 fallback ─────────────────────────
    msg_lower = message.lower()

    # 名片/简介相关
    if any(kw in msg_lower for kw in ["名片", "简介", "介绍", "bio", "文案"]):
        reply = (
            "我可以帮您生成专业的名片文案！请提供以下信息：\n\n"
            "1️⃣ 您的姓名和职位\n"
            "2️⃣ 公司名称和行业\n"
            "3️⃣ 主要技能或业务描述\n"
            "4️⃣ 希望突出的亮点\n\n"
            "例如：\"我叫张三，是某科技公司的产品总监，擅长用户增长和数据分析\""
        )
        return ChatResponse(reply=reply, type="text")

    # 标签相关
    if any(kw in msg_lower for kw in ["标签", "关键词", "标签推荐", "tag"]):
        reply = (
            "根据您的信息，我推荐以下标签方向：\n\n"
            "🏷️ **职业标签**：产品经理 / 技术专家 / 市场总监\n"
            "🏷️ **能力标签**：用户增长 / 数据分析 / 战略规划\n"
            "🏷️ **行业标签**：互联网 / 金融科技 / 企业服务\n\n"
            "需要我进一步推荐具体标签吗？请告诉我您的行业和职位。"
        )
        return ChatResponse(reply=reply, type="text")

    # 匹配/合作伙伴
    if any(kw in msg_lower for kw in ["匹配", "合作", "伙伴", "推荐", "人脉"]):
        reply = (
            "我来帮您分析合作匹配度！请告诉我：\n\n"
            "🤝 您寻找什么样的合作伙伴？\n"
            "🎯 您的核心需求是什么？\n"
            "💼 您能提供什么资源或能力？\n\n"
            "我会根据您的信息推荐最匹配的人选。"
        )
        return ChatResponse(reply=reply, type="text")

    # 访客/数据
    if any(kw in msg_lower for kw in ["访客", "数据", "统计", "分析", "谁看过"]):
        reply = (
            "📊 **访客数据分析**\n\n"
            "我可以帮您分析名片的访客数据：\n"
            "• 谁浏览了您的名片\n"
            "• 访客的行业分布\n"
            "• 热门浏览时段\n"
            "• 访客转化建议\n\n"
            "请前往「访客统计」页面查看详细数据，或告诉我您想了解的具体问题。"
        )
        return ChatResponse(reply=reply, type="text")

    # 默认回复
    reply = (
        "🤖 **您好！我是AI数智名片助手**\n\n"
        "我可以帮您：\n\n"
        "✍️ **生成文案** - 名片简介、公司介绍、推荐语、品牌标语\n"
        "🏷️ **推荐标签** - 根据职业和行业智能推荐标签\n"
        "🎯 **合作匹配** - 分析潜在合作伙伴匹配度\n"
        "📊 **访客洞察** - 分析名片访客数据\n\n"
        "请告诉我您的需求，我来帮助您！"
    )
    return ChatResponse(reply=reply, type="text")


# ── API 端点 ──────────────────────────────────────────────────────────


@router.post("/write", response_model=WriteResponse)
async def generate_copy(
    data: WriteRequest,
    current_user: User = Depends(get_current_user),
):
    """生成名片文案

    根据用途和参数生成对应的名片文案。
    支持四种用途：
    - bio: 个人简介
    - company: 公司介绍
    - recommendation: 推荐语
    - slogan: 名片标语
    """
    content = await WritingAssistant.generate(
        purpose=data.purpose,
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
