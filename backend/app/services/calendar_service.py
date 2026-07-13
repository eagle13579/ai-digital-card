"""日历集成服务基类 — 配置驱动 + 自动降级。

所有日历/会议平台集成继承此基类，实现统一的日历操作接口:
  - list_events()     — 列出日程/会议
  - create_event()    — 创建日程/会议
  - update_event()    — 更新日程/会议
  - delete_event()    — 删除日程/会议

当平台 API 凭据未配置时自动降级到日志输出，保证业务流程不被阻断。

支持平台:
  - Zoom (calendar_zoom.py)
  - 腾讯会议 (calendar_tencent.py)

与 CRM 集成: 所有日历事件通过 CRM 联系人 ID 关联，在 CrmActivity 时间线中记录。

使用示例:
    from app.services.calendar_zoom import zoom_calendar

    # 列出会议（降级安全）
    events = await zoom_calendar.list_events(user_id=123)

    # 创建会议并关联CRM联系人
    event = await zoom_calendar.create_event(
        user_id=123,
        title="客户会议",
        start_time="2026-07-02T10:00:00",
        end_time="2026-07-02T11:00:00",
        contact_ids=[456, 789],  # CRM联系人ID
    )

降级策略:
  - 平台 TOKEN/KEY 为空 → 仅记录日志，标记为降级模式
  - API 调用失败 → 记录错误日志，返回标准错误响应
  - 所有方法都在降级模式下返回格式一致的响应
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger(__name__)


# ── 数据模型 ─────────────────────────────────────────────────────────────────


@dataclass
class CalendarEvent:
    """平台无关的日程/会议数据模型。

    日历集成服务与外部平台之间的中间表示，
    各平台 adapter 负责转换 <-> 平台原生格式。
    """

    id: str = ""
    """事件ID（平台方唯一标识）"""
    title: str = ""
    """事件标题"""
    description: str = ""
    """事件描述/备注"""
    start_time: str = ""
    """开始时间 (ISO 8601, 如 2026-07-02T10:00:00+08:00)"""
    end_time: str = ""
    """结束时间 (ISO 8601)"""
    timezone: str = "Asia/Shanghai"
    """时区"""
    location: str = ""
    """会议地点/链接"""
    meeting_url: str = ""
    """视频会议入会链接（Zoom/腾讯会议专属）"""
    meeting_id: str = ""
    """会议号"""
    meeting_password: str = ""
    """会议密码"""
    status: str = "scheduled"
    """事件状态: scheduled | confirmed | cancelled | completed"""
    contact_ids: list[int] = field(default_factory=list)
    """关联的 CRM 联系人 ID 列表"""
    owner_id: int = 0
    """创建事件的用户 ID"""
    platform: str = ""
    """来源平台: zoom | tencent"""
    raw: dict[str, Any] = field(default_factory=dict)
    """平台原始返回数据（调试用）"""

    def to_dict(self) -> dict[str, Any]:
        """转为字典（JSON 友好）。"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "timezone": self.timezone,
            "location": self.location,
            "meeting_url": self.meeting_url,
            "meeting_id": self.meeting_id,
            "meeting_password": self.meeting_password,
            "status": self.status,
            "contact_ids": self.contact_ids,
            "owner_id": self.owner_id,
            "platform": self.platform,
        }


@dataclass
class CalendarResult:
    """日历操作的标准结果包装。"""

    success: bool = True
    """操作是否成功"""
    degraded: bool = False
    """是否处于降级模式（未配置 → 仅日志）"""
    event: CalendarEvent | None = None
    """操作涉及的日程事件（创建/更新/查询）"""
    events: list[CalendarEvent] = field(default_factory=list)
    """事件列表（list_events 使用）"""
    total: int = 0
    """事件总数（用于分页）"""
    error: str | None = None
    """错误信息（success=False 时）"""
    platform: str = ""
    """来源平台标识"""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "degraded": self.degraded,
            "event": self.event.to_dict() if self.event else None,
            "events": [e.to_dict() for e in self.events],
            "total": self.total,
            "error": self.error,
            "platform": self.platform,
        }


