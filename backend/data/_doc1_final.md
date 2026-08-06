# 数据库设计文档 V1.0

> **所属项目**: AI企业数字名片·六度人脉智能匹配系统（链客宝 / liankebao）
> **文档定位**: 阶段3.1 数据库规范整改 —— 数据库设计基线（DBD, Database Design Baseline）
> **编制**: 数智DBA（数据库工程师）
> **日期**: 2026-08-03
> **数据来源**: ① `backend/app/models/` 65 个模型文件实扫（AST 解析）；② 主库 `backend/data/digital_brochure.db`（SQLite，123 表）`sqlite_master` + `PRAGMA table_info/index_list` 实查；③ alembic 迁移目录（`alembic/versions/`，目标 PostgreSQL 18）
> **配套文档**: 《敏感数据加密方案.md》《三环境隔离与备份SOP.md》《索引优化建议.md》
> **铁律声明**: 本文档仅梳理与输出方案，未修改任何生产数据。

---

## 一、文档说明与统计总览

| 指标 | 数值 | 说明 |
|---|---|---|
| 数据库引擎 | SQLite（开发/现状）→ PostgreSQL 18（生产目标） | `backend/app/config.py` 默认 `sqlite+aiosqlite:///./data/digital_brochure.db`；`alembic.ini` 指向 `postgresql+asyncpg://postgres:postgres@localhost:5432/digital_brochure` |
| 总表数 | **123** | `sqlite_master` 实查 |
| 总字段数 | **1085** | `PRAGMA table_info` 实查 |
| 总索引数 | **223** | `PRAGMA index_list` 实查（含 30 个 sqlite_autoindex 唯一约束索引） |
| 有数据表数 | **8** | match_records=7337 / audit_logs=2608 / user_tags=806 / connections=120 / users=104 / trust_network=50 / visitor_logs=25 / brochures=20 |
| 占位表数 | **29** | 仅 `id` 单列，模型为占位桩（见 1.3） |
| 模型文件 | 65 个 | `backend/app/models/*.py` + `app/crm/crm_models.py` |
| 完整模型数 | 51 | 模型列数 ≥ 3 |

### 1.1 数据库文件清单（现状）

| 文件 | 大小 | 用途 |
|---|---|---|
| `backend/data/digital_brochure.db` | 3.2MB | 主库（123 表，业务全量） |
| `backend/data/feedback.db` | 45KB | 反馈库（独立 SQLite） |
| `backend/data/online_learning.db` | 41KB | 在线学习库（独立 SQLite） |
| `backend/data/vector_index.db` | — | 向量索引库（`app/ai/vector_search.py` 定义） |
| `backend/data/digital_brochure.db.bak.20260713_*` | 1.9MB×2 | 存量手工备份 |

### 1.2 三库现状与整改方向

| 库 | 现状 | 整改方向（详见《三环境隔离与备份SOP.md》） |
|---|---|---|
| 开发库 | 本机 SQLite `digital_brochure.db` | 保留 SQLite 或独立 PG 实例，库名 `digital_brochure_dev` |
| 测试库 | 测试用 `:memory:` / `test.db` | 独立 PG 实例，库名 `digital_brochure_test` |
| 生产库 | 目标 PostgreSQL 18 | 库名 `digital_brochure_prod`，独立实例/集群 |

### 1.3 占位表清单（29 张，仅 `id` 列）

> **风险提示**: 以下表在 `models/*.py` 中存在同名模型类，但模型仅声明了 `id` 主键（占位桩），**表结构未落地**。涉及业务功能（如支付流水 `payment_transaction`、钱包 `wallet`、企业 `enterprise`）当前**无真实表结构支撑**，与《项目现状盘点报告V1.0》R4「核心业务表零数据」风险一致。

`activity`、`api_usage_log`、`business_card`、`business_need`、`contact`、`contract`、`deal`、`deal_activity`、`enterprise`、`enterprise_relation`、`import_history`、`match_credit_log`、`membership_order`、`metrics_snapshot`、`online_matching_events`、`online_matching_feedback`、`online_matching_registrations`、`order`、`payment_transaction`、`private_board_order`、`product`、`rate_limit_record`、`review`、`revoked_token`、`subscription`、`user_event`、`wallet`、`wallet_transaction`、`withdrawal`

> ⚠️ **整改建议**: 阶段3.2 逐表补全模型列定义并生成 alembic 迁移；优先 `payment_transaction`（支付链路）、`wallet`/`wallet_transaction`/`withdrawal`（资金链路）、`business_card`/`enterprise`（核心名片与企业画像）。

### 1.4 命名规范（建议基线）

| 对象 | 规范 | 现状符合度 |
|---|---|---|
| 表名 | 复数小写下划线（`users`/`payment_orders`） | ✅ 大部分符合；`order`/`contact`/`product` 单数需评估 |
| 字段名 | 小写下划线（`user_id`/`created_at`） | ✅ 符合 |
| 主键 | `id INTEGER PRIMARY KEY AUTOINCREMENT` | ✅ 全部符合（除 `prompt_templates.id`、`social_connections.id` 为 VARCHAR） |
| 外键 | `*_id` 命名 + `ForeignKey` | 🟡 部分表未声明 FK（如 `match_records`），整改时补全 |
| 时间戳 | `created_at` / `updated_at` | ✅ 核心表具备；`pages`/`match_records` 等缺 `updated_at` |
| 软删除 | `deleted_at` / `is_deleted` | 🟡 仅 `contacts`/`user_relations` 具备，需统一 |

---

## 二、按业务域表结构明细

> 以下所有表均来自对 `digital_brochure.db` 的实查（`PRAGMA table_info` / `PRAGMA index_list` / `SELECT COUNT(*)`），与模型文件交叉核对。字段「说明」列优先取模型 `comment`，无注释处由 DBA 补注（标注 ★）。

---

## A. 用户与认证

### users — 用户主表 ⭐核心表

- **数据量**: 104 行 | **字段数**: 18 | **索引数**: 3（均为 UNIQUE 约束自动索引）

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键，自增 |
| username | VARCHAR(64) | | | | 用户名（唯一）★登录名 |
| phone | VARCHAR(20) | | ✅ | | **手机号（明文，🔴敏感，见加密方案）**，唯一 |
| password_hash | VARCHAR(128) | | ✅ | | 密码哈希（bcrypt/argon2）★ |
| wechat_openid | VARCHAR(64) | | | | 微信 OpenID（唯一，🔴敏感） |
| name | VARCHAR(64) | | ✅ | | 姓名/昵称 |
| company | VARCHAR(128) | | ✅ | | 公司 |
| title | VARCHAR(128) | | ✅ | | 职位 |
| intro | TEXT | | ✅ | | 个人简介 |
| avatar | VARCHAR(256) | | ✅ | | 头像URL |
| role | VARCHAR(16) | | ✅ | | 角色: user/admin（与RBAC并存，盘点4.2风险R3） |
| membership_tier | VARCHAR(16) | | ✅ | | 会员等级: free/gold/diamond/board |
| membership_expires_at | DATETIME | | | | 会员过期时间 |
| membership_synced_at | DATETIME | | | | 最后同步链客宝时间 |
| unlock_quota | INTEGER | | ✅ | | 本月剩余解锁配额 |
| quota_reset_at | DATETIME | | | | 配额重置时间 |
| created_at | DATETIME | | ✅ | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | | ✅ | CURRENT_TIMESTAMP | 更新时间 |

**索引**: `sqlite_autoindex_users_1`(username, UNIQUE)、`sqlite_autoindex_users_2`(phone, UNIQUE)、`sqlite_autoindex_users_3`(wechat_openid, UNIQUE)

**业务说明**: 全系统用户主表，贯通名片/匹配/支付/社群。`phone` 明文存储为🔴高风险项（R1/R2），整改见《敏感数据加密方案.md》；`role` 与 RBAC 三表并存，属4套权限体系之一，阶段2已冻结复核。

---

### user_consents — GDPR 用户同意记录

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 3

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| user_id | INTEGER | | ✅ | | 用户ID |
| consent_type | VARCHAR(64) | | ✅ | | 同意类型（如 privacy/terms） |
| granted | BOOLEAN | | ✅ | | 是否同意 |
| consent_version | VARCHAR(16) | | ✅ | | 版本 |
| source | VARCHAR(64) | | ✅ | | 来源 |
| ip | VARCHAR(45) | | ✅ | | IP |
| user_agent | VARCHAR(512) | | ✅ | | UA |
| detail | TEXT | | ✅ | | 详情 |
| created_at | DATETIME | | ✅ | | 时间 |

**索引**: `idx_consent_user_type`(user_id,consent_type)、`idx_consent_user_created`(user_id,created_at)、`ix_user_consents_user_id`(user_id)

**业务说明**: GDPR 合规（M4-F12~F14 数据导出/审计/删除）依赖，`users` 删除时需级联清理。

---

### revoked_token — 令牌吊销表（占位）

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键（仅占位） |

**业务说明**: ⚠️占位表。令牌吊销功能需要 `token/jti/expires_at` 等列，模型待补全。

---

### user_event — 用户事件表（占位）

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1
- **业务说明**: ⚠️占位表。用户行为事件采集待实现。

---

### invitation_codes — 内测邀请码

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| code | VARCHAR(8) | | ✅ | | 邀请码 |
| batch_id | VARCHAR(32) | | ✅ | | 批次ID |
| max_uses | INTEGER | | ✅ | | 最大使用次数 |
| used_count | INTEGER | | ✅ | | 已用次数 |
| created_by | INTEGER | | ✅ | | 创建人 |
| expires_at | DATETIME | | ✅ | | 过期时间 |
| is_active | BOOLEAN | | ✅ | | 是否有效 |
| remark | TEXT | | ✅ | | 备注 |
| created_at | DATETIME | | ✅ | | 创建时间 |
| updated_at | DATETIME | | ✅ | | 更新时间 |

**索引**: `ix_invitation_codes_code`(code)、`ix_invitation_codes_id`(id)

**业务说明**: M3-F14 内测邀请码：生成/核验/兑换/统计。

---

### tenants — 多租户表

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| name | VARCHAR(128) | | ✅ | | 租户名 |
| slug | VARCHAR(64) | | ✅ | | 唯一标识（唯一约束） |
| plan | VARCHAR(16) | | ✅ | | 套餐 |
| created_at | DATETIME | | ✅ | | 创建时间 |

**索引**: `sqlite_autoindex_tenants_1`(slug, UNIQUE)

**业务说明**: M4-F17 多租户接口；`six_degrees.py` 中 `_IS_MULTI_TENANT` 按 `DATABASE_URL` 是否 PG 判断启用。

---

### api_keys — API Key 管理

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| user_id | INTEGER | | ✅ | | 所属用户 |
| key | VARCHAR(64) | | ✅ | | Key（唯一） |
| name | VARCHAR(128) | | ✅ | | 名称 |
| permissions | TEXT | | ✅ | | 权限列表 |
| rate_limit | INTEGER | | ✅ | | 限流 |
| is_active | BOOLEAN | | ✅ | | 是否启用 |
| last_used_at | DATETIME | | ✅ | | 最后使用时间 |
| created_at | DATETIME | | ✅ | | 创建时间 |
| updated_at | DATETIME | | ✅ | | 更新时间 |

**索引**: `ix_api_keys_user_id`(user_id)、`sqlite_autoindex_api_keys_1`(key, UNIQUE)

**业务说明**: M4-F15 API Key 生命周期管理；`key` 属机密字段，建议加密存储（见加密方案扩展清单）。

---

### api_key_usage — API Key 用量

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| api_key_id | INTEGER | | ✅ | | Key ID |
| date | VARCHAR(10) | | ✅ | | 日期 |
| request_count | INTEGER | | ✅ | | 请求数 |
| created_at | DATETIME | | ✅ | | 创建时间 |

**索引**: `ix_api_key_usage_api_key_id`(api_key_id)

---

### sdk_apps — 开发者 SDK 应用

- **数据量**: 0 行 | **字段数**: 20 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| name | VARCHAR(128) | | ✅ | | 应用名 |
| description | TEXT | | ✅ | | 描述 |
| app_id | VARCHAR(64) | | ✅ | | 应用ID（唯一） |
| app_secret | VARCHAR(128) | | ✅ | | 应用密钥（🔴机密，建议加密） |
| developer_id | INTEGER | | ✅ | | 开发者ID |
| sdk_type | VARCHAR(32) | | ✅ | | SDK类型 |
| platform | VARCHAR(32) | | ✅ | | 平台 |
| status | VARCHAR(16) | | ✅ | | 状态 |
| version | VARCHAR(16) | | ✅ | | 版本 |
| permissions | TEXT | | ✅ | | 权限 |
| redirect_uris | TEXT | | ✅ | | 回调URI |
| icon_url | VARCHAR(512) | | ✅ | | 图标 |
| homepage_url | VARCHAR(512) | | ✅ | | 主页 |
| privacy_policy_url | VARCHAR(512) | | ✅ | | 隐私政策 |
| is_verified | BOOLEAN | | ✅ | | 是否认证 |
| is_public | BOOLEAN | | ✅ | | 是否公开 |
| total_installs | INTEGER | | ✅ | | 安装数 |
| created_at | DATETIME | | ✅ | | 创建时间 |
| updated_at | DATETIME | | ✅ | | 更新时间 |

**索引**: `idx_sdk_developer`、`ix_sdk_apps_developer_id`(developer_id)、`idx_sdk_type_status`、`idx_sdk_status`、`sqlite_autoindex_sdk_apps_1`(app_id, UNIQUE)

---

### developer_rewards / developer_reward_balances / reward_redemptions — 开发者激励

- **数据量**: 各 0 行
- **developer_rewards**(10列): id, developer_id, reward_type, points, reason, source_id, source_desc, status, created_at, issued_at；索引: `ix_developer_rewards_id`, `ix_developer_rewards_developer_id`
- **developer_reward_balances**(6列): id, developer_id, total_points, used_points, balance, updated_at；索引: `ix_developer_reward_balances_id`, `ix_developer_reward_balances_developer_id`
- **reward_redemptions**(8列): id, developer_id, points_spent, redemption_type, quota_amount, description, status, created_at；索引: `ix_reward_redemptions_id`, `ix_reward_redemptions_developer_id`

**业务说明**: 开发者激励积分体系（SDK 分发激励），支撑开发者门户商业闭环。

---

## B. 名片与画册

### brochures — 电子画册 ⭐核心表

