# 侦察报告 #2: 藏经知识库搜索架构现状

> 侦察时间: 2026-06-22
> 侦察目标: 藏经知识库 (keyword: 藏经, port: 5005)
> 产品根目录: D:\向海容的知识库\wiki\wiki\记忆宫殿\L5孵化室\产品开发
> 报告输出: D:\向海容的知识库\wiki\wiki\记忆宫殿\L5孵化室\五池\Feature库\zvec\

---

## 一、藏经≈大航海知识库 — 身份确认

通过 `_唤醒看板/skybridge.py` 和白泽控制台注册表确认：

| 字段 | 值 |
|------|-----|
| **keyword** | `藏经` |
| **name** | `大航海知识库` |
| **tagline** | 出海RAG问答系统 |
| **service** | `localhost:5005` |
| **command** | `python3 run_knowledge_base.py` |
| **desc** | 中韩出海数智港专属知识库，文档上传→RAG问答 |

**结论**: "藏经"是"大航海知识库"的快捷别名。同一个产品，同一个代码库。

---

## 二、搜索架构全景

### 2.1 代码仓库位置

| 仓库 | 路径 | 端口 |
|------|------|------|
| **大航海知识库 (藏经)** | `产品开发/大航海知识库/` | 5005 (实际日志显示曾在54676) |
| **企业知识库RAG (兄弟产品)** | `产品开发/企业知识库RAG/` | 5112 |
| **三级混合搜索引擎 (已归档)** | `产品开发/_archive/三级混合搜索+RRF融合引擎/` | 5041 |

### 2.2 文件结构 (大航海知识库)

```
大航海知识库/
├── acq_inject.py              # 客户获取引擎（无关搜索）
├── dark_reader_injector.py     # 暗色模式UI（无关搜索）
├── entropy_engine.py           # 熵审计引擎（无关搜索）
├── polaris_dashboard_sdk.py    # 北极星指标仪表板（含 search_hit_rate 指标）
├── wisdom_blueprint.py         # 经典智慧注入（简单关键词匹配，非核心）
├── atoms/                      # 认知原子定义
├── data/                       # 数据目录
├── static/                     # 静态资源
├── collection.db               # SQLite数据库
└── 价值判断报告.md             # 产品评估报告
```

### 2.3 搜索核心代码 (在企业知识库RAG中，被大航海知识库引用)

**关键文件清单：**

| 文件 | 行数 | 职责 |
|------|------|------|
| `simple_rag.py` | 478 | **核心检索引擎** — BM25 + TF-IDF + RRF混合搜索 |
| `rag_routes.py` | 94 | **搜索API路由** — /api/search, /api/rag/ask, /api/status |
| `app.py` | 487 | 主应用入口，注册rag_bp |
| `simple_kb_adapter.py` | 62 | MCP协议适配器，包装SimpleRAGEngine |
| `document_ingester.py` | 996 | 文档摄入管道（MarkItDown转换+分块） |
| `knowledge_organizer.py` | 1396 | 知识图谱引擎（LLM+规则混合实体抽取） |
| `feishu_kb_sync.py` | 409 | 飞书知识库双向同步 |

---

## 三、当前搜索技术栈

### 3.1 SimpleRAGEngine (simple_rag.py) — 核心引擎

```
SimpleRAGEngine
├── BM25搜索          (rank_bm25库, jieba分词)
├── TF-IDF搜索        (纯Python实现, 余弦相似度)
├── RRF融合排序       (Reciprocal Rank Fusion, k=60)
└── LLM问答           (可选DeepSeek API, 兜底混合搜索摘要)
```

**支持3种搜索模式:**
- `bm25` — 仅BM25关键词搜索
- `tfidf` — 仅TF-IDF余弦相似度
- `hybrid` (默认) — BM25 + TF-IDF + RRF融合

**搜索流程:**
```
用户查询 → jieba分词 → BM25评分 + TF-IDF余弦相似度
                    → RRF融合排序 → Top-K结果
                    → (可选) LLM生成回答
```

### 3.2 搜索API端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/search?q=关键词&top_k=5&mode=hybrid` | GET | 知识库搜索 |
| `/api/rag/ask` | POST | RAG问答 (JSON体: {question, top_k}) |
| `/api/status` | GET | 服务状态 |
| `/api/rag/health` | GET | 健康检查 |

### 3.3 数据源

1. **飞书知识库** — `feishu_kb_sync.py` 从 Feishu Wiki 同步文档到本地 `data/uploads/`
2. **本地上传** — 用户通过Web界面上传文档，保存到 `data/uploads/`
3. **内置FAQ** — 无文档时使用3条内置FAQ示例

### 3.4 搜索质量现状

| 方面 | 现状 |
|------|------|
| 检索方式 | 纯词法 (BM25 + TF-IDF)，**无向量语义检索** |
| 中文分词 | jieba |
| 排序融合 | RRF (k=60) |
| 重排序 | 无 (仅LLM可选) |
| 向量嵌入 | ❌ 无 |
| 语义搜索 | ❌ 无 |
| 知识图谱 | 有knowledge_organizer.py但未集成到搜索链路 |
| 持久化 | SQLite + JSON文件 |

---

## 四、已归档的"三级混合搜索+RRF融合引擎"

位置: `产品开发/_archive/三级混合搜索+RRF融合引擎/`

