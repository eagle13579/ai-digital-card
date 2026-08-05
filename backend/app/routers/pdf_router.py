"""
PDF 解析路由 — AI数智名片 PDF 注入能力

提供三个端点:
  POST /api/pdf/convert   — 通用 PDF → Markdown 转换
  POST /api/pdf/hybrid    — 混合模式（产品手册/复杂表格）
  POST /api/pdf/health    — PDF 解析引擎健康检查
"""
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.pdf_service import (
    check_java_available,
    convert_pdf_to_markdown,
    convert_pdf_hybrid,
    convert_pdf_with_images,
)

router = APIRouter(prefix="/api/pdf", tags=["PDF 解析"])

# ── 文件上传限制 ──────────────────────────────────────────────
MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS: set = {".pdf"}


# ═══════════════════════════════════════════════════════════════
# 响应模型
# ═══════════════════════════════════════════════════════════════

class PDFConvertResponse(BaseModel):
    """PDF 转换结果响应"""
    success: bool = Field(..., description="转换是否成功")
    message: str = Field("", description="提示信息")
    markdown_path: str = Field("", description="生成的 Markdown 文件路径")
    file_name: str = Field("", description="原始文件名")


class PDFHealthResponse(BaseModel):
    """PDF 引擎健康检查响应"""
    status: str = Field(..., description="服务状态（ok/error）")
    java_available: bool = Field(..., description="Java 是否可用")
    java_version: str = Field("", description="Java 版本")
    opendataloader_version: str = Field("", description="opendataloader-pdf 版本")


# ═══════════════════════════════════════════════════════════════
# 健康检查端点
# ═══════════════════════════════════════════════════════════════

@router.get("/health", response_model=PDFHealthResponse)
async def pdf_health():
    """检查 PDF 解析引擎的健康状态"""
    java_info = check_java_available()

    return PDFHealthResponse(
        status="ok" if java_info["available"] else "error",
        java_available=java_info["available"],
        java_version=java_info["version"],
        opendataloader_version="2.5.0",
    )


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

async def _save_upload(file: UploadFile) -> str:
    """保存上传的 PDF 文件到临时目录，返回文件路径。"""
    # 检查文件扩展名
    ext = os.path.splitext(file.filename or "file.pdf")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，仅支持 PDF 文件",
        )

    # 检查文件大小
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=(
                f"文件过大（{len(contents) / 1024 / 1024:.1f}MB），"
                f"最大允许 {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
            ),
        )

    # 保存临时文件
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    temp_filename = f"pdf_{uuid.uuid4().hex}{ext}"
    temp_path = upload_dir / temp_filename

    with open(temp_path, "wb") as f:
        f.write(contents)

    return str(temp_path)


def _cleanup_temp(file_path: str) -> None:
    """清理临时文件。"""
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
    except Exception:
        pass


def _read_markdown_content(md_path: str) -> str:
    """读取 Markdown 文件内容。"""
    if not os.path.isfile(md_path):
        return ""
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════
# 通用 PDF → Markdown 转换
# ═══════════════════════════════════════════════════════════════

@router.post("/convert", response_model=PDFConvertResponse)
async def pdf_convert(
    file: UploadFile = File(..., description="PDF 文件（最大 50MB）"),
    password: Optional[str] = Form(None, description="PDF 密码（如加密）"),
    pages: Optional[str] = Form(None, description="页码范围，如 \"1,3,5-7\""),
    current_user: User = Depends(get_current_user),
):
    """通用 PDF → Markdown 转换（本地 Java 快速管线）

    适合文本型 PDF、简单排版的文档。
    - 速度: ≈0.015s/page（本地 Java）
    - 支持密码加密 PDF
    - 支持指定页码范围
    """
    temp_path: str = ""
    try:
        temp_path = await _save_upload(file)
        md_path = convert_pdf_to_markdown(
            file_path=temp_path,
            password=password,
            pages=pages,
        )
        content = _read_markdown_content(md_path)

        return PDFConvertResponse(
            success=True,
            message="PDF 转换成功",
            markdown_path=md_path,
            file_name=file.filename or "file.pdf",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"PDF 转换失败: {str(exc)}",
        )
    finally:
        if temp_path:
            _cleanup_temp(temp_path)


