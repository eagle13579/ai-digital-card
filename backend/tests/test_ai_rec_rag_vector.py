"""AI数字名片 三模块单元测试: recommmendation / rag_pipeline / vector_search

测试覆盖:
  1. RecommendEngine (personalize_recommend, tag/graph/semantic 评分, _build_recommend_item)
     + OnlineLearningTracker.get_trending_tags (第965行)
  2. RAGPipeline (query, query_stream, _fallback_answer)
     + DeepSeekClient.chat, ContextBuilder 各方法
  3. VectorSearchIndex (add/remove/clear, save/load, add_or_update, delete, search)
     + VectorSearchEngine (build_index, search, rerank, search_brochures)
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import numpy as np
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag_pipeline import (
    RAGPipeline, DeepSeekClient, ContextBuilder,
    RAGContext, RAGResponse,
)
from app.ai.recommendation import (
    RecommendEngine, RecommendItem, RecommendResult, OnlineLearningTracker,
)
from app.ai.vector_search import (
    VectorSearchIndex, VectorSearchEngine,
    NumpyEmbedding, EmbeddingBackend,
    get_embedding_backend, get_vector_index,
    EMBEDDING_DIM, VECTOR_TOP_K,
)


# ══════════════════════════════════════════════════════════════════════
# Fixtures (模块级, 轻量 mock)
# ══════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_db():
    """Mock AsyncSession with properly chained execute → scalars → first/all."""
    db = AsyncMock(spec=AsyncSession)
    # db.execute(query) returns a coroutine; await yields execute.return_value
    scalar_mock = MagicMock()
    scalar_mock.first = MagicMock(return_value=None)
    scalar_mock.all = MagicMock(return_value=[])
    result_mock = MagicMock()
    result_mock.scalars = MagicMock(return_value=scalar_mock)
    db.execute = AsyncMock(return_value=result_mock)
    return db


@pytest.fixture
def numpy_backend():
    """Ensure numpy backend is used (zero deps)."""
    return NumpyEmbedding(dim=64)


@pytest.fixture
def temp_db_path():
    """Temporary SQLite file for VectorSearchIndex persistence tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    if os.path.isfile(path):
        os.unlink(path)


# ══════════════════════════════════════════════════════════════════════
# 1. recommendation.py — RecommendEngine & OnlineLearningTracker
# ══════════════════════════════════════════════════════════════════════

