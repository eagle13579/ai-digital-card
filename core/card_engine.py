"""
AI名片生成引擎核心逻辑
==================================
CardTemplate — 名片模板定义 (name, fields, layout, styles)
UserCard     — 用户名片数据模型
render_card  — 将模板 + 数据渲染为 HTML / JSON

支持多个模板: 简约 / 商务 / 创意
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# CardTemplate — 名片模板
# ---------------------------------------------------------------------------

@dataclass
class CardTemplate:
    """名片模板类

    Attributes:
        name:        模板名称 (简体中文)
        template_id: 模板唯一标识
        fields:      需要填充的字段列表
        layout:      布局类型 (vertical | horizontal | modern)
        styles:      CSS 样式覆盖字典 (可包含 color, bg, font, border_radius 等)
        description: 模板描述
    """
    name: str
    template_id: str
    fields: List[str] = field(default_factory=list)
    layout: str = "vertical"
    styles: Dict[str, str] = field(default_factory=dict)
    description: str = ""


# ---------------------------------------------------------------------------
# 预置模板
# ---------------------------------------------------------------------------

DEFAULT_TEMPLATES: Dict[str, CardTemplate] = {
    "minimal": CardTemplate(
        name="简约",
        template_id="minimal",
        fields=["name", "title", "company", "phone", "email", "avatar"],
        layout="vertical",
        styles={
            "bg_color": "#ffffff",
            "text_color": "#1a1a2e",
            "accent_color": "#4a6cf7",
            "font_family": "'Inter', -apple-system, sans-serif",
            "border_radius": "12px",
            "shadow": "0 4px 24px rgba(0,0,0,0.08)",
            "card_width": "360px",
        },
        description="简洁白底风格，适合日常社交场合使用",
    ),
    "business": CardTemplate(
        name="商务",
        template_id="business",
        fields=["name", "title", "company", "phone", "email", "avatar", "social_links"],
        layout="horizontal",
        styles={
            "bg_color": "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
            "text_color": "#e0e0e0",
            "accent_color": "#f5a623",
            "font_family": "'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif",
            "border_radius": "16px",
            "shadow": "0 8px 32px rgba(0,0,0,0.25)",
            "card_width": "480px",
            "header_bg": "rgba(255,255,255,0.06)",
        },
        description="深色商务风格，推荐用于正式商业场合",
    ),
    "creative": CardTemplate(
        name="创意",
        template_id="creative",
        fields=["name", "title", "company", "phone", "email", "avatar", "social_links"],
        layout="modern",
        styles={
            "bg_color": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "text_color": "#ffffff",
            "accent_color": "#ffd700",
            "font_family": "'Poppins', 'Inter', sans-serif",
            "border_radius": "24px",
            "shadow": "0 12px 40px rgba(102,126,234,0.35)",
            "card_width": "400px",
            "avatar_border": "3px solid rgba(255,255,255,0.5)",
            "overlay": "rgba(0,0,0,0.15)",
        },
        description="渐变色创意风格，适合设计师 / 创业者等个性展示",
    ),
}


def get_template(template_id: str) -> CardTemplate:
    """获取预置模板，若未找到则返回简约模板"""
    return DEFAULT_TEMPLATES.get(template_id, DEFAULT_TEMPLATES["minimal"])


def list_templates() -> Dict[str, str]:
    """返回模板 ID → 名称 映射"""
    return {tid: tpl.name for tid, tpl in DEFAULT_TEMPLATES.items()}


# ---------------------------------------------------------------------------
# UserCard — 用户名片数据模型
# ---------------------------------------------------------------------------

@dataclass
class SocialLink:
    """社交媒体链接"""
    platform: str       # wechat, linkedin, github, twitter, etc.
    label: str          # 显示文本
    url: str            # 链接


@dataclass
class UserCard:
    """用户名片数据

    Attributes:
        name:         姓名
        title:        职位/头衔
        company:      公司/组织
        phone:        手机号
        email:        邮箱
        avatar:       头像 URL (可选)
        social_links: 社交媒体链接列表
        bio:          个人简介 (可选)
        card_id:      名片唯一识别 ID
        created_at:   创建时间
        template_id:  使用的模板 ID
    """
    name: str = ""
    title: str = ""
    company: str = ""
    phone: str = ""
    email: str = ""
    avatar: str = ""
    social_links: List[SocialLink] = field(default_factory=list)
    bio: str = ""
    card_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    template_id: str = "minimal"

    def to_dict(self) -> Dict[str, Any]:
        """转为普通字典"""
        d = asdict(self)
        d["social_links"] = [asdict(link) for link in self.social_links]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserCard":
        """从字典恢复 UserCard 对象"""
        socials_raw = data.pop("social_links", [])
        card = cls(**data)
        card.social_links = [SocialLink(**s) for s in socials_raw] if socials_raw else []
        return card


# ---------------------------------------------------------------------------
# 渲染引擎
# ---------------------------------------------------------------------------

_TEMPLATE_HTML_MINIMAL = """\
<div class="card-wrapper" style="width:{styles[card_width]};margin:0 auto;">
  <div class="card-inner" style="
    background:{styles[bg_color]};
    color:{styles[text_color]};
    border-radius:{styles[border_radius]};
    box-shadow:{styles[shadow]};
    font-family:{styles[font_family]};
    padding:32px 28px;
    position:relative;
    overflow:hidden;
  ">
    <div class="card-header" style="display:flex;align-items:center;gap:20px;margin-bottom:24px;">
      {avatar_html}
      <div>
        <h1 style="margin:0;font-size:22px;font-weight:700;color:{styles[text_color]};">{name}</h1>
        <p style="margin:4px 0 0;font-size:14px;opacity:0.75;">{title} @ {company}</p>
      </div>
    </div>

    <div class="card-body" style="display:flex;flex-direction:column;gap:12px;">
      <div class="info-row" style="display:flex;align-items:center;gap:10px;font-size:14px;">
        <span style="font-size:16px;">📞</span>
        <a href="tel:{phone}" style="color:{styles[text_color]};text-decoration:none;opacity:0.85;">{phone}</a>
      </div>
      <div class="info-row" style="display:flex;align-items:center;gap:10px;font-size:14px;">
        <span style="font-size:16px;">✉️</span>
        <a href="mailto:{email}" style="color:{styles[accent_color]};text-decoration:none;">{email}</a>
      </div>
      {bio_html}
    </div>
    {social_html}
  </div>
