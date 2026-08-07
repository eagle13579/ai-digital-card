# 侦察报告：大航海知识库搜索架构现状

> 生成时间: 2026-06-22  
> 目标系统: 大航海知识库 (远航:5004)  
> 侦察范围: 企业知识库RAG + 大航海知识库

---

## 一、系统架构总览

```
┌─────────────────────────────────────────────────────────┐
│                 大航海知识库 (远航:5004)                   │
│                     Flask App (app.py)                    │
├─────────────────────────────────────────────────────────┤
│  继承自: 企业知识库RAG (src/ 完整模块)                     │
│  启动: run_knowledge_base.py → sys.path注入RAG src       │
├─────────────────────────────────────────────────────────┤
│  主要端点:                                               │
│  ├─ /api/search                    — 混合搜索           │
│  ├─ /api/rag/ask                   — RAG 问答           │
│  ├─ /api/documents/upload          — 文档上传           │
│  ├─ /api/status                    — 健康检查           │
│  ├─ /api/feishu/sync              — 飞书同步           │
│  └─ MCP / mcp_server              — 数字员工调用        │
└─────────────────────────────────────────────────────────┘
```

## 二、搜索引擎层 (5引擎)

### 1. BM25 全文搜索 — `bm25_search.py`
| 属性 | 值 |
|------|-----|
| 实现 | rank_bm25.BM25Okapi + 纯 Python 备用 |
| 分词 | jieba 中文分词 + 正则英文分词 |
| 参数 | k1=1.5, b=0.75 |
| 备用 | PurePythonBM25 (零依赖) |
| **状态** | ✅ 可用 |

### 2. TF-IDF 向量搜索 — `embeddings.py`
| 属性 | 值 |
|------|-----|
| 实现 | scikit-learn TfidfVectorizer |
| 备用 | PurePythonTfidfVectorizer (仅numpy) |
| 相似度 | 余弦相似度 (cosine_similarity) |
| 特征数 | max_features=10000 |
| **状态** | ✅ 可用 |
| **⚠️ 限制** | 非真实dense vector，中文按单字切分 |

### 3. RRF 混合搜索 v3 — `hybrid_search.py`
| 属性 | 值 |
|------|-----|
| 融合算法 | Reciprocal Rank Fusion (k=60) |
| 检索路数 | BM25 + TF-IDF + FTS5 (三路) |
| 查询重写 | LLM (DeepSeek) / 规则策略 |
| 同义词映射 | RAG, 向量, 分块, API, LLM等 |
| 代词消解 | 多轮对话上下文消歧 |
| **状态** | ✅ 可用 (v3最新版) |

### 4. OpenSpace 多策略融合 — `openspace_search.py`
| 属性 | 值 |
|------|-----|
| 策略数 | BM25 + TF-IDF + FTS5 (三路并行) |
| 融合模式 | RRF / 归一化加权 / 并集去重 / 自动选择 |
| 权重 | bm25=0.33, tfidf=0.33, fts5=0.34 |
| **状态** | ✅ 可用 |

### 5. SimpleRAG (备用) — `simple_rag.py`, `rag_routes.py`
| 属性 | 值 |
|------|-----|
| 用途 | 轻量备选RAG，通过 Blueprint 注册 |
| **状态** | ✅ 可用 (备用) |

## 三、重排序层

### ReRanker — `reranker.py`
| 策略 | 实现 | 说明 |
|------|------|------|
| LLM | DeepSeek API 逐条评分 | 最准确，较慢 |
| Cross-Encoder | BAAI/bge-reranker-v2-m3 | 本地快速 |
| Hybrid (推荐) | LLM + 特征加权融合 | 兼顾速度与质量 |
| **默认** | hybrid | 可配置 (config.yaml) |
| **状态** | ✅ 可用 |

## 四、场景适配层

### SceneAdapter — `scene_adapter.py`
| 场景 | 描述 | 搜索策略调整 |
|------|------|------------|
| 合规查询 | 法规/税务/用工 | top_k↑, BM25优先 |
| 技术问答 | API/代码/架构 | openspace搜索 |
| 流程咨询 | SOP/操作步骤 | top_k中, 精确匹配 |
| 日常 | 普通咨询 | hybrid默认 |
| **状态** | ✅ 可用 (纯规则，零LLM) |

## 五、存储层

### DocumentStore — `storage.py`
```
数据库: data/knowledge_base.db
引擎:   SQLite + FTS5
模式:   WAL (并发)

表结构:
├─ documents     — 文档元数据 + 完整内容
├─ chunks        — 分块内容 + 向量(pickle序列化blob)
├─ chunks_fts    — FTS5虚拟表 (全文检索)
├─ teams         — 团队管理
├─ team_members  — 团队成员
└─ document_permissions — 文档权限
```

| 属性 | 值 |
|------|-----|
| 当前数据量 | **空库** (documents=0, chunks=0) |
| 向量存储 | pickle序列化存入blob字段 |
| **⚠️ 限制** | 无独立向量数据库 |

## 六、MCP 协议层