class TestRecommendEngine:
    """RecommendEngine: personalize_recommend + 各维度评分"""

    @pytest.mark.asyncio
    async def test_personalize_recommend_user_not_found(self, mock_db):
        """用户不存在 → 返回空 RecommendResult"""
        mock_db.execute.return_value.scalars.return_value.first.return_value = None
        engine = RecommendEngine(mock_db)
        result = await engine.personalize_recommend(user_id=999)
        assert isinstance(result, RecommendResult)
        assert result.items == []
        assert result.strategy_used == "hybrid"

    @pytest.mark.asyncio
    async def test_personalize_recommend_tag_strategy(self, mock_db):
        """策略=tag: 只走标签评分"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.name = "测试用户"
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_user

        engine = RecommendEngine(mock_db)
        # Mock _score_by_tag_match to return known scores
        engine._score_by_tag_match = AsyncMock(return_value=({2: 0.8, 3: 0.5}, "tag"))
        engine._score_by_graph = AsyncMock()
        engine._score_by_semantic = AsyncMock()
        engine._build_recommend_item = AsyncMock(side_effect=lambda uid, fs, ts, gs, ss: RecommendItem(
            user_id=uid, name=f"User{uid}", score=fs,
            tag_match_score=ts, graph_score=gs, semantic_score=ss,
        ))

        result = await engine.personalize_recommend(user_id=1, strategy="tag")
        engine._score_by_tag_match.assert_awaited_once()
        engine._score_by_graph.assert_not_called()
        engine._score_by_semantic.assert_not_called()
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_personalize_recommend_graph_strategy(self, mock_db):
        """策略=graph: 只走图谱评分"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.name = "测试用户"
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_user

        engine = RecommendEngine(mock_db)
        engine._score_by_graph = AsyncMock(return_value=({2: 0.9}, "graph"))
        engine._score_by_tag_match = AsyncMock()
        engine._score_by_semantic = AsyncMock()
        engine._build_recommend_item = AsyncMock(return_value=RecommendItem(
            user_id=2, name="User2", score=0.9,
        ))

        result = await engine.personalize_recommend(user_id=1, strategy="graph")
        engine._score_by_graph.assert_awaited_once()
        engine._score_by_tag_match.assert_not_called()
        engine._score_by_semantic.assert_not_called()

    @pytest.mark.asyncio
    async def test_personalize_recommend_semantic_strategy(self, mock_db):
        """策略=semantic: 只走语义评分"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.name = "测试用户"
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_user

        engine = RecommendEngine(mock_db)
        engine._score_by_semantic = AsyncMock(return_value=({3: 0.75}, "semantic"))
        engine._score_by_tag_match = AsyncMock()
        engine._score_by_graph = AsyncMock()
        engine._build_recommend_item = AsyncMock(return_value=RecommendItem(
            user_id=3, name="User3", score=0.75,
        ))

        result = await engine.personalize_recommend(user_id=1, strategy="semantic")
        engine._score_by_semantic.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_personalize_recommend_hybrid_scoring(self, mock_db):
        """hybrid 策略: 加权融合 tag(0.4)+graph(0.3)+semantic(0.3)"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.name = "测试用户"
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_user

        engine = RecommendEngine(mock_db)
        engine._score_by_tag_match = AsyncMock(return_value=({2: 1.0}, "tag"))
        engine._score_by_graph = AsyncMock(return_value=({2: 0.5}, "graph"))
        engine._score_by_semantic = AsyncMock(return_value=({2: 0.0}, "semantic"))
        engine._build_recommend_item = AsyncMock(return_value=RecommendItem(
            user_id=2, name="User2", score=0.55,
        ))

        result = await engine.personalize_recommend(user_id=1, strategy="hybrid")
        # hybrid = 0.4*1.0 + 0.3*0.5 + 0.3*0.0 = 0.55
        engine._build_recommend_item.assert_awaited_once()
        args = engine._build_recommend_item.call_args
        assert args[0][0] == 2  # user_id
        assert abs(args[0][1] - 0.55) < 0.01  # final_score ~0.55


