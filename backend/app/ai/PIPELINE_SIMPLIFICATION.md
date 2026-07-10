# AI管道简化评估

> 评估日期: 2026-07-10
> 项目: AI数智名片
> 路径: `D:/AI数智名片/backend/app/ai/`

## 当前状态

| 管道 | 文件 | 行数 | 核心功能 | 关键类 |
|------|------|:----:|---------|--------|
| RAG | `rag_pipeline.py` | 747 | 向量搜索+DeepSeek+源引用 | `RAGPipeline`, `DeepSeekClient`, `ContextBuilder`, `HyDEQueryTransformer`, `RAGContext`, `RAGResponse` |
| SAG | `sag_pipeline.py` | 582 | 自校验+逻辑补全+矛盾检测(6种推理模式) | `SAGPipeline`, `SAGMode`, `SAGDepth`, `SAGContext`, `SAGResponse`, `SAGStep`, `SAGPromptFactory` |
| Hybrid | `hybrid_pipeline.py` | 253 | RAG+SAG融合(先检索后校验) | `HybridPipeline`, `FusionStrategy` |
| Router | `pipeline_router.py` | 387 | 三管道路由+查询分类 | `PipelineRouter`, `PipelineType`, `QueryClassifier`, `RouteResult` |

**合计**: 4文件, ~1969行

## 功能重叠分析

| 重叠区域 | 涉及文件 | 问题 |
|----------|---------|------|
| LLM客户端 | `rag_pipeline.py` (`DeepSeekClient`), `sag_pipeline.py` (复用RAG的) | SAG已复用RAG的DeepSeekClient, 无问题 |
| 上下文构建 | `rag_pipeline.py` (`ContextBuilder`, `RAGContext`), `sag_pipeline.py` (`SAGContext`), `hybrid_pipeline.py` | 各自有独立Context类, 结构相似但字段不同 |
| 响应格式 | `rag_pipeline.py` (`RAGResponse`), `sag_pipeline.py` (`SAGResponse`), `pipeline_router.py` (`RouteResult`) | 三套响应格式, 可统一为`PipelineResponse` |
| 路由逻辑 | `pipeline_router.py` (`QueryClassifier` + `PipelineRouter`), `hybrid_pipeline.py` (硬编码RAG→SAG顺序) | Hybrid硬编码了RAG→SAG流程, 与Router的自动路由有重叠 |

## 简化方案

### 方案A(推荐): RAG为主,SAG为选项

保留三管道的差异化能力, 但重构调用关系:

```
┌─────────────────────────────────────────────────┐
│  PipelineRouter (精简为配置路由)                  │
│                                                  │
│  ┌─────────────────────────────────┐             │
│  │  RAGPipeline (主入口)           │             │
│  │  ├─ 向量搜索 + 图谱 + 画像      │             │
│  │  ├─ DeepSeek 模型调用           │             │
│  │  └─ 可选: SAG post-process     │ ← 新增开关  │
│  └─────────────────────────────────┘             │
│         ↑ config: {sag_enabled: bool}            │
│  ┌─────────────────────────────────┐             │
│  │  SAGPipeline (纯推理模块)       │             │
│  │  保留6种推理模式                │             │
│  │  作为RAG的可选后处理步骤        │             │
│  └─────────────────────────────────┘             │
└─────────────────────────────────────────────────┘
```

**具体变更**:
1. **删除** `hybrid_pipeline.py` 独立文件 — 其逻辑合并到 `rag_pipeline.py`
   - `RAGPipeline` 新增 `sag_enabled: bool = False` 参数
   - 启用时, 生成回答后自动调用 `SAGPipeline.analyze()` 做校验/补全
   - `FusionStrategy` 逻辑内联到 `RAGPipeline._apply_sag_post_process()`
2. **保留** `sag_pipeline.py` — 不修改
3. **精简** `pipeline_router.py`
   - 移除三元路由逻辑(RAG/SAG/Hybrid)
   - 改为: RAG为主, 通过 `QueryClassifier` 判断是否需要SAG后处理
   - `PipelineRouter` 简化为配置适配器而非代码路由
