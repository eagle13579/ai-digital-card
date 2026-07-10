"""
hybrid_pipeline.py - 已废弃, 功能已合并到 rag_pipeline.py
============================================================

此文件保留仅用于向后兼容。新代码请直接使用 RAGPipeline 的 fusion_mode 参数:

    # 替代 HybridPipeline (完整 RAG→SAG 融合)
    pipeline = RAGPipeline(db, fusion_mode="hybrid")
    result = await pipeline.query(user_id=1, query_text="...")

    # 仅 SAG 校验 (不修正回答)
    pipeline = RAGPipeline(db, fusion_mode="rag_with_sag")
    result = await pipeline.query(user_id=1, query_text="...")

    # 纯 RAG (默认行为)
    pipeline = RAGPipeline(db, fusion_mode="rag_only")
    result = await pipeline.query(user_id=1, query_text="...")

所有原有导入 (from app.ai.hybrid_pipeline import HybridPipeline) 仍然可用，
但会收到废弃警告。
"""

import logging
import warnings
from dataclasses import dataclass, field
from typing import Any, Optional

from app.ai.rag_pipeline import RAGPipeline, RAGResponse
from app.ai.sag_pipeline import (
    SAGPipeline,
    SAGMode,
    SAGDepth,
    SAGResponse,
)
from app.config import settings

logger = logging.getLogger(__name__)

# 发出废弃警告
warnings.warn(
    "hybrid_pipeline.py 已废弃, 请使用 RAGPipeline(fusion_mode='hybrid') 替代。",
    DeprecationWarning,
    stacklevel=2,
)


# ======================================================================
# 融合策略 (保留向后兼容)
# ======================================================================


class FusionStrategy:
    """RAG 与 SAG 的融合策略

    .. deprecated::
        请使用 RAGPipeline(fusion_mode='hybrid') 替代。
    """

    CONFIDENCE_THRESHOLD: float = 0.4

    @staticmethod
    def should_correct(rag_response: RAGResponse, sag_response: SAGResponse) -> bool:
        """判断是否需要用 SAG 结果修正 RAG 输出"""
        if rag_response.confidence < 0.6:
            return True
        if sag_response.score is not None and sag_response.score < 40:
            return True
        if sag_response.confidence > rag_response.confidence + 0.2:
            return True
        return False

    @staticmethod
    def merge_results(
        rag: RAGResponse,
        sag: SAGResponse,
        use_correction: bool,
    ) -> dict:
        """融合 RAG 和 SAG 结果为一个统一响应"""
        merged = {
            "answer": rag.answer,
            "sources": rag.sources,
            "analysis": sag.conclusion if sag.reasoning_chain else None,
            "reasoning_chain": [s.to_dict() for s in sag.reasoning_chain] if sag.reasoning_chain else None,
            "confidence": max(rag.confidence, sag.confidence) if use_correction else rag.confidence,
            "suggestions": sag.suggestions,
            "has_correction": use_correction,
            "pipeline": "hybrid",
            "rag_confidence": rag.confidence,
            "sag_confidence": sag.confidence,
        }

        if use_correction and sag.score is not None and sag.score < 50:
            merged["answer"] += f"\n\n[逻辑校验提示] 推理引擎发现部分信息可能需要进一步确认，建议多方核实。"

        return merged


# ======================================================================
# Hybrid 管道主类 (保留向后兼容 — 委托给 RAGPipeline)
# ======================================================================


class HybridPipeline:
    """RAG + SAG 融合管道

    .. deprecated::
        请使用 RAGPipeline(fusion_mode='hybrid') 替代。

        示例::

            pipeline = RAGPipeline(db, fusion_mode="hybrid")
            result = await pipeline.query(user_id=1, query_text="...")
    """

    def __init__(self, db):
        self.db = db
        self.rag = RAGPipeline(db, fusion_mode="hybrid")
        self.sag = SAGPipeline()
        self.fusion = FusionStrategy()

    async def query(
        self,
        user_id: int,
        query_text: str,
        top_k: int = 10,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        conversation_history: list[dict] | None = None,
        reasoning_depth: SAGDepth = SAGDepth.STANDARD,
    ) -> dict:
        """执行 Hybrid 查询 (委托给 RAGPipeline)"""
        rag_response: RAGResponse = await self.rag.query(
            user_id=user_id,
            query_text=query_text,
            top_k=top_k,
            temperature=temperature,
            max_tokens=max_tokens,
            include_sources=True,
            conversation_history=conversation_history,
        )
        # 将 RAGResponse 转为 dict (向后兼容原有 HybridPipeline 接口)
        return rag_response.to_dict()

    async def query_stream(
        self,
        user_id: int,
        query_text: str,
        top_k: int = 10,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        conversation_history: list[dict] | None = None,
    ):
        """流式 Hybrid 查询 (委托给 RAGPipeline)"""
        async for chunk in self.rag.query_stream(
            user_id=user_id,
            query_text=query_text,
            top_k=top_k,
            temperature=temperature,
            max_tokens=max_tokens,
            conversation_history=conversation_history,
        ):
            yield chunk

    async def close(self):
        await self.rag.close()
        await self.sag.close()
