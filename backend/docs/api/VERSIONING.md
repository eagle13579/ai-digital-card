# 链客宝 API 版本化方案

> 版本：2.0
> 最后更新：2026-07-04
> 状态：**已实施**

---

## 1. 版本化策略选择

### 决策：URL 路径前缀版

```
https://api.liankebao.top/api/v1/users
https://api.liankebao.top/api/v2/users
```

**理由**：
- 直观、易于缓存和反向代理配置
- 客户端无需解析响应头或 Accept header
- 与当前已有 `/api/v1/audit`、`/api/v1/chat` 的**渐进式路径一致**
- 便于 nginx 等网关做流量分发

### 不采纳的方案

| 方案 | 理由 |
|------|------|
| Header 版（`Accept: application/vnd.chainke.v1+json`） | 调试不便，CDN 缓存困难 |
| 子域名版（`v1.api.liankebao.top`） | 证书与 DNS 配置复杂 |
| 参数版（`?version=1`） | 极易被忽略，URL 语义不清晰 |

---

## 2. API 生命周期模型

```
v1 (稳定) ──→ v1.1 (新增字段，向后兼容) ──→ v2 (发布) ──→ v1 (废弃) ──→ v1 (EOL/下线)
                        ↑                           ↑                            ↑
                   次版本发布                   主版本发布                  v1 下线日
```

| 阶段 | 行为 | 持续时间 |
|------|------|----------|
| **开发中 (alpha)** | 仅内部可用，可任意 break | 不定 |
| **预览 (beta/preview)** | 开放给合作方，文档标记 `(beta)` | ≤ 3 个月 |
| **稳定 (stable)** | 生产可用，遵循兼容规则 | 无限 |
| **废弃 (deprecated)** | 仍运行但不再更新，响应加 `Sunset` 头 | ≥ 6 个月 |
| **下线 (EOL)** | 返回 410 Gone | - |

---

## 3. 向后兼容规则

以下变更**允许**在次版本内进行：

- ✅ 新增可选请求参数/请求体字段
- ✅ 新增响应字段（客户端必须忽略未知字段）
- ✅ 修复 bug（行为变化在合理范围内）
- ✅ 新增枚举值
- ✅ 扩展 rate limit 配额

以下变更**必须**发布主版本（v1 → v2）：

- ❌ 删除或重命名资源路径
- ❌ 删除或重命名请求参数字段
- ❌ 删除或重命名响应字段
- ❌ 将可选字段改为必填
- ❌ 改变响应类型（如 array → object）
- ❌ 改变业务行为语义
- ❌ 降低安全性或隐私保护级别

---

## 4. 废弃（Deprecation）流程

### 4.1 响应头标记

当路由进入废弃阶段，需在响应中包含：

```http
Sunset: Sat, 31 Dec 2027 23:59:59 GMT
Deprecation: true
```

### 4.2 服务端日志警告

在废弃版本调用时输出 WARNING 级别日志：

```python
logger.warning(
    "[Deprecated] client=%s ip=%s version=v1 endpoint=%s",
    client_id, client_ip, request.url.path
)
```

### 4.3 废弃时间线

| 动作 | 时间 | 通知方式 |
|------|------|----------|
| 公告废弃计划 | T-6 个月 | 开发者门户 + 邮件 |
| 正式废弃（Deprecation header） | T-0 | 响应头标记 |
| 进入维护模式（仅修复安全漏洞） | T-3 个月 | 邮件 |
| 下线（返回 410 Gone） | T+0 | API 文档更新 + 公告 |

---

## 5. 当前路由结构分析

### 5.1 前缀模式分布

截至 2026-07-04，后端路由存在**三种前缀模式**：

| 模式 | 示例 | 数量 |
|------|------|------|
| 无 `/api` 前缀 | `/health`， `/sitemap.xml` | 少数（健康检查/SEO） |
| `/api/...`（无版本） | `/api/auth/login`， `/api/contacts` | **多数（约 40 个 router）** |
| `/api/v1/...`（已版本化） | `/api/v1/audit`， `/api/v1/chat` | 约 10 个 router |

### 5.2 路由注册架构

所有领域路由通过 `app/core/domain_routes.py` 聚合注册：

