"""IM 机器人 Webhook 路由 — Slack / 飞书 / 钉钉 三平台回调入口。

路由:
  - POST /api/bot/webhook/{platform}     — 统一回调入口
  - POST /api/bot/slack/webhook           — Slack 专用入口
  - POST /api/bot/feishu/webhook          — 飞书专用入口
  - POST /api/bot/dingtalk/webhook        — 钉钉专用入口

所有平台都实现配置驱动 + 自动降级: 未配置 Token 时返回 200 但 body 标记降级。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.services.bot_service import BotCommand, get_bot, list_bots
from app.services.bot_slack import slack_bot
from app.services.bot_feishu import feishu_bot
from app.services.bot_dingtalk import dingtalk_bot
from app.services.webhook_signer import verify as hmac_verify

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bot", tags=["IM 机器人"])


# ── Webhook 签名校验（BUG-022 修复） ─────────────────────────────────────────


def _platform_webhook_secret(platform: str) -> str:
    """获取各平台 Webhook 签名校验密钥（未配置返回空串）。"""
    if platform == "slack":
        return settings.SLACK_SIGNING_SECRET or ""
    if platform == "feishu":
        # 飞书事件订阅使用加密密钥（Encrypt Key），未单独配置时回退 APP_SECRET
        return getattr(settings, "FEISHU_ENCRYPT_KEY", "") or settings.FEISHU_APP_SECRET or ""
    if platform == "dingtalk":
        return settings.DINGTALK_SECRET or ""
    return ""


def _verify_webhook_signature(platform: str, raw_body: bytes, request: Request) -> bool:
    """校验平台 Webhook 回调签名（HMAC-SHA256，防伪造回调）。

    统一接入 app.services.webhook_signer（HMAC-SHA256 hex 摘要）:
      1. 通用 X-Webhook-Signature 头 — webhook_signer 标准签名，内部调用方统一使用；
      2. 平台原生签名 — Slack v0 / 飞书 X-Lark-Signature / 钉钉 timestamp+sign。
    任一通过即视为有效；签名密钥未配置时 fail-closed 拒绝（防止绕过）。
    """
    headers = {k.lower(): v for k, v in request.headers.items()}
    secret = _platform_webhook_secret(platform)
    if not secret:
        logger.warning("[%s] Webhook 签名密钥未配置，拒绝请求（fail-closed，防伪造回调）", platform)
        return False

    # 1) 通用签名：X-Webhook-Signature = HMAC-SHA256(raw_body, secret) hex
    generic_sig = headers.get("x-webhook-signature", "")
    if generic_sig and hmac_verify(raw_body, generic_sig, secret):
        return True

    # 2) 平台原生签名
    if platform == "slack":
        return slack_bot.verify_slack_signature(raw_body, dict(request.headers))

    if platform == "feishu":
        # 飞书: X-Lark-Signature = base64(hmac_sha256(timestamp + "\n" + body, secret))
        signature = headers.get("x-lark-signature", "")
        timestamp = headers.get("x-lark-request-timestamp", "")
        if not signature or not timestamp:
            return False
        string_to_sign = f"{timestamp}\n".encode("utf-8") + raw_body
        expected = base64.b64encode(
            hmac.new(secret.encode("utf-8"), string_to_sign, hashlib.sha256).digest()
        ).decode("utf-8")
        return hmac.compare_digest(expected, signature)

    if platform == "dingtalk":
        # 钉钉: sign = base64(hmac_sha256(timestamp + "\n" + secret, secret))
        query = dict(request.query_params)
        timestamp = headers.get("x-dingtalk-timestamp", "") or query.get("timestamp", "")
        signature = headers.get("x-dingtalk-signature", "") or query.get("sign", "")
        if not signature or not timestamp:
            return False
        string_to_sign = f"{timestamp}\n{secret}"
        expected = base64.urlsafe_b64encode(
            hmac.new(secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256).digest()
        ).decode("utf-8")
        return hmac.compare_digest(expected, signature)

    return False


# ── 工具函数 ─────────────────────────────────────────────────────────────────


async def _get_body_bytes(request: Request) -> bytes:
    """获取原始请求体 bytes。"""
    return await request.body()


async def _parse_form_data(request: Request) -> dict[str, str]:
    """解析 URL-encoded 表单数据。"""
    form = await request.form()
    return {k: v for k, v in form.items()}


# ── 统一回调入口 ─────────────────────────────────────────────────────────────


@router.post("/webhook/{platform}")
async def bot_webhook(platform: str, request: Request):
    """统一的 IM 平台回调入口。

    根据 platform 路由到对应平台的处理器。
    支持: slack / feishu / dingtalk
    """
    platform = platform.lower().strip()

    bot = get_bot(platform)
    if bot is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"ok": False, "error": f"不支持的平台: {platform}"},
        )

    if not bot._enabled:
        logger.info("[%s] 收到回调但机器人未配置（已降级）", platform)
        return {
            "ok": True,
            "degraded": True,
            "platform": platform,
            "message": f"{platform} 机器人未配置，已忽略回调",
        }

    raw_body = await _get_body_bytes(request)
    content_type = request.headers.get("content-type", "")

    if platform == "slack":
        return await _handle_slack_webhook(request, raw_body, content_type)
    elif platform == "feishu":
        return await _handle_feishu_webhook(request, raw_body, content_type)
    elif platform == "dingtalk":
        return await _handle_dingtalk_webhook(request, raw_body, content_type)
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"ok": False, "error": f"不支持的平台: {platform}"},
        )


# ── 健康检查 ─────────────────────────────────────────────────────────────────


@router.get("/status")
async def bot_status():
    """获取所有机器人注册状态。"""
    return {
        "bots": list_bots(),
        "enabled_count": sum(1 for v in list_bots().values() if v),
    }


# ── 各平台独立入口 ───────────────────────────────────────────────────────────


@router.post("/slack/webhook")
async def slack_webhook(request: Request):
    """Slack Events API / 斜杠命令回调入口。

    处理:
      - url_verification (challenge 响应)
      - 斜杠命令 (slash commands)
      - Event Callbacks (events)
    """
    raw_body = await _get_body_bytes(request)
    content_type = request.headers.get("content-type", "")
    return await _handle_slack_webhook(request, raw_body, content_type)


@router.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    """飞书事件回调入口。"""
    raw_body = await _get_body_bytes(request)
    content_type = request.headers.get("content-type", "")
    return await _handle_feishu_webhook(request, raw_body, content_type)


@router.post("/dingtalk/webhook")
async def dingtalk_webhook(request: Request):
    """钉钉回调入口。"""
    raw_body = await _get_body_bytes(request)
    content_type = request.headers.get("content-type", "")
    return await _handle_dingtalk_webhook(request, raw_body, content_type)


# ── 平台专用处理器 ───────────────────────────────────────────────────────────


async def _handle_slack_webhook(
    request: Request, raw_body: bytes, content_type: str
) -> Response:
    """处理 Slack 回调。"""
    if not slack_bot._enabled:
        return JSONResponse({"ok": True, "degraded": True, "message": "Slack 机器人未配置"})

    # BUG-022 修复: 签名校验（防伪造回调）
    if not _verify_webhook_signature("slack", raw_body, request):
        logger.warning("Slack webhook 签名校验失败，拒绝请求")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"ok": False, "error": "签名校验失败"},
        )

    body_str = raw_body.decode("utf-8")

    # ── url_verification ──────────────────────────────────────────────────
    if content_type and "json" in content_type:
        try:
            data = json.loads(body_str)
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"ok": False, "error": "无效的 JSON 请求体"},
            )

        # Slack URL 验证挑战
        if data.get("type") == "url_verification":
            challenge = data.get("challenge", "")
            return JSONResponse({"challenge": challenge})

        # Event Callback
        if data.get("type") == "event_callback":
            event = data.get("event", {})
            event_type = event.get("type", "")

            if event_type == "app_mention":
                # 被 @提及时的回复
                text = event.get("text", "")
                channel = event.get("channel", "")
                user = event.get("user", "")
                logger.info(
                    "Slack app_mention: user=%s channel=%s text=%s",
                    user, channel, text[:100],
                )

            return JSONResponse({"ok": True})

    # ── 斜杠命令 (application/x-www-form-urlencoded) ─────────────────────
    form_data = await _parse_form_data(request)
    if "command" in form_data and "text" in form_data:
        cmd = slack_bot.parse_slash_command(form_data)
        reply = await slack_bot.handle_command(cmd)
        return JSONResponse({"text": reply, "response_type": "ephemeral"})

    logger.info("Slack webhook 收到未知格式请求: content_type=%s", content_type)
    return JSONResponse({"ok": True})


async def _handle_feishu_webhook(
    request: Request, raw_body: bytes, content_type: str
) -> Response:
    """处理飞书回调。"""
    if not feishu_bot._enabled:
        return JSONResponse({"ok": True, "degraded": True, "message": "飞书机器人未配置"})

    # BUG-022 修复: 签名校验（防伪造回调）
    if not _verify_webhook_signature("feishu", raw_body, request):
        logger.warning("飞书 webhook 签名校验失败，拒绝请求")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"ok": False, "error": "签名校验失败"},
        )

    body_str = raw_body.decode("utf-8")
    try:
        data = json.loads(body_str)
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"ok": False, "error": "无效的 JSON 请求体"},
        )

    # ── URL 验证挑战 ──────────────────────────────────────────────────────
    if data.get("type") == "url_verification":
        challenge = data.get("challenge", "")
        token = data.get("token", "")
        logger.debug("飞书 url_verification: challenge=%s", challenge)
        return JSONResponse({"challenge": challenge})

    # ── 事件回调 ──────────────────────────────────────────────────────────
    event = data.get("event", {})
    event_type = event.get("type", "")
    logger.info("飞书事件: type=%s", event_type)

    # 消息事件: 处理命令
    if event_type == "im.message.receive_v1":
        message = event.get("message", {})
        msg_type = message.get("message_type", "")
        content_raw = message.get("content", "{}")

        if msg_type == "text":
            try:
                content_obj = json.loads(content_raw)
                text = content_obj.get("text", "")
            except (json.JSONDecodeError, TypeError):
                text = content_raw

            # 如果是命令格式 (/xxx)
            if text.startswith("/"):
                parts = text[1:].strip().split()
                cmd = BotCommand(
                    command=parts[0] if parts else "",
                    args=parts[1:] if len(parts) > 1 else [],
                    raw_text=text,
                    user_id=event.get("sender", {}).get("sender_id", {}).get("open_id", ""),
                    channel=message.get("chat_id", ""),
                    platform="feishu",
                )
                reply = await feishu_bot.handle_command(cmd)
                # 飞书需要异步回消息，这里先记录
                logger.info("飞书命令回复: %s", reply[:100])

    return JSONResponse({"ok": True})


async def _handle_dingtalk_webhook(
    request: Request, raw_body: bytes, content_type: str
) -> Response:
    """处理钉钉回调。"""
    if not dingtalk_bot._enabled:
        return JSONResponse({"ok": True, "degraded": True, "message": "钉钉机器人未配置"})

    # BUG-022 修复: 签名校验（防伪造回调）
    if not _verify_webhook_signature("dingtalk", raw_body, request):
        logger.warning("钉钉 webhook 签名校验失败，拒绝请求")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"ok": False, "error": "签名校验失败"},
        )

    body_str = raw_body.decode("utf-8")
    try:
        data = json.loads(body_str)
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"ok": False, "error": "无效的 JSON 请求体"},
        )

    # 钉钉回调包含 msgtype 字段
    msg_type = data.get("msgtype", "")
    logger.info("钉钉回调: msgtype=%s", msg_type)

    if msg_type == "text":
        text = data.get("text", {}).get("content", "")
        if text.startswith("/"):
            parts = text[1:].strip().split()
            cmd = BotCommand(
                command=parts[0] if parts else "",
                args=parts[1:] if len(parts) > 1 else [],
                raw_text=text,
                user_id=data.get("senderId", data.get("senderStaffId", "")),
                channel=data.get("conversationId", ""),
                platform="dingtalk",
            )
            reply = await dingtalk_bot.handle_command(cmd)
            logger.info("钉钉命令回复: %s", reply[:100])

    return JSONResponse({"ok": True})
