"""邮件 HTML 模板 — 集中管理所有业务邮件模板。

所有模板均为 Python 函数，接受关键字参数，返回渲染后的 HTML 字符串。
使用 Python f-string / str.format() 渲染，无外部模板引擎依赖。

模板列表:
  - welcome_html()              — 新用户欢迎
  - trial_expiring_3d_html()    — 试用 3 天后到期
  - trial_expiring_1d_html()    — 试用 1 天后到期
  - trial_expired_html()        — 试用已过期
  - crm_new_contact_html()      — CRM 新联系人通知

所有模板使用统一的邮件 HTML 框架，支持:
  - 浅色主题
  - 响应式布局（inline CSS）
  - 中文友好
  - 品牌色 (#1890ff)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional


# ── 邮件框架 ──────────────────────────────────────────────────────────────────

_MAIL_WRAPPER = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject}</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:'PingFang SC','Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:#f5f5f5;min-width:320px;">
<tr><td style="padding:24px 16px;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" align="center" style="max-width:600px;margin:0 auto;width:100%;">
<!-- Header -->
<tr>
<td style="background:linear-gradient(135deg,#1890ff,#096dd9);border-radius:8px 8px 0 0;padding:32px 24px;text-align:center;">
<h1 style="margin:0;font-size:20px;color:#ffffff;font-weight:600;">{header_title}</h1>
</td>
</tr>
<!-- Body -->
<tr>
<td style="background-color:#ffffff;padding:32px 24px;border-left:1px solid #e8e8e8;border-right:1px solid #e8e8e8;">
{body}
</td>
</tr>
<!-- Footer -->
<tr>
<td style="background-color:#fafafa;border-radius:0 0 8px 8px;padding:16px 24px;border:1px solid #e8e8e8;text-align:center;font-size:12px;color:#999999;">
<p style="margin:4px 0;">AI数智名片 · 让每一次连接更有价值</p>
<p style="margin:4px 0;">此邮件由系统自动发送，请勿回复。</p>
<p style="margin:4px 0;">&copy; {year} AI数智名片 版权所有</p>
</td>
</tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def _render(subject: str, header_title: str, body: str) -> str:
    """用统一框架包裹邮件正文。"""
    return _MAIL_WRAPPER.format(
        subject=subject,
        header_title=header_title,
        body=body,
        year=datetime.now().year,
    )


# ── 常用组件 ──────────────────────────────────────────────────────────────────


def _btn(text: str, url: str) -> str:
    """渲染 CTA 按钮。"""
    return f"""\
<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin:24px auto;">
<tr>
<td style="background-color:#1890ff;border-radius:4px;padding:12px 32px;">
<a href="{url}" target="_blank" style="color:#ffffff;text-decoration:none;font-size:15px;font-weight:500;display:inline-block;">{text}</a>
</td>
</tr>
</table>"""


def _info_row(label: str, value: str) -> str:
    """信息行。"""
    safe_value = value.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    return f"""\
<tr>
<td style="padding:6px 0;color:#666666;font-size:14px;width:80px;vertical-align:top;">{label}</td>
<td style="padding:6px 0;color:#333333;font-size:14px;">{safe_value}</td>
</tr>"""


# ── 模板函数 ──────────────────────────────────────────────────────────────────


def welcome_html(*, name: str, login_url: str = "#") -> str:
    """新用户欢迎邮件。

    Args:
        name: 用户姓名
        login_url: 登录/开始使用链接
    """
    body = f"""\
<p style="margin:0 0 16px;font-size:15px;color:#333333;line-height:1.6;">Hi，{name}，欢迎加入 AI数智名片！</p>
<p style="margin:0 0 16px;font-size:14px;color:#666666;line-height:1.6;">
感谢您注册使用 AI数智名片。通过我们的平台，您可以：
</p>
<ul style="margin:0 0 16px;padding-left:20px;font-size:14px;color:#666666;line-height:1.8;">
<li>创建精美的电子名片，随时随地分享</li>
<li>智能匹配潜在客户，拓展人脉网络</li>
<li>CRM 客户管理，跟进商机一目了然</li>
<li>AI 智能推荐，精准触达目标人群</li>
</ul>
<p style="margin:0 0 8px;font-size:14px;color:#666666;line-height:1.6;">
立即开始，创建您的第一张数字名片！
</p>
{_btn('开始使用', login_url)}"""
    return _render(
        subject="欢迎加入 AI数智名片",
        header_title="🎉 欢迎加入 AI数智名片",
        body=body,
    )


def trial_expiring_3d_html(
    *,
    name: str,
    company_name: str = "",
    end_date: str,
    upgrade_url: str = "#",
) -> str:
    """试用 3 天后到期提醒。

    Args:
        name: 用户姓名
        company_name: 企业名称（可选）
        end_date: 到期日期 (YYYY-MM-DD)
        upgrade_url: 升级链接
    """
    company = f"（{company_name}）" if company_name else ""
    body = f"""\
