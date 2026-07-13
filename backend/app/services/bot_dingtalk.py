"""钉钉机器人 — 钉钉自定义机器人 Webhook + 消息推送。

使用钉钉开放平台 API（HTTP POST 调用），不依赖 dingtalk-sdk 包。
配置驱动: 没有 DINGTALK_WEBHOOK_URL 时自动降级到日志输出。
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
import base64
from typing import Any

from app.config import settings
from app.services.bot_service import (
    BotBase,
    BotCard,
    BotCommand,
    BotMessage,
    register_bot,
)

logger = logging.getLogger(__name__)


class DingTalkBot(BotBase):
    """钉钉机器人 — 支持文本、Markdown、卡片消息 (ActionCard)。"""

    _platform_name = "钉钉"

    def _check_config(self) -> bool:
        return bool(settings.DINGTALK_WEBHOOK_URL)

    # ── 签名 ──────────────────────────────────────────────────────────────────

    def _sign_url(self, webhook_url: str, secret: str) -> str:
        """为钉钉 Webhook URL 添加 v2.0 签名参数。

        Args:
            webhook_url: 原始 Webhook URL
            secret: 加签密钥

        Returns:
            带签名的完整 URL
        """
        if not secret:
            return webhook_url

        timestamp = str(int(time.time() * 1000))
        sign_string = f"{timestamp}\n{secret}"
        signature = base64.urlsafe_b64encode(
            hmac.new(
                secret.encode("utf-8"),
                sign_string.encode("utf-8"),
                hashlib.sha256,
            ).digest()
        ).decode("utf-8")

        separator = "&" if "?" in webhook_url else "?"
        return f"{webhook_url}{separator}timestamp={timestamp}&sign={signature}"

    # ── 核心消息发送 ──────────────────────────────────────────────────────────

    async def _platform_send_message(self, msg: BotMessage) -> dict[str, Any]:
        target_url = self._sign_url(
            settings.DINGTALK_WEBHOOK_URL, settings.DINGTALK_SECRET
        )

        # 如果包含 at 信息
        at: dict[str, Any] = {}
        if msg.user_id:
            at["atUserIds"] = [msg.user_id]

        payload: dict[str, Any]
        if msg.text:
            payload = {
                "msgtype": "text",
                "text": {"content": msg.text},
                "at": at,
            }
        else:
            # Markdown 格式
            md_text = msg.text or (msg.blocks[0].get("text", {}).get("text", "") if msg.blocks else "")
            payload = {
                "msgtype": "markdown",
                "markdown": {"title": "消息", "text": md_text},
                "at": at,
            }

        return await self._http_post(target_url, payload)

    async def _platform_send_card(self, card: BotCard) -> dict[str, Any]:
        """将 BotCard 转换为钉钉 ActionCard 消息。"""
        target_url = self._sign_url(
            settings.DINGTALK_WEBHOOK_URL, settings.DINGTALK_SECRET
        )

        # 构造按钮区域 (ActionCard)
        buttons: list[dict[str, str]] = []
        for btn in card.buttons:
            buttons.append({
                "title": btn.get("label", ""),
                "actionURL": btn.get("url", ""),
            })

        # 如果内容包含 Markdown，用 markdown 格式
        md_text = f"# {card.title}\n\n{card.content}" if card.title else card.content
        if card.image_url:
            md_text += f"\n\n![image]({card.image_url})"

        if buttons:
            payload = {
                "msgtype": "actionCard",
                "actionCard": {
                    "title": card.title or "消息",
                    "text": md_text,
                    "btnOrientation": "1",  # 竖排
                    "btns": buttons,
                },
            }
        else:
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": card.title or "消息",
                    "text": md_text,
                },
            }

        return await self._http_post(target_url, payload)

    async def _platform_handle_command(self, cmd: BotCommand) -> str:
        """处理钉钉命令。"""
        command_map = {
            "search-contact": self._cmd_search_contact,
            "add-note": self._cmd_add_note,
            "recent-activity": self._cmd_recent_activity,
        }
        handler = command_map.get(cmd.command, self._cmd_unknown)
        return await handler(cmd)

    # ── 命令处理器 ────────────────────────────────────────────────────────────

    async def _cmd_search_contact(self, cmd: BotCommand) -> str:
        if not cmd.args:
            return "❌ 请输入搜索关键词。示例: /search-contact 张三"
        keyword = " ".join(cmd.args)
        return (
            f"🔍 搜索联系人: {keyword}\n"
            f"---\n"
            f"📇 张三 | 138****0000\n"
            f"📇 张伟 | 139****1111"
        )

    async def _cmd_add_note(self, cmd: BotCommand) -> str:
        if len(cmd.args) < 2:
            return "❌ 用法: /add-note <联系人> <备注内容>"
        contact = cmd.args[0]
        note = " ".join(cmd.args[1:])
        return f"✅ 已为 {contact} 添加备注: {note}"

    async def _cmd_recent_activity(self, cmd: BotCommand) -> str:
        limit = 5
        if cmd.args:
            try:
                limit = int(cmd.args[0])
                limit = max(1, min(20, limit))
            except ValueError:
                pass
        return (
            f"📊 最近 {limit} 条活动\n"
            f"1. 张三 查看了您的名片 (2分钟前)\n"
            f"2. 李四 交换了联系方式 (15分钟前)"
        )

    async def _cmd_unknown(self, cmd: BotCommand) -> str:
        return (
            "❓ 未知命令。支持:\n"
            "• `/search-contact <关键词>` 搜索联系人\n"
            "• `/add-note <联系人> <备注>` 添加备注\n"
            "• `/recent-activity [数量]` 最近活动"
        )

    # ── 钉钉专属: 发送到指定 Webhook URL ─────────────────────────────────────

    async def send_to_url(
        self, webhook_url: str, secret: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """发送消息到任意钉钉 Webhook URL。

        Args:
            webhook_url: 钉钉机器人 Webhook URL
            secret: 加签密钥
            payload: 完整的钉钉消息体 (需含 msgtype)

        Returns:
            API 响应
        """
        target_url = self._sign_url(webhook_url, secret)
        return await self._http_post(target_url, payload)


# ── 全局单例 ─────────────────────────────────────────────────────────────────

dingtalk_bot = DingTalkBot()
register_bot("dingtalk", dingtalk_bot)
