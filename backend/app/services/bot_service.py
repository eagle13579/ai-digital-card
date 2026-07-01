"""IM 机器人服务基类 — 配置驱动 + 自动降级。

所有平台机器人继承此基类，实现统一的 send_message / send_card / handle_command 接口。
当平台 TOKEN/密钥未配置时自动降级到日志输出，不抛出异常。
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# ── 数据模型 ─────────────────────────────────────────────────────────────────


@dataclass
class BotMessage:
    """机器人消息体（平台无关的中间表示）。"""

    text: str = ""
    """纯文本内容"""
    blocks: list[dict[str, Any]] = field(default_factory=list)
    """结构化块（各平台原生格式），发送时优先于 text"""
    attachments: list[dict[str, Any]] = field(default_factory=list)
    """附件（富媒体、按钮等）"""
    channel: str = ""
    """目标频道/群聊 ID"""
    user_id: str = ""
    """目标用户 ID（私信时使用）"""
    thread_ts: str = ""
    """回复线程的父消息时间戳（Slack 专属）"""


@dataclass
class BotCard:
    """机器人卡片消息（平台无关的中间表示）。"""

    title: str = ""
    """卡片标题"""
    content: str = ""
    """卡片正文（Markdown 或纯文本）"""
    buttons: list[dict[str, str]] = field(default_factory=list)
    """按钮列表: [{"label": "查看详情", "url": "https://..."}, ...]"""
    image_url: str = ""
    """可选图片 URL"""
    color: str = ""
    """卡片主题色 (十六进制 #RRGGBB 或命名色)"""
    channel: str = ""
    """目标频道"""
    user_id: str = ""
    """目标用户"""


@dataclass
class BotCommand:
    """解析后的机器人命令。"""

    command: str = ""
    """命令名称 (如 /search-contact)"""
    args: list[str] = field(default_factory=list)
    """命令参数列表"""
    raw_text: str = ""
    """原始命令文本"""
    user_id: str = ""
    """发起命令的用户"""
    channel: str = ""
    """命令来源频道"""
    platform: str = ""
    """来源平台 (slack / feishu / dingtalk)"""


# ── 基类 ─────────────────────────────────────────────────────────────────────


class BotBase(ABC):
    """机器人服务基类。

    子类需实现:
      - _platform_send_message(msg)     — 发送消息
      - _platform_send_card(card)       — 发送卡片
      - _platform_handle_command(cmd)   — 处理命令
      - _platform_name                  — 平台名称字符串
    """

    def __init__(self) -> None:
        self._enabled: bool = self._check_config()
        if not self._enabled:
            logger.info(
                "%s 机器人未配置 Token/Secret — 已降级到日志输出模式",
                self._platform_name,
            )

    # ── 子类必须实现的接口 ────────────────────────────────────────────────────

    @property
    @abstractmethod
    def _platform_name(self) -> str:
        """平台名称，用于日志标识。"""

    @abstractmethod
    def _check_config(self) -> bool:
        """检查平台配置是否完整。返回 True 表示可以真实发送。"""

    @abstractmethod
    async def _platform_send_message(self, msg: BotMessage) -> dict[str, Any]:
        """平台原生发送消息实现。"""

    @abstractmethod
    async def _platform_send_card(self, card: BotCard) -> dict[str, Any]:
        """平台原生发送卡片实现。"""

    @abstractmethod
    async def _platform_handle_command(self, cmd: BotCommand) -> str:
        """平台原生命令处理。返回回复文本。"""

    # ── 降级感知的公开接口 ────────────────────────────────────────────────────

    async def send_message(self, msg: BotMessage) -> dict[str, Any]:
        """发送一条消息。未配置时降级到日志输出。"""
        if not self._enabled:
            logger.info("[%s 降级] send_message: %s", self._platform_name, msg.text)
            return {"ok": True, "degraded": True, "text": msg.text}

        try:
            result = await self._platform_send_message(msg)
            logger.debug("[%s] send_message ok: %s", self._platform_name, msg.text[:80])
            return result
        except Exception as exc:
            logger.error(
                "[%s] send_message 失败: %s", self._platform_name, exc, exc_info=True
            )
            return {"ok": False, "error": str(exc)}

    async def send_card(self, card: BotCard) -> dict[str, Any]:
        """发送一张卡片。未配置时降级到日志输出。"""
        if not self._enabled:
            logger.info(
                "[%s 降级] send_card: %s - %s",
                self._platform_name,
                card.title,
                card.content[:60],
            )
            return {"ok": True, "degraded": True, "title": card.title}

        try:
            result = await self._platform_send_card(card)
            logger.debug("[%s] send_card ok: %s", self._platform_name, card.title)
            return result
        except Exception as exc:
            logger.error(
                "[%s] send_card 失败: %s", self._platform_name, exc, exc_info=True
            )
            return {"ok": False, "error": str(exc)}

    async def handle_command(self, cmd: BotCommand) -> str:
        """处理一个斜杠命令。未配置时降级返回提示信息。"""
        if not self._enabled:
            logger.info(
                "[%s 降级] handle_command: /%s (args=%s)",
                self._platform_name,
                cmd.command,
                cmd.args,
            )
            return (
                f"⚠️ {self._platform_name} 机器人未配置，"
                f"命令 /{cmd.command} 无法执行。请配置平台 Token 后重试。"
            )

        try:
            reply = await self._platform_handle_command(cmd)
            logger.debug(
                "[%s] handle_command /%s → %s",
                self._platform_name,
                cmd.command,
                reply[:60],
            )
            return reply
        except Exception as exc:
            logger.error(
                "[%s] handle_command /%s 异常: %s",
                self._platform_name,
                cmd.command,
                exc,
                exc_info=True,
            )
            return f"❌ 命令 /{cmd.command} 执行失败: {exc}"

    # ── 通用辅助方法 ──────────────────────────────────────────────────────────

    @staticmethod
    def _now_ts() -> str:
        """返回当前 Unix 时间戳字符串（毫秒）。"""
        return str(int(time.time() * 1000))

    @staticmethod
    def _hmac_sha256(secret: str, body: bytes) -> str:
        """HMAC-SHA256 签名，返回十六进制字符串。"""
        return hmac.new(
            secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _base64url(data: bytes) -> str:
        """标准 base64url 编码（无填充）。"""
        import base64
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    # ── 异常安全 HTTP 请求 ───────────────────────────────────────────────────

    async def _http_post(
        self, url: str, json_data: dict[str, Any], headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """发送 HTTP POST 请求，返回 JSON 响应。失败时抛出异常。"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=json_data, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def _http_get(
        self, url: str, headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """发送 HTTP GET 请求，返回 JSON 响应。"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()


# ── 机器人注册表 ─────────────────────────────────────────────────────────────

_bot_registry: dict[str, BotBase] = {}


def register_bot(platform: str, bot: BotBase) -> None:
    """注册一个机器人实例到全局注册表。"""
    _bot_registry[platform] = bot
    logger.info("机器人已注册: %s (启用=%s)", platform, bot._enabled)


def get_bot(platform: str) -> BotBase | None:
    """按平台名获取机器人实例。"""
    return _bot_registry.get(platform)


def get_enabled_bots() -> list[tuple[str, BotBase]]:
    """获取所有已启用的机器人列表。"""
    return [(name, bot) for name, bot in _bot_registry.items() if bot._enabled]


def list_bots() -> dict[str, bool]:
    """列出所有注册的机器人及其启用状态。"""
    return {name: bot._enabled for name, bot in _bot_registry.items()}