# ── 基类 ─────────────────────────────────────────────────────────────────────


class CalendarBase(ABC):
    """日历集成服务基类。

    所有日历/会议平台集成（Zoom、腾讯会议等）继承此类。

    子类必须实现:
      - _platform_name          — 平台名称字符串
      - _check_config()         — 检查配置是否完整
      - _platform_list_events() — 平台原生列出事件
      - _platform_create_event()— 平台原生创建事件
      - _platform_update_event()— 平台原生更新事件
      - _platform_delete_event()— 平台原生删除事件
    """

    def __init__(self) -> None:
        self._enabled: bool = self._check_config()
        if not self._enabled:
            logger.info(
                "%s 日历集成未配置 API 凭据 — 已降级到日志输出模式",
                self._platform_name,
            )
        else:
            logger.info("%s 日历集成已启用", self._platform_name)

    # ── 子类必须实现的接口 ────────────────────────────────────────────────────

    @property
    @abstractmethod
    def _platform_name(self) -> str:
        """平台名称，用于日志标识。"""

    @abstractmethod
    def _check_config(self) -> bool:
        """检查平台 API 配置是否完整。返回 True 表示已配置。"""

    @abstractmethod
    async def _platform_list_events(
        self,
        user_id: int,
        *,
        start_time: str | None = None,
        end_time: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CalendarResult:
        """平台原生列出日程事件。"""

    @abstractmethod
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
        """平台原生创建日程/会议事件。"""

    @abstractmethod
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
        """平台原生更新日程事件。"""

    @abstractmethod
    async def _platform_delete_event(self, event_id: str) -> CalendarResult:
        """平台原生删除日程事件。"""

    # ── 可选覆写的钩子 ───────────────────────────────────────────────────────

    async def _on_event_created(
        self, event: CalendarEvent, result: CalendarResult
    ) -> None:
        """事件创建后的钩子（用于 CRM 活动记录等）。"""

    async def _on_event_deleted(
        self, event_id: str, result: CalendarResult
    ) -> None:
        """事件删除后的钩子。"""

    # ── 降级感知的公开接口 ────────────────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        """此日历集成是否已配置并启用。"""
        return self._enabled

    async def list_events(
        self,
        user_id: int,
        *,
        start_time: str | None = None,
        end_time: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CalendarResult:
        """列出日程事件。

        Args:
            user_id: 用户 ID
            start_time: 开始时间过滤（ISO 8601）
            end_time: 结束时间过滤（ISO 8601）
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            CalendarResult
        """
        if not self._enabled:
            logger.info(
                "[%s 降级] list_events user_id=%s page=%s",
                self._platform_name,
                user_id,
                page,
            )
            return CalendarResult(
                success=True,
                degraded=True,
                events=[],
                total=0,
                platform=self._platform_name,
            )

        try:
            result = await self._platform_list_events(
                user_id=user_id,
                start_time=start_time,
                end_time=end_time,
                page=page,
                page_size=page_size,
            )
            logger.debug(
                "[%s] list_events ok: user_id=%s count=%s",
                self._platform_name,
                user_id,
                len(result.events),
            )
            return result
        except Exception as exc:
            logger.error(
                "[%s] list_events 失败: %s",
                self._platform_name,
                exc,
                exc_info=True,
            )
            return CalendarResult(
                success=False,
                degraded=False,
                error=str(exc),
                platform=self._platform_name,
            )

    async def create_event(
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
        """创建日程/会议事件。

        Args:
            user_id: 创建者用户 ID
            title: 事件标题
            start_time: 开始时间（ISO 8601）
            end_time: 结束时间（ISO 8601）
            description: 事件描述
            timezone: 时区（默认 Asia/Shanghai）
            location: 地点/会议室
            contact_ids: 关联的 CRM 联系人 ID 列表

        Returns:
            CalendarResult
        """
        if not self._enabled:
            logger.info(
                "[%s 降级] create_event user_id=%s title=%s",
                self._platform_name,
                user_id,
                title,
            )
            return CalendarResult(
                success=True,
                degraded=True,
                event=CalendarEvent(
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                    contact_ids=contact_ids or [],
                    owner_id=user_id,
                    platform=self._platform_name,
                ),
                platform=self._platform_name,
            )

        try:
            result = await self._platform_create_event(
                user_id=user_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description,
                timezone=timezone,
                location=location,
                contact_ids=contact_ids,
            )
            if result.success and result.event:
                await self._on_event_created(result.event, result)
            logger.info(
                "[%s] create_event ok: title=%s event_id=%s",
                self._platform_name,
                title,
                result.event.id if result.event else "N/A",
            )
            return result
        except Exception as exc:
            logger.error(
                "[%s] create_event 失败: %s",
                self._platform_name,
                exc,
                exc_info=True,
            )
            return CalendarResult(
                success=False,
                degraded=False,
                error=str(exc),
                platform=self._platform_name,
            )

    async def update_event(
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
        """更新日程事件。

        Args:
            event_id: 事件 ID（平台方唯一标识）
            title: 新标题
            description: 新描述
            start_time: 新开始时间
            end_time: 新结束时间
            timezone: 新时区
            location: 新地点
            status: 新状态

        Returns:
            CalendarResult
        """
        if not self._enabled:
            logger.info(
                "[%s 降级] update_event event_id=%s title=%s",
                self._platform_name,
                event_id,
                title,
            )
            return CalendarResult(
                success=True,
                degraded=True,
                platform=self._platform_name,
            )

        try:
            result = await self._platform_update_event(
                event_id=event_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                timezone=timezone,
                location=location,
                status=status,
            )
            logger.debug(
                "[%s] update_event ok: event_id=%s", self._platform_name, event_id
            )
            return result
        except Exception as exc:
            logger.error(
                "[%s] update_event 失败: event_id=%s error=%s",
                self._platform_name,
                event_id,
                exc,
                exc_info=True,
            )
            return CalendarResult(
                success=False,
                degraded=False,
                error=str(exc),
                platform=self._platform_name,
            )

    async def delete_event(self, event_id: str) -> CalendarResult:
        """删除日程事件。

        Args:
            event_id: 事件 ID（平台方唯一标识）

        Returns:
            CalendarResult
        """
        if not self._enabled:
            logger.info(
                "[%s 降级] delete_event event_id=%s",
                self._platform_name,
                event_id,
            )
            return CalendarResult(
                success=True,
                degraded=True,
                platform=self._platform_name,
            )

        try:
            result = await self._platform_delete_event(event_id=event_id)
            await self._on_event_deleted(event_id, result)
            logger.info(
                "[%s] delete_event ok: event_id=%s",
                self._platform_name,
                event_id,
            )
            return result
        except Exception as exc:
            logger.error(
                "[%s] delete_event 失败: event_id=%s error=%s",
                self._platform_name,
                event_id,
                exc,
                exc_info=True,
            )
            return CalendarResult(
                success=False,
                degraded=False,
                error=str(exc),
                platform=self._platform_name,
            )


# ── 日历集成注册表 ───────────────────────────────────────────────────────────

_calendar_registry: dict[str, CalendarBase] = {}


def register_calendar(platform: str, service: CalendarBase) -> None:
    """注册一个日历集成服务到全局注册表。"""
    _calendar_registry[platform] = service
    logger.info(
        "日历集成已注册: %s (启用=%s)", platform, service.enabled
    )


def get_calendar(platform: str) -> CalendarBase | None:
    """按平台名获取日历集成服务实例。"""
    return _calendar_registry.get(platform)


def get_enabled_calendars() -> list[tuple[str, CalendarBase]]:
    """获取所有已启用的日历集成列表。"""
    return [(name, svc) for name, svc in _calendar_registry.items() if svc.enabled]


def list_calendars() -> dict[str, bool]:
    """列出所有注册的日历集成及其启用状态。"""
    return {name: svc.enabled for name, svc in _calendar_registry.items()}