4. **新增统一基类** (可选): `BasePipeline` 接口

**优点**:
- 减少1个独立文件(hybrid_pipeline.py)
- 消除Hybrid与Router之间的功能重叠
- 调用方只需了解RAGPipeline接口
- SAG作为纯能力模块可独立使用

**缺点**:
- SAG不能单独作为对外管道(仅做内部后处理)
- 需小幅修改RAGPipeline签名

### 方案B: 统一Pipeline接口

```
┌──────────────────────────────────────────┐
│  BasePipeline (抽象基类)                  │
│  ├─ async def query(...)                 │
│  ├─ async def stream(...)                │
│  └─ config: PipelineConfig               │
│                                          │
│  RAGPipeline(BasePipeline)               │
│  SAGPipeline(BasePipeline)               │
│  HybridPipeline(BasePipeline) ← 配置组合 │
│                                          │
│  PipelineRouter → config["mode"] 选择    │
└──────────────────────────────────────────┘
```

**具体变更**:
1. 创建 `base_pipeline.py` — 定义 `BasePipeline` 抽象基类 + `PipelineConfig`
2. 三个管道实现统一接口
3. `HybridPipeline` 改为组合模式而非独立管道
4. `pipeline_router.py` 通过 `config["mode"]` 选择实现

**优点**:
- 接口统一, 扩展方便
- 调用方代码与具体管道解耦
- 测试时可mock基类

**缺点**:
- 引入新抽象层, 增加复杂度
- 需要修改3个现有文件
- 过度工程化(目前只有3个管道)

## 建议

当前三管道设计在产品层面是**差异化能力**(全球名片产品唯一), 建议保留框架但:

1. **SAG → RAG的可选后处理步骤**
   - RAGPipeline新增 `sag_enabled: bool = False` 开关
   - 启用时: `RAGPipeline.query()` → RAG生成 → SAG校验 → 修正输出
   - 不启用: 行为与原RAG一致

2. **删除 `hybrid_pipeline.py` 独立文件**
   - 逻辑合并到 `rag_pipeline.py` 内部方法 `_apply_sag_post_process()`
   - `FusionStrategy` 类改为 `RAGPipeline` 的内部枚举或配置

3. **精简 `pipeline_router.py` 为配置路由**
   - `QueryClassifier` 保留(判断查询类型)
   - `PipelineRouter` 改为仅做配置适配: `config["sag_enabled"]` 决定是否启用SAG
   - 移除三元路由分发逻辑

4. **更新 `__init__.py` 的懒加载映射**
   - 添加 `SAGPipeline`, `SAGMode`, `SAGContext`, `SAGResponse` 导出
   - 删除 `HybridPipeline` 导出(文件删除后)

## 时间估算

| 步骤 | 工时 | 影响文件 |
|------|:----:|---------|
| 1. RAGPipeline 新增 sag_enabled 参数 | 1h | `rag_pipeline.py` |
| 2. 实现 `_apply_sag_post_process()` | 1.5h | `rag_pipeline.py` |
| 3. 删除 hybrid_pipeline.py, 迁移逻辑 | 0.5h | `hybrid_pipeline.py` (删除) |
| 4. 精简 pipeline_router.py | 1h | `pipeline_router.py` |
| 5. 更新 __init__.py + 测试 | 1h | `__init__.py`, `tests/` |
| **总计** | **5h** | **4文件** |

## 保留(不做变更)

| 组件 | 原因 |
|------|------|
| `sag_pipeline.py` | 完整保留, 6种推理模式是核心竞争力 |
| `SAGPipeline` 类 | 作为纯能力模块, 不修改接口 |
| `DeepSeekClient` | 已由RAG和SAG共用, 无需变更 |
| `QueryClassifier` | 保留判断逻辑, 输出改为 `sag_enabled` 布尔值 |
