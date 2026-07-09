# AI数字名片 — 产品需求文档 (PRD)

> 版本: v1.0 | 更新日期: 2026-07-08  
> 项目目录: `D:\AI数智名片`  
> 仓库: `https://github.com/eagle13579/ai-digital-card`

---

## 1. 产品定位

**一句话定义**:  
AI数字名片是一套以"电子画册 + AI智能匹配 + 信任网络"为核心能力的商务人脉管理工具，帮助用户在微信生态内创建精美的数字名片/画册、自动匹配潜在客户/供应商/合作伙伴、并通过信任关系图谱沉淀人脉资产。

**目标用户**:
- 中小企业主 / 创业者（找客户、找投资人）
- 销售 / BD 人员（找线索、拓客）
- 自由职业者 / 个体服务者（展示个人品牌）
- 采购 / 供应链人员（找供应商）

**核心差异**:
- ✅ 将"名片"从单页静态卡片升级为**多页电子画册**（翻页效果）
- ✅ 基于供需标签的**AI双向匹配引擎**（不只是搜，还主动推荐）
- ✅ **信任网络图谱**可视化（1度/2度人脉）
- ✅ 微信生态天然传播（小程序 + H5 + 海报）

---

## 2. 功能清单

### 2.1 P0 — 最简可用 (MVP)

#### 2.1.1 用户注册/登录
| 项目 | 说明 |
|------|------|
| **输入** | 手机号 + 密码 (微信小程序: wx.login code) |
| **输出** | JWT token + 用户信息 |
| **验收标准** | 用户可注册、登录、获取自己的profile；小程序可静默登录打通 openid |
| **状态** | ✅ 已完成 (后端 auth_router、前端 login page) |

#### 2.1.2 电子画册创建与管理
| 项目 | 说明 |
|------|------|
| **输入** | 姓名/公司/职位/手机/微信/简介 + 用途选择 (partner/client/investor/supplier) |
| **输出** | 多页画册 (Brochure + Pages)，支持封面/正文/图片/视频四种页面类型 |
| **验收标准** | 用户可创建、编辑、删除画册；每页可填内容；前端按用途提供模板推荐 |
| **状态** | ⚠️ 后端接口就绪 (brochure.py / BrochureService)，前端 CardEditorPage 已实现但API调用路径不统一 |

**后端 API 路由**:
- `POST /api/v1/brochures` — 创建画册
- `GET /api/v1/brochures` — 列表（cursor分页）
- `GET /api/v1/brochures/{id}` — 详情
- `PUT /api/v1/brochures/{id}` — 更新
- `DELETE /api/v1/brochures/{id}` — 删除
- `POST /api/v1/brochures/{id}/publish` — 发布
- `GET /api/v1/brochures/share/{share_token}` — 公开访问
- `GET /api/v1/brochures/template/{purpose}` — 用途模板
- `POST /api/v1/brochures/smart-search` — 智能搜索 (别名路由)

#### 2.1.3 画册公开查看 & 分享
| 项目 | 说明 |
|------|------|
| **输入** | share_token (16位hex) |
| **输出** | 完整翻页HTML (StPageFlip渲染) + 小程序引导 |
| **验收标准** | 非登录用户可通过链接查看画册；支持翻页动画；底部有"打开小程序"引导按钮 |
| **状态** | ✅ 已完成 (brochure_viewer.py / BrochureRenderer) — 含精美主题色系统 |

**分享方式**:
- H5链接: `/view/{share_token}`
- 分享 token 自动生成 (uuid4.hex[:16])
- 查看计数自动递增

#### 2.1.4 AI智能匹配引擎
| 项目 | 说明 |
|------|------|
| **输入** | 用户的供需标签 (provide/need) + 简介 + 画册内容 |
| **输出** | 按综合匹配度排序的用户列表 (含脱敏信息) |
| **验收标准** | 点击匹配后返回Top N推荐用户，显示匹配度分数和共同标签 |
| **状态** | ⚠️ 后端MatchEngine完整实现 (三层评分: 标签重叠40% + 语义相似40% + 标签权重20%)，但前端调用路径未对齐 |

