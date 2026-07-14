# AI数智名片 — 匹配引擎全量状态盘点报告 (SAG盘点)

> **日期**: 2026-07-13 | **分析范围**: 路由、服务、数据、模型、训练管道

---

## 一、当前数据量统计

### 1.1 数据库概览

| 数据库 | 大小 | 状态 |
|--------|------|------|
| `digital_brochure.db` | **1.8 MB** | WAL模式，活跃使用中（含SHM+WAL日志） |
| `feedback.db` | 44 KB | 少量反馈数据 |
| `online_learning.db` | 40 KB | 在线学习状态存储 |
| `vector_index.db` | — | 向量索引（位于 app/data/） |

> ⚠️ `sqlite3` CLI 当前不可用，无法精确获取表行数。以下为估算:

| 数据项 | 估算值 | 来源 |
|--------|--------|------|
| 用户数 | **~15-30** | training_data.json 含15个用户ID |
| 标签总数 | 数百 | 15用户 × 平均10-20标签/用户 |
| 匹配记录数 | ~数十 | training_data中26条正样本来源 |
| 反馈记录 | **极少** | feedback.db仅44KB |

### 1.2 训练数据统计

| 指标 | 数值 |
|------|------|
| 总样本数 | **104** |
| 正样本数 | **26** |
| 负样本数 | **78** (3:1负采样比) |
| 用户数 | **15** |
| 特征数 | **10** |
| 数据文件 | `training_data.json` (53KB) |

**特征列表**: tag_overlap_score, common_tag_count, overlap_provide_to_need, overlap_need_to_provide, vector_semantic, tag_count_a, tag_count_b, avg_weight_a, avg_weight_b, tag_weight_score

---

## 二、当前匹配引擎架构

### 2.1 API 路由 (`match_v2.py`)

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v2/match/recommend` | POST | 每日推荐（V2五层评分 + 可选协同过滤） |
| `/api/v2/match/diverse` | POST | 多样性推荐（混合搜索 + MMR重排序） |
| `/api/v2/match/explain` | POST | 匹配理由解释（四头注意力详情） |
| `/api/v2/match/stats` | GET | 引擎状态查询 |

### 2.2 五层评分架构 (`matching_engine_v2.py`)

```
综合评分 = tag_overlap         × 0.35  ← 供需标签重叠
         + vector_semantic    × 0.25  ← 向量语义相似度
         + tag_weight         × 0.10  ← 标签兴趣强度
         + industry_complement × 0.20 ← 行业互补（10类）
         + attention_score     × 0.10 ← 四头注意力匹配
```

**行业分类**: 10类 (AI/科技, 金融/投资, 制造/工业, 教育/培训, 医疗/健康, 地产/物业, 电商/零售, 法律/合规, 品牌/营销, 传媒/内容)

**供需映射**: 7个源头行业 → 目标行业映射（如 AI/科技 → 制造/工业, 医疗/健康, 教育/培训, 金融/投资）

**注意力四头**: 行业头 / 能力头 / 地区头 / 热度头 (temperature=0.8, 所有用户hotness=0.5硬编码)

### 2.3 V2 能力清单

```
✓ 五层综合评分引擎 (V2)          ✓ 头部注意力匹配 (四头)
✓ MMR 多样性重排序                ✓ ItemBasedCF 协同过滤
✓ UserBasedCF 协同过滤            ✓ 行业互补分析 (10类)
✓ 混合搜索 (关键词+向量)          ✓ 反馈闭环
✓ 在线学习管道                     ✓ 三塔模型推理（代码级）
✓ 向量语义搜索                     ✓ 匹配可解释性
```

### 2.4 三塔 ML 模型 (`ml/` 目录)

| 模块 | 架构 | 输出 | 训练状态 |
|------|------|------|----------|
| `user_tower.py` | DNN: 256→128 → L2-Norm | **128d** 用户嵌入 | ❌ **未训练** |
| `enterprise_tower.py` | BN→DNN: 256→128 → L2-Norm | **128d** 企业嵌入 | ❌ **未训练** |
| `behavior_tower.py` | TransformerEncoder→MeanPool→128d | **128d** 行为嵌入 | ❌ **仅模拟数据** |
| `tower_ensemble.py` | 三塔集成评分 + OnlineWeightOptimizer | **[0,1]评分** | ❌ **未训练/集成** |
| `three_tower_model.py` (scripts) | 重叠(4→8→4) + 语义(1→4→2) + 权重(5→8→4) → 合并→Sigmoid | **[0,1]评分** | ✅ **已训练** (14KB .pt文件) |

### 2.5 ThreeTowerModel 训练指标 (`training_report.json`)

| 指标 | 值 | 分析 |
|------|-----|------|
| Accuracy | **0.9524** | ⚠️ 疑似过拟合（104样本, 20%验证集≈20条） |
| Precision | 0.8333 | — |
| Recall | **1.0** | ⚠️ 全部正样本都召回（极端） |
| F1 | 0.9091 | — |
| AUC | **1.0** | ⚠️ 完美AUC极其可疑 |

**特征重要性排序**（Top 5）:
| 特征 | 重要性 | 所属塔 |
|------|--------|--------|
| avg_weight_a | **0.9691** | Tower 3 (标签权重) |
| tag_weight_score | **0.9597** | Tower 3 (标签权重) |
| avg_weight_b | **0.9154** | Tower 3 (标签权重) |
| tag_count_a | **0.8026** | Tower 3 (标签权重) |
| tag_count_b | 0.3180 | Tower 3 (标签权重) |
| ... | | |
| vector_semantic | **0.0001** | ❌ 被模型完全忽略 |

底层数据在 `/d/AI数智名片/backend/analysis/` 目录下，通过本文档可访问完整分析。

Generated report saved to `D:\AI数智名片\backend\analysis\matching_engine_sag_report.md`

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="todo">
<｜｜DSML｜｜parameter name="todos" string="false">[{"content":"检查 V2路由完整端点 match_v2.py","id":"1","status":"completed"},{"content":"检查 matching_engine_v2.py 五层评分架构","id":"2","status":"completed"},{"content":"检查 training_data.json 数据量+特征","id":"3","status":"completed"},{"content":"检查 matching_model.pt 模型可加载性","id":"4","status":"completed"},{"content":"检查 training_report.json 训练指标","id":"5","status":"completed"},{"content":"检查 digital_brochure.db 数据库统计","id":"6","status":"completed"},{"content":"检查 ml/ 目录结构","id":"7","status":"completed"},{"content":"检查 scripts/ 目录下的训练脚本","id":"8","status":"completed"},{"content":"汇总输出完整盘点报告","id":"9","status":"completed"}]