- **数据量**: 20 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| user_id | INTEGER | | ✅ | | 所属用户 |
| title | VARCHAR(128) | | ✅ | | 画册标题 |
| cover | VARCHAR(256) | | ✅ | | 封面URL |
| purpose | VARCHAR(32) | | ✅ | | 用途: partner/client/investor/supplier |
| pages_count | INTEGER | | ✅ | | 页数 |
| status | VARCHAR(16) | | ✅ | | 状态: draft/published |
| share_token | VARCHAR(32) | | ✅ | | 分享令牌（唯一） |
| view_count | INTEGER | | ✅ | | 浏览量 |
| album_meta | TEXT | | | | 多媒体元数据 |
| created_at | DATETIME | | ✅ | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | | ✅ | CURRENT_TIMESTAMP | 更新时间 |
| visibility | VARCHAR(16) | | ✅ | 'public' | 可见性 |
| platform_id | INTEGER | | | NULL | 关联平台ID |

**索引**: `sqlite_autoindex_brochures_1`(share_token, UNIQUE)

**业务说明**: M1 核心实体。**缺失索引**: `user_id`、`(user_id,status)` 组合查询高频（列表/状态过滤），见《索引优化建议.md》。

---

### pages — 画册页面

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| brochure_id | INTEGER | | ✅ | | 所属画册 |
| sort_order | INTEGER | | ✅ | | 排序 |
| content_type | VARCHAR(16) | | ✅ | | 内容类型: text/image/video |
| content | TEXT | | ✅ | | 内容 |
| image_url | VARCHAR(256) | | ✅ | | 图片URL |
| media_url | VARCHAR(512) | | ✅ | | 媒体URL |
| ai_summary | TEXT | | ✅ | | AI摘要 |

**业务说明**: 画册页内容。**缺失索引**: `brochure_id`（高频按画册取页，见索引建议）。

---

### business_card — 企业数字名片（占位）

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1
- **业务说明**: ⚠️占位表。M1 名片页 `/u/{username}` 目前基于 `users` 表渲染（`routers/public.py`），本表为链客宝合并占位，待补全名片专属字段（模板/样式/社交链接等）。

---

### nfc_cards — NFC 名片卡

- **数据量**: 0 行 | **字段数**: 7 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| user_id | INTEGER | | ✅ | | 用户 |
| nfc_uid | VARCHAR(64) | | ✅ | | NFC UID（唯一） |
| card_data_json | TEXT | | ✅ | | 卡数据JSON |
| vcard_raw | TEXT | | ✅ | | vCard原文 |
| created_at | DATETIME | | ✅ | | 创建时间 |
| updated_at | DATETIME | | ✅ | | 更新时间 |

**索引**: `ix_nfc_cards_user_id`(user_id)、`ix_nfc_cards_nfc_uid`(nfc_uid)

**业务说明**: M1-F15 分享二维码/NFC 的硬件卡载体。

---

### nfc_tap_records — NFC 打卡记录

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| from_user_id | INTEGER | | ✅ | | 发起方 |
| to_user_id | INTEGER | | ✅ | | 接收方 |
| nfc_uid | VARCHAR(64) | | ✅ | | NFC UID |
| created_at | DATETIME | | ✅ | | 时间 |

**索引**: `ix_nfc_tap_records_from_user_id`(from_user_id)、`ix_nfc_tap_records_to_user_id`(to_user_id)

---

### visitor_logs — 访客记录

- **数据量**: 25 行 | **字段数**: 11 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| brochure_id | INTEGER | | ✅ | | 被访画册 |
| visitor_id | VARCHAR(64) | | ✅ | | 访客标识 |
| visitor_ip | VARCHAR(48) | | ✅ | | 访客IP |
| visitor_name | VARCHAR(64) | | ✅ | | 访客名 |
| source | VARCHAR(32) | | ✅ | | 来源 |
| page_viewed | VARCHAR(64) | | ✅ | | 浏览页 |
| duration | INTEGER | | ✅ | | 停留秒数 |
| interested | BOOLEAN | | ✅ | | 是否感兴趣 |
| contact_msg | TEXT | | ✅ | | 留言 |
| visit_time | DATETIME | | ✅ | | 访问时间 |

**业务说明**: M1-F18 访客记录与兴趣。**缺失索引**: `brochure_id`、`visit_time`（高频按画册查访客，见索引建议）。

---

### referral_links — 分享/推荐链接

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| owner_user_id | INTEGER | | ✅ | | 归属用户 |
| code | VARCHAR(32) | | ✅ | | 推荐码（唯一） |
| title | VARCHAR(100) | | ✅ | | 标题 |
| description | VARCHAR(500) | | ✅ | | 描述 |
| invite_type | VARCHAR(20) | | ✅ | | 邀请类型 |
| redirect_url | VARCHAR(500) | | ✅ | | 跳转URL |
| scan_count | INTEGER | | ✅ | | 扫码数 |
| register_count | INTEGER | | ✅ | | 注册数 |
| is_active | BOOLEAN | | ✅ | | 是否有效 |
| expires_at | DATETIME | | ✅ | | 过期时间 |
| created_at | DATETIME | | ✅ | | 创建时间 |
| updated_at | DATETIME | | ✅ | | 更新时间 |

**索引**: `ix_referral_links_code`(code)、`ix_referral_links_id`、`idx_referral_owner`、`ix_referral_links_owner_user_id`(owner_user_id)

**业务说明**: 名片分享裂变与推荐注册统计。

---

### user_tags — 供需标签 ⭐匹配核心表

- **数据量**: 806 行 | **字段数**: 7 | **索引数**: 0 ⚠️

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| user_id | INTEGER | | ✅ | | 用户ID |
| tag_type | VARCHAR(16) | | ✅ | | 类型: provide(供应)/need(需求) |
| tag | VARCHAR(64) | | ✅ | | 标签词 |
| weight | FLOAT | | ✅ | | 权重 |
| source | VARCHAR(16) | | ✅ | | 来源: manual/ai/import |
| created_at | DATETIME | | ✅ | | 创建时间 |

**业务说明**: M2 供需匹配核心输入（供需标签画像）。**0 索引为🔴高危**：匹配引擎按 `user_id`、`tag_type` 高频查询（806行已出现全表扫描），见《索引优化建议.md》P0 清单。

---

## C. 匹配与推荐

### match_records — 匹配记录 ⭐核心表（7337行）

- **数据量**: 7337 行 | **字段数**: 8 | **索引数**: 0 ⚠️🔴

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| user_a_id | INTEGER | | ✅ | | 匹配方A |
| user_b_id | INTEGER | | ✅ | | 匹配方B |
| match_score | FLOAT | | ✅ | | 匹配得分 |
| status | VARCHAR(16) | | ✅ | | 状态: pending/matched/confirmed |
| common_tags | TEXT | | ✅ | | 共同标签JSON |
| source | VARCHAR(16) | | ✅ | | 来源: auto/manual |
| created_at | DATETIME | | ✅ | | 创建时间 |

**业务说明**: M2 匹配引擎产出。**0 索引为全库最严重性能隐患**：7337 行全表扫描 × 每次推荐请求；`(user_a_id,user_b_id)` 唯一对去重查询、`status` 过滤、`match_score` 排序均为高频路径，P0 建索引见《索引优化建议.md》。**缺 FK 声明**（模型 `tag.py` 中 `MatchRecord` 用 ForeignKey 但 SQLite 建表未落 FK），整改时补全。

---

### unlock_records — 付费解锁记录

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| user_id | INTEGER | | ✅ | | 解锁方用户ID |
| target_user_id | INTEGER | | ✅ | | 被解锁用户ID |
| match_record_id | INTEGER | | ✅ | | 关联匹配记录ID |
| created_at | DATETIME | | ✅ | | 创建时间 |

**业务说明**: M2-F06 付费解锁联系方式（幂等/配额扣减）的流水。**缺失索引**: `(user_id,target_user_id)` 幂等检查高频，见索引建议。

---

### match_credit_log — 匹配积分流水（占位）

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1
- **业务说明**: ⚠️占位表。匹配积分/信用流水待实现。

---

### online_matching_events / online_matching_feedback / online_matching_registrations — 在线匹配三表（占位）

- **数据量**: 各 0 行 | **字段数**: 各 1 | **索引数**: 各 1
- **业务说明**: ⚠️三张均为占位表。`__init__.py` 中已导入 `OnlineMatchingFeedback/OnlineMatchingEvent/OnlineMatchingRegistration` 模型，但仅 `id` 列，在线撮合功能待实现。

---

### six_degree_path_cache — 六度路径缓存

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| from_user_id | INTEGER | | ✅ | | 起点用户 |
| to_user_id | INTEGER | | ✅ | | 终点用户 |
| path_json | TEXT | | ✅ | | 路径JSON |
| path_length | INTEGER | | ✅ | | 路径长度 |
| total_trust_score | FLOAT | | ✅ | | 信任总分 |
| hit_count | INTEGER | | ✅ | | 命中次数 |
| expires_at | DATETIME | | ✅ | | 过期时间 |
| created_at | DATETIME | | | | 创建时间 |
| updated_at | DATETIME | | | | 更新时间 |

**索引**: `idx_path_cache_expires`(expires_at)、`ix_six_degree_path_cache_from_user_id`(from_user_id)、`ix_six_degree_path_cache_id`、`ix_six_degree_path_cache_to_user_id`(to_user_id)、`sqlite_autoindex_six_degree_path_cache_1`(from_user_id,to_user_id, UNIQUE)

**业务说明**: M2-F14 六度路径查找结果缓存，唯一约束保证 (from,to) 单条缓存。

---

### user_relations — 六度关系主表

- **数据量**: 0 行 | **字段数**: 18 | **索引数**: 6

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| from_user_id | INTEGER | | ✅ | | 关系发起方 |
| to_user_id | INTEGER | | ✅ | | 关系接收方 |
| relation_type | VARCHAR(20) | | ✅ | | 关系类型 |
| label | VARCHAR(100) | | | | 标签 |
| trust_score | FLOAT | | ✅ | | 信任度 0~1 |
| interaction_count | INTEGER | | ✅ | | 互动次数 |
| last_interaction_at | DATETIME | | | | 最近互动时间 |
| bidirectional | BOOLEAN | | ✅ | | 是否双向 |
| is_active | BOOLEAN | | ✅ | | 是否有效 |
| source | VARCHAR(30) | | | | 来源 |
| source_detail | VARCHAR(200) | | | | 来源详情 |
| version | BIGINT | | ✅ | | 乐观锁版本号 |
| created_at | DATETIME | | | | 创建时间 |
| updated_at | DATETIME | | | | 更新时间 |
| deleted_at | DATETIME | | | | 软删除时间 |
| is_deleted | BOOLEAN | | | | 是否删除 |
| organization_id | INTEGER | | | | 组织ID |

**索引**: `idx_user_relation_active`、`ix_user_relations_from_user_id`(from_user_id)、`ix_user_relations_id`、`ix_user_relations_to_user_id`(to_user_id)、`idx_user_relation_to`、`sqlite_autoindex_user_relations_1`(from_user_id,to_user_id,relation_type, UNIQUE)

**业务说明**: M2-F15 六度关系建立/查询/信任度更新；`version` 乐观锁防并发覆盖；BFS 遍历依赖 from/to 双向索引。

---

### relation_events — 关系变更事件

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| relation_id | INTEGER | | ✅ | | 关系ID |
| from_user_id | INTEGER | | ✅ | | 发起方 |
| to_user_id | INTEGER | | ✅ | | 接收方 |
| event_type | VARCHAR(30) | | ✅ | | 事件类型 |
| old_trust_score | FLOAT | | ✅ | | 旧信任度 |
| new_trust_score | FLOAT | | ✅ | | 新信任度 |
| reason | VARCHAR(200) | | ✅ | | 原因 |
| metadata_json | TEXT | | ✅ | | 元数据 |
| created_at | DATETIME | | ✅ | | 时间 |

**索引**: `ix_relation_events_created_at`、`ix_relation_events_to_user_id`、`ix_relation_events_relation_id`、`ix_relation_events_from_user_id`、`ix_relation_events_id`

**业务说明**: 信任度变更审计事件流（M2-F15 写审计事件）。

---

### trust_network — 信任网络

- **数据量**: 50 行 | **字段数**: 4 | **索引数**: 0 ⚠️

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| user_id | INTEGER | | ✅ | | 用户 |
| trusted_user_id | INTEGER | | ✅ | | 信任的用户 |
| created_at | DATETIME | | ✅ | | 时间 |

**业务说明**: M3-F07 信任网络（简单版）。**缺失索引**: `user_id` 查询高频（M2-F13 六度网络 min_trust 过滤），见索引建议。

---

### connections — 人脉连接（120行）

- **数据量**: 120 行 | **字段数**: 9 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| user_id | INTEGER | | ✅ | | 用户 |
| contact_id | INTEGER | | ✅ | | 联系人用户ID |
| source | VARCHAR(32) | | ✅ | | 来源 |
| status | VARCHAR(16) | | ✅ | | 状态: pending/accepted |
| strength | FLOAT | | ✅ | | 关系强度 |
| label | VARCHAR(64) | | ✅ | | 标签 |
| created_at | DATETIME | | ✅ | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | | ✅ | CURRENT_TIMESTAMP | 更新时间 |

**索引**: `sqlite_autoindex_connections_1`(user_id,contact_id, UNIQUE)

**业务说明**: M3-F04/F05 人脉连接请求→审批闭环。**缺失索引**: `status`（待办列表过滤）、`contact_id` 反向查询，见索引建议。

---

### social_connections — 社交连接（链客宝合并）

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | VARCHAR(36) | ✅ | ✅ | | 主键（UUID） |
| user_id | INTEGER | | ✅ | | 用户 |
| contact_id | INTEGER | | ✅ | | 联系人 |
| source | VARCHAR(32) | | ✅ | | 来源 |
| message | TEXT | | ✅ | | 消息 |
| status | VARCHAR(16) | | ✅ | | 状态 |
| strength | FLOAT | | ✅ | | 强度 |
| created_at | DATETIME | | ✅ | | 创建时间 |
| updated_at | DATETIME | | ✅ | | 更新时间 |

**索引**: `sqlite_autoindex_social_connections_1`(user_id,contact_id, UNIQUE)

**业务说明**: 与 `connections` 功能重叠（4套权限体系同源问题在连接域也有体现），建议评估合并。

---

## D. 人脉与CRM