class TestOnlineLearningTracker:
    """OnlineLearningTracker — get_trending_tags (第965行附近)"""

    def test_get_trending_tags_empty_db(self, temp_db_path):
        """空数据库 → 返回空 dict"""
        tracker = OnlineLearningTracker(db_path=temp_db_path)
        trending = tracker.get_trending_tags(hours=24)
        assert trending == {}

    def test_get_trending_tags_with_data(self, temp_db_path):
        """有点击数据 → 按热度返回"""
        tracker = OnlineLearningTracker(db_path=temp_db_path)
        now = time.time()
        conn = tracker._get_conn()
        conn.execute("INSERT INTO click_events (user_id, target_id, created_at) VALUES (1, 10, ?)", (now - 100,))
        conn.execute("INSERT INTO click_events (user_id, target_id, created_at) VALUES (2, 10, ?)", (now - 200,))
        conn.execute("INSERT INTO click_events (user_id, target_id, created_at) VALUES (1, 20, ?)", (now - 300,))
        conn.commit()
        conn.close()

        trending = tracker.get_trending_tags(hours=24)
        assert trending == {10: 2, 20: 1}

    def test_get_trending_tags_outside_window(self, temp_db_path):
        """超时窗口外的数据不统计"""
        tracker = OnlineLearningTracker(db_path=temp_db_path)
        conn = tracker._get_conn()
        conn.execute(
            "INSERT INTO click_events (user_id, target_id, created_at) VALUES (1, 99, ?)",
            (time.time() - 48 * 3600,),  # 48 hours ago
        )
        conn.commit()
        conn.close()

        trending = tracker.get_trending_tags(hours=24)
        assert 99 not in trending

    def test_get_trending_tags_max_50(self, temp_db_path):
        """最多返回50条"""
        tracker = OnlineLearningTracker(db_path=temp_db_path)
        conn = tracker._get_conn()
        now = time.time()
        for i in range(60):
            conn.execute(
                "INSERT INTO click_events (user_id, target_id, created_at) VALUES (1, ?, ?)",
                (100 + i, now - i),
            )
        conn.commit()
        conn.close()

        trending = tracker.get_trending_tags(hours=24)
        assert len(trending) <= 50

    def test_track_then_get_trending(self, temp_db_path):
        """track_click → get_trending_tags 集成验证"""
        tracker = OnlineLearningTracker(db_path=temp_db_path)
        tracker.track_click(user_id=1, target_id=42)
        tracker.track_click(user_id=1, target_id=42)
        tracker.track_click(user_id=2, target_id=42)
        trending = tracker.get_trending_tags(hours=24)
        assert trending.get(42) == 3


# ══════════════════════════════════════════════════════════════════════
# 2. rag_pipeline.py — DeepSeekClient, ContextBuilder, RAGPipeline
# ══════════════════════════════════════════════════════════════════════

class TestDeepSeekClient:
    """DeepSeekClient.chat — mock HTTP 调用"""

    @pytest.mark.asyncio
    async def test_chat_success(self):
        """正常非流式响应"""
        client = DeepSeekClient(api_key="test-key")
        with patch.object(client, "_get_session", new=AsyncMock()) as mock_get_session:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value={
                "choices": [{"message": {"content": "你好,我是AI"}}],
                "usage": {"total_tokens": 42},
            })
            mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_resp.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.post = MagicMock(return_value=mock_resp)
            mock_get_session.return_value = mock_session

            result = await client.chat(messages=[{"role": "user", "content": "你好"}])
            assert isinstance(result, dict)
            assert result["content"] == "你好,我是AI"
            assert result["tokens_used"] == 42

    @pytest.mark.asyncio
    async def test_chat_api_error(self):
        """API 返回非200 → 返回错误 dict"""
        client = DeepSeekClient(api_key="test-key")
        with patch.object(client, "_get_session", new=AsyncMock()) as mock_get_session:
            mock_resp = AsyncMock()
            mock_resp.status = 401
            mock_resp.text = AsyncMock(return_value="Unauthorized")
            mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_resp.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.post = MagicMock(return_value=mock_resp)
            mock_get_session.return_value = mock_session

            result = await client.chat(messages=[])
            assert "error" in result
            assert "401" in result["error"]

    @pytest.mark.asyncio
    async def test_chat_empty_messages(self):
        """空消息列表也能正常调用（无 content 兜底）"""
        client = DeepSeekClient(api_key="test-key")
        with patch.object(client, "_get_session", new=AsyncMock()) as mock_get_session:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value={
                "choices": [{"message": {"content": ""}}],
                "usage": {"total_tokens": 0},
            })
            mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_resp.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.post = MagicMock(return_value=mock_resp)
            mock_get_session.return_value = mock_session

            result = await client.chat(messages=[])
            assert result["content"] == ""

    @pytest.mark.asyncio
    async def test_chat_empty_api_key_does_not_crash(self):
        """空 API key 不会崩溃（底层 session 仍可创建）"""
        client = DeepSeekClient(api_key="")
        with patch.object(client, "_get_session", new=AsyncMock()) as mock_get_session:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value={
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"total_tokens": 1},
            })
            mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_resp.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.post = MagicMock(return_value=mock_resp)
            mock_get_session.return_value = mock_session

            result = await client.chat(messages=[{"role": "user", "content": "hi"}])
            assert result["content"] == "ok"