### MCPServer — `mcp_server.py`
| 模式 | 说明 |
|------|------|
| stdio | 数字员工CLI嵌入 |
| SSE (HTTP) | 远程调用 (Starlette+Uvicorn) |
| 工具数 | 5个: search_knowledge, ask_question, list_documents, get_document, get_knowledge_status |
| 搜索模式 | hybrid / bm25 / tfidf |
| **状态** | ✅ 可用 |

## 七、LLM 集成

| 组件 | 详情 |
|------|------|
| 模型 | DeepSeek Chat (deepseek-chat) |
| API | https://api.deepseek.com |
| 用途 | 回答生成, 查询重写, ReRank评分 |
| 降级 | API不可用时回退到摘要模式 |
| **状态** | ⚠️ 需要 DEEPSEEK_API_KEY 环境变量 |

## 八、当前问题与风险

### 🔴 关键问题
1. **知识库为空** — `knowledge_base.db` 有库无表，数据量为0
2. **无真实向量嵌入** — 使用 TF-IDF 替代 dense vector embedding，中文检索精度有限
3. **无独立向量数据库** — 向量以 pickle blob 存 SQLite，非生产方案

### 🟡 增强机会
1. `embeddings.py` — 可接入 sentence-transformers / bge 等真实嵌入模型
2. `storage.py` — 向量存储可替换为 faiss / chromadb / qdrant
3. `hybrid_search.py` — 可集成向量检索作为第四路 (当前只有BM25+TF-IDF+FTS5)
4. `reranker.py` — Cross-Encoder 模型当前只声明未实际加载 (需下载模型权重)
5. 查询重写模块的 LLM 策略依赖 DeepSeek API，可在本地用小模型替代

### 🟢 已有优势
1. 三路并行检索 (BM25+TF-IDF+FTS5) + RRF融合，架构设计合理
2. 查询重写 + ReRanker + SceneAdapter 形成完整RAG流水线
3. MCP 协议支持数字员工调用
4. 纯 Python 实现，无外部向量数据库依赖 (部署简单)

## 九、模块清单与替换优先级

| 模块 | 文件 | 当前技术 | 建议替换/增强 | 优先级 |
|------|------|---------|--------------|--------|
| embeddings | `src/embeddings.py` | TF-IDF (sklearn/numpy) | 接入dense vector嵌入 | P0 |
| storage | `src/storage.py` | SQLite + pickle blob | 向量独立存储 (faiss/chroma) | P1 |
| hybrid_search | `src/hybrid_search.py` | BM25+TF-IDF+FTS5 | 加入向量检索作为第四路 | P1 |
| reranker | `src/reranker.py` | DeepSeek/Cross-Encoder | 优化Cross-Encoder加载 | P2 |
| scene_adapter | `src/scene_adapter.py` | 规则分类 | 可升级为LLM分类 | P3 |

## 十、关键文件路径

```
大航海知识库 (运行实例):
├─ 产品开发/大航海知识库/
│  ├─ run_knowledge_base.py              ← 启动入口
│  ├─ collection.db                       ← 飞书集合缓存(空)
│  ├─ wisdom_blueprint.py                 ← 经典智慧注入
│  ├─ entropy_engine.py                   ← 熵审计
│  ├─ polaris_dashboard_sdk.py            ← 北极星指标
│  └─ acq_inject.py                       ← 客户获取引擎

大航海知识库 (实际数据目录):
├─ 产品开发/出海项目/中韩出海数智港/22_大航海/大航海知识库/
│  ├─ run_knowledge_base.py               ← 实际启动入口
│  ├─ src/app.py                          ← 独立API入口(继承RAG)
│  ├─ src/feishu_kb_sync.py               ← 飞书同步
│  ├─ data/knowledge_base.db              ← 主数据库(空)
│  └─ data/seeds/                         ← 种子文档
│  └─ data/uploads/                       ← 上传文档(飞书同步)

企业知识库RAG (核心引擎):
├─ 产品开发/企业知识库RAG/
│  ├─ app.py                              ← Flask Web MVP
│  └─ src/
│     ├─ __init__.py                      ← 模块导出
│     ├─ api.py                           ← Flask API端点
│     ├─ app_factory.py                   ← 统一应用工厂
│     ├─ document_api.py                  ← KnowledgeBaseAPI
│     ├─ bm25_search.py                   ← BM25引擎
│     ├─ embeddings.py                    ← TF-IDF向量引擎
│     ├─ hybrid_search.py                 ← RRF混合引擎
│     ├─ openspace_search.py              ← 多策略融合引擎
│     ├─ storage.py                       ← SQLite存储
│     ├─ reranker.py                      ← 重排序引擎
│     ├─ scene_adapter.py                 ← 场景适配器
│     ├─ mcp_server.py                    ← MCP协议服务器
│     ├─ rag_api.py                       ← RAG问答引擎
│     ├─ config.py                        ← 配置管理
│     └─ llm_client.py                    ← DeepSeek客户端
```

---

*报告完毕 — 大航海知识库搜索架构采用纯Python三层RAG管道 (检索→重排序→生成)，当前为空库状态，具备完整的混合搜索能力但缺乏真实向量嵌入。*
