# AI数智名片 — AI引擎架构深度分析报告

> **分析者**: 天吴 (Bai Ze Legion, P8)  
> **分析日期**: 2026-07-14  
> **项目路径**: `D:\AI数智名片\backend\app\ai\`  
> **代码量**: ~25个模块，约15,000+ 行 Python

---

## 一、AI引擎全景架构

### 1.1 分层架构总览

```
┌──────────────────────────────────────────────────────────────────────┐
│                      API / Route Layer (FastAPI)                     │
├──────────────────────────────────────────────────────────────────────┤
│                     AI Gateway Layer (统一协议)                       │
│  AIGatewayProtocol ← DirectAIGateway / CachedAIGateway /            │
│                         FallbackAIGateway                            │
│  ModelRegistryProtocol / AIMetricsProviderProtocol                    │
├──────────────────────────────────────────────────────────────────────┤
│                   AI 能力中间层 (业务逻辑)                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │
│  │ OCR  │ │NLP/  │ │ RAG  │ │知识   │ │编码  │ │优化   │            │
│  │      │ │提取  │ │管道  │ │图谱   │ │助手  │ │分析   │            │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘            │
├──────────────────────────────────────────────────────────────────────┤
│               推荐 & 反馈引擎层                                       │
│  ┌────────┐ ┌───────────┐ ┌─────────┐ ┌────────┐ ┌───────────┐     │
│  │推荐引擎│ │反馈闭环    │ │在线学习  │ │Bandit  │ │ A/B测试   │     │
│  └────────┘ └───────────┘ └─────────┘ └────────┘ └───────────┘     │
├──────────────────────────────────────────────────────────────────────┤
│                盖娅进化系统 (自学习/自演化)                             │
│  ┌────────────────┐ ┌──────────────┐ ┌──────────────────────┐      │
│  │ GaiaEvolution  │ │ GaiaTrainer  │ │ GaiaFlywheel (飞轮)  │      │
│  │ Brain          │ │ (训练管线)    │ │ (定时自动演化)       │      │
│  └────────────────┘ └──────────────┘ └──────────────────────┘      │
├──────────────────────────────────────────────────────────────────────┤
│               基础设施层                                              │
│  向量索引(SQLite)   Embedding后端(M3E/numpy/API)  模型注册/推理     │
│  缓存(Redis)        SQLite持久化                  Cron调度            │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.2 模块依赖关系

```
ai/
├── __init__.py                    # Lazy imports (防循环依赖)
├── ocr.py                         # ← 独立模块
├── extractor.py                   # ← 依赖 DeepSeek API
├── vector_search.py               # ← 核心依赖: embedding + SQLite
├── rag_pipeline.py                # ← 依赖 vector_search + DeepSeek API
├── knowledge_graph.py             # ← 独立, 读 DB
├── recommendation.py              # ← 核心编排:
│                                   #   → vector_search (语义)
│                                   #   → knowledge_graph (图谱)
│                                   #   → feedback_loop (反馈)
│                                   #   → online_learning (权重)
├── feedback_loop.py               # ← SQLite 持久化
├── online_learning.py             # ← 依赖 feedback_loop
├── bandit_engine.py               # ← 独立, Thompson Sampling
├── ab_testing.py                  # ← 独立, 统计检验
├── writing_assistant.py           # ← 依赖 DeepSeek API
├── optimization.py                # ← 独立, 规则引擎
├── gaia_evolution_brain.py        # ← 核心编排:
│                                   #   → vector_search (索引)
│                                   #   → gaia 模型表 (DB)
├── gaia_trainer.py                # ← 依赖 gaia_evolution_brain
├── gaia_flywheel.py               # ← 编排 brain + trainer
├── model_registry.py              # ← SQLite 持久化
├── model_serving.py               # ← MLX/HF/ST 三层降级
├── training_pipeline.py           # ← 代码→ChatML 转换
├── knowledge_model_service.py     # ← 心智模型管理
├── mcp_adapter.py                 # ← MCP协议 → DesignQA
├── cron/
│   ├── learning_cron.py           # ← 定时触发在线学习
│   └── design_qa_cron.py          # ← 定时审核设计条目
├── gateway/
│   ├── interfaces.py              # ← 协议定义 (Protocol)
│   ├── __init__.py
│   └── adapters/
│       ├── direct_api_adapter.py  # ← DeepSeek 直连
│       ├── cached_gateway_adapter.py  # ← 缓存+限流+熔断
│       └── fallback_gateway_adapter.py # ← 降级链
```

