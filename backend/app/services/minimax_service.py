"""
MiniMax API Service — 多模态AI能力封装层

提供 MiniMax 图片生成、TTS语音合成、文档管线能力的统一服务接口。
参考 MiniMax-AI/skills (frontend-dev + minimax-multimodal-toolkit) 封装。

使用前需配置环境变量:
  MINIMAX_API_KEY=<your_key>
  MINIMAX_API_BASE=https://api.minimaxi.com  (或 https://api.minimax.io)
"""

from __future__ import annotations

import io
import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


# ── 配置 ────────────────────────────────────────────────────────────

@dataclass
class MiniMaxConfig:
    """MiniMax API 配置"""
    api_key: str = os.getenv("MINIMAX_API_KEY", "")
    api_base: str = os.getenv("MINIMAX_API_BASE", "https://api.minimaxi.com")
    image_model: str = "image-01"
    tts_model: str = "speech-2.8-hd"
    tts_default_voice: str = "male-qn-qingse"


def _get_config() -> MiniMaxConfig:
    config = MiniMaxConfig()
    if not config.api_key:
        logger.warning("MINIMAX_API_KEY 未设置 — MiniMax API 不可用")
    return config


# ── 图片生成 ────────────────────────────────────────────────────────

async def generate_image(
    prompt: str,
    aspect_ratio: str = "1:1",
    n: int = 1,
    model: str = None,
    seed: int = None,
) -> dict:
    """生成图片

    Args:
        prompt: 图片描述文本
        aspect_ratio: 宽高比 (1:1, 16:9, 4:3, 3:2, 2:3, 3:4, 9:16, 21:9)
        n: 生成数量
        model: 模型名 (默认 image-01)
        seed: 随机种子 (用于复现)

    Returns:
        {"images": [{"url": str, "b64_json": str|null}], "model": str}
    """
    import httpx

    config = _get_config()
    if not config.api_key:
        return {"error": "MINIMAX_API_KEY 未配置", "images": []}

    payload = {
        "model": model or config.image_model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "n": n,
        "response_format": "url",
        "prompt_optimizer": True,
    }
    if seed is not None:
        payload["seed"] = seed

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{config.api_base}/v1/image_generation",
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            images = [
                {"url": img.get("url", ""), "b64_json": img.get("b64_json")}
                for img in data.get("data", [])
            ]
            return {"images": images, "model": payload["model"]}
    except Exception as e:
        logger.error("MiniMax 图片生成失败: %s", e)
        return {"error": str(e), "images": []}


# ── TTS 语音合成 ────────────────────────────────────────────────────

async def synthesize_speech(
    text: str,
    voice_id: str = None,
    speed: float = 1.0,
    volume: float = 1.0,
    pitch: int = 0,
    fmt: str = "mp3",
    model: str = None,
) -> dict:
    """文本转语音

    Args:
        text: 要合成的文本
        voice_id: 音色ID (默认 male-qn-qingse)
        speed: 语速 0.5-2.0
        volume: 音量 0.1-2.0
        pitch: 音调 -12 到 +12
        fmt: 输出格式 (mp3, wav, pcm)
        model: 模型名 (默认 speech-2.8-hd)

    Returns:
        {"audio_url": str|null, "audio_bytes": bytes|null, "error": str|null}
    """
    import httpx

    config = _get_config()
    if not config.api_key:
        return {"error": "MINIMAX_API_KEY 未配置", "audio_url": None, "audio_bytes": None}

    voice_id = voice_id or config.tts_default_voice
    payload = {
        "model": model or config.tts_model,
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "vol": volume,
            "pitch": pitch,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": fmt,
            "channel": 1,
        },
        "language_boost": "auto",
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{config.api_base}/v1/t2a_v2",
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            audio_bytes = resp.content
            return {"audio_url": None, "audio_bytes": audio_bytes, "error": None}
    except Exception as e:
        logger.error("MiniMax TTS 失败: %s", e)
        return {"error": str(e), "audio_url": None, "audio_bytes": None}


# ── 健康检查 ─────────────────────────────────────────────────────────

def health() -> dict:
    """检查 MiniMax API 配置状态"""
    config = _get_config()
    return {
        "configured": bool(config.api_key),
        "api_base": config.api_base,
        "has_key": bool(config.api_key),
        "status": "ok" if config.api_key else "missing_api_key",
    }
