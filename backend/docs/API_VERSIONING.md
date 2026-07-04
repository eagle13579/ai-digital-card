# 链客宝 API 版本化方案

> 版本：2.0
> 最后更新：2026-07-04
> 状态：**已实施**
>
> 详细文档参见：`docs/api/VERSIONING.md`

---

## 当前版本状态

| 版本 | 状态 | 路由范围 |
|------|------|----------|
| **v1 (legacy 旧路径)** | **向后兼容保留中** (deprecated) | 所有 `/api/xxx` 旧前缀路由 |
| **v1 (版本化路径)** | **稳定 — 生产可用** | 所有 `/api/v1/xxx` 路由 |
| **v2** | **未发布 — 预留** | 新增路由走 `/api/v2/xxx` |

## 核心实现

所有版本化逻辑集中在 `app/core/domain_routes.py` 的 `_versionize()` 函数中：

1. 自动将 `/api/xxx` 前缀的路由复制为 `/api/v1/xxx` 版本
2. 同时保留旧 `/api/xxx` 路由（标记为 `deprecated=True`，tag 追加 `(legacy)`）
3. 已使用 `/api/v*` 前缀的路由保持不变
4. 健康检查、SEO、SSR 等路由不参与版本化

**无需修改任何现有 router 文件**。修改 `main.py` 也仅在新版本发布时才需要。

## 兼容策略

### 旧路由保留
- 所有旧的 `/api/xxx` 路由**至少保留 6 个月**
- 标记为 `deprecated=True`，但功能完全正常
- 旧路由的 Swagger 文档 tag 追加 `(legacy)` 便于识别

### 向后兼容保证
- 现有客户端无需任何修改即可继续使用 `/api/xxx` 路径
- 后端自动将 `/api/xxx` 路由也注册为 `/api/v1/xxx` 版本化路径
- 两个前缀访问同一份路由处理函数，行为完全一致

## 弃用流程

### 响应头标记
弃用路由需要在响应中包含：
```http
Sunset: Sat, 31 Dec 2027 23:59:59 GMT
Deprecation: true
```

### 弃用时间线
| 动作 | 时间 | 通知方式 |
|------|------|----------|
| 公告废弃计划 | T-6 个月 | 开发者门户 + 邮件 |
| 正式废弃（加 Deprecation header） | T-0 | 响应头标记 |
| 进入维护模式（仅修复安全漏洞） | T-3 个月 | 邮件 |
| 下线（返回 410 Gone） | T+0 | API 文档更新 + 公告 |

## 新增 v2 路由

### 方式一：在现有 domain 组中新增

```python
# app/routers/ai_v2.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/v2/ai", tags=["AI v2"])
```

在 `domain_routes.py` 的对应 `_collect` 调用中新增即可：

```python
def get_ai_routers() -> List[APIRouter]:
    return _collect([
        ...
        ("app.routers.ai_v2", "router"),  # 新增
    ])
```

### 方式二：独立注册到 main.py

```python
from app.routers import ai_v2
app.include_router(ai_v2.router)
```

## 验证新旧双前缀

```bash
# 旧路径 —— 应该返回数据
curl http://localhost:8001/api/contacts/list

# 新路径 —— 应该返回相同数据
curl http://localhost:8001/api/v1/contacts/list
```

## 附录：路由前缀一览

| 原始 prefix | 版本化 prefix | 状态 |
|-------------|---------------|------|
| `/api/auth` | `/api/v1/auth` | 废弃 ✓ |
| `/api/contacts` | `/api/v1/contacts` | 废弃 ✓ |
| `/api/products` | `/api/v1/products` | 废弃 ✓ |
| `/api/orders` | `/api/v1/orders` | 废弃 ✓ |
| `/api/needs` | `/api/v1/needs` | 废弃 ✓ |
| `/api/business-card` | `/api/v1/business-card` | 废弃 ✓ |
| `/api/matching` | `/api/v1/matching` | 废弃 ✓ |
| `/api/payment/alipay` | `/api/v1/payment/alipay` | 废弃 ✓ |
| `/api/payment/wxpay` | `/api/v1/payment/wxpay` | 废弃 ✓ |
| `/api/v1/audit` | `/api/v1/audit` (不变) | 稳定 ✓ |
| `/api/v1/chat` | `/api/v1/chat` (不变) | 稳定 ✓ |
| `/api/v1/ai` | `/api/v1/ai` (不变) | 稳定 ✓ |
| `/api/v1/analytics` | `/api/v1/analytics` (不变) | 稳定 ✓ |
| `/api/v1/billing` | `/api/v1/billing` (不变) | 稳定 ✓ |
| `/api/v1/onboarding` | `/api/v1/onboarding` (不变) | 稳定 ✓ |
| `/api/v1/workflow` | `/api/v1/workflow` (不变) | 稳定 ✓ |
| `/api/v1/geo` | `/api/v1/geo` (不变) | 稳定 ✓ |
| `/api/v1/recommendations` | `/api/v1/recommendations` (不变) | 稳定 ✓ |
| `/api/v1/events` | `/api/v1/events` (不变) | 稳定 ✓ |
| `/api/v1/monitor` | `/api/v1/monitor` (不变) | 稳定 ✓ |
