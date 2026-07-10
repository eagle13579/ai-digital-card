"""
AI数字名片 检索增强生成(RAG)管道
=================================
从向量搜索升级为完整的RAG管道，包含：
  1. 上下文构建（向量搜索结果 + 用户画像 + 关系图谱）
  2. AI Gateway 模型路由（DeepSeek -> Cache -> Ollama 降级链）
  3. 源引用追踪（每个回复片段关联原始数据源）
  4. 支持多轮对话上下文

依赖:
  - vector_search.py 提供向量搜索
  - knowledge_graph.py 提供关系图谱上下文
  - config.py 中 DEEPSEEK_API_KEY / DEEPSEEK_API_URL
  - app.ai.gateway.model_registry.ModelRegistry 提供多模型降级路由
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Optional

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.vector_search import VectorSearchEngine
from app.cache import cache
from app.config import settings
from app.models.brochure import Brochure, Page
from app.models.tag import MatchRecord, UserTag
from app.models.user import User

logger = logging.getLogger(__name__)


# ======================================================================
# 数据模型
# ======================================================================


@dataclass
class RAGContext:
    """RAG 上下文 - 包含检索结果和用户画像"""
    query: str
    user_id: int
    vector_results: list[dict] = field(default_factory=list)
    user_profile: dict = field(default_factory=dict)
    related_brochures: list[dict] = field(default_factory=list)
    match_suggestions: list[dict] = field(default_factory=list)
    knowledge_graph_context: dict = field(default_factory=dict)
    source_refs: list[dict] = field(default_factory=list)
    conversation_history: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "user_id": self.user_id,
            "vector_results": self.vector_results[:5],
            "user_profile": self.user_profile,
            "related_brochures": self.related_brochures[:3],
            "match_suggestions": self.match_suggestions[:3],
            "knowledge_graph_context": self.knowledge_graph_context,
            "source_refs": self.source_refs,
            "conversation_history": self.conversation_history[-5:],
        }


@dataclass
class RAGResponse:
    """RAG 响应 - 包含生成的回答和源引用"""
    answer: str
    sources: list[dict] = field(default_factory=list)
    confidence: float = 0.0
    model_used: str = "deepseek-chat"
    tokens_used: int = 0
    provider: str = "deepseek"
    degraded: bool = False
    # ── Hybrid/SAG enrichment fields (fusion_mode != "rag_only" 时填充) ──
    analysis: Optional[str] = None
    reasoning_chain: Optional[list] = None
    suggestions: Optional[list] = None
    has_correction: bool = False
    pipeline: str = "rag_only"
    rag_confidence: Optional[float] = None
    sag_confidence: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "sources": self.sources,
            "confidence": self.confidence,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "provider": self.provider,
            "degraded": self.degraded,
            "analysis": self.analysis,
            "reasoning_chain": self.reasoning_chain,
            "suggestions": self.suggestions,
            "has_correction": self.has_correction,
            "pipeline": self.pipeline,
            "rag_confidence": self.rag_confidence,
            "sag_confidence": self.sag_confidence,
        }


# ======================================================================
# DeepSeek API 调用
# ======================================================================


class DeepSeekClient:
    """DeepSeek API 客户端 - 支持非流式和流式调用

    注意：新代码应优先使用 ModelRegistry，DeepSeekClient 仅作为
    向后兼容的兜底方案保留。
    """

    BASE_URL: str = settings.DEEPSEEK_API_URL or "https://api.deepseek.com/v1/chat/completions"
    API_KEY: str = settings.DEEPSEEK_API_KEY or ""

    def __init__(self, api_key: str = "", base_url: str = ""):
        self.api_key = api_key or self.API_KEY
        self.base_url = base_url or self.BASE_URL
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
            )
        return self._session

    async def chat(
        self,
        messages: list[dict],
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> dict | AsyncGenerator[str, None]:
        """调用 DeepSeek Chat API

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            model: 模型名
            temperature: 温度
            max_tokens: 最大输出 token 数
            stream: 是否流式返回

        Returns:
            非流式: 完整响应 dict
            流式: AsyncGenerator[str, None] 逐块产出文本
        """
        from app.middleware.metrics import track_ai_inference
        from app.ai.metrics_collector import record_ai_call

        import time as _time
        _start = _time.monotonic()

        with track_ai_inference(model_name=model):
            session = await self._get_session()
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
            }

            try:
                async with session.post(self.base_url, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"DeepSeek API error (status={resp.status}): {error_text}")
                        _latency = (_time.monotonic() - _start) * 1000
                        record_ai_call(model_name=model, tokens=0, latency_ms=_latency, is_error=True)
                        return {"error": f"API调用失败: {resp.status}", "detail": error_text}

                    if stream:
                        return self._stream_response(resp)

                    data = await resp.json()
                    result = self._parse_response(data)
                    # 记录 token 用量和延迟
                    _latency = (_time.monotonic() - _start) * 1000
                    tokens_used = result.get("tokens_used", 0) if isinstance(result, dict) else 0
                    record_ai_call(
                        model_name=model,
                        tokens=tokens_used,
                        latency_ms=_latency,
                        is_error=bool(result.get("error")) if isinstance(result, dict) else False,
                    )
                    return result
            except aiohttp.ClientError as e:
                logger.error(f"DeepSeek API network error: {e}")
                _latency = (_time.monotonic() - _start) * 1000
                record_ai_call(model_name=model, tokens=0, latency_ms=_latency, is_error=True)
                return {"error": f"网络错误: {str(e)}"}
            except Exception as e:
                logger.error(f"DeepSeek API unexpected error: {e}")
                _latency = (_time.monotonic() - _start) * 1000
                record_ai_call(model_name=model, tokens=0, latency_ms=_latency, is_error=True)
                return {"error": f"未知错误: {str(e)}"}

    async def _stream_response(self, resp: aiohttp.ClientResponse) -> AsyncGenerator[str, None]:
        """解析流式响应"""
        async for line in resp.content:
            if line.startswith(b"data: "):
                chunk = line[6:].strip()
                if chunk == b"[DONE]":
                    break
                try:
                    data = json.loads(chunk)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue

    def _parse_response(self, data: dict) -> dict:
        """解析非流式响应为统一格式"""
        try:
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            usage = data.get("usage", {})
            return {
                "content": message.get("content", ""),
                "role": message.get("role", "assistant"),
                "finish_reason": choice.get("finish_reason", ""),
                "tokens_used": usage.get("total_tokens", 0),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            }
        except (IndexError, KeyError, TypeError) as e:
            logger.error(f"Parse DeepSeek response error: {e}, raw: {data}")
            return {"content": "", "error": f"解析响应失败: {str(e)}"}

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


# ======================================================================
# 上下文构建器
# ======================================================================


class ContextBuilder:
    """构建 RAG 上下文的工具类"""

    @staticmethod
    async def build_user_profile(db: AsyncSession, user_id: int) -> dict:
        """构建用户画像"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            return {}

        # 获取标签
        result = await db.execute(
            select(UserTag).where(UserTag.user_id == user_id)
        )
        tags = result.scalars().all()
        provide_tags = [t.tag for t in tags if t.tag_type == "provide"]
        need_tags = [t.tag for t in tags if t.tag_type == "need"]

        return {
            "user_id": user.id,
            "name": user.name,
            "company": user.company,
            "title": user.title,
            "intro": user.intro,
            "provide_tags": provide_tags,
            "need_tags": need_tags,
            "membership_tier": user.membership_tier,
        }

    @staticmethod
    async def build_brochure_context(db: AsyncSession, user_id: int) -> list[dict]:
        """构建用户画册内容摘要"""
        result = await db.execute(
            select(Brochure).where(
                Brochure.user_id == user_id,
                Brochure.status == "published",
            )
        )
        brochures = result.scalars().all()
        contexts = []
        for b in brochures:
            pages_result = await db.execute(
                select(Page).where(Page.brochure_id == b.id).order_by(Page.sort_order)
            )
            pages = pages_result.scalars().all()
            page_summaries = []
            for p in pages:
                summary = p.ai_summary or p.content[:200] if p.content else ""
                if summary:
                    page_summaries.append(summary)
            contexts.append({
                "brochure_id": b.id,
                "title": b.title,
                "purpose": b.purpose,
                "page_count": b.pages_count,
                "content_summary": page_summaries[:5],
            })
        return contexts

    @staticmethod
    async def build_vector_context(
        db: AsyncSession,
        query: str,
        user_id: int,
        top_k: int = 10,
    ) -> list[dict]:
        """构建向量搜索结果上下文"""
        vse = VectorSearchEngine(db)
        try:
            results = await vse.search(query=query, top_k=top_k, min_score=0.3)
            return results
        except Exception as e:
            logger.warning(f"Vector search failed (fallback: empty): {e}")
            return []

    @staticmethod
    async def build_match_context(
        db: AsyncSession,
        user_id: int,
        top_k: int = 5,
    ) -> list[dict]:
        """构建匹配建议上下文"""
        result = await db.execute(
            select(MatchRecord).where(
                (MatchRecord.user_a_id == user_id) | (MatchRecord.user_b_id == user_id),
                MatchRecord.match_score >= 0.5,
            ).order_by(MatchRecord.match_score.desc()).limit(top_k)
        )
        records = result.scalars().all()
        suggestions = []
        for r in records:
            target_id = r.user_b_id if r.user_a_id == user_id else r.user_a_id
            user_result = await db.execute(select(User).where(User.id == target_id))
            target_user = user_result.scalars().first()
            if target_user:
                suggestions.append({
                    "user_id": target_user.id,
                    "name": target_user.name,
                    "company": target_user.company,
                    "title": target_user.title,
                    "match_score": r.match_score,
                    "status": r.status,
                })
        return suggestions

    @staticmethod
    def build_system_prompt(context: RAGContext) -> str:
        """构建系统提示词"""
        prompt_parts = [
            '你是「AI数字名片」智能助手，帮助用户管理数字名片、建立人脉连接、分析商业匹配。',
            '',
            '【场景化引导路由】',
            '根据用户输入的关键词，按以下场景分类回答：',
            '- 用户问「怎么用」「如何使用」「教程」「指南」 → 优先返回名片功能全览和操作教程，分步骤引导',
            '- 用户问「名片」「创建」「编辑」「修改」「模板」 → 优先返回名片创建和编辑步骤，介绍名片模板功能',
            '- 用户问「人脉」「匹配」「推荐」「找人」「找」「搜索」 → 优先返回人脉匹配和推荐机制说明，展示匹配结果',
            '- 用户问「信任」「验证」「安全」「靠谱」 → 优先返回信任网络、实名验证和隐私保护机制说明',
            '- 用户问「扫码」「添加」「建联」「连接」「联系」 → 优先返回扫码建联流程和人脉触达路径',
            '- 用户问「订阅」「付费」「Token」「套餐」「价格」「会员」 → 优先返回定价方案和订阅说明',
            '- 用户问「关系」「关系网」「社交」「好友」 → 优先返回关系图谱和社交网络说明',
            '- 用户问「平台」「功能」「能做什么」「介绍」 → 优先返回平台功能全景介绍',
            '- 默认 → 返回通用帮助和功能导航，附上核心功能快捷入口',
            '每个场景回复使用Markdown格式，包含具体操作步骤和功能入口。如果检索到的信息与场景相关，优先使用检索信息增强回复。',
            "",
            "请使用以下检索到的信息来回答问题。如果信息不足，请如实说明。",
            "回答时请附上信息来源引用，格式为 [来源: 类型/名称]。",
            "",
            "=== 用户画像 ===",
        ]

        profile = context.user_profile
        if profile:
            prompt_parts.append(f"用户: {profile.get('name', '未知')}")
            prompt_parts.append(f"公司: {profile.get('company', '未设置')}")
            prompt_parts.append(f"职位: {profile.get('title', '未设置')}")
            prompt_parts.append(f"简介: {profile.get('intro', '无')}")
            provide = profile.get("provide_tags", [])
            need = profile.get("need_tags", [])
            if provide:
                prompt_parts.append(f"能提供: {'、'.join(provide)}")
            if need:
                prompt_parts.append(f"需要: {'、'.join(need)}")

        prompt_parts.append("")
        prompt_parts.append("=== 向量搜索结果 ===")
        for i, vr in enumerate(context.vector_results[:5], 1):
            name = vr.get("user_name", vr.get("name", f"用户{vr.get('user_id', '?')}"))
            company = vr.get("company", "")
            intro = vr.get("intro", "")
            score = vr.get("score", 0)
            prompt_parts.append(f"{i}. {name} ({company}) - 相似度: {score:.2f}")
            if intro:
                prompt_parts.append(f"   简介: {intro[:300]}")

        prompt_parts.append("")
        prompt_parts.append("=== 匹配建议 ===")
        for j, ms in enumerate(context.match_suggestions, 1):
            prompt_parts.append(f"{j}. {ms.get('name', '?')} - {ms.get('company', '?')} - 匹配度: {ms.get('match_score', 0):.2f}")

        if context.knowledge_graph_context:
            prompt_parts.append("")
            prompt_parts.append("=== 关系图谱 ===")
            kg = context.knowledge_graph_context
            if kg.get("trusted_connections"):
                prompt_parts.append(f"信任连接: {len(kg['trusted_connections'])} 个")
            if kg.get("common_tags_with_others"):
                prompt_parts.append(f"共同标签关联: {len(kg['common_tags_with_others'])} 个")
            if kg.get("industry_peers"):
                prompt_parts.append(f"行业同行: {len(kg['industry_peers'])} 个")

        prompt_parts.append("")
        prompt_parts.append("回答要求:")
        prompt_parts.append("1. 基于上述检索信息回答问题")
        prompt_parts.append("2. 对每个事实标注来源引用")
        prompt_parts.append("3. 如果信息不足，明确告知用户")
        prompt_parts.append("4. 使用中文回答")
        prompt_parts.append("5. 可以给出进一步的行动建议")

        return "\n".join(prompt_parts)


