# Token 双重计费定价模型设计文档

## 1. 背景与目标

当前 `usage_service.py` 仅按功能维度（ocr/visitor/api/card 等）记录使用次数，缺乏对 AI 调用的 **token 级别追踪** 和 **双重计费支持**。

**目标：** 设计并实现一套 token 追踪系统，区分：
1. **内部模型/内容调用（internal）** — 自有模型如 M3E embedding、本地 MLX 推理、规则引擎、知识图谱查询（不产生第三方 API 成本）
2. **外部大模型调用（external）** — 调用第三方 LLM API 如 DeepSeek Chat/Embedding、OpenAI、HuggingFace（产生第三方 API 成本）

在收费侧：内部 token 按平台定价收费，外部 token 按大模型成本 + 加价收费。

---

## 2. AI 调用分类

### 2.1 外部调用（external）— 调用第三方 LLM API

| 组件 | 文件 | 调用类型 | 依赖 |
|------|------|----------|------|
| DirectAIGateway | `gateway/adapters/direct_api_adapter.py` | chat/stream/embed | DeepSeek API（httpx） |
| DeepSeekClient | `rag_pipeline.py` | chat/stream | DeepSeek API（aiohttp） |
| SAGPipeline | `sag_pipeline.py` | chat | 复用 DeepSeekClient |
| OpenAIEmbedding | `vector_search.py` | embed | OpenAI API |
| DeepSeekEmbedding | `vector_search.py` | embed | DeepSeek API |
| ModelServingClient (HF) | `model_serving.py` | embed | HuggingFace Inference API |

### 2.2 内部调用（internal）— 零第三方成本

| 组件 | 文件 | 类型 | 备注 |
|------|------|------|------|
| M3EEmbedding | `vector_search.py` | 本地模型推理 | M3E base，768维，本地运行 |
| NumpyEmbedding | `vector_search.py` | 本地模拟 | 降级方案，零外部依赖 |
| ModelServingClient (MLX) | `model_serving.py` | 本地 MLX 推理 | Mac mini 自建推理服务 |
| KnowledgeGraph | `knowledge_graph.py` | 纯 DB 查询 | SQL + 内存计算 |
| BanditEngine | `bandit_engine.py` | 规则引擎 | 基于逻辑的 A/B 测试 |
| AbTesting | `ab_testing.py` | 规则计算 | 内部逻辑 |
| FeedbackLoop | `feedback_loop.py` | 内部处理 | 用户反馈处理 |
| Optimization | `optimization.py` | 算法计算 | 内部优化算法 |

---

## 3. Token 定价模型

### 3.1 定价原则

```
内部 token 定价 = 固定平台价（覆盖服务器折旧+电费+维护）
外部 token 定价 = 第三方模型成本 × (1 + 加价率) + 平台费
```

### 3.2 定价表

#### 3.2.1 内部模型定价（platform_pricing）

| 模型/服务 | token 类型 | 单价（¥/1K tokens） | 说明 |
|-----------|-----------|---------------------|------|
| M3E embedding | embedding | ¥0.001 | 本地模型，仅电费成本 |
| Numpy embedding | embedding | ¥0.0005 | 降级方案，几乎零成本 |
| MLX 本地推理 | generation | ¥0.005 | Mac mini 自建推理 |
| 知识图谱查询 | query | ¥0.002 | DB 查询，固定成本 |
| 规则引擎 | rule | ¥0.001 | 内部逻辑计算 |
| 向量搜索（本地） | search | ¥0.002 | 本地索引查询 |

#### 3.2.2 外部模型定价（external_pricing）

