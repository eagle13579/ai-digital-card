"""
名片分享功能模块
==================================
generate_share_link(card_id)  — 返回唯一分享链接
generate_qr_code(url)        — 返回二维码 data URL
share_to_social(card_id, platform) — 支持微信 / LinkedIn 分享
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# qrcode 和 PIL 为可选依赖，非强制
try:
    import qrcode
    from qrcode.image.pil import PilImage

    _QR_AVAILABLE = True
except ImportError:
    _QR_AVAILABLE = False

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

_SHARE_DB: Dict[str, "ShareRecord"] = {}  # 内存存储 (MVP 阶段)


@dataclass
class ShareRecord:
    """分享记录"""
    card_id: str
    share_token: str
    created_at: float = field(default_factory=time.time)
    view_count: int = 0
    expires_at: Optional[float] = None


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

# 默认基础 URL，可从环境变量覆盖
BASE_URL = "https://ai-card.example.com"


def _configure_base_url(custom_url: Optional[str] = None) -> str:
    """获取配置的 base URL"""
    if custom_url:
        return custom_url.rstrip("/")
    # 尝试读取环境变量
    import os
    return os.environ.get("AI_CARD_BASE_URL", BASE_URL).rstrip("/")


# ---------------------------------------------------------------------------
# 分享链接生成
# ---------------------------------------------------------------------------

def _generate_token(card_id: str) -> str:
    """基于 card_id + 时间戳 + 随机数生成唯一 token"""
    raw = f"{card_id}:{time.time_ns()}:{uuid.uuid4().hex}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def generate_share_link(
    card_id: str,
    base_url: Optional[str] = None,
    expires_in_days: Optional[int] = None,
) -> str:
    """生成名片分享链接

    Args:
        card_id:        名片唯一 ID
        base_url:       自定义基础 URL (可选)
        expires_in_days: 链接有效期(天)，None 表示永久

    Returns:
        完整分享链接
    """
    token = _generate_token(card_id)
    base = _configure_base_url(base_url)

    record = ShareRecord(
        card_id=card_id,
        share_token=token,
        created_at=time.time(),
        view_count=0,
        expires_at=time.time() + expires_in_days * 86400 if expires_in_days else None,
    )
    _SHARE_DB[token] = record

    return f"{base}/card/{token}"


def get_share_record(token: str) -> Optional[ShareRecord]:
    """根据 token 获取分享记录"""
    record = _SHARE_DB.get(token)
    if record is None:
        return None
    # 检查过期
    if record.expires_at is not None and time.time() > record.expires_at:
        _SHARE_DB.pop(token, None)
        return None
    record.view_count += 1
    return record


# ---------------------------------------------------------------------------
# 二维码生成
# ---------------------------------------------------------------------------

def generate_qr_code(
    url: str,
    box_size: int = 10,
    border: int = 2,
    fill_color: str = "#1a1a2e",
    back_color: str = "#ffffff",
) -> str:
    """生成二维码 data URL (base64 编码的 PNG)

    Args:
        url:         二维码内容 URL
        box_size:    每格像素大小
        border:      边框格子数
        fill_color:  前景色 (二维码颜色)
        back_color:  背景色

    Returns:
        data:image/png;base64,... 格式的 data URL

    Raises:
        ImportError: 若未安装 qrcode 或 Pillow 依赖
    """
    if not _QR_AVAILABLE:
        raise ImportError(
            "请先安装 qrcode 和 Pillow 依赖: pip install qrcode[pil] Pillow"
        )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img: PilImage = qr.make_image(fill_color=fill_color, back_color=back_color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def generate_qr_svg(url: str, size: int = 200) -> str:
    """使用纯 Python 生成简单二维码 SVG (无需外部依赖)

    这是一个极简实现，仅用于 MVP 原型。生产环境建议使用 qrcode 库。
    """
    # 使用 qrcode 库生成，若无则用占位 SVG
    if _QR_AVAILABLE:
        data_url = generate_qr_code(url, box_size=6, border=2)
        return f'<img src="{data_url}" width="{size}" height="{size}" alt="QR Code"/>'

    # 兜底: SVG 占位符
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{size}" height="{size}" rx="8" fill="#f0f0f0"/>
  <rect x="20" y="20" width="40" height="40" rx="4" fill="#333"/>
  <rect x="70" y="20" width="40" height="40" rx="4" fill="#333"/>
  <rect x="20" y="70" width="40" height="40" rx="4" fill="#333"/>
  <rect x="140" y="20" width="40" height="40" rx="4" fill="#333"/>
  <rect x="20" y="140" width="40" height="40" rx="4" fill="#333"/>
  <rect x="90" y="100" width="20" height="20" rx="2" fill="#333"/>
  <rect x="130" y="90" width="30" height="30" rx="2" fill="#333"/>
  <rect x="90" y="140" width="30" height="30" rx="2" fill="#333"/>
  <text x="{size//2}" y="{size-10}" text-anchor="middle" font-size="10" fill="#999">QR Placeholder</text>
</svg>"""


