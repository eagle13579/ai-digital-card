"""AI名片/画册内容生成服务 — 根据用户输入/名片OCR自动生成精美画册。

使用 ModelRegistry（DeepSeek → Cache → Ollama 降级链）而非直接调用 DeepSeek API。
"""

import json
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# ── 模板风格配置 ──────────────────────────────────────────────────────────

TEMPLATE_STYLES = {
    "professional": {
        "name": "专业商务",
        "description": "简洁大方的专业商务风格",
        "theme": {
            "primary": "#2563eb",
            "secondary": "#1d4ed8",
            "gradient": "linear-gradient(135deg, #2563eb, #1d4ed8)",
            "bg_start": "#0a0f1a",
            "bg_mid": "#1a2332",
            "bg_end": "#0e121f",
            "accent": "rgba(37,99,235,0.15)",
        },
    },
    "creative": {
        "name": "创意设计",
        "description": "富有创意与个性的设计风格",
        "theme": {
            "primary": "#ec4899",
            "secondary": "#f43f5e",
            "gradient": "linear-gradient(135deg, #ec4899, #f43f5e)",
            "bg_start": "#1a0a1e",
            "bg_mid": "#2d1b3a",
            "bg_end": "#1a0f1e",
            "accent": "rgba(236,72,153,0.15)",
        },
    },
    "minimal": {
        "name": "极简主义",
        "description": "干净清爽的极简风格",
        "theme": {
            "primary": "#64748b",
            "secondary": "#475569",
            "gradient": "linear-gradient(135deg, #64748b, #475569)",
            "bg_start": "#0f1117",
            "bg_mid": "#1e2028",
            "bg_end": "#111318",
            "accent": "rgba(100,116,139,0.15)",
        },
    },
    "tech": {
        "name": "科技感",
        "description": "前沿科技的视觉风格",
        "theme": {
            "primary": "#06b6d4",
            "secondary": "#0891b2",
            "gradient": "linear-gradient(135deg, #06b6d4, #0891b2)",
            "bg_start": "#0a121a",
            "bg_mid": "#162230",
            "bg_end": "#0e141f",
            "accent": "rgba(6,182,212,0.15)",
        },
    },
}


def _build_system_prompt_for_contact() -> str:
    return (
        "你是一个专业的名片/画册内容生成助手。根据用户提供的联系信息，"
        "生成一份精美的电子名片或画册内容。"
        "请严格按照 JSON 格式输出，不要包含其他说明文字。\n\n"
        "输出格式:\n"
        "{\n"
        '  "title": "画册标题 (简短有力)",\n'
        '  "pages": [\n'
        "    {\"type\": \"cover\", \"content\": \"封面文案\", \"style\": \"centered\"},\n"
        "    {\"type\": \"text\", \"content\": \"正文内容\", \"style\": \"card\"},\n"
        "    {\"type\": \"contact\", \"content\": \"联系方式文案\", \"style\": \"compact\"}\n"
        "  ],\n"
        '  "tags": ["标签1", "标签2"],\n'
        '  "suggested_template": "professional|creative|minimal|tech"\n'
        "}"
    )


def _build_system_prompt_for_brief(template: str) -> str:
    style_desc = TEMPLATE_STYLES.get(template, TEMPLATE_STYLES["professional"])
    return (
        f"你是一个专业的画册内容生成助手。根据用户的一句话简介，"
        f"生成多页精美画册内容。风格：{style_desc['name']}。\n\n"
        "请严格按照 JSON 格式输出一个数组，不要包含其他说明文字。\n\n"
        "输出格式:\n"
        "[\n"
        "  {\"title\": \"页面标题 (带 emoji)\", \"content\": \"页面内容（详细、有吸引力）\", "
        '"layout": "cover|text|split|image", "icon": "📝"},\n'
        "  ...\n"
        "]"
    )


def _build_system_prompt_for_enhance() -> str:
    return (
        "你是一个专业的画册内容增强助手。分析已有画册的内容，"
        "补充AI生成的优化建议、标签推荐和内容改进方案。"
        "请严格按照 JSON 格式输出，不要包含其他说明文字。\n\n"
        "输出格式:\n"
        "{\n"
        '  "suggestions": [{"field": "title", "suggestion": "建议标题"}],\n'
        '  "tags": ["推荐标签"],\n'
        '  "summary": "画册内容总结",\n'
        '  "missing_sections": ["建议补充的章节"]\n'
        "}"
    )


