import json
from typing import Optional

from app.models.brochure import Brochure


class BrochureRenderer:
    """画册 HTML 渲染器 - 将图册数据渲染为完整 HTML 页面（含用途主题适配）"""

    # 各用途对应的主题色系
    PURPOSE_THEMES = {
        "partner": {
            "primary": "#f5576c",
            "secondary": "#f093fb",
            "gradient": "linear-gradient(90deg, #f093fb, #f5576c)",
            "bg": "linear-gradient(135deg, #1a0a1e, #2d1b3a, #1a0f1e)",
            "accent": "rgba(245,87,108,0.15)",
            "glow": "rgba(245,87,108,0.3)",
            "badge_bg": "rgba(245,87,108,0.15)",
            "badge_color": "#f5576c",
            "badge_border": "rgba(245,87,108,0.25)",
            "highlight_border": "#f5576c",
            "emoji": "🤝",
            "label": "找合作伙伴",
        },
        "client": {
            "primary": "#4ade80",
            "secondary": "#22c55e",
            "gradient": "linear-gradient(90deg, #4ade80, #22c55e)",
            "bg": "linear-gradient(135deg, #0a1a0e, #1a2d1b, #0e1a0f)",
            "accent": "rgba(74,222,128,0.15)",
            "glow": "rgba(74,222,128,0.3)",
            "badge_bg": "rgba(74,222,128,0.15)",
            "badge_color": "#4ade80",
            "badge_border": "rgba(74,222,128,0.25)",
            "highlight_border": "#4ade80",
            "emoji": "💰",
            "label": "找客户",
        },
        "investor": {
            "primary": "#facc15",
            "secondary": "#eab308",
            "gradient": "linear-gradient(90deg, #facc15, #eab308)",
            "bg": "linear-gradient(135deg, #1a1a0a, #2d2d1b, #1a1a0e)",
            "accent": "rgba(250,204,21,0.15)",
            "glow": "rgba(250,204,21,0.3)",
            "badge_bg": "rgba(250,204,21,0.15)",
            "badge_color": "#facc15",
            "badge_border": "rgba(250,204,21,0.25)",
            "highlight_border": "#facc15",
            "emoji": "📈",
            "label": "找投资人",
        },
        "supplier": {
            "primary": "#60a5fa",
            "secondary": "#3b82f6",
            "gradient": "linear-gradient(90deg, #60a5fa, #3b82f6)",
            "bg": "linear-gradient(135deg, #0a0e1a, #1b1f2d, #0e0f1a)",
            "accent": "rgba(96,165,250,0.15)",
            "glow": "rgba(96,165,250,0.3)",
            "badge_bg": "rgba(96,165,250,0.15)",
            "badge_color": "#60a5fa",
            "badge_border": "rgba(96,165,250,0.25)",
            "highlight_border": "#60a5fa",
            "emoji": "🔧",
            "label": "找供应商",
        },
    }

    @staticmethod
    def get_theme(purpose: str) -> dict:
        """获取用途对应的主题配置，无效或空用途返回默认主题"""
        if purpose and purpose in BrochureRenderer.PURPOSE_THEMES:
            return BrochureRenderer.PURPOSE_THEMES[purpose]
        # 默认主题（紫色渐变）
        return {
            "primary": "#f5576c",
            "secondary": "#f093fb",
            "gradient": "linear-gradient(90deg, #f093fb, #f5576c)",
            "bg": "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
            "accent": "rgba(245,87,108,0.15)",
            "glow": "rgba(245,87,108,0.3)",
            "badge_bg": "rgba(245,87,108,0.15)",
            "badge_color": "#f5576c",
            "badge_border": "rgba(245,87,108,0.25)",
            "highlight_border": "#f5576c",
            "emoji": "📇",
            "label": "",
        }

    @staticmethod
    def render_brochure_html(
        brochure: Brochure,
        base_url: str = "",
    ) -> str:
        """将画册数据渲染为完整的翻页图册 HTML

        Args:
            brochure: Brochure 实例（含 pages 关系）
            base_url: 静态资源基础 URL

        Returns:
            完整的 HTML 字符串
        """
        # 获取用途主题
        theme = BrochureRenderer.get_theme(brochure.purpose)

        pages_html = ""
        for page in brochure.pages:
            pages_html += BrochureRenderer._render_page(page, base_url, theme)

        # 解析 album_meta（如果有）
        meta = {}
        if brochure.album_meta:
            try:
                meta = json.loads(brochure.album_meta)
            except (json.JSONDecodeError, TypeError):
                meta = {}

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{brochure.title} - AI数字名片</title>
    <script src="https://cdn.tailwindcss.com" onerror="window.__tailwindFailed=true"></script>
    <script src="https://cdn.jsdelivr.net/npm/stpageflip@1.0.4/dist/stpageflip.min.js" onerror="window.__stpageflipFailed=true"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: {theme["bg"]};
            min-height: 100vh;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #fff;
            overflow-x: hidden;
        }}
        .glass {{
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 16px;
        }}
        .page-container {{
            width: 100%;
            max-width: 360px;
            margin: 0 auto;
            padding: 16px;
        }}
        .brochure-title {{
            text-align: center;
            padding: 24px 16px 8px;
            font-size: 20px;
            font-weight: 600;
            background: {theme["gradient"]};
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .purpose-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            background: {theme["badge_bg"]};
            color: {theme["badge_color"]};
            border: 1px solid {theme["badge_border"]};
            margin: 4px auto 12px;
        }}
        .st-pageflip-container {{
            width: 100%;
            max-width: 340px;
            margin: 12px auto;
            min-height: 480px;
        }}
        .page-flip-page {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(255,255,255,0.15);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        .page-flip-page h2 {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            background: {theme["gradient"]};
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .page-flip-page .content {{
            font-size: 14px;
            line-height: 1.6;
            color: rgba(255,255,255,0.8);
            white-space: pre-wrap;
            text-align: center;
        }}
        .page-flip-page img {{
            max-width: 100%;
            border-radius: 12px;
            margin: 8px 0;
        }}
        .share-bar {{
            display: flex;
            justify-content: center;
            gap: 16px;
            padding: 16px;
        }}
        .share-btn {{
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.2);
            color: #fff;
            padding: 10px 24px;
            border-radius: 24px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .share-btn:hover {{
            background: rgba(255,255,255,0.2);
            transform: translateY(-1px);
        }}
        .view-count {{
            text-align: center;
            color: rgba(255,255,255,0.4);
            font-size: 12px;
            padding: 8px 0 24px;
        }}
        /* ===== CDN 降级样式 ===== */
        /* Tailwind 降级 — 基础 normalize/hold 样式 */
        .tailwind-failed body, .tailwind-failed div, .tailwind-failed span,
        .tailwind-failed h1, .tailwind-failed h2, .tailwind-failed button {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        /* StPageFlip 降级 — 平铺模式（纵向滚动） */
        .page-flip-page.flat-mode {{
            margin-bottom: 20px !important;
            position: relative !important;
            opacity: 1 !important;
            visibility: visible !important;
            transform: none !important;
            min-height: 200px;
        }}
        .flipbook-flat .page-flip-page {{
            margin-bottom: 20px !important;
            position: relative !important;
            opacity: 1 !important;
            visibility: visible !important;
            transform: none !important;
            min-height: 200px;
        }}
    </style>
</head>
<body>
    <div class="brochure-title">{brochure.title}</div>
    {"".join((
        f'<div class="purpose-badge">{theme["emoji"]} {theme["label"]}</div>'
    )) if brochure.purpose and brochure.purpose in BrochureRenderer.PURPOSE_THEMES else ""}
    <div class="page-container">
        <div class="st-pageflip-container" id="flipbook">
            {pages_html}
        </div>
    </div>
    <div class="share-bar">
        <button class="share-btn" onclick="shareBrochure()">📤 分享</button>
        <button class="share-btn" onclick="window.location.reload()">🔄 刷新</button>
    </div>
    <div class="view-count">👁️ 已浏览 {brochure.view_count} 次</div>

    <script>
        // === CDN 降级检测 ===
        if (window.__tailwindFailed) {{
            document.documentElement.classList.add('tailwind-failed');
        }}

        const flipbook = document.getElementById('flipbook');

        if (window.__stpageflipFailed) {{
            // StPageFlip 加载失败 → 平铺降级模式
            flipbook.classList.add('flipbook-flat');
            // 确保所有页面可见（移除 StPageFlip 可能附加的任何隐藏样式）
            document.querySelectorAll('.page-flip-page').forEach(function(el) {{
                el.style.position = 'relative';
                el.style.opacity = '1';
                el.style.visibility = 'visible';
                el.style.transform = 'none';
            }});
        }} else if (typeof StPageFlip !== 'undefined') {{
            try {{
                const flip = new StPageFlip(flipbook, {{
                    width: 320,
                    height: 460,
                    showCover: true,
                    maxShadowOpacity: 0.5,
                    flippingTime: 600,
                    autoSize: true,
                    swipeDistance: 30,
                }});
                flip.loadFromHTML(document.querySelectorAll('.page-flip-page'));
            }} catch (e) {{
                // 初始化异常时降级为平铺模式
                flipbook.classList.add('flipbook-flat');
                console.warn('StPageFlip 初始化失败，已降级为平铺模式:', e);
            }}
        }} else {{
            // StPageFlip 未定义 → 平铺降级模式
            flipbook.classList.add('flipbook-flat');
        }}

        function shareBrochure() {{
            const url = window.location.href;
            if (navigator.share) {{
                navigator.share({{ title: '{brochure.title}', url: url }});
            }} else {{
                navigator.clipboard.writeText(url).then(() => {{
                    alert('链接已复制到剪贴板');
                }});
            }}
        }}
    </script>
</body>
</html>"""

    @staticmethod
    def _render_page(page, base_url: str, theme: dict) -> str:
        """渲染单个页面为 HTML（支持用途主题色）"""
        content = page.content or ""
        image_html = ""

        if page.image_url:
            img_src = page.image_url
            if base_url and not img_src.startswith(("http://", "https://", "data:")):
                img_src = base_url.rstrip("/") + "/" + img_src.lstrip("/")
            image_html = f'<img src="{img_src}" alt="page image" />'

        return f"""
        <div class="page-flip-page">
            <h2>{"📇" if page.content_type == "cover" else "📄"} {page.content_type.upper()}</h2>
            {image_html}
            <div class="content">{content}</div>
        </div>"""

    @staticmethod
    def render_share_preview(
        brochure: Brochure,
    ) -> str:
        """生成分享预览卡片（用于社交媒体分享的 meta 标签）

        Args:
            brochure: Brochure 实例

        Returns:
            HTML meta 标签字符串
        """
        description = ""
        if brochure.pages:
            first_page = brochure.pages[0]
            description = first_page.content[:200] if first_page.content else "AI数字名片"

        return f"""<meta property="og:title" content="{brochure.title}" />
<meta property="og:description" content="{description}" />
<meta property="og:type" content="website" />
<meta name="description" content="{description}" />"""
