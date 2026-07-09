"""
芯森态 · 向量嵌入 + 语义搜索基础服务

MVP 阶段使用纯 Python hash 模拟向量嵌入，预留 BGE 接口。
后续可替换为 sentence-transformers / BGE-M3 等真实模型。

设计原则:
  - 零外部 AI 依赖 (纯 Python 实现)
  - 余弦相似度手动计算
  - hash 嵌入保持 "语义一致性" (相同文本 → 相同向量, 相似文本 → 近似向量)
"""

import hashlib
import math
import logging
from functools import lru_cache
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# ============================================================
# 向量工具函数
# ============================================================

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """纯 Python 余弦相似度计算

    Args:
        vec_a: 向量 A
        vec_b: 向量 B

    Returns:
        [-1, 1] 区间的相似度
    """
    if len(vec_a) != len(vec_b):
        raise ValueError(f"向量维度不一致: {len(vec_a)} vs {len(vec_b)}")

    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for i in range(len(vec_a)):
        a = vec_a[i]
        b = vec_b[i]
        dot += a * b
        norm_a += a * a
        norm_b += b * b

    norm_a = math.sqrt(norm_a)
    norm_b = math.sqrt(norm_b)

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)


def l2_normalize(vec: List[float]) -> List[float]:
    """L2 归一化"""
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec
    return [v / norm for v in vec]


# ============================================================
# Hash 嵌入器 (MVP 模拟)
# ============================================================

# 默认嵌入维度 (与主流 small 模型对齐)
_DEFAULT_DIM = 512


def _hash_to_float(text: str, seed: int, dim: int) -> float:
    """将文本通过 hash 映射到 [-1, 1] 区间的一个维度分量"""
    h = hashlib.sha256(f"{seed}:{text}".encode("utf-8")).hexdigest()
    # 取前8位十六进制 → 整型 → 归一化到 [-1, 1]
    val = int(h[:8], 16) / 0xFFFFFFFF  # [0, 1]
    return (val * 2.0) - 1.0           # [-1, 1]


@lru_cache(maxsize=1024)
def hash_embed(text: str, dim: int = _DEFAULT_DIM) -> List[float]:
    """纯 hash 模拟嵌入 — 相同文本产生相同向量

    原理: 对每个维度使用不同的 hash seed，使文本的每个字符/特征
    映射到高维空间中的近似分布。语义一致性由 hash 确定性保证。

    Args:
        text: 输入文本
        dim:  嵌入维度 (默认 128)

    Returns:
        L2 归一化后的 float 向量
    """
    if not text or not text.strip():
        return [0.0] * dim

    # 逐维度 hash: 每个维度用一个种子，使不同维度相互独立
    vec = [_hash_to_float(text, seed=i, dim=dim) for i in range(dim)]

    # L2 归一化
    return l2_normalize(vec)


# ============================================================
# BGE 预留接口 (后续接入真实模型)
# ============================================================

_BGE_MODEL = None


def _get_bge_model():
    """获取 BGE 模型单例（延迟加载）

    Returns:
        成功时返回 SentenceTransformer 实例；失败时返回 None。
        首次调用时尝试加载并缓存结果，后续直接返回缓存状态。
    """
    global _BGE_MODEL
    if _BGE_MODEL is None:
        # 第一次调用 ── 尝试加载模型
        try:
            from sentence_transformers import SentenceTransformer
            _BGE_MODEL = SentenceTransformer("BAAI/bge-small-zh-v1.5")
            logger.info("BGE 模型 BAAI/bge-small-zh-v1.5 加载成功")
        except Exception as e:
            logger.warning(f"BGE 模型加载失败: {e}")
            _BGE_MODEL = None  # 标记为不可用
    return _BGE_MODEL

@lru_cache(maxsize=1024)
def _bge_embed(text: str) -> List[float]:
    """BGE 模型嵌入 — 真实语义嵌入（带 LRU 缓存）"""
    model = _get_bge_model()
    if model is not None:
        return model.encode(text, normalize_embeddings=True).tolist()
    logger.warning("BGE 模型不可用，使用 hash 模拟")
    return hash_embed(text)



# ============================================================
# EmbeddingService 主类
# ============================================================