# ======================================================================
# HyDE 检索增强
# ======================================================================


class HyDEQueryTransformer:
    """HyDE (Hypothetical Document Embeddings) 检索增强转换器

    1. 用 LLM 生成一段假设文档（理想回答），将简短查询扩展为
       语义丰富的描述文本
    2. 对原始查询和假设文档分别做向量搜索，加权融合去重
    """

    HYDE_SYSTEM_PROMPT: str = (
        "你是一个商务匹配专家。给定用户的查询，生成一段理想的回答文本，"
        "包含你想找到什么样的合作伙伴、什么背景、什么技能。"
        "这段文本将用于向量搜索，请写得详细具体。"
    )

    # 原始查询权重 vs HyDE 假设文档权重
    QUERY_WEIGHT: float = 0.4
    HYDE_WEIGHT: float = 0.6

    def __init__(self, deepseek_client: DeepSeekClient):
        self.deepseek = deepseek_client

    async def hyde_generate(self, query: str) -> str:
        """用 DeepSeek 生成假设文档（理想回答文本）"""
        messages = [
            {"role": "system", "content": self.HYDE_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]
        response = await self.deepseek.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=512,
            stream=False,
        )
        content = response.get("content", "") if isinstance(response, dict) else str(response)
        if not content or response.get("error"):
            logger.warning(f"HyDE generation returned empty or error, fallback to original query: {response.get('error', '')}")
            return query
        logger.debug(f"HyDE generated hypothetical doc ({len(content)} chars): {content[:100]}...")
        return content

    async def hyde_search(
        self,
        db: AsyncSession,
        query: str,
        hyde_doc: str,
        user_id: int,
        top_k: int = 10,
    ) -> list[dict]:
        """分别用原 query 和 hypothetical doc 做向量搜索，加权融合去重

        融合策略:
          - 原 query 结果: 分数 × QUERY_WEIGHT (0.4)
          - HyDE 结果: 分数 × HYDE_WEIGHT (0.6)
          - 按 user_id 去重，取最高加权分
          - 按加权分降序排列
        """
        vse = VectorSearchEngine(db)

        try:
            query_results = await vse.search(query=query, top_k=top_k, min_score=0.3)
            hyde_results = await vse.search(query=hyde_doc, top_k=top_k, min_score=0.3)
        except Exception as e:
            logger.warning(f"HyDE vector search failed (fallback: original query): {e}")
            try:
                return await vse.search(query=query, top_k=top_k, min_score=0.3)
            except Exception:
                return []

        # 加权融合
        merged: dict[int, dict] = {}

        for r in query_results:
            uid = r.get("user_id")
            if uid is None:
                continue
            r["_weighted_score"] = r.get("score", 0) * self.QUERY_WEIGHT
            r["_source"] = "query"
            merged[uid] = r

        for r in hyde_results:
            uid = r.get("user_id")
            if uid is None:
                continue
            hyde_score = r.get("score", 0) * self.HYDE_WEIGHT
            if uid in merged:
                merged[uid]["score"] = max(merged[uid]["score"], r.get("score", 0))
                merged[uid]["_weighted_score"] = max(merged[uid]["_weighted_score"], hyde_score)
            else:
                r["_weighted_score"] = hyde_score
                r["_source"] = "hyde"
                merged[uid] = r

        # 按加权分降序排列，去掉辅助字段
        sorted_results = sorted(merged.values(), key=lambda x: x["_weighted_score"], reverse=True)
        for r in sorted_results:
            r.pop("_weighted_score", None)
            r.pop("_source", None)

        return sorted_results[:top_k]


