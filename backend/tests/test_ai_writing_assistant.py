"""Tests for WritingAssistant (writing_assistant.py)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.writing_assistant import WritingAssistant


class TestWritingAssistantBuildPrompt:
    """_build_user_prompt — sync prompt construction."""

    def test_bio_full(self):
        prompt = WritingAssistant._build_user_prompt(
            "bio", name="张三", position="工程师",
            company="某公司", industry="IT", skills="Python"
        )
        assert "姓名：张三" in prompt
        assert "职位：工程师" in prompt
        assert "公司：某公司" in prompt
        assert "行业：IT" in prompt
        assert "技能/专长：Python" in prompt
        assert "个人简介" in prompt

    def test_company_full(self):
        prompt = WritingAssistant._build_user_prompt(
            "company", company_name="某科技", industry="AI",
            description="做AI产品", highlights="技术领先"
        )
        assert "公司名称：某科技" in prompt
        assert "行业领域：AI" in prompt
        assert "业务描述：做AI产品" in prompt
        assert "核心优势：技术领先" in prompt

    def test_recommendation(self):
        prompt = WritingAssistant._build_user_prompt(
            "recommendation", name="李四",
            relationship="同事", highlights="优秀"
        )
        assert "被推荐人：李四" in prompt
        assert "关系背景：同事" in prompt
        assert "推荐亮点：优秀" in prompt

    def test_slogan_full(self):
        prompt = WritingAssistant._build_user_prompt(
            "slogan", name="王五", position="CTO",
            company="某公司", core_value="创新"
        )
        assert "姓名：王五" in prompt
        assert "职位：CTO" in prompt
        assert "公司：某公司" in prompt
        assert "核心价值：创新" in prompt

    def test_unknown_purpose(self):
        prompt = WritingAssistant._build_user_prompt("unknown")
        assert prompt == "请生成一段简单的自我介绍。"

    def test_empty_kwargs(self):
        prompt = WritingAssistant._build_user_prompt("bio")
        assert "个人简介" in prompt
        assert "姓名：" not in prompt


class TestWritingAssistantGenerate:
    """generate — async DeepSeek API call."""

    @pytest.mark.asyncio
    async def test_no_api_key(self):
        result = await WritingAssistant.generate("bio", api_key=None)
        assert "需要配置" in result

    @pytest.mark.asyncio
    async def test_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "生成的文案内容。"}}]
        }
        with patch("httpx.AsyncClient") as mc:
            mc.return_value.__aenter__.return_value.post.return_value = mock_resp
            with patch("app.middleware.metrics.track_ai_inference") as tr:
                tr.return_value.__enter__.return_value = None
                result = await WritingAssistant.generate(
                    "bio", api_key="sk-test", name="张三"
                )
                assert result == "生成的文案内容。"

    @pytest.mark.asyncio
    async def test_api_failure(self):
        with patch("httpx.AsyncClient") as mc:
            mc.return_value.__aenter__.return_value.post.side_effect = Exception("网络错误")
            with patch("app.middleware.metrics.track_ai_inference") as tr:
                tr.return_value.__enter__.return_value = None
                result = await WritingAssistant.generate("bio", api_key="sk-test")
                assert "失败" in result
                assert "网络错误" in result

    @pytest.mark.asyncio
    async def test_generate_all(self):
        with patch.object(
            WritingAssistant, "generate", new=AsyncMock(return_value="ok")
        ) as mock_gen:
            fields = {"name": "张三", "position": "工程师", "company": "某公司"}
            results = await WritingAssistant.generate_all(fields, api_key="sk-test")
            assert mock_gen.call_count == 4
            assert set(results.keys()) == {"bio", "company", "recommendation", "slogan"}
            for v in results.values():
                assert v == "ok"

    @pytest.mark.asyncio
    async def test_generate_all_no_api_key(self):
        with patch.object(WritingAssistant, "generate", wraps=WritingAssistant.generate):
            results = await WritingAssistant.generate_all(
                {"name": "张三"}, api_key=None
            )
            for k, v in results.items():
                assert "需要配置" in v, f"{k} did not return placeholder"
