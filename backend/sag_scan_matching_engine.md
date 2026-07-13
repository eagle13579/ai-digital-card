# SAG扫描：AI数智名片现有匹配引擎完整能力档案

> 扫描日期：2026-07-13
> 扫描范围：D:\AI数智名片\backend
> 扫描文件：matching_engine.py, recommend_service.py, matching_client.py, match.py, recommend.py, recommendation.py (1020行), vector_search.py (1537行), online_learning.py, feedback_loop.py, knowledge_graph.py, tag.py, match_hook.py, data/目录

---

## 一、整体架构总览（5层）

### 第1层：路由层 (API Endpoints)
| 路由 | 文件 | 功能 |
|------|------|------|
| `GET /api/match/recommend` | `match.py` | 分页标签匹配推荐（单层标签重叠） |
| `POST /api/match/engine` | `match.py` | 标签匹配引擎（单层） |
| `GET /api/match/records` | `match.py` | 匹配记录查询 |
| `PUT /api/match/records/{id}/status` | `match.py` | 更新匹配状态 |
| `POST /api/match/semantic-search` | `match.py` | 语义搜索匹配用户 |
| `POST /api/match/rerank` | `match.py` | 语义重排序 |
| `POST /api/match/{record_id}/unlock` | `match.py` | 付费解锁联系方式 |
| `POST /api/recommend/personal` | `recommend.py` | 个性化推荐（三维加权） |
| `POST /api/recommend/discover` | `recommend.py` | 发现推荐 |
| `POST /api/recommend/similar` | `recommend.py` | 相似名片推荐 |
| `POST /api/recommend/rag-query` | `recommend.py` | RAG智能问答 |
| `GET /api/recommend/graph-summary` | `recommend.py` | 关系图谱摘要 |
| `GET /api/recommend/graph` | `recommend.py` | 完整关系图谱 |
| `POST /api/recommend/feedback` | `recommend.py` | 反馈提交 (like/dislike/skip) |
| `POST /api/recommend/{id}/feedback` | `recommend.py` | 旧版反馈接口 (1-5⭐) |
| `GET /api/recommend/feedback/stats` | `recommend.py` | 反馈统计 |
| `POST /api/match/unlock` | `match.py` | 付费解锁 |

### 第2层：匹配服务层 (Services)
| 服务 | 文件 | 行数 | 功能 |
|------|------|------|------|
| `MatchEngine` | `matching_engine.py` | 440 | 三层综合评分引擎 |
| `RecommendService` | `recommend_service.py` | 177 | 推荐服务编排 + 反馈闭环 |
| `MatchingClient` | `matching_client.py` | 95 | 外部HTTP匹配引擎客户端 |

### 第3层：AI引擎层 (AI)
| 引擎 | 文件 | 行数 | 功能 |
|------|------|------|------|
| `RecommendEngine` | `recommendation.py` | 1020 | 多维混合推荐引擎 |
| `VectorSearchEngine` | `vector_search.py` | 1537 | 向量搜索 + TF-IDF |
| `OnlineLearningEngine` | `online_learning.py` | 576 | 在线学习（反馈→权重） |
| `FeedbackLoop` | `feedback_loop.py` | 582 | 反馈闭环 |
| `CachedKnowledgeGraphBuilder` | `knowledge_graph.py` | (存在) | 关系图谱 |
| `OnlineLearningTracker` | `recommendation.py` | ~220 | 行为追踪 + 协同过滤 |
| `RAGPipeline` | (存在) | - | RAG智能问答 |

### 第4层：数据模型层
| 模型 | 表名 | 字段 |
|------|------|------|
| `UserTag` | `user_tags` | id, user_id, tag_type(provide/need), tag, weight, source |
| `MatchRecord` | `match_records` | id, user_a_id, user_b_id, match_score, status, common_tags, source |