</div>"""

_TEMPLATE_HTML_BUSINESS = """\
<div class="card-wrapper" style="width:{styles[card_width]};margin:0 auto;">
  <div class="card-inner" style="
    background:{styles[bg_color]};
    color:{styles[text_color]};
    border-radius:{styles[border_radius]};
    box-shadow:{styles[shadow]};
    font-family:{styles[font_family]};
    padding:0;
    position:relative;
    overflow:hidden;
  ">
    <!-- 头部区域 -->
    <div class="biz-header" style="
      background:{styles.get('header_bg','rgba(255,255,255,0.06)')};
      padding:28px 28px 20px;
      display:flex;align-items:center;gap:20px;
      border-bottom:1px solid rgba(255,255,255,0.08);
    ">
      {avatar_html}
      <div style="flex:1;">
        <h1 style="margin:0;font-size:24px;font-weight:700;color:{styles[accent_color]};">{name}</h1>
        <p style="margin:4px 0 2px;font-size:14px;opacity:0.9;">{title}</p>
        <p style="margin:0;font-size:13px;opacity:0.6;">🏢 {company}</p>
      </div>
    </div>

    <!-- 联系信息 -->
    <div class="biz-body" style="padding:20px 28px 24px;display:flex;flex-direction:column;gap:14px;">
      <div class="info-row" style="display:flex;align-items:center;gap:12px;font-size:14px;">
        <span style="width:20px;text-align:center;font-size:16px;">📞</span>
        <span>{phone}</span>
      </div>
      <div class="info-row" style="display:flex;align-items:center;gap:12px;font-size:14px;">
        <span style="width:20px;text-align:center;font-size:16px;">✉️</span>
        <a href="mailto:{email}" style="color:{styles[accent_color]};text-decoration:none;">{email}</a>
      </div>
      {bio_html}
    </div>

    {social_html}

    <div class="biz-footer" style="
      text-align:center;padding:12px;font-size:10px;opacity:0.3;
      border-top:1px solid rgba(255,255,255,0.06);
    ">AI 数字名片 · {company}</div>
  </div>
