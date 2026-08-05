"""UnifiedPushService — 行业动态推送服务

集成 baize_libs/multi_channel_delivery 模块，
提供三种推送模式（实时推送、定时推送、主动拉取），
支持 stdout / telegram / email 三种投递渠道。

从 config.yaml 读取推送渠道和目标的配置。
"""

from __future__ import annotations

import logging
import os
import sys
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# ── 将 baize_libs 加入 Python 路径 ──────────────────────────────────────
BAIZE_LIBS_PATH = os.path.join(
    "D:\\", "向海容的知识库", "wiki", "wiki", "记忆宫殿",
    "profiles", "evolution", "_shared_sync", "baize_libs",
)
if os.path.isdir(BAIZE_LIBS_PATH) and BAIZE_LIBS_PATH not in sys.path:
    sys.path.insert(0, BAIZE_LIBS_PATH)

# 一定可导入 — 由 task 约束的 import 验证保证
from multi_channel_delivery import (
    StdoutDelivery,
    TelegramDelivery,
    EmailDelivery,
    get_delivery,
    DeliveryBackend,
)

logger = logging.getLogger(__name__)

# ── 推送模式枚举 ─────────────────────────────────────────────────────────


class PushMode(Enum):
    """推送模式"""
    REALTIME = "realtime"       # 实时推送 — API 请求时即时推送
    SCHEDULED = "scheduled"     # 定时推送 — 每日摘要 / 定时汇总
    PULL = "pull"               # 主动拉取 — 用户查看名片时触发


# ── 推送结果数据结构 ─────────────────────────────────────────────────────


@dataclass
class PushResult:
    """单次推送结果"""
    mode: PushMode
    method: str
    channel: str
    status: str          # "ok" | "error" | "skipped"
    message: str
    detail: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ── 配置加载 ─────────────────────────────────────────────────────────────

_DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def load_config(config_path: str = _DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """从 YAML 文件加载推送配置。

    Args:
        config_path: YAML 配置文件路径。默认使用本模块同目录下的 config.yaml。

    Returns:
        配置字典，形如:
        {
            "channels": [
                {"method": "stdout", "enabled": true},
                {"method": "telegram", "enabled": true, "chatId": "..."},
                {"method": "email", "enabled": false, "to": "...", "from": "..."},
            ],
            "modes": {
                "realtime": {"enabled": true, "channels": ["stdout", "telegram"]},
                "scheduled": {"enabled": true, "channels": ["stdout", "email"]},
                "pull": {"enabled": true, "channels": ["stdout"]},
            }
        }
    """
    if not os.path.isfile(config_path):
        logger.warning("推送配置文件不存在: %s，使用默认配置", config_path)
        return _default_config()

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    return cfg


def _default_config() -> dict[str, Any]:
    """返回默认推送配置（仅 stdout，全部启用）。"""
    return {
        "channels": [
            {"method": "stdout", "enabled": True},
        ],
        "modes": {
            "realtime": {"enabled": True, "channels": ["stdout"]},
            "scheduled": {"enabled": True, "channels": ["stdout"]},
            "pull": {"enabled": True, "channels": ["stdout"]},
        },
    }


# ── 统一推送服务 ─────────────────────────────────────────────────────────


class UnifiedPushService:
    """行业动态推送统一服务。

    使用方式:
        svc = UnifiedPushService()
        # 实时推送
        await svc.push_realtime("新用户匹配: ...")
        # 定时推送 (每日摘要)
        await svc.push_scheduled("今日动态: ...")
        # 主动拉取 (用户查看名片时)
        await svc.push_pull("user_123", "你的名片被查看了")
    """

    def __init__(self, config_path: str = _DEFAULT_CONFIG_PATH):
        self._config = load_config(config_path)
        self._backends: dict[str, DeliveryBackend] = {}
        self._init_backends()

    # ── 初始化投递后端 ─────────────────────────────────────────────────

    def _init_backends(self) -> None:
        """根据 config 初始化所有启用的投递后端。"""
        channels = self._config.get("channels", [])
        for ch in channels:
            if not ch.get("enabled", True):
                continue
            method = ch.get("method", "stdout")
            try:
                self._backends[method] = get_delivery(method, config=ch)
            except ValueError as e:
                logger.warning("初始化推送后端 '%s' 失败: %s（跳过）", method, e)

        # 兜底：至少保留 stdout
        if "stdout" not in self._backends:
            self._backends["stdout"] = StdoutDelivery()

    def get_backend(self, method: str) -> DeliveryBackend | None:
        """按名称获取投递后端实例。"""
        return self._backends.get(method)

    # ── 内部推送逻辑 ───────────────────────────────────────────────────

    def _push_to_channels(
        self,
        text: str,
        mode: PushMode,
        subject: str = "",
        override_channels: list[str] | None = None,
    ) -> list[PushResult]:
        """向指定模式绑定的所有渠道推送一条消息。

        Args:
            text: 推送正文。
            mode: 推送模式。
            subject: 推送主题（邮件或摘要场景使用）。
            override_channels: 可选，覆盖配置中该模式绑定的渠道列表。

        Returns:
            PushResult 列表。
        """
        mode_cfg = self._config.get("modes", {}).get(mode.value, {})
        if not mode_cfg.get("enabled", True):
            logger.info("推送模式 '%s' 未启用，跳过推送", mode.value)
            return [PushResult(
                mode=mode, method="none", channel="none",
                status="skipped", message=f"模式 '{mode.value}' 未启用",
            )]

        channels = override_channels or mode_cfg.get("channels", list(self._backends.keys()))
        results: list[PushResult] = []

        for ch_name in channels:
            backend = self._backends.get(ch_name)
            if backend is None:
                results.append(PushResult(
                    mode=mode, method=ch_name, channel=ch_name,
                    status="error", message=f"后端 '{ch_name}' 未初始化",
                ))
                continue

            try:
                resp = backend.send(text, subject=subject)
                results.append(PushResult(
                    mode=mode, method=ch_name, channel=ch_name,
                    status=resp.get("status", "ok"),
                    message=resp.get("message", ""),
                    detail=resp,
                ))
                logger.info("[%s] 推送成功 -> %s: %s", mode.value, ch_name, resp.get("message", ""))
            except Exception as e:
                logger.exception("[%s] 推送失败 -> %s: %s", mode.value, ch_name, e)
                results.append(PushResult(
                    mode=mode, method=ch_name, channel=ch_name,
                    status="error", message=str(e),
                ))

        return results

    # ── 三种推送模式 ───────────────────────────────────────────────────

    def push_realtime(
        self,
        text: str,
        subject: str = "实时动态",
        channels: list[str] | None = None,
    ) -> list[PushResult]:
        """实时推送 — 适合 API 请求时即时发送 (如新匹配、新消息)。

        Args:
            text: 推送内容。
            subject: 推送主题。
            channels: 覆盖渠道列表。

        Returns:
            推送结果列表。
        """
        return self._push_to_channels(text, PushMode.REALTIME, subject, channels)

    def push_scheduled(
        self,
        text: str,
        subject: str = "",
        channels: list[str] | None = None,
    ) -> list[PushResult]:
        """定时推送 — 每日摘要、定时动态汇总。

        Args:
            text: 推送内容（摘要正文）。
            subject: 邮件主题，为空自动生成 "行业动态摘要 - YYYY-MM-DD"。
            channels: 覆盖渠道列表。

        Returns:
            推送结果列表。
        """
        if not subject:
            subject = f"行业动态摘要 - {datetime.now().strftime('%Y-%m-%d')}"
        return self._push_to_channels(text, PushMode.SCHEDULED, subject, channels)

    def push_pull(
        self,
        user_id: str,
        text: str,
        subject: str = "名片动态",
        channels: list[str] | None = None,
    ) -> list[PushResult]:
        """主动拉取推送 — 用户查看名片时触发。

        Args:
            user_id: 目标用户标识（用于日志/个性化）。
            text: 推送内容。
            subject: 推送主题。
            channels: 覆盖渠道列表。

        Returns:
            推送结果列表。
        """
        personalized_text = f"[用户 {user_id}] {text}"
        return self._push_to_channels(personalized_text, PushMode.PULL, subject, channels)

    # ── 便捷方法 ───────────────────────────────────────────────────────

    def reload_config(self, config_path: str = _DEFAULT_CONFIG_PATH) -> None:
        """重新加载配置并重建后端。"""
        self._config = load_config(config_path)
        self._backends.clear()
        self._init_backends()
        logger.info("推送配置已重新加载（%d 个后端）", len(self._backends))


# ── 模块级单例（可选） ───────────────────────────────────────────────────

_default_service: UnifiedPushService | None = None


def get_push_service() -> UnifiedPushService:
    """获取全局默认推送服务实例（单例）。"""
    global _default_service
    if _default_service is None:
        _default_service = UnifiedPushService()
    return _default_service
