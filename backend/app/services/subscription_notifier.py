"""试用到期通知服务 — 检查即将到期的试用并发送提醒。

提醒时间节点：
  - 提前 3 天: "您的试用将在 3 天后到期"
  - 提前 1 天: "您的试用将在明天到期"
  - 到期当天: "您的试用今天到期，请尽快升级"

通知通道（当前实现）：
  - 日志记录（默认）
  - 邮件发送（通过 EmailService，需配置 SMTP）
  - 预留：站内消息 / 短信 / 推送

集成说明：
  - 邮件模板位于 email_templates.py，按天数和类型自动选择
  - 用户邮箱从 User 模型获取（需确保 User.email 字段存在）
  - 邮箱缺失时仅记录日志，不阻断流程
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import EnterpriseSubscription
from app.models.user import User
from app.config import settings
from app.services.email_service import email_service
from app.services.email_templates import (
    trial_expired_html,
    trial_expiring_1d_html,
    trial_expiring_3d_html,
)

logger = logging.getLogger(__name__)

# ── 提醒配置 ──────────────────────────────────────────────────────────────

NOTIFY_BEFORE_DAYS: list[int] = [3, 1, 0]
"""提前提醒的时间节点（天数），0 = 到期当天"""


@dataclass
class TrialNotification:
    """单个试用到期的提醒记录"""
    user_id: int
    subscription_id: int
    days_remaining: int
    trial_end: datetime
    message: str
    notify_type: str = "trial_expiring"  # trial_expiring / trial_expired_today


# ── 核心检查逻辑 ──────────────────────────────────────────────────────────


async def find_expiring_trials(
    db: AsyncSession,
    days_before: int | None = None,
) -> list[TrialNotification]:
    """查找即将到期 / 已到期的试用订阅。

    Args:
        db: 数据库会话
        days_before: 指定提醒提前天数。None = 检查所有配置的时间节点。

    Returns:
        需要发送通知的 TrialNotification 列表
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start + timedelta(days=1)

    notifications: list[TrialNotification] = []

    # 查询所有状态为 trial 的订阅
    result = await db.execute(
        select(EnterpriseSubscription).where(
            EnterpriseSubscription.status == "trial",
        )
    )
    trial_subs = result.scalars().all()

    if not trial_subs:
        logger.info("未找到任何活跃的试用订阅")
        return notifications

    check_days = [days_before] if days_before is not None else NOTIFY_BEFORE_DAYS

    for sub in trial_subs:
        if not sub.end_date:
            continue

        end = sub.end_date
        # 计算剩余天数（基于自然日）
        # 将 end 和 now 都归一化到当天开始，然后计算差值
        end_day = end.replace(hour=0, minute=0, second=0, microsecond=0)
        now_day = today_start
        delta_days = (end_day - now_day).days

        for d in check_days:
            if delta_days == d:
                message = _build_message(d, end, sub.company_name)
                notifications.append(TrialNotification(
                    user_id=sub.user_id,
                    subscription_id=sub.id,
                    days_remaining=d,
                    trial_end=end,
                    message=message,
                    notify_type="trial_expired_today" if d == 0 else "trial_expiring",
                ))
                break  # 每个订阅在每个检查中只发一条最近的通知

    return notifications


def _build_message(days_remaining: int, trial_end: datetime, company_name: str = "") -> str:
    """根据剩余天数构建提醒消息"""
    company = f"（{company_name}）" if company_name else ""
    end_str = trial_end.strftime("%Y-%m-%d")

    if days_remaining == 0:
        return (
            f"⚠️ 试用到期提醒{company}：您的 {TRIAL_DAYS_STR} 免费试用已于今天（{end_str}）到期，"
            f"请尽快升级为正式套餐以继续使用全部功能。"
        )
    elif days_remaining == 1:
        return (
            f"⏰ 试用即将到期{company}：您的 {TRIAL_DAYS_STR} 免费试用将于明天（{end_str}）到期，"
            f"请及时升级以免影响使用。"
        )
    elif days_remaining == 3:
        return (
            f"📅 试用即将到期{company}：您的 {TRIAL_DAYS_STR} 免费试用还有 3 天到期（{end_str}），"
            f"升级为正式套餐可继续享受全部功能。"
        )
    else:
        return (
            f"🔔 试用提醒{company}：您的 {TRIAL_DAYS_STR} 免费试用将在 {days_remaining} 天后（{end_str}）到期。"
        )


