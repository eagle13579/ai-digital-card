"""
PDF 解析服务 — 基于 opendataloader-pdf 引擎

提供三种 PDF → Markdown 解析模式：
  1. convert_pdf_to_markdown     — 通用快速转换（本地 Java 管线）
  2. convert_pdf_hybrid          — 混合模式（处理复杂产品手册、表格等）
  3. convert_pdf_with_images     — 含图片描述的富 Markdown 输出
  4. check_java_available        — Java 运行时健康检查
"""
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import opendataloader_pdf

logger = logging.getLogger(__name__)

# ── 默认输出目录 ──────────────────────────────────────────────
DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "pdf_output",
)


# ═══════════════════════════════════════════════════════════════
# 健康检查
# ═══════════════════════════════════════════════════════════════

def check_java_available() -> dict:
    """检查 Java 运行时环境是否满足 opendataloader-pdf 的要求。

    Returns:
        dict: {
            "available": bool,        # Java 是否可用
            "version": str,           # Java 版本字符串（如 "11.0.29"）
            "major_version": int,     # 主版本号（如 11）
            "error": str | None,      # 错误信息（如有）
        }
    """
    result: dict = {
        "available": False,
        "version": "",
        "major_version": 0,
        "error": None,
    }

    # 1. 检查 java 命令是否存在
    java_path = shutil.which("java")
    if not java_path:
        result["error"] = "Java 未安装或不在系统 PATH 中"
        return result

    # 2. 获取版本信息
    try:
        proc = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version_output = proc.stderr if proc.stderr else proc.stdout
        result["version"] = version_output.strip()

        # 解析主版本号 (e.g. "openjdk version \"11.0.29\" 2026-04-21" -> 11)
        for line in version_output.splitlines():
            if "version" in line:
                match = re.search(r'"(\d+)', line)
                if match:
                    result["major_version"] = int(match.group(1))
                    break

        result["available"] = result["major_version"] >= 11
        if not result["available"]:
            result["error"] = (
                f"Java 版本过低（{result['major_version']}），"
                f"需要 Java 11 或更高版本"
            )

    except FileNotFoundError:
        result["error"] = "Java 命令未找到"
    except subprocess.TimeoutExpired:
        result["error"] = "Java 版本检查超时"
    except Exception as exc:
        result["error"] = f"Java 检查异常: {exc}"

    return result


# ═══════════════════════════════════════════════════════════════
# 通用转换
# ═══════════════════════════════════════════════════════════════

def convert_pdf_to_markdown(
    file_path: str,
    output_dir: Optional[str] = None,
    password: Optional[str] = None,
    pages: Optional[str] = None,
    keep_line_breaks: bool = False,
) -> str:
    """通用 PDF → Markdown 快速转换（本地 Java 管线，约 0.015s/page）。

    适合：
      - 文本型 PDF
      - 简单排版的文档
      - 不需要图片/表格增强的场景

    Args:
        file_path: 输入 PDF 文件路径。
        output_dir: 输出目录（默认: backend/data/pdf_output/）。
        password: PDF 密码（如加密）。
        pages: 页码范围，如 "1,3,5-7"（默认全部）。
        keep_line_breaks: 是否保留原始换行。

    Returns:
        输出的 Markdown 文件路径。

    Raises:
        FileNotFoundError: PDF 文件不存在或 Java 不可用。
        RuntimeError: 转换失败。
    """
    # 校验输入
    file_path = os.path.abspath(file_path)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"PDF 文件不存在: {file_path}")

    java_check = check_java_available()
    if not java_check["available"]:
        raise RuntimeError(f"Java 环境检查失败: {java_check['error']}")

    # 确定输出目录
    out_dir = output_dir or DEFAULT_OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    logger.info(
        "PDF→Markdown 转换开始: %s → %s",
        file_path, out_dir,
    )

    try:
        opendataloader_pdf.convert(
            input_path=file_path,
            output_dir=out_dir,
            password=password,
            format="markdown",
            pages=pages,
            keep_line_breaks=keep_line_breaks,
            quiet=True,
        )
    except Exception as exc:
        raise RuntimeError(f"PDF 转换失败: {exc}") from exc

    # 返回生成的 Markdown 文件路径（与输入文件同名，扩展名为 .md）
    basename = Path(file_path).stem
    md_path = os.path.join(out_dir, f"{basename}.md")
    if os.path.isfile(md_path):
        logger.info("PDF 转换成功: %s", md_path)
        return md_path

    # 如果生成的文件不在指定输出目录，可能是随输入目录输出
    input_dir = os.path.dirname(file_path)
    alt_path = os.path.join(input_dir, f"{basename}.md")
    if os.path.isfile(alt_path):
        logger.info("PDF 转换成功: %s", alt_path)
        return alt_path

    logger.warning("PDF 转换完成但未找到输出文件，预期路径: %s", md_path)
    return md_path


# ═══════════════════════════════════════════════════════════════
# 混合模式转换（复杂产品手册专用）
# ═══════════════════════════════════════════════════════════════

