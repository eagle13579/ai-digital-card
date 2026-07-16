# 基线 v1 — AI数智名片

基线ID: B-AIC-001
日期: 2026-07-16

## 代码审计

| 维度 | 值 |
|------|-----|
| Python文件数（全项目） | 1,768 |
| Python文件数（backend/） | 443 |
| 后端代码总行数 | 127,558 |
| API端点（FastAPI routers） | 328 |
| 数据模型文件（models/） | 52 |
| Schema文件（schemas/） | 1（__init__.py） |
| AI模块文件（ai/） | 35 |
| Agent模块文件（agents/） | 27 |
| 前端文件（TS/TSX/JS） | 222 |
| 文档文件数（backend/docs/） | 41 |

## 目录结构（backend/app/ 关键目录）

```
backend/app/
├── agents/            # 27 个Agent模块（架构Agent、数据Agent、安全Agent等）
├── ai/                # 35 个AI模块（RAG、向量搜索、推荐、OCR等）
├── brokers/           # 消息代理层
├── cache/             # 缓存层（Redis适配器）
├── config/            # 配置
├── connectors/        # 外部连接器
├── crm/               # CRM模块
├── docs/              # 41 个文档
├── events/            # 事件系统
├── graphql/           # GraphQL（strawberry-graphql）
├── i18n/              # 国际化
├── identity/          # 身份认证
├── middleware/        # 中间件
├── models/            # 52 个数据模型（SQLAlchemy）
├── payment/           # 支付模块
├── repositories/      # 数据仓库
├── routers/           # 328 个API端点
├── schemas/           # Pydantic schemas
├── sdk/               # SDK
├── services/          # 业务服务层
├── static/            # 静态文件
├── templates/         # Jinja2模板
├── utils/             # 工具函数
```

## 技术栈

| 维度 | 内容 |
|------|------|
| 后端语言 | Python 3.12 |
| 后端框架 | FastAPI 0.115+（通过 uvicorn 部署） |
| ORM | SQLAlchemy 2.0+ |
| 数据库 | PostgreSQL（asyncpg） |
| 缓存 | Redis 5+ |
| 向量搜索 | sentence-transformers + scikit-learn |
| 前端框架 | Vite + React 19 + Tailwind CSS |
| GraphQL | Strawberry GraphQL 0.320+ |
| 认证 | JWT（PyJWT）、OAuth2、微信登录 |
| 支付 | 链客宝支付SDK |
| 可观测性 | OpenTelemetry |
| 国际化 | i18n/i18nice |
| CI/测试 | pytest, ruff, bandit, safety |

## API端点清单

**认证模块**（auth.py）: 4个端点
- POST `/register` — 注册
- POST `/login` — 登录
- POST `/wx-login` — 微信登录
- POST `/wx-mini-login` — 微信小程序登录

**名片管理**（brochure.py, brochure_new.py）: 15个端点
- GET /POST/PUT/DELETE `/` — 名片CRUD
- GET `/template/{purpose}` — 按用途获取模板
- GET `/share/{share_token}` — 分享链接访问
- POST `/{brochure_id}/publish` — 发布名片
- POST `/{brochure_id}/refresh-token` — 刷新分享令牌
- POST `/smart-search` — 智能搜索
- POST `/upload-cover`, `/upload-file`, `/upload-video` — 文件上传
- POST `/batch-import`, `/batch-export` — 批量导入导出

**用户管理**（user.py）: 5个端点
- GET/PUT `/me` — 当前用户详情/编辑
- GET `/` — 用户列表
- GET `/{user_id}` — 用户详情
- GET `/search/list` — 搜索用户

**匹配推荐**（match.py, matching.py, recommend.py）: 18个端点
- GET `/recommend` — 推荐
- POST `/engine` — 匹配引擎
- GET/PUT `/records` — 匹配记录
- POST `/semantic-search`, `/rerank` — 语义搜索与重排序
- POST `/{record_id}/unlock` — 解锁匹配
- POST `/personal`, `/discover`, `/similar` — 推荐系统
- POST `/rag-query` — RAG查询
- GET `/graph-summary`, `/graph` — 知识图谱
- POST `/feedback` — 推荐反馈