---

## 二、各模块深度分析

### 2.1 向量搜索引擎 (`vector_search.py`) — 核心基础设施

| 维度 | 当前实现 | 状态 |
|------|---------|------|
| Embedding后端 | M3E (本地, 768维) / numpy (降级) / OpenAI / DeepSeek | ✅ 完善 |
| 索引存储 | SQLite (BLOB序列化) + 内存双重结构 | ✅ 完善 |
| 搜索方式 | 余弦相似度 (暴力全量) | ⚠️ 无近似NN |
| 增量更新 | add_or_update() 支持 | ✅ 完善 |
| 重排序 | 基础 rerank 函数 | ⚠️ 简单 |

**代码质量**: 良好。有完善的降级链、缓存、持久化、惰性加载。  
**瓶颈**: 全量暴力搜索, 无 HNSW/IVF 等 ANN 索引; 无分片/分布式支持。

### 2.2 RAG 管道 (`rag_pipeline.py`) — 对话智能

**工作流**:
```
Query → ContextBuilder (4路并行)
        ├─ build_user_profile  (用户画像)
        ├─ build_brochure_context (画册内容)
        ├─ build_vector_context (向量搜索)
        └─ build_match_context (匹配建议)
        ↓
  System Prompt (含5类上下文) → DeepSeek API → RAGResponse (含源引用)
```

**亮点**: 多路并行上下文构建、源引用追踪、LLM不可用时降级为结构化回复。  
**可改进**: 无多轮对话持久化、无 CoT/Agent 模式、Prompt 模板硬编码。

### 2.3 知识图谱 (`knowledge_graph.py`) — 关系网络

**关系类型 (6种)**:
1. `tag_match` — 标签供需匹配
2. `trust` — 信任连接
3. `industry_peer` — 同行
4. `match_record` — 匹配记录
5. `brochure_view` — 浏览画册
6. `own_brochure` — 拥有画册

**算法**: BFS 最短路径 + 递归邻居扩展 (max_depth=2)  
**存储**: 纯内存构建, 从 DB 实时查询。无图数据库。  
**局限**: 无社区发现、无 PageRank/Node2Vec、无持久化图存储。

### 2.4 推荐引擎 (`recommendation.py`) — 核心业务引擎

**混合推荐公式**:
```
final_score = W_tag * tag_score + W_graph * graph_score + W_semantic * semantic_score
```
默认: W_tag=0.40, W_graph=0.30, W_semantic=0.30 (在线学习可动态调整)

**反馈闭环**:
```
用户反馈 → FeedbackLoop → 权重调整 [0.6, 1.5] → 影响 final_score
在线学习 → RecommendEngine.refresh_online_weights() → 热更新 W_*
数据网络效应 → 协同过滤 + 热门推荐 → boost [1.0, 1.2]
```

**亮点**: 多维度加权、在线学习热更新、三层反馈调整（用户级+网络级+全局）。  
**问题**: 冷启动无处理、无实时序列推荐、无深度模型。

### 2.5 反馈闭环 (`feedback_loop.py`) — 强化学习基础

```
User → POST /api/recommend/{id}/feedback
  ├── rating: -1/0/1/2/3/4/5
  ├── SQLite 持久化 (feedback / weight_cache / feedback_meta)
  ├── 每10条反馈触发 _adjust_weights()
  │     boost = 1.0 + pos*0.15 + neg*(-0.20) + (avg_rating-3)*0.05
  │     clamp [0.6, 1.5]
  └── 极端评分 (-1, 5) → GaiaEvolutionBrain.ingest_feedback()
```

### 2.6 在线学习 (`online_learning.py`) — 推荐权重自适应

```
每100条反馈触发一次:
  1. 统计正/负反馈比例
  2. net_adjust = batch_likes*0.05 + batch_dislikes*(-0.05)
  3. global_adjustment ∈ [0.5, 1.5]
  4. 各维度权重 = base * global_adjustment
  5. 持久化到 online_weights.json
  6. 热更新 RecommendEngine 权重
```

**局限**: 简单线性调整, 无梯度下降、无贝叶斯优化。

### 2.7 盖娅进化系统

#### GaiaEvolutionBrain — "大脑"

**知识来源**:
- 复盘提炼 (retrospective)
- 用户反馈 (feedback, 极端评分)
- A/B 测试结果 (ab_test)
- 手动/系统注入