### 第5层：数据存储
| 文件 | 用途 |
|------|------|
| `data/digital_brochure.db` | 主业务数据库 (SQLite) |
| `data/feedback.db` | 反馈闭环数据库 (SQLite) |
| `data/online_learning.db` | 在线学习 + 行为追踪 (SQLite) |
| `data/learning_log.jsonl` | 在线学习日志 |
| `data/jwt_rsa_*.pem` | JWT密钥对 |

---

## 二、匹配引擎能力矩阵

### 2.1 标签匹配（Tag Matching）—— 核心能力

**实现位置**：`MatchEngine` (matching_engine.py) + `RecommendEngine._score_by_tag_match` (recommendation.py)

**算法**：
- **供需双向匹配**：用户的 `provide` 标签与对方的 `need` 标签匹配，反之亦然
- **加权计算**：`score += weight_provide * weight_need`
- **归一化**：`max_score` 归一化到 [0, 1]

**MatchEngine三层评分公式**：
```
score = tag_overlap * 0.40 + vector_semantic * 0.40 + tag_weight * 0.20
```

**RecommendEngine三维加权**：
```
final_score = WEIGHT_TAG_MATCH(0.40) * t_score + WEIGHT_GRAPH(0.30) * g_score + WEIGHT_SEMANTIC(0.30) * s_score
```

**优点**：
- ✅ 供需双向匹配设计合理（A提供→B需要 + A需要→B提供）
- ✅ 权重可配置、可在线学习调整
- ✅ 标签来源支持 manual/ai/import 三种
- ✅ 支持分页和最低分数阈值

**缺点/可升级点**：
- ❌ **纯精确标签匹配**：只做 `tag == tag` 的字符串相等匹配，无标签同义词/层级体系
- ❌ **无标签推荐机制**：用户如果没有标签，推荐降级为空
- ❌ **无标签质量分**：所有标签权重平权，无法区分高频高价值标签 vs 低频冷门标签
- ⚠️ `match.py` 的 `/recommend` 和 `/engine` 接口中的标签匹配实现是 MatchEngine 的**简化版**（无余弦相似度、无语义向量），存在代码重复

### 2.2 向量语义搜索（Vector Semantic Search）—— 核心能力

**实现位置**：`VectorSearchEngine` / `VectorSearchIndex` (vector_search.py, 1537行)

**后端支持**：
| 后端 | 维度 | 依赖 | 说明 |
|------|------|------|------|
| `m3e` (默认) | 768 | sentence-transformers + moka-ai/m3e-base | 本地模型，零API成本 |
| `numpy` (降级) | 768 | numpy | TF-IDF模拟，零外部依赖 |
| `openai` | 1536 | openai库 | API调用 text-embedding-3-small |
| `deepseek` | 1024 | openai库 | API调用 text-embedding-v2 |

**功能**：
- SQLite持久化索引 (`vector_index.db`)
- 向量搜索 + 重排序 (rerank)
- 标签+简介+brochure内容的embedding构建
- 混合搜索（关键词权重0.3 + 向量权重0.7）

**优点**：
- ✅ 多后端切换能力（本地/云端可配置）
- ✅ 完善的降级机制（M3E失败→numpy回退）
- ✅ SQLite持久化，增量更新
- ✅ 混合搜索设计合理

**缺点/可升级点**：
- ❌ **无ANN索引**：使用暴力搜索，用户量大幅增长时性能会成为瓶颈
- ❌ **M3E模型较旧**：m3e-base是2023年模型，可升级到 bge-m3 / stella / gte 等新模型
- ⚠️ 增量更新时无过期机制，不会自动清理已删除用户/内容的向量
- ⚠️ numpy降级方案的语义理解能力有限

### 2.3 关系图谱（Knowledge Graph）—— 次核心能力

**实现位置**：`CachedKnowledgeGraphBuilder` (knowledge_graph.py)

**功能**：
- 构建用户间的关系图谱
- 多级深度关系探索 (depth=1~3)
- 推荐候选生成：`get_recommendation_candidates()`
- 图谱摘要：`get_graph_summary()`
- 缓存机制

