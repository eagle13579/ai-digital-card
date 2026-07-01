# AI数字名片 API SDK 生成策略

> 本文档定义了 AI数字名片 REST API（150+ 端点，OpenAPI 3.1 规范）的 SDK 生成策略、工具选型、发布流程与 CI 集成方案。

---

## 1. 目标语言

| 语言       | 运行时 / 平台     | 用途           | 输出目录                          |
| ---------- | ----------------- | -------------- | --------------------------------- |
| Python     | Python 3.12+      | 后端 SDK       | `backend/app/sdk/`                |
| TypeScript | Node 20+ / Browser | 前端 SDK       | `frontend/src/lib/api-sdk/`       |

> **后续可扩展**：Java (Android)、Swift (iOS)、Go (微服务)、Dart (Flutter miniapp)。

---

## 2. 生成工具选型

### 2.1 主选：openapi-generator (OpenAPI Generator CLI)

| 特性           | 说明                                                           |
| -------------- | -------------------------------------------------------------- |
| 成熟度         | 社区活跃，支持 50+ 语言生成器                                   |
| 规范支持       | OpenAPI 3.0 / 3.1 全支持                                       |
| Python 生成器  | `python` (httpx/urllib3 客户端)                                 |
| TypeScript 生成器 | `typescript-fetch` 或 `typescript-axios`                       |
| 自定义模板     | 支持 Mustache 模板覆盖，可定制生成代码风格                       |
| 缺点           | 生成的代码偏"样板化"，体积较大                                    |

### 2.2 备选：Fern

| 特性           | 说明                                                           |
| -------------- | -------------------------------------------------------------- |
| 定位           | 面向 API-first 团队的现代代码生成器                               |
| 特点           | 类型更安全、生成代码更精简、支持自定义中间件                       |
| 适用场景       | 如果后续 SDK 需要支持多语言（Python/TS/Go/Java）且追求开发者体验   |
| 采用条件       | 通过 PoC 验证后切换，详见下文 §6                                  |

**当前选择**：openapi-generator（成熟、稳定、社区支持好）。

---

## 3. 生成流程

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  openapi.yaml    │ ──► │  generate_sdk.py  │ ──► │  Python SDK          │
│  (OpenAPI 3.1)   │     │  (SDK生成脚本)     │     │  backend/app/sdk/    │
└─────────────────┘     │                   │     ├──────────────────────┤
                         │  · 下载/校验规范   │     │  TypeScript SDK       │
                         │  · 调用生成器      │     │  frontend/src/lib/   │
                         │  · 后处理/格式化   │     │  api-sdk/             │
                         │  · 输出到目标目录   │     └──────────────────────┘
                         └──────────────────┘
```

### 3.1 输入
- `openapi.yaml` — 项目根目录的 OpenAPI 3.1 规范文件（自动生成，3674 行，84KB）
- **权威来源**：`http://localhost:8201/openapi.json`（开发环境实时端点）
- 回退来源：项目根目录 `openapi.yaml`

### 3.2 生成步骤

1. **获取规范**：优先从后端服务实时获取，回退到本地文件
2. **校验规范**：检查 OpenAPI 版本兼容性、必填字段完整性
3. **生成 Python SDK**：`openapi-generator-cli generate -g python -i <spec> -o backend/app/sdk/`
4. **生成 TypeScript SDK**：`openapi-generator-cli generate -g typescript-fetch -i <spec> -o frontend/src/lib/api-sdk/`
5. **后处理**：格式化 Python 代码（black），格式化 TypeScript 代码（prettier）
6. **清理**：移除生成器自带的测试/样例文件（保持目录干净）

### 3.3 生成产物版本控制

- `backend/app/sdk/` 和 `frontend/src/lib/api-sdk/` 生成的 SDK 代码 **提交到 Git 仓库**
- 原因：开发者在没有生成器环境时也能使用 SDK，且 CI 可做版本一致性检查
- `.gitignore` 中 **不忽略** 这两个目录

---

## 4. 发布策略

### 4.1 Python 包（GitHub Packages）

```yaml
# .github/workflows/sdk-publish-python.yml
name: Publish Python SDK
on:
  push:
    paths:
      - 'openapi.yaml'
    branches: [main]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Generate SDK
        run: python scripts/generate_sdk.py
      - name: Build & Publish
        run: |
          cd backend/app/sdk
          pip install build twine
          python -m build
          twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```

