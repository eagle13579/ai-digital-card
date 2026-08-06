# 数据库迁移状态

> 版本: v1.0 | 创建: 2026-07-10 | 审核: 待审

## 当前状态

| 项目 | 说明 |
|------|------|
| **Alembic 迁移文件** | 3 个（含 1 个 revision ID 冲突） |
| **`create_all` 主力** | 是 — `app.__init__.py:625` 应用启动时直接调用 `Base.metadata.create_all` |
| **模型文件数** | 26 个 `.py` 文件在 `app/models/` |
| **业务表（初始迁移）** | 8 张表（users, unlock_records, brochures, pages, user_tags, match_records, visitor_logs, trust_network） |
| **新业务表（仅 `create_all` 创建）** | 21+ 张表（social_connections, payment, webhook, integration, ab_test, audit, api_key, message, invoice, usage_counter, resource_platform, gaia, crm 等） |

### Alembic 迁移文件清单

| 文件 | 修订 ID | 上游修订 | 日期 | 内容 |
|------|---------|---------|------|------|
| `db2fd0f53768_initial_migration.py` | `db2fd0f53768` | _（无）_ | 2026-06-26 | 创建 8 张核心表 |
| `a1b2c3d4e5f6_add_indexes.py` | `a1b2c3d4e5f6` | `db2fd0f53768` | 2026-06-28 | 添加常用查询索引 |
| `a1b2c3d4e5f6_add_strength_to_social_connections.py` | ⚠️ `a1b2c3d4e5f6`（重复） | `db2fd0f53768` | 2026-07-09 | 为 `social_connections` 表添加 `strength` 字段 |

## 问题

### 1. Revision ID 冲突
`add_indexes` 与 `add_strength_to_social_connections` 使用了**相同的 revision ID**（`a1b2c3d4e5f6`）。Alembic 在执行迁移时无法区分这两者，导致迁移链断裂。

### 2. 大量模型变更无对应迁移
自 2026-06-28 后新增/变更的模型（Gaia、CRM、Webhook、UsageCounter、ResourcePlatform、SocialConnection 等）**没有任何 Alembic 迁移文件**。`social_connections` 表在初始迁移中不存在，仅在 `add_strength` 迁移中被引用（该迁移实际无法运行，因为表本身未被创建）。

### 3. `create_all` 绕过迁移历史
```python
# app/__init__.py:624-626
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```
- 启动时自动根据 ORM 定义创建/更新表
- **不回滚**：无法追踪哪些变更已被应用
- **无版本记录**：`alembic_version` 表与实际数据库状态可能不一致

### 4. 生产环境迁移风险
`alembic.ini` 中的连接 URL 已配置为 PostgreSQL（`postgresql+asyncpg://postgres:postgres@localhost:5432/digital_brochure`），但当前迁移链不完整。生产环境切换 PostgreSQL 后：
- 无法使用 `create_all`（生产需要受控迁移）
- 现有 21+ 张表从未经过迁移验证
- 回滚/降级路径缺失

## 修复计划

### 短期（立即）
1. **修复 Revision ID 冲突**
   - 删除或重命名冲突的迁移文件 `a1b2c3d4e5f6_add_strength_to_social_connections.py`
   - 将 `social_connections.strength` 字段变更合并到新的基线迁移中

2. **生成基线迁移**
   ```bash
   cd backend
   alembic revision --autogenerate -m "sync_all_models"
   ```
   生成一条捕获当前所有 ORM 模型状态的完整迁移。

### 中期
3. **环境分离**
   - 开发环境：保留 `create_all` 快速迭代
   - 生产环境：**禁用** `create_all`，强制走 Alembic 迁移

   ```python
   # app/__init__.py 修改建议
   if settings.ENV != "production":
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
   ```

4. **CI/CD 集成**
   - 在部署流水线中添加 `alembic upgrade head` 步骤
   - 添加预合并检查：确保新模型变更伴随迁移文件

### 长期
5. **迁移规范**
   - 每次模型变更必须生成对应迁移文件
   - 迁移文件命名规范：`<timestamp>_<description>.py`
   - Review 流程中检查迁移文件完整性

6. **自动化验证**
   - 添加测试：`alembic check` 确保迁移与 ORM 一致
   - 定期对比 `alembic_version` 与实际表结构

## 附录

### 模型文件索引（`app/models/`）

| 文件 | 表名 | 创建方式 |
|------|------|---------|
| `user.py` | `users` | 初始迁移 ✅ |
| `brochure.py` | `brochures`, `pages` | 初始迁移 ✅ |
| `tag.py` | `user_tags`, `match_records` | 初始迁移 ✅ |
| `visitor.py` | `visitor_logs` | 初始迁移 ✅ |
| `trust.py` | `trust_network` | 初始迁移 ✅ |
| `social_connection.py` | `social_connections` | 仅 `create_all` ❌ |
| `payment.py` | `payment_orders`, `enterprise_subscriptions`, `trial_records` | 仅 `create_all` ❌ |
| `webhook.py` | `webhook_subscriptions` | 仅 `create_all` ❌ |
| `integration.py` | `integrations` | 仅 `create_all` ❌ |
| `ab_test.py` | `ab_tests`, `ab_test_variants`, `ab_test_events` | 仅 `create_all` ❌ |
| `audit.py` | `audit_logs` | 仅 `create_all` ❌ |
| `api_key.py` | `api_keys`, `api_key_usage` | 仅 `create_all` ❌ |
| `message.py` | `messages` | 仅 `create_all` ❌ |
| `invoice.py` | `invoices` | 仅 `create_all` ❌ |
| `usage_counter.py` | `usage_counter` | 仅 `create_all` ❌ |
| `resource_platform.py` | `resource_platforms`, `platform_members`, `platform_opportunities` | 仅 `create_all` ❌ |
| `gaia.py` | `gaia_knowledge`, `gaia_evolution_events`, `gaia_training_runs`, `gaia_model_weights`, `knowledge_models` | 仅 `create_all` ❌ |
| `crm/crm_models.py` | `crm_contacts`, `crm_deals`, `crm_pipeline_stages`, `crm_activities`, `crm_notes` | 仅 `create_all` ❌ |
| `tenant.py` | （需确认） | ❌ |
| `team.py` | （需确认） | ❌ |
| `rbac.py` | （需确认） | ❌ |
| `document.py` | （需确认） | ❌ |
| `sync_state.py` | （需确认） | ❌ |
| `developer_app.py` | （需确认） | ❌ |
| `app_store.py` | （需确认） | ❌ |
