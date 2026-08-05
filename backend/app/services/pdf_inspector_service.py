"""
PDF 智能处理服务（pdf-inspector 封装，独立于原 pdf_service.py）
=====================================
基于 GitHub ★10.4k 开源项目 firecrawl/pdf-inspector（Rust 引擎，免 OCR）。

能力:
  - classify: 分类 PDF（text_based / scanned / image_based / mixed）+ 置信度
  - extract:  位置感知文本提取（多栏/字体/坐标）
  - markdown: 转干净 Markdown（标题/列表/代码块/表格/粗斜体/链接）

接入: 2026-08-05 白泽远程分身（吸收自抖音「AI情报局」推荐 GitHub 热门项目）
参考: skill: pdf-inspector-tool。注意: 不与原 pdf_service.py(opendataloader-pdf) 冲突
"""
import logging
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

try:
    import pdf_inspector as _pi
    PDF_INSPECTOR_AVAILABLE = True
except ImportError:  # pragma: no cover
    _pi = None
    PDF_INSPECTOR_AVAILABLE = False
    logger.warning("pdf-inspector 未安装（pip install pdf-inspector），PDF 服务降级不可用")


class PdfInspectionError(Exception):
    """PDF 解析失败（文件损坏/非 PDF/扫描异常）"""


def _read_bytes(source: Union[str, Path, bytes]) -> bytes:
    """统一入参：路径或 bytes"""
    if isinstance(source, (str, Path)):
        return Path(source).read_bytes()
    return source


def classify(source: Union[str, Path, bytes]) -> dict:
    """分类 PDF，返回 {pdf_type, pages, confidence, needs_ocr}"""
    if not PDF_INSPECTOR_AVAILABLE:
        raise PdfInspectionError("pdf-inspector 未安装")
    try:
        data = _read_bytes(source)
        result = _pi.classify_pdf_bytes(data)
        pdf_type = getattr(result, "pdf_type", "unknown")
        return {
            "pdf_type": pdf_type,          # text_based / scanned / image_based / mixed
            "pages": getattr(result, "pages", None),
            "confidence": getattr(result, "confidence", None),
            "needs_ocr": pdf_type in ("scanned", "image_based"),
        }
    except ValueError as e:
        raise PdfInspectionError(f"PDF 解析失败: {e}") from e


def extract_text(source: Union[str, Path, bytes]) -> str:
    """提取纯文本（位置感知，多栏顺序正确）"""
    if not PDF_INSPECTOR_AVAILABLE:
        raise PdfInspectionError("pdf-inspector 未安装")
    try:
        data = _read_bytes(source)
        return str(_pi.extract_text_bytes(data))
    except ValueError as e:
        raise PdfInspectionError(f"PDF 解析失败: {e}") from e


def to_markdown(source: Union[str, Path, bytes]) -> str:
    """转 Markdown（含表格/标题/列表检测）"""
    if not PDF_INSPECTOR_AVAILABLE:
        raise PdfInspectionError("pdf-inspector 未安装")
    try:
        data = _read_bytes(source)
        result = _pi.extract_pages_markdown_bytes(data)
        # PagesExtractionResult 对象 → 提取每页 markdown 拼接
        pages = getattr(result, "pages", None)
        if pages is None:
            return str(result)
        if isinstance(pages, list):
            return "\n\n".join(str(p) for p in pages)
        return str(pages)
    except ValueError as e:
        raise PdfInspectionError(f"PDF 解析失败: {e}") from e


def process(source: Union[str, Path, bytes]) -> dict:
    """一站式：分类 + 文本提取"""
    data = _read_bytes(source)
    return {
        "classification": classify(data),
        "text": extract_text(data),
    }


def smart_extract(source: Union[str, Path, bytes]) -> dict:
    """智能提取：文本 PDF 直接提取；扫描/图片 PDF 标记需 OCR（省成本路由）"""
    data = _read_bytes(source)
    cls = classify(data)
    if cls["needs_ocr"]:
        return {
            "classification": cls,
            "extracted": False,
            "message": "扫描版/图片型 PDF，需 OCR 引擎处理（pdf-inspector 不做 OCR）",
        }
    return {
        "classification": cls,
        "extracted": True,
        "text": extract_text(data),
    }
