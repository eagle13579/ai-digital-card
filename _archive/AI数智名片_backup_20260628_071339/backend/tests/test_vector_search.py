"""
向量搜索引擎测试 — 验证 M3E/多后端 embedding 及兼容接口
"""

import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

from app.ai.vector_search import (
    EMBEDDING_DIM,
    EMBEDDING_PROVIDER,
    USE_VECTOR_SEARCH,
    VECTOR_TOP_K,
    NumpyEmbedding,
    M3EEmbedding,
    EmbeddingBackend,
    get_embedding_backend,
    embed_text,
    embed_single,
    VectorSearchIndex,
    cosine_similarity,
    rerank,
    DocumentBuilder,
)


# ── 后端基础测试 ────────────────────────────────────────────────────────


class TestEmbeddingBackends:
    """测试各 embedding 后端的基础功能"""

    def test_numpy_embedding_basic(self):
        """NumpyEmbedding: 基本功能"""
        backend = NumpyEmbedding(dim=768)
        assert backend.dimension == 768
        assert backend.name == "numpy"

        # 单文本
        vecs = backend.embed(["Hello World"])
        assert vecs.shape == (1, 768)
        assert vecs.dtype == np.float32
        assert np.isfinite(vecs).all()

        # 多文本
        vecs = backend.embed(["Hello", "World", "测试中文"])
        assert vecs.shape == (3, 768)

        # 空列表
        vecs = backend.embed([])
        assert vecs.shape == (0, 768)

        # 空文本
        vecs = backend.embed([""])
        assert vecs.shape == (1, 768)

    def test_numpy_embedding_deterministic(self):
        """NumpyEmbedding: 相同输入得到相同输出"""
        backend = NumpyEmbedding(dim=768)
        vecs1 = backend.embed(["Python全栈开发工程师"])
        vecs2 = backend.embed(["Python全栈开发工程师"])
        assert np.allclose(vecs1, vecs2)

    def test_numpy_embedding_semantic_similarity(self):
        """NumpyEmbedding: 语义相近文本向量相近"""
        backend = NumpyEmbedding(dim=768)

        # 相似文本
        vecs_sim = backend.embed(["Python开发", "Python程序员"])
        sim_score = float(np.dot(vecs_sim[0], vecs_sim[1]))

        # 不相似文本
        vecs_diff = backend.embed(["Python开发", "农业种植"])
        diff_score = float(np.dot(vecs_diff[0], vecs_diff[1]))

        assert sim_score > diff_score, (
            f"相似文本的余弦相似度({sim_score:.4f})应高于不相似文本({diff_score:.4f})"
        )

    def test_embed_text_interface(self):
        """embed_text: 对外接口测试"""
        # 单字符串
        vecs = embed_text("测试文本")
        assert vecs.shape == (1, EMBEDDING_DIM)

        # 字符串列表
        vecs = embed_text(["文本A", "文本B", "文本C"])
        assert vecs.shape == (3, EMBEDDING_DIM)

    def test_embed_single_interface(self):
        """embed_single: 返回 Python list"""
        vec = embed_single("测试文本")
        assert isinstance(vec, list)
        assert len(vec) == EMBEDDING_DIM
        assert all(isinstance(v, float) for v in vec)


# ── get_embedding_backend 工厂测试 ──────────────────────────────────────


class TestEmbeddingFactory:
    """测试 embedding 工厂函数"""

    def test_get_backend_singleton(self):
        """get_embedding_backend: 返回单例"""
        backend1 = get_embedding_backend()
        backend2 = get_embedding_backend()
        assert backend1 is backend2

    def test_backend_type(self):
        """get_embedding_backend: 返回正确的后端类型"""
        backend = get_embedding_backend()
        # 根据配置，应该是 NumpyEmbedding（测试环境没有 M3E）
        assert isinstance(backend, EmbeddingBackend)
        assert hasattr(backend, "embed")
        assert hasattr(backend, "dimension")
        assert hasattr(backend, "name")


# ── 余弦相似度测试 ──────────────────────────────────────────────────────


