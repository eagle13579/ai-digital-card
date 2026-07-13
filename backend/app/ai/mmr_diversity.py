"""
AI数字名片 MMR（最大边际相关性）多样性重排序模块
=============================================

MMR（Maximal Marginal Relevance）是一种经典的多样性重排序算法，
在保持与查询(query)相关性的同时，最大化结果集合的多样性。

MMR 公式:
    MMR = argmax(λ · Rel(i) - (1-λ) · max_{j∈S} Sim(i, j))

    其中:
        Rel(i)       = item i 与 query 的相关性分数（余弦相似度）
        Sim(i, j)    = item i 与已选 item j 之间的相似度
        λ            = 多样性参数 [0, 1]
                       λ=1 完全按相关性排序, λ=0 完全按多样性排序
        S            = 已选中的结果集合

典型用途:
    - 匹配/推荐结果重排序：替换已有的简单排序逻辑
    - 搜索结果覆盖优化：确保结果覆盖 query 的不同方面
    - 名片推荐多样性：避免推荐过于相似的名片

移植来源:
    - 源项目: 链客宝 (chainke-full/backend/features/mmr_diversity.py)
    - 适配: AI数智名片 async/await 风格, FastAPI 项目结构
"""

from __future__ import annotations

import math
import statistics
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# ======================================================================
# 核心 MMR 排序函数
# ======================================================================