### contacts — 通讯录导入联系人（隐私加密范式表）⭐参考实现

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| user_id | INTEGER | | ✅ | | 归属用户ID |
| name | VARCHAR(64) | | ✅ | | 联系人姓名 |
| phone_hash | VARCHAR(64) | | ✅ | | 手机号 SHA-256 哈希（去重用） |
| phone_enc | TEXT | | ✅ | | 手机号 Fernet 加密密文 |
| phone_last4 | VARCHAR(4) | | ✅ | | 手机号后4位（展示用） |
| company | VARCHAR(128) | | ✅ | | 公司 |
| position | VARCHAR(128) | | ✅ | | 职位 |
| source | VARCHAR(16) | | ✅ | | 来源: wechat/csv/manual |
| is_matched | SMALLINT | | ✅ | | 是否已匹配处理 |
| matched_user_id | INTEGER | | | | 匹配到的平台用户ID |
| created_at | DATETIME | | ✅ | | 创建时间 |
| updated_at | DATETIME | | ✅ | | 更新时间 |
| deleted_at | DATETIME | | | | 软删除时间 |

**索引**: `ix_contacts_user_id`(user_id)

**业务说明**: M3-F01 通讯录导入。**本表是「不落明文手机号」的标杆实现**（hash+enc+last4），《敏感数据加密方案.md》将以其模式推广到 `crm_contacts`/`users`。⚠️ 盘点 R1 指出本表 0 行未经验证；导入逻辑（`routers/contacts.py`）需真实数据验证。

---

### import_history — 导入历史（占位）

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1
- **业务说明**: ⚠️占位表。通讯录导入批次历史待实现。

---

### crm_contacts — CRM 联系人（🔴明文敏感字段）

- **数据量**: 0 行 | **字段数**: 20 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| owner_id | INTEGER | | ✅ | | CRM所属用户 |
| user_id | INTEGER | | | | 关联的平台用户(名片交换对方) |
| name | VARCHAR(128) | | ✅ | | 姓名 |
| phone | VARCHAR(32) | | ✅ | | **手机号（明文🔴，见加密方案）** |
| email | VARCHAR(128) | | ✅ | | **邮箱（明文🔴，见加密方案）** |
| company | VARCHAR(256) | | ✅ | | 公司 |
| title | VARCHAR(128) | | ✅ | | 职位 |
| department | VARCHAR(128) | | ✅ | | 部门 |
| avatar | VARCHAR(512) | | ✅ | | 头像URL |
| intro | TEXT | | ✅ | | 个人简介/备注 |
| source | VARCHAR(16) | | ✅ | | 来源: match/manual/visitor/import |
| source_record_id | INTEGER | | | | 来源记录ID(如MatchRecord.id) |
| tags | TEXT | | ✅ | | 联系人标签(JSON数组) |
| pipeline_stage_id | INTEGER | | | | 当前管道阶段 |
| deal_value | NUMERIC(12, 2) | | | | 预估成交金额 |
| deal_currency | VARCHAR(8) | | ✅ | | 币种 |
| last_contacted_at | DATETIME | | | | 最后联系时间 |
| created_at | DATETIME | | ✅ | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | | ✅ | CURRENT_TIMESTAMP | 更新时间 |

**索引**: `ix_crm_contacts_user_id`(user_id)、`ix_crm_contacts_owner_id`(owner_id)

**业务说明**: 内置 CRM 联系人主表。**🔴 R1 风险: `phone`/`email` 明文存储 20 列**。整改优先级最高：新增 `phone_hash`/`phone_enc`/`phone_last4` 与 `email_hash`/`email_enc` 列，迁移+回滚方案见《敏感数据加密方案.md》。

---

### crm_deals — CRM 商机

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| owner_id | INTEGER | | ✅ | | 归属用户 |
| contact_id | INTEGER | | ✅ | | 关联联系人 |
| pipeline_stage_id | INTEGER | | ✅ | | 管道阶段 |
| title | VARCHAR(256) | | ✅ | | 标题 |
| value | NUMERIC(12, 2) | | ✅ | | 金额 |
| currency | VARCHAR(8) | | ✅ | | 币种 |
| probability | FLOAT | | ✅ | | 赢单概率 |
| expected_close_date | DATETIME | | ✅ | | 预计成交日 |
| status | VARCHAR(16) | | ✅ | | 状态 |
| lost_reason | TEXT | | ✅ | | 丢单原因 |
| created_at | DATETIME | | ✅ | | 创建时间 |
| updated_at | DATETIME | | ✅ | | 更新时间 |

**索引**: `ix_crm_deals_contact_id`(contact_id)、`ix_crm_deals_owner_id`(owner_id)

---

### crm_pipeline_stages — 销售管道阶段

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 1
- 字段: id, user_id(索引), name, sort_order, color, is_default, is_closed, win_probability, created_at
- **业务说明**: 销售管道自定义阶段（默认+用户自定义）。

---

### crm_notes — CRM 备注

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 1
- 字段: id, owner_id(索引), contact_id, deal_id, content, is_pinned, created_at, updated_at

---

### crm_activities — CRM 活动

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 2
- 字段: id, owner_id(索引), contact_id(索引), deal_id, activity_type, title, description, source_model, source_record_id, activity_date, created_at

---

### crm_documents — CRM 文档（Document）

- **数据量**: 0 行 | **字段数**: 15 | **索引数**: 1
- 字段: id, owner_id(索引), contact_id, deal_id, doc_type, template_name, title, doc_number, content_html, content_data, total_amount, currency, status, created_at, updated_at
- **业务说明**: M1-F17 文档模块（编号规则 Q/C/P）落库。

---

### crm_campaigns / crm_campaign_recipients — 邮件营销

- **数据量**: 各 0 行
- **crm_campaigns**(14列): id, owner_id(索引), name, subject, template_name, template_params, target_filter, status, total_recipients, sent_count, opened_count, unsubscribed_count, created_at, updated_at
- **crm_campaign_recipients**(14列): id, campaign_id(索引), contact_id, **email(明文🔴)**, name, tracking_token(索引), sent, sent_at, send_error, opened, opened_at, unsubscribed, unsubscribed_at, created_at
- **业务说明**: 邮件营销闭环；`crm_campaign_recipients.email` 明文列纳入加密范围（见加密方案扩展清单）。

---

### crm_forms / crm_form_submission_logs — 表单收集

- **数据量**: 各 0 行
- **crm_forms**(18列): id, owner_id(索引), name, title, description, fields, submit_action, redirect_url, success_message, enable_honeypot, enable_rate_limit, auto_tags, is_active, submission_count, embed_theme, embed_primary_color, created_at, updated_at
- **crm_form_submission_logs**(10列): id, form_id(索引), submitter_ip, submitter_ua, payload, contact_id, honeypot_triggered, success, error_message, created_at
- **业务说明**: 潜客表单（含蜜罐反垃圾）；`payload` 可能含联系方式，建议加密（扩展清单）。

---

### crm_workflow_rules / crm_workflow_logs — CRM 工作流

- **数据量**: 各 0 行
- **crm_workflow_rules**(10列): id, owner_id(索引), name, description, trigger_event, conditions, actions, enabled, created_at, updated_at
- **crm_workflow_logs**(9列): id, owner_id(索引), rule_id, rule_name, trigger_event, context_snapshot, action_results, success, created_at

---

### customer_journey_stages — 客户旅程阶段

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 1
- 字段: id, contact_id(索引), pipeline_id, stage, entered_at, duration_days, actions_taken, score, next_action

---

## E. 社群与组织

### organizations / organization_members / organization_invites — 组织

- **数据量**: 各 0 行
- **organizations**(5列): id, name, slug(索引,唯一), owner_id, created_at
- **organization_members**(5列): id, org_id, user_id, role, joined_at；索引 `ix_organization_members_id`
- **organization_invites**(6列): id, org_id, email(明文🔴), token(索引), status, created_at
- **业务说明**: M3-F08~F10 组织 CRUD/成员/邀请。`organization_invites.email` 明文纳入加密扩展清单。

---

### teams / team_members / team_invites — 团队

- **数据量**: 各 0 行
- **teams**(13列): id, name, slug(唯一), description, logo, website, industry, size, owner_id, max_members, is_active, created_at, updated_at；索引 `sqlite_autoindex_teams_1`
- **team_members**(9列): id, team_id, user_id, role, title_in_team, is_active, joined_at, invited_by, created_at；**0索引⚠️**
- **team_invites**(13列): id, team_id, inviter_id, invitee_email(明文🔴), invitee_phone(明文🔴), invitee_id, role, status, token(唯一), message, expires_at, created_at, updated_at
- **业务说明**: M3-F11~F13 团队管理。`team_invites.invitee_email/invitee_phone` 明文纳入加密扩展清单；`team_members` 缺 `team_id` 索引。

---

### approval_requests — 审批请求

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 0
- 字段: id, team_id, requester_id, action, target_user_id, reason, status, reviewer_id, reject_reason, created_at, reviewed_at
- **业务说明**: 团队/组织审批流。**0索引⚠️**，`team_id`+`status` 查询高频，见索引建议。

---

### platforms / platform_members / platform_opportunities / resource_platforms — 平台商机

- **数据量**: 各 0 行
- **platforms**(14列): id, name, platform_no(唯一), creator_id, annual_fee, description, created_at, updated_at, province, city, district, **contact_name, phone(明文🔴), industries**
- **platform_members**(5列): id, platform_id, user_id, role, joined_at
- **platform_opportunities**(10列): id, platform_id, creator_id, title, description, industry, city, budget, status, created_at；**0索引⚠️**
- **resource_platforms**(10列): id, name, platform_no(唯一), creator_id, annual_fee, description, member_limit, visibility, created_at, updated_at
- **业务说明**: 平台商机撮合（M2 延伸）。`platforms.phone` 明文纳入加密扩展清单。

---

### messages — 站内消息

- **数据量**: 0 行 | **字段数**: 7 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| sender_id | INTEGER | | ✅ | | 发送方 |
| receiver_id | INTEGER | | ✅ | | 接收方 |
| content | TEXT | | ✅ | | 内容 |
| is_read | BOOLEAN | | ✅ | | 是否已读 |
| conversation_id | VARCHAR(36) | | ✅ | | 会话ID |
| created_at | DATETIME | | ✅ | | 时间 |

**索引**: `ix_messages_created_at`、`ix_messages_sender_id`、`ix_messages_conversation_id`、`ix_messages_is_read`、`ix_messages_receiver_id`

**业务说明**: M3-F15 站内消息与未读。建议补 `(receiver_id,is_read)` 组合索引（未读数统计），见索引建议。

---

## F. 支付与商业

### payment_orders — 支付订单 ⭐

- **数据量**: 0 行 | **字段数**: 12 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| order_no | VARCHAR(32) | | ✅ | | 订单号（唯一） |
| user_id | INTEGER | | ✅ | | 用户 |
| membership_tier | VARCHAR(16) | | ✅ | | 会员档位 |
| channel | VARCHAR(16) | | ✅ | | 渠道: alipay/wechat |
| channel_order_no | VARCHAR(64) | | ✅ | | 渠道订单号 |
| status | VARCHAR(16) | | ✅ | | 状态: pending/paid/failed |
| total_cents | INTEGER | | ✅ | | 金额(分) |
| paid_at | DATETIME | | | | 支付时间 |
| raw_callback | VARCHAR(2048) | | ✅ | | 回调原文（🔴含签名等敏感信息，建议加密/脱敏存储） |
| created_at | DATETIME | | ✅ | | 创建时间 |
| updated_at | DATETIME | | ✅ | | 更新时间 |

**索引**: `sqlite_autoindex_payment_orders_1`(order_no, UNIQUE)

**业务说明**: M4/公共支付链路。⚠️ R5 风险：表 0 行，支付宝/微信回调未经真实渠道验证。**缺失索引**: `user_id`、`status`、`channel_order_no`，见索引建议。

---

### payment_transaction — 支付流水（占位）

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1
- **业务说明**: ⚠️占位表。**🔴 R5 支付链路核心流水表无真实结构**，阶段3.2 优先补全（字段建议: id/order_id/user_id/amount/currency/channel/status/transaction_no/raw_callback/created_at），见加密方案与索引建议。

---

### order / membership_order / private_board_order / product / contract / deal / deal_activity — 订单/商品/合同（占位）

- **数据量**: 各 0 行 | **字段数**: 各 1 | **索引数**: 各 1
- **业务说明**: ⚠️全部占位表。`order`/`membership_order`/`private_board_order`（会员/私董会订单）、`product`（商品）、`contract`（合同）、`deal`/`deal_activity`（链客宝合并商机）。`__init__.py` 已导入模型但仅 `id` 列，待补全。

---

### subscription — 个人订阅（占位）

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1
- **业务说明**: ⚠️占位表。订阅路由（`subscription_router.py`）已实现 plans/current/upgrade/downgrade/trial，但订阅落库表未实现，现依赖 `enterprise_subscriptions` 或内存态，待补全（建议字段: id/user_id/plan_tier/status/start_at/end_at/auto_renew/cancel_reason）。

---

### enterprise_subscriptions — 企业订阅

- **数据量**: 0 行 | **字段数**: 12 | **索引数**: 0 ⚠️

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| user_id | INTEGER | | ✅ | | 用户 |
| company_name | VARCHAR(128) | | ✅ | | 企业名 |
| seats | INTEGER | | ✅ | | 席位 |
| tier | VARCHAR(32) | | ✅ | | 档位 |
| start_date | DATETIME | | ✅ | | 开始 |
| end_date | DATETIME | | ✅ | | 结束 |
| auto_renew | BOOLEAN | | ✅ | | 自动续费 |
| status | VARCHAR(16) | | ✅ | | 状态 |
| features | JSON | | ✅ | | 功能包 |
| created_at | DATETIME | | ✅ | | 创建时间 |
| updated_at | DATETIME | | ✅ | | 更新时间 |

**业务说明**: 企业订阅（公共商业能力）。**0索引⚠️**，`user_id` 查询高频，见索引建议。

---

### trial_records — 试用记录

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 0 ⚠️
- 字段: id, user_id, subscription_id, trial_tier, status, started_at, expires_at, converted_at, created_at
- **业务说明**: 订阅试用链路；0索引，`user_id` 查询高频。

---

### invoices — 发票

- **数据量**: 0 行 | **字段数**: 17 | **索引数**: 1
- 字段: id, invoice_no(唯一), user_id, amount, tax_rate, tax_amount, total_amount, status, order_no, buyer_name, buyer_tax_id, seller_name, seller_tax_id, items, notes, created_at, updated_at
- **业务说明**: 发票模块（M4 公共商业）。`buyer_tax_id` 属敏感税号，建议加密（扩展清单）。

