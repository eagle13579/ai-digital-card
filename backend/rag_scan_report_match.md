# RAG扫描报告：AI数智名片 — 匹配相关数据模型与路由

> 扫描时间：2026-07-13
> 项目路径：`D:\AI数智名片\backend`

---

## 一、数据模型清单 (app/models/)

| # | 文件名 | 表名 | 匹配相关度 |
|---|--------|------|-----------|
| 1 | **tag.py** | `user_tags`, `match_records` | ⭐⭐⭐ 核心 |
| 2 | **user.py** | `users`, `unlock_records` | ⭐⭐⭐ 核心 |
| 3 | **brochure.py** | `brochures`, `pages` | ⭐⭐ 重要 |
| 4 | **connection.py** | `connections` | ⭐⭐ 重要 |
| 6 | **six_degrees.py** | `user_relations`, `relation_events`, `six_degree_path_cache`, `referral_links` | ⭐⭐ 重要 |
| 7 | **match_credit_log.py** | `match_credit_log` | ⭐ 辅助(仅id字段,桩) |
| 8 | **online_matching_feedback.py** | `online_matching_feedback`, `online_matching_events`, `online_matching_registrations` | ⭐ 辅助(仅id字段,桩) |
| 9 | **business_card.py** | `business_card` | ⭐ 辅助(仅id字段,桩) |
| 10 | **business_need.py** | `business_need` | ⭐ 辅助(仅id字段,桩) |
| 其他 | (39个文件) | — | 非直接匹配相关 |

---

## 二、核心数据模型详析

### 2.1 UserTag (tag.py) — 标签模型

```
表: user_tags
├── id: int (PK, autoincrement)
├── user_id: int (FK → users.id)
├── tag_type: str(16)         — "provide" | "need"
├── tag: str(64)              — 标签文本
├── weight: float             — 权重 (默认1.0)
├── source: str(16)           — "manual" | "ai" | "import"
└── created_at: datetime
```

### 2.2 MatchRecord (tag.py) — 匹配记录

```
表: match_records
├── id: int (PK, autoincrement)
├── user_a_id: int (FK → users.id)
├── user_b_id: int (FK → users.id)
├── match_score: float        — 匹配分数 (默认0.0)
├── status: str(16)           — "pending" | "matched" | "confirmed"
├── common_tags: str(Text)    — JSON数组
├── source: str(16)           — "auto" | "manual"
└── created_at: datetime
```

### 2.3 User (user.py) — 用户模型（匹配相关字段）

```
表: users
├── id, username, phone, name, company, title, intro, avatar
├── membership_tier: str(16)      — "free" | "gold" | "diamond" | "board"
├── membership_expires_at: datetime?
├── unlock_quota: int             — 本月剩余解锁配额
├── quota_reset_at: datetime?
└── created_at, updated_at
```

### 2.4 UnlockRecord (user.py) — 解锁记录

```
表: unlock_records
├── id: int (PK)
├── user_id: int
├── target_user_id: int
├── match_record_id: int
└── created_at: datetime
```

### 2.5 Brochure (brochure.py) — 画册模型（匹配相关字段）

```
表: brochures
├── id, user_id, title, cover
├── purpose: str(32)          — "partner/client/investor/supplier/business/personal/startup"
├── status: str(16)           — "draft" | "published"
├── visibility: str(16)       — "public" | "platform" | "network" | "private"
└── platform_id: int?
```

### 2.6 Connection (connection.py) — 社交关系

```
表: connections
├── id, user_id, contact_id
├── source: str(32)           — "platform" | "scan" | "manual"
├── status: str(16)           — "pending" | "approved" | "rejected"
├── strength: float           — 关系强度评分
├── label: str(64)
└── created_at, updated_at
```

### 2.7 UserRelation (six_degrees.py) — 六度人脉关系边

```
表: user_relations
├── id, from_user_id, to_user_id
├── relation_type: str(20)    — "invite/contact/brochure/coop/refer"
├── trust_score: float        — 0.0~1.0
├── interaction_count: int
├── bidirectional: bool
├── is_active: bool
├── source, source_detail
├── version (乐观锁)
├── organization_id (多租户)
└── created_at, updated_at, deleted_at, is_deleted
```

---

## 三、API端点清单

