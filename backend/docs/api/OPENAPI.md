# 链客宝 OpenAPI 增强指南

> 版本：1.0  
> 最后更新：2026-06-26  
> 用途：提升自动生成 API 文档的可用性和自动化发布能力

---

## 1. FastAPI OpenAPI 配置优化

### 1.1 当前配置

在 `app/main.py` 中：

```python
app = FastAPI(
    title="链客宝 API",
    description="链客宝 — 企业家供需匹配平台后端服务",
    version="1.0.0",
)
```

### 1.2 增强配置

```python
app = FastAPI(
    title="链客宝 API",
    description="链客宝 — 企业家供需匹配平台后端服务",
    version="1.0.0",
    # ── OpenAPI 增强 ─────────────────────────────────
    openapi_tags=[                                              # ① 标签排序与描述
        {
            "name": "认证与微信解密",
            "description": "微信登录、JWT 签发、手机号解密",
            "externalDocs": {
                "description": "微信官方文档",
                "url": "https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/login.html",
            },
        },
        {
            "name": "企业数字名片",
            "description": "名片 CRUD、AI 生成名片、名片同步",
        },
        {
            "name": "联系人管理",
            "description": "客户/联系人资源管理",
        },
        {
            "name": "电子画册桥接",
            "description": "供小程序端调用的电子画册数据接口",
        },
        {
            "name": "健康检查",
            "description": "服务健康状态与 Sentry 错误上报测试",
        },
    ],
    # ── 联系方式与 License ───────────────────────────
    contact={
        "name": "链客宝技术团队",
        "url": "https://liankebao.top",
        "email": "dev@liankebao.top",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://liankebao.top/license",
    },
    # ── OpenAPI 路径定制 ─────────────────────────────
    openapi_url="/api/v1/openapi.json",                         # ② 统一路径
    docs_url="/api/v1/docs",                                    # ③ Swagger UI
    redoc_url="/api/v1/redoc",                                  # ④ ReDoc
)
```

### 1.3 效果

- `openapi_tags` → Swagger UI 顶部标签按定义顺序排列
- `contact` / `license_info` → OpenAPI 根信息中包含团队联系方式
- `openapi_url` 带版本前缀 → 避免未来多版本冲突

---

## 2. 为路由添加 x- 扩展标签

### 2.1 使用场景

`x-` 扩展属性不会被标准工具解析，但能被自定义工具（API 门户、API 治理平台）识别。

```python
from fastapi import APIRouter, Query

router = APIRouter(
    prefix="/api/v1/contacts",
    tags=["联系人管理"],
)

@router.get(
    "/",
    summary="获取联系人列表",
    description="分页查询联系人。支持按名称、标签、创建时间筛选。",
    # ── OpenAPI 扩展 ─────────────────────────────
    openapi_extra={
        "x-rate-limit": {
            "window": "1m",
            "max": 60,
        },
        "x-business-domain": "crm",
        "x-deprecated": False,
        "x-audience": "internal",
        "x-permissions": ["contacts:read"],
    },
)
async def list_contacts(...):
    ...
```

### 2.2 常用 x- 扩展表

| 扩展名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `x-rate-limit` | object | 端点级限流配置 | `{"window": "1m", "max": 60}` |
| `x-business-domain` | string | 业务域归属 | `crm`, `payment`, `auth` |
| `x-deprecated` | boolean | 是否废弃 | `false` |
| `x-audience` | string | 目标调用方 | `internal`, `partner`, `public` |
| `x-permissions` | array | 所需权限列表 | `["contacts:read", "contacts:write"]` |
| `x-since` | string | 版本引入时间 | `v1.0.0` |
| `x-version` | string | 引入版本号 | `1.0.0` |
| `x-sunset` | string | 废弃/下线日期 | `2027-12-31` |

### 2.3 装饰器封装（推荐）

为避免在每个 endpoint 中重复写 `openapi_extra`，封装一个装饰器：

```python
# app/core/openapi.py
from functools import wraps
from typing import Callable

def api_endpoint(
    summary: str = "",
    description: str = "",
    business_domain: str = "",
    rate_limit: dict | None = None,
    permissions: list[str] | None = None,
    deprecated: bool = False,
):
    """为 endpoint 注入 OpenAPI 扩展元数据"""
    def decorator(func: Callable):
        extra = {}
        if business_domain:
            extra["x-business-domain"] = business_domain
        if rate_limit:
            extra["x-rate-limit"] = rate_limit
        if permissions:
            extra["x-permissions"] = permissions
        if deprecated:
            extra["x-deprecated"] = True
        
        func._openapi_extra = extra
        return func
    return decorator

# 使用
@router.get("/")
@api_endpoint(summary="联系人列表", business_domain="crm", rate_limit={"window": "1m", "max": 60})
async def list_contacts(...):
    ...
```

---

## 3. 请求/响应模型文档增强

