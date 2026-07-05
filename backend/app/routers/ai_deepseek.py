"""DeepSeek AI 代理端点 — 对话/生成/状态检查"""
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai/deepseek", tags=["DeepSeek AI"])

# ── 常量 ──────────────────────────────────────────────────────────────
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
TIMEOUT_SEC = 10


# ── 请求/响应模型 ──────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = []
    temperature: float = 0.7
    max_tokens: int = 2048


class ChatResponse(BaseModel):
    reply: str
    model: str = DEEPSEEK_MODEL
    usage: Optional[dict] = None


class GenerateRequest(BaseModel):
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 2048


class GenerateResponse(BaseModel):
    content: str
    model: str = DEEPSEEK_MODEL


class StatusResponse(BaseModel):
    status: str
    configured: bool
    message: str = ""


# ── 辅助函数 ──────────────────────────────────────────────────────────

def _get_api_key() -> str:
    """从配置获取 DeepSeek API Key（同时检查环境变量以支持 .env 来源）"""
    key = settings.DEEPSEEK_API_KEY or ""
    if not key:
        import os
        key = os.environ.get("DEEPSEEK_API_KEY", "")
    return key.strip()


async def _call_deepseek(payload: dict, timeout: int = TIMEOUT_SEC) -> dict:
    """调用 DeepSeek API 并返回原始 JSON 响应"""
    api_key = _get_api_key()
    if not api_key:
        raise HTTPException(status_code=502, detail="DeepSeek API Key 未配置")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(DEEPSEEK_CHAT_URL, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException:
            logger.error("DeepSeek API 请求超时")
            raise HTTPException(status_code=504, detail="DeepSeek API 请求超时，请稍后重试")
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            body = ""
            try:
                body = e.response.text
            except Exception:
                pass
            logger.error("DeepSeek API HTTP %s: %s", status, body)
            if status == 401:
                raise HTTPException(status_code=502, detail="DeepSeek API Key 认证失败")
            raise HTTPException(status_code=502, detail=f"DeepSeek API 请求失败 (HTTP {status})")
        except httpx.RequestError as e:
            logger.error("DeepSeek API 网络错误: %s", e)
            raise HTTPException(status_code=502, detail="无法连接到 DeepSeek API，请检查网络")


# ── API 端点 ──────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def deepseek_chat(req: ChatRequest):
    """调用 DeepSeek 进行多轮对话

    接收消息列表，通过 DeepSeek API 生成回复。
    """
    if not req.messages:
        raise HTTPException(status_code=400, detail="消息列表不能为空")

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": m.role, "content": m.content} for m in req.messages],
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
    }

    data = await _call_deepseek(payload)

    try:
        reply = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        logger.error("DeepSeek 响应格式异常: %s", data)
        raise HTTPException(status_code=502, detail="DeepSeek 响应格式异常")

    usage = data.get("usage")
    return ChatResponse(reply=reply, usage=usage)


@router.post("/generate", response_model=GenerateResponse)
async def deepseek_generate(req: GenerateRequest):
    """调用 DeepSeek 生成名片文案

    根据用户输入的 prompt 生成对应的文案内容。
    """
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt 不能为空")

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的名片文案撰写助手。请根据用户需求生成简洁、专业、有吸引力的名片文案。",
            },
            {"role": "user", "content": req.prompt},
        ],
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
    }

    data = await _call_deepseek(payload)

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        logger.error("DeepSeek 响应格式异常: %s", data)
        raise HTTPException(status_code=502, detail="DeepSeek 响应格式异常")

    return GenerateResponse(content=content)


@router.get("/status", response_model=StatusResponse)
async def deepseek_status():
    """检查 DeepSeek API Key 是否配置有效

    尝试用一个简单的请求验证 API Key 的有效性。
    """
    api_key = _get_api_key()
    if not api_key:
        return StatusResponse(
            status="error",
            configured=False,
            message="DEEPSEEK_API_KEY 未配置，请在 .env 文件中设置",
        )

    # 使用一个最小请求验证 key 有效性
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            resp = await client.post(DEEPSEEK_CHAT_URL, json=payload, headers=headers)
            resp.raise_for_status()
            return StatusResponse(status="ok", configured=True, message="DeepSeek API 连接正常")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return StatusResponse(
                    status="error", configured=False,
                    message="DEEPSEEK_API_KEY 认证失败，请检查 Key 是否正确",
                )
            return StatusResponse(
                status="degraded", configured=True,
                message=f"DeepSeek API 返回异常 (HTTP {e.response.status_code})",
            )
        except httpx.TimeoutException:
            return StatusResponse(
                status="degraded", configured=True,
                message="DeepSeek API 连接超时",
            )
        except httpx.RequestError as e:
            return StatusResponse(
                status="degraded", configured=True,
                message=f"无法连接到 DeepSeek API: {e}",
            )