```
main.py
  ├── register_all(app)          ← 通过 domain_routes.py 注册 40+ router
  │     ├── get_auth_routers()       → auth, alipay, wxpay, recharge, membership
  │     ├── get_business_routers()   → business_card, products, orders, needs...
  │     ├── get_matching_routers()   → matching_engine, trust_score, lbs_match...
  │     ├── get_growth_routers()     → onboarding, learning_center, retro_board...
  │     ├── get_ai_routers()         → chat, feedback, ai_recommend...
  │     ├── get_compliance_routers() → compliance, audit, gdpr...
  │     ├── get_system_routers()     → storage, subscription, workflow...
  │     ├── get_i18n_routers()       → i18n_bp, i18n_router, i18n_routes
  │     ├── get_integration_routers()→ wechat, wxpay, alipay, payment_callback
  │     ├── get_seo_routers()        → seo, ssr_router, geo
  │     └── get_mobile_routers()     → mobile_api batch/mobile routers
  ├── simple_auth_router           ← 简单认证（独立 SQLite）
  ├── simple_plan_router           ← 套餐路由（独立 SQLite）
  └── audit.router                 ← 审计日志（单独注册，已 v1）

路由版本化逻辑: _versionize() 自动将 /api/* → /api/v1/*，同时保留旧路径。
```

---

## 6. 版本化实现方案（已实施）

### 6.1 核心机制：`_versionize()`

实现在 `app/core/domain_routes.py` 中，对每个 router 自动执行：

1. **跳过规则**：若 prefix 已为 `/api/v*` 或属于跳过前缀（health、metrics、docs、SEO、SSR），不处理
2. **自动版本化**：若 prefix 以 `/api/` 开头，自动创建新 router 并替换为 `/api/v1/`
3. **向后兼容**：同时创建 legacy router，保留原 prefix，标记为 `deprecated=True`，tag 追加 `(legacy)` 标记

```python
# 示例：原 router prefix="/api/contacts"
# 自动生成：
#   new_router     prefix="/api/v1/contacts"   tags=["联系人管理"]
#   legacy_router  prefix="/api/contacts"      tags=["联系人管理 (legacy)"],  deprecated=True
```

### 6.2 无需修改现有代码

- **不修改任何现有 router 文件** — 无需添加 `router_v1`
- **不修改 `main.py`** 中的注册逻辑
- 版本化逻辑在 `domain_routes.py` 中透明完成

### 6.3 当前版本状态

| 版本 | 状态 | 路由范围 |
|------|------|----------|
| **v1 (legacy 旧路径)** | **已废弃** — 向后兼容保留中 | 所有 `/api/xxx` 旧前缀路由（deprecated: true） |
| **v1 (新路径)** | **稳定** — 生产可用 | 所有 `/api/v1/xxx` 版本化路由 |
| **v2** | **未发布** — 预留 | 新增路由走 `/api/v2/xxx` |

> **重要**：当前版本化逻辑将旧 `/api/xxx` 路径标记为 `deprecated=True`，但**功能完全正常**。客户端应逐步迁移到 `/api/v1/xxx` 路径。

---

## 7. 新增 v2 路由指南

### 7.1 新增 v2 router 文件

在 `app/routers/` 下新建文件，prefix 直接使用 `/api/v2/`：

```python
# app/routers/ai_v2.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v2/ai", tags=["AI v2"])

@router.post("/chat")
async def chat_v2():
    return {"version": "v2", "message": "new chat endpoint"}
```

### 7.2 在 domain_routes.py 中注册

在对应的 domain 组中加入 `_collect` 列表：

```python
def get_ai_routers() -> List[APIRouter]:
    return _collect([
        ("app.routers.chat", "router"),
        ("app.routers.feedback", "router"),
        ("app.routers.ai_recommend", "router"),
        ("app.routers.recommendations", "router"),
        ("features.collaborative_filter.cf_router", "router"),
        ("app.routers.ai_v2", "router"),          # ← 新增 v2 router
    ])
```

> `_versionize` 函数会检测 prefix 以 `/api/v` 开头并跳过处理，因此 v2 路由保持原样。

### 7.3 或创建一个新 domain 组

对于大量 v2 路由，建议创建独立的 domain 组：

```python
def get_v2_routers() -> List[APIRouter]:
    return _collect([
        ("app.routers.ai_v2", "router"),
        ("app.routers.matching_v2", "router"),
        # ...
    ], versionize=False)  # 关闭自动版本化
```

然后在 `get_all_domains()` 和 `register_all()` 中注册。