</div>"""

_TEMPLATE_HTML_CREATIVE = """\
<div class="card-wrapper" style="width:{styles[card_width]};margin:0 auto;">
  <div class="card-inner" style="
    background:{styles[bg_color]};
    color:{styles[text_color]};
    border-radius:{styles[border_radius]};
    box-shadow:{styles[shadow]};
    font-family:{styles[font_family]};
    padding:0;
    position:relative;
    overflow:hidden;
  ">
    <!-- 装饰叠加层 -->
    <div style="position:absolute;top:-60px;right:-60px;width:180px;height:180px;
                border-radius:50%;background:rgba(255,255,255,0.06);"></div>
    <div style="position:absolute;bottom:-40px;left:-40px;width:140px;height:140px;
                border-radius:50%;background:rgba(255,255,255,0.05);"></div>

    <!-- 头像区域 — 大图居中 -->
    <div class="creative-avatar" style="
      text-align:center;padding:36px 28px 16px;
      position:relative;z-index:1;
    ">
      {avatar_html_creative}
      <h1 style="margin:12px 0 0;font-size:26px;font-weight:800;letter-spacing:1px;">{name}</h1>
      <p style="margin:4px 0 0;font-size:14px;opacity:0.85;">{title}</p>
      <p style="margin:4px 0 0;font-size:13px;opacity:0.65;">✨ {company}</p>
    </div>

    <!-- 分隔装饰 -->
    <div style="height:2px;margin:0 32px;background:linear-gradient(90deg,transparent,{styles[accent_color]},transparent);opacity:0.4;"></div>

    <!-- 联系信息 -->
    <div class="creative-body" style="padding:20px 28px 24px;position:relative;z-index:1;">
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div style="display:flex;align-items:center;justify-content:center;gap:24px;">
          <a href="tel:{phone}" style="color:{styles[text_color]};text-decoration:none;text-align:center;">
            <div style="width:44px;height:44px;border-radius:50%;background:rgba(255,255,255,0.12);
                        display:flex;align-items:center;justify-content:center;font-size:20px;margin:0 auto 4px;">📞</div>
            <span style="font-size:12px;opacity:0.7;">电话</span>
          </a>
          <a href="mailto:{email}" style="color:{styles[text_color]};text-decoration:none;text-align:center;">
            <div style="width:44px;height:44px;border-radius:50%;background:rgba(255,255,255,0.12);
                        display:flex;align-items:center;justify-content:center;font-size:20px;margin:0 auto 4px;">✉️</div>
            <span style="font-size:12px;opacity:0.7;">邮件</span>
          </a>
        </div>
      </div>
      {bio_html}
    </div>

    {social_html}
  </div>
