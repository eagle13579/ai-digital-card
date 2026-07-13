"""公开 Profile 页面路由 — SSR SEO landing page (GET /u/{username})"""

import json
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.brochure import Brochure

router = APIRouter(tags=["公开页面"])

# ── 合规页面（隐私 / 条款 / Cookie） ──────────────────────────────────

PRIVACY_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} - AI数智名片</title>
    <meta name="description" content="{description}">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
               color: #333; background: #f8f9fa; line-height: 1.8; }}
        .container {{ max-width: 860px; margin: 0 auto; padding: 40px 20px; }}
        h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; color: #1a1a2e; }}
        h2 {{ font-size: 1.3rem; margin-top: 2rem; margin-bottom: 0.8rem; color: #1a1a2e;
              border-bottom: 2px solid #e0e0e0; padding-bottom: 0.3rem; }}
        p, li {{ font-size: 0.95rem; color: #555; }}
        ul {{ padding-left: 1.5rem; }}
        li {{ margin-bottom: 0.4rem; }}
        .meta {{ color: #999; font-size: 0.85rem; margin-bottom: 2rem; }}
        .footer {{ margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #e0e0e0;
                   text-align: center; color: #999; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p class="meta">最后更新：{last_updated}</p>
        {content}
        <div class="footer">
            <p>&copy; AI数智名片 &mdash; 如有疑问请联系 support@liankebao.top</p>
        </div>
    </div>
</body>
</html>"""


@router.get("/privacy", response_class=HTMLResponse, include_in_schema=True)
async def privacy_policy():
    """隐私政策页面 — 满足个人信息保护法 / GDPR 透明度要求。"""
    title = "隐私政策"
    description = "AI数智名片隐私政策 — 了解我们如何收集、使用和保护您的个人信息。"
    last_updated = "2025年6月1日"
    content = """
    <h2>一、信息收集</h2>
    <p>我们仅收集为您提供服务所必需的信息，包括：</p>
    <ul>
        <li><strong>账户信息</strong>：手机号、用户名、头像等注册信息。</li>
        <li><strong>名片资料</strong>：您创建的个人/企业名片中的姓名、职位、公司、简介等。</li>
        <li><strong>使用数据</strong>：页面访问记录、匹配交互、浏览行为等匿名统计数据。</li>
        <li><strong>设备信息</strong>：IP 地址、浏览器类型、操作系统等基础技术信息。</li>
    </ul>

    <h2>二、信息使用</h2>
    <p>收集的信息仅用于以下目的：</p>
    <ul>
        <li>提供、维护和改善我们的服务；</li>
        <li>AI 匹配推荐和个性化内容展示；</li>
        <li>平台安全运营和反滥用检测；</li>
        <li>根据您的同意发送必要的服务通知。</li>
    </ul>
    <p>我们不会将您的个人信息出售给第三方。在获得您明确同意前，不会将数据用于上述范围之外的用途。</p>

    <h2>三、数据存储与保护</h2>
    <p>您的数据存储在阿里云（中国大陆）的安全服务器上。我们采用行业标准的加密技术（TLS 1.3）传输数据，并对敏感数据实施静态加密。我们定期进行安全审计和渗透测试。</p>

    <h2>四、您的权利</h2>
    <p>根据《个人信息保护法》和 GDPR，您享有以下权利：</p>
    <ul>
        <li><strong>访问权</strong>：通过「设置 → 数据导出」获取您的所有个人数据。</li>
        <li><strong>更正权</strong>：在个人资料页面随时修改您的信息。</li>
        <li><strong>删除权（被遗忘权）</strong>：通过「设置 → 删除账户」执行账户匿名化。</li>
        <li><strong>撤回同意</strong>：在 Cookie 偏好设置中随时撤回分析/营销类同意。</li>
    </ul>

    <h2>五、Cookie 政策</h2>
    <p>我们使用必要的 Cookie 以确保服务正常运行。分析类和广告类 Cookie 仅在您同意后启用。详情请查看我们的 <a href="/cookies">Cookie 政策</a>。</p>

    <h2>六、第三方服务</h2>
    <p>我们的服务可能集成以下第三方 SDK：微信登录、百度统计、阿里云（存储/CDN），这些服务商的数据处理受其各自隐私政策约束。</p>

    <h2>七、联系方式</h2>
    <p>如您对隐私实践有任何疑问或投诉，请联系我们的数据保护官：<br>
    邮箱：privacy@liankebao.top<br>
    地址：中国（具体地址见营业执照）</p>

    <h2>八、政策更新</h2>
    <p>我们可能不时更新本隐私政策。重大变更将通过站内通知或邮件告知您。继续使用服务即表示您同意更新后的政策。</p>
    """
    html = PRIVACY_HTML_TEMPLATE.format(
        title=title,
        description=description,
        last_updated=last_updated,
        content=content,
    )
    return HTMLResponse(html)


@router.get("/terms", response_class=HTMLResponse, include_in_schema=True)
async def terms_of_service():
    """服务条款页面 — 平台使用规则与用户协议。"""
    title = "服务条款"
    description = "AI数智名片服务条款 — 使用本平台即表示您同意以下条款。"
    last_updated = "2025年6月1日"
    content = """
    <h2>一、服务说明</h2>
    <p>AI数智名片是一个基于 AI 的商业社交与名片管理平台。我们提供：名片创建与管理、AI 智能匹配、商务社交网络、CRM 客户管理等功能。</p>

    <h2>二、用户义务</h2>
    <ul>
        <li>您必须提供真实、准确的注册信息。</li>
        <li>您对账户下的所有活动负责，请妥善保管登录凭证。</li>
        <li>不得利用平台从事违法活动、发送垃圾信息、侵犯他人权益。</li>
        <li>不得反向工程、破解或滥用平台 API。</li>
    </ul>

    <h2>三、知识产权</h2>
    <p>您保留在平台上创建的内容（名片、画册等）的所有权。平台代码、品牌标识和底层技术的知识产权归平台所有。</p>

    <h2>四、服务可用性</h2>
    <p>我们尽力保证 99.9% 的服务可用性，但不对不可抗力因素（如自然灾害、网络攻击、政府行为等）造成的服务中断承担责任。</p>

    <h2>五、付费服务</h2>
    <p>付费会员和增值服务的费用在购买时明示。除非另有约定，已支付的费用不予退还。自动续费服务可在「设置」中随时取消。</p>

    <h2>六、责任限制</h2>
    <p>在法律允许的最大范围内，平台不对因使用服务而产生的间接、附带或惩罚性损害赔偿承担责任。我们的总赔偿金额不超过您在过去 12 个月内支付的费用总额。</p>

    <h2>七、终止</h2>
    <p>任何一方均可随时终止本协议。您可以通过删除账户来终止协议。如您违反本条款，我们保留暂停或终止您账户的权利。</p>

    <h2>八、适用法律</h2>
    <p>本条款受中华人民共和国法律管辖。因本条款引起的争议，双方应协商解决；协商不成的，提交平台运营方所在地有管辖权的法院裁决。</p>
    """
    html = PRIVACY_HTML_TEMPLATE.format(
        title=title,
        description=description,
        last_updated=last_updated,
        content=content,
    )
    return HTMLResponse(html)


@router.get("/cookies", response_class=HTMLResponse, include_in_schema=True)
async def cookie_policy():
    """Cookie 政策页面 — 说明 Cookie 的使用与管理。"""
    title = "Cookie 政策"
    description = "AI数智名片Cookie政策 — 了解我们如何使用 Cookie 和类似技术。"
    last_updated = "2025年6月1日"
    content = """
    <h2>一、什么是 Cookie</h2>
    <p>Cookie 是存储在您设备上的小型文本文件，用于记住您的偏好设置、登录状态和操作行为。</p>

    <h2>二、我们使用的 Cookie 类型</h2>
    <ul>
        <li><strong>必要性 Cookie</strong>（始终启用）：维持登录会话、CSRF 保护、负载均衡。没有这些 Cookie，服务将无法正常运行。</li>
        <li><strong>功能性 Cookie</strong>（需同意）：记住您的语言偏好、主题设置、最近查看的名片。</li>
        <li><strong>分析性 Cookie</strong>（需同意）：百度统计等用于匿名统计页面访问量、用户行为趋势，帮助我们优化产品。</li>
        <li><strong>广告性 Cookie</strong>（需同意）：用于展示相关广告和衡量广告效果（当前未启用）。</li>
    </ul>

    <h2>三、Cookie 有效期</h2>
    <ul>
        <li><strong>会话 Cookie</strong>：关闭浏览器后自动删除。</li>
        <li><strong>持久 Cookie</strong>：最长保留 365 天后自动过期。</li>
    </ul>

    <h2>四、管理 Cookie</h2>
    <p>您可以通过浏览器设置随时删除或阻止 Cookie。但禁用必要性 Cookie 可能导致部分功能无法正常使用。您也可以在平台「设置 → 隐私与安全」中管理您的同意偏好。</p>

    <h2>五、第三方 Cookie</h2>
    <p>我们使用的第三方服务（如百度统计）可能会设置其自己的 Cookie，这些 Cookie 受第三方隐私政策约束。</p>
    """
    html = PRIVACY_HTML_TEMPLATE.format(
        title=title,
        description=description,
        last_updated=last_updated,
        content=content,
    )
    return HTMLResponse(html)


def _escape_html(text: str) -> str:
    """简单 HTML 转义"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _truncate(text: str, max_len: int = 200) -> str:
    """截断文本"""
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "…"


@router.get("/u/{username}", response_class=HTMLResponse)
async def public_profile(
    username: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """SSR 公开用户 Profile 页面（含 OpenGraph + Schema.org 结构化数据）"""
    # ── 查询用户 ──────────────────────────────────────────────────────────
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # ── 查询已发布的画册 ──────────────────────────────────────────────────
    result = await db.execute(
        select(Brochure)
        .where(Brochure.user_id == user.id, Brochure.status == "published")
        .order_by(Brochure.updated_at.desc())
    )
    brochures = result.scalars().all()

    # ── 组装数据 ──────────────────────────────────────────────────────────
    base_url = str(request.base_url).rstrip("/")
    page_url = f"{base_url}/u/{username}"
    avatar_url = user.avatar if user.avatar else f"{base_url}/static/default-avatar.png"

    name = user.name or username
    title = user.title or ""
    company = user.company or ""
    intro = user.intro or ""
    seo_description = _truncate(
        intro or f"{name} 的AI数字名片" + (f" — {title}" if title else ""),
        200,
    )
    og_image = avatar_url

    # ── 构建 brochure cards HTML ────────────────────────────────────────
    brochure_cards_html = ""
    if brochures:
        cards = []
        for b in brochures:
            b_title = _escape_html(b.title)
            b_cover = b.cover if b.cover else ""
            b_purpose_label = _escape_html(
                {
                    "partner": "找合作伙伴",
                    "client": "找客户",
                    "investor": "找投资人",
                    "supplier": "找供应商",
                }.get(b.purpose, b.purpose)
            )
            b_url = f"{base_url}/view/{b.share_token}"
            b_created = b.created_at.strftime("%Y-%m-%d") if b.created_at else ""
            b_desc = _truncate(
                f"{b_purpose_label} · {b.pages_count}页"
                if b_purpose_label
                else f"{b.pages_count}页",
                100,
            )

            cards.append(
                f"""<a href="{b_url}" class="brochure-card">
                    <div class="card-cover"{" style='background-image:url(\"" + _escape_html(b_cover) + "\")'" if b_cover else ""}>
                        <div class="card-cover-fallback">{b_title[0] if b_title else "📄"}</div>
                    </div>
                    <div class="card-body">
                        <h3>{b_title}</h3>
                        <p>{b_desc}</p>
                        <span class="card-date">{b_created}</span>
                    </div>
                </a>"""
            )
        brochure_cards_html = "\n".join(cards)

    # ── Schema.org JSON-LD ────────────────────────────────────────────────
    schema_ld = {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "mainEntity": {
            "@type": "Person",
            "name": name,
            "description": seo_description,
            "image": og_image,
            "url": page_url,
            "jobTitle": title or None,
            "worksFor": {"@type": "Organization", "name": company} if company else None,
        },
        "name": f"{name} 的AI数字名片",
        "description": seo_description,
        "url": page_url,
        "image": og_image,
    }
    # Clean None values
    schema_ld["mainEntity"] = {
        k: v for k, v in schema_ld["mainEntity"].items() if v is not None
    }
    schema_json = json.dumps(schema_ld, ensure_ascii=False)

    # ── 读取模板并填充 ──────────────────────────────────────────────────
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(BASE_DIR, "templates", "public_profile.html")
    with open(template_path, encoding="utf-8") as f:
        html_template = f.read()

    html = html_template.format(
        PAGE_TITLE=_escape_html(f"{name} 的AI数字名片 - AI数智名片"),
        SEO_DESCRIPTION=_escape_html(seo_description),
        OG_TITLE=_escape_html(f"{name} 的AI数字名片"),
        OG_DESCRIPTION=_escape_html(seo_description),
        OG_IMAGE=_escape_html(og_image),
        OG_URL=_escape_html(page_url),
        OG_TYPE="profile",
        SCHEMA_JSON=schema_json,
        USERNAME=_escape_html(username),
        USER_NAME=_escape_html(name),
        USER_INITIAL=_escape_html(name[0] if name else "?"),
        USER_TITLE=_escape_html(title),
        USER_COMPANY=_escape_html(company),
        USER_TITLE_AND_COMPANY=_escape_html(
            f"{title} · {company}" if title and company else (title or company or "")
        ),
        USER_INTRO=_escape_html(intro),
        USER_AVATAR=_escape_html(avatar_url),
        BROCHURE_CARDS=brochure_cards_html or "<div class='empty-state'>暂无公开名片</div>",
    )

    return HTMLResponse(html)