---

### escrow_deals / escrow_milestones / escrow_disputes — 担保交易

- **数据量**: 各 0 行
- **escrow_deals**(9列): id, buyer_id(索引), seller_id(索引), amount, status(索引), title, description, created_at, updated_at
- **escrow_milestones**(7列): id, deal_id(索引), name, description, status, due_date, completed_at
- **escrow_disputes**(10列): id, deal_id(索引), initiator_id, reason, description, status, evidence, resolution, created_at, resolved_at
- **业务说明**: 担保交易（escrow_router.py）：创建/查询/放款/dispute。

---

### wallet / wallet_transaction / withdrawal — 钱包（占位）

- **数据量**: 各 0 行 | **字段数**: 各 1 | **索引数**: 各 1
- **业务说明**: ⚠️三张均占位表。`wallet`（余额）、`wallet_transaction`（流水）、`withdrawal`（提现）模型待补全；资金链路表结构缺失为🔴高危，阶段3.2 优先（建议字段: 金额用 `Numeric(12,2)`/分存储、状态机、审计）。

---

### email_campaigns — 邮件营销（独立）

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 0 ⚠️
- 字段: id, name, subject, content_template, target_segment, scheduled_at, sent_count, open_count, click_count, status, created_at
- **业务说明**: 与 crm_campaigns 功能重叠，建议评估合并。

---

### usage_counters — 用量计数

- **数据量**: 0 行 | **字段数**: 18 | **索引数**: 2
- 字段: id, user_id(索引), feature, period, used_count, limit_count, reset_at, model_type, model_name, token_type, prompt_tokens, completion_tokens, total_tokens, token_cost, external_cost, markup_rate, created_at, updated_at + `sqlite_autoindex_usage_counters_1`(user_id,feature,period, UNIQUE)
- **业务说明**: 会员配额/API 用量计数，唯一约束 (user_id,feature,period) 保证周期内单条。

---

## G. 权限RBAC与审计

### rbac_roles / rbac_role_permissions / rbac_user_roles — RBAC 三表

- **数据量**: 各 0 行
- **rbac_roles**(7列): id, name(唯一), display_name, description, is_system, created_at, updated_at；索引 `sqlite_autoindex_rbac_roles_1`
- **rbac_role_permissions**(5列): id, role_id, permission_key, created_at；索引 `sqlite_autoindex_rbac_role_permissions_1`(role_id,permission_key, UNIQUE)
- **rbac_user_roles**(5列): id, user_id, role_id, granted_by, created_at；索引 `sqlite_autoindex_rbac_user_roles_1`(user_id,role_id, UNIQUE)
- **业务说明**: M4-F18 RBAC 角色权限模型。权限矩阵在 `models/rbac.py` 硬编码（admin/editor/viewer × brochure/user/team/sso/system/ai/export 权限键）。⚠️ 盘点 R3：45/85 路由未显式鉴权，RBAC 覆盖待复核；且 `users.role` 与 RBAC 并存（4套权限体系之一），阶段2 已冻结整改方向。

---

### audit_logs — 审计日志（2608行）

- **数据量**: 2608 行 | **字段数**: 8 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ | | 主键 |
| user_id | INTEGER | | ✅ | | 用户 |
| action | VARCHAR(32) | | ✅ | | 动作 |
| resource | VARCHAR(128) | | ✅ | | 资源 |
| detail | TEXT | | ✅ | | 详情 |
| ip | VARCHAR(45) | | ✅ | | IP |
| user_agent | VARCHAR(512) | | ✅ | | UA |
| timestamp | DATETIME | | ✅ | | 时间 |

**索引**: `idx_audit_user_action`(user_id,timestamp)、`idx_audit_user_id`(user_id)、`idx_audit_action`(action)、`idx_audit_timestamp`(timestamp)

**业务说明**: 全操作审计（M4-F09）。数据量增长快，建议按月归档分区（见 SOP 保留策略）。

---

### rate_limit_record — 限流记录（占位）

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1
- **业务说明**: ⚠️占位表。限流中间件记录待实现。

---

### error_logs — 前端错误日志

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 3
- 字段: id, msg, url, line, col, stack, page, user_id, user_agent, ip, created_at；索引 `idx_error_log_page`/`idx_error_log_user_id`/`idx_error_log_created_at`

---

### analytics_events — 埋点事件

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 4
- 字段: id, user_id(索引), session_id(索引), event_type(索引), properties, page_url, ip_address, user_agent, created_at(索引)

---

### metrics_snapshot — 指标快照（占位）

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1
- **业务说明**: ⚠️占位表。平台指标快照（M4-F08 stats 用）待实现。

---

### retention_cohorts — 留存队列

- **数据量**: 0 行 | **字段数**: 6 | **索引数**: 1
- 字段: id, cohort_date(索引), day_offset, user_count, active_count, retention_rate

---

### funnel_definitions — 漏斗定义

- **数据量**: 0 行 | **字段数**: 6 | **索引数**: 1
- 字段: id, funnel_name(索引), step_name, step_order, event_type, time_limit_minutes

---

## H. AI与智能引擎

### gaia_knowledge — GAIA 知识图谱

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 5
- 字段: id, source(索引), source_id, knowledge_type(索引), title, content, tags, confidence, impact_score, is_active(索引), vector_embedded, created_at, updated_at
- **业务说明**: GAIA 进化大脑知识沉淀（M4 公共 AI）。

---

### gaia_evolution_events — GAIA 进化事件

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 4
- 字段: id, event_type(索引), event_source, description, metadata, reference_type, reference_id, created_at(索引)

---

### gaia_training_runs / gaia_model_weights — GAIA 训练

- **数据量**: 各 0 行
- **gaia_training_runs**(14列): id, status(索引), trigger, knowledge_count, feedback_count, weights_count, vector_index_size, duration_ms, metrics, error_message, started_at, completed_at, created_at, updated_at
- **gaia_model_weights**(9列): id, module(索引), weights, version, description, training_run_id, is_active, created_at, updated_at

---

### knowledge_models — 知识模型

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 5
- 字段: id, model_id(索引), category(索引), name, source, source_ref, content, tags, confidence, version, is_active(索引), vector_embedded, created_at, updated_at

---

### quality_baselines / quality_samples / quality_eval_jobs — 质量评估（F18）

- **数据量**: 各 0 行
- **quality_baselines**(25列): id, baseline_id, name, description, agent_version, model_name, canary_deployment_id, avg_usefulness/accuracy/completeness/coherence/harmlessness/total, sample_count, passing_count, passing_rate, passing_threshold, score_distribution, tags, sample_meta, is_active, is_archived, created_at, updated_at, evaluated_at；5索引
- **quality_samples**(25列): id, sample_id, input_text, agent_output, expected_output, category, tags, sample_meta, canary_deployment_id, agent_version, model_name, status, eval_method, score_*×6, eval_detail, eval_log, error_message, evaluated_at, created_at, updated_at；5索引
- **quality_eval_jobs**(14列): id, job_id, status, eval_method, sample_ids, model_config, total_samples, completed_samples, failed_samples, baseline_id, summary, created_at, started_at, completed_at；1索引
- **业务说明**: F18 Agent 质量评估看板；⚠️ L1017 TODO：质量评估接 LLM 网关未实现（盘点 4.3 冻结）。

---

### accuracy_baselines / accuracy_check_records / accuracy_calibration_records / accuracy_gate_configs — 准确率门禁（F20）

- **数据量**: 各 0 行
- **accuracy_baselines**(23列): id, baseline_id, name, description, accuracy_threshold, pass_immediately, warn_threshold, quality_baseline_id, quality_avg_total, sample_count, passing_count, passing_rate, agent_version, model_name, calibration_type, calibration_id, is_active, is_archived, meta_data, effective_from, effective_until, created_at, updated_at；5索引
- **accuracy_check_records**(25列): id, check_id, source, baseline_id, baseline_threshold, baseline_name, current_accuracy, current_sample_count, current_passing_count, deviation, deviation_percent, decision, passed, blocked, quality_avg_total, quality_baseline_total, block_reason, block_details, ci_pipeline_id, ci_build_number, ci_commit_sha, ci_branch, meta_data, checked_at, created_at；5索引
- **accuracy_calibration_records**(24列): id, calibration_id, calibration_type, status, old_baseline_id, old_accuracy_threshold, new_baseline_id, new_accuracy_threshold, new_pass_immediately, new_warn_threshold, delta, delta_percent, quality_baseline_id, quality_avg_total, sample_count, passing_count, passing_rate, details, error_message, notification_sent, notification_channels, meta_data, calibrated_at, created_at；4索引
- **accuracy_gate_configs**(18列): id, gate_config_id, enabled, ci_block_enabled, default_accuracy_threshold, default_pass_immediately, default_warn_threshold, ci_block_on_warn, ci_required_samples, ci_auto_calibrate_on_degradation, auto_calibrate, monthly_calibration_day, quarterly_calibration_month, notify_on_calibration, notification_channels, meta_data, created_at, updated_at；1索引
- **业务说明**: F20 名片 Agent 准确率门禁（CI/CD 阻断）；⚠️ L1014 TODO：webhook 发送未实现（盘点 4.3 冻结）。

---

### token_budget_alert / token_consumption_record — Token 预算（F19）

- **数据量**: 各 0 行
- **token_budget_alert**(15列): id, alert_id, rule_name(索引), alert_level, current_usage, token_limit, usage_ratio, threshold, agent_name, user_id, message, detail, is_resolved, resolved_at, created_at(索引)；4索引
- **token_consumption_record**(19列): id, record_id, agent_name(索引), user_id, session_id, rule_name(索引), prompt_tokens, completion_tokens, total_tokens, is_truncated, is_downgraded, degrade_strategy, estimated_cost, cost_per_token, model_name, operation, status, metadata_json, created_at(索引)；7索引
- **业务说明**: F19 Token 消耗分析仪表盘；数据量大，建议按月归档（见 SOP）。

---

### prompt_templates — Prompt 模板库（F12）

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 3
- 字段: id(VARCHAR主键), name, category(索引), version, description, system_prompt, user_prompt_template, parameters_schema, output_schema, tags, is_active(索引), created_at, updated_at；`sqlite_autoindex_prompt_templates_1`(name,version, UNIQUE)

---

### circuit_breaker_state — 熔断状态（占位）

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1
- **业务说明**: ⚠️占位表。AI 网关熔断器状态持久化待实现。

---

## I. 平台与支撑

### ab_tests / ab_test_variants / ab_test_events / ab_test_decision_logs — AB 测试

- **数据量**: 各 0 行
- **ab_tests**(15列): id, user_id(索引), name, description, status(索引), traffic_fraction, min_sample_size, significance_level, metric, target_brochure_id(索引), created_at, updated_at, started_at, completed_at, cached_results
- **ab_test_variants**(14列): id, experiment_id(索引), name, description, sort_order, is_control, config, weight, is_default, impressions, clicks, conversions, views, created_at
- **ab_test_events**(8列): id, experiment_id(索引), variant_id(索引), user_id(索引), visitor_id(索引), event_type, metadata, created_at(索引)
- **ab_test_decision_logs**(8列): id, experiment_id(索引), decision, variant_name, p_value, reason, details, created_at(索引)
- **业务说明**: AB 测试平台（定价/功能实验）。

---

### webhook_subscriptions — Webhook 订阅

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1
- 字段: id, user_id(索引), name, url, secret(🔴机密，建议加密), events, active, retry_count, timeout_seconds, last_triggered_at, last_response_code, last_error, created_at, updated_at
- **业务说明**: Webhook 事件订阅（公共平台能力）。

---

### integrations — 第三方集成

- **数据量**: 0 行 | **字段数**: 12 | **索引数**: 1
- 字段: id, user_id(索引), provider, name, enabled, config(🔴可能含密钥，建议加密), last_sync_at, webhook_url, webhook_secret(🔴), webhook_enabled, created_at, updated_at

---

### app_store_plugins / app_store_plugin_versions / app_store_plugin_reviews / app_store_plugin_installs — 应用商店

- **数据量**: 各 0 行
- **app_store_plugins**(18列): id, developer_id(索引), name, description, icon_url, category(索引), version, price, status(索引), install_count, rating, rating_count, homepage_url, documentation_url, repository_url, tags, created_at, updated_at
- **app_store_plugin_versions**(10列): id, plugin_id(索引), version, changelog, download_url, required_api_version, file_size, checksum, is_published, created_at
- **app_store_plugin_reviews**(6列): id, plugin_id(索引), reviewer_id, status, comments, created_at
- **app_store_plugin_installs**(7列): id, plugin_id(索引), user_id(索引), version_id, is_active, installed_at, uninstalled_at

---

### activity / api_usage_log / contact / enterprise / enterprise_relation / business_need — 占位表

- **数据量**: 各 0 行 | **字段数**: 各 1 | **索引数**: 各 1
- **业务说明**: ⚠️六张占位表。`activity`/`contact`（链客宝合并活动/联系人）、`api_usage_log`（API 用量）、`enterprise`/`enterprise_relation`（企业库与关系，M2 结构化企业数据库核心）、`business_need`（供需需求）。**`enterprise`/`business_need` 是供需匹配数据底座，占位缺失为🔴高危**，阶段3.2 优先补全。

---

## 三、与盘点报告风险项对照

| 盘点风险 | 本文档关联表 | 处置 |
|---|---|---|
| R1 `crm_contacts` 明文 phone/email | crm_contacts（20列） | 加密方案（交付物2） |
| R2 `users.phone` 明文 + unlock 直出明文 | users（18列）、unlock_records | 加密方案（交付物2） |
| R3 45/85 路由无显式鉴权 | users.role、rbac_* | 阶段2权限整改（另文） |
| R4 核心业务表零数据/占位 | 29 张占位表 | 阶段3.2 逐表补全（本文档 1.3） |
| R5 支付链路 0 行 | payment_transaction（占位） | 阶段3.2 优先补全 |
| R6 公开页泄露联系方式 | users.phone | 加密方案 + 脱敏返回 |
| R7 v1_deprecated 兼容层 | — | 阶段2 评估下线 |

## 四、后续整改路线（3.2+）

1. **补全 29 张占位表**：优先支付（payment_transaction/wallet/wallet_transaction/withdrawal）→ 企业（enterprise/enterprise_relation/business_need）→ 其余。
2. **统一命名与约束**：单数表名评估、FK 补全（match_records 等）、`updated_at` 补齐、软删除统一。
3. **执行敏感字段加密迁移**（交付物2 的迁移脚本）。
4. **执行索引优化**（交付物4 的建索引 SQL）。
5. **三环境落地**：PG 18 生产库初始化 + 备份自动化（交付物3）。

