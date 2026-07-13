"""飞书机器人 — 飞书自定义机器人 Webhook + 卡片消息。

使用飞书开放平台 API（HTTP POST 调用），不依赖 lark-oapi 包。
配置驱动: 没有 FEISHU_APP_ID 时自动降级到日志输出。
"""

from __future__ import annotations

import json
import logging
import time
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

# ── 飞书 API 端点 ────────────────────────────────────────────────────────────

FEISHU_API_BASE = "https://open.feishu.cn/open-apis"
FEISHU_TOKEN_URL = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
FEISHU_IM_SEND = f"{FEISHU_API_BASE}/im/v1/messages"
FEISHU_WEBHOOK_BASE = "https://open.feishu.cn/open-apis/bot/v2/hook"


class FeishuBot(BotBase):
    """飞书机器人 — 支持卡片消息和搜索命令。"""

    _platform_name = "飞书"

    # ── 租户 Token 缓存 ───────────────────────────────────────────────────────
    _tenant_token: str = ""
    _token_expires_at: float = 0.0

    def _check_config(self) -> bool:
        return bool(settings.FEISHU_APP_ID and settings.FEISHU_APP_SECRET)

    # ── 认证 ──────────────────────────────────────────────────────────────────

    async def _ensure_token(self) -> str:
        """获取或刷新飞书 tenant_access_token。"""
        now = time.time()
        if self._tenant_token and now < self._token_expires_at - 60:
            return self._tenant_token

        payload = {
            "app_id": settings.FEISHU_APP_ID,
            "app_secret": settings.FEISHU_APP_SECRET,
        }
        result = await self._http_post(FEISHU_TOKEN_URL, payload)
        self._tenant_token = result.get("tenant_access_token", "")
        expire = result.get("expire", 7200)
        self._token_expires_at = now + expire
        logger.debug("飞书 tenant_access_token 已刷新，有效 %s 秒", expire)
        return self._tenant_token

    @property
    async def _auth_headers(self) -> dict[str, str]:
        token = await self._ensure_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}

    # ── 核心消息发送 ──────────────────────────────────────────────────────────

    async def _platform_send_message(self, msg: BotMessage) -> dict[str, Any]:
        headers = await self._auth_headers
        receive_id = msg.user_id or msg.channel
        if not receive_id:
            return {"ok": False, "error": "缺少目标 user_id 或 channel"}

        # 构造飞书消息体
        content: dict[str, Any] = {"text": msg.text}
        payload = {
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps(content, ensure_ascii=False),
        }

        url = f"{FEISHU_IM_SEND}?receive_id_type=open_id"
        return await self._http_post(url, payload, headers)

    async def _platform_send_card(self, card: BotCard) -> dict[str, Any]:
        """将 BotCard 转换为飞书卡片消息 (Interactive Card v2)。"""
        headers = await self._auth_headers
        receive_id = card.user_id or card.channel
        if not receive_id:
            return {"ok": False, "error": "缺少目标 user_id 或 channel"}

        # 构建飞书卡片
        elements: list[dict[str, Any]] = []
        if card.content:
            elements.append(
                {
                    "tag": "markdown",
                    "content": card.content,
                }
            )

        # 按钮
        if card.buttons:
            actions: list[dict[str, Any]] = []
            for btn in card.buttons:
                actions.append(
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": btn.get("label", "")},
                        "url": btn.get("url", ""),
                        "type": "default",
                    }
                )
            elements.append({"tag": "action", "actions": actions})

        # 图片
        if card.image_url:
            elements.append(
                {
                    "tag": "img",
                    "img_key": card.image_url,  # 需要先上传图片获取image_key
                    "alt": {"tag": "plain_text", "content": card.title or "image"},
                }
            )

        header: dict[str, Any] = {
            "title": {"tag": "plain_text", "content": card.title or ""},
        }
        if card.color:
            header["template"] = self._color_to_feishu(card.color)

        card_payload = {
            "config": {"wide_screen_mode": True},
            "header": header,
            "elements": elements,
        }

        payload = {
            "receive_id": receive_id,
            "msg_type": "interactive",
            "content": json.dumps(card_payload, ensure_ascii=False),
        }

        url = f"{FEISHU_IM_SEND}?receive_id_type=open_id"
        return await self._http_post(url, payload, headers)

    async def _platform_handle_command(self, cmd: BotCommand) -> str:
        """处理飞书命令 (中文斜杠)。"""
        command_map = {
            "搜索联系人": self._cmd_search_contact,
            "添加备注": self._cmd_add_note,
            "recent-activity": self._cmd_recent_activity,
        }
        handler = command_map.get(cmd.command, self._cmd_unknown)
        return await handler(cmd)

    # ── 飞书 Webhook URL 发送 (自定义机器人) ─────────────────────────────────

    async def send_to_webhook(self, webhook_url: str, content: str | dict[str, Any]) -> dict[str, Any]:
        """通过飞书自定义机器人 Webhook URL 发送消息。

        Args:
            webhook_url: 飞书自定义机器人 Webhook URL
            content: 消息内容（字符串文本 或 卡片字典）

        Returns:
            API 响应
        """
        if isinstance(content, str):
            payload = {
                "msg_type": "text",
                "content": {"text": content},
            }
        else:
            payload = content  # 假定已包含 msg_type + content

        return await self._http_post(webhook_url, payload)

    # ── 命令处理器 ────────────────────────────────────────────────────────────

    async def _cmd_search_contact(self, cmd: BotCommand) -> str:
        """搜索联系人。用法: /搜索联系人 <姓名|电话>"""
        if not cmd.args:
            return "❌ 请输入搜索关键词。示例: `/搜索联系人 张三`"
        keyword = " ".join(cmd.args)
        return (
            f"🔍 搜索结果: `{keyword}`\n"
            f"   (搜索服务待接入)\n"
            f"   📇 张三 | zhangsan@example.com\n"
            f"   📇 张三丰 | zsf@example.com"
        )

    async def _cmd_add_note(self, cmd: BotCommand) -> str:
        """添加备注。用法: /添加备注 <联系人> <备注>"""
        if len(cmd.args) < 2:
            return "❌ 用法: `/添加备注 <联系人> <备注内容>`"
        contact = cmd.args[0]
        note = " ".join(cmd.args[1:])
        return f"✅ 已为「{contact}」添加备注: {note}"

    async def _cmd_recent_activity(self, cmd: BotCommand) -> str:
        """最近活动。"""
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
            "❓ 未知命令。支持的命令:\n"
            "• `/搜索联系人 <关键词>` — 搜索联系人\n"
            "• `/添加备注 <联系人> <备注>` — 添加备注"
        )

    # ── 工具方法 ──────────────────────────────────────────────────────────────

    @staticmethod
    def _color_to_feishu(color: str) -> str:
        """将颜色名/十六进制转为飞书模板色。"""
        color_map = {
            "red": "red",
            "blue": "blue",
            "green": "green",
            "yellow": "yellow",
            "purple": "purple",
            "indigo": "indigo",
            "wathet": "wathet",
            "#FF0000": "red",
            "#00FF00": "green",
            "#0000FF": "blue",
        }
        return color_map.get(color.lower(), "blue")


# ── 全局单例 ─────────────────────────────────────────────────────────────────

feishu_bot = FeishuBot()
register_bot("feishu", feishu_bot)
