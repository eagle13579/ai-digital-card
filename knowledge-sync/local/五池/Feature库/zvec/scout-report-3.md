# 侦察报告 #3: 链客宝匹配引擎架构现状

> 侦察日期: 2026-06-22
> 目标: 链客宝 (B2B匹配引擎) — 搜索架构 + 向量搜索模块
> 输出至: 五池/Feature库/zvec/scout-report-3.md

---

## 一、代码资产全景

### 匹配引擎算法归档 (归档路径: 链客宝/匹配引擎算法归档/)

| 文件 | 行数 | 功能 | 状态 |
|:-----|:----:|:-----|:----:|
| matching_engine.py | 1,211 | 核心6步评分匹配引擎 v2.1 | ✅ 可运行(路由被网关遮挡) |
| feature_pipeline.py | 634 | 特征工程: category_vector + TF-IDF + price_norm + recency | ✅ 可用 |
| search_index.py | 1,237 | FTS5全文搜索引擎 + Memory搜索 + 缓存 | ✅ 可用 |
| recommend.py | 604 | 推荐系统: 产品推荐 + 个性化 + LLM理由 | ✅ 可用 |
| data_enrichment.py | 891 | 企查查API数据丰富管道 + 17行业Mock | ✅ 可用 |
| llm_service.py | 253 | DeepSeek LLM: 匹配理由 + 企业描述 + 摘要 | ✅ 可用 |
| **总计** | **~4,830** | | |

### 信任引擎增强 (链客宝/trust_engine/)

| 文件 | 行数 | 功能 | 状态 |
|:-----|:----:|:-----|:----:|
| matching.py | 330 | Step 0信任预过滤 + Step 7信任加权修正 | ✅ 独立可用, 未接入主管线 |

### 平台架构设计 (链客宝/链客宝平台架构设计_2026-05-28.md)

```
前端呈现层 (Shell SPA)
  → API Gateway (FastAPI + 动态路由注册)
    → 引擎内核层 (Plugin Registry · Event Bus · Auth · DB)
      → 数据层 (Shared DB + Module DB)
```

---

## 二、核心匹配引擎：6步评分管线 (matching_engine.py v2.1)

| 步骤 | 评分范围 | 方法 | 行号 |
|:-----|:--------:|:-----|:----:|
| ① 类目匹配 | 0-40分 | `_match_category()` — 精确匹配/同义词/SequenceMatcher | L463-495 |
| ② 关键词匹配 | 0-40分 | `_match_keywords_v1/v2()` — TF-IDF余弦 + jieba分词 | L540-637 |
| ③ 价格区间匹配 | 0-20分 | `_parse_budget()` + log压缩 + sigmoid | L724-755 |
| ④ 冷启动加权 | 1.2x | `_is_cold_start_item()` — 7天内新发布 | L759-807 |
| ⑤ 反馈闭环 | ±10% | `record_feedback()` — like+0.1, dislike-0.1 | L811-823 |
| ⑥ 特征集成 | 10%权重 | `feature_pipeline.compute_similarity()` — 特征管道 | 集成调用 |

**API路由**:
- `GET /api/matching/needs/{id}/products` → 需求匹配产品
- `GET /api/matching/products/{id}/needs` → 产品匹配需求
- `POST /api/matching/refresh` → 重建索引
- `GET /api/matching/metrics` → 监控指标
- A/B测试: `?strategy=v1|v2` 参数切换新旧引擎

---

## 三、向量搜索现状 — 🔴 关键问题

### 当前状态：休眠（Dead Code）

**证据**:

1. **`_apply_vector_bonus()` 是死代码** (matching_engine.py L639-669)
   ```python
   from app.vector_search import USE_VECTOR_SEARCH as _USE_VS
   if _USE_VS:  # ← 永远为 False
       ...
   ```

2. **`USE_VECTOR_SEARCH=0` 硬编码** — 配置从未启用

3. **DeepSeek API Key = 空** — 无法调用云端 embedding

4. **M3E模型未下载** — 本地 embedding 模型不存在

5. **`vector_search_router.py` 列在清单中但文件不存在/为空** — 路由层缺失

6. **`vector_search.py` 存在于 AI数字名片 项目** (1,480行, 多后端支持), 但未被链客宝引用
   - 位置: `AI数字名片/backend/app/ai/vector_search.py`
   - 支持 M3E本地 / numpy降级 / OpenAI / DeepSeek 四种后端
   - 有 SQLite 持久化向量索引
   - 有 `VectorSearchEngine` 兼容包装类