---

*本文档由数智DBA基于代码库实扫与数据库实查产出；表结构以 `digital_brochure.db` 实测为准，模型注释交叉核对；后续表结构变更须经 DBA 评审并同步更新本文档。*

---

## 附录A: 全量表字段字典（自动化实查）

> 以下由数据库实查脚本自动生成（sqlite_master + PRAGMA table_info/index_list），字段说明列留空处参见正文各表业务说明。

### api_key_usage

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| api_key_id | INTEGER |  | ✅ |  | |
| date | VARCHAR(10) |  | ✅ |  | |
| request_count | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_api_key_usage_api_key_id` (api_key_id)

### api_keys

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| key | VARCHAR(64) |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| permissions | TEXT |  | ✅ |  | |
| rate_limit | INTEGER |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| last_used_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_api_keys_user_id` (user_id) 
- `sqlite_autoindex_api_keys_1` (key) UNIQUE

### developer_reward_balances

- **数据量**: 0 行 | **字段数**: 6 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| developer_id | INTEGER |  | ✅ |  | |
| total_points | INTEGER |  | ✅ |  | |
| used_points | INTEGER |  | ✅ |  | |
| balance | INTEGER |  | ✅ |  | |
| updated_at | DATETIME |  |  |  | |

**索引**:
- `ix_developer_reward_balances_id` (id) 
- `ix_developer_reward_balances_developer_id` (developer_id) UNIQUE

### developer_rewards

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| developer_id | INTEGER |  | ✅ |  | |
| reward_type | VARCHAR(32) |  | ✅ |  | |
| points | INTEGER |  | ✅ |  | |
| reason | VARCHAR(256) |  |  |  | |
| source_id | INTEGER |  |  |  | |
| source_desc | VARCHAR(128) |  |  |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |
| issued_at | DATETIME |  |  |  | |

**索引**:
- `ix_developer_rewards_id` (id) 
- `ix_developer_rewards_developer_id` (developer_id)

### invitation_codes

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| code | VARCHAR(8) |  | ✅ |  | |
| batch_id | VARCHAR(32) |  |  |  | |
| max_uses | INTEGER |  |  |  | |
| used_count | INTEGER |  |  |  | |
| created_by | INTEGER |  |  |  | |
| expires_at | DATETIME |  |  |  | |
| is_active | BOOLEAN |  |  |  | |
| remark | TEXT |  |  |  | |
| created_at | DATETIME |  |  |  | |
| updated_at | DATETIME |  |  |  | |

**索引**:
- `ix_invitation_codes_code` (code) UNIQUE
- `ix_invitation_codes_id` (id)

### revoked_token ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_revoked_token_id` (id)

### reward_redemptions

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| developer_id | INTEGER |  | ✅ |  | |
| points_spent | INTEGER |  | ✅ |  | |
| redemption_type | VARCHAR(32) |  | ✅ |  | |
| quota_amount | INTEGER |  |  |  | |
| description | VARCHAR(256) |  |  |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |

**索引**:
- `ix_reward_redemptions_id` (id) 
- `ix_reward_redemptions_developer_id` (developer_id)

### sdk_apps

- **数据量**: 0 行 | **字段数**: 20 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| app_id | VARCHAR(64) |  | ✅ |  | |
| app_secret | VARCHAR(128) |  |  |  | |
| developer_id | INTEGER |  | ✅ |  | |
| sdk_type | VARCHAR(32) |  | ✅ |  | |
| platform | VARCHAR(32) |  |  |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| version | VARCHAR(16) |  |  |  | |
| permissions | TEXT |  |  |  | |
| redirect_uris | TEXT |  |  |  | |
| icon_url | VARCHAR(512) |  |  |  | |
| homepage_url | VARCHAR(512) |  |  |  | |
| privacy_policy_url | VARCHAR(512) |  |  |  | |
| is_verified | BOOLEAN |  | ✅ |  | |
| is_public | BOOLEAN |  | ✅ |  | |
| total_installs | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_sdk_developer` (developer_id) 
- `ix_sdk_apps_developer_id` (developer_id) 
- `idx_sdk_type_status` (sdk_type, status) 
- `idx_sdk_status` (status) 
- `sqlite_autoindex_sdk_apps_1` (app_id) UNIQUE

### tenants

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| slug | VARCHAR(64) |  | ✅ |  | |
| plan | VARCHAR(16) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_tenants_1` (slug) UNIQUE

### user_consents

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 3

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| consent_type | VARCHAR(64) |  | ✅ |  | |
| granted | BOOLEAN |  | ✅ |  | |
| consent_version | VARCHAR(16) |  |  |  | |
| source | VARCHAR(64) |  |  |  | |
| ip | VARCHAR(45) |  |  |  | |
| user_agent | VARCHAR(512) |  |  |  | |
| detail | TEXT |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_consent_user_type` (user_id, consent_type) 
- `idx_consent_user_created` (user_id, created_at) 
- `ix_user_consents_user_id` (user_id)

### user_event ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_user_event_id` (id)

### users

- **数据量**: 104 行 | **字段数**: 18 | **索引数**: 3

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| username | VARCHAR(64) |  |  |  | |
| phone | VARCHAR(20) |  | ✅ |  | |
| password_hash | VARCHAR(128) |  | ✅ |  | |
| wechat_openid | VARCHAR(64) |  |  |  | |
| name | VARCHAR(64) |  | ✅ |  | |
| company | VARCHAR(128) |  | ✅ |  | |
| title | VARCHAR(128) |  | ✅ |  | |
| intro | TEXT |  | ✅ |  | |
| avatar | VARCHAR(256) |  | ✅ |  | |
| role | VARCHAR(16) |  | ✅ |  | |
| membership_tier | VARCHAR(16) |  | ✅ |  | |
| membership_expires_at | DATETIME |  |  |  | |
| membership_synced_at | DATETIME |  |  |  | |
| unlock_quota | INTEGER |  | ✅ |  | |
| quota_reset_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_users_3` (wechat_openid) UNIQUE
- `sqlite_autoindex_users_2` (phone) UNIQUE
- `sqlite_autoindex_users_1` (username) UNIQUE

---

## B.名片与画册

### brochures

- **数据量**: 20 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| title | VARCHAR(128) |  | ✅ |  | |
| cover | VARCHAR(256) |  | ✅ |  | |
| purpose | VARCHAR(32) |  | ✅ |  | |
| pages_count | INTEGER |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| share_token | VARCHAR(32) |  | ✅ |  | |
| view_count | INTEGER |  | ✅ |  | |
| album_meta | TEXT |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| visibility | VARCHAR(16) |  | ✅ | 'public' | |
| platform_id | INTEGER |  |  | NULL | |

**索引**:
- `sqlite_autoindex_brochures_1` (share_token) UNIQUE

### business_card ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_business_card_id` (id)

### nfc_cards

- **数据量**: 0 行 | **字段数**: 7 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| nfc_uid | VARCHAR(64) |  | ✅ |  | |
| card_data_json | TEXT |  | ✅ |  | |
| vcard_raw | TEXT |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_nfc_cards_user_id` (user_id) 
- `ix_nfc_cards_nfc_uid` (nfc_uid) UNIQUE

### nfc_tap_records

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| from_user_id | INTEGER |  | ✅ |  | |
| to_user_id | INTEGER |  | ✅ |  | |
| nfc_uid | VARCHAR(64) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_nfc_tap_records_from_user_id` (from_user_id) 
- `ix_nfc_tap_records_to_user_id` (to_user_id)

### pages

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| brochure_id | INTEGER |  | ✅ |  | |
| sort_order | INTEGER |  | ✅ |  | |
| content_type | VARCHAR(16) |  | ✅ |  | |
| content | TEXT |  | ✅ |  | |
| image_url | VARCHAR(256) |  | ✅ |  | |
| media_url | VARCHAR(512) |  | ✅ |  | |
| ai_summary | TEXT |  | ✅ |  | |

### referral_links

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_user_id | INTEGER |  | ✅ |  | |
| code | VARCHAR(32) |  | ✅ |  | |
| title | VARCHAR(100) |  |  |  | |
| description | VARCHAR(500) |  |  |  | |
| invite_type | VARCHAR(20) |  | ✅ |  | |
| redirect_url | VARCHAR(500) |  |  |  | |
| scan_count | INTEGER |  | ✅ |  | |
| register_count | INTEGER |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| expires_at | DATETIME |  |  |  | |
| created_at | DATETIME |  |  |  | |
| updated_at | DATETIME |  |  |  | |

**索引**:
- `ix_referral_links_code` (code) UNIQUE
- `ix_referral_links_id` (id) 
- `idx_referral_owner` (owner_user_id, is_active) 
- `ix_referral_links_owner_user_id` (owner_user_id)

### user_tags

- **数据量**: 806 行 | **字段数**: 7 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| tag_type | VARCHAR(16) |  | ✅ |  | |
| tag | VARCHAR(64) |  | ✅ |  | |
| weight | FLOAT |  | ✅ |  | |
| source | VARCHAR(16) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### visitor_logs

- **数据量**: 25 行 | **字段数**: 11 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| brochure_id | INTEGER |  | ✅ |  | |
| visitor_id | VARCHAR(64) |  |  |  | |
| visitor_ip | VARCHAR(48) |  | ✅ |  | |
| visitor_name | VARCHAR(64) |  | ✅ |  | |
| source | VARCHAR(32) |  | ✅ |  | |
| page_viewed | VARCHAR(64) |  | ✅ |  | |
| duration | INTEGER |  | ✅ |  | |
| interested | BOOLEAN |  | ✅ |  | |
| contact_msg | TEXT |  | ✅ |  | |
| visit_time | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

---

## C.匹配与推荐

### connections

- **数据量**: 120 行 | **字段数**: 9 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  | ✅ |  | |
| source | VARCHAR(32) |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| strength | FLOAT |  | ✅ |  | |
| label | VARCHAR(64) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_connections_1` (user_id, contact_id) UNIQUE

### match_credit_log ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_match_credit_log_id` (id)

### match_records

- **数据量**: 7337 行 | **字段数**: 8 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_a_id | INTEGER |  | ✅ |  | |
| user_b_id | INTEGER |  | ✅ |  | |
| match_score | FLOAT |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| common_tags | TEXT |  | ✅ |  | |
| source | VARCHAR(16) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### online_matching_events ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_online_matching_events_id` (id)

### online_matching_feedback ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_online_matching_feedback_id` (id)

### online_matching_registrations ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_online_matching_registrations_id` (id)

### relation_events

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| relation_id | INTEGER |  | ✅ |  | |
| from_user_id | INTEGER |  | ✅ |  | |
| to_user_id | INTEGER |  | ✅ |  | |
| event_type | VARCHAR(30) |  | ✅ |  | |
| old_trust_score | FLOAT |  |  |  | |
| new_trust_score | FLOAT |  |  |  | |
| reason | VARCHAR(200) |  |  |  | |
| metadata_json | TEXT |  |  |  | |
| created_at | DATETIME |  |  |  | |

**索引**:
- `ix_relation_events_created_at` (created_at) 
- `ix_relation_events_to_user_id` (to_user_id) 
- `ix_relation_events_relation_id` (relation_id) 
- `ix_relation_events_from_user_id` (from_user_id) 
- `ix_relation_events_id` (id)

### six_degree_path_cache

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| from_user_id | INTEGER |  | ✅ |  | |
| to_user_id | INTEGER |  | ✅ |  | |
| path_json | TEXT |  | ✅ |  | |
| path_length | INTEGER |  | ✅ |  | |
| total_trust_score | FLOAT |  | ✅ |  | |
| hit_count | INTEGER |  | ✅ |  | |
| expires_at | DATETIME |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |
| updated_at | DATETIME |  |  |  | |

**索引**:
- `idx_path_cache_expires` (expires_at) 
- `ix_six_degree_path_cache_from_user_id` (from_user_id) 
- `ix_six_degree_path_cache_id` (id) 
- `ix_six_degree_path_cache_to_user_id` (to_user_id) 
- `sqlite_autoindex_six_degree_path_cache_1` (from_user_id, to_user_id) UNIQUE

### social_connections

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | VARCHAR(36) | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  | ✅ |  | |
| source | VARCHAR(32) |  | ✅ |  | |
| message | TEXT |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| strength | FLOAT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_social_connections_1` (id) UNIQUE

### trust_network

- **数据量**: 50 行 | **字段数**: 4 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| trusted_user_id | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### unlock_records

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| target_user_id | INTEGER |  | ✅ |  | |
| match_record_id | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### user_relations

- **数据量**: 0 行 | **字段数**: 18 | **索引数**: 6

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| from_user_id | INTEGER |  | ✅ |  | |
| to_user_id | INTEGER |  | ✅ |  | |
| relation_type | VARCHAR(20) |  | ✅ |  | |
| label | VARCHAR(100) |  |  |  | |
| trust_score | FLOAT |  | ✅ |  | |
| interaction_count | INTEGER |  | ✅ |  | |
| last_interaction_at | DATETIME |  |  |  | |
| bidirectional | BOOLEAN |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| source | VARCHAR(30) |  |  |  | |
| source_detail | VARCHAR(200) |  |  |  | |
| version | BIGINT |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |
| updated_at | DATETIME |  |  |  | |
| deleted_at | DATETIME |  |  |  | |
| is_deleted | BOOLEAN |  |  |  | |
| organization_id | INTEGER |  |  |  | |

**索引**:
- `idx_user_relation_active` (from_user_id, is_active, trust_score) 
- `ix_user_relations_from_user_id` (from_user_id) 
- `ix_user_relations_id` (id) 
- `ix_user_relations_to_user_id` (to_user_id) 
- `idx_user_relation_to` (to_user_id, is_active) 
- `sqlite_autoindex_user_relations_1` (from_user_id, to_user_id) UNIQUE

---

## D.人脉与CRM

### contacts

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(64) |  | ✅ |  | |
| phone_hash | VARCHAR(64) |  | ✅ |  | |
| phone_enc | TEXT |  | ✅ |  | |
| phone_last4 | VARCHAR(4) |  | ✅ |  | |
| company | VARCHAR(128) |  | ✅ |  | |
| position | VARCHAR(128) |  | ✅ |  | |
| source | VARCHAR(16) |  | ✅ |  | |
| is_matched | SMALLINT |  | ✅ |  | |
| matched_user_id | INTEGER |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| deleted_at | DATETIME |  |  |  | |

**索引**:
- `ix_contacts_user_id` (user_id)

### crm_activities

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  | ✅ |  | |
| deal_id | INTEGER |  |  |  | |
| activity_type | VARCHAR(16) |  | ✅ |  | |
| title | VARCHAR(256) |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| source_model | VARCHAR(32) |  |  |  | |
| source_record_id | INTEGER |  |  |  | |
| activity_date | DATETIME |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_activities_owner_id` (owner_id) 
- `ix_crm_activities_contact_id` (contact_id)