**优点**：
- ✅ 支持关系深度扩展（1~3级）
- ✅ 缓存加速
- ✅ 与推荐引擎集成

**缺点/可升级点**：
- ❌ 未在本次扫描中完全读取知识图谱具体实现（需要单独SAG）
- ⚠️ 图算法仅限于邻居扩展，无PageRank/Node2Vec等图嵌入
- ⚠️ 关系权重未见在线学习调整

### 2.4 反馈闭环（Feedback Loop）—— 次核心能力

**实现位置**：`FeedbackLoop` (feedback_loop.py, 582行)

**机制**：
- 用户动作: `like` (+1), `dislike` (-1), `skip` (0)
- 评分模式: 1-5⭐ 映射
- 权重范围: `[0.6, 1.5]`
- 触发阈值: 每10条反馈自动调整
- SQLite持久化 + 内存缓存

**优点**：
- ✅ 双反馈模式（like/dislike/skip + 星级评分）
- ✅ 单例模式保证全局状态一致
- ✅ 权重缓存加速
- ✅ 内联反馈（在推荐请求中直接提交）

**缺点/可升级点**：
- ❌ **无用户维度个性化反馈**：`get_feedback_boost(user_id, content_id)` 是用户-内容对级别，但无内容维度的聚合反馈
- ❌ **SQLite并发问题**：单例模式在线程安全方面可能存在竞态条件
- ⚠️ 无反馈数据的可视化和分析面板

### 2.5 在线学习（Online Learning）—— 新能力

**实现位置**：`OnlineLearningEngine` (online_learning.py, 576行) + `OnlineLearningTracker` (recommendation.py)

**机制**：
- 每100条反馈触发一次学习
- 调整幅度: like+0.05, dislike-0.05
- 全局调整系数: `[0.5, 1.5]`
- 三个维度权重等比例缩放
- JSON持久化 + 热更新 RecommendEngine

**行为追踪 (OnlineLearningTracker)**：
- 点击追踪 (weight+0.05, cap=1.3)
- 分享追踪 (weight+0.15, cap=1.3)
- 7天时间衰减
- 协同过滤（"喜欢X的人也喜欢Y"）
- 二级关联网络扩展
- 24小时热门趋势

**优点**：
- ✅ 完整的在线学习闭环架构
- ✅ 行为追踪 + 协同过滤实现扎实
- ✅ 支持权重热更新（无需重启服务）
- ✅ 时间衰减机制防止权重漂移
- ✅ 协同过滤网络效应（二级扩展）

**缺点/可升级点**：
- ❌ **行为数据在内存+SQLite**：规模增长后需迁移到Redis/PostgreSQL
- ❌ **学习策略简单**：仅按正负反馈比例做等比例调整，无强化学习/上下文Bandit
- ❌ **权重维度粒度粗**：全局三个维度的调整，而非用户级别或标签级别的个性化权重
- ⚠️ 冷启动问题：新用户无行为数据时无法利用在线学习
- ⚠️ 二级协同过滤的SQL查询复杂度随数据量指数上升

### 2.6 混合搜索（Hybrid Search）—— 补充能力

**实现位置**：`MatchEngine.hybrid_search` (matching_engine.py, 第218~338行)

**机制**：
- 关键词评分（用户名/公司/职位/标签/画册标题）
- 向量评分（VectorSearchEngine）
- 加权融合: `keyword*0.3 + vector*0.7`

**优点**：
- ✅ 双通道搜索覆盖全面
- ✅ 关键词权重可配置

**缺点/可升级点**：
- ❌ 关键词搜索是逐用户遍历的全表扫描，性能很差
- ❌ 无全文索引（如SQLite FTS5）

### 2.7 每日推荐（Daily Recommendations）

**实现位置**：`MatchEngine.get_daily_recommendations` (matching_engine.py)

**机制**：
- 对所有其他用户逐一计算完整三层评分
- 按分数降序取top
- 自动保存MatchRecord
- 支持min_score阈值

**优点**：
- ✅ 全量扫描保证覆盖度

