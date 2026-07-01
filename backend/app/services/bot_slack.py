"""Slack 机器人 — Slack Events API + Block Kit。

使用标准 Slack Web API（HTTP POST 调用），不依赖 slack_sdk 包。
配置驱动: 没有 SLACK_BOT_TOKEN 时自动降级到日志输出。
"""

from __future__ import annotations

import json
import logging
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

# ── Slack API 端点 ───────────────────────────────────────────────────────────

SLACK_API_BASE = "https://slack.com/api"
SLACK_CHAT_POST_MESSAGE = f"{SLACK_API_BASE}/chat.postMessage"
SLACK_VIEWS_OPEN = f"{SLACK_API_BASE}/views.open"


class SlackBot(BotBase):
    """Slack Bot — 支持斜杠命令和 Block Kit 消息。"""

    _platform_name = "Slack"

    def _check_config(self) -> bool:
        return bool(settings.SLACK_BOT_TOKEN)

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"}

    # ── 核心消息发送 ──────────────────────────────────────────────────────────

    async def _platform_send_message(self, msg: BotMessage) -> dict[str, Any]:
        payload: dict[str, Any] = {"channel": msg.channel}

        if msg.blocks:
            payload["blocks"] = msg.blocks
            payload["text"] = msg.text or " "
        elif msg.attachments:
            payload["attachments"] = msg.attachments
            payload["text"] = msg.text or " "
        else:
            payload["text"] = msg.text

        if msg.thread_ts:
            payload["thread_ts"] = msg.thread_ts

        return await self._http_post(SLACK_CHAT_POST_MESSAGE, payload, self._auth_headers)

    async def _platform_send_card(self, card: BotCard) -> dict[str, Any]:
        """将 BotCard 转换为 Slack Block Kit 消息。"""
        blocks: list[dict[str, Any]] = []

        # 标题
        if card.title:
            blocks.append(
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": card.title, "emoji": True},
                }
            )

        # 正文
        if card.content:
            blocks.append(
                {"type": "section", "text": {"type": "mrkdwn", "text": card.content}}
            )

        # 图片
        if card.image_url:
            blocks.append(
                {
                    "type": "image",
                    "image_url": card.image_url,
                    "alt_text": card.title or "card image",
                }
            )

        # 按钮
        if card.buttons:
            elements = []
            for btn in card.buttons:
                elements.append(
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": btn.get("label", ""), "emoji": True},
                        "url": btn.get("url", ""),
                        "action_id": f"btn_{btn.get('label', 'unknown')}",
                    }
                )
            blocks.append({"type": "actions", "elements": elements})

        msg = BotMessage(
            text=card.title or card.content[:80],
            blocks=blocks,
            channel=card.channel,
            user_id=card.user_id,
        )
        return await self.send_message(msg)

    async def _platform_handle_command(self, cmd: BotCommand) -> str:
        """处理 Slack 斜杠命令。"""
        command_map = {
            "search-contact": self._cmd_search_contact,
            "add-note": self._cmd_add_note,
            "recent-activity": self._cmd_recent_activity,
        }
        handler = command_map.get(cmd.command, self._cmd_unknown)
        return await handler(cmd)

    # ── 命令处理器 ────────────────────────────────────────────────────────────

    async def _cmd_search_contact(self, cmd: BotCommand) -> str:
        """搜索联系人。用法: /search-contact <姓名|电话|邮箱>"""
        if not cmd.args:
            return (
                "❌ 请输入搜索关键词。示例: `/search-contact 张三`"
            )
        keyword = " ".join(cmd.args)
        # TODO: 接入真实联系人搜索服务
        return (
            f"🔍 *搜索联系人*: `{keyword}`\n"
            f"   (搜索服务待接入 — 返回模拟结果)\n"
            f"   📇 张三 | 138****0000 | zhangsan@example.com\n"
            f"   📇 张伟 | 139****1111 | zhangwei@example.com"
        )

    async def _cmd_add_note(self, cmd: BotCommand) -> str:
        """添加备注。用法: /add-note <联系人> <备注内容>"""
        if len(cmd.args) < 2:
            return "❌ 用法: `/add-note <联系人姓名> <备注内容>`"
        contact = cmd.args[0]
        note = " ".join(cmd.args[1:])
        # TODO: 接入真实备注存储
        return f"✅ 已为 *{contact}* 添加备注: _{note}_"

    async def _cmd_recent_activity(self, cmd: BotCommand) -> str:
        """最近活动。用法: /recent-activity [数量]"""
        limit = 5
        if cmd.args:
            try:
                limit = int(cmd.args[0])
                limit = max(1, min(20, limit))
            except ValueError:
                pass
        # TODO: 接入真实活动日志
        return (
            f"📊 *最近 {limit} 条活动*\n"
            f"1. 张三 查看了您的名片 (2分钟前)\n"
            f"2. 李四 交换了联系方式 (15分钟前)\n"
            f"3. 王五 导出了联系人 (1小时前)"
        )

    async def _cmd_unknown(self, cmd: BotCommand) -> str:
        """未知命令处理。"""
        return (
            f"❓ 未知命令 `/`。支持的命令:\n"
            f"• `/search-contact <关键词>` — 搜索联系人\n"
            f"• `/add-note <联系人> <备注>` — 添加备注\n"
            f"• `/recent-activity [数量]` — 查看最近活动"
        )

    # ── Slack Events API 回调验证 ────────────────────────────────────────────

    def verify_slack_signature(self, body: bytes, headers: dict[str, str]) -> bool:
        """验证 Slack 请求签名 (v0)。

        Args:
            body: 原始请求体 bytes
            headers: 请求头字典 (需包含 X-Slack-Signature, X-Slack-Request-Timestamp)

        Returns:
            签名有效返回 True；无 secret 配置或验证失败返回 False
        """
        if not settings.SLACK_SIGNING_SECRET:
            logger.warning("SLACK_SIGNING_SECRET 未配置，跳过签名验证")
            return False

        signature = headers.get("X-Slack-Signature", "")
        timestamp = headers.get("X-Slack-Request-Timestamp", "")

        if not signature or not timestamp:
            logger.warning("Slack 请求缺少签名头")
            return False

        # 构造 basestring: v0:{timestamp}:{body}
        basestring = f"v0:{timestamp}:".encode("utf-8") + body
        expected = "v0=" + self._hmac_sha256(settings.SLACK_SIGNING_SECRET, basestring)

        return hmac.compare_digest(expected, signature)

    def parse_event(self, raw_body: bytes) -> dict[str, Any]:
        """解析 Slack Events API 回调事件。

        Args:
            raw_body: 原始请求体 bytes

        Returns:
            解析后的事件字典。包含 type, event 等字段。
        """
        return json.loads(raw_body)

    def parse_slash_command(self, form_data: dict[str, str]) -> BotCommand:
        """解析 Slack 斜杠命令表单数据。

        Args:
            form_data: URL-encoded 表单数据字典

        Returns:
            BotCommand 对象
        """
        raw = form_data.get("text", "")
        parts = raw.strip().split()
        return BotCommand(
            command=form_data.get("command", "").lstrip("/"),
            args=parts,
            raw_text=raw,
            user_id=form_data.get("user_id", ""),
            channel=form_data.get("channel_id", ""),
            platform="slack",
        )


# ── 全局单例 ─────────────────────────────────────────────────────────────────

slack_bot = SlackBot()
register_bot("slack", slack_bot)
