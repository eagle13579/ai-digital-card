"""notification — 行业动态推送模块

基于 baize_libs/multi_channel_delivery 的统一推送服务。
支持 StdoutDelivery, TelegramDelivery, EmailDelivery 三种渠道，
以及实时推送、定时推送、主动拉取三种推送模式。

Usage:
    from notification.notification_service import UnifiedPushService
    svc = UnifiedPushService()
    svc.push_realtime("新名片匹配: ...")
"""

from notification.notification_service import (
    UnifiedPushService,
    PushMode,
    PushResult,
)

__all__ = [
    "UnifiedPushService",
    "PushMode",
    "PushResult",
]