**后端 API**:
- `POST /api/v1/match/engine` — 触发匹配引擎
- `GET /api/v1/match/records` — 获取匹配记录
- `PUT /api/v1/match/records/{id}/status` — 更新匹配状态
- `POST /api/v1/match/semantic-search` — 语义搜索
- `POST /api/v1/match/{record_id}/unlock` — 付费解锁联系方式

**评分公式**:
```
score = tag_overlap × 0.40 + vector_semantic × 0.40 + tag_weight × 0.20
```

### 2.2 P1 — 核心体验增强

#### 2.2.1 AI智能生成画册内容
| 项目 | 说明 |
|------|------|
| **输入** | 用户基本信息 (姓名/公司/职位/简介) + 用途 (partner/client/investor/supplier) |
| **输出** | 自动生成的画册页面文案 + 模板配色方案 |
| **验收标准** | 用户只需填简单表单，AI自动生成多页画册内容 (封面文案、介绍、卖点等) |
| **状态** | ❌ 未实现 — 需连接 DeepSeek API 创建 `/api/v1/ai/generate-brochure` 端点 |

#### 2.2.2 信任网络图谱
| 项目 | 说明 |
|------|------|
| **输入** | 用户ID |
| **输出** | 关系图谱 (节点: person/company/industry/tag, 边: works_at/matched/trusted) |
| **验收标准** | 图谱展示1度/2度关系，节点可点击查看详情；显示匹配连接 |
| **状态** | ⚠️ 知识图谱服务完整实现 (knowledge_graph.py, 527行)，含网络查询/洞察分析/连接推荐，但前端 NetworkGraphPage 集成待验证 |

**后端 API**:
- `GET /api/v1/knowledge-graph/network/{user_id}?depth=2` — 获取用户网络
- `GET /api/v1/knowledge-graph/insights/{user_id}` — 用户洞察分析
- `GET /api/v1/knowledge-graph/connect` — 连接推荐
- `POST /api/v1/knowledge-graph/rebuild` — 重建图谱 (管理员)

#### 2.2.3 信任关系管理
| 项目 | 说明 |
|------|------|
| **输入** | 被信任用户ID |
| **输出** | 信任关系记录 (双向展示: 我信任的人 / 信任我的人) |
| **验收标准** | 用户可添加/移除信任关系，查看互信列表，信任度数计算 (1度直接信任、2度间接信任) |
| **状态** | ✅ 完整实现 (trust.py router + TrustService) |

**后端 API**:
- `GET /api/v1/trust/network` — 获取我的信任网络
- `POST /api/v1/trust/network` — 添加信任关系
- `DELETE /api/v1/trust/network/{trusted_user_id}` — 移除信任关系
- `GET /api/v1/trust/network/{user_id}` — 查看指定用户信任网络

#### 2.2.4 标签管理 (供需匹配基础)
| 项目 | 说明 |
|------|------|
| **输入** | 标签文本 + 类型 (provide/need) + 权重 |
| **输出** | 用户标签列表 |
| **验收标准** | 用户可添加/删除供需标签，标签权重影响匹配排序 |
| **状态** | ✅ UserTag模型 + tag_router 已实现 |

### 2.3 P2 — 扩展功能

#### 2.3.1 付费解锁联系方式
| 项目 | 说明 |
|------|------|
| **输入** | match_record_id |
| **输出** | 完整的姓名/电话/微信号 (脱敏→明文) |
| **验收标准** | 免费会员看到脱敏信息，付费会员 (gold/diamond/board) 可消耗配额解锁完整联系方式 |
| **状态** | ⚠️ 后端完整实现 (含配额管理/配额定时重置) — 但支付流程未连通 |

#### 2.3.2 批量导入/导出名片
| 项目 | 说明 |
|------|------|
| **输入** | CSV文件 |
| **输出** | 导入结果 (创建/重复/错误) / CSV导出文件 |
| **验收标准** | 用户可通过CSV批量导入名片 (去重)，也可导出所有名片为CSV |
| **状态** | ✅ 已实现 (BrochureService.batch_import_from_csv / batch_export_csv) |

#### 2.3.3 游客访问记录
| 项目 | 说明 |
|------|------|
| **输入** | visitor_id / visitor_ip / source |
| **输出** | 访问记录列表 |
| **验收标准** | 画册主人可查看谁访问了自己的画册 |
| **状态** | ✅ VisitorLog模型 + visitor_router 已实现 |

