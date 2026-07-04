"""
链客宝 — API 文档中心门户路由
==============================
提供开发者文档门户页面服务。

路由:
  GET /docs/portal  → 文档门户首页
  GET /docs/{section}  → 各文档章节（锚点跳转）
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

logger = __import__("logging").getLogger(__name__)

router = APIRouter(tags=["开发者文档门户"])

# ── 模板路径 ────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_TEMPLATES_DIR = _HERE.parent.parent / "templates"
_PORTAL_HTML = _TEMPLATES_DIR / "docs_portal.html"


def _load_portal_html() -> str:
    """加载 docs_portal.html，失败时返回降级页面"""
    if _PORTAL_HTML.is_file():
        with open(_PORTAL_HTML, "r", encoding="utf-8") as f:
            return f.read()
    logger.warning("docs_portal.html 未找到: %s", _PORTAL_HTML)
    return """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>文档门户</title></head><body style="font-family:sans-serif;padding:2rem;">
<h1>🔗 链客宝 API 文档</h1><p>文档门户页面正在构建中。</p>
<p>请参考 <a href="/docs">Swagger UI</a> 或 <a href="/redoc">ReDoc</a>。</p></body></html>"""


# 缓存 HTML 内容（避免每次请求都读盘）
_PORTAL_CACHE: str | None = None


def _get_portal_html() -> str:
    global _PORTAL_CACHE
    if _PORTAL_CACHE is None:
        _PORTAL_CACHE = _load_portal_html()
    return _PORTAL_CACHE


# ── 重置缓存（热更新用） ──────────────────────────────────────────
def reload_portal_cache() -> None:
    """重新加载 HTML 模板（部署或模板更新后调用）"""
    global _PORTAL_CACHE
    _PORTAL_CACHE = None
    logger.info("文档门户缓存已重置")


@router.get(
    "/docs/portal",
    response_class=HTMLResponse,
    summary="开发者文档门户首页",
    description="返回 Stripe 风格的 API 文档门户，含快速开始、API参考、SDK、Webhook、定价、错误码、Changelog 等章节。",
)
async def docs_portal_home() -> HTMLResponse:
    """返回文档门户首页"""
    return HTMLResponse(content=_get_portal_html())


@router.get(
    "/docs/{section}",
    response_class=HTMLResponse,
    summary="开发者文档章节页面",
    description="返回文档门户的指定章节（通过 URL hash 定位）。",
)
async def docs_portal_section(section: str) -> HTMLResponse:
    """
    返回文档门户页面并跳转到指定章节。

    章节映射:
      - quickstart  → 快速开始
      - auth        → 认证模块
      - cards       → 名片模块
      - matching    → 匹配模块
      - payment     → 支付模块
      - nfc         → NFC 名片
      - crm         → CRM 模块
      - sdk         → SDK
      - webhooks    → Webhook
      - pricing     → 定价
      - errors      → 错误码
      - changelog   → 版本历史
    """
    html = _get_portal_html()
    # 注入 section hash
    section_map = {
        "quickstart": "quickstart",
        "auth": "api-auth",
        "cards": "api-cards",
        "matching": "api-matching",
        "payment": "api-payment",
        "nfc": "api-nfc",
        "crm": "api-crm",
        "sdk": "sdk",
        "webhooks": "webhooks",
        "pricing": "pricing",
        "errors": "errors",
        "changelog": "changelog",
    }
    anchor = section_map.get(section.lower(), "quickstart")
    # 插入跳转脚本
    script = f"""<script>
window.addEventListener('load', function() {{
    window.location.hash = '#{anchor}';
}});
</script>"""
    modified = html.replace("</body>", f"{script}\n</body>")
    return HTMLResponse(content=modified)