<p style="margin:0 0 16px;font-size:15px;color:#333333;line-height:1.6;">{name} 您好，</p>
<p style="margin:0 0 16px;font-size:14px;color:#666666;line-height:1.6;">
您的 AI数智名片{company} <strong>14天免费试用</strong> 将于 <strong>{end_date}</strong> 到期，仅剩 <strong>3 天</strong>。
</p>
<p style="margin:0 0 16px;font-size:14px;color:#666666;line-height:1.6;">
升级为正式套餐后，您将可以继续使用全部功能，包括智能匹配、无限访客记录、API 接入等。
</p>
{_btn('立即升级', upgrade_url)}
<p style="margin:16px 0 0;font-size:12px;color:#999999;line-height:1.6;">
💡 提示：升级越早，优惠越多。企业版还支持 SSO 和团队协作功能。
</p>"""
    return _render(
        subject="【提醒】您的 AI数智名片试用将在 3 天后到期",
        header_title="📅 试用即将到期",
        body=body,
    )


def trial_expiring_1d_html(
    *,
    name: str,
    company_name: str = "",
    end_date: str,
    upgrade_url: str = "#",
) -> str:
    """试用 1 天后到期提醒。

    Args:
        name: 用户姓名
        company_name: 企业名称（可选）
        end_date: 到期日期 (YYYY-MM-DD)
        upgrade_url: 升级链接
    """
    company = f"（{company_name}）" if company_name else ""
    body = f"""\
<p style="margin:0 0 16px;font-size:15px;color:#333333;line-height:1.6;">{name} 您好，</p>
<p style="margin:0 0 16px;font-size:14px;color:#666666;line-height:1.6;">
您的 AI数智名片{company} <strong>14天免费试用</strong> 将于 <strong>明天（{end_date}）</strong> 到期！
</p>
<p style="margin:0 0 16px;font-size:14px;color:#E02020;line-height:1.6;">
⚠️ 请及时升级，以免影响您正常使用。
</p>
<p style="margin:0 0 16px;font-size:14px;color:#666666;line-height:1.6;">
升级后所有数据、配置、客户关系将完整保留。
</p>
{_btn('立即升级以免中断', upgrade_url)}"""
    return _render(
        subject="【紧急提醒】您的 AI数智名片试用明天到期",
        header_title="⏰ 试用明天到期",
        body=body,
    )


def trial_expired_html(
    *,
    name: str,
    company_name: str = "",
    end_date: str,
    upgrade_url: str = "#",
) -> str:
    """试用已过期通知。

    Args:
        name: 用户姓名
        company_name: 企业名称（可选）
        end_date: 到期日期 (YYYY-MM-DD)
        upgrade_url: 升级链接
    """
    company = f"（{company_name}）" if company_name else ""
    body = f"""\
<p style="margin:0 0 16px;font-size:15px;color:#333333;line-height:1.6;">{name} 您好，</p>
<p style="margin:0 0 16px;font-size:14px;color:#666666;line-height:1.6;">
您的 AI数智名片{company} <strong>14天免费试用</strong> 已于 <strong>{end_date}</strong> 到期。
</p>
<p style="margin:0 0 16px;font-size:14px;color:#E02020;line-height:1.6;">
⚠️ 您的部分高级功能已受限。
</p>
<p style="margin:0 0 16px;font-size:14px;color:#666666;line-height:1.6;">
升级为正式套餐即可恢复全部功能，并且您的所有数据都完整保留。
</p>
{_btn('升级恢复服务', upgrade_url)}
<p style="margin:16px 0 0;font-size:12px;color:#999999;line-height:1.6;">
标准版仅 ¥99/月，企业版 ¥499/月。支持微信/支付宝付款。
</p>"""
    return _render(
        subject="【通知】您的 AI数智名片试用已到期",
        header_title="⚠️ 试用已到期",
        body=body,
    )


def crm_new_contact_html(
    *,
    owner_name: str,
    contact_name: str,
    contact_company: str = "",
    contact_title: str = "",
    contact_email: str = "",
    contact_phone: str = "",
    source: str = "",
    crm_url: str = "#",
) -> str:
    """CRM 新联系人通知。

    Args:
        owner_name: CRM 所属用户姓名
        contact_name: 新联系人姓名
        contact_company: 公司
        contact_title: 职位
        contact_email: 邮箱
        contact_phone: 电话
        source: 来源描述 (如"名片交换"、"手动添加")
        crm_url: CRM 联系人详情链接
    """
    rows = ""
    if contact_company:
        rows += _info_row("公司", contact_company)
    if contact_title:
        rows += _info_row("职位", contact_title)
    if contact_email:
        rows += _info_row("邮箱", contact_email)
    if contact_phone:
        rows += _info_row("电话", contact_phone)
    if source:
        rows += _info_row("来源", source)

    body = f"""\