#### 2.3.4 海报生成 (朋友圈分享)
| 项目 | 说明 |
|------|------|
| **输入** | 用户名片信息 + 模板选择 |
| **输出** | 分享海报图片 (PNG/JPG) |
| **验收标准** | 一键生成可分享到朋友圈的精美海报 |
| **状态** | ❌ 未实现 — 需要海报渲染服务 |

---

## 3. 传播方案

### 3.1 微信小程序分享

| 方式 | 实现 |
|------|------|
| **wx.shareAppMessage** | 小程序内点击"分享"后调用微信原生分享，好友收到小程序卡片 (含封面/标题/描述) |
| **场景值识别** | 从分享卡片进入时获取 `share_token`，自动跳转到对应画册详情页 |
| **裂变激励** | 分享获得额外AI调用次数 (每日上限3次，`share.ts` 已实现) |

**代码位置**: `liankebao-weapp/src/utils/share.ts` — getTodayShareCount / incrementShareCount

### 3.2 生成海报发朋友圈

| 方式 | 实现 |
|------|------|
| **海报生成** | 需新建服务: 接收名片信息 → 渲染为图文海报 (PNG) → 保存到 CDN/上传 → 返回下载URL |
| **分享到朋友圈** | 用户长按保存海报到相册，或小程序 `wx.saveImageToPhotosAlbum` |
| **海报模板** | 至少提供3套模板 (商务/简约/科技)，含二维码 |

**状态**: ❌ 未实现 — P2计划

### 3.3 H5链接分享

| 方式 | 实现 |
|------|------|
| **公开链接** | `/view/{share_token}` — 用 StPageFlip 渲染翻页画册，无需登录即可查看 |
| **微信内H5** | 含"打开小程序"引导按钮 (`_build_miniapp_guide_html`)，点击跳转小程序详情页 |
| **QR码** | 分享链接可通过后端生成二维码 (需集成 qrcode 库) |
| **SEO优化** | 微信内不做SEO，但 Open Graph 标签需加 (标题/描述/封面) 以便在聊天中展示卡片 |

**状态**: ⚠️ H5查看页已完成 (brochure_viewer.py)，分享链接生成已完成 (`/share-link`端点)，QR码未实现

---

## 4. 架构概览

