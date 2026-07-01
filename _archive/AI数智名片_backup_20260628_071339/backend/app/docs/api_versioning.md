# API 版本化方案

## 当前状态
- 路由定义在 `routers/*.py`，使用 `APIRouter(prefix="/api/xxx")`
- 生产已使用 `/api/xxx` 路径，无版本前缀
- `__init__.py` 中的 `APIVersionRedirectMiddleware` 方向相反（剥离而非添加前缀），需废弃

## 迁移方案

### Phase 1: 兼容层（立即）

**1.1 替换 middleware**
```python
@app.middleware("http")
async def add_v1_prefix(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/") and not path.startswith("/api/v1/"):
        new_path = path.replace("/api/", "/api/v1/", 1)
        request.scope["path"] = new_path
        request.scope["raw_path"] = new_path.encode()
    return await call_next(request)
```

**1.2 双注册路由**
```python
app.include_router(auth_router)                  # /api/auth（旧）
app.include_router(auth_router, prefix="/api/v1")  # /api/v1/auth（新）
```
每个 router 注册两次，OpenAPI 同时暴露两套路径。

**1.3 执行步骤**
1. 注释旧 `APIVersionRedirectMiddleware`
2. 添加 `add_v1_prefix` middleware
3. 每个 `app.include_router()` 增加第二行注册
4. 验证：新旧路径均正常
5. 前端更新 API 基地址为 `/api/v1/`

### Phase 2: 新版本（未来）

**2.1 v2 路由**
```
routers/
├── auth.py              # v1（prefix="/api/auth"）
├── v2/
│   ├── __init__.py      # 导出 v2_router
│   └── auth.py          # v2（prefix="/api/v2/auth"）
```
`create_app()` 中注册：`app.include_router(v2_router)`

**2.2 废弃旧路径**
所有客户端迁移到 `/api/v1/` 后：
1. 移除 `add_v1_prefix` middleware
2. 移除无前缀的 `app.include_router(xxx_router)` 注册
3. 只保留 `app.include_router(xxx_router, prefix="/api/v1")`

## 影响
- **前端**: 无影响，旧请求 `/api/xxx` 被 middleware 重写为 `/api/v1/xxx`
- **OpenAPI**: 同时暴露 `/api/v1/` 和 `/api/` 两套路径
- **性能**: middleware 字符串替换，μs 级开销
- **第三方**: webhook / OAuth callback URL 需逐步更新
- **测试**: 需覆盖新旧两条路径
