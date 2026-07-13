# 代码清理审计报告

> 生成时间: 2026-07-13  
> 扫描范围: D:/AI数智名片/  
> 审计项: 1)未使用import  2)docs/目录审计  3)归档/备份目录清理方案

---

## 一、未使用 import 扫描结果

使用 `flake8 --select=F401` 对 `app/` 目录进行全量扫描，共发现 **461 个 F401 级别警告**（模块导入但未使用）。

### 1.1 高优先级（业务代码中的废弃导入）

**app/\_\_init\_\_.py**
- Line 4: `import sys` 未使用
- Line 5: `from pathlib import Path` 未使用
- Line 11: `from fastapi.responses import FileResponse` 未使用
- Line 93: `from app.middleware import get_metrics_instance` 未使用

**AI 模块（app/ai/）**
| 文件 | 未使用导入 |
|------|-----------|
| `feedback_loop.py:30` | `import json` |
| `feedback_loop.py:35` | `from dataclasses import field` |
| `gaia_evolution_brain.py:22-23` | `import numpy as np`, `sqlalchemy.desc/and_/update` 共4个 |
| `gaia_flywheel.py:43` | `GaiaKnowledge`, `GaiaEvolutionEvent`, `GaiaTrainingRun`, `GaiaModelWeights` |
| `gaia_trainer.py:18,22` | `import numpy as np`, `VectorSearchIndex`, `embed_text` |
| `knowledge_graph.py:14,19` | `import json`, `sqlalchemy.func/union` |
| `recommendation.py:23-39` | 11个导入全部未使用（含`json`, `sqlalchemy.func`, `FeedbackLoop`等） |
| `vector_search.py:27-34` | `json`, `math`, `collections.Counter` |
| `mcp_adapter.py:125,181-182` | `asyncio`, `stdio_server`, `ListToolsRequest` 等5个 |

**路由模块（app/routers/）**
| 文件 | 未使用导入 |
|------|-----------|
| `ab_test.py:15,21` | `pydantic.Field`, `ABTestingEngine`, `SignificanceTester` |
| `app_store.py:39` | `app.core.response.api_error` |
| `brochure.py:1,5` | `import json`, `fastapi.Form` |
| `docs.py:6` | `fastapi.Request` |
| `docs_portal_router.py:13,16` | `os`, `fastapi.Request` |
| `export.py:8,12,17` | `fastapi.HTTPException/Query`, `joinedload`, `UserTag` |
| `gaia_router.py:9,16-17` | `typing.Any`, `GaiaEvolutionBrain`, `GaiaTrainer` |
| `gdpr.py:15` | `fastapi.HTTPException/status` |
| `match.py:4` | `fastapi.File` |
| `oauth.py:13` | `app.config.settings` |
| `payment.py:9,17-18` | `fastapi.status`, `format_date`, `ProductConfig` |
| `recommend.py:17,24-25` | `FeedbackLoop`, `apply_feedback_boost`, `FeedbackAction` 等5个 |
| `sso.py:11,14,26,244` | `timedelta`, `httpx`, `TokenResponse`, `get_current_user` |
| `tag.py:9` | `TagInput` |
| `user.py:1` | `fastapi.HTTPException` |
| `webhooks.py:32` | `sqlalchemy.delete` |

**服务模块（app/services/）**
| 文件 | 未使用导入 |
|------|-----------|
| `brochure.py:11` | `app.models.user.User` |
| `calendar_tencent.py:39-41,229` | `hashlib`, `hmac`, `json`, `re` |
| `crm_bridge.py:10` | `import requests` |
| `dedup.py:5` | `typing.Tuple` |
| `importer.py:15` | `NAME_SIMILARITY_THRESHOLD` |
| `knowledge_graph.py:21` | `app.models.brochure.Brochure` |
| `matching_engine.py:3,8,13` | `typing.Optional`, `DocumentBuilder`, `cosine_similarity`, `cache.invalidate` |
| `recommend_service.py:12-21` | 7个导入未使用（含`field`, `Enum`, `get_feedback_loop`等） |
| `sales_prediction.py:437,542` | `crm_models.CrmContact/CrmPipelineStage` (重复2次) |
| `media_service.py:7` | `import os` |
| `sla_monitor.py:23,29,31` | `os`, `timedelta`, `typing.Optional` |
| `sso_service.py:9` | `import json` |

**中间件（app/middleware/）**
| 文件 | 未使用导入 |
|------|-----------|
| `api_key.py:10,14,17` | `asyncio`, `HTTPException`, `AsyncSession` |
| `audit.py:17,20` | `datetime.datetime`, `sqlalchemy.select` |
| `logging_middleware.py:21` | `ContextVar` |
| `metrics.py:16` | `functools.wraps` |
| `otel.py:137` | `FastAPIInstrumentor` |
| `rate_limit_middleware.py:28` | `defaultdict` |
| `rbac.py:16` | `get_permissions_for_role`, `has_permission` |
| `sso.py:12` | `HTTPException`, `status` |

