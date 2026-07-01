"""Tests for AIExtractor (extractor.py)."""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.extractor import AIExtractor


class TestAIExtractorExtractFields:
    """extract_fields_from_text — sync regex field extraction."""

    def test_full_fields(self):
        text = ("姓名：张三\n职位：技术总监\n公司：某科技公司\n"
                "电话：13800138000\n邮箱：zhang@test.com\n微信：wx_zhang")
        result = AIExtractor.extract_fields_from_text(text)
        assert result["name"] == "张三"
        assert result["phone"] == "13800138000"
        assert result["email"] == "zhang@test.com"
        assert result["wechat"] == "wx_zhang"
        assert result["title"] == "技术总监"
        assert result["company"] == "某科技公司"
        assert result["raw_text"] == text.strip()

    def test_partial_fields(self):
        text = "13800138000\ncontact@example.com"
        result = AIExtractor.extract_fields_from_text(text)
        assert result["phone"] == "13800138000"
        assert result["email"] == "contact@example.com"
        assert result["name"] is None

    def test_chinese_name_fallback(self):
        text = "李四\n13800138000\ntest@mail.com"
        result = AIExtractor.extract_fields_from_text(text)
        assert result["name"] == "李四"

    def test_empty_text(self):
        result = AIExtractor.extract_fields_from_text("")
        assert result["name"] is None
        assert result["phone"] is None
        assert result["raw_text"] == ""

    def test_no_matches(self):
        result = AIExtractor.extract_fields_from_text("纯文本段落，没有名片信息。")
        assert result["name"] is None
        assert result["phone"] is None


class TestAIExtractorDefaultLayout:
    """_default_layout — sync layout generation."""

    def test_complete_fields(self):
        fields = {"name": "张三", "title": "总监", "company": "某公司",
                  "phone": "13800138000", "email": "a@b.com", "wechat": "wx123"}
        pages = AIExtractor._default_layout(fields)
        assert len(pages) == 4
        assert pages[0]["content_type"] == "cover"
        assert "张三" in pages[0]["content"]
        assert "13800138000" in pages[1]["content"]
        assert pages[3]["content_type"] == "image"

    def test_minimal_fields(self):
        fields = {"name": "张三"}
        pages = AIExtractor._default_layout(fields)
        assert pages[0]["content"] == "张三"
        assert "暂无联系方式" in pages[1]["content"]
        assert "暂无企业信息" in pages[2]["content"]


class TestAIExtractorPDF:
    """extract_text_from_pdf — sync PDF extraction."""

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="PDF 文件不存在"):
            AIExtractor.extract_text_from_pdf("/nonexistent/test.pdf")

    @patch("app.ai.extractor.os.path.exists", return_value=True)
    @patch("app.ai.extractor.pdfplumber")
    def test_empty_pdf(self, mock_pdf, mock_exists):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None
        mock_pdf.open.return_value.__enter__.return_value.pages = [mock_page]
        with pytest.raises(ValueError, match="未能从 PDF 中提取出文本"):
            AIExtractor.extract_text_from_pdf("/tmp/empty.pdf")

    @patch("app.ai.extractor.os.path.exists", return_value=True)
    @patch("app.ai.extractor.pdfplumber")
    def test_successful_extraction(self, mock_pdf, mock_exists):
        p1, p2 = MagicMock(), MagicMock()
        p1.extract_text.return_value = "第一页内容\n"
        p2.extract_text.return_value = "第二页内容"
        mock_pdf.open.return_value.__enter__.return_value.pages = [p1, p2]
        text = AIExtractor.extract_text_from_pdf("/tmp/test.pdf")
        assert "第一页内容" in text
        assert "第二页内容" in text


class TestAIExtractorAsync:
    """Async methods: generate_summary, auto_layout, rag_match."""

    @pytest.mark.asyncio
    async def test_generate_summary_no_key(self):
        result = await AIExtractor.generate_summary("test", api_key=None)
        assert "需要配置" in result

    @pytest.mark.asyncio
    async def test_generate_summary_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "生成的成功摘要。"}}]
        }
        with patch("httpx.AsyncClient") as mc:
            mc.return_value.__aenter__.return_value.post.return_value = mock_resp
            result = await AIExtractor.generate_summary("test", api_key="sk-test")
            assert result == "生成的成功摘要。"

    @pytest.mark.asyncio
    async def test_generate_summary_failure(self):
        with patch("httpx.AsyncClient") as mc:
            mc.return_value.__aenter__.return_value.post.side_effect = Exception("Timeout")
            result = await AIExtractor.generate_summary("test", api_key="sk-test")
            assert "失败" in result and "Timeout" in result

    @pytest.mark.asyncio
    async def test_auto_layout_no_key(self):
        result = await AIExtractor.auto_layout({"name": "张三"}, api_key=None)
        assert len(result) == 4
        assert result[0]["content_type"] == "cover"

    @pytest.mark.asyncio
    async def test_auto_layout_api_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {
                "content": '[{"sort_order":0,"content_type":"cover","content":"张三"}]'
            }}]
        }
        with patch("httpx.AsyncClient") as mc:
            mc.return_value.__aenter__.return_value.post.return_value = mock_resp
            result = await AIExtractor.auto_layout({"name": "张三"}, api_key="sk-test")
            assert len(result) == 1
            assert result[0]["content_type"] == "cover"

    @pytest.mark.asyncio
    async def test_rag_match_no_key_with_tags(self):
        with patch(
            "app.ai.vector_search.VectorSearchEngine.compute_semantic_similarity",
            return_value=0.5,
        ):
            result = await AIExtractor.rag_match(
                "找Python开发者", ["Python", "开发"], api_key=None
            )
            assert result["fallback"] is True
            assert result["matched"] is True
            assert result["confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_rag_match_no_key_no_tags(self):
        result = await AIExtractor.rag_match("query", [], api_key=None)
        assert result["fallback"] is True
        assert result["matched"] is False
