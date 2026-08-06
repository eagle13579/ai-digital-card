# zvec 架构分析文档

> 项目: 阿里巴巴开源高性能嵌入式向量数据库  
> 版本: 基于源码 master 分支分析  
> 分析时间: 2026-06-22  
> 用途: 白泽军团 Feature 库架构参考

---

## 一、架构全景图

```
┌─────────────────────────────────────────────────────────────────────┐
│                    语言绑定层 (Language Bindings)                     │
│  ┌───────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐    │
│  │  Python   │ │  Node.js │ │  Go    │ │  Rust  │ │  Dart    │    │
│  │  (PyBind) │ │          │ │        │ │        │ │          │    │
│  └─────┬─────┘ └──────────┘ └────────┘ └────────┘ └──────────┘    │
│        │  C API (zvec/c_api.h) — extern "C" 接口                    │
├────────┼───────────────────────────────────────────────────────────┤
│        ▼                                                           │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │              数据库层 (zvec::db) — 7 files                │     │
│  │                                                           │     │
│  │  Collection  (CreateAndOpen/Open/Insert/Query/Delete)     │     │
│  │  CollectionSchema / FieldSchema  (Schema定义与管理)        │     │
│  │  Doc / DocHelper  (文档模型, 序列化, 字段类型系统)          │     │
│  │  SearchQuery / MultiQuery / SubQuery / GroupByQuery       │     │
│  │  IndexParams (HNSW/IVF/FLAT/DiskAnn/Vamana/FTS/INVERT)   │     │
│  │  QueryParams / FtsState / Reranker (reranker::rerank)    │     │
│  │  Stats / Config / Options / Type / Status                 │     │
│  └──────────────────┬────────────────────────────────────────┘     │
│                     │                                              │
├─────────────────────┼─────────────────────────────────────────────┤
│                     ▼                                              │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │           核心引擎层 (zvec::core) — 30+ files              │     │
│  │                                                           │     │
│  │  ┌──────────────────────────────────────────────────┐     │     │
│  │  │        索引框架 (index_framework.h)               │     │     │
│  │  │                                                   │     │     │
│  │  │  IndexFactory  (全局工厂, 按名称创建所有组件)       │     │     │
│  │  │  IndexModule   (所有组件的基类, name+revision)      │     │     │
│  │  │  IndexFlow / IndexSparseFlow (稠密/稀疏搜索流)     │     │     │
│  │  │                                                   │     │     │
│  │  │  ┌─────────────┐  ┌──────────────┐               │     │     │
│  │  │  │ IndexRunner  │  │ IndexSearcher │               │     │     │
│  │  │  │ (运行器)     │  │ (搜索器)      │               │     │     │
│  │  │  └──────┬──────┘  └──────┬───────┘               │     │     │
│  │  │         │                │                         │     │     │
│  │  │  ┌──────┴──────┐  ┌──────┴───────┐               │     │     │
│  │  │  │IndexBuilder │  │IndexStreamer │               │     │     │
│  │  │  │(构建器)     │  │(流式写入)    │               │     │     │
│  │  │  └──────┬──────┘  └──────┬───────┘               │     │     │
│  │  │         │                │                         │     │     │
│  │  │  ┌──────┴──────┐  ┌──────┴───────┐               │     │     │
│  │  │  │IndexCluster │  │IndexConverter│               │     │     │
│  │  │  │(聚类)       │  │(格式转换)    │               │     │     │
│  │  │  └─────────────┘  └──────────────┘               │     │     │
│  │  └──────────────────────────────────────────────────┘     │     │
│  │                                                           │     │
│  │  ┌──────────────────────────────────────────────────┐     │     │
│  │  │        索引数据模型                                 │     │     │
│  │  │  IndexMeta      (数据类型/维度/元素大小)            │     │     │
│  │  │  IndexHolder    (训练数据持有者, OnePass/MultiPass) │     │     │
│  │  │  IndexProvider  (在线向量查询提供者)                │     │     │
│  │  │  IndexBundle    (索引序列化包, Trivial/Memory/MMap)│     │     │
│  │  │  IndexStorage   (持久化存储, Segment-based架构)    │     │     │
│  │  │  IndexMemory    (MemoryBlock 内存管理, 3种类型)    │     │     │
│  │  └──────────────────────────────────────────────────┘     │     │
│  │                                                           │     │
│  │  ┌──────────────────────────────────────────────────┐     │     │
│  │  │        索引算法组件                                │     │     │
│  │  │  IndexMetric     (距离度量: L2/IP/Cosine/...)     │     │     │
│  │  │  IndexTrainer    (训练器: 量化器/聚类训练)          │     │     │
│  │  │  IndexReformer   (向量格式转换器: 量化/反量化)      │     │     │
│  │  │  IndexReducer    (搜索结果归约器)                   │     │     │
│  │  │  IndexRefiner    (搜索结果精炼器)                   │     │     │
│  │  │  IndexFilter     (搜索结果过滤器)                   │     │     │
│  │  │  IndexDumper     (索引持久化输出器)                 │     │     │
│  │  └──────────────────────────────────────────────────┘     │     │
│  └──────────────────┬────────────────────────────────────────┘     │
│                     │                                              │
├─────────────────────┼─────────────────────────────────────────────┤
│                     ▼                                              │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │           加速引擎 (zvec::turbo) — 3+ files                │     │
│  │                                                           │     │
│  │  SIMD 加速内核:                                            │     │
│  │  - avx512_vnni/uniform_int8/  (统一int8量化距离计算)        │     │
│  │  - avx512_vnni/record_quantized_int8/  (逐记录int8量化)    │     │
│  │  - squared_euclidean.h / cosine.h / quantize.h            │     │
│  │  - turbo.h  (统一调度入口)                                  │     │
│  └──────────────────┬────────────────────────────────────────┘     │
│                     │                                              │
├─────────────────────┼─────────────────────────────────────────────┤
│                     ▼                                              │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │        算法基础设施层 (zvec::ailego) — 17 files             │     │
│  │                                                           │     │
│  │  ┌──────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐  │     │
│  │  │ 设计模式  │ │ 数据结构 │ │ 并行计算 │ │ 编码/存储    │  │     │
│  │  │ Factory  │ │ Vector  │ │ThreadPool│ │ JSON         │  │     │
│  │  │ Singleton│ │ Heap    │ │ThreadQ  │ │ MMapFile     │  │     │
│  │  │ Closure  │ │ Cube    │ │         │ │ CRC32C       │  │     │
│  │  │          │ │ Blob    │ │         │ │ File/IO      │  │     │
│  │  └──────────┘ └─────────┘ └─────────┘ └──────────────┘  │     │
│  └───────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

### 数据流: 写入路径

```
Python Collection.insert(docs)
  → _Collection.Insert() (C++ PyBind)
    → CollectionImpl::Insert() (db层验证+转换)
      → WAL日志写入 (持久化保证)
        → Segment追加 (按列存储到IndexStorage)
          → 触发IndexStreamer流式写入
            → IndexBuilder::TrainAndBuild() 后台异步构建
              → IndexDumper 持久化索引段
