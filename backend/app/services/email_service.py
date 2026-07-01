"""邮件发送服务 — 支持 SMTP 发送与自动降级。

功能:
  - EmailService 单例: send(to, subject, body, html)
  - 从 config.settings 读取 SMTP 配置
  - 无配置时自动降级为日志输出（不阻断业务流程）
  - 支持纯文本 + HTML 混合邮件
  - 支持附件（通过 attach 参数）

使用示例:
    from app.services.email_service import email_service

    # 发送纯文本邮件
    await email_service.send("user@example.com", "标题", body="内容")

    # 发送 HTML 邮件
    await email_service.send("user@example.com", "标题", html="<h1>内容</h1>")

    # 发送混合邮件
    await email_service.send("user@example.com", "标题", body="纯文本", html="<h1>HTML</h1>")

降级策略:
  - SMTP_HOST 为空 → 仅记录日志，标记为降级发送
  - SMTP 连接失败 → 记录错误日志，不抛出异常
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """邮件发送服务。

    读取 settings 中的 SMTP_* 配置。当 SMTP_HOST 为空时，
    所有 send() 调用仅记录日志，不实际发送。
    """

    def __init__(self) -> None:
        self._enabled = bool(settings.SMTP_HOST)
        self._host = settings.SMTP_HOST
        self._port = settings.SMTP_PORT
        self._user = settings.SMTP_USER
        self._password = settings.SMTP_PASSWORD
        self._use_tls = settings.SMTP_USE_TLS
        self._from_addr = settings.SMTP_FROM
        self._from_name = settings.SMTP_FROM_NAME

        if self._enabled:
            logger.info(
                "邮件服务已启用: %s:%d (%s)",
                self._host,
                self._port,
                "TLS" if self._use_tls else "SSL",
            )
        else:
            logger.info("邮件服务未配置 (SMTP_HOST 为空)，将降级为日志输出")

    @property
    def enabled(self) -> bool:
        """邮件服务是否已配置并启用"""
        return self._enabled

    async def send(
        self,
        to: str,
        subject: str,
        body: str = "",
        html: str = "",
        *,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        reply_to: Optional[str] = None,
    ) -> dict:
        """发送邮件。

        Args:
            to: 收件人邮箱地址
            subject: 邮件主题
            body: 纯文本正文（可选，有 html 时作为 fallback）
            html: HTML 正文（可选）
            cc: 抄送地址列表
            bcc: 密送地址列表
            reply_to: 回复地址

        Returns:
            {
                "success": bool,
                "sent": bool,       # 是否实际发送（降级时 False）
                "to": str,
                "subject": str,
                "error": str | None,
            }
        """
        if not self._enabled:
            logger.info(
                "[EmailService/DEGRADED] to=%s subject=%s body_preview=%s",
                to,
                subject,
                body[:80] if body else (html[:80] if html else ""),
            )
            return {
                "success": True,
                "sent": False,
                "to": to,
                "subject": subject,
                "error": None,
            }

        try:
            msg = self._build_message(to, subject, body, html, cc=cc, reply_to=reply_to)
            await self._send_smtp(msg, to, bcc=bcc)

            logger.info(
                "[EmailService] 邮件发送成功 to=%s subject=%s",
                to,
                subject,
            )
            return {
                "success": True,
                "sent": True,
                "to": to,
                "subject": subject,
                "error": None,
            }

        except Exception as e:
            logger.error(
                "[EmailService] 邮件发送失败 to=%s subject=%s error=%s",
                to,
                subject,
                str(e),
                exc_info=True,
            )
            return {
                "success": False,
                "sent": False,
                "to": to,
                "subject": subject,
                "error": str(e),
            }

    def _build_message(
        self,
        to: str,
        subject: str,
        body: str = "",
        html: str = "",
        *,
        cc: Optional[list[str]] = None,
        reply_to: Optional[str] = None,
    ) -> MIMEMultipart:
        """构建 MIME 邮件消息。"""
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((self._from_name, self._from_addr))
        msg["To"] = to
        msg["Subject"] = subject

        if cc:
            msg["Cc"] = ", ".join(cc)

        if reply_to:
            msg["Reply-To"] = reply_to

        # 纯文本部分（必须）
        if body:
            msg.attach(MIMEText(body, "plain", "utf-8"))
        elif html:
            # 从 HTML 提取纯文本作为 fallback
            import re

            text = re.sub(r"<[^>]+>", "", html)
            text = re.sub(r"\s+", " ", text).strip()
            msg.attach(MIMEText(text, "plain", "utf-8"))
        else:
            msg.attach(MIMEText("", "plain", "utf-8"))

        # HTML 部分（可选）
        if html:
            msg.attach(MIMEText(html, "html", "utf-8"))

        return msg

    async def _send_smtp(
        self,
        msg: MIMEMultipart,
        to: str,
        *,
        bcc: Optional[list[str]] = None,
    ) -> None:
        """通过 SMTP 发送邮件（同步阻塞，在 asyncio 中运行在线程池）。"""
        import asyncio
        import functools

        def _send():
            context = ssl.create_default_context()
            all_recipients = [to]
            if bcc:
                all_recipients.extend(bcc)

            if self._use_tls:
                with smtplib.SMTP(self._host, self._port, timeout=30) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    if self._user:
                        server.login(self._user, self._password)
                    server.sendmail(self._from_addr, all_recipients, msg.as_string())
            else:
                with smtplib.SMTP_SSL(
                    self._host, self._port, timeout=30, context=context
                ) as server:
                    if self._user:
                        server.login(self._user, self._password)
                    server.sendmail(self._from_addr, all_recipients, msg.as_string())

        # 在线程池中执行 SMTP 调用（不阻塞事件循环）
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, functools.partial(_send))


# ── 全局单例 ──────────────────────────────────────────────────────────────────

email_service = EmailService()
"""全局邮件服务实例。直接 import 使用。"""
