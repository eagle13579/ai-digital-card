"""
IM 桥接适配器 — 统一企微 (WeCom / 企业微信) + 钉钉 (DingTalk) 消息推送。

提供:
  - 统一的 send / send_message / send_card 接口
  - 平台自动发现与降级 (未配置 → 日志输出)
  - 全局单例 im_bridge

依赖配置项 (settings):
  - WECOM_CORP_ID / WECOM_AGENT_ID / WECOM_SECRET   — 企微
  - DINGTALK_APP_KEY / DINGTALK_APP_SECRET / DINGTALK_AGENT_ID — 钉钉（BUG-018 工作通知）
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
        # access_token 进程内缓存（BUG-018）
        self._token: str = ""
        self._token_expires_at: float = 0.0
        if self._enabled:
            corp_preview = self._corp_id[:6] if len(self._corp_id) > 6 else self._corp_id
            logger.info("企微适配器已就绪 (corp_id=%s...)", corp_preview)
        else:
            logger.warning("企微适配器未配置 (需 WECOM_CORP_ID + WECOM_AGENT_ID), 降级为日志输出")

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ── 企微 access_token 获取（带进程内缓存） ──────────────────────────

    async def _get_access_token(self) -> str:
        """获取企微应用 access_token（缓存 100 分钟，官方有效期 7200s）。"""
        import time as _time

        now = _time.time()
        if self._token and self._token_expires_at > now + 120:
            return self._token

        import httpx
        url = (
            "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            f"?corpid={self._corp_id}&corpsecret={self._secret}"
        )
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            data = resp.json()
        if data.get("errcode") != 0:
            logger.warning("企微 gettoken 失败: %s", data)
            return ""
        self._token = data.get("access_token", "")
        self._token_expires_at = now + int(data.get("expires_in", 7200))
        return self._token

    async def send_message(self, msg: IMMessage) -> dict[str, Any]:
        """发送文本消息到企微（BUG-018：对接真实 应用消息推送 API）"""
        if not self._enabled:
            logger.info("[企微降级] 发给 user=%s: %s", msg.user_id, msg.text)
            return {"platform": "wecom", "status": "degraded", "reason": "未配置"}

        import httpx
        token = await self._get_access_token()
        if not token:
            return {"platform": "wecom", "status": "failed", "error": "access_token 获取失败"}

        # POST https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}",
                    json={
                        "touser": msg.user_id,
                        "msgtype": "text",
                        "agentid": int(self._agent_id) if str(self._agent_id).isdigit() else self._agent_id,
                        "text": {"content": msg.text},
                        "safe": 0,
                    },
                )
                data = resp.json()
            if data.get("errcode") != 0:
                logger.warning("[企微] 发送失败 user=%s: %s", msg.user_id, data)
                return {"platform": "wecom", "status": "failed", "error": data}
            logger.info("[企微] 发送文本消息 user=%s: %s", msg.user_id, msg.text)
            return {
                "platform": "wecom",
                "status": "sent",
                "touser": msg.user_id,
                "msgtype": "text",
                "msgid": data.get("msgid", ""),
            }
        except Exception as e:  # noqa: BLE001
            logger.warning("[企微] 发送文本消息异常: %s", e)
            return {"platform": "wecom", "status": "failed", "error": str(e)}

    async def send_card(self, msg: IMMessage) -> dict[str, Any]:
        """发送卡片消息到企微（BUG-018：对接真实 模板卡片消息 API）"""
        if not self._enabled:
            logger.info("[企微降级] 卡片发给 user=%s: %s", msg.user_id, msg.title)
            return {"platform": "wecom", "status": "degraded", "reason": "未配置"}

        import httpx
        token = await self._get_access_token()
        if not token:
            return {"platform": "wecom", "status": "failed", "error": "access_token 获取失败"}

        # 企微 template_card（text_notice 类型）
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}",
                    json={
                        "touser": msg.user_id,
                        "msgtype": "template_card",
                        "agentid": int(self._agent_id) if str(self._agent_id).isdigit() else self._agent_id,
                        "template_card": {
                            "card_type": "text_notice",
                            "main_title": {"title": msg.title},
                            "sub_title_text": msg.card_data.get("content") or msg.text,
                            "task_id": str(abs(hash(msg.title)) % 1000000),
                        },
                    },
                )
                data = resp.json()
            if data.get("errcode") != 0:
                logger.warning("[企微] 卡片发送失败 user=%s: %s", msg.user_id, data)
                return {"platform": "wecom", "status": "failed", "error": data}
            logger.info("[企微] 发送卡片消息 user=%s: %s", msg.user_id, msg.title)
            return {
                "platform": "wecom",
                "status": "sent",
                "touser": msg.user_id,
                "msgtype": "template_card",
                "msgid": data.get("msgid", ""),
            }
        except Exception as e:  # noqa: BLE001
            logger.warning("[企微] 发送卡片消息异常: %s", e)
            return {"platform": "wecom", "status": "failed", "error": str(e)}


# ── 钉钉适配器 ──────────────────────────────────────────────────────────────


class DingTalkAdapter:
    """钉钉 (DingTalk) 消息适配器

    配置项:
      - DINGTALK_APP_KEY     — 应用 AppKey
      - DINGTALK_APP_SECRET  — 应用 AppSecret
      - DINGTALK_AGENT_ID    — 应用 AgentId（工作通知必填，BUG-018）
    """

    _platform = IMPlatform.DINGTALK

    def __init__(self) -> None:
        self._app_key = getattr(settings, "DINGTALK_APP_KEY", "") or ""
        self._app_secret = getattr(settings, "DINGTALK_APP_SECRET", "") or ""
        self._agent_id = getattr(settings, "DINGTALK_AGENT_ID", "") or ""
        self._enabled = bool(self._app_key and self._agent_id)
        # access_token 进程内缓存（BUG-018，参考企微实现）
        self._token: str = ""
        self._token_expires_at: float = 0.0
        if self._enabled:
            key_preview = self._app_key[:6] if len(self._app_key) > 6 else self._app_key
            logger.info("钉钉适配器已就绪 (app_key=%s..., agent_id=%s)", key_preview, self._agent_id)
        else:
            logger.warning(
                "钉钉适配器未配置 (需 DINGTALK_APP_KEY + DINGTALK_AGENT_ID), 降级为日志输出"
            )

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ── 钉钉 access_token 获取（带进程内缓存，BUG-018） ──────────────

    async def _get_access_token(self) -> str:
        """获取钉钉应用 access_token（缓存 100 分钟，官方有效期 7200s）。

        使用新版 v1.0 oauth2/accessToken 接口；失败时降级尝试旧版 gettoken。
        """
        import time as _time

        now = _time.time()
        if self._token and self._token_expires_at > now + 120:
            return self._token

        import httpx

        # 新版接口: POST https://api.dingtalk.com/v1.0/oauth2/accessToken
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.dingtalk.com/v1.0/oauth2/accessToken",
                    json={"appKey": self._app_key, "appSecret": self._app_secret},
                )
                data = resp.json()
            token = data.get("accessToken") or data.get("access_token")
            if token:
                self._token = token
                self._token_expires_at = now + int(data.get("expireIn", data.get("expires_in", 7200)))
                return self._token
            logger.warning("钉钉 v1.0 gettoken 失败: %s", data)
        except Exception as e:  # noqa: BLE001
            logger.warning("钉钉 v1.0 gettoken 异常: %s", e)

        # 旧版接口降级: GET https://oapi.dingtalk.com/gettoken?appkey=&appsecret=
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://oapi.dingtalk.com/gettoken",
                    params={"appkey": self._app_key, "appsecret": self._app_secret},
                )
                data = resp.json()
            if data.get("errcode") == 0 and data.get("access_token"):
                self._token = data["access_token"]
                self._token_expires_at = now + int(data.get("expires_in", 7200))
                return self._token
            logger.warning("钉钉旧版 gettoken 失败: %s", data)
        except Exception as e:  # noqa: BLE001
            logger.warning("钉钉旧版 gettoken 异常: %s", e)
        return ""

    async def send_message(self, msg: IMMessage) -> dict[str, Any]:
        """发送文本消息到钉钉（BUG-018：对接真实 工作通知消息 API）"""
        if not self._enabled:
            logger.info("[钉钉降级] 发给 user=%s: %s", msg.user_id, msg.text)
            return {"platform": "dingtalk", "status": "degraded", "reason": "未配置"}

        import httpx
        token = await self._get_access_token()
        if not token:
            return {"platform": "dingtalk", "status": "failed", "error": "access_token 获取失败"}

        # POST https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2",
                    params={"access_token": token},
                    json={
                        "agent_id": int(self._agent_id) if str(self._agent_id).isdigit() else self._agent_id,
                        "userid_list": msg.user_id,
                        "msg": {"msgtype": "text", "text": {"content": msg.text}},
                    },
                )
                data = resp.json()
            if data.get("errcode") != 0:
                logger.warning("[钉钉] 发送失败 user=%s: %s", msg.user_id, data)
                return {"platform": "dingtalk", "status": "failed", "error": data}
            logger.info("[钉钉] 发送文本消息 user=%s: %s", msg.user_id, msg.text)
            return {
                "platform": "dingtalk",
                "status": "sent",
                "userid": msg.user_id,
                "msgtype": "text",
                "task_id": data.get("task_id", ""),
            }
        except Exception as e:  # noqa: BLE001
            logger.warning("[钉钉] 发送文本消息异常: %s", e)
            return {"platform": "dingtalk", "status": "failed", "error": str(e)}

    async def send_card(self, msg: IMMessage) -> dict[str, Any]:
        """发送卡片消息到钉钉（BUG-018：对接真实 工作通知 markdown 卡片 API）"""
        if not self._enabled:
            logger.info("[钉钉降级] 卡片发给 user=%s: %s", msg.user_id, msg.title)
            return {"platform": "dingtalk", "status": "degraded", "reason": "未配置"}

        import httpx
        token = await self._get_access_token()
        if not token:
            return {"platform": "dingtalk", "status": "failed", "error": "access_token 获取失败"}

        # 组装 markdown 卡片正文
        title = msg.title or "通知"
        content = msg.card_data.get("content") or msg.text or ""
        lines = [f"### {title}", content]
        for btn in msg.buttons:
            label = btn.get("label", "")
            url = btn.get("url", "")
            if label and url:
                lines.append(f"- [{label}]({url})")
        markdown_text = "\n\n".join(lines)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2",
                    params={"access_token": token},
                    json={
                        "agent_id": int(self._agent_id) if str(self._agent_id).isdigit() else self._agent_id,
                        "userid_list": msg.user_id,
                        "msg": {
                            "msgtype": "markdown",
                            "markdown": {"title": title, "text": markdown_text},
                        },
                    },
                )
                data = resp.json()
            if data.get("errcode") != 0:
                logger.warning("[钉钉] 卡片发送失败 user=%s: %s", msg.user_id, data)
                return {"platform": "dingtalk", "status": "failed", "error": data}
            logger.info("[钉钉] 发送卡片消息 user=%s: %s", msg.user_id, msg.title)
            return {
                "platform": "dingtalk",
                "status": "sent",
                "userid": msg.user_id,
                "msgtype": "markdown",
                "task_id": data.get("task_id", ""),
            }
        except Exception as e:  # noqa: BLE001
            logger.warning("[钉钉] 发送卡片消息异常: %s", e)
            return {"platform": "dingtalk", "status": "failed", "error": str(e)}


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
