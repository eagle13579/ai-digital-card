"""Zoom 日历会议集成服务。

基于 CalendarBase 实现 Zoom Meeting API 集成:
  - 创建/列出/更新/删除 Zoom 会议
  - 通过 OAuth 2.0 或 Server-to-Server OAuth 鉴权
  - 自动降级: 无 ZOOM_* 环境变量时仅记录日志
  - 关联 CRM 联系人（通过 contact_ids 参数）

配置（.env）:
    ZOOM_ACCOUNT_ID=xxx          # Server-to-Server OAuth
    ZOOM_CLIENT_ID=xxx
    ZOOM_CLIENT_SECRET=xxx
    # 或传统 JWT:
    ZOOM_API_KEY=xxx
    ZOOM_API_SECRET=xxx

使用示例:
    from app.services.calendar_zoom import zoom_calendar

    # 创建会议
    result = await zoom_calendar.create_event(
        user_id=123,
        title="产品演示 - 张三",
        start_time="2026-07-02T10:00:00",
        end_time="2026-07-02T11:00:00",
        description="演示AI数字名片新功能",
        contact_ids=[456, 789],
    )
    print(result.event.meeting_url)  # Zoom 入会链接

    # 列出会议
    result = await zoom_calendar.list_events(user_id=123)

    # 删除会议
    await zoom_calendar.delete_event("meeting_id_xxx")
"""

from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any

import httpx

from app.config import settings
from app.services.calendar_service import (
    CalendarBase,
    CalendarEvent,
    CalendarResult,
    register_calendar,
)

logger = logging.getLogger(__name__)

# ── Zoom API 常量 ────────────────────────────────────────────────────────────

ZOOM_API_BASE = "https://api.zoom.us/v2"
ZOOM_AUTH_URL = "https://zoom.us/oauth/token"
ZOOM_TOKEN_EXPIRE_BUFFER = 60  # Token 过期前 60 秒刷新


