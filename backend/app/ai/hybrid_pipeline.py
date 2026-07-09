"""
Hybrid 推理管道 — RAG + SAG 融合
======================================
先 RAG 检索外部材料 → 再 SAG 自校验/逻辑补全 → 融合输出

解决场景:
  1. 需要私有资料（名片库/匹配记录）+ 复杂逻辑推理的业务查询
     "这些推荐中谁最有可能和我合作成功？"
  2. RAG 结果有内部矛盾时，SAG 自校验自动修正
     "为什么推荐了A也推荐了B，但A和B是竞争对手？"
  3. RAG 检索信息不足时，SAG 逻辑补全
     "对方资料不全，但凭已知信息能推断到什么程度？"

架构:
  HybridPipeline
    ├─ RAGPipeline    — 先做外部检索（向量/图谱/画像）
    ├─ SAGPipeline    — 再做自我推演（校验/补全/推理）
    └─ 融合策略       — 根据 SAG 校验结果修正 RAG 输出

使用方式:
    hybrid = HybridPipeline(db)
    result = await hybrid.query(
        user_id=1,
        query_text="这些推荐里谁最适合和我合作？",
    )
"""

import logging
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


# ======================================================================
# 融合策略
# ======================================================================


class FusionStrategy:
    """RAG 与 SAG 的融合策略"""

    # 当 SAG 自校验发现 RAG 结果置信度低于此值时触发修正
    CONFIDENCE_THRESHOLD: float = 0.4

    @staticmethod
    def should_correct(rag_response: RAGResponse, sag_response: SAGResponse) -> bool:
        """判断是否需要用 SAG 结果修正 RAG 输出"""
        # 1. RAG 自身置信度低（LLM 降级了）
        if rag_response.confidence < 0.6:
            return True
        # 2. SAG 检测到矛盾
        if sag_response.score is not None and sag_response.score < 40:
            return True
        # 3. SAG 置信度显著高于 RAG
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
# Hybrid 管道主类
# ======================================================================


class HybridPipeline:
    """RAG + SAG 融合管道

    执行流程:
        Phase 1: RAG 检索 — 向量搜索 + 画像构建 + 关系图谱
        Phase 2: SAG 自校验 — 检验 RAG 结果的逻辑一致性
        Phase 3: SAG 逻辑补全 — 针对 RAG 信息不足的部分推理补充
        Phase 4: 融合输出 — 合并 RAG 事实 + SAG 推理
    """

    def __init__(self, db):
        self.db = db
        self.rag = RAGPipeline(db)
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
        """执行 Hybrid 查询

        两步走:
            1. RAG 检索外部知识
            2. SAG 校验+补全 + 融合输出
        """
        # Phase 1: RAG 检索
        rag_response: RAGResponse = await self.rag.query(
            user_id=user_id,
            query_text=query_text,
            top_k=top_k,
            temperature=temperature,
            max_tokens=max_tokens,
            include_sources=True,
            conversation_history=conversation_history,
        )

        # 如果 RAG 完全不可用（LLM 降级），跳过 SAG
        if rag_response.confidence < 0.3:
            return {
                "answer": rag_response.answer,
                "sources": rag_response.sources,
                "pipeline": "rag_only",
                "confidence": rag_response.confidence,
                "has_correction": False,
            }

        # Phase 2: SAG 自校验
        sag_check: SAGResponse = await self.sag.analyze(
            mode=SAGMode.CONTRADICTION_DETECT,
            content={
                "query": query_text,
                "rag_answer": rag_response.answer[:1000],
                "rag_sources": rag_response.sources[:5],
                "rag_confidence": rag_response.confidence,
            },
            depth=SAGDepth.FAST,  # 校验用快速模式
            temperature=0.3,  # 校验用低温度
        )

        # Phase 3: 决定是否需要修正
        needs_correction = self.fusion.should_correct(rag_response, sag_check)

        # Phase 4: 如需修正，做深度推理
        sag_reasoning: SAGResponse | None = None
        if needs_correction or query_text.lower().startswith(("为什么", "怎么", "如何", "哪个")):
            # 含推理需求的查询走深度 SAG
            reasoning_mode = self._detect_reasoning_mode(query_text)
            sag_reasoning = await self.sag.analyze(
                mode=reasoning_mode,
                content={
                    "query": query_text,
                    "rag_answer": rag_response.answer[:1500],
                    "rag_sources": rag_response.sources[:5],
                },
                depth=reasoning_depth,
                temperature=temperature,
            )

            # 用 SAG 推理结论补充 RAG 答案
            rag_response.answer += f"\n\n【推理分析】\n{sag_reasoning.conclusion}"

        # Phase 5: 融合输出
        result = self.fusion.merge_results(
            rag=rag_response,
            sag=sag_reasoning or sag_check,
            use_correction=needs_correction,
        )

        # 统计 token
        result["tokens_used"] = {
            "rag": rag_response.tokens_used if hasattr(rag_response, 'tokens_used') else 0,
            "sag": sag_reasoning.tokens_used if sag_reasoning else (sag_check.tokens_used if hasattr(sag_check, 'tokens_used') else 0),
        }

        return result

    def _detect_reasoning_mode(self, query: str) -> SAGMode:
        """根据查询内容自动选择 SAG 推理模式"""
        q = query.lower()
        if any(kw in q for kw in ["推荐", "哪个", "谁更", "比较", "哪个更"]):
            return SAGMode.EXPLAIN_RECOMMEND
        elif any(kw in q for kw in ["匹配", "合作", "互补", "对接", "供需"]):
            return SAGMode.MATCHING_REASONING
        elif any(kw in q for kw in ["信任", "可靠", "靠谱", "风险"]):
            return SAGMode.TRUST_INFERENCE
        elif any(kw in q for kw in ["优化", "改进", "建议", "怎么改"]):
            return SAGMode.OPTIMIZE_SUGGEST
        elif any(kw in q for kw in ["质量", "评审", "打分", "评价"]):
            return SAGMode.QUALITY_REVIEW
        else:
            # 默认用推荐解释
            return SAGMode.EXPLAIN_RECOMMEND

    async def query_stream(
        self,
        user_id: int,
        query_text: str,
        top_k: int = 10,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        conversation_history: list[dict] | None = None,
    ):
        """流式 Hybrid 查询"""
        # 先流式返回 RAG 结果
        async for chunk in self.rag.query_stream(
            user_id=user_id,
            query_text=query_text,
            top_k=top_k,
            temperature=temperature,
            max_tokens=max_tokens,
            conversation_history=conversation_history,
        ):
            yield chunk

        # 再补充 SAG 逻辑分析（非流式）
        sag_result = await self.sag.analyze(
            mode=SAGMode.EXPLAIN_RECOMMEND,
            content={"query": query_text},
            depth=SAGDepth.FAST,
            temperature=temperature,
        )
        if sag_result.conclusion:
            yield f"\n\n【推理分析】\n{sag_result.conclusion}"

    async def close(self):
        await self.rag.close()
        await self.sag.close()
