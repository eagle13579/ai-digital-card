"""AI 对话聊天 API — 飞书白泽 AI 会话接口"""
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.usage_service import record_token_usage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI 对话"])


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ChatRequest(BaseModel):
    message: str = ""
    messages: list[ChatMessage] = []
    session_id: str = ""
    stream: bool = False
    temperature: float = 0.7
    max_tokens: int = 2048


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    model: str = "baize-4k"
    usage: dict = {}


def _get_feishu_adapter():
    from app.ai.gateway.adapters.feishu_baize_adapter import FeishuBaizeAdapter
    return FeishuBaizeAdapter()


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(req: ChatRequest, current_user: User = Depends(get_current_user)):
    """AI 智能对话 — 基于飞书白泽的知识问答"""
    if not req.message and not req.messages:
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    if not settings.FEISHU_APP_ID or not settings.FEISHU_APP_SECRET:
        raise HTTPException(status_code=502, detail="飞书配置未完成，请配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")

    try:
        adapter = _get_feishu_adapter()

        messages = []
        if req.message:
            messages.append({"role": "user", "content": req.message})
        else:
            messages.extend([{"role": m.role, "content": m.content} for m in req.messages])

        from app.ai.gateway.interfaces import AIRequest

        ai_request = AIRequest(
            model=settings.FEISHU_BAIZE_DEFAULT_MODEL,
            messages=messages,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            stream=req.stream,
        )

        if req.stream:
            async def generate():
                async for token in adapter.stream_chat(ai_request):
                    yield token

            return StreamingResponse(generate(), media_type="text/event-stream")

        response = await adapter.chat(ai_request)

        # 记录 token 消耗
        if response.usage and not req.stream:
            prompt = response.usage.get("prompt_tokens", 0)
            completion = response.usage.get("completion_tokens", 0)
            total = response.usage.get("total_tokens", prompt + completion)
            try:
                await record_token_usage(
                    user_id=current_user.id,
                    feature="ai_chat",
                    model_type="external",
                    model_name=response.model or "baize-4k",
                    prompt_tokens=prompt,
                    completion_tokens=completion,
                    total_tokens=total,
                )
            except Exception:
                logger.warning("Token用量记录失败（非阻断）", exc_info=True)

        return ChatResponse(
            reply=response.content,
            session_id=req.session_id or "new",
            model=response.model,
            usage=response.usage,
        )

    except Exception as e:
        logger.error("AI对话异常: %s", e)
        raise HTTPException(status_code=500, detail=f"AI服务暂不可用: {str(e)}")
