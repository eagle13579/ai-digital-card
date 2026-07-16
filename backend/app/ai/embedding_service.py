"""
AI数智名片 Embedding服务 — 三明治匹配管线在线层

基于 sentence-transformers 的本地 Embedding 服务。
提供 embed_text() / embed_batch() 接口，支持缓存已计算的 embedding。
"""

import hashlib
import logging
import os
import time
from collections import OrderedDict
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── 配置 ──
try:
    from app.config import settings as _settings
    EMBEDDING_MODEL = getattr(_settings, "EMBEDDING_MODEL", "BAAI/bge-m3")
    EMBEDDING_DIM = int(getattr(_settings, "EMBEDDING_DIM", 1024))
    EMBEDDING_CACHE_SIZE = int(getattr(_settings, "EMBEDDING_CACHE_SIZE", 10000))
except Exception:
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")
    EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", "1024"))
    EMBEDDING_CACHE_SIZE = int(os.environ.get("EMBEDDING_CACHE_SIZE", "10000"))


class LRUCache:
    """简单 LRU 缓存，用于 embedding 缓存"""
    def __init__(self, capacity: int = 10000):
        self._cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._capacity = capacity

    def get(self, key: str) -> Optional[np.ndarray]:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key: str, value: np.ndarray) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._capacity:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)


class EmbeddingService:
    """Embedding 服务 — 本地 sentence-transformers 模型"""
    def __init__(self, model_name: str = EMBEDDING_MODEL, cache_size: int = EMBEDDING_CACHE_SIZE):
        self._model_name = model_name
        self._model = None
        self._dim = EMBEDDING_DIM
        self._cache = LRUCache(capacity=cache_size)
        self._loaded = False

    def _load_model(self) -> None:
        if self._loaded:
            return
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"[EmbeddingService] Loading model: {self._model_name}")
            t0 = time.time()
            self._model = SentenceTransformer(self._model_name, device="cpu")
            test_vec = self._model.encode(["测试"], normalize_embeddings=True)
            self._dim = test_vec.shape[-1]
            self._loaded = True
            logger.info(f"[EmbeddingService] Model loaded: {self._model_name}, dim={self._dim}, took={time.time()-t0:.2f}s")
        except Exception as e:
            logger.error(f"[EmbeddingService] Model load failed: {e}, falling back to numpy")
            self._model = None
            self._loaded = True

    @staticmethod
    def _cache_key(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def embed_text(self, text: str) -> np.ndarray:
        """对单条文本生成 embedding"""
        if not text or not text.strip():
            return np.zeros(self._dim, dtype=np.float32)
        key = self._cache_key(text)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        self._load_model()
        if self._model is not None:
            vec = self._model.encode([text], normalize_embeddings=True)
            vec = np.asarray(vec[0], dtype=np.float32)
        else:
            rng = np.random.RandomState(abs(hash(text)) % (2**31))
            vec = rng.randn(self._dim).astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 1e-8:
                vec = vec / norm
        self._cache.put(key, vec)
        return vec

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """对批量文本生成 embedding"""
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        results = [None] * len(texts)
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []
        for i, text in enumerate(texts):
            stripped = text.strip() if text else ""
            if not stripped:
                results[i] = np.zeros(self._dim, dtype=np.float32)
                continue
            key = self._cache_key(stripped)
            cached = self._cache.get(key)
            if cached is not None:
                results[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(stripped)
        if uncached_texts:
            self._load_model()
            if self._model is not None:
                batch_vecs = self._model.encode(uncached_texts, normalize_embeddings=True)
                if hasattr(batch_vecs, "numpy"):
                    batch_vecs = batch_vecs.numpy()
                batch_vecs = np.asarray(batch_vecs, dtype=np.float32)
            else:
                batch_vecs = np.zeros((len(uncached_texts), self._dim), dtype=np.float32)
                for j, txt in enumerate(uncached_texts):
                    rng = np.random.RandomState(abs(hash(txt)) % (2**31))
                    v = rng.randn(self._dim).astype(np.float32)
                    norm = np.linalg.norm(v)
                    if norm > 1e-8:
                        v = v / norm
                    batch_vecs[j] = v
            for idx, vec in zip(uncached_indices, batch_vecs):
                results[idx] = vec
                self._cache.put(self._cache_key(uncached_texts[uncached_indices.index(idx)]), vec)
        return np.array(results, dtype=np.float32)

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def cache_size(self) -> int:
        return self._cache.size

    def clear_cache(self) -> None:
        self._cache.clear()
        logger.info("[EmbeddingService] Cache cleared")


_global_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取全局 EmbeddingService 单例"""
    global _global_embedding_service
    if _global_embedding_service is None:
        _global_embedding_service = EmbeddingService()
    return _global_embedding_service
