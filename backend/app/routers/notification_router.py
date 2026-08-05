"""notification_router — 行业动态推送 API 端点

提供 POST /api/notification/push 用于手动触发推送。
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from notification.notification_service import (
    UnifiedPushService,
    PushMode,
    get_push_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notification", tags=["行业动态推送"])


# ── 请求 / 响应模型 ────────────────────────────────────────────────────


class PushModeParam(str, Enum):
    """API 接受的推送模式参数"""
    realtime = "realtime"
    scheduled = "scheduled"
    pull = "pull"


class PushRequest(BaseModel):
    """推送请求体"""
    mode: PushModeParam = Field(default=PushModeParam.realtime, description="推送模式: realtime / scheduled / pull")
    text: str = Field(..., min_length=1, max_length=10000, description="推送正文")
    subject: str = Field(default="", description="推送主题（选填，为空时自动生成）")
    channels: list[str] | None = Field(default=None, description="覆盖渠道列表（选填，为空时使用配置）")


class ChannelResult(BaseModel):
    mode: str
    method: str
    channel: str
    status: str
    message: str
    detail: dict[str, Any] = {}
    timestamp: str


class PushResponse(BaseModel):
    success: bool
    mode: str
    results: list[ChannelResult]
    total: int
    succeeded: int
    failed: int


# ── API 端点 ────────────────────────────────────────────────────────────


@router.post("/push", response_model=PushResponse)
async def push_notification(req: PushRequest):
    """手动触发行业动态推送。

    支持三种推送模式:
      - realtime: 实时推送（适合 API 请求时触发）
      - scheduled: 定时推送（适合每日摘要）
      - pull: 主动拉取（适合用户查看名片时触发）

    可通过 channels 参数覆盖配置中的渠道列表。
    """
    svc = get_push_service()

    # 映射 API 参数到内部枚举
    mode_map = {
        PushModeParam.realtime: PushMode.REALTIME,
        PushModeParam.scheduled: PushMode.SCHEDULED,
        PushModeParam.pull: PushMode.PULL,
    }
    mode = mode_map[req.mode]

    try:
        if req.mode == PushModeParam.realtime:
            results = svc.push_realtime(req.text, req.subject, req.channels)
        elif req.mode == PushModeParam.scheduled:
            results = svc.push_scheduled(req.text, req.subject, req.channels)
        else:
            results = svc.push_pull("api_trigger", req.text, req.subject, req.channels)
    except Exception as e:
        logger.exception("推送调用异常: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    channel_results = [
        ChannelResult(
            mode=r.mode.value,
            method=r.method,
            channel=r.channel,
            status=r.status,
            message=r.message,
            detail=r.detail,
            timestamp=r.timestamp,
        )
        for r in results
    ]

    succeeded = sum(1 for r in results if r.status == "ok")
    failed = len(results) - succeeded

    return PushResponse(
        success=failed == 0,
        mode=req.mode.value,
        results=channel_results,
        total=len(results),
        succeeded=succeeded,
        failed=failed,
    )
