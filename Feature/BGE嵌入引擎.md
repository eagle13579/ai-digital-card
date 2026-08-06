---
id: feature-bge-embedding
name: BGE语义嵌入引擎
version: 1.0.0
created: 2026-07-09
status: stable
dependencies: [sentence-transformers>=5.6.0, torch>=2.0.0]
source: code/api/services/embedding_service.py
---

## 一句话定位
512维语义嵌入引擎，支持BGE真实模型 + hash fallback + LRU缓存

## 能力
- EmbeddingService.embed(text) → List[float] (512维)
- hash_embed(text) → 快速降级嵌入
- cosine_similarity(a, b) → 相似度
- search(query, items, top_k, text_key) → 排序结果
- 自动检测BGE模型可用性，不可用时降级hash

## 适用产品
所有需要语义搜索、文本相似度计算的产品

## 使用方式
```python
from api.services.embedding_service import get_embedding_service
svc = get_embedding_service(dim=512)
emb = svc.embed("芯森态AI招商")
results = svc.search("招商方案", items, top_k=3, text_key="desc")
```

## 部署要求
- sentence-transformers + torch 已安装
- BGE模型缓存: cache/modelscope/BAAI/bge-small-zh-v1___5
- 无GPU需求，CPU推理 ~30ms/条