### 7.4 直接注册到 main.py

对于独立的 v2 路由，可直接在 `main.py` 中注册：

```python
# main.py —— 新增 v2 路由示例
from app.routers import ai_v2
app.include_router(ai_v2.router)   # prefix 已在 router 中定义为 /api/v2/ai
```

---

## 8. 兼容策略

### 8.1 旧路由保留策略

| 策略 | 说明 |
|------|------|
| **保留期限** | 旧路由（`/api/xxx`）至少保留 **6 个月** |
| **废弃标记** | 旧路由自动标记为 `deprecated=True`，tag 追加 `(legacy)` |
| **完整功能** | 旧路由功能完全正常，仅标记废弃 |
| **移除流程** | 6 个月后评审使用率，低于阈值则移除 |

### 8.2 客户端迁移建议

1. 所有新客户端直接使用 `/api/v1/xxx` 路径
2. 旧客户端逐步将请求路径从 `/api/xxx` 迁移到 `/api/v1/xxx`
3. 监控旧路径调用量，确保迁移完成后再下线

### 8.3 双前缀测试验证

验证新旧两种前缀均可访问：

```bash
# 旧路径 —— 应该返回数据（可能 marked as deprecated）
curl http://localhost:8001/api/contacts/list

# 新路径 —— 应该返回相同数据
curl http://localhost:8001/api/v1/contacts/list
```

---

## 9. 无版本请求的默认行为

### 9.1 确定性规则

```
请求 /api/xxx     →  等效于 /api/v1/xxx（通过 legacy 路由）
请求 /api/v1/xxx  →  精确匹配 v1 路由
请求 /api/v2/xxx  →  精确匹配 v2 路由（如果存在）
```

### 9.2 客户端版本协商

| 方式 | 优先级 | 示例 |
|------|--------|------|
| URL 路径直接指定 | 最高 | `GET /api/v2/users` |
| `X-Api-Version` 请求头 | 中 | `X-Api-Version: 2` |
| 无任何指定 | 最低（默认） | 路由到 legacy 版本 |

---

## 10. 版本发布清单

每次新版本发布前检查：

1. [ ] `VERSION` 常量已更新
2. [ ] OpenAPI `version` 字段已更新
3. [ ] `CHANGELOG.md` 已记录变更
4. [ ] 向后兼容检查清单已执行
5. [ ] 废弃路由的 `Sunset` 头已更新
6. [ ] 开发者门户文档已同步
7. [ ] 测试覆盖新旧两套路由
8. [ ] 部署脚本中的路由健康检查已更新

---

## 附录：路由前缀速查

| Router 文件 | 原始 prefix | 版本化 prefix | 状态 |
|-------------|-------------|---------------|------|
| `auth.py` | `/api/auth` | `/api/v1/auth` | 废弃 ✓ |
| `alipay.py` | `/api/payment/alipay` | `/api/v1/payment/alipay` | 废弃 ✓ |
| `wxpay.py` | `/api/payment/wxpay` | `/api/v1/payment/wxpay` | 废弃 ✓ |
| `contacts.py` | `/api/contacts` | `/api/v1/contacts` | 废弃 ✓ |
| `products.py` | `/api/products` | `/api/v1/products` | 废弃 ✓ |
| `orders.py` | `/api/orders` | `/api/v1/orders` | 废弃 ✓ |
| `needs.py` | `/api/needs` | `/api/v1/needs` | 废弃 ✓ |
| `business_card.py` | `/api/business-card` | `/api/v1/business-card` | 废弃 ✓ |
| `matching_engine.py` | `/api/matching` | `/api/v1/matching` | 废弃 ✓ |
| `kg_coldstart.py` | `/api/matching` | `/api/v1/matching` | 废弃 ✓ |
| `audit.py` | `/api/v1/audit` | `/api/v1/audit` (不变) | 稳定 ✓ |
| `chat.py` | `/api/v1/chat` | `/api/v1/chat` (不变) | 稳定 ✓ |
| `ai_recommend.py` | `/api/v1/ai` | `/api/v1/ai` (不变) | 稳定 ✓ |
| `analytics.py` | `/api/v1/analytics` | `/api/v1/analytics` (不变) | 稳定 ✓ |
| `billing.py` | `/api/v1/billing` | `/api/v1/billing` (不变) | 稳定 ✓ |