```

### 数据流: 查询路径

```
Python collection.query(Query(...), topk=10, filter="...")
  → QueryExecutor.execute() (Python组装MultiQuery/SubQuery)
    → _Collection.Query() (C++ PyBind)
      → CollectionImpl::Query()
        → MultiQuery解析 → 每个SubQuery独立执行
          → IndexFlow::search() 分发到具体的IndexSearcher
            → HNSWSearcher / IVFSearcher / FlatSearcher / ...
              → 距离计算: IndexMetric::distance() 调用SIMD内核
                → top-K结果收集
          → 多查询结果合并 + Reranker (RRF/Weighted/Callback)
            → 后过滤 (SQL表达式过滤)
              → 字段反查 (从Provider拿完整Doc)
                → 返回 DocPtrList
```

---

## 二、关键抽象

### 2.1 索引组件体系 (IndexModule 继承树)

```
IndexModule (基类: name_, revision_)
├── IndexRunner (运行器接口: search/add/cleanup/stats)
│   ├── IndexSearcher (搜索器: init/load/meta)
│   ├── IndexBuilder (构建器: init/train/build/dump)
│   ├── IndexStreamer (流式更新器)
│   └── IndexReducer (归约器)
├── IndexMetric (距离度量)
├── IndexCluster (聚类器)
├── IndexStorage (持久化存储)
├── IndexDumper (索引输出)
├── IndexConverter (格式转换)
├── IndexReformer (向量变换)
├── IndexTrainer (训练器)
├── IndexRefiner (精炼器)
└── IndexLogger (日志)
```

所有索引组件通过 `IndexFactory` 统一创建，使用 `INDEX_FACTORY_REGISTER_*` 宏注册。

### 2.2 数据持有者体系

```
IndexHolder (训练数据, 可单次/多次遍历)
├── OnePassNumericalIndexHolder<T> (单次遍历, list存储, 迭代即销毁)
├── MultiPassNumericalIndexHolder<T> (多次遍历, vector存储)
├── OnePassBinaryIndexHolder<T> (单次遍历, 二进制向量)
└── IndexHybridHolder (稠密+稀疏混合)