| 模型 | token 类型 | 成本价（¥/1K tokens） | 加价率 | 售价（¥/1K tokens） |
|------|-----------|----------------------|--------|---------------------|
| deepseek-chat (input) | chat_input | ¥0.0027 | 50% | ¥0.0041 |
| deepseek-chat (output) | chat_output | ¥0.0110 | 50% | ¥0.0165 |
| deepseek-reasoner (input) | chat_input | ¥0.0055 | 50% | ¥0.0083 |
| deepseek-reasoner (output) | chat_output | ¥0.0219 | 50% | ¥0.0329 |
| deepseek-coder (input) | chat_input | ¥0.0014 | 50% | ¥0.0021 |
| deepseek-coder (output) | chat_output | ¥0.0028 | 50% | ¥0.0042 |
| text-embedding-3-small | embedding | ¥0.0002 | 50% | ¥0.0003 |
| text-embedding-3-large | embedding | ¥0.0013 | 50% | ¥0.0020 |
| HuggingFace API | embedding | ¥0.005 | 30% | ¥0.0065 |

> 注：成本价以 USD 计价，按汇率 7.25 转换为 ¥。加价率可配置，默认 external = 50%，internal = 0%。

### 3.3 计费公式

```
total_cost = sum(internal_tokens × internal_unit_price)
            + sum(external_cost × (1 + external_markup))
            + platform_fee

其中:
  external_cost = ∑(prompt_tokens × cost_input + completion_tokens × cost_output) / 1000
  platform_fee  = total_tokens × platform_fee_rate（可选，默认 0）
```

---

## 4. 数据库模型扩展

在 `UsageCounter` 模型上新增字段（向后兼容，所有字段可空/有默认值）：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model_type` | String(16) | "internal" | 模型类型: internal / external |
| `model_name` | String(64) | "" | 模型名称: m3e / deepseek-chat 等 |
| `token_type` | String(16) | "chat" | token 类型: chat / embedding / search / rule / query |
| `prompt_tokens` | Integer | 0 | 输入 token 数（外部模型） |
| `completion_tokens` | Integer | 0 | 输出 token 数（外部模型） |
| `total_tokens` | Integer | 0 | 总 token 数 |
| `token_cost` | Float | 0.0 | 总费用（¥） |
| `external_cost` | Float | 0.0 | 外部模型成本（¥，仅 external 有效） |
| `markup_rate` | Float | 0.0 | 加价率（external 默认 0.5） |

### 唯一约束更新

`unique_constraint("user_id", "feature", "period")` → 保持不变（按 feature 统计）
新增复合索引: `("user_id", "model_type")` 支持按类型汇总查询

---

## 5. API 设计

### 5.1 token 追踪服务（新增）

`TokenTracker` — 记录每次 AI 调用的 token 消耗

```python
class TokenTracker:
    async def record_token_usage(
        user_id: int,
        model_type: str,       # "internal" | "external"
        model_name: str,       # "deepseek-chat", "m3e", etc.
        token_type: str,       # "chat", "embedding", "search", "rule", "query"
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        db: AsyncSession,
    ) -> UsageCounter
    """
    记录 token 使用量。
    自动计算 token_cost（平台定价）和 external_cost（外部成本）。
    如果当月已有记录则累加，否则新建。
    """

    async def get_token_usage_summary(
        user_id: int,
        db: AsyncSession,
    ) -> dict
    """
    返回用户的 token 使用汇总：
    {
        "internal": {"total_tokens": N, "total_cost": M},
        "external": {"total_tokens": N, "total_cost": M, "external_cost": C},
        "grand_total": {"total_tokens": N, "total_cost": M}
    }
    """
```

### 5.2 TokenPricing（新增配置类）

```python
class TokenPricing:
    @staticmethod
    def get_internal_price(model_name: str) -> float
    """获取内部模型单价（¥/1K tokens）"""

    @staticmethod
    def get_external_cost(model_name: str, token_type: str = "input") -> float
    """获取外部模型成本（¥/1K tokens）"""

    @staticmethod
    def get_markup_rate(model_type: str) -> float
    """获取加价率"""