### 3.1 `/api/match/*` (app/routers/match.py) — 匹配路由

| 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|
| GET | `/api/match/recommend` | `page`, `size=10`, `min_score=0.3` | 获取匹配推荐（分页+脱敏）基于标签供需计算 |
| POST | `/api/match/engine` | `min_score=0.3` | 匹配引擎全量计算（标签供需匹配，top20存MatchRecord） |
| GET | `/api/match/records` | `status?` | 获取当前用户匹配记录列表 |
| PUT | `/api/match/records/{record_id}/status` | `record_id`, `{status}` | 更新匹配记录状态（pending/matched/confirmed） |
| POST | `/api/match/semantic-search` | `{query, top_k, min_score}` | 语义搜索匹配的用户 |
| POST | `/api/match/rerank` | `{query, candidates, top_k?}` | 语义重排序已有匹配结果 |
| POST | `/api/match/{record_id}/unlock` | `record_id`, `{match_record_id}?` | 付费解锁匹配对象联系方式（会员+配额检查） |

### 3.2 `/api/recommend/*` (app/routers/recommend.py) — 推荐路由

| 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|
| POST | `/api/recommend/personal` | `{top_k, strategy, exclude_user_ids, feedback?}` | 个性化推荐（tag/graph/semantic/hybrid 四策略） |
| POST | `/api/recommend/discover` | `{top_k, purpose?, feedback?}` | 发现页全局推荐（可按用途筛选） |
| POST | `/api/recommend/similar` | `{target_user_id, top_k, feedback?}` | 相似名片推荐 |
| POST | `/api/recommend/rag-query` | `{query, top_k, temperature, max_tokens}` | RAG智能问答（向量+用户画像+图谱→DeepSeek生成） |
| GET | `/api/recommend/graph-summary` | — | 获取当前用户关系图谱摘要 |
| GET | `/api/recommend/graph` | `depth=1` | 获取完整关系图谱（支持深度1-3层） |
| POST | `/api/recommend/feedback` | `{content_id, action, source, recommendation_id?}` | 提交推荐反馈(like/dislike/skip) |
| POST | `/api/recommend/{item_id}/feedback` | `item_id`, `{rating, source}` | 旧版反馈提交（1-5星/👍-1/👎1） |
| GET | `/api/recommend/feedback/stats` | — | 反馈闭环全局统计 |
| GET | `/api/recommend/feedback/my` | `limit=50` | 当前用户的所有反馈记录 |
| POST | `/api/recommend/feedback/adjust` | — | 手动触发权重调整 |

---

## 四、MatchEngine类完整结构 (app/services/matching_engine.py)

### 评分公式

```
final_score = tag_overlap * 0.40 + vector_semantic * 0.40 + tag_weight * 0.20
```

### 方法签名

| 方法 | 类型 | 参数 | 返回值 | 说明 |
|------|------|------|--------|------|
| `_build_tag_vector` | static cached | `(db, user_id, tag_type) → dict[str, float]` | 标签向量 | 构建用户 provide/need 标签映射 |
| `_cosine_similarity` | static | `(vec_a, vec_b) → float` | [0,1] | 余弦相似度（归一化到[0,1]） |
| `_tag_overlap_score` | static | `(provide_a, need_b, provide_b, need_a) → (float, list[dict])` | 分数+匹配详情 | 双向标签供需重叠匹配 |
| `_build_user_document` | static async | `(db, user_id) → list[str]` | 文本片段列表 | 构建用户文档（intro+标签+brochure内容+AI摘要） |
| `_compute_vector_semantic` | static async | `(db, user_a_id, user_b_id) → float` | [0,1] | TF-IDF向量语义相似度 |
| `_compute_tag_weight_score` | static | `(provide_a, need_a, provide_b, need_b) → float` | [0,1] | 标签权重综合分（数量+权重各50%） |
| `compute_similarity` | **static async** | `(db, user_a_id, user_b_id) → dict{score, tag_overlap, vector_semantic, tag_weight, common_tags}` | 完整评分详情 | **主入口**：三层综合评分 |
| `hybrid_search` | static async | `(db, query_text, current_user_id, top_k, keyword_weight, vector_weight) → list[dict]` | 混合搜索结果 | 关键词(30%) + 向量(70%) 混合搜索 |
| `get_daily_recommendations` | static async | `(db, user_id, limit=10, min_score=0.1) → list[dict]` | 每日推荐列表 | 全量用户排序+自动保存MatchRecord |
| `record_interest` | static async | `(db, user_id, target_user_id) → MatchRecord` | MatchRecord | 记录用户兴趣（不存在则创建,存在则更新为confirmed） |