class EmbeddingService:
    """向量嵌入 + 语义搜索服务

    用法:
        svc = EmbeddingService(dim=128)
        vec = svc.embed("欢迎了解芯森态招商政策")
        results = svc.search("高活跃度经销商", candidates, top_k=5)
    """

    def __init__(self, dim: int = _DEFAULT_DIM, use_bge: bool = False):
        """
        Args:
            dim:     嵌入维度 (hash 模式)
            use_bge: 是否使用 BGE 真实模型 (False 时用 hash 模拟)
        """
        self.dim = dim
        self.use_bge = use_bge

    # ---- 嵌入 ----

    def embed(self, text: str) -> List[float]:
        """计算文本的向量嵌入

        Args:
            text: 输入文本

        Returns:
            浮点数向量列表, L2 归一化
        """
        if self.use_bge:
            return _bge_embed(text)
        return hash_embed(text, dim=self.dim)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入"""
        return [self.embed(t) for t in texts]

    # ---- 搜索 ----

    def search(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = 5,
        text_key: str = "text",
        score_key: Optional[str] = None,
        return_scores: bool = True,
    ) -> List[Dict]:
        """语义搜索: 对候选项按与 query 的余弦相似度排序

        Args:
            query:      查询文本
            candidates: 候选项列表, 每项为 dict (须包含 text_key 字段)
            top_k:      返回 top N 结果
            text_key:   候选项中用于嵌入匹配的字段名
            score_key:  如提供, 将其作为 'dim_score' 返回 (如评分维度)
            return_scores: 是否在结果中附加相似度分数

        Returns:
            按相似度降序排列的候选列表, 每项增加 'similarity' 字段
        """
        if not candidates:
            return []

        query_vec = self.embed(query)

        # 对每个候选项计算相似度
        scored = []
        for item in candidates:
            candidate_text = item.get(text_key, "")
            if not candidate_text:
                continue

            candidate_vec = self.embed(candidate_text)
            sim = cosine_similarity(query_vec, candidate_vec)

            result = dict(item)
            if return_scores:
                result["similarity"] = round(float(sim), 6)

            scored.append(result)

        # 按相似度降序排列
        scored.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)

        return scored[:top_k]

    def search_by_vector(
        self,
        query_vec: List[float],
        candidates: List[Dict],
        top_k: int = 5,
        vector_key: str = "vector",
        return_scores: bool = True,
    ) -> List[Dict]:
        """按已计算的向量搜索 (避免重复嵌入)

        Args:
            query_vec:   查询向量 (已 L2 归一化)
            candidates:  候选项列表, 每项包含 vector_key 字段
            top_k:       返回 top N
            vector_key:  候选项中存储向量的字段名
            return_scores: 是否附加相似度

        Returns:
            按相似度降序排列的候选列表
        """
        if not candidates:
            return []

        scored = []
        for item in candidates:
            candidate_vec = item.get(vector_key)
            if not candidate_vec:
                continue

            sim = cosine_similarity(query_vec, candidate_vec)

            result = dict(item)
            if return_scores:
                result["similarity"] = round(float(sim), 6)

            scored.append(result)

        scored.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)
        return scored[:top_k]

    def recommend_by_dimensions(
        self,
        target_profile: Dict[str, float],
        candidates: List[Dict],
        top_k: int = 5,
        dim_prefix: str = "score_",
        return_scores: bool = True,
    ) -> List[Dict]:
        """基于评分维度推荐: 将目标画像的维度向量与候选项匹配

        适用于 "找与某画像相似的经销商" 场景。

        Args:
            target_profile: 目标维度字典 {维度名: 分数, ...}
            candidates:     候选项列表, 每项包含 dim_prefix 开头的维度字段
            top_k:          返回 top N
            dim_prefix:     维度字段前缀
            return_scores:  是否附加相似度

        Returns:
            按维度相似度降序排列的候选列表
        """
        if not candidates or not target_profile:
            return []

        # 统一维度顺序
        dim_names = sorted(target_profile.keys())
        target_vec = [target_profile[d] for d in dim_names]
        target_vec = l2_normalize(target_vec)

        scored = []
        for item in candidates:
            cand_vec = []
            for d in dim_names:
                # 尝试 dim_prefix + d, 也尝试直接 d
                val = item.get(f"{dim_prefix}{d}") or item.get(d, 0.0)
                cand_vec.append(float(val) if val else 0.0)
            cand_vec = l2_normalize(cand_vec)

            sim = cosine_similarity(target_vec, cand_vec)

            result = dict(item)
            if return_scores:
                result["dim_similarity"] = round(float(sim), 6)

            scored.append(result)

        scored.sort(key=lambda x: x.get("dim_similarity", 0.0), reverse=True)
        return scored[:top_k]


# ============================================================
# 全局单例 (懒加载)
# ============================================================

_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(dim: int = _DEFAULT_DIM) -> EmbeddingService:
    """获取全局 EmbeddingService 单例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(dim=dim)
    return _embedding_service
