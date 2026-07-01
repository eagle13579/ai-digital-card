"""AI 能力模块 - OCR 扫描 + NLP 提取 + DeepSeek 摘要 + 向量搜索 + 文案写作 + 优化分析"""

from app.ai.extractor import AIExtractor
from app.ai.ocr import OCRScanner
from app.ai.vector_search import (
    VectorSearchEngine,
    VectorSearchIndex,
    DocumentBuilder,
    EmbeddingBackend,
    NumpyEmbedding,
    M3EEmbedding,
    OpenAIEmbedding,
    DeepSeekEmbedding,
    get_embedding_backend,
    get_vector_index,
    embed_text,
    embed_single,
    rerank,
    cosine_similarity,
    sync_vector_index,
)
from app.ai.writing_assistant import WritingAssistant
from app.ai.optimization import OptimizationAnalyzer
from app.ai.ab_testing import ABTestingEngine, get_ab_testing_engine
from app.ai.rag_pipeline import (
    RAGPipeline,
    DeepSeekClient,
    ContextBuilder,
    RAGContext,
    RAGResponse,
)
from app.ai.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphBuilder,
    CachedKnowledgeGraphBuilder,
    GraphNode,
    GraphEdge,
)
from app.ai.recommendation import (
    RecommendEngine,
    RecommendItem,
    RecommendResult,
)

__all__ = [
    "AIExtractor",
    "OCRScanner",
    "VectorSearchEngine",
    "VectorSearchIndex",
    "DocumentBuilder",
    "EmbeddingBackend",
    "NumpyEmbedding",
    "M3EEmbedding",
    "OpenAIEmbedding",
    "DeepSeekEmbedding",
    "get_embedding_backend",
    "get_vector_index",
    "embed_text",
    "embed_single",
    "rerank",
    "cosine_similarity",
    "sync_vector_index",
    "WritingAssistant",
    "OptimizationAnalyzer",
    "ABTestingEngine",
    "get_ab_testing_engine",
    "RAGPipeline",
    "DeepSeekClient",
    "ContextBuilder",
    "RAGContext",
    "RAGResponse",
    "KnowledgeGraph",
    "KnowledgeGraphBuilder",
    "CachedKnowledgeGraphBuilder",
    "GraphNode",
    "GraphEdge",
    "RecommendEngine",
    "RecommendItem",
    "RecommendResult",
    "AIServiceClient",
]


# ======================================================================
# AIServiceClient — HTTP 远程调用 + 本地 fallback
# ======================================================================

import aiohttp
import asyncio
import json
import logging
from typing import Any, Optional

import app.ai.ocr as _ai_ocr
import app.ai.extractor as _ai_extractor
import app.ai.writing_assistant as _ai_writing
import app.ai.ab_testing as _ai_ab
import app.ai.recommendation as _ai_recommend
import app.ai.vector_search as _ai_vector
import app.ai.rag_pipeline as _ai_rag

logger = logging.getLogger(__name__)


