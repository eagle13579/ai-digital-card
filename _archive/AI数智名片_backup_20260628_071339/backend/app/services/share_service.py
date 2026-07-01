"""名片分享服务 — QR码生成 & NFC NDEF 记录"""

import io
from typing import Optional

import qrcode
from qrcode.image.pil import PilImage

from app.config import settings


def get_base_url() -> str:
    """构造对外公开的基础 URL（优先从环境读取）"""
    return settings.BASE_URL.rstrip("/") if hasattr(settings, "BASE_URL") and settings.BASE_URL else "http://localhost:8000"


def build_share_url(share_token: str) -> str:
    """基于 share_token 构建前端可访问的名片链接"""
    base = get_base_url()
    return f"{base}/view/{share_token}"


def generate_qr_code(share_token: str, box_size: int = 10, border: int = 2) -> bytes:
    """
    根据 share_token 生成 QR 码 PNG 图片字节流。
    
    Args:
        share_token: 画册分享 token
        box_size: QR 码每格像素大小（默认 10 → 约 290x290）
        border: 边框格子数（默认 2）

    Returns:
        PNG 格式图片二进制数据
    """
    share_url = build_share_url(share_token)
    qr = qrcode.QRCode(
        version=None,          # 自动推断
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(share_url)
    qr.make(fit=True)

    img: PilImage = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_nfc_ndef_record(share_token: str) -> dict:
    """
    生成 NFC NDEF 记录（以 JSON 返回, 供客户端写卡/展示）。
    
    NFC NDEF 支持以下两种方式:
      1) URI 记录 — Android / iOS 自动打开浏览器
      2) Text + URI 组合记录 — 额外携带名片摘要

    Args:
        share_token: 画册分享 token

    Returns:
        dict 包含 ndef_records 和 share_url
    """
    share_url = build_share_url(share_token)

    ndef_records = [
        {
            "type": "uri",
            "uri": share_url,
            "description": "AI数智名片 - 点击打开",
        },
    ]

    return {
        "share_url": share_url,
        "share_token": share_token,
        "ndef_records": ndef_records,
        "ndef_message": [
            # TNF = 0x01 (well-known), RTD = "U" (URI)
            {"tnf": 1, "type": "U", "payload": share_url},
        ],
        # 兼容 Android AAR (Android Application Record)
        # 如果没有匹配的 App, 回退到浏览器
        "android_aar": {
            "package_name": "com.nousresearch.digitalbrochure",
            # 如果未安装 App, 走浏览器
            "fallback_url": share_url,
        },
        "mime_type": "application/vnd.nfc.ndef",
    }
