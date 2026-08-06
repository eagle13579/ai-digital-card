"""
AI 数字名片 —— 匹配引擎客户端

对接匹配引擎 (matching-engine) API:
  http://127.0.0.1:5090/api/v1/…

用法:
    client = MatchingClient()
    enterprises = await client.get_enterprises(page=1, page_size=20)
    matches = await client.match_enterprises(ent_id=42, intent="寻找合作伙伴", top_k=10)
"""

from __future__ import annotations

import os
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
DEFAULT_BASE_URL = "http://127.0.0.1:5090"
DEFAULT_TIMEOUT = 5.0  # 秒
ENV_KEY_NAME = "MATCHING_ENGINE_KEY"
DEFAULT_API_KEY = "dev-key-change-in-production"


class MatchingClient:
    """AI 数字名片专用的匹配引擎客户端。

    与芯森态的 MatchingClient 不同，本客户端专为 AI 数字名片场景设计，
    不包含芯森态的业务字段。
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """初始化客户端。

        Args:
            base_url: 匹配引擎基础地址，默认 http://127.0.0.1:5090
            api_key: API Key；不传则从环境变量 MATCHING_ENGINE_KEY 读取
            timeout: 请求超时秒数，默认 5 秒
        """
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key or os.getenv(ENV_KEY_NAME, DEFAULT_API_KEY)

        # httpx 连接池 —— 支持连接复用、自动重试连接
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout),
            headers={
                "x-api-key": self._api_key,
                "Content-Type": "application/json",
            },
        )

    # ------------------------------------------------------------------
    # 底层请求封装
    # ------------------------------------------------------------------

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """发送 GET 请求并返回 JSON 响应。"""
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """发送 POST 请求并返回 JSON 响应。"""
        resp = await self._client.post(path, json=json)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # 公开业务方法
    # ------------------------------------------------------------------

    async def get_enterprises(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """分页获取企业列表。

        Args:
            page: 页码，从 1 开始
            page_size: 每页条数

        Returns:
            匹配引擎返回的企业分页数据
        """
        return await self._get(
            "/api/v1/enterprises",
            params={"page": page, "page_size": page_size},
        )

    async def match_enterprises(
        self,
        enterprise_id: int,
        intent: str,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """根据企业 ID 和意图进行企业匹配。

        Args:
            enterprise_id: 目标企业 ID
            intent: 匹配意图描述（例如 "寻找供应链合作伙伴"）
            top_k: 返回的最匹配数量

        Returns:
            匹配结果列表
        """
        return await self._post(
            "/api/v1/match",
            json={
                "enterprise_id": enterprise_id,
                "intent": intent,
                "top_k": top_k,
            },
        )

    async def send_feedback(
        self,
        enterprise_id: int,
        action: str,
        score: float,
    ) -> dict[str, Any]:
        """提交匹配反馈。

        Args:
            enterprise_id: 被反馈的企业 ID
            action: 反馈动作（如 "click", "like", "dislike", "skip"）
            score: 评分（0.0 ~ 1.0）

        Returns:
            反馈处理结果
        """
        return await self._post(
            "/api/v1/feedback",
            json={
                "enterprise_id": enterprise_id,
                "action": action,
                "score": score,
            },
        )

    async def get_trending(self) -> dict[str, Any]:
        """获取实时 trending 企业列表。"""
        return await self._get("/api/v1/realtime/trending")

    async def get_bandit_stats(self) -> dict[str, Any]:
        """获取 Bandit 算法统计。"""
        return await self._get("/api/v1/bandit/stats")

    async def get_abtest_stats(self) -> dict[str, Any]:
        """获取 A/B 测试统计。"""
        return await self._get("/api/v1/abtest/stats")

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """关闭底层 httpx 连接池，释放资源。"""
        await self._client.aclose()

    async def __aenter__(self) -> "MatchingClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