# ═══════════════════════════════════════════════════════════════
# 混合模式转换（复杂产品手册专用）
# ═══════════════════════════════════════════════════════════════

@router.post("/hybrid", response_model=PDFConvertResponse)
async def pdf_hybrid(
    file: UploadFile = File(..., description="PDF 文件（最大 50MB，适合产品手册/复杂表格）"),
    password: Optional[str] = Form(None, description="PDF 密码"),
    pages: Optional[str] = Form(None, description="页码范围"),
    hybrid_mode: str = Form("auto", description="混合模式：auto（动态三选）/ full（全量走AI）"),
    hybrid_url: Optional[str] = Form(None, description="Hybrid 后端服务器 URL"),
    table_method: str = Form("default", description="表格方法：default / cluster"),
    current_user: User = Depends(get_current_user),
):
    """混合模式 PDF 解析 — 简单页走本地，复杂页走 AI

    适合：
    - 复杂产品手册 / 说明书 PDF
    - 包含大量表格、扫描件、图表的文档
    - 需要高精度表格提取（TEDS 0.928）

    要求：
    - 如需 AI 增强，需先启动 hybrid server:
        opendataloader-pdf-hybrid --port 5002
    """
    temp_path: str = ""
    try:
        temp_path = await _save_upload(file)

        md_path = convert_pdf_hybrid(
            file_path=temp_path,
            password=password,
            pages=pages,
            hybrid_mode=hybrid_mode,
            hybrid_url=hybrid_url,
            table_method=table_method,
        )
        content = _read_markdown_content(md_path)

        return PDFConvertResponse(
            success=True,
            message="PDF 混合模式转换成功",
            markdown_path=md_path,
            file_name=file.filename or "file.pdf",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"PDF 混合模式转换失败: {str(exc)}",
        )
    finally:
        if temp_path:
            _cleanup_temp(temp_path)


# ═══════════════════════════════════════════════════════════════
# 含图片描述转换
# ═══════════════════════════════════════════════════════════════

@router.post("/with-images", response_model=PDFConvertResponse)
async def pdf_with_images(
    file: UploadFile = File(..., description="PDF 文件（最大 50MB，图文混排文档）"),
    password: Optional[str] = Form(None, description="PDF 密码"),
    pages: Optional[str] = Form(None, description="页码范围"),
    image_output: str = Form("embedded", description="图片输出：embedded（Base64嵌入）/ external（文件引用）"),
    image_format: str = Form("png", description="图片格式：png / jpeg"),
    include_header_footer: bool = Form(False, description="是否包含页眉页脚"),
    current_user: User = Depends(get_current_user),
):
    """PDF → Markdown 转换，含图片提取和嵌入

    适合：
    - 产品目录、说明书等图文混排文档
    - 需要在 Markdown 中嵌入图片的场景
    - image_output=embedded 时图片以 Base64 编码嵌入

    如需 AI 图片描述（alt text），启动 hybrid server 时添加:
        opendataloader-pdf-hybrid --enrich-picture-description
    """
    temp_path: str = ""
    try:
        temp_path = await _save_upload(file)

        md_path = convert_pdf_with_images(
            file_path=temp_path,
            password=password,
            pages=pages,
            image_output=image_output,
            image_format=image_format,
            include_header_footer=include_header_footer,
        )
        content = _read_markdown_content(md_path)

        return PDFConvertResponse(
            success=True,
            message="PDF 含图片转换成功",
            markdown_path=md_path,
            file_name=file.filename or "file.pdf",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"PDF 含图片转换失败: {str(exc)}",
        )
    finally:
        if temp_path:
            _cleanup_temp(temp_path)
