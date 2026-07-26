"""
MiniMax API Service — 多模态AI能力封装层

优先级链路 (零成本优先):
  1. 本地免费服务 http://localhost:5100 (Windows) / http://192.168.1.233:5100 (Mac Mini)
  2. edge-tts (TTS专用, 免费, 无API Key)
  3. MiniMax API (需 MINIMAX_API_KEY, 付费回退)

环境变量:
  MINIMAX_API_KEY=<your_key>
  MINIMAX_API_BASE=https://api.minimaxi.com
  LOCAL_MEDIA_SERVER=http://localhost:5100  (可选覆盖)
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ── 本地服务地址 ─────────────────────────────────────────────────────
LOCAL_SERVICE_URLS = [
    os.getenv("LOCAL_MEDIA_SERVER", "http://localhost:5100"),
    "http://192.168.1.233:5100",
]

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


# ── 提供商自动检测 (惰性初始化) ─────────────────────────────────────

_have_edge_tts: Optional[bool] = None
_local_server_url: str = ""
_local_server_ok: bool = False


def _check_edge_tts() -> bool:
    global _have_edge_tts
    if _have_edge_tts is not None:
        return _have_edge_tts
    try:
        import edge_tts  # noqa: F401
        _have_edge_tts = True
        logger.info("edge-tts 可用 (免费TTS)")
    except ImportError:
        _have_edge_tts = False
        logger.info("edge-tts 不可用 (pip install edge-tts 可启用免费TTS)")
    return _have_edge_tts


async def _check_local_server() -> str:
    """检查本地媒体服务是否可用，返回可用URL或空字符串"""
    global _local_server_url, _local_server_ok
    if _local_server_ok and _local_server_url:
        return _local_server_url

    import httpx

    for url in LOCAL_SERVICE_URLS:
        try:
            async with httpx.AsyncClient(timeout=2) as c:
                r = await c.get(f"{url}/api/v1/minimax/health")
                if r.status_code == 200:
                    _local_server_url = url
                    _local_server_ok = True
                    logger.info("发现本地媒体服务: %s", url)
                    return url
        except Exception:
            continue

    logger.warning("本地媒体服务不可用 (检查 localhost:5100 / 192.168.1.233:5100)")
    return ""


async def _ensure_providers():
    """确保提供商状态已初始化"""
    _check_edge_tts()
    await _check_local_server()


# ── 图片生成 ────────────────────────────────────────────────────────


async def generate_image(
    prompt: str,
    aspect_ratio: str = "1:1",
    n: int = 1,
    model: str = None,
    seed: int = None,
) -> dict:
    """生成图片

    优先级: 本地服务 → MiniMax API (付费回退)

    Args:
        prompt: 图片描述文本
        aspect_ratio: 宽高比 (1:1, 16:9, 4:3, 3:2, 2:3, 3:4, 9:16, 21:9)
        n: 生成数量
        model: 模型名 (默认 image-01)
        seed: 随机种子 (用于复现)

    Returns:
        {"images": [{"url": str, "b64_json": str|null}], "model": str, "source": str}
    """
    # ── 方案1: 本地服务 (免费) ──
    local_url = await _check_local_server()
    if local_url:
        import httpx

        try:
            payload = {"prompt": prompt, "aspect_ratio": aspect_ratio, "n": n}
            async with httpx.AsyncClient(timeout=60) as c:
                resp = await c.post(
                    f"{local_url}/api/v1/minimax/image/generate",
                    json=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    images = data.get("images", [])
                    if images:
                        logger.info("本地服务图片生成成功: %s", prompt[:50])
                        return {
                            "images": images,
                            "model": "local-service (免费)",
                            "source": "local",
                        }
                    # 本地服务返回了错误，降级
                    err_msg = data.get("error", "本地服务返回空结果")
                    logger.warning("本地服务图片生成失败: %s", err_msg)
                else:
                    logger.warning(
                        "本地服务返回 %s: %s", resp.status_code, resp.text[:200]
                    )
        except Exception as e:
            logger.warning("本地服务图片生成异常: %s", e)

    # ── 方案2: MiniMax API (付费回退) ──
    config = _get_config()
    if config.api_key:
        import httpx

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
                logger.info("MiniMax API 图片生成成功: %s", prompt[:50])
                return {"images": images, "model": payload["model"], "source": "minimax"}
        except Exception as e:
            logger.error("MiniMax 图片生成失败: %s", e)
            return {"error": str(e), "images": [], "model": None, "source": None}

    return {"error": "无可用图片生成服务", "images": [], "model": None, "source": None}


# ── TTS 语音合成 ────────────────────────────────────────────────────


async def _edge_tts_impl(text: str, voice: str) -> dict:
    """使用 edge-tts 合成语音 (免费, 无API Key)"""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return {"audio_bytes": audio_bytes, "error": None, "source": "edge-tts"}


async def _local_tts(text: str, voice: str, speed: float) -> dict:
    """通过本地服务合成语音"""
    local_url = await _check_local_server()
    if not local_url:
        return {"audio_bytes": None, "error": "本地服务不可用", "source": None}

    import httpx

    payload = {"text": text, "voice_id": voice, "speed": speed}
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            resp = await c.post(
                f"{local_url}/api/v1/minimax/tts/synthesize",
                json=payload,
            )
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                if "audio" in content_type or resp.status_code == 200:
                    audio_bytes = resp.content
                    if audio_bytes and len(audio_bytes) > 100:
                        logger.info("本地服务TTS成功: %s bytes", len(audio_bytes))
                        return {
                            "audio_bytes": audio_bytes,
                            "error": None,
                            "source": "local",
                        }
                # JSON response with error
                data = resp.json()
                return {
                    "audio_bytes": None,
                    "error": data.get("error", "本地服务TTS返回异常"),
                    "source": None,
                }
            return {
                "audio_bytes": None,
                "error": f"本地服务返回 {resp.status_code}",
                "source": None,
            }
    except Exception as e:
        return {"audio_bytes": None, "error": str(e), "source": None}


async def _minimax_tts_impl(
    text: str, voice_id: str, speed: float, volume: float, pitch: int, fmt: str, model: str
) -> dict:
    """MiniMax API TTS (付费回退)"""
    config = _get_config()
    if not config.api_key:
        return {
            "error": "MINIMAX_API_KEY 未配置",
            "audio_url": None,
            "audio_bytes": None,
            "source": None,
        }

    import httpx

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
            logger.info("MiniMax TTS成功: %s bytes", len(audio_bytes))
            return {
                "audio_url": None,
                "audio_bytes": audio_bytes,
                "error": None,
                "source": "minimax",
            }
    except Exception as e:
        logger.error("MiniMax TTS 失败: %s", e)
        return {"error": str(e), "audio_url": None, "audio_bytes": None, "source": None}


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

    优先级: 本地服务 → edge-tts (免费) → MiniMax API (付费回退)

    Args:
        text: 要合成的文本
        voice_id: 音色ID (默认 male-qn-qingse, edge-tts默认 zh-CN-XiaoxiaoNeural)
        speed: 语速 0.5-2.0
        volume: 音量 0.1-2.0
        pitch: 音调 -12 到 +12
        fmt: 输出格式 (mp3, wav, pcm)
        model: 模型名 (默认 speech-2.8-hd)

    Returns:
        {"audio_url": str|null, "audio_bytes": bytes|null, "error": str|null, "source": str}
    """
    if not text:
        return {"error": "text 不能为空", "audio_url": None, "audio_bytes": None, "source": None}

    # ── 方案1: 本地服务 (免费) ──
    result = await _local_tts(text, voice_id or "male-qn-qingse", speed)
    if result.get("audio_bytes"):
        return {
            "audio_url": None,
            "audio_bytes": result["audio_bytes"],
            "error": None,
            "source": result.get("source", "local"),
        }

    # ── 方案2: edge-tts (免费, 无API Key) ──
    if _check_edge_tts():
        try:
            # edge-tts 用中文音色; 如果调用方指定了 voice_id 则用它
            edge_voice = voice_id or "zh-CN-XiaoxiaoNeural"
            edge_result = await _edge_tts_impl(text, edge_voice)
            if edge_result.get("audio_bytes"):
                logger.info("edge-tts TTS成功: %s bytes", len(edge_result["audio_bytes"]))
                return {
                    "audio_url": None,
                    "audio_bytes": edge_result["audio_bytes"],
                    "error": None,
                    "source": "edge-tts",
                }
        except Exception as e:
            logger.warning("edge-tts 失败: %s", e)

    # ── 方案3: MiniMax API (付费回退) ──
    return await _minimax_tts_impl(text, voice_id, speed, volume, pitch, fmt, model)


# ── 健康检查 ─────────────────────────────────────────────────────────


async def health() -> dict:
    """检查各提供商状态"""
    await _ensure_providers()
    config = _get_config()
    return {
        "configured": bool(config.api_key),
        "api_base": config.api_base,
        "has_key": bool(config.api_key),
        "status": "ok" if (config.api_key or _local_server_ok or _have_edge_tts) else "missing_api_key",
        "providers": {
            "local_server": _local_server_ok,
            "local_server_url": _local_server_url if _local_server_ok else None,
            "edge_tts": _have_edge_tts,
            "minimax_api": bool(config.api_key),
        },
        "active": "local-service" if _local_server_ok else ("edge-tts" if _have_edge_tts else ("minimax" if config.api_key else "none")),
    }
