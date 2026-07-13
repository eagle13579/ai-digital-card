"""
AI数字名片 MMR 多样性模块单元测试
================================

测试覆盖:
  1. mmr_rerank — 核心 MMR 重排序
     - 基础功能 (返回全部/第一轮选相关性最高)
     - 极端 lambda 参数 (完全相关性 / 完全多样性)
     - 边界情况 (空列表 / 单元素 / top_n 截断)
     - 参数校验 (无效 lambda / 缺失 embedding / 维度不一致)
  2. batch_mmr_rerank — 批量处理
  3. compute_diversity_score — 多样性评估
  4. _cosine_similarity — 余弦相似度准确性
  5. MMRDiversityEngine — 异步包装类
"""

from typing import Any, Dict, List

import pytest

from app.ai.mmr_diversity import (
    MMRDiversityEngine,
    _build_similarity_matrix,
    _cosine_similarity,
    batch_mmr_rerank,
    compute_diversity_score,
    mmr_rerank,
)


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def simple_candidates() -> List[Dict[str, Any]]:
    """4个简单候选，向量分布在2D空间四个方向。"""
    return [
        {"id": "A", "embedding": [1.0, 0.0], "relevance_score": 0.9},
        {"id": "B", "embedding": [0.0, 1.0], "relevance_score": 0.8},
        {"id": "C", "embedding": [1.0, 1.0], "relevance_score": 0.7},
        {"id": "D", "embedding": [0.0, 0.0], "relevance_score": 0.6},
    ]


@pytest.fixture
def similar_candidates() -> List[Dict[str, Any]]:
    """3个高度相似的候选。"""
    return [
        {"id": "X1", "embedding": [1.0, 0.0, 0.0], "relevance_score": 0.95},
        {"id": "X2", "embedding": [0.98, 0.02, 0.0], "relevance_score": 0.90},
        {"id": "X3", "embedding": [0.96, 0.04, 0.0], "relevance_score": 0.85},
    ]


@pytest.fixture
def diverse_candidates() -> List[Dict[str, Any]]:
    """3个完全不同的候选（正交向量）。"""
    return [
        {"id": "A", "embedding": [1.0, 0.0, 0.0], "relevance_score": 0.9},
        {"id": "B", "embedding": [0.0, 1.0, 0.0], "relevance_score": 0.8},
        {"id": "C", "embedding": [0.0, 0.0, 1.0], "relevance_score": 0.7},
    ]


@pytest.fixture
def no_relevance_candidates() -> List[Dict[str, Any]]:
    """没有预计算 relevance_score 的候选（自动计算）。"""
    return [
        {"id": "A", "embedding": [1.0, 0.0]},
        {"id": "B", "embedding": [0.0, 1.0]},
        {"id": "C", "embedding": [0.5, 0.5]},
    ]


# ======================================================================
# 1. mmr_rerank — 基础功能
# ======================================================================


class TestMMRRerankBasic:
    """MMR 基础功能测试"""

    def test_returns_all_candidates(self, simple_candidates):
        """应当返回全部候选（未指定 top_n 时）"""
        result = mmr_rerank(simple_candidates, [1.0, 0.0], lambda_param=0.5)
        assert len(result) == 4

    def test_first_is_highest_relevance(self):
        """第一轮应当返回相关性最高的候选"""
        cand = [
            {"id": "A", "embedding": [1.0, 0.0], "relevance_score": 0.5},
            {"id": "B", "embedding": [0.0, 1.0], "relevance_score": 0.9},
            {"id": "C", "embedding": [1.0, 1.0], "relevance_score": 0.7},
        ]
        result = mmr_rerank(cand, [1.0, 0.0], lambda_param=0.5)
        assert result[0]["id"] == "B"  # B 相关性 0.9 最高

    def test_result_contains_mmr_score(self, simple_candidates):
        """每个结果应包含 mmr_score 字段"""
        result = mmr_rerank(simple_candidates, [1.0, 0.0], lambda_param=0.5)
        for item in result:
            assert "mmr_score" in item

    def test_result_contains_relevance_score(self, simple_candidates):
        """每个结果应包含 relevance_score 字段"""
        result = mmr_rerank(simple_candidates, [1.0, 0.0], lambda_param=0.5)
        for item in result:
            assert "relevance_score" in item

    def test_original_dict_not_mutated(self, simple_candidates):
        """不应修改原始候选字典"""
        original_ids = [c["id"] for c in simple_candidates]
        mmr_rerank(simple_candidates, [1.0, 0.0], lambda_param=0.5)
        assert [c["id"] for c in simple_candidates] == original_ids
        # 原始字典不应有 mmr_score
        for c in simple_candidates:
            assert "mmr_score" not in c

    def test_auto_compute_relevance(self, no_relevance_candidates):
        """没有预计算 relevance_score 时应当自动计算"""
        query = [1.0, 0.0]  # 与 A 完全一致, 与 C 部分匹配, 与 B 无关
        result = mmr_rerank(no_relevance_candidates, query, lambda_param=1.0)
        # lambda=1.0: 完全按相关性排序，A(与query一致) > C(部分匹配) > B(无关)
        assert result[0]["id"] == "A"
        assert result[-1]["id"] == "B"