**设计目标**: BM25全文 + 向量语义 + 知识图谱 三级混合 → RRF融合

但此版本已归档（atoms中标记"已迁移到五池"），当前生产环境中**只有BM25+TF-IDF两级词法搜索**在运行。

---

## 五、zvec可替换的模块 (可替换性分析)

### 5.1 直接替换目标: SimpleRAGEngine

```python
# 当前 (simple_rag.py)
class SimpleRAGEngine:
    def __init__(self):
        self._bm25 = BM25Okapi(tokenized)     # 词法
        self._tfidf_vectors = [...]            # 词法TF-IDF
        self._vocab = {}                       # 词表

    def search(self, query, top_k, mode):
        if mode == 'bm25':   → 仅BM25
        if mode == 'tfidf':  → 仅TF-IDF
        if mode == 'hybrid': → BM25 + TF-IDF + RRF
```

**替换为zvec后:**
```python
# 目标 (zvec)
collection = zvec.create_and_open(path="./kb", schema=schema)
results = collection.query_multi(
    queries=[
        Query(field_name="embedding", vector=query_embedding),  # 语义
        Query(field_name="content", fts=Fts(match_string=q)),   # 关键词
    ],
    reranker=DefaultLocalReRanker(),  # 重排序
    topk=10,
)
```

**变更范围:**
1. `simple_rag.py` — 整个文件替换为zvec调用
2. `rag_routes.py` — 适配器层微调 (保持API兼容)
3. `simple_kb_adapter.py` — 适配器层微调
4. `app.py` — 初始化代码调整

### 5.2 替换可行性评估

| 维度 | 评估 | 说明 |
|------|------|------|
| **接口兼容** | 🟢 高 | rag_routes.py 只调 `engine.search()` 和 `engine.ask()`，接口易保持 |
| **功能覆盖** | 🟢 高 | zvec的FTS完全覆盖BM25，向量检索远超TF-IDF |
| **质量提升** | 🟢 显著 | 从纯词法→语义+词法混合+重排序，Recall大幅提升 |
| **迁移成本** | 🟡 中 | 需修改3-4个文件，新增embedding初始化代码 |
| **风险** | 🟢 低 | RAG场景有明确评估指标(Recall@K, MRR)，效果可量化 |

### 5.3 保持不变的部分

| 模块 | 原因 |
|------|------|
| `feishu_kb_sync.py` | 知识库同步逻辑，与检索无关 |
| `document_ingester.py` | 文档摄入管道，zvec不替代此功能 |
| `knowledge_organizer.py` | 知识图谱独立功能，可后续集成到zvec reranker |
| `rag_routes.py` (API层) | 只需微调，保持前端兼容 |
| `acq_inject.py` | 客户获取引擎，无关 |

---

## 六、zvec集成后搜索链路对比

### 当前 (SimpleRAG)
```
用户查询 → jieba分词 → BM25评分
                      → RRF融合 → Top-K
           jieba分词 → TF-IDF评分
                            ↓ (可选)
                     DeepSeek LLM → 生成回答
```

### 集成zvec后
```
用户查询 → DefaultLocalDenseEmbedding → 向量embedding
                                      → MultiQuery(向量+FTS)
         → jieba分词 → FTS检索(内置BM25)
                            ↓
                    DefaultLocalReRanker → 重排序
                            ↓
                    Top-K结果 → (可选) LLM生成回答
```

### 关键提升
1. **语义理解**: 从jieba词法匹配 → 向量语义匹配
2. **混合检索**: 词法+语义一次完成，RRF融合更成熟
3. **内置重排序**: DefaultLocalReRanker 二次精排
4. **进程内运行**: 无需外部数据库服务
5. **纯本地**: 数据安全可控

---

## 七、相关文件索引

### 大航海知识库 (藏经)
- `D:\向海容的知识库\wiki\wiki\记忆宫殿\L5孵化室\产品开发\大航海知识库\`
- 日志: `service_5005.log` (实际运行时端口54676)

### 企业知识库RAG (搜索代码实际所在)
- `D:\向海容的知识库\wiki\wiki\记忆宫殿\L5孵化室\产品开发\企业知识库RAG\`
- 核心搜索: `simple_rag.py` (478行)
- API路由: `rag_routes.py` (94行)
- 主入口: `app.py` (487行)
- KB适配器: `simple_kb_adapter.py` (62行)
- 文档摄入: `document_ingester.py` (996行)
- 知识图谱: `knowledge_organizer.py` (1396行)
- 飞书同步: `src/feishu_kb_sync.py` (409行)

### zvec (替换方案)
- `D:\向海容的知识库\wiki\wiki\记忆宫殿\L5孵化室\五池\Feature库\zvec\`
- `architecture.md` — zvec架构分析
- `features.yaml` — zvec功能特征
- `product-plan.md` — 产品集成方案 (含藏经知识库P0方案)

---

## 八、结论与建议

1. **藏经知识库** = **大航海知识库** (port 5005)，是面向中韩出海数智港的知识库RAG系统
2. **当前搜索纯词法** (BM25 + TF-IDF + RRF)，无向量语义检索，有较大提升空间
3. **zvec替换可行性高** — 接口优雅、功能超越、迁移成本低
4. **已有方案文档** — `product-plan.md` 已包含完整的集成方案
5. **建议作为P0优先实施** — 替换SimpleRAGEngine，获得语义+词法混合检索能力