### 3.1 Pydantic 模型添加示例与描述

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ContactCreate(BaseModel):
    """创建联系人请求"""
    name: str = Field(
        ...,
        description="联系人姓名",
        min_length=1,
        max_length=100,
        examples=["张三"],
    )
    phone: Optional[str] = Field(
        None,
        description="手机号",
        pattern=r"^1[3-9]\d{9}$",
        examples=["13800138000"],
    )
    tags: list[str] = Field(
        default=[],
        description="标签列表",
        examples=[["VIP", "上海"]],
    )

class ContactResponse(BaseModel):
    """联系人响应"""
    id: str = Field(..., description="联系人唯一 ID", examples=["c-abc123"])
    name: str = Field(..., description="联系人姓名", examples=["张三"])
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "c-abc123",
                "name": "张三",
                "phone": "13800138000",
                "tags": ["VIP", "上海"],
                "created_at": "2026-06-26T10:30:00Z",
            }
        }
```

### 3.2 效果

- 字段上的 `examples` 数组 → Swagger UI 自动填入示例值
- 模型级 `json_schema_extra["example"]` → "Example" 标签页展示完整示例
- `description` 支持 markdown 格式（部分 UI 渲染）

---

## 4. API 文档自动发布

### 4.1 方案选择

| 方案 | 适用场景 | 难度 |
|------|----------|------|
| Swagger UI + ReDoc（内嵌） | 开发/测试环境 | 低 |
| GitHub Pages / GitLab Pages | 公开 API 文档 | 中 |
| Stoplight / SwaggerHub | 团队协作 + 设计优先 | 中 |
| 自建 API Portal（VitePress + openapi-ts） | 企业级文档门户 | 高 |

### 4.2 推荐：Stoplight 方案（团队协作）

1. 安装 Stoplight CLI 或使用 Stoplight Studio
2. 将生成的 `openapi.json` 同步到 Stoplight 工作区
3. 团队成员可在线评论、mock 调试

```bash
# 在 CI 流水线中执行
npx @stoplight/cli push openapi.json \
  --workspace chainke-api \
  --token $STOPLIGHT_TOKEN
```

### 4.3 推荐：VitePress 自建门户（企业级）

项目结构：

```
docs/api-portal/
├── .vitepress/
│   └── config.js
├── index.md
├── guide/
│   ├── getting-started.md
│   └── authentication.md
└── reference/
    └── openapi.md       # 自动生成，引用 openapi.json
```

使用 `openapi-ts` 生成 TypeScript 类型定义和 API 客户端：

```bash
npm install -g @hey-api/openapi-ts
openapi-ts \
  --input http://localhost:8001/api/v1/openapi.json \
  --output ./frontend/src/api/generated
```

### 4.4 CI/CD 集成（GitHub Actions 示例）

```yaml
# .github/workflows/api-docs.yml
name: Publish API Docs
on:
  push:
    branches: [main]
    paths: ["backend/app/**/*.py"]

jobs:
  generate-and-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Start backend & dump OpenAPI
        run: |
          cd backend
          pip install -r requirements.txt
          uvicorn app.main:app --host 0.0.0.0 --port 8001 &
          sleep 5
          curl -o openapi.json http://localhost:8001/api/v1/openapi.json
      
      - name: Upload to Stoplight
        run: |
          npx @stoplight/cli push openapi.json \
            --workspace chainke-api \
            --token ${{ secrets.STOPLIGHT_TOKEN }}
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          publish_dir: ./docs/api-portal/.vitepress/dist
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

---

## 5. 多版本 OpenAPI 共存

当存在 v1、v2 多个 API 版本时，生成各自独立的 OpenAPI 规范：

```python
# 方案 A：在同一个 FastAPI 实例上通过子应用挂载
from fastapi import FastAPI

v1 = FastAPI(title="链客宝 API v1", version="1.0.0", openapi_prefix="/api/v1")
v2 = FastAPI(title="链客宝 API v2", version="2.0.0", openapi_prefix="/api/v2")

# 分别注册路由到 v1 和 v2
# ...

app.mount("/api/v1", v1)
app.mount("/api/v2", v2)
```

访问路径：
- `http://localhost:8001/api/v1/docs` → v1 Swagger UI
- `http://localhost:8001/api/v1/openapi.json` → v1 OpenAPI
- `http://localhost:8001/api/v2/docs` → v2 Swagger UI

---

## 6. 检查清单

部署前确认：

1. [ ] `openapi_tags` 定义完整，覆盖所有 router 的 `tags`
2. [ ] 关键 Pydantic 模型有 `examples` 和 `description`
3. [ ] 高频使用 endpoint（如登录、创建资源）有完整 `json_schema_extra["example"]`
4. [ ] 核心端点添加 `openapi_extra` 的 `x-` 扩展标签
5. [ ] `openapi_url` 使用版本化路径
6. [ ] CI 中配置 OpenAPI 导出步骤
7. [ ] 文档门户（Stoplight / VitePress）已配置自动同步
