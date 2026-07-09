"""AI 代理端点 — 支持 DeepSeek 和飞书白泽双提供商"""
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

from app.config import settings
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.usage_service import record_token_usage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai/deepseek", tags=["AI 代理"])

# ── 常量 ──────────────────────────────────────────────────────────────
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
TIMEOUT_SEC = 10


def _use_feishu_baize() -> bool:
    """判断是否使用飞书白泽（飞书配置存在时优先使用）"""
    return bool(settings.FEISHU_APP_ID and settings.FEISHU_APP_SECRET)


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

async def _call_feishu_baize(messages: list[dict], temperature: float, max_tokens: int) -> dict:
    """调用飞书白泽 API"""
    from app.ai.gateway.adapters.feishu_baize_adapter import FeishuBaizeAdapter
    from app.ai.gateway.interfaces import AIRequest

    adapter = FeishuBaizeAdapter()
    ai_request = AIRequest(
        model=settings.FEISHU_BAIZE_DEFAULT_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    response = await adapter.chat(ai_request)
    return {
        "choices": [{
            "message": {"content": response.content},
            "finish_reason": response.finish_reason,
        }],
        "usage": response.usage,
        "model": response.model,
    }


@router.post("/chat", response_model=ChatResponse)
async def deepseek_chat(req: ChatRequest, current_user: User = Depends(get_current_user)):
    """调用 AI 进行多轮对话（飞书白泽优先，DeepSeek 降级）

    接收消息列表，通过 AI API 生成回复。
    优先使用飞书白泽（配置了 FEISHU_APP_ID 时），否则使用 DeepSeek。
    """
    if not req.messages:
        raise HTTPException(status_code=400, detail="消息列表不能为空")

    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    if _use_feishu_baize():
        try:
            data = await _call_feishu_baize(messages, req.temperature, req.max_tokens)
            reply = data["choices"][0]["message"]["content"]
            usage = data.get("usage")
            return ChatResponse(reply=reply, model=data.get("model", "baize-4k"), usage=usage)
        except Exception as e:
            logger.warning("飞书白泽调用失败，降级到 DeepSeek: %s", e)

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
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
    # 记录 token 消耗
    if usage:
        try:
            await record_token_usage(
                user_id=current_user.id,
                feature="ai_deepseek_chat",
                model_type="external",
                model_name=DEEPSEEK_MODEL,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )
        except Exception:
            logger.warning("Token用量记录失败（非阻断）")
    return ChatResponse(reply=reply, usage=usage)


@router.post("/generate", response_model=GenerateResponse)
async def deepseek_generate(req: GenerateRequest):
    """调用 AI 生成名片文案（飞书白泽优先，DeepSeek 降级）

    根据用户输入的 prompt 生成对应的文案内容。
    优先使用飞书白泽（配置了 FEISHU_APP_ID 时），否则使用 DeepSeek。
    """
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt 不能为空")

    messages = [
        {
            "role": "system",
            "content": "你是一个专业的名片文案撰写助手。请根据用户需求生成简洁、专业、有吸引力的名片文案。",
        },
        {"role": "user", "content": req.prompt},
    ]

    if _use_feishu_baize():
        try:
            data = await _call_feishu_baize(messages, req.temperature, req.max_tokens)
            content = data["choices"][0]["message"]["content"]
            return GenerateResponse(content=content, model=data.get("model", "baize-4k"))
        except Exception as e:
            logger.warning("飞书白泽调用失败，降级到 DeepSeek: %s", e)

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
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


async def _check_feishu_status() -> dict:
    """检查飞书白泽 API 状态"""
    if not settings.FEISHU_APP_ID or not settings.FEISHU_APP_SECRET:
        return {"status": "error", "configured": False, "message": "FEISHU_APP_ID/FEISHU_APP_SECRET 未配置"}

    from app.ai.gateway.adapters.feishu_baize_adapter import FeishuBaizeAdapter

    try:
        adapter = FeishuBaizeAdapter()
        await adapter._ensure_token()
        return {"status": "ok", "configured": True, "message": "飞书白泽 API 连接正常"}
    except Exception as e:
        return {"status": "error", "configured": False, "message": f"飞书白泽认证失败: {str(e)}"}


@router.get("/status", response_model=StatusResponse)
async def deepseek_status():
    """检查 AI API 状态（飞书白泽优先）

    检查当前配置的 AI 提供商状态。
    优先使用飞书白泽（配置了 FEISHU_APP_ID 时），否则使用 DeepSeek。
    """
    if _use_feishu_baize():
        result = await _check_feishu_status()
        return StatusResponse(**result)

    api_key = _get_api_key()
    if not api_key:
        return StatusResponse(
            status="error",
            configured=False,
            message="DEEPSEEK_API_KEY 未配置，请在 .env 文件中设置",
        )

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
