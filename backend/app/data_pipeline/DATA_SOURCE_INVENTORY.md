# 📊 AI数智名片 — 数据源盘点文档 & 管道架构图

> **版本**: 1.0.0 | **更新日期**: 2026-07-25 | **维护方**: 数据管道团队
> **文档定位**: 全系统数据源-模型双向索引、管道架构、调度策略、异常处理、演进路线

---

## 目录

1. [数据源总览（清单表格）](#1-数据源总览清单表格)
2. [P0-P3 模型与数据源双向映射矩阵](#2-p0-p3-模型与数据源双向映射矩阵)
3. [数据流架构图（ASCII）](#3-数据流架构图ascii)
4. [各模型独立数据流描述](#4-各模型独立数据流描述)
5. [7×24 自动化 cron 调度表](#5-724-自动化-cron-调度表)
6. [异常处理策略（超时/重试/告警）](#6-异常处理策略超时重试告警)
7. [渐进增强路线图](#7-渐进增强路线图)
8. [附录：核心模块清单](#8-附录核心模块清单)

---

## 1. 数据源总览（清单表格）

### 1.1 完整数据源清单

| # | 数据源ID | 名称 | 类型 | 引擎 | 采集频率 | 支持模型（ID列表） | 数据格式 | 日容量 | 状态 |
|---|---------|------|------|------|---------|-------------------|---------|--------|------|
| 1 | `enterprise_websites` | 企业官网采集 | web_scraping | `cloak_scraper` (CloakBrowser) | 60 min | `matching_model_v2`, `user_tower_pretrained`, `data_augmentation`, `enhance_user_data` | JSON结构化 (企业简介/标签/联系方式/行业) | 500+ URL/日 | ✅ P0已启用 |
| 2 | `url_batch_crawler` | URL批量爬虫 | web_scraping | `crawler` (AI解析) | 30 min | `prepare_v2_training_data`, `matching_model_v2`, `training_data_generator` | JSON结构化 (HTML→名片) | 1000+ URL/日 | ✅ P0已启用 |
| 3 | `xiaohongshu` | 小红书内容采集 | social_media | `xiaohongshu-openclaw` | 180 min | `online_learning`, `recommendation`, `training_pipeline`, `rag_pipeline` | JSON (笔记/画像/话题) | 200+ 笔记/日 | ✅ P0已启用 |
| 4 | `qichacha` | 企查查企业数据 | business_data | `qichacha_client` | 1440 min (每日) | `data_augmentation`, `enhance_user_data`, `sales_prediction` | JSON结构化 (工商/风险/知识产权) | 100+ 企业/日 | ✅ P0已启用 |
| 5 | `baidu_search` | 百度搜索采集 | search_engine | `web_search` | 60 min | `gaia_evolution_brain`, `recommendation`, `rag_pipeline` | JSON (搜索/趋势/情报) | 500+ 搜索/日 | ✅ P0已启用 |
| 6 | `user_behavior_feedback` | 用户行为反馈流 | user_behavior | `feedback_loop` | 5 min (实时) | `online_learning`, `bandit_engine`, `recommendation`, `gaia_trainer` | JSON流 (👍/👎/⭐/点击/分享) | 实时流 | ✅ P1已启用 |
| 7 | `crm_matching_data` | CRM匹配数据 | business_transaction | `crm_pipeline` | 30 min | `matching_model_v2`, `sales_prediction`, `gaia_evolution_brain`, `bandit_engine` | JSON (匹配/转化/成交) | 持续流 | ✅ P0已启用 |
| 8 | `knowledge_base` | 知识库数据 | structured_knowledge | `knowledge_model_service` | 1440 min (每日) | `knowledge_graph`, `rag_pipeline`, `smart_matcher`, `embedding_service` | JSON结构化 (心智模型/行业知识/合规) | 增量更新 | ✅ P1已启用 |
| 9 | `web_pages_rag` | 网页RAG数据 | web_content | `rag_pipeline` | 120 min | `rag_pipeline`, `knowledge_graph`, `vector_search` | JSON+向量 (文档/索引) | 500+ 文档/日 | ✅ P2已启用 |

### 1.2 数据源属性详情

| 数据源ID | API端点 | 去重窗口 | 最大陈旧容忍 | 质量规则 |
|---------|---------|---------|-------------|---------|
| `enterprise_websites` | `POST /api/mingpian/scrape` | 60 min | 24h | min_confidence ≥ 0.3 |
| `url_batch_crawler` | `POST /api/crawler/scrape` + `/api/crawler/batch` | 60 min | 12h | min_confidence ≥ 0.3 |
| `xiaohongshu` | 脚本: `scripts/baidu_search_xhs.py` | 60 min | 48h | min_confidence ≥ 0.3 |
| `qichacha` | 脚本: `app/services/qichacha_client.py` | 60 min | 168h (7天) | min_confidence ≥ 0.3 |
| `baidu_search` | (内置web_search) | 60 min | 24h | min_confidence ≥ 0.3 |
| `user_behavior_feedback` | `POST /api/recommend/{item_id}/feedback` | 60 min | 1h | min_confidence ≥ 0.3 |
| `crm_matching_data` | (内置crm_pipeline) | 60 min | 6h | min_confidence ≥ 0.3 |
| `knowledge_base` | (内置knowledge_model_service) | 60 min | 168h (7天) | min_confidence ≥ 0.3 |
| `web_pages_rag` | (内置rag_pipeline) | 60 min | 24h | min_confidence ≥ 0.3 |

---

## 2. P0-P3 模型与数据源双向映射矩阵

### 2.1 模型→数据源 映射表

| 优先级 | 模型ID | 模型名称 | 训练类型 | 训练脚本 | 产出文件 | 依赖数据源 |
|-------|--------|---------|---------|---------|---------|-----------|
| **P0** | `matching_model_v2` | 名片匹配模型v2 | offline_batch | `scripts/train_matching_model_v2.py` | `models/matching_model_v2.pt` | `enterprise_websites`, `url_batch_crawler`, `crm_matching_data` |
| **P0** | `matching_model_v2_mac` | 名片匹配模型v2 (Mac MPS) | offline_batch | `scripts/train_matching_model_v2_mac_mps.py` | `models/matching_model_v2_mac.pt` | `enterprise_websites`, `url_batch_crawler`, `crm_matching_data` |
| **P0** | `prepare_v2_training_data` | V2训练数据准备 | offline_batch | `scripts/prepare_v2_training_data.py` | `data/v2_training_data.json` | `enterprise_websites`, `url_batch_crawler`, `xiaohongshu` |
| **P0** | `user_tower_pretrained` | 用户塔预训练 | offline_batch | `scripts/pretrain_user_tower.py` | `data/models/user_tower_pretrained.pt` | `enterprise_websites`, `qichacha`, `crm_matching_data` |
| **P0** | `data_augmentation` | 数据增强管道 | offline_batch | `scripts/data_augmentation.py` | `data/augmented_dataset.json` | `enterprise_websites`, `qichacha`, `xiaohongshu` |
| **P0** | `enhance_user_data` | 用户数据增强 | offline_batch | `scripts/enhance_user_data.py` | `data/enhanced_user_data.json` | `enterprise_websites`, `qichacha`, `url_batch_crawler` |
| **P0** | `training_data_generator` | 训练数据生成器 | offline_batch | `app/services/training_data_generator.py` | `data/training_data.json` | `url_batch_crawler`, `baidu_search` |
| **P1** | `online_learning` | 在线学习引擎 | online | `app/ai/online_learning.py` | `data/online_weights.json` | `user_behavior_feedback`, `crm_matching_data`, `xiaohongshu` |
| **P1** | `gaia_trainer` | Gaia训练器 | offline_batch | `app/ai/gaia_trainer.py` | `data/models/gaia_weights.json` | `user_behavior_feedback`, `knowledge_base`, `baidu_search` |
| **P1** | `gaia_evolution_brain` | Gaia进化脑 | evolution | `app/ai/gaia_evolution_brain.py` | `data/evolution_state.json` | `user_behavior_feedback`, `baidu_search`, `crm_matching_data` |
| **P1** | `recommendation` | 推荐引擎 | online | `app/ai/recommendation.py` | `data/recommendation_weights.json` | `user_behavior_feedback`, `xiaohongshu`, `baidu_search` |
| **P1** | `bandit_engine` | 多臂赌博机引擎 | online | `app/ai/bandit_engine.py` | `data/bandit_state.json` | `user_behavior_feedback`, `crm_matching_data` |
| **P2** | `sales_prediction` | 销售预测模型 | offline_batch | `app/services/sales_prediction.py` | `data/sales_prediction_model.json` | `crm_matching_data`, `qichacha`, `enterprise_websites` |
| **P2** | `model_absorb_daemon` | 模型吸收守护进程 | self_supervised | `../gaia-commercial/scripts/model_absorb_daemon.py` | `../gaia-commercial/data/absorbed_models/` | `web_pages_rag`, `knowledge_base` |
| **P2** | `rag_pipeline` | RAG知识管道 | self_supervised | `app/ai/rag_pipeline.py` | `data/rag_index/` | `web_pages_rag`, `xiaohongshu`, `knowledge_base` |
| **P3** | `embedding_service` | 向量嵌入服务 | self_supervised | `app/ai/embedding_service.py` | `data/embeddings/` | `web_pages_rag`, `knowledge_base` |
| **P3** | `knowledge_graph` | 知识图谱引擎 | self_supervised | `app/ai/knowledge_graph.py` | `data/knowledge_graph/` | `knowledge_base`, `enterprise_websites`, `web_pages_rag` |

### 2.2 数据源→模型 反向映射表

| 数据源ID | 数据源名称 | 供应的模型 | P0 | P1 | P2 | P3 |
|---------|-----------|-----------|----|----|----|----|
| `enterprise_websites` | 企业官网采集 | 7个模型 | matching_model_v2, prepare_v2_training_data, user_tower_pretrained, data_augmentation, enhance_user_data | — | sales_prediction | knowledge_graph |
| `url_batch_crawler` | URL批量爬虫 | 4个模型 | matching_model_v2, prepare_v2_training_data, enhance_user_data, training_data_generator | — | — | — |
| `xiaohongshu` | 小红书内容采集 | 5个模型 | prepare_v2_training_data, data_augmentation | online_learning, recommendation | rag_pipeline | — |
| `qichacha` | 企查查企业数据 | 3个模型 | user_tower_pretrained, data_augmentation, enhance_user_data | — | sales_prediction | — |
| `baidu_search` | 百度搜索采集 | 3个模型 | training_data_generator | gaia_trainer, gaia_evolution_brain, recommendation | — | — |
| `user_behavior_feedback` | 用户行为反馈流 | 4个模型 | — | online_learning, gaia_trainer, gaia_evolution_brain, recommendation, bandit_engine | — | — |
| `crm_matching_data` | CRM匹配数据 | 4个模型 | matching_model_v2, user_tower_pretrained | gaia_evolution_brain, bandit_engine | sales_prediction | — |
| `knowledge_base` | 知识库数据 | 3个模型 | — | gaia_trainer | model_absorb_daemon, rag_pipeline | embedding_service, knowledge_graph |
| `web_pages_rag` | 网页RAG数据 | 4个模型 | — | — | model_absorb_daemon, rag_pipeline | embedding_service, knowledge_graph |

### 2.3 数据源热度矩阵（按使用模型数排序）

```
 enterprise_websites ████████████████████████ 7模型 (P0×5 + P2×1 + P3×1)
 xiaohongshu         █████████████████       5模型 (P0×2 + P1×2 + P2×1)
 url_batch_crawler   ██████████████           4模型 (P0×4)
 user_behavior_feed  ██████████████           4模型 (P1×4)
 web_pages_rag       ██████████████           4模型 (P2×2 + P3×2)
 crm_matching_data   ██████████████           4模型 (P0×2 + P1×1 + P2×1)
 knowledge_base      ██████████               3模型 (P1×1 + P2×2 + P3×2)
 qichacha            ██████████               3模型 (P0×3)
 baidu_search        ██████████               3模型 (P0×1 + P1×2)
```

---

## 3. 数据流架构图（ASCII）

```
═══════════════════════════════════════════════════════════════════════════════
                    AI数智名片 — 统一数据管道架构
═══════════════════════════════════════════════════════════════════════════════

                          ┌─────────────────────────────────────┐
                          │         爬虫采集层 (Crawler Layer)           │
                          │  data_pipeline/crawler_orchestrator.py    │
                          ├─────────────────────────────────────┤
                          │                                     │
  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │CloakBrowser│  │URL爬虫   │  │企查查    │  │百度搜索  │  │小红书    │
  │智能爬虫   │  │AI解析    │  │企业数据  │  │搜索引擎  │  │内容采集  │
  │enterprise │  │batch     │  │qichacha  │  │baidu     │  │xiaohongshu│
  │_websites  │  │_crawler  │  │_client   │  │_search   │  │-openclaw │
  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘
        │             │             │             │             │
        └─────────────┴─────────────┴─────────────┴─────────────┘
                                  │
                          ┌───────▼───────────────────────────────┐
                          │   用户行为反馈流 (Real-time Stream)       │
                          │   user_behavior_feedback / crm_data    │
                          │   POST /api/recommend/{id}/feedback     │
                          └───────────────┬───────────────────────┘
                                          │
              ════════════════════════════╪═══════════════════════════
              ▲                                                      ▲
              ║   Phase 1: 统一采集调度                               ║
              ║   data_pipeline/crawler_orchestrator.py               ║
              ║   · 按注册表频率调度  · 到期自动触发                    ║
              ║   · 失败重试≤3次      · 采集状态持久化                 ║
              ╚═══════════════════════════╤═══════════════════════════╝
                                          │
              ┌───────────────────────────▼───────────────────────────┐
              │          原始数据暂存区 (Raw Data Staging)              │
              │   data/raw/{source_id}_{timestamp}.json                │
              └───────────────────────────┬───────────────────────────┘
                                          │
              ════════════════════════════╪═══════════════════════════
              ▲                                                      ▲
              ║   Phase 2: 数据治理层                                  ║
              ║   data_pipeline/data_curator.py                       ║
              ║                                                       ║
              ║   ┌─────────────────────────────────────────┐         ║
              ║   │  ① 去重 (MD5指纹 + 60min窗口)            │         ║
              ║   │  ② 标准化 (企业/用户行为两类规范化)       │         ║
              ║   │  ③ 质量控制 (confidence ≥ 0.3)           │         ║
              ║   │  ④ 新鲜度检查 (max_staleness_hours)      │         ║
              ║   └─────────────────────────────────────────┘         ║
              ╚═══════════════════════════╤═══════════════════════════╝
                                          │
              ┌───────────────────────────▼───────────────────────────┐
              │          治理后数据存储 (Curated Data Store)           │
              │   data_pipeline/.data_curator_state.json               │
              │   (唯一记录 + 时间戳索引)                               │
              └───────────────────────────┬───────────────────────────┘
                                          │
              ════════════════════════════╪═══════════════════════════
              ▲                                                      ▲
              ║   Phase 3: 模型供给层                                  ║
              ║   data_pipeline/model_feeder.py                       ║
              ║                                                       ║
              ║   ┌─────────────────────────────────────────┐         ║
              ║   │  ① 查注册表: 哪个模型该训练了?            │         ║
              ║   │  ② 查数据源: 依赖的数据源有新数据吗?     │         ║
              ║   │  ③ 按优先级: P0→P1→P2→P3 顺序执行       │         ║
              ║   │  ④ 调用训练脚本 (subprocess / 直接API)   │         ║
              ║   └─────────────────────────────────────────┘         ║
              ╚═══════════════════════════╤═══════════════════════════╝
                                          │
              ┌───────────────────────────▼───────────────────────────┐
              │         模型注册表调度中心                              │
              │         data_pipeline/model_registry.py               │
              │         · P0→P3 排序 · 频率检查 · 依赖解析            │
              └───────────────────────────┬───────────────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │          ┌────────────────▼────────────────┐          │
              │          │     模型训练管道 (模型专属)        │          │
              │          └────┬──────┬──────┬──────┬───────┘          │
              │               │      │      │      │                  │
     ┌────────▼───┐  ┌───────▼──┐  ┌─▼──────┐  ┌─▼────────┐        │
     │ 离线批训练   │  │ 在线学习  │  │ 自监督  │  │ 进化学习  │        │
     │ (P0)        │  │ (P1)     │  │ (P2/P3) │  │ (P1)     │        │
     │ train_match │  │ online   │  │ rag_    │  │ gaia_    │        │
     │ _model_v2   │  │ _learning│  │ pipeline│  │ evolution│        │
     │ pretrain_   │  │ bandit_  │  │ model_  │  │ _brain   │        │
     │ user_tower  │  │ engine   │  │ absorb  │  │          │        │
     │ prepare_v2  │  │ recommend│  │ embed   │  │          │        │
     │ data_aug    │  │          │  │ kg      │  │          │        │
     └──────┬──────┘  └────┬─────┘  └───┬─────┘  └─────┬────┘        │
            │              │            │              │              │
            └──────────────┴────────────┴──────────────┘              │
                                   │                                  │
              ┌────────────────────▼────────────────────┐             │
              │          模型产出 (Model Artifacts)                     │
              ├─────────────────────────────────────────┤             │
              │  🟦 .pt权重  │  🟩 JSON权重  │  🟧 向量索引  │             │
              │  match_model │ online_weights│ rag_index/  │             │
              │  user_tower  │ bandit_state  │ embeddings/ │             │
              │  .pt         │ gaia_weights  │ knowledge   │             │
              │              │ evolution     │ _graph/     │             │
              └────────────────────┬────────────────────┘             │
                                   │                                  │
              ┌────────────────────▼────────────────────┐             │
              │     API服务层 (推理/推荐/匹配/预测/RAG)                  │
              │                                            │             │
              │  ┌────────┐ ┌────────┐ ┌───────┐ ┌───────┐ │             │
              │  │推荐API  │ │匹配API │ │预测API│ │RAG API│ │             │
              │  │/api/rec│ │/api/   │ │/api/  │ │/api/  │ │             │
              │  │ommend  │ │matching│ │predict│ │qa     │ │             │
              │  └────────┘ └────────┘ └───────┘ └───────┘ │             │
              └─────────────────────────────────────────────┘             │
                                                                          │
              ════════════════════════════════════════════════════════════
              全局控制器 PipelineController (pipeline_controller.py)
              调度链: Collect → Curate → Feed → Train
              ────────────────────────────────────────────────────────
              cron 触发: 每5分钟 (full cycle) / 实时流 (feedback)
              告警桥接: cron_alert_bridge.py → 飞书Bot通知
              健康检查: cron_health_check.py (每15分钟)
              ════════════════════════════════════════════════════════════
```

---

## 4. 各模型独立数据流描述

### 4.1 P0 模型（核心匹配与训练数据管道）

#### 4.1.1 `matching_model_v2` — 名片匹配模型v2

```
企业官网 ──→ CloakBrowser ──→ 结构化企业数据 → DataCurator ──┐
URL批量  ──→ AI解析爬虫  ──→ 结构化名片数据 → DataCurator ──┤
CRM匹配  ──→ CRM管道     ──→ 匹配记录/转化   → DataCurator ──┤
                                                            ▼
                                              train_matching_model_v2.py
                                              (三塔模型,13特征,防过拟合)
                                                            ▼
                                              models/matching_model_v2.pt
                                              ↓ 推理API
                                              POST /api/matching
```

**训练频率**: 每6小时 | **数据新鲜度要求**: ≤24h | **训练类型**: offline_batch

#### 4.1.2 `prepare_v2_training_data` — V2训练数据准备

```
企业官网 ──→ CloakBrowser ──→ 企业信息 → Curator ──┐
URL批量  ──→ AI解析爬虫  ──→ 名片信息 → Curator ──┤
小红书   ──→ openclaw    ──→ 笔记/画像 → Curator ──┤
                                                    ▼
                                    prepare_v2_training_data.py
                                    (13特征拼接, 正负样本生成)
                                                    ▼
                                    data/v2_training_data.json
                                    (供给 matching_model_v2 训练)
```

**训练频率**: 每2小时 | **数据新鲜度要求**: ≤12h | **训练类型**: offline_batch

#### 4.1.3 `user_tower_pretrained` — 用户塔预训练

```
企业官网 ──→ CloakBrowser ──→ 企业画像 → Curator ──┐
企查查   ──→ qichacha_client ──→ 工商数据 → Curator ──┤
CRM匹配  ──→ CRM管道 ──→ 用户标签 → Curator ──┤
                                                ▼
                                pretrain_user_tower.py
                                                ▼
                                data/models/user_tower_pretrained.pt
                                (用户嵌入向量, 供推荐/匹配使用)
```

**训练频率**: 每12小时 | **数据新鲜度要求**: ≤72h | **训练类型**: offline_batch

#### 4.1.4 `data_augmentation` — 数据增强管道

```
企业官网 ──→ CloakBrowser ──→ 企业信息 → Curator ──┐
企查查   ──→ qichacha_client ──→ 结构化数据 → Curator ──┤
小红书   ──→ openclaw ──→ 笔记 → Curator ──┤
                                            ▼
                            data_augmentation.py
                            (同义词替换/回译/噪声注入)
                                            ▼
                            data/augmented_dataset.json
```

**训练频率**: 每4小时 | **数据新鲜度要求**: ≤48h | **训练类型**: offline_batch

#### 4.1.5 `enhance_user_data` — 用户数据增强

```
企业官网 ──→ CloakBrowser ──→ 企业画像 → Curator ──┐
企查查   ──→ qichacha_client ──→ 工商数据 → Curator ──┤
URL批量  ──→ AI解析爬虫 ──→ 名片信息 → Curator ──┤
                                                ▼
                                enhance_user_data.py
                                                ▼
                                data/enhanced_user_data.json
```

**训练频率**: 每4小时 | **数据新鲜度要求**: ≤48h | **训练类型**: offline_batch

#### 4.1.6 `training_data_generator` — 训练数据生成器

```
URL批量  ──→ AI解析爬虫 ──→ 名片数据 → Curator ──┐
百度搜索 ──→ web_search  ──→ 行业情报 → Curator ──┤
                                                ▼
                            training_data_generator.py
                                                ▼
                            data/training_data.json
```

**训练频率**: 每2小时 | **数据新鲜度要求**: ≤12h | **训练类型**: offline_batch

---

### 4.2 P1 模型（在线学习与推荐引擎）

#### 4.2.1 `online_learning` — 在线学习引擎

```
用户反馈 ──→ POST /api/recommend/{id}/feedback ──→ feedback 队列 ──┐
CRM匹配  ──→ CRM管道 ──→ 匹配转化数据 ──→ Curator ──┤
小红书   ──→ openclaw ──→ 用户画像 → Curator ──┤
                                                ▼
                                app/ai/online_learning.py
                                (阈值触发: 达100条反馈或每30min)
                                                ▼
                                data/online_weights.json
                                (全局调整系数 + 个性化权重)
```

**触发机制**: 反馈积累达阈值或定时检查 | **数据新鲜度**: ≤2h | **训练类型**: online

#### 4.2.2 `gaia_trainer` — Gaia训练器

```
用户反馈 ──→ feedback流 ──→ Curator ──┐
知识库   ──→ knowledge_model ──→ Curator ──┤
百度搜索 ──→ web_search ──→ Curator ──┤
                                        ▼
                        app/ai/gaia_trainer.py
                                        ▼
                        data/models/gaia_weights.json
```

**训练频率**: 每6小时 | **数据新鲜度要求**: ≤24h | **训练类型**: offline_batch

#### 4.2.3 `gaia_evolution_brain` — Gaia进化脑

```
用户反馈 ──→ feedback流 ──→ Curator ──┐
百度搜索 ──→ web_search ──→ 趋势数据 → Curator ──┤
CRM匹配  ──→ CRM管道 ──→ 成交分析 → Curator ──┤
                                                ▼
                                app/ai/gaia_evolution_brain.py
                                (进化算法: 策略变异+选择+重组)
                                                ▼
                                data/evolution_state.json
```

**训练频率**: 每1小时 | **数据新鲜度要求**: ≤6h | **训练类型**: evolution

#### 4.2.4 `recommendation` — 推荐引擎

```
用户反馈 ──→ feedback流 ──→ 实时行为 → Curator ──┐
小红书   ──→ openclaw ──→ 内容画像 → Curator ──┤
百度搜索 ──→ web_search ──→ 热点趋势 → Curator ──┤
                                                ▼
                                app/ai/recommendation.py
                                (协同过滤+内容推荐混合)
                                                ▼
                                data/recommendation_weights.json
```

**触发机制**: 实时反馈驱动 | **数据新鲜度**: ≤2h | **训练类型**: online

#### 4.2.5 `bandit_engine` — 多臂赌博机引擎

```
用户反馈 ──→ feedback流 ──→ 👍/👎/⭐实时数据 → Curator ──┐
CRM匹配  ──→ CRM管道 ──→ 转化数据 → Curator ──┤
                                                ▼
                                app/ai/bandit_engine.py
                                (Thompson Sampling / UCB)
                                                ▼
                                data/bandit_state.json
```

**训练频率**: 每15分钟 | **数据新鲜度要求**: ≤1h | **训练类型**: online

---

### 4.3 P2 模型（批量与知识管道）

#### 4.3.1 `sales_prediction` — 销售预测模型

```
CRM匹配  ──→ CRM管道 ──→ 成交记录 → Curator ──┐
企查查   ──→ qichacha_client ──→ 企业数据 → Curator ──┤
企业官网 ──→ CloakBrowser ──→ 行业信息 → Curator ──┤
                                                ▼
                                app/services/sales_prediction.py
                                                ▼
                                data/sales_prediction_model.json
```

**训练频率**: 每日 (每24小时) | **数据新鲜度要求**: ≤168h (7天)

#### 4.3.2 `model_absorb_daemon` — 模型吸收守护进程

```
网页RAG  ──→ rag_pipeline ──→ 文档/知识 → Curator ──┐
知识库   ──→ knowledge_model ──→ 结构化知识 → Curator ──┤
                                                ▼
                        ../gaia-commercial/scripts/model_absorb_daemon.py
                                                ▼
                        ../gaia-commercial/data/absorbed_models/
```

**训练频率**: 每日 (每24小时) | **数据新鲜度要求**: ≤168h (7天)

#### 4.3.3 `rag_pipeline` — RAG知识管道

```
网页RAG  ──→ 网页抓取 ──→ 文本提取 ──→ 向量化 ──┐
小红书   ──→ openclaw ──→ 笔记内容 → Curator ──┤
知识库   ──→ knowledge_model ──→ 领域知识 → Curator ──┤
                                                ▼
                                app/ai/rag_pipeline.py
                                (分块→嵌入→索引构建)
                                                ▼
                                data/rag_index/
                                (FAISS向量索引 + 文档存储)
```

**训练频率**: 每2小时 | **数据新鲜度要求**: ≤24h | **训练类型**: self_supervised

---

### 4.4 P3 模型（支撑性架构级）

#### 4.4.1 `embedding_service` — 向量嵌入服务

```
网页RAG  ──→ 网页内容 → Curator ──┐
知识库   ──→ 领域知识 → Curator ──┤
                                    ▼
                            app/ai/embedding_service.py
                            (文本→向量, 支持多种embedding模型)
                                    ▼
                            data/embeddings/
                            (向量缓存 + 索引)
```

**训练频率**: 每12小时 | **数据新鲜度要求**: ≤168h (7天) | **训练类型**: self_supervised

#### 4.4.2 `knowledge_graph` — 知识图谱引擎

```
知识库   ──→ 心智模型/行业知识 → Curator ──┐
企业官网 ──→ CloakBrowser ──→ 企业实体 → Curator ──┤
网页RAG  ──→ 网页内容 → Curator ──┤
                                    ▼
                            app/ai/knowledge_graph.py
                            (实体抽取→关系构建→图存储)
                                    ▼
                            data/knowledge_graph/
                            (Neo4j / NetworkX 序列化)
```

**训练频率**: 每日 (每24小时) | **数据新鲜度要求**: ≤336h (14天) | **训练类型**: self_supervised

---

## 5. 7×24 自动化 cron 调度表

### 5.1 主管道调度 (PipelineController)

| 作业ID | 调度频率 | 执行命令 | 模式 | 说明 |
|-------|---------|---------|------|------|
| `pipeline_full_cycle` | 每5分钟 `*/5 * * * *` | `python -m app.data_pipeline.pipeline_controller --mode full` | full | 全周期: 采集→治理→训练 |
| `pipeline_collect` | 每1分钟 `* * * * *` (高频) | `python -m app.data_pipeline.pipeline_controller --mode collect` | collect | 仅数据采集（实时性要求高的数据源） |
| `pipeline_train` | 每5分钟 `*/5 * * * *` | `python -m app.data_pipeline.pipeline_controller --mode train` | train | 仅检查训练任务（避免全周期阻塞） |
| `pipeline_status` | 每15分钟 `*/15 * * * *` | `python -m app.data_pipeline.pipeline_controller --mode status --json` | status | 状态报告（供告警/监控使用） |

### 5.2 数据源级调度（各数据源按注册表频率）

| 数据源 | 最小频率 | 推荐cron表达式 | 说明 |
|-------|---------|---------------|------|
| `user_behavior_feedback` | 5 min | `*/5 * * * *` | 实时反馈流，高频轮询 |
| `url_batch_crawler` | 30 min | `*/30 * * * *` | 批量URL采集，中等频率 |
| `enterprise_websites` | 60 min | `0 * * * *` | 企业官网，每小时整点 |
| `baidu_search` | 60 min | `0 * * * *` | 搜索引擎，每小时整点 |
| `web_pages_rag` | 120 min | `0 */2 * * *` | RAG文档，每2小时 |
| `xiaohongshu` | 180 min | `0 */3 * * *` | 小红书，每3小时 |
| `crm_matching_data` | 30 min | `*/30 * * * *` | CRM数据，中等频率 |
| `qichacha` | 1440 min (1天) | `0 3 * * *` | 企查查，每日凌晨3点 |
| `knowledge_base` | 1440 min (1天) | `0 4 * * *` | 知识库，每日凌晨4点 |

### 5.3 模型级调度（按优先级）

| 优先级 | 模型 | 频率 | 推荐cron | 窗口 |
|-------|------|------|---------|------|
| **P0** | `prepare_v2_training_data` | 120 min | `0 */2 * * *` | 12h |
| **P0** | `training_data_generator` | 120 min | `0 */2 * * *` | 12h |
| **P0** | `data_augmentation` | 240 min | `0 */4 * * *` | 48h |
| **P0** | `enhance_user_data` | 240 min | `0 */4 * * *` | 48h |
| **P0** | `matching_model_v2` | 360 min | `0 */6 * * *` | 24h |
| **P0** | `user_tower_pretrained` | 720 min | `0 */12 * * *` | 72h |
| **P1** | `bandit_engine` | 15 min | `*/15 * * * *` | 1h |
| **P1** | `online_learning` | 30 min | `*/30 * * * *` | 2h |
| **P1** | `recommendation` | 30 min | `*/30 * * * *` | 2h |
| **P1** | `gaia_evolution_brain` | 60 min | `0 * * * *` | 6h |
| **P1** | `gaia_trainer` | 360 min | `0 */6 * * *` | 24h |
| **P2** | `rag_pipeline` | 120 min | `0 */2 * * *` | 24h |
| **P2** | `sales_prediction` | 1440 min | `0 5 * * *` | 168h |
| **P2** | `model_absorb_daemon` | 1440 min | `0 6 * * *` | 168h |
| **P3** | `embedding_service` | 720 min | `0 */12 * * *` | 168h |
| **P3** | `knowledge_graph` | 1440 min | `0 7 * * *` | 336h |

### 5.4 辅助调度

| 作业 | 频率 | 说明 |
|------|------|------|
| `cron_alert_bridge` | 每5分钟 `*/5 * * * *` | 监控所有cron任务状态，发现error → 飞书告警 |
| `cron_health_check` | 每15分钟 `*/15 * * * *` | 管道健康检查（数据源可达性、模型文件存在性） |
| `learning_cron` | 每30分钟 `*/30 * * * *` | 在线学习阈值检查，达阈值自动触发 |
| `cleanup_stale_data` | 每日 `0 2 * * *` | 清理超过max_staleness的旧数据 |

---

## 6. 异常处理策略（超时/重试/告警）

### 6.1 异常分级

| 级别 | 定义 | 响应策略 |
|------|------|---------|
| 🟢 INFO | 数据新鲜但无需采集/训练 | 仅日志记录，无操作 |
| 🟡 WARNING | 单次采集返回0条/单个模型脚本丢失 | 日志警告 + 自动重试(≤3次) |
| 🟠 ERROR | 连续3次采集失败/模型训练exit非0 | 重试中断 + 飞书告警 + 降级跳过 |
| 🔴 CRITICAL | 管道核心模块崩溃/注册表损坏 | 立即告警 + 熔断停止后续任务 |

### 6.2 超时控制

| 阶段 | 默认超时 | 最大超时 | 超时后行为 |
|------|---------|---------|-----------|
| 爬虫采集 (单数据源) | 120s | 300s | 记录timeout状态，跳过该数据源，不影响其他源 |
| 数据治理 (单批次) | 60s | 120s | 治理跳过，标记数据为"未治理"，后续重试 |
| 模型训练 (离线) | 600s (10min) | 1800s (30min) | subprocess.TimeoutExpired → 记录timeout → 飞书告警 |
| 在线学习 (实时) | 30s | 60s | 跳过本轮，排队到下个周期 |
| 全管道周期 | 1200s (20min) | 3600s (1h) | 强制中断，部分结果已保存 |

### 6.3 重试策略

```
采集层:  重试 ≤ 3次, 间隔 30s/60s/120s (指数退避)
治理层:  重试 ≤ 2次, 间隔 10s/30s
训练层:  重试 ≤ 1次, 间隔 60s (脚本缺失不重试)
在线层:  不重试, 下次周期自动处理
```

### 6.4 告警通道

| 告警级别 | 推送方式 | 目标 | 内容 |
|---------|---------|------|------|
| 🟠 ERROR | 飞书Bot消息 | 技术负责飞书群 | `[数据管道] {数据源/模型ID} 失败: {原因}` |
| 🔴 CRITICAL | 飞书Bot + 邮件 | 技术+产品群 | `[紧急] 管道熔断: {模块} 已停止, 需人工干预` |
| 📊 每日报告 | 飞书Bot | 技术群 | 前24h采集/训练成功率统计 |

### 6.5 熔断机制 (Circuit Breaker)

```
连续失败 ≥ 3次 (同一模块):
  → 模块自动熔断 (状态标记为 "circuit_open")
  → 熔断持续时间: 30分钟 (熔断期不再调用该模块)
  → 半开尝试: 30分钟后尝试1次, 成功则关闭, 失败则再熔断60分钟
  → 人工介入: 可通过 API POST /api/pipeline/reset/{module} 手工重置
```

### 6.6 数据一致性保障

```
1. 幂等采集: 同一条数据在60min窗口内重复采集 → DataCurator去重丢弃
2. 原子写入: RAW数据先落盘再入Curator, 写失败不污染治理状态
3. 版本追踪: 每次治理更新 .data_curator_state.json, 支持回滚
4. 校验和: 关键模型产出文件附带 MD5 校验, 加载时验证完整性
```

---

## 7. 渐进增强路线图

### 7.1 当前状态 (Phase 0 — P0桩/Stub 模式)

```
┌──────────────────────────────────────────────────────┐
│ 当前实现评估:                                          │
│                                                      │
│  crawler_orchestrator.py ── 桩实现 (_simulate_*)      │
│  data_source_registry.json ── 完整注册 (9数据源)      │
│  model_registry.py ───────── 完整注册 (17模型)         │
│  data_curator.py ─────────── 完整实现 (去重+标准化)     │
│  model_feeder.py ─────────── 完整实现 (调度+执行)      │
│  pipeline_controller.py ──── 完整实现 (全周期控制)     │
│                                                      │
│  真实引擎接入: 0/9 (所有爬虫在桩模式运行)               │
│  模型训练脚本: 3/17 真实存在 (matching/tower/V2准备)   │
│  cron调度: 部分配置, 依赖外部 cron 系统                │
└──────────────────────────────────────────────────────┘
```

### 7.2 演进路线图

```
Phase 1: 接入真实爬虫引擎 (2-4周)
┌──────────────────────────────────────────────────────┐
│ 目标: 爬虫从桩切换到真实引擎                              │
│                                                      │
│ P0 ── CloakBrowser 集成                               │
│   · 替换 enterprise_websites 的 _simulate → 真实调用   │
│   · script: scripts/cloak_scraper_bridge.py           │
│                                                      │
│ P0 ── URL AI解析管道                                   │
│   · 替换 url_batch_crawler 的桩                        │
│   · 集成 Hermes web_search / parse_html 工具链         │
│                                                      │
│ P0 ── 企查查API集成                                    │
│   · app/services/qichacha_client.py 完善              │
│   · 企业认证 + API限流处理                             │
│                                                      │
│ 交付物:                                               │
│   · 真实数据进入 data/raw/ 目录                         │
│   · 验证: matching_model_v2 使用真实数据训练            │
└──────────────────────────────────────────────────────┘

Phase 2: 全数据源真实接入 (4-8周)
┌──────────────────────────────────────────────────────┐
│ 目标: 所有9数据源切换到真实生产引擎                        │
│                                                      │
│ P0 ── 百度搜索: 接入Hermes web_search 真实API           │
│ P0 ── 小红书: scripts/baidu_search_xhs.py 完善+认证    │
│ P1 ── 用户反馈流: 上线POST反馈API + 队列               │
│ P1 ── CRM管道: 对接真实CRM系统                         │
│ P1 ── 知识库: knowledge_model_service 启动             │
│ P2 ── RAG网页: 爬虫→清洗→向量化全自动                   │
│                                                      │
│ 交付物:                                               │
│   · 全自动数据管道: 爬虫→治理→训练→模型产出              │
│   · 验证: 所有P0模型使用真实数据训练，精度达标            │
└──────────────────────────────────────────────────────┘

Phase 3: 质量与监控体系 (8-12周)
┌──────────────────────────────────────────────────────┐
│ 目标: 企业级数据质量+监控+告警                           │
│                                                      │
│ 数据质量:                                             │
│   · 引入 Great Expectations 数据质量断言                │
│   · 实时新鲜度仪表盘 + 延迟告警                         │
│   · 异常检测: 数据量突降/突增自动识别                    │
│                                                      │
│ 监控体系:                                             │
│   · Prometheus + Grafana 管道指标                     │
│   · 各模型训练指标 (loss/accuracy/f1) 历史追踪          │
│   · 数据血缘追踪 (数据源→治理→模型→API)                │
│                                                      │
│ 交付物:                                               │
│   · 数据质量SLA: 99.9% 新鲜度达标                      │
│   · P0链路MTTR < 15分钟                               │
└──────────────────────────────────────────────────────┘

Phase 4: 智能调度与自愈 (12-16周)
┌──────────────────────────────────────────────────────┐
│ 目标: 自适应调度 + 自动异常修复                          │
│                                                      │
│ 智能调度:                                             │
│   · 基于数据量/价的自适应频率调整                        │
│   · 模型训练优先级动态排序 (根据在线效果)                │
│   · 错峰调度: 避免所有数据源同时采集造成洪峰              │
│                                                      │
│ 自动修复:                                             │
│   · 采集器故障 → 尝试备用引擎/降级数据源                │
│   · 模型训练失败 → 自动回滚到上一版本                   │
│   · 数据源过慢 → 自动延长窗口 + 通知                    │
│                                                      │
│ 交付物:                                               │
│   · 全自动化管道: 无人干预可持续运行                     │
│   · 自愈成功率 ≥ 90%                                  │
└──────────────────────────────────────────────────────┘
```

### 7.3 从P0桩到真实引擎的切换清单

| 数据源 | 当前状态 | Phase | 真实引擎 | 依赖条件 | 预计工时 |
|-------|---------|-------|---------|---------|---------|
| `enterprise_websites` | 🔴 桩 | 1 | CloakBrowser | 部署CloakBrowser服务 | 40h |
| `url_batch_crawler` | 🔴 桩 | 1 | AI解析管道+Hermes工具 | web_search工具可用 | 24h |
| `qichacha` | 🔴 桩 | 1 | qichacha_client.py | 企查查API Key | 16h |
| `baidu_search` | 🔴 桩 | 2 | Hermes web_search | API配额充足 | 8h |
| `xiaohongshu` | 🔴 桩 | 2 | openclaw脚本 | 小红书Cookie/Token | 24h |
| `user_behavior_feedback` | 🟡 半桩 | 2 | POST反馈API | 前端集成 | 16h |
| `crm_matching_data` | 🔴 桩 | 2 | CRM系统对接 | CRM API开放 | 40h |
| `knowledge_base` | 🟢 可用 | 2 | knowledge_model_service | 知识库数据准备 | 16h |
| `web_pages_rag` | 🔴 桩 | 2 | rag_pipeline爬虫 | 爬虫合规审查 | 24h |

> **图例**: 🟢 已可用 → 🟡 部分可用 → 🔴 桩/未接入

---

## 8. 附录：核心模块清单

### 8.1 管道代码文件

| 文件 | 作用 | 状态 |
|------|------|------|
| `data_pipeline/__init__.py` | 包入口，版本1.0.0 | ✅ 稳定 |
| `data_pipeline/crawler_orchestrator.py` | 爬虫调度器（桩模式） | ✅ 稳定 (待接入真实引擎) |
| `data_pipeline/data_curator.py` | 数据治理：去重+标准化 | ✅ 稳定 |
| `data_pipeline/model_registry.py` | 模型注册表管理 | ✅ 稳定 |
| `data_pipeline/model_feeder.py` | 模型数据供给+训练调度 | ✅ 稳定 |
| `data_pipeline/pipeline_controller.py` | 管道主控制器 | ✅ 稳定 |
| `data_pipeline/data_source_registry.json` | 数据源注册表 (9源) | ✅ 稳定 |
| `data_pipeline/DATA_SOURCE_INVENTORY.md` | **本文档** | ✅ 本文件 |

### 8.2 数据存储文件

| 文件 | 用途 | 格式 |
|------|------|------|
| `.crawler_state.json` | 爬虫状态持久化 | JSON |
| `.data_curator_state.json` | 治理状态 (去重指纹) | JSON |
| `.model_feeder_state.json` | 训练记录持久化 | JSON |

### 8.3 外部依赖

| 模块 | 用途 | 集成状态 |
|------|------|---------|
| `app/services/qichacha_client.py` | 企查查API客户端 | 🔴 待完善 |
| `app/services/training_data_generator.py` | 训练数据生成 | 🔴 待创建 |
| `app/ai/online_learning.py` | 在线学习引擎 | ✅ 已实现 |
| `app/ai/gaia_trainer.py` | Gaia训练器 | 🔴 待创建 |
| `app/ai/gaia_evolution_brain.py` | Gaia进化脑 | 🔴 待创建 |
| `app/ai/recommendation.py` | 推荐引擎 | 🔴 待创建 |
| `app/ai/bandit_engine.py` | 多臂赌博机 | 🔴 待创建 |
| `app/ai/rag_pipeline.py` | RAG管道 | 🔴 待创建 |
| `app/ai/embedding_service.py` | 向量嵌入 | 🔴 待创建 |
| `app/ai/knowledge_graph.py` | 知识图谱 | 🔴 待创建 |

### 8.4 训练脚本清单

| 脚本 | 状态 | 备注 |
|------|------|------|
| `scripts/train_matching_model_v2.py` | ✅ 已实现 (733行) | 三塔模型, 13特征, 防过拟合 |
| `scripts/train_matching_model_v2_mac_mps.py` | ✅ 已实现 | Mac MPS兼容版 |
| `scripts/pretrain_user_tower.py` | ✅ 已实现 | 用户塔预训练 |
| `scripts/prepare_v2_training_data.py` | 🔴 待创建 | V2训练数据准备 |
| `scripts/data_augmentation.py` | 🔴 待创建 | 数据增强 |
| `scripts/enhance_user_data.py` | 🔴 待创建 | 用户数据增强 |

---

> **文档维护**: 本文件与 `data_source_registry.json`、`model_registry.py` 保持同步。
> 每次新增数据源或模型时，请同时更新：
> 1. `data_source_registry.json` — 数据源注册
> 2. `model_registry.py` — 模型注册
> 3. `DATA_SOURCE_INVENTORY.md` — 本文档 (Section 1-2 矩阵表格)
> 4. cron 配置 — 调度表 (Section 5)