class AIServiceClient:
    """AI 服务客户端 — 统一 HTTP 远程调用，失败时自动 fallback 到本地直接调用。

    用法:
        client = AIServiceClient()
        result = await client.vector_search(query="xxx")
        result = await client.rag(query="xxx", user_id=1)
    """

    def __init__(self, base_url: str = "http://localhost:8202", timeout: int = 3):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ── 通用远程调用 + fallback ────────────────────────────────

    async def _remote_call(self, endpoint: str, **kwargs) -> dict:
        """尝试 HTTP 远程调用，超时或异常时抛出。"""
        url = f"{self.base_url}/ai/{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=kwargs, timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                resp.raise_for_status()
                return await resp.json()

    def _run_local(self, fn, *args, **kwargs):
        """同步本地 fallback（在 executor 中运行以避免阻塞事件循环）。"""
        return fn(*args, **kwargs)

    async def _run_local_async(self, fn, *args, **kwargs):
        """异步本地 fallback。"""
        if asyncio.iscoroutinefunction(fn):
            return await fn(*args, **kwargs)
        else:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, fn, *args, **kwargs)

    # ── 对外方法 ───────────────────────────────────────────────

    async def vector_search(self, query: str, top_k: int = 10, **kwargs) -> dict:
        """向量搜索。先远程，失败 fallback 到本地 VectorSearchEngine。"""
        try:
            return await self._remote_call("vector_search", query=query, top_k=top_k, **kwargs)
        except Exception as e:
            logger.warning("vector_search 远程调用失败 (%s)，fallback 到本地", e)
            engine = _ai_vector.VectorSearchEngine()
            results = engine.search(query=query, top_k=top_k, **kwargs)
            return {"results": results, "source": "local"}

    async def rag(self, query: str, user_id: int, **kwargs) -> dict:
        """RAG 问答。先远程，失败 fallback 到本地 RAGPipeline。"""
        try:
            return await self._remote_call("rag", query=query, user_id=user_id, **kwargs)
        except Exception as e:
            logger.warning("rag 远程调用失败 (%s)，fallback 到本地", e)
            pipeline = _ai_rag.RAGPipeline()
            result = await self._run_local_async(pipeline.answer, query=query, user_id=user_id, **kwargs)
            return {"result": result, "source": "local"}

    async def recommend(self, user_id: int, **kwargs) -> dict:
        """个性化推荐。先远程，失败 fallback 到本地 RecommendEngine。"""
        try:
            return await self._remote_call("recommend", user_id=user_id, **kwargs)
        except Exception as e:
            logger.warning("recommend 远程调用失败 (%s)，fallback 到本地", e)
            engine = _ai_recommend.RecommendEngine()
            result = await self._run_local_async(engine.personalize_recommend, user_id=user_id, **kwargs)
            return {"result": result, "source": "local"}

    async def ocr(self, image_base64: str, **kwargs) -> dict:
        """OCR 识别。先远程，失败 fallback 到本地 OCRScanner。"""
        try:
            return await self._remote_call("ocr", image_base64=image_base64, **kwargs)
        except Exception as e:
            logger.warning("ocr 远程调用失败 (%s)，fallback 到本地", e)
            scanner = _ai_ocr.OCRScanner()
            text = self._run_local(scanner.extract_text_from_image, image_base64, **kwargs)
            contacts = self._run_local(scanner.extract_contact_info, text)
            business = self._run_local(scanner.extract_business_info, text)
            return {"text": text, "contacts": contacts, "business_info": business, "source": "local"}

    async def writing(self, style: str, prompt: str, **kwargs) -> dict:
        """文案写作。先远程，失败 fallback 到本地 WritingAssistant。"""
        try:
            return await self._remote_call("writing", style=style, prompt=prompt, **kwargs)
        except Exception as e:
            logger.warning("writing 远程调用失败 (%s)，fallback 到本地", e)
            assistant = _ai_writing.WritingAssistant()
            result = self._run_local(assistant.generate, style=style, prompt=prompt, **kwargs)
            return {"result": result, "source": "local"}

    async def ab_test_analyze(self, experiment_id: int, **kwargs) -> dict:
        """A/B 测试分析。先远程，失败 fallback 到本地 ABTestingEngine。"""
        try:
            return await self._remote_call("ab_test_analyze", experiment_id=experiment_id, **kwargs)
        except Exception as e:
            logger.warning("ab_test_analyze 远程调用失败 (%s)，fallback 到本地", e)
            engine = _ai_ab.ABTestingEngine()
            result = self._run_local(engine.analyze, experiment_id=experiment_id, **kwargs)
            return {"result": result, "source": "local"}

    async def extract(self, text: str, **kwargs) -> dict:
        """信息提取。先远程，失败 fallback 到本地 AIExtractor。"""
        try:
            return await self._remote_call("extract", text=text, **kwargs)
        except Exception as e:
            logger.warning("extract 远程调用失败 (%s)，fallback 到本地", e)
            extractor = _ai_extractor.AIExtractor()
            fields = self._run_local(extractor.extract_fields_from_text, text=text, **kwargs)
            return {"fields": fields, "source": "local"}
