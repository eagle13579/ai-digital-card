# ADR-004: 47 个 Router 的模块化路由注册策略

**状态**: Accepted
**日期**: 2026-06-26
**决策者**: 后端组

## 上下文

链客宝后端有 47 个业务路由模块（Router），涵盖用户、企业、匹配、消息、支付、管理后台等。路由注册面临选择：

- **方案 A**：使用 FastAPI `APIRouter`，每个模块独立文件，在 `main.py` 中 `include_router`
- **方案 B**：使用 Blueprint 风格框架（如 Flask Blueprints 或自定义路由注册器）
- **方案 C**：自动扫描 + 装饰器方式注册

## 决策

采用 **方案 A：FastAPI APIRouter + main.py 显式 import 注册**。

具体做法：

1. 每个模块一个文件，位于 `app/routers/` 目录下
2. 每个文件定义 `router = APIRouter(prefix="/api/v1/xxx", tags=["xxx"])`
3. **`main.py` 中显式 import 所有 47 个 router 并 `app.include_router()`**
4. 按领域分组文件夹（如 `routers/user/`、`routers/enterprise/`、`routers/match/`）
5. 文件夹内 `__init__.py` 导出该领域所有 router

代码结构：

```
app/routers/
├── __init__.py              # 聚合导出函数
├── user/
│   ├── __init__.py          # from .profile import router as user_profile
│   ├── profile.py
│   └── auth.py
├── enterprise/
│   ├── __init__.py
│   ├── profile.py
│   └── search.py
├── match/
│   ├── __init__.py
│   ├── matching.py
│   └── recommendation.py
└── ... (47 个 router 分布在约 12 个领域目录)
```

`main.py` 注册方式：

```python
from app.routers import get_all_routers

app = FastAPI()
for router in get_all_routers():
    app.include_router(router)
```

## 理由

1. **FastAPI 第一方方案** — `APIRouter` 是 FastAPI 原生支持的方案，支持 `prefix`、`tags`、`dependencies`、`responses`，与 OpenAPI 文档生成完美集成
2. **显式优于隐式** — 自动扫描/装饰器方案虽然"酷"，但调试时难以追踪路由来源。`main.py` 中的 `include_router` 调用提供了明确的注册顺序和可读性
3. **IDE 可追溯** — 显式 import 让 IDE 可以跳转到 router 定义处，自动扫描方案做不到
4. **懒加载友好** — `get_all_routers()` 可以按需返回部分 router（开发环境只加载部分路由加速热重载）
5. **测试便利** — 每个 router 可以单独 `TestClient` 测试，无需启动整个应用

## 后果

**正面**:
- 路由注册流程透明，新人可以快速了解系统有哪些 API
- OpenAPI 文档自动按 `tags` 分组，前端可读性高
- IDE 支持跳转和重构，维护成本低

**负面**:
- 47 个 router 全部 import 导致应用启动时加载所有模块（约 0.5-1s），但可接受
- 新增 router 需要修改两个文件（router 本身 + `__init__.py`），略繁琐
- 如果未来路由数超过 200 个，`main.py` 变得冗长，届时可考虑自动注册

## 替代方案

| 方案 | 否决理由 |
|------|---------|
| 自动扫描/装饰器 | 隐式注册难以调试，IDE 不能跳转，启动顺序不可控 |
| Flask Blueprints | 团队使用 FastAPI，引入 Flask 模式属于过度设计 |
| 单一超大 router 文件 | 47 个路由写在一个文件约 5000+ 行，不可维护 |
| 微服务拆分 | 当前规模不需要微服务，单体+模块化更高效 |