```

---

## 6. 集成方案

### 6.1 AI Gateway 层集成

在 `AIGatewayProtocol` 的 `chat()` 和 `embed()` 方法返回后，自动调用 `TokenTracker.record_token_usage()`。

**方案 A（推荐）：注入回调解耦**
- 在 `AIMetricsProviderProtocol` 中扩展 `record_call` 方法
- Gateway 实现类（DirectAIGateway 等）在成功响应后调用 metrics provider
- metrics provider 内部调用 `TokenTracker.record_token_usage()`

**方案 B：直接集成**
- 在 `direct_api_adapter.py` 成功调用后直接调用 `TokenTracker`
- 在 `rag_pipeline.py` / `sag_pipeline.py` 成功调用后调用 `TokenTracker`
- 在 `vector_search.py` embed 后调用 `TokenTracker`

### 6.2 API 路由层集成

现有 `usage_service.py` 的 `increment_usage()` 函数继续存在（按功能计次）。
新增的 token 追踪是独立的累计系统，两者并行。

### 6.3 管理员查询接口

新增路由提供用户 token 使用报表：
- `GET /api/v1/admin/usage/tokens/{user_id}` — 指定用户 token 汇总
- `GET /api/v1/admin/usage/tokens` — 全平台 token 汇总

---

## 7. 实现步骤

### Step 1: 配置文件
- `app/ai/token_pricing.py` — 定价常量与计算函数

### Step 2: 模型扩展
- `app/models/usage_counter.py` — 新增 token 相关字段

### Step 3: Token 追踪服务
- `app/services/usage_service.py` — 新增 `record_token_usage()` 和 `get_token_usage_summary()`

### Step 4: 网关集成
- 在 `direct_api_adapter.py` 中集成 token 追踪（作为 metrics provider 的扩展）
- 在 `rag_pipeline.py` / `sag_pipeline.py` 中集成

### Step 5: 管理 API
- 新增 token 使用报表路由

---

## 8. 数据库迁移说明

当前 `UsageCounter` 表结构不变，新字段通过 `ALTER TABLE` 或 Alembic 迁移添加。

```sql
ALTER TABLE usage_counters ADD COLUMN model_type VARCHAR(16) DEFAULT 'internal';
ALTER TABLE usage_counters ADD COLUMN model_name VARCHAR(64) DEFAULT '';
ALTER TABLE usage_counters ADD COLUMN token_type VARCHAR(16) DEFAULT 'chat';
ALTER TABLE usage_counters ADD COLUMN prompt_tokens INTEGER DEFAULT 0;
ALTER TABLE usage_counters ADD COLUMN completion_tokens INTEGER DEFAULT 0;
ALTER TABLE usage_counters ADD COLUMN total_tokens INTEGER DEFAULT 0;
ALTER TABLE usage_counters ADD COLUMN token_cost REAL DEFAULT 0.0;
ALTER TABLE usage_counters ADD COLUMN external_cost REAL DEFAULT 0.0;
ALTER TABLE usage_counters ADD COLUMN markup_rate REAL DEFAULT 0.0;

CREATE INDEX IF NOT EXISTS idx_usage_model_type ON usage_counters(user_id, model_type);
```

---

## 9. 示例场景

### 场景 1: 用户发起 RAG 查询
```
1. 向量搜索 (internal, M3E embedding) → 50 tokens × ¥0.001/1K = ¥0.00005
2. DeepSeek chat (external, deepseek-chat) → 
     input: 800 tokens × ¥0.0027/1K = ¥0.00216 (成本)
     output: 300 tokens × ¥0.0110/1K = ¥0.00330 (成本)
     售价: (800×0.0041 + 300×0.0165)/1000 = ¥0.00823
3. 总费用 = ¥0.00005 + ¥0.00823 = ¥0.00828
```

### 场景 2: 用户创建名片
```
1. OCR识别 (external, deepseek-vision)  → 一次性计次（现有体系）
2. 名片质量评审 SAG (external, deepseek-chat)  → 按 token 计费
3. 关系图谱查询 (internal, knowledge_graph) → ¥0.002
```

---

## 10. 未来扩展

- **Token 套餐包**：支持预购 token 包，按月/按年重置
- **阶梯定价**：使用量越大单价越低
- **自定义模型定价**：管理员可配置自有模型的 token 定价
- **企业租户隔离**：按企业维度汇总 token 消耗
- **实时计费告警**：token 消耗超阈值时触发告警