### 三层评分详解

```
1. tag_overlap (40%):
   - 双向匹配：我的provide ∩ 对方的need, 对方的provide ∩ 我的need
   - weight * weight 累积求和
   - 归一化到 [0, 1]

2. vector_semantic (40%):
   - 构建双方文档：intro + 标签文本 + brochure标题 + 页面AI摘要
   - VectorSearchEngine.compute_semantic_similarity() — TF-IDF向量化+余弦

3. tag_weight (20%):
   - tag_count_score = min(总数A, 总数B) / max(总数A, 总数B) × 0.5
   - weight_norm = min(1.0, (平均权重A + 平均权重B) / 4.0) × 0.5
```

---

## 五、推荐引擎架构 (app/ai/recommendation.py)

### RecommendEngine 类

#### 权重配置
```
WEIGHT_TAG_MATCH  = 0.40   标签匹配（协同过滤）
WEIGHT_GRAPH      = 0.30   图谱社交
WEIGHT_SEMANTIC   = 0.30   语义相似
```
> 权重可被 `OnlineLearningTracker` 在线学习引擎热更新

#### 核心方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `personalize_recommend` | `(user_id, top_k=20, exclude_ids, strategy="hybrid")` | 个性化推荐 — 并行计算三个维度 → 加权融合 → 在线学习调整 → 反馈闭环调整 |
| `_score_by_tag_match` | `(user_id, exclude_set) → dict[user_id, score]` | 标签匹配评分 — 供需匹配度（SQL查询） |
| `_score_by_graph` | `(user_id, exclude_set) → dict[user_id, score]` | 图谱社交评分 — CachedKnowledgeGraphBuilder |
| `_score_by_semantic` | `(user_id, exclude_set) → dict[user_id, score]` | 语义相似评分 — VectorSearchEngine |
| `_build_recommend_item` | `(user_id, final_score, tag_score, graph_score, semantic_score) → RecommendItem` | 构建推荐条目（含理由生成） |
| `discover` | `(user_id, top_k=30, purpose=None)` | 发现推荐 — 按用途筛选+标签匹配 |
| `similar_users` | `(target_user_id, current_user_id, top_k=10)` | 相似推荐 — 向量搜索(50%) + 同行业(30%) + 相同标签(20%) |

#### 推荐分数调整链路
```
原始score
  → 加权融合 (tag*0.4 + graph*0.3 + semantic*0.3)
  → 在线学习提升 [_aff_weights: 1.0~1.3]
  → 数据网络效应提升 [_network_aff: 1.0~1.2, _trending: 1.0~1.15]
  → 反馈闭环调整 [FeedbackLoop.get_feedback_boost(): 0.6~1.5]
  → 最终排序
```

### OnlineLearningTracker（在线学习追踪器）

| 方法 | 说明 |
|------|------|
| `track_click(user_id, target_id)` | 记录点击行为（权重+0.05） |
| `track_share(user_id, target_id)` | 记录分享行为（权重+0.15） |
| `get_user_affinities(user_id) → dict` | 获取用户偏好权重 [1.0, 1.3] |
| `get_user_click_count(user_id, days=30)` | 统计近期点击次数 |
| `get_user_share_count(user_id, days=30)` | 统计近期分享次数 |
| `get_network_affinities(user_id, depth=2) → dict` | 协同过滤：喜欢X的人也喜欢Y |
| `get_trending_tags(hours=24) → dict` | 获取近期热门目标 |
| `decay_old_weights(max_age_days=30)` | 衰减旧权重（>30天未更新→1.0） |
| `cleanup_old_events(max_age_days=90)` | 清理旧事件记录 |

---

## 六、数据库配置 (app/database.py)

```
引擎类型: SQLAlchemy Async (async_sessionmaker)
默认URL: sqlite+aiosqlite:///./data/digital_brochure.db
PostgreSQL: 支持连接池 (pool_size=20, max_overflow=10, pool_pre_ping=True)
Base: DeclarativeBase
会话: AsyncSessionLocal (expire_on_commit=False)
埋点: track_db_query (数据库查询耗时度量)
```