### crm_campaign_recipients

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| campaign_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  | ✅ |  | |
| email | VARCHAR(128) |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| tracking_token | VARCHAR(64) |  | ✅ |  | |
| sent | BOOLEAN |  | ✅ |  | |
| sent_at | DATETIME |  |  |  | |
| send_error | TEXT |  | ✅ |  | |
| opened | BOOLEAN |  | ✅ |  | |
| opened_at | DATETIME |  |  |  | |
| unsubscribed | BOOLEAN |  | ✅ |  | |
| unsubscribed_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_campaign_recipients_tracking_token` (tracking_token) UNIQUE
- `ix_crm_campaign_recipients_campaign_id` (campaign_id)

### crm_campaigns

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(256) |  | ✅ |  | |
| subject | VARCHAR(512) |  | ✅ |  | |
| template_name | VARCHAR(64) |  | ✅ |  | |
| template_params | TEXT |  | ✅ |  | |
| target_filter | TEXT |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| total_recipients | INTEGER |  | ✅ |  | |
| sent_count | INTEGER |  | ✅ |  | |
| opened_count | INTEGER |  | ✅ |  | |
| unsubscribed_count | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_campaigns_owner_id` (owner_id)

### crm_contacts

- **数据量**: 0 行 | **字段数**: 20 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| user_id | INTEGER |  |  |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| phone | VARCHAR(32) |  | ✅ |  | |
| email | VARCHAR(128) |  | ✅ |  | |
| company | VARCHAR(256) |  | ✅ |  | |
| title | VARCHAR(128) |  | ✅ |  | |
| department | VARCHAR(128) |  | ✅ |  | |
| avatar | VARCHAR(512) |  | ✅ |  | |
| intro | TEXT |  | ✅ |  | |
| source | VARCHAR(16) |  | ✅ |  | |
| source_record_id | INTEGER |  |  |  | |
| tags | TEXT |  | ✅ |  | |
| pipeline_stage_id | INTEGER |  |  |  | |
| deal_value | NUMERIC(12, 2) |  |  |  | |
| deal_currency | VARCHAR(8) |  | ✅ |  | |
| last_contacted_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_contacts_user_id` (user_id) 
- `ix_crm_contacts_owner_id` (owner_id)

### crm_deals

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  | ✅ |  | |
| pipeline_stage_id | INTEGER |  | ✅ |  | |
| title | VARCHAR(256) |  | ✅ |  | |
| value | NUMERIC(12, 2) |  | ✅ |  | |
| currency | VARCHAR(8) |  | ✅ |  | |
| probability | FLOAT |  | ✅ |  | |
| expected_close_date | DATETIME |  |  |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| lost_reason | TEXT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_deals_contact_id` (contact_id) 
- `ix_crm_deals_owner_id` (owner_id)

### crm_documents

- **数据量**: 0 行 | **字段数**: 15 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  |  |  | |
| deal_id | INTEGER |  |  |  | |
| doc_type | VARCHAR(16) |  | ✅ |  | |
| template_name | VARCHAR(64) |  | ✅ |  | |
| title | VARCHAR(256) |  | ✅ |  | |
| doc_number | VARCHAR(32) |  | ✅ |  | |
| content_html | TEXT |  | ✅ |  | |
| content_data | JSON |  | ✅ |  | |
| total_amount | FLOAT |  | ✅ |  | |
| currency | VARCHAR(8) |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_documents_owner_id` (owner_id)

### crm_form_submission_logs

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| form_id | INTEGER |  | ✅ |  | |
| submitter_ip | VARCHAR(45) |  |  |  | |
| submitter_ua | TEXT |  |  |  | |
| payload | TEXT |  |  |  | |
| contact_id | INTEGER |  |  |  | |
| honeypot_triggered | BOOLEAN |  |  |  | |
| success | BOOLEAN |  |  |  | |
| error_message | TEXT |  |  |  | |
| created_at | DATETIME |  |  | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_form_submission_logs_form_id` (form_id)

### crm_forms

- **数据量**: 0 行 | **字段数**: 18 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| title | VARCHAR(256) |  |  |  | |
| description | TEXT |  |  |  | |
| fields | TEXT |  | ✅ |  | |
| submit_action | VARCHAR(32) |  |  |  | |
| redirect_url | VARCHAR(512) |  |  |  | |
| success_message | VARCHAR(256) |  |  |  | |
| enable_honeypot | BOOLEAN |  |  |  | |
| enable_rate_limit | BOOLEAN |  |  |  | |
| auto_tags | TEXT |  |  |  | |
| is_active | BOOLEAN |  |  |  | |
| submission_count | INTEGER |  |  |  | |
| embed_theme | VARCHAR(32) |  |  |  | |
| embed_primary_color | VARCHAR(16) |  |  |  | |
| created_at | DATETIME |  |  | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  |  | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_forms_owner_id` (owner_id)

### crm_notes

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  |  |  | |
| deal_id | INTEGER |  |  |  | |
| content | TEXT |  | ✅ |  | |
| is_pinned | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_notes_owner_id` (owner_id)

### crm_pipeline_stages

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(64) |  | ✅ |  | |
| sort_order | INTEGER |  | ✅ |  | |
| color | VARCHAR(16) |  | ✅ |  | |
| is_default | BOOLEAN |  | ✅ |  | |
| is_closed | BOOLEAN |  | ✅ |  | |
| win_probability | FLOAT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_pipeline_stages_user_id` (user_id)

### crm_workflow_logs

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| rule_id | INTEGER |  | ✅ |  | |
| rule_name | VARCHAR(128) |  | ✅ |  | |
| trigger_event | VARCHAR(32) |  | ✅ |  | |
| context_snapshot | TEXT |  | ✅ |  | |
| action_results | TEXT |  | ✅ |  | |
| success | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_workflow_logs_owner_id` (owner_id)

### crm_workflow_rules

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| trigger_event | VARCHAR(32) |  | ✅ |  | |
| conditions | TEXT |  | ✅ |  | |
| actions | TEXT |  | ✅ |  | |
| enabled | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_workflow_rules_owner_id` (owner_id)

### customer_journey_stages

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| contact_id | INTEGER |  | ✅ |  | |
| pipeline_id | INTEGER |  |  |  | |
| stage | VARCHAR(20) |  | ✅ |  | |
| entered_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| duration_days | INTEGER |  | ✅ |  | |
| actions_taken | TEXT |  | ✅ |  | |
| score | FLOAT |  | ✅ |  | |
| next_action | VARCHAR(256) |  | ✅ |  | |

**索引**:
- `ix_customer_journey_stages_contact_id` (contact_id)

### import_history ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_import_history_id` (id) 

---

## E.社群与组织

### approval_requests

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| team_id | INTEGER |  | ✅ |  | |
| requester_id | INTEGER |  | ✅ |  | |
| action | VARCHAR(7) |  | ✅ |  | |
| target_user_id | INTEGER |  |  |  | |
| reason | TEXT |  |  |  | |
| status | VARCHAR(8) |  | ✅ |  | |
| reviewer_id | INTEGER |  |  |  | |
| reject_reason | TEXT |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| reviewed_at | DATETIME |  |  |  | |

### messages

- **数据量**: 0 行 | **字段数**: 7 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| sender_id | INTEGER |  | ✅ |  | |
| receiver_id | INTEGER |  | ✅ |  | |
| content | TEXT |  | ✅ |  | |
| is_read | BOOLEAN |  | ✅ |  | |
| conversation_id | VARCHAR(36) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_messages_created_at` (created_at) 
- `ix_messages_sender_id` (sender_id) 
- `ix_messages_conversation_id` (conversation_id) 
- `ix_messages_is_read` (is_read) 
- `ix_messages_receiver_id` (receiver_id)

### organization_invites

- **数据量**: 0 行 | **字段数**: 6 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| org_id | INTEGER |  | ✅ |  | |
| email | VARCHAR(255) |  | ✅ |  | |
| token | VARCHAR(64) |  | ✅ |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |

**索引**:
- `ix_organization_invites_id` (id) 
- `ix_organization_invites_token` (token) UNIQUE

### organization_members

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| org_id | INTEGER |  | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| role | VARCHAR(20) |  | ✅ |  | |
| joined_at | DATETIME |  |  |  | |

**索引**:
- `ix_organization_members_id` (id)

### organizations

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(200) |  | ✅ |  | |
| slug | VARCHAR(100) |  | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |

**索引**:
- `ix_organizations_slug` (slug) UNIQUE
- `ix_organizations_id` (id)

### platform_members

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| platform_id | INTEGER |  | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| role | VARCHAR(20) |  | ✅ |  | |
| joined_at | INTEGER |  | ✅ |  | |

**索引**:
- `sqlite_autoindex_platform_members_1` (platform_id, user_id) UNIQUE

### platform_opportunities

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| platform_id | INTEGER |  | ✅ |  | |
| creator_id | INTEGER |  | ✅ |  | |
| title | VARCHAR(200) |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| industry | VARCHAR(50) |  | ✅ |  | |
| city | VARCHAR(50) |  | ✅ |  | |
| budget | INTEGER |  | ✅ |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| created_at | INTEGER |  | ✅ |  | |

### platforms

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| platform_no | VARCHAR(32) |  |  |  | |
| creator_id | INTEGER |  | ✅ |  | |
| annual_fee | FLOAT |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| province | VARCHAR(32) |  |  |  | |
| city | VARCHAR(32) |  |  |  | |
| district | VARCHAR(32) |  |  |  | |
| contact_name | VARCHAR(64) |  |  |  | |
| phone | VARCHAR(20) |  |  |  | |
| industries | TEXT |  |  |  | |

**索引**:
- `sqlite_autoindex_platforms_1` (platform_no) UNIQUE

### resource_platforms

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(100) |  | ✅ |  | |
| platform_no | VARCHAR(50) |  |  |  | |
| creator_id | INTEGER |  | ✅ |  | |
| annual_fee | INTEGER |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| member_limit | INTEGER |  | ✅ |  | |
| visibility | VARCHAR(20) |  | ✅ |  | |
| created_at | INTEGER |  | ✅ |  | |
| updated_at | INTEGER |  | ✅ |  | |

**索引**:
- `sqlite_autoindex_resource_platforms_1` (platform_no) UNIQUE

### team_invites

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| team_id | INTEGER |  | ✅ |  | |
| inviter_id | INTEGER |  | ✅ |  | |
| invitee_email | VARCHAR(256) |  | ✅ |  | |
| invitee_phone | VARCHAR(20) |  | ✅ |  | |
| invitee_id | INTEGER |  |  |  | |
| role | VARCHAR(6) |  | ✅ |  | |
| status | VARCHAR(8) |  | ✅ |  | |
| token | VARCHAR(128) |  | ✅ |  | |
| message | TEXT |  | ✅ |  | |
| expires_at | DATETIME |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_team_invites_1` (token) UNIQUE

### team_members

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| team_id | INTEGER |  | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| role | VARCHAR(6) |  | ✅ |  | |
| title_in_team | VARCHAR(128) |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| joined_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| invited_by | INTEGER |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### teams

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| slug | VARCHAR(64) |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| logo | VARCHAR(256) |  | ✅ |  | |
| website | VARCHAR(256) |  | ✅ |  | |
| industry | VARCHAR(64) |  | ✅ |  | |
| size | VARCHAR(16) |  | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| max_members | INTEGER |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_teams_1` (slug) UNIQUE

---

## F.支付与商业

### contract ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_contract_id` (id)

### deal ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_deal_id` (id)

### deal_activity ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_deal_activity_id` (id)

### email_campaigns

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(256) |  | ✅ |  | |
| subject | VARCHAR(512) |  | ✅ |  | |
| content_template | TEXT |  | ✅ |  | |
| target_segment | TEXT |  | ✅ |  | |
| scheduled_at | DATETIME |  |  |  | |
| sent_count | INTEGER |  | ✅ |  | |
| open_count | INTEGER |  | ✅ |  | |
| click_count | INTEGER |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### enterprise_subscriptions

- **数据量**: 0 行 | **字段数**: 12 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| company_name | VARCHAR(128) |  | ✅ |  | |
| seats | INTEGER |  | ✅ |  | |
| tier | VARCHAR(32) |  | ✅ |  | |
| start_date | DATETIME |  | ✅ |  | |
| end_date | DATETIME |  | ✅ |  | |
| auto_renew | BOOLEAN |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| features | JSON |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### escrow_deals

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| buyer_id | INTEGER |  | ✅ |  | |
| seller_id | INTEGER |  | ✅ |  | |
| amount | FLOAT |  | ✅ |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| title | VARCHAR(255) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| created_at | DATETIME |  |  |  | |
| updated_at | DATETIME |  |  |  | |

**索引**:
- `ix_escrow_deals_id` (id) 
- `ix_escrow_deals_seller_id` (seller_id) 
- `ix_escrow_deals_status` (status) 
- `ix_escrow_deals_buyer_id` (buyer_id)

### escrow_disputes

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| deal_id | INTEGER |  | ✅ |  | |
| initiator_id | INTEGER |  | ✅ |  | |
| reason | VARCHAR(500) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| evidence | TEXT |  |  |  | |
| resolution | TEXT |  |  |  | |
| created_at | DATETIME |  |  |  | |
| resolved_at | DATETIME |  |  |  | |

**索引**:
- `ix_escrow_disputes_deal_id` (deal_id) 
- `ix_escrow_disputes_id` (id)

### escrow_milestones

- **数据量**: 0 行 | **字段数**: 7 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| deal_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(200) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| due_date | DATETIME |  |  |  | |
| completed_at | DATETIME |  |  |  | |

**索引**:
- `ix_escrow_milestones_deal_id` (deal_id) 
- `ix_escrow_milestones_id` (id)

### invoices

