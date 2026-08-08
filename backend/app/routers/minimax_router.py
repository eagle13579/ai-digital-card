"""MiniMax AI 多模态 API 路由 — 图片生成 + TTS + 健康检查"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from typing import Any
from pydantic import BaseModel
from app.middleware.rbac import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/minimax", tags=["minimax"])


# ── 请求模型 ────────────────────────────────────────────────────────

class ImageRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "1:1"
    n: int = 1


class TTSRequest(BaseModel):
    text: str
    voice_id: str = "male-qn-qingse"
    speed: float = 1.0


# ── 路由 ────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    """MiniMax API 配置健康检查"""
    from app.services.minimax_service import health as _health
    return _health()


@router.post("/image/generate")
async def generate_image(req: ImageRequest,
                         _perm: Any = Depends(require_permission("ai:generate"))):
    """生成图片"""
    from app.services.minimax_service import generate_image as _gen
    result = await _gen(prompt=req.prompt, aspect_ratio=req.aspect_ratio, n=req.n)
    if "error" in result and result.get("error"):
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@router.post("/tts/synthesize")
async def synthesize_speech(req: TTSRequest,
                            _perm: Any = Depends(require_permission("ai:generate"))):
    """文本转语音"""
    from app.services.minimax_service import synthesize_speech as _tts
    result = await _tts(text=req.text, voice_id=req.voice_id, speed=req.speed)
    if "error" in result and result.get("error"):
        raise HTTPException(status_code=502, detail=result["error"])
    return result