# ======================================================================
# 2. mmr_rerank — lambda 参数行为
# ======================================================================


class TestMMRRerankLambda:
    """MMR lambda 参数行为测试"""

    def test_lambda_one_orders_by_relevance(self):
        """lambda=1.0 时完全按相关性降序"""
        cand = [
            {"id": "A", "embedding": [1.0, 0.0], "relevance_score": 0.3},
            {"id": "B", "embedding": [0.0, 1.0], "relevance_score": 0.9},
            {"id": "C", "embedding": [1.0, 1.0], "relevance_score": 0.6},
        ]
        result = mmr_rerank(cand, [1.0, 0.0], lambda_param=1.0)
        expected = ["B", "C", "A"]  # 按分数降序
        assert [r["id"] for r in result] == expected

    def test_lambda_zero_favors_diversity(self, similar_candidates):
        """lambda=0.0 时完全按多样性排序"""
        # 三个高度相似的候选，lambda=0 时会尽量选不同的
        result = mmr_rerank(
            similar_candidates, [1.0, 0.0, 0.0], lambda_param=0.0
        )
        # 第一轮选相关性最高的 X1 (0.95)
        assert result[0]["id"] == "X1"

    def test_lambda_zero_diverse_picks_different(self):
        """lambda=0.0 时 A 和 B(不同) 会被优先选择"""
        # A 与 B 正交（不同），A 与 C 相似
        cand = [
            {"id": "A", "embedding": [1.0, 0.0], "relevance_score": 0.9},
            {"id": "B", "embedding": [0.0, 1.0], "relevance_score": 0.4},
            {"id": "C", "embedding": [0.99, 0.01], "relevance_score": 0.3},
        ]
        result = mmr_rerank(cand, [1.0, 0.0], lambda_param=0.0)
        # 第一轮: A (最高分 0.9)
        # 第二轮: B (与 A 不相似) > C (与 A 高度相似)
        assert result[0]["id"] == "A"
        assert result[1]["id"] == "B"

    def test_lambda_half_balanced(self, simple_candidates):
        """lambda=0.5 时均衡兼顾相关性和多样性"""
        result = mmr_rerank(simple_candidates, [1.0, 0.0], lambda_param=0.5)
        # 第一轮: 相关性最高的 A (0.9)
        assert result[0]["id"] == "A"
        # 第二轮: 应当选择 B 或 D(与 A 不同) 而不是 C(与 A 相似)
        # D 分数最低 (0.6)，但与 A 完全正交; B 也完全正交(分数 0.8)
        # 综合: lambda=0.5 时
        # B: 0.5*0.8 - 0.5*0.0 = 0.4
        # D: 0.5*0.6 - 0.5*0.0 = 0.3
        # 所以 B 应该第二
        assert result[1]["id"] == "B"


# ======================================================================
# 3. mmr_rerank — 边界情况
# ======================================================================


class TestMMRRerankEdgeCases:
    """MMR 边界情况测试"""

    def test_empty_candidates(self):
        """空候选列表应返回空列表"""
        result = mmr_rerank([], [1.0, 0.0], lambda_param=0.5)
        assert result == []

    def test_single_candidate(self):
        """单候选应直接返回"""
        cand = [{"id": "X", "embedding": [1.0, 0.0], "relevance_score": 0.8}]
        result = mmr_rerank(cand, [1.0, 0.0], lambda_param=0.5)
        assert len(result) == 1
        assert result[0]["id"] == "X"
        assert result[0]["relevance_score"] == 0.8

    def test_top_n_returns_partial(self, simple_candidates):
        """top_n 应只返回前 N 个"""
        result = mmr_rerank(simple_candidates, [1.0, 0.0], lambda_param=0.5, top_n=2)
        assert len(result) == 2

    def test_top_n_greater_than_list(self, simple_candidates):
        """top_n 大于列表长度应全部返回"""
        result = mmr_rerank(simple_candidates, [1.0, 0.0], lambda_param=0.5, top_n=10)
        assert len(result) == 4

    def test_deterministic(self, simple_candidates):
        """相同输入应产生相同输出"""
        result1 = mmr_rerank(simple_candidates, [1.0, 0.0], lambda_param=0.5)
        result2 = mmr_rerank(simple_candidates, [1.0, 0.0], lambda_param=0.5)
        assert [r["id"] for r in result1] == [r["id"] for r in result2]

    def test_two_candidates(self):
        """两个候选应正确排序"""
        cand = [
            {"id": "A", "embedding": [1.0, 0.0], "relevance_score": 0.9},
            {"id": "B", "embedding": [0.0, 1.0], "relevance_score": 0.8},
        ]
        result = mmr_rerank(cand, [1.0, 0.0], lambda_param=0.5)
        assert len(result) == 2
        assert result[0]["id"] == "A"  # 相关性最高