def mmr_rerank(
    candidates: List[Dict[str, Any]],
    query_embedding: List[float],
    lambda_param: float = 0.5,
    top_n: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """MMR 多样性重排序 — 在相关性基础上最大化结果多样性。

    每个候选必须包含 ``embedding`` 字段（特征向量），
    可选包含 ``relevance_score`` 字段（预计算相关性分数）。
    若未提供 ``relevance_score``，则自动用余弦相似度计算候选与 query 的相关性。

    Parameters
    ----------
    candidates : List[Dict[str, Any]]
        候选列表，每个元素为字典，至少包含:
        - ``embedding``: List[float] — 候选的特征向量
        - 可选 ``relevance_score``: float — 预计算的相关性分数
    query_embedding : List[float]
        查询的特征向量，用于计算与候选的相关性。
    lambda_param : float, default=0.5
        多样性参数，取值 [0, 1]:
        - 1.0 → 完全按相关性排序（无多样性）
        - 0.0 → 完全按多样性排序（忽略相关性）
        - 0.5 → 均衡模式
    top_n : int | None, default=None
        返回前 top_n 个结果，默认返回全部。

    Returns
    -------
    List[Dict[str, Any]]
        重排序后的候选列表，新增字段:
        - ``mmr_score``: float — 综合 MMR 分数
        - ``relevance_score``: float — 与 query 的相关性分数

    Raises
    ------
    ValueError
        - candidates 为空时
        - lambda_param 不在 [0, 1] 范围内
        - 候选缺少 embedding 字段
        - 特征向量维度不一致

    Examples
    --------
    >>> cand = [
    ...     {"id": 1, "embedding": [1.0, 0.0], "relevance_score": 0.9},
    ...     {"id": 2, "embedding": [0.0, 1.0], "relevance_score": 0.8},
    ...     {"id": 3, "embedding": [1.0, 1.0], "relevance_score": 0.7},
    ... ]
    >>> result = mmr_rerank(cand, [1.0, 0.0], lambda_param=0.5)
    >>> len(result) == 3
    True
    >>> result[0]["id"]  # 第一轮选相关性最高的
    1
    """
    # ── 输入校验 ──
    n = len(candidates)
    if n == 0:
        return []

    if not (0.0 <= lambda_param <= 1.0):
        raise ValueError(
            f"lambda_param 必须在 [0, 1] 范围内, 当前值: {lambda_param}"
        )

    # 验证每个候选包含 embedding 字段
    for i, cand in enumerate(candidates):
        if "embedding" not in cand:
            raise ValueError(
                f"candidates[{i}] 缺少 'embedding' 字段"
            )

    # 验证 embedding 维度一致
    dim = len(candidates[0]["embedding"])
    for i, cand in enumerate(candidates):
        if len(cand["embedding"]) != dim:
            raise ValueError(
                f"候选人[{i}] 的 embedding 维度 ({len(cand['embedding'])}) "
                f"与 candidates[0] ({dim}) 不一致"
            )

    # ── 计算/获取相关性分数 ──
    has_relevance = "relevance_score" in candidates[0]
    if has_relevance:
        # 使用预计算的相关性分数
        relevance = [cand["relevance_score"] for cand in candidates]
    else:
        # 用余弦相似度计算候选与 query 的相关性
        relevance = [
            _cosine_similarity(cand["embedding"], query_embedding)
            for cand in candidates
        ]

    # ── 预计算候选两两之间的余弦相似度矩阵 ──
    # 避免后续重复计算
    embeddings = [cand["embedding"] for cand in candidates]
    sim_matrix = _build_similarity_matrix(embeddings)

    def _sim_func(i: int, j: int) -> float:
        return sim_matrix[i][j]

    # ── MMR 贪婪选择 ──
    selected_indices: List[int] = []
    remaining_indices = list(range(n))

    # 已选集合大小 → 最大相似度缓存
    max_sim_to_selected: List[float] = [0.0] * n

    # 第一轮：选相关性最高的 item
    first_idx = max(remaining_indices, key=lambda i: relevance[i])
    selected_indices.append(first_idx)
    remaining_indices.remove(first_idx)

    # 更新剩余 item 到已选集的最大相似度
    for i in remaining_indices:
        max_sim_to_selected[i] = _sim_func(i, first_idx)

    # 后续轮次：按 MMR 分数选择
    while remaining_indices:
        best_idx = -1
        best_score = -math.inf

        for i in remaining_indices:
            mmr_score = (
                lambda_param * relevance[i]
                - (1.0 - lambda_param) * max_sim_to_selected[i]
            )
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i

        # 安全兜底（不应发生）
        if best_idx == -1:
            best_idx = remaining_indices[0]
            best_score = 0.0

        selected_indices.append(best_idx)
        remaining_indices.remove(best_idx)

        # 更新 max_sim_to_selected 缓存
        for i in remaining_indices:
            sim = _sim_func(i, best_idx)
            if sim > max_sim_to_selected[i]:
                max_sim_to_selected[i] = sim

    # ── 截断并组装结果 ──
    if top_n is not None and top_n < n:
        selected_indices = selected_indices[:top_n]

    result = []
    for idx in selected_indices:
        item = dict(candidates[idx])  # 复制一份，不修改原始数据
        item["mmr_score"] = round(
            lambda_param * relevance[idx]
            - (1.0 - lambda_param) * max_sim_to_selected[idx],
            6,
        )
        item["relevance_score"] = relevance[idx]
        result.append(item)

    return result


# ======================================================================
# 批量 MMR 处理
# ======================================================================


def batch_mmr_rerank(
    query_groups: List[Tuple[List[Dict[str, Any]], List[float]]],
    lambda_param: float = 0.5,
    top_n: Optional[int] = None,
) -> List[List[Dict[str, Any]]]:
    """批量执行 MMR 重排序（适用于多个 query 独立排序）。

    Parameters
    ----------
    query_groups : List[Tuple[List[Dict], List[float]]]
        每个 tuple: (candidates, query_embedding)
    lambda_param : float, default=0.5
        多样性参数。
    top_n : int | None, default=None
        每组返回 top_n 个结果。

    Returns
    -------
    List[List[Dict[str, Any]]]
        每组重排序后的结果列表。
    """
    results = []
    for candidates, query_embedding in query_groups:
        result = mmr_rerank(
            candidates=candidates,
            query_embedding=query_embedding,
            lambda_param=lambda_param,
            top_n=top_n,
        )
        results.append(result)
    return results


# ======================================================================
# 多样性评估指标
# ======================================================================


def compute_diversity_score(
    items: List[Any],
    similarity_fn: Optional[Callable[[Any, Any], float]] = None,
) -> float:
    """计算排序结果的平均多样性分数。

    定义为 ``1 - 平均两两相似度``。
    值越接近 1 表示结果越多样化，越接近 0 表示结果越相似。

    若 items 为包含 ``embedding`` 字段的字典列表且未提供
    ``similarity_fn``，则自动使用余弦相似度计算。

    Parameters
    ----------
    items : List[Any]
        排好序的候选列表。若包含 ``embedding`` 字段则自动计算。
    similarity_fn : Callable | None, default=None
        两两相似度函数，签名 ``fn(a, b) -> float``。
        若为 None 且 items 包含 embedding，则自动使用余弦相似度。

    Returns
    -------
    float
        [0, 1] 范围内的多样性分数，1 表示完全多样。

    Examples
    --------
    >>> items = [{"embedding": [1.0, 0.0]}, {"embedding": [0.0, 1.0]}]
    >>> compute_diversity_score(items)
    1.0
    """
    n = len(items)
    if n <= 1:
        return 1.0

    # 自动选择相似度计算方式（基于 embedding 字段）
    if similarity_fn is None and n > 0 and isinstance(items[0], dict) and "embedding" in items[0]:
        embeddings = [item["embedding"] for item in items]
        sim_matrix = _build_similarity_matrix(embeddings)
        # 直接使用预计算矩阵求平均相似度，避免闭包索引问题
        total_sim = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                total_sim += sim_matrix[i][j]
        pair_count = n * (n - 1) // 2
        avg_sim = total_sim / pair_count if pair_count > 0 else 0.0
        return 1.0 - avg_sim

    if similarity_fn is None:
        # 如果没有 embedding 也没有自定义函数，默认 0 相似度
        return 1.0

    total_sim = 0.0
    pair_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            total_sim += similarity_fn(items[i], items[j])
            pair_count += 1

    avg_sim = total_sim / pair_count if pair_count > 0 else 0.0
    return 1.0 - avg_sim


# ======================================================================
# 内部工具函数
# ======================================================================


def _cosine_similarity(
    vec_a: Sequence[float],
    vec_b: Sequence[float],
) -> float:
    """计算两个向量的余弦相似度。

    结果裁剪到 [0, 1] 范围以消除负值。

    Parameters
    ----------
    vec_a : Sequence[float]
        向量 A
    vec_b : Sequence[float]
        向量 B

    Returns
    -------
    float
        [0, 1] 范围内的余弦相似度。
    """
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(v * v for v in vec_a))
    norm_b = math.sqrt(sum(v * v for v in vec_b))

    norm_product = norm_a * norm_b
    if norm_product == 0.0:
        return 0.0

    # 裁剪到 [0, 1]（余弦值原本是 [-1, 1]，这里转成非负）
    raw = dot / norm_product
    # 对于 embedding 向量，通常都是非负的，但做一层保护
    return max(0.0, min(1.0, raw))