# ---------------------------------------------------------------------------
# 社交平台分享
# ---------------------------------------------------------------------------

@dataclass
class SocialShareResult:
    """社交分享结果"""
    platform: str
    success: bool
    message: str
    share_url: str = ""


def _build_wechat_share_url(card_id: str, title: str, summary: str) -> str:
    """构建微信分享链接 (使用微信 JS-SDK scheme)"""
    base = _configure_base_url()
    token = _generate_token(card_id)
    share_url = f"{base}/card/{token}"

    # 微信分享通过 JS-SDK 实现，此处返回卡片 URL
    # 实际集成需前端接入 wx.config / wx.updateAppMessageShareData
    return share_url


def _build_linkedin_share_url(url: str, title: str, summary: str) -> str:
    """构建 LinkedIn 分享链接"""
    import urllib.parse
    params = urllib.parse.urlencode({
        "url": url,
        "title": title,
        "summary": summary,
        "source": "AI数字名片",
    })
    return f"https://www.linkedin.com/sharing/share-offsite/?{params}"


def share_to_social(
    card_id: str,
    platform: str,
    card_data: Optional[Dict] = None,
) -> SocialShareResult:
    """分享名片到社交平台

    Args:
        card_id:   名片唯一 ID
        platform:  平台名称 ("wechat" | "linkedin")
        card_data: 可选的卡片数据 (name, title, company 等)

    Returns:
        SocialShareResult 包含分享结果
    """
    platform = platform.lower().strip()
    title = card_data.get("name", "AI数字名片") if card_data else "AI数字名片"
    summary = card_data.get("title", "") if card_data else ""
    company = card_data.get("company", "") if card_data else ""
    if company:
        summary = f"{summary} @ {company}" if summary else company

    base = _configure_base_url()
    token = _generate_token(card_id)
    card_url = f"{base}/card/{token}"

    if platform == "wechat":
        share_url = _build_wechat_share_url(card_id, title, summary)
        return SocialShareResult(
            platform="wechat",
            success=True,
            message="微信分享链接已生成 (需集成 JS-SDK 完成分享)",
            share_url=share_url,
        )

    elif platform == "linkedin":
        share_url = _build_linkedin_share_url(card_url, title, summary)
        return SocialShareResult(
            platform="linkedin",
            success=True,
            message="LinkedIn 分享链接已生成",
            share_url=share_url,
        )

    else:
        return SocialShareResult(
            platform=platform,
            success=False,
            message=f"不支持的分享平台: {platform} (支持: wechat, linkedin)",
            share_url="",
        )


def share_card_qr_embed(
    card_id: str,
    card_data: Optional[Dict] = None,
    base_url: Optional[str] = None,
) -> Dict:
    """一站式生成分享链接 + 二维码 data URL + 社交分享链接

    适合 API 端点一次返回所有分享信息
    """
    link = generate_share_link(card_id, base_url=base_url)
    qr_data_url = generate_qr_code(link)

    result = {
        "card_id": card_id,
        "share_link": link,
        "qr_code_data_url": qr_data_url,
        "platforms": {},
    }

    if card_data:
        for p in ["wechat", "linkedin"]:
            sr = share_to_social(card_id, p, card_data)
            result["platforms"][p] = {
                "success": sr.success,
                "message": sr.message,
                "share_url": sr.share_url,
            }

    return result


# ---------------------------------------------------------------------------
# 快速测试
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # 演示用法
    test_card_id = "test-card-001"
    card_data = {
        "name": "张三",
        "title": "产品总监",
        "company": "AI科技有限公司",
    }

    print("=== 分享链接 ===")
    link = generate_share_link(test_card_id)
    print(f"  {link}")

    print("\n=== QR 二维码 ===")
    try:
        qr = generate_qr_code(link)
        print(f"  data URL 长度: {len(qr)} 字符")
    except ImportError:
        print("  (需要安装 qrcode 库)")

    print("\n=== 社交分享 ===")
    for p in ["wechat", "linkedin", "twitter"]:
        result = share_to_social(test_card_id, p, card_data)
        print(f"  [{result.platform}] {result.message}")
        if result.share_url:
            print(f"    URL: {result.share_url}")

    print("\n=== 一站式分享 ===")
    all_info = share_card_qr_embed(test_card_id, card_data)
    print(f"  链接: {all_info['share_link']}")
    print(f"  平台: {list(all_info['platforms'].keys())}")