```
┌────────────────────────────────────────────────────────────────────┐
│                        前端层 (Presentation)                        │
│                                                                    │
│  ┌──────────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  React 19 + Vite 6   │  │  微信小程序(原生)  │  │  Taro 多平台  │ │
│  │  (H5 / 管理后台)      │  │  miniapp/        │  │  liankebao-  │ │
│  │  frontend/           │  │  3 Tab页 + 10+页  │  │  weapp/      │ │
│  │  ⚡ SSR 就绪          │  │  组件化架构        │  │  (编译后)     │ │
│  └────────┬─────────────┘  └────────┬─────────┘  └──────┬───────┘ │
│           │                         │                    │         │
│           │     HTTP / WebSocket    │                    │         │
└───────────┼─────────────────────────┼────────────────────┼─────────┘
            │                         │                    │
            ▼                         ▼                    ▼
┌────────────────────────────────────────────────────────────────────┐
│                       网关层 (Gateway)                              │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Nginx / API Gateway                                         │  │
│  │  * 路由分发 (H5→:8200, API→:8002)                            │  │
│  │  * SSL 终止 / CORS / 限流                                    │  │
│  │  * 静态资源缓存 (frontend/dist)                                │  │
│  │  * WebSocket 代理 (AI聊天)                                    │  │
│  └─────────────────────────┬────────────────────────────────────┘  │
└────────────────────────────┼────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                       后端层 (Backend)                              │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  FastAPI (Async) — port 8002/8201                            │  │
│  │  ├── Middleware (20个): RequestID / CORS / RateLimit / I18n  │  │
│  │  │                  / CSRF / SecurityHeaders / Metrics / OTEL│  │
│  │  ├── Routers (40+): auth / user / brochure / match / trust   │  │
│  │  │                  / knowledge-graph / payment / webhook ... │  │
│  │  ├── Service Layer: matching_engine / trust_service /        │  │
│  │  │                  brochure_service / knowledge_graph ...    │  │
│  │  ├── AI Engine: vector_search / OCR / NLP / DeepSeek集成      │  │
│  │  └── Task Queue: 异步任务 (匹配/通知/导出)                    │  │
│  └─────────────────────────┬────────────────────────────────────┘  │
│                            │                                       │
│  ┌─────────────────────────┴────────────────────────────────────┐  │
│  │  基础设施 (Infrastructure)                                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │  │
│  │  │ SQLite   │  │  Redis   │  │  文件存储  │  │ 外部AI API   │ │  │
│  │  │ (开发)    │  │ 缓存/限流  │  │ 上传目录   │  │ DeepSeek等   │ │  │
│  │  │ PostgreSQL│  │ 会话管理   │  │ uploads/  │  │             │ │  │
│  │  │ (生产)    │  │          │  │           │  │             │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### 4.1 技术栈明细

| 层级 | 技术 | 版本/说明 |
|------|------|-----------|
| **前端 (H5)** | React + Vite + TailwindCSS | React 19 / Vite 6 / Tailwind v4 |
| **前端 (小程序)** | 原生微信小程序 + Taro | 双版本并行开发 |
| **后端** | FastAPI + SQLAlchemy | Async 异步架构 |
| **数据库** | SQLite (开发) / PostgreSQL (生产) | Alembic 迁移已配置 |
| **缓存** | Redis | 速率限制、会话缓存、向量缓存 |
| **AI** | DeepSeek API + TF-IDF + 向量搜索 | 本地 TF-IDF (零依赖) + 可切换 m3e/OpenAI |
| **部署** | Docker + Nginx + GitHub Actions | 含蓝绿部署/金丝雀发布 |
| **监控** | Sentry + Prometheus + OpenTelemetry | 生产级可观测性 |

### 4.2 端口说明

| 端口 | 服务 | 说明 |
|------|------|------|
| 8002 | FastAPI 后端 | 当前开发端口 |
| 8201 | FastAPI 后端 | 文档中记录的端口 (需对齐) |
| 5173 | Vite 开发服务器 | 前端开发 |
| 6379 | Redis | 缓存服务 |

---

## 5. 数据模型

### 5.1 表结构总览

```
users ──┬── brochures ──┬── pages
         │               │
         ├── user_tags    ├── visitor_logs
         │                │
         ├── match_records
         │
         ├── trust_network
         │
         └── unlock_records