class TestContextBuilder:
    """ContextBuilder 各静态方法"""

    @pytest.mark.asyncio
    async def test_build_user_profile_found(self, mock_db):
        """用户存在 → 返回完整的画像 dict"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.name = "张三"
        mock_user.company = "阿里"
        mock_user.title = "工程师"
        mock_user.intro = "做AI"
        mock_user.membership_tier = "gold"

        mock_tags = [
            MagicMock(tag="Python", tag_type="provide"),
            MagicMock(tag="Go", tag_type="need"),
        ]

        # chain: db.execute → scalars() → first() / all()
        user_scalar = MagicMock()
        user_scalar.first = MagicMock(return_value=mock_user)
        tag_scalar = MagicMock()
        tag_scalar.all = MagicMock(return_value=mock_tags)

        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalars=MagicMock(return_value=user_scalar)),
            MagicMock(scalars=MagicMock(return_value=tag_scalar)),
        ])

        profile = await ContextBuilder.build_user_profile(mock_db, 1)
        assert profile["user_id"] == 1
        assert profile["name"] == "张三"
        assert "Python" in profile["provide_tags"]
        assert "Go" in profile["need_tags"]

    @pytest.mark.asyncio
    async def test_build_user_profile_not_found(self, mock_db):
        """用户不存在 → 返回空 dict"""
        # mock_db already has execute → scalars → first = None from fixture
        profile = await ContextBuilder.build_user_profile(mock_db, 999)
        assert profile == {}

    @pytest.mark.asyncio
    async def test_build_vector_context_empty_db(self, mock_db):
        """无向量索引 → 返回空列表"""
        with patch("app.ai.rag_pipeline.VectorSearchEngine") as mock_vse_cls:
            mock_vse = MagicMock()
            mock_vse.search = AsyncMock(return_value=[])
            mock_vse_cls.return_value = mock_vse
            results = await ContextBuilder.build_vector_context(mock_db, "Python", 1, 10)
            assert results == []

    @pytest.mark.asyncio
    async def test_build_match_context_no_records(self, mock_db):
        """无 MatchRecord → 返回空列表"""
        # mock_db fixture already has scalars().all() returning []
        results = await ContextBuilder.build_match_context(mock_db, 1)
        assert results == []

    def test_build_system_prompt_contains_context(self):
        """system prompt 包含用户和结果信息"""
        ctx = RAGContext(
            query="找Python开发伙伴",
            user_id=1,
            user_profile={"name": "张三", "company": "阿里", "title": "工程师"},
            vector_results=[{"user_name": "李四", "company": "腾讯", "score": 0.95}],
            match_suggestions=[{"name": "王五", "company": "字节", "match_score": 0.88}],
        )
        prompt = ContextBuilder.build_system_prompt(ctx)
        assert "张三" in prompt
        assert "李四" in prompt
        assert "腾讯" in prompt
        assert "王五" in prompt
        assert "字节" in prompt


class TestRAGPipeline:
    """RAGPipeline.query / query_stream / _fallback_answer"""

    @pytest.mark.asyncio
    async def test_query_success(self, mock_db):
        """正常 RAG 查询 → 返回 RAGResponse"""
        pipe = RAGPipeline(mock_db)

        # Mock DeepSeekClient.chat
        pipe.deepseek.chat = AsyncMock(return_value={
            "content": "推荐您联系李四(腾讯)",
            "tokens_used": 88,
        })

        # Mock ContextBuilder methods
        pipe.context_builder.build_user_profile = AsyncMock(return_value={
            "name": "张三", "company": "阿里",
        })
        pipe.context_builder.build_brochure_context = AsyncMock(return_value=[])
        pipe.context_builder.build_vector_context = AsyncMock(return_value=[
            {"user_id": 2, "user_name": "李四", "company": "腾讯", "score": 0.95},
        ])
        pipe.context_builder.build_match_context = AsyncMock(return_value=[])
        pipe.context_builder.build_system_prompt = MagicMock(return_value="You are a helpful assistant.")

        result = await pipe.query(user_id=1, query_text="找Python开发")
        assert isinstance(result, RAGResponse)
        assert "李四" in result.answer
        assert result.confidence == 0.9
        assert len(result.sources) >= 1

    @pytest.mark.asyncio
    async def test_query_llm_error_fallback(self, mock_db):
        """LLM 报错 → 走 _fallback_answer 降级"""
        pipe = RAGPipeline(mock_db)
        pipe.deepseek.chat = AsyncMock(return_value={"error": "API失败: 500"})

        pipe.context_builder.build_user_profile = AsyncMock(return_value={})
        pipe.context_builder.build_brochure_context = AsyncMock(return_value=[])
        pipe.context_builder.build_vector_context = AsyncMock(return_value=[])
        pipe.context_builder.build_match_context = AsyncMock(return_value=[])
        pipe.context_builder.build_system_prompt = MagicMock(return_value="system prompt")

        result = await pipe.query(user_id=1, query_text="test")
        assert result.confidence == 0.5  # 降级置信度

    @pytest.mark.asyncio
    async def test_query_stream_yields_chunks(self, mock_db):
        """流式查询 → 产出文本块"""
        pipe = RAGPipeline(mock_db)

        async def mock_stream_fn(*args, **kwargs):
            async def _gen():
                for chunk in ["推荐", "您", "联系", "李四"]:
                    yield chunk
            return _gen()

        pipe.deepseek.chat = MagicMock(side_effect=mock_stream_fn)
        pipe.context_builder.build_user_profile = AsyncMock(return_value={})
        pipe.context_builder.build_brochure_context = AsyncMock(return_value=[])
        pipe.context_builder.build_vector_context = AsyncMock(return_value=[])
        pipe.context_builder.build_match_context = AsyncMock(return_value=[])
        pipe.context_builder.build_system_prompt = MagicMock(return_value="system")

        chunks = []
        async for chunk in pipe.query_stream(user_id=1, query_text="test"):
            chunks.append(chunk)
        assert len(chunks) >= 1
        assert "".join(chunks) == "推荐您联系李四"

    @pytest.mark.asyncio
    async def test_query_empty_text(self, mock_db):
        """空查询文本 → 仍正常返回"""
        pipe = RAGPipeline(mock_db)
        pipe.deepseek.chat = AsyncMock(return_value={
            "content": "请提供您的问题",
            "tokens_used": 10,
        })
        pipe.context_builder.build_user_profile = AsyncMock(return_value={})
        pipe.context_builder.build_brochure_context = AsyncMock(return_value=[])
        pipe.context_builder.build_vector_context = AsyncMock(return_value=[])
        pipe.context_builder.build_match_context = AsyncMock(return_value=[])
        pipe.context_builder.build_system_prompt = MagicMock(return_value="system")

        result = await pipe.query(user_id=1, query_text="")
        assert isinstance(result, RAGResponse)

    def test_fallback_answer_with_vector_results(self):
        """降级回答包含向量搜索结果"""
        ctx = RAGContext(
            query="找Python",
            user_id=1,
            vector_results=[
                {"user_name": "李四", "company": "腾讯", "score": 0.95},
                {"user_name": "王五", "company": "字节", "score": 0.85},
            ],
        )
        pipe = RAGPipeline(mock_db := MagicMock())
        answer = pipe._fallback_answer(ctx)
        assert "李四" in answer
        assert "腾讯" in answer
        assert "字节" in answer


# ══════════════════════════════════════════════════════════════════════
# 3. vector_search.py — VectorSearchIndex & VectorSearchEngine
# ══════════════════════════════════════════════════════════════════════

class TestVectorSearchIndex:
    """VectorSearchIndex: add/remove/clear, save/load, add_or_update, delete, search"""

    @pytest.fixture(autouse=True)
    def _use_numpy_backend(self):
        """确保全局 backend 是 numpy (64维, 轻量)"""
        with patch("app.ai.vector_search.get_embedding_backend") as mock_get:
            backend = NumpyEmbedding(dim=64)
            mock_get.return_value = backend
            yield

    def _make_index(self, db_path):
        """Helper: 创建 VectorSearchIndex 并绕过自动加载"""
        with patch.object(VectorSearchIndex, "_auto_load", return_value=False):
            return VectorSearchIndex(db_path=db_path)

    def test_add_and_search(self, temp_db_path):
        """添加文档 → search 能召回"""
        idx = self._make_index(temp_db_path)
        idx.add_document(1, "Python全栈开发工程师", {"content_type": "user", "content_id": 1})
        idx.add_document(2, "Java后端架构师", {"content_type": "user", "content_id": 2})

        results = idx.search("Python", top_k=5)
        assert len(results) > 0
        # 得分最高的是 Python 文档
        top = results[0]
        assert top["id"] == 1 or top["score"] > results[-1]["score"]

    def test_search_empty_index(self, temp_db_path):
        """空索引 → 返回空列表"""
        idx = self._make_index(temp_db_path)
        assert idx.search("anything", top_k=5) == []

    def test_search_empty_query(self, temp_db_path):
        """空查询 → 返回空列表"""
        idx = self._make_index(temp_db_path)
        idx.add_document(1, "some doc", {})
        assert idx.search("", top_k=5) == []
        assert idx.search("   ", top_k=5) == []

    def test_remove_document(self, temp_db_path):
        """删除文档 → search 不再包含"""
        idx = self._make_index(temp_db_path)
        idx.add_document(1, "Python开发", {})
        idx.add_document(2, "Java开发", {})
        idx.remove_document(1)
        results = idx.search("Python", top_k=5)
        ids = [r["id"] for r in results]
        assert 1 not in ids

    def test_clear(self, temp_db_path):
        """清空索引 → size = 0, search 空"""
        idx = self._make_index(temp_db_path)
        idx.add_document(1, "doc1", {})
        idx.add_document(2, "doc2", {})
        assert idx.size == 2
        idx.clear()
        assert idx.size == 0
        assert idx.search("doc", top_k=5) == []

    def test_save_and_load(self, temp_db_path):
        """save_index → load_index 持久化正确"""
        with patch.object(VectorSearchIndex, "_auto_load", return_value=False):
            idx1 = VectorSearchIndex(db_path=temp_db_path)
        idx1.add_document(1, "持久化测试文本", {"content_type": "test", "content_id": 1})
        saved = idx1.save_index()
        assert saved == 1

        # 新实例加载
        with patch.object(VectorSearchIndex, "_auto_load", return_value=False):
            idx2 = VectorSearchIndex(db_path=temp_db_path)
        loaded = idx2.load_index(temp_db_path)
        assert loaded == 1
        results = idx2.search("持久化", top_k=5)
        assert len(results) == 1
        # doc_id = hash("test:1") & 0x7FFFFFFF — not equal to original input ID
        assert results[0]["metadata"]["content_type"] == "test"
        assert results[0]["metadata"]["content_id"] == 1

    def test_add_or_update_new(self, temp_db_path):
        """add_or_update 新增条目"""
        idx = self._make_index(temp_db_path)
        ok = idx.add_or_update("user", 42, "AI产品经理", {"extra": "data"})
        assert ok is True
        assert idx.size == 1

    def test_add_or_update_skip_unchanged(self, temp_db_path):
        """add_or_update 相同 hash → 跳过 (返回 False)"""
        idx = self._make_index(temp_db_path)
        idx.add_or_update("user", 42, "内容不变")
        ok = idx.add_or_update("user", 42, "内容不变")  # 同内容
        assert ok is False

    def test_delete(self, temp_db_path):
        """delete 从内存和 SQLite 删除"""
        idx = self._make_index(temp_db_path)
        idx.add_or_update("user", 10, "可删除文档")
        assert idx.has_entry("user", 10) is True
        removed = idx.delete("user", 10)
        assert removed is True
        assert idx.has_entry("user", 10) is False
        assert idx.size == 0

    def test_size_property(self, temp_db_path):
        """size 属性准确反映文档数"""
        idx = self._make_index(temp_db_path)
        assert idx.size == 0
        idx.add_document(1, "a", {})
        assert idx.size == 1
        idx.add_document(2, "b", {})
        assert idx.size == 2
        idx.remove_document(1)
        assert idx.size == 1


class TestVectorSearchEngine:
    """VectorSearchEngine 包装类: build_index, search, rerank, search_brochures"""

    def _make_engine(self):
        """创建 mock 引擎，替换 backend 为 numpy，db.query 返回 mock"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        engine = VectorSearchEngine(db=db)
        engine._backend = NumpyEmbedding(dim=64)
        return engine

    def test_build_index_no_documents(self):
        """空数据库 → build_index 不崩溃, _index_built = False"""
        engine = self._make_engine()
        with patch("app.ai.vector_search.DocumentBuilder.build_all_documents",
                   return_value=([], [])):
            engine.build_index()
            assert engine._index_built is False

    def test_search_without_build(self):
        """未 build → search 返回空列表"""
        engine = self._make_engine()
        engine._index_built = False
        assert engine.search("anything") == []

    def test_search_exclude_user(self):
        """search 排除指定用户"""
        engine = self._make_engine()
        engine._index_built = True
        engine.user_ids = [1, 2]
        # 64-dim to match numpy backend
        dim = engine._backend.dimension
        engine.user_vectors = np.zeros((2, dim), dtype=np.float32)
        engine.user_vectors[0, 0] = 1.0
        engine.user_vectors[1, 1] = 1.0

        # Mock db query to return user objects
        user_mock = MagicMock()
        user_mock.id = 2
        user_mock.name = "李四"
        user_mock.company = "腾讯"
        user_mock.title = "工程师"
        user_mock.avatar = ""
        engine.db.query.return_value.filter.return_value.first.return_value = user_mock

        # Mock app.cache.redis.get_redis to return None (no cache)
        with patch("app.cache.redis.get_redis", return_value=None):
            results = engine.search("test", top_k=5, exclude_user_id=1, min_score=0.0)
        user_ids = [r["user_id"] for r in results]
        assert 1 not in user_ids
        assert 2 in user_ids

    def test_rerank_empty_candidates(self):
        """空候选列表 → rerank 原样返回"""
        engine = self._make_engine()
        result = engine.rerank([], "query")
        assert result == []

    def test_rerank_orders_by_semantic_score(self):
        """rerank 按语义分数降序"""
        engine = self._make_engine()
        candidates = [
            {"user_id": 1, "name": "张三"},
            {"user_id": 2, "name": "李四"},
        ]
        with patch("app.ai.vector_search.DocumentBuilder.build_user_document",
                   side_effect=["Python开发", "Java架构"]):
            result = engine.rerank(candidates, "Python")
        assert len(result) == 2
        assert "semantic_score" in result[0]

    def test_search_brochures_empty_query(self):
        """空查询 → brochure搜索返回空"""
        engine = self._make_engine()
        assert engine.search_brochures("", top_k=5) == []

    def test_search_brochures_no_published(self):
        """无 published brochure → 返回空列表"""
        engine = self._make_engine()
        engine.db.query.return_value.filter.return_value.all.return_value = []
        assert engine.search_brochures("Python", top_k=5) == []
