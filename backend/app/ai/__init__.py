"""AI 能力模块 - OCR 扫描 + NLP 提取 + DeepSeek 摘要 + 向量搜索"""

from app.ai.extractor import AIExtractor
from app.ai.ocr import OCRScanner
from app.ai.vector_search import (
    VectorSearchEngine,
    VectorSearchIndex,
    DocumentBuilder,
    EmbeddingBackend,
    NumpyEmbedding,
    M3EEmbedding,
    OpenAIEmbedding,
    DeepSeekEmbedding,
    get_embedding_backend,
    get_vector_index,
    embed_text,
    embed_single,
    rerank,
    cosine_similarity,
    sync_vector_index,
)

__all__ = [
    "AIExtractor",
    "OCRScanner",
    "VectorSearchEngine",
    "VectorSearchIndex",
    "DocumentBuilder",
    "EmbeddingBackend",
    "NumpyEmbedding",
    "M3EEmbedding",
    "OpenAIEmbedding",
    "DeepSeekEmbedding",
    "get_embedding_backend",
    "get_vector_index",
    "embed_text",
    "embed_single",
    "rerank",
    "cosine_similarity",
    "sync_vector_index",
]
