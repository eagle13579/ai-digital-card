"""文件魔数（Magic Number）校验工具 — 上传安全加固（BUG-033 修复）。

问题背景:
  upload-cover / upload-file / upload-video 等接口此前仅校验扩展名（+可选 MIME），
  攻击者将恶意文件改名 .png/.pdf/.mp4 即可绕过校验。

本模块统一校验「文件头字节」，判断文件真实类型:
  - 图片: JPEG / PNG / GIF / WebP / BMP（魔数表 + 可选 PIL 解码校验）
  - 文档: PDF（%PDF- 头）/ OOXML-ZIP / 旧版 OLE2
  - 视频: MP4（ftyp box）/ WebM（EBML 魔数）（+ 可选 ffprobe 探针）

设计原则:
  1. 纯 stdlib 实现（魔数表），无第三方依赖硬性要求；
  2. PIL / ffprobe 已安装时自动启用深度校验（解码/探针），未安装时降级为魔数校验；
  3. MIME 为空时由「扩展名 + 魔数」双验证兜底（BUG-033 要求）。
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# ── 魔数表（文件头字节） ─────────────────────────────────────────────────────

# 图片
MAGIC_JPEG = b"\xff\xd8\xff"
MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
MAGIC_GIF87 = b"GIF87a"
MAGIC_GIF89 = b"GIF89a"
MAGIC_BMP = b"BM"
MAGIC_RIFF = b"RIFF"
MAGIC_WEBP = b"WEBP"

# 文档
MAGIC_PDF = b"%PDF-"
MAGIC_ZIP = b"PK\x03\x04"  # docx/pptx/xlsx/zip 均为 ZIP 容器
MAGIC_OLE2 = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # 旧版 doc/xls/ppt

# 视频
MAGIC_EBML = b"\x1a\x45\xdf\xa3"  # WebM (Matroska/EBML)
FTYP_OFFSET = 4
FTYP_MAGIC = b"ftyp"

# 扩展名 → 图片魔数类型
_IMAGE_EXT_TO_MAGIC: dict[str, str] = {
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".png": "png",
    ".gif": "gif",
    ".webp": "webp",
    ".bmp": "bmp",
}

# 扩展名 → 视频魔数类型
_VIDEO_EXT_TO_MAGIC: dict[str, str] = {
    ".mp4": "mp4",
    ".webm": "webm",
}

# ── 图片魔数检测 ─────────────────────────────────────────────────────────────


def detect_image_type(data: bytes) -> str | None:
    """通过文件头检测图片真实类型。

    Returns:
        "jpeg" | "png" | "gif" | "webp" | "bmp"，无法识别返回 None。
    """
    if not data:
        return None
    if data.startswith(MAGIC_JPEG):
        return "jpeg"
    if data.startswith(MAGIC_PNG):
        return "png"
    if data.startswith(MAGIC_GIF87) or data.startswith(MAGIC_GIF89):
        return "gif"
    if data.startswith(MAGIC_RIFF) and len(data) >= 12 and data[8:12] == MAGIC_WEBP:
        return "webp"
    if data.startswith(MAGIC_BMP):
        return "bmp"
    return None


def _verify_image_with_pil(data: bytes, expected_type: str) -> bool:
    """PIL 解码校验（已安装时启用）。校验失败/异常返回 False；未安装返回 True（降级）。"""
    try:
        from PIL import Image
        import io

        with Image.open(io.BytesIO(data)) as img:
            img.verify()
        return True
    except ImportError:
        return True  # PIL 未安装 → 依赖魔数校验
    except Exception as exc:  # 解码失败 = 伪造图片
        logger.warning("图片 PIL 解码校验失败: %s", exc)
        return False


def verify_image(data: bytes, ext: str) -> bool:
    """校验图片文件头与扩展名一致（MIME 为空时兜底的双验证之一）。

    Args:
        data: 文件内容字节
        ext:  扩展名（含点，小写，如 ".png"）

    Returns:
        True 校验通过；False 魔数不匹配或 PIL 解码失败。
    """
    ext = ext.lower()
    expected = _IMAGE_EXT_TO_MAGIC.get(ext)
    if expected is None:
        return False
    actual = detect_image_type(data)
    if actual != expected:
        logger.warning("图片魔数不匹配: ext=%s actual=%s", ext, actual)
        return False
    # 深度校验（PIL 可用时）
    if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        if not _verify_image_with_pil(data, expected):
            return False
    return True


# ── 视频魔数检测 ─────────────────────────────────────────────────────────────


def detect_video_type(data: bytes) -> str | None:
    """通过文件头检测视频真实类型。

    Returns:
        "mp4" | "webm"，无法识别返回 None。
    """
    if not data:
        return None
    if len(data) >= FTYP_OFFSET + 4 and data[FTYP_OFFSET : FTYP_OFFSET + 4] == FTYP_MAGIC:
        return "mp4"
    if data.startswith(MAGIC_EBML):
        return "webm"
    return None


def _verify_video_with_ffprobe(file_path: str) -> bool:
    """ffprobe 探针校验（已安装时启用）。无法探针/未安装返回 True（降级）。"""
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-of", "json", file_path],
            capture_output=True,
            timeout=30,
        )
        return proc.returncode == 0
    except FileNotFoundError:
        return True  # ffprobe 未安装 → 依赖魔数校验
    except subprocess.TimeoutExpired:
        logger.warning("ffprobe 探针超时，跳过深度校验")
        return True
    except Exception as exc:
        logger.warning("ffprobe 探针异常: %s", exc)
        return True


def verify_video(data: bytes, ext: str, file_path: str | None = None) -> bool:
    """校验视频文件头与扩展名一致。

    Args:
        data:      文件内容字节（至少前 16 字节）
        ext:       扩展名（含点，小写，如 ".mp4"）
        file_path: 已落盘文件路径（可选，ffprobe 深度校验用）

    Returns:
        True 校验通过；False 魔数不匹配或 ffprobe 探针失败。
    """
    ext = ext.lower()
    expected = _VIDEO_EXT_TO_MAGIC.get(ext)
    if expected is None:
        return False
    actual = detect_video_type(data)
    if actual != expected:
        logger.warning("视频魔数不匹配: ext=%s actual=%s", ext, actual)
        return False
    # 深度校验（ffprobe 可用且文件已落盘时）
    if file_path and Path(file_path).exists():
        if not _verify_video_with_ffprobe(file_path):
            logger.warning("视频 ffprobe 探针校验失败: %s", file_path)
            return False
    return True


# ── 文档魔数检测 ─────────────────────────────────────────────────────────────


def verify_pdf(data: bytes) -> bool:
    """校验 PDF 文件头（%PDF-）。"""
    return bool(data and data.startswith(MAGIC_PDF))


def verify_office_doc(data: bytes, ext: str) -> bool:
    """校验 Office 文档文件头。

    - .docx/.pptx/.xlsx/.zip → ZIP 容器 (PK\\x03\\x04)
    - .doc/.xls/.ppt（旧版） → OLE2 复合文档

    Args:
        data: 文件内容字节
        ext:  扩展名（含点，小写）

    Returns:
        True 校验通过；False 魔数不匹配。
    """
    ext = ext.lower()
    if ext in (".docx", ".pptx", ".xlsx", ".zip"):
        return bool(data and data.startswith(MAGIC_ZIP))
    if ext in (".doc", ".xls", ".ppt"):
        return bool(data and data.startswith(MAGIC_OLE2))
    return False


def verify_file_magic(data: bytes, ext: str) -> bool:
    """统一文件魔数校验入口（按扩展名分发）。

    Args:
        data: 文件内容字节
        ext:  扩展名（含点，小写）

    Returns:
        True 校验通过；False 魔数不匹配。
    """
    ext = ext.lower()
    if ext in _IMAGE_EXT_TO_MAGIC:
        return verify_image(data, ext)
    if ext in _VIDEO_EXT_TO_MAGIC:
        return verify_video(data, ext)
    if ext == ".pdf":
        return verify_pdf(data)
    if ext in (".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip"):
        return verify_office_doc(data, ext)
    # 未知扩展名：不拦截（由上层扩展名白名单负责）
    return True
