"""腾讯会议日历会议集成服务。

基于 CalendarBase 实现腾讯会议 API 集成:
  - 创建/列出/更新/删除腾讯会议
  - 使用腾讯会议 OAuth 2.0 鉴权（JWT 签名）
  - 自动降级: 无 TENCENT_* 环境变量时仅记录日志
  - 关联 CRM 联系人（通过 contact_ids 参数）

配置（.env）:
    TENCENT_MEETING_APP_ID=***
    TENCENT_MEETING_SDK_ID=***
    TENCENT_MEETING_SECRET=***

注意: 腾讯会议 API 使用 JWT 签名方式鉴权，每个请求都需要
动态生成签名令牌，不需要长期 access_token。

使用示例:
    from app.services.calendar_tencent import tencent_calendar

    # 创建会议
    result = await tencent_calendar.create_event(
        user_id=123,
        title="客户需求沟通",
        start_time="2026-07-02T14:00:00",
        end_time="2026-07-02T15:00:00",
        contact_ids=[456, 789],
    )
    print(result.event.meeting_url)  # 腾讯会议入会链接

    # 列出会议
    result = await tencent_calendar.list_events(user_id=123)

    # 删除会议
    await tencent_calendar.delete_event("meeting_id_xxx")
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import uuid
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

# ── 腾讯会议 API 常量 ────────────────────────────────────────────────────────

TENCENT_API_BASE = "https://api.meeting.qq.com/v1"
TENCENT_TOKEN_EXPIRE_SECONDS = 86400  # JWT 签名有效期为 24 小时


class TencentCalendar(CalendarBase):
    """腾讯会议日历会议集成服务。

    使用腾讯会议开放平台 API（JWT 签名鉴权）。
    无配置时自动降级到日志输出。
    """

    def __init__(self) -> None:
        self._app_id: str = ""
        self._sdk_id: str = ""
        self._secret: str = ""
        super().__init__()

    # ── 平台标识 ────────────────────────────────────────────────────────────

    @property
    def _platform_name(self) -> str:
        return "腾讯会议"

    # ── 配置检查 ────────────────────────────────────────────────────────────

    def _check_config(self) -> bool:
        """检查腾讯会议 API 是否已配置。"""
        app_id = getattr(settings, "TENCENT_MEETING_APP_ID", "")
        sdk_id = getattr(settings, "TENCENT_MEETING_SDK_ID", "")
        secret = getattr(settings, "TENCENT_MEETING_SECRET", "")

        if app_id and secret:
            self._app_id = app_id
            self._sdk_id = sdk_id
            self._secret = secret
            logger.info(
                "腾讯会议日历集成已配置 (app_id=%s)",
                app_id[:8] + "..." if len(app_id) > 8 else app_id,
            )
            return True

        # 兼容旧命名 TENCENT_WECHAT_*
        app_id2 = getattr(settings, "TENCENT_WECHAT_APP_ID", "")
        secret2 = getattr(settings, "TENCENT_WECHAT_SECRET", "")
        if app_id2 and secret2:
            self._app_id = app_id2
            self._sdk_id = sdk_id or app_id2  # 默认 sdk_id = app_id
            self._secret = secret2
            logger.info(
                "腾讯会议日历集成已配置 (向后兼容, app_id=%s)",
                app_id2[:8] + "...",
            )
            return True

        return False

    # ── JWT 签名 ────────────────────────────────────────────────────────────

    def _generate_jwt(self) -> str:
        """生成腾讯会议 API JWT 签名。

        腾讯会议要求每个请求携带 JWT Bearer Token，
        签名算法: HMAC-SHA256。
        """
        import jwt as pyjwt

        now = int(time.time())
        payload = {
            "app_id": self._app_id,
            "sdk_id": self._sdk_id or self._app_id,
            "iat": now,
            "exp": now + TENCENT_TOKEN_EXPIRE_SECONDS,
            "jti": str(uuid.uuid4()),
        }
        token = pyjwt.encode(payload, self._secret, algorithm="HS256")
        return token

    # ── HTTP 请求辅助 ───────────────────────────────────────────────────────

    async def _tencent_request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """发送腾讯会议 API 请求。"""
        token = self._generate_jwt()
        url = f"{TENCENT_API_BASE}{path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-TC-Action": path.split("/")[-1] if "/" in path else "",
            "X-TC-RequestId": str(uuid.uuid4()),
            "X-TC-Region": "ap-guangzhou",
            "AppId": self._app_id,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method=method, url=url, json=json_data, headers=headers
            )
            if resp.status_code == 401:
                logger.warning(
                    "腾讯会议 API 鉴权失败，可能 secret 已变更"
                )
            resp.raise_for_status()
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
        """列出腾讯会议（最近会议列表）。

        腾讯会议 API 不提供按用户列出所有会议的接口，
        改为查询最近的会议记录。
        """
        body: dict[str, Any] = {
            "page": page,
            "page_size": min(page_size, 100),
        }
        if start_time:
            body["start_time"] = start_time
        if end_time:
            body["end_time"] = end_time

        data = await self._tencent_request("POST", "/meetings", json_data=body)
        meeting_list = data.get("meeting_info_list", [])

        events = []
        for m in meeting_list:
            event = self._tencent_meeting_to_event(m)
            event.owner_id = user_id
            events.append(event)

        return CalendarResult(
            success=True,
            events=events,
            total=data.get("total_count", len(events)),
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
        """在腾讯会议上创建一个新会议。

        腾讯会议 API 字段说明:
          - type: 0=预约会议, 1=快速会议
          - start_time/end_time: Unix 时间戳（秒）
        """
        import datetime as dt
        import re

        # 解析 ISO 时间 → Unix 时间戳
        def _to_ts(iso_str: str) -> int:
            # 尝试多种格式
            formats = [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%d %H:%M:%S",
            ]
            clean = iso_str.replace("Z", "+00:00")
            for fmt in formats:
                try:
                    return int(dt.datetime.strptime(clean[:len(clean) - 3] if "%z" in fmt and clean.endswith(":00") else clean[:19], fmt[:19]).timestamp())
                except (ValueError, IndexError):
                    continue
            # fallback: 当前时间
            return int(time.time())

        duration = max(1, (_to_ts(end_time) - _to_ts(start_time)) // 60)

        body = {
            "subject": title,
            "type": 0,  # 预约会议
            "start_time": _to_ts(start_time),
            "end_time": _to_ts(end_time),
            "password": "",
            "settings": {
                "mute_enable": 1,           # 入会静音
                "allow_unmute_self": 1,      # 允许自行解除静音
                "allow_enter_before_host": 0,
                "watermark": 0,
                "auto_recording": "none",
            },
        }
        if description:
            body["description"] = description[:500]

        data = await self._tencent_request("POST", "/meetings", json_data=body)
        meeting = data.get("meeting_info", data)
        event = self._tencent_meeting_to_event(meeting)
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
        """更新腾讯会议。

        腾讯会议支持修改: subject, start_time, end_time, password 等。
        """
        import datetime as dt

        body: dict[str, Any] = {}
        if title is not None:
            body["subject"] = title
        if description is not None:
            body["description"] = description[:500]
        if start_time is not None:
            body["start_time"] = int(
                dt.datetime.fromisoformat(start_time.replace("Z", "+00:00")).timestamp()
            )
        if end_time is not None:
            body["end_time"] = int(
                dt.datetime.fromisoformat(end_time.replace("Z", "+00:00")).timestamp()
            )
        if status is not None:
            if status == "cancelled":
                body["status"] = 2  # 腾讯会议: 2=已取消
            else:
                body["status"] = 1  # 腾讯会议: 1=正常

        if body:
            await self._tencent_request(
                "PUT", f"/meetings/{event_id}", json_data=body
            )

        # 获取更新后的会议详情
        data = await self._tencent_request("GET", f"/meetings/{event_id}")
        meeting = data.get("meeting_info", data)
        event = self._tencent_meeting_to_event(meeting)

        return CalendarResult(
            success=True,
            event=event,
            platform=self._platform_name,
        )

    async def _platform_delete_event(self, event_id: str) -> CalendarResult:
        """删除腾讯会议。"""
        body = {"meeting_id": event_id}
        await self._tencent_request("DELETE", f"/meetings/{event_id}", json_data=body)
        return CalendarResult(
            success=True,
            platform=self._platform_name,
        )

    # ── 辅助方法 ────────────────────────────────────────────────────────────

    @staticmethod
    def _tencent_meeting_to_event(data: dict[str, Any]) -> CalendarEvent:
        """将腾讯会议 API 返回的会议数据转为 CalendarEvent。"""
        import datetime as dt

        meeting_id = str(data.get("meeting_id", data.get("meeting_code", "")))
        start_ts = data.get("start_time", 0)
        end_ts = data.get("end_time", 0)

        def _ts_to_iso(ts: int) -> str:
            try:
                return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
            except (OSError, ValueError, OverflowError):
                return ""

        return CalendarEvent(
            id=meeting_id,
            title=data.get("subject", data.get("topic", "")),
            description=data.get("description", ""),
            start_time=_ts_to_iso(start_ts if isinstance(start_ts, int) else int(start_ts or 0)),
            end_time=_ts_to_iso(end_ts if isinstance(end_ts, int) else int(end_ts or 0)),
            timezone="Asia/Shanghai",
            location="",
            meeting_url=data.get("join_url", ""),
            meeting_id=meeting_id,
            meeting_password=data.get("password", ""),
            status="scheduled",
            platform="tencent",
            raw=data,
        )


# ── 全局单例 ─────────────────────────────────────────────────────────────────

tencent_calendar = TencentCalendar()
"""全局腾讯会议日历集成实例。直接 import 使用。"""

# 自动注册到注册表
register_calendar("tencent", tencent_calendar)
