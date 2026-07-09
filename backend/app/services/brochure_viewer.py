"""公开画册查看服务 — StPageFlip 翻页HTML + 小程序引导"""
import asyncio
import logging

from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.brochure import Brochure
from app.services.brochure_render import BrochureRenderer

logger = logging.getLogger(__name__)

# 全局DB超时配置（秒）
_DB_QUERY_TIMEOUT = 8
_DB_COMMIT_TIMEOUT = 5
_DB_REFRESH_TIMEOUT = 5


def _build_miniapp_guide_html(share_token: str) -> str:
    """构建小程序引导 HTML 片段"""
    return f"""
    <div style="text-align:center;padding:20px 16px 32px">
        <div style="display:inline-flex;align-items:center;gap:8px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:12px 28px;border-radius:30px;font-size:15px;font-weight:600;cursor:pointer;border:none;box-shadow:0 4px 15px rgba(102,126,234,0.4);transition:all 0.3s" onclick="openMiniProgram()" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='none'">
            <span style="font-size:20px">🔍</span>
            打开小程序查看更多
            <span style="font-size:12px;opacity:0.8">›</span>
        </div>
        <p style="color:rgba(255,255,255,0.4);font-size:12px;margin-top:8px">在微信小程序中获得完整体验 · AI数智名片</p>
    </div>
    <script>
    function openMiniProgram() {{
        var shareToken = '{share_token}';
        // 微信小程序环境
        if (typeof wx !== 'undefined' && wx.miniProgram) {{
            wx.miniProgram.navigateTo({{
                url: '/pages/brochure/detail?share_token=' + encodeURIComponent(shareToken)
            }});
        }} else {{
            var ua = navigator.userAgent.toLowerCase();
            if (ua.indexOf('micromessenger') > -1) {{
                // 在微信中但无小程序上下文 — 提示用户下拉
                var guide = document.createElement('div');
                guide.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:9999;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;font-size:16px';
                guide.innerHTML = '<div style="font-size:48px;margin-bottom:16px">👇</div><div>下拉微信首页进入小程序</div><div style="font-size:13px;color:rgba(255,255,255,0.6);margin-top:8px">搜索"AI数智名片"</div><div style="margin-top:24px;padding:10px 32px;border:1px solid rgba(255,255,255,0.3);border-radius:20px;cursor:pointer" onclick="this.parentElement.remove()">我知道了</div>';
                document.body.appendChild(guide);
            }} else {{
                // 非微信环境
                alert('请在微信中打开此链接，体验完整功能');
            }}
        }}
    }}
    </script>
    """


async def render_public_brochure_html(
    db: AsyncSession,
    share_token: str,
) -> str:
    """生成公开画册的完整翻页HTML（含访问计数 & 小程序引导）

    Args:
        db: 数据库会话
        share_token: 分享 token

    Returns:
        完整的 HTML 字符串

    Raises:
        ValueError: 画册不存在、未发布或操作超时
    """
    # ── 1. 带 timeout 的 DB 查询 ──────────────────────────────
    try:
        result = await asyncio.wait_for(
            db.execute(
                select(Brochure)
                .options(selectinload(Brochure.pages))
                .where(
                    Brochure.share_token == share_token,
                )
            ),
            timeout=_DB_QUERY_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "DB query timeout for share_token=%s (timeout=%ss)",
            share_token,
            _DB_QUERY_TIMEOUT,
        )
        raise ValueError("画册加载超时，请稍后重试")

    brochure = result.scalars().first()
    if brochure is None:
        raise ValueError("画册不存在或链接已失效")

    # ── 2. 带 timeout 的访问计数 ──────────────────────────────
    brochure.view_count += 1
    try:
        await asyncio.wait_for(db.commit(), timeout=_DB_COMMIT_TIMEOUT)
        await asyncio.wait_for(db.refresh(brochure), timeout=_DB_REFRESH_TIMEOUT)
    except asyncio.TimeoutError:
        logger.warning(
            "DB commit/refresh timeout for share_token=%s (继续渲染)",
            share_token,
        )
        # 不阻塞页面渲染 — 计数失败不影响用户体验

    # ── 3. 生成翻页 HTML ──────────────────────────────────────
    html = BrochureRenderer.render_brochure_html(brochure)

    # 在 </body> 前插入小程序引导
    mini_app_html = _build_miniapp_guide_html(share_token)
    html = html.replace("</body>", mini_app_html + "\n</body>")

    return html