IndexProvider (在线查询, 通过key随机访问)
├── MultiPassNumericalIndexProvider<T> (数值向量查询)
├── MultiPassBinaryIndexProvider<T> (二进制向量查询)
└── IndexSparseProvider (稀疏向量查询)
```

### 2.3 存储体系: 三层内存管理

```
MemoryBlock (内存块: 3种类型)
├── MBT_MMAP        (mmap文件映射, 零拷贝)
├── MBT_BUFFERPOOL  (BufferPool缓存池, 引用计数管理)
└── MBT_HEAP_SCRATCH (堆分配临时缓冲区, 深拷贝语义)

IndexStorage (存储抽象)
├── Segment (数据段: read/write/fetch/resize/clone)
│   ├── MMapSegment (mmap映射段)
│   └── BufferSegment (BufferPool段)
└── IndexBundle (序列化包, 用于索引训练/持久化交互)
    ├── TrivialIndexBundle (内存map)
    ├── MemoryIndexBundle (字符串存储)
    └── MMapFileIndexBundle (文件mmap)
```

### 2.4 查询模型

```
QueryTarget (查询目标: 向量或全文)
├── VectorClause (稠密向量/稀疏向量查询)
└── FtsClause (全文检索查询)

SubQuery (子查询: target + num_candidates)
MultiQuery (多查询: 多个SubQuery + filter + reranker)
GroupByVectorQuery (分组查询: group_by_field + group_topk)

Reranker (重排序器)
├── RrfParams (RRF融合: 1/(k+rank+1))
├── WeightedParams (加权融合)
└── CallbackParams (用户回调)
```

### 2.5 索引类型体系

```
IndexParams (索引参数基类)
├── VectorIndexParams (向量索引基类: metric + quantize)
│   ├── HnswIndexParams (HNSW图索引)
│   ├── HnswRabitqIndexParams (HNSW + RaBitQ量化)
│   ├── IVFIndexParams (IVF倒排索引)
│   ├── FlatIndexParams (暴力搜索)
│   ├── DiskAnnIndexParams (磁盘ANN)
│   └── VamanaIndexParams (Vamana图索引)
├── InvertIndexParams (标量倒排索引)
└── FtsIndexParams (全文检索索引)
```

### 2.6 类型系统 (DataType)

```
DataType 枚举:
  基础标量: BOOL, INT8, INT16, INT32, INT64, UINT32, UINT64, FLOAT, DOUBLE, STRING, BINARY
  稠密向量: VECTOR_BINARY32, VECTOR_FP16, VECTOR_FP32, VECTOR_INT8, VECTOR_INT16
  稀疏向量: SPARSE_VECTOR_FP16, SPARSE_VECTOR_FP32
  数组类型: ARRAY_BINARY~ARRAY_DOUBLE

Doc::Value = variant<monostate, bool, int32_t, uint32_t, int64_t, uint64_t,
                     float, double, string, 各种vector<>, sparse_pair...>