**缺点/可升级点**：
- ❌ **O(N)全表扫描**：每个用户都要跑一次三层评分，数据量大时完全不可行
- ❌ **无增量推荐**：每次都是全量重算
- ❌ **无推荐解释**：仅返回分数，无个性化推荐理由

### 2.8 CRM集成（CRM Integration）

**实现位置**：`sync_match_to_crm` (match_hook.py, 279行)

**机制**：
- 名片交换 → 自动创建/更新CRM联系人
- 通过 phone/email 查重
- 自动初始化客户管道阶段
- 记录名片交换活动到时间线

**优点**：
- ✅ 完整的双向同步（A↔B同时创建）
- ✅ 智能查重（user_id优先 → phone/email兜底）
- ✅ 梯度降级（无CRM模块时静默跳过）
- ✅ 自动创建默认管道阶段

**缺点/可升级点**：
- ❌ 仅在 `_do_exchange_card` 处调用，覆盖面窄
- ⚠️ 更新联系人时无脏检查可能导致不必要的写操作

### 2.9 会员体系与付费解锁

**实现位置**：`match.py` 的解锁路由

**机制**：
- 会员等级: free / gold / diamond / board
- 脱敏规则: 姓名首字+**、电话前3+****+后4、公司前2+**、头像_blur
- 月度配额: 按会员等级配置
- 解锁记录持久化 (UnlockRecord)

**优点**：
- ✅ 脱敏机制完善
- ✅ 配额重置幂等

**缺点/可升级点**：
- ⚠️ 脱敏逻辑与匹配路由耦合，可提取为独立模块
- ⚠️ 无企业版/团队版会员体系

---

## 三、数据流全景图

```
用户访问 /api/recommend/personal
  │
  ▼
RecommendService.personalize()
  │
  ▼
RecommendEngine.personalize_recommend()
  │
  ├── async _score_by_tag_match()    → UserTag表查询 → 标签供需匹配
  ├── async _score_by_graph()        → KnowledgeGraph → 社交关系
  └── async _score_by_semantic()     → VectorSearchEngine → 语义相似
  │
  ▼
  三维加权融合 (WEIGHT_TAG_MATCH=0.40, WEIGHT_GRAPH=0.30, WEIGHT_SEMANTIC=0.30)
  在线学习提升 (affinity 1.0~1.3)
  网络效应提升 (协同过滤 1.0~1.2)
  反馈闭环调整 (boost 0.6~1.5)
  │
  ▼
  _build_recommend_item() → 构建结果，附带推荐理由
  │
  ▼
  返回 RecommendResult
  │
  ▼
  用户反馈 → FeedbackLoop.record_feedback()
  │
  ├── 每10条 → _adjust_weights()
  └── OnlineLearningEngine.check_and_learn()
      │
      └── 每100条 → run_learning_cycle()
           → 更新 RecommendEngine.WEIGHT_* 三权重
```

---

## 四、代码质量问题

### 4.1 重复代码
- `match.py` 的 `/recommend` 和 `/engine` 接口中的标签匹配实现是 `MatchEngine._tag_overlap_score()` 的**简化复制版**（无余弦相似度、无向量语义、无标签权重综合评分）
- `match.py` 中的 `_desensitize_user()` 在多个接口中重复调用
- `match.py` 和 `matching_engine.py` 中对 MatchRecord 的创建/查询逻辑存在重复

### 4.2 性能风险
- **全表扫描多处**：每日推荐、关键词搜索、标签匹配（对所有用户逐一扫描）
- **无分页游标**：`select(User).where(User.id != current_user.id)` 在用户量>10万时崩溃
- **N+1查询模式**：逐用户查询Tag/Brochure/Page是典型的N+1问题

### 4.3 可维护性
- **单例混乱**：`FeedbackLoop` 和 `OnlineLearningEngine` 都是单例，但初始化方式不同
- **混合关注点**：`match.py` 同时包含脱敏、解锁、匹配、画册别名路由，职责过重（629行）
- **SQLite并发**：`FeedbackLoop` 和 `OnlineLearningTracker` 都使用 SQLite，但无写锁机制
- **回退埋点**：`vector_search.py` 中多处 `except: return numpy` 静默降级，难以发现生产问题