class ZoomCalendar(CalendarBase):
    """Zoom 日历会议集成服务。

    使用 Zoom Server-to-Server OAuth（推荐）或 JWT 鉴权。
    无配置时自动降级到日志输出。
    """

    def __init__(self) -> None:
        self._access_token: str = ""
        self._token_expires_at: float = 0.0
        self._s2s_oauth: bool = False
        super().__init__()

    # ── 平台标识 ────────────────────────────────────────────────────────────

    @property
    def _platform_name(self) -> str:
        return "Zoom"

    # ── 配置检查 ────────────────────────────────────────────────────────────

    def _check_config(self) -> bool:
        """检查 Zoom API 是否已配置。

        支持两种鉴权方式:
          1. Server-to-Server OAuth (推荐): ZOOM_ACCOUNT_ID + ZOOM_CLIENT_ID + ZOOM_CLIENT_SECRET
          2. JWT (传统): ZOOM_API_KEY + ZOOM_API_SECRET
        """
        if settings.ZOOM_ACCOUNT_ID and settings.ZOOM_CLIENT_ID and settings.ZOOM_CLIENT_SECRET:
            self._s2s_oauth = True
            logger.info(
                "Zoom 日历集成使用 Server-to-Server OAuth (account=%s)",
                settings.ZOOM_ACCOUNT_ID[:8] + "...",
            )
            return True
        if settings.ZOOM_API_KEY and settings.ZOOM_API_SECRET:
            self._s2s_oauth = False
            logger.info(
                "Zoom 日历集成使用 JWT 鉴权 (api_key=%s)",
                settings.ZOOM_API_KEY[:8] + "...",
            )
            return True
        return False

    # ── 鉴权 ────────────────────────────────────────────────────────────────

    async def _ensure_token(self) -> str:
        """获取或刷新 Zoom API Token。"""
        if self._access_token and time.time() < self._token_expires_at - ZOOM_TOKEN_EXPIRE_BUFFER:
            return self._access_token

        if self._s2s_oauth:
            return await self._get_s2s_token()
        else:
            return await self._get_jwt_token()

    async def _get_s2s_token(self) -> str:
        """获取 Server-to-Server OAuth Token。"""
        credentials = f"{settings.ZOOM_CLIENT_ID}:{settings.ZOOM_CLIENT_SECRET}"
        encoded = base64.b64encode(credentials.encode()).decode()

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                ZOOM_AUTH_URL,
                data={
                    "grant_type": "account_credentials",
                    "account_id": settings.ZOOM_ACCOUNT_ID,
                },
                headers={
                    "Authorization": f"Basic {encoded}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            resp.raise_for_status()
            body = resp.json()
            self._access_token = body["access_token"]
            self._token_expires_at = time.time() + body.get("expires_in", 3600)
            logger.debug("Zoom S2S OAuth token 已刷新")
            return self._access_token

    async def _get_jwt_token(self) -> str:
        """获取 JWT Token（传统方式，仅用于向后兼容）。"""
        import jwt as pyjwt

        payload = {
            "iss": settings.ZOOM_API_KEY,
            "exp": int(time.time()) + 3600,
        }
        token = pyjwt.encode(
            payload, settings.ZOOM_API_SECRET, algorithm="HS256"
        )
        self._access_token = token
        self._token_expires_at = time.time() + 3600
        logger.debug("Zoom JWT token 已生成")
        return token

    # ── HTTP 请求辅助 ───────────────────────────────────────────────────────

    async def _zoom_request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """发送 Zoom API 请求，自动处理 Token 刷新。"""
        token = await self._ensure_token()
        url = f"{ZOOM_API_BASE}{path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method=method, url=url, json=json_data, headers=headers
            )
            if resp.status_code == 401:
                # Token 可能过期，强制刷新后重试一次
                self._access_token = ""
                token = await self._ensure_token()
                headers["Authorization"] = f"Bearer {token}"
                resp = await client.request(
                    method=method, url=url, json=json_data, headers=headers
                )
            resp.raise_for_status()
            if resp.status_code == 204:
                return {}
            return resp.json()

    # ── 平台原生实现 ─────────────────────────────────────────────────────────

    async def _platform_list_events(
        self,
        user_id: int,
        *,
        start_time: str | None = None,
        end_time: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CalendarResult:
        """列出 Zoom 用户的所有会议（最近 30 天）。"""
        params: dict[str, Any] = {
            "page_size": min(page_size, 300),
            "page_number": page,
        }
        if start_time:
            params["from"] = start_time[:10]  # Zoom 接受 YYYY-MM-DD
        if end_time:
            params["to"] = end_time[:10]

        data = await self._zoom_request("GET", f"/users/me/meetings")
        meetings = data.get("meetings", [])

        events = []
        for m in meetings:
            event = self._zoom_meeting_to_event(m)
            event.owner_id = user_id
            events.append(event)

        return CalendarResult(
            success=True,
            events=events,
            total=data.get("total_records", len(events)),
            platform=self._platform_name,
        )

    async def _platform_create_event(
        self,
        user_id: int,
        title: str,
        start_time: str,
        end_time: str,
        *,
        description: str = "",
        timezone: str = "Asia/Shanghai",
        location: str = "",
        contact_ids: list[int] | None = None,
    ) -> CalendarResult:
        """在 Zoom 上创建一个新会议。"""
        # 计算时长（分钟）
        duration = self._compute_duration_minutes(start_time, end_time)

        body = {
            "topic": title,
            "type": 2,  # Scheduled meeting
            "start_time": start_time,
            "duration": duration,
            "timezone": timezone,
            "agenda": description[:2000] if description else "",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": True,
                "watermark": False,
                "approval_type": 0,  # Automatically approve
                "registration_type": 1,
                "audio": "both",
                "auto_recording": "none",
                "enforce_login": False,
            },
        }

        data = await self._zoom_request("POST", "/users/me/meetings", json_data=body)
        event = self._zoom_meeting_to_event(data)
        event.owner_id = user_id
        event.contact_ids = contact_ids or []

        return CalendarResult(
            success=True,
            event=event,
            platform=self._platform_name,
        )

    async def _platform_update_event(
        self,
        event_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        timezone: str | None = None,
        location: str | None = None,
        status: str | None = None,
    ) -> CalendarResult:
        """更新 Zoom 会议。"""
        # Zoom PATCH 只接受部分字段
        body: dict[str, Any] = {}
        if title is not None:
            body["topic"] = title
        if description is not None:
            body["agenda"] = description[:2000]
        if start_time is not None:
            body["start_time"] = start_time
        if end_time is not None and start_time is not None:
            body["duration"] = self._compute_duration_minutes(start_time, end_time)
        if timezone is not None:
            body["timezone"] = timezone
        if status is not None:
            if status == "cancelled":
                # Zoom 用 PATCH meetingId/status 取消会议
                await self._zoom_request(
                    "PUT", f"/meetings/{event_id}/status", json_data={"action": "end"}
                )
                return CalendarResult(
                    success=True, platform=self._platform_name
                )
            body["status"] = status

        if body:
            await self._zoom_request(
                "PATCH", f"/meetings/{event_id}", json_data=body
            )

        # 获取更新后的会议信息
        data = await self._zoom_request("GET", f"/meetings/{event_id}")
        event = self._zoom_meeting_to_event(data)

        return CalendarResult(
            success=True,
            event=event,
            platform=self._platform_name,
        )

    async def _platform_delete_event(self, event_id: str) -> CalendarResult:
        """删除 Zoom 会议。"""
        await self._zoom_request("DELETE", f"/meetings/{event_id}")
        return CalendarResult(
            success=True,
            platform=self._platform_name,
        )

    # ── 辅助方法 ────────────────────────────────────────────────────────────

    @staticmethod
    def _zoom_meeting_to_event(data: dict[str, Any]) -> CalendarEvent:
        """将 Zoom API 返回的会议数据转为 CalendarEvent。"""
        return CalendarEvent(
            id=str(data.get("id", "")),
            title=data.get("topic", ""),
            description=data.get("agenda", ""),
            start_time=data.get("start_time", ""),
            end_time=data.get("start_time", ""),  # Zoom 只有 start + duration
            timezone=data.get("timezone", "Asia/Shanghai"),
            location=data.get("location", ""),
            meeting_url=data.get("join_url", ""),
            meeting_id=str(data.get("id", "")),
            meeting_password=data.get("password", ""),
            status="scheduled",
            platform="zoom",
            raw=data,
        )

    @staticmethod
    def _compute_duration_minutes(start_time: str, end_time: str) -> int:
        """计算两个 ISO 时间之间的分钟数。"""
        from datetime import datetime as dt

        fmt = "%Y-%m-%dT%H:%M:%S"
        # 去掉时区后缀做简单解析
        start_clean = start_time.replace("Z", "").split("+")[0].split("-")[0]
        end_clean = end_time.replace("Z", "").split("+")[0].split("-")[0]
        # 如果只有日期，补时间
        if "T" not in start_clean:
            start_clean += "T00:00:00"
        if "T" not in end_clean:
            end_clean += "T00:00:00"

        try:
            s = dt.strptime(start_clean[:19], fmt)
            e = dt.strptime(end_clean[:19], fmt)
            return max(1, int((e - s).total_seconds() / 60))
        except ValueError:
            return 60  # 默认 1 小时


# ── 全局单例 ─────────────────────────────────────────────────────────────────

zoom_calendar = ZoomCalendar()
"""全局 Zoom 日历集成实例。直接 import 使用。"""

# 自动注册到注册表
register_calendar("zoom", zoom_calendar)
