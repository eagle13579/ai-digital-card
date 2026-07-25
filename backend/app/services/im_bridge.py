"""
IM 桥接适配器 — 统一企微 (WeCom / 企业微信) + 钉钉 (DingTalk) 消息推送。

提供:
  - 统一的 send / send_message / send_card 接口
  - 平台自动发现与降级 (未配置 → 日志输出)
  - 全局单例 im_bridge

依赖配置项 (settings):
  - WECOM_CORP_ID / WECOM_AGENT_ID / WECOM_SECRET   — 企微
  - DINGTALK_APP_KEY / DINGTALK_APP_SECRET             — 钉钉
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


# ── 平台枚举 ─────────────────────────────────────────────────────────────────


class IMPlatform(str, Enum):
    """支持的 IM 平台"""
    WECOM = "wecom"       # 企业微信
    DINGTALK = "dingtalk"  # 钉钉


# ── 数据模型 ─────────────────────────────────────────────────────────────────


@dataclass
class IMMessage:
    """统一 IM 消息体"""
    platform: IMPlatform
    user_id: str                   # 企微 UserID / 钉钉 userId
    text: str = ""                 # 纯文本 / Markdown
    title: str = ""                # 卡片标题
    card_data: dict[str, Any] = field(default_factory=dict)   # 卡片扩展字段
    buttons: list[dict[str, str]] = field(default_factory=list)  # [{"label":..., "url":..., "action":...}]


# ── 企微适配器 ──────────────────────────────────────────────────────────────


class WeComAdapter:
    """企业微信 (WeCom) 消息适配器

    配置项:
      - WECOM_CORP_ID    — 企业 ID
      - WECOM_AGENT_ID   — 应用 AgentId
      - WECOM_SECRET     — 应用 Secret
    """

    _platform = IMPlatform.WECOM

    def __init__(self) -> None:
        self._corp_id = getattr(settings, "WECOM_CORP_ID", "") or ""
        self._agent_id = getattr(settings, "WECOM_AGENT_ID", "") or ""
        self._secret = getattr(settings, "WECOM_SECRET", "") or ""
        self._enabled = bool(self._corp_id and self._agent_id)
        if self._enabled:
            corp_preview = self._corp_id[:6] if len(self._corp_id) > 6 else self._corp_id
            logger.info("企微适配器已就绪 (corp_id=%s...)", corp_preview)
        else:
            logger.warning("企微适配器未配置 (需 WECOM_CORP_ID + WECOM_AGENT_ID), 降级为日志输出")

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def send_message(self, msg: IMMessage) -> dict[str, Any]:
        """发送文本消息到企微"""
        if not self._enabled:
            logger.info("[企微降级] 发给 user=%s: %s", msg.user_id, msg.text)
            return {"platform": "wecom", "status": "degraded", "reason": "未配置"}

        # TODO: 对接企微 应用消息推送 API
        # POST https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}
        logger.info("[企微] 发送文本消息 user=%s: %s", msg.user_id, msg.text)
        return {
            "platform": "wecom",
            "status": "simulated",
            "touser": msg.user_id,
            "msgtype": "text",
        }

    async def send_card(self, msg: IMMessage) -> dict[str, Any]:
        """发送卡片消息到企微"""
        if not self._enabled:
            logger.info("[企微降级] 卡片发给 user=%s: %s", msg.user_id, msg.title)
            return {"platform": "wecom", "status": "degraded", "reason": "未配置"}

        # TODO: 对接企微 模板卡片消息 API
        logger.info("[企微] 发送卡片消息 user=%s: %s", msg.user_id, msg.title)
        return {
            "platform": "wecom",
            "status": "simulated",
            "touser": msg.user_id,
            "msgtype": "template_card",
        }


# ── 钉钉适配器 ──────────────────────────────────────────────────────────────


class DingTalkAdapter:
    """钉钉 (DingTalk) 消息适配器

    配置项:
      - DINGTALK_APP_KEY     — 应用 AppKey
      - DINGTALK_APP_SECRET  — 应用 AppSecret
    """

    _platform = IMPlatform.DINGTALK

    def __init__(self) -> None:
        self._app_key = getattr(settings, "DINGTALK_APP_KEY", "") or ""
        self._app_secret = getattr(settings, "DINGTALK_APP_SECRET", "") or ""
        self._enabled = bool(self._app_key)
        if self._enabled:
            key_preview = self._app_key[:6] if len(self._app_key) > 6 else self._app_key
            logger.info("钉钉适配器已就绪 (app_key=%s...)", key_preview)
        else:
            logger.warning("钉钉适配器未配置 (需 DINGTALK_APP_KEY), 降级为日志输出")

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def send_message(self, msg: IMMessage) -> dict[str, Any]:
        """发送文本消息到钉钉"""
        if not self._enabled:
            logger.info("[钉钉降级] 发给 user=%s: %s", msg.user_id, msg.text)
            return {"platform": "dingtalk", "status": "degraded", "reason": "未配置"}

        # TODO: 对接钉钉 工作通知消息 API
        # POST https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2
        logger.info("[钉钉] 发送文本消息 user=%s: %s", msg.user_id, msg.text)
        return {
            "platform": "dingtalk",
            "status": "simulated",
            "userid": msg.user_id,
            "msgtype": "text",
        }

    async def send_card(self, msg: IMMessage) -> dict[str, Any]:
        """发送卡片消息到钉钉"""
        if not self._enabled:
            logger.info("[钉钉降级] 卡片发给 user=%s: %s", msg.user_id, msg.title)
            return {"platform": "dingtalk", "status": "degraded", "reason": "未配置"}

        # TODO: 对接钉钉 互动卡片消息 API
        logger.info("[钉钉] 发送卡片消息 user=%s: %s", msg.user_id, msg.title)
        return {
            "platform": "dingtalk",
            "status": "simulated",
            "userid": msg.user_id,
            "msgtype": "action_card",
        }


# ── 统一桥接器 ──────────────────────────────────────────────────────────────


class IMBridge:
    """IM 桥接器 — 统一企微 + 钉钉 消息推送入口"""

    def __init__(self) -> None:
        self.wecom = WeComAdapter()
        self.dingtalk = DingTalkAdapter()
        logger.info(
            "IM 桥接器就绪 (wecom=%s, dingtalk=%s)",
            self.wecom.enabled,
            self.dingtalk.enabled,
        )

    def get_adapter(self, platform: IMPlatform | str) -> WeComAdapter | DingTalkAdapter:
        """获取指定平台的适配器实例"""
        if isinstance(platform, str):
            platform = IMPlatform(platform.lower().strip())
        if platform == IMPlatform.WECOM:
            return self.wecom
        if platform == IMPlatform.DINGTALK:
            return self.dingtalk
        raise ValueError(f"不支持的 IM 平台: {platform!r}")

    def list_adapters(self) -> list[dict[str, Any]]:
        """列出所有适配器及其状态"""
        return [
            {"platform": "wecom", "enabled": self.wecom.enabled},
            {"platform": "dingtalk", "enabled": self.dingtalk.enabled},
        ]

    async def send(self, msg: IMMessage) -> dict[str, Any]:
        """统一消息发送入口 (自动选择平台的 send 或 send_card)"""
        adapter = self.get_adapter(msg.platform)
        if msg.card_data or msg.buttons:
            return await adapter.send_card(msg)
        return await adapter.send_message(msg)

    async def send_text(
        self,
        platform: IMPlatform | str,
        user_id: str,
        text: str,
    ) -> dict[str, Any]:
        """快捷发送纯文本消息"""
        return await self.send(IMMessage(
            platform=IMPlatform(platform.lower().strip()) if isinstance(platform, str) else platform,
            user_id=user_id,
            text=text,
        ))

    async def send_card(
        self,
        platform: IMPlatform | str,
        user_id: str,
        title: str,
        content: str = "",
        buttons: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """快捷发送卡片消息"""
        return await self.send(IMMessage(
            platform=IMPlatform(platform.lower().strip()) if isinstance(platform, str) else platform,
            user_id=user_id,
            title=title,
            text=content,
            buttons=buttons or [],
            card_data={"content": content},
        ))


# ── 全局单例 ─────────────────────────────────────────────────────────────────

im_bridge = IMBridge()
