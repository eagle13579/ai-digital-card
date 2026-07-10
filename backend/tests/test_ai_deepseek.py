"""DeepSeek AI 代理测试 — API密钥管理 & 错误处理 & 请求格式"""

from __future__ import annotations
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport


class TestDeepSeekAPIManagement:
    """DeepSeek API 密钥管理和配置测试"""

    def test_get_api_key_from_settings(self):
        """从 settings 获取 DEEPSEEK_API_KEY"""
        from app.routers.ai_deepseek import _get_api_key
        from app.config import settings

        # 当 settings 中有值时
        original_value = settings.DEEPSEEK_API_KEY
        try:
            settings.DEEPSEEK_API_KEY = "test-key-12345"
            key = _get_api_key()
            assert key == "test-key-12345"
        finally:
            settings.DEEPSEEK_API_KEY = original_value

    def test_get_api_key_empty_returns_empty_string(self):
        """当 API Key 为空时应返回空字符串"""
        from app.routers.ai_deepseek import _get_api_key
        from app.config import settings

        original_value = settings.DEEPSEEK_API_KEY
        try:
            settings.DEEPSEEK_API_KEY = ""
            key = _get_api_key()
            assert key == ""
        finally:
            settings.DEEPSEEK_API_KEY = original_value


class TestDeepSeekErrorHandling:
    """DeepSeek API 错误处理测试"""

    @pytest.mark.asyncio
    async def test_chat_without_api_key_returns_502(self, client):
        """未配置 API Key 时调用 /api/v1/ai/deepseek/chat 返回 502"""
        from app.config import settings

        original = settings.DEEPSEEK_API_KEY
        try:
            settings.DEEPSEEK_API_KEY = ""
            payload = {
                "messages": [{"role": "user", "content": "Hello"}],
            }
            resp = await client.post("/api/v1/ai/deepseek/chat", json=payload)
            assert resp.status_code == 502
            assert "未配置" in resp.text or "API Key" in resp.text
        finally:
            settings.DEEPSEEK_API_KEY = original

    @pytest.mark.asyncio
    async def test_chat_with_empty_messages_returns_400(self, client):
        """空消息列表应返回 400"""
        payload = {"messages": []}
        resp = await client.post("/api/v1/ai/deepseek/chat", json=payload)
        assert resp.status_code == 400
        assert "不能为空" in resp.text

    @pytest.mark.asyncio
    async def test_generate_with_empty_prompt_returns_400(self, client):
        """空 prompt 应返回 400"""
        payload = {"prompt": "  ", "temperature": 0.7, "max_tokens": 2048}
        resp = await client.post("/api/v1/ai/deepseek/generate", json=payload)
        # The 'strip' check is server-side in generate endpoint
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_generate_without_api_key_returns_502(self, client):
        """未配置 API Key 时调用 /api/v1/ai/deepseek/generate 返回 502"""
        from app.config import settings

        original = settings.DEEPSEEK_API_KEY
        try:
            settings.DEEPSEEK_API_KEY = ""
            payload = {"prompt": "写一个名片文案"}
            resp = await client.post("/api/v1/ai/deepseek/generate", json=payload)
            assert resp.status_code == 502
            assert "未配置" in resp.text or "API Key" in resp.text
        finally:
            settings.DEEPSEEK_API_KEY = original

    @pytest.mark.asyncio
    async def test_status_endpoint_returns_200(self, client):
        """GET /api/v1/ai/deepseek/status 应返回 200 (即使未配置)"""
        resp = await client.get("/api/v1/ai/deepseek/status")
        assert resp.status_code == 200
        body = resp.json()
        assert "status" in body
        assert "configured" in body
        # 未配置时 should 返回 error
        assert body["configured"] is False
        assert body["status"] == "error"


class TestDeepSeekRequestFormat:
    """DeepSeek API 请求格式和模拟响应测试"""

    @pytest.mark.asyncio
    async def test_chat_request_format(self):
        """验证发送给 DeepSeek API 的请求格式是否正确"""
        from app.routers.ai_deepseek import _call_deepseek

        test_payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "test"}],
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        # 使用 mock 模拟 httpx.AsyncClient 的 POST 方法
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "choices": [{"message": {"content": "Hello!"}}],
                "usage": {"total_tokens": 10},
            }
        )
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await _call_deepseek(test_payload)

            # 验证请求参数
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert args[0] == "https://api.deepseek.com/v1/chat/completions"
            assert kwargs["json"]["model"] == "deepseek-chat"
            assert kwargs["json"]["messages"][0]["role"] == "user"
            assert "temperature" in kwargs["json"]

            # 验证响应被正确解析
            assert result["choices"][0]["message"]["content"] == "Hello!"

    @pytest.mark.asyncio
    async def test_http_401_returns_502(self):
        """DeepSeek API 返回 401 时应返回 502 并提示认证失败"""
        from app.routers.ai_deepseek import _call_deepseek

        test_payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "test"}],
        }

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = Exception(
            "401 Client Error: Unauthorized"
        )
        # httpx.HTTPStatusError 需要 response 属性
        import httpx

        http_error = httpx.HTTPStatusError(
            "401 Unauthorized", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = http_error

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await _call_deepseek(test_payload)
            assert exc_info.value.status_code == 502
            assert "认证失败" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_timeout_returns_504(self):
        """DeepSeek API 超时应返回 504"""
        from app.routers.ai_deepseek import _call_deepseek

        test_payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "test"}],
        }

        import httpx

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException(
                "Connection timed out", request=MagicMock()
            )

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await _call_deepseek(test_payload)
            assert exc_info.value.status_code == 504
            assert "超时" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_network_error_returns_502(self):
        """DeepSeek API 网络错误时应返回 502"""
        from app.routers.ai_deepseek import _call_deepseek

        test_payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "test"}],
        }

        import httpx

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.RequestError(
                "DNS resolution failed", request=MagicMock()
            )

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await _call_deepseek(test_payload)
            assert exc_info.value.status_code == 502
            assert "网络" in exc_info.value.detail or "连接" in exc_info.value.detail
