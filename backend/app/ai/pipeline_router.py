"""
三管道路由器 — RAG / SAG / Hybrid 自动路由
==================================================
根据查询类型自动选择最优管道，对外暴露统一接口。

路由逻辑:
  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
  │ 事实查询      │ ──→ │ RAG 管道     │     │ 零外部依赖       │
  │ "用户是谁"   │     │ 向量+图谱+画像│     │                  │
  └──────────────┘     └──────────────┘     └──────────────────┘

  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
  │ 逻辑推理      │ ──→ │ SAG 管道     │     │ 纯模型自我推演   │
  │ "为什么推荐" │     │ 6种推理模式   │     │ 无外部检索       │
  └──────────────┘     └──────────────┘     └──────────────────┘

  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
  │ 混合查询      │ ──→ │ Hybrid 管道  │     │ RAG 事实 + SAG   │
  │ "谁最适合"   │     │ 校验+补全    │     │ 推理校验         │
  └──────────────┘     └──────────────┘     └──────────────────┘

  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
  │ 名片操作      │ ──→ │ Direct 管道  │     │ 直接操作 DB      │
  │ 创建/更新    │     │ CRUD         │     │ 不经过 AI        │
  └──────────────┘     └──────────────┘     └──────────────────┘

状态查询:
  GET /api/pipeline/status → 返回三管道健康状态
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag_pipeline import RAGPipeline, RAGResponse
from app.ai.sag_pipeline import (
    SAGPipeline,
    SAGMode,
    SAGDepth,
    SAGResponse,
)
from app.ai.hybrid_pipeline import HybridPipeline
from app.config import settings

logger = logging.getLogger(__name__)


# ======================================================================
# 管道类型
# ======================================================================


class PipelineType(str, Enum):
    RAG = "rag"
    """检索增强生成 — 外部知识检索 + LLM 生成"""
    SAG = "sag"
    """自我推演 — 纯推理，不依赖外部检索"""
    HYBRID = "hybrid"
    """RAG + SAG 融合 — 先检索后校验"""
    DIRECT = "direct"
    """直接操作 — 不走 AI 管道"""


# ======================================================================
# 查询分类器
# ======================================================================


class QueryClassifier:
    """查询分类器 — 根据输入自动判断该走哪个管道"""

    # SAG 关键词（推理类查询 — 含数据引用+推理意图）
    SAG_KEYWORDS = {
        "为什么", "怎么", "如何", "哪个更好", "谁更",
        "比较", "对比", "区别", "差异",
        "分析", "判断", "评估", "评价",
        "觉得", "认为", "建议", "推荐理由",
        "可靠吗", "靠谱吗", "可信吗",
        "优化", "改进", "提升", "完善",
        "逻辑", "矛盾", "一致", "合理",
        "理由", "原因", "因为", "所以",
        "推荐",
        "匹配",
    }

    # RAG 关键词（事实类查询 — 涉及具体数据/实体）
    RAG_KEYWORDS = {
        "是谁", "是什么", "哪家公司", "什么公司",
        "联系方式", "电话", "邮箱", "地址",
        "行业", "规模", "简介",
        "标签", "匹配记录", "访问记录",
        "最近", "最新", "历史",
        "这个人", "这家公司", "这个用户",
        "匹配", "合作伙伴", "合作",
        "用户", "名片", "画册",
        "这个",
    }

    @classmethod
    def classify(cls, query: str) -> PipelineType:
        """根据查询文本自动分类"""
        q = query.lower().strip()

        # 1. 混合查询：含推理需求 + 涉具体数据
        rag_count = sum(1 for kw in cls.RAG_KEYWORDS if kw in q)
        sag_count = sum(1 for kw in cls.SAG_KEYWORDS if kw in q)

        if rag_count >= 1 and sag_count >= 1:
            return PipelineType.HYBRID

        # 2. 纯推理查询
        if sag_count >= 1:
            return PipelineType.SAG

        # 3. 事实查询
        if rag_count >= 1:
            return PipelineType.RAG

        # 4. 默认：短查询走 RAG，长查询走 Hybrid；
        # 含数据指标词(谁/哪些/几个/什么)的短查询走 Hybrid
        data_indicators = ["谁", "哪些", "几个", "什么", "哪"]
        has_data_ref = any(ind in q for ind in data_indicators)
        if len(q) < 10 and not has_data_ref:
            return PipelineType.RAG
        return PipelineType.HYBRID

    @classmethod
    def detect_sag_mode(cls, query: str) -> SAGMode:
        """从查询中检测 SAG 推理模式"""
        q = query.lower()
        if any(kw in q for kw in ["推荐", "哪个", "谁更", "推荐理由"]):
            return SAGMode.EXPLAIN_RECOMMEND
        elif any(kw in q for kw in ["匹配", "合作", "互补", "供需"]):
            return SAGMode.MATCHING_REASONING
        elif any(kw in q for kw in ["信任", "可靠", "风险"]):
            return SAGMode.TRUST_INFERENCE
        elif any(kw in q for kw in ["优化", "改进", "建议"]):
            return SAGMode.OPTIMIZE_SUGGEST
        elif any(kw in q for kw in ["质量", "评审", "打分"]):
            return SAGMode.QUALITY_REVIEW
        elif any(kw in q for kw in ["矛盾", "一致", "冲突"]):
            return SAGMode.CONTRADICTION_DETECT
        else:
            return SAGMode.EXPLAIN_RECOMMEND


# ======================================================================
# 路由结果
# ======================================================================


@dataclass
class RouteResult:
    """路由结果 — 统一响应格式"""
    answer: str
    pipeline: PipelineType
    confidence: float = 0.0
    sources: list[dict] = field(default_factory=list)
    sag_analysis: str | None = None
    reasoning_chain: list[dict] | None = None
    score: float | None = None
    suggestions: list[str] = field(default_factory=list)
    tokens_used: dict = field(default_factory=dict)
    has_correction: bool = False

    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "pipeline": self.pipeline.value,
            "confidence": self.confidence,
            "sources": self.sources,
            "sag_analysis": self.sag_analysis,
            "reasoning_chain": self.reasoning_chain,
            "score": self.score,
            "suggestions": self.suggestions,
            "tokens_used": self.tokens_used,
            "has_correction": self.has_correction,
        }


# ======================================================================
# 三管道路由器主类
# ======================================================================


class PipelineRouter:
    """三管道路由器 — 统一入口，自动路由到最优管道

    用法:
        router = PipelineRouter(db)
        result = await router.query(
            user_id=1,
            query_text="为什么推荐这个人给我？",
        )
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rag: RAGPipeline | None = None
        self.sag: SAGPipeline | None = None
        self.hybrid: HybridPipeline | None = None

    def _ensure_rag(self) -> RAGPipeline:
        if self.rag is None:
            self.rag = RAGPipeline(self.db)
        return self.rag

    def _ensure_sag(self) -> SAGPipeline:
        if self.sag is None:
            self.sag = SAGPipeline()
        return self.sag

    def _ensure_hybrid(self) -> HybridPipeline:
        if self.hybrid is None:
            self.hybrid = HybridPipeline(self.db)
        return self.hybrid

    async def query(
        self,
        user_id: int,
        query_text: str,
        top_k: int = 10,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        force_pipeline: str | None = None,
        conversation_history: list[dict] | None = None,
    ) -> RouteResult:
        """统一查询入口 — 自动路由

        Args:
            user_id: 用户 ID
            query_text: 查询文本
            top_k: 向量搜索返回数量
            temperature: LLM 温度
            max_tokens: 最大 token 数
            force_pipeline: 强制指定管道 ("rag" / "sag" / "hybrid")
            conversation_history: 对话历史

        Returns:
            RouteResult 统一响应
        """
        # 1. 选择管道
        if force_pipeline:
            pipeline_type = PipelineType(force_pipeline)
        else:
            pipeline_type = QueryClassifier.classify(query_text)

        logger.info(f"PipelineRouter: classified '{query_text[:50]}' → {pipeline_type.value}")

        # 2. 路由执行
        if pipeline_type == PipelineType.SAG:
            return await self._route_sag(query_text, user_id, temperature, max_tokens)
        elif pipeline_type == PipelineType.HYBRID:
            return await self._route_hybrid(
                user_id, query_text, top_k, temperature, max_tokens, conversation_history
            )
        else:
            return await self._route_rag(
                user_id, query_text, top_k, temperature, max_tokens, conversation_history
            )

    async def _route_rag(
        self,
        user_id: int,
        query_text: str,
        top_k: int,
        temperature: float,
        max_tokens: int,
        conversation_history: list[dict] | None,
    ) -> RouteResult:
        """路由到 RAG 管道"""
        rag = self._ensure_rag()
        response: RAGResponse = await rag.query(
            user_id=user_id,
            query_text=query_text,
            top_k=top_k,
            temperature=temperature,
            max_tokens=max_tokens,
            include_sources=True,
            conversation_history=conversation_history,
        )

        return RouteResult(
            answer=response.answer,
            pipeline=PipelineType.RAG,
            confidence=response.confidence,
            sources=response.sources,
            tokens_used={"rag": response.tokens_used},
        )

    async def _route_sag(
        self,
        query_text: str,
        user_id: int,
        temperature: float,
        max_tokens: int,
    ) -> RouteResult:
        """路由到 SAG 管道"""
        sag = self._ensure_sag()
        mode = QueryClassifier.detect_sag_mode(query_text)

        response: SAGResponse = await sag.analyze(
            mode=mode,
            content={"query": query_text},
            user_id=user_id,
            depth=SAGDepth.STANDARD,
            temperature=min(temperature, 0.5),
            max_tokens=max_tokens,
        )

        return RouteResult(
            answer=response.conclusion,
            pipeline=PipelineType.SAG,
            confidence=response.confidence,
            sag_analysis=response.conclusion,
            reasoning_chain=[s.to_dict() for s in response.reasoning_chain],
            score=response.score,
            suggestions=response.suggestions,
            tokens_used={"sag": response.tokens_used},
        )

    async def _route_hybrid(
        self,
        user_id: int,
        query_text: str,
        top_k: int,
        temperature: float,
        max_tokens: int,
        conversation_history: list[dict] | None,
    ) -> RouteResult:
        """路由到 Hybrid 管道"""
        hybrid = self._ensure_hybrid()
        result = await hybrid.query(
            user_id=user_id,
            query_text=query_text,
            top_k=top_k,
            temperature=temperature,
            max_tokens=max_tokens,
            conversation_history=conversation_history,
        )

        return RouteResult(
            answer=result.get("answer", ""),
            pipeline=PipelineType.HYBRID,
            confidence=result.get("confidence", 0.5),
            sources=result.get("sources", []),
            sag_analysis=result.get("analysis"),
            score=result.get("score"),
            suggestions=result.get("suggestions", []),
            tokens_used=result.get("tokens_used", {}),
            has_correction=result.get("has_correction", False),
        )

    async def get_status(self) -> dict:
        """获取三管道健康状态"""
        status = {
            "rag": self.rag is not None,
            "sag": self.sag is not None,
            "hybrid": self.hybrid is not None,
            "deepseek_api_key_configured": bool(settings.DEEPSEEK_API_KEY),
            "deepseek_api_url": settings.DEEPSEEK_API_URL or "https://api.deepseek.com",
        }

        # 测试 RAG 连通性（如果已初始化）
        if self.rag:
            try:
                test = await self.rag.deepseek.chat(
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=5,
                )
                status["deepseek_reachable"] = not isinstance(test, dict) or "error" not in str(test.get("content", ""))
            except Exception:
                status["deepseek_reachable"] = False

        return status

    async def close(self):
        """关闭所有管道"""
        if self.rag:
            await self.rag.close()
        if self.sag:
            await self.sag.close()
        if self.hybrid:
            await self.hybrid.close()
