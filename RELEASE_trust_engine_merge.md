# RELEASE — 链客宝信任体系迁移至 AI数智名片

> 分支: `feature/trust-engine-merge`
> 日期: 2026-08-07
> 状态: ✅ 已发布 v1.3.0（三级合并完成，master b4f9b2d + tag v1.3.0-trust-engine）

## 背景

链客宝（已废弃 2026-08-04）核心资产 = 信任体系（trust_engine 三维评分 + 五级分级 + 匹配增强）。
AI数智名片原有 trust 模块仅含简单信任关系（TrustNetwork），缺失深度信任评分能力。
本次将链客宝 trust_engine 全量迁移并适配 AI数智名片异步架构。

## 变更内容

| 文件 | 说明 |
|:-----|:-----|
| `app/trust_engine/` (3文件) | 评分引擎 scoring.py + 五级分级 tier.py + 匹配增强 matching.py |
| `app/models/trust_score.py` | 5 张表模型（Integer user_id 适配） |
| `app/services/trust_score_service.py` | 异步评分服务（对接 get_db 真实数据） |
| `app/routers/trust_score_router.py` | 7 个 API 端点 |
| `alembic/versions/a1b2c3d4e5f6_*.py` | 建表迁移 |
| `alembic/env.py` | 修复既有 bug + 支持 .env DATABASE_URL |
| `tests/test_trust_score_engine.py` | 9 个单元测试 |

## 新增 API 端点

- `GET  /api/v1/trust/score/{user_id}` — 信任评分（公开）
- `GET  /api/v1/trust/score/{user_id}/history` — 评分历史
- `POST /api/v1/trust/score/{user_id}/recalc` — 触发重算
- `GET  /api/v1/trust/qualifications` — 资质列表
- `POST /api/v1/trust/qualifications` — 新增资质（自动重算评分）
- `GET  /api/v1/trust/reviews/{user_id}` — 用户评价（公开）
- `POST /api/v1/trust/reviews` — 发表评价（自动重算被评方）

## 评分机制（H08 阳光下行走，公式公开）

```
TRUST_SCORE = 资质可信度×40% + 交易可信度×35% + 合规健康度×25%
时间衰减: exp(-0.1 × 距最近成交月数)
五级分级: 0-39 待完善 / 40-59 基础 / 60-79 良好 / 80-89 优秀 / 90-100 顶级
匹配增强: Step0 信任预过滤（<最低要求移除, <40降权50%）+ Step7 信任加权(15%)
```

## 验证

- ✅ 语法检查 8 文件全过
- ✅ 单元测试 9/9 通过（评分计算/分级边界/预过滤）
- ✅ 端到端：真实 PG 库写入资质 → 计算 47.54 基础级 → 查询 → 清理
- ✅ 生产库 5 张表已创建（trust_qualifications / trust_score_snapshots / trust_audit_reports / trust_reviews / trust_score_logs）

## 修复的既有问题

1. 链客宝 scoring.py: TransactionData 缺 `months_since_last_trade` 字段（calculate_from_raw_data 引用报错）
2. 链客宝 scoring.py: `qual_data.active_qual_count` 引用不存在字段（改从 ComplianceData 取）
3. AI数智名片 alembic/env.py: `PlatformMember` 应为 `ResourcePlatformMember`（既有 import 错误，导致 alembic 无法运行）
4. AI数智名片 alembic 不读 .env DATABASE_URL（一直连 SQLite），已修复为环境变量优先

## 待确认

1. [ ] 确认合并 develop → release → master
2. [ ] 是否给信任体系加「每日快照 cron」（每天 02:00 全量重算所有用户评分）
