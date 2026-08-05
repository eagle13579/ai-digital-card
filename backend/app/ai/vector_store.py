"""
AI数智名片 向量数据库服务 — 三明治匹配管线在线层

基于 ChromaDB 的向量数据库封装，支持：
  - 增/删/查 操作
  - Collection 隔离（客户/供应商/经销商分开）
  - 持久化存储
  - 向量相似度搜索
"""

import logging
import os
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

VECTOR_STORE_DIR = os.environ.get(
    "VECTOR_STORE_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "vector_store"),
)

COLLECTION_NAMES = {
    "customers": "客户",
    "suppliers": "供应商",
    "dealers": "经销商",
}


class VectorStore:
    """向量数据库封装 — 基于 ChromaDB
    每个 collection 对应一种业务实体类型（客户/供应商/经销商）。
    """
    def __init__(self, persist_dir: str = VECTOR_STORE_DIR):
        self._persist_dir = persist_dir
        self._client = None
        self._collections: dict[str, "Collection"] = {}
        self._initialized = False

    def _init(self) -> None:
        if self._initialized:
            return
        try:
            import chromadb
            from chromadb.config import Settings
            os.makedirs(self._persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self._persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
            self._initialized = True
            logger.info(f"[VectorStore] ChromaDB 已初始化, persist_dir={self._persist_dir}")
        except Exception as e:
            logger.error(f"[VectorStore] ChromaDB 初始化失败: {e}")
            raise

    def _get_or_create_collection(self, name: str):
        if name not in COLLECTION_NAMES:
            raise ValueError(f"不支持的 collection: {name}，可用: {list(COLLECTION_NAMES.keys())}")
        if name in self._collections:
            return self._collections[name]
        self._init()
        try:
            collection = self._client.get_collection(name)
            logger.info(f"[VectorStore] 获取已有 collection: {name}")
        except Exception:
            collection = self._client.create_collection(
                name=name, metadata={"description": COLLECTION_NAMES[name]},
            )
            logger.info(f"[VectorStore] 创建 collection: {name}")
        self._collections[name] = collection
        return collection

    def add_item(self, collection_name: str, item_id: str | int, text: str,
                 embedding: list[float] | np.ndarray, metadata: dict = None) -> None:
        collection = self._get_or_create_collection(collection_name)
        str_id = str(item_id)
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        meta = metadata or {}
        meta["text"] = text
        meta["item_id"] = str_id
        try:
            existing = collection.get(ids=[str_id])
            if existing and existing["ids"]:
                collection.update(ids=[str_id], embeddings=[embedding], metadatas=[meta])
            else:
                collection.add(ids=[str_id], embeddings=[embedding], metadatas=[meta], documents=[text])
        except Exception as e:
            logger.error(f"[VectorStore] 添加失败 {collection_name}/{str_id}: {e}")
            raise

    def add_batch(self, collection_name: str, items: list[dict]) -> int:
        collection = self._get_or_create_collection(collection_name)
        ids, embeddings, metadatas, documents = [], [], [], []
        for item in items:
            str_id = str(item["id"])
            emb = item["embedding"]
            if isinstance(emb, np.ndarray):
                emb = emb.tolist()
            meta = item.get("metadata", {})
            meta["text"] = item["text"]
            meta["item_id"] = str_id
            ids.append(str_id)
            embeddings.append(emb)
            metadatas.append(meta)
            documents.append(item["text"])
        try:
            collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
            logger.info(f"[VectorStore] 批量添加 {len(ids)} 条到 {collection_name}")
            return len(ids)
        except Exception as e:
            logger.error(f"[VectorStore] 批量添加失败: {e}")
            raise

    def delete_item(self, collection_name: str, item_id: str | int) -> None:
        collection = self._get_or_create_collection(collection_name)
        collection.delete(ids=[str(item_id)])

    def search(self, collection_name: str, query_embedding: list[float] | np.ndarray,
               top_k: int = 10, include_metadata: bool = True) -> list[dict]:
        collection = self._get_or_create_collection(collection_name)
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["metadatas", "distances", "documents"],
            )
            output = []
            if results and results["ids"] and results["ids"][0]:
                for i, rid in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i] if results.get("distances") else 0.0
                    score = 1.0 / (1.0 + distance) if distance > 0 else 1.0
                    meta = {}
                    if include_metadata and results.get("metadatas") and results["metadatas"][0]:
                        meta = results["metadatas"][0][i] or {}
                    doc = ""
                    if results.get("documents") and results["documents"][0]:
                        doc = results["documents"][0][i] or ""
                    output.append({"id": rid, "text": doc or meta.get("text", ""),
                                   "score": round(score, 4), "metadata": meta})
            return output
        except Exception as e:
            logger.error(f"[VectorStore] 搜索失败 {collection_name}: {e}")
            raise

    def get_item(self, collection_name: str, item_id: str | int) -> Optional[dict]:
        collection = self._get_or_create_collection(collection_name)
        try:
            result = collection.get(ids=[str(item_id)])
            if result and result["ids"]:
                return {"id": result["ids"][0],
                        "text": result["documents"][0] if result.get("documents") else "",
                        "metadata": result["metadatas"][0] if result.get("metadatas") else {}}
            return None
        except Exception:
            return None

    def count(self, collection_name: str) -> int:
        try:
            return self._get_or_create_collection(collection_name).count()
        except Exception:
            return 0

    def list_collections(self) -> list[dict]:
        self._init()
        result = []
        for name, label in COLLECTION_NAMES.items():
            try:
                c = self._get_or_create_collection(name)
                cnt = c.count()
            except Exception:
                cnt = 0
            result.append({"name": name, "label": label, "count": cnt})
        return result

    def delete_collection(self, name: str) -> None:
        if name not in COLLECTION_NAMES:
            raise ValueError(f"不支持的 collection: {name}")
        self._init()
        try:
            self._client.delete_collection(name)
            if name in self._collections:
                del self._collections[name]
        except Exception as e:
            logger.error(f"[VectorStore] 删除 collection 失败 {name}: {e}")
            raise

    @property
    def persist_dir(self) -> str:
        return self._persist_dir


_global_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _global_vector_store
    if _global_vector_store is None:
        _global_vector_store = VectorStore()
    return _global_vector_store