```

### 5.2 user 表 (`users`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int (PK) | 主键 |
| username | str(64), unique | 用户名 |
| phone | str(20), unique | 手机号 |
| password_hash | str(128) | 密码哈希 |
| wechat_openid | str(64), unique | 微信小程序 openid |
| name | str(64) | 姓名 (非空) |
| company | str(128) | 公司 |
| title | str(128) | 职位 |
| intro | text | 个人简介 |
| avatar | str(256) | 头像URL |
| role | str(16) | 角色: user/admin |
| membership_tier | str(16) | 会员等级: free/gold/diamond/board |
| membership_expires_at | datetime | 会员过期时间 |
| unlock_quota | int | 本月剩余解锁配额 |
| quota_reset_at | datetime | 配额重置时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 5.3 brochure 表 (`brochures`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int (PK) | 主键 |
| user_id | int (FK→users) | 创建者 |
| title | str(128) | 标题 |
| cover | str(256) | 封面图URL |
| purpose | str(32) | 用途: partner/client/investor/supplier |
| pages_count | int | 页面数 |
| status | str(16) | draft/published |
| share_token | str(32), unique | 分享token |
| view_count | int | 访问次数 |
| album_meta | text, nullable | 翻页图册元数据 (JSON) |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**关系**: `owner → User`, `pages → Page[]`

### 5.4 page 表 (`pages`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int (PK) | 主键 |
| brochure_id | int (FK→brochures) | 所属画册 |
| sort_order | int | 排序序号 |
| content_type | str(16) | text/image/cover/video |
| content | text | 文字内容 |
| image_url | str(256) | 图片URL |
| media_url | str(512) | 视频/多媒体URL |
| ai_summary | text | AI摘要 |

### 5.5 match_record 表 (`match_records`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int (PK) | 主键 |
| user_a_id | int (FK→users) | 匹配发起方 |
| user_b_id | int (FK→users) | 匹配对象 |
| match_score | float | 匹配分 (0~1) |
| status | str(16) | pending/matched/confirmed |
| common_tags | text (JSON) | 共同标签列表 |
| source | str(16) | auto/manual |
| created_at | datetime | 创建时间 |

### 5.6 user_tag 表 (`user_tags`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int (PK) | 主键 |
| user_id | int (FK→users) | 用户ID |
| tag_type | str(16) | provide/need |
| tag | str(64) | 标签文本 |
| weight | float | 权重 (默认1.0) |
| source | str(16) | manual/ai/import |
| created_at | datetime | 创建时间 |

### 5.7 trust_network 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int (PK) | 主键 |
| user_id | int (FK→users) | 主动信任方 |
| trusted_user_id | int (FK→users) | 被信任方 |
| created_at | datetime | 创建时间 |

**索引**: 唯一约束 (user_id, trusted_user_id)

### 5.8 unlock_record 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int (PK) | 主键 |
| user_id | int | 解锁方用户ID |
| target_user_id | int | 被解锁用户ID |
| match_record_id | int | 关联匹配记录ID |
| created_at | datetime | 解锁时间 |

---

## 6. 已知问题清单 (需修复)

> 以下问题基于代码排查得出，按严重程度排序。

### P0 级别 (阻塞核心功能)

| # | 问题 | 模块 | 描述 | 修复方向 |
|---|------|------|------|----------|
| 1 | **前端 MatchingPage 调用路径不匹配** | 前端→后端 | MatchingPage 调用 `GET /api/v1/brochure/list` (单数) 和 `POST /api/card/{id}/match`，但后端实际路由是 `GET /api/v1/brochures` (复数) 和 `POST /api/v1/match/engine` | 修改前端API调用或添加别名路由 |
| 2 | **CardEditorPage 部分 API 调用不对齐** | 前端→后端 | CardEditorPage 内部调用路径可能与实际后端路由不匹配 | 审查 CardEditor 所有 fetch 调用，统一使用 v1 前缀 |
| 3 | **缺少 AI 自动生成画册端点** | 后端 | 用户填完基本信息后无法 AI 自动生成画册内容，需手动逐页编辑 | 新建 `/api/v1/ai/generate-brochure`，调用 DeepSeek API 生成页面文案 + 模板建议 |
| 4 | **miniapp 部分页面路由不存在** | 小程序 | `app.json` 中注册了 `pages/brochure/create/index`、`pages/brochure/preview/index`、`pages/ai/match/index`、`pages/network/graph/index` 但物理文件缺失 | 创建缺失页面文件或调整 app.json 引用 |

### P1 级别 (体验问题)

| # | 问题 | 模块 | 描述 | 修复方向 |
|---|------|------|------|----------|
| 5 | **分享链接缺少 BASE_URL** | 后端 | `get_share_link` 返回 `/brochure/share/{token}` 相对路径而不是完整 `https://...` URL | 使用 `settings.BASE_URL` 拼接完整链接 |
| 6 | **双端口不一致** | 后端配置 | 文档/老的 main.py 记录 port 8201，但 run.py 实际用 port 8002，miniapp config 连 8002 | 统一端口或文档对齐 |
| 7 | **海报生成未实现** | 全栈 | 无法生成可发朋友圈的分享海报 | 新建海报渲染服务 (Pillow/node-canvas) |
| 8 | **QR码生成未实现** | 后端 | H5分享没有附带二维码的能力 | 集成 qrcode 库，分享端点返回二维码图片URL |
| 9 | **小程序分享的每日计数存本地** | 小程序 | 分享次数计数用 Taro.getStorageSync 存本地，换设备/清缓存后丢失 | 改为后端存储 (Redis/DB) |

### P2 级别 (优化/增强)