---

## 七、辅助引擎和工具

### VectorSearchEngine (app/ai/vector_search.py)
- 多后端：m3e(默认768维) / numpy / openai / deepseek
- 核心功能：`embed_text()`, `search()`, `rerank()`, `build_index()`, `compute_semantic_similarity()` (TF-IDF回退)
- SQLite持久化索引

### FeedbackLoop (app/ai/feedback_loop.py)
- SQLite持久化 feedback.db
- 记录`like/dislike/skip/star`动作
- 每N条自动触发权重调整
- `get_feedback_boost(user_id, content_id) → float [0.6, 1.5]`

### CachedKnowledgeGraphBuilder (app/ai/knowledge_graph.py)
- 5种节点类型: User / Brochure / Tag / Connection / Trust
- Redis缓存支持
- `build_user_graph(user_id, max_depth)`, `get_recommendation_candidates()`, `get_graph_summary()`

---

## 八、架构总览：匹配推荐数据流

```
┌───────────────┐     ┌──────────────────────┐
│  前端请求     │────→│    Router Layer      │
│ /api/match/*  │     │ /api/recommend/*     │
│ /api/recommend│     └────────┬─────────────┘
└───────────────┘              │
                               ▼
┌───────────────────────────────────────────────────┐
│                Service / AI Layer                 │
├─────────────────────┬─────────────────────────────┤
│  MatchEngine        │  RecommendEngine            │
│  ┌───────────────┐  │  ┌──────────────────────┐  │
│  │ tag_overlap   │  │  │ personalize_recommend │  │
│  │ vector_semantic│  │  │ discover            │  │
│  │ tag_weight    │  │  │ similar_users       │  │
│  │ hybrid_search │  │  └──────┬───────────────┘  │
│  └───────────────┘  │         │                   │
├─────────────────────┼─────────┼───────────────────┤
│ VectorSearchEngine  │  CachedKnowledgeGraph       │
│ (M3E/TF-IDF)       │  (关系图谱)                  │
├─────────────────────┼─────────────────────────────┤
│ OnlineLearningTracker│ FeedbackLoop               │
│ (点击/分享追踪)     │ (反馈闭环权重调整)          │
└─────────────────────┴─────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────┐
│               Data Layer (Models)                 │
├───────────────────────────────────────────────────┤
│ UserTag (provide/need) → MatchRecord → Unlock    │
│ User → Brochure/Page → Connection → UserRelation │
│ MatchCreditLog → OnlineMatchingFeedback           │
└───────────────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────┐
│              Database Layer                       │
├───────────────────────────────────────────────────┤
│ PostgreSQL (主) / SQLite (开发+AI反馈)            │
│ Redis (缓存+图谱缓存)                             │
└───────────────────────────────────────────────────┘
```

---

## 九、关键发现

1. **两个匹配引擎并行存在**: `MatchEngine`(matching_engine.py) 是静态工具类，而 `RecommendEngine`(recommendation.py) 是面向用户的推荐引擎，两者有重叠但互不调用
2. **评分公式不一致**: MatchEngine用 `tag_overlap(0.4) + vector_semantic(0.4) + tag_weight(0.2)`，RecommendEngine用 `tag(0.4) + graph(0.3) + semantic(0.3)`
3. **脱敏机制**: free会员看到脱敏信息（姓名首字**，手机138****5678，头像加_blur后缀）；付费会员(gold/diamond/board)看到完整信息
4. **配额系统**: free=0次/月, gold=20, diamond=60, board=200，每月1日自动重置
5. **多个模型是桩(stub)**：`match_credit_log.py`, `online_matching_feedback.py`, `business_card.py`, `business_need.py` 都只有id列
6. **反馈闭环完整**: 支持内联提交(推荐请求中直接带feedback)和独立API提交，权重范围[0.6, 1.5]
7. **在线学习引擎**: 基于SQLite独立存储，追踪点击(+0.05)和分享(+0.15)行为，有7天时间衰减机制

---

> 报告生成完毕。共扫描50个模型文件, 2个路由文件, 1个服务文件, 1个AI推荐引擎文件。