def _build_similarity_matrix(
    embeddings: Sequence[Sequence[float]],
) -> List[List[float]]:
    """预计算所有候选两两之间的余弦相似度矩阵。

    Parameters
    ----------
    embeddings : Sequence[Sequence[float]]
        所有候选的特征向量列表。

    Returns
    -------
    List[List[float]]
        n×n 相似度矩阵，sim_matrix[i][j] = cos_sim(embeddings[i], embeddings[j])
    """
    n = len(embeddings)
    # 预计算模长
    norms = [
        math.sqrt(sum(v * v for v in vec))
        for vec in embeddings
    ]

    matrix: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            if i == j:
                matrix[i][j] = 1.0
            else:
                sim = _cosine_similarity(embeddings[i], embeddings[j])
                matrix[i][j] = sim
                matrix[j][i] = sim
    return matrix


# ======================================================================
# 异步服务类（FastAPI 集成用）
# ======================================================================


class MMRDiversityEngine:
    """MMR 多样性重排序引擎（异步包装类）。

    提供 async 接口以便在 FastAPI 依赖注入中无缝使用。
    核心算法是同步的，此处仅做薄层包装。
    """

    def __init__(self, lambda_param: float = 0.5):
        """

        Parameters
        ----------
        lambda_param : float, default=0.5
            默认多样性参数。
        """
        self.lambda_param = lambda_param

    async def rerank(
        self,
        candidates: List[Dict[str, Any]],
        query_embedding: List[float],
        lambda_param: Optional[float] = None,
        top_n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """异步 MMR 重排序（薄包装，直接调用同步函数）。

        Parameters
        ----------
        candidates : List[Dict[str, Any]]
            候选列表。
        query_embedding : List[float]
            查询向量。
        lambda_param : float | None, default=None
            覆盖实例的默认 lambda_param。
        top_n : int | None, default=None
            返回前 top_n 个结果。

        Returns
        -------
        List[Dict[str, Any]]
            重排序后的候选列表。
        """
        return mmr_rerank(
            candidates=candidates,
            query_embedding=query_embedding,
            lambda_param=lambda_param if lambda_param is not None else self.lambda_param,
            top_n=top_n,
        )

    async def compute_diversity(
        self,
        items: List[Dict[str, Any]],
        similarity_fn: Optional[Callable[[Any, Any], float]] = None,
    ) -> float:
        """异步计算多样性分数。

        Parameters
        ----------
        items : List[Dict[str, Any]]
            候选列表。
        similarity_fn : Callable | None, default=None
            自定义相似度函数。

        Returns
        -------
        float
            多样性分数。
        """
        return compute_diversity_score(items, similarity_fn=similarity_fn)
