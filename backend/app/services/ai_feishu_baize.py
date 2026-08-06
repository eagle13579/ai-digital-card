"""飞书白泽 AI 服务 — 基于飞书开放平台 AI API。

使用飞书应用凭证（app_id + app_secret）获取 tenant_access_token，
然后调用飞书白泽大模型 API。

认证流程:
    1. POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
       → 获取 tenant_access_token
    2. 使用 token 调用 AI API: https://open.feishu.cn/open-apis/ai/v1/chat/completions

配置驱动: 没有 FEISHU_APP_ID 时自动降级到日志输出。
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, AsyncGenerator

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class FeishuBaizeService:
    """飞书白泽 AI 服务封装。"""

    _tenant_token: str = ""
    _token_expires_at: float = 0.0

    def _check_config(self) -> bool:
        return bool(settings.FEISHU_APP_ID and settings.FEISHU_APP_SECRET)

    async def _ensure_token(self) -> str:
        """获取或刷新飞书 tenant_access_token。"""
        now = time.time()
        if self._tenant_token and now < self._token_expires_at - 60:
            return self._tenant_token

        payload = {
            "app_id": settings.FEISHU_APP_ID,
            "app_secret": settings.FEISHU_APP_SECRET,
        }

        token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(token_url, json=payload)
                response.raise_for_status()
                result = response.json()
            except httpx.HTTPStatusError as e:
                logger.error("飞书 token 获取失败: %s", e.response.text)
                raise
            except Exception as e:
                logger.error("飞书 token 请求异常: %s", e)
                raise

        self._tenant_token = result.get("tenant_access_token", "")
        expire = result.get("expire", 7200)
        self._token_expires_at = now + expire
        logger.debug("飞书 tenant_access_token 已刷新，有效 %s 秒", expire)
        return self._tenant_token

    async def _get_auth_headers(self) -> dict[str, str]:
        token = await self._ensure_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncGenerator[str, None]:
        """调用飞书白泽进行对话。

        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "你好"}]
            model: 模型名称，默认使用 FEISHU_BAIZE_DEFAULT_MODEL
            temperature: 温度参数，控制输出随机性
            max_tokens: 最大输出 token 数
            stream: 是否流式输出

        Returns:
            非流式: 返回完整响应字典
            流式: 返回 token 生成器
        """
        if not self._check_config():
            logger.warning("飞书配置未完成，无法调用白泽 AI")
            raise RuntimeError("飞书配置未完成")

        headers = await self._get_auth_headers()
        model_name = model or settings.FEISHU_BAIZE_DEFAULT_MODEL

        payload: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        api_url = settings.FEISHU_BAIZE_API_URL

        async with httpx.AsyncClient(timeout=30.0) as client:
            if stream:
                async with client.stream("POST", api_url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_text():
                        if chunk.startswith("data: "):
                            chunk = chunk[6:]
                        if chunk.strip():
                            try:
                                data = json.loads(chunk)
                                if "choices" in data and data["choices"]:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
            else:
                response = await client.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                raise StopAsyncIteration(response.json())

    async def generate(
        self,
        prompt: str,
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """生成文本（单次提示词）。

        Args:
            prompt: 提示词
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大输出 token 数

        Returns:
            生成的文本内容
        """
        messages = [{"role": "user", "content": prompt}]
        result = await self.chat(messages, model, temperature, max_tokens)

        if isinstance(result, dict) and "error" in result:
            logger.error("飞书白泽生成失败: %s", result["error"])
            return ""

        if isinstance(result, dict):
            choices = result.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")

        return ""


feishu_baize = FeishuBaizeService()