- **数据量**: 0 行 | **字段数**: 17 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| invoice_no | VARCHAR(32) |  | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| amount | FLOAT |  | ✅ |  | |
| tax_rate | FLOAT |  | ✅ |  | |
| tax_amount | FLOAT |  | ✅ |  | |
| total_amount | FLOAT |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| order_no | VARCHAR(32) |  | ✅ |  | |
| buyer_name | VARCHAR(128) |  | ✅ |  | |
| buyer_tax_id | VARCHAR(32) |  | ✅ |  | |
| seller_name | VARCHAR(128) |  | ✅ |  | |
| seller_tax_id | VARCHAR(32) |  | ✅ |  | |
| items | JSON |  | ✅ |  | |
| notes | TEXT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_invoices_1` (invoice_no) UNIQUE

### membership_order ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_membership_order_id` (id)

### order ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_order_id` (id)

### payment_orders

- **数据量**: 0 行 | **字段数**: 12 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| order_no | VARCHAR(32) |  | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| membership_tier | VARCHAR(16) |  | ✅ |  | |
| channel | VARCHAR(16) |  | ✅ |  | |
| channel_order_no | VARCHAR(64) |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| total_cents | INTEGER |  | ✅ |  | |
| paid_at | DATETIME |  |  |  | |
| raw_callback | VARCHAR(2048) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_payment_orders_1` (order_no) UNIQUE

### payment_transaction ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_payment_transaction_id` (id)

### private_board_order ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_private_board_order_id` (id)

### product ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_product_id` (id)

### subscription ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_subscription_id` (id)

### trial_records

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| subscription_id | INTEGER |  | ✅ |  | |
| trial_tier | VARCHAR(32) |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| started_at | DATETIME |  | ✅ |  | |
| expires_at | DATETIME |  | ✅ |  | |
| converted_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### usage_counters

- **数据量**: 0 行 | **字段数**: 18 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| feature | VARCHAR(32) |  | ✅ |  | |
| period | VARCHAR(16) |  | ✅ |  | |
| used_count | INTEGER |  | ✅ |  | |
| limit_count | INTEGER |  | ✅ |  | |
| reset_at | DATETIME |  |  |  | |
| model_type | VARCHAR(16) |  | ✅ |  | |
| model_name | VARCHAR(64) |  | ✅ |  | |
| token_type | VARCHAR(16) |  | ✅ |  | |
| prompt_tokens | INTEGER |  | ✅ |  | |
| completion_tokens | INTEGER |  | ✅ |  | |
| total_tokens | INTEGER |  | ✅ |  | |
| token_cost | FLOAT |  | ✅ |  | |
| external_cost | FLOAT |  | ✅ |  | |
| markup_rate | FLOAT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_usage_counters_user_id` (user_id) 
- `sqlite_autoindex_usage_counters_1` (user_id, feature, period) UNIQUE

### wallet ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_wallet_id` (id)

### wallet_transaction ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_wallet_transaction_id` (id)

### withdrawal ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_withdrawal_id` (id) 

---

## G.权限RBAC与审计

### analytics_events

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  |  |  | |
| session_id | VARCHAR(64) |  |  |  | |
| event_type | VARCHAR(32) |  | ✅ |  | |
| properties | JSON |  |  |  | |
| page_url | VARCHAR(512) |  |  |  | |
| ip_address | VARCHAR(45) |  |  |  | |
| user_agent | VARCHAR(512) |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |

**索引**:
- `ix_analytics_events_session_id` (session_id) 
- `ix_analytics_events_created_at` (created_at) 
- `ix_analytics_events_event_type` (event_type) 
- `ix_analytics_events_user_id` (user_id)

### audit_logs

- **数据量**: 2608 行 | **字段数**: 8 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  |  |  | |
| action | VARCHAR(32) |  | ✅ |  | |
| resource | VARCHAR(128) |  | ✅ |  | |
| detail | TEXT |  |  |  | |
| ip | VARCHAR(45) |  | ✅ |  | |
| user_agent | VARCHAR(512) |  |  |  | |
| timestamp | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_audit_user_action` (user_id, timestamp) 
- `idx_audit_user_id` (user_id) 
- `idx_audit_action` (action) 
- `idx_audit_timestamp` (timestamp)

### error_logs

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 3

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| msg | TEXT |  | ✅ |  | |
| url | VARCHAR(1024) |  |  |  | |
| line | INTEGER |  |  |  | |
| col | INTEGER |  |  |  | |
| stack | TEXT |  |  |  | |
| page | VARCHAR(256) |  |  |  | |
| user_id | INTEGER |  |  |  | |
| user_agent | VARCHAR(512) |  |  |  | |
| ip | VARCHAR(45) |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_error_log_page` (page) 
- `idx_error_log_user_id` (user_id) 
- `idx_error_log_created_at` (created_at)

### funnel_definitions

- **数据量**: 0 行 | **字段数**: 6 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| funnel_name | VARCHAR(32) |  | ✅ |  | |
| step_name | VARCHAR(32) |  | ✅ |  | |
| step_order | INTEGER |  | ✅ |  | |
| event_type | VARCHAR(32) |  | ✅ |  | |
| time_limit_minutes | INTEGER |  | ✅ |  | |

**索引**:
- `ix_funnel_definitions_funnel_name` (funnel_name)

### metrics_snapshot ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_metrics_snapshot_id` (id)

### rate_limit_record ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_rate_limit_record_id` (id)

### rbac_role_permissions

- **数据量**: 0 行 | **字段数**: 4 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| role_id | INTEGER |  | ✅ |  | |
| permission_key | VARCHAR(64) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_rbac_role_permissions_1` (role_id, permission_key) UNIQUE

### rbac_roles

- **数据量**: 0 行 | **字段数**: 7 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(32) |  | ✅ |  | |
| display_name | VARCHAR(64) |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| is_system | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_rbac_roles_1` (name) UNIQUE

### rbac_user_roles

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| role_id | INTEGER |  | ✅ |  | |
| granted_by | INTEGER |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_rbac_user_roles_1` (user_id, role_id) UNIQUE

### retention_cohorts

- **数据量**: 0 行 | **字段数**: 6 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| cohort_date | DATETIME |  | ✅ |  | |
| day_offset | INTEGER |  | ✅ |  | |
| user_count | INTEGER |  | ✅ |  | |
| active_count | INTEGER |  | ✅ |  | |
| retention_rate | INTEGER |  | ✅ |  | |

**索引**:
- `ix_retention_cohorts_cohort_date` (cohort_date) 

---

## H.AI与智能引擎

### accuracy_baselines

- **数据量**: 0 行 | **字段数**: 23 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| baseline_id | VARCHAR(64) |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| accuracy_threshold | FLOAT |  | ✅ |  | |
| pass_immediately | FLOAT |  |  |  | |
| warn_threshold | FLOAT |  |  |  | |
| quality_baseline_id | VARCHAR(64) |  |  |  | |
| quality_avg_total | FLOAT |  |  |  | |
| sample_count | INTEGER |  |  |  | |
| passing_count | INTEGER |  |  |  | |
| passing_rate | FLOAT |  |  |  | |
| agent_version | VARCHAR(64) |  |  |  | |
| model_name | VARCHAR(128) |  |  |  | |
| calibration_type | VARCHAR(32) |  |  |  | |
| calibration_id | VARCHAR(64) |  |  |  | |
| is_active | BOOLEAN |  |  |  | |
| is_archived | BOOLEAN |  |  |  | |
| meta_data | JSON |  |  |  | |
| effective_from | DATETIME |  | ✅ |  | |
| effective_until | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |
| updated_at | DATETIME |  | ✅ |  | |

**索引**:
- `idx_accuracy_baseline_effective` (effective_from) 
- `ix_accuracy_baselines_agent_version` (agent_version) 
- `ix_accuracy_baselines_baseline_id` (baseline_id) UNIQUE
- `idx_accuracy_baseline_version` (agent_version) 
- `idx_accuracy_baseline_active` (is_active)

### accuracy_calibration_records

- **数据量**: 0 行 | **字段数**: 24 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| calibration_id | VARCHAR(64) |  | ✅ |  | |
| calibration_type | VARCHAR(32) |  | ✅ |  | |
| status | VARCHAR(32) |  | ✅ |  | |
| old_baseline_id | VARCHAR(64) |  |  |  | |
| old_accuracy_threshold | FLOAT |  |  |  | |
| new_baseline_id | VARCHAR(64) |  |  |  | |
| new_accuracy_threshold | FLOAT |  |  |  | |
| new_pass_immediately | FLOAT |  |  |  | |
| new_warn_threshold | FLOAT |  |  |  | |
| delta | FLOAT |  |  |  | |
| delta_percent | FLOAT |  |  |  | |
| quality_baseline_id | VARCHAR(64) |  |  |  | |
| quality_avg_total | FLOAT |  |  |  | |
| sample_count | INTEGER |  |  |  | |
| passing_count | INTEGER |  |  |  | |
| passing_rate | FLOAT |  |  |  | |
| details | JSON |  |  |  | |
| error_message | TEXT |  |  |  | |
| notification_sent | BOOLEAN |  |  |  | |
| notification_channels | JSON |  |  |  | |
| meta_data | JSON |  |  |  | |
| calibrated_at | DATETIME |  | ✅ |  | |
| created_at | DATETIME |  | ✅ |  | |

**索引**:
- `ix_accuracy_calibration_records_calibration_id` (calibration_id) UNIQUE
- `idx_accuracy_calib_status` (status) 
- `idx_accuracy_calib_time` (calibrated_at) 
- `idx_accuracy_calib_type` (calibration_type)

### accuracy_check_records

- **数据量**: 0 行 | **字段数**: 25 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| check_id | VARCHAR(64) |  | ✅ |  | |
| source | VARCHAR(32) |  | ✅ |  | |
| baseline_id | VARCHAR(64) |  | ✅ |  | |
| baseline_threshold | FLOAT |  | ✅ |  | |
| baseline_name | VARCHAR(128) |  |  |  | |
| current_accuracy | FLOAT |  | ✅ |  | |
| current_sample_count | INTEGER |  |  |  | |
| current_passing_count | INTEGER |  |  |  | |
| deviation | FLOAT |  |  |  | |
| deviation_percent | FLOAT |  |  |  | |
| decision | VARCHAR(32) |  | ✅ |  | |
| passed | BOOLEAN |  | ✅ |  | |
| blocked | BOOLEAN |  |  |  | |
| quality_avg_total | FLOAT |  |  |  | |
| quality_baseline_total | FLOAT |  |  |  | |
| block_reason | TEXT |  |  |  | |
| block_details | JSON |  |  |  | |
| ci_pipeline_id | VARCHAR(128) |  |  |  | |
| ci_build_number | VARCHAR(64) |  |  |  | |
| ci_commit_sha | VARCHAR(64) |  |  |  | |
| ci_branch | VARCHAR(128) |  |  |  | |
| meta_data | JSON |  |  |  | |
| checked_at | DATETIME |  | ✅ |  | |
| created_at | DATETIME |  | ✅ |  | |

**索引**:
- `idx_accuracy_check_source` (source) 
- `ix_accuracy_check_records_check_id` (check_id) UNIQUE
- `idx_accuracy_check_time` (checked_at) 
- `idx_accuracy_check_decision` (decision) 
- `idx_accuracy_check_baseline` (baseline_id)

### accuracy_gate_configs

- **数据量**: 0 行 | **字段数**: 18 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| gate_config_id | VARCHAR(64) |  | ✅ |  | |
| enabled | BOOLEAN |  |  |  | |
| ci_block_enabled | BOOLEAN |  |  |  | |
| default_accuracy_threshold | FLOAT |  |  |  | |
| default_pass_immediately | FLOAT |  |  |  | |
| default_warn_threshold | FLOAT |  |  |  | |
| ci_block_on_warn | BOOLEAN |  |  |  | |
| ci_required_samples | INTEGER |  |  |  | |
| ci_auto_calibrate_on_degradation | BOOLEAN |  |  |  | |
| auto_calibrate | BOOLEAN |  |  |  | |
| monthly_calibration_day | INTEGER |  |  |  | |
| quarterly_calibration_month | INTEGER |  |  |  | |
| notify_on_calibration | BOOLEAN |  |  |  | |
| notification_channels | JSON |  |  |  | |
| meta_data | JSON |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |
| updated_at | DATETIME |  | ✅ |  | |

**索引**:
- `ix_accuracy_gate_configs_gate_config_id` (gate_config_id) UNIQUE

### circuit_breaker_state

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_circuit_breaker_state_id` (id)

### gaia_evolution_events

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| event_type | VARCHAR(32) |  | ✅ |  | |
| event_source | VARCHAR(32) |  | ✅ |  | |
| description | VARCHAR(512) |  | ✅ |  | |
| metadata | JSON |  |  |  | |
| reference_type | VARCHAR(32) |  |  |  | |
| reference_id | INTEGER |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_gaia_evolution_events_created_at` (created_at) 
- `ix_gaia_evolution_events_event_type` (event_type) 
- `idx_gaia_event_ref` (reference_type, reference_id) 
- `idx_gaia_event_type_time` (event_type, created_at)

### gaia_knowledge

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| source | VARCHAR(32) |  | ✅ |  | |
| source_id | VARCHAR(64) |  |  |  | |
| knowledge_type | VARCHAR(32) |  | ✅ |  | |
| title | VARCHAR(256) |  | ✅ |  | |
| content | TEXT |  | ✅ |  | |
| tags | JSON |  |  |  | |
| confidence | FLOAT |  | ✅ |  | |
| impact_score | FLOAT |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| vector_embedded | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_gaia_knowledge_active` (is_active, created_at) 
- `idx_gaia_knowledge_source` (source, source_id) 
- `ix_gaia_knowledge_knowledge_type` (knowledge_type) 
- `ix_gaia_knowledge_source` (source) 
- `idx_gaia_knowledge_type` (knowledge_type, confidence)

### gaia_model_weights

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| module | VARCHAR(64) |  | ✅ |  | |
| weights | JSON |  | ✅ |  | |
| version | VARCHAR(32) |  | ✅ |  | |
| description | VARCHAR(512) |  | ✅ |  | |
| training_run_id | INTEGER |  |  |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_gaia_weights_module_active` (module, is_active, version) 
- `ix_gaia_model_weights_module` (module)

### gaia_training_runs

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| trigger | VARCHAR(32) |  | ✅ |  | |
| knowledge_count | INTEGER |  | ✅ |  | |
| feedback_count | INTEGER |  | ✅ |  | |
| weights_count | INTEGER |  | ✅ |  | |
| vector_index_size | INTEGER |  | ✅ |  | |
| duration_ms | INTEGER |  | ✅ |  | |
| metrics | JSON |  |  |  | |
| error_message | TEXT |  |  |  | |
| started_at | DATETIME |  |  |  | |
| completed_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_gaia_training_status` (status, created_at) 
- `ix_gaia_training_runs_status` (status)