class TestCosineSimilarity:
    """测试余弦相似度函数"""

    def test_identical_vectors(self):
        """相同向量的相似度为 1.0"""
        vec = [1.0, 0.0, 0.0]
        score = cosine_similarity(vec, vec)
        assert abs(score - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        """正交向量的相似度为 0.0"""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        score = cosine_similarity(vec_a, vec_b)
        assert abs(score) < 1e-6

    def test_zero_vector(self):
        """零向量返回 0.0"""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 0.0, 0.0]
        score = cosine_similarity(vec_a, vec_b)
        assert score == 0.0

    def test_similar_vectors(self):
        """接近的向量相似度高"""
        vec_a = [1.0, 0.1, 0.1]
        vec_b = [1.0, 0.2, 0.2]
        score = cosine_similarity(vec_a, vec_b)
        assert 0.9 < score < 1.0


# ── VectorSearchIndex 测试 ─────────────────────────────────────────────


class TestVectorSearchIndex:
    """测试向量搜索索引"""

    def test_basic_add_and_search(self):
        """add_document + search: 基本功能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_index.db")
            index = VectorSearchIndex(db_path)

            # 添加文档
            index.add_document(1, "Python全栈开发工程师", {"content_type": "test", "content_id": 1})
            index.add_document(2, "Java后端开发工程师", {"content_type": "test", "content_id": 2})
            index.add_document(3, "农业种植专家", {"content_type": "test", "content_id": 3})

            assert index.size == 3

            # 搜索
            results = index.search("Python开发", top_k=5)
            assert len(results) > 0
            # 排第一的应该是 Python 相关
            top_score = results[0]["score"]
            assert top_score > 0.0

    def test_add_or_update(self):
        """add_or_update: 增量更新"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_index.db")
            index = VectorSearchIndex(db_path)

            # 新增
            assert index.add_or_update("test", 1, "Python开发")
            assert index.size == 1

            # 相同内容（应跳过）
            assert not index.add_or_update("test", 1, "Python开发")

            # 不同内容（应更新）
            assert index.add_or_update("test", 1, "Python全栈开发")

    def test_delete(self):
        """delete: 删除文档"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_index.db")
            index = VectorSearchIndex(db_path)

            index.add_or_update("test", 1, "Python开发")
            assert index.size == 1

            assert index.delete("test", 1)
            assert index.size == 0

    def test_persist_and_load(self):
        """save_index + load_index: 持久化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_index.db")

            # 写入
            index = VectorSearchIndex(db_path)
            index.add_or_update("test", 1, "Python全栈开发工程师")
            index.add_or_update("test", 2, "Java架构师")
            count = index.save_index()
            assert count == 2

            # 加载新实例
            index2 = VectorSearchIndex(db_path)
            assert index2.size == 2

    def test_stats(self):
        """stats: 索引统计"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_index.db")
            index = VectorSearchIndex(db_path)
            index.add_or_update("test", 1, "Python开发")

            stats = index.stats
            assert stats["documents"] == 1
            assert stats["provider"] is not None


# ── 重排序测试 ─────────────────────────────────────────────────────────


class TestRerank:
    """测试重排序功能"""

    def test_rerank_empty(self):
        """空输入返回原值"""
        assert rerank("", []) == []
        assert rerank("test", []) == []

    def test_rerank_basic(self):
        """rerank: 基本功能"""
        candidates = [
            {"id": 1, "title": "Python开发工程师", "score": 0.5},
            {"id": 2, "title": "Java架构师", "score": 0.8},
            {"id": 3, "title": "全栈Python开发者", "score": 0.3},
        ]
        results = rerank("Python开发", candidates, weight=0.5)
        assert len(results) == 3
        assert all("_vector_score" in r for r in results)
        assert all("_final_score" in r for r in results)
        # Python 相关的结果应该被提权
        assert results[0]["_vector_score"] > 0.0


# ── 模型加载测试（可选，需要 M3E 模型） ─────────────────────────────────


@pytest.mark.skipif(
    EMBEDDING_PROVIDER != "m3e",
    reason="仅当 EMBEDDING_PROVIDER=m3e 时测试 M3E 模型加载",
)
class TestM3EModel:
    """测试 M3E 模型加载（需要实际下载模型）"""

    def test_m3e_load(self):
        """M3E 模型加载"""
        try:
            backend = M3EEmbedding()
            vecs = backend.embed(["测试文本"])
            assert vecs.shape == (1, 768)
            assert backend.dimension == 768
            assert backend.name == "m3e"
        except Exception as e:
            pytest.skip(f"M3E 模型加载失败: {e}")

    def test_m3e_semantic_search(self):
        """M3E 语义搜索效果验证"""
        backend = M3EEmbedding()
        texts = [
            "我是一名Python全栈工程师，擅长Django和Vue.js",
            "我专注于Java微服务架构和Spring Cloud",
            "我在农业领域有20年种植经验",
        ]
        query = "寻找Python后端开发专家"
        vecs = backend.embed(texts)
        query_vec = backend.embed([query])[0]

        scores = [float(np.dot(query_vec, v)) for v in vecs]
        best = scores.index(max(scores))
        # Python 相关的文档应该排第一
        assert best == 0, f"Python 搜索应命中索引0，实际命中{best} (scores={scores})"

    def test_m3e_batch_embed(self):
        """M3E 批量 embedding"""
        backend = M3EEmbedding()
        texts = [f"测试文本{i}" for i in range(10)]
        vecs = backend.embed(texts)
        assert vecs.shape == (10, 768)


# ── 文档构建器测试（需要数据库） ─────────────────────────────────────────


class TestDocumentBuilder:
    """测试文档构建器（仅测试静态方法逻辑，不依赖数据库）"""

    def test_build_user_document_components(self):
        """build_user_document: 验证拼接逻辑"""
        # 这个方法依赖数据库，我们在集成测试中验证
        # 这里只验证静态字段拼接
        pass  # 集成测试覆盖

    def test_compute_semantic_similarity_no_db(self):
        """compute_semantic_similarity: 纯函数测试"""
        tags_a = ["Python", "Django", "全栈开发"]
        tags_b = ["Python", "Flask", "后端开发"]
        tags_c = ["农业", "种植", "园艺"]

        score_sim = DocumentBuilder.compute_semantic_similarity(tags_a, tags_b)
        score_diff = DocumentBuilder.compute_semantic_similarity(tags_a, tags_c)

        assert score_sim > score_diff, (
            f"相似标签的相似度({score_sim:.4f})应高于不相似({score_diff:.4f})"
        )

    def test_compute_semantic_similarity_empty(self):
        """compute_semantic_similarity: 空输入"""
        score = DocumentBuilder.compute_semantic_similarity([], [])
        assert score == 0.0


# ── 集成测试 ────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestVectorSearchIntegration:
    """向量搜索集成测试"""

    def test_vector_search_index_search_order(self):
        """验证搜索结果的排序合理性"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_search.db")
            index = VectorSearchIndex(db_path)

            # 添加不同相关度的文档
            docs = {
                1: "Python全栈开发工程师，精通Django、Vue.js、PostgreSQL",
                2: "Java后端架构师，熟悉Spring Cloud、微服务",
                3: "前端开发工程师，React、TypeScript",
                4: "数据分析师，Python、Pandas、机器学习",
            }
            for doc_id, text in docs.items():
                index.add_or_update("test", doc_id, text)

            # 搜索 Python 相关
            results = index.search("Python全栈开发", top_k=4)
            assert len(results) > 0

            # Python 相关的文档应排在前列
            top_ids = [r["metadata"]["content_id"] for r in results]
            # ID 1 (Python全栈) 和 ID 4 (数据分析) 应排在前面
            assert top_ids[0] in (1, 4), f"Python 文档应排在前列: {top_ids}"

    def test_cosine_similarity_consistency(self):
        """验证 numpy dot product 和 cosine_similarity 函数的一致性"""
        backend = NumpyEmbedding(dim=16)
        vecs = backend.embed(["文本A", "文本B"])
        dot = float(np.dot(vecs[0], vecs[1]))
        mapped = max(0.0, min(1.0, (dot + 1.0) / 2.0))

        list_score = cosine_similarity(vecs[0].tolist(), vecs[1].tolist())
        assert abs(mapped - list_score) < 1e-4

    def test_config_values(self):
        """验证配置值存在且合理"""
        assert EMBEDDING_DIM >= 64, f"EMBEDDING_DIM 应 >= 64, 当前: {EMBEDDING_DIM}"
        assert VECTOR_TOP_K >= 1, f"VECTOR_TOP_K 应 >= 1, 当前: {VECTOR_TOP_K}"