**模型模块（app/models/）— 大量 SQLAlchemy 类型被全局导入但未直接使用**
> 约30个模型文件存在相同的模式：从 `sqlalchemy` 导入 `String, DateTime, Float, Boolean, Text, ForeignKey` 等类型，但模型中实际使用 `Column(Integer)` / `Column(String(...))` 形式，这些顶层导入未使用。
> 典型文件：`activity.py`, `api_usage_log.py`, `business_card.py`, `business_need.py`, `contract.py`, `deal.py`, `enterprise.py`, `order.py`, `product.py`, `subscription.py`, `wallet.py` 等。

### 1.2 清理建议

1. **高优先级（15+个）**：`app/ai/recommendation.py`（11个无用导入）、`app/routers/recommend.py`（5个）、`app/services/recommend_service.py`（7个）、`app/routers/sso.py`（4个）— 这些是核心业务逻辑，建议立即清理
2. **中优先级（约60个）**：各 router/service/middleware 文件中独立的废弃导入 — 逐个文件清理
3. **低优先级（约380个）**：约30个模型文件中重复的 `sqlalchemy` 类型导入 — 这些是模板遗留，可通过统一导入模式消除（建议用 `from sqlalchemy import Column, Integer, String as ColString` 替代）

**总工作量估计**：约 80 个文件需要修改，每文件 1-3 行删除。

---

## 二、docs/ 目录审计

### 2.1 双 docs 目录分析

发现 **两个独立 docs 目录**：

| 路径 | 文件数 | 领域 |
|------|--------|------|
| `backend/docs/` | 38 | 后端架构、部署、ADR、API 版本化、定价引擎等 |
| `/docs/`（根目录） | 43 | 运营、合规(SOC2)、集成、产品、测试、安全等 |

### 2.2 重叠内容检查

存在明显内容重叠的文档：

| 主题 | backend/docs 版本 | root/docs 版本 | 状态 |
|------|------------------|----------------|------|
| API 设计规范 | `backend/docs/api/STANDARDS.md` (2026-06-26) | `/docs/API_STANDARDS.md` | 重复，内容应统一 |
| SLA | `backend/docs/deployment/SLA.md` | `/docs/SLA.md` | 重复 |
| 安全 | 无对应 | `/docs/SECURITY.md` | 仅根目录有 |
| 可观测性 | `backend/docs/observability/` | `/docs/OBSERVABILITY.md` | 拆分不合理 |
| SOC2 | 无对应 | `/docs/soc2/` + `/docs/compliance/SOC2_*` | 仅根目录有 |
| 部署 | `backend/docs/deployment/` | `/docs/ops/` | **高度重叠**（`DEPLOYMENT_CHECKLIST` vs `PREVIEW_DEPLOY/LAUNCH_CHECKLIST`） |

### 2.3 过时文档标记

以下文档可能已过时或需更新：

| 文档 | 最后更新 | 问题 |
|------|---------|------|
| `backend/docs/OPEN_API_V1.md` | 2026-06-26 | 2862行的巨型 V1 文档，与 `api/OPENAPI.md` 内容重叠 |
| `backend/docs/adr/ADR-004` | 2026-06-26 | 标题"47个Router"，但实际已有65+个，数量已过时 |
| `backend/docs/api_portal_migration_plan.md` | 无日期 | 引用 `D:\\链客宝\\` 旧路径，是迁移旧项目的计划文档，**任务已完成，可归档** |
| `backend/docs/DEVELOPER_PORTAL.md` | 无日期 | 开发者门户文档，需确认是否已实施完成 |
| `root/docs/全自动版本开发协议.md` | 无日期 | 命名不规范（中文文件名），与 `开发版本管理最佳实践.md` 内容可能有重叠 |

### 2.4 清理建议

1. **立即归档**：`backend/docs/api_portal_migration_plan.md` — 旧项目迁移计划，任务已结束
2. **统一合并**：将 `root/docs/API_STANDARDS.md` 合并到 `backend/docs/api/STANDARDS.md`，删除根目录副本
3. **统一合并**：将 `root/docs/SLA.md` 合并到 `backend/docs/deployment/SLA.md`
4. **去重治理**：梳理 `root/docs/ops/` 与 `backend/docs/deployment/`，合并相同主题文档
5. **更新标记**：`ADR-004.md` 标题从"47个Router"改为"65+个Router"以反映实际情况
6. **重命名**：`root/docs/全自动版本开发协议.md` 和 `root/docs/开发版本管理最佳实践.md` 改为英文命名
7. **建立索引**：两个 docs 目录之间缺少交叉引用，建议在 `backend/docs/INDEX.md` 中增加 root docs 的引用链接

---

## 三、归档目录清理方案

### 3.1 现有归档/备份目录总览

| 目录 | 大小 | 内容 | 状态 |
|------|------|------|------|
| `/_archive/` | **49 MB** | 4个子目录：App原型(151K)、WebComponent(45M)、小程序(122K)、整体项目备份(3.2M) | ✅ 已归档，有描述 |
| `/_backups/` | 196K | 2026-07-11 的快照 + backup.log | 🔶 可清理 |
| `/backups/` | 33K | `api_key_system` 子目录 | 🔶 可清理 |
| `/backend/tests_bak/` | 80K | 5个测试备份文件(test_api.py等) | 🔶 可清理 |
| `/miniapp_bak/` | 132K | 完整的小程序备份(含组件/页面/图片) | 🔶 可清理 |
| 根目录 `soc2_audit_package.zip` | 25K | SOC2审计包zip | 🔶 确认是否可删 |