# ======================================================================
# 4. mmr_rerank — 参数校验
# ======================================================================


class TestMMRRerankValidation:
    """MMR 参数校验测试"""

    def test_invalid_lambda_negative(self):
        """lambda 小于 0 应抛 ValueError"""
        with pytest.raises(ValueError, match="lambda_param"):
            mmr_rerank(
                [{"id": "A", "embedding": [1.0], "relevance_score": 0.9}],
                [1.0],
                lambda_param=-0.1,
            )

    def test_invalid_lambda_greater_than_one(self):
        """lambda 大于 1 应抛 ValueError"""
        with pytest.raises(ValueError, match="lambda_param"):
            mmr_rerank(
                [{"id": "A", "embedding": [1.0], "relevance_score": 0.9}],
                [1.0],
                lambda_param=1.1,
            )

    def test_missing_embedding_field(self):
        """候选缺少 embedding 字段应抛 ValueError"""
        with pytest.raises(ValueError, match="embedding"):
            mmr_rerank(
                [{"id": "A", "relevance_score": 0.9}],
                [1.0],
                lambda_param=0.5,
            )

    def test_vector_dimension_mismatch(self):
        """特征向量维度不一致应抛 ValueError"""
        with pytest.raises(ValueError, match="维度"):
            mmr_rerank(
                [
                    {"id": "A", "embedding": [1.0, 0.0], "relevance_score": 0.9},
                    {"id": "B", "embedding": [1.0], "relevance_score": 0.8},
                ],
                [1.0, 0.0],
                lambda_param=0.5,
            )

    def test_lambda_at_boundary_zero(self):
        """lambda=0.0 是合法边界值"""
        cand = [{"id": "A", "embedding": [1.0], "relevance_score": 0.9}]
        result = mmr_rerank(cand, [1.0], lambda_param=0.0)
        assert len(result) == 1

    def test_lambda_at_boundary_one(self):
        """lambda=1.0 是合法边界值"""
        cand = [{"id": "A", "embedding": [1.0], "relevance_score": 0.9}]
        result = mmr_rerank(cand, [1.0], lambda_param=1.0)
        assert len(result) == 1


# ======================================================================
# 5. batch_mmr_rerank
# ======================================================================


class TestBatchMMR:
    """批量 MMR 处理测试"""

    def test_batch_multiple_groups(self):
        """批量 MMR 应正确处理多个 group"""
        groups = [
            (
                [
                    {"id": "A", "embedding": [1.0, 0.0], "relevance_score": 0.9},
                    {"id": "B", "embedding": [0.0, 1.0], "relevance_score": 0.8},
                ],
                [1.0, 0.0],
            ),
            (
                [
                    {"id": "C", "embedding": [1.0, 0.0], "relevance_score": 0.7},
                    {"id": "D", "embedding": [0.0, 1.0], "relevance_score": 0.6},
                ],
                [1.0, 0.0],
            ),
        ]
        results = batch_mmr_rerank(groups, lambda_param=0.5)
        assert len(results) == 2
        assert len(results[0]) == 2
        assert len(results[1]) == 2
        assert results[0][0]["id"] == "A"
        assert results[1][0]["id"] == "C"

    def test_batch_empty_group(self):
        """批量处理中空的 group 应返回空列表"""
        groups = [
            ([], [1.0, 0.0]),
        ]
        results = batch_mmr_rerank(groups, lambda_param=0.5)
        assert len(results) == 1
        assert results[0] == []

    def test_batch_with_top_n(self):
        """批量处理支持 top_n 截断"""
        groups = [
            (
                [
                    {"id": "A", "embedding": [1.0, 0.0], "relevance_score": 0.9},
                    {"id": "B", "embedding": [0.0, 1.0], "relevance_score": 0.8},
                    {"id": "C", "embedding": [1.0, 1.0], "relevance_score": 0.7},
                ],
                [1.0, 0.0],
            ),
        ]
        results = batch_mmr_rerank(groups, lambda_param=0.5, top_n=2)
        assert len(results[0]) == 2


