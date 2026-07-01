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
            b_purpose = b.purpose if b.purpose else ""
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