**AI助手**（ai_assist.py）: 4个端点
- POST `/chat` — AI对话
- POST `/write` — AI写作
- POST `/write/all` — 批量写作
- GET `/optimize/{brochure_id}` — 优化名片

**通信录**（contacts.py）: 6个端点
- POST `/import` — 导入通信录
- GET `/` — 通信录列表
- GET `/stats` — 通信录统计
- GET `/match-result` — 匹配结果
- DELETE `/{contact_id}` — 删除联系人
- DELETE `/` — 清空通信录

**消息**（messages.py）: 6个端点
- GET `/` — 消息列表
- GET `/conversations` — 会话列表
- GET `/{conversation_id}` — 会话详情
- POST `/` — 发送消息
- POST `/{conversation_id}/read` — 标记已读
- GET `/unread/count` — 未读数

**团队管理**（team.py）: 15个端点
- POST/GET/PUT/DELETE `/` — 团队CRUD
- GET `/{team_id}` — 团队详情
- GET `/{team_id}/members` — 成员列表
- PUT `/{team_id}/members/{user_id}/role`, `/title` — 角色/头衔修改
- DELETE `/{team_id}/members/{user_id}` — 移除成员
- POST `/{team_id}/invites` — 邀请成员
- GET `/{team_id}/invites` — 邀请列表
- POST `/invites/{token}/accept|decline` — 接受/拒绝邀请
- POST `/{team_id}/approval-requests` — 审批请求
- GET `/{team_id}/approval-requests` — 审批列表
- PUT `/{team_id}/approval-requests/{req_id}` — 审批操作

**支付**（payment.py）: 8个端点
- POST `/create` — 创建订单
- POST `/notify/{channel}` — 支付通知
- GET `/query/{order_no}` — 查询订单
- GET `/orders` — 订单列表
- GET `/products` — 产品列表
- GET `/enterprise/plans` — 企业套餐
- POST `/enterprise/subscribe` — 企业订阅
- GET/PUT `/enterprise/subscription`, `/cancel` — 订阅管理

**订阅**（subscription_router.py）: 13个端点
- GET `/plans`, `/current` — 套餐/当前订阅
- POST `/upgrade`, `/downgrade` — 升降级
- POST `/trial/start` — 试用
- GET `/trial/status` — 试用状态
- POST `/notify/check`, `/cancel`, `/cancel-immediate` — 取消
- POST `/ab-test/start`, GET `/ab-test/status` — A/B测试
- GET `/cancel/reasons` — 取消原因

**其他模块** — 涵盖组织管理、平台管理、标签、信任网络、访客日志、Webhook、集成、发票、SSO/OAuth、应用商店、爬虫、OCR、文档、增长指标、HA高可用、GDPR等，共计百余个端点。

完整端点列表见 `backend/app/routers/` 下各路由文件。

## 已知问题

- models/ 下有52个模型文件，但 schemas/ 仅1个 __init__.py 文件，schema定义可能分散在服务层或routers内，缺乏统一Schema管理
- backend/app/下包含 `backup_observability` 目录，疑似历史遗留
- 项目同时包含 FastAPI 和 Flask 依赖（requirements_full.txt中有Flask 3.0），可能存在混用风险，需确认
- 未发现独立测试覆盖率数据，需补充
- 部分路由文件（如brochure_new.py）与已有路由存在功能重叠，需确认是否重复注册

## 审计数据来源

- Python文件数: `find . -name '*.py' | wc -l`
- 代码行数: `find . -name '*.py' -exec cat {} \; | wc -l`
- API端点: `grep -rn '@router\.' backend/app/routers/ --include='*.py' | grep -E '(get|post|put|delete|patch|head|options)\(' | wc -l`
- 模型文件: `find backend/app/models/ -name '*.py' | wc -l`
- AI模块: `find backend/app/ai/ -name '*.py' | wc -l`
- Agent模块: `find backend/app/agents/ -name '*.py' | wc -l`
- 文档文件: `find backend/docs/ -type f | wc -l`
- 前端文件: `find frontend/ -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' | grep -v node_modules | wc -l`
