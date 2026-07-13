"""
RAG 管道测试 - 验证检索增强生成各组件
====================================
测试覆盖:
  1. DeepSeekClient API 调用（mock）
  2. ContextBuilder 上下文构建
  3. RAGPipeline 完整查询流程
  4. 降级回退机制
  5. 源引用追踪
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientError

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag_pipeline import (
    RAGPipeline,
    DeepSeekClient,
    ContextBuilder,
    RAGContext,
    RAGResponse,
)


# ======================================================================
# Mock 数据
# ======================================================================

MOCK_USER = MagicMock()
MOCK_USER.id = 1
MOCK_USER.name = "张三"
MOCK_USER.company = "阿里巴巴"
MOCK_USER.title = "高级工程师"
MOCK_USER.intro = "专注于AI产品开发"
MOCK_USER.membership_tier = "gold"

MOCK_USER_2 = MagicMock()
MOCK_USER_2.id = 2
MOCK_USER_2.name = "李四"
MOCK_USER_2.company = "腾讯"
MOCK_USER_2.title = "产品经理"
MOCK_USER_2.intro = "擅长产品策略规划"

MOCK_TAGS = [
    MagicMock(tag="Python", tag_type="provide", weight=1.0),
    MagicMock(tag="AI开发", tag_type="provide", weight=0.8),
    MagicMock(tag="项目外包", tag_type="need", weight=0.9),
    MagicMock(tag="投资", tag_type="need", weight=0.7),
]

MOCK_BROCHURE = MagicMock()
MOCK_BROCHURE.id = 1
MOCK_BROCHURE.title = "AI解决方案"
MOCK_BROCHURE.purpose = "partner"
MOCK_BROCHURE.pages_count = 3
MOCK_BROCHURE.status = "published"

MOCK_PAGE = MagicMock()
MOCK_PAGE.id = 1
MOCK_PAGE.sort_order = 0
MOCK_PAGE.content = "我们提供AI驱动的数字名片解决方案"
MOCK_PAGE.ai_summary = "AI数字名片解决方案介绍"

MOCK_MATCH_RECORD = MagicMock()
MOCK_MATCH_RECORD.id = 1
MOCK_MATCH_RECORD.user_a_id = 1
MOCK_MATCH_RECORD.user_b_id = 2
MOCK_MATCH_RECORD.match_score = 0.85
MOCK_MATCH_RECORD.status = "matched"

MOCK_VECTOR_RESULTS = [
    {
        "user_id": 2,
        "user_name": "李四",
        "company": "腾讯",
        "intro": "擅长产品策略规划",
        "score": 0.82,
    },
    {
        "user_id": 3,
        "user_name": "王五",
        "company": "字节跳动",
        "intro": "AI产品专家",
        "score": 0.75,
    },
]


# ======================================================================
# DeepSeekClient 测试
# ======================================================================


class TestDeepSeekClient:
    """DeepSeek API 客户端测试"""

    @pytest.mark.asyncio
    async def test_chat_success(self):
        """测试非流式 chat 成功调用"""
        client = DeepSeekClient(api_key="test-key")

        mock_response_data = {
            "choices": [{
                "message": {"content": "你好！我是AI助手。", "role": "assistant"},
                "finish_reason": "stop",
            }],
            "usage": {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
        }

        with patch.object(client, "_get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.post = MagicMock()
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response_data)
            mock_session.post.return_value = AsyncMock()
            mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_session

            result = await client.chat(
                messages=[{"role": "user", "content": "你好"}],
                model="deepseek-chat",
            )

            assert result["content"] == "你好！我是AI助手。"
            assert result["tokens_used"] == 100
            assert result["role"] == "assistant"
            assert result["finish_reason"] == "stop"

        await client.close()

    @pytest.mark.asyncio
    async def test_chat_api_error(self):
        """测试 API 返回错误"""
        client = DeepSeekClient(api_key="test-key")

        with patch.object(client, "_get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.post = MagicMock()
            mock_resp = AsyncMock()
            mock_resp.status = 401
            mock_resp.text = AsyncMock(return_value="Unauthorized")
            mock_session.post.return_value = AsyncMock()
            mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_session

            result = await client.chat(
                messages=[{"role": "user", "content": "你好"}],
            )

            assert "error" in result
            assert "API调用失败" in result["error"]

        await client.close()

    @pytest.mark.asyncio
    async def test_chat_network_error(self):
        """测试网络错误"""
        client = DeepSeekClient(api_key="test-key")

        with patch.object(client, "_get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.post = MagicMock()
            mock_session.post.side_effect = None
            mock_session.post.return_value = AsyncMock()
            mock_session.post.return_value.__aenter__ = AsyncMock(side_effect=ClientError("Connection failed"))
            mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_session

            result = await client.chat(
                messages=[{"role": "user", "content": "你好"}],
            )

            assert "error" in result
            assert "网络错误" in result["error"]

        await client.close()

    @pytest.mark.asyncio
    async def test_parse_response_with_missing_fields(self):
        """测试解析响应时缺少字段"""
        client = DeepSeekClient(api_key="test-key")
        result = client._parse_response({})
        assert result["content"] == ""
        # Missing fields don't trigger error — code returns defaults gracefully
        assert "error" not in result

    def test_init_defaults(self):
        """测试默认初始化"""
        client = DeepSeekClient()
        assert client.api_key is not None
        assert client.base_url is not None


# ======================================================================
# ContextBuilder 测试
# ======================================================================


class TestContextBuilder:
    """上下文构建器测试"""

    @pytest.mark.asyncio
    async def test_build_user_profile(self):
        """测试构建用户画像"""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock 用户查询
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = MOCK_USER
        mock_db.execute.return_value = mock_result

        # Mock 标签查询 - 需要两个调用
        def mock_execute_side_effect(query):
            mock = MagicMock()
            if hasattr(query, 'where') and 'user_id' in str(query.whereclause):
                mock.scalars.return_value.all.return_value = MOCK_TAGS
            else:
                mock.scalars.return_value.first.return_value = MOCK_USER
            return mock

        mock_db.execute = AsyncMock(side_effect=mock_execute_side_effect)

        builder = ContextBuilder()
        profile = await builder.build_user_profile(mock_db, 1)

        assert profile["user_id"] == 1
        assert profile["name"] == "张三"
        assert profile["company"] == "阿里巴巴"
        assert "Python" in profile["provide_tags"]
        assert "投资" in profile["need_tags"]

    def test_build_system_prompt_with_full_context(self):
        """测试构建完整系统提示词"""
        context = RAGContext(
            query="推荐AI方向的合作伙伴",
            user_id=1,
            user_profile={
                "user_id": 1,
                "name": "张三",
                "company": "阿里巴巴",
                "title": "高级工程师",
                "intro": "AI产品开发",
                "provide_tags": ["Python", "AI开发"],
                "need_tags": ["投资", "项目外包"],
            },
            vector_results=MOCK_VECTOR_RESULTS,
            match_suggestions=[
                {"user_id": 2, "name": "李四", "company": "腾讯", "match_score": 0.85},
            ],
            knowledge_graph_context={
                "trusted_connections": 5,
                "common_tags_with_others": 12,
                "industry_peers": 8,
            },
        )

        builder = ContextBuilder()
        prompt = builder.build_system_prompt(context)

        assert "张三" in prompt
        assert "阿里巴巴" in prompt
        assert "Python" in prompt
        assert "李四" in prompt
        assert "腾讯" in prompt
        assert "信任连接" in prompt
        assert "来源引用" in prompt

    def test_build_system_prompt_minimal(self):
        """测试构建最小系统提示词（无额外信息）"""
        context = RAGContext(query="你好", user_id=1)
        builder = ContextBuilder()
        prompt = builder.build_system_prompt(context)

        assert "检索" in prompt
        assert "来源引用" in prompt
        assert "中文回答" in prompt


# ======================================================================
# RAGPipeline 测试
# ======================================================================


class TestRAGPipeline:
    """RAG 管道主流程测试"""

    @pytest.mark.asyncio
    async def test_query_success(self):
        """测试完整的 RAG 查询流程"""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock 所有数据库查询
        def db_execute_side_effect(query):
            mock = MagicMock()
            # User profile query
            mock.scalars.return_value.first.return_value = MOCK_USER
            # Tags query
            mock.scalars.return_value.all.return_value = MOCK_TAGS
            return mock

        mock_db.execute = AsyncMock(side_effect=db_execute_side_effect)

        # Mock vector search
        with patch("app.ai.rag_pipeline.VectorSearchEngine") as mock_vse:
            mock_vse_instance = AsyncMock()
            mock_vse_instance.search = AsyncMock(return_value=MOCK_VECTOR_RESULTS)
            mock_vse.return_value = mock_vse_instance

            pipeline = RAGPipeline(mock_db)

            # Mock context builder sub-methods to return clean dicts
            pipeline.context_builder.build_match_context = AsyncMock(return_value=[])
            pipeline.context_builder.build_brochure_context = AsyncMock(return_value=[])
            pipeline.context_builder.build_vector_context = AsyncMock(return_value=MOCK_VECTOR_RESULTS)

            # Mock DeepSeekClient.chat
            pipeline.deepseek.chat = AsyncMock(return_value={
                "content": "根据检索结果，推荐您联系李四（腾讯，匹配度0.82）[来源: 向量搜索]，他在产品策略方面有丰富经验。",
                "tokens_used": 150,
                "role": "assistant",
                "finish_reason": "stop",
                "prompt_tokens": 80,
                "completion_tokens": 70,
            })

            result = await pipeline.query(
                user_id=1,
                query_text="推荐AI方向的合作伙伴",
                top_k=10,
            )

            assert isinstance(result, RAGResponse)
            assert result.answer
            assert "李四" in result.answer
            assert len(result.sources) > 0
            assert result.tokens_used == 150
            assert result.model_used == "deepseek-chat"

            await pipeline.close()

    @pytest.mark.asyncio
    async def test_query_fallback(self):
        """测试 LLM 不可用时的降级回退"""
        mock_db = AsyncMock(spec=AsyncSession)

        def db_execute_side_effect(query):
            mock = MagicMock()
            mock.scalars.return_value.first.return_value = MOCK_USER
            mock.scalars.return_value.all.return_value = MOCK_TAGS
            return mock

        mock_db.execute = AsyncMock(side_effect=db_execute_side_effect)

        with patch("app.ai.rag_pipeline.VectorSearchEngine") as mock_vse:
            mock_vse_instance = AsyncMock()
            mock_vse_instance.search = AsyncMock(return_value=MOCK_VECTOR_RESULTS)
            mock_vse.return_value = mock_vse_instance

            pipeline = RAGPipeline(mock_db)

            # Mock context builder sub-methods to return clean dicts
            pipeline.context_builder.build_match_context = AsyncMock(return_value=[])
            pipeline.context_builder.build_brochure_context = AsyncMock(return_value=[])
            pipeline.context_builder.build_vector_context = AsyncMock(return_value=MOCK_VECTOR_RESULTS)
            pipeline.deepseek.chat = AsyncMock(return_value={
                "error": "API调用失败: 429",
            })

            result = await pipeline.query(
                user_id=1,
                query_text="推荐合作伙伴",
            )

            assert isinstance(result, RAGResponse)
            assert result.answer
            assert "李四" in result.answer  # fallback 中包含用户信息
            assert result.confidence == 0.5  # 降级置信度

            await pipeline.close()

    @pytest.mark.asyncio
    async def test_empty_context(self):
        """测试空上下文（新用户，无数据）"""
        mock_db = AsyncMock(spec=AsyncSession)

        mock_empty_user = MagicMock()
        mock_empty_user.id = 99
        mock_empty_user.name = "新用户"
        mock_empty_user.company = ""
        mock_empty_user.title = ""
        mock_empty_user.intro = ""
        mock_empty_user.membership_tier = "free"

        def db_execute_side_effect(query):
            mock = MagicMock()
            mock.scalars.return_value.first.return_value = mock_empty_user
            mock.scalars.return_value.all.return_value = []
            return mock

        mock_db.execute = AsyncMock(side_effect=db_execute_side_effect)

        with patch("app.ai.rag_pipeline.VectorSearchEngine") as mock_vse:
            mock_vse_instance = AsyncMock()
            mock_vse_instance.search = AsyncMock(return_value=[])
            mock_vse.return_value = mock_vse_instance

            pipeline = RAGPipeline(mock_db)

            # Mock 返回合理回答
            pipeline.deepseek.chat = AsyncMock(return_value={
                "content": "您好！根据您的信息，目前系统中还没有找到与您匹配的推荐。建议您完善个人资料和标签，以获得更精准的推荐。",
                "tokens_used": 50,
                "role": "assistant",
                "finish_reason": "stop",
                "prompt_tokens": 30,
                "completion_tokens": 20,
            })

            result = await pipeline.query(
                user_id=99,
                query_text="有什么推荐？",
            )

            assert result.answer
            assert result.tokens_used == 50

            await pipeline.close()

    @pytest.mark.asyncio
    async def test_query_with_conversation_history(self):
        """测试带对话历史的 RAG 查询"""
        mock_db = AsyncMock(spec=AsyncSession)

        pipeline = RAGPipeline(mock_db)
        pipeline.deepseek.chat = AsyncMock(return_value={
            "content": "基于之前提到的AI方向，我推荐您联系李四。",
            "tokens_used": 60,
        })

        # 使用上下文构建器 mock
        pipeline.context_builder.build_user_profile = AsyncMock(return_value={
            "user_id": 1, "name": "张三",
        })
        pipeline.context_builder.build_brochure_context = AsyncMock(return_value=[])
        pipeline.context_builder.build_vector_context = AsyncMock(return_value=MOCK_VECTOR_RESULTS)
        pipeline.context_builder.build_match_context = AsyncMock(return_value=[])

        result = await pipeline.query(
            user_id=1,
            query_text="你刚才推荐了谁？",
            conversation_history=[
                {"role": "user", "content": "推荐AI方向的合作伙伴"},
                {"role": "assistant", "content": "推荐您联系李四"},
            ],
        )

        assert result.answer
        assert len(result.sources) > 0

        await pipeline.close()


# ======================================================================
# RAGContext / RAGResponse 数据模型测试
# ======================================================================


class TestDataModels:
    """RAG 数据模型测试"""

    def test_rag_context_defaults(self):
        """测试 RAGContext 默认值"""
        ctx = RAGContext(query="test", user_id=1)
        assert ctx.query == "test"
        assert ctx.user_id == 1
        assert ctx.vector_results == []
        assert ctx.user_profile == {}
        assert ctx.related_brochures == []
        assert ctx.match_suggestions == []
        assert ctx.source_refs == []
        assert ctx.conversation_history == []

    def test_rag_context_to_dict(self):
        """测试 RAGContext 序列化"""
        ctx = RAGContext(
            query="test",
            user_id=1,
            vector_results=MOCK_VECTOR_RESULTS,
            user_profile={"name": "张三"},
        )
        d = ctx.to_dict()
        assert d["query"] == "test"
        assert d["user_id"] == 1
        assert len(d["vector_results"]) == 2
        assert d["user_profile"]["name"] == "张三"

    def test_rag_response_defaults(self):
        """测试 RAGResponse 默认值"""
        resp = RAGResponse(answer="你好")
        assert resp.answer == "你好"
        assert resp.sources == []
        assert resp.confidence == 0.0
        assert resp.model_used == "deepseek-chat"
        assert resp.tokens_used == 0

    def test_rag_response_to_dict(self):
        """测试 RAGResponse 序列化"""
        resp = RAGResponse(
            answer="测试回答",
            sources=[{"type": "vector", "user_id": 1}],
            confidence=0.9,
            model_used="deepseek-chat",
            tokens_used=100,
        )
        d = resp.to_dict()
        assert d["answer"] == "测试回答"
        assert d["confidence"] == 0.9
        assert len(d["sources"]) == 1


# ======================================================================
# 源引用追踪测试
# ======================================================================


class TestSourceReferences:
    """源引用追踪测试"""

    @pytest.mark.asyncio
    async def test_sources_from_vector_results(self):
        """测试向量搜索结果转为源引用"""
        mock_db = AsyncMock()

        with patch("app.ai.rag_pipeline.VectorSearchEngine") as mock_vse:
            mock_vse_instance = AsyncMock()
            mock_vse_instance.search = AsyncMock(return_value=MOCK_VECTOR_RESULTS)
            mock_vse.return_value = mock_vse_instance

            pipeline = RAGPipeline(mock_db)
            pipeline.context_builder.build_user_profile = AsyncMock(return_value={})
            pipeline.context_builder.build_brochure_context = AsyncMock(return_value=[])
            pipeline.context_builder.build_vector_context = AsyncMock(return_value=MOCK_VECTOR_RESULTS)
            pipeline.context_builder.build_match_context = AsyncMock(return_value=[])
            pipeline.deepseek.chat = AsyncMock(return_value={"content": "OK", "tokens_used": 10})

            result = await pipeline.query(user_id=1, query_text="test", include_sources=True)

            sources_types = [s["type"] for s in result.sources]
            assert "vector_search" in sources_types

            await pipeline.close()

    @pytest.mark.asyncio
    async def test_sources_disabled(self):
        """测试关闭源引用"""
        mock_db = AsyncMock()

        with patch("app.ai.rag_pipeline.VectorSearchEngine") as mock_vse:
            mock_vse_instance = AsyncMock()
            mock_vse.return_value = mock_vse_instance

            pipeline = RAGPipeline(mock_db)
            pipeline.context_builder.build_user_profile = AsyncMock(return_value={})
            pipeline.context_builder.build_brochure_context = AsyncMock(return_value=[])
            pipeline.context_builder.build_vector_context = AsyncMock(return_value=MOCK_VECTOR_RESULTS)
            pipeline.context_builder.build_match_context = AsyncMock(return_value=[])
            pipeline.deepseek.chat = AsyncMock(return_value={"content": "OK", "tokens_used": 10})

            result = await pipeline.query(user_id=1, query_text="test", include_sources=False)

            assert result.sources == []

            await pipeline.close()