| # | 问题 | 模块 | 描述 | 修复方向 |
|---|------|------|------|----------|
| 10 | **匹配引擎全量扫描** | 后端 | `get_daily_recommendations` 遍历所有用户，O(n²) 复杂度，用户量1000+后性能问题 | 引入向量预索引 + 分片计算 |
| 11 | **TrustNetwork 缺少双向确认** | 后端 | 信任关系目前是单向 (A信任B，B不需要确认)，缺少"好友"式双向确认流程 | 添加 pending/confirmed 状态字段，B需确认 |
| 12 | **知识图谱缺少前端可视化** | 前端 | NetworkGraphPage 引用了 `KnowledgeGraphEmbed` 组件但交互效果待验证 | 验证/完善图谱交互 (D3.js/vis-network) |
| 13 | **测试覆盖率不足** | 全栈 | 核心流程 (匹配/解锁/信任) 缺乏集成测试 | 补充 e2e / 集成测试 |
| 14 | **会员支付流程未连通** | 全栈 | 会员解锁配额的扣减逻辑已实现，但支付下单/回调流程未打通 | 对接微信支付统一下单 + 回调通知 |

---

## 7. 分阶段实施路线图

### Phase 0 — 修复 & 打通 (当前 ~ 2周)

| 任务 | 优先级 | 负责人 | 预计工时 |
|------|--------|--------|----------|
| 修复前端 MatchingPage API 路径 | P0 | 前端 | 2天 |
| 统一后端端口 (8002) 并文档对齐 | P1 | 后端 | 0.5天 |
| 修复分享链接为完整 URL | P1 | 后端 | 0.5天 |
| 补充缺失的小程序页面 | P0 | 小程序 | 2天 |
| 验证 CardEditorPage CRUD 全流程 | P0 | 全栈 | 3天 |
| 验证信任图谱前端渲染 | P1 | 前端 | 2天 |

### Phase 1 — AI核心能力 (3~4周)

| 任务 | 优先级 | 预计工时 |
|------|--------|----------|
| 实现 AI 自动生成画册 (DeepSeek + Brochure) | P0 | 5天 |
| 海报生成服务 (Pillow渲染 + 模板) | P2 | 5天 |
| QR码生成 & 分享增强 | P1 | 2天 |
| 匹配引擎性能优化 (向量索引) | P2 | 3天 |
| 小程序分享次数改为后端存储 | P1 | 1天 |

### Phase 2 — 社交 & 付费 (4~6周)

| 任务 | 优先级 | 预计工时 |
|------|--------|----------|
| 信任关系双向确认 (好友系统) | P2 | 3天 |
| 微信支付接入 (下单/回调) | P1 | 5天 |
| 会员体系全流程测试 | P1 | 3天 |
| E2E 测试补充 | P2 | 5天 |
| 知识图谱完善 (更多边类型 + 前端交互优化) | P2 | 5天 |

### Phase 3 — 规模化 (6~8周)

| 任务 | 预计工时 |
|------|----------|
| 数据库迁移 PostgreSQL | 3天 |
| 匹配引擎分布式化 (向量数据库) | 5天 |
| 数据看板/分析报表 | 3天 |
| 国际化 (i18n 完善) | 3天 |
| BI / 管理员后台 | 5天 |

---

## 附录

### A. 技术债务记录

| 项目 | 位置 | 说明 |
|------|------|------|
| main.py 已废弃 | backend/main.py | 文件只跳转到 run.py，应删除或标记清晰 |
| 数据库使用 SQLite (开发) | backend/data/digital_brochure.db | 生产应切换 PostgreSQL |
| .env 有多处 | backend/.env + .env.production + 根目录 .env.example | 环境变量分散，需统一管理 |
| test_500.py 等测试脚本在根目录 | /test_*.py | 测试应与 backend/tests/ 合并 |

### B. 架构决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 前端框架 | React 19 + Vite 6 | 生态成熟，H5兼容性好 |
| 后端框架 | FastAPI (Async) | 高吞吐、自动文档、类型安全 |
| 数据库 | SQLAlchemy (Async) | ORM 分离、支持多后端 |
| 匹配引擎 | 标签重叠 + TF-IDF 语义 | 零外部依赖，可离线运行 |
| 小程序 | 原生 + Taro | 原生保证性能，Taro 用于多平台 |
| AI模型 | DeepSeek API | 性价比高，中文能力强 |