def convert_pdf_hybrid(
    file_path: str,
    output_dir: Optional[str] = None,
    password: Optional[str] = None,
    pages: Optional[str] = None,
    hybrid_backend: str = "docling-fast",
    hybrid_mode: str = "auto",
    hybrid_url: Optional[str] = None,
    hybrid_timeout: Optional[int] = None,
    hybrid_fallback: bool = True,
    table_method: str = "default",
) -> str:
    """混合模式 PDF 解析 — 简单页走本地，复杂页（表格/扫描件）走 AI 后端。

    适合：
      - 复杂产品手册 PDF
      - 包含大量表格、扫描件、图表的文档
      - 需要高精度表格提取的场景（TEDS 0.928）

    Args:
        file_path: 输入 PDF 文件路径。
        output_dir: 输出目录。
        password: PDF 密码。
        pages: 页码范围。
        hybrid_backend: 混合后端类型（"docling-fast" 或 "hancom-ai"）。
        hybrid_mode: 混合模式（"auto"=动态三选, "full"=全量走AI）。
        hybrid_url: 混合后端服务器 URL（覆盖默认）。
        hybrid_timeout: 请求超时（毫秒，0=无限制）。
        hybrid_fallback: 后端出错时是否回退到本地 Java 管线。
        table_method: 表格检测方法（"default" 或 "cluster"）。

    Returns:
        输出的 Markdown 文件路径。
    """
    file_path = os.path.abspath(file_path)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"PDF 文件不存在: {file_path}")

    java_check = check_java_available()
    if not java_check["available"]:
        raise RuntimeError(f"Java 环境检查失败: {java_check['error']}")

    out_dir = output_dir or DEFAULT_OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    logger.info(
        "PDF→Markdown 混合模式转换开始: %s (hybrid=%s, mode=%s)",
        file_path, hybrid_backend, hybrid_mode,
    )

    # 构建 convert_kwargs
    convert_kwargs = dict(
        input_path=file_path,
        output_dir=out_dir,
        password=password,
        format="markdown",
        pages=pages,
        quiet=True,
        hybrid=hybrid_backend,
        hybrid_mode=hybrid_mode,
        hybrid_fallback=hybrid_fallback,
        table_method=table_method,
        markdown_with_html=True,  # 复杂表格需要 HTML 标签支持
    )

    if hybrid_url:
        convert_kwargs["hybrid_url"] = hybrid_url
    if hybrid_timeout is not None:
        convert_kwargs["hybrid_timeout"] = str(hybrid_timeout)

    try:
        opendataloader_pdf.convert(**convert_kwargs)
    except Exception as exc:
        raise RuntimeError(f"PDF 混合模式转换失败: {exc}") from exc

    basename = Path(file_path).stem
    md_path = os.path.join(out_dir, f"{basename}.md")
    if os.path.isfile(md_path):
        logger.info("PDF 混合模式转换成功: %s", md_path)
        return md_path

    input_dir = os.path.dirname(file_path)
    alt_path = os.path.join(input_dir, f"{basename}.md")
    if os.path.isfile(alt_path):
        return alt_path

    return md_path


# ═══════════════════════════════════════════════════════════════
# 含图片描述的 PDF 转换
# ═══════════════════════════════════════════════════════════════

def convert_pdf_with_images(
    file_path: str,
    output_dir: Optional[str] = None,
    password: Optional[str] = None,
    pages: Optional[str] = None,
    image_output: str = "embedded",
    image_format: str = "png",
    include_header_footer: bool = False,
) -> str:
    """PDF → Markdown 转换，含图片提取和嵌入。

    适合：
      - 需要提取 PDF 中图片的场景
      - 产品目录、说明书等图文混排文档
      - 希望 Markdown 中直接嵌入 Base64 图片的场景

    要求：Hybrid 服务器需配置 --enrich-picture-description
    以启用 AI 图片描述（alt text）生成。

    Args:
        file_path: 输入 PDF 文件路径。
        output_dir: 输出目录。
        password: PDF 密码。
        pages: 页码范围。
        image_output: 图片输出模式（"embedded"=Base64嵌入, "external"=文件引用, "off"=关闭）。
        image_format: 图片格式（"png" 或 "jpeg"）。
        include_header_footer: 是否包含页眉页脚。

    Returns:
        输出的 Markdown 文件路径。
    """
    file_path = os.path.abspath(file_path)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"PDF 文件不存在: {file_path}")

    java_check = check_java_available()
    if not java_check["available"]:
        raise RuntimeError(f"Java 环境检查失败: {java_check['error']}")

    out_dir = output_dir or DEFAULT_OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    logger.info(
        "PDF→Markdown（含图片）转换开始: %s (image_output=%s)",
        file_path, image_output,
    )

    try:
        opendataloader_pdf.convert(
            input_path=file_path,
            output_dir=out_dir,
            password=password,
            format="markdown",
            pages=pages,
            quiet=True,
            image_output=image_output,
            image_format=image_format,
            include_header_footer=include_header_footer,
        )
    except Exception as exc:
        raise RuntimeError(f"PDF 含图片转换失败: {exc}") from exc

    basename = Path(file_path).stem
    md_path = os.path.join(out_dir, f"{basename}.md")
    if os.path.isfile(md_path):
        logger.info("PDF 含图片转换成功: %s", md_path)
        return md_path

    input_dir = os.path.dirname(file_path)
    alt_path = os.path.join(input_dir, f"{basename}.md")
    if os.path.isfile(alt_path):
        return alt_path

    return md_path
