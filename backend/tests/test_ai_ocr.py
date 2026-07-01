"""Tests for OCRScanner (ocr.py)."""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.ai.ocr import OCRScanner


class TestOCRPreprocess:
    """preprocess_image — sync PIL image processing."""

    def test_color_to_grayscale(self):
        img = Image.new("RGB", (100, 50), color=(200, 200, 200))
        processed = OCRScanner.preprocess_image(img)
        assert processed.mode == "L"
        assert processed.size == (100, 50)

    def test_already_grayscale(self):
        img = Image.new("L", (200, 80), color=128)
        processed = OCRScanner.preprocess_image(img)
        assert processed.mode == "L"

    def test_extreme_small_image(self):
        img = Image.new("RGB", (1, 1), color=0)
        processed = OCRScanner.preprocess_image(img)
        assert processed.mode == "L"


class TestOCRContactInfo:
    """extract_contact_info — sync regex extraction."""

    def test_full_contact(self):
        text = "电话：13800138000\n邮箱：test@example.com\n微信：wechat123"
        result = OCRScanner.extract_contact_info(text)
        assert result["phone"] == "13800138000"
        assert result["email"] == "test@example.com"
        assert result["wechat"] == "wechat123"

    def test_landline_fallback(self):
        text = "Tel: 010-12345678\nEmail: a@b.com"
        result = OCRScanner.extract_contact_info(text)
        assert result["phone"] == "010-12345678"
        assert result["email"] == "a@b.com"

    def test_wechat_alpha_fallback(self):
        text = "联系人 test_user_42 其他内容"
        result = OCRScanner.extract_contact_info(text)
        assert result["wechat"] == "test_user_42"

    def test_no_info(self):
        result = OCRScanner.extract_contact_info("纯文本内容，无任何联系方式。")
        assert result["phone"] is None
        assert result["email"] is None
        assert result["wechat"] is None

    def test_wechat_labeled(self):
        text = "WX: myWechat123"
        result = OCRScanner.extract_contact_info(text)
        assert result["wechat"] == "myWechat123"


class TestOCRBusinessInfo:
    """extract_business_info — sync regex extraction."""

    def test_full_business(self):
        text = ("公司：某科技企业有限公司\n职位：技术总监\n"
                "地址：北京市海淀区\nhttps://example.com")
        result = OCRScanner.extract_business_info(text)
        assert "科技" in result["company_name"]
        assert result["position"] is not None
        assert result["website"] == "https://example.com"

    def test_company_line_fallback(self):
        # "有限公司" followed by '-' prevents regex match; fallback triggers
        text = "编号：ABC-有限公司-123\n联系人王经理"
        result = OCRScanner.extract_business_info(text)
        assert "有限公司" in result["company_name"]

    def test_position_line_fallback(self):
        text = "某公司\n技术部总监\n地址：上海"
        result = OCRScanner.extract_business_info(text)
        assert result["position"] is not None

    def test_no_info(self):
        result = OCRScanner.extract_business_info("随便写写。")
        assert result["company_name"] is None
        assert result["position"] is None
        assert result["address"] is None
        assert result["website"] is None


class TestOCRScanCard:
    """scan_card / scan_with_paddle — sync file-based scanning."""

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="图像文件不存在"):
            OCRScanner.scan_card("/nonexistent/img.png")

    @patch("app.ai.ocr._PADDLE_AVAILABLE", False)
    def test_no_paddle_path(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        try:
            Image.new("RGB", (50, 20)).save(tmp.name)
            tmp.close()
            result = OCRScanner.scan_card(tmp.name)
            assert "OCR" in result
        finally:
            os.unlink(tmp.name)

    @patch("app.ai.ocr._PADDLE_AVAILABLE", False)
    def test_no_paddle_image_obj(self):
        img = Image.new("RGB", (50, 20))
        result = OCRScanner.scan_card(img)
        assert "OCR" in result

    @patch("app.ai.ocr._PADDLE_AVAILABLE", False)
    def test_external_ocr_flag(self):
        img = Image.new("RGB", (50, 20))
        result = OCRScanner.scan_card(img, use_external_ocr=True)
        assert "PaddleOCR" in result or "OCR" in result

    def test_scan_with_paddle_unavailable(self):
        with patch("app.ai.ocr._PADDLE_AVAILABLE", False):
            text, conf = OCRScanner.scan_with_paddle("/tmp/img.png")
            assert text == ""
            assert conf == 0.0