<p style="margin:0 0 16px;font-size:15px;color:#333333;line-height:1.6;">{owner_name} 您好，</p>
<p style="margin:0 0 16px;font-size:14px;color:#666666;line-height:1.6;">
您的 CRM 中新增了一位联系人：
</p>
<div style="background-color:#f0f5ff;border:1px solid #d6e4ff;border-radius:6px;padding:16px;margin:0 0 16px;">
<p style="margin:0 0 8px;font-size:16px;color:#1890ff;font-weight:600;">{contact_name}</p>
<table cellpadding="0" cellspacing="0" border="0">
{rows}
</table>
</div>
{_btn('查看联系人', crm_url)}
<p style="margin:16px 0 0;font-size:12px;color:#999999;line-height:1.6;">
💡 您可以为此联系人添加备注、设置商机阶段，或安排后续跟进。
</p>"""
    return _render(
        subject=f"【CRM】新联系人: {contact_name}",
        header_title="👤 新联系人通知",
        body=body,
    )


# ── 邮件营销模板 ────────────────────────────────────────────────────────────────


def campaign_broadcast_html(
    *,
    name: str = "",
    subject: str = "",
    inner_body: str = "",
    unsubscribe_url: str = "#",
    tracking_pixel_url: str = "",
) -> str:
    """邮件营销 — 带追踪像素和退订链接的广播邮件。

    Args:
        name: 收件人姓名
        subject: 邮件主题
        inner_body: 邮件正文 HTML（由具体模板渲染）
        unsubscribe_url: 退订链接
        tracking_pixel_url: 追踪像素 URL（可选，已自动嵌入到 footer）
    """
    pixel_tag = (
        f'<img src="{tracking_pixel_url}" width="1" height="1" '
        f'style="display:none;" alt=""/>'
    ) if tracking_pixel_url else ""

    footer = f"""\
{pixel_tag}
<div style="margin-top:24px;padding-top:16px;border-top:1px solid #e8e8e8;font-size:12px;color:#999999;text-align:center;">
<p style="margin:4px 0;">您收到此邮件是因为您在 AI数智名片 注册或与我们有业务往来。</p>
<p style="margin:4px 0;">
<a href="{unsubscribe_url}" target="_blank" style="color:#1890ff;text-decoration:underline;">点击此处退订</a>
—— 我们尊重您的隐私，退订后将不再向您发送营销邮件。
</p>
<p style="margin:4px 0;">&copy; {datetime.now().year} AI数智名片 版权所有</p>
</div>"""

    body = f"""\
<p style="margin:0 0 16px;font-size:15px;color:#333333;line-height:1.6;">
{inner_body}
</p>
{footer}"""

    return _render(
        subject=subject or "AI数智名片",
        header_title="📧 邮件营销",
        body=body,
    )


def unsubscribe_confirmed_html(
    *,
    email: str = "",
) -> str:
    """退订确认页（纯展示，在 API 中作为 HTML 响应返回）。"""
    body = f"""\
<p style="margin:0 0 16px;font-size:15px;color:#333333;line-height:1.6;text-align:center;">
✅ 您已成功退订
</p>
<p style="margin:0 0 16px;font-size:14px;color:#666666;line-height:1.6;text-align:center;">
{email} 将不再收到 AI数智名片的营销邮件。
</p>
<p style="margin:0 0 16px;font-size:14px;color:#666666;line-height:1.6;text-align:center;">
如果您误操作，请联系管理员重新订阅。
</p>"""
    return _render(
        subject="退订确认",
        header_title="📭 退订成功",
        body=body,
    )