# ======================================================================
# RAG 管道主类
# ======================================================================


class RAGPipeline:
    """检索增强生成管道 - 整合搜索 + 上下文 + LLM 生成

    使用 ModelRegistry 进行多模型路由（DeepSeek -> Cache -> Ollama 降级链），
    DeepSeekClient 保留为向后兼容兜底。
    """

    def __init__(self, db: AsyncSession, fusion_mode: str = "rag_only"):
        self.db = db
        self.deepseek = DeepSeekClient()
        self.context_builder = ContextBuilder()
        self.hyde_transformer = HyDEQueryTransformer(self.deepseek)
        self.fusion_mode = fusion_mode  # "rag_only" | "rag_with_sag" | "hybrid"
        if fusion_mode in ("rag_with_sag", "hybrid"):
            from app.ai.sag_pipeline import SAGPipeline
            self.sag = SAGPipeline()
        # ModelRegistry: 多模型降级路由（DeepSeek -> Cache -> Ollama）
        # 使用延迟导入避免循环依赖
        from app.ai.gateway.model_registry import ModelRegistry
        self.model_registry = ModelRegistry(
            deepseek_api_key=settings.DEEPSEEK_API_KEY,
            deepseek_base_url=settings.DEEPSEEK_API_URL,
        )

    async def query(
        self,
        user_id: int,
        query_text: str,
        top_k: int = 10,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        include_sources: bool = True,
        conversation_history: list[dict] | None = None,
    ) -> RAGResponse:
        """执行 RAG 查询

        Args:
            user_id: 当前用户 ID
            query_text: 查询文本
            top_k: 向量搜索返回数量
            temperature: LLM 温度
            max_tokens: 最大 token 数
            include_sources: 是否包含源引用
            conversation_history: 多轮对话历史

        Returns:
            RAGResponse 包含答案和源引用
        """
        # 1. 构建上下文
        context = RAGContext(
            query=query_text,
            user_id=user_id,
            conversation_history=conversation_history or [],
        )

        # HyDE: 用 DeepSeek 生成假设文档替代原查询进行向量搜索
        hyde_query = query_text
        if settings.USE_HYDE:
            hyde_query = await self.hyde_transformer.hyde_generate(query_text)

        # 并行构建各层上下文
        import asyncio
        (
            context.user_profile,
            context.related_brochures,
            context.vector_results,
            context.match_suggestions,
        ) = await asyncio.gather(
            self.context_builder.build_user_profile(self.db, user_id),
            self.context_builder.build_brochure_context(self.db, user_id),
            self.context_builder.build_vector_context(self.db, hyde_query, user_id, top_k),
            self.context_builder.build_match_context(self.db, user_id),
        )

        # 2. 构建系统提示词
        system_prompt = self.context_builder.build_system_prompt(context)

        # 3. 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]

        # 添加对话历史
        for msg in context.conversation_history:
            messages.append(msg)

        # 添加用户当前问题
        messages.append({"role": "user", "content": query_text})

        # 4. 通过 ModelRegistry 调用 AI（DeepSeek -> Cache -> Ollama 降级链）
        provider = "deepseek"
        degraded = False

        from app.middleware.metrics import track_ai_inference
        from app.ai.metrics_collector import record_ai_call

        try:
            with track_ai_inference(model_name="deepseek-chat-rag"):
                # 尝试使用 ModelRegistry 路由
                from app.ai.gateway.interfaces import AIRequest

                ai_request = AIRequest(
                    model="deepseek-chat",
                    prompt=system_prompt,
                    messages=messages[1:],  # 排除 system prompt（已单独传入）
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                )
                gateway_response, provider = await self.model_registry.route(ai_request)
                answer = gateway_response.content
                tokens_used = gateway_response.usage.get("total_tokens", 0)
                degraded = (provider != "deepseek")
                model_used = gateway_response.model

        except Exception as gateway_error:
            # ModelRegistry 降级链全部失败，回退到 DeepSeekClient 兜底
            logger.warning(
                f"ModelRegistry fallback chain exhausted: {gateway_error}. "
                "Falling back to DeepSeekClient."
            )
            with track_ai_inference(model_name="deepseek-chat-rag-fallback"):
                legacy_response = await self.deepseek.chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                )
            answer = legacy_response.get("content", "") if isinstance(legacy_response, dict) else str(legacy_response)
            error = legacy_response.get("error", "") if isinstance(legacy_response, dict) else ""
            tokens_used = legacy_response.get("tokens_used", 0) if isinstance(legacy_response, dict) else 0
            model_used = "deepseek-chat"
            provider = "deepseek_legacy"

            if error:
                logger.warning(f"RAG pipeline LLM error (DeepSeekClient fallback): {error}")
                # 降级: 直接返回向量搜索结果
                answer = self._fallback_answer(context)
                degraded = True
                record_ai_call(model_name="deepseek-chat-rag", tokens=0, latency_ms=0, is_error=True)
            else:
                record_ai_call(model_name="deepseek-chat-rag", tokens=tokens_used, latency_ms=0, is_error=False)

        else:
            # ModelRegistry 成功 — 记录指标
            record_ai_call(
                model_name=f"deepseek-chat-rag",
                tokens=tokens_used,
                latency_ms=0,
                is_error=False,
            )

        # 5. 构建源引用
        sources = []
        if include_sources:
            for vr in context.vector_results[:5]:
                sources.append({
                    "type": "vector_search",
                    "user_id": vr.get("user_id"),
                    "user_name": vr.get("user_name", vr.get("name", "")),
                    "company": vr.get("company", ""),
                    "score": vr.get("score", 0),
                })
            for ms in context.match_suggestions[:3]:
                sources.append({
                    "type": "match_record",
                    "user_id": ms.get("user_id"),
                    "user_name": ms.get("name", ""),
                    "company": ms.get("company", ""),
                    "match_score": ms.get("match_score", 0),
                })

        # 6. 生成 RAG 响应
        response = RAGResponse(
            answer=answer,
            sources=sources,
            confidence=0.9 if not degraded else 0.5,
            model_used=model_used,
            tokens_used=tokens_used,
            provider=provider,
            degraded=degraded,
        )

        # 7. 可选: SAG 后处理校验（fusion_mode="rag_with_sag" 或 "hybrid"）
        if self.fusion_mode in ("rag_with_sag", "hybrid"):
            response = await self._apply_sag_post_process(
                response=response,
                query_text=query_text,
                temperature=temperature,
            )

        return response

    def _fallback_answer(self, context: RAGContext) -> str:
        """降级方案：当 LLM 不可用时，基于检索结果生成结构化回复"""
        parts = ["我暂时无法使用 AI 生成能力，以下是基于检索结果的信息：\n"]

        if context.vector_results:
            parts.append("**相关用户推荐：**")
            for i, vr in enumerate(context.vector_results[:5], 1):
                name = vr.get("user_name", vr.get("name", f"用户{vr.get('user_id', '?')}"))
                company = vr.get("company", "")
                score = vr.get("score", 0)
                parts.append(f"  {i}. {name} ({company}) - 匹配度 {score:.2f}")
            parts.append("")

        if context.match_suggestions:
            parts.append("**匹配建议：**")
            for j, ms in enumerate(context.match_suggestions, 1):
                parts.append(f"  {j}. {ms.get('name', '?')} - {ms.get('company', '?')} - 分数: {ms.get('match_score', 0):.2f}")

        return "\n".join(parts)

    async def _apply_sag_post_process(
        self,
        response: RAGResponse,
        query_text: str,
        temperature: float,
    ) -> RAGResponse:
        """SAG 后处理: 对 RAG 结果进行自校验/逻辑补全

        当 fusion_mode="rag_with_sag" 时: 仅做快速矛盾检测
        当 fusion_mode="hybrid" 时: 完整执行 RAG→SAG 融合流程
        """
        if not hasattr(self, 'sag'):
            return response

        # 记录原始 RAG 置信度
        response.rag_confidence = response.confidence

        # 如果 RAG 完全不可用（LLM 降级），跳过 SAG
        if response.confidence < 0.3:
            response.pipeline = "rag_only"
            return response

        from app.ai.sag_pipeline import SAGMode, SAGDepth, SAGResponse

        # Phase 1: 快速矛盾检测（所有 fusion_mode 均执行）
        sag_check: SAGResponse = await self.sag.analyze(
            mode=SAGMode.CONTRADICTION_DETECT,
            content={
                "query": query_text,
                "rag_answer": response.answer[:1000],
                "rag_sources": response.sources[:5],
                "rag_confidence": response.confidence,
            },
            depth=SAGDepth.FAST,
            temperature=0.3,
        )

        # Phase 2: 判断是否需要修正
        needs_correction = self._fusion_should_correct(response, sag_check)

        if self.fusion_mode == "rag_with_sag":
            # 仅记录校验结果, 不修改回答
            response.has_correction = needs_correction
            response.sag_confidence = sag_check.confidence if hasattr(sag_check, 'confidence') else 0.0
            response.pipeline = "rag_with_sag"
            response.analysis = sag_check.conclusion if sag_check.reasoning_chain else None
            return response

        # fusion_mode == "hybrid": 执行完整融合流程
        # Phase 3: 如需修正, 做深度推理
        sag_reasoning: SAGResponse | None = None
        reasoning_depth: SAGDepth = SAGDepth.STANDARD
        if needs_correction or query_text.lower().startswith(("为什么", "怎么", "如何", "哪个")):
            reasoning_mode = self._detect_reasoning_mode(query_text)
            sag_reasoning = await self.sag.analyze(
                mode=reasoning_mode,
                content={
                    "query": query_text,
                    "rag_answer": response.answer[:1500],
                    "rag_sources": response.sources[:5],
                },
                depth=reasoning_depth,
                temperature=temperature,
            )
            # 用 SAG 推理结论补充 RAG 答案
            if sag_reasoning.conclusion:
                response.answer += f"\n\n【推理分析】\n{sag_reasoning.conclusion}"

        # Phase 4: 融合输出
        use_correction = needs_correction
        merged = self._fusion_merge(response, sag_reasoning or sag_check, use_correction)

        # 将融合结果写回 response
        response.has_correction = merged.get("has_correction", needs_correction)
        response.analysis = merged.get("analysis")
        response.reasoning_chain = merged.get("reasoning_chain")
        response.suggestions = merged.get("suggestions")
        response.pipeline = merged.get("pipeline", "hybrid")
        response.sag_confidence = merged.get("sag_confidence", 0.0)
        if use_correction:
            response.confidence = merged.get("confidence", response.confidence)

        return response

    def _fusion_should_correct(self, rag: RAGResponse, sag) -> bool:
        """判断是否需要用 SAG 结果修正 RAG 输出"""
        # 1. RAG 自身置信度低
        if rag.confidence < 0.6:
            return True
        # 2. SAG 检测到矛盾
        sag_score = sag.score if hasattr(sag, 'score') and sag.score is not None else 100
        if sag_score < 40:
            return True
        # 3. SAG 置信度显著高于 RAG
        sag_conf = sag.confidence if hasattr(sag, 'confidence') and sag.confidence is not None else 0.0
        if sag_conf > rag.confidence + 0.2:
            return True
        return False

    def _fusion_merge(self, rag: RAGResponse, sag, use_correction: bool) -> dict:
        """融合 RAG 和 SAG 结果为一个统一 dict"""
        sag_conclusion = sag.conclusion if hasattr(sag, 'conclusion') else None
        sag_reasoning = [s.to_dict() for s in sag.reasoning_chain] if hasattr(sag, 'reasoning_chain') and sag.reasoning_chain else None
        sag_suggestions = sag.suggestions if hasattr(sag, 'suggestions') else None
        sag_conf = sag.confidence if hasattr(sag, 'confidence') and sag.confidence is not None else 0.0
        sag_score = sag.score if hasattr(sag, 'score') and sag.score is not None else 100

        merged: dict = {
            "analysis": sag_conclusion if sag_reasoning else None,
            "reasoning_chain": sag_reasoning,
            "confidence": max(rag.confidence, sag_conf) if use_correction else rag.confidence,
            "suggestions": sag_suggestions,
            "has_correction": use_correction,
            "pipeline": "hybrid",
            "rag_confidence": rag.confidence,
            "sag_confidence": sag_conf,
        }

        if use_correction and sag_score < 50:
            rag.answer += f"\n\n[逻辑校验提示] 推理引擎发现部分信息可能需要进一步确认，建议多方核实。"

        return merged

    def _detect_reasoning_mode(self, query: str):
        """根据查询内容自动选择 SAG 推理模式"""
        from app.ai.sag_pipeline import SAGMode
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
            return SAGMode.EXPLAIN_RECOMMEND

    async def query_stream(
        self,
        user_id: int,
        query_text: str,
        top_k: int = 10,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        conversation_history: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """流式 RAG 查询"""
        # 构建上下文（同上）
        context = RAGContext(
            query=query_text,
            user_id=user_id,
            conversation_history=conversation_history or [],
        )

        # HyDE: 用 DeepSeek 生成假设文档替代原查询进行向量搜索
        hyde_query = query_text
        if settings.USE_HYDE:
            hyde_query = await self.hyde_transformer.hyde_generate(query_text)

        import asyncio
        (
            context.user_profile,
            context.related_brochures,
            context.vector_results,
            context.match_suggestions,
        ) = await asyncio.gather(
            self.context_builder.build_user_profile(self.db, user_id),
            self.context_builder.build_brochure_context(self.db, user_id),
            self.context_builder.build_vector_context(self.db, hyde_query, user_id, top_k),
            self.context_builder.build_match_context(self.db, user_id),
        )

        system_prompt = self.context_builder.build_system_prompt(context)
        messages = [{"role": "system", "content": system_prompt}]

        for msg in (conversation_history or []):
            messages.append(msg)
        messages.append({"role": "user", "content": query_text})

        result = await self.deepseek.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        if isinstance(result, AsyncGenerator):
            async for chunk in result:
                yield chunk
        else:
            yield result.get("content", "") if isinstance(result, dict) else str(result)

    async def close(self):
        await self.deepseek.close()
        await self.model_registry.close()