# ======================================================================
# 6. compute_diversity_score
# ======================================================================


class TestComputeDiversityScore:
    """多样性评估分数测试"""

    def test_identical_items_with_auto_sim(self):
        """完全相同的 embedding 多样性分数应为 0"""
        items = [
            {"embedding": [1.0, 0.0]},
            {"embedding": [1.0, 0.0]},
            {"embedding": [1.0, 0.0]},
        ]
        score = compute_diversity_score(items)
        assert score == pytest.approx(0.0, abs=1e-6)

    def test_orthogonal_items_with_auto_sim(self):
        """正交 embedding 多样性分数应为 1"""
        items = [
            {"embedding": [1.0, 0.0]},
            {"embedding": [0.0, 1.0]},
        ]
        score = compute_diversity_score(items)
        assert score == pytest.approx(1.0, abs=1e-6)

    def test_single_item(self):
        """单元素列表多样性分数应为 1"""
        score = compute_diversity_score([{"embedding": [1.0, 0.0]}])
        assert score == pytest.approx(1.0)

    def test_empty_list(self):
        """空列表多样性分数应为 1"""
        score = compute_diversity_score([])
        assert score == pytest.approx(1.0)

    def test_custom_similarity_fn(self):
        """自定义相似度函数应正常工作"""
        items = ["A", "B", "C"]

        def sim(a, b):
            return 1.0 if a == b else 0.0

        # A, B, C 互不相同，pair_count=3, 两两相似度=0
        score = compute_diversity_score(items, similarity_fn=sim)
        assert score == pytest.approx(1.0)

    def test_custom_similarity_fn_all_same(self):
        """自定义相似度函数: 全部相同"""
        items = ["A", "A", "A"]

        def sim(a, b):
            return 1.0

        score = compute_diversity_score(items, similarity_fn=sim)
        assert score == pytest.approx(0.0)

    def test_no_embedding_no_function(self):
        """没有 embedding 也没有自定义函数应返回 1.0"""
        items = ["A", "B", "C"]  # 纯字符串，没有 embedding
        score = compute_diversity_score(items)
        assert score == pytest.approx(1.0)

    def test_mixed_diversity(self):
        """半相似半不同的多样性分数应该在 (0, 1) 之间"""
        # A 与 B 正交, A 与 C 半相似, B 与 C 半相似
        items = [
            {"embedding": [1.0, 0.0]},  # A
            {"embedding": [0.0, 1.0]},  # B
            {"embedding": [0.7, 0.7]},  # C (与 A、B 都部分相似)
        ]
        score = compute_diversity_score(items)
        assert 0.0 < score < 1.0


# ======================================================================
# 7. _cosine_similarity
# ======================================================================


class TestCosineSimilarity:
    """余弦相似度准确性测试"""

    def test_identical_vectors(self):
        """相同向量的余弦相似度应为 1"""
        sim = _cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        assert sim == pytest.approx(1.0, abs=1e-6)

    def test_orthogonal_vectors(self):
        """正交向量的余弦相似度应为 0"""
        sim = _cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert sim == pytest.approx(0.0, abs=1e-6)

    def test_zero_vector(self):
        """零向量的余弦相似度应为 0"""
        sim = _cosine_similarity([0.0, 0.0], [1.0, 0.0])
        assert sim == pytest.approx(0.0)

    def test_both_zero_vectors(self):
        """两个零向量的余弦相似度应为 0"""
        sim = _cosine_similarity([0.0, 0.0], [0.0, 0.0])
        assert sim == pytest.approx(0.0)

    def test_partial_similarity(self):
        """部分相似的向量余弦值应在 (0, 1) 之间"""
        sim = _cosine_similarity([1.0, 0.0], [1.0, 1.0])
        # cos(45°) = 1/√2 ≈ 0.707
        assert sim == pytest.approx(0.70710678, abs=1e-6)

    def test_negative_values_clipped(self):
        """负余弦值应被裁剪到 0"""
        # 相反向量: cos(180°) = -1
        sim = _cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        assert sim == pytest.approx(0.0)


# ======================================================================
# 8. _build_similarity_matrix
# ======================================================================