### knowledge_models

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| model_id | VARCHAR(32) |  | ✅ |  | |
| category | VARCHAR(32) |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| source | VARCHAR(64) |  | ✅ |  | |
| source_ref | VARCHAR(256) |  |  |  | |
| content | TEXT |  | ✅ |  | |
| tags | JSON |  |  |  | |
| confidence | FLOAT |  | ✅ |  | |
| version | VARCHAR(16) |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| vector_embedded | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_knowledge_models_category` (category) 
- `idx_km_category` (category, confidence) 
- `idx_km_model_id` (model_id) 
- `ix_knowledge_models_model_id` (model_id) UNIQUE
- `idx_km_active` (is_active, created_at)

### prompt_templates

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 3

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | VARCHAR(64) | ✅ | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| category | VARCHAR(18) |  | ✅ |  | |
| version | VARCHAR(32) |  | ✅ |  | |
| description | VARCHAR(512) |  | ✅ |  | |
| system_prompt | TEXT |  | ✅ |  | |
| user_prompt_template | TEXT |  | ✅ |  | |
| parameters_schema | JSON |  |  |  | |
| output_schema | JSON |  |  |  | |
| tags | JSON |  |  |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ |  | |
| updated_at | DATETIME |  | ✅ |  | |

**索引**:
- `idx_prompt_category` (category) 
- `idx_prompt_active` (is_active) 
- `sqlite_autoindex_prompt_templates_1` (id) UNIQUE

### quality_baselines

- **数据量**: 0 行 | **字段数**: 25 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| baseline_id | VARCHAR(64) |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| agent_version | VARCHAR(64) |  |  |  | |
| model_name | VARCHAR(128) |  |  |  | |
| canary_deployment_id | VARCHAR(64) |  |  |  | |
| avg_usefulness | FLOAT |  |  |  | |
| avg_accuracy | FLOAT |  |  |  | |
| avg_completeness | FLOAT |  |  |  | |
| avg_coherence | FLOAT |  |  |  | |
| avg_harmlessness | FLOAT |  |  |  | |
| avg_total | FLOAT |  |  |  | |
| sample_count | INTEGER |  |  |  | |
| passing_count | INTEGER |  |  |  | |
| passing_rate | FLOAT |  |  |  | |
| passing_threshold | FLOAT |  |  |  | |
| score_distribution | JSON |  |  |  | |
| tags | JSON |  |  |  | |
| sample_meta | JSON |  |  |  | |
| is_active | BOOLEAN |  |  |  | |
| is_archived | BOOLEAN |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |
| updated_at | DATETIME |  | ✅ |  | |
| evaluated_at | DATETIME |  |  |  | |

**索引**:
- `idx_quality_baseline_version` (agent_version, model_name) 
- `idx_quality_baseline_active` (is_active) 
- `ix_quality_baselines_agent_version` (agent_version) 
- `ix_quality_baselines_baseline_id` (baseline_id) UNIQUE
- `ix_quality_baselines_model_name` (model_name)

### quality_eval_jobs

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| job_id | VARCHAR(64) |  | ✅ |  | |
| status | VARCHAR(32) |  | ✅ |  | |
| eval_method | VARCHAR(32) |  |  |  | |
| sample_ids | JSON |  |  |  | |
| model_config | JSON |  |  |  | |
| total_samples | INTEGER |  |  |  | |
| completed_samples | INTEGER |  |  |  | |
| failed_samples | INTEGER |  |  |  | |
| baseline_id | VARCHAR(64) |  |  |  | |
| summary | JSON |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |
| started_at | DATETIME |  |  |  | |
| completed_at | DATETIME |  |  |  | |

**索引**:
- `ix_quality_eval_jobs_job_id` (job_id) UNIQUE

### quality_samples

- **数据量**: 0 行 | **字段数**: 25 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| sample_id | VARCHAR(64) |  | ✅ |  | |
| input_text | TEXT |  | ✅ |  | |
| agent_output | TEXT |  | ✅ |  | |
| expected_output | TEXT |  |  |  | |
| category | VARCHAR(64) |  |  |  | |
| tags | JSON |  |  |  | |
| sample_meta | JSON |  |  |  | |
| canary_deployment_id | VARCHAR(64) |  |  |  | |
| agent_version | VARCHAR(64) |  |  |  | |
| model_name | VARCHAR(128) |  |  |  | |
| status | VARCHAR(32) |  | ✅ |  | |
| eval_method | VARCHAR(32) |  | ✅ |  | |
| score_usefulness | FLOAT |  |  |  | |
| score_accuracy | FLOAT |  |  |  | |
| score_completeness | FLOAT |  |  |  | |
| score_coherence | FLOAT |  |  |  | |
| score_harmlessness | FLOAT |  |  |  | |
| score_total | FLOAT |  |  |  | |
| eval_detail | JSON |  |  |  | |
| eval_log | TEXT |  |  |  | |
| error_message | TEXT |  |  |  | |
| evaluated_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |
| updated_at | DATETIME |  | ✅ |  | |

**索引**:
- `idx_quality_sample_category` (category) 
- `idx_quality_sample_status` (status) 
- `idx_quality_sample_created` (created_at) 
- `ix_quality_samples_category` (category) 
- `ix_quality_samples_sample_id` (sample_id) UNIQUE

### token_budget_alert

- **数据量**: 0 行 | **字段数**: 15 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| alert_id | VARCHAR(64) |  | ✅ |  | |
| rule_name | VARCHAR(128) |  | ✅ |  | |
| alert_level | VARCHAR(16) |  | ✅ |  | |
| current_usage | INTEGER |  |  |  | |
| token_limit | INTEGER |  |  |  | |
| usage_ratio | FLOAT |  |  |  | |
| threshold | FLOAT |  |  |  | |
| agent_name | VARCHAR(128) |  |  |  | |
| user_id | INTEGER |  |  |  | |
| message | TEXT |  |  |  | |
| detail | TEXT |  |  |  | |
| is_resolved | BOOLEAN |  |  |  | |
| resolved_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |

**索引**:
- `ix_token_budget_alert_rule_name` (rule_name) 
- `ix_token_budget_alert_alert_id` (alert_id) UNIQUE
- `ix_token_budget_alert_created_at` (created_at) 
- `ix_token_budget_alert_id` (id)

### token_consumption_record

- **数据量**: 0 行 | **字段数**: 19 | **索引数**: 7

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| record_id | VARCHAR(64) |  | ✅ |  | |
| agent_name | VARCHAR(128) |  | ✅ |  | |
| user_id | INTEGER |  |  |  | |
| session_id | VARCHAR(64) |  |  |  | |
| rule_name | VARCHAR(128) |  |  |  | |
| prompt_tokens | INTEGER |  |  |  | |
| completion_tokens | INTEGER |  |  |  | |
| total_tokens | INTEGER |  |  |  | |
| is_truncated | BOOLEAN |  |  |  | |
| is_downgraded | BOOLEAN |  |  |  | |
| degrade_strategy | VARCHAR(32) |  |  |  | |
| estimated_cost | FLOAT |  |  |  | |
| cost_per_token | FLOAT |  |  |  | |
| model_name | VARCHAR(64) |  |  |  | |
| operation | VARCHAR(64) |  |  |  | |
| status | VARCHAR(32) |  |  |  | |
| metadata_json | TEXT |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |

**索引**:
- `ix_token_consumption_record_created_at` (created_at) 
- `ix_token_consumption_record_rule_name` (rule_name) 
- `ix_token_consumption_record_id` (id) 
- `ix_token_consumption_record_agent_name` (agent_name) 
- `ix_token_consumption_record_record_id` (record_id) UNIQUE
- `ix_token_consumption_record_session_id` (session_id) 
- `ix_token_consumption_record_user_id` (user_id) 

---

## I.平台与支撑

### ab_test_decision_logs

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| experiment_id | INTEGER |  | ✅ |  | |
| decision | VARCHAR(16) |  | ✅ |  | |
| variant_name | VARCHAR(64) |  |  |  | |
| p_value | FLOAT |  |  |  | |
| reason | TEXT |  | ✅ |  | |
| details | JSON |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_ab_test_decision_logs_created_at` (created_at) 
- `ix_ab_test_decision_logs_experiment_id` (experiment_id)

### ab_test_events

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| experiment_id | INTEGER |  | ✅ |  | |
| variant_id | INTEGER |  | ✅ |  | |
| user_id | INTEGER |  |  |  | |
| visitor_id | VARCHAR(64) |  |  |  | |
| event_type | VARCHAR(32) |  | ✅ |  | |
| metadata | JSON |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_ab_test_events_variant_id` (variant_id) 
- `ix_ab_test_events_experiment_id` (experiment_id) 
- `ix_ab_test_events_visitor_id` (visitor_id) 
- `ix_ab_test_events_user_id` (user_id) 
- `ix_ab_test_events_created_at` (created_at)

### ab_test_variants

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| experiment_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(64) |  | ✅ |  | |
| description | VARCHAR(256) |  | ✅ |  | |
| sort_order | INTEGER |  | ✅ |  | |
| is_control | BOOLEAN |  | ✅ |  | |
| config | JSON |  |  |  | |
| weight | FLOAT |  | ✅ |  | |
| is_default | BOOLEAN |  | ✅ |  | |
| impressions | INTEGER |  | ✅ |  | |
| clicks | INTEGER |  | ✅ |  | |
| conversions | INTEGER |  | ✅ |  | |
| views | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_ab_test_variants_experiment_id` (experiment_id)

### ab_tests

- **数据量**: 0 行 | **字段数**: 15 | **索引数**: 3

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| traffic_fraction | FLOAT |  | ✅ |  | |
| min_sample_size | INTEGER |  | ✅ |  | |
| significance_level | FLOAT |  | ✅ |  | |
| metric | VARCHAR(32) |  | ✅ |  | |
| target_brochure_id | INTEGER |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| started_at | DATETIME |  |  |  | |
| completed_at | DATETIME |  |  |  | |
| cached_results | JSON |  |  |  | |

**索引**:
- `ix_ab_tests_user_id` (user_id) 
- `ix_ab_tests_target_brochure_id` (target_brochure_id) 
- `ix_ab_tests_status` (status)

### activity ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_activity_id` (id)

### api_usage_log ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_api_usage_log_id` (id)

### app_store_plugin_installs

- **数据量**: 0 行 | **字段数**: 7 | **索引数**: 3

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| plugin_id | INTEGER |  | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| version_id | INTEGER |  |  |  | |
| is_active | INTEGER |  | ✅ |  | |
| installed_at | DATETIME |  |  |  | |
| uninstalled_at | DATETIME |  |  |  | |

**索引**:
- `ix_app_store_plugin_installs_user_id` (user_id) 
- `ix_app_store_plugin_installs_plugin_id` (plugin_id) 
- `ix_app_store_plugin_installs_id` (id)

### app_store_plugin_reviews

- **数据量**: 0 行 | **字段数**: 6 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| plugin_id | INTEGER |  | ✅ |  | |
| reviewer_id | INTEGER |  | ✅ |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| comments | TEXT |  |  |  | |
| created_at | DATETIME |  |  |  | |

**索引**:
- `ix_app_store_plugin_reviews_plugin_id` (plugin_id) 
- `ix_app_store_plugin_reviews_id` (id)

### app_store_plugin_versions

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| plugin_id | INTEGER |  | ✅ |  | |
| version | VARCHAR(32) |  | ✅ |  | |
| changelog | TEXT |  |  |  | |
| download_url | VARCHAR(512) |  |  |  | |
| required_api_version | VARCHAR(32) |  | ✅ |  | |
| file_size | INTEGER |  |  |  | |
| checksum | VARCHAR(128) |  |  |  | |
| is_published | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |

**索引**:
- `ix_app_store_plugin_versions_plugin_id` (plugin_id) 
- `ix_app_store_plugin_versions_id` (id)

### app_store_plugins

- **数据量**: 0 行 | **字段数**: 18 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| developer_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| icon_url | VARCHAR(512) |  |  |  | |
| category | VARCHAR(64) |  | ✅ |  | |
| version | VARCHAR(32) |  | ✅ |  | |
| price | FLOAT |  | ✅ |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| install_count | INTEGER |  | ✅ |  | |
| rating | FLOAT |  | ✅ |  | |
| rating_count | INTEGER |  | ✅ |  | |
| homepage_url | VARCHAR(512) |  |  |  | |
| documentation_url | VARCHAR(512) |  |  |  | |
| repository_url | VARCHAR(512) |  |  |  | |
| tags | VARCHAR(512) |  |  |  | |
| created_at | DATETIME |  |  |  | |
| updated_at | DATETIME |  |  |  | |

**索引**:
- `ix_app_store_plugins_developer_id` (developer_id) 
- `ix_app_store_plugins_id` (id) 
- `ix_app_store_plugins_category` (category) 
- `ix_app_store_plugins_status` (status)

### business_need ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_business_need_id` (id)

### contact ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_contact_id` (id)

### enterprise ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_enterprise_id` (id)

### enterprise_relation ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_enterprise_relation_id` (id)

### integrations

- **数据量**: 0 行 | **字段数**: 12 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| provider | VARCHAR(32) |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| enabled | BOOLEAN |  | ✅ |  | |
| config | TEXT |  | ✅ |  | |
| last_sync_at | DATETIME |  |  |  | |
| webhook_url | VARCHAR(512) |  | ✅ |  | |
| webhook_secret | VARCHAR(128) |  | ✅ |  | |
| webhook_enabled | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_integrations_user_id` (user_id)

### webhook_subscriptions

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| url | VARCHAR(512) |  | ✅ |  | |
| secret | VARCHAR(128) |  | ✅ |  | |
| events | TEXT |  | ✅ |  | |
| active | BOOLEAN |  | ✅ |  | |
| retry_count | INTEGER |  | ✅ |  | |
| timeout_seconds | INTEGER |  | ✅ |  | |
| last_triggered_at | DATETIME |  |  |  | |
| last_response_code | INTEGER |  |  |  | |
| last_error | TEXT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_webhook_subscriptions_user_id` (user_id) 

---

## 附录: 全库统计

| 指标 | 数值 |
|---|---|
| 总表数 | 123 |
| 总字段数 | 1085 |
| 总索引数 | 223 |
| 有数据表数 | 8 |
| 占位表数 | 29 |