```

---

## 三、可复用技术模式 / 设计模式 (6个)

### 模式1: 抽象工厂 + 宏注册 (AILEGO_FACTORY_REGISTER)

**位置**: `src/include/zvec/ailego/pattern/factory.h`  
**核心**: `Factory<TBase>` 模板类 + `AILEGO_FACTORY_REGISTER` 宏

**机制**:
- `Factory<TBase>` 是全局单例工厂, 内部持有 `map<const char*, function<TBase*()>>`
- `Factory<TBase>::Register<TImpl>` 内嵌类在静态初始化时自动向工厂注册
- `AILEGO_FACTORY_REGISTER(NAME, BASE, IMPL, ...)` 宏创建静态 Register 对象
- 使用 `__attribute__((used, retain))` 防止链接器裁剪
- 使用 `std::atomic<Factory*>` + 双重检查锁 确保跨DSO安全

**用法示例** (index_factory.h):
```cpp
INDEX_FACTORY_REGISTER_SEARCHER(HnswSearcher)
INDEX_FACTORY_REGISTER_METRIC(L2)
IndexFactory::CreateSearcher("HnswSearcher")  // 按名称创建
```

**评估**: 高度可复用。适合需要插件式扩展、按名称创建多态对象的系统。

**集成点**: 白泽军团若有按名称加载算法的需求 (如不同的检索策略、不同的模型后端), 可直接采用此模式。

---

### 模式2: 流水线架构 (IndexFlow)

**位置**: `src/include/zvec/core/framework/index_flow.h`  
**核心**: `IndexFlow` 类将搜索拆分为可替换的阶段

**流水线阶段**:
1. **Storage**: 数据从哪里来 (MMap/BufferPool/Heap)
2. **Reformer**: 向量如何变换 (量化/反量化/精度转换)
3. **Searcher**: 近邻搜索算法 (HNSW/IVF/Flat/DiskANN)
4. **Metric**: 距离如何计算 (L2/IP/Cosine, 含SIMD加速)
5. **User Reformer/Searcher/Metric**: 用户自定义覆盖

**特点**: 每个阶段可通过 `IndexFactory` 按名称替换, 实现算法组合的可插拔性。典型的 Strategy + Pipeline 模式。

**集成点**: 白泽军团的多阶段数据处理管道 (如: 文档解析 → 分块 → 向量化 → 索引) 可参考此架构。

---

### 模式3: 多态存储后端 (IndexStorage + MemoryBlock)

**位置**: `src/include/zvec/core/framework/index_storage.h`  
**核心**: Segment + MemoryBlock 抽象, 三种存储后端

| 后端 | 内存类型 | 适用场景 |
|------|---------|---------|
| MMapFileIndexBundle | MBT_MMAP | 大索引文件, 零拷贝读 |
| BufferPool | MBT_BUFFERPOOL | 内存受限, 引用计数淘汰 |
| TrivialIndexBundle | MBT_HEAP_SCRATCH | 临时数据, 小数据集 |

**MemoryBlock 的引用计数**:
- BufferPool块: `acquire_one()` / `release_one()` 管理引用
- Heap块: 深拷贝语义, 每个副本持有独立缓冲区
- MMap块: 裸指针, 由文件生命周期管理

**集成点**: 白泽军团需要多级存储 (内存+磁盘+缓存) 的产品可直接复用此抽象。

---

### 模式4: 查询结果融合框架 (Reranker)

**位置**: `src/include/zvec/db/reranker.h` + `python/zvec/extension/multi_vector_reranker.py`  
**核心**: `std::variant<RrfParams, WeightedParams, CallbackParams>` 类型安全的分发

**三种策略**:
1. **RRF (Reciprocal Rank Fusion)**: 无需分数标准化, 1/(k+rank+1)
2. **Weighted Fusion**: 按权重加权, 需距离标准化
3. **Callback (Python)**: 用户自定义逻辑

**Python 扩展**:
- `RrfReRanker`, `WeightedReRanker`, `CallbackReRanker` 均继承自 `RerankFunction`
- C++ 端通过 PyBind 暴露 `_reranker_rerank()` 函数
- 跨语言无缝调用

**集成点**: 白泽军团的多路召回融合 (向量+关键词+知识图谱) 可参考此模式。

---

### 模式5: 双阶段训练构建 (TrainAndBuild + TrainBuildAndDump)

**位置**: `src/include/zvec/core/framework/index_builder.h`  
**核心**: 静态方法组合训练/构建/持久化

```cpp
static int TrainAndBuild(const IndexBuilder::Pointer &builder,
                          IndexHolder::Pointer holder) {
    auto two_pass_holder = IndexHelper::MakeTwoPassHolder(std::move(holder));
    int ret = builder->train(two_pass_holder);
    if (ret == 0) {
        ret = builder->build(std::move(two_pass_holder));
    }
    return ret;
}