### 3.2 `_archive/` 详细分析

| 子目录 | 大小 | 建议 |
|--------|------|------|
| `AI数字名片App/` | 151K | App原型，已归档，可保留 |
| `AI数字名片WebComponent/` | **45 MB** | WebComponent 旧版本，最大文件，如已不再引用可删除 |
| `AI数字名片小程序/` | 122K | 小程序旧版本，可保留 |
| `AI数智名片_backup_20260628_071339/` | 3.2M | 全量备份快照，建议保留3个月，可标记清理日期 |
| `backup_script.py` | 4K | 备份脚本，可保留 |

### 3.3 清理建议

#### 建议立即删除（确认无引用后）
1. **`/backend/tests_bak/`（80K）** — tests/ 目录已有最新测试文件，这些 bak 是旧版本，完全可删除
2. **`/miniapp_bak/`（132K）** — `miniapp/` 目录是当前版本，bak 已无用途，可删除
3. **`/_backups/2026-07-11/`（196K）** — 两周前的增量备份，确认版本无回滚需要后删除
4. **`/backups/api_key_system/`（33K）** — 旧备份，确认后删除

#### 建议有条件删除
5. **`/_archive/AI数字名片WebComponent/`（45 MB）** — 占用最大空间，确认 `frontend/` 目录已完全替代后删除
6. **`/_archive/AI数智名片_backup_20260628_071339/`（3.2M）** — 超过两周的项目全量备份，可考虑清理

#### 建议保留
7. **`/_archive/AI数字名片App/`（151K）** — 产品原型归档
8. **`/_archive/AI数字名片小程序/`（122K）** — 小程序历史版本归档
9. **`/_archive/backup_script.py`（4K）** — 备份脚本，方便未来使用

#### 总空间回收预期
- 立即删除：~441K + 1个目录结构
- 有条件删除：~48.2 MB（主要是 WebComponent）
- **最大可回收：~48.6 MB**

---

## 四、liankebao-weapp 分离状态确认

| 检查项 | 结果 |
|--------|------|
| 独立项目结构 | ✅ 是 — 自有 `package.json`, `tsconfig.json`, `project.config.json` |
| 技术栈 | 基于 **Taro 3.6**（跨端框架）+ React 18 + TypeScript |
| 与 backend 耦合关系 | ✅ **已分离** — 无直接代码依赖，通过 REST API 通信 |
| 是否可独立构建 | ✅ 是 — 有独立的 `build:weapp` 脚本 |
| 建议 | **保持当前状态**，liankebao-weapp 作为独立小程序项目维护即可 |

---

## 五、清理建议总清单（优先级排序）

| 优先级 | 类别 | 项 | 预计工作量 |
|--------|------|----|-----------|
| **P0** | import | 清理 `app/ai/recommendation.py`（11个无用导入） | 5分钟 |
| **P0** | import | 清理 `app/routers/sso.py`（4个无用导入，含 `httpx`） | 3分钟 |
| **P0** | import | 清理 `app/routers/recommend.py`（5个无用导入） | 3分钟 |
| **P0** | import | 清理 `app/services/recommend_service.py`（7个无用导入） | 5分钟 |
| **P0** | import | 清理 `app/services/sales_prediction.py`（重复无用导入） | 3分钟 |
| **P1** | archive | 删除 `backend/tests_bak/` | 1分钟 |
| **P1** | archive | 删除 `miniapp_bak/` | 1分钟 |
| **P1** | archive | 删除 `_backups/` 旧快照 | 1分钟 |
| **P1** | archive | 删除 `backups/api_key_system/` | 1分钟 |
| **P1** | docs | 归档 `api_portal_migration_plan.md` | 1分钟 |
| **P1** | docs | 更新 ADR-004 标题（47→65+） | 2分钟 |
| **P2** | import | 清理各 router/service/middleware 中约60个独立无用导入 | 30分钟 |
| **P2** | docs | 合并 root/docs 与 backend/docs 的重叠内容 | 1小时 |
| **P2** | docs | 根目录2个中文命名文档改为英文 | 5分钟 |
| **P2** | archive | 清理 `_archive/WebComponent`（45MB）— 确认后删除 | 5分钟 |
| **P2** | archive | 清理 `_archive/backup_20260628`（3.2MB） | 2分钟 |
| **P3** | import | 约30个模型文件的 SQLAlchemy 类型导入统一优化 | 40分钟 |
| **P3** | docs | 建立双 docs 目录交叉引用索引 | 20分钟 |

**总计可回收空间**: 立即 ~440KB + 有条件 ~48MB = **~48.6 MB**  
**总计代码清理**: 约 80 个文件需修改，约 460 行无用 import 语句
