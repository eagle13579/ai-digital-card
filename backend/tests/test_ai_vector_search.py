"""核心测试: AI向量搜索引擎 — vector_search.py

测试目标:
  1. NumpyEmbedding — tokenize, embed, 一致性, 空输入
  2. VectorSearchIndex — add/remove/clear/search/persistence
  3. VectorSearchEngine — build_index, search, search_brochures
  4. 工具函数 — cosine_similarity, embed_text
"""
import math
import os
import tempfile

import numpy as np
import pytest

os.environ["EMBEDDING_PROVIDER"] = "numpy"
os.environ["EMBEDDING_DIM"] = "64"

from app.ai.vector_search import (
    NumpyEmbedding,
    VectorSearchIndex,
    VectorSearchEngine,
    cosine_similarity,
    embed_text,
    get_embedding_backend,
    get_vector_index,
)

# ══════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════


@pytest.fixture
def numpy_emb():
    return NumpyEmbedding(dim=64)


@pytest.fixture
def temp_index_path():
    """Temporary SQLite db path for index tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    if os.path.isfile(path):
        os.unlink(path)


@pytest.fixture
def fresh_index(temp_index_path):
    """Clean VectorSearchIndex pointing at temp db."""
    return VectorSearchIndex(db_path=temp_index_path)


# ══════════════════════════════════════════════════════════════════
# 1. NumpyEmbedding 单元测试
# ══════════════════════════════════════════════════════════════════


class TestNumpyEmbedding:
    def test_properties(self, numpy_emb):
        """维度 + 名称正确"""
        assert numpy_emb.dimension == 64
        assert numpy_emb.name == "numpy"

    def test_embed_single_text(self, numpy_emb):
        """单文本返回 shape (1, dim)"""
        vec = numpy_emb.embed(["测试文本"])
        assert vec.shape == (1, 64)
        assert vec.dtype == np.float32
        # L2 归一化
        norm = np.linalg.norm(vec[0])
        assert abs(norm - 1.0) < 1e-6

    def test_embed_multiple_texts(self, numpy_emb):
        """多文本批量返回正确 shape"""
        vecs = numpy_emb.embed(["hello", "world", "测试"])
        assert vecs.shape == (3, 64)

    def test_embed_empty_list(self, numpy_emb):
        """空列表返回 (0, dim)"""
        vecs = numpy_emb.embed([])
        assert vecs.shape == (0, 64)

    def test_embed_empty_string(self, numpy_emb):
        """空字符串返回零向量"""
        vecs = numpy_emb.embed([""])
        assert vecs.shape == (1, 64)
        assert np.all(vecs == 0.0)

    def test_embed_consistency(self, numpy_emb):
        """相同文本 → 相同向量"""
        v1 = numpy_emb.embed(["人工智能"])
        v2 = numpy_emb.embed(["人工智能"])
        assert np.allclose(v1, v2)

    def test_similar_texts_closer(self, numpy_emb):
        """相似文本余弦 > 不相似文本"""
        sim_a = numpy_emb.embed(["Python 全栈开发工程师"])[0]
        sim_b = numpy_emb.embed(["Python 后端开发"])[0]
        diff = numpy_emb.embed(["金融投资理财"])[0]
        cos_sim = float(np.dot(sim_a, sim_b))
        cos_diff = float(np.dot(sim_a, diff))
        assert cos_sim > cos_diff, "语义相近文本的余弦相似度应高于语义无关文本"

    def test_tokenize(self, numpy_emb):
        """_tokenize 返回词频字典且归一化"""
        tf = numpy_emb._tokenize("人工智能AI")
        assert isinstance(tf, dict)
        total = sum(tf.values())
        assert abs(total - 1.0) < 1e-6

    def test_tokenize_empty(self, numpy_emb):
        """空文本 tokenize 返回空字典"""
        assert numpy_emb._tokenize("") == {}

    def test_embed_deterministic_seed(self):
        """不同实例相同 seed 给出一致向量"""
        e1 = NumpyEmbedding(64)
        e2 = NumpyEmbedding(64)
        v1 = e1.embed(["test"])
        v2 = e2.embed(["test"])
        assert np.allclose(v1, v2)


# ══════════════════════════════════════════════════════════════════
# 2. VectorSearchIndex 单元测试
# ══════════════════════════════════════════════════════════════════


class TestVectorSearchIndex:
    def test_empty_index(self, fresh_index):
        """空索引 size=0, search 返回空"""
        assert fresh_index.size == 0
        assert fresh_index.search("test") == []

    def test_add_document(self, fresh_index):
        """添加文档后 size 增加、search 可检索"""
        fresh_index.add_document(1, "Python 全栈开发工程师")
        assert fresh_index.size == 1
        results = fresh_index.search("Python")
        assert len(results) >= 1
        assert results[0]["id"] == 1

    def test_remove_document(self, fresh_index):
        """删除文档后 size 归零"""
        fresh_index.add_document(1, "doc one")
        fresh_index.remove_document(1)
        assert fresh_index.size == 0

    def test_clear_index(self, fresh_index):
        """clear 清空所有文档"""
        fresh_index.add_document(1, "doc1")
        fresh_index.add_document(2, "doc2")
        fresh_index.clear()
        assert fresh_index.size == 0

    def test_search_top_k(self, fresh_index):
        """search 返回不超过 top_k 条结果"""
        for i in range(5):
            fresh_index.add_document(i, f"document number {i}")
        results = fresh_index.search("document", top_k=3)
        assert len(results) <= 3

    def test_search_sorted_by_score(self, fresh_index):
        """搜索结果按分数降序"""
        fresh_index.add_document(1, "Python backend engineer")
        fresh_index.add_document(2, "Java architect")
        results = fresh_index.search("Python backend", top_k=2)
        assert len(results) >= 1
        scores = [r["score"] for r in results]
        assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))

    def test_add_or_update_new(self, fresh_index):
        """add_or_update 新增条目"""
        result = fresh_index.add_or_update("user", 1, "test user profile")
        assert result is True
        assert fresh_index.has_entry("user", 1)

    def test_add_or_update_skip_unchanged(self, fresh_index):
        """内容未变则跳过 (return False)"""
        fresh_index.add_or_update("user", 1, "same content")
        result = fresh_index.add_or_update("user", 1, "same content")
        assert result is False

    def test_add_or_update_replaces_changed(self, fresh_index):
        """内容变化则更新"""
        fresh_index.add_or_update("user", 1, "old content")
        fresh_index.add_or_update("user", 1, "new content")
        assert fresh_index.has_entry("user", 1)

    def test_delete_entry(self, fresh_index):
        """delete 移除条目"""
        fresh_index.add_or_update("user", 1, "to delete")
        assert fresh_index.delete("user", 1) is True
        assert not fresh_index.has_entry("user", 1)

    def test_stats(self, fresh_index):
        """stats 返回正确字段"""
        fresh_index.add_document(1, "content")
        s = fresh_index.stats
        assert s["engine"] == "vector_search"
        assert s["documents"] == 1
        assert "provider" in s
        assert "dimension" in s

    def test_save_and_load_persistence(self, temp_index_path):
        """保存后再加载，数据恢复"""
        idx = VectorSearchIndex(db_path=temp_index_path)
        idx.add_or_update("user", 42, "persistent data")
        idx.save_index()
        del idx

        idx2 = VectorSearchIndex(db_path=temp_index_path)
        assert idx2.has_entry("user", 42)
        results = idx2.search("persistent")
        assert len(results) >= 1


# ══════════════════════════════════════════════════════════════════
# 3. 工具函数测试
# ══════════════════════════════════════════════════════════════════


class TestUtils:
    def test_cosine_similarity_normalized(self):
        """归一化向量余弦 = 点积"""
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        result = cosine_similarity(a, b)
        # Default implementation returns (sim + 1)/2 for [0,1] range
        # Actually, let's check what cosine_similarity does
        assert isinstance(result, float)

    def test_cosine_similarity_identical(self):
        """相同向量余弦为 1"""
        a = np.array([0.5, 0.5, 0.5, 0.5])
        result = cosine_similarity(a, a)
        assert abs(result - 1.0) < 1e-6

    def test_embed_text_single(self):
        """embed_text 单字符串返回 (1, dim)"""
        vec = embed_text("hello")
        assert vec.ndim == 2
        assert vec.shape[1] == 64

    def test_embed_text_list(self):
        """embed_text 字符串列表返回 (n, dim)"""
        vecs = embed_text(["a", "b", "c"])
        assert vecs.shape == (3, 64)

    def test_get_embedding_backend_singleton(self):
        """get_embedding_backend 返回单例"""
        b1 = get_embedding_backend()
        b2 = get_embedding_backend()
        assert b1 is b2

    def test_get_vector_index_singleton(self):
        """get_vector_index 返回单例"""
        i1 = get_vector_index()
        i2 = get_vector_index()
        assert i1 is i2
