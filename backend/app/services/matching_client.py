"""
匹配引擎 HTTP 客户端
====================
封装对匹配引擎 (:5090) 的 HTTP 调用，提供企业列表拉取和企业匹配能力。

使用方式:
    client = MatchingClient()
    items = await client.match(product={...}, need={...}, top_k=10)
    await client.close()
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)


class MatchingClient:
    """匹配引擎 HTTP 客户端

    基于 httpx.AsyncClient 实现，连接本地匹配引擎 :5090。
    API key 通过环境变量 MATCHING_ENGINE_API_KEY 配置，默认 dev-key-change-in-production。
    """

    BASE_URL: str = "http://127.0.0.1:5090/api/v1"

    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
        self._base_url = base_url or os.getenv("MATCHING_ENGINE_URL", self.BASE_URL)
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def _api_key(self) -> str:
        return os.getenv("MATCHING_ENGINE_API_KEY", "dev-key-change-in-production")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._client

    async def fetch_enterprises(self, page: int = 1, page_size: int = 20) -> list[dict]:
        """拉取企业列表

        Args:
            page: 页码（从 1 开始）
            page_size: 每页数量

        Returns:
            企业列表，失败时返回空列表
        """
        api_key = self._api_key
        try:
            client = await self._get_client()
            resp = await client.get(
                "/enterprises",
                params={"page": page, "page_size": page_size},
                headers={"x-api-key": api_key},
            )
            resp.raise_for_status()
            body = resp.json()
            if body.get("code") == 200:
                return body.get("data", [])
            logger.warning("企业列表返回异常 code=%s", body.get("code"))
            return []
        except Exception as e:
            logger.warning("获取企业列表失败: %s", e)
            return []

    async def match(self, product: dict, need: dict, top_k: int = 10) -> list[dict]:
        """企业匹配 - 基于产品和需求匹配合作伙伴

        Args:
            product: 产品信息字典，如 {"name": "...", "industry": "...", "tags": [...], "description": "..."}
            need: 需求字典，如 {"intent": "cooperation", "requirements": "..."}
            top_k: 返回数量上限

        Returns:
            匹配结果列表，失败时返回空列表
        """
        api_key = self._api_key
        try:
            client = await self._get_client()
            logger.info(
                "[MatchingClient] Calling match, api_key=%s",
                "SET" if api_key else "EMPTY",
            )
            resp = await client.post(
                "/match",
                json={"product": product, "need": need, "top_k": top_k},
                headers={"x-api-key": api_key},
            )
            logger.info("[MatchingClient] Response: %s", resp.status_code)
            resp.raise_for_status()
            body = resp.json()
            logger.info(
                "[MatchingClient] Body: code=%s, data_len=%s",
                body.get("code"),
                len(body.get("data", [])),
            )
            if body.get("code") == 200:
                return body.get("data", [])
            logger.warning("匹配返回异常 code=%s", body.get("code"))
            return []
        except Exception as e:
            logger.error("[MatchingClient] Error: %s", e, exc_info=True)
            return []

    async def close(self):
        """关闭底层 HTTP 客户端连接"""
        if self._client:
            await self._client.aclose()
            self._client = None