class TestBuildSimilarityMatrix:
    """相似度矩阵构建测试"""

    def test_square_matrix(self):
        """应返回 n×n 矩阵"""
        embeddings = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
        matrix = _build_similarity_matrix(embeddings)
        assert len(matrix) == 3
        assert len(matrix[0]) == 3

    def test_diagonal_is_one(self):
        """对角线元素应为 1"""
        embeddings = [[1.0, 0.0], [0.0, 1.0]]
        matrix = _build_similarity_matrix(embeddings)
        assert matrix[0][0] == pytest.approx(1.0)
        assert matrix[1][1] == pytest.approx(1.0)

    def test_symmetric(self):
        """矩阵应对称"""
        embeddings = [[1.0, 0.0], [0.0, 1.0], [0.7, 0.7]]
        matrix = _build_similarity_matrix(embeddings)
        for i in range(3):
            for j in range(3):
                assert matrix[i][j] == pytest.approx(matrix[j][i])

    def test_zero_embedding(self):
        """含零向量的矩阵构建应正常"""
        embeddings = [[0.0, 0.0], [1.0, 0.0]]
        matrix = _build_similarity_matrix(embeddings)
        assert matrix[0][1] == pytest.approx(0.0)
        assert matrix[1][0] == pytest.approx(0.0)


# ======================================================================
# 9. MMRDiversityEngine — 异步包装类
# ======================================================================


class TestMMRDiversityEngine:
    """MMRDiversityEngine 异步包装类测试"""

    @pytest.mark.asyncio
    async def test_rerank_async(self):
        """异步 rerank 应正常工作"""
        engine = MMRDiversityEngine(lambda_param=0.5)
        cand = [
            {"id": "A", "embedding": [1.0, 0.0], "relevance_score": 0.9},
            {"id": "B", "embedding": [0.0, 1.0], "relevance_score": 0.8},
        ]
        result = await engine.rerank(cand, [1.0, 0.0])
        assert len(result) == 2
        assert result[0]["id"] == "A"

    @pytest.mark.asyncio
    async def test_rerank_with_override_lambda(self):
        """异步 rerank 支持覆盖 lambda_param"""
        engine = MMRDiversityEngine(lambda_param=0.5)
        cand = [
            {"id": "A", "embedding": [1.0, 0.0], "relevance_score": 0.9},
            {"id": "B", "embedding": [0.0, 1.0], "relevance_score": 0.8},
        ]
        result = await engine.rerank(cand, [1.0, 0.0], lambda_param=1.0)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_rerank_with_top_n(self):
        """异步 rerank 支持 top_n"""
        engine = MMRDiversityEngine(lambda_param=0.5)
        cand = [
            {"id": "A", "embedding": [1.0, 0.0], "relevance_score": 0.9},
            {"id": "B", "embedding": [0.0, 1.0], "relevance_score": 0.8},
        ]
        result = await engine.rerank(cand, [1.0, 0.0], top_n=1)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_compute_diversity_async(self):
        """异步 compute_diversity 应正常工作"""
        engine = MMRDiversityEngine()
        items = [
            {"embedding": [1.0, 0.0]},
            {"embedding": [0.0, 1.0]},
        ]
        score = await engine.compute_diversity(items)
        assert score == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_default_lambda_param(self):
        """MMRDiversityEngine 默认 lambda_param 应为 0.5"""
        engine = MMRDiversityEngine()
        assert engine.lambda_param == 0.5


# ======================================================================
# 10. 大规模/稳定性测试
# ======================================================================


class TestMMRStability:
    """MMR 稳定性与性能测试"""

    def test_100_candidates(self):
        """100个候选应快速完成排序"""
        n = 100
        cand = [
            {
                "id": f"item_{i}",
                "embedding": [1.0 if j == i % 10 else 0.0 for j in range(10)],
                "relevance_score": round(0.5 + 0.5 * (i / n), 4),
            }
            for i in range(n)
        ]
        import time

        start = time.time()
        result = mmr_rerank(cand, [1.0] * 10, lambda_param=0.5)
        elapsed = time.time() - start

        assert len(result) == n
        # 100个候选应在 2 秒内完成
        assert elapsed < 2.0, f"100候选排序耗时 {elapsed:.3f}s > 2s"

    def test_100_candidates_deterministic(self):
        """100个候选多次运行结果一致"""
        n = 100
        cand = [
            {
                "id": f"item_{i}",
                "embedding": [1.0 if j == i % 10 else 0.0 for j in range(10)],
                "relevance_score": round(0.5 + 0.5 * (i / n), 4),
            }
            for i in range(n)
        ]
        query = [1.0] * 10
        result1 = mmr_rerank(cand, query, lambda_param=0.5)
        result2 = mmr_rerank(cand, query, lambda_param=0.5)
        assert [r["id"] for r in result1] == [r["id"] for r in result2]
