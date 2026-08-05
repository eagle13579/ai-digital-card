"""
OCR 扫描路由 - 名片图像识别与联系方式提取
POST /api/ocr/scan: 接收图片 → OCR识别 → 返回结构化信息
"""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from app.ai.ocr import OCRScanner
from app.config import settings
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/ocr", tags=["OCR扫描"])

# 文件上传限制
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class OCRScanResponse(BaseModel):
    """OCR 扫描结果响应"""
    raw_text: str = Field("", description="OCR 识别的原始文本")
    contact: dict = Field(
        default_factory=lambda: {"phone": None, "email": None, "wechat": None},
        description="提取的联系方式",
    )
    business: dict = Field(
        default_factory=lambda: {
            "company_name": None,
            "position": None,
            "address": None,
            "website": None,
        },
        description="提取的企业信息",
    )
    text_lines: list[dict] = Field(
        default_factory=list,
        description="每行文本的详细信息（text + confidence + box）",
    )


@router.post("/scan", response_model=OCRScanResponse)
async def ocr_scan(
    file: UploadFile = File(..., description="名片图片文件（jpg/png/bmp/webp，最大10MB）"),
    current_user: User = Depends(get_current_user),
):
    """
    扫描名片图片，提取文字信息并结构化解析

    - 支持格式: jpg, jpeg, png, bmp, webp
    - 最大文件大小: 10MB
    - 返回: raw_text（原始识别文本）+ contact（联系方式）+ business（企业信息）
    """
    # ── 文件校验 ──────────────────────────────────────────────
    # 检查文件扩展名
    ext = os.path.splitext(file.filename or "image.jpg")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，支持: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 检查文件大小
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大（{len(contents) / 1024 / 1024:.1f}MB），最大允许 {MAX_FILE_SIZE / 1024 / 1024:.0f}MB",
        )

    # ── 保存临时文件 ──────────────────────────────────────────
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    temp_filename = f"ocr_{uuid.uuid4().hex}{ext}"
    temp_path = upload_dir / temp_filename

    try:
        with open(temp_path, "wb") as f:
            f.write(contents)

        # ── OCR 识别 ──────────────────────────────────────────
        from PIL import Image

        image = Image.open(temp_path)

        scanner = OCRScanner()
        raw_text = scanner.scan_card(image, use_external_ocr=True)

        # 如果 PaddleOCR 不可用，回退到预处理后的文本
        if not raw_text or raw_text.startswith("【"):
            # 重新用路径方式尝试
            raw_text = scanner.scan_card(str(temp_path))

        # ── 提取结构化信息 ────────────────────────────────────
        contact = scanner.extract_contact_info(raw_text)
        business = scanner.extract_business_info(raw_text)

        # ── 获取详细行信息（仅当 PaddleOCR 可用时） ────────────
        text_lines = scanner.scan_with_paddle_detailed(str(temp_path))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR 识别失败: {str(e)}",
        )
    finally:
        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()

    return OCRScanResponse(
        raw_text=raw_text,
        contact=contact,
        business=business,
        text_lines=text_lines,
    )