### 4.4 可测试性
- 数据库依赖强（无 Repository 抽象层）
- 单例模式难以 mock
- 缺少单元测试覆盖

---

## 五、升级建议（按优先级）

### P0 紧急
1. **N+1查询优化**：标签/画册/Page查询使用 `joinedload` 或 `selectinload`，避免逐用户查询
2. **全表扫描改索引扫描**：`hybrid_search` 关键词搜索、每日推荐的全量遍历
3. **代码去重**：统一 `match.py` 中两份标签匹配逻辑，统一调用 `MatchEngine`

### P1 重要
4. **标签语义化升级**：
   - 引入标签同义词映射（前端开发≈web开发≈H5开发）
   - 标签层级体系（编程语言→Python→Django）
   - 自动标签推荐（根据简介/画册内容AI生成标签）
5. **向量搜索性能升级**：
   - 引入ANN索引（faiss / hnswlib / pgvector）
   - M3E模型升级到 bge-m3 或 gte-Qwen2
6. **在线学习升级**：
   - 迁移到Redis存储行为数据
   - 引入用户级别个性化权重（非仅全局调整）
   - 增加探索-利用策略（ε-greedy / Thompson Sampling）

### P2 提升
7. **知识图谱增强**：引入图嵌入（Node2Vec）替代简单的邻居扩展
8. **推荐解释增强**：`_build_recommend_item` 中的理由从3条模板扩展到个性化解释
9. **反馈可视化**：增加反馈数据看板（高频标签、拒绝模式、匹配分布）
10. **冷启动机制**：为用户提供入门标签选择器，或基于简介AI提取初始标签

### P3 长期
11. **统一搜索后端**：迁移到ElasticSearch / Meilisearch
12. **A/B测试框架**：支持推荐策略的实验对比
13. **实时流处理**：行为数据走Kafka/RabbitMQ，而非同步写入SQLite
14. **微服务拆分**：匹配引擎拆为独立服务

---

## 六、总结

**当前能力评级**：
- 标签匹配：⭐⭐⭐⭐（设计合理，但缺语义匹配和层级体系）
- 向量搜索：⭐⭐⭐⭐（多后端、降级机制完善，性能需升级）
- 关系图谱：⭐⭐⭐（基础可用，算法简单）
- 反馈闭环：⭐⭐⭐⭐（完整闭环，缺个性和可视化）
- 在线学习：⭐⭐⭐（架构完整，策略简单）
- CRM集成：⭐⭐⭐⭐（完整的企业级功能）
- 性能与可扩展性：⭐⭐（全表扫描普遍，需要架构升级）
- 代码质量：⭐⭐⭐（有重复代码、关注点混合、可测试性一般）

**综合评分**：基础能力扎实，适合中小规模用户（<1万），大用户量需要架构升级。

**文件路径**：`D:\AI数智名片\backend\`

**已扫描的关键文件清单**：
1. `app/services/matching_engine.py` — MatchEngine 三层评分 (440行)
2. `app/services/recommend_service.py` — 推荐服务编排 (177行)
3. `app/services/matching_client.py` — 外部HTTP客户端 (95行)
4. `app/routers/match.py` — 匹配路由 (629行)
5. `app/routers/recommend.py` — 推荐路由 (520行)
6. `app/ai/recommendation.py` — 推荐引擎核心 (1020行)
7. `app/ai/vector_search.py` — 向量搜索引擎 (1537行)
8. `app/ai/online_learning.py` — 在线学习引擎 (576行)
9. `app/ai/feedback_loop.py` — 反馈闭环 (582行)
10. `app/ai/knowledge_graph.py` — 知识图谱 (存在)
11. `app/models/tag.py` — 标签数据模型 (31行)
12. `app/crm/match_hook.py` — CRM匹配钩子 (279行)