**进化循环**:
```
1. _collect_pending_knowledge()  → 未向量化的知识
2. _embed_knowledge_batch()      → 写入向量索引
3. _compute_and_update_weights() → 按知识分布调模块权重
4. 记录 GaiaTrainingRun
```

**覆盖模块**: recommendation / search / extractor / writing / optimization / rag / knowledge_graph

**问题**: 权重更新策略过于简单(仅按知识类型比例+置信度), 无法从数据中学习复杂模式。

#### GaiaTrainer — "训练管线"

**完整管线**:
```
1. collect_training_data()   → 知识 + 反馈 + 交互
2. compute_evolved_weights() → 类型权重分析
3. update_vector_index()     → 增量刷新
4. deploy_weights()          → 版本管理 + 写入 DB
5. 记录 GaiaTrainingRun
```

#### GaiaFlywheel — "飞轮"

```
每30分钟(可配置):
  阶段1: brain.process_evolution_cycle() → 知识聚合+事件处理
  阶段2: trainer.run_training_cycle()    → 训练管线
  阶段3: 统计报告
```

### 2.8 AI Gateway 层

**三层适配器**:
```
FallbackAIGateway
  └── CachedAIGateway (缓存 + 限流 + 熔断)
        └── DirectAIGateway (DeepSeek API)
```

**功能**:
- 缓存 (CacheProtocol, TTL=3600s)
- 限流 (TokenBucket, per-model RPM)
- 熔断 (CircuitBreaker, 3次连续失败 → 30s 冷却)
- 降级链 (primary → fallback1 → fallback2 ...)
- 成本估算 (按模型定价)
- 延迟百分位统计 (p50/p90/p99)

### 2.9 其他模块

| 模块 | 功能 | 实现方式 |
|------|------|---------|
| OCR | 名片图像文字识别 | PaddleOCR + PIL预处理 + 正则提取 |
| Extractor | PDF/NLP字段提取 | pdfplumber + 正则 + DeepSeek摘要 |
| Writing Assistant | 文案生成 | DeepSeek API (bio/company/recommendation/slogan) |
| Optimization | 名片完整度/关键词/专业度 | 规则引擎 + 权重计算 |
| Bandit | 个性化排序 | Thompson Sampling (Beta分布) |
| A/B Testing | 实验管理 | 卡方检验 + 贝叶斯概率 |
| MCP Adapter | DesignQA工具暴露 | MCP协议 (2025-03-26) |

---

## 三、Coze Loop 可注入点分析

> **Coze Loop 模式**: 扣子平台的 Agent 工作环 (工具链编排 + 知识库RAG + 多Agent协作 + 人机交互循环)

### 3.1 高价值注入点 (P0)

#### 注入点 #1: RAG Pipeline → Agent Loop 重构

| 现状 | Coze Loop 注入方案 |
|------|-------------------|
| `RAGPipeline.query()` 单轮固定 | 改为 **Agentic Loop**: Query → Plan → Tool Calls → Observe → React |
| Prompt 模板硬编码 | 引入 **动态Prompt组装器**: system_prompt = base + personality + context_rules + tool_defs |
| 无工具调用 | 注册 **MCP 工具集**: critque_design / audit_design / search_knowledge / get_recommendation |
| 无多步推理 | 注入 **CoT/ReAct 循环**: 每一步输出 Thought → Action → Observation |

**收益**: 从"一次性问答"升级为"可自主推理、多步执行、调用工具的智能Agent"  
**文件**: `rag_pipeline.py` + `mcp_adapter.py`

#### 注入点 #2: GaiaEvolutionBrain → 知识库RAG (Coze KB Pattern)

| 现状 | Coze Loop 注入方案 |
|------|-------------------|
| 线性知识权重计算 | 引入 **知识片段自动分段 + embedding + 混合检索 (BM25+向量)** |
| 无知识版本管理 | 注入 **知识库版本控制**: 每个演化周期生成快照, 支持回滚 |
| 无知识质量评分 | 注入 **置信度校准**: 基于用户隐式反馈自动调整知识置信度 |
| 单库 | 拆分 **多知识库**: design_kb / feedback_kb / pattern_kb / rule_kb |

**收益**: 从简单权重更新升级为"结构化知识库 + 智能检索 + 置信度校准"  
**文件**: `gaia_evolution_brain.py` → `_compute_and_update_weights()`

#### 注入点 #3: 推荐引擎 → 多策略Agent编排

