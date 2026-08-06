"""
PrivateMatchEngine HTTP 客户端
================================
封装对 PrivateMatchEngine (芯森态 :5080) 的 HTTP 调用，提供企业批量评分、
合同查询和推荐结果二次排序能力。

使用方式:
    client = PrivateMatchClient()
    # 批量评分（推荐用于 rerank）
    result = await client.score_enterprises(enterprises=[...], context={...})
    # 合同查询
    contract = await client.get_contract(enterprise_id="123")
    await client.close()
"""

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://127.0.0.1:5080"
DEFAULT_TIMEOUT = 5.0


class PrivateMatchClient:
    """PrivateMatchEngine (芯森态) 异步 HTTP 客户端

    基于 httpx.AsyncClient 实现。
    核心 API (来自 OpenAPI spec):
      - POST /api/v1/score          — 批量企业评分
      - POST /api/v1/tenant/config  — 租户权重配置
      - GET  /api/v1/contract/{id}  — 企业签约状态查询
      - GET  /health                — 健康检查
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._client

    async def score_enterprises(
        self,
        enterprises: list[dict[str, Any]],
        context: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """批量企业评分 — PME 核心评分接口

        POST /api/v1/score

        Args:
            enterprises: 企业列表，每项须含 id, name；可选 industry, tags, score, description
            context:     评分上下文，可选 user_id, tenant_id, preferences

        Returns:
            评分后的企业列表（含额外评分字段），失败返回空列表
        """
        client = await self._get_client()
        try:
            payload: dict[str, Any] = {
                "enterprises": enterprises,
                "context": context or {},
            }
            resp = await client.post("/api/v1/score", json=payload)
            if resp.status_code == 200:
                body = resp.json()
                # 兼容两种返回格式: 直接列表 或 {data: [...]}
                if isinstance(body, list):
                    return body
                return body.get("data", body.get("results", body.get("enterprises", [])))
            logger.warning("score_enterprises 返回 status=%s", resp.status_code)
            return []
        except Exception as e:
            logger.warning("score_enterprises 调用失败: %s", e)
            return []

    async def get_contract(self, enterprise_id: str) -> dict[str, Any]:
        """查询企业签约状态

        GET /api/v1/contract/{enterprise_id}

        Args:
            enterprise_id: 企业 ID

        Returns:
            合同信息字典，失败返回空字典
        """
        client = await self._get_client()
        try:
            resp = await client.get(f"/api/v1/contract/{enterprise_id}")
            if resp.status_code == 200:
                return resp.json()
            logger.warning("get_contract 返回 status=%s", resp.status_code)
            return {}
        except Exception as e:
            logger.warning("get_contract 调用失败: %s", e)
            return {}

    async def rerank(
        self,
        items: list[dict[str, Any]],
        context: Optional[dict[str, Any]] = None,
        top_k: int = 20,
    ) -> list[dict[str, Any]]:
        """推荐结果二次排序 — 使用 PME 批量评分对已有推荐列表重排

        流程:
          1. 将 items 转换为 PME EnterpriseItem 格式
          2. 调用 score_enterprises 批量评分
          3. 按 PME 评分降序排列

        Args:
            items:  待排序的推荐结果列表
            context: 排序上下文 (user_id, tenant_id, preferences)
            top_k:   返回数量上限

        Returns:
            排序后的结果列表（含 pme_score 等额外字段）
        """
        if not items:
            return []

        # 转换为 EnterpriseItem 格式
        enterprises = []
        for item in items:
            enterprises.append({
                "id": str(item.get("enterprise_id", item.get("user_id", item.get("id", "")))),
                "name": str(item.get("enterprise_name", item.get("name", item.get("company", "")))),
                "industry": str(item.get("industry", item.get("title", ""))),
                "tags": item.get("tags", item.get("common_tags", [])),
                "score": float(item.get("score", 0.0)),
                "description": str(item.get("description", item.get("intro", ""))),
            })

        if not enterprises:
            return items[:top_k]

        scored = await self.score_enterprises(enterprises, context)

        if not scored:
            return items[:top_k]

        # 合并评分结果回原始 items
        scored_map: dict[str, dict] = {}
        for s in scored:
            sid = str(s.get("id", ""))
            scored_map[sid] = s

        ranked = []
        for item in items:
            eid = str(item.get("enterprise_id", item.get("user_id", item.get("id", ""))))
            pm = scored_map.get(eid, {})
            pme_score = float(pm.get("score", pm.get("pme_score", 0.0)))
            dimensions = pm.get("dimensions", pm.get("details", {}))
            if isinstance(dimensions, dict):
                dimensions = {k: v.get("raw", v.get("score", v)) if isinstance(v, dict) else v for k, v in dimensions.items()}

            ranked.append({
                **item,
                "pme_score": pme_score,
                "pme_dimensions": dimensions if isinstance(dimensions, dict) else {},
                "pme_ranked": True,
                "original_score": float(item.get("score", 0.0)),
                "score": pme_score if pme_score > 0 else float(item.get("score", 0.0)),
            })

        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked[:top_k]

    async def health(self) -> dict[str, Any]:
        """PME 健康检查"""
        client = await self._get_client()
        try:
            resp = await client.get("/health")
            if resp.status_code == 200:
                return resp.json()
            return {"status": "unhealthy", "code": resp.status_code}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    async def close(self):
        """关闭底层 HTTP 客户端连接"""
        if self._client:
            await self._client.aclose()
            self._client = None
