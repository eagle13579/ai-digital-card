---
name: superpowers-zero-dep-vector-search
version: 1.0.0
description: Superpowers零依赖向量搜索引擎Feature — 纯Python TF-IDF向量化+BM25混合检索+种子索引构建+CLI+Web服务
created_at: 2026-07-05
atomic_models:
  - 零依赖设计哲学: numpy可选，纯Python TF-IDF兜底，无外部依赖
  - 双模向量化: numpy_tfidf(加速) / simple_tfidf(纯Python零依赖)
  - BM25混合检索: 关键词评分(alpha) + 向量语义评分(1-alpha) 混合排序
  - 种子索引预构建: 产品/大师/部门/角色预索引 + 增量加载
  - 稀疏/稠密双兼容: 支持numpy ndarray和Python dict两种向量表示
  - 即插即用三模式: CLI(--build/--query) + Python import + Flask Web API
entry_points:
  - layer: 知识检索
    trigger: 需要语义搜索/向量检索/混合搜索能力
    usage: "from vector_search import VectorSearchEngine; engine = VectorSearchEngine(); engine.build_index(docs); results = engine.search('query')"
  - layer: 嵌入式搜索
    trigger: 产品需要内置搜索但不想加外部依赖
    usage: "USE_VECTOR_SEARCH=1 EMBEDDING_MODE=simple_tfidf 开启搜索，零依赖"
products: []
applicable_domains:
  - 向量搜索
  - 知识检索
  - 混合搜索
  - 嵌入式搜索引擎
source: D:\superpowers\vector_search.py (570行)