| 现状 | Coze Loop 注入方案 |
|------|-------------------|
| 固定权重混合 (40/30/30) | **动态策略选择器**: 根据用户画像/场景自动切换推荐策略 |
| 无场景区分 | 注入 **场景识别器**: 发现模式 / 精准匹配 / 社交关系探索 |
| 无解释 | 注入 **推荐解释生成器**: LLM生成每个推荐的理由(自然语言) |
| 冷启动无策略 | 注入 **冷启动策略**: 基于画像分类 → 专家规则 → Bandit探索 |

**收益**: 从"一刀切评分"升级为"场景感知 + 策略自适应 + 可解释推荐"  
**文件**: `recommendation.py`

### 3.2 中价值注入点 (P1)

#### 注入点 #4: FeedbackLoop → 人机交互闭环

```
现状: rating → weight_adjustment (单向)
Coze Loop: 用户 ↔ Agent 多轮对话 ↓
  1. Agent: "我推荐了张三给您，原因是..."
  2. 用户: "他不够匹配, 我需要的是..."
  3. Agent: "明白了, 我调整策略为... 同时帮您搜索..."
  4. 用户: "这个更好, 为什么之前没推荐?"
  5. Agent: "因为... 现在已添加到您的偏好中"
```

**收益**: 从被动评分升级为"对话式反馈 + 主动调优"  
**文件**: `feedback_loop.py`, `rag_pipeline.py` (新增feedback路由)

#### 注入点 #5: OnlineLearning → 在线强化学习

| 现状 | Coze Loop 注入方案 |
|------|-------------------|
| 线性调整 (0.05步长) | **Contextual Bandit (LinUCB)**: 根据上下文特征动态选择臂 |
| 全局统一权重 | **用户分群权重**: 按 membership/行业/行为分群独立学习 |
| 阈值触发 | **实时增量学习**: 每收到反馈即梯度更新 |

**收益**: 从"规则式调参"升级为"上下文感知的在线学习"  
**文件**: `online_learning.py`, `bandit_engine.py`

#### 注入点 #6: Knowledge Graph → GraphRAG (Coze 关系推理)

| 现状 | Coze Loop 注入方案 |
|------|-------------------|
| BFS 最短路径 | **GraphRAG**: 将子图序列化为LLM上下文, 进行关系推理 |
| 6种固定关系 | **动态关系发现**: LLM从用户交互中识别新的关系类型 |
| 无社区发现 | **Louvain/NMF 社区发现**: 自动发现用户社群 |

**收益**: 从"简单图遍历"升级为"图增强推理"  
**文件**: `knowledge_graph.py`

### 3.3 低价值注入点 (P2)

| 注入点 | 说明 | 文件 |
|--------|------|------|
| #7 OCR → 多模态Agent | 用VLM替代PaddleOCR, 支持名片图像多轮问答 | `ocr.py` |
| #8 Cron → 定时Agent | 用Coze Scheduler替代简单cron, 支持复杂触发条件 | `cron/*` |
| #9 TrainingPipeline → 知识蒸馏 | Coze知识库导出 → 微调小模型 | `training_pipeline.py` |
| #10 Gateway → LLM Router | 用Coze多模型路由替代硬编码降级链 | `gateway/*` |

---

## 四、架构评分总结

| 维度 | 评分 | 说明 |
|------|------|------|
| 代码质量 | ⭐⭐⭐⭐⭐ | 类型注解完善、异常处理全面、日志详尽 |
| 架构设计 | ⭐⭐⭐⭐ | 分层清晰, 但部分耦合(如recommendation直接引多个模块) |
| 可扩展性 | ⭐⭐⭐⭐ | Gateway层协议化设计优秀, 新后端即插即用 |
| 自学习能力 | ⭐⭐⭐ | 基础反馈闭环OK, 但进化策略简单 |
| Agent化程度 | ⭐⭐ | RAG无Agent Loop, 无工具调用 |
| 生产就绪度 | ⭐⭐⭐⭐⭐ | Gateway有缓存/限流/熔断/降级, 生产级 |
| Coze兼容性 | ⭐⭐⭐ | 可注入点明确, 现有架构支持渐进升级 |

## 五、推荐优先级

```
P0 (本周)   → Agent RAG 重构 → 多知识库 → 推荐场景化
P1 (本月)   → 对话反馈闭环 → Contextual Bandit → GraphRAG
P2 (下月)   → 多模态OCR → Cron Agent → Gateway Router
```
