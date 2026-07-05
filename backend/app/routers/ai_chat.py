"""AI 对话聊天 API — RAG 会话接口"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI 对话"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""
    stream: bool = False


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(req: ChatRequest):
    """AI 智能对话 — 基于 RAG 的知识问答"""
    try:
        from app.ai.rag_pipeline import RAGPipeline
        rag = RAGPipeline()
        reply = await rag.answer(req.message, req.session_id)
        return ChatResponse(reply=reply, session_id=req.session_id or "new")
    except ImportError:
        logger.warning("RAGPipeline 未加载，使用降级回复")
        return ChatResponse(
            reply=f"这是AI智能对话的测试回复。您的问题是: {req.message}\n\n（当前为降级模式，完整AI功能需配置 DeepSeek API Key）",
            session_id=req.session_id or "new",
        )
    except Exception as e:
        logger.error("AI对话异常: %s", e)
        raise HTTPException(status_code=500, detail=f"AI服务暂不可用: {str(e)}")
