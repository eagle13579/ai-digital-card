# AI数字名片 — 企业家供需匹配平台

## 一句话定位

AI驱动的企业家数字名片与供需匹配平台 — 上传名片即生成3D翻页图册，AI标签匹配自动推荐合作机会

## 版本

v2.1 · 2026-05-31 · 唤醒上下文+架构全景图+五层模式重构

v2.2 · 2026-05-31 · 链客宝生态融合 — 信任网络桥接+企盟匹配+网关路由升级

## 产品架构

```
客户端层                     接入层                     API网关层 :8003
┌────────────────┐    ┌──────────────────┐    ┌──────────────────────────┐
│ H5翻页图册查看器 │    │ Alpine.js +      │    │ FastAPI + SQLAlchemy     │
│ 名片编辑器(4步) │◀───│ Tailwind CDN     │◀───│ JWT认证 · CORS · 7路由   │
│ 首页(名片列表)   │    │ 零构建部署        │    │ 30个API端点               │
│ Share公开页     │    │ StPageFlip 3D    │    └──────┬───────────────────┘
└────────────────┘    └──────────────────┘           │
                         ┌──────────────────────────────┴────────────┐
                         │              引擎层                        │
                         │  ┌────────┐ ┌────────┐ ┌────────┐ ┌─────┐ │
                         │  │匹配引擎 │ │OCR扫描 │ │AI提取  │ │信任 │ │
                         │  │余弦+知识│ │pdfplum │ │DeepSeek│ │网络 │ │
                         │  │图谱融合  │ │Tessera │ │正则NLP │ │     │ │
                         │  └────────┘ └────────┘ └────────┘ └─────┘ │
                         └──────────────────────────────────────────┘
                                      │
                         ┌────────────┴────────────┐
                         │      数据层 SQLite       │
                         │  User/Brochure/Page/    │
                         │  UserTag/MatchRecord/   │
                         │  VisitorLog/TrustNetwork│
                         └─────────────────────────┘
```

## 核心功能

| 功能 | 状态 | 来源 |
|:-----|:----:|:-----|
| JWT认证（注册/登录/微信Mock） | ✅ | 合并自存档v1.0 |
| 画册CRUD（含多页管理） | ✅ | 独立项目升级 |
| 发布+share_token分享 | ✅ | 合并自链客宝 |
| 公开访问（无需登录） | ✅ | 独立项目 |
| 标签系统（provide/need双维度） | ✅ | 合并自存档v1.0 |
| 供需匹配引擎（余弦+知识图谱） | ✅ | 三源合并 |
| 信任网络 | ✅ | 独立项目保留 |
| OCR名片扫描 | ✅ | 合并自链客宝 |
| NLP字段提取（正则+DeepSeek） | ✅ | 合并自链客宝 |
| AI自动排版 | ✅ | 合并自存档v1.0 |
| 访客日志+兴趣表达 | ✅ | 独立项目保留 |
| 二维码/扫码跳转 | ✅ | 独立项目保留 |
| H5翻页图册查看（StPageFlip 3D） | ✅ | 合并自存档v1.0 |
| 4步名片编辑器 | ✅ | 新创建 |

## 后端模块清单（21文件 + 12服务）

```
backend/
├── main.py                     # 入口 (:8003)
├── requirements.txt
├── app/
│   ├── __init__.py             # create_app() + CORS + 路由注册
│   ├── config.py               # Settings (JWT/DB/AI)
│   ├── database.py             # SQLAlchemy引擎
│   ├── models/ (5)             # User/Brochure+Page/Tag/Match/Visitor/Trust
│   ├── schemas/                # Pydantic 模型
│   ├── routers/ (8)            # Auth/User/Brochure/Tag/Match/Trust/Visitor
│   ├── services/ (5)           # Brochure/Tag/MatchingEngine Trust/BrochureRender
│   ├── ai/ (2)                 # Extractor (NLP+AI) + OCR Scanner
│   └── templates/ (3)          # 查看器/编辑器/首页
├── data/                       # SQLite数据库
└── scripts/
    └── migrate_v1_to_v2.py     # 数据迁移
```

## API端点（30个）

| 分组 | 端点数 | 路径前缀 |
|:-----|:------:|:---------|
| 认证 | 3 | `/api/auth/*` |
| 用户 | 4 | `/api/users/*` |
| 画册 | 7 | `/api/brochures/*` |
| 标签 | 4 | `/api/tags/*` |
| 匹配 | 3 | `/api/match/*` |
| 信任 | 4 | `/api/trust/*` |
| 访客 | 3 | `/api/visitors/*` |
| 健康 | 2 | `/health`, `/api/health` |

## 定价模式

免费注册，基础名片免费。高级功能：VIP会员¥999/月（AI扫描+高级匹配+数据分析）

## 数字员工

**计名**（Digital Card Officer）— 名片设计与供需匹配AI员工
- 灵魂来源：乔布斯(审美)+林纳斯(工程)+宫本武藏(战略)
- 能力：名片设计、OCR识别、匹配算法、用户洞察
- 端口: 8003

## 部署

```bash
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8003
# → Swagger: http://localhost:8003/docs
```

## 工业化成熟度

| 维度 | v2.1评分 | v2.2目标 |
|:-----|:-------:|:---------|
| JWT认证 | 8/10 | 9/10 |
| 多租户支持 | 6/10 | 8/10 |
| 测试覆盖 | 3/10 | 7/10 |
| CI/CD | 2/10 | 7/10 |
| 监控可观测 | 2/10 | 5/10 |
| **综合** | **4.5/10** | **7/10** |

---

## v2.2 (当前版本 · 2026-05-31)

### 版本目标

AI数字名片与链客宝生态深度融合 — 信任网络桥接、企盟匹配打通、网关路由升级

### 已完成特性

- **信任网络→企盟匹配桥接**: `chainke_bridge.py` 实现 `sync_trust_to_chainke()` 和 `sync_matches_from_chainke()`，使用 Python 标准库 urllib，零额外依赖
- **链客宝数据同步端点**: `GET /api/brochure/sync/chainke`，手动触发信任数据推送+匹配拉取
- **网关路由升级**: `gateway.py` 新增 5 条 brochure 代理路由 (`/api/brochure/*`, `/api/auth/*`, `/api/tag/*`, `/api/match/*`, `/api/external/*` → :8003)
- **故障降级**: 链客宝不可达时自动 fallback 到本地匹配引擎
- **文档更新**: 架构全景图新增「链客宝生态融合」章节，PRODUCT.md 版本记录更新

## 相关文档

| 文档 | 说明 |
|:-----|:------|
| [_唤醒上下文.md](./_唤醒上下文.md) | 唤醒词「名片」— 产品快速上下文、API速查、启动方式 |
| [架构全景图_2026-05-31.md](./架构全景图_2026-05-31.md) | 五层架构全景 — Gateway/Kanban/delegate/Profiles/execute |
| [digital_brochure_api.py](./digital_brochure_api.py) | 单体API服务源码（1559行） |
| [backend/](./backend/) | 模块化后端（21文件 + 12服务） |
| [PRODUCT.md](./PRODUCT.md) | 产品定义（本文） |