class BrochureGenerationService:
    """基于用户输入的画册/名片内容自动生成服务"""

    def __init__(self) -> None:
        self._registry: Any = None

    async def _get_registry(self) -> Any:
        """Lazy-init ModelRegistry with fallback chain."""
        if self._registry is None:
            from app.ai.gateway.model_registry import ModelRegistry

            self._registry = ModelRegistry(
                deepseek_api_key=settings.DEEPSEEK_API_KEY,
                deepseek_base_url=settings.DEEPSEEK_API_URL,
            )
        return self._registry

    async def _call_ai(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str | None:
        """通过 ModelRegistry 调用 AI（带降级链）。"""
        try:
            from app.ai.gateway.interfaces import AIRequest

            registry = await self._get_registry()
            request = AIRequest(
                model="deepseek-chat",
                prompt=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            response, provider = await registry.route(request)
            logger.info(
                "BrochureGenerationService: served by '%s' provider", provider
            )
            return response.content.strip()
        except Exception as exc:
            logger.warning(
                "BrochureGenerationService: all AI providers failed: %s", exc
            )
            return None

    async def generate_from_contact(self, contact_info: dict) -> dict:
        """从联系人信息生成名片/画册。

        Args:
            contact_info: {name, title, company, phone, email, wechat, skills, intro}

        Returns:
            {title, pages: [{type, content, style}], tags, suggested_template}
        """
        system_prompt = _build_system_prompt_for_contact()
        user_message = (
            "请根据以下联系人信息生成一份电子名片/画册内容：\n\n"
            f"姓名：{contact_info.get('name', '')}\n"
            f"职位：{contact_info.get('title', '')}\n"
            f"公司：{contact_info.get('company', '')}\n"
            f"电话：{contact_info.get('phone', '')}\n"
            f"邮箱：{contact_info.get('email', '')}\n"
            f"微信：{contact_info.get('wechat', '')}\n"
            f"技能：{contact_info.get('skills', '')}\n"
            f"简介：{contact_info.get('intro', '')}\n"
        )

        raw = await self._call_ai(system_prompt, user_message)
        if raw:
            try:
                # Try to extract JSON from markdown code block if present
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0].strip()
                result = json.loads(raw)
                return self._validate_generated_contact(result, contact_info)
            except (json.JSONDecodeError, KeyError) as exc:
                logger.warning("Failed to parse AI response as JSON: %s", exc)

        # Fallback: 根据联系人信息生成默认画册内容
        return self._fallback_contact(contact_info)

    async def generate_pages_from_brief(
        self, brief: str, template: str = "professional"
    ) -> list[dict]:
        """从一句话简介生成多页画册。

        Args:
            brief: 用户的一句话介绍（如："我是AI创业者，专注企业智能解决方案"）
            template: 模板风格 (professional/creative/minimal/tech)

        Returns:
            [{title, content, layout, icon}] 多页画册内容
        """
        if template not in TEMPLATE_STYLES:
            template = "professional"

        system_prompt = _build_system_prompt_for_brief(template)
        user_message = f"请根据以下一句话简介生成一份精美的多页画册内容：\n\n{brief}"

        raw = await self._call_ai(system_prompt, user_message)
        if raw:
            try:
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0].strip()
                result = json.loads(raw)
                if isinstance(result, list):
                    return self._validate_generated_pages(result, brief)
            except (json.JSONDecodeError, KeyError) as exc:
                logger.warning("Failed to parse AI response as JSON: %s", exc)

        # Fallback
        return self._fallback_pages(brief, template)

    async def enhance_existing_brochure(self, brochure_id: int) -> list[dict]:
        """增强已有画册内容（AI补充描述/标签/建议）。

        Args:
            brochure_id: 画册 ID

        Returns:
            [{"field": ..., "suggestion": ..., "tags": [...], ...}]
        """
        # 尝试从数据库读取画册信息
        brochure_info = ""
        try:
            from app.database import AsyncSessionLocal
            from app.models.brochure import Brochure, Page
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Brochure)
                    .options(selectinload(Brochure.pages))
                    .where(Brochure.id == brochure_id)
                )
                brochure = result.scalars().first()
                if brochure:
                    pages_text = "\n".join(
                        f"  - [{p.content_type}] {p.content[:100]}"
                        for p in (brochure.pages or [])
                    )
                    brochure_info = (
                        f"标题：{brochure.title}\n"
                        f"封面：{brochure.cover}\n"
                        f"用途：{brochure.purpose}\n"
                        f"页面数：{brochure.pages_count}\n"
                        f"页面内容：\n{pages_text}"
                    )
        except Exception as exc:
            logger.warning(
                "Failed to load brochure %d from DB: %s", brochure_id, exc
            )
            brochure_info = f"画册ID: {brochure_id}"

        system_prompt = _build_system_prompt_for_enhance()
        user_message = f"请分析以下画册内容，给出优化建议：\n\n{brochure_info}"

        raw = await self._call_ai(system_prompt, user_message)
        if raw:
            try:
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0].strip()
                result = json.loads(raw)
                if isinstance(result, dict):
                    return [result]
            except (json.JSONDecodeError, KeyError) as exc:
                logger.warning("Failed to parse AI response as JSON: %s", exc)

        return [
            {
                "suggestions": [],
                "tags": [],
                "summary": "无法生成增强建议（AI服务不可用）",
                "missing_sections": [],
            }
        ]

    # ── 校验与兜底 ──────────────────────────────────────────────────

    def _validate_generated_contact(self, result: dict, contact_info: dict) -> dict:
        """确保返回结构完整。"""
        if not isinstance(result.get("pages"), list):
            result["pages"] = []
        if not result.get("title"):
            result["title"] = f"{contact_info.get('name', '名片')}的名片"
        if not result.get("tags"):
            result["tags"] = [contact_info.get("title", ""), contact_info.get("company", "")]
            result["tags"] = [t for t in result["tags"] if t]
        if not result.get("suggested_template"):
            result["suggested_template"] = "professional"
        return result

    def _validate_generated_pages(self, pages: list[dict], brief: str) -> list[dict]:
        """确保每页结构完整。"""
        validated = []
        for page in pages:
            validated.append({
                "title": page.get("title", "页面"),
                "content": page.get("content", brief),
                "layout": page.get("layout", "text"),
                "icon": page.get("icon", "📄"),
            })
        if not validated:
            validated = self._fallback_pages(brief, "professional")
        return validated

    def _fallback_contact(self, contact_info: dict) -> dict:
        """AI 不可用时的兜底名片生成。"""
        name = contact_info.get("name", "联系人")
        title = contact_info.get("title", "")
        company = contact_info.get("company", "")
        intro = contact_info.get("intro", "")

        pages = [
            {
                "type": "cover",
                "content": f"{name}\n{title}" if title else name,
                "style": "centered",
            },
        ]
        if intro:
            pages.append({
                "type": "text",
                "content": intro,
                "style": "card",
            })
        if company or title:
            comp_text = f"就职于 {company}" if company else ""
            pages.append({
                "type": "text",
                "content": f"{title} {comp_text}".strip(),
                "style": "card",
            })
        pages.append({
            "type": "contact",
            "content": f"📞 {contact_info.get('phone', '')}　✉️ {contact_info.get('email', '')}"
            if contact_info.get("phone") or contact_info.get("email")
            else "联系方式",
            "style": "compact",
        })

        return {
            "title": f"{name}的名片",
            "pages": pages,
            "tags": [t for t in [title, company] if t],
            "suggested_template": "professional",
        }

    def _fallback_pages(self, brief: str, template: str) -> list[dict]:
        """AI 不可用时的兜底画册页面生成。"""
        theme = TEMPLATE_STYLES.get(template, TEMPLATE_STYLES["professional"])
        return [
            {
                "title": f"{theme['name']}封面",
                "content": brief,
                "layout": "cover",
                "icon": "🎨",
            },
            {
                "title": "💡 关于我",
                "content": f"{brief}\n\n致力于通过创新技术与专业服务，为客户创造最大价值。",
                "layout": "text",
                "icon": "💡",
            },
            {
                "title": "📋 核心优势",
                "content": "• 丰富的行业经验\n• 专业的技术能力\n• 良好的客户口碑\n• 高效的交付能力",
                "layout": "split",
                "icon": "⭐",
            },
            {
                "title": "📱 联系我",
                "content": "期待与您合作！\n\n欢迎通过画册上的联系方式与我取得联系。",
                "layout": "text",
                "icon": "📞",
            },
        ]