### P2-7 从未完成

匹配引擎代码头部的 GAP 清单明确标注:
```
P2: ⑦ 向量检索正式接入 ⑧ A/B测试框架
```
⑧ 已完成, ⑦ 从未启动。

### 蜂巢会议结论 (2026-06-01)

> **AI能力利用率: ~40%**
> 问题3: Vector Search 休眠
> - matching_engine的 _apply_vector_bonus() 是死代码
> - 修复: 配API Key + 设 USE_VECTOR_SEARCH=1

---

## 四、zvec 集成可行性

### zvec产品价值评分: **9/10 (P0)**

来自 `五池/Feature库/zvec/product-plan.md`:

| 能力 | 链客宝适用场景 | 优先度 |
|:-----|:-------------|:------:|
| 稠密向量检索 (HNSW/FLAT) | 企业画像语义匹配 — 替代当前TF-IDF向量增强 | P0 |
| 标量过滤 (SQL表达式) | 按行业/地域/规模/注册资本筛选 | P0 |
| 混合检索 (MultiQuery) | 向量 + FTS关键词 + 标量过滤 一次查询 | P0 |
| DiskAnn | 千万级企业库低内存检索 | P1 |
| 内置Embedding (DefaultLocalDenseEmbedding) | 纯本地, 无需API Key, 解决当前Key空问题 | **关键收益** |
| 内置ReRanker | 对召回结果重排序, 提升Top-K精度 | P1 |

### 当前架构中可被 zvec 替代的组件

| 当前组件 | 功能 | zvec替代方案 |
|:---------|:-----|:------------|
| `feature_pipeline._compute_tfidf_vector()` | TF-IDF语义相似度 | zvec稠密向量 + MultiQuery |
| `matching_engine._apply_vector_bonus()` | 向量增强(死代码) | zvec向量检索(真正激活) |
| `search_index.py` (FTS5) | 全文搜索 | zvec内置FTS(中文分词+BM25) |
| `vector_search.py` (AI数字名片) | 多后端embedding | zvec DefaultLocalDenseEmbedding |

### 集成后架构提议

```
┌─────────────────────────────────────────────┐
│              链客宝匹配引擎 v3.0              │
│                                             │
│  输入: Product, BusinessNeed                 │
│                                             │
│  Step 1-3: 规则评分 (类目/关键词/价格)       │
│  Step 4-5: 冷启动 + 反馈修正                 │
│  Step 6:  zvec 语义匹配 (替代死代码)          │
│  Step 0+7: trust_engine 信任增强             │
│                                             │
│  zvec 混合检索管道:                          │
│    ┌─ 企业描述 → DefaultLocalDenseEmbedding  │
│    ├─ 标量过滤 (行业+地域+规模)               │
│    ├─ FTS关键词 (产品名+标签)                 │
│    └─ MultiQuery + DefaultLocalReRanker      │
└─────────────────────────────────────────────┘
```

---

## 五、现存架构问题汇总

| 问题 | 严重度 | 说明 |
|:-----|:------:|:-----|
| ① 向量搜索休眠 | 🔴 P0 | `_apply_vector_bonus()` 死代码, USE_VECTOR_SEARCH=0 |
| ② 网关路由冲突 | 🟡 P1 | gateway将`/api/match/*`路由到8003而非8000 |
| ③ 数据库孤岛 | 🟡 P1 | 8000/8001用chainke.db, 8003用digital_brochure.db |
| ④ trust_engine未集成 | 🟡 P1 | Step0+7独立存在, 未接入匹配管线 |
| ⑤ zvec零集成 | 🟢 P2 | 架构文档已就绪, 产品计划已评估, 代码未开始 |

---

## 六、结论

1. **链客宝匹配引擎代码完整可运行** — 6步评分管线成熟, 约4,830行核心代码
2. **向量搜索是最大短板** — `_apply_vector_bonus()` 是死代码, 现有向量搜索组件在AI数字名片项目中闲置
3. **zvec是当前最优的向量搜索升级方案** — 评分9/10(P0), 内置本地embedding解决API Key缺失问题, 可直接替代已死的向量增强代码
4. **trust_engine/matching.py 可作为Step0+7独立集成** — 与zvec升级互不冲突

**建议下一步**: 创建 `链客宝匹配引擎v3.0` 升级计划, 将 zvec 集成作为 P0 任务, 替换 `_apply_vector_bonus()` 死代码, 并同步将 trust_engine 接入匹配管线。