- 包名：`ai-digital-business-card-sdk`
- 发布平台：PyPI（公开）或 GitHub Packages（私有）

### 4.2 TypeScript 包（npm）

```yaml
# .github/workflows/sdk-publish-npm.yml
name: Publish npm SDK
on:
  push:
    paths:
      - 'openapi.yaml'
    branches: [main]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://registry.npmjs.org'
      - name: Generate SDK
        run: python scripts/generate_sdk.py
      - name: Build & Publish
        run: |
          cd frontend/src/lib/api-sdk
          npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

- 包名：`@ai-digital-business-card/sdk`
- 发布平台：npm registry（公开）或 GitHub Packages（私有）

---

## 5. CI 集成

### 5.1 触发条件

| 触发方式           | 说明                                     |
| ------------------ | ---------------------------------------- |
| Push 到 main 分支  | openapi.yaml 有变更时自动触发             |
| 定时触发（每日）   | 确保 SDK 与后端 API 实时保持一致          |
| 手动触发（workflow_dispatch） | 异常修复或紧急发布时使用       |

### 5.2 自动生成工作流

```yaml
# .github/workflows/sdk-autogen.yml
name: Auto-Generate SDK
on:
  push:
    paths:
      - 'openapi.yaml'
    branches: [main]
  schedule:
    - cron: '0 6 * * *'  # 每天 06:00 UTC
  workflow_dispatch:

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Setup Java (for openapi-generator)
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'
      - name: Install openapi-generator
        run: |
          wget https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.12.0/openapi-generator-cli-7.12.0.jar
          echo "alias openapi-generator-cli='java -jar $(pwd)/openapi-generator-cli-7.12.0.jar'" >> ~/.bashrc
      - name: Generate SDK
        run: python scripts/generate_sdk.py
      - name: Check for Changes
        id: git-check
        run: |
          git add -A
          git diff --cached --quiet || echo "changed=true" >> $GITHUB_OUTPUT
      - name: Commit SDK Changes
        if: steps.git-check.outputs.changed == 'true'
        run: |
          git config user.name "SDK Bot"
          git config user.email "sdk-bot@ai-digital-business-card.com"
          git commit -m "chore(sdk): auto-generate SDK from openapi.yaml [skip ci]"
          git push
```

### 5.3 一致性检查

- **PR 检查**：在 PR 中如果 openapi.yaml 有变更，自动运行 SDK 生成并对比生成产物是否一致
- **失败策略**：不一致时 PR 标记为失败，要求提交者重新生成 SDK

---

## 6. 工具选型评估

### 6.1 openapi-generator vs Fern

| 维度           | openapi-generator              | Fern                              |
| -------------- | ------------------------------ | --------------------------------- |
| 学习曲线       | 低（CLI 成熟，文档齐全）         | 中（需学习 Fern DSL）              |
| 生成代码质量   | 通用、样板化                     | 精简、类型更安全                    |
| 自定义能力     | Mustache 模板覆盖               | 自定义中间件 + 代码片段             |
| 多语言支持     | 50+ 语言                        | Python / TS / Go / Java           |
| CI 集成        | JAR + Docker 两种模式            | Fern CLI + Cloud 模式              |
| 社区           | 大（20k+ stars）                | 小但快速增长                        |
| 许可证         | Apache 2.0                     | MIT                               |

### 6.2 切换策略

1. **Phase 1**（当前）：使用 openapi-generator
2. **Phase 2**（Q3 评估）：运行 Fern PoC，对比生成代码质量和开发效率
3. **Phase 3**（如果通过）：迁移到 Fern，保留 openapi-generator 作为回退方案

---

## 7. 目录结构约定

```
D:/AI数智名片/
├── openapi.yaml                    # OpenAPI 3.1 规范（权威源）
├── docs/api/
│   └── SDK_GENERATION.md           # 本文档
├── scripts/
│   └── generate_sdk.py             # SDK 生成脚本
├── backend/app/sdk/                # 生成的 Python SDK（提交到 Git）
│   ├── openapi_client/             # openapi-generator 产出
│   ├── pyproject.toml              # 独立包配置
│   └── README.md
├── frontend/src/lib/api-sdk/       # 生成的 TypeScript SDK（提交到 Git）
│   ├── src/
│   ├── package.json
│   └── tsconfig.json
└── frontend/src/lib/
    └── api-client.ts               # 基础 API 客户端（SDK 前身，手写）