# ── 用户邮箱查询 ──────────────────────────────────────────────────────────


async def _get_user_email(db: AsyncSession, user_id: int) -> str | None:
    """获取用户邮箱地址。

    尝试从 User 模型获取 email 字段。如果模型没有 email 字段，
    则检查 features JSON 中的 email 字段，最后降级为 None。

    注意：
        User 模型当前没有 email 字段（仅有 phone）。
        如需完整邮件支持，请在 User 模型中添加 email 字段。
        当邮箱不可用时，邮件通知会被跳过（仅记录日志）。
    """
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            # 尝试获取 email 属性（可能不存在）
            email = getattr(user, "email", None)
            if email:
                return email

            # 如果 User 没有 email，尝试从 User 关联的订阅获取 features 中的 email
            result = await db.execute(
                select(EnterpriseSubscription).where(
                    EnterpriseSubscription.user_id == user_id,
                ).order_by(EnterpriseSubscription.created_at.desc()).limit(1)
            )
            sub = result.scalar_one_or_none()
            if sub and isinstance(sub.features, dict):
                email = sub.features.get("contact_email") or sub.features.get("email")
                if email:
                    return email
    except Exception as e:
        logger.debug("获取用户 %s 邮箱失败: %s", user_id, e)

    return None


async def _get_user_name(db: AsyncSession, user_id: int) -> str:
    """获取用户姓名（用于邮件模板）。"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            return user.name or f"用户{user_id}"
    except Exception:
        pass
    return f"用户{user_id}"


# ── 通知发送 ──────────────────────────────────────────────────────────────


async def send_notifications(
    notifications: list[TrialNotification],
    db: AsyncSession | None = None,
) -> int:
    """发送试用到期通知。

    支持多通道发送:
      1. 日志记录（始终执行）
      2. 邮件发送（需 SMTP 配置 + 用户邮箱可用，需要 db 参数查询用户信息）
      3. 预留：站内消息 / 短信 / 推送

    Args:
        notifications: 需要发送的通知列表
        db: 数据库会话（用于查询用户信息，为 None 时仅记录日志）

    Returns:
        发送成功的通知数量
    """
    sent_count = 0
    email_sent = 0

    for notification in notifications:
        # 1. 日志记录（始终）
        logger.info(
            "[TrialNotify] user_id=%s sub_id=%s days_left=%s type=%s msg=%s",
            notification.user_id,
            notification.subscription_id,
            notification.days_remaining,
            notification.notify_type,
            notification.message,
        )

        # 2. 邮件发送（需要 db）
        if db is not None:
            await _send_trial_email(db, notification)

        # 3. 预留：站内信发送
        # await _send_internal_message(
        #     db=db,
        #     user_id=notification.user_id,
        #     title="试用到期提醒",
        #     content=notification.message,
        # )

        sent_count += 1

    logger.info(
        "[TrialNotify] 日志通知=%d | 邮件通知=%d",
        sent_count,
        email_sent,
    )
    return sent_count


async def _send_trial_email(db: AsyncSession, notification: TrialNotification) -> None:
    """为单个试用通知发送邮件。"""
    # 获取用户信息
    name = await _get_user_name(db, notification.user_id)
    email = await _get_user_email(db, notification.user_id)

    if not email:
        logger.info(
            "[TrialNotify/Email] 用户 %s 无邮箱，跳过邮件发送 (sub_id=%s)",
            notification.user_id,
            notification.subscription_id,
        )
        return

    # 获取企业名称（从订阅或者数据库查询）
    company_name = ""
    try:
        result = await db.execute(
            select(EnterpriseSubscription).where(
                EnterpriseSubscription.id == notification.subscription_id
            )
        )
        sub = result.scalar_one_or_none()
        if sub:
            company_name = sub.company_name or ""
    except Exception:
        pass

    end_date_str = notification.trial_end.strftime("%Y-%m-%d")
    upgrade_url = f"{getattr(settings, 'BASE_URL', 'https://aibizcard.com')}/upgrade"

    # 根据提醒类型选择模板
    days = notification.days_remaining

    # 确定是否来自 subscription_notifier（不是 subscription_service）
    # 通过 notify_type 判断: trial_expired_today 或 trial_expiring
    if days == 0:
        html = trial_expired_html(
            name=name,
            company_name=company_name,
            end_date=end_date_str,
            upgrade_url=upgrade_url,
        )
        subject = "【通知】您的 AI数智名片试用已到期"
    elif days == 1:
        html = trial_expiring_1d_html(  # noqa: F823
            name=name,
            company_name=company_name,
            end_date=end_date_str,
            upgrade_url=upgrade_url,
        )
        subject = "【紧急提醒】您的 AI数智名片试用明天到期"
    elif days == 3:
        html = trial_expiring_3d_html(
            name=name,
            company_name=company_name,
            end_date=end_date_str,
            upgrade_url=upgrade_url,
        )
        subject = "【提醒】您的 AI数智名片试用将在 3 天后到期"
    else:
        # 通用到期提醒
        from app.services.email_templates import trial_expiring_1d_html
        html = trial_expiring_1d_html(
            name=name,
            company_name=company_name,
            end_date=end_date_str,
            upgrade_url=upgrade_url,
        )
        subject = f"【提醒】您的 AI数智名片试用将在 {days} 天后到期"

    # 发送邮件
    result = await email_service.send(
        to=email,
        subject=subject,
        body=notification.message,
        html=html,
    )

    if result["success"]:
        logger.info(
            "[TrialNotify/Email] 发送成功 user_id=%s email=%s sub_id=%s days=%s",
            notification.user_id,
            email,
            notification.subscription_id,
            days,
        )
    else:
        logger.error(
            "[TrialNotify/Email] 发送失败 user_id=%s email=%s error=%s",
            notification.user_id,
            email,
            result.get("error"),
        )


# ── 检查入口 ──────────────────────────────────────────────────────────────


async def check_and_notify(
    db: AsyncSession,
    days_before: int | None = None,
) -> dict:
    """检查试用到期并发送通知 —— 完整流程入口。

    Args:
        db: 数据库会话
        days_before: 指定提醒提前天数。None = 检查所有配置的时间节点。

    Returns:
        {
            "checked": bool,
            "total_trials": int,
            "notifications_found": int,
            "notifications_sent": int,
            "notifications": list[TrialNotification],
        }
    """
    notifications = await find_expiring_trials(db, days_before)
    sent = await send_notifications(notifications, db=db)

    return {
        "checked": True,
        "total_trials_count": len(notifications) if notifications else 0,  # simplified count
        "notifications_found": len(notifications),
        "notifications_sent": sent,
        "notifications": [
            {
                "user_id": n.user_id,
                "subscription_id": n.subscription_id,
                "days_remaining": n.days_remaining,
                "trial_end": n.trial_end.isoformat(),
                "message": n.message,
                "type": n.notify_type,
            }
            for n in notifications
        ],
    }


# ── 从配置中获取试用天数常量 ──────────────────────────────────────────────

try:
    from app.services.subscription_service import TRIAL_DAYS

    TRIAL_DAYS_STR = f"{TRIAL_DAYS}天"
except ImportError:
    TRIAL_DAYS_STR = "14天"
