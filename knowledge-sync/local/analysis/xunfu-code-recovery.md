# 询赋吸收代码恢复方案

## 现状：代码没丢，是迁移断了

我找到了三层代码，每一层都在但**相互没连上**：

```
                        老miniapp (原生微信)         新liankebao-weapp (Taro)
                        ┌────────────────────┐      ┌─────────────────────┐
                        │ ✅ 平台列表页       │      │ ❌ supply-demand空壳 │
                        │ ✅ 平台详情页       │      │    (写了UI但没接API) │
【前端】正式页面         │ ✅ 平台管理页       │      └─────────────────────┘
                        │ ✅ 创建平台页       │
                        │ ✅ platform-bridge  │
                        └────────────────────┘
                                ↓ 调用                  
                        ┌────────────────────┐
                        │ ✅ platform_router  │  ← 已注册到 __init__.py
后端API (询赋吸收模块)   │ ✅ connection_router│  ← 已注册到 __init__.py
                        │ ✅ Platform 模型    │
                        │ ✅ Connection 模型  │
                        └────────────────────┘
```

**关键发现**：

**后端是完整的** — `platform_router.py`、`connection_router.py`、模型文件都在，已注册到app中。

**老miniapp是完整的** — `miniapp/pages/platform/` 下有 list/detail/manage/create 四个完整页面，带 WXML+JS+WXSS，通过 `platform-bridge.js` 桥接层调用后端API。

**新liankebao-weapp(supply-demand)是空壳** — 只写了前端UI框架(3个Tab、骨架屏、空状态)，但：
- 接口调的是不存在的 `/api/v1/matches` 
- 列表点击跳转的页面均不存在
- 没有连接老代码的 platform_router

## 恢复方案

### 第一优先级：修复断链 (今天可完成)

```python
# liankebao-weapp/src/api/ 新建 platform.ts
export interface Platform {
  id: number
  name: string
  platform_no?: string
  creator_id: number
  annual_fee: number
  description: string
  member_count: number
  resource_count: number
  created_at: string
  updated_at: string
}

const platformApi = {
  list: (keyword?, skip=0, limit=20) => 
    get('/api/business-card/platforms', { keyword, skip, limit }),
  getById: (id) => get(`/api/business-card/platforms/${id}`),
  create: (data) => post('/api/business-card/platforms', data),
  getMembers: (id) => get(`/api/business-card/platforms/${id}/members`),
  join: (id) => post(`/api/business-card/platforms/${id}/join`),
  getReport: (id) => get(`/api/business-card/platforms/${id}/report`),
}
```

| 页面 | 需修改 | 参考 |
|------|--------|------|
| `supply-demand/index.tsx` | 把 `/api/v1/matches` 改为调用 platformApi.list | 老代码 `platform-bridge.js#L9` |
| 新建 `supply-demand/detail/index.tsx` | 平台详情页(3Tab:介绍/资源/商机) | 老代码 `detail/index.wxml` + `detail/index.js` |
| 新建 `supply-demand/create/index.tsx` | 创建平台表单(名称/简介/省市区/行业) | 老代码 `create/index.js` |
| 新建 `supply-demand/manage/index.tsx` | 平台管理(成员/审核/覆盖率/排名) | 老代码 `manage/index.wxml` + `manage/index.js` |

### 代码对比

**老miniapp (完整)** → **新Taro (待建)**

```
miniapp/pages/platform/list/          →  liankebao-weapp/pages/supply-demand/ (改名为供需大厅)
miniapp/pages/platform/detail/       →  liankebao-weapp/pages/supply-demand/detail/
miniapp/pages/platform/create/       →  liankebao-weapp/pages/supply-demand/publish/ (改名为发布供需)
miniapp/pages/platform/manage/       →  liankebao-weapp/pages/supply-demand/manage/
```

老代码的WXML模板+JS逻辑可以直接作为UI逻辑参考迁移到Taro React组件。

### 页面路由修正

| 文件 | 当前 | 修正为 |
|------|------|--------|
| `index.tsx` 首页入口 | `/pages/market/index`(404) | `/pages/supply-demand/index` |
| `supply-demand/index.tsx` 发布 | `/pages/post-need/index`(404) | `/pages/supply-demand/publish/index` |
| `supply-demand/index.tsx` 详情 | `/pages/supply-demand/detail/index`(404) | `/pages/supply-demand/detail/index`(新建) |
| `supply-demand/index.tsx` API | `/api/v1/matches`(404) | `/api/business-card/platforms` |

---

要不要我现在就开始修复？步骤：
1. 先建 `platform.ts` API封装
2. 修首页入口路由
3. 修supply-demand页对接真实API
4. 新建详情页和发布页