```

---

## 8. 生成脚本使用方式

```bash
# 安装依赖（首次）
pip install pyyaml requests

# 生成 SDK（需要 Java 环境以运行 openapi-generator）
python scripts/generate_sdk.py

# 仅校验 OpenAPI 规范
python scripts/generate_sdk.py --validate-only

# 仅生成 Python SDK
python scripts/generate_sdk.py --lang python

# 仅生成 TypeScript SDK
python scripts/generate_sdk.py --lang typescript

# 使用本地文件（不请求后端）
python scripts/generate_sdk.py --local
```

---

## 9. Python SDK 使用文档

### 9.1 安装

```bash
# 项目内直接使用
cd backend
pip install -e .

# 或仅安装 SDK 依赖
pip install httpx>=0.27.0 pydantic>=2.0.0
```

SDK 文件位于 `backend/app/sdk/`，通过 Python 导入使用：

```python
from app.sdk import ApiClient, User, Brochure, CrmContact
```

### 9.2 初始化

```python
import os
from app.sdk import ApiClient

# 方式一：环境变量自动配置（推荐）
client = ApiClient()
# 需要设置:
#   export AICARD_BASE_URL=http://localhost:8201
#   export AICARD_API_KEY=your-jwt-token

# 方式二：显式指定
client = ApiClient(
    base_url="http://localhost:8201",
    api_key="your-jwt-token",
)

# 方式三：先初始化，后登录获取 token
client = ApiClient(base_url="http://localhost:8201")
token = client.auth().login(phone="13800138000", password="mypassword")
client.set_token(token.access_token)
```

### 9.3 认证 API

```python
# 注册
token = client.auth().register(
    phone="13800138000",
    password="StrongP@ss1",
    name="张三",
    company="某某科技",
    title="技术总监",
)
print(token.access_token)  # JWT token
print(token.user.name)     # "张三"

# 登录
token = client.auth().login(phone="13800138000", password="StrongP@ss1")
client.set_token(token.access_token)

# 微信登录（Mock）
token = client.auth().wx_login(code="mock_code_1234")
```

### 9.4 用户 API

```python
from app.sdk import UserUpdate

# 获取当前用户
me = client.users().me()
print(f"用户: {me.name}, 等级: {me.membership_tier}")

# 更新个人信息
updated = client.users().update(UserUpdate(name="李四", company="新公司"))
print(updated.name)  # "李四"

# 获取指定用户
user = client.users().get(user_id=42)
```

### 9.5 名片 API

```python
from app.sdk import BrochureCreate, BrochureUpdate, Page

# 列出名片（分页）
brochures = client.brochures().list(page=1, page_size=10)
print(f"共 {brochures.total} 张名片")
for b in brochures.items:
    print(f"  [{b.id}] {b.title} ({b.status})")

# 创建名片
new_brochure = client.brochures().create(BrochureCreate(
    title="我的产品介绍",
    purpose="client",
    pages=[
        Page(sort_order=0, content_type="cover", content="欢迎页"),
        Page(sort_order=1, content_type="text", content="服务详情..."),
    ],
))
print(f"创建成功，ID: {new_brochure.id}")

# 获取名片详情
brochure = client.brochures().get(brochure_id=1)
for page in brochure.pages:
    print(f"  第 {page.sort_order} 页: {page.content_type}")

# 更新名片
client.brochures().update(1, BrochureUpdate(title="新标题"))

# 发布/下架
client.brochures().publish(1)
client.brochures().unpublish(1)

# 删除
client.brochures().delete(1)
```

### 9.6 CRM API

```python
from app.sdk import CrmContactCreate, CrmContactUpdate, CrmDealCreate, CrmNoteCreate

# ── 联系人 ──────────────────────────────────────────────

# 创建联系人
contact = client.contacts().create(CrmContactCreate(
    name="王五",
    phone="13900139000",
    email="wangwu@example.com",
    company="合作公司",
    title="市场经理",
    source="manual",
))
print(f"联系人 ID: {contact.id}")

