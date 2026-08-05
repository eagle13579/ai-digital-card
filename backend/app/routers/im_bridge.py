"""
IM 桥接路由 — 企微 + 钉钉 消息推送 API。

路由:
  - GET  /api/im/status               — 查看各平台适配器状态
  - POST /api/im/send                 — 统一发送 (根据 platform 字段自动路由)
  - POST /api/im/wecom/send           — 发送到企微
  - POST /api/im/dingtalk/send        — 发送到钉钉
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.services.im_bridge import (
    IMPlatform,
    IMMessage,
    im_bridge,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/im", tags=["IM 桥接"])


# ── 状态查询 ─────────────────────────────────────────────────────────────────


@router.get("/status")
async def im_status():
    """查询所有 IM 平台适配器的状态"""
    adapters = im_bridge.list_adapters()
    return {
        "service": "im_bridge",
        "adapters": adapters,
        "total": len(adapters),
        "enabled": sum(1 for a in adapters if a["enabled"]),
    }


# ── 统一发送 ─────────────────────────────────────────────────────────────────


@router.post("/send")
async def im_send(payload: dict[str, Any]):
    """统一消息发送接口。

    Body:
      platform  (str)    — "wecom" | "dingtalk"
      user_id   (str)    — 目标用户 ID
      text      (str, optional)  — 文本内容
      title     (str, optional)  — 卡片标题
      buttons   (list, optional) — [{"label":"确认","url":"https://..."}]
    """
    platform = payload.get("platform", "").lower().strip()
    user_id = payload.get("user_id", "")
    if not platform:
        raise HTTPException(status_code=400, detail="缺少 platform 参数 (wecom/dingtalk)")
    if not user_id:
        raise HTTPException(status_code=400, detail="缺少 user_id 参数")

    msg = IMMessage(
        platform=IMPlatform(platform),
        user_id=user_id,
        text=payload.get("text", ""),
        title=payload.get("title", ""),
        card_data=payload.get("card_data", {}),
        buttons=payload.get("buttons", []),
    )
    result = await im_bridge.send(msg)
    logger.info("IM 发送结果: %s", result)
    return result


# ── 企微专用 ────────────────────────────────────────────────────────────────


@router.post("/wecom/send")
async def wecom_send(payload: dict[str, Any]):
    """发送消息到企业微信。

    Body:
      user_id   (str)             — 企微 UserID
      text      (str, optional)   — 文本内容
      title     (str, optional)   — 卡片标题
      buttons   (list, optional)  — 按钮列表
    """
    user_id = payload.get("user_id", "")
    if not user_id:
        raise HTTPException(status_code=400, detail="缺少 user_id 参数")

    msg = IMMessage(
        platform=IMPlatform.WECOM,
        user_id=user_id,
        text=payload.get("text", ""),
        title=payload.get("title", ""),
        card_data=payload.get("card_data", {}),
        buttons=payload.get("buttons", []),
    )
    result = await im_bridge.send(msg)
    logger.info("企微发送结果: %s", result)
    return result


# ── 钉钉专用 ────────────────────────────────────────────────────────────────


@router.post("/dingtalk/send")
async def dingtalk_send(payload: dict[str, Any]):
    """发送消息到钉钉。

    Body:
      user_id   (str)             — 钉钉 userId
      text      (str, optional)   — 文本内容
      title     (str, optional)   — 卡片标题
      buttons   (list, optional)  — 按钮列表
    """
    user_id = payload.get("user_id", "")
    if not user_id:
        raise HTTPException(status_code=400, detail="缺少 user_id 参数")

    msg = IMMessage(
        platform=IMPlatform.DINGTALK,
        user_id=user_id,
        text=payload.get("text", ""),
        title=payload.get("title", ""),
        card_data=payload.get("card_data", {}),
        buttons=payload.get("buttons", []),
    )
    result = await im_bridge.send(msg)
    logger.info("钉钉发送结果: %s", result)
    return result


# ── 健康检查 ─────────────────────────────────────────────────────────────────


@router.get("/health")
async def im_health():
    """IM 桥接模块健康检查"""
    return {"status": "ok", "service": "im_bridge", "adapters": im_bridge.list_adapters()}