</div>"""

_LAYOUT_MAP = {
    "minimal": _TEMPLATE_HTML_MINIMAL,
    "vertical": _TEMPLATE_HTML_MINIMAL,
    "business": _TEMPLATE_HTML_BUSINESS,
    "horizontal": _TEMPLATE_HTML_BUSINESS,
    "creative": _TEMPLATE_HTML_CREATIVE,
    "modern": _TEMPLATE_HTML_CREATIVE,
}


def _build_avatar_html(user_card: UserCard, style_key: str = "default") -> str:
    """构建头像 HTML 片段"""
    if user_card.avatar:
        if style_key == "creative":
            return f'<img src="{user_card.avatar}" alt="" style="width:100px;height:100px;border-radius:50%;border:{user_card.styles.get("avatar_border","3px solid rgba(255,255,255,0.5)")};object-fit:cover;display:inline-block;">'
        return f'<img src="{user_card.avatar}" alt="" style="width:64px;height:64px;border-radius:50%;object-fit:cover;flex-shrink:0;">'
    # 无头像时显示首字母
    initial = user_card.name[0] if user_card.name else "?"
    if style_key == "creative":
        return f'<div style="width:100px;height:100px;border-radius:50%;background:rgba(255,255,255,0.15);display:inline-flex;align-items:center;justify-content:center;font-size:36px;font-weight:600;">{initial}</div>'
    return f'<div style="width:64px;height:64px;border-radius:50%;background:rgba(255,255,255,0.10);display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:600;flex-shrink:0;">{initial}</div>'


def _build_bio_html(user_card: UserCard) -> str:
    """构建简介 HTML 片段"""
    if not user_card.bio:
        return ""
    return f'<div class="bio" style="margin-top:4px;font-size:13px;opacity:0.7;border-left:2px solid currentColor;padding-left:10px;">{user_card.bio}</div>'


def _build_social_html(user_card: UserCard, styles: Dict[str, str]) -> str:
    """构建社交媒体链接 HTML 片段"""
    if not user_card.social_links:
        return ""
    links_html = "".join(
        f'<a href="{link.url}" target="_blank" rel="noopener noreferrer" '
        f'style="display:inline-flex;align-items:center;gap:6px;padding:6px 14px;'
        f'border-radius:20px;background:rgba(255,255,255,0.08);color:{styles.get("text_color","#fff")};'
        f'text-decoration:none;font-size:12px;transition:background 0.2s;" '
        f'onmouseover="this.style.background=\'rgba(255,255,255,0.16)\'" '
        f'onmouseout="this.style.background=\'rgba(255,255,255,0.08)\'">'
        f'{_platform_icon(link.platform)}{link.label}</a>'
        for link in user_card.social_links
    )
    return f'<div class="social-links" style="display:flex;flex-wrap:wrap;gap:8px;margin-top:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.08);">{links_html}</div>'


def _platform_icon(platform: str) -> str:
    """返回平台对应 emoji 图标"""
    icons = {
        "wechat": "💬",
        "linkedin": "🔗",
        "github": "💻",
        "twitter": "🐦",
        "weibo": "📱",
        "website": "🌐",
        "email": "✉️",
    }
    return icons.get(platform.lower(), "🔗")


def render_card(
    template: CardTemplate,
    user_card: UserCard,
    output_format: str = "html",
    extra_styles: Optional[Dict[str, str]] = None,
) -> str:
    """将模板与用户数据结合，渲染名片

    Args:
        template:      使用的模板对象
        user_card:     用户名片数据
        output_format: "html" 或 "json"
        extra_styles:  额外样式覆盖

    Returns:
        渲染后的 HTML 字符串 或 JSON 字符串
    """
    if output_format == "json":
        return json.dumps({
            "template": {"id": template.template_id, "name": template.name},
            "card": user_card.to_dict(),
        }, ensure_ascii=False, indent=2)

    # 获取布局模板
    layout_key = template.layout if template.layout in _LAYOUT_MAP else template.template_id
    html_template = _LAYOUT_MAP.get(layout_key, _TEMPLATE_HTML_MINIMAL)

    # 合并样式: 模板预设 + 额外覆盖
    styles = dict(template.styles)
    if extra_styles:
        styles.update(extra_styles)

    user_card.styles = styles  # for avatar helper

    avatar_html = _build_avatar_html(user_card, template.template_id)
    avatar_html_creative = _build_avatar_html(user_card, "creative")
    bio_html = _build_bio_html(user_card)
    social_html = _build_social_html(user_card, styles)

    rendered = html_template.format(
        name=user_card.name,
        title=user_card.title,
        company=user_card.company,
        phone=user_card.phone,
        email=user_card.email,
        avatar=user_card.avatar,
        avatar_html=avatar_html,
        avatar_html_creative=avatar_html_creative,
        bio_html=bio_html,
        social_html=social_html,
        styles=styles,
    )

    # 包裹完整 HTML 文档
    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>{user_card.name} - AI 数字名片</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Poppins:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      padding: 20px;
    }}
    @media (prefers-color-scheme: dark) {{
      body {{ background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); }}
    }}
    a:hover {{ opacity: 0.8; }}
    @media (max-width: 480px) {{
      .card-wrapper {{ width: 100% !important; }}
    }}
  </style>
</head>
<body>
  {rendered}
</body>
</html>"""

    return full_html