# 联系人列表
contacts = client.contacts().list(search="王五", page=1, page_size=20)
for c in contacts.items:
    print(f"  {c.name} - {c.company} ({c.source})")

# 联系人详情
contact = client.contacts().get(contact_id=1)

# 更新联系人
client.contacts().update(1, CrmContactUpdate(
    company="新公司名",
    deal_value=50000.0,
))

# 删除联系人
client.contacts().delete(1)

# ── 销售管道 ────────────────────────────────────────────

# 管道阶段
stages = client.crm().stages()
for s in stages:
    print(f"  [{s.id}] {s.name} (概率: {s.win_probability}%)")

# 创建机会
deal = client.crm().create_deal(CrmDealCreate(
    contact_id=1,
    pipeline_stage_id=2,
    title="大客户合作",
    value=100000.0,
    probability=60.0,
))

# 拖拽变更阶段
client.crm().move_deal(deal_id=1, pipeline_stage_id=3)

# ── 活动时间线 ──────────────────────────────────────────

activities = client.contacts().timeline(contact_id=1)
for a in activities:
    print(f"  [{a.activity_type}] {a.title} ({a.activity_date})")

# 手动添加活动
activity = client.crm().create_activity(
    contact_id=1,
    activity_type="meeting",
    title="商务面谈",
    description="讨论了合作方案",
)

# ── 笔记 ────────────────────────────────────────────────

note = client.crm().create_note(CrmNoteCreate(
    contact_id=1,
    content="客户对产品很感兴趣，下次跟进报价",
))

notes = client.contacts().notes(contact_id=1)
for n in notes:
    print(f"  {n.content[:50]}...")

# ── 统计 ────────────────────────────────────────────────

stats = client.crm().stats()
print(f"总联系人: {stats.get('total_contacts')}")
```

### 9.7 其他 API

```python
# 标签
client.tags().list(tag_type="provide")
client.tags().batch_set(
    tags=[{"tag": "AI技术", "weight": 1.0}],
    tag_type="provide",
)

# 匹配
matches = client.matches().list(status="pending")

# 访客
visitors = client.visitors().list(brochure_id=1)

# 订阅
plans = client.subscriptions().get_plans()
current = client.subscriptions().get_current()
client.subscriptions().start_trial()

# 消息
convs = client.messages().conversations()
unread = client.messages().unread_count()
client.messages().send(receiver_id=2, content="你好！")
```

### 9.8 错误处理

```python
from app.sdk import ApiClient, ApiError, NetworkError, TimeoutError

client = ApiClient()

try:
    user = client.users().me()
except ApiError as e:
    print(f"API 错误: [{e.status}] code={e.code} {e}")
except TimeoutError as e:
    print(f"请求超时: {e}")
except NetworkError as e:
    print(f"网络错误: {e}")
```

### 9.9 自定义配置

```python
from app.sdk import ApiClient
from app.sdk.client import ClientConfig

config = ClientConfig(
    base_url="http://localhost:8201",
    api_key="",
    timeout=30.0,          # 30秒超时
    max_retries=3,         # 最多重试3次
    retry_base_delay=0.5,  # 初始退避0.5秒
    retry_max_delay=10.0,  # 最大退避10秒
)
client = ApiClient(config=config)
```

### 9.10 资源清理

```python
# 使用上下文管理器（推荐）
with ApiClient() as client:
    user = client.users().me()
    # 退出时自动关闭连接

# 或手动关闭
client = ApiClient()
try:
    user = client.users().me()
finally:
    client.close()
```

---

## 10. 注意事项

1. **Java 依赖**：openapi-generator 需要 Java 17+ 运行环境
2. **规范质量**：确保 OpenAPI 规范中的 `operationId` 唯一且有语义（影响生成的方法名）
3. **向后兼容**：对 SDK 做版本管理，API 变更时遵循语义化版本
4. **手动覆盖**：如果生成的 SDK 不满足某些场景（如流式上传），在手写 wrapper 中封装
5. **安全**：SDK 中不包含任何 API 密钥/令牌；认证通过调用方注入
6. **OpenAPI 3.1**：openapi-generator 7.x 版本才完整支持 3.1，确保使用 v7+
7. **Python SDK 版本**：当前手写 SDK (`app/sdk/`) 是 openapi-generator 自动生成的补充方案，两者共存；需要完整 150+ 端点覆盖时使用自动生成版本