static int TrainBuildAndDump(const IndexBuilder::Pointer &builder,
                              IndexHolder::Pointer holder,
                              const IndexDumper::Pointer &dumper) {
    int ret = TrainAndBuild(builder, std::move(holder));
    if (ret == 0) {
        ret = builder->dump(dumper);
    }
    return ret;
}
```

**特点**: Template Method 模式的变体。`train()` 学习数据分布 (如k-means聚类), `build()` 构建索引结构 (如HNSW图), `dump()` 持久化。各Builder子类只需实现具体算法。

**集成点**: 白泽军团中任何需要"学习→构建→持久化"三步走的任务 (如模型训练、索引构建、知识库冷启动) 均可采用。

---

### 模式6: 跨DSO安全的原子化单例

**位置**: `src/include/zvec/ailego/pattern/factory.h` (Factory::Instance)  
**核心**: 解决动态库加载时的单例重复初始化问题

**问题背景**:
- Python extension (`_zvec.so`) 和 DiskANN plugin (`libzvec_diskann_plugin.so`) 需要共享同一个 Factory 实例
- 传统的 magic static `static Factory factory` 在不同DSO中有各自的 guard variable
- Plugin 加载时 guard 为0, 导致 Factory 被二次构造, 擦除已有注册

**解决方案**:
```cpp
static Factory *Instance(void) {
    static std::atomic<Factory *> ptr{nullptr};  // 无guard variable (常量初始化)
    Factory *cur = ptr.load(std::memory_order_acquire);
    if (cur) return cur;
    Factory *created = new Factory();
    if (ptr.compare_exchange_strong(cur, created, ...)) {
        return created;
    }
    delete created;
    return cur;
}
```

**核心要点**:
- `static std::atomic<T*>` 是常量初始化, 无 guard variable
- atomic 指针跨DSO共享 (STT_GNU_UNIQUE)
- double-checked locking + CAS 确保线程安全

**集成点**: 白泽军团若有 Plugin 架构 (主程序 + 动态库插件), 此模式防止单例重复初始化。

---

## 四、额外发现的设计洞见

### 4.1 Pass-Based 数据遍历设计
`IndexHolder` 分为 OnePass (消费即销毁) 和 MultiPass (可多次遍历), 用 `multipass()` 标志区分。训练流水线中, MakeTwoPassHolder 将 OnePass 转换为 MultiPass, 允许 train() 和 build() 各遍历一次。这种设计对大内存数据集至关重要。

### 4.2 稀疏/稠密向量统一查询路径
查询层 (`QueryTarget`) 通过 `std::variant<VectorClause, FtsClause>` 统一表达向量查询和全文检索。`IndexFlow` 和 `IndexSparseFlow` 并行处理两种向量类型。C++ 类型系统确保编译期类型安全分发。

### 4.3 Python 层 QueryExecutor 模式
Python SDK 的 `QueryExecutor` 封装了查询构建逻辑:
```
Query → SubQuery[] → MultiQuery → C++ Query → rerank → DocList
```
它将 Python 端 EmbeddingFunction (如 Qwen/OpenAI/SentenceTransformer) 生成的向量注入查询, 实现"用户输入文本 → 自动向量化 → 混合搜索 → 重排序"的端到端流程。

### 4.4 索引版本控制
`IndexModule` 基类包含 `revision_` 字段, `IndexRunner::Stats` 包含 `revision_id_`。版本号用于索引热更新和缓存失效判断。

### 4.5 插件系统的双重路径
核心引擎通过 `IndexPluginBroker` 管理动态库插件 (DiskAnn), 同时通过 `IndexFactory` 管理编译期注册的组件。前者用于外部扩展 (如不同的存储后端), 后者用于内部算法注册。

---

## 五、与白泽军团现有系统的集成点

### 集成点A: Embedding Function 扩展框架
**位置**: `python/zvec/extension/embedding_function.py`  
**方式**: Protocol 类定义 `embed(input) -> VectorType` 接口  
**可集成对象**: 白泽军团已有 Embedding 服务可直接实现 `DenseEmbeddingFunction` / `SparseEmbeddingFunction` Protocol  
**价值**: 零代码修改接入 zvec 的混合搜索链路; 复用白泽的模型路由、批处理、缓存机制

### 集成点B: Reranker 扩展框架
**位置**: `python/zvec/extension/multi_vector_reranker.py`  
**方式**: `RerankFunction` 基类 + `_reranker_rerank()` C++ 后端  
**可集成对象**: 白泽军团的自定义排序/过滤逻辑  
**价值**: 可在搜索管道中插入白泽的rerank模型 (如 cross-encoder, LLM-based reranker)

### 集成点C: 存储后端抽象 (IndexStorage + MemoryBlock)
**位置**: `src/include/zvec/core/framework/index_storage.h`  
**可集成对象**: 白泽军团已有的对象存储/S3/分布式文件系统  
**方式**: 实现 `IndexStorage` 子类, 接入 `IndexFactory` 注册  
**价值**: zvec 可存储到白泽存储基础设施, 而非仅本地文件系统

### 集成点D: SIMD 加速内核 (turbo)
**位置**: `src/turbo/`  
**可集成对象**: 白泽军团的距离计算、向量量化、评分函数  
**方式**: 复用或扩展 turbo 层的 SIMD 内核, 在白泽的计算引擎中直接调用  
**价值**: 共享经过业界验证的高性能向量计算实现

### 集成点E: 混合搜索管道编排
**位置**: `python/zvec/executor/query_executor.py` + `src/include/zvec/db/query.h`  
**可集成对象**: 白泽军团的多模态搜索、知识增强检索  
**方式**: SubQuery 列表支持任意数量、不同类型的查询子句, 结果通过 Reranker 融合  
**价值**: 原生支持"稠密向量 + 稀疏向量 + 全文检索 + SQL过滤"四路混合

### 集成点F: 工厂 + 宏注册模式 (代码基础设施)
**位置**: `src/include/zvec/ailego/pattern/factory.h`  
**可集成对象**: 白泽军团的算法注册、插件加载基础设施  
**价值**: 解决跨DSO单例问题, 提供编译期注册、运行时按名创建的能力

---

## 六、项目结构统计

| 目录 | 文件数 | 用途 |
|------|--------|------|
| src/include/zvec/ailego/ | 17 头文件 | 算法基础设施 (模式/容器/并行/编码/IO) |
| src/include/zvec/core/framework/ | 28+ 头文件 | 索引框架抽象基类体系 |
| src/include/zvec/core/interface/ | 5+ 头文件 | 对外接口常量/构建器 |
| src/include/zvec/db/ | 11 头文件 | 数据库层 (Collection/Schema/Doc/Query) |
| src/include/zvec/plugin/ | 1 头文件 | DiskAnn 插件接口 |
| src/include/zvec/turbo/ | 1 头文件 | SIMD 加速入口 |
| src/turbo/ | 3+ 头文件 | AVX512 VNNI SIMD 内核实现 |
| src/db/ | 7+ 源文件 | 数据库层实现 |
| python/zvec/ | 9 模块文件 | Python SDK |
| python/zvec/extension/ | 16 文件 | Embedding/Reranker 扩展 |
| python/zvec/executor/ | 2 文件 | 查询执行器 |
| python/zvec/model/ | 8+ 文件 | 数据模型 |
| python/zvec/typing/ | 1+ 文件 | 类型枚举 |

---

## 七、关键架构决策 (ADR)

1. **嵌入式架构**: 不部署独立服务, Collection 以文件系统路径打开, 进程内直接索引和查询
2. **列式存储**: 每列独立 IndexStorage Segment, 支持按需读取、部分加载
3. **WAL + 异步索引**: 写入先刷 WAL 保证持久性, 索引构建异步进行
4. **分段合并**: 每个 Segment 最多 10M 文档, 超过自动拆分; optimize() 触发合并
5. **C API 为核心**: 所有语言绑定通过 C API 对接, 而非直接暴露 C++ ABI
6. **运行时多态** vs **编译期模板**: 索引算法用虚函数多态 (灵活性), 数值容器用模板 (性能